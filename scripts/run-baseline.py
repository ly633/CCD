"""Run the unchanged upstream sample benchmark and retain auditable results."""
import argparse
import ctypes
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import statistics
import subprocess
import time

ROOT = Path(__file__).resolve().parents[1]
FOLDERS = {
    "simulation": ["chain", "cow-heads", "golf-ball", "mat-twist"],
    "handcrafted": [
        "erleben-sliding-spike", "erleben-spike-wedge", "erleben-sliding-wedge",
        "erleben-wedge-crack", "erleben-spike-crack", "erleben-wedges",
        "erleben-cube-cliff-edges", "erleben-spike-hole",
        "erleben-cube-internal-edges", "erleben-spikes", "unit-tests",
    ],
}


def command(*args):
    return subprocess.check_output(args, cwd=ROOT, text=True, encoding="utf-8").strip()


def sha256(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def dataset_manifest(data):
    groups = {}
    for category, folders in FOLDERS.items():
        for primitive in ("vertex-face", "edge-edge"):
            files = []
            for folder in folders:
                directory = data / folder / primitive
                paths = sorted(directory.iterdir())
                if not paths:
                    raise RuntimeError(f"Empty dataset folder: {directory}")
                for path in paths:
                    if not path.is_file() or path.suffix != ".csv":
                        raise RuntimeError(f"Unexpected input in upstream traversal: {path}")
                    with path.open("rb") as stream:
                        lines = sum(1 for _ in stream)
                    if lines % 8:
                        raise RuntimeError(f"Invalid query row count: {path}")
                    files.append({"path": path.relative_to(data).as_posix(),
                                  "sha256": sha256(path), "queries": lines // 8})
            groups[f"{category}/{primitive}"] = {
                "queries": sum(f["queries"] for f in files), "files": files}
    return groups


def parse_output(output, manifest):
    pattern = r"Running (simulation|handcrafted) (vertex-face|edge-edge) data:"
    matches = list(re.finditer(pattern, output))
    if len(matches) != 4:
        raise RuntimeError(f"Expected 4 benchmark groups, found {len(matches)}")
    results = []
    fields = {
        "queries": (r"total # of queries:\s+(\d+)", int),
        "ground_truth_positives": (r"total positives:\s+(\d+)", int),
        "false_positives": (r"# of false positives:\s+(\d+)", int),
        "false_negatives": (r"# of false negatives:\s+(\d+)", int),
        "ccd_seconds": (r"total time:\s+([\d.eE+-]+) s", float),
        "average_microseconds": (r"average time:\s+([\d.eE+-]+)", float),
    }
    # fmt::print headers and spdlog summaries have different buffering on
    # Windows when redirected. Associate the four ordered summary blocks
    # with the four ordered headers, rather than using header positions.
    values = {}
    for field, (regex, convert) in fields.items():
        found = re.findall(regex, output)
        if len(found) != 4:
            raise RuntimeError(f"Expected 4 {field} entries, got {len(found)}")
        values[field] = [convert(value) for value in found]
    for index, match in enumerate(matches):
        key = f"{match[1]}/{match[2]}"
        result = {"group": key}
        for field in fields:
            result[field] = values[field][index]
        if result["queries"] != manifest[key]["queries"]:
            raise RuntimeError(f"Query count mismatch for {key}")
        results.append(result)
    return results


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--build-dir", default="build-baseline")
    parser.add_argument("--output", default=None,
                        help="Result directory; defaults to a new timestamped directory")
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument("--warmups", type=int, default=1)
    parser.add_argument("--cpu", type=int, default=0,
                        help="Windows logical CPU affinity; -1 leaves scheduling unrestricted")
    args = parser.parse_args()
    if args.repeats < 1 or args.warmups < 0:
        parser.error("repeats must be >= 1 and warmups must be >= 0")
    build = ROOT / args.build_dir
    executable = build / "app/Release/Tight_Inclusion_bin.exe"
    data = ROOT / "external/baseline/Sample-Queries-4d6cce3"
    output_dir = ROOT / (args.output or ("baseline-results/" + dt.datetime.now().strftime("%Y%m%d-%H%M%S-msvc")))
    if (output_dir / "results.json").exists():
        raise FileExistsError(f"Existing results will not be overwritten: {output_dir}")
    output_dir.mkdir(parents=True, exist_ok=True)
    if not executable.is_file():
        raise FileNotFoundError(executable)
    if os.name == "nt" and args.cpu >= 0:
        kernel = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel.GetCurrentProcess.restype = ctypes.c_void_p
        kernel.SetProcessAffinityMask.argtypes = [ctypes.c_void_p, ctypes.c_size_t]
        kernel.SetProcessAffinityMask.restype = ctypes.c_int
        if not kernel.SetProcessAffinityMask(kernel.GetCurrentProcess(), 1 << args.cpu):
            raise ctypes.WinError(ctypes.get_last_error())
    manifest = dataset_manifest(data)
    (output_dir / "dataset-manifest.json").write_text(
        json.dumps(manifest, indent=2), encoding="utf-8")
    dependencies = {}
    for name in ("spdlog", "CCD-Query-IO", "pbar", "CLI11"):
        directory = ROOT / "external/baseline" / name
        dependencies[name] = command("git", "-C", str(directory), "rev-parse", "HEAD")
    dependencies["Sample-Queries"] = "4d6cce33477d8d5c666c31c8ea23e1aea97be371"
    cache_prefixes = ("CMAKE_CXX_FLAGS", "CMAKE_GENERATOR:", "CMAKE_GENERATOR_PLATFORM:",
                      "TIGHT_INCLUSION_", "GMP_", "Eigen3_DIR:", "CCD_IO_SAMPLE_QUERIES_DIR:")
    build_settings = [line for line in (build / "CMakeCache.txt").read_text(encoding="utf-8").splitlines()
                      if line.startswith(cache_prefixes)]
    report = {
        "created_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "upstream_tag": "v1.0.6", "upstream_commit": command("git", "rev-parse", "v1.0.6"),
        "checkout_commit": command("git", "rev-parse", "HEAD"),
        "branch": command("git", "branch", "--show-current"),
        "core_source_diff": command("git", "diff", "v1.0.6", "--", "src", "app", "CMakeLists.txt", "cmake"),
        "platform": platform.platform(), "python": platform.python_version(),
        "logical_cpu_affinity": args.cpu, "benchmark_threads": 1,
        "executable": str(executable), "executable_sha256": sha256(executable),
        "gmp_runtime_sha256": sha256(executable.parent / "gmp.dll"),
        "build_settings": build_settings,
        "dependencies": dependencies,
        "parameters": {"precision": "double", "method": "BREADTH_FIRST_SEARCH",
                       "tolerance": 1e-6, "minimum_separation": 0.0,
                       "max_iterations": 1000000, "t_max": 1.0,
                       "numerical_error": [-1, -1, -1], "no_zero_toi": False},
        "timing_scope": "Upstream per-query timers; excludes file loading; wall time recorded separately",
        "warmups": [], "runs": [],
        "limitations": ["Official sample subset, not the full 60-million-query dataset",
                        "Boolean ground truth only; no exact TOI error measurement",
                        "Passing this dataset is not a proof of conservativeness"],
    }
    if report["core_source_diff"]:
        raise RuntimeError("Original baseline requires unchanged upstream algorithm and app sources")
    for index in range(args.warmups + args.repeats):
        warmup = index < args.warmups
        number = index + 1 if warmup else index - args.warmups + 1
        label = f"{'warmup' if warmup else 'run'}-{number}"
        log = output_dir / f"{label}.log"
        print(f"Starting {label}: {executable.name} --no-pbar", flush=True)
        started = time.perf_counter()
        with log.open("wb") as stream:
            process = subprocess.run([str(executable), "--no-pbar"], cwd=ROOT,
                                     stdout=stream, stderr=subprocess.STDOUT)
        wall = time.perf_counter() - started
        if process.returncode:
            raise RuntimeError(f"Benchmark exit code {process.returncode}; see {log}")
        groups = parse_output(log.read_text(encoding="utf-8", errors="replace"), manifest)
        run = {"log": log.name, "wall_seconds": wall, "groups": groups,
               "ccd_seconds": sum(g["ccd_seconds"] for g in groups)}
        report["warmups" if warmup else "runs"].append(run)
        (output_dir / "results.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
        if any(g["false_negatives"] for g in groups):
            raise RuntimeError(f"False negatives found; see {log}")
        print(f"Completed {label}: CCD {run['ccd_seconds']:.6f}s, wall {wall:.3f}s, FN=0", flush=True)
    summary = []
    for group_index, group in enumerate(report["runs"][0]["groups"]):
        timings = [r["groups"][group_index]["ccd_seconds"] for r in report["runs"]]
        for run in report["runs"]:
            for metric in ("queries", "ground_truth_positives", "false_positives", "false_negatives"):
                if run["groups"][group_index][metric] != group[metric]:
                    raise RuntimeError(f"Non-deterministic {metric} in {group['group']}")
        summary.append({**{k: v for k, v in group.items() if k not in ("ccd_seconds", "average_microseconds")},
                        "median_ccd_seconds": statistics.median(timings),
                        "min_ccd_seconds": min(timings), "max_ccd_seconds": max(timings),
                        "median_microseconds_per_query": statistics.median(timings) * 1e6 / group["queries"]})
    report["summary"] = summary
    report["total_queries_per_run"] = sum(g["queries"] for g in summary)
    report["median_total_ccd_seconds"] = statistics.median(r["ccd_seconds"] for r in report["runs"])
    report["correctness_passed"] = True
    (output_dir / "results.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps({"total_queries_per_run": report["total_queries_per_run"],
                      "median_total_ccd_seconds": report["median_total_ccd_seconds"],
                      "summary": summary}, indent=2), flush=True)


if __name__ == "__main__":
    main()

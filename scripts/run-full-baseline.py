"""Run the complete data preparation and unchanged CCD benchmark as one job.

Every phase writes status.json. A failed phase stops the job. The official
upstream algorithm and app remain unchanged. --adopt-download-pid can wait
for a download already launched by this workspace instead of duplicating it.
"""
import argparse
import ctypes
import datetime as dt
import gzip
import importlib.util
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import time
import traceback

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "external/baseline/Full-CCD-2020"
CACHE = ROOT / ".cache/downloads/full-ccd-2020"
SIZES = {
    "handcrafted": 1395440, "simulation-cow-heads": 666336779,
    "simulation-chain": 1451673931, "simulation-golf-ball": 833187667,
    "simulation-mat-twist": 413467056,
}


def utc():
    return dt.datetime.now(dt.timezone.utc).isoformat()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True)
    parser.add_argument("--adopt-download-pid", type=int)
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument("--warmups", type=int, default=1)
    args = parser.parse_args()
    output = (ROOT / args.output).resolve()
    if not output.is_relative_to(ROOT / "baseline-results"):
        raise RuntimeError("Output must be inside baseline-results")
    output.mkdir(parents=True, exist_ok=True)
    if (output / "status.json").exists() or (output / "results.json").exists():
        raise RuntimeError("Existing job results will not be overwritten")
    state = {"created_utc": utc(), "pid": os.getpid(), "status": "running",
             "phase": "initializing", "root": str(ROOT), "output": str(output),
             "warmups": args.warmups, "repeats": args.repeats,
             "scope": "Complete original NYU 2020 dataset, Tight-Inclusion v1.0.6 only"}

    def update(phase=None, **changes):
        if phase:
            state["phase"] = phase
        state.update(changes)
        state["updated_utc"] = utc()
        temporary = output / "status.json.tmp"
        temporary.write_text(json.dumps(state, indent=2), encoding="utf-8")
        temporary.replace(output / "status.json")

    def download_progress():
        progress = {}
        for name, size in SIZES.items():
            path = CACHE / f"ccd-queries-{name}.tar.gz"
            if not path.exists():
                path = path.with_suffix(path.suffix + ".part")
            current = path.stat().st_size if path.exists() else 0
            progress[name] = {"downloaded_bytes": current, "total_bytes": size,
                              "percent": round(100 * current / size, 2)}
            transfer_status = CACHE / f"{name}-download-status.json"
            if transfer_status.exists():
                progress[name]["transfer"] = json.loads(transfer_status.read_text(encoding="utf-8"))
        return progress

    def run(phase, command, log_name):
        update(phase, command=command, active_child_pid=None)
        with (output / log_name).open("wb") as log:
            process = subprocess.Popen(command, cwd=ROOT, stdout=log,
                                       stderr=subprocess.STDOUT)
            update(active_child_pid=process.pid)
            while process.poll() is None:
                update(downloads=download_progress())
                time.sleep(10)
        update(active_child_pid=None, last_exit_code=process.returncode)
        if process.returncode:
            raise RuntimeError(f"{phase} failed with exit code {process.returncode}; see {log_name}")

    try:
        update()
        if args.adopt_download_pid:
            if os.name != "nt":
                raise RuntimeError("Adopting a download process requires Windows")
            kernel = ctypes.WinDLL("kernel32", use_last_error=True)
            kernel.OpenProcess.argtypes = [ctypes.c_uint32, ctypes.c_int, ctypes.c_uint32]
            kernel.OpenProcess.restype = ctypes.c_void_p
            kernel.WaitForSingleObject.argtypes = [ctypes.c_void_p, ctypes.c_uint32]
            kernel.GetExitCodeProcess.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_uint32)]
            kernel.CloseHandle.argtypes = [ctypes.c_void_p]
            handle = kernel.OpenProcess(0x100000 | 0x1000, False, args.adopt_download_pid)
            if not handle:
                raise ctypes.WinError(ctypes.get_last_error())
            try:
                update("download_and_extract", active_child_pid=args.adopt_download_pid)
                while kernel.WaitForSingleObject(handle, 0) == 0x102:
                    update(downloads=download_progress())
                    time.sleep(10)
                exit_code = ctypes.c_uint32()
                if not kernel.GetExitCodeProcess(handle, ctypes.byref(exit_code)):
                    raise ctypes.WinError(ctypes.get_last_error())
                if exit_code.value:
                    raise RuntimeError(f"Adopted downloader exited with code {exit_code.value}")
            finally:
                kernel.CloseHandle(handle)
            update(active_child_pid=None)
        else:
            run("download_and_extract", [sys.executable, "-u", "scripts/fetch-full-data.py"], "download.log")

        spec = importlib.util.spec_from_file_location("baseline_runner", ROOT / "scripts/run-baseline.py")
        baseline = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(baseline)
        manifest, provenance = baseline.prepared_full_manifest(DATA)
        update("validate_archives", downloads=download_progress(),
               total_queries=provenance["total_queries"], groups={k: v["queries"] for k, v in manifest.items()})
        # Read gzip streams to EOF explicitly. tar extraction alone is not a
        # substitute for checking every archive's gzip trailer/CRC.
        validations = []
        for record in provenance["archives"]:
            path = ROOT / record["archive"]
            if path.stat().st_size != record["bytes"] or baseline.sha256(path) != record["sha256"]:
                raise RuntimeError(f"Archive hash/size changed: {path}")
            update(validating_archive=record["name"])
            size = 0
            heartbeat = time.monotonic()
            with gzip.open(path, "rb") as source:
                while chunk := source.read(8 * 1024 * 1024):
                    size += len(chunk)
                    if time.monotonic() - heartbeat > 20:
                        update(validating_uncompressed_bytes=size)
                        heartbeat = time.monotonic()
            validations.append({"archive": record["name"], "sha256": record["sha256"],
                                "gzip_crc_passed": True, "tar_bytes": size})
        (output / "archive-validation.json").write_text(json.dumps(validations, indent=2), encoding="utf-8")
        provenance["integrity"] = "Published HTTP sizes, archive SHA-256 recheck, gzip CRC to EOF, per-CSV SHA-256 at extraction and row counts"
        provenance["gzip_crc_validated_utc"] = utc()
        (DATA / "provenance.json").write_text(json.dumps(provenance, indent=2), encoding="utf-8")

        shell = shutil.which("pwsh") or shutil.which("powershell")
        if not shell:
            raise RuntimeError("PowerShell is required for the MSVC build")
        run("configure_and_build", [shell, "-NoProfile", "-ExecutionPolicy", "Bypass", "-File",
            "scripts/setup-baseline.ps1", "-BuildDirectory", "build-baseline-full",
            "-LogDirectory", str(output / "setup"), "-DataDirectory", str(DATA)], "build-driver.log")
        environment = {"recorded_utc": utc(), "platform": platform.platform(),
                       "python": sys.version, "python_executable": sys.executable}
        query = "Get-CimInstance Win32_Processor | Select-Object Name,NumberOfCores,NumberOfLogicalProcessors | ConvertTo-Json"
        environment["cpu"] = json.loads(subprocess.check_output([shell, "-NoProfile", "-Command", query], text=True))
        (output / "environment.json").write_text(json.dumps(environment, indent=2), encoding="utf-8")
        run("benchmark", [sys.executable, "-u", "scripts/run-baseline.py",
            "--dataset", "full-2020", "--build-dir", "build-baseline-full", "--data-dir", str(DATA),
            "--output", str(output), "--warmups", str(args.warmups), "--repeats", str(args.repeats),
            "--cpu", "0"], "benchmark-driver.log")
        result = json.loads((output / "results.json").read_text(encoding="utf-8"))
        if not result.get("correctness_passed") or len(result["runs"]) != args.repeats:
            raise RuntimeError("Benchmark did not complete all requested runs")
        update("complete", status="complete", completed_utc=utc(),
               total_queries=result["total_queries_per_run"],
               median_ccd_seconds=result["median_total_ccd_seconds"],
               summary=result["summary"])
        print(json.dumps(state, indent=2), flush=True)
    except BaseException as error:
        update(status="failed", active_child_pid=None, error=str(error), failed_utc=utc())
        traceback.print_exc()
        raise


if __name__ == "__main__":
    main()

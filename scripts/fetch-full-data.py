"""Download and audit the complete original 2020 CCD benchmark from NYU.

Archives remain in .cache/downloads; CSVs remain under external/baseline.
Extraction rejects non-regular/unsafe entries and records each CSV's SHA-256
and query count without loading the dataset into memory. run-full-baseline.py
additionally reads every gzip stream to EOF to validate archive CRCs.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor
import datetime as dt
import hashlib
import json
from pathlib import Path, PurePosixPath
import shutil
import tarfile
import time
import traceback
import urllib.request

from importlib.util import module_from_spec, spec_from_file_location

ROOT = Path(__file__).resolve().parents[1]
spec = spec_from_file_location("baseline", ROOT / "scripts/run-baseline.py")
baseline = module_from_spec(spec)
spec.loader.exec_module(baseline)
SOURCES = [
    ("handcrafted", "61519/2", 1395440),
    ("simulation-cow-heads", "61520/3", 666336779),
    ("simulation-chain", "61520/4", 1451673931),
    ("simulation-golf-ball", "61520/5", 833187667),
    ("simulation-mat-twist", "61520/6", 413467056),
]


def save_json(path, data):
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(data, indent=2), encoding="utf-8")
    temporary.replace(path)


def receive_response(response, partial, expected_size, progress):
    """Keep the longest verified prefix even when the server ignores Range.

    With HTTP 200, compare received bytes against the existing partial file
    before appending. A dropped connection must never truncate saved progress.
    """
    retained = partial.stat().st_size if partial.exists() else 0
    if retained > expected_size:
        raise RuntimeError(f"Partial archive is larger than expected: {partial}")
    if response.status == 206:
        expected_range = f"bytes {retained}-{expected_size - 1}/{expected_size}"
        if response.headers.get("Content-Range") != expected_range:
            raise RuntimeError("Incorrect HTTP range response")
        received = retained
    elif response.status == 200:
        received = 0
    else:
        raise RuntimeError(f"Unexpected HTTP status: {response.status}")
    content_length = response.headers.get("Content-Length")
    if content_length is not None and int(content_length) != expected_size - received:
        raise RuntimeError("HTTP Content-Length does not match the published archive size")
    mode = "r+b" if partial.exists() else "w+b"
    with partial.open(mode) as output:
        output.seek(received)
        while chunk := response.read(256 * 1024):
            if received + len(chunk) > expected_size:
                raise RuntimeError("Server sent more bytes than the published archive size")
            overlap = min(len(chunk), max(0, retained - received))
            if overlap and output.read(overlap) != chunk[:overlap]:
                raise RuntimeError("Downloaded data does not match the saved prefix; existing file preserved")
            if overlap < len(chunk):
                output.write(chunk[overlap:])
                output.flush()
            received += len(chunk)
            progress(received, max(retained, received), response.status)
    if received != expected_size:
        raise RuntimeError(f"Connection ended early: received {received} of {expected_size} bytes; saved prefix retained")


def download(source, cache, attempts=12):
    name, item, expected_size = source
    filename = f"ccd-queries-{name}.tar.gz"
    url = f"https://archive.nyu.edu/bitstream/2451/{item}/{filename}"
    target = cache / filename
    partial = target.with_suffix(target.suffix + ".part")
    if not target.exists():
        for attempt in range(1, attempts + 1):
            try:
                offset = partial.stat().st_size if partial.exists() else 0
                if offset == expected_size:
                    partial.rename(target)
                    break
                headers = {"Accept-Encoding": "identity"}
                if offset:
                    headers["Range"] = f"bytes={offset}-"
                request = urllib.request.Request(url, headers=headers)
                print(f"DOWNLOAD {name}: attempt {attempt}/{attempts}, retaining {offset} bytes", flush=True)
                with urllib.request.urlopen(request, timeout=180) as response:
                    started = reported = time.monotonic()
                    def report(received, saved, status):
                        nonlocal reported
                        now = time.monotonic()
                        if now - reported >= 20:
                            phase = "verifying_saved_prefix" if received < offset else "downloading_new_bytes"
                            speed = (received - (offset if status == 206 else 0)) / (now - started) / 1e6
                            event = {"updated_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
                                     "name": name, "attempt": attempt, "phase": phase,
                                     "response_status": status, "received_bytes": received,
                                     "saved_bytes": saved, "total_bytes": expected_size,
                                     "MB_per_second": round(speed, 3)}
                            save_json(cache / f"{name}-download-status.json", event)
                            print(f"DOWNLOAD {name}: {phase}, saved {saved / expected_size:.1%}, received {received / 1e6:.1f} MB, {speed:.2f} MB/s", flush=True)
                            reported = now
                    receive_response(response, partial, expected_size, report)
                partial.rename(target)
                break
            except Exception as error:
                event = {"updated_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
                         "name": name, "attempt": attempt, "phase": "retry_wait",
                         "error": repr(error), "saved_bytes": partial.stat().st_size if partial.exists() else 0}
                save_json(cache / f"{name}-download-status.json", event)
                print(f"DOWNLOAD {name} attempt {attempt} failed: {error!r}; retaining {event['saved_bytes']} bytes", flush=True)
                if attempt == attempts:
                    traceback.print_exc()
                    raise
                time.sleep(min(10 * attempt, 60))
    if target.stat().st_size != expected_size:
        raise RuntimeError(f"Unexpected existing archive size: {target}")
    digest = baseline.sha256(target)
    save_json(cache / f"{name}-download-status.json", {
        "updated_utc": dt.datetime.now(dt.timezone.utc).isoformat(), "name": name,
        "phase": "download_complete", "saved_bytes": expected_size, "sha256": digest})
    print(f"DOWNLOADED {name}: {expected_size} bytes, SHA256={digest}", flush=True)
    return {"name": name, "url": url, "bytes": expected_size, "sha256": digest,
            "archive": str(target.relative_to(ROOT))}


def extract(record, destination, cache):
    marker = cache / f"{record['name']}-extracted.json"
    if marker.exists():
        saved = json.loads(marker.read_text(encoding="utf-8"))
        if saved["archive_sha256"] == record["sha256"] and saved["destination"] == str(destination):
            if all((destination / f["path"]).is_file() and
                   (destination / f["path"]).stat().st_size == f["bytes"] for f in saved["files"]):
                print(f"Already extracted: {record['name']}", flush=True)
                return saved["files"]
    allowed_folders = set(sum(baseline.FOLDERS.values(), []))
    files = []
    seen = set()
    started = time.monotonic()
    with tarfile.open(ROOT / record["archive"], mode="r|gz") as package:
        for member in package:
            parts = PurePosixPath(member.name).parts
            if not parts or parts[0] not in allowed_folders or ".." in parts or "\\" in member.name:
                raise RuntimeError(f"Unexpected archive entry: {member.name}")
            target = destination.joinpath(*parts).resolve()
            if not target.is_relative_to(destination):
                raise RuntimeError(f"Unsafe archive entry: {member.name}")
            if member.isdir():
                target.mkdir(parents=True, exist_ok=True)
                continue
            if not member.isfile() or len(parts) != 3 or parts[1] not in ("vertex-face", "edge-edge") or not parts[2].endswith(".csv"):
                raise RuntimeError(f"Unsupported archive entry: {member.name}")
            if member.name in seen:
                raise RuntimeError(f"Duplicate archive entry: {member.name}")
            seen.add(member.name)
            target.parent.mkdir(parents=True, exist_ok=True)
            digest = hashlib.sha256()
            lines = size = 0
            final_byte = b""
            with package.extractfile(member) as source, target.open("wb") as output:
                while chunk := source.read(4 * 1024 * 1024):
                    output.write(chunk)
                    digest.update(chunk)
                    lines += chunk.count(b"\n")
                    size += len(chunk)
                    final_byte = chunk[-1:]
            if size and final_byte != b"\n":
                lines += 1
            if size != member.size or lines % 8:
                raise RuntimeError(f"Invalid CSV byte/row count: {member.name}")
            files.append({"path": member.name, "bytes": size,
                          "sha256": digest.hexdigest(), "queries": lines // 8})
            if time.monotonic() - started >= 20:
                print(f"EXTRACT {record['name']}: {len(files)} CSV files", flush=True)
                started = time.monotonic()
    save_json(marker, {"archive_sha256": record["sha256"], "destination": str(destination), "files": files})
    print(f"EXTRACTED {record['name']}: {len(files)} files, {sum(f['queries'] for f in files):,} queries", flush=True)
    return files


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workers", type=int, default=4)
    args = parser.parse_args()
    cache = ROOT / ".cache/downloads/full-ccd-2020"
    destination = (ROOT / "external/baseline/Full-CCD-2020").resolve()
    cache.mkdir(parents=True, exist_ok=True)
    destination.mkdir(parents=True, exist_ok=True)
    if shutil.disk_usage(destination).free < 80 * 1024**3:
        raise RuntimeError("At least 80 GiB free space is required for full data preparation")
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        records = list(pool.map(lambda source: download(source, cache), SOURCES))
    # Extract sequentially to avoid disk contention.
    files = []
    for record in records:
        files.extend(extract(record, destination, cache))
    paths = [f["path"] for f in files]
    if len(set(paths)) != len(paths):
        raise RuntimeError("Archives overlap")
    if {p.relative_to(destination).as_posix() for p in destination.rglob("*.csv")} != set(paths):
        raise RuntimeError("Untracked CSV files in full dataset directory")
    groups = {}
    for category, folders in baseline.FOLDERS.items():
        for primitive in ("vertex-face", "edge-edge"):
            selected = sorted((f for f in files if f["path"].split('/')[0] in folders
                               and f["path"].split('/')[1] == primitive), key=lambda f: f["path"])
            for folder in folders:
                if not any(f["path"].startswith(f"{folder}/{primitive}/") for f in selected):
                    raise RuntimeError(f"Missing dataset category: {folder}/{primitive}")
            groups[f"{category}/{primitive}"] = {
                "queries": sum(f["queries"] for f in selected), "files": selected}
    save_json(destination / "dataset-manifest.json", groups)
    save_json(destination / "provenance.json", {
        "created_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "collection": "https://archive.nyu.edu/handle/2451/61518",
        "dataset": "Complete original 2020 handcrafted and simulation datasets",
        "archives": records, "files": len(files), "uncompressed_bytes": sum(f["bytes"] for f in files),
        "total_queries": sum(g["queries"] for g in groups.values()),
        "integrity": "Published HTTP sizes, locally recorded archive SHA-256, per-CSV SHA-256 and row counts; gzip CRC checked by run-full-baseline.py",
    })
    print(json.dumps({k: v["queries"] for k, v in groups.items()}, indent=2), flush=True)
    print(f"Full dataset ready: {destination}", flush=True)


if __name__ == "__main__":
    main()

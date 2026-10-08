"""Fetch the official dataset at its upstream-pinned revision, with integrity checks."""
import hashlib
from pathlib import Path
import shutil
import urllib.request
import zipfile

ROOT = Path(__file__).resolve().parents[1]
REVISION = "4d6cce33477d8d5c666c31c8ea23e1aea97be371"
SHA256 = "1bab4462d6d42148bfadcca8a08c2dfb1d2de0d0e9f2072ac71ea8f6c37ba891"
URL = f"https://codeload.github.com/Continuous-Collision-Detection/Sample-Queries/zip/{REVISION}"
archive = ROOT / ".cache/downloads/sample-queries-4d6cce3.zip"
destination = ROOT / "external/baseline/Sample-Queries-4d6cce3"
archive.parent.mkdir(parents=True, exist_ok=True)
if not archive.exists():
    print(f"Downloading {URL}", flush=True)
    with urllib.request.urlopen(URL, timeout=60) as response, archive.open("wb") as output:
        shutil.copyfileobj(response, output)
with archive.open("rb") as stream:
    actual = hashlib.file_digest(stream, "sha256").hexdigest()
if actual != SHA256:
    raise RuntimeError(f"Dataset archive hash mismatch: {actual}")
destination.mkdir(parents=True, exist_ok=True)
with zipfile.ZipFile(archive) as package:
    for item in package.infolist():
        parts = Path(item.filename).parts
        if parts[0] != f"Sample-Queries-{REVISION}":
            raise RuntimeError(f"Unexpected archive entry: {item.filename}")
        target = destination.joinpath(*parts[1:]).resolve()
        if not target.is_relative_to(destination.resolve()):
            raise RuntimeError(f"Unsafe archive entry: {item.filename}")
        if item.is_dir():
            target.mkdir(parents=True, exist_ok=True)
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            with package.open(item) as source, target.open("wb") as output:
                shutil.copyfileobj(source, output)
print(f"Verified and extracted official sample data: {destination}", flush=True)

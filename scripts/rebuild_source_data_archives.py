#!/usr/bin/env python3
"""Rebuild submission ZIP archives and refresh Source Data checksums."""

from pathlib import Path
import hashlib
import zipfile

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "Source_Data"

files = [
    path for path in SOURCE.rglob("*")
    if path.is_file() and path.name not in {
        "Source_Data.xlsx", "Supplementary_Tables.xlsx",
        "Source_Data_CSV.zip", "Supplementary_Tables_CSV.zip", "checksums.sha256"
    }
]
with zipfile.ZipFile(SOURCE / "Source_Data_CSV.zip", "w", zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
    for path in sorted(files):
        archive.write(path, path.relative_to(SOURCE))

tables = sorted((ROOT / "tables").glob("*.csv"))
with zipfile.ZipFile(SOURCE / "Supplementary_Tables_CSV.zip", "w", zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
    for path in tables:
        archive.write(path, path.name)

def digest(path):
    value = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()

checksum_files = [path for path in sorted(SOURCE.rglob("*")) if path.is_file() and path.name != "checksums.sha256"]
(SOURCE / "checksums.sha256").write_text(
    "\n".join(f"{digest(path)}  {path.relative_to(SOURCE)}" for path in checksum_files) + "\n",
    encoding="utf-8",
)

print("Rebuilt CSV archives and refreshed Source Data checksums")

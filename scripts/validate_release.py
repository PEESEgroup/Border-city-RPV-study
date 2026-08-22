#!/usr/bin/env python3
"""Validate completeness and key numerical identities in the public release."""

from __future__ import annotations

import csv
import hashlib
import json
import math
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def rows(path: Path):
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


errors = []
forbidden = [ROOT / "tables/table_s_candidate_pair_screening.tex"]
for path in forbidden:
    if path.exists():
        errors.append(f"superseded selection artifact retained: {path.relative_to(ROOT)}")

required = [
    *(ROOT / "Source_Data/csv" / f"Fig_{i}.csv" for i in range(1, 7)),
    ROOT / "Source_Data/csv/Fig_S_grid_atlas.csv",
    ROOT / "Source_Data/csv/Fig_S_grid_sensitivity_city.csv",
    ROOT / "Source_Data/csv/Fig_S_grid_sensitivity_pair.csv",
    ROOT / "Source_Data/csv/Fig_S_policy.csv",
    ROOT / "Source_Data/csv/Fig_S_large_roof.csv",
    ROOT / "Source_Data/csv/Fig_S_detroit_windsor.csv",
    ROOT / "Source_Data/csv/Fig_S_economic_uncertainty.csv",
    ROOT / "Source_Data/csv/Fig_S7_building_planform_local_context_quality.csv",
    ROOT / "Source_Data/csv/Fig_S7_building_planform_local_context_pooled.csv",
    ROOT / "Source_Data/csv/Fig_S7_building_planform_local_context_city_specific.csv",
    ROOT / "Source_Data/csv/Fig_S7_building_planform_local_context_sensitivities.csv",
    ROOT / "Source_Data/csv/Fig_S8_sector_economic_envelope_inputs.csv",
    ROOT / "Source_Data/csv/Fig_S8_sector_economic_envelope_city.csv",
    ROOT / "Source_Data/csv/Fig_S8_sector_economic_envelope_pairwise.csv",
    ROOT / "Source_Data/csv/Fig_S8_sector_economic_envelope_central.csv",
    ROOT / "Source_Data/csv/Fig_S8_sector_economic_envelope_comparisons.csv",
    ROOT / "Source_Data/csv/Fig_S8_sector_economic_envelope_provenance.csv",
    ROOT / "Source_Data/Source_Data.xlsx",
    ROOT / "Source_Data/Source_Data_CSV.zip",
    *(ROOT / "figures/main" / f"Fig_{i}.pdf" for i in range(1, 7)),
    ROOT / "figures/supplementary/Fig_S_planform_local_context.pdf",
    ROOT / "figures/supplementary/Fig_S_sector_economic_envelope.pdf",
]
for path in required:
    if not path.exists() or path.stat().st_size == 0:
        errors.append(f"missing or empty: {path.relative_to(ROOT)}")

manifest = {row["item"]: row for row in rows(ROOT / "Source_Data/source_data_manifest.csv")}
for item in [f"Fig_{i}" for i in range(1, 7)]:
    actual = len(rows(ROOT / f"Source_Data/csv/{item}.csv"))
    expected = int(manifest[item]["rows"])
    if actual != expected:
        errors.append(f"{item}: manifest rows {expected}, actual {actual}")

fig2 = rows(ROOT / "Source_Data/csv/Fig_2.csv")
if sum(row.get("panel") == "a" for row in fig2) != 36:
    errors.append("Fig_2 panel a must contain 36 city-segment rows")
if sum(row.get("panel") == "b" for row in fig2) != 6:
    errors.append("Fig_2 panel b must contain six pair rows")

fig4a = rows(ROOT / "Source_Data/csv/Fig_4a.csv")
if len(fig4a) != 12:
    errors.append("Fig_4a must contain 12 primary cities")

uncertainty = rows(ROOT / "Source_Data/csv/Fig_S_economic_uncertainty.csv")
if len(uncertainty) != 12:
    errors.append("Supplementary economic uncertainty must contain 12 primary cities")
if any(row.get("City") in {"Detroit", "Windsor"} for row in uncertainty):
    errors.append("Detroit or Windsor found in primary economic uncertainty table")

sector_central = rows(ROOT / "Source_Data/csv/Fig_S8_sector_economic_envelope_central.csv")
primary_sector_central = [row for row in sector_central if row.get("scope") == "primary"]
primary_sector_aligned = sum(
    row.get("aligned_with_observed_sector_leader", "").lower() == "true"
    for row in primary_sector_central
)
if len(primary_sector_central) != 12 or primary_sector_aligned != 11:
    errors.append(
        f"sector-envelope central comparison expected 11/12 primary alignments, found {primary_sector_aligned}/{len(primary_sector_central)}"
    )

sector_summary = rows(ROOT / "Source_Data/csv/Fig_S8_sector_economic_envelope_pairwise.csv")
primary_sector_summary = [row for row in sector_summary if row.get("scope") == "primary"]
stable_count = sum(row.get("stable_economic_direction", "").lower() == "true" for row in primary_sector_summary)
fully_aligned_count = sum(math.isclose(float(row.get("alignment_share", "nan")), 1.0) for row in primary_sector_summary)
if len(primary_sector_summary) != 24 or stable_count != 19 or fully_aligned_count != 16:
    errors.append(
        "sector-envelope primary summary expected 24 rows, 19 stable directions and 16 fully aligned summaries; "
        f"found {len(primary_sector_summary)}, {stable_count} and {fully_aligned_count}"
    )

grid = rows(ROOT / "Source_Data/csv/Fig_S_grid_atlas.csv")
if len(grid) != 5238:
    errors.append(f"grid atlas expected 5,238 cells, found {len(grid)}")

dw = rows(ROOT / "Source_Data/csv/Fig_S_detroit_windsor_c.csv")
central = {
    row.get("city"): float(row.get("irr_pct"))
    for row in dw if row.get("scenario") == "Grant-realized central"
}
if central and (not math.isclose(central.get("Detroit", -99), 2.68, abs_tol=1e-9) or not math.isclose(central.get("Windsor", -99), 3.01, abs_tol=1e-9)):
    errors.append(f"Detroit–Windsor central IRRs differ from 2.68/3.01: {central}")

for line in (ROOT / "Source_Data/checksums.sha256").read_text(encoding="utf-8").splitlines():
    expected, relative = line.split("  ", 1)
    path = ROOT / "Source_Data" / relative
    if path.exists() and digest(path) != expected:
        errors.append(f"checksum mismatch: Source_Data/{relative}")

private_pattern = re.compile(r"/(?:datasets/joe|home/(?:yuezhuo|user))/")
for directory in [ROOT / "Source_Data", ROOT / "tables", ROOT / "docs", ROOT / "evidence", ROOT / "code"]:
    for path in directory.rglob("*"):
        if path.is_file() and path.suffix.lower() in {".csv", ".json", ".md", ".txt", ".tex"}:
            if private_pattern.search(path.read_text(encoding="utf-8", errors="ignore")):
                errors.append(f"private absolute path retained: {path.relative_to(ROOT)}")

report = {
    "status": "PASS" if not errors else "FAIL",
    "errors": errors,
    "source_data_csv_files": len(list((ROOT / "Source_Data/csv").glob("*.csv"))),
    "main_figures": len(list((ROOT / "figures/main").glob("Fig_[1-6].pdf"))),
    "supplementary_figures": len(list((ROOT / "figures/supplementary").glob("*.pdf"))),
}
print(json.dumps(report, indent=2, ensure_ascii=False))
sys.exit(1 if errors else 0)

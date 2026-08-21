#!/usr/bin/env python3
"""Build the active six-primary-pair Source Data records for revised Fig. 1."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "evidence" / "v1_verified_data"
OUT = ROOT / "Source_Data"
CSV_OUT = OUT / "csv"

PAIRS = [
    (1, "Vienna--Bratislava", "vienna", "bratislava"),
    (2, "Singapore--Johor Bahru", "singapore", "johorbahru"),
    (3, "San Diego--Tijuana", "sandiego", "tijuana"),
    (4, "El Paso--Juarez", "elpaso", "juarez"),
    (5, "Hong Kong--Shenzhen", "hongkong", "shenzhen"),
    (6, "Monaco--Nice", "monaco", "nice"),
]
PRIMARY_CITIES = [city for _, _, c1, c2 in PAIRS for city in (c1, c2)]


def base_row(panel: str, record_type: str) -> dict[str, object]:
    return {
        "panel": panel,
        "record_type": record_type,
        "pair_order": "",
        "pair": "",
        "city": "",
        "city_role": "",
        "metric": "",
        "value": "",
        "unit": "",
        "attribute_value": "",
        "definition": "",
        "source_file": "",
        "notes": "",
    }


def add_metric(rows, panel, record_type, metric, value, unit, source_file, notes=""):
    row = base_row(panel, record_type)
    row.update(
        metric=metric,
        value=value,
        unit=unit,
        source_file=source_file,
        notes=notes,
    )
    rows.append(row)


def main() -> None:
    coverage = pd.read_csv(DATA / "city_image_coverage_14cities.csv")
    city_metrics = pd.read_csv(DATA / "city_pv_metrics_14cities.csv")
    pair_results = pd.read_csv(DATA / "pair_results_7pairs.csv")

    coverage = coverage.loc[coverage["city"].isin(PRIMARY_CITIES)].copy()
    all_buildings = city_metrics.loc[
        city_metrics["city_key"].isin(PRIMARY_CITIES)
        & city_metrics["Segment"].eq("All buildings")
    ].copy()

    totals = {
        "primary_cities": len(PRIMARY_CITIES),
        "primary_pairs": len(PAIRS),
        "unique_orthophotos": int(coverage["image_count"].sum()),
        "mapped_area_km2": float(coverage["covered_area_km2"].sum()),
        "buildings": int(all_buildings["Buildings"].sum()),
        "building_footprint_area_km2": float(
            all_buildings["Building footprint area (m2)"].sum() / 1e6
        ),
        "mapped_pv_area_km2": float(all_buildings["PV area (m2)"].sum() / 1e6),
    }

    assert totals["unique_orthophotos"] == 326790
    assert abs(totals["mapped_area_km2"] - 5812.528531629437) < 1e-9
    assert totals["buildings"] == 4709656
    assert abs(totals["building_footprint_area_km2"] - 784.8896703373625) < 1e-9
    assert abs(totals["mapped_pv_area_km2"] - 19.2508271900072) < 1e-9

    rows: list[dict[str, object]] = []
    summary_specs = [
        ("primary_cities", totals["primary_cities"], "cities"),
        ("primary_pairs", totals["primary_pairs"], "pairs"),
        ("unique_orthophotos", totals["unique_orthophotos"], "orthophotos"),
        ("mapped_area", totals["mapped_area_km2"], "km2"),
        ("buildings", totals["buildings"], "buildings"),
        ("building_footprint_area", totals["building_footprint_area_km2"], "km2"),
        ("mapped_rooftop_pv_area", totals["mapped_pv_area_km2"], "km2"),
    ]
    for metric, value, unit in summary_specs:
        source = (
            "city_image_coverage_14cities.csv"
            if metric in {"unique_orthophotos", "mapped_area"}
            else "city_pv_metrics_14cities.csv"
        )
        if metric in {"primary_cities", "primary_pairs"}:
            source = "main_figure_pair_manifest_6pairs"
        notes = "Labelled validation tiles are a subset and are not added to the source-image total." if metric in {"unique_orthophotos", "mapped_area"} else ""
        add_metric(rows, "a", "displayed_summary", metric, value, unit, source, notes)

    # Panel b: city-level inventory accompanying the rendered density surfaces.
    coverage_idx = coverage.set_index("city")
    metric_idx = all_buildings.set_index("city_key")
    for pair_order, pair, c1, c2 in PAIRS:
        for role, city in (("city_1", c1), ("city_2", c2)):
            city_name = str(metric_idx.loc[city, "City"])
            values = [
                ("unique_orthophotos", coverage_idx.loc[city, "image_count"], "orthophotos", "city_image_coverage_14cities.csv"),
                ("mapped_area", coverage_idx.loc[city, "covered_area_km2"], "km2", "city_image_coverage_14cities.csv"),
                ("buildings", metric_idx.loc[city, "Buildings"], "buildings", "city_pv_metrics_14cities.csv"),
                ("pv_positive_buildings", metric_idx.loc[city, "PV-positive buildings"], "buildings", "city_pv_metrics_14cities.csv"),
                ("building_footprint_area", metric_idx.loc[city, "Building footprint area (m2)"] / 1e6, "km2", "city_pv_metrics_14cities.csv"),
                ("mapped_pv_area", metric_idx.loc[city, "PV area (m2)"] / 1e6, "km2", "city_pv_metrics_14cities.csv"),
                ("pv_utilization", metric_idx.loc[city, "PV utilization (%)"], "%", "city_pv_metrics_14cities.csv"),
            ]
            for metric, value, unit, source in values:
                row = base_row("b", "city_mapping_summary")
                row.update(
                    pair_order=pair_order,
                    pair=pair,
                    city=city_name,
                    city_role=role,
                    metric=metric,
                    value=value,
                    unit=unit,
                    source_file=source,
                    notes="Density surface uses footprint-linked PV representative points with an 8-pixel Gaussian smoothing parameter.",
                )
                rows.append(row)

    # Panel c is a conceptual analysis diagram; record the exact definitions.
    definitions = [
        ("pv_utilization", "Mapped PV area divided by total building-footprint area."),
        ("installation_prevalence", "PV-positive buildings divided by all eligible buildings."),
        ("roof_selection", "Mean footprint of PV-positive buildings divided by the mean footprint of all eligible buildings."),
        ("conditional_intensity", "Mapped PV area divided by the complete footprint area of PV-positive buildings."),
        ("spatial_concentration", "Distribution of mapped deployment across eligible 1-km grid cells; this is separate from the multiplicative identity."),
        ("contextual_diagnostics", "Income ordering, standardized IRR and documented-policy friction are directional contextual comparisons, not identified causal mechanisms."),
    ]
    for metric, definition in definitions:
        row = base_row("c", "concept_definition")
        row.update(
            metric=metric,
            definition=definition,
            source_file="manuscript Methods and Fig. 1 caption",
        )
        rows.append(row)

    # Panel d: two independently evaluated attributes for the primary pairs.
    pair_idx = pair_results.set_index("pair")
    for pair_order, pair, c1, c2 in PAIRS:
        source_pair = pair
        rec = pair_idx.loc[source_pair]
        for metric, attribute in (
            ("sector_leadership", rec["sectoral_direction_attribute"]),
            ("income_relation", rec["income_relation_attribute"]),
        ):
            row = base_row("d", "pair_attribute")
            row.update(
                pair_order=pair_order,
                pair=pair,
                city=str(rec["c1"]),
                city_role="city_1",
                metric=metric,
                attribute_value=str(attribute),
                definition=(
                    "Whether residential and non-residential PV leadership points to the same city or splits across the pair."
                    if metric == "sector_leadership"
                    else "Whether the all-building PV leader follows or reverses the within-pair income ordering."
                ),
                source_file="pair_results_7pairs.csv; six primary pairs only",
            )
            rows.append(row)

    CSV_OUT.mkdir(parents=True, exist_ok=True)
    out_path = CSV_OUT / "Fig_1.csv"
    pd.DataFrame(rows).to_csv(out_path, index=False)

    checks = {
        "status": "pass",
        "figure": "Fig. 1",
        "primary_pairs": 6,
        "primary_cities": 12,
        "detroit_windsor_excluded_from_main_figure": True,
        "totals": totals,
        "fig1_csv_rows": len(rows),
        "image_count_note": "326,790 is the unique source-orthophoto total. The 623 labelled tiles are a subset and are not added again.",
    }
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "source_data_checks_fig1.json").write_text(
        json.dumps(checks, indent=2), encoding="utf-8"
    )
    print(out_path)


if __name__ == "__main__":
    main()

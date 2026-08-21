#!/usr/bin/env python3
"""Build the reviewer-facing large-roof Supplementary sensitivity figure."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import matplotlib.figure
import matplotlib.axes
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
MANUSCRIPT_ROOT = ROOT
ORIGINAL_SCRIPT_DIR = ROOT / "code/original"
ORIGINAL_SCRIPT = ORIGINAL_SCRIPT_DIR / "plot_fig6b_large_roof_leverage.py"
INPUT = ROOT / "evidence/v1_verified_data/roofsize_14cities.csv"
CENTRAL = ROOT / "evidence/v1_verified_data/prevalence_intensity_14cities.csv"
FIGURE_DIR = ROOT / "figures/supplement/revision"
SOURCE_DIR = ROOT / "Source_Data/csv"
NOTES_DIR = ROOT / "Source_Data/figure_notes"
CHECKS_PATH = ROOT / "Source_Data/source_data_checks_fig_s_large_roof.json"

PAIRS = [
    ("vienna", "bratislava"),
    ("singapore", "johorbahru"),
    ("sandiego", "tijuana"),
    ("elpaso", "juarez"),
    ("hongkong", "shenzhen"),
    ("monaco", "nice"),
]
CITY_ORDER = [city for pair in PAIRS for city in pair]


def load_original_module():
    sys.path.insert(0, str(ORIGINAL_SCRIPT_DIR))
    spec = importlib.util.spec_from_file_location("original_large_roof", ORIGINAL_SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load {ORIGINAL_SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def render_with_panel_labels(module, output: Path, metrics: Path) -> None:
    """Reuse the original panel grammar and add regular vector panel identifiers."""
    original_savefig = matplotlib.figure.Figure.savefig
    original_axes_text = matplotlib.axes.Axes.text

    def text_without_arrow(axis, x, y, value, *args, **kwargs):
        if isinstance(value, str):
            value = value.replace(" -> ", " to ")
        return original_axes_text(axis, x, y, value, *args, **kwargs)

    def labelled_savefig(fig, *args, **kwargs):
        if not getattr(fig, "_supp_panel_labels_added", False):
            fig.canvas.draw()
            axes = fig.axes
            if len(axes) >= 2:
                for label, axis in zip(("a,", "b,"), axes[:2]):
                    pos = axis.get_position()
                    fig.text(
                        max(0.004, pos.x0 - 0.032),
                        min(0.995, pos.y1 + 0.012),
                        label,
                        ha="left",
                        va="top",
                        fontsize=11.5,
                        fontweight="normal",
                        family="sans-serif",
                        color="black",
                    )
            fig._supp_panel_labels_added = True
        return original_savefig(fig, *args, **kwargs)

    matplotlib.figure.Figure.savefig = labelled_savefig
    matplotlib.axes.Axes.text = text_without_arrow
    try:
        rows = module.load_rows(INPUT)
        module.plot_large_roof_leverage(rows, PAIRS, output, metrics)
    finally:
        matplotlib.figure.Figure.savefig = original_savefig
        matplotlib.axes.Axes.text = original_axes_text


def build_source_data(module) -> tuple[pd.DataFrame, dict[str, object]]:
    rows = module.load_rows(INPUT)
    points, uplifts = module.compute_large_roof_metrics(rows, PAIRS)
    point_df = pd.DataFrame(points).rename(columns={"all_utilization": "all_utilization_current"})
    point_df = point_df[point_df["city"].isin(CITY_ORDER)].copy()
    point_df["kind"] = "observed_city"
    point_df["pair"] = point_df["city"].map(
        {city: f"{a}--{b}" for a, b in PAIRS for city in (a, b)}
    )
    for col in [
        "area_share_1000",
        "pv_utilization_1000",
        "absolute_contribution_1000",
        "pv_area_share_1000",
        "all_utilization_current",
    ]:
        point_df[f"{col}_pct"] = 100 * point_df[col]

    uplift_df = pd.DataFrame(uplifts)
    uplift_df["kind"] = "illustrative_within_pair_benchmark"
    uplift_df["pair"] = uplift_df["pair"].str.replace("-", "--", regex=False)
    for col in [
        "area_share_1000",
        "current_utilization_1000",
        "frontier_utilization_1000",
        "all_utilization_current",
        "uplift_all",
        "all_utilization_counterfactual",
    ]:
        uplift_df[f"{col}_pct"] = 100 * uplift_df[col]

    source = pd.concat([point_df, uplift_df], ignore_index=True, sort=False)
    source["scope"] = "six primary pairs"
    source["interpretation"] = source["kind"].map({
        "observed_city": "observed mapped-PV and footprint quantities",
        "illustrative_within_pair_benchmark": "illustrative sensitivity; not causal, a target or a forecast",
    })

    central = pd.read_csv(CENTRAL).set_index("city_key")
    observed = point_df.set_index("city")
    max_all_error = float(
        (100 * observed.loc[CITY_ORDER, "all_utilization_current"]
         - central.loc[CITY_ORDER, "pv_utilization_pct"]).abs().max()
    )
    formula_error = float(
        (
            uplift_df["uplift_all"]
            - uplift_df["area_share_1000"]
            * (uplift_df["frontier_utilization_1000"] - uplift_df["current_utilization_1000"])
        ).abs().max()
    )
    checks = {
        "status": "pass",
        "primary_city_count": int(len(point_df)),
        "primary_pair_count": int(len(PAIRS)),
        "illustrative_benchmark_row_count": int(len(uplift_df)),
        "maximum_all_utilization_error_percentage_points": max_all_error,
        "maximum_benchmark_formula_error": formula_error,
        "detroit_windsor_excluded": not source["city"].isin(["detroit", "windsor"]).any(),
        "source_row_count": int(len(source)),
        "current_supplementary_figure": "S5",
    }
    assert checks["primary_city_count"] == 12
    assert checks["primary_pair_count"] == 6
    assert checks["illustrative_benchmark_row_count"] == 6
    assert max_all_error < 1e-8
    assert formula_error < 1e-12
    assert checks["detroit_windsor_excluded"]
    return source, checks


def write_notes() -> None:
    text = """# Source Data notes for the large-roof Supplementary sensitivity

Panel a reports observed quantities for the 12 primary cities. Large roofs are buildings in the 1000+ m2 footprint bin. Horizontal position is their share of city building-footprint area, vertical position is mapped PV area divided by building-footprint area in that bin, and bubble area represents the share of city mapped PV area located in the bin.

Panel b is an illustrative within-pair benchmark sensitivity. For the city with lower observed large-roof utilization in each primary pair, the calculation replaces that value with the paired city's observed large-roof utilization while holding the city's large-roof footprint share and all other roof-size-bin contributions fixed. The reported change is `large_roof_footprint_share * (paired_observed_large_roof_utilization - current_large_roof_utilization)`.

The benchmark is not a causal counterfactual, policy target or forecast. It does not account for structural suitability, usable roof area, orientation, pitch, shading, ownership, tenancy, onsite load, grid hosting capacity, financing, permitting or siting limits.

Detroit and Windsor are excluded because they are retained as a separate supplementary candidate-pair sensitivity.

Reproduction command from the revision root:

`python code/revision/plot_supp_large_roof_sensitivity.py`
"""
    NOTES_DIR.mkdir(parents=True, exist_ok=True)
    (NOTES_DIR / "Fig_S_large_roof_notes.md").write_text(text, encoding="utf-8")


def main() -> None:
    FIGURE_DIR.mkdir(parents=True, exist_ok=True)
    SOURCE_DIR.mkdir(parents=True, exist_ok=True)
    module = load_original_module()
    source, checks = build_source_data(module)
    source.to_csv(SOURCE_DIR / "Fig_S_large_roof.csv", index=False)
    CHECKS_PATH.write_text(json.dumps(checks, indent=2) + "\n", encoding="utf-8")
    write_notes()
    intermediate = SOURCE_DIR / "Fig_S_large_roof_original_metrics.csv"
    render_with_panel_labels(
        module,
        FIGURE_DIR / "fig_s_large_roof_sensitivity.pdf",
        intermediate,
    )
    render_with_panel_labels(
        module,
        FIGURE_DIR / "fig_s_large_roof_sensitivity.png",
        intermediate,
    )
    print(json.dumps(checks, indent=2))


if __name__ == "__main__":
    main()

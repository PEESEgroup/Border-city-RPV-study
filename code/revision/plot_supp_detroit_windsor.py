#!/usr/bin/env python3
"""Build the Detroit--Windsor supplementary candidate-pair figure package."""

from __future__ import annotations

import json
import math
from pathlib import Path

import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.patches import Patch


ROOT = Path(__file__).resolve().parents[2]
GRID_INPUT = ROOT / "evidence/v1_verified_data/grid_1km_14cities.geojson"
GRID_SUMMARY = ROOT / "evidence/v1_verified_data/grid_1km_city_heterogeneity_summary.csv"
ROOFSIZE_INPUT = ROOT / "evidence/v1_verified_data/roofsize_14cities.csv"
IRR_INPUT = ROOT / "evidence/v1_verified_data/detroit_windsor_irr_sensitivity.csv"
MAPPING_INPUT = ROOT / "tables/table_s_detroit_windsor_mapping.csv"
BOUNDARY_DIR = ROOT / "data/boundary"
FIGURE_DIR = ROOT / "figures/supplement/revision"
SOURCE_DIR = ROOT / "Source_Data/csv"
SPATIAL_DIR = ROOT / "Source_Data/spatial"
NOTES_DIR = ROOT / "Source_Data/figure_notes"
CHECKS_PATH = ROOT / "Source_Data/source_data_checks_fig_s_detroit_windsor.json"

GRID_CRS = "EPSG:6933"
CITIES = ["detroit", "windsor"]
DISPLAY = {"detroit": "Detroit", "windsor": "Windsor"}
DATES = {"detroit": "15 May 2025", "windsor": "6 June 2025"}
CITY_COLORS = {"detroit": "#4C78A8", "windsor": "#D28E4B"}
BIN_LABELS = ["zero", ">0 to 0.25", ">0.25 to 1", ">1 to 2.5", ">2.5 to 5", ">5 to 10", ">10"]
BIN_COLORS = ["#e5e5e5", "#f6e8c3", "#dfc27d", "#c2a96b", "#80cdc1", "#35978f", "#01665e"]
BIN_EDGES = [-math.inf, 0, 0.25, 1, 2.5, 5, 10, math.inf]


def configure_style() -> None:
    plt.rcParams.update({
        "font.family": "sans-serif",
        "font.sans-serif": ["Liberation Sans", "DejaVu Sans"],
        "font.size": 8.2,
        "axes.labelsize": 8.8,
        "xtick.labelsize": 7.5,
        "ytick.labelsize": 7.5,
        "legend.fontsize": 7.3,
        "axes.linewidth": 0.65,
    })


def load_inputs() -> tuple[gpd.GeoDataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    grid = gpd.read_file(GRID_INPUT)
    grid = grid[grid["city_key"].isin(CITIES) & grid["eligible_50_buildings"].astype(bool)].copy()
    grid = grid.to_crs(GRID_CRS)
    grid["pv_utilization_pct"] = 100 * grid["pv_utilization"]
    grid["zero_pv_eligible_cell"] = grid["pv_area_m2"] == 0
    grid["color_bin"] = pd.cut(
        grid["pv_utilization_pct"],
        bins=BIN_EDGES,
        labels=BIN_LABELS,
        include_lowest=True,
        right=True,
    ).astype(str)
    grid["imagery_date"] = grid["city_key"].map(DATES)

    roof = pd.read_csv(ROOFSIZE_INPUT)
    roof = roof[roof["city"].isin(CITIES)].copy()
    roof["pv_utilization_pct"] = 100 * roof["pv_area_ratio"]
    roof["footprint_share_pct"] = 100 * roof["building_area_m2"] / roof.groupby("city")["building_area_m2"].transform("sum")
    roof["pv_area_share_pct"] = 100 * roof["pv_area_m2"] / roof.groupby("city")["pv_area_m2"].transform("sum")

    irr = pd.read_csv(IRR_INPUT)
    rows = []
    lookup = irr.set_index("scenario")["IRR (%)"]
    scenarios = [
        ("central_support_realized", "Both supports realized\n(central)",
         "Detroit central: credit realized", "Windsor central: quote + grant"),
        ("neither_capital_support", "No capital support",
         "Detroit no federal credit", "Windsor quote, no grant"),
        ("detroit_credit_windsor_no_grant", "Detroit credit;\nWindsor no grant",
         "Detroit central: credit realized", "Windsor quote, no grant"),
    ]
    for order, (scenario_id, label, detroit_row, windsor_row) in enumerate(scenarios):
        rows.extend([
            {"scenario_id": scenario_id, "scenario_label": label, "scenario_order": order,
             "city_key": "detroit", "City": "Detroit", "irr_pct": float(lookup.loc[detroit_row])},
            {"scenario_id": scenario_id, "scenario_label": label, "scenario_order": order,
             "city_key": "windsor", "City": "Windsor", "irr_pct": float(lookup.loc[windsor_row])},
        ])
    irr_plot = pd.DataFrame(rows)
    mapping = pd.read_csv(MAPPING_INPUT)
    return grid, roof, irr_plot, mapping


def load_boundary(city: str) -> gpd.GeoDataFrame:
    return gpd.read_file(BOUNDARY_DIR / f"{city}.geojson").to_crs(GRID_CRS)


def plot_map(axis, grid: gpd.GeoDataFrame, city: str) -> None:
    boundary = load_boundary(city)
    boundary.plot(ax=axis, facecolor="#fafafa", edgecolor="#5f5f5f", linewidth=0.55, zorder=0)
    city_grid = grid[grid["city_key"] == city]
    for label, color in zip(BIN_LABELS, BIN_COLORS):
        subset = city_grid[city_grid["color_bin"] == label]
        if not subset.empty:
            subset.plot(ax=axis, facecolor=color, edgecolor="none", linewidth=0, zorder=1)
    boundary.plot(ax=axis, facecolor="none", edgecolor="#333333", linewidth=0.65, zorder=2)
    minx, miny, maxx, maxy = boundary.total_bounds
    pad_x = max((maxx - minx) * 0.035, 800)
    pad_y = max((maxy - miny) * 0.035, 800)
    axis.set_xlim(minx - pad_x, maxx + pad_x)
    axis.set_ylim(miny - pad_y, maxy + pad_y)
    axis.set_aspect("equal", adjustable="box")
    axis.set_xticks([])
    axis.set_yticks([])
    axis.set_title(f"{DISPLAY[city]}   {DATES[city]}", loc="left", fontsize=8.6, fontweight="normal", pad=2.5)
    for spine in axis.spines.values():
        spine.set_visible(False)


def build_figure(grid: gpd.GeoDataFrame, roof: pd.DataFrame, irr: pd.DataFrame) -> None:
    configure_style()
    fig = plt.figure(figsize=(7.25, 5.15))
    outer = fig.add_gridspec(
        2, 2,
        height_ratios=[1.22, 1.0],
        width_ratios=[1.04, 0.96],
        left=0.075, right=0.985, top=0.965, bottom=0.095,
        hspace=0.46, wspace=0.42,
    )
    maps = outer[0, :].subgridspec(1, 2, wspace=0.10)
    ax_detroit = fig.add_subplot(maps[0, 0])
    ax_windsor = fig.add_subplot(maps[0, 1])
    plot_map(ax_detroit, grid, "detroit")
    plot_map(ax_windsor, grid, "windsor")

    map_handles = [Patch(facecolor=color, edgecolor="none", label=label) for label, color in zip(BIN_LABELS, BIN_COLORS)]
    fig.legend(
        handles=map_handles,
        loc="upper center",
        bbox_to_anchor=(0.52, 0.535),
        ncol=4,
        frameon=False,
        title="Eligible-grid PV utilization (%)",
        title_fontsize=7.7,
        handlelength=1.0,
        columnspacing=1.0,
        handletextpad=0.35,
        labelspacing=0.3,
    )

    ax_roof = fig.add_subplot(outer[1, 0])
    bin_order = ["0-50", "50-100", "100-200", "200-500", "500-1000", "1000+"]
    x = np.arange(len(bin_order))
    for city in CITIES:
        d = roof[roof["city"] == city].set_index("roof_size_bin").loc[bin_order]
        ax_roof.plot(
            x, d["pv_utilization_pct"],
            color=CITY_COLORS[city], marker="o", markersize=4.2,
            linewidth=1.35, label=DISPLAY[city], zorder=3,
        )
        large = float(d.loc["1000+", "pv_utilization_pct"])
        ax_roof.text(
            x[-1] + (0.06 if city == "windsor" else -0.05),
            large + 0.08,
            f"{large:.2f}%",
            color=CITY_COLORS[city],
            ha="left" if city == "windsor" else "right",
            va="bottom",
            fontsize=7.3,
        )
    ax_roof.set_xticks(x, bin_order, rotation=28, ha="right")
    ax_roof.set_ylabel("PV utilization (%)")
    ax_roof.set_xlabel("Building-footprint area (m$^2$)")
    ax_roof.set_ylim(0, max(2.25, roof["pv_utilization_pct"].max() * 1.13))
    ax_roof.set_xlim(-0.15, len(bin_order) - 0.62)
    ax_roof.grid(axis="y", linestyle="--", linewidth=0.6, color="#bdbdbd", alpha=0.5)
    ax_roof.legend(frameon=False, loc="upper left", ncol=2, handlelength=1.5, columnspacing=1.0)
    for spine in ("top", "right"):
        ax_roof.spines[spine].set_visible(False)

    ax_irr = fig.add_subplot(outer[1, 1])
    scenario_order = ["central_support_realized", "neither_capital_support", "detroit_credit_windsor_no_grant"]
    y_positions = {scenario: 2 - i for i, scenario in enumerate(scenario_order)}
    for scenario in scenario_order:
        d = irr[irr["scenario_id"] == scenario].set_index("city_key")
        y = y_positions[scenario]
        values = [float(d.loc[city, "irr_pct"]) for city in CITIES]
        ax_irr.plot(values, [y, y], color="#8c8c8c", linewidth=1.0, zorder=1)
        for city, value in zip(CITIES, values):
            ax_irr.scatter(value, y, s=34, color=CITY_COLORS[city], edgecolor="white", linewidth=0.5, zorder=3)
            ax_irr.text(
                value + (0.09 if city == "windsor" else -0.09), y + 0.10,
                f"{value:.2f}%", color=CITY_COLORS[city],
                ha="left" if city == "windsor" else "right", va="bottom", fontsize=7.1,
            )
    labels = [
        irr.loc[irr["scenario_id"] == scenario, "scenario_label"].iloc[0]
        for scenario in scenario_order
    ]
    ax_irr.axvline(0, color="#777777", linestyle="--", linewidth=0.7, zorder=0)
    ax_irr.set_yticks([2, 1, 0], labels)
    ax_irr.set_xlabel("Modelled IRR (%)")
    ax_irr.set_xlim(-0.75, 3.45)
    ax_irr.set_ylim(-0.45, 2.45)
    ax_irr.grid(axis="x", linestyle="--", linewidth=0.6, color="#bdbdbd", alpha=0.5)
    legend_handles = [
        plt.Line2D([], [], marker="o", linestyle="none", color=CITY_COLORS[city], label=DISPLAY[city], markersize=5)
        for city in CITIES
    ]
    ax_irr.legend(handles=legend_handles, frameon=False, loc="lower right", ncol=2, handletextpad=0.35, columnspacing=0.8)
    for spine in ("top", "right"):
        ax_irr.spines[spine].set_visible(False)

    fig.canvas.draw()
    fig.text(0.018, 0.976, "a,", ha="left", va="top", fontsize=11.5, fontweight="normal")
    for label, axis in (("b,", ax_roof), ("c,", ax_irr)):
        pos = axis.get_position()
        fig.text(max(0.008, pos.x0 - 0.055), pos.y1 + 0.018, label, ha="left", va="top", fontsize=11.5, fontweight="normal")

    FIGURE_DIR.mkdir(parents=True, exist_ok=True)
    fig.savefig(FIGURE_DIR / "fig_s_detroit_windsor_spatial_sensitivity.pdf", bbox_inches="tight", pad_inches=0.035)
    fig.savefig(FIGURE_DIR / "fig_s_detroit_windsor_spatial_sensitivity.png", dpi=300, bbox_inches="tight", pad_inches=0.035)
    plt.close(fig)


def write_source_data(
    grid: gpd.GeoDataFrame,
    roof: pd.DataFrame,
    irr: pd.DataFrame,
    mapping: pd.DataFrame,
) -> dict[str, object]:
    SOURCE_DIR.mkdir(parents=True, exist_ok=True)
    SPATIAL_DIR.mkdir(parents=True, exist_ok=True)
    NOTES_DIR.mkdir(parents=True, exist_ok=True)

    grid_export = grid.drop(columns="geometry").copy()
    grid_export["panel"] = "a"
    grid_export.to_csv(SOURCE_DIR / "Fig_S_detroit_windsor_a.csv", index=False)
    grid.to_file(SPATIAL_DIR / "Fig_S_detroit_windsor_grid_cells.geojson", driver="GeoJSON")

    roof_export = roof.copy()
    roof_export["panel"] = "b"
    roof_export.to_csv(SOURCE_DIR / "Fig_S_detroit_windsor_b.csv", index=False)
    irr_export = irr.copy()
    irr_export["panel"] = "c"
    irr_export.to_csv(SOURCE_DIR / "Fig_S_detroit_windsor_c.csv", index=False)

    combined = pd.concat([
        grid_export.assign(record_type="eligible_grid_cell"),
        roof_export.assign(record_type="roof_size_bin"),
        irr_export.assign(record_type="irr_scenario"),
    ], ignore_index=True, sort=False)
    combined.to_csv(SOURCE_DIR / "Fig_S_detroit_windsor.csv", index=False)

    summary = pd.read_csv(GRID_SUMMARY).set_index("city_key")
    actual_counts = grid.groupby("city_key").size()
    expected_counts = summary.loc[CITIES, "eligible_grid_cells_50plus"].astype(int)
    count_error = int((actual_counts.loc[CITIES] - expected_counts).abs().max())
    zero_share = 100 * grid.groupby("city_key")["zero_pv_eligible_cell"].mean()
    zero_error = float((zero_share.loc[CITIES] - 100 * summary.loc[CITIES, "zero_pv_eligible_grid_share"]).abs().max())
    central = irr[irr["scenario_id"] == "central_support_realized"].set_index("city_key")["irr_pct"]
    mixed = irr[irr["scenario_id"] == "detroit_credit_windsor_no_grant"].set_index("city_key")["irr_pct"]
    mapping_lookup = mapping.set_index("metric")
    observed_gap = float(mapping_lookup.loc["all_building_pv_utilization_pct", "detroit"]) - float(
        mapping_lookup.loc["all_building_pv_utilization_pct", "windsor"]
    )
    checks = {
        "status": "pass",
        "candidate_pair_only": True,
        "eligible_grid_cells_detroit": int(actual_counts.loc["detroit"]),
        "eligible_grid_cells_windsor": int(actual_counts.loc["windsor"]),
        "maximum_eligible_cell_count_error": count_error,
        "maximum_zero_pv_share_error_percentage_points": zero_error,
        "roof_size_rows": int(len(roof)),
        "irr_scenario_rows": int(len(irr)),
        "central_grant_realized_irr_detroit_pct": float(central.loc["detroit"]),
        "central_grant_realized_irr_windsor_pct": float(central.loc["windsor"]),
        "central_scenario_alignment_with_windsor_pv_lead": bool(central.loc["windsor"] > central.loc["detroit"] and observed_gap < 0),
        "windsor_no_grant_reverses_order_relative_to_detroit_credit": bool(mixed.loc["detroit"] > mixed.loc["windsor"]),
        "combined_source_rows": int(len(combined)),
        "current_supplementary_figure": "S6",
    }
    assert count_error == 0
    assert zero_error < 1e-8
    assert len(roof) == 12
    assert len(irr) == 6
    assert abs(central.loc["detroit"] - 2.677420752186806) < 1e-10
    assert abs(central.loc["windsor"] - 3.0061892075569054) < 1e-10
    assert checks["central_scenario_alignment_with_windsor_pv_lead"]
    assert checks["windsor_no_grant_reverses_order_relative_to_detroit_credit"]
    CHECKS_PATH.write_text(json.dumps(checks, indent=2) + "\n", encoding="utf-8")
    return checks


def write_notes() -> None:
    text = """# Source Data notes for the Detroit--Windsor supplementary figure

Detroit--Windsor is a separately reported candidate-pair sensitivity and is not part of the six-pair primary figure set. It is not an external validation, random sample expansion or proof of generalizability.

Panel a uses the same globally anchored 1-km EPSG:6933 grid, at-least-50-buildings eligibility rule and fixed utilization bins as the 12-city atlas. All 395 Detroit and 125 Windsor eligible cells are shown, including zero-PV cells. Buildings are assigned by representative point and complete linked-PV and footprint areas follow the assigned building. Municipal boundaries are shown without assuming equivalence to DTE or ENWIN service territories. Imagery dates are 15 May 2025 and 6 June 2025.

Panel b reports observed PV utilization within the six building-footprint bins used for the primary cities. Utilization is complete linked PV-polygon area divided by building-footprint area within each bin. Windsor leads in every bin; the 1000+ m2 bin is labelled because it contributes most of the citywide gap.

Panel c reports three standardized IRR comparisons. The central row assumes realized capital support for both cities and gives 2.68% for Detroit and 3.01% for Windsor. The no-support row removes the Detroit federal credit and Windsor grant. The mixed row retains the Detroit federal credit and removes the Windsor grant, giving 2.68% versus 0.15% and reversing the ordering. These are scenario diagnostics, not observed project returns or causal explanations of mapped deployment.

Reproduction command from the revision root:

`python code/revision/plot_supp_detroit_windsor.py`
"""
    (NOTES_DIR / "Fig_S_detroit_windsor_notes.md").write_text(text, encoding="utf-8")


def main() -> None:
    grid, roof, irr, mapping = load_inputs()
    checks = write_source_data(grid, roof, irr, mapping)
    write_notes()
    build_figure(grid, roof, irr)
    print(json.dumps(checks, indent=2))


if __name__ == "__main__":
    main()

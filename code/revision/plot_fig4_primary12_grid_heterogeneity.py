#!/usr/bin/env python3
"""Build revised Fig. 4 on within-city 1-km grid heterogeneity.

Panel a summarizes eligible-cell PV-utilization distributions for 12 primary
cities. Panel b compares spatial concentration and the prevalence of eligible
cells without mapped PV. Panel c compares the signed aggregate citywide gap
with the signed median eligible-grid gap for six primary pairs.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.lines import Line2D
from matplotlib.offsetbox import AnnotationBbox, DrawingArea
from matplotlib.patches import PathPatch
from matplotlib.path import Path as MplPath

import plot_fig3_primary6_combined as style


ROOT = Path(__file__).resolve().parents[2]
GRID_INPUT = ROOT / "evidence/v1_verified_data/grid_1km_14cities.csv"
CITY_SUMMARY_INPUT = ROOT / "evidence/v1_verified_data/grid_1km_city_heterogeneity_summary.csv"
PAIR_SUMMARY_INPUT = ROOT / "evidence/v1_verified_data/pair_grid_heterogeneity_comparison.csv"

OUTDIR = ROOT / "figures/main/revision"
PANEL_OUTDIR = ROOT / "figures/panels/revision"
SOURCE_DIR = ROOT / "Source_Data/csv"
NOTES_DIR = ROOT / "Source_Data/figure_notes"
CHECKS_PATH = ROOT / "Source_Data/source_data_checks_fig4.json"
LOG_PATH = ROOT / "logs/13_fig4_grid_heterogeneity_draft.md"

TEXT = style.TEXT
MUTED = style.MUTED
AXIS = style.AXIS
GRID = style.GRID
PAIR_ORDER = style.PAIR_ORDER
PAIR_NAMES = style.PAIR_NAMES
PAIR_COLORS = style.PAIR_COLORS
SHOW_NAME = style.SHOW_NAME

PAIR_LABELS = {
    ("vienna", "bratislava"): "VIE–BRA",
    ("singapore", "johorbahru"): "SIN–JB",
    ("sandiego", "tijuana"): "SD–TIJ",
    ("elpaso", "juarez"): "EP–JUA",
    ("hongkong", "shenzhen"): "HK–SZ",
    ("monaco", "nice"): "MON–NIC",
}

PANEL_LABEL_VISIBLE_HEIGHT_PT = {"a": 9.49, "b": 9.49, "c": 9.49}
PANEL_LABEL_X = {"a": -0.33, "b": -0.20, "c": -0.42}


@lru_cache(maxsize=None)
def vector_panel_glyph(label: str) -> tuple[MplPath, float]:
    """Trace the Myriad Pro reference glyph into a compound vector path."""
    rgb = plt.imread(style.PANEL_GLYPHS[label])[..., :3]
    luminance = 0.2126 * rgb[..., 0] + 0.7152 * rgb[..., 1] + 0.0722 * rgb[..., 2]
    alpha = np.clip((0.92 - luminance) / 0.72, 0.0, 1.0)

    trace_figure = plt.figure(figsize=(1, 1))
    trace_axis = trace_figure.add_axes([0, 0, 1, 1])
    contour = trace_axis.contourf(alpha, levels=[0.45, 1.01], colors=["black"])
    paths = contour.get_paths()
    plt.close(trace_figure)
    if not paths:
        raise RuntimeError(f"Could not trace panel glyph {label}")

    compound = MplPath.make_compound_path(*paths)
    vertices = compound.vertices.copy()
    finite = np.isfinite(vertices).all(axis=1)
    xmin = float(vertices[finite, 0].min())
    xmax = float(vertices[finite, 0].max())
    ymin = float(vertices[finite, 1].min())
    ymax = float(vertices[finite, 1].max())
    glyph_height = ymax - ymin
    normalized = vertices.copy()
    normalized[:, 0] = (vertices[:, 0] - xmin) / glyph_height
    normalized[:, 1] = (ymax - vertices[:, 1]) / glyph_height
    return MplPath(normalized, compound.codes), (xmax - xmin) / glyph_height


def add_vector_panel_label(ax: plt.Axes, label: str) -> None:
    """Add a scale-independent Myriad Pro panel label below the axes top."""
    glyph_path, aspect = vector_panel_glyph(label)
    height = PANEL_LABEL_VISIBLE_HEIGHT_PT[label]
    width = height * aspect
    vertices = glyph_path.vertices.copy()
    vertices[:, 0] *= height
    vertices[:, 1] *= height
    drawing = DrawingArea(width, height, 0, 0, clip=False)
    drawing.add_artist(
        PathPatch(
            MplPath(vertices, glyph_path.codes),
            facecolor="#222222",
            edgecolor="none",
            linewidth=0,
        )
    )
    ax.add_artist(
        AnnotationBbox(
            drawing,
            (PANEL_LABEL_X[label], 1.0),
            xycoords=ax.transAxes,
            box_alignment=(0.0, 1.0),
            frameon=False,
            pad=0.0,
            annotation_clip=False,
        )
    )


def city_metadata() -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    n_pairs = len(PAIR_ORDER)
    for pair_index, pair in enumerate(PAIR_ORDER):
        center = (n_pairs - 1 - pair_index) * 2.70
        for role, city in enumerate(pair):
            rows.append(
                {
                    "city_key": city,
                    "city": SHOW_NAME[city],
                    "pair_index": pair_index,
                    "pair_key": PAIR_NAMES[pair],
                    "pair_label": PAIR_LABELS[pair],
                    "city_role": role + 1,
                    "city_color": PAIR_COLORS[pair][role],
                    "city_y": center + (0.34 if role == 0 else -0.34),
                    "pair_y": center,
                }
            )
    return pd.DataFrame(rows)


def read_inputs() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    grid = pd.read_csv(GRID_INPUT)
    city_summary = pd.read_csv(CITY_SUMMARY_INPUT)
    pair_summary = pd.read_csv(PAIR_SUMMARY_INPUT)
    return grid, city_summary, pair_summary


def build_panel_data() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, dict[str, object]]:
    grid, city_summary, pair_summary = read_inputs()
    metadata = city_metadata()
    primary = metadata["city_key"].tolist()

    eligible = grid.loc[
        grid["city_key"].isin(primary) & grid["eligible_50_buildings"].astype(bool)
    ].copy()
    eligible["pv_utilization_pct"] = eligible["pv_utilization"] * 100.0

    distribution = (
        eligible.groupby("city_key", sort=False)["pv_utilization_pct"]
        .agg(
            eligible_grid_count="size",
            p10=lambda x: x.quantile(0.10),
            p25=lambda x: x.quantile(0.25),
            median=lambda x: x.quantile(0.50),
            p75=lambda x: x.quantile(0.75),
            p90=lambda x: x.quantile(0.90),
            zero_pv_grid_count=lambda x: int((x == 0).sum()),
        )
        .reset_index()
    )
    distribution = metadata.merge(distribution, on="city_key", how="left", validate="one_to_one")

    summary = city_summary.loc[city_summary["city_key"].isin(primary)].copy()
    summary = metadata.merge(summary, on="city_key", how="left", validate="one_to_one")
    summary["top_decile_pv_area_share_pct"] = summary["top_decile_pv_area_share"] * 100.0
    summary["zero_pv_eligible_cell_share_pct"] = summary["zero_pv_eligible_grid_share"] * 100.0
    summary["eligible_cell_count"] = summary["eligible_grid_cells_50plus"]
    summary["top_decile_cell_count"] = summary["top_decile_utilization_cells"].astype(int)

    tie_rows: list[dict[str, object]] = []
    for city in primary:
        city_grid = eligible.loc[eligible["city_key"] == city].copy()
        values = city_grid["pv_utilization"].sort_values(ascending=False, kind="mergesort").to_numpy()
        top_n = max(1, int(np.ceil(0.10 * len(values))))
        cutoff = float(values[top_n - 1])
        above = int(np.sum(values > cutoff))
        tied = int(np.sum(values == cutoff))
        selected_at_cutoff = top_n - above
        tie_rows.append(
            {
                "city_key": city,
                "top_decile_cutoff_utilization": cutoff,
                "cutoff_tie_cell_count": tied,
                "cutoff_tie_cells_selected": selected_at_cutoff,
                "cutoff_tie_cells_excluded": tied - selected_at_cutoff,
            }
        )
    summary = summary.merge(pd.DataFrame(tie_rows), on="city_key", how="left", validate="one_to_one")

    expected_pairs = {PAIR_NAMES[pair] for pair in PAIR_ORDER}
    pairs = pair_summary.loc[pair_summary["pair"].isin(expected_pairs)].copy()
    pair_meta = []
    for pair_index, pair in enumerate(PAIR_ORDER):
        pair_meta.append(
            {
                "pair": PAIR_NAMES[pair],
                "pair_index": pair_index,
                "pair_label": PAIR_LABELS[pair],
                "city1_key": pair[0],
                "city2_key": pair[1],
                "pair_y": (len(PAIR_ORDER) - 1 - pair_index) * 2.70,
                "city1_color": PAIR_COLORS[pair][0],
                "city2_color": PAIR_COLORS[pair][1],
            }
        )
    pairs = pd.DataFrame(pair_meta).merge(pairs, on="pair", how="left", validate="one_to_one")
    pairs["aggregate_leader_key"] = np.where(
        pairs["aggregate_gap_pp"] >= 0, pairs["city1_key"], pairs["city2_key"]
    )
    pairs["median_grid_leader_key"] = np.where(
        pairs["grid_median_gap_pp"] >= 0, pairs["city1_key"], pairs["city2_key"]
    )
    pairs["same_direction_aggregate_vs_grid_median"] = pairs[
        "aggregate_and_grid_median_same_direction"
    ].astype(bool)
    pairs["pairwise_probability_city1_gt_city2"] = pairs[
        "probability_c1_grid_exceeds_c2_grid"
    ]
    pairs["leader_direction_differs"] = ~pairs["same_direction_aggregate_vs_grid_median"]
    pairs["aggregate_color"] = np.where(
        pairs["aggregate_gap_pp"] >= 0, pairs["city1_color"], pairs["city2_color"]
    )
    pairs["median_grid_color"] = np.where(
        pairs["grid_median_gap_pp"] >= 0, pairs["city1_color"], pairs["city2_color"]
    )

    frozen = summary.set_index("city_key")
    computed = distribution.set_index("city_key")
    max_quantile_error = float(
        max(
            np.max(np.abs(computed["p10"] - frozen["grid_utilization_p10_pct"])),
            np.max(np.abs(computed["median"] - frozen["grid_utilization_median_pct"])),
            np.max(np.abs(computed["p90"] - frozen["grid_utilization_p90_pct"])),
        )
    )
    checks = {
        "primary_city_count": int(len(metadata)),
        "primary_pair_count": int(len(pairs)),
        "eligible_grid_count": int(len(eligible)),
        "expected_eligible_grid_count": 5238,
        "max_quantile_error_percentage_points": max_quantile_error,
        "aggregate_vs_median_direction_disagreement_count": int(
            pairs["leader_direction_differs"].sum()
        ),
        "direction_disagreement_pairs": pairs.loc[
            pairs["leader_direction_differs"], "pair"
        ].tolist(),
        "top_decile_share_min_pct": float(summary["top_decile_pv_area_share_pct"].min()),
        "top_decile_share_max_pct": float(summary["top_decile_pv_area_share_pct"].max()),
        "detroit_or_windsor_present": bool(
            set(["detroit", "windsor"]) & set(metadata["city_key"])
        ),
    }

    assert checks["primary_city_count"] == 12
    assert checks["primary_pair_count"] == 6
    assert checks["eligible_grid_count"] == checks["expected_eligible_grid_count"]
    assert checks["max_quantile_error_percentage_points"] < 1e-8
    assert checks["aggregate_vs_median_direction_disagreement_count"] == 3
    assert not checks["detroit_or_windsor_present"]
    return distribution, pairs, summary, checks


def clean_axis(ax: plt.Axes) -> None:
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_visible(False)
    ax.spines["bottom"].set_color(AXIS)
    ax.spines["bottom"].set_linewidth(0.75)
    ax.tick_params(axis="x", colors=AXIS, labelsize=9.8, length=3.0, width=0.7)
    ax.tick_params(axis="y", length=0, pad=5)
    ax.grid(axis="x", color=GRID, linewidth=0.55, alpha=0.75, zorder=0)
    ax.set_axisbelow(True)


def draw_panel_a(ax: plt.Axes, data: pd.DataFrame, panel_label: bool = True) -> None:
    clean_axis(ax)
    for _, row in data.iterrows():
        y = float(row["city_y"])
        color = str(row["city_color"])
        ax.plot([row["p10"], row["p90"]], [y, y], color=AXIS, linewidth=1.15, zorder=2)
        ax.plot(
            [row["p25"], row["p75"]],
            [y, y],
            color=color,
            linewidth=5.4,
            alpha=0.62,
            solid_capstyle="butt",
            zorder=3,
        )
        ax.scatter(
            row["median"],
            y,
            s=36,
            facecolor=color,
            edgecolor="white",
            linewidth=0.65,
            zorder=4,
        )
        label_above = int(row["city_role"]) == 1
        ax.annotate(
            f'{row["median"]:.2f}',
            (row["median"], y),
            xytext=(3.2, 5.5 if label_above else -5.5),
            textcoords="offset points",
            fontsize=8.2,
            color=MUTED,
            va="bottom" if label_above else "top",
            ha="left",
            zorder=5,
        )

    for pair_index in range(1, len(PAIR_ORDER)):
        upper = data.loc[data["pair_index"] == pair_index - 1, "city_y"].min()
        lower = data.loc[data["pair_index"] == pair_index, "city_y"].max()
        ax.axhline((upper + lower) / 2.0, color="#e8e3df", linewidth=0.6, zorder=0)

    ax.set_xlim(0, 18.0)
    ax.set_xticks([0, 5, 10, 15])
    ax.set_ylim(data["city_y"].min() - 0.78, data["city_y"].max() + 0.78)
    ax.set_yticks(data["city_y"])
    ax.set_yticklabels(data["city"])
    for tick in ax.get_yticklabels():
        tick.set_color("#000000")
        tick.set_fontsize(10.0)
    ax.set_xlabel("Eligible-grid PV utilization (%)", fontsize=10.8, color=TEXT, labelpad=5)

    legend = [
        Line2D([0], [0], color=AXIS, linewidth=1.15, label="10th–90th"),
        Line2D([0], [0], color=AXIS, linewidth=5.4, alpha=0.62, label="IQR"),
        Line2D(
            [0], [0], marker="o", markersize=5.2, markerfacecolor=AXIS,
            markeredgecolor="white", linewidth=0, label="Median"
        ),
    ]
    ax.legend(
        handles=legend,
        ncol=1,
        frameon=False,
        fontsize=7.8,
        handlelength=1.6,
        columnspacing=0.8,
        handletextpad=0.45,
        loc="upper right",
        bbox_to_anchor=(0.995, 0.995),
        borderaxespad=0.0,
    )
    ax.text(
        0.99,
        0.015,
        "≥50 buildings;\nzero-PV grids retained.",
        transform=ax.transAxes,
        fontsize=8.0,
        color=MUTED,
        ha="right",
        va="bottom",
    )
    if panel_label:
        add_vector_panel_label(ax, "a")


def draw_gap_panel(
    ax: plt.Axes,
    data: pd.DataFrame,
    panel_label: bool = True,
    panel_id: str = "c",
) -> None:
    clean_axis(ax)
    ax.axvline(0, color=AXIS, linewidth=0.8, zorder=1)

    yticklabels = []
    for _, row in data.iterrows():
        y = float(row["pair_y"])
        ya = y + 0.14
        ym = y - 0.14
        linestyle = (0, (2.0, 1.5)) if row["leader_direction_differs"] else "-"
        ax.plot(
            [row["aggregate_gap_pp"], row["grid_median_gap_pp"]],
            [ya, ym],
            color="#a79e97",
            linewidth=1.15,
            linestyle=linestyle,
            zorder=2,
        )
        ax.scatter(
            row["aggregate_gap_pp"], ya, marker="o", s=41,
            facecolor=row["aggregate_color"], edgecolor="white", linewidth=0.7, zorder=3
        )
        ax.scatter(
            row["grid_median_gap_pp"], ym, marker="D", s=36,
            facecolor=row["median_grid_color"], edgecolor="white", linewidth=0.7, zorder=3
        )
        ax.annotate(
            f'{row["aggregate_gap_pp"]:+.2f}',
            (row["aggregate_gap_pp"], ya), xytext=(0, 5.0), textcoords="offset points",
            fontsize=8.0, color=MUTED, ha="center", va="bottom"
        )
        ax.annotate(
            f'{row["grid_median_gap_pp"]:+.2f}',
            (row["grid_median_gap_pp"], ym), xytext=(0, -5.0), textcoords="offset points",
            fontsize=8.0, color=MUTED, ha="center", va="top"
        )
        yticklabels.append(row["pair_label"] + ("*" if row["leader_direction_differs"] else ""))

    ax.set_xlim(-1.35, 6.45)
    ax.set_xticks([-1, 0, 2, 4, 6])
    ax.set_ylim(data["pair_y"].min() - 0.78, data["pair_y"].max() + 0.78)
    ax.set_yticks(data["pair_y"])
    ax.set_yticklabels(yticklabels, fontsize=9.5, color="#000000")
    ax.set_xlabel(
        "Signed PV-utilization gap\n(percentage points)",
        fontsize=10.0,
        color=TEXT,
        labelpad=5,
    )

    legend = [
        Line2D(
            [0], [0], marker="o", markersize=5.4, markerfacecolor=AXIS,
            markeredgecolor="white", linewidth=0, label="Aggregate citywide"
        ),
        Line2D(
            [0], [0], marker="D", markersize=5.0, markerfacecolor=AXIS,
            markeredgecolor="white", linewidth=0, label="Median eligible grid"
        ),
    ]
    ax.legend(
        handles=legend,
        ncol=1,
        frameon=False,
        fontsize=7.8,
        handletextpad=0.45,
        columnspacing=0.7,
        loc="lower right",
        bbox_to_anchor=(0.99, 0.185),
        borderaxespad=0.0,
    )
    ax.text(
        0.99,
        0.015,
        "City 1 − city 2;\n* leader differs.",
        transform=ax.transAxes,
        fontsize=7.9,
        color=MUTED,
        ha="right",
        va="bottom",
    )
    if panel_label:
        add_vector_panel_label(ax, panel_id)


def draw_concentration_panel(
    ax_top: plt.Axes,
    ax_zero: plt.Axes,
    data: pd.DataFrame,
    panel_label: bool = True,
    panel_id: str = "b",
    show_ylabels: bool = True,
) -> None:
    for ax in (ax_top, ax_zero):
        clean_axis(ax)
        ax.set_ylim(data["city_y"].min() - 0.78, data["city_y"].max() + 0.78)

    for _, pair_data in data.groupby("pair_index", sort=True):
        pair_data = pair_data.sort_values("city_role")
        ys = pair_data["city_y"].to_numpy()
        for ax, column in (
            (ax_top, "top_decile_pv_area_share_pct"),
            (ax_zero, "zero_pv_eligible_cell_share_pct"),
        ):
            xs = pair_data[column].to_numpy()
            ax.plot(xs, ys, color="#b7afa9", linewidth=1.1, zorder=2)
            for (_, row), x, y in zip(pair_data.iterrows(), xs, ys):
                ax.scatter(
                    x, y, s=38, facecolor=row["city_color"], edgecolor="white",
                    linewidth=0.7, zorder=3
                )

    for pair_index in range(1, len(PAIR_ORDER)):
        upper = data.loc[data["pair_index"] == pair_index - 1, "city_y"].min()
        lower = data.loc[data["pair_index"] == pair_index, "city_y"].max()
        divider = (upper + lower) / 2.0
        ax_top.axhline(divider, color="#e8e3df", linewidth=0.6, zorder=0)
        ax_zero.axhline(divider, color="#e8e3df", linewidth=0.6, zorder=0)

    ax_top.set_xlim(0, 70)
    ax_top.set_xticks([0, 20, 40, 60])
    ax_zero.set_xlim(0, 26)
    ax_zero.set_xticks([0, 10, 20])
    ax_top.set_yticks(data["city_y"])
    if show_ylabels:
        labels = [
            name + ("†" if key == "monaco" else "")
            for name, key in zip(data["city"], data["city_key"])
        ]
        ax_top.set_yticklabels(labels)
        for tick in ax_top.get_yticklabels():
            tick.set_color("#000000")
            tick.set_fontsize(9.7)
    else:
        ax_top.tick_params(axis="y", labelleft=False)
    ax_zero.set_yticks(data["city_y"])
    ax_zero.tick_params(axis="y", labelleft=False)
    ax_top.set_xlabel(
        "Top-decile grids\nPV-area share (%)",
        fontsize=9.5,
        color=TEXT,
        labelpad=6,
    )
    ax_zero.set_xlabel(
        "Eligible grids without\nmapped PV (%)",
        fontsize=9.5,
        color=TEXT,
        labelpad=6,
    )
    if panel_label:
        add_vector_panel_label(ax_top, panel_id)


def save_standalone_panels(
    distribution: pd.DataFrame,
    pairs: pd.DataFrame,
    concentration: pd.DataFrame,
) -> None:
    fig, ax = plt.subplots(figsize=(3.95, 5.85))
    draw_panel_a(ax, distribution)
    fig.subplots_adjust(left=0.29, right=0.98, top=0.94, bottom=0.23)
    for suffix, dpi in (("pdf", None), ("png", 300)):
        fig.savefig(
            PANEL_OUTDIR / f"fig4a_primary12_grid_distribution.{suffix}",
            dpi=dpi, bbox_inches="tight", pad_inches=0.04, facecolor="white"
        )
    plt.close(fig)

    fig = plt.figure(figsize=(5.225, 5.85))
    gs = fig.add_gridspec(1, 2, width_ratios=[1.15, 1.0], wspace=0.31)
    ax_top = fig.add_subplot(gs[0, 0])
    ax_zero = fig.add_subplot(gs[0, 1], sharey=ax_top)
    draw_concentration_panel(ax_top, ax_zero, concentration, panel_id="b")
    fig.subplots_adjust(left=0.27, right=0.98, top=0.94, bottom=0.23)
    for suffix, dpi in (("pdf", None), ("png", 300)):
        fig.savefig(
            PANEL_OUTDIR / f"fig4b_primary12_grid_concentration.{suffix}",
            dpi=dpi, bbox_inches="tight", pad_inches=0.04, facecolor="white"
        )
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(3.775, 5.85))
    draw_gap_panel(ax, pairs, panel_id="c")
    fig.subplots_adjust(left=0.28, right=0.98, top=0.94, bottom=0.23)
    for suffix, dpi in (("pdf", None), ("png", 300)):
        fig.savefig(
            PANEL_OUTDIR / f"fig4c_primary6_aggregate_vs_grid_median.{suffix}",
            dpi=dpi, bbox_inches="tight", pad_inches=0.04, facecolor="white"
        )
    plt.close(fig)


def save_combined_figure(
    distribution: pd.DataFrame,
    pairs: pd.DataFrame,
    concentration: pd.DataFrame,
) -> None:
    fig = plt.figure(figsize=(10.835, 5.665), facecolor="white")
    outer = fig.add_gridspec(
        1,
        5,
        width_ratios=[1.34, 0.25, 1.57, 0.52, 1.08],
        wspace=0.0,
    )
    ax_a = fig.add_subplot(outer[0, 0])
    middle = outer[0, 2].subgridspec(1, 2, width_ratios=[1.16, 1.0], wspace=0.30)
    ax_b1 = fig.add_subplot(middle[0, 0], sharey=ax_a)
    ax_b2 = fig.add_subplot(middle[0, 1], sharey=ax_b1)
    ax_c = fig.add_subplot(outer[0, 4])

    draw_panel_a(ax_a, distribution)
    draw_concentration_panel(
        ax_b1,
        ax_b2,
        concentration,
        panel_id="b",
        show_ylabels=False,
    )
    draw_gap_panel(ax_c, pairs, panel_id="c")
    fig.subplots_adjust(left=0.115, right=0.985, top=0.93, bottom=0.235)

    for suffix, dpi in (("pdf", None), ("png", 300)):
        fig.savefig(
            OUTDIR / f"fig_4.{suffix}",
            dpi=dpi, bbox_inches="tight", pad_inches=0.04, facecolor="white"
        )
    plt.close(fig)


def write_source_data(
    distribution: pd.DataFrame,
    pairs: pd.DataFrame,
    concentration: pd.DataFrame,
    checks: dict[str, object],
) -> None:
    panel_a_columns = [
        "pair_index", "pair_key", "city_role", "city_key", "city",
        "eligible_grid_count", "zero_pv_grid_count", "p10", "p25", "median", "p75", "p90",
    ]
    panel_b_columns = [
        "pair_index", "pair", "pair_label", "city1_key", "city2_key",
        "aggregate_gap_pp", "grid_median_gap_pp", "same_direction_aggregate_vs_grid_median",
        "leader_direction_differs", "aggregate_leader_key", "median_grid_leader_key",
        "pairwise_probability_city1_gt_city2",
    ]
    panel_c_columns = [
        "pair_index", "pair_key", "city_role", "city_key", "city", "eligible_cell_count",
        "top_decile_cell_count", "top_decile_pv_area_share_pct", "zero_pv_eligible_cell_share_pct",
        "top_decile_cutoff_utilization", "cutoff_tie_cell_count", "cutoff_tie_cells_selected",
        "cutoff_tie_cells_excluded",
    ]

    source_a = distribution[panel_a_columns].sort_values(["pair_index", "city_role"])
    source_b = concentration[panel_c_columns].sort_values(["pair_index", "city_role"])
    source_c = pairs[panel_b_columns].sort_values("pair_index")
    source_a.to_csv(SOURCE_DIR / "Fig_4a.csv", index=False)
    source_b.to_csv(SOURCE_DIR / "Fig_4b.csv", index=False)
    source_c.to_csv(SOURCE_DIR / "Fig_4c.csv", index=False)

    combined = pd.concat(
        [
            source_a.assign(panel="Fig. 4a"),
            source_b.assign(panel="Fig. 4b"),
            source_c.assign(panel="Fig. 4c"),
        ],
        ignore_index=True,
        sort=False,
    )
    first = combined.pop("panel")
    combined.insert(0, "panel", first)
    combined.to_csv(SOURCE_DIR / "Fig_4.csv", index=False)
    CHECKS_PATH.write_text(json.dumps(checks, indent=2) + "\n", encoding="utf-8")

    notes = """# Source Data notes for Fig. 4

Fig. 4 uses a globally anchored 1 km by 1 km grid in EPSG:6933. Buildings are assigned to grid cells by their representative points. The complete building footprint and linked rooftop PV area follow the assigned building. Boundary-crossing grid cells therefore retain only buildings assigned to the audited city boundary.

Eligible cells contain at least 50 buildings. All eligible cells are retained, including cells with no mapped rooftop PV. Panel a percentiles are calculated across these eligible cells.

For panel c, each signed gap is the first-listed city minus the second-listed city. A positive value indicates that the first-listed city leads. The disagreement flag is generated directly by comparing the signs of the aggregate citywide gap and the median eligible-grid gap.

For panel b, the number of top-decile cells is `max(1, ceil(0.10 × eligible-cell count))`. Cells are ranked by grid-level PV utilization in descending order. Exactly that number of cells is retained. If cells tie at the cutoff, the fixed-size rule is retained rather than expanding the top group to include all ties. The Source Data report the number of tied cells selected and excluded at each cutoff. Monaco has five eligible cells, so its top-decile summary is based on one cell and is marked as a small-denominator result.

The grid summaries describe spatial concentration and heterogeneity. They do not identify policy mechanisms or causal effects.
"""
    (NOTES_DIR / "Fig_4_notes.md").write_text(notes, encoding="utf-8")


def write_log(checks: dict[str, object]) -> None:
    text = f"""# Fig. 4 draft record

Date: 2026-08-20

Status: compact visual draft ready for author review.

## Scope

- Main-text scope is restricted to 12 cities and six primary border-city pairs.
- Detroit and Windsor are excluded from all three panels.
- The figure uses one common 1-km grid definition and the at-least-50-buildings eligibility rule.
- Zero-PV eligible cells are retained.
- The combined canvas is the arithmetic midpoint between the 13.0 × 6.8 inch first draft and the 8.67 × 4.53 inch compact draft; type sizes are retained for a less crowded relative scale.
- Panels a and b share the same city-axis positions and limits. Black city labels are shown once on panel a and suppressed on panel b in the combined figure.
- Independent horizontal spacers retain the a-to-b gap while using a shorter b-to-c gap; the vector b label is positioned closer to panel b.
- Panel labels are compound vector paths traced from the regular Myriad Pro reference glyphs, use a common 9.49 pt visible height, and remain within the axes upper boundary.
- Panel a median values are placed above first-listed-city boxes and below second-listed-city boxes to avoid covering intervals and markers.
- Eligibility and gap-direction notes are placed inside the lower-right corners of panels a and c, respectively.

## Panels

- Fig. 4a: eligible-grid PV-utilization distributions shown as 10th to 90th percentile ranges, interquartile ranges and medians.
- Fig. 4b: top-decile PV-area shares and zero-PV eligible-cell shares.
- Fig. 4c: signed aggregate citywide gaps compared with signed median eligible-grid gaps.

## Automated checks

- Eligible primary-city cells: {checks['eligible_grid_count']}.
- Quantile reproduction maximum error: {checks['max_quantile_error_percentage_points']:.3g} percentage points.
- Aggregate versus median-grid direction disagreements: {checks['aggregate_vs_median_direction_disagreement_count']}.
- Disagreement pairs: {', '.join(checks['direction_disagreement_pairs'])}.
- Top-decile PV-area-share range: {checks['top_decile_share_min_pct']:.2f}% to {checks['top_decile_share_max_pct']:.2f}%.

## Outputs

- `figures/main/revision/fig_4.pdf`
- `figures/main/revision/fig_4.png`
- standalone PDF and PNG panels under `figures/panels/revision/`
- `Source_Data/csv/Fig_4.csv` and panel-specific CSV files
- `Source_Data/figure_notes/Fig_4_notes.md`
- `Source_Data/source_data_checks_fig4.json`
"""
    LOG_PATH.write_text(text, encoding="utf-8")


def main() -> None:
    for directory in (OUTDIR, PANEL_OUTDIR, SOURCE_DIR, NOTES_DIR, LOG_PATH.parent):
        directory.mkdir(parents=True, exist_ok=True)
    distribution, pairs, concentration, checks = build_panel_data()
    for obsolete in (
        "fig4b_primary6_aggregate_vs_grid_median.pdf",
        "fig4b_primary6_aggregate_vs_grid_median.png",
        "fig4c_primary12_grid_concentration.pdf",
        "fig4c_primary12_grid_concentration.png",
    ):
        path = PANEL_OUTDIR / obsolete
        if path.exists():
            path.unlink()
    save_standalone_panels(distribution, pairs, concentration)
    save_combined_figure(distribution, pairs, concentration)
    write_source_data(distribution, pairs, concentration, checks)
    write_log(checks)
    print(json.dumps(checks, indent=2))


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Build the combined revised Fig. 2 with aligned panels and one legend.

Panel a preserves the original three-row utilization dumbbells without shaded
pattern groups. Panel b aligns one attribute row to the centre of each city
pair in panel a. The two panels share the y coordinates, marker definition and
small-denominator annotation.
"""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import numpy as np
import pandas as pd
from matplotlib.offsetbox import AnnotationBbox, OffsetImage
from matplotlib.lines import Line2D
from matplotlib.patches import Rectangle
from matplotlib.transforms import blended_transform_factory

import plot_fig2a_primary6_utilization_dumbbell as panel_a
import plot_fig2b_primary6_overlapping_attributes as panel_b


ROOT = Path(__file__).resolve().parents[2]
OUTDIR = ROOT / "figures/main/revision"
SOURCE_DATA = ROOT / "Source_Data/csv/Fig_2.csv"
CHECKS = ROOT / "Source_Data/source_data_checks_fig2.json"
PANEL_LABEL_A = ROOT / "figures/assets/revision/fig2_panel_label_a_myriadpro.png"
PANEL_LABEL_B = ROOT / "figures/assets/revision/fig2_panel_label_b_myriadpro.png"

TEXT = "#222222"
MUTED = "#4a4f52"
GRID = "#d8dddc"
VALUE_1_FILL = "#d9d9d9"
VALUE_2_FILL = "#efefef"
ROW_STEP = 0.56
PAIR_GAP = 0.40
PAIR_STEP = ROW_STEP * 3 + PAIR_GAP


def pair_centre(index: int) -> float:
    return index * PAIR_STEP + ROW_STEP


def add_myriad_panel_label(ax: plt.Axes, path: Path, xy: tuple[float, float], coords) -> None:
    """Place a regular Myriad Pro panel label rendered from the original Fig. 1."""
    rgb = mpimg.imread(path)[..., :3]
    luminance = 0.2126 * rgb[..., 0] + 0.7152 * rgb[..., 1] + 0.0722 * rgb[..., 2]
    alpha = np.clip((0.92 - luminance) / 0.72, 0.0, 1.0)
    rgba = np.zeros((*rgb.shape[:2], 4), dtype=float)
    rgba[..., :3] = np.array([34, 34, 34]) / 255.0
    rgba[..., 3] = alpha
    image = OffsetImage(rgba, zoom=0.055, interpolation="antialiased")
    label = AnnotationBbox(
        image,
        xy,
        xycoords=coords,
        box_alignment=(0.0, 0.5),
        frameon=False,
        pad=0.0,
        annotation_clip=False,
    )
    ax.add_artist(label)


def value_label(ax: plt.Axes, value: float, other: float, y: float) -> None:
    if abs(value - other) > 0.72:
        offset, ha = (0, 4), "center"
    elif value < other:
        offset, ha = (-6, 4), "right"
    else:
        offset, ha = (6, 4), "left"
    ax.annotate(
        f"{value:.2f}",
        (value, y),
        xytext=offset,
        textcoords="offset points",
        ha=ha,
        va="bottom",
        fontsize=5.8,
        color=MUTED,
        zorder=5,
    )


def draw_panel_a(ax: plt.Axes, city_data: pd.DataFrame) -> None:
    trans = blended_transform_factory(ax.transAxes, ax.transData)
    for pair_index, pair in enumerate(panel_a.PAIR_ORDER):
        c1, c2 = pair
        base_y = pair_index * PAIR_STEP
        centre = pair_centre(pair_index)
        pair_data = city_data.loc[city_data["pair_order"].eq(pair_index + 1)]
        color = panel_a.PAIR_COLOR[pair]

        for segment_index, segment in enumerate(panel_a.SEGMENTS):
            y = base_y + segment_index * ROW_STEP
            segment_data = pair_data.loc[pair_data["Segment"].eq(segment)].set_index("city_role")
            v1 = float(segment_data.at["city_1", "PV utilization (%)"])
            v2 = float(segment_data.at["city_2", "PV utilization (%)"])
            ax.plot([v1, v2], [y, y], color="#aab2b2", lw=0.9, zorder=2)
            ax.scatter(v1, y, s=27, facecolor=color, edgecolor=color, lw=0.8, zorder=4)
            ax.scatter(v2, y, s=27, facecolor="white", edgecolor=color, lw=1.05, zorder=4)
            value_label(ax, v1, v2, y)
            value_label(ax, v2, v1, y)
            ax.text(
                -0.03,
                y,
                panel_a.SEGMENT_LABEL[segment],
                transform=trans,
                ha="right",
                va="center",
                fontsize=7.0,
                color=TEXT,
                clip_on=False,
            )

        if pair_index < len(panel_a.PAIR_ORDER) - 1:
            ax.axhline(base_y + ROW_STEP * 2 + PAIR_GAP / 2, color="#e7e9e8", lw=0.6, zorder=0)

        marker_x = -0.56
        ax.plot(
            [marker_x],
            [centre - 0.18],
            marker="o",
            markersize=4.0,
            color=color,
            markerfacecolor=color,
            transform=trans,
            clip_on=False,
        )
        ax.plot(
            [marker_x],
            [centre + 0.18],
            marker="o",
            markersize=4.0,
            color=color,
            markerfacecolor="white",
            markeredgewidth=1.1,
            transform=trans,
            clip_on=False,
        )
        suffix = "†" if pair == ("monaco", "nice") else ""
        ax.text(
            -0.52,
            centre,
            f"{panel_a.SHOW_NAME[c1]} -\n{panel_a.SHOW_NAME[c2]}{suffix}",
            transform=trans,
            ha="left",
            va="center",
            fontsize=7.6,
            color=TEXT,
            linespacing=1.04,
            clip_on=False,
        )

    ax.set_xlim(0, 10)
    ax.set_xticks([0, 2, 4, 6, 8, 10])
    ax.set_yticks([])
    ax.set_xlabel("Rooftop PV utilization (%)", fontsize=8.2, color=TEXT, labelpad=5)
    ax.tick_params(axis="x", labelsize=7.2, colors=MUTED, length=2.5, width=0.6)
    ax.grid(axis="x", color=GRID, lw=0.55, zorder=0)
    for spine in ["top", "right", "left"]:
        ax.spines[spine].set_visible(False)
    ax.spines["bottom"].set_color("#b8bdbc")
    ax.spines["bottom"].set_linewidth(0.6)
    ax.text(
        -0.56,
        pair_centre(len(panel_a.PAIR_ORDER) - 1) + 0.93,
        "† Small denominator;\nsee Supplementary Table S1.",
        transform=trans,
        ha="left",
        va="center",
        fontsize=5.8,
        color=MUTED,
        linespacing=1.0,
        clip_on=False,
    )
    add_myriad_panel_label(ax, PANEL_LABEL_A, (-0.58, -0.50), trans)


def marker_face(role: str, color: str) -> str:
    if role == "city_1":
        return color
    if role == "city_2":
        return "white"
    return "#eeeeea"


def attribute_label(value: str) -> str:
    return {
        "same-side": "Same-side",
        "split": "Split",
        "income-aligned": "Aligned",
        "reversed": "Reversed",
    }.get(value, value.title())


def leader_fill(role: str) -> str:
    return VALUE_1_FILL if role == "city_1" else VALUE_2_FILL


def draw_panel_b(ax: plt.Axes, attributes: pd.DataFrame) -> None:
    x_centres = [0.45, 1.35, 2.25, 3.40, 4.72]
    headers = ["All\nPV", "Res.\nPV", "Non-res.\nPV", "Sector\nleadership", "Income\nordering"]
    leader_columns = ["all_building_leader", "residential_leader", "nonresidential_leader"]
    ax.set_xlim(0, 5.35)
    ax.set_yticks([])
    ax.set_facecolor("white")
    for spine in ax.spines.values():
        spine.set_visible(False)

    for i, row in attributes.iterrows():
        pair = panel_a.PAIR_ORDER[i]
        color = panel_a.PAIR_COLOR[pair]
        y = pair_centre(i)
        for x, width, column in zip(x_centres[:3], [0.82, 0.82, 0.82], leader_columns):
            role = str(row[f"{column}_role"])
            ax.add_patch(Rectangle((x - width / 2, y - 0.40), width, 0.80, facecolor=leader_fill(role), edgecolor="none", linewidth=0))
            ax.scatter(x, y, s=28, facecolor=marker_face(role, color), edgecolor=color, lw=1.05, zorder=4)
        sector_value = str(row["sector_leadership"])
        income_value = str(row["income_ordering"])
        ax.add_patch(
            Rectangle(
                (x_centres[3] - 1.27 / 2, y - 0.40),
                1.27,
                0.80,
                facecolor=VALUE_1_FILL if sector_value == "same-side" else VALUE_2_FILL,
                edgecolor="none",
                linewidth=0,
            )
        )
        ax.add_patch(
            Rectangle(
                (x_centres[4] - 1.17 / 2, y - 0.40),
                1.17,
                0.80,
                facecolor=VALUE_1_FILL if income_value == "income-aligned" else VALUE_2_FILL,
                edgecolor="none",
                linewidth=0,
            )
        )
        ax.text(x_centres[3], y, attribute_label(sector_value), ha="center", va="center", fontsize=6.15, color=TEXT)
        ax.text(x_centres[4], y, attribute_label(income_value), ha="center", va="center", fontsize=6.15, color=TEXT)

    ax.set_xticks(x_centres)
    ax.set_xticklabels(headers, fontsize=6.2, fontweight="normal", color=TEXT, linespacing=1.0)
    ax.tick_params(axis="x", which="both", bottom=True, top=False, labelbottom=True, length=0, pad=5)

    add_myriad_panel_label(ax, PANEL_LABEL_B, (-0.03, -0.50), ax.transData)


def save_combined_source_data(city_data: pd.DataFrame, attributes: pd.DataFrame) -> None:
    a = city_data.copy()
    a.insert(0, "panel", "a")
    a.insert(1, "record_type", "city_segment_utilization")
    b = attributes.copy()
    b.insert(0, "panel", "b")
    b.insert(1, "record_type", "pair_overlapping_attributes")
    combined = pd.concat([a, b], ignore_index=True, sort=False)
    SOURCE_DATA.parent.mkdir(parents=True, exist_ok=True)
    combined.to_csv(SOURCE_DATA, index=False)


def main() -> None:
    city_data = panel_a.load_primary_data()
    attributes = panel_b.build_source_data()
    save_combined_source_data(city_data, attributes)

    fig = plt.figure(figsize=(7.0, 5.75), dpi=300)
    grid = fig.add_gridspec(1, 2, width_ratios=[0.55, 0.45], wspace=0.10)
    ax_a = fig.add_subplot(grid[0, 0])
    ax_b = fig.add_subplot(grid[0, 1], sharey=ax_a)
    y_bottom = (len(panel_a.PAIR_ORDER) - 1) * PAIR_STEP + 2 * ROW_STEP + 0.66
    y_top = -0.72
    ax_a.set_ylim(y_bottom, y_top)
    draw_panel_a(ax_a, city_data)
    draw_panel_b(ax_b, attributes)

    legend = [
        Line2D([0], [0], marker="o", linestyle="none", markerfacecolor="#6f7f7b", markeredgecolor="#6f7f7b", markersize=4.5, label="first-listed city"),
        Line2D([0], [0], marker="o", linestyle="none", markerfacecolor="white", markeredgecolor="#6f7f7b", markersize=4.5, label="second-listed city"),
    ]
    ax_a.legend(
        handles=legend,
        loc="lower right",
        bbox_to_anchor=(0.995, 0.008),
        frameon=False,
        ncol=1,
        fontsize=6.0,
        handletextpad=0.45,
        labelspacing=0.35,
        borderaxespad=0.0,
        labelcolor=MUTED,
    )
    fig.subplots_adjust(left=0.245, right=0.992, top=0.975, bottom=0.13)

    OUTDIR.mkdir(parents=True, exist_ok=True)
    pdf = OUTDIR / "fig_2.pdf"
    png = OUTDIR / "fig_2.png"
    fig.savefig(pdf, bbox_inches="tight", pad_inches=0.02)
    fig.savefig(png, dpi=300, bbox_inches="tight", pad_inches=0.02)
    plt.close(fig)

    checks = {
        "status": "combined_figure_ready",
        "primary_pairs": 6,
        "primary_cities": 12,
        "panel_a_city_segment_rows": len(city_data),
        "panel_b_pair_rows": len(attributes),
        "shared_y_coordinates": True,
        "shared_marker_legend": True,
        "shared_small_denominator_note": True,
        "marker_legend_location": "inside panel a lower right in two rows",
        "small_denominator_note_location": "two lines below Nice and above the panel-a x-axis label",
        "panel_b_column_headers": "regular-weight x tick labels aligned with panel-a x tick labels",
        "reduced_top_whitespace": True,
        "panel_labels": "regular Myriad Pro a, and b,",
        "panel_b_cell_fills": [VALUE_1_FILL, VALUE_2_FILL],
        "panel_b_grid_lines": False,
        "panel_b_contextual_diagnostic_columns": 0,
        "panel_b_attributes": ["sector_leadership", "income_ordering"],
        "shaded_groups": 0,
        "svg_generated": False,
        "detroit_windsor_excluded": True,
        "output_pdf": str(pdf.relative_to(ROOT)),
        "source_data": str(SOURCE_DATA.relative_to(ROOT)),
    }
    CHECKS.write_text(json.dumps(checks, indent=2) + "\n", encoding="utf-8")
    print(f"[ok] Wrote {pdf}")
    print(f"[ok] Wrote {png}")
    print(f"[ok] Wrote {SOURCE_DATA}")
    print(json.dumps(checks, indent=2))


if __name__ == "__main__":
    main()

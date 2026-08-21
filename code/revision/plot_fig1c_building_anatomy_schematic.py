#!/usr/bin/env python3
"""Create a standalone schematic draft for revised main Fig. 1c.

The panel establishes the analytical order of the revised manuscript:
observed citywide deployment is decomposed into building-level dimensions,
then compared with contextual diagnostics. Arrows show analysis order only.
"""

from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, Rectangle


ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = ROOT / "figures" / "panels" / "revision"
OUT_STEM = OUT_DIR / "fig1c_building_anatomy_schematic"

TEXT = "#222222"
MUTED = "#5b6261"
GRID = "#d8dddc"
LIGHT_BG = "#f5f6f4"
ANATOMY_BG = "#f4f7f5"
CONTEXT_BG = "#f7f7f7"

COMPONENTS = [
    ("Installation prevalence", "Buildings with mapped PV", "#4f8f80"),
    ("Roof selection", "Mean footprint of PV-positive roofs\nrelative to all roofs", "#b8873a"),
    ("Conditional intensity", "PV area / footprint area\namong PV-positive buildings", "#8b6aa7"),
    ("Spatial concentration", "Distribution across eligible\n1-km grid cells", "#4d78a8"),
]


def add_box(ax, xy, width, height, facecolor, edgecolor=GRID, linewidth=0.8):
    patch = Rectangle(
        xy,
        width,
        height,
        transform=ax.transAxes,
        facecolor=facecolor,
        edgecolor=edgecolor,
        linewidth=linewidth,
        clip_on=False,
    )
    ax.add_patch(patch)
    return patch


def add_arrow(ax, x0, x1, y, label):
    arrow = FancyArrowPatch(
        (x0, y),
        (x1, y),
        transform=ax.transAxes,
        arrowstyle="-|>",
        mutation_scale=9,
        linewidth=0.9,
        color=MUTED,
        shrinkA=0,
        shrinkB=0,
    )
    ax.add_patch(arrow)
    ax.text(
        (x0 + x1) / 2,
        y + 0.045,
        label,
        transform=ax.transAxes,
        ha="center",
        va="bottom",
        fontsize=7.4,
        color=MUTED,
    )


def build_figure():
    mpl.rcParams.update(
        {
            "font.family": "sans-serif",
            "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans"],
            "font.size": 8,
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
            "svg.fonttype": "none",
        }
    )

    fig, ax = plt.subplots(figsize=(11.2, 4.35))
    fig.patch.set_facecolor("white")
    ax.set_facecolor("white")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    ax.text(0.015, 0.96, "c", fontsize=14, fontweight="bold", color=TEXT, va="top")
    ax.text(
        0.05,
        0.96,
        "From citywide gaps to building-level anatomy",
        fontsize=11.2,
        fontweight="bold",
        color=TEXT,
        va="top",
    )

    # Stage 1: observed deployment.
    left_x, left_y, left_w, left_h = 0.035, 0.24, 0.205, 0.57
    add_box(ax, (left_x, left_y), left_w, left_h, LIGHT_BG)
    ax.text(
        left_x + 0.018,
        left_y + left_h - 0.055,
        "Observed deployment",
        fontsize=9.2,
        fontweight="bold",
        color=TEXT,
        va="top",
        transform=ax.transAxes,
    )
    ax.text(
        left_x + 0.018,
        left_y + left_h - 0.15,
        "12 cities\nin six primary\nborder-city pairs",
        fontsize=8.4,
        color=TEXT,
        va="top",
        linespacing=1.35,
        transform=ax.transAxes,
    )
    ax.plot(
        [left_x + 0.018, left_x + left_w - 0.018],
        [left_y + 0.235, left_y + 0.235],
        transform=ax.transAxes,
        color=GRID,
        lw=0.8,
    )
    ax.text(
        left_x + 0.018,
        left_y + 0.19,
        "PV utilization",
        fontsize=8.4,
        fontweight="bold",
        color=TEXT,
        va="top",
        transform=ax.transAxes,
    )
    ax.text(
        left_x + 0.018,
        left_y + 0.125,
        "mapped PV area\nbuilding-footprint area",
        fontsize=7.4,
        color=MUTED,
        va="top",
        linespacing=1.25,
        transform=ax.transAxes,
    )
    ax.plot(
        [left_x + 0.022, left_x + left_w - 0.022],
        [left_y + 0.095, left_y + 0.095],
        transform=ax.transAxes,
        color=MUTED,
        lw=0.65,
    )

    # Stage 2: building-level anatomy.
    mid_x, mid_y, mid_w, mid_h = 0.315, 0.155, 0.405, 0.69
    add_box(ax, (mid_x, mid_y), mid_w, mid_h, ANATOMY_BG, edgecolor="#aabbb5", linewidth=1.0)
    ax.text(
        mid_x + 0.018,
        mid_y + mid_h - 0.045,
        "Building-level anatomy",
        fontsize=9.4,
        fontweight="bold",
        color=TEXT,
        va="top",
        transform=ax.transAxes,
    )

    cell_w = (mid_w - 0.054) / 2
    cell_h = 0.19
    positions = [
        (mid_x + 0.018, mid_y + 0.385),
        (mid_x + 0.036 + cell_w, mid_y + 0.385),
        (mid_x + 0.018, mid_y + 0.17),
        (mid_x + 0.036 + cell_w, mid_y + 0.17),
    ]
    for (title, desc, color), (x, y) in zip(COMPONENTS, positions):
        add_box(ax, (x, y), cell_w, cell_h, "white", edgecolor=GRID, linewidth=0.7)
        add_box(ax, (x, y), 0.008, cell_h, color, edgecolor=color, linewidth=0)
        ax.text(
            x + 0.02,
            y + cell_h - 0.042,
            title,
            fontsize=8.1,
            fontweight="bold",
            color=TEXT,
            va="top",
            transform=ax.transAxes,
        )
        ax.text(
            x + 0.02,
            y + cell_h - 0.105,
            desc,
            fontsize=6.9,
            color=MUTED,
            va="top",
            linespacing=1.25,
            transform=ax.transAxes,
        )

    ax.plot(
        [mid_x + 0.018, mid_x + mid_w - 0.018],
        [mid_y + 0.115, mid_y + 0.115],
        transform=ax.transAxes,
        color="#aabbb5",
        lw=0.8,
    )
    ax.text(
        mid_x + mid_w / 2,
        mid_y + 0.072,
        "Utilization = prevalence × roof selection × conditional intensity",
        fontsize=7.2,
        color=TEXT,
        ha="center",
        va="center",
        transform=ax.transAxes,
    )

    # Stage 3: contextual diagnostics.
    right_x, right_y, right_w, right_h = 0.795, 0.24, 0.17, 0.57
    add_box(ax, (right_x, right_y), right_w, right_h, CONTEXT_BG, edgecolor="#aeb3b2", linewidth=0.9)
    ax.text(
        right_x + 0.016,
        right_y + right_h - 0.055,
        "Contextual diagnostics",
        fontsize=8.7,
        fontweight="bold",
        color=TEXT,
        va="top",
        transform=ax.transAxes,
    )
    diagnostic_labels = ["Income ordering", "Standardized IRR", "Documented-policy\nfriction"]
    for i, label in enumerate(diagnostic_labels):
        y = right_y + right_h - 0.145 - i * 0.115
        ax.plot(
            [right_x + 0.018, right_x + 0.018],
            [y - 0.045, y + 0.02],
            transform=ax.transAxes,
            color="#7d8583",
            lw=1.7,
        )
        ax.text(
            right_x + 0.031,
            y,
            label,
            fontsize=7.7,
            color=TEXT,
            va="top",
            linespacing=1.2,
            transform=ax.transAxes,
        )
    ax.plot(
        [right_x + 0.016, right_x + right_w - 0.016],
        [right_y + 0.13, right_y + 0.13],
        transform=ax.transAxes,
        color=GRID,
        lw=0.8,
    )
    ax.text(
        right_x + 0.016,
        right_y + 0.095,
        "Directional comparisons,\nnot causal explanations",
        fontsize=6.7,
        color=MUTED,
        va="top",
        linespacing=1.2,
        transform=ax.transAxes,
    )

    add_arrow(ax, left_x + left_w + 0.012, mid_x - 0.012, 0.52, "Decompose")
    add_arrow(ax, mid_x + mid_w + 0.012, right_x - 0.012, 0.52, "Contextualize")

    ax.text(
        0.5,
        0.055,
        "Citywide rooftop PV gaps reflect distinct combinations of installation prevalence, roof selection, conditional intensity and spatial concentration.",
        fontsize=8.5,
        fontweight="bold",
        color=TEXT,
        ha="center",
        va="center",
        transform=ax.transAxes,
    )
    ax.plot([0.035, 0.965], [0.105, 0.105], transform=ax.transAxes, color=TEXT, lw=1.1)
    ax.text(
        0.965,
        0.012,
        "Analytical sequence, not a causal pathway",
        fontsize=6.6,
        color=MUTED,
        ha="right",
        va="bottom",
        transform=ax.transAxes,
    )

    return fig


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    fig = build_figure()
    for suffix in ("pdf", "svg", "png"):
        kwargs = {"bbox_inches": "tight", "pad_inches": 0.05}
        if suffix == "png":
            kwargs["dpi"] = 300
        fig.savefig(OUT_STEM.with_suffix(f".{suffix}"), **kwargs)
    plt.close(fig)
    print(OUT_STEM)


if __name__ == "__main__":
    main()

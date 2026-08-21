#!/usr/bin/env python3
"""Create a standalone schematic draft for revised main Fig. 1d.

The panel places the six primary city pairs on two independently evaluated
descriptive dimensions. It does not treat the former pattern labels as three
mutually exclusive categories and does not include Detroit–Windsor.
"""

from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle


ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = ROOT / "figures" / "panels" / "revision"
OUT_STEM = OUT_DIR / "fig1d_overlapping_attributes_schematic"

TEXT = "#222222"
MUTED = "#5b6261"
GRID = "#d8dddc"
LIGHT_BG = "#f7f7f6"
HEADER_BG = "#f0f2f1"

PAIR_COLORS = {
    "Vienna–Bratislava": "#7f8f49",
    "Singapore–Johor Bahru": "#b8873a",
    "San Diego–Tijuana": "#4f8f80",
    "El Paso–Juarez": "#4d78a8",
    "Hong Kong–Shenzhen": "#8b6aa7",
    "Monaco–Nice": "#bd6f74",
}

PLACEMENT = {
    ("same", "aligned"): [
        "Vienna–Bratislava",
        "Singapore–Johor Bahru",
        "San Diego–Tijuana",
    ],
    ("same", "reversed"): ["El Paso–Juarez"],
    ("split", "aligned"): [],
    ("split", "reversed"): ["Hong Kong–Shenzhen", "Monaco–Nice"],
}


def add_rect(ax, x, y, w, h, facecolor, edgecolor=GRID, linewidth=0.8):
    rect = Rectangle(
        (x, y),
        w,
        h,
        transform=ax.transAxes,
        facecolor=facecolor,
        edgecolor=edgecolor,
        linewidth=linewidth,
        clip_on=False,
    )
    ax.add_patch(rect)
    return rect


def add_pair(ax, x, y, label, color):
    ax.plot(
        [x, x + 0.036],
        [y, y],
        transform=ax.transAxes,
        color=color,
        lw=1.1,
        solid_capstyle="round",
        zorder=2,
    )
    ax.scatter(
        [x],
        [y],
        transform=ax.transAxes,
        s=31,
        facecolor=color,
        edgecolor=color,
        linewidth=0.8,
        zorder=3,
    )
    ax.scatter(
        [x + 0.036],
        [y],
        transform=ax.transAxes,
        s=31,
        facecolor="white",
        edgecolor=color,
        linewidth=1.0,
        zorder=3,
    )
    ax.text(
        x + 0.053,
        y,
        label,
        transform=ax.transAxes,
        ha="left",
        va="center",
        fontsize=7.6,
        color=TEXT,
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

    fig, ax = plt.subplots(figsize=(9.8, 5.2))
    fig.patch.set_facecolor("white")
    ax.set_facecolor("white")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    ax.text(0.015, 0.96, "d", fontsize=14, fontweight="bold", color=TEXT, va="top")
    ax.text(
        0.055,
        0.96,
        "Two overlapping attributes organize the six pairwise contrasts",
        fontsize=11.2,
        fontweight="bold",
        color=TEXT,
        va="top",
    )
    ax.text(
        0.055,
        0.895,
        "Six fixed primary pairs in a purposive comparative sample",
        fontsize=7.5,
        color=MUTED,
        va="top",
    )

    # Matrix geometry.
    grid_x, grid_y = 0.245, 0.19
    grid_w, grid_h = 0.70, 0.59
    label_w = 0.19
    col_w = grid_w / 2
    row_h = grid_h / 2

    # Column group title and headers.
    ax.text(
        grid_x + grid_w / 2,
        0.845,
        "Relation between all-building PV leadership and income ordering",
        transform=ax.transAxes,
        ha="center",
        va="center",
        fontsize=8.4,
        fontweight="bold",
        color=TEXT,
    )
    for j, title in enumerate(("Income-aligned", "Income-reversed")):
        x = grid_x + j * col_w
        add_rect(ax, x, grid_y + grid_h, col_w, 0.07, HEADER_BG)
        ax.text(
            x + col_w / 2,
            grid_y + grid_h + 0.035,
            title,
            transform=ax.transAxes,
            ha="center",
            va="center",
            fontsize=8.1,
            fontweight="bold",
            color=TEXT,
        )

    # Row header and labels.
    add_rect(ax, grid_x - label_w, grid_y + grid_h, label_w, 0.07, HEADER_BG)
    ax.text(
        grid_x - label_w / 2,
        grid_y + grid_h + 0.035,
        "Residential vs non-residential leadership",
        transform=ax.transAxes,
        ha="center",
        va="center",
        fontsize=7.0,
        fontweight="bold",
        color=TEXT,
    )
    row_specs = [
        ("same", "Same-side", grid_y + row_h),
        ("split", "Split", grid_y),
    ]
    col_specs = [("aligned", grid_x), ("reversed", grid_x + col_w)]

    for row_key, row_title, y in row_specs:
        add_rect(ax, grid_x - label_w, y, label_w, row_h, HEADER_BG)
        ax.text(
            grid_x - label_w / 2,
            y + row_h / 2,
            row_title,
            transform=ax.transAxes,
            ha="center",
            va="center",
            fontsize=8.1,
            fontweight="bold",
            color=TEXT,
        )

        for col_key, x in col_specs:
            add_rect(ax, x, y, col_w, row_h, "white")
            pairs = PLACEMENT[(row_key, col_key)]
            if not pairs:
                ax.text(
                    x + col_w / 2,
                    y + row_h / 2,
                    "No primary pair",
                    transform=ax.transAxes,
                    ha="center",
                    va="center",
                    fontsize=7.3,
                    color=MUTED,
                    style="italic",
                )
                continue

            spacing = 0.078
            start_y = y + row_h / 2 + spacing * (len(pairs) - 1) / 2
            for i, pair in enumerate(pairs):
                add_pair(
                    ax,
                    x + 0.038,
                    start_y - i * spacing,
                    pair,
                    PAIR_COLORS[pair],
                )

    # Explanatory footer.
    ax.plot([0.055, 0.945], [0.12, 0.12], transform=ax.transAxes, color=TEXT, lw=1.0)
    ax.text(
        0.055,
        0.075,
        "The two attributes are evaluated independently. Their combinations describe the observed cases and do not define universal city types.",
        transform=ax.transAxes,
        ha="left",
        va="center",
        fontsize=7.6,
        color=TEXT,
    )
    ax.text(
        0.945,
        0.022,
        "Filled and open circles denote the first-listed and second-listed city",
        transform=ax.transAxes,
        ha="right",
        va="bottom",
        fontsize=6.5,
        color=MUTED,
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

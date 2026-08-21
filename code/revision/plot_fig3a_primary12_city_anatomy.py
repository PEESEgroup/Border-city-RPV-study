#!/usr/bin/env python3
"""Draft Fig. 3a: three-factor city anatomy in the visual language of original Fig. 6a."""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.image as mpimg
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.offsetbox import AnnotationBbox, OffsetImage


ROOT = Path(__file__).resolve().parents[2]
INPUT = ROOT / "evidence/v1_verified_data/prevalence_intensity_14cities.csv"
OUTDIR = ROOT / "figures/panels/revision"
SOURCE_DATA = ROOT / "Source_Data/csv/Fig_3a.csv"
PANEL_LABEL = ROOT / "figures/assets/revision/fig2_panel_label_a_myriadpro.png"

PAIR_ORDER = [
    ("vienna", "bratislava"),
    ("singapore", "johorbahru"),
    ("sandiego", "tijuana"),
    ("elpaso", "juarez"),
    ("hongkong", "shenzhen"),
    ("monaco", "nice"),
]

PAIR_COLORS = {
    ("vienna", "bratislava"): ("#c97c5d", "#8c4f3f"),
    ("singapore", "johorbahru"): ("#d9a441", "#9a6a12"),
    ("sandiego", "tijuana"): ("#5aa469", "#2f6b3b"),
    ("elpaso", "juarez"): ("#4f7cac", "#1f4e79"),
    ("hongkong", "shenzhen"): ("#b07bac", "#7f4f7c"),
    ("monaco", "nice"): ("#d16d8a", "#8f3458"),
}

METRICS = [
    ("prevalence_pct", "PV-positive-building\nprevalence (%)", [0, 5, 10, 15], 16.2),
    ("roof_size_selection", "Roof selection\nratio", [0, 4, 8, 12], 12.8),
    ("conditional_intensity_pct", "Conditional PV-area\nintensity (%)", [0, 10, 20, 30], 32.5),
]

TEXT = "#2f2a27"
AXIS = "#6e6259"
GRID = "#d8d0ca"


def add_myriad_panel_label(ax: plt.Axes) -> None:
    if not PANEL_LABEL.exists():
        ax.text(-0.33, 1.14, "a,", transform=ax.transAxes, ha="left", va="center", fontsize=13)
        return
    rgb = mpimg.imread(PANEL_LABEL)[..., :3]
    luminance = 0.2126 * rgb[..., 0] + 0.7152 * rgb[..., 1] + 0.0722 * rgb[..., 2]
    alpha = np.clip((0.92 - luminance) / 0.72, 0.0, 1.0)
    rgba = np.zeros((*rgb.shape[:2], 4), dtype=float)
    rgba[..., :3] = np.array([34, 34, 34]) / 255.0
    rgba[..., 3] = alpha
    label = AnnotationBbox(
        OffsetImage(rgba, zoom=0.046, interpolation="antialiased"),
        (-0.33, 1.14),
        xycoords=ax.transAxes,
        box_alignment=(0.0, 0.5),
        frameon=False,
        pad=0.0,
        annotation_clip=False,
    )
    ax.add_artist(label)


def build_source_data() -> pd.DataFrame:
    raw = pd.read_csv(INPUT)
    order = []
    roles = {}
    colors = {}
    for pair_order, (city_1, city_2) in enumerate(PAIR_ORDER, start=1):
        order.extend([city_1, city_2])
        roles[city_1] = (pair_order, "city_1")
        roles[city_2] = (pair_order, "city_2")
        colors[city_1], colors[city_2] = PAIR_COLORS[(city_1, city_2)]

    out = raw.loc[raw["city_key"].isin(order)].copy()
    out["city_order"] = out["city_key"].map({city: index + 1 for index, city in enumerate(order)})
    out["pair_order"] = out["city_key"].map(lambda city: roles[city][0])
    out["city_role"] = out["city_key"].map(lambda city: roles[city][1])
    out["plot_color"] = out["city_key"].map(colors)
    out = out.sort_values("city_order").reset_index(drop=True)
    keep = [
        "pair_order",
        "city_order",
        "city_role",
        "city_key",
        "City",
        "building_count",
        "pv_positive_buildings",
        "prevalence",
        "prevalence_pct",
        "roof_size_selection",
        "conditional_intensity",
        "conditional_intensity_pct",
        "pv_utilization",
        "pv_utilization_pct",
        "factor_product",
        "factor_identity_error_pp",
        "plot_color",
    ]
    out = out[keep]
    if len(out) != 12:
        raise ValueError(f"Expected 12 primary cities, found {len(out)}")
    return out


def draw(data: pd.DataFrame) -> plt.Figure:
    fig, axes = plt.subplots(1, 3, figsize=(7.25, 5.15), dpi=300, sharey=True)
    fig.patch.set_facecolor("white")
    y = np.arange(len(data), dtype=float)

    for column, (metric, title, ticks, xmax) in enumerate(METRICS):
        ax = axes[column]
        values = data[metric].to_numpy(float)
        ax.set_facecolor("white")
        ax.hlines(y, 0.0, values, color=data["plot_color"], linewidth=2.35, alpha=0.95, zorder=2)
        ax.scatter(
            values,
            y,
            s=34,
            c=data["plot_color"],
            edgecolors="white",
            linewidths=0.75,
            zorder=4,
        )
        for yi, value in zip(y, values):
            label = f"{value:.1f}" if value >= 1 else f"{value:.2f}"
            ax.annotate(
                label,
                (value, yi),
                xytext=(4, 0),
                textcoords="offset points",
                ha="left",
                va="center",
                fontsize=6.5,
                color=TEXT,
                clip_on=False,
            )

        ax.set_xlim(0, xmax)
        ax.set_xticks(ticks)
        ax.set_title(title, fontsize=9.0, color=TEXT, pad=8, fontweight="normal")
        ax.grid(axis="x", linestyle="--", linewidth=0.7, alpha=0.55, color=GRID, zorder=0)
        ax.tick_params(axis="x", labelsize=7.3, colors=TEXT, length=2.5)
        ax.tick_params(axis="y", length=0)
        for spine in ("top", "right", "left"):
            ax.spines[spine].set_visible(False)
        ax.spines["bottom"].set_color(AXIS)
        ax.spines["bottom"].set_linewidth(0.8)
        for boundary in (1.5, 3.5, 5.5, 7.5, 9.5):
            ax.axhline(boundary, color="#e8e2de", linewidth=0.8, zorder=0)

    axes[0].set_yticks(y)
    axes[0].set_yticklabels(data["City"], fontsize=7.5, color=TEXT)
    axes[0].invert_yaxis()
    for label, color in zip(axes[0].get_yticklabels(), data["plot_color"]):
        label.set_color(color)

    fig.text(
        0.55,
        0.975,
        "PV utilization = prevalence × roof selection × conditional intensity",
        ha="center",
        va="top",
        fontsize=8.2,
        color="#544a43",
    )
    add_myriad_panel_label(axes[0])
    fig.subplots_adjust(left=0.175, right=0.972, bottom=0.085, top=0.86, wspace=0.30)
    return fig


def main() -> None:
    data = build_source_data()
    SOURCE_DATA.parent.mkdir(parents=True, exist_ok=True)
    data.to_csv(SOURCE_DATA, index=False)
    OUTDIR.mkdir(parents=True, exist_ok=True)
    fig = draw(data)
    pdf = OUTDIR / "fig3a_primary12_city_anatomy.pdf"
    png = OUTDIR / "fig3a_primary12_city_anatomy.png"
    fig.savefig(pdf, bbox_inches="tight", pad_inches=0.025, facecolor="white")
    fig.savefig(png, dpi=300, bbox_inches="tight", pad_inches=0.025, facecolor="white")
    plt.close(fig)
    print(f"[ok] Wrote {pdf}")
    print(f"[ok] Wrote {png}")
    print(f"[ok] Wrote {SOURCE_DATA}")


if __name__ == "__main__":
    main()

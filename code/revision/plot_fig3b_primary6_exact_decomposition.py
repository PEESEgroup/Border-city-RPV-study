#!/usr/bin/env python3
"""Draft Fig. 3b: exact three-factor pair decomposition in original Fig. 6c style."""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.image as mpimg
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import LinearSegmentedColormap, TwoSlopeNorm
from matplotlib.offsetbox import AnnotationBbox, OffsetImage


ROOT = Path(__file__).resolve().parents[2]
INPUT = ROOT / "evidence/v1_verified_data/pair_prevalence_intensity_decomposition.csv"
OUTDIR = ROOT / "figures/panels/revision"
SOURCE_DATA = ROOT / "Source_Data/csv/Fig_3b.csv"
PANEL_LABEL = ROOT / "figures/assets/revision/fig2_panel_label_b_myriadpro.png"

PAIR_ORDER = [
    "Vienna--Bratislava",
    "Singapore--Johor Bahru",
    "San Diego--Tijuana",
    "El Paso--Juarez",
    "Hong Kong--Shenzhen",
    "Monaco--Nice",
]

PAIR_LABELS = {
    "Vienna--Bratislava": "VIE - BRA",
    "Singapore--Johor Bahru": "SIN - JB",
    "San Diego--Tijuana": "SD - TIJ",
    "El Paso--Juarez": "EP - JUA",
    "Hong Kong--Shenzhen": "HK - SZ",
    "Monaco--Nice": "MON - NIC",
}

COLUMNS = [
    "prevalence_contribution_pp",
    "roof_size_selection_contribution_pp",
    "conditional_intensity_contribution_pp",
    "pv_utilization_gap_pp",
]

COLUMN_LABELS = [
    "Prevalence",
    "Roof\nselection",
    "Conditional\nintensity",
    "Observed\nPV gap",
]

TEXT = "#2f2a27"


def add_myriad_panel_label(ax: plt.Axes) -> None:
    if not PANEL_LABEL.exists():
        ax.text(-0.20, 1.14, "b,", transform=ax.transAxes, ha="left", va="center", fontsize=13)
        return
    rgb = mpimg.imread(PANEL_LABEL)[..., :3]
    luminance = 0.2126 * rgb[..., 0] + 0.7152 * rgb[..., 1] + 0.0722 * rgb[..., 2]
    alpha = np.clip((0.92 - luminance) / 0.72, 0.0, 1.0)
    rgba = np.zeros((*rgb.shape[:2], 4), dtype=float)
    rgba[..., :3] = np.array([34, 34, 34]) / 255.0
    rgba[..., 3] = alpha
    ax.add_artist(
        AnnotationBbox(
            OffsetImage(rgba, zoom=0.046, interpolation="antialiased"),
            (-0.20, 1.14),
            xycoords=ax.transAxes,
            box_alignment=(0.0, 0.5),
            frameon=False,
            pad=0.0,
            annotation_clip=False,
        )
    )


def build_source_data() -> pd.DataFrame:
    raw = pd.read_csv(INPUT)
    out = raw.loc[raw["pair"].isin(PAIR_ORDER)].copy()
    out["pair_order"] = out["pair"].map({pair: i + 1 for i, pair in enumerate(PAIR_ORDER)})
    out["display_pair"] = out["pair"].map(PAIR_LABELS)
    out = out.sort_values("pair_order").reset_index(drop=True)
    if len(out) != 6:
        raise ValueError(f"Expected six primary pairs, found {len(out)}")
    recalculated = out[
        [
            "prevalence_contribution_pp",
            "roof_size_selection_contribution_pp",
            "conditional_intensity_contribution_pp",
        ]
    ].sum(axis=1)
    error = recalculated - out["pv_utilization_gap_pp"]
    if float(error.abs().max()) > 1e-9:
        raise ValueError(f"Exact decomposition failed; maximum error is {error.abs().max():.3g} pp")
    out["recalculated_gap_pp"] = recalculated
    out["recalculated_error_pp"] = error
    first = ["pair_order", "display_pair", "pair", "c1", "c2"]
    remaining = [column for column in out.columns if column not in first]
    return out[first + remaining]


def draw(data: pd.DataFrame) -> plt.Figure:
    matrix = data[COLUMNS].to_numpy(float)
    vmax = max(float(np.nanmax(np.abs(matrix))), 1.0)
    norm = TwoSlopeNorm(vmin=-vmax, vcenter=0.0, vmax=vmax)
    cmap = LinearSegmentedColormap.from_list(
        "city_gap_diverging",
        ["#2f5d8c", "#f7f5f1", "#c97c5d"],
        N=256,
    )

    fig = plt.figure(figsize=(5.35, 3.85), dpi=300)
    fig.patch.set_facecolor("white")
    gs = fig.add_gridspec(nrows=2, ncols=1, height_ratios=[1.0, 0.040], hspace=0.64)
    ax = fig.add_subplot(gs[0, 0])
    cax = fig.add_subplot(gs[1, 0])
    im = ax.imshow(matrix, cmap=cmap, norm=norm, aspect="auto", zorder=1)

    nrows, ncols = matrix.shape
    ax.set_xticks(np.arange(ncols))
    ax.set_xticklabels(COLUMN_LABELS, fontsize=8.4, color="black")
    ax.set_yticks(np.arange(nrows))
    ax.set_yticklabels(data["display_pair"], fontsize=8.5, color="black")
    ax.tick_params(axis="x", length=0, pad=5)
    ax.tick_params(axis="y", length=0)

    ax.set_xticks(np.arange(-0.5, ncols, 1), minor=True)
    ax.set_yticks(np.arange(-0.5, nrows, 1), minor=True)
    ax.grid(which="minor", color="white", linewidth=1.2)
    ax.tick_params(which="minor", bottom=False, left=False)
    ax.axvline(2.5, color="#5e5148", linewidth=1.0, alpha=0.55, zorder=4)

    ax.text(
        1.0,
        1.045,
        "Exact decomposition contributions",
        transform=ax.get_xaxis_transform(),
        ha="center",
        va="bottom",
        fontsize=8.8,
        color="#544a43",
    )
    ax.text(
        3.0,
        1.045,
        "Pairwise difference",
        transform=ax.get_xaxis_transform(),
        ha="center",
        va="bottom",
        fontsize=8.8,
        color="#544a43",
    )

    for i in range(nrows):
        for j in range(ncols):
            value = float(matrix[i, j])
            color = "white" if abs(value) > vmax * 0.55 else TEXT
            ax.text(
                j,
                i,
                f"{value:+.2f}",
                ha="center",
                va="center",
                fontsize=8.0,
                color=color,
                zorder=5,
            )

    for spine in ax.spines.values():
        spine.set_visible(False)
    add_myriad_panel_label(ax)

    cbar = fig.colorbar(im, cax=cax, orientation="horizontal")
    cbar.set_label(
        "Contribution or observed gap (percentage points)\nFirst listed minus second listed city",
        fontsize=8.0,
    )
    cbar.ax.tick_params(labelsize=7.5, length=2.5, colors="black")
    cbar.outline.set_linewidth(0.6)
    fig.subplots_adjust(left=0.20, right=0.975, bottom=0.16, top=0.84)
    return fig


def main() -> None:
    data = build_source_data()
    SOURCE_DATA.parent.mkdir(parents=True, exist_ok=True)
    data.to_csv(SOURCE_DATA, index=False)
    OUTDIR.mkdir(parents=True, exist_ok=True)
    fig = draw(data)
    pdf = OUTDIR / "fig3b_primary6_exact_decomposition.pdf"
    png = OUTDIR / "fig3b_primary6_exact_decomposition.png"
    fig.savefig(pdf, bbox_inches="tight", pad_inches=0.025, facecolor="white")
    fig.savefig(png, dpi=300, bbox_inches="tight", pad_inches=0.025, facecolor="white")
    plt.close(fig)
    print(f"[ok] Wrote {pdf}")
    print(f"[ok] Wrote {png}")
    print(f"[ok] Wrote {SOURCE_DATA}")


if __name__ == "__main__":
    main()

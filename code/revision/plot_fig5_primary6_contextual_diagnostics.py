#!/usr/bin/env python3
"""Build revised Fig. 5 contextual directional diagnostics.

The four-panel layout retains the visual grammar of the original Fig. 3:
return-friction bubble map, four contextual gap scatters, five signed gap bars
and a directional-agreement count matrix. Only the six primary pairs are used.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.image as mpimg
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.lines import Line2D
from matplotlib.offsetbox import AnnotationBbox, DrawingArea
from matplotlib.patches import PathPatch, Rectangle
from matplotlib.path import Path as MplPath

import plot_fig3_primary6_combined as style


ROOT = Path(__file__).resolve().parents[2]
PAIR_INPUT = ROOT / "evidence/v1_verified_data/pair_results_7pairs.csv"
INCOME_INPUT = ROOT / "evidence/v1_verified_data/income_14cities.csv"

OUTDIR = ROOT / "figures/main/revision"
PANEL_OUTDIR = ROOT / "figures/panels/revision"
SOURCE_DIR = ROOT / "Source_Data/csv"
NOTES_DIR = ROOT / "Source_Data/figure_notes"
CHECKS_PATH = ROOT / "Source_Data/source_data_checks_fig5.json"
LOG_PATH = ROOT / "logs/16_fig5_contextual_diagnostics_draft.md"

TEXT = "#222222"
MUTED = "#68615d"
AXIS = "#5c554f"
GRID = "#dfdbd7"
POSITIVE = "#e65353"
NEGATIVE = "#4f79a7"

PAIR_COLORS = {
    "Vienna--Bratislava": "#6c8a3b",
    "Singapore--Johor Bahru": "#d29a2e",
    "San Diego--Tijuana": "#2f7f6f",
    "El Paso--Juarez": "#4f7cac",
    "Hong Kong--Shenzhen": "#b07bac",
    "Monaco--Nice": "#d16d8a",
}
PAIR_LABELS = {
    "Vienna--Bratislava": "VIE–BRA",
    "Singapore--Johor Bahru": "SIN–JB",
    "San Diego--Tijuana": "SD–TIJ",
    "El Paso--Juarez": "EP–JUA",
    "Hong Kong--Shenzhen": "HK–SZ",
    "Monaco--Nice": "MON–NIC",
}
PAIR_DISPLAY = {key: key.replace("--", " – ") for key in PAIR_COLORS}
PAIR_ORDER = list(PAIR_COLORS)

PANEL_HEIGHT_PT = 9.49
PANEL_LABEL_POSITIONS = {
    "a": (0.008, 0.955),
    "b": (0.505, 0.955),
    "c": (0.008, 0.450),
    "d": (0.650, 0.450),
}


def _load_glyph_rgb(label: str) -> np.ndarray:
    rgb = mpimg.imread(style.PANEL_GLYPHS[label])[..., :3]
    if label != "d":
        return rgb
    comma_source = mpimg.imread(style.PANEL_GLYPHS["c"])[..., :3]
    repaired = np.ones_like(rgb)
    baseline_shift = 18
    letter_cutoff = 76
    repaired[: rgb.shape[0] - baseline_shift, :letter_cutoff] = rgb[
        baseline_shift:, :letter_cutoff
    ]
    comma_crop = comma_source[121:159, 86:109]
    from PIL import Image

    comma_image = Image.fromarray(np.uint8(np.clip(comma_crop, 0.0, 1.0) * 255.0))
    comma_image = comma_image.resize((19, 30), Image.Resampling.LANCZOS)
    comma_crop = np.asarray(comma_image, dtype=float) / 255.0
    repaired[125:155, 78:97] = np.minimum(repaired[125:155, 78:97], comma_crop)
    return repaired


@lru_cache(maxsize=None)
def vector_panel_glyph(label: str) -> tuple[MplPath, float]:
    """Trace the retained Myriad Pro reference label into a vector path."""
    rgb = _load_glyph_rgb(label)
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
    xmin, xmax = float(vertices[finite, 0].min()), float(vertices[finite, 0].max())
    ymin, ymax = float(vertices[finite, 1].min()), float(vertices[finite, 1].max())
    glyph_height = ymax - ymin
    normalized = vertices.copy()
    normalized[:, 0] = (vertices[:, 0] - xmin) / glyph_height
    normalized[:, 1] = (ymax - vertices[:, 1]) / glyph_height
    return MplPath(normalized, compound.codes), (xmax - xmin) / glyph_height


def add_figure_panel_label(fig: plt.Figure, label: str, xy: tuple[float, float]) -> None:
    glyph_path, aspect = vector_panel_glyph(label)
    height = PANEL_HEIGHT_PT
    width = height * aspect
    vertices = glyph_path.vertices.copy()
    vertices[:, 0] *= height
    vertices[:, 1] *= height
    drawing = DrawingArea(width, height, 0, 0, clip=False)
    drawing.add_artist(
        PathPatch(
            MplPath(vertices, glyph_path.codes),
            facecolor=TEXT,
            edgecolor="none",
            linewidth=0,
        )
    )
    fig.add_artist(
        AnnotationBbox(
            drawing,
            xy,
            xycoords=fig.transFigure,
            box_alignment=(0.0, 1.0),
            frameon=False,
            pad=0.0,
            annotation_clip=False,
        )
    )


def load_primary_pairs() -> pd.DataFrame:
    pairs = pd.read_csv(PAIR_INPUT)
    pairs = pairs.loc[pairs["pair"].isin(PAIR_ORDER)].copy()
    pairs["pair"] = pd.Categorical(pairs["pair"], PAIR_ORDER, ordered=True)
    pairs = pairs.sort_values("pair").reset_index(drop=True)

    income = pd.read_csv(INCOME_INPUT).set_index("city_key")
    gdp = []
    for row in pairs.itertuples(index=False):
        c1 = str(row.c1).lower().replace(" ", "")
        c2 = str(row.c2).lower().replace(" ", "")
        v1 = float(income.at[c1, "GDP per Capita PPP USD (2024)"])
        v2 = float(income.at[c2, "GDP per Capita PPP USD (2024)"])
        gdp.append(v1 - v2)
    pairs["gdp_gap_c1_minus_c2_usd"] = gdp
    pairs["pair_color"] = pairs["pair"].astype(str).map(PAIR_COLORS)
    pairs["pair_short"] = pairs["pair"].astype(str).map(PAIR_LABELS)
    return pairs


def marker_sizes(values: pd.Series | np.ndarray) -> np.ndarray:
    arr = np.abs(np.asarray(values, dtype=float))
    max_value = max(float(arr.max()), 1e-9)
    return 45.0 + 650.0 * arr / max_value


def marker_size_for_value(value: float, max_value: float) -> float:
    return 45.0 + 650.0 * abs(value) / max(max_value, 1e-9)


def style_plain_axis(ax: plt.Axes, grid_axis: str = "both") -> None:
    ax.spines[["top", "right"]].set_visible(False)
    ax.spines[["left", "bottom"]].set_color(AXIS)
    ax.spines[["left", "bottom"]].set_linewidth(0.65)
    ax.tick_params(labelsize=6.5, width=0.55, length=2.5, colors=TEXT)
    ax.grid(True, axis=grid_axis, color=GRID, lw=0.45, ls=":", zorder=0)


def draw_panel_a(ax: plt.Axes, pairs: pd.DataFrame) -> pd.DataFrame:
    x = pairs["total_friction_advantage_c1"].to_numpy(float)
    y = pairs["irr_gap_c1_minus_c2_pp"].to_numpy(float)
    pv_gap = pairs["all_pv_gap_c1_minus_c2_pp"].to_numpy(float)
    sizes = marker_sizes(pv_gap)

    xlim = (-4.3, 12.6)
    ylim = (-11.8, 16.5)
    ax.set_xlim(*xlim)
    ax.set_ylim(*ylim)
    ax.add_patch(Rectangle((xlim[0], ylim[0]), -xlim[0], -ylim[0], color="#ecebea", zorder=-4))
    ax.add_patch(Rectangle((0, ylim[0]), xlim[1], -ylim[0], color="#dedddb", zorder=-4))
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.set_xticks([])
    ax.set_yticks([])
    ax.axhline(0, color="#111111", lw=0.8, zorder=1)
    ax.axvline(0, color="#111111", lw=0.8, zorder=1)
    ax.annotate("", (xlim[1], 0), (xlim[1] - 0.7, 0), arrowprops=dict(arrowstyle="->", lw=0.8, color="#111111"))
    ax.annotate("", (0, ylim[1]), (0, ylim[1] - 1.3), arrowprops=dict(arrowstyle="->", lw=0.8, color="#111111"))
    ax.text(xlim[1] - 0.35, 0.7, "Lower total friction\nin city 1", ha="right", va="bottom", fontsize=7.0, color=TEXT)
    ax.text(0.22, ylim[1] - 0.35, "Higher standardized IRR\nin city 1", ha="left", va="top", fontsize=7.0, color=TEXT)

    for idx, row in pairs.iterrows():
        ax.scatter(
            x[idx], y[idx], s=sizes[idx], color=row["pair_color"], alpha=0.80,
            edgecolor="#2f2f2f", linewidth=0.55, zorder=4,
        )

    offsets = {
        "Vienna--Bratislava": (0.65, -0.35, "left", "top"),
        "Singapore--Johor Bahru": (-0.75, -1.65, "right", "top"),
        "San Diego--Tijuana": (0.70, 1.00, "left", "bottom"),
        "El Paso--Juarez": (0.65, 0.95, "left", "bottom"),
        "Hong Kong--Shenzhen": (0.65, -0.95, "left", "top"),
        "Monaco--Nice": (0.65, -0.65, "left", "top"),
    }
    for idx, row in pairs.iterrows():
        pair = str(row["pair"])
        dx, dy, ha, va = offsets[pair]
        gap = float(row["all_pv_gap_c1_minus_c2_pp"])
        decimals = 2 if abs(gap) < 0.1 else 1
        ax.text(
            x[idx] + dx,
            y[idx] + dy,
            f"{row['pair_short']} | {gap:+.{decimals}f} pp",
            fontsize=6.7,
            ha=ha,
            va=va,
            color=TEXT,
            zorder=6,
        )

    # A custom legend keeps circles separated, directly addressing the original overlap.
    legend_values = [0.5, 2.0, 6.0]
    legend_y = [11.1, 7.5, 3.3]
    legend_x = -3.45
    ax.text(-4.05, 13.75, "|PV-utilization gap|", fontsize=6.7, color=TEXT, ha="left", va="top")
    max_gap = float(np.abs(pv_gap).max())
    for val, y0 in zip(legend_values, legend_y):
        ax.scatter(
            legend_x, y0, s=marker_size_for_value(val, max_gap), color="#bdbdbd",
            alpha=0.65, edgecolor="#555555", linewidth=0.45, zorder=5,
        )
        ax.text(-2.55, y0, f"{val:.1f} pp", fontsize=6.4, color=TEXT, ha="left", va="center")

    export = pairs[
        [
            "pair", "c1", "c2", "all_pv_gap_c1_minus_c2_pp",
            "irr_gap_c1_minus_c2_pp", "total_friction_advantage_c1",
            "pair_color", "pair_short",
        ]
    ].copy()
    export["bubble_size_points2"] = sizes
    return export


def draw_panel_b(fig: plt.Figure, pairs: pd.DataFrame) -> tuple[list[plt.Axes], pd.DataFrame]:
    positions = [
        [0.560, 0.765, 0.183, 0.190],
        [0.765, 0.765, 0.183, 0.190],
        [0.560, 0.580, 0.183, 0.125],
        [0.765, 0.580, 0.183, 0.125],
    ]
    specs = [
        ("income_gap_c1_minus_c2_usd", "Annual income gap (US$ thousands)", 1000.0),
        ("gdp_gap_c1_minus_c2_usd", "GDP per capita PPP gap (US$ thousands)", 1000.0),
        ("irr_gap_c1_minus_c2_pp", "Standardized IRR gap (pp)", 1.0),
        ("total_friction_advantage_c1", "Total-friction advantage (score points)", 1.0),
    ]
    axes: list[plt.Axes] = []
    rows: list[dict[str, object]] = []
    y = pairs["all_pv_gap_c1_minus_c2_pp"].to_numpy(float)
    for panel_index, (pos, (column, xlabel, divisor)) in enumerate(zip(positions, specs)):
        ax = fig.add_axes(pos)
        axes.append(ax)
        x = pairs[column].to_numpy(float) / divisor
        for idx, row in pairs.iterrows():
            ax.scatter(
                x[idx], y[idx], s=52, color=row["pair_color"], alpha=0.82,
                edgecolor="#3a3a3a", linewidth=0.45, zorder=3,
            )
            rows.append(
                {
                    "pair": str(row["pair"]),
                    "indicator": column,
                    "indicator_value": float(x[idx]),
                    "indicator_unit_divisor": divisor,
                    "all_pv_gap_pp": float(y[idx]),
                }
            )
        style_plain_axis(ax)
        ax.axhline(0, color="#b5b0ac", lw=0.5, zorder=1)
        ax.set_xlabel(xlabel, fontsize=5.7, color=TEXT, labelpad=1.1)
        ax.set_ylim(-1.65, 6.55)
        ax.set_yticks([-1, 0, 2, 4, 6])
        if panel_index % 2 == 0:
            ax.set_ylabel("All-building PV gap (pp)", fontsize=5.8, color=TEXT, labelpad=1.5)
        else:
            ax.set_yticklabels([])
        if column in {"income_gap_c1_minus_c2_usd", "gdp_gap_c1_minus_c2_usd"}:
            lo, hi = float(x.min()), float(x.max())
            pad = max((hi - lo) * 0.16, 4.0)
            ax.set_xlim(min(0.0, lo) - pad, hi + pad)
        else:
            lo, hi = float(x.min()), float(x.max())
            pad = max((hi - lo) * 0.13, 0.8)
            ax.set_xlim(lo - pad, hi + pad)
    return axes, pd.DataFrame(rows)


def draw_pair_legend(fig: plt.Figure) -> None:
    handles = [
        Line2D([0], [0], marker="o", linestyle="none", markersize=5.2,
               markerfacecolor=PAIR_COLORS[pair], markeredgecolor="#333333", markeredgewidth=0.45,
               label=PAIR_DISPLAY[pair])
        for pair in PAIR_ORDER
    ]
    fig.legend(
        handles=handles,
        loc="center",
        bbox_to_anchor=(0.505, 0.505),
        ncol=6,
        frameon=False,
        fontsize=5.0,
        handletextpad=0.35,
        columnspacing=0.45,
        borderaxespad=0,
    )


def draw_panel_c(fig: plt.Figure, pairs: pd.DataFrame) -> tuple[list[plt.Axes], pd.DataFrame]:
    specs = [
        ("irr_gap_c1_minus_c2_pp", "Standardized\nIRR gap", "pp"),
        ("administrative_friction_advantage_c1", "Administrative\nfriction advantage", "score"),
        ("revenue_friction_advantage_c1", "Revenue\nfriction advantage", "score"),
        ("residential_pv_gap_c1_minus_c2_pp", "Residential\nPV gap", "pp"),
        ("nonresidential_pv_gap_c1_minus_c2_pp", "Non-residential\nPV gap", "pp"),
    ]
    x0, y0, total_w, h, gap = 0.132, 0.125, 0.495, 0.325, 0.009
    width = (total_w - 4 * gap) / 5
    y = np.arange(len(pairs))[::-1]
    axes: list[plt.Axes] = []
    rows: list[dict[str, object]] = []
    for panel_index, (column, xlabel, unit) in enumerate(specs):
        ax = fig.add_axes([x0 + panel_index * (width + gap), y0, width, h])
        axes.append(ax)
        values = pairs[column].to_numpy(float)
        colors = [POSITIVE if value >= 0 else NEGATIVE for value in values]
        ax.barh(y, values, height=0.62, color=colors, edgecolor="none", zorder=2)
        ax.axvline(0, color="#7d7772", lw=0.55, zorder=3)
        max_abs = max(float(np.max(np.abs(values))), 0.5)
        ax.set_xlim(-1.42 * max_abs, 1.42 * max_abs)
        ax.set_ylim(-0.65, len(pairs) - 0.35)
        ax.set_xlabel(xlabel, fontsize=5.55, color=TEXT, labelpad=1.6, linespacing=0.92)
        ax.tick_params(axis="x", labelsize=5.25, width=0.45, length=2.0, colors=TEXT, pad=1)
        ax.grid(axis="x", color=GRID, lw=0.45, zorder=0)
        for spine in ax.spines.values():
            spine.set_visible(False)
        if panel_index == 0:
            ax.set_yticks(y)
            ax.set_yticklabels([PAIR_DISPLAY[p] for p in PAIR_ORDER], fontsize=5.45, color=TEXT)
            ax.tick_params(axis="y", length=0, pad=2)
        else:
            ax.set_yticks(y)
            ax.set_yticklabels([])
            ax.tick_params(axis="y", length=0)
        for row_index, value in enumerate(values):
            ypos = y[row_index]
            if abs(value) >= 0.55 * max_abs:
                xpos = value - np.sign(value) * 0.055 * max_abs
                ha = "right" if value > 0 else "left"
                color = "white"
            else:
                offset = 0.060 * max_abs
                xpos = value + (offset if value >= 0 else -offset)
                ha = "left" if value >= 0 else "right"
                color = TEXT
            ax.text(xpos, ypos, f"{value:.2f}", ha=ha, va="center", fontsize=5.3, color=color)
            rows.append(
                {
                    "pair": str(pairs.iloc[row_index]["pair"]),
                    "metric": column,
                    "value": float(value),
                    "unit": unit,
                }
            )
    return axes, pd.DataFrame(rows)


def sign_match(indicator: np.ndarray, outcome: np.ndarray) -> tuple[int, int]:
    indicator = np.asarray(indicator, dtype=float)
    outcome = np.asarray(outcome, dtype=float)
    valid = np.isfinite(indicator) & np.isfinite(outcome) & (~np.isclose(indicator, 0.0)) & (~np.isclose(outcome, 0.0))
    matched = int(np.sum(np.sign(indicator[valid]) == np.sign(outcome[valid])))
    return matched, int(valid.sum())


def directional_agreement(pairs: pd.DataFrame) -> pd.DataFrame:
    indicators = [
        ("Income", "income_gap_c1_minus_c2_usd"),
        ("GDP per capita PPP", "gdp_gap_c1_minus_c2_usd"),
        ("Standardized IRR", "irr_gap_c1_minus_c2_pp"),
        ("Administrative friction", "administrative_friction_advantage_c1"),
        ("Revenue friction", "revenue_friction_advantage_c1"),
    ]
    outcomes = [
        ("All-building PV", "all_pv_gap_c1_minus_c2_pp"),
        ("Residential PV", "residential_pv_gap_c1_minus_c2_pp"),
        ("Non-residential PV", "nonresidential_pv_gap_c1_minus_c2_pp"),
    ]
    rows = []
    for indicator_label, indicator_col in indicators:
        for outcome_label, outcome_col in outcomes:
            matched, valid = sign_match(pairs[indicator_col], pairs[outcome_col])
            rows.append(
                {
                    "indicator": indicator_label,
                    "outcome": outcome_label,
                    "matched_pairs": matched,
                    "valid_pairs": valid,
                    "match_fraction": matched / valid if valid else np.nan,
                }
            )
    return pd.DataFrame(rows)


def draw_panel_d(fig: plt.Figure, agreement: pd.DataFrame) -> tuple[plt.Axes, plt.Axes]:
    ax = fig.add_axes([0.758, 0.0962, 0.190, 0.3538])
    cax = fig.add_axes([0.955, 0.1162, 0.009, 0.3088])
    indicators = ["Income", "GDP per capita PPP", "Standardized IRR", "Administrative friction", "Revenue friction"]
    outcomes = ["All-building PV", "Residential PV", "Non-residential PV"]
    matrix = np.zeros((len(indicators), len(outcomes)))
    denoms = np.zeros_like(matrix, dtype=int)
    for i, indicator in enumerate(indicators):
        for j, outcome in enumerate(outcomes):
            row = agreement.loc[(agreement["indicator"] == indicator) & (agreement["outcome"] == outcome)].iloc[0]
            matrix[i, j] = int(row["matched_pairs"])
            denoms[i, j] = int(row["valid_pairs"])
    cmap = plt.get_cmap("GnBu").copy()
    image = ax.imshow(matrix, cmap=cmap, vmin=0, vmax=6, aspect="auto")
    ax.set_xticks(np.arange(len(outcomes)))
    ax.set_xticklabels(["All-building PV", "Res. PV", "Non-res. PV"], fontsize=5.55, color=TEXT)
    ax.set_yticks(np.arange(len(indicators)))
    ax.set_yticklabels(
        ["Income", "GDP per capita PPP", "IRR", "Admin friction", "Revenue friction"],
        rotation=-30,
        ha="right",
        va="center",
        rotation_mode="anchor",
        fontsize=5.45,
        color=TEXT,
    )
    ax.tick_params(axis="both", which="major", width=0.45, length=2.0)
    ax.tick_params(axis="x", which="major", pad=2)
    ax.tick_params(axis="y", which="major", pad=2)
    for i in range(matrix.shape[0]):
        for j in range(matrix.shape[1]):
            color = "white" if matrix[i, j] >= 4 else "#111111"
            ax.text(j, i, f"{int(matrix[i, j])}/{denoms[i, j]}", ha="center", va="center", fontsize=5.9, color=color)
    ax.set_xticks(np.arange(-0.5, len(outcomes), 1), minor=True)
    ax.set_yticks(np.arange(-0.5, len(indicators), 1), minor=True)
    ax.grid(which="minor", color="#dddddd", linewidth=0.45)
    ax.tick_params(which="minor", bottom=False, left=False)
    for spine in ax.spines.values():
        spine.set_visible(False)
    colorbar = fig.colorbar(image, cax=cax, ticks=np.arange(0, 7, 1))
    colorbar.ax.tick_params(labelsize=5.5, width=0.45, length=2)
    colorbar.outline.set_linewidth(0.45)
    colorbar.set_label("Matched pairs", fontsize=5.7, color=TEXT, labelpad=1.5)
    return ax, cax


def build_combined_figure(pairs: pd.DataFrame) -> tuple[plt.Figure, dict[str, pd.DataFrame]]:
    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "font.size": 7.0,
            "axes.linewidth": 0.65,
            "xtick.color": TEXT,
            "ytick.color": TEXT,
            "axes.labelcolor": TEXT,
            "text.color": TEXT,
        }
    )
    fig = plt.figure(figsize=(8.45, 5.10), dpi=300, facecolor="white")
    ax_a = fig.add_axes([0.055, 0.535, 0.430, 0.420])
    panel_a = draw_panel_a(ax_a, pairs)
    _, panel_b = draw_panel_b(fig, pairs)
    draw_pair_legend(fig)
    _, panel_c = draw_panel_c(fig, pairs)
    panel_d = directional_agreement(pairs)
    draw_panel_d(fig, panel_d)
    for label, xy in PANEL_LABEL_POSITIONS.items():
        add_figure_panel_label(fig, label, xy)
    return fig, {"a": panel_a, "b": panel_b, "c": panel_c, "d": panel_d}


def save_outputs(fig: plt.Figure, panels: dict[str, pd.DataFrame]) -> None:
    OUTDIR.mkdir(parents=True, exist_ok=True)
    PANEL_OUTDIR.mkdir(parents=True, exist_ok=True)
    SOURCE_DIR.mkdir(parents=True, exist_ok=True)
    NOTES_DIR.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUTDIR / "fig_5.pdf", bbox_inches="tight", pad_inches=0.025)
    fig.savefig(OUTDIR / "fig_5.png", dpi=300, bbox_inches="tight", pad_inches=0.025)

    # Panel-level vector and preview files are clipped from the same vector canvas.
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    panel_boxes = {
        "a": matplotlib.transforms.Bbox.from_extents(0.010, 0.505, 0.495, 0.970),
        "b": matplotlib.transforms.Bbox.from_extents(0.495, 0.505, 0.970, 0.970),
        "c": matplotlib.transforms.Bbox.from_extents(0.005, 0.050, 0.635, 0.470),
        "d": matplotlib.transforms.Bbox.from_extents(0.625, 0.050, 0.975, 0.470),
    }
    for label, box in panel_boxes.items():
        bbox_inches = matplotlib.transforms.TransformedBbox(box, fig.transFigure).transformed(fig.dpi_scale_trans.inverted())
        fig.savefig(PANEL_OUTDIR / f"fig5{label}_primary6_contextual_diagnostics.pdf", bbox_inches=bbox_inches, pad_inches=0.01)
        fig.savefig(PANEL_OUTDIR / f"fig5{label}_primary6_contextual_diagnostics.png", dpi=300, bbox_inches=bbox_inches, pad_inches=0.01)
        panels[label].to_csv(SOURCE_DIR / f"Fig_5{label}.csv", index=False)

    combined = []
    for label, table in panels.items():
        item = table.copy()
        item.insert(0, "panel", label)
        combined.append(item)
    pd.concat(combined, ignore_index=True, sort=False).to_csv(SOURCE_DIR / "Fig_5.csv", index=False)


def write_checks(pairs: pd.DataFrame, agreement: pd.DataFrame) -> None:
    def count(indicator: str, outcome: str = "All-building PV") -> str:
        row = agreement.loc[(agreement["indicator"] == indicator) & (agreement["outcome"] == outcome)].iloc[0]
        return f"{int(row['matched_pairs'])}/{int(row['valid_pairs'])}"

    checks = {
        "primary_pair_count": int(len(pairs)),
        "detroit_or_windsor_present": bool(pairs[["c1", "c2"]].isin(["Detroit", "Windsor"]).any().any()),
        "all_building_alignment": {
            "income": count("Income"),
            "standardized_irr": count("Standardized IRR"),
            "total_policy_friction": sign_match(
                pairs["total_friction_advantage_c1"], pairs["all_pv_gap_c1_minus_c2_pp"]
            ),
            "administrative_friction": count("Administrative friction"),
            "revenue_friction": count("Revenue friction"),
        },
        "san_diego_tijuana": pairs.loc[
            pairs["pair"].astype(str) == "San Diego--Tijuana",
            [
                "all_pv_gap_c1_minus_c2_pp",
                "residential_pv_gap_c1_minus_c2_pp",
                "nonresidential_pv_gap_c1_minus_c2_pp",
            ],
        ].iloc[0].to_dict(),
        "panel_labels": ["a,", "b,", "c,", "d,"],
        "bubble_legend_layout": "custom vertically separated circles",
        "exclusive_pair_shading_present": False,
    }
    matched, valid = checks["all_building_alignment"]["total_policy_friction"]
    checks["all_building_alignment"]["total_policy_friction"] = f"{matched}/{valid}"
    CHECKS_PATH.write_text(json.dumps(checks, indent=2), encoding="utf-8")


def write_notes() -> None:
    (NOTES_DIR / "Fig_5_notes.md").write_text(
        """# Source Data notes for Fig. 5

Fig. 5 contains only the six primary border-city pairs. Detroit and Windsor are excluded and remain a supplementary sensitivity case.

All signed gaps use the fixed first-listed city minus second-listed city order. Positive friction advantage means that the first-listed city has the lower documented-friction score. IRR and PV-utilization gaps are positive when the first-listed city has the higher value.

Panel a bubble area represents the absolute all-building PV-utilization gap. The legend circles use the same area scale and are placed at separate vertical positions to avoid the overlap identified in review.

Panels a to d are directional contextual diagnostics. They do not identify causal mechanisms or establish that IRR has general explanatory power. IRR and revenue-friction indicators partly share electricity-tariff and export-compensation inputs.

Panel d excludes zero-valued indicator or outcome gaps from the valid denominator. This produces a five-pair valid denominator for administrative-friction comparisons because El Paso and Juarez are tied on administrative friction.
""",
        encoding="utf-8",
    )


def write_log() -> None:
    LOG_PATH.write_text(
        """# Fig. 5 contextual diagnostics draft

Date: 2026-08-20

Status: four-panel visual draft generated for author review.

- Retains the original Fig. 3 two-row, four-panel logic.
- Uses only six primary pairs.
- Panel a retains the return-friction quadrant and bubble grammar with separated bubble-legend circles.
- Panel b retains four small contextual scatter plots without fitted lines.
- Panel c retains five signed metric bars and removes all mutually exclusive pair-group shading.
- Panel d reports matched over valid pairs and excludes ties from valid denominators.
- San Diego--Tijuana gaps use the boundary-audited values: 1.966 pp all-building, 2.433 pp residential and 1.247 pp non-residential.
- All-building directional counts reproduce 6/6 for standardized IRR, 4/6 for total documented-policy friction and 3/6 for income.
- Panel labels are traced as vector Myriad Pro glyphs and use one common visible height.
""",
        encoding="utf-8",
    )


def main() -> None:
    pairs = load_primary_pairs()
    fig, panels = build_combined_figure(pairs)
    save_outputs(fig, panels)
    plt.close(fig)
    write_checks(pairs, panels["d"])
    write_notes()
    write_log()
    print(f"Wrote {OUTDIR / 'fig_5.pdf'}")


if __name__ == "__main__":
    main()

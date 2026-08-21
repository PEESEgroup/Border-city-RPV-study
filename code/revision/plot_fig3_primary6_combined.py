#!/usr/bin/env python3
"""Build revised Fig. 3 as one four-panel figure.

Panel a shows the three city-level factors underlying PV utilization.
Panel b migrates the original Fig. 6a roof-size profiles.
Panel c shows the exact pairwise decomposition.
Panel d migrates the original Fig. 6c building-use prevalence heatmap while
removing the policy diagnostic strips.
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.image as mpimg
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.collections import LineCollection
from matplotlib.colors import LinearSegmentedColormap, TwoSlopeNorm, to_rgba
from matplotlib.lines import Line2D
from matplotlib.offsetbox import AnnotationBbox, OffsetImage
from matplotlib.patches import Patch, Rectangle
from PIL import Image

plt.rcParams["hatch.linewidth"] = 0.85


ROOT = Path(__file__).resolve().parents[2]
ANATOMY_INPUT = ROOT / "evidence/v1_verified_data/prevalence_intensity_14cities.csv"
DECOMPOSITION_INPUT = ROOT / "evidence/v1_verified_data/pair_prevalence_intensity_decomposition.csv"
ROOFSIZE_INPUT = ROOT / "evidence/v1_verified_data/roofsize_14cities.csv"
BUILDING_CLASS_INPUT = ROOT / "evidence/v1_verified_data/building_class_14cities.csv"
LOW_COUNT_INPUT = ROOT / "evidence/v1_verified_tables/table_s2_roofsize_building_class_full_values.csv"
LABEL_COMPLETENESS_INPUT = ROOT / "evidence/v1_verified_tables/table_s_building_use_label_completeness.csv"

OUTDIR = ROOT / "figures/main/revision"
PANEL_OUTDIR = ROOT / "figures/panels/revision"
SOURCE_DIR = ROOT / "Source_Data/csv"
CHECKS = ROOT / "Source_Data/source_data_checks_fig3.json"

PANEL_GLYPHS = {
    "a": ROOT / "figures/assets/revision/fig2_panel_label_a_myriadpro.png",
    "b": ROOT / "figures/assets/revision/fig2_panel_label_b_myriadpro.png",
    "c": ROOT / "figures/assets/revision/fig3_panel_label_c_myriadpro.png",
    "d": ROOT / "figures/assets/revision/fig3_panel_label_d_myriadpro.png",
}
PANEL_LABEL_BOX_POINTS = {
    "a": 26.92,
    "b": 26.92,
    "c": 19.13,
    "d": 24.45,
}

PAIR_ORDER = [
    ("vienna", "bratislava"),
    ("singapore", "johorbahru"),
    ("sandiego", "tijuana"),
    ("elpaso", "juarez"),
    ("hongkong", "shenzhen"),
    ("monaco", "nice"),
]

PAIR_NAMES = {
    ("vienna", "bratislava"): "Vienna--Bratislava",
    ("singapore", "johorbahru"): "Singapore--Johor Bahru",
    ("sandiego", "tijuana"): "San Diego--Tijuana",
    ("elpaso", "juarez"): "El Paso--Juarez",
    ("hongkong", "shenzhen"): "Hong Kong--Shenzhen",
    ("monaco", "nice"): "Monaco--Nice",
}

PAIR_SHORT = {
    ("vienna", "bratislava"): "VIE - BRA",
    ("singapore", "johorbahru"): "SIN - JB",
    ("sandiego", "tijuana"): "SD - TIJ",
    ("elpaso", "juarez"): "EP - JUA",
    ("hongkong", "shenzhen"): "HK - SZ",
    ("monaco", "nice"): "MON - NIC",
}

SHOW_NAME = {
    "vienna": "Vienna",
    "bratislava": "Bratislava",
    "singapore": "Singapore",
    "johorbahru": "Johor Bahru",
    "sandiego": "San Diego",
    "tijuana": "Tijuana",
    "elpaso": "El Paso",
    "juarez": "Juarez",
    "hongkong": "Hong Kong",
    "shenzhen": "Shenzhen",
    "monaco": "Monaco",
    "nice": "Nice",
}

PAIR_COLORS = {
    ("vienna", "bratislava"): ("#c97c5d", "#8c4f3f"),
    ("singapore", "johorbahru"): ("#d9a441", "#9a6a12"),
    ("sandiego", "tijuana"): ("#5aa469", "#2f6b3b"),
    ("elpaso", "juarez"): ("#4f7cac", "#1f4e79"),
    ("hongkong", "shenzhen"): ("#b07bac", "#7f4f7c"),
    ("monaco", "nice"): ("#d16d8a", "#8f3458"),
}

CLASS_ORDER = [
    "single-residential",
    "multi-residential",
    "commercial",
    "industrial",
    "public & infrastructure",
    "others",
]

CLASS_LABELS = ["Single-res", "Multi-res", "Commercial", "Industrial", "Public/Infra", "Others"]
ANATOMY_METRICS = [
    ("prevalence_pct", "PV-positive-building\nprevalence (%)", [0, 5, 10, 15], 16.2),
    ("roof_size_selection", "Roof selection\nratio", [0, 4, 8, 12], 12.8),
    ("conditional_intensity_pct", "Conditional PV-area\nintensity (%)", [0, 10, 20, 30], 32.5),
]
ANATOMY_PATTERNS = ["||||", "////", None]

DECOMPOSITION_COLUMNS = [
    "prevalence_contribution_pp",
    "roof_size_selection_contribution_pp",
    "conditional_intensity_contribution_pp",
    "pv_utilization_gap_pp",
]

DECOMPOSITION_LABELS = ["Prevalence", "Roof\nselection", "Conditional\nintensity", "Observed\nPV gap"]
TEXT = "#2f2a27"
MUTED = "#5b514a"
AXIS = "#6e6259"
GRID = "#d8d0ca"
DIVERGING_COLORS = ["#2f5d8c", "#f7f5f1", "#c97c5d"]
LOW_COUNT_THRESHOLD = 50
LABEL_COMPLETENESS_THRESHOLD = 40.0
ORIGINAL_FIG6A_ASPECT = 549.206 / 331.920
ORIGINAL_FIG6A_PDF_WIDTH_IN = 331.920 / 72.0
ORIGINAL_FIG6A_PDF_HEIGHT_IN = 549.206 / 72.0
ORIGINAL_FIG6A_CANVAS_WIDTH_IN = 4.9
ORIGINAL_FIG6A_CANVAS_HEIGHT_IN = 1.32 * len(PAIR_ORDER)
ORIGINAL_FIG6A_SCRIPT = ROOT / "code/original/plot_fig6a_roofsize_utilization_share.py"


def load_original_fig6a_module():
    """Load the original Fig. 6a drawing functions without altering them."""
    spec = importlib.util.spec_from_file_location("original_fig6a_plot", ORIGINAL_FIG6A_SCRIPT)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load original Fig. 6a script: {ORIGINAL_FIG6A_SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


ORIGINAL_FIG6A = load_original_fig6a_module()


def add_panel_label(
    ax: plt.Axes,
    label: str,
    xy: tuple[float, float],
    target_box_points: float | None = None,
) -> None:
    if target_box_points is None:
        target_box_points = PANEL_LABEL_BOX_POINTS[label]
    path = PANEL_GLYPHS[label]
    if not path.exists():
        ax.text(*xy, f"{label},", transform=ax.transAxes, fontsize=12.5, ha="left", va="center")
        return
    rgb = mpimg.imread(path)[..., :3]
    if label == "d":
        # The extracted d, asset ended at the text baseline and clipped the
        # comma descender. Rebuild it in memory with the complete comma from
        # the matching c, Myriad Pro asset while retaining the original d.
        comma_source = mpimg.imread(PANEL_GLYPHS["c"])[..., :3]
        repaired = np.ones_like(rgb)
        baseline_shift = 18
        letter_cutoff = 76
        repaired[: rgb.shape[0] - baseline_shift, :letter_cutoff] = rgb[
            baseline_shift:, :letter_cutoff
        ]
        comma_crop = comma_source[121:159, 86:109]
        comma_image = Image.fromarray(np.uint8(np.clip(comma_crop, 0.0, 1.0) * 255.0))
        comma_image = comma_image.resize((19, 30), Image.Resampling.LANCZOS)
        comma_crop = np.asarray(comma_image, dtype=float) / 255.0
        comma_x = 78
        comma_y = 125
        repaired[comma_y : comma_y + 30, comma_x : comma_x + 19] = np.minimum(
            repaired[comma_y : comma_y + 30, comma_x : comma_x + 19],
            comma_crop,
        )
        rgb = repaired
    luminance = 0.2126 * rgb[..., 0] + 0.7152 * rgb[..., 1] + 0.0722 * rgb[..., 2]
    alpha = np.clip((0.92 - luminance) / 0.72, 0.0, 1.0)
    rgba = np.zeros((*rgb.shape[:2], 4), dtype=float)
    rgba[..., :3] = np.array([34, 34, 34]) / 255.0
    rgba[..., 3] = alpha
    zoom = target_box_points / float(rgba.shape[0])
    ax.add_artist(
        AnnotationBbox(
            OffsetImage(rgba, zoom=zoom, interpolation="antialiased"),
            xy,
            xycoords=ax.transAxes,
            box_alignment=(0.0, 0.5),
            frameon=False,
            pad=0.0,
            annotation_clip=False,
        )
    )


def build_anatomy_data() -> pd.DataFrame:
    raw = pd.read_csv(ANATOMY_INPUT)
    order = [city for pair in PAIR_ORDER for city in pair]
    pair_lookup = {city: i + 1 for i, pair in enumerate(PAIR_ORDER) for city in pair}
    role_lookup = {pair[0]: "city_1" for pair in PAIR_ORDER} | {pair[1]: "city_2" for pair in PAIR_ORDER}
    color_lookup = {
        city: color
        for pair in PAIR_ORDER
        for city, color in zip(pair, PAIR_COLORS[pair])
    }
    out = raw.loc[raw["city_key"].isin(order)].copy()
    out["city_order"] = out["city_key"].map({city: i + 1 for i, city in enumerate(order)})
    out["pair_order"] = out["city_key"].map(pair_lookup)
    out["city_role"] = out["city_key"].map(role_lookup)
    out["plot_color"] = out["city_key"].map(color_lookup)
    for metric, _, _, xmax in ANATOMY_METRICS:
        out[f"{metric}_bar_fraction"] = out[metric] / xmax
    out = out.sort_values("city_order").reset_index(drop=True)
    if len(out) != 12:
        raise ValueError(f"Expected 12 primary cities, found {len(out)}")
    if float(out["factor_identity_error_pp"].abs().max()) > 1e-9:
        raise ValueError("Panel a factor identity check failed")
    return out


def build_decomposition_data() -> pd.DataFrame:
    raw = pd.read_csv(DECOMPOSITION_INPUT)
    names = [PAIR_NAMES[pair] for pair in PAIR_ORDER]
    out = raw.loc[raw["pair"].isin(names)].copy()
    out["pair_order"] = out["pair"].map({name: i + 1 for i, name in enumerate(names)})
    out["display_pair"] = out["pair_order"].map({i + 1: PAIR_SHORT[pair] for i, pair in enumerate(PAIR_ORDER)})
    out = out.sort_values("pair_order").reset_index(drop=True)
    contribution_sum = out[
        [
            "prevalence_contribution_pp",
            "roof_size_selection_contribution_pp",
            "conditional_intensity_contribution_pp",
        ]
    ].sum(axis=1)
    out["recalculated_gap_pp"] = contribution_sum
    out["recalculated_error_pp"] = contribution_sum - out["pv_utilization_gap_pp"]
    if len(out) != 6 or float(out["recalculated_error_pp"].abs().max()) > 1e-9:
        raise ValueError("Panel b exact decomposition check failed")
    return out


def build_roofsize_data() -> pd.DataFrame:
    raw = pd.read_csv(ROOFSIZE_INPUT)
    order = [city for pair in PAIR_ORDER for city in pair]
    out = raw.loc[raw["city"].isin(order)].copy()
    out["pair_order"] = out["city"].map({city: i + 1 for i, pair in enumerate(PAIR_ORDER) for city in pair})
    out["city_role"] = out["city"].map({pair[0]: "city_1" for pair in PAIR_ORDER} | {pair[1]: "city_2" for pair in PAIR_ORDER})
    out["city_order"] = out["city"].map({city: i + 1 for i, city in enumerate(order)})
    out["roof_area_share_pct"] = out.groupby("city")["building_area_m2"].transform(lambda values: values / values.sum() * 100.0)
    out["pv_utilization_pct"] = out["pv_area_ratio"] * 100.0
    out["low_building_count_bin"] = out["building_count"] < LOW_COUNT_THRESHOLD
    out = out.sort_values(["city_order", "bin_left_m2"]).reset_index(drop=True)
    if len(out) != 72:
        raise ValueError(f"Expected 72 primary roof-size rows, found {len(out)}")
    return out


def build_building_use_data() -> pd.DataFrame:
    raw = pd.read_csv(BUILDING_CLASS_INPUT)
    raw = raw.loc[raw["scope"].eq("city")].copy()
    low = pd.read_csv(LOW_COUNT_INPUT)
    low["low_count_cell"] = low["low_count_cell"].astype(str).str.lower().isin({"true", "1", "yes"})
    low_keys = set(
        zip(
            low.loc[low["low_count_cell"], "city_key"].str.lower(),
            low.loc[low["low_count_cell"], "building_class_key"].str.lower(),
        )
    )
    completeness = pd.read_csv(LABEL_COMPLETENESS_INPUT)
    completeness["city_key"] = completeness["city"].str.lower().str.replace(" ", "", regex=False)
    risk_cities = set(
        completeness.loc[
            (completeness["labeled_area_pct"] < LABEL_COMPLETENESS_THRESHOLD)
            | (completeness["labeled_buildings_pct"] < LABEL_COMPLETENESS_THRESHOLD),
            "city_key",
        ]
    )

    rows = []
    for pair_order, pair in enumerate(PAIR_ORDER, start=1):
        city_1, city_2 = pair
        a = raw.loc[raw["name"].eq(city_1)].set_index("base_class_key")
        b = raw.loc[raw["name"].eq(city_2)].set_index("base_class_key")
        for class_order, class_key in enumerate(CLASS_ORDER, start=1):
            prevalence_1 = float(a.at[class_key, "pv_building_count_ratio"] * 100.0)
            prevalence_2 = float(b.at[class_key, "pv_building_count_ratio"] * 100.0)
            low_count = (city_1, class_key) in low_keys or (city_2, class_key) in low_keys
            label_risk = class_key == "others" or city_1 in risk_cities or city_2 in risk_cities
            rows.append(
                {
                    "pair_order": pair_order,
                    "pair": PAIR_NAMES[pair],
                    "display_pair": PAIR_SHORT[pair],
                    "city_1": city_1,
                    "city_2": city_2,
                    "class_order": class_order,
                    "building_class_key": class_key,
                    "building_class": CLASS_LABELS[class_order - 1],
                    "city_1_prevalence_pct": prevalence_1,
                    "city_2_prevalence_pct": prevalence_2,
                    "prevalence_gap_pp": prevalence_1 - prevalence_2,
                    "low_count_flag": low_count,
                    "label_completeness_flag": label_risk,
                    "reliability_hatch": low_count or label_risk,
                }
            )
    out = pd.DataFrame(rows)
    if len(out) != 36:
        raise ValueError(f"Expected 36 primary building-use cells, found {len(out)}")
    return out


def draw_panel_a(ax: plt.Axes, data: pd.DataFrame, compact: bool) -> None:
    """Draw three factor-specific data bars in one shared panel.

    Each factor retains the fixed scale used by the former three-column panel.
    Printed labels report the original values so that bar lengths are not read
    as direct comparisons between quantities with different units.
    """
    centres = np.arange(len(data), dtype=float) * 3.05
    offsets = [-0.64, 0.0, 0.64]
    metric_codes = ["P", "R", "I"]
    metric_styles = [
        {"height": 0.48, "alpha": 0.92, "hatch": None, "face": True},
        {"height": 0.36, "alpha": 0.34, "hatch": "////", "face": True},
        {"height": 0.22, "alpha": 0.82, "hatch": None, "face": True},
    ]
    value_size = 4.4 if compact else 6.3
    label_size = 5.1 if compact else 7.2

    for row_index, row in data.iterrows():
        centre = centres[row_index]
        color = row["plot_color"]
        for metric_index, ((metric, _, _, _), offset, code, style) in enumerate(
            zip(ANATOMY_METRICS, offsets, metric_codes, metric_styles)
        ):
            y = centre + offset
            fraction = float(row[f"{metric}_bar_fraction"])
            value = float(row[metric])
            ax.barh(y, 1.0, height=style["height"], color="#f1efed", edgecolor="none", zorder=0)
            ax.barh(
                y,
                fraction,
                height=style["height"],
                color=to_rgba(color, style["alpha"]),
                edgecolor=color if style["hatch"] else "none",
                linewidth=0.45,
                hatch=style["hatch"],
                zorder=3,
            )
            ax.text(0.012, y, code, ha="left", va="center", fontsize=4.0 if compact else 5.4, color="white" if fraction > 0.12 and metric_index != 1 else MUTED, zorder=5)
            if metric == "roof_size_selection":
                number = f"{value:.1f}"
            elif value < 1:
                number = f"{value:.2f}%"
            else:
                number = f"{value:.1f}%"
            ax.text(min(fraction + 0.025, 1.07), y, number, ha="left", va="center", fontsize=value_size, color=TEXT, clip_on=False, zorder=5)

        if row_index % 2 == 1 and row_index < len(data) - 1:
            ax.axhline(centre + 1.50, color="#e8e2de", linewidth=0.55, zorder=0)

    ax.set_xlim(0, 1.18)
    ax.set_ylim(centres[-1] + 1.45, -3.60)
    ax.set_yticks(centres)
    ax.set_yticklabels(data["City"], fontsize=label_size, color=TEXT)
    for tick, color in zip(ax.get_yticklabels(), data["plot_color"]):
        tick.set_color(color)
    ax.set_xticks([0, 0.5, 1.0])
    ax.set_xticklabels(["0", "50", "100"], fontsize=4.8 if compact else 7.0, color=MUTED)
    ax.set_xlabel("Position within each factor scale (%)", fontsize=5.3 if compact else 7.8, color=TEXT, labelpad=3)
    ax.tick_params(axis="y", length=0, pad=2)
    ax.tick_params(axis="x", length=2.0, width=0.55, pad=2)
    ax.grid(axis="x", linestyle="--", linewidth=0.45, alpha=0.50, color=GRID, zorder=0)
    for spine in ("top", "right", "left"):
        ax.spines[spine].set_visible(False)
    ax.spines["bottom"].set_color(AXIS)
    ax.spines["bottom"].set_linewidth(0.55)

    legend_handles = [
        Patch(facecolor="#6f7f7b", edgecolor="none", label="P  Prevalence (%)"),
        Patch(facecolor=to_rgba("#6f7f7b", 0.34), edgecolor="#6f7f7b", hatch="////", linewidth=0.45, label="R  Roof selection"),
        Rectangle((0, 0), 1, 0.35, facecolor="#6f7f7b", edgecolor="none", label="I  Conditional intensity (%)"),
    ]
    ax.legend(handles=legend_handles, loc="upper left", bbox_to_anchor=(0.0, 1.005), frameon=False, ncol=1, fontsize=4.7 if compact else 6.8, handlelength=1.3, handleheight=0.7, labelspacing=0.35, borderaxespad=0)
    ax.text(0.0, -0.075, "Bars use separate fixed factor scales; labels show original values.", transform=ax.transAxes, ha="left", va="top", fontsize=4.3 if compact else 6.2, color=MUTED, clip_on=False)
    add_panel_label(ax, "a", (-0.34 if compact else -0.28, 1.025))


def draw_panel_a_pair_axis(
    ax: plt.Axes,
    pair_data: pd.DataFrame,
    pair: tuple[str, str],
    index: int,
) -> None:
    """Draw one pair-aligned anatomy facet using pattern-coded metrics."""
    pair_data = pair_data.set_index("city_key")
    metric_centres = np.array([2.0, 1.18, 0.36])
    city_offsets = [0.17, -0.17]
    bar_height = 0.27
    color_a, color_b = PAIR_COLORS[pair]

    for city, color, offset in zip(pair, (color_a, color_b), city_offsets):
        row = pair_data.loc[city]
        for metric_index, ((metric, _, _, _), centre, hatch) in enumerate(
            zip(ANATOMY_METRICS, metric_centres, ANATOMY_PATTERNS)
        ):
            y = centre + offset
            fraction = float(row[f"{metric}_bar_fraction"])
            value = float(row[metric])
            ax.barh(
                y,
                1.0,
                height=bar_height,
                color="#f1efed",
                edgecolor="none",
                zorder=0,
            )
            bar_patch = ax.barh(
                y,
                fraction,
                height=bar_height,
                color=to_rgba(color, 0.10 if hatch else 0.72),
                edgecolor=color,
                linewidth=0.55,
                zorder=3,
            )[0]
            if metric_index == 0:
                stripe_segments = [
                    [(x, y - bar_height / 2.0), (x, y + bar_height / 2.0)]
                    for x in np.arange(0.011, fraction, 0.022)
                ]
            elif metric_index == 1:
                diagonal_dx = 0.030
                stripe_segments = [
                    [(x, y - bar_height / 2.0), (x + diagonal_dx, y + bar_height / 2.0)]
                    for x in np.arange(-diagonal_dx, fraction, 0.038)
                ]
            else:
                stripe_segments = []
            if stripe_segments:
                stripes = LineCollection(
                    stripe_segments,
                    colors=[color],
                    linewidths=0.95,
                    capstyle="butt",
                    zorder=4,
                )
                stripes.set_clip_path(bar_patch)
                ax.add_collection(stripes)
            if metric == "roof_size_selection":
                number = f"{value:.1f}"
            elif value < 1:
                number = f"{value:.2f}%"
            else:
                number = f"{value:.1f}%"
            ax.text(
                min(fraction + 0.020, 0.975),
                y,
                number,
                ha="left",
                va="center",
                fontsize=8.5,
                color=TEXT,
                clip_on=False,
                zorder=5,
            )

    ax.set_xlim(0, 1.0)
    ax.set_ylim(-0.48, 2.52)
    ax.set_yticks(metric_centres)
    ax.set_yticklabels(["P", "R", "I"], fontsize=10.2, color=TEXT)
    ax.tick_params(axis="y", length=0, pad=4)
    ax.set_xticks([0, 0.5, 1.0])
    if index == len(PAIR_ORDER) - 1:
        ax.set_xticklabels(["0", "50", "100"], fontsize=10.2, color=MUTED)
        ax.set_xlabel("Position within each metric scale (%)", fontsize=11.0, color=TEXT, labelpad=4)
    else:
        ax.set_xticklabels([])
    ax.tick_params(axis="x", length=2.0, width=0.55, pad=2)
    ax.grid(axis="x", linestyle="--", linewidth=0.45, alpha=0.50, color=GRID, zorder=0)
    for spine in ("top", "right", "left"):
        ax.spines[spine].set_visible(False)
    ax.spines["bottom"].set_color(AXIS)
    ax.spines["bottom"].set_linewidth(0.55)

    city_handles = [
        Patch(
            facecolor=to_rgba(color, 0.70),
            edgecolor=color,
            linewidth=0.70,
            label=SHOW_NAME[city],
        )
        for city, color in zip(pair, (color_a, color_b))
    ]
    ax.legend(
        handles=city_handles,
        loc="upper center",
        bbox_to_anchor=(0.5, 1.20),
        ncol=2,
        frameon=False,
        fontsize=10.0,
        handlelength=1.70,
        handleheight=0.65,
        handletextpad=0.45,
        columnspacing=1.00,
        borderaxespad=0,
    )


def draw_panel_a_combined(
    fig: plt.Figure,
    spec,
    data: pd.DataFrame,
    reference_positions: list[tuple[float, float, float, float]],
) -> list[plt.Axes]:
    """Align the six anatomy facets to the six original Fig. 6a rows."""
    outer_box = spec.get_position(fig)
    axes = []
    for index, (pair, position) in enumerate(zip(PAIR_ORDER, reference_positions)):
        x0, y0, width, height = position
        ax = fig.add_axes(
            [
                outer_box.x0 + x0 * outer_box.width,
                outer_box.y0 + y0 * outer_box.height,
                width * outer_box.width,
                height * outer_box.height,
            ]
        )
        pair_rows = data.loc[data["city_key"].isin(pair)].copy()
        draw_panel_a_pair_axis(ax, pair_rows, pair, index)
        axes.append(ax)

    metric_handles = [
        Patch(
            facecolor=to_rgba("#6f7f7b", 0.10 if hatch else 0.72),
            edgecolor="#6f7f7b",
            hatch=hatch,
            linewidth=0.55,
            label=label,
        )
        for hatch, label in zip(
            ANATOMY_PATTERNS,
            ["P  Prevalence (%)", "R  Roof selection ratio", "I  Conditional intensity (%)"],
        )
    ]
    fig.legend(
        handles=metric_handles,
        loc="upper center",
        bbox_to_anchor=(
            outer_box.x0 + outer_box.width / 2.0,
            axes[-1].get_position().y0 - 0.050,
        ),
        bbox_transform=fig.transFigure,
        ncol=3,
        frameon=False,
        fontsize=7.2,
        handlelength=1.35,
        handleheight=0.70,
        columnspacing=0.35,
        handletextpad=0.38,
        borderaxespad=0,
    )
    first_axis_box = axes[0].get_position()
    ylabel_offset_in = 0.38
    ylabel_x = first_axis_box.x0 - ylabel_offset_in / fig.get_figwidth()
    fig.text(
        ylabel_x,
        (outer_box.y0 + outer_box.y1) / 2.0,
        "Deployment component",
        rotation=90,
        ha="center",
        va="center",
        fontsize=10.5,
        color=TEXT,
    )
    panel_label_x = (
        ylabel_x - first_axis_box.x0
    ) / first_axis_box.width
    add_panel_label(axes[0], "a", (panel_label_x, 1.22))
    return axes


def draw_heatmap(
    ax: plt.Axes,
    cax: plt.Axes,
    matrix: np.ndarray,
    row_labels: list[str],
    column_labels: list[str],
    compact: bool,
    hatches: np.ndarray | None = None,
    colorbar_label: str = "",
    colorbar_orientation: str = "vertical",
    show_xlabels: bool = True,
    value_decimals: int = 1,
    ytick_rotation: float = 0.0,
    xtick_rotation: float = 0.0,
    xtick_fontsize: float | None = None,
) -> tuple[plt.AxesImage, float]:
    vmax = max(float(np.nanmax(np.abs(matrix))), 1.0)
    norm = TwoSlopeNorm(vmin=-vmax, vcenter=0.0, vmax=vmax)
    cmap = LinearSegmentedColormap.from_list("city_gap_diverging", DIVERGING_COLORS, N=256)
    im = ax.imshow(matrix, cmap=cmap, norm=norm, aspect="auto", zorder=1)
    nrows, ncols = matrix.shape
    ax.set_xticks(np.arange(ncols))
    x_fontsize = xtick_fontsize if xtick_fontsize is not None else (5.2 if compact else 10.8)
    ax.set_xticklabels(
        column_labels,
        fontsize=x_fontsize,
        color="black",
        linespacing=0.95,
        rotation=xtick_rotation,
        rotation_mode="anchor",
        ha="right" if xtick_rotation else "center",
        va="top" if xtick_rotation else "baseline",
    )
    ax.set_yticks(np.arange(nrows))
    ax.set_yticklabels(
        row_labels,
        fontsize=5.5 if compact else 10.8,
        color="black",
        rotation=ytick_rotation,
        rotation_mode="anchor",
        ha="right",
        va="center",
    )
    ax.tick_params(axis="x", length=0, pad=3, labelbottom=show_xlabels)
    ax.tick_params(axis="y", length=0, pad=4)
    ax.set_xticks(np.arange(-0.5, ncols, 1), minor=True)
    ax.set_yticks(np.arange(-0.5, nrows, 1), minor=True)
    ax.grid(which="minor", color="white", linewidth=0.8 if compact else 1.2)
    ax.tick_params(which="minor", bottom=False, left=False)
    if hatches is not None:
        for i in range(nrows):
            for j in range(ncols):
                if bool(hatches[i, j]):
                    ax.add_patch(
                        Rectangle(
                            (j - 0.5, i - 0.5),
                            1.0,
                            1.0,
                            facecolor=(1, 1, 1, 0.06),
                            edgecolor="#777777",
                            linewidth=0.45 if compact else 0.8,
                            hatch="////",
                            zorder=4.5,
                        )
                    )
    for i in range(nrows):
        for j in range(ncols):
            value = float(matrix[i, j])
            display_value = 0.0 if abs(value) < 0.055 else value
            ax.text(
                j,
                i,
                f"{display_value:+.{value_decimals}f}",
                ha="center",
                va="center",
                fontsize=4.9 if compact else 10.3,
                color="white" if abs(value) > vmax * 0.55 else TEXT,
                zorder=5,
            )
    for spine in ax.spines.values():
        spine.set_visible(False)
    cbar = ax.figure.colorbar(im, cax=cax, orientation=colorbar_orientation)
    if colorbar_orientation == "vertical":
        cbar.set_label(
            colorbar_label,
            fontsize=5.0 if compact else 10.0,
            labelpad=4,
            rotation=270,
            va="bottom",
        )
    else:
        cbar.set_label(colorbar_label, fontsize=4.8 if compact else 10.0, labelpad=2)
    cbar.ax.tick_params(labelsize=4.8 if compact else 9.6, length=2.0, colors="black", pad=2)
    cbar.outline.set_linewidth(0.5)
    return im, vmax


def draw_panel_c(
    ax: plt.Axes,
    cax: plt.Axes,
    data: pd.DataFrame,
    compact: bool,
    show_xlabels: bool = True,
) -> None:
    matrix = data[DECOMPOSITION_COLUMNS].to_numpy(float).T
    column_labels = [label.replace(" - ", "–") for label in data["display_pair"].tolist()]
    draw_heatmap(
        ax,
        cax,
        matrix,
        DECOMPOSITION_LABELS,
        column_labels,
        compact,
        colorbar_label="Contribution or gap (pp)",
        colorbar_orientation="vertical",
        show_xlabels=show_xlabels,
        value_decimals=1,
        ytick_rotation=0.0,
        xtick_rotation=30.0,
        xtick_fontsize=9.6,
    )
    ax.axhline(2.5, color="#5e5148", linewidth=0.9, alpha=0.55, zorder=6)
    ax.set_title("Utilization-gap decomposition", loc="left", fontsize=6.0 if compact else 11.0, pad=5, color=TEXT)
    add_panel_label(ax, "c", (-0.04 if compact else -0.14, 1.075))


def roofsize_pair_data(data: pd.DataFrame, pair: tuple[str, str]) -> tuple[pd.DataFrame, pd.DataFrame]:
    a = data.loc[data["city"].eq(pair[0])].sort_values("bin_left_m2")
    b = data.loc[data["city"].eq(pair[1])].sort_values("bin_left_m2")
    return a, b


def draw_original_fig6a_pair(
    ax: plt.Axes,
    data: pd.DataFrame,
    pair: tuple[str, str],
    index: int,
) -> None:
    """Draw one roof-size facet with the untouched original Fig. 6a grammar."""
    a, b = roofsize_pair_data(data, pair)
    line_a, line_b, _ = ORIGINAL_FIG6A.draw_roofsize_pair_axis(
        ax=ax,
        rows_a=a.to_dict("records"),
        rows_b=b.to_dict("records"),
        city_a=pair[0],
        city_b=pair[1],
        metric="pv_area_ratio",
        as_percent=True,
        share_metric="roof_area",
        show_share_axis=True,
        show_xlabel=index == len(PAIR_ORDER) - 1,
        show_metric_label=False,
        show_frontier_label=False,
    )
    ax.legend(
        [line_a, line_b],
        [line_a.get_label(), line_b.get_label()],
        loc="upper left",
        bbox_to_anchor=(0.0, 1.14),
        ncol=2,
        frameon=False,
        fontsize=10.0,
        handlelength=1.7,
        columnspacing=1.0,
    )
    if index < len(PAIR_ORDER) - 1:
        ax.tick_params(axis="x", labelbottom=False)


def original_fig6a_axis_positions(data: pd.DataFrame) -> list[tuple[float, float, float, float]]:
    """Recover the original tight-layout axes geometry on its native canvas."""
    reference, axes = plt.subplots(
        nrows=len(PAIR_ORDER),
        ncols=1,
        figsize=(ORIGINAL_FIG6A_CANVAS_WIDTH_IN, ORIGINAL_FIG6A_CANVAS_HEIGHT_IN),
        dpi=220,
        sharex=True,
        sharey=False,
    )
    for index, (ax, pair) in enumerate(zip(axes, PAIR_ORDER)):
        draw_original_fig6a_pair(ax, data, pair, index)
    ORIGINAL_FIG6A.add_large_roof_frontier_xtick_note(axes[-1])
    reference.tight_layout(rect=(0.055, 0.02, 0.93, 0.995), h_pad=0.72)
    positions = [tuple(float(value) for value in ax.get_position().bounds) for ax in axes]
    plt.close(reference)
    return positions


def draw_roofsize_axis(
    ax: plt.Axes,
    data: pd.DataFrame,
    pair: tuple[str, str],
    compact: bool,
    show_xlabels: bool,
    show_share_axis: bool,
) -> plt.Axes:
    a, b = roofsize_pair_data(data, pair)
    x = np.arange(len(a), dtype=float)
    color_a, color_b = PAIR_COLORS[pair]
    values_a = a["pv_utilization_pct"].to_numpy(float)
    values_b = b["pv_utilization_pct"].to_numpy(float)
    share_a = a["roof_area_share_pct"].to_numpy(float)
    share_b = b["roof_area_share_pct"].to_numpy(float)
    line_width = 1.25 if compact else 2.1
    marker_size = 3.1 if compact else 4.7

    share_ax = ax.twinx()
    share_ax.bar(x - 0.17, share_a, width=0.34, color=to_rgba(color_a, 0.32), edgecolor="none", zorder=0)
    share_ax.bar(x + 0.17, share_b, width=0.34, color=to_rgba(color_b, 0.32), edgecolor="none", zorder=0)
    share_ax.set_ylim(0, 100)
    share_ax.set_zorder(0)
    share_ax.patch.set_alpha(0)
    share_ax.spines["top"].set_visible(False)
    share_ax.spines["left"].set_visible(False)
    if show_share_axis:
        share_ax.set_yticks([0, 50, 100])
        share_ax.tick_params(axis="y", labelsize=4.3 if compact else 7.0, colors="#8d8178", length=1.8, pad=1)
        share_ax.spines["right"].set_color("#b9b0aa")
        share_ax.spines["right"].set_linewidth(0.55)
    else:
        share_ax.set_yticks([])
        share_ax.spines["right"].set_visible(False)

    ax.set_zorder(2)
    ax.patch.set_alpha(0)
    line_a = ax.plot(x, values_a, color=color_a, marker="o", markersize=marker_size, markeredgecolor="white", markeredgewidth=0.45, linewidth=line_width, label=SHOW_NAME[pair[0]], zorder=4)[0]
    line_b = ax.plot(x, values_b, color=color_b, marker="o", markersize=marker_size, markeredgecolor="white", markeredgewidth=0.45, linewidth=line_width, label=SHOW_NAME[pair[1]], zorder=4)[0]
    ax.scatter([x[-1]], [values_a[-1]], s=24 if compact else 48, color=color_a, edgecolor="black", linewidth=0.55, zorder=6)
    ax.scatter([x[-1]], [values_b[-1]], s=24 if compact else 48, color=color_b, edgecolor="black", linewidth=0.55, zorder=6)
    local_max = max(float(values_a.max()), float(values_b.max()))
    ax.set_ylim(0, local_max * 1.23 if local_max > 0 else 1)
    ax.set_xlim(-0.45, len(x) - 0.55)
    ax.grid(axis="y", linestyle="--", linewidth=0.45, alpha=0.28, color="#8d8178")
    ax.set_xticks(x)
    if show_xlabels:
        ax.set_xticklabels(a["roof_size_bin"], rotation=28, ha="right", fontsize=4.8 if compact else 7.8)
    else:
        ax.set_xticklabels([])
    ax.tick_params(axis="x", length=1.7, colors="black", pad=1)
    ax.tick_params(axis="y", labelsize=4.6 if compact else 7.5, colors="black", length=1.7, pad=1)
    for spine in ("top", "right"):
        ax.spines[spine].set_visible(False)
    ax.spines["left"].set_color(AXIS)
    ax.spines["bottom"].set_color(AXIS)
    ax.spines["left"].set_linewidth(0.55)
    ax.spines["bottom"].set_linewidth(0.55)
    ax.legend(
        [line_a, line_b],
        [line_a.get_label(), line_b.get_label()],
        loc="upper left",
        bbox_to_anchor=(0.0, 1.08 if compact else 1.13),
        ncol=2,
        frameon=False,
        fontsize=4.8 if compact else 7.6,
        handlelength=1.15,
        handletextpad=0.25,
        columnspacing=0.65,
        borderaxespad=0,
    )
    return share_ax


def draw_panel_b_combined(
    fig: plt.Figure,
    spec,
    data: pd.DataFrame,
    reference_positions: list[tuple[float, float, float, float]] | None = None,
) -> list[plt.Axes]:
    """Map the original Fig. 6a axes geometry onto its native-size allocation."""
    outer_box = spec.get_position(fig)
    if reference_positions is None:
        reference_positions = original_fig6a_axis_positions(data)
    axes = []
    for index, (pair, position) in enumerate(zip(PAIR_ORDER, reference_positions)):
        x0, y0, width, height = position
        ax = fig.add_axes(
            [
                outer_box.x0 + x0 * outer_box.width,
                outer_box.y0 + y0 * outer_box.height,
                width * outer_box.width,
                height * outer_box.height,
            ]
        )
        draw_original_fig6a_pair(ax, data, pair, index)
        axes.append(ax)
    ORIGINAL_FIG6A.add_large_roof_frontier_xtick_note(axes[-1])
    fig.text(
        outer_box.x0 + 0.05 * outer_box.width,
        outer_box.y0 + 0.50 * outer_box.height,
        "PV utilization (%)",
        rotation=90,
        ha="left",
        va="center",
        fontsize=10.5,
        color="black",
    )
    fig.text(
        outer_box.x0 + 0.95 * outer_box.width,
        outer_box.y0 + 0.50 * outer_box.height,
        "Share of city stock (%)",
        rotation=270,
        ha="right",
        va="center",
        fontsize=10.5,
        color="#6e6259",
    )
    first_axis_box = axes[0].get_position()
    ylabel_x = outer_box.x0 + 0.05 * outer_box.width
    panel_label_x = (ylabel_x - first_axis_box.x0) / first_axis_box.width
    add_panel_label(axes[0], "b", (panel_label_x, 1.22))
    return axes


def building_use_matrices(data: pd.DataFrame) -> tuple[np.ndarray, np.ndarray, list[str]]:
    matrix = data.pivot(index="pair_order", columns="class_order", values="prevalence_gap_pp").sort_index().to_numpy(float)
    hatches = data.pivot(index="pair_order", columns="class_order", values="reliability_hatch").sort_index().to_numpy(bool)
    labels = data.drop_duplicates("pair_order").sort_values("pair_order")["display_pair"].tolist()
    return matrix, hatches, labels


def draw_panel_d(
    ax: plt.Axes,
    cax: plt.Axes,
    data: pd.DataFrame,
    compact: bool,
    show_xlabels: bool = True,
) -> None:
    matrix, hatches, labels = building_use_matrices(data)
    matrix = matrix.T
    hatches = hatches.T
    labels = [label.replace(" - ", "–") for label in labels]
    draw_heatmap(
        ax,
        cax,
        matrix,
        CLASS_LABELS,
        labels,
        compact,
        hatches=hatches,
        colorbar_label="Prevalence gap (pp)",
        colorbar_orientation="vertical",
        show_xlabels=show_xlabels,
        value_decimals=1,
        ytick_rotation=0.0,
        xtick_rotation=30.0,
        xtick_fontsize=9.6,
    )
    ax.axhline(1.5, color="#5e5148", linewidth=0.9, alpha=0.55, zorder=6)
    ax.set_title("Building-use prevalence gaps", loc="left", fontsize=6.0 if compact else 11.0, pad=5, color=TEXT)
    ax.set_xlabel("City pairs", fontsize=6.2 if compact else 12.5, labelpad=4, color=TEXT)
    add_panel_label(ax, "d", (-0.04 if compact else -0.14, 1.075))
    hatch = Patch(
        facecolor="white",
        edgecolor="#777777",
        hatch="////",
        linewidth=0.7,
        label="Low count or label-completeness risk",
    )
    ax.legend(
        handles=[hatch],
        loc="upper center",
        bbox_to_anchor=(0.5, -0.205),
        frameon=False,
        fontsize=4.5 if compact else 8.8,
        handlelength=1.10,
        handletextpad=0.42,
        labelspacing=0.15,
        borderaxespad=0,
    )


def save_standalone_panel_a(data: pd.DataFrame, roofsize_data: pd.DataFrame) -> tuple[Path, Path]:
    fig = plt.figure(figsize=(5.30, 8.50), dpi=300)
    fig.patch.set_facecolor("white")
    vertical_margin = (1.0 - ORIGINAL_FIG6A_CANVAS_HEIGHT_IN / fig.get_figheight()) / 2.0
    container_width = ORIGINAL_FIG6A_CANVAS_WIDTH_IN / fig.get_figwidth()
    grid = fig.add_gridspec(
        1,
        1,
        left=0.06,
        right=0.06 + container_width,
        top=1.0 - vertical_margin,
        bottom=vertical_margin,
    )
    reference_positions = original_fig6a_axis_positions(roofsize_data)
    draw_panel_a_combined(fig, grid[0, 0], data, reference_positions)
    pdf = PANEL_OUTDIR / "fig3a_primary12_city_anatomy_bars.pdf"
    png = PANEL_OUTDIR / "fig3a_primary12_city_anatomy_bars.png"
    fig.savefig(pdf, bbox_inches="tight", pad_inches=0.025, facecolor="white")
    fig.savefig(png, dpi=300, bbox_inches="tight", pad_inches=0.025, facecolor="white")
    plt.close(fig)
    return pdf, png


def save_standalone_panel_b(data: pd.DataFrame) -> tuple[Path, Path]:
    fig, axes = plt.subplots(
        len(PAIR_ORDER),
        1,
        figsize=(ORIGINAL_FIG6A_CANVAS_WIDTH_IN, ORIGINAL_FIG6A_CANVAS_HEIGHT_IN),
        dpi=220,
        sharex=True,
        sharey=False,
    )
    fig.patch.set_facecolor("white")
    for index, (ax, pair) in enumerate(zip(axes, PAIR_ORDER)):
        draw_original_fig6a_pair(ax, data, pair, index)
    ORIGINAL_FIG6A.add_large_roof_frontier_xtick_note(axes[-1])
    fig.tight_layout(rect=(0.055, 0.02, 0.93, 0.995), h_pad=0.72)
    fig.text(0.05, 0.50, "PV utilization (%)", rotation=90, ha="left", va="center", fontsize=10.5, color="black")
    fig.text(0.95, 0.50, "Share of city stock (%)", rotation=270, ha="right", va="center", fontsize=10.5, color="#6e6259")
    pdf = PANEL_OUTDIR / "fig3b_primary6_roofsize_profiles.pdf"
    png = PANEL_OUTDIR / "fig3b_primary6_roofsize_profiles.png"
    fig.savefig(pdf, bbox_inches="tight", transparent=True)
    fig.savefig(png, dpi=300, bbox_inches="tight", transparent=True)
    plt.close(fig)
    return pdf, png


def save_standalone_panel_c(data: pd.DataFrame) -> tuple[Path, Path]:
    fig = plt.figure(figsize=(6.15, 3.25), dpi=300)
    grid = fig.add_gridspec(1, 2, width_ratios=[1.0, 0.040], wspace=0.10)
    ax = fig.add_subplot(grid[0, 0])
    cax = fig.add_subplot(grid[0, 1])
    draw_panel_c(ax, cax, data, compact=False)
    fig.subplots_adjust(left=0.22, right=0.90, bottom=0.17, top=0.89)
    pdf = PANEL_OUTDIR / "fig3c_primary6_exact_decomposition.pdf"
    png = PANEL_OUTDIR / "fig3c_primary6_exact_decomposition.png"
    fig.savefig(pdf, bbox_inches="tight", pad_inches=0.025, facecolor="white")
    fig.savefig(png, dpi=300, bbox_inches="tight", pad_inches=0.025, facecolor="white")
    plt.close(fig)
    return pdf, png


def save_standalone_panel_d(data: pd.DataFrame) -> tuple[Path, Path]:
    fig = plt.figure(figsize=(6.15, 4.15), dpi=300)
    grid = fig.add_gridspec(1, 2, width_ratios=[1.0, 0.040], wspace=0.10)
    ax = fig.add_subplot(grid[0, 0])
    cax = fig.add_subplot(grid[0, 1])
    draw_panel_d(ax, cax, data, compact=False)
    fig.subplots_adjust(left=0.18, right=0.90, top=0.88, bottom=0.16)
    pdf = PANEL_OUTDIR / "fig3d_primary6_building_use_gaps.pdf"
    png = PANEL_OUTDIR / "fig3d_primary6_building_use_gaps.png"
    fig.savefig(pdf, bbox_inches="tight", pad_inches=0.025, facecolor="white")
    fig.savefig(png, dpi=300, bbox_inches="tight", pad_inches=0.025, facecolor="white")
    plt.close(fig)
    return pdf, png


def draw_panel_cd_subfigure(
    fig: plt.Figure,
    spec,
    decomposition_data: pd.DataFrame,
    building_use_data: pd.DataFrame,
    primary_reference_positions: list[tuple[float, float, float, float]] | None = None,
) -> tuple[plt.Axes, plt.Axes, plt.Axes, plt.Axes]:
    """Draw transposed panels c and d with a shared city-pair x axis."""
    content_spec = spec
    if primary_reference_positions is not None:
        primary_bottom = min(position[1] for position in primary_reference_positions)
        primary_top = max(position[1] + position[3] for position in primary_reference_positions)
        wrapper = spec.subgridspec(
            3,
            1,
            height_ratios=[1.0 - primary_top, primary_top - primary_bottom, primary_bottom],
            hspace=0.0,
        )
        content_spec = wrapper[1, 0]
    grid = content_spec.subgridspec(
        2,
        2,
        height_ratios=[4.0, 6.0],
        width_ratios=[1.0, 0.036],
        hspace=0.20,
        wspace=0.08,
    )
    ax_c = fig.add_subplot(grid[0, 0])
    cax_c = fig.add_subplot(grid[0, 1])
    ax_d = fig.add_subplot(grid[1, 0], sharex=ax_c)
    cax_d = fig.add_subplot(grid[1, 1])
    draw_panel_c(ax_c, cax_c, decomposition_data, compact=False, show_xlabels=False)
    draw_panel_d(ax_d, cax_d, building_use_data, compact=False, show_xlabels=True)
    return ax_c, cax_c, ax_d, cax_d


def save_standalone_panel_cd(
    decomposition_data: pd.DataFrame,
    building_use_data: pd.DataFrame,
) -> tuple[Path, Path]:
    fig = plt.figure(figsize=(4.875, 7.20), dpi=300)
    outer = fig.add_gridspec(1, 1, left=0.20, right=0.90, bottom=0.10, top=0.95)
    draw_panel_cd_subfigure(fig, outer[0, 0], decomposition_data, building_use_data)
    pdf = PANEL_OUTDIR / "fig3cd_transposed_heatmaps_subfigure.pdf"
    png = PANEL_OUTDIR / "fig3cd_transposed_heatmaps_subfigure.png"
    fig.savefig(pdf, bbox_inches="tight", pad_inches=0.025, facecolor="white")
    fig.savefig(png, dpi=300, bbox_inches="tight", pad_inches=0.025, facecolor="white")
    plt.close(fig)
    return pdf, png


def save_source_data(a: pd.DataFrame, b: pd.DataFrame, c: pd.DataFrame, d: pd.DataFrame) -> None:
    SOURCE_DIR.mkdir(parents=True, exist_ok=True)
    a.to_csv(SOURCE_DIR / "Fig_3a.csv", index=False)
    c.to_csv(SOURCE_DIR / "Fig_3b.csv", index=False)
    b.to_csv(SOURCE_DIR / "Fig_3c.csv", index=False)
    d.to_csv(SOURCE_DIR / "Fig_3d.csv", index=False)
    parts = []
    for label, record_type, frame in [
        ("a", "city_anatomy", a),
        ("b", "city_roof_size_profile", c),
        ("c", "pair_exact_decomposition", b),
        ("d", "pair_building_use_gap", d),
    ]:
        part = frame.copy()
        part.insert(0, "panel", label)
        part.insert(1, "record_type", record_type)
        parts.append(part)
    pd.concat(parts, ignore_index=True, sort=False).to_csv(SOURCE_DIR / "Fig_3.csv", index=False)


def build_combined_figure(
    a: pd.DataFrame,
    b: pd.DataFrame,
    c: pd.DataFrame,
    d: pd.DataFrame,
) -> tuple[Path, Path, dict[str, float]]:
    """Build an Illustrator-ready master without scaling the Fig. 3b panel.

    The middle allocation retains the physical width and height of the original
    Fig. 6a PDF. The master canvas and the other panels expand around it.
    """
    panel_width_in = ORIGINAL_FIG6A_CANVAS_WIDTH_IN
    right_group_width_in = 3.15
    panel_a_b_overlap_in = 0.60
    panel_b_cd_gap_in = 0.80
    outer_left = 0.020
    outer_right = 0.990
    master_height = 8.50
    vertical_margin = (1.0 - ORIGINAL_FIG6A_CANVAS_HEIGHT_IN / master_height) / 2.0
    panel_a_left_in = 0.0
    panel_b_left_in = panel_width_in - panel_a_b_overlap_in
    panel_cd_left_in = panel_b_left_in + panel_width_in + panel_b_cd_gap_in
    content_width_in = panel_cd_left_in + right_group_width_in
    master_width = content_width_in / (outer_right - outer_left)
    fig = plt.figure(figsize=(master_width, master_height), dpi=300)
    fig.patch.set_facecolor("white")

    def physical_slot(left_in: float, width_in: float):
        left = outer_left + left_in / master_width
        right = left + width_in / master_width
        grid = fig.add_gridspec(
            1,
            1,
            left=left,
            right=right,
            top=1.0 - vertical_margin,
            bottom=vertical_margin,
        )
        return grid[0, 0]

    panel_a_spec = physical_slot(panel_a_left_in, panel_width_in)
    panel_b_spec = physical_slot(panel_b_left_in, panel_width_in)
    panel_cd_spec = physical_slot(panel_cd_left_in, right_group_width_in)

    reference_positions = original_fig6a_axis_positions(c)
    axes_a = draw_panel_a_combined(fig, panel_a_spec, a, reference_positions)
    axes_b = draw_panel_b_combined(fig, panel_b_spec, c, reference_positions)

    ax_c, cax_c, ax_d, cax_d = draw_panel_cd_subfigure(
        fig,
        panel_cd_spec,
        b,
        d,
        primary_reference_positions=reference_positions,
    )

    panel_a_box = panel_a_spec.get_position(fig)
    panel_b_box = panel_b_spec.get_position(fig)
    right_group_box = panel_cd_spec.get_position(fig)
    panel_c_box = ax_c.get_position()
    panel_d_box = ax_d.get_position()
    panel_ab_top = axes_b[0].get_position().y1
    panel_ab_bottom = axes_b[-1].get_position().y0
    geometry = {
        "master_canvas_width_in": float(fig.get_figwidth()),
        "master_canvas_height_in": float(fig.get_figheight()),
        "panel_a_allocated_width_in": float(panel_a_box.width * fig.get_figwidth()),
        "panel_a_allocated_height_in": float(panel_a_box.height * fig.get_figheight()),
        "panel_a_b_intercolumn_gap_in": float((panel_b_box.x0 - panel_a_box.x1) * fig.get_figwidth()),
        "panel_b_cd_subfigure_gap_in": float((right_group_box.x0 - panel_b_box.x1) * fig.get_figwidth()),
        "panel_a_b_nominal_overlap_in": panel_a_b_overlap_in,
        "panel_b_cd_clearance_in": panel_b_cd_gap_in,
        "panel_b_allocated_width_in": float(panel_b_box.width * fig.get_figwidth()),
        "panel_b_allocated_height_in": float(panel_b_box.height * fig.get_figheight()),
        "panel_b_original_pdf_width_in": ORIGINAL_FIG6A_PDF_WIDTH_IN,
        "panel_b_original_pdf_height_in": ORIGINAL_FIG6A_PDF_HEIGHT_IN,
        "panel_b_original_canvas_width_in": ORIGINAL_FIG6A_CANVAS_WIDTH_IN,
        "panel_b_original_canvas_height_in": ORIGINAL_FIG6A_CANVAS_HEIGHT_IN,
        "panel_c_width_in": float(panel_c_box.width * fig.get_figwidth()),
        "panel_d_width_in": float(panel_d_box.width * fig.get_figwidth()),
        "panel_c_height_in": float(panel_c_box.height * fig.get_figheight()),
        "panel_d_height_in": float(panel_d_box.height * fig.get_figheight()),
        "panel_cd_shared_x": True,
        "panel_c_top_alignment_error_in": float(abs(panel_c_box.y1 - panel_ab_top) * fig.get_figheight()),
        "panel_d_bottom_alignment_error_in": float(abs(panel_d_box.y0 - panel_ab_bottom) * fig.get_figheight()),
    }
    OUTDIR.mkdir(parents=True, exist_ok=True)
    pdf = OUTDIR / "fig_3.pdf"
    png = OUTDIR / "fig_3.png"
    fig.savefig(pdf, bbox_inches="tight", pad_inches=0.025, facecolor="white")
    fig.savefig(png, dpi=300, bbox_inches="tight", pad_inches=0.025, facecolor="white")
    plt.close(fig)
    return pdf, png, geometry


def main() -> None:
    a = build_anatomy_data()
    b = build_decomposition_data()
    c = build_roofsize_data()
    d = build_building_use_data()
    save_source_data(a, b, c, d)

    OUTDIR.mkdir(parents=True, exist_ok=True)
    PANEL_OUTDIR.mkdir(parents=True, exist_ok=True)
    a_pdf, a_png = save_standalone_panel_a(a, c)
    b_pdf, b_png = save_standalone_panel_b(c)
    c_pdf, c_png = save_standalone_panel_c(b)
    d_pdf, d_png = save_standalone_panel_d(d)
    cd_pdf, cd_png = save_standalone_panel_cd(b, d)
    combined_pdf, combined_png, combined_geometry = build_combined_figure(a, b, c, d)

    checks = {
        "status": "combined_figure_ready",
        "primary_pairs": 6,
        "primary_cities": 12,
        "panel_a_rows": len(a),
        "panel_a_max_identity_error_pp": float(a["factor_identity_error_pp"].abs().max()),
        "panel_a_layout": "six pair-aligned facets sharing the original Fig. 6a row geometry",
        "panel_a_bar_scaling": "separate fixed factor scales with original values printed",
        "panel_a_pair_facets": len(PAIR_ORDER),
        "panel_a_metric_encoding": "equal-thickness bars with vertical hatch, diagonal hatch, and solid fill",
        "panel_a_bar_face": "city-coloured translucent fill with city-coloured outlines",
        "panel_a_background_track": "light-grey fill without outline",
        "panel_a_city_encoding": "pair-specific colors identified by in-facet horizontal bar swatches",
        "panel_a_x_axis_range_pct": [0, 100],
        "panel_a_ylabel": "Deployment component",
        "panel_a_ylabel_offset_in": 0.38,
        "panel_a_pair_legend_anchor_y": 1.20,
        "panel_a_pair_legend_alignment": "centred",
        "panel_a_metric_centres": [2.0, 1.18, 0.36],
        "panel_a_metric_centre_spacing": 0.82,
        "panel_a_city_bar_offsets": [0.17, -0.17],
        "panel_a_city_bar_height": 0.27,
        "panel_a_stripe_rendering": "explicit clipped vector lines, not renderer-dependent bar hatches",
        "panel_a_stripe_linewidth_pt": 0.95,
        "panel_a_metric_legend_location": "compact centred row immediately below the x-axis label",
        "panel_a_metric_legend_offset_from_last_axis": 0.050,
        "panel_a_panel_b_row_alignment": "exact shared normalized axes positions",
        "panel_a_panel_b_equal_canvas": True,
        "panel_b_rows": len(c),
        "panel_b_roof_size_bins_per_city": int(c.groupby("city").size().min()),
        "panel_b_low_count_bins": int(c["low_building_count_bin"].sum()),
        "panel_b_original_fig6a_aspect": ORIGINAL_FIG6A_ASPECT,
        "panel_b_original_canvas_aspect": ORIGINAL_FIG6A_CANVAS_HEIGHT_IN / ORIGINAL_FIG6A_CANVAS_WIDTH_IN,
        "panel_b_combined_aspect_constrained": False,
        "panel_b_combined_physical_size_preserved": True,
        "panel_b_original_style_function_reused": True,
        "panel_b_tight_layout_h_pad": 0.72,
        **combined_geometry,
        "panel_c_matrix_shape": [len(DECOMPOSITION_COLUMNS), len(PAIR_ORDER)],
        "panel_c_transposed": True,
        "panel_c_max_decomposition_error_pp": float(b["recalculated_error_pp"].abs().max()),
        "panel_d_cells": len(d),
        "panel_d_matrix_shape": [len(CLASS_LABELS), len(PAIR_ORDER)],
        "panel_d_transposed": True,
        "panel_d_hatched_cells": int(d["reliability_hatch"].sum()),
        "panel_d_policy_strips": 0,
        "panel_cd_colorbars": "separate vertical colorbars on the right",
        "panel_cd_height_ratio": [4, 6],
        "panel_cd_equal_width": True,
        "panel_cd_ytick_rotation_deg": 0.0,
        "panel_cd_width_fraction_of_previous": 0.75,
        "panel_cd_width_fraction_of_original": 0.50,
        "panel_cd_internal_font_increase_pt": 2.0,
        "panel_cd_xtick_rotation_deg": 30.0,
        "panel_cd_xtick_fontsize_pt": 9.6,
        "panel_d_xlabel": "City pairs",
        "panel_d_reliability_legend_location": "compact single row below the City pairs x label",
        "panel_cd_primary_vertical_alignment": "panel c top and panel d bottom aligned to the first and last panel a/b facet axes",
        "panel_top_subtitles": 2,
        "panel_label_style": "regular Myriad Pro glyphs normalized by visible letter height against the Fig. 2 reference",
        "panel_label_font_increase_pt": 6.0,
        "panel_label_increment_from_previous_pt": 4.0,
        "panel_d_comma_repair": "complete comma descender reused and scale-normalized from the matching Myriad Pro c glyph asset",
        "panel_label_visible_size_match": "a/c x-height and b/d ascender height calibrated to within approximately 1%",
        "panel_label_box_points_by_glyph": PANEL_LABEL_BOX_POINTS,
        "panel_label_alignment": "a and b aligned to left y-label anchors; c and d aligned to left y-tick-label region",
        "detroit_windsor_excluded": True,
        "svg_generated": False,
        "combined_pdf": str(combined_pdf.relative_to(ROOT)),
        "combined_png": str(combined_png.relative_to(ROOT)),
        "panel_a_pdf": str(a_pdf.relative_to(ROOT)),
        "panel_a_png": str(a_png.relative_to(ROOT)),
        "panel_b_pdf": str(b_pdf.relative_to(ROOT)),
        "panel_b_png": str(b_png.relative_to(ROOT)),
        "panel_c_pdf": str(c_pdf.relative_to(ROOT)),
        "panel_c_png": str(c_png.relative_to(ROOT)),
        "panel_d_pdf": str(d_pdf.relative_to(ROOT)),
        "panel_d_png": str(d_png.relative_to(ROOT)),
        "panel_cd_subfigure_pdf": str(cd_pdf.relative_to(ROOT)),
        "panel_cd_subfigure_png": str(cd_png.relative_to(ROOT)),
        "source_data": str((SOURCE_DIR / "Fig_3.csv").relative_to(ROOT)),
    }
    CHECKS.write_text(json.dumps(checks, indent=2) + "\n", encoding="utf-8")
    print(f"[ok] Wrote {combined_pdf}")
    print(f"[ok] Wrote {combined_png}")
    print(f"[ok] Wrote {a_pdf}")
    print(f"[ok] Wrote {b_pdf}")
    print(f"[ok] Wrote {c_pdf}")
    print(f"[ok] Wrote {d_pdf}")
    print(f"[ok] Wrote {cd_pdf}")
    print(f"[ok] Wrote {SOURCE_DIR / 'Fig_3.csv'}")
    print(json.dumps(checks, indent=2))


if __name__ == "__main__":
    main()

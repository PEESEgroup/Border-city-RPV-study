#!/usr/bin/env python3
"""Figure 5 layout refined.

Updates requested:
- remove explicit mpl rcParams settings for font.family / pdf.fonttype / ps.fonttype
- place city-pair names on panel a
- display numeric values inside panel a matrices
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import cast

import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.axes import Axes
from matplotlib.colors import Colormap
from matplotlib.colors import LinearSegmentedColormap, ListedColormap
from matplotlib.figure import Figure
from matplotlib.gridspec import SubplotSpec
from matplotlib.image import AxesImage
import numpy as np
import pandas as pd

ROOT = Path("REPOSITORY_ROOT/manuscript")

PAIR_ORDER = [
    ("vienna", "bratislava"),
    ("singapore", "johorbahru"),
    ("sandiego", "tijuana"),
    ("elpaso", "juarez"),
    ("hongkong", "shenzhen"),
    ("monaco", "nice"),
]

SHOW = {
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

CITY_ALIASES = {
    "vienna": "vienna",
    "bratislava": "bratislava",
    "singapore": "singapore",
    "johor bahru": "johorbahru",
    "johorbahru": "johorbahru",
    "johor-bahru": "johorbahru",
    "san diego": "sandiego",
    "sandiego": "sandiego",
    "tijuana": "tijuana",
    "el paso": "elpaso",
    "elpaso": "elpaso",
    "juarez": "juarez",
    "ciudad juarez": "juarez",
    "hong kong": "hongkong",
    "hongkong": "hongkong",
    "hong kong sar": "hongkong",
    "shenzhen": "shenzhen",
    "monaco": "monaco",
    "nice": "nice",
    "nice france": "nice",
    "nice, france": "nice",
}

COMPONENT_SOURCE_COLUMNS = {
    "A": "A: Export compensation friction",
    "B": "B: Export constraint friction",
    "C": "C: Settlement complexity friction",
    "D": "D: Policy uncertainty friction",
    "E": "E: Small-system approval friction",
    "F": "F: Building/planning approval friction",
    "G": "G: Grid study/fee friction",
    "H": "H: Professional credential friction",
}
INDEX_SOURCE_COLUMNS = {
    "Rev.": "Revenue Friction Index",
    "Adm.": "Administrative Friction Index",
    "Total": "Total Friction Index",
}
COLUMN_ORDER = ["A", "B", "C", "D", "E", "F", "G", "H", "Rev.", "Adm.", "Total"]

# Shared title geometry for the three top section headers.
# Keep these values identical so Revenue, Admin., and Leader titles/rules align.
SECTION_TITLE_Y = 1.07
SECTION_RULE_Y = 1.05
SECTION_RULE_X0 = 0.10
SECTION_RULE_X1 = 0.90
SECTION_TITLE_FONTSIZE = 10.0


def draw_section_header(ax: Axes, title: str) -> None:
    """Draw an aligned section title and divider rule above an axis."""
    ax.text(
        0.5,
        SECTION_TITLE_Y,
        title,
        transform=ax.transAxes,
        ha="center",
        va="bottom",
        fontsize=SECTION_TITLE_FONTSIZE,
        # fontweight="semibold",
        color="#1f1f1f",
        clip_on=False,
    )
    ax.plot(
        [SECTION_RULE_X0, SECTION_RULE_X1],
        [SECTION_RULE_Y, SECTION_RULE_Y],
        transform=ax.transAxes,
        color="#b9c0c7",
        lw=0.9,
        clip_on=False,
    )


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Draw optimized Fig. 5 policy-friction matrix.")
    p.add_argument("--csv", type=Path, default=ROOT / "data/Policy_frictions/border_city_pv_friction_matrix.csv")
    # Only output a single final composite panel.
    # Keep the historical flag name as an alias for backwards compatibility.
    p.add_argument(
        "--out-pdf",
        "--panel-a-composite-pdf",
        dest="out_pdf",
        type=Path,
        default=ROOT / "figures/panels/fig_5a.pdf",
        help="Output PDF for the final composite (matrix + leader table).",
    )
    p.add_argument(
        "--out-png",
        dest="out_png",
        type=Path,
        default=None,
        help="Optional output PNG path. Defaults to --out-pdf with a .png suffix.",
    )
    p.add_argument("--dpi", type=int, default=300)
    return p.parse_args()


def set_style() -> None:
    # Keep only general sizing; do not force font.family / pdf.fonttype / ps.fonttype.
    mpl.rcParams.update({
        "axes.titlesize": 10,
        "axes.labelsize": 9,
        "xtick.labelsize": 8.5,
        "ytick.labelsize": 8.5,
    })


def city_key(value: object) -> str:
    text = str(value).split(",", 1)[0].strip().lower().replace("_", " ").replace("-", " ")
    text = " ".join(text.split())
    return CITY_ALIASES.get(text, text.replace(" ", ""))


def pair_label(pair: tuple[str, str]) -> str:
    return f"{SHOW[pair[0]]}–{SHOW[pair[1]]}"


def require_columns(df: pd.DataFrame, path: Path, columns: list[str]) -> None:
    missing = [c for c in columns if c not in df.columns]
    if missing:
        raise ValueError(f"{path} is missing required columns: {missing}")


def load_friction_table(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    required = ["City", *COMPONENT_SOURCE_COLUMNS.values(), *INDEX_SOURCE_COLUMNS.values()]
    require_columns(df, path, required)

    work = df.copy()
    work["city_key"] = work["City"].map(city_key)
    indexed = work.drop_duplicates(subset=["city_key"], keep="first").set_index("city_key")

    ordered_keys = [k for pair in PAIR_ORDER for k in pair]
    missing = [k for k in ordered_keys if k not in indexed.index]
    if missing:
        print(f"[warning] Missing expected cities: {missing}")

    ordered = indexed.reindex(ordered_keys)
    out = pd.DataFrame(index=ordered_keys)
    for short, src in COMPONENT_SOURCE_COLUMNS.items():
        out[short] = pd.to_numeric(ordered[src], errors="coerce")
    for short, src in INDEX_SOURCE_COLUMNS.items():
        out[short] = pd.to_numeric(ordered[src], errors="coerce")

    out.index = [SHOW[k] for k in ordered_keys]
    return out[COLUMN_ORDER]


def build_pair_summary(friction_table: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for c1, c2 in PAIR_ORDER:
        city1, city2 = SHOW[c1], SHOW[c2]
        row: dict[str, object] = {"Pair": pair_label((c1, c2)), "City1": city1, "City2": city2}
        for label, col in [("Lower Rev.", "Rev."), ("Lower Adm.", "Adm."), ("Lower Total", "Total")]:
            v1 = pd.to_numeric(pd.Series([friction_table.at[city1, col]]), errors="coerce").iloc[0]
            v2 = pd.to_numeric(pd.Series([friction_table.at[city2, col]]), errors="coerce").iloc[0]
            if pd.isna(v1) or pd.isna(v2):
                code = "NA"
            elif np.isclose(float(v1), float(v2), rtol=1e-9, atol=1e-12):
                code = "Tie"
            else:
                code = "C1" if float(v1) < float(v2) else "C2"
            row[label] = code
        rows.append(row)
    return pd.DataFrame(rows)


def policy_cmap() -> LinearSegmentedColormap:
    return LinearSegmentedColormap.from_list(
        "policy_friction",
        ["#fbfaf8", "#e7edf4", "#c6d3e0", "#889bb1", "#44566b"],
    )


def add_pair_spacing(
    table: pd.DataFrame,
    gap_value=np.nan,
) -> tuple[np.ndarray, list[str], list[int], list[tuple[float, str]], list[str]]:
    """Return spaced matrix plus labeling helpers.

    Returns:
    - spaced matrix rows
    - city labels (with blanks for gap rows)
    - blank-row indices
    - pair-center (y, label) positions
    - pair label per row (pair name repeated for both city rows; blank for gap rows)
    """
    data_rows: list[np.ndarray] = []
    labels: list[str] = []
    blank_rows: list[int] = []
    pair_centers: list[tuple[float, str]] = []
    pair_row_labels: list[str] = []
    cursor = 0
    for pair_i, pair in enumerate(PAIR_ORDER):
        start = cursor
        for city_key_name in pair:
            city = SHOW[city_key_name]
            data_rows.append(table.loc[city].to_numpy(dtype=float))
            labels.append(city)
            pair_row_labels.append(pair_label(pair))
            cursor += 1
        center = start + 0.5
        pair_centers.append((center, pair_label(pair)))
        if pair_i < len(PAIR_ORDER) - 1:
            data_rows.append(np.full(table.shape[1], gap_value, dtype=float))
            labels.append("")
            pair_row_labels.append("")
            blank_rows.append(cursor)
            cursor += 1
    return np.vstack(data_rows), labels, blank_rows, pair_centers, pair_row_labels


def add_pair_rows(
    table: pd.DataFrame,
) -> tuple[np.ndarray, list[str], list[tuple[float, str]], list[str]]:
    """Return matrix rows without inserted blank spacer rows.

    Produces 12 rows (2 per pair) rather than 17.
    """
    data_rows: list[np.ndarray] = []
    labels: list[str] = []
    pair_centers: list[tuple[float, str]] = []
    pair_row_labels: list[str] = []
    cursor = 0
    for pair in PAIR_ORDER:
        start = cursor
        for city_key_name in pair:
            city = SHOW[city_key_name]
            data_rows.append(table.loc[city].to_numpy(dtype=float))
            labels.append(city)
            pair_row_labels.append(pair_label(pair))
            cursor += 1
        pair_centers.append((start + 0.5, pair_label(pair)))
    return np.vstack(data_rows), labels, pair_centers, pair_row_labels


def annotate_values(ax: Axes, matrix: np.ndarray, vmin: float, vmax: float) -> None:
    for i in range(matrix.shape[0]):
        for j in range(matrix.shape[1]):
            v = matrix[i, j]
            if not np.isfinite(v):
                continue
            txt = f"{int(v)}" if float(v).is_integer() else f"{v:.1f}"
            t = (v - vmin) / max(vmax - vmin, 1e-9)
            color = "#ffffff" if t >= 0.60 else "#222222"
            ax.text(j, i, txt, ha="center", va="center", fontsize=8.5, color=color)


def annotate_values_scaled(ax: Axes, matrix: np.ndarray, vmin: float, vmax: float, x_scale: float) -> None:
    for i in range(matrix.shape[0]):
        for j in range(matrix.shape[1]):
            v = matrix[i, j]
            if not np.isfinite(v):
                continue
            txt = f"{int(v)}" if float(v).is_integer() else f"{v:.1f}"
            t = (v - vmin) / max(vmax - vmin, 1e-9)
            color = "#ffffff" if t >= 0.60 else "#222222"
            ax.text(j * x_scale, i, txt, ha="center", va="center", fontsize=8.5, color=color)


def shrink_axis_height(ax: Axes, fraction: float = 0.25) -> None:
    """Shrink an axis vertically in figure coordinates.

    Useful for making horizontal colorbars visually thin without reworking
    the surrounding GridSpec layout.
    """
    fraction = float(max(0.05, min(1.0, fraction)))
    pos = ax.get_position()
    new_h = pos.height * fraction
    ax.set_position((pos.x0, pos.y0 + (pos.height - new_h) / 2.0, pos.width, new_h))


def draw_heatmap_block(
    ax: Axes,
    matrix: np.ndarray,
    columns: list[str],
    ylabels: list[str] | None,
    vmin: float,
    vmax: float,
    cmap: Colormap,
    header: str,
    show_ylabels: bool,
    blank_rows: list[int],
    show_values: bool = True,
    x_scale: float = 1.0,
    *,
    square_cells: bool = False,
) -> AxesImage:
    x_scale = float(max(0.25, x_scale))
    ncols = len(columns)
    nrows = matrix.shape[0]
    extent = (-0.5 * x_scale, (ncols - 0.5) * x_scale, nrows - 0.5, -0.5)
    aspect = "equal" if square_cells else "auto"
    im = ax.imshow(
        matrix,
        aspect=aspect,
        cmap=cmap,
        vmin=vmin,
        vmax=vmax,
        interpolation="none",
        extent=extent,
    )

    ax.set_xticks(np.arange(ncols) * x_scale)
    ax.set_xticklabels(columns, fontsize=9.5)
    ax.tick_params(axis="x", top=True, bottom=False, labeltop=True, labelbottom=False, length=0, pad=1)

    if ylabels is not None and show_ylabels:
        # Only label actual city rows; skip inserted blank spacer rows.
        tick_positions = [i for i, t in enumerate(ylabels) if t != ""]
        tick_labels = [t for t in ylabels if t != ""]
        ax.set_yticks(tick_positions)
        ax.set_yticklabels(tick_labels, fontsize=8.4)
        ax.tick_params(axis="y", length=0, pad=1, labelleft=True)
    else:
        # Important: when axes share a y-axis, do NOT reset y ticks/labels here,
        # otherwise it overrides the left axis' city labels.
        ax.tick_params(axis="y", length=0, pad=4, left=False, labelleft=False)

    ax.set_xticks(np.arange(-0.5, ncols, 1) * x_scale, minor=True)
    ax.set_yticks(np.arange(-0.5, matrix.shape[0], 1), minor=True)
    ax.grid(which="minor", color="white", linewidth=0.8)
    ax.tick_params(which="minor", bottom=False, left=False)

    for r in blank_rows:
        ax.axhline(r, color="white", lw=10, zorder=5)

    for spine in ax.spines.values():
        spine.set_visible(False)

    # Header (draw once; use shared geometry so all three titles/rules align).
    draw_section_header(ax, header)

    if show_values:
        if np.isclose(x_scale, 1.0):
            annotate_values(ax, matrix, vmin, vmax)
        else:
            annotate_values_scaled(ax, matrix, vmin, vmax, x_scale)

    return im


def plot_policy_matrix_heatmaps(
    fig: Figure,
    gs: SubplotSpec,
    friction_table: pd.DataFrame,
    *,
    x_scale: float = 2.0,
    square_cells: bool = False,
) -> dict[str, object]:
    rev_cols = ["A", "B", "C", "D"]
    adm_cols = ["E", "F", "G", "H"]
    sum_cols = ["Rev.", "Adm.", "Total"]

    spaced_table, ylabels, blank_rows, pair_centers, pair_row_labels = add_pair_spacing(friction_table)
    col_index = {c: i for i, c in enumerate(COLUMN_ORDER)}

    rev = spaced_table[:, [col_index[c] for c in rev_cols]]
    adm = spaced_table[:, [col_index[c] for c in adm_cols]]
    summ = spaced_table[:, [col_index[c] for c in sum_cols]]

    cmap = policy_cmap().copy()
    cmap.set_bad("white")

    vmax_components = 3
    vmax_indices = max(float(np.nanmax(summ)), 1.0)
    if square_cells:
        x_scale = 1.0
    else:
        x_scale = float(max(1.0, x_scale))  # larger -> visually narrower cells in x

    # Panel A has 3 blocks; y-axis tick labels show city names only.
    sub = gs.subgridspec(
        1, 3,
        width_ratios=[4.1, 4.1, 3.25],
        wspace=0.0,
        hspace=0.0,
    )

    ax_rev = fig.add_subplot(sub[0, 0])
    ax_adm = fig.add_subplot(sub[0, 1], sharey=ax_rev)
    ax_sum = fig.add_subplot(sub[0, 2], sharey=ax_rev)

    im_rev = draw_heatmap_block(
        ax_rev,
        rev,
        rev_cols,
        ylabels,
        0,
        vmax_components,
        cmap,
        "Revenue-side frictions",
        True,
        blank_rows,
        True,
        x_scale=x_scale,
        square_cells=square_cells,
    )
    draw_heatmap_block(
        ax_adm,
        adm,
        adm_cols,
        ylabels,
        0,
        vmax_components,
        cmap,
        "Administrative frictions",
        False,
        blank_rows,
        True,
        x_scale=x_scale,
        square_cells=square_cells,
    )
    im_sum = draw_heatmap_block(
        ax_sum,
        summ,
        sum_cols,
        ylabels,
        0,
        vmax_indices,
        cmap,
        "Summary indices",
        False,
        blank_rows,
        True,
        x_scale=x_scale,
        square_cells=square_cells,
    )

    plt.setp(ax_adm.get_yticklabels(), visible=False)
    plt.setp(ax_sum.get_yticklabels(), visible=False)

    # ax_rev.text(0.0, -0.165,
    #             "Higher score = greater friction", #; Rev., Adm. and Total are sums of component scores.
    #             transform=ax_rev.transAxes, ha="left", va="top", fontsize=8.6, color="#555555")

    return {
        "im_components": im_rev,
        "im_indices": im_sum,
        "blank_rows": blank_rows,
        "ylabels": ylabels,
        "pair_centers": pair_centers,
        "pair_row_labels": pair_row_labels,
        "ax_rev": ax_rev,
        "ax_adm": ax_adm,
        "ax_sum": ax_sum,
    }


def plot_policy_matrix_components_only(
    fig: Figure,
    gs: SubplotSpec,
    friction_table: pd.DataFrame,
    *,
    x_scale: float = 2.0,
    square_cells: bool = False,
    compact_rows: bool = False,
) -> dict[str, object]:
    """Panel A (components only): revenue + administrative blocks.

    Notes:
    - In the composite layout we prefer non-square cells (aspect='auto') to
      avoid large internal whitespace created by square-cell constraints.
    - Spacing between the two matrices is controlled via the SubGridSpec.
    """
    rev_cols = ["A", "B", "C", "D"]
    adm_cols = ["E", "F", "G", "H"]

    if compact_rows:
        spaced_table, ylabels, pair_centers, pair_row_labels = add_pair_rows(friction_table)
        blank_rows: list[int] = []
    else:
        spaced_table, ylabels, blank_rows, pair_centers, pair_row_labels = add_pair_spacing(friction_table)
    col_index = {c: i for i, c in enumerate(COLUMN_ORDER)}

    rev = spaced_table[:, [col_index[c] for c in rev_cols]]
    adm = spaced_table[:, [col_index[c] for c in adm_cols]]

    cmap = policy_cmap().copy()
    cmap.set_bad("white")

    vmax_components = 3

    # For non-square cells, larger x_scale => visually narrower cells.
    # This helps keep the composite compact without forcing equal aspect.
    x_scale = 1.0 if square_cells else float(max(1.0, x_scale))

    # Tighten the gap between matrices.
    sub = gs.subgridspec(1, 2, width_ratios=[1.0, 1.0], wspace=0.01, hspace=0.0)

    ax_rev = fig.add_subplot(sub[0, 0])
    ax_adm = fig.add_subplot(sub[0, 1], sharey=ax_rev)

    im_rev = draw_heatmap_block(
        ax_rev,
        rev,
        rev_cols,
        ylabels,
        0,
        vmax_components,
        cmap,
        "Revenue frictions",
        True,
        blank_rows,
        True,
        x_scale=x_scale,
        square_cells=square_cells,
    )
    draw_heatmap_block(
        ax_adm,
        adm,
        adm_cols,
        ylabels,
        0,
        vmax_components,
        cmap,
        "Admin. frictions",
        False,
        blank_rows,
        True,
        x_scale=x_scale,
        square_cells=square_cells,
    )

    plt.setp(ax_adm.get_yticklabels(), visible=False)

    ax_rev.text(0.0, -0.03,
                "Higher score = greater friction.",
                transform=ax_rev.transAxes, ha="left", va="top", fontsize=7.8, color="#555555")

    return {
        "im_components": im_rev,
        "blank_rows": blank_rows,
        "ylabels": ylabels,
        "pair_centers": pair_centers,
        "pair_row_labels": pair_row_labels,
        "ax_rev": ax_rev,
        "ax_adm": ax_adm,
    }


def plot_policy_matrix_colorbars(
    fig: Figure,
    gs: SubplotSpec,
    im_components: AxesImage,
    im_indices: AxesImage,
    *,
    ax_rev: Axes,
    ax_adm: Axes,
    ax_sum: Axes,
) -> None:
    """Draw thin horizontal colorbars under Panel A.

    Separated out so composite layouts can align Panel A/B rows in a shared top row.
    """
    # Use the actual matrix axes positions to align colorbar widths precisely.
    # We create an invisible container axis to reserve the GridSpec slot.
    container = fig.add_subplot(gs)
    container.axis("off")
    cpos = container.get_position()

    comp_left = ax_rev.get_position().x0
    comp_right = ax_adm.get_position().x1
    sum_left = ax_sum.get_position().x0
    sum_right = ax_sum.get_position().x1

    cax_comp = fig.add_axes((comp_left, cpos.y0, comp_right - comp_left, cpos.height))
    cax_sum = fig.add_axes((sum_left, cpos.y0, sum_right - sum_left, cpos.height))

    shrink_axis_height(cax_comp, 0.22)
    shrink_axis_height(cax_sum, 0.22)

    cb_comp = fig.colorbar(im_components, cax=cax_comp, orientation="horizontal")
    cb_comp.set_label("Component score (0–3)", fontsize=9.3, labelpad=3)
    cb_comp.set_ticks([0, 1, 2, 3])
    cb_comp.ax.tick_params(labelsize=8.5, length=2)

    cb_sum = fig.colorbar(im_indices, cax=cax_sum, orientation="horizontal")
    cb_sum.set_label("Index score", fontsize=9.3, labelpad=3)
    cb_sum.ax.tick_params(labelsize=8.5, length=2)


def _summary_to_codes(summary: pd.DataFrame) -> tuple[np.ndarray, np.ndarray]:
    cols = ["Lower Rev.", "Lower Adm.", "Lower Total"]
    code_map = {"C1": 0, "C2": 1, "Tie": 2, "NA": 3}
    labels = summary[cols].astype(str).to_numpy(dtype=object)
    values = summary[cols].astype(str).apply(lambda s: s.map(code_map).fillna(3)).to_numpy(dtype=float)
    return values, labels


def _build_aligned_summary(values6: np.ndarray, labels6: np.ndarray, blank_rows: list[int]) -> tuple[np.ndarray, np.ndarray]:
    """Expand the 6x3 pair summary to match Panel A's spaced rows.

    For each pair, repeat the same C1/C2/Tie row twice (one per city), then insert a blank row.
    This yields 17 rows (12 city rows + 5 gaps), matching Panel A.
    """
    expanded_vals: list[np.ndarray] = []
    expanded_labels: list[np.ndarray] = []
    for pair_i in range(values6.shape[0]):
        expanded_vals.append(values6[pair_i])
        expanded_vals.append(values6[pair_i])
        expanded_labels.append(labels6[pair_i])
        expanded_labels.append(labels6[pair_i])
        if pair_i < values6.shape[0] - 1:
            expanded_vals.append(np.full(values6.shape[1], np.nan, dtype=float))
            expanded_labels.append(np.array(["", "", ""], dtype=object))
    return np.vstack(expanded_vals), np.vstack(expanded_labels)


def _build_city_aligned_summary(values6: np.ndarray, labels6: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Expand the 6x3 pair summary to 12 rows (one per city row; no gaps)."""
    expanded_vals: list[np.ndarray] = []
    expanded_labels: list[np.ndarray] = []
    for pair_i in range(values6.shape[0]):
        expanded_vals.append(values6[pair_i])
        expanded_vals.append(values6[pair_i])
        expanded_labels.append(labels6[pair_i])
        expanded_labels.append(labels6[pair_i])
    return np.vstack(expanded_vals), np.vstack(expanded_labels)


def plot_lower_friction_summary(
    ax: Axes,
    summary: pd.DataFrame,
    *,
    aligned_blank_rows: list[int] | None = None,
    aligned_pair_centers: list[tuple[float, str]] | None = None,
    align_to_city_rows: bool = False,
    merge_pair_rows: bool = False,
    show_footer: bool = True,
    show_ylabels: bool = True,
) -> None:
    cols = ["Lower Rev.", "Lower Adm.", "Lower Total"]
    display_cols = ["Rev.", "Adm.", "Total"]

    values6, labels6 = _summary_to_codes(summary)
    if align_to_city_rows:
        values, labels = _build_city_aligned_summary(values6, labels6)
        row_labels = ["" for _ in range(values.shape[0])]
    elif aligned_blank_rows is not None:
        values, labels = _build_aligned_summary(values6, labels6, aligned_blank_rows)
        row_labels = ["" for _ in range(values.shape[0])]
    else:
        values, labels = values6, labels6
        row_labels = summary["Pair"].tolist()

    cmap = ListedColormap(["#dfe8f3", "#efe6db", "#ececec", "#ffffff"])
    cmap = cmap.copy()
    cmap.set_bad("#ffffff")
    x_scale = 1.85  # slightly narrower cells in x for tighter composite
    ncols = len(cols)
    nrows = values.shape[0]
    extent = (-0.5 * x_scale, (ncols - 0.5) * x_scale, nrows - 0.5, -0.5)
    ax.imshow(values, aspect="auto", cmap=cmap, vmin=-0.5, vmax=3.5, interpolation="none", extent=extent)

    ax.set_xticks(np.arange(len(cols)) * x_scale)
    ax.set_xticklabels(display_cols, fontsize=9.1, linespacing=0.9)
    ax.tick_params(axis="x", top=True, bottom=False, labeltop=True, labelbottom=False, length=0, pad=1)

    if show_ylabels and aligned_blank_rows is None and not align_to_city_rows:
        ax.set_yticks(np.arange(len(row_labels)))
        ax.set_yticklabels(row_labels, fontsize=9.1)
        ax.tick_params(axis="y", length=0, pad=5)
    elif show_ylabels and (aligned_blank_rows is not None or align_to_city_rows):
        # Aligned variants intentionally hide y labels; keep ticks for standalone use.
        ax.set_yticks(np.arange(len(row_labels)))
        ax.set_yticklabels([""] * len(row_labels))
        ax.tick_params(axis="y", length=0, pad=5)
    else:
        # When used alongside Panel A with a shared y-axis, do NOT reset shared ticks.
        ax.tick_params(axis="y", length=0, left=False, labelleft=False)

    # Grid styling.
    if aligned_blank_rows is not None and merge_pair_rows:
        # Only vertical separators; do not draw horizontal lines within a pair.
        for x in np.arange(0.5, len(cols), 1.0):
            ax.axvline(float(x) * x_scale, color="white", lw=1.0)
        # Add thick white bands at the inserted gap rows to match Panel A.
        for r in aligned_blank_rows:
            ax.axhline(float(r), color="white", lw=10, zorder=5)
    else:
        ax.set_xticks(np.arange(-0.5, len(cols), 1) * x_scale, minor=True)
        ax.set_yticks(np.arange(-0.5, len(row_labels), 1), minor=True)
        ax.grid(which="minor", color="white", linewidth=1.0)
        ax.tick_params(which="minor", bottom=False, left=False)

    for spine in ax.spines.values():
        spine.set_visible(False)

    if aligned_blank_rows is not None and merge_pair_rows:
        # Place one set of labels per pair at the pair centers.
        if aligned_pair_centers is None:
            raise ValueError("aligned_pair_centers must be provided when merge_pair_rows=True")
        for pair_i, (y, _) in enumerate(aligned_pair_centers):
            for j in range(values6.shape[1]):
                txt = str(labels6[pair_i, j])
                if txt == "":
                    continue
                fontstyle = "italic" if txt == "Tie" else "normal"
                ax.text(j * x_scale, y, txt, ha="center", va="center", fontsize=9.6,
                        color="#222222", fontstyle=fontstyle)
    else:
        for i in range(values.shape[0]):
            for j in range(values.shape[1]):
                txt = str(labels[i, j])
                if txt == "":
                    continue
                fontstyle = "italic" if txt == "Tie" else "normal"
                ax.text(j * x_scale, i, txt, ha="center", va="center", fontsize=9.6,
                        color="#222222", fontstyle=fontstyle)

    # Title for the leader panel (must show in both merged and unmerged modes).
    # Use the same geometry as the two heatmap section headers.
    draw_section_header(ax, "Lower-friction leader")

    if show_footer:
        ax.text(0.0, -0.15,
                "C1 = first-listed city\nC2 = second-listed city\nTie = equal friction score",
                transform=ax.transAxes, ha="left", va="top", fontsize=8.4, color="#555555")


def save_panel_a_composite(
    pdf_path: Path,
    friction: pd.DataFrame,
    summary: pd.DataFrame,
    dpi: int,
    *,
    png_path: Path | None = None,
) -> None:
    """Save Fig.5 panel A as a single square panel.

    Layout:
    - Left: friction component matrices (A–H), aligned to the same spaced city rows.
    - Right: within-pair lower-friction leader (Rev/Adm/Total) aligned to the same rows.
    """
    pdf_path.parent.mkdir(parents=True, exist_ok=True)
    if png_path is not None:
        png_path.parent.mkdir(parents=True, exist_ok=True)
    set_style()

    fig = plt.figure(figsize=(5.4, 5.4), dpi=dpi)
    gs = fig.add_gridspec(
        2, 2,
        height_ratios=[12.2, 1.10],
        width_ratios=[3.25, 1.55],
        wspace=0.01,
        hspace=0.06,
        left=0.155,
        right=0.985,
        top=0.915,
        bottom=0.07,
    )

    # Use spaced rows (blank separators between pairs) so the leader panel can merge
    # each pair's two city rows while keeping between-pair spacing.
    out = plot_policy_matrix_components_only(fig, gs[0, 0], friction, square_cells=False, compact_rows=False)

    ax_leader = fig.add_subplot(gs[0, 1])
    plot_lower_friction_summary(
        ax_leader,
        summary,
        aligned_blank_rows=cast(list[int], out["blank_rows"]),
        aligned_pair_centers=cast(list[tuple[float, str]], out["pair_centers"]),
        merge_pair_rows=True,
        show_footer=False,
        show_ylabels=False,
    )
    # Keep row alignment with Panel A without sharing the y-axis (avoids tick artifacts).
    ax_leader.set_ylim(cast(Axes, out["ax_rev"]).get_ylim())
    ax_leader.set_yticks([])
    ax_leader.tick_params(axis="y", left=False, labelleft=False)

    # Colorbar for component score.
    cbar_slot = fig.add_subplot(gs[1, 0])
    cbar_slot.axis("off")
    cpos = cbar_slot.get_position()
    comp_left = cast(Axes, out["ax_rev"]).get_position().x0
    comp_right = cast(Axes, out["ax_adm"]).get_position().x1
    cax_comp = fig.add_axes((comp_left, cpos.y0, 0.75 * (comp_right - comp_left), cpos.height))
    shrink_axis_height(cax_comp, 0.22)
    cb_comp = fig.colorbar(cast(AxesImage, out["im_components"]), cax=cax_comp, orientation="horizontal")
    cb_comp.set_label("Component score (0–3)", fontsize=9.0, labelpad=3)
    cb_comp.set_ticks([0, 1, 2, 3])
    cb_comp.ax.tick_params(labelsize=8.3, length=2)

    ax_footer = fig.add_subplot(gs[1, 1])
    ax_footer.axis("off")
    ax_footer.text(
        0.0, 0.60,
        "C1 = first-listed city\nC2 = second-listed city\nTie = equal",
        ha="left", va="center", fontsize=8.2, color="#555555",
    )

    # fig.text(
    #     0.07, 0.04,
    #     "Descriptive scoring summary of documented rules and requirements;\nnot a causal estimate of policy effects.",
    #     ha="left", va="bottom", fontsize=8.0, color="#555555",
    # )

    # Avoid bbox_inches="tight" so the PDF keeps the exact 6.3×6.3 in page size.
    # Avoid bbox_inches="tight" so the PDF keeps the exact 6.3×6.3 in page size.
    fig.savefig(pdf_path)
    if png_path is not None:
        fig.savefig(png_path)
    plt.close(fig)


def save_panel_a(path: Path, friction: pd.DataFrame, dpi: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    set_style()
    fig = plt.figure(figsize=(9.4, 5.3))
    gs = fig.add_gridspec(2, 1, height_ratios=[12.0, 1.25], left=0.07, right=0.98, top=0.86, bottom=0.18, hspace=0.12)
    out = plot_policy_matrix_heatmaps(fig, gs[0], friction, square_cells=True)
    plot_policy_matrix_colorbars(
        fig,
        gs[1],
        cast(AxesImage, out["im_components"]),
        cast(AxesImage, out["im_indices"]),
        ax_rev=cast(Axes, out["ax_rev"]),
        ax_adm=cast(Axes, out["ax_adm"]),
        ax_sum=cast(Axes, out["ax_sum"]),
    )
    fig.savefig(path, dpi=dpi, bbox_inches="tight")
    plt.close(fig)


def save_panel_b(path: Path, summary: pd.DataFrame, dpi: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    set_style()
    fig, ax = plt.subplots(figsize=(4.2, 3.5))
    plot_lower_friction_summary(ax, summary, show_footer=True, show_ylabels=True)
    fig.subplots_adjust(left=0.43, right=0.98, top=0.82, bottom=0.22)
    fig.savefig(path, dpi=dpi, bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    args = parse_args()
    friction = load_friction_table(args.csv)
    summary = build_pair_summary(friction)

    out_png = args.out_png if args.out_png is not None else Path(args.out_pdf).with_suffix(".png")
    save_panel_a_composite(args.out_pdf, friction, summary, int(args.dpi), png_path=out_png)
    print(f"Wrote final composite PDF: {args.out_pdf}")
    print(f"Wrote final composite PNG: {out_png}")


if __name__ == "__main__":
    main()

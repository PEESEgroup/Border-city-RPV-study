#!/usr/bin/env python3
"""Fig. 5b: weighted component-segment alignment matrix.

Sign conventions:
- Component advantage = second-city component score - first-city component score.
  Positive values mean the first-listed city has lower friction.
- PV advantage = first-city utilization - second-city utilization.
  Positive values mean the first-listed city has higher observed utilization.
- Signed alignment contribution = component advantage * segment-specific PV
  advantage in percentage points. Positive values mean lower friction and higher
  utilization occur on the same side of the border pair.

The factor-level Res./Non-res. weights preserve the original Fig. 5b logic:
for each component and segment, sum |component_advantage| only for city pairs
where component advantage and segment PV advantage have the same non-zero sign,
then normalize the two segment scores within component.

The visual grammar is deliberately a matrix: no ribbons, arrows, curved
connectors, central nodes, or width-as-link encodings are used.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.lines import Line2D
from matplotlib.patches import Patch, Rectangle


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
}

COMPONENT_COLUMNS = {
    "A": "A: Export compensation friction",
    "B": "B: Export constraint friction",
    "C": "C: Settlement complexity friction",
    "D": "D: Policy uncertainty friction",
    "E": "E: Small-system approval friction",
    "F": "F: Building/planning approval friction",
    "G": "G: Grid study/fee friction",
    "H": "H: Professional credential friction",
}
REVENUE_COMPONENTS = ["A", "B", "C", "D"]
ADMIN_COMPONENTS = ["E", "F", "G", "H"]
COMPONENTS = REVENUE_COMPONENTS + ADMIN_COMPONENTS

SEGMENTS = ["Residential", "Non-residential"]
PV_COLUMNS = {
    "Residential": "residential_pv_share_of_building",
    "Non-residential": "non_residential_pv_share_of_building",
}

PAIR_COLORS = {
    ("vienna", "bratislava"): "#c97c5d",
    ("singapore", "johorbahru"): "#d9a441",
    ("sandiego", "tijuana"): "#5aa469",
    ("elpaso", "juarez"): "#4f7cac",
    ("hongkong", "shenzhen"): "#b07bac",
    ("monaco", "nice"): "#d16d8a",
}
SEGMENT_COLORS = {
    "Residential": "#d4f4e5",
    "Non-residential": "#e8ddff",
}
GRID_COLOR = "#e7e7e7"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate Fig. 5b weighted alignment matrix.")
    parser.add_argument(
        "--policy-csv",
        type=Path,
        default=ROOT / "data/Policy_frictions/border_city_pv_friction_matrix.csv",
    )
    parser.add_argument(
        "--pair-area-csv",
        type=Path,
        default=ROOT / "data/Building_PVs/pair_area_summary.csv",
    )
    parser.add_argument("--out-pdf", type=Path, default=ROOT / "figures/panels/fig_5b.pdf")
    parser.add_argument("--out-png", type=Path, default=ROOT / "figures/panels/fig_5b.png")
    parser.add_argument("--out-svg", type=Path, default=ROOT / "figures/panels/fig_5b.svg")
    parser.add_argument(
        "--out-data-csv",
        type=Path,
        default=ROOT / "outputs/fig_panel_b_weighted_alignment_matrix_data.csv",
    )
    parser.add_argument(
        "--out-summary-csv",
        type=Path,
        default=ROOT / "outputs/fig_panel_b_weighted_alignment_factor_summary.csv",
    )
    parser.add_argument("--dpi", type=int, default=300)
    return parser.parse_args()


def set_style() -> None:
    mpl.rcParams.update(
        {
            "axes.titlesize": 9,
            "axes.labelsize": 8,
            "xtick.labelsize": 7,
            "ytick.labelsize": 8,
        }
    )


def city_key(value: object) -> str:
    text = str(value).split(",", 1)[0].strip().lower().replace("_", " ").replace("-", " ")
    text = " ".join(text.split())
    return CITY_ALIASES.get(text, text.replace(" ", ""))


def pair_label(pair: tuple[str, str]) -> str:
    return f"{SHOW[pair[0]]}–{SHOW[pair[1]]}"


def sign(value: float, tol: float = 1e-12) -> int:
    if not np.isfinite(value) or abs(value) <= tol:
        return 0
    return 1 if value > 0 else -1


def require_columns(df: pd.DataFrame, path: Path, columns: list[str]) -> None:
    missing = [column for column in columns if column not in df.columns]
    if missing:
        raise ValueError(f"{path} is missing required columns: {missing}")


def load_policy(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    require_columns(df, path, ["City", *COMPONENT_COLUMNS.values()])
    work = df.copy()
    work["city_key"] = work["City"].map(city_key)
    out = work.drop_duplicates(subset=["city_key"], keep="first").set_index("city_key")
    out = out[list(COMPONENT_COLUMNS.values())].rename(columns={v: k for k, v in COMPONENT_COLUMNS.items()})
    return out.apply(pd.to_numeric, errors="coerce")


def load_pv(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    require_columns(df, path, ["scope", "name", *PV_COLUMNS.values()])
    work = df.loc[df["scope"].astype(str).str.lower().eq("city")].copy()
    work["city_key"] = work["name"].map(city_key)
    out = work.drop_duplicates(subset=["city_key"], keep="first").set_index("city_key")
    return out[list(PV_COLUMNS.values())].rename(columns={v: k for k, v in PV_COLUMNS.items()}).apply(
        pd.to_numeric, errors="coerce"
    )


def build_pair_component_tables(policy: pd.DataFrame, pv: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    comp_rows = []
    pv_rows = []
    missing = []
    for first_city, second_city in PAIR_ORDER:
        for city in (first_city, second_city):
            if city not in policy.index:
                missing.append(f"{city} in policy table")
            if city not in pv.index:
                missing.append(f"{city} in PV table")
        if missing:
            continue

        comp_row = {
            "city_pair": pair_label((first_city, second_city)),
            "first_city": SHOW[first_city],
            "second_city": SHOW[second_city],
            "first_city_key": first_city,
            "second_city_key": second_city,
        }
        pv_row = comp_row.copy()
        for component in COMPONENTS:
            comp_row[component] = float(policy.at[second_city, component] - policy.at[first_city, component])
        for segment in SEGMENTS:
            pv_row[segment] = float(100.0 * (pv.at[first_city, segment] - pv.at[second_city, segment]))
        comp_rows.append(comp_row)
        pv_rows.append(pv_row)

    if missing:
        raise ValueError("Missing required city records: " + "; ".join(sorted(set(missing))))

    comp_adv = pd.DataFrame(comp_rows)
    pv_adv = pd.DataFrame(pv_rows)
    if len(comp_adv) != len(PAIR_ORDER) or len(pv_adv) != len(PAIR_ORDER):
        raise ValueError("Expected all six city pairs in component and PV tables.")
    if comp_adv["city_pair"].duplicated().any():
        raise ValueError("Duplicated city pairs in component table.")
    if comp_adv[COMPONENTS].isna().any().any() or pv_adv[SEGMENTS].isna().any().any():
        raise ValueError("Missing component or PV advantage values.")
    return comp_adv, pv_adv


def build_plot_tables(comp_adv: pd.DataFrame, pv_adv: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    merged = comp_adv.merge(
        pv_adv[["city_pair", "first_city", "second_city", *SEGMENTS]],
        on=["city_pair", "first_city", "second_city"],
        validate="one_to_one",
    )
    rows = []
    for component in COMPONENTS:
        group = "Revenue frictions" if component in REVENUE_COMPONENTS else "Administrative frictions"
        for segment in SEGMENTS:
            for _, row in merged.iterrows():
                component_advantage = float(row[component])
                pv_advantage = float(row[segment])
                contribution = component_advantage * pv_advantage
                rows.append(
                    {
                        "factor": component,
                        "factor_group": group,
                        "segment": segment,
                        "city_pair": row["city_pair"],
                        "first_city": row["first_city"],
                        "second_city": row["second_city"],
                        "component_advantage": component_advantage,
                        "pv_advantage": pv_advantage,
                        "signed_alignment_contribution": contribution,
                        "contribution_magnitude": abs(contribution),
                        "same_direction": sign(component_advantage) != 0
                        and sign(pv_advantage) != 0
                        and sign(component_advantage) == sign(pv_advantage),
                    }
                )

    detail = pd.DataFrame(rows)
    if detail.duplicated(subset=["factor", "segment", "city_pair"]).any():
        raise ValueError("Duplicated factor-segment-city_pair records.")
    if sorted(detail["factor"].unique()) != COMPONENTS:
        raise ValueError("Not all A-H factors are present.")
    if sorted(detail["segment"].unique()) != sorted(SEGMENTS):
        raise ValueError("Residential and non-residential segments are not both present.")

    summary_rows = []
    for component in COMPONENTS:
        group = "Revenue frictions" if component in REVENUE_COMPONENTS else "Administrative frictions"
        component_detail = detail.loc[detail["factor"].eq(component)].copy()
        scores = {}
        for segment in SEGMENTS:
            seg_detail = component_detail.loc[component_detail["segment"].eq(segment)]
            scores[segment] = float(
                seg_detail.loc[seg_detail["same_direction"], "component_advantage"].abs().sum()
            )
        total = scores["Residential"] + scores["Non-residential"]
        res_weight = scores["Residential"] / total if total > 0 else np.nan
        nonres_weight = scores["Non-residential"] / total if total > 0 else np.nan
        summary_rows.append(
            {
                "factor": component,
                "factor_group": group,
                "residential_total_alignment": scores["Residential"],
                "nonresidential_total_alignment": scores["Non-residential"],
                "residential_weight": res_weight,
                "nonresidential_weight": nonres_weight,
            }
        )

        detail.loc[detail["factor"].eq(component), "res_weight_for_factor"] = res_weight
        detail.loc[detail["factor"].eq(component), "nonres_weight_for_factor"] = nonres_weight

    summary = pd.DataFrame(summary_rows)
    if summary[["residential_weight", "nonresidential_weight"]].isna().any().any():
        raise ValueError("Could not compute factor-level Res./Non-res. weights.")
    return detail, summary


def x_from_contribution(value: float, scale: float) -> float:
    if scale <= 0:
        return 0.0
    return float(np.clip(value / scale, -1.0, 1.0))


def draw_cell_marks(
    ax: plt.Axes,
    detail: pd.DataFrame,
    factor: str,
    segment: str,
    x_center: float,
    y_center: float,
    scale: float,
    max_magnitude: float,
) -> None:
    cell_w = 1.52
    cell_h = 0.58
    left = x_center - cell_w / 2
    bottom = y_center - cell_h / 2
    ax.add_patch(
        Rectangle(
            (left, bottom),
            cell_w,
            cell_h,
            facecolor="#fbfbfb",
            edgecolor="#eeeeee",
            linewidth=0.5,
            zorder=0,
        )
    )
    ax.vlines(x_center, bottom + 0.05, bottom + cell_h - 0.05, color="#9a9a9a", lw=0.7, zorder=1)
    ax.hlines(y_center, left + 0.06, left + cell_w - 0.06, color="#eeeeee", lw=0.5, zorder=0)

    sub = detail.loc[detail["factor"].eq(factor) & detail["segment"].eq(segment)].copy()
    sub["pair_index"] = sub["city_pair"].map({pair_label(pair): idx for idx, pair in enumerate(PAIR_ORDER)})
    sub = sub.sort_values("pair_index")
    y_offsets = np.linspace(-0.20, 0.20, len(PAIR_ORDER))
    for offset, (_, row) in zip(y_offsets, sub.iterrows()):
        pair = PAIR_ORDER[int(row["pair_index"])]
        contribution = float(row["signed_alignment_contribution"])
        magnitude = float(row["contribution_magnitude"])
        x = x_center + x_from_contribution(contribution, scale) * (cell_w * 0.43)
        size = 14.0 + 44.0 * np.sqrt(magnitude / max_magnitude) if max_magnitude > 0 else 16.0
        ax.scatter(
            x,
            y_center + offset,
            s=size,
            color=PAIR_COLORS[pair],
            edgecolor="white",
            linewidth=0.35,
            alpha=0.92,
            zorder=3,
        )


def draw_weight_bar(ax: plt.Axes, row: pd.Series, x: float, y: float) -> None:
    width = 0.8
    height = 0.16
    res = float(row["residential_weight"])
    nonres = float(row["nonresidential_weight"])
    ax.add_patch(Rectangle((x, y - height / 2), width, height, facecolor="#f2f2f2", edgecolor="#d8d8d8", lw=0.5))
    ax.add_patch(Rectangle((x, y - height / 2), width * res, height, facecolor=SEGMENT_COLORS["Residential"], edgecolor="none"))
    ax.add_patch(
        Rectangle(
            (x + width * res, y - height / 2),
            width * nonres,
            height,
            facecolor=SEGMENT_COLORS["Non-residential"],
            edgecolor="none",
        )
    )
    ax.text(x + width + 0.14, y, f"{res:.0%} / {nonres:.0%}", ha="left", va="center", fontsize=7.1, color="#333333")


def draw_panel(detail: pd.DataFrame, summary: pd.DataFrame, out_pdf: Path, out_png: Path, out_svg: Path, dpi: int) -> None:
    set_style()
    fig, ax = plt.subplots(figsize=(4.82, 4.32), dpi=dpi)
    ax.set_axis_off()
    fig.patch.set_facecolor("white")

    x_group = 0.04
    x_factor = 0.34
    x_res = 1.55
    x_nonres = 3.35
    x_weight = 4.58
    y_map = {"A": 7.0, "B": 6.2, "C": 5.4, "D": 4.6, "E": 3.35, "F": 2.55, "G": 1.75, "H": 0.95}

    ax.set_xlim(-0.18, 6.12)
    ax.set_ylim(-0.65, 8.10)

    ax.text(x_factor, 7.60, "Factor", ha="center", va="bottom", fontsize=8.2)
    ax.text(x_res, 7.60, "Residential", ha="center", va="bottom", fontsize=8.3)
    ax.text(x_nonres, 7.60, "Non-residential", ha="center", va="bottom", fontsize=8.3)
    ax.text(x_weight + 0.76, 7.60, "Res. / Non-res. weight", ha="center", va="bottom", fontsize=7.7, linespacing=0.95)

    ax.text(
        x_group,
        5.80,
        "Revenue frictions",
        ha="center",
        va="center",
        rotation=90,
        fontsize=8.0,
        color="#555555",
        # fontweight="semibold",
    )
    ax.text(
        x_group,
        2.15,
        "Admin. frictions",
        ha="center",
        va="center",
        rotation=90,
        fontsize=8.0,
        color="#555555",
        # fontweight="semibold",
    )

    for y in [6.6, 5.8, 5.0, 4.05, 2.95, 2.15, 1.35, 0.55]:
        ax.hlines(y, 0.2, 5.82, color=GRID_COLOR, lw=0.45, zorder=0)
    # ax.hlines(4.18, 0.05, 5.82, color="#d5d5d5", lw=0.8, zorder=0)

    max_abs = float(detail["signed_alignment_contribution"].abs().max())
    scale = float(np.ceil(max_abs * 10.0) / 10.0) if max_abs > 0 else 1.0

    for component in COMPONENTS:
        y = y_map[component]
        ax.text(x_factor, y, component, ha="center", va="center", fontsize=8.4, color="#1f1f1f")
        draw_cell_marks(ax, detail, component, "Residential", x_res, y, scale, max_abs)
        draw_cell_marks(ax, detail, component, "Non-residential", x_nonres, y, scale, max_abs)
        draw_weight_bar(ax, summary.loc[summary["factor"].eq(component)].iloc[0], x_weight, y)

    # Direction cue under the two contribution columns.
    for x, label in [(x_res, "Residential"), (x_nonres, "Non-residential")]:
        y = 0.18
        ax.hlines(y, x - 0.48, x + 0.48, color="#9a9a9a", lw=0.7)
        ax.vlines(x, y - 0.06, y + 0.06, color="#777777", lw=0.8)
        ax.text(x - 0.40, y - 0.18, "opposite", ha="right", va="center", fontsize=6.3, color="#555555")
        ax.text(x + 0.40, y - 0.18, "aligned", ha="left", va="center", fontsize=6.3, color="#555555")

    pair_handles = [
        Line2D([0], [0], marker="o", linestyle="none", markerfacecolor=PAIR_COLORS[pair], markeredgecolor="white", markersize=5.5)
        for pair in PAIR_ORDER
    ]
    pair_labels = [pair_label(pair) for pair in PAIR_ORDER]
    leg1 = fig.legend(
        pair_handles,
        pair_labels,
        loc="lower center",
        bbox_to_anchor=(0.34, 0.095),
        ncol=2,
        frameon=False,
        fontsize=6.5,
        handletextpad=0.35,
        columnspacing=0.70,
    )
    fig.add_artist(leg1)

    size_handles = [
        Line2D([0], [0], marker="o", linestyle="none", color="#777777", markerfacecolor="#777777", markersize=size)
        for size in [3.2, 5.2, 7.2]
    ]
    leg2 = fig.legend(
        size_handles,
        ["smaller contribution", "medium contribution", "larger contribution"],
        loc="lower center",
        bbox_to_anchor=(0.80, 0.095),
        ncol=1,
        frameon=False,
        fontsize=6.4,
        handletextpad=0.45,
    )
    fig.add_artist(leg2)

    legend_y = 0.09
    ax.add_patch(
        Rectangle(
            (x_weight, legend_y),
            0.14,
            0.12,
            facecolor=SEGMENT_COLORS["Residential"],
            edgecolor="none",
            clip_on=False,
        )
    )
    ax.text(x_weight + 0.18, legend_y, "Residential", ha="left", va="center", fontsize=6.5, color="#333333")
    ax.add_patch(
        Rectangle(
            (x_weight + 0.96, legend_y ),
            0.14,
            0.12,
            facecolor=SEGMENT_COLORS["Non-residential"],
            edgecolor="none",
            clip_on=False,
        )
    )
    ax.text(x_weight + 1.14, legend_y, "Non-res.", ha="left", va="center", fontsize=6.5, color="#333333")

    fig.subplots_adjust(left=0.025, right=0.995, top=0.94, bottom=0.2)
    for path in (out_pdf, out_png, out_svg):
        path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_pdf, bbox_inches="tight")
    fig.savefig(out_png, bbox_inches="tight", dpi=dpi)
    fig.savefig(out_svg, bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    args = parse_args()
    policy = load_policy(args.policy_csv)
    pv = load_pv(args.pair_area_csv)
    comp_adv, pv_adv = build_pair_component_tables(policy, pv)
    detail, summary = build_plot_tables(comp_adv, pv_adv)

    for path in (args.out_data_csv, args.out_summary_csv):
        path.parent.mkdir(parents=True, exist_ok=True)
    detail.to_csv(args.out_data_csv, index=False)
    summary.to_csv(args.out_summary_csv, index=False)

    draw_panel(detail, summary, args.out_pdf, args.out_png, args.out_svg, args.dpi)

    for path in (args.out_pdf, args.out_png, args.out_svg, args.out_data_csv, args.out_summary_csv):
        if not path.exists():
            raise FileNotFoundError(f"Expected output was not created: {path}")

    print("Preserved original factor-level weight logic:")
    print("  score(component, segment) = sum |component_advantage| over same-sign city pairs")
    print("  weights are normalized between Residential and Non-residential within each component")
    print("Signed contribution table uses component_advantage * PV advantage in percentage points.")
    print(f"Wrote panel PDF: {args.out_pdf}")
    print(f"Wrote panel PNG: {args.out_png}")
    print(f"Wrote panel SVG: {args.out_svg}")
    print(f"Wrote detailed data CSV: {args.out_data_csv}")
    print(f"Wrote factor summary CSV: {args.out_summary_csv}")


if __name__ == "__main__":
    main()

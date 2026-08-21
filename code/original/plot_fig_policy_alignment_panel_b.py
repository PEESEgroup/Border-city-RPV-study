#!/usr/bin/env python3
"""Fig. 5b: descriptive signed alignment matrix.

This panel intentionally avoids arrows, ribbons, paths, line widths, and
Sankey/alluvial layout. It presents four pair-level descriptors in parallel:
revenue friction advantage, residential PV utilization advantage,
non-residential PV utilization advantage, and administrative friction advantage.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.lines import Line2D


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
    "san diego": "sandiego",
    "sandiego": "sandiego",
    "tijuana": "tijuana",
    "el paso": "elpaso",
    "elpaso": "elpaso",
    "juarez": "juarez",
    "ciudad juarez": "juarez",
    "hong kong": "hongkong",
    "hongkong": "hongkong",
    "shenzhen": "shenzhen",
    "monaco": "monaco",
    "nice": "nice",
}

PAIR_COLORS = {
    ("vienna", "bratislava"): "#c97c5d",
    ("singapore", "johorbahru"): "#d9a441",
    ("sandiego", "tijuana"): "#5aa469",
    ("elpaso", "juarez"): "#4f7cac",
    ("hongkong", "shenzhen"): "#b07bac",
    ("monaco", "nice"): "#d16d8a",
}

REVENUE_COL = "Revenue Friction Index"
ADMIN_COL = "Administrative Friction Index"
RES_PV_COL = "residential_pv_share_of_building"
NONRES_PV_COL = "non_residential_pv_share_of_building"

PLOT_COLUMNS = [
    ("revenue_advantage", "Revenue friction\nadvantage", "score gap", "friction"),
    ("res_pv_advantage", "Residential PV\nadvantage", "pp", "pv"),
    ("nonres_pv_advantage", "Non-residential PV\nadvantage", "pp", "pv"),
    ("admin_advantage", "Administrative friction\nadvantage", "score gap", "friction"),
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate redesigned Fig. 5b signed-alignment matrix.")
    parser.add_argument(
        "--policy-csv",
        type=Path,
        default=ROOT / "data/Policy_frictions/border_city_pv_friction_matrix.csv",
        help="City-level policy-friction matrix with revenue/admin index scores.",
    )
    parser.add_argument(
        "--pair-area-csv",
        type=Path,
        default=ROOT / "data/Building_PVs/pair_area_summary.csv",
        help="City-level PV utilization summary with residential and non-residential shares.",
    )
    parser.add_argument("--out-pdf", type=Path, default=ROOT / "figures/panels/fig_5b.pdf")
    parser.add_argument("--out-png", type=Path, default=ROOT / "figures/panels/fig_5b.png")
    parser.add_argument("--out-svg", type=Path, default=ROOT / "figures/panels/fig_5b.svg")
    parser.add_argument(
        "--out-csv",
        type=Path,
        default=ROOT / "outputs/fig_policy_alignment_panel_b_data.csv",
        help="Intermediate table used for plotting.",
    )
    parser.add_argument("--dpi", type=int, default=300)
    parser.add_argument(
        "--near-zero-pv-pp",
        type=float,
        default=0.10,
        help="PV utilization advantages with absolute value below this pp threshold are shown as near-zero.",
    )
    parser.add_argument(
        "--near-zero-friction",
        type=float,
        default=0.05,
        help="Friction advantages with absolute value below this score threshold are shown as near-zero.",
    )
    return parser.parse_args()


def set_style() -> None:
    mpl.rcParams.update(
        {
            "axes.titlesize": 9,
            "axes.labelsize": 8,
            "xtick.labelsize": 7.5,
            "ytick.labelsize": 8.2,
        }
    )


def city_key(value: object) -> str:
    text = str(value).split(",", 1)[0].strip().lower().replace("_", " ").replace("-", " ")
    text = " ".join(text.split())
    return CITY_ALIASES.get(text, text.replace(" ", ""))


def pair_label(pair: tuple[str, str]) -> str:
    return f"{SHOW[pair[0]]}–{SHOW[pair[1]]}"


def require_columns(df: pd.DataFrame, path: Path, columns: list[str]) -> None:
    missing = [column for column in columns if column not in df.columns]
    if missing:
        raise ValueError(f"{path} is missing required columns: {missing}")


def load_policy(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    require_columns(df, path, ["City", REVENUE_COL, ADMIN_COL])
    work = df.copy()
    work["city_key"] = work["City"].map(city_key)
    out = work.drop_duplicates(subset=["city_key"], keep="first").set_index("city_key")
    return out[[REVENUE_COL, ADMIN_COL]].apply(pd.to_numeric, errors="coerce")


def load_pv(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    require_columns(df, path, ["scope", "name", RES_PV_COL, NONRES_PV_COL])
    work = df.loc[df["scope"].astype(str).str.lower().eq("city")].copy()
    work["city_key"] = work["name"].map(city_key)
    out = work.drop_duplicates(subset=["city_key"], keep="first").set_index("city_key")
    return out[[RES_PV_COL, NONRES_PV_COL]].apply(pd.to_numeric, errors="coerce")


def build_alignment_table(policy: pd.DataFrame, pv: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    missing: list[str] = []

    for first_city, second_city in PAIR_ORDER:
        for city in (first_city, second_city):
            if city not in policy.index:
                missing.append(f"{city} in policy table")
            if city not in pv.index:
                missing.append(f"{city} in PV table")

        if missing:
            continue

        revenue_advantage = float(policy.at[second_city, REVENUE_COL] - policy.at[first_city, REVENUE_COL])
        admin_advantage = float(policy.at[second_city, ADMIN_COL] - policy.at[first_city, ADMIN_COL])
        res_pv_advantage = float(100.0 * (pv.at[first_city, RES_PV_COL] - pv.at[second_city, RES_PV_COL]))
        nonres_pv_advantage = float(100.0 * (pv.at[first_city, NONRES_PV_COL] - pv.at[second_city, NONRES_PV_COL]))

        rows.append(
            {
                "city_pair": pair_label((first_city, second_city)),
                "first_city": SHOW[first_city],
                "second_city": SHOW[second_city],
                "revenue_advantage": revenue_advantage,
                "res_pv_advantage": res_pv_advantage,
                "nonres_pv_advantage": nonres_pv_advantage,
                "admin_advantage": admin_advantage,
            }
        )

    if missing:
        raise ValueError("Missing required city records: " + "; ".join(sorted(set(missing))))

    table = pd.DataFrame(rows)
    if len(table) != len(PAIR_ORDER):
        raise ValueError(f"Expected {len(PAIR_ORDER)} city pairs, found {len(table)}.")
    if table["city_pair"].duplicated().any():
        duplicates = table.loc[table["city_pair"].duplicated(), "city_pair"].tolist()
        raise ValueError(f"Duplicated city pairs in alignment table: {duplicates}")
    if table[PLOT_COLUMNS[0][0]].isna().any() or table[[column[0] for column in PLOT_COLUMNS]].isna().any().any():
        missing_values = table.loc[table[[column[0] for column in PLOT_COLUMNS]].isna().any(axis=1), "city_pair"].tolist()
        raise ValueError(f"Missing plotting values for city pairs: {missing_values}")

    return table


def symmetric_limit(values: pd.Series, minimum: float) -> float:
    max_abs = float(np.nanmax(np.abs(values.to_numpy(dtype=float))))
    return max(minimum, float(np.ceil(max_abs * 1.15)))


def format_value(value: float, kind: str) -> str:
    if kind == "friction":
        return f"{value:+.0f}"
    return f"{value:+.1f}"


def draw_matrix(table: pd.DataFrame, out_pdf: Path, out_png: Path, out_svg: Path, dpi: int, near_zero_pv_pp: float, near_zero_friction: float) -> None:
    set_style()

    fig, axes = plt.subplots(
        nrows=1,
        ncols=4,
        figsize=(7.1, 3.95),
        dpi=dpi,
        sharey=True,
        gridspec_kw={"wspace": 0.14},
    )

    y_positions = np.arange(len(table))
    pair_colors = [PAIR_COLORS[pair] for pair in PAIR_ORDER]
    positive_color = "#3d6f5a"
    negative_color = "#7b4f78"
    zero_color = "#8c8c8c"

    friction_lim = symmetric_limit(table[["revenue_advantage", "admin_advantage"]].stack(), minimum=1.0)
    pv_lim = symmetric_limit(table[["res_pv_advantage", "nonres_pv_advantage"]].stack(), minimum=0.5)
    xlims = {"friction": friction_lim, "pv": pv_lim}
    near_zero = {"friction": near_zero_friction, "pv": near_zero_pv_pp}

    for ax, (column, title, unit, kind) in zip(axes, PLOT_COLUMNS):
        limit = xlims[kind]
        threshold = near_zero[kind]
        ax.axvline(0, color="#555555", lw=0.8, zorder=1)
        ax.set_xlim(-limit, limit)
        ax.set_ylim(-0.6, len(table) - 0.4)
        ax.invert_yaxis()
        ax.set_title(title, pad=8)
        ax.set_xlabel(unit)
        ax.grid(axis="x", color="#e1e1e1", linestyle="--", linewidth=0.55, zorder=0)
        ax.set_xticks([-limit, 0, limit])
        if kind == "pv":
            ax.set_xticklabels([f"-{limit:g}", "0", f"+{limit:g}"])
        else:
            ax.set_xticklabels([f"-{limit:g}", "0", f"+{limit:g}"])
        ax.tick_params(axis="y", length=0)
        ax.tick_params(axis="x", length=2.5, pad=2)
        for spine in ("top", "right", "left"):
            ax.spines[spine].set_visible(False)
        ax.spines["bottom"].set_color("#666666")
        ax.spines["bottom"].set_linewidth(0.7)

        for idx, row in table.iterrows():
            y = y_positions[idx]
            value = float(row[column])
            color = positive_color if value > 0 else negative_color
            if abs(value) <= threshold:
                ax.plot(0, y, marker="o", ms=4.2, color=zero_color, zorder=4)
            else:
                ax.barh(
                    y,
                    value,
                    height=0.36,
                    left=0,
                    color=color,
                    alpha=0.86,
                    edgecolor="none",
                    zorder=3,
                )
                ax.plot(value, y, marker="o", ms=4.0, color=color, markeredgecolor="white", markeredgewidth=0.45, zorder=4)

            text_x = np.sign(value) * min(abs(value) + 0.07 * limit, 0.92 * limit) if abs(value) > threshold else 0.07 * limit
            ha = "left" if text_x >= 0 else "right"
            ax.text(
                text_x,
                y,
                format_value(value, kind),
                ha=ha,
                va="center",
                fontsize=6.7,
                color="#2f2f2f",
                zorder=5,
            )

        # Subtle row guides.
        for y in y_positions:
            ax.axhline(y + 0.5, color="#eeeeee", lw=0.45, zorder=0)

    axes[0].set_yticks(y_positions)
    axes[0].set_yticklabels(table["city_pair"].tolist())
    for label, color in zip(axes[0].get_yticklabels(), pair_colors):
        label.set_color(color)
        label.set_fontsize(8.4)
    for ax in axes[1:]:
        ax.tick_params(labelleft=False)

    fig.suptitle(
        "Descriptive alignment of friction and PV-utilization advantages",
        fontsize=10.5,
        y=0.985,
    )
    note = (
        "Positive values indicate first-listed city advantage; negative values indicate second-listed city advantage. "
        "Friction advantages = lower scores; PV-utilization advantages = higher observed utilization."
    )
    fig.text(0.5, 0.035, note, ha="center", va="bottom", fontsize=7.2, color="#333333")

    handles = [
        Line2D([0], [0], color=positive_color, lw=5, label="First-listed city advantage"),
        Line2D([0], [0], color=negative_color, lw=5, label="Second-listed city advantage"),
        Line2D([0], [0], marker="o", color="none", markerfacecolor=zero_color, markeredgecolor=zero_color, label="Tie / near zero"),
    ]
    fig.legend(
        handles=handles,
        loc="lower center",
        bbox_to_anchor=(0.5, 0.075),
        ncol=3,
        frameon=False,
        fontsize=7.2,
        handlelength=1.5,
        columnspacing=1.25,
    )

    fig.subplots_adjust(left=0.22, right=0.985, top=0.82, bottom=0.24)
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
    table = build_alignment_table(policy, pv)
    args.out_csv.parent.mkdir(parents=True, exist_ok=True)
    table.to_csv(args.out_csv, index=False)

    print("Sign convention:")
    print("  revenue_advantage = second city revenue friction score - first city revenue friction score")
    print("  admin_advantage = second city administrative friction score - first city administrative friction score")
    print("  res_pv_advantage = first city residential PV utilization - second city residential PV utilization, in pp")
    print("  nonres_pv_advantage = first city non-residential PV utilization - second city non-residential PV utilization, in pp")
    print(f"Wrote plotting data: {args.out_csv}")

    draw_matrix(
        table=table,
        out_pdf=args.out_pdf,
        out_png=args.out_png,
        out_svg=args.out_svg,
        dpi=args.dpi,
        near_zero_pv_pp=args.near_zero_pv_pp,
        near_zero_friction=args.near_zero_friction,
    )
    print(f"Wrote panel PDF: {args.out_pdf}")
    print(f"Wrote panel PNG: {args.out_png}")
    print(f"Wrote panel SVG: {args.out_svg}")


if __name__ == "__main__":
    main()

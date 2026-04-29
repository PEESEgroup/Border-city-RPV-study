#!/usr/bin/env python3
"""Plot within-pair ranking scatter/bump charts for six border city pairs.

For each pair, each city is ranked only against its paired city (rank 1 or 2)
across six metrics:
- Income
- PV utilization
- Residential PV share
- Non-residential PV share
- IRR
- Policy friction
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

try:
    import matplotlib.pyplot as plt
except ModuleNotFoundError as exc:
    raise SystemExit(
        "matplotlib is required for plotting. Install it with: pip install matplotlib"
    ) from exc


PAIR_ORDER = [
    "Vienna–Bratislava",
    "Singapore–Johor Bahru",
    "San Diego–Tijuana",
    "El Paso–Juarez",
    "Hong Kong–Shenzhen",
    "Monaco–Nice",
]

SHOW_NAME_MAP = {
    "vienna": "Vienna",
    "bratislava": "Bratislava",
    "elpaso": "El Paso",
    "juarez": "Juarez",
    "sandiego": "San Diego",
    "tijuana": "Tijuana",
    "hongkong": "Hong Kong",
    "shenzhen": "Shenzhen",
    "singapore": "Singapore",
    "johorbahru": "Johor Bahru",
    "nice": "Nice",
    "monaco": "Monaco",
}

CITY_ALIASES = {
    "san diego": "sandiego",
    "tijuana": "tijuana",
    "el paso": "elpaso",
    "juarez": "juarez",
    "ciudad juarez": "juarez",
    "hong kong": "hongkong",
    "shenzhen": "shenzhen",
    "singapore": "singapore",
    "johor bahru": "johorbahru",
    "vienna": "vienna",
    "bratislava": "bratislava",
    "monaco": "monaco",
    "nice": "nice",
}

IRR_COLUMN = "IRR (%)"
TOTAL_FRICTION_COLUMN = "Total Friction Index"
INCOME_COLUMN = "Annual Income USD (net, Numbeo)"
PV_UTIL_COLUMN = "pv_share_of_building"
RES_PV_COLUMN = "residential_pv_share_of_building"
NONRES_PV_COLUMN = "non_residential_pv_share_of_building"

METRICS = [
    ("Income", INCOME_COLUMN, True),
    ("PV utilization", PV_UTIL_COLUMN, True),
    ("Res PV", RES_PV_COLUMN, True),
    ("Non-res PV", NONRES_PV_COLUMN, True),
    ("IRR", IRR_COLUMN, True),
    ("Policy friction", TOTAL_FRICTION_COLUMN, False),
]

PAIR_COLORS = {
    "Vienna–Bratislava": "#c97c5d",
    "Singapore–Johor Bahru": "#d9a441",
    "San Diego–Tijuana": "#5aa469",
    "Hong Kong–Shenzhen": "#b07bac",
    "Monaco–Nice": "#d16d8a",
    "El Paso–Juarez": "#4f7cac",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Create a within-pair ranking scatter/bump figure for six border pairs. "
            "Each city is ranked only against its paired city (rank 1 or 2)."
        )
    )
    parser.add_argument(
        "--friction-csv",
        default="Border/manuscript/data/Figure_2/border_city_pv_friction_matrix.csv",
        help="Directional border-city PV friction matrix CSV.",
    )
    parser.add_argument(
        "--economic-csv",
        default="Border/manuscript/data/Figure_2/economic_analysis_results.csv",
        help="City-level economic results CSV.",
    )
    parser.add_argument(
        "--income-csv",
        default="Border/manuscript/data/Figure_2/border_city_pairs_A_numbeo_2024.csv",
        help="City-level annual income CSV from Numbeo.",
    )
    parser.add_argument(
        "--pair-area-csv",
        default="Border/manuscript/data/Figure_2/pair_area_summary.csv",
        help="City-level PV/building share summary CSV.",
    )
    parser.add_argument(
        "--out-pdf",
        "--out-png",
        dest="out_pdf",
        default="Border/manuscript/figures/panels/within_pair_rank_scatter.pdf",
        help="Output ranking figure PDF path.",
    )
    parser.add_argument(
        "--out-csv",
        default="Border/manuscript/data/Figure_2/within_pair_rank_table.csv",
        help="Output CSV path for the 12-row rank table.",
    )
    return parser.parse_args()


def _city_key(value: str) -> str:
    normalized = " ".join(str(value).strip().lower().replace("_", " ").replace("-", " ").split())
    return CITY_ALIASES.get(normalized, normalized.replace(" ", ""))


def _income_city_key(value: str) -> str:
    city_only = str(value).split(",", 1)[0].strip()
    return _city_key(city_only)


def _pair_city_order(pair_name: str) -> list[str]:
    return [_city_key(part) for part in pair_name.split("–")]


def _display_city_name(city_key: str) -> str:
    return SHOW_NAME_MAP.get(city_key, city_key.title())


def _resolve_path(primary: str, fallback: str | None = None) -> Path:
    p = Path(primary)
    if p.exists():
        return p
    if fallback:
        fb = Path(fallback)
        if fb.exists():
            return fb
    return p


def _two_city_ranks(v1: float, v2: float, higher_is_better: bool) -> tuple[float, float]:
    # With two-city ranking, ties receive 1.5/1.5 for a neutral middle rank.
    if np.isclose(v1, v2, rtol=1e-12, atol=1e-12):
        return 1.5, 1.5

    if higher_is_better:
        return (1.0, 2.0) if v1 > v2 else (2.0, 1.0)
    return (1.0, 2.0) if v1 < v2 else (2.0, 1.0)


def build_rank_table(
    friction_df: pd.DataFrame,
    economic_df: pd.DataFrame,
    income_df: pd.DataFrame,
    pair_area_df: pd.DataFrame,
) -> pd.DataFrame:
    friction = friction_df.copy()
    friction["city_key"] = friction["City"].map(_city_key)

    economic = economic_df.copy()
    economic["city_key"] = economic["City"].map(_city_key)
    economic = economic.set_index("city_key")

    income = income_df.copy()
    income["city_key"] = income["City"].map(_income_city_key)
    income = income[["city_key", INCOME_COLUMN]].dropna(subset=["city_key"])
    income = income.drop_duplicates(subset=["city_key"], keep="first").set_index("city_key")

    city_pv = pair_area_df[pair_area_df["scope"] == "city"].copy()
    city_pv["city_key"] = city_pv["name"].map(_city_key)
    city_pv = city_pv.set_index("city_key")

    rows: list[dict[str, float | str]] = []

    for pair_name in PAIR_ORDER:
        group = friction.loc[friction["Pair"] == pair_name].copy()
        if group.empty:
            raise ValueError(f"No friction rows found for pair: {pair_name}")

        city_order = _pair_city_order(pair_name)
        group["city_order"] = group["city_key"].map({city_order[0]: 0, city_order[1]: 1})
        group = group.sort_values(["city_order", "city_key"], kind="stable").reset_index(drop=True)
        if len(group) != 2:
            raise ValueError(f"Expected exactly 2 rows for {pair_name}, found {len(group)}")

        c1 = str(group.loc[0, "city_key"])
        c2 = str(group.loc[1, "city_key"])

        if c1 not in economic.index or c2 not in economic.index:
            raise ValueError(f"Missing economic rows for {pair_name}: {c1}, {c2}")
        if c1 not in income.index or c2 not in income.index:
            raise ValueError(f"Missing income rows for {pair_name}: {c1}, {c2}")
        if c1 not in city_pv.index or c2 not in city_pv.index:
            raise ValueError(f"Missing PV rows for {pair_name}: {c1}, {c2}")

        metric_values = {
            "Income": (float(income.at[c1, INCOME_COLUMN]), float(income.at[c2, INCOME_COLUMN])),
            "PV utilization": (float(city_pv.at[c1, PV_UTIL_COLUMN]), float(city_pv.at[c2, PV_UTIL_COLUMN])),
            "Res PV": (float(city_pv.at[c1, RES_PV_COLUMN]), float(city_pv.at[c2, RES_PV_COLUMN])),
            "Non-res PV": (
                float(city_pv.at[c1, NONRES_PV_COLUMN]),
                float(city_pv.at[c2, NONRES_PV_COLUMN]),
            ),
            "IRR": (float(economic.at[c1, IRR_COLUMN]), float(economic.at[c2, IRR_COLUMN])),
            "Policy friction": (
                float(group.loc[0, TOTAL_FRICTION_COLUMN]),
                float(group.loc[1, TOTAL_FRICTION_COLUMN]),
            ),
        }

        rank_maps: dict[str, tuple[float, float]] = {}
        for metric_name, _col, higher_is_better in METRICS:
            v1, v2 = metric_values[metric_name]
            rank_maps[metric_name] = _two_city_ranks(v1, v2, higher_is_better)

        rows.append(
            {
                "pair": pair_name,
                "city": _display_city_name(c1),
                "city_key": c1,
                "within_pair_rank_income": rank_maps["Income"][0],
                "within_pair_rank_pv_utilization": rank_maps["PV utilization"][0],
                "within_pair_rank_res_pv": rank_maps["Res PV"][0],
                "within_pair_rank_nonres_pv": rank_maps["Non-res PV"][0],
                "within_pair_rank_irr": rank_maps["IRR"][0],
                "within_pair_rank_policy_friction": rank_maps["Policy friction"][0],
            }
        )
        rows.append(
            {
                "pair": pair_name,
                "city": _display_city_name(c2),
                "city_key": c2,
                "within_pair_rank_income": rank_maps["Income"][1],
                "within_pair_rank_pv_utilization": rank_maps["PV utilization"][1],
                "within_pair_rank_res_pv": rank_maps["Res PV"][1],
                "within_pair_rank_nonres_pv": rank_maps["Non-res PV"][1],
                "within_pair_rank_irr": rank_maps["IRR"][1],
                "within_pair_rank_policy_friction": rank_maps["Policy friction"][1],
            }
        )

    return pd.DataFrame(rows)


def plot_within_pair_rank_scatter(rank_df: pd.DataFrame, out_pdf: Path) -> None:
    metric_cols = [
        "within_pair_rank_income",
        "within_pair_rank_pv_utilization",
        "within_pair_rank_res_pv",
        "within_pair_rank_nonres_pv",
        "within_pair_rank_irr",
        "within_pair_rank_policy_friction",
    ]
    metric_labels = [
        "Income",
        "PV utilization",
        "Res PV",
        "Non-res PV",
        "IRR",
        "Policy friction",
    ]
    x = np.arange(len(metric_cols), dtype=float)

    # Match the rendered height of the paired utilization bar chart for easier side-by-side use.
    fig_height = max(11.75, 1.57 * len(PAIR_ORDER) + 2.33)
    fig, axes = plt.subplots(
        nrows=len(PAIR_ORDER),
        ncols=1,
        figsize=(12 / 1.335, fig_height / 1.1),
        sharex=True,
        dpi=220,
    )
    background_color = "#f6f1e8"
    fig.patch.set_facecolor(background_color)
    if len(PAIR_ORDER) == 1:
        axes = [axes]

    for idx, pair_name in enumerate(PAIR_ORDER):
        ax = axes[idx]
        ax.set_facecolor(background_color)
        sub = rank_df[rank_df["pair"] == pair_name].copy()
        if len(sub) != 2:
            raise ValueError(f"Expected 2 city rows for {pair_name}, got {len(sub)}")

        pair_color = PAIR_COLORS.get(pair_name, "#4a4a4a")

        for line_i, (_row_idx, row) in enumerate(sub.iterrows()):
            y = row[metric_cols].to_numpy(dtype=float)
            linestyle = "-" if line_i == 0 else "--"
            ax.plot(
                x,
                y,
                color=pair_color,
                linewidth=2.3,
                linestyle=linestyle,
                marker="o",
                markersize=7.2,
                markerfacecolor="white",
                markeredgewidth=1.7,
                alpha=0.95,
            )

            left_city = str(row["city"])
            ax.text(
                x[0] - 0.22,
                y[0],
                left_city,
                ha="right",
                va="center",
                fontsize=12,
                color="#4e463d",
                fontweight="medium",
            )

        # Compress the visual distance between rank-1 and rank-2 rows within each pair.
        ax.set_ylim(2.5, 0.5)
        ax.set_yticks([1.0, 2.0])
        ax.set_yticklabels([])
        ax.tick_params(axis="y", length=0)
        ax.grid(axis="y", color="#d7d1c6", linewidth=0.95, alpha=0.95)
        ax.grid(axis="x", linestyle="--", color="#8f8a80", linewidth=0.8, alpha=0.24)
        ax.set_title(pair_name, loc="center", fontsize=12, fontweight="bold", color="#4e463d", pad=-2)

        for spine in ax.spines.values():
            spine.set_visible(False)

    for ax in axes[:-1]:
        ax.set_xticks([])
        ax.set_xticklabels([])
        ax.tick_params(axis="x", length=0, labelbottom=False)

    axes[-1].set_xticks(x)
    axes[-1].set_xticklabels(metric_labels, fontsize=13, rotation=0, ha="center")
    axes[-1].tick_params(axis="x", pad=6, length=0, labelbottom=True)

    # fig.suptitle("Within-Pair City Ranking Across PV/Economic/Friction Metrics", fontsize=18, fontweight="bold", y=0.997)
    # fig.text(
    #     0.995,
    #     0.5,
    #     "Rank 1 = better within each city pair\n(higher is better for PV/IRR, lower is better for frictions)",
    #     rotation=90,
    #     va="center",
    #     ha="right",
    #     fontsize=11,
    #     color="#4e463d",
    # )

    # Increase inter-pair separation while keeping within-pair city lines tight.
    # fig.tight_layout(rect=(0.08, 0.04, 0.97, 0.985), h_pad=2)
    out_pdf.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_pdf, bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    args = parse_args()

    friction_csv = _resolve_path(args.friction_csv)
    economic_csv = _resolve_path(args.economic_csv)
    income_csv = _resolve_path(args.income_csv)
    pair_area_csv = _resolve_path(
        args.pair_area_csv,
        fallback="Border/manuscript/data/Figure_2/pair_area_summary.csv",
    )

    friction_df = pd.read_csv(friction_csv)
    economic_df = pd.read_csv(economic_csv)
    income_df = pd.read_csv(income_csv)
    pair_area_df = pd.read_csv(pair_area_csv)

    rank_df = build_rank_table(
        friction_df=friction_df,
        economic_df=economic_df,
        income_df=income_df,
        pair_area_df=pair_area_df,
    )

    out_pdf = Path(args.out_pdf)
    out_csv = Path(args.out_csv)

    plot_within_pair_rank_scatter(rank_df, out_pdf)
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    rank_df.to_csv(out_csv, index=False)

    print(f"Wrote figure: {out_pdf}")
    print(f"Wrote table: {out_csv}")


if __name__ == "__main__":
    main()

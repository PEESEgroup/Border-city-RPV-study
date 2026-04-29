#!/usr/bin/env python3
"""Plot PV utilization gap scatter with three x-axis factors in a row.

y-axis: PV utilization gap
x-axes: Year-1 Savings gap, IRR gap, Total Friction Index gap
First subplot is 1.5x wider than the other two.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

try:
    import matplotlib.pyplot as plt
    from matplotlib.ticker import FuncFormatter
except ModuleNotFoundError as exc:
    raise SystemExit(
        "matplotlib is required for plotting. Install it with: pip install matplotlib"
    ) from exc


TARGET_PAIR_ORDER = [
    "Hong Kong–Shenzhen",
    "Monaco–Nice",
]

ALL_PAIR_ORDER = [
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

X_FACTORS = [
    "Annual Income USD (net, Numbeo)",
    "IRR (%)",
    "Total Friction Index",
]
Y_FACTOR = "PV Utilization Gap"
PV_COLUMN = "pv_share_of_building"
INCOME_COLUMN = "Annual Income USD (net, Numbeo)"

# Pair palette for all border-city pairs shown in this scatter.
PAIR_COLORS = {
    "vienna-bratislava": "#6c8a3b",
    "bratislava-vienna": "#6c8a3b",
    "singapore-johorbahru": "#d29a2e",
    "johorbahru-singapore": "#d29a2e",
    "sandiego-tijuana": "#2f7f6f",
    "tijuana-sandiego": "#2f7f6f",
    "elpaso-juarez": "#4f7cac",
    "juarez-elpaso": "#4f7cac",
    "hongkong-shenzhen": "#b07bac",
    "shenzhen-hongkong": "#b07bac",
    "monaco-nice": "#d16d8a",
    "nice-monaco": "#d16d8a",
}
OTHER_PAIR_COLOR = "#b8b8b8"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Plot PV utilization gap scatter with three x-axis factors "
            "(Annual Income, IRR, Total Friction Index) in a row."
        )
    )
    parser.add_argument(
        "--friction-csv",
        default="Border/factors/border_city_pv_friction_matrix.csv",
        help="Directional border-city PV friction matrix CSV.",
    )
    parser.add_argument(
        "--economic-csv",
        default="Border/factors/economic_analysis_results.csv",
        help="City-level economic analysis results CSV.",
    )
    parser.add_argument(
        "--income-csv",
        default="Border/factors/border_city_pairs_A_numbeo_2024.csv",
        help="City income data CSV from Numbeo.",
    )
    parser.add_argument(
        "--pair-area-csv",
        default="Border/prediction/pair_area_summary.csv",
        help="PV/building area summary with city-level PV adoption metrics.",
    )
    parser.add_argument(
        "--base-class-csv",
        default="Border/prediction/pair_base_class_ratio_summary.csv",
        help=(
            "Per-base-class summary CSV used to derive matched all-building "
            "PV utilization, consistent with infer_src/plot_city_rpv_utilization_within_pair_hbar.py."
        ),
    )
    parser.add_argument(
        "--gap-mode",
        default="signed",
        choices=["abs", "signed"],
        help="Use absolute gaps or signed gaps.",
    )
    parser.add_argument(
        "--out-png",
        default="Border/prediction/pv_gap_three_factors_scatter.png",
        help="Output image path.",
    )
    parser.add_argument(
        "--out-csv",
        default="",
        help=(
            "Output CSV path for plotted data. "
            "Default: same as --out-png but with .csv extension."
        ),
    )
    parser.add_argument(
        "--out-pdf",
        default="",
        help=(
            "Output PDF path for the same figure. "
            "Default: same as --out-png but with .pdf extension."
        ),
    )
    parser.add_argument(
        "--title",
        default="",
        help="Plot title.",
    )
    return parser.parse_args()


def _city_key(value: str) -> str:
    normalized = " ".join(str(value).strip().lower().replace("_", " ").replace("-", " ").split())
    return CITY_ALIASES.get(normalized, normalized.replace(" ", ""))


def _gap(a: float, b: float, mode: str) -> float:
    return abs(a - b) if mode == "abs" else (a - b)


def _pair_city_order(pair_name: str) -> list[str]:
    return [_city_key(part) for part in pair_name.split("–")]


def _pair_slug(city1: str, city2: str) -> str:
    return f"{city1}-{city2}"


def _pair_label(city1: str, city2: str) -> str:
    return f"{SHOW_NAME_MAP.get(city1, city1.title())} - {SHOW_NAME_MAP.get(city2, city2.title())}"


def _pair_color(city1: str, city2: str) -> str:
    return PAIR_COLORS.get(f"{city1}-{city2}", OTHER_PAIR_COLOR)


def _build_sizes(values: pd.Series, min_size: float = 120.0, max_size: float = 950.0) -> np.ndarray:
    arr = values.astype(float).to_numpy()
    if len(arr) == 0:
        return np.array([], dtype=float)
    vmin = float(np.nanmin(arr))
    vmax = float(np.nanmax(arr))
    if np.isclose(vmin, vmax):
        return np.full_like(arr, (min_size + max_size) / 2.0, dtype=float)
    scaled = (arr - vmin) / (vmax - vmin)
    return min_size + scaled * (max_size - min_size)


def _map_size(
    value: float, vmin: float, vmax: float, min_size: float = 120.0, max_size: float = 950.0
) -> float:
    if np.isclose(vmin, vmax):
        return (min_size + max_size) / 2.0
    scaled = (float(value) - vmin) / (vmax - vmin)
    return min_size + scaled * (max_size - min_size)


def load_city_matched_all_shares(base_class_csv: Path) -> dict[str, float]:
    base_df = pd.read_csv(base_class_csv)
    base_df = base_df.copy()
    base_df["scope"] = base_df["scope"].astype(str).str.strip().str.lower()
    city_df = base_df[base_df["scope"] == "city"].copy()
    if city_df.empty:
        return {}

    city_df["city_key"] = city_df["name"].map(_city_key)
    city_df["building_area_m2"] = pd.to_numeric(city_df["building_area_m2"], errors="coerce").fillna(0.0)
    city_df["pv_area_m2"] = pd.to_numeric(city_df["pv_area_m2"], errors="coerce").fillna(0.0)

    agg = (
        city_df.groupby("city_key", as_index=False)[["building_area_m2", "pv_area_m2"]]
        .sum(min_count=1)
        .fillna(0.0)
    )

    shares: dict[str, float] = {}
    for row in agg.itertuples(index=False):
        city_key = str(row.city_key)
        building_area = float(row.building_area_m2)
        pv_area = float(row.pv_area_m2)
        shares[city_key] = (pv_area / building_area) if building_area > 0 else 0.0
    return shares


def build_gap_table(
    friction_df: pd.DataFrame,
    economic_df: pd.DataFrame,
    income_df: pd.DataFrame,
    pair_area_df: pd.DataFrame,
    matched_all_shares: dict[str, float],
    gap_mode: str,
    pair_order: list[str],
) -> pd.DataFrame:
    friction = friction_df.copy()
    friction["city_key"] = friction["City"].map(_city_key)

    economic = economic_df.copy()
    economic["city_key"] = economic["City"].map(_city_key)
    economic = economic.set_index("city_key")

    income = income_df.copy()
    # Extract city name from "City, Country" format
    income["city_name"] = income["City"].str.split(",").str[0].str.strip()
    income["city_key"] = income["city_name"].map(_city_key)
    income = income.set_index("city_key")

    city_pv = pair_area_df[pair_area_df["scope"] == "city"].copy()
    city_pv["city_key"] = city_pv["name"].map(_city_key)
    if matched_all_shares:
        city_pv[PV_COLUMN] = city_pv.apply(
            lambda r: matched_all_shares.get(str(r["city_key"]), float(r[PV_COLUMN])),
            axis=1,
        )
    city_pv = city_pv.set_index("city_key")

    if PV_COLUMN not in city_pv.columns:
        raise ValueError(f"Missing PV column in pair-area CSV: {PV_COLUMN}")

    rows = []
    for pair_name in pair_order:
        group = friction.loc[friction["Pair"] == pair_name].copy()
        if group.empty:
            raise ValueError(f"No friction rows found for pair: {pair_name}")

        city_order = _pair_city_order(pair_name)
        group["city_order"] = group["city_key"].map({city_order[0]: 0, city_order[1]: 1})
        group = group.sort_values(["city_order", "city_key"], kind="stable").reset_index(drop=True)
        if len(group) != 2:
            raise ValueError(f"Expected exactly 2 directional rows for {pair_name}, found {len(group)}")

        city1 = str(group.loc[0, "city_key"])
        city2 = str(group.loc[1, "city_key"])
        if city1 not in economic.index or city2 not in economic.index:
            raise ValueError(f"Missing economic row for pair {pair_name}: {city1}, {city2}")
        if city1 not in city_pv.index or city2 not in city_pv.index:
            raise ValueError(f"Missing PV row for pair {pair_name}: {city1}, {city2}")
        if city1 not in income.index or city2 not in income.index:
            raise ValueError(f"Missing income row for pair {pair_name}: {city1}, {city2}")

        row_data = {
            "pair": _pair_slug(city1, city2),
            "pair_label": _pair_label(city1, city2),
            "city1": city1,
            "city2": city2,
            "pv_adoption_gap": _gap(
                float(city_pv.at[city1, PV_COLUMN]),
                float(city_pv.at[city2, PV_COLUMN]),
                gap_mode,
            ),
        }

        # Add gaps for all x-axis factors
        for factor in X_FACTORS:
            if factor == "Total Friction Index":
                row_data[factor] = _gap(
                    float(group.loc[0, factor]),
                    float(group.loc[1, factor]),
                    gap_mode,
                )
            elif factor == "Annual Income USD (net, Numbeo)":
                row_data[factor] = _gap(
                    float(income.at[city1, INCOME_COLUMN]),
                    float(income.at[city2, INCOME_COLUMN]),
                    gap_mode,
                )
            else:  # "IRR (%)"
                row_data[factor] = _gap(
                    float(economic.at[city1, factor]),
                    float(economic.at[city2, factor]),
                    gap_mode,
                )
        rows.append(row_data)

    return pd.DataFrame(rows)


def orient_rows_to_positive_pv_gap(plot_df: pd.DataFrame) -> pd.DataFrame:
    oriented = plot_df.copy()
    negative_gap_mask = oriented["pv_adoption_gap"] < 0
    if negative_gap_mask.any():
        oriented.loc[negative_gap_mask, ["city1", "city2"]] = oriented.loc[
            negative_gap_mask, ["city2", "city1"]
        ].to_numpy()
        oriented.loc[negative_gap_mask, "pair_label"] = [
            _pair_label(city1, city2)
            for city1, city2 in oriented.loc[negative_gap_mask, ["city1", "city2"]].itertuples(index=False)
        ]
        signed_cols = ["pv_adoption_gap"] + X_FACTORS
        oriented.loc[negative_gap_mask, signed_cols] = -oriented.loc[
            negative_gap_mask, signed_cols
        ].to_numpy()
    return oriented


def plot_gap_scatter_three_factors(
    gaps_df: pd.DataFrame,
    out_path: Path,
    out_pdf_path: Path,
    out_csv_path: Path,
    title: str,
) -> None:
    required_cols = {"city1", "city2", "pair_label", "pv_adoption_gap"} | set(X_FACTORS)
    missing = required_cols - set(gaps_df.columns)
    if missing:
        raise ValueError(f"Missing columns for plotting: {sorted(missing)}")

    col_list = ["city1", "city2", "pair_label", "pv_adoption_gap"] + X_FACTORS
    plot_df = gaps_df.loc[:, col_list].copy().dropna().reset_index(drop=True)
    if plot_df.empty:
        raise ValueError("No valid rows available after dropping NaNs.")

    pv_gap = plot_df["pv_adoption_gap"].astype(float)
    abs_pv_gap = pv_gap.abs()
    colors = [
        _pair_color(str(c1), str(c2))
        for c1, c2 in plot_df[["city1", "city2"]].itertuples(index=False)
    ]

    # Keep the three subplots exactly the same size.
    # Width reduced by 60% from 18 to 7.2.
    fig, axes = plt.subplots(1, 3, figsize=(8.5, 6), dpi=220)
    fig.subplots_adjust(wspace=0.30)

    # Shared y-range for all panels.
    # Lower bound is fixed at -0.02 as requested; upper bound keeps data headroom.
    y_lower = -0.02
    y_max_data = float(pv_gap.max())
    y_pad = max(0.008, y_max_data * 0.12 if y_max_data > 0 else 0.02)
    y_upper = max(0.02, y_max_data + y_pad)
    fixed_ylim = (y_lower, y_upper)

    for ax_idx, (ax, x_factor) in enumerate(zip(axes, X_FACTORS)):
        x = plot_df[x_factor].astype(float)

        ax.scatter(
            x,
            pv_gap,
            s=200,
            color=colors,
            alpha=0.82,
            edgecolors="#222222",
            linewidths=0.7,
            zorder=3,
        )

        ax.set_ylim(fixed_ylim)

        # Data-driven x-limits (avoid symmetric-around-zero whitespace).
        x_min, x_max = float(x.min()), float(x.max())
        x_range = x_max - x_min
        # Widen x-range beyond data extents so xticks can render fully.
        x_pad_amount = max(x_range * 0.15, 1.5)
        x_low = x_min - x_pad_amount
        x_high = x_max + x_pad_amount
        if ax_idx == 0:
            x_low = 0.0
        ax.set_xlim((x_low, x_high))

        # Linear regression line (y = m*x + b) for each subplot.
        x_vals = x.to_numpy(dtype=float)
        y_vals = pv_gap.to_numpy(dtype=float)
        if len(x_vals) >= 2 and np.unique(x_vals).size >= 2:
            slope, intercept = np.polyfit(x_vals, y_vals, 1)
            x_line = np.linspace(x_low, x_high, 100)
            y_line = slope * x_line + intercept
            ax.plot(
                x_line,
                y_line,
                color="#333333",
                linestyle="--",
                linewidth=1.5,
                alpha=0.9,
                zorder=2,
            )

        if x_factor == "Annual Income USD (net, Numbeo)":
            x_factor = "Annual Income USD"
            def income_formatter(val, _pos):
                return f"{int(val / 1000)}k"

            ax.xaxis.set_major_formatter(FuncFormatter(income_formatter))
        if x_factor == "Total Friction Index":
            x_factor = "Policy Friction Score"
        ax.axhline(0.0, color="#666666", linewidth=1.0, linestyle="-", zorder=0)
        ax.axvline(0.0, color="#666666", linewidth=1.0, linestyle="-", zorder=0)
        ax.grid(True, alpha=0.25, linestyle="--")
        ax.tick_params(labelsize=11)

        ax.set_xlabel(f"Gap of {x_factor}", fontsize=12)
        if ax_idx == 0:
            ax.set_ylabel(f"Gap of {Y_FACTOR.replace('gap', '')}", fontsize=12)
        else:
            ax.set_ylabel("")

        # Draw a visible outer frame around each subplot.
        for spine in ax.spines.values():
            spine.set_visible(True)
            spine.set_linewidth(1.0)
            spine.set_color("#444444")

    pair_handles = [
        axes[-1].scatter(
            [],
            [],
            s=130.0,
            color=_pair_color(*_pair_city_order(pair_name)),
            alpha=0.9,
            edgecolors="#222222",
            linewidths=0.7,
        )
        for pair_name in ALL_PAIR_ORDER
    ]
    pair_labels = [_pair_label(*_pair_city_order(pair_name)) for pair_name in ALL_PAIR_ORDER]

    fig.legend(
        pair_handles,
        pair_labels,
        loc="center left",
        bbox_to_anchor=(0.98, 0.5),
        frameon=False,
        fontsize=8,
        title_fontsize=11,
    )

    if title:
        fig.suptitle(title, fontsize=14, y=0.98)

    export_df = plot_df.copy()
    export_df["color"] = colors
    export_df["abs_pv_adoption_gap"] = abs_pv_gap
    export_df = export_df.loc[
        :,
        ["pair_label", "city1", "city2", "pv_adoption_gap", "abs_pv_adoption_gap", "color"]
        + X_FACTORS,
    ]

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_pdf_path.parent.mkdir(parents=True, exist_ok=True)
    out_csv_path.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(out_path, bbox_inches="tight")
    fig.savefig(out_pdf_path, bbox_inches="tight")
    plt.close(fig)
    export_df.to_csv(out_csv_path, index=False)


def main() -> None:
    args = parse_args()

    friction_df = pd.read_csv(args.friction_csv)
    economic_df = pd.read_csv(args.economic_csv)
    income_df = pd.read_csv(args.income_csv)
    pair_area_df = pd.read_csv(args.pair_area_csv)
    matched_all_shares = load_city_matched_all_shares(Path(args.base_class_csv))

    plot_df = build_gap_table(
        friction_df=friction_df,
        economic_df=economic_df,
        income_df=income_df,
        pair_area_df=pair_area_df,
        matched_all_shares=matched_all_shares,
        gap_mode=args.gap_mode,
        pair_order=ALL_PAIR_ORDER,
    )

    out_path = Path(args.out_png)
    out_pdf_path = Path(args.out_pdf) if args.out_pdf else out_path.with_suffix(".pdf")
    out_csv_path = Path(args.out_csv) if args.out_csv else out_path.with_suffix(".csv")
    plot_gap_scatter_three_factors(
        gaps_df=plot_df,
        out_path=out_path,
        out_pdf_path=out_pdf_path,
        out_csv_path=out_csv_path,
        title=args.title,
    )
    print(f"Wrote plot: {out_path}")
    print(f"Wrote plot PDF: {out_pdf_path}")
    print(f"Wrote plot data: {out_csv_path}")


if __name__ == "__main__":
    main()

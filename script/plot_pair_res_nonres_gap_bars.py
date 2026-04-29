#!/usr/bin/env python3
"""Plot five side-by-side bar charts for border-pair gap metrics."""

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


THIS_FILE = Path(__file__).resolve()
if THIS_FILE.parent.name == "script" and THIS_FILE.parents[1].name == "manuscript":
    BORDER_ROOT = THIS_FILE.parents[2]
else:
    BORDER_ROOT = THIS_FILE.parents[3]

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
ADMIN_COLUMN = "Administrative Friction Index"
REVENUE_COLUMN = "Revenue Friction Index"
RES_PV_COLUMN = "residential_pv_share_of_building"
NONRES_PV_COLUMN = "non_residential_pv_share_of_building"

METRICS = [
    ("IRR gap (%)", "Gap of IRR (%)"),
    ("Admin friction gap", "Gap of Admin Friction"),
    ("Revenue friction gap", "Gap of Revenue Friction"),
    ("Res PV gap (pp)", "Gap of Res PV Share (pp)"),
    ("Non-res PV gap (pp)", "Gap of Non-res PV Share (pp)"),
]

NEGATIVE_COLOR = "#4c78a8"
POSITIVE_COLOR = "#e45756"
ZERO_COLOR = "#b8b8b8"
LABEL_FONT_SIZE = 12
TICK_FONT_SIZE = 11
VALUE_FONT_SIZE = 11


def _default_pair_area_csv() -> Path:
    candidates = [
        BORDER_ROOT / "manuscript" / "data" / "Building_PVs" / "pair_area_summary.csv",
        BORDER_ROOT / "plots" / "csv" / "pair_area_summary.csv",
        BORDER_ROOT / "prediction" / "pair_area_summary.csv",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return candidates[0]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Create five aligned bar plots with rows = 6 city pairs and "
            "metrics = IRR gap, admin friction gap, revenue friction gap, "
            "res PV gap, non-res PV gap."
        )
    )
    parser.add_argument(
        "--friction-csv",
        type=Path,
        default=BORDER_ROOT / "manuscript" / "data" / "Policy_frictions" / "border_city_pv_friction_matrix.csv",
        help="Directional border-city PV friction matrix CSV.",
    )
    parser.add_argument(
        "--economic-csv",
        type=Path,
        default=BORDER_ROOT / "manuscript" / "data" / "PV_Eco_model" / "economic_analysis_results.csv",
        help="City-level economic results CSV.",
    )
    parser.add_argument(
        "--pair-area-csv",
        type=Path,
        default=_default_pair_area_csv(),
        help="City-level PV/building share summary CSV.",
    )
    parser.add_argument(
        "--gap-mode",
        default="signed",
        choices=["signed", "abs"],
        help="Whether to use signed or absolute gaps.",
    )
    parser.add_argument(
        "--out-png",
        type=Path,
        default=BORDER_ROOT / "plots" / "images" / "pair_res_nonres_5metric_barplots.png",
        help="Output bar plot PNG path.",
    )
    parser.add_argument(
        "--out-csv",
        type=Path,
        default=None,
        help="Output CSV for plotted values (defaults to out-png with .csv).",
    )
    parser.add_argument(
        "--out-pdf",
        type=Path,
        default=None,
        help="Output PDF path (defaults to out-png with .pdf).",
    )
    return parser.parse_args()


def _city_key(value: str) -> str:
    normalized = " ".join(str(value).strip().lower().replace("_", " ").replace("-", " ").split())
    return CITY_ALIASES.get(normalized, normalized.replace(" ", ""))


def _pair_city_order(pair_name: str) -> list[str]:
    return [_city_key(part) for part in pair_name.split("–")]


def _pair_label(city1: str, city2: str) -> str:
    return f"{SHOW_NAME_MAP.get(city1, city1.title())} - {SHOW_NAME_MAP.get(city2, city2.title())}"


def _gap(a: float, b: float, mode: str) -> float:
    return abs(a - b) if mode == "abs" else (a - b)


def build_gap_table(
    friction_df: pd.DataFrame,
    economic_df: pd.DataFrame,
    pair_area_df: pd.DataFrame,
    gap_mode: str,
) -> pd.DataFrame:
    friction = friction_df.copy()
    friction["city_key"] = friction["City"].map(_city_key)

    economic = economic_df.copy()
    economic["city_key"] = economic["City"].map(_city_key)
    economic = economic.set_index("city_key")

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
            raise ValueError(f"Expected exactly 2 directional rows for {pair_name}, found {len(group)}")

        city1 = str(group.loc[0, "city_key"])
        city2 = str(group.loc[1, "city_key"])

        if city1 not in economic.index or city2 not in economic.index:
            raise ValueError(f"Missing economic rows for {pair_name}: {city1}, {city2}")
        if city1 not in city_pv.index or city2 not in city_pv.index:
            raise ValueError(f"Missing PV rows for {pair_name}: {city1}, {city2}")

        rows.append(
            {
                "pair_label": _pair_label(city1, city2),
                "IRR gap (%)": _gap(float(economic.at[city1, IRR_COLUMN]), float(economic.at[city2, IRR_COLUMN]), gap_mode),
                "Admin friction gap": _gap(float(group.loc[0, ADMIN_COLUMN]), float(group.loc[1, ADMIN_COLUMN]), gap_mode),
                "Revenue friction gap": _gap(float(group.loc[0, REVENUE_COLUMN]), float(group.loc[1, REVENUE_COLUMN]), gap_mode),
                "Res PV gap (pp)": _gap(float(city_pv.at[city1, RES_PV_COLUMN]), float(city_pv.at[city2, RES_PV_COLUMN]), gap_mode) * 100.0,
                "Non-res PV gap (pp)": _gap(
                    float(city_pv.at[city1, NONRES_PV_COLUMN]),
                    float(city_pv.at[city2, NONRES_PV_COLUMN]),
                    gap_mode,
                ) * 100.0,
            }
        )

    return pd.DataFrame(rows)


def _bar_colors(values: np.ndarray) -> list[str]:
    colors: list[str] = []
    for value in values:
        if np.isclose(value, 0.0):
            colors.append(ZERO_COLOR)
        elif value > 0:
            colors.append(POSITIVE_COLOR)
        else:
            colors.append(NEGATIVE_COLOR)
    return colors


def _axis_limit(values: np.ndarray) -> float:
    finite = values[np.isfinite(values)]
    if finite.size == 0:
        return 1.0
    max_abs = float(np.max(np.abs(finite)))
    return max(max_abs * 1.22, 1e-6)


def plot_bar_grid(table_df: pd.DataFrame, out_png: Path, out_pdf: Path | None = None) -> None:
    y = np.arange(len(table_df))
    pair_labels = table_df["pair_label"].astype(str).tolist()

    fig, axes = plt.subplots(1, len(METRICS), figsize=(19.5, 5.4), dpi=240, sharey=True)
    fig.patch.set_alpha(0.0)

    for ax, (column, title) in zip(axes, METRICS):
        values = table_df[column].to_numpy(dtype=float)
        ax.barh(y, values, color=_bar_colors(values), edgecolor="none", height=0.68, zorder=2)
        ax.axvline(0.0, color="#333333", linewidth=1.0)
        limit = _axis_limit(values)
        ax.set_xlim(-limit, limit)
        ax.set_axisbelow(True)
        ax.xaxis.grid(True, color="#e6e6e6", linewidth=0.8)
        ax.yaxis.grid(False)
        ax.tick_params(axis="x", labelsize=TICK_FONT_SIZE)
        ax.tick_params(axis="y", length=0)
        ax.set_xlabel(title, fontsize=LABEL_FONT_SIZE, fontweight="normal", labelpad=10)

        for idx, value in enumerate(values):
            offset = limit * 0.035
            x = value + offset if value >= 0 else value - offset
            ha = "left" if value >= 0 else "right"
            ax.text(
                x,
                idx,
                f"{value:.2f}",
                va="center",
                ha=ha,
                fontsize=VALUE_FONT_SIZE,
                color="#222222",
                fontweight="bold",
            )

        for spine in ax.spines.values():
            spine.set_visible(False)

    axes[0].set_yticks(y)
    axes[0].set_yticklabels(pair_labels, fontsize=LABEL_FONT_SIZE, fontweight="normal")
    axes[0].invert_yaxis()
    for ax in axes[1:]:
        ax.tick_params(axis="y", labelleft=False)

    fig.subplots_adjust(left=0.22, right=0.98, top=0.92, bottom=0.14, wspace=0.30)
    out_png.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_png, bbox_inches="tight", transparent=True)
    if out_pdf is not None:
        out_pdf.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(out_pdf, bbox_inches="tight", transparent=True)
    plt.close(fig)


def main() -> None:
    args = parse_args()

    friction_df = pd.read_csv(args.friction_csv)
    economic_df = pd.read_csv(args.economic_csv)
    pair_area_df = pd.read_csv(args.pair_area_csv)

    table_df = build_gap_table(
        friction_df=friction_df,
        economic_df=economic_df,
        pair_area_df=pair_area_df,
        gap_mode=args.gap_mode,
    )

    out_png = args.out_png
    out_pdf = args.out_pdf if args.out_pdf is not None else out_png.with_suffix(".pdf")
    out_csv = args.out_csv if args.out_csv is not None else out_png.with_suffix(".csv")

    plot_bar_grid(table_df, out_png, out_pdf)
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    table_df.to_csv(out_csv, index=False)

    print(f"Wrote bar plots: {out_png}")
    print(f"Wrote PDF: {out_pdf}")
    print(f"Wrote values: {out_csv}")


if __name__ == "__main__":
    main()

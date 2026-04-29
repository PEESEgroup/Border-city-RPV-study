#!/usr/bin/env python3
"""Redraw cumulative discounted cash flow profiles with pair colors."""

from __future__ import annotations

import argparse
import csv
import os
import sys
from pathlib import Path

os.environ.setdefault("MPLCONFIGDIR", "/tmp/matplotlib")

import matplotlib.pyplot as plt
import numpy as np


THIS_FILE = Path(__file__).resolve()
if THIS_FILE.parent.name == "script" and THIS_FILE.parents[1].name == "manuscript":
    BORDER_ROOT = THIS_FILE.parents[2]
else:
    BORDER_ROOT = THIS_FILE.parents[3]
DATASET_ROOT = BORDER_ROOT.parent
if str(DATASET_ROOT) not in sys.path:
    sys.path.insert(0, str(DATASET_ROOT))

try:
    from econimic_model import calculate_solar_economics, city_solar_data_checked
except ModuleNotFoundError:
    from Border.factors.econimic_model import calculate_solar_economics, city_solar_data_checked


PAIR_ORDER = [
    ("Vienna", "Bratislava"),
    ("Singapore", "Johor Bahru"),
    ("San Diego", "Tijuana"),
    ("El Paso", "Ciudad Juarez"),
    ("Hong Kong", "Shenzhen"),
    ("Monaco", "Nice"),
]

PAIR_COLORS = {
    ("vienna", "bratislava"): ("#c97c5d", "#8c4f3f"),
    ("elpaso", "juarez"): ("#4f7cac", "#1f4e79"),
    ("sandiego", "tijuana"): ("#5aa469", "#2f6b3b"),
    ("hongkong", "shenzhen"): ("#b07bac", "#7f4f7c"),
    ("singapore", "johorbahru"): ("#d9a441", "#9a6a12"),
    ("monaco", "nice"): ("#d16d8a", "#8f3458"),
}

CITY_DISPLAY_NAMES = {
    "Vienna": "Vienna",
    "Bratislava": "Bratislava",
    "San Diego": "San Diego",
    "Tijuana": "Tijuana",
    "El Paso": "El Paso",
    "Ciudad Juarez": "Juarez",
    "Hong Kong": "Hong Kong",
    "Shenzhen": "Shenzhen",
    "Singapore": "Singapore",
    "Johor Bahru": "Johor Bahru",
    "Monaco": "Monaco",
    "Nice": "Nice",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Plot cumulative discounted cash flow profiles using the economic model, "
            "with pair colors."
        )
    )
    parser.add_argument(
        "--out",
        default=str(BORDER_ROOT / "manuscript" / "figures" / "panels" / "discounted_cashflow_profiles_narrow_tall.pdf"),
        help="Output figure path.",
    )
    parser.add_argument(
        "--system-size-kw",
        type=float,
        default=5.0,
        help="PV system size in kW.",
    )
    parser.add_argument(
        "--years",
        type=int,
        default=25,
        help="Project lifetime in years.",
    )
    parser.add_argument(
        "--discount-rate",
        type=float,
        default=0.05,
        help="Discount rate used for discounted cash flows.",
    )
    parser.add_argument(
        "--fig-width",
        type=float,
        default=7.2,
        help="Figure width in inches.",
    )
    parser.add_argument(
        "--fig-height",
        type=float,
        default=4.5,
        help="Figure height in inches.",
    )
    parser.add_argument(
        "--csv-out",
        default=str(
            BORDER_ROOT
            / "manuscript"
            / "data"
            / "PV_Eco_model"
            / "discounted_cashflow_profiles_city_year.csv"
        ),
        help="Output CSV path for yearly cash-flow series.",
    )
    return parser.parse_args()


def _city_key(value: str) -> str:
    return "".join(str(value).strip().lower().replace("_", " ").replace("-", " ").split())


def _pair_key(city1: str, city2: str) -> str:
    city1_key = _city_key(city1)
    city2_key = _city_key(city2)
    if city1_key == "ciudadjuarez":
        city1_key = "juarez"
    if city2_key == "ciudadjuarez":
        city2_key = "juarez"
    return city1_key, city2_key


def _pair_colors(city1: str, city2: str) -> tuple[str, str] | None:
    return PAIR_COLORS.get(_pair_key(city1, city2))


def plot_discounted_profiles(
    detailed_results: dict[str, dict[str, list[float]]],
    out_path: Path,
    fig_width: float,
    fig_height: float,
) -> None:
    fig, ax = plt.subplots(figsize=(fig_width, fig_height), dpi=220)

    final_points: list[tuple[float, float, str, str]] = []
    max_year = 0
    y_values = []

    for city1, city2 in PAIR_ORDER:
        pair_colors = _pair_colors(city1, city2)

        for index, city in enumerate((city1, city2)):
            if city not in detailed_results:
                continue

            city_color = pair_colors[index] if pair_colors is not None else "#7d8597"

            years = detailed_results[city]["years"]
            cumulative = detailed_results[city]["cumulative_discounted_cashflows"]
            max_year = max(max_year, int(max(years)))
            y_values.extend(cumulative)

            ax.plot(
                years,
                cumulative,
                color=city_color,
                linestyle="-",
                linewidth=1.8,
                alpha=0.95,
            )

            final_points.append((float(years[-1]), float(cumulative[-1]), city, city_color))

    ax.axhline(0.0, color="#777777", linewidth=0.9, linestyle="-", zorder=0)

    if final_points:
        y_min = min(y_values)
        y_max = max(y_values)
        y_span = y_max - y_min if not np.isclose(y_max, y_min) else 1.0
        x_offset = max_year * 0.018 if max_year > 0 else 0.4
        for x_end, y_end, city, pair_color in final_points:
            text_x = x_end + x_offset
            text_y = y_end
            va = "center"

            ax.text(
                text_x,
                text_y,
                CITY_DISPLAY_NAMES.get(city, city),
                fontsize=11,
                color=pair_color,
                ha="left",
                va=va,
            )

    ax.set_xlabel("Year", fontsize=11)
    ax.set_ylabel("Cumulative Discounted Cash Flow ($)", fontsize=11)
    ax.grid(True, alpha=0.25, linestyle="--")
    ax.tick_params(
        axis="both",
        which="both",
        labelsize=9,
        bottom=True,
        left=True,
        top=False,
        right=False,
        length=3.5,
        width=0.8,
        color="#555555",
        direction="out",
    )
    ax.spines["left"].set_visible(True)
    ax.spines["bottom"].set_visible(True)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_linewidth(0.8)
    ax.spines["bottom"].set_linewidth(0.8)
    ax.spines["left"].set_color("#555555")
    ax.spines["bottom"].set_color("#555555")

    y_pad = (max(y_values) - min(y_values)) * 0.08 if y_values else 1.0
    ax.set_xlim(-0.3, 25.0)
    if y_values:
        ax.set_ylim(min(y_values) - y_pad, max(y_values) + y_pad)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(out_path, bbox_inches="tight")
    plt.close(fig)


def export_discounted_cashflow_csv(
    detailed_results: dict[str, dict[str, list[float]]],
    out_path: Path,
) -> None:
    rows: list[dict[str, object]] = []

    for city1, city2 in PAIR_ORDER:
        for city in (city1, city2):
            if city not in detailed_results:
                continue

            years = detailed_results[city]["years"]
            annual_cashflows = detailed_results[city]["annual_cashflows"]
            discounted_cashflows = detailed_results[city]["discounted_cashflows"]
            cumulative = detailed_results[city]["cumulative_discounted_cashflows"]

            for year in years:
                if year == 0:
                    annual_cashflow = ""
                    discounted_cashflow = ""
                else:
                    annual_cashflow = annual_cashflows[year - 1]
                    discounted_cashflow = discounted_cashflows[year - 1]

                rows.append(
                    {
                        "city": city,
                        "city_display": CITY_DISPLAY_NAMES.get(city, city),
                        "year": year,
                        "annual_cashflow_usd": annual_cashflow,
                        "discounted_cashflow_usd": discounted_cashflow,
                        "cumulative_discounted_cashflow_usd": cumulative[year],
                    }
                )

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(
            csv_file,
            fieldnames=[
                "city",
                "city_display",
                "year",
                "annual_cashflow_usd",
                "discounted_cashflow_usd",
                "cumulative_discounted_cashflow_usd",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    args = parse_args()
    _, detailed_results = calculate_solar_economics(
        city_data=city_solar_data_checked,
        system_size_kw=args.system_size_kw,
        years=args.years,
        discount_rate=args.discount_rate,
    )
    plot_discounted_profiles(
        detailed_results,
        Path(args.out),
        fig_width=args.fig_width,
        fig_height=args.fig_height,
    )
    export_discounted_cashflow_csv(
        detailed_results,
        Path(args.csv_out),
    )


if __name__ == "__main__":
    main()

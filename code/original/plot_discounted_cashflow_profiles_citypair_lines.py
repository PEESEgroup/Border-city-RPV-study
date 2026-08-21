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
    BORDER_ROOT = THIS_FILE.parents[2]
DATASET_ROOT = BORDER_ROOT.parent
if str(DATASET_ROOT) not in sys.path:
    sys.path.insert(0, str(DATASET_ROOT))

try:
    from econimic_model import calculate_solar_economics, city_solar_data_checked
except ModuleNotFoundError:
    from Border.factors.econimic_model import calculate_solar_economics, city_solar_data_checked

try:
    from plot_fig4_uncertainty_supplement import build_uncertainty_results
except ModuleNotFoundError:
    from Border.manuscript.script.plot_fig4_uncertainty_supplement import build_uncertainty_results


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
        default=3.15,
        help="Figure width in inches.",
    )
    parser.add_argument(
        "--fig-height",
        type=float,
        default=5.67,
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
    uncertainty_results: dict[str, dict[str, dict[str, np.ndarray]]] | None = None,
) -> None:
    fig, axes = plt.subplots(
        nrows=3,
        ncols=2,
        figsize=(fig_width, fig_height),
        dpi=220,
        sharex=True,
        sharey=True,
        constrained_layout=True,
    )
    axes_flat = axes.ravel()

    y_values: list[float] = []
    for city1, city2 in PAIR_ORDER:
        for city in (city1, city2):
            if city in detailed_results:
                y_values.extend(detailed_results[city]["cumulative_discounted_cashflows"])
            if uncertainty_results and city in uncertainty_results:
                q = uncertainty_results[city]["cumulative_discounted_cashflows"]
                y_values.extend(q["p2_5"].tolist())
                y_values.extend(q["p97_5"].tolist())

    y_pad = (max(y_values) - min(y_values)) * 0.08 if y_values else 1.0
    y_min = min(y_values) - y_pad if y_values else -1.0
    y_max = max(y_values) + y_pad if y_values else 1.0

    for pair_index, (city1, city2) in enumerate(PAIR_ORDER):
        ax = axes_flat[pair_index]
        pair_colors = _pair_colors(city1, city2)
        if pair_colors is None:
            pair_colors = ("#7d8597", "#4d5767")

        pair_end_values: list[tuple[float, str, str]] = []

        for index, city in enumerate((city1, city2)):
            if city not in detailed_results:
                continue

            city_color = pair_colors[index]
            years = detailed_results[city]["years"]
            cumulative = detailed_results[city]["cumulative_discounted_cashflows"]

            if uncertainty_results and city in uncertainty_results:
                q = uncertainty_results[city]["cumulative_discounted_cashflows"]
                band_years = np.arange(len(q["median"]))
                ax.fill_between(
                    band_years,
                    q["p2_5"],
                    q["p97_5"],
                    color=city_color,
                    alpha=0.10,
                    linewidth=0,
                    zorder=1,
                )

            ax.plot(
                years,
                cumulative,
                color=city_color,
                linestyle="-",
                linewidth=2.2,
                alpha=0.98,
                zorder=3,
            )
            ax.scatter(
                [years[-1]],
                [cumulative[-1]],
                s=18,
                color=city_color,
                edgecolor="white",
                linewidth=0.6,
                zorder=4,
            )

            payback_year = None
            for year, value in zip(years, cumulative):
                if year > 0 and value >= 0:
                    payback_year = int(year)
                    break
            if payback_year is not None:
                ax.scatter(
                    [payback_year],
                    [0],
                    s=16,
                    marker="D",
                    color=city_color,
                    edgecolor="white",
                    linewidth=0.5,
                    zorder=5,
                )

            pair_end_values.append((float(cumulative[-1]), city, city_color))

        ax.axhline(0.0, color="#777777", linewidth=0.85, linestyle="-", zorder=0)
        ax.set_title(
            f"{CITY_DISPLAY_NAMES.get(city1, city1)} - {CITY_DISPLAY_NAMES.get(city2, city2)}",
            fontsize=7.3,
            pad=2.5,
        )
        ax.set_xlim(-0.4, 25.4)
        ax.set_ylim(y_min, y_max)
        ax.grid(True, alpha=0.22, linestyle="--", linewidth=0.6)
        ax.tick_params(
            axis="both",
            which="both",
            labelsize=6.8,
            bottom=True,
            left=True,
            top=False,
            right=False,
            length=2.7,
            width=0.7,
            color="#555555",
            direction="out",
        )
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.spines["left"].set_linewidth(0.7)
        ax.spines["bottom"].set_linewidth(0.7)
        ax.spines["left"].set_color("#555555")
        ax.spines["bottom"].set_color("#555555")

        if pair_end_values:
            ordered_end_values = sorted(pair_end_values, reverse=True)
            for rank, (y_end, city, city_color) in enumerate(ordered_end_values):
                text_y = y_end + (0.035 * (y_max - y_min) if rank == 0 else -0.035 * (y_max - y_min))
                text_y = float(np.clip(text_y, y_min + 0.05 * (y_max - y_min), y_max - 0.05 * (y_max - y_min)))
                ax.text(
                    24.6,
                    text_y,
                    f"{CITY_DISPLAY_NAMES.get(city, city)} ${y_end/1000:.1f}k",
                    fontsize=7.0,
                    color=city_color,
                    ha="right",
                    va="center",
                    bbox=dict(facecolor="white", edgecolor="none", alpha=0.72, pad=1.2),
                    zorder=6,
                )

    for ax in axes_flat[len(PAIR_ORDER):]:
        ax.set_visible(False)

    fig.supxlabel("Year", fontsize=9.5)
    fig.supylabel("Cumulative discounted cash flow ($)", fontsize=9.5)

    out_path.parent.mkdir(parents=True, exist_ok=True)
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
        uncertainty_results=build_uncertainty_results()[0],
    )
    export_discounted_cashflow_csv(
        detailed_results,
        Path(args.csv_out),
    )


if __name__ == "__main__":
    main()

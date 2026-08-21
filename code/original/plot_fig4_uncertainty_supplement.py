#!/usr/bin/env python3
"""Supplementary uncertainty version of Figure 4a using Monte Carlo propagation."""

from __future__ import annotations

import os
import sys
from pathlib import Path

os.environ.setdefault("MPLCONFIGDIR", "/tmp/matplotlib")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.lines import Line2D
from matplotlib.patches import Patch


THIS_FILE = Path(__file__).resolve()
if THIS_FILE.parent.name == "script" and THIS_FILE.parents[1].name == "manuscript":
    BORDER_ROOT = THIS_FILE.parents[2]
else:
    BORDER_ROOT = THIS_FILE.parents[2]
DATASET_ROOT = BORDER_ROOT.parent
if str(DATASET_ROOT) not in sys.path:
    sys.path.insert(0, str(DATASET_ROOT))

try:
    from econimic_model import city_solar_data_checked, compute_irr
except ModuleNotFoundError:
    from Border.manuscript.script.econimic_model import city_solar_data_checked, compute_irr


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

YEARS = 25
SYSTEM_SIZE_KW = 5.0
DISCOUNT_RATE = 0.05
N_SIMS = 1000
RNG_SEED = 20260423

# Relative / absolute uncertainty assumptions for key city-level inputs.
REL_SD = {
    "cost_per_watt": 0.10,
    "pv_yield_kwh_per_kw_year": 0.05,
    "elec_rate": 0.10,
    "export_rate": 0.15,
}
ABS_SD = {
    "self_consumption_ratio": 0.05,
    "capex_reduction": 0.03,
    "om_rate": 0.002,
}


def _city_key(value: str) -> str:
    return "".join(str(value).strip().lower().replace("_", " ").replace("-", " ").split())


def _pair_key(city1: str, city2: str) -> tuple[str, str]:
    city1_key = _city_key(city1)
    city2_key = _city_key(city2)
    if city1_key == "ciudadjuarez":
        city1_key = "juarez"
    if city2_key == "ciudadjuarez":
        city2_key = "juarez"
    return city1_key, city2_key


def _pair_colors(city1: str, city2: str) -> tuple[str, str] | None:
    return PAIR_COLORS.get(_pair_key(city1, city2))


def _sample_positive_normal(rng: np.random.Generator, mean: float, rel_sd: float, n: int) -> np.ndarray:
    values = rng.normal(loc=mean, scale=abs(mean) * rel_sd, size=n)
    floor = max(mean * 0.2, 1e-6)
    return np.clip(values, floor, None)


def _sample_bounded_normal(
    rng: np.random.Generator,
    mean: float,
    abs_sd: float,
    n: int,
    lower: float,
    upper: float,
) -> np.ndarray:
    values = rng.normal(loc=mean, scale=abs_sd, size=n)
    return np.clip(values, lower, upper)


def simulate_city(params: dict[str, float], rng: np.random.Generator) -> dict[str, np.ndarray]:
    cost_per_watt = _sample_positive_normal(rng, params["cost_per_watt"], REL_SD["cost_per_watt"], N_SIMS)
    pv_yield = _sample_positive_normal(
        rng, params["pv_yield_kwh_per_kw_year"], REL_SD["pv_yield_kwh_per_kw_year"], N_SIMS
    )
    elec_rate = _sample_positive_normal(rng, params["elec_rate"], REL_SD["elec_rate"], N_SIMS)
    export_rate = _sample_positive_normal(rng, params["export_rate"], REL_SD["export_rate"], N_SIMS)
    self_consumption_ratio = _sample_bounded_normal(
        rng,
        params.get("self_consumption_ratio", 0.7),
        ABS_SD["self_consumption_ratio"],
        N_SIMS,
        0.4,
        0.95,
    )
    capex_reduction = _sample_bounded_normal(
        rng,
        params.get("capex_reduction", 0.0),
        ABS_SD["capex_reduction"],
        N_SIMS,
        0.0,
        0.5,
    )
    om_rate = _sample_bounded_normal(
        rng,
        params.get("om_rate", 0.01),
        ABS_SD["om_rate"],
        N_SIMS,
        0.001,
        0.04,
    )

    degradation = float(params.get("degradation_rate", 0.005))
    years = np.arange(YEARS)
    discount_factors = (1.0 + DISCOUNT_RATE) ** np.arange(1, YEARS + 1)

    gross_cost = SYSTEM_SIZE_KW * cost_per_watt * 1000.0
    net_cost = gross_cost * (1.0 - capex_reduction)
    export_ratio = 1.0 - self_consumption_ratio
    blended_value = elec_rate * self_consumption_ratio + export_rate * export_ratio

    production_year0 = SYSTEM_SIZE_KW * pv_yield
    production = production_year0[:, None] * ((1.0 - degradation) ** years[None, :])
    annual_savings = production * blended_value[:, None]
    annual_om = gross_cost[:, None] * om_rate[:, None]
    annual_cashflows = annual_savings - annual_om
    discounted_cashflows = annual_cashflows / discount_factors[None, :]
    cumulative_discounted_cashflows = np.concatenate(
        [-net_cost[:, None], -net_cost[:, None] + np.cumsum(discounted_cashflows, axis=1)],
        axis=1,
    )

    npv_costs = net_cost + np.sum(annual_om / discount_factors[None, :], axis=1)
    npv_energy = np.sum(production / discount_factors[None, :], axis=1)
    lcoe = np.where(npv_energy > 0, npv_costs / npv_energy, np.nan)
    npv = -net_cost + np.sum(discounted_cashflows, axis=1)

    irr = np.array(
        [
            compute_irr([-float(net_cost[i]), *annual_cashflows[i].tolist()])
            for i in range(N_SIMS)
        ],
        dtype=float,
    )
    irr_pct = irr * 100.0

    return {
        "net_capex": net_cost,
        "npv": npv,
        "irr_pct": irr_pct,
        "blended_value": blended_value,
        "lcoe": lcoe,
        "elec_rate": elec_rate,
        "export_rate": export_rate,
        "cumulative_discounted_cashflows": cumulative_discounted_cashflows,
    }


def summarize_quantiles(values: np.ndarray) -> dict[str, np.ndarray]:
    return {
        "p2_5": np.nanpercentile(values, 2.5, axis=0),
        "median": np.nanpercentile(values, 50.0, axis=0),
        "p97_5": np.nanpercentile(values, 97.5, axis=0),
    }


def build_uncertainty_results() -> tuple[dict[str, dict[str, np.ndarray]], pd.DataFrame]:
    rng = np.random.default_rng(RNG_SEED)
    city_results: dict[str, dict[str, np.ndarray]] = {}
    summary_rows: list[dict[str, float | str]] = []

    for city, params in city_solar_data_checked.items():
        sims = simulate_city(params, rng)
        city_results[city] = {metric: summarize_quantiles(values) for metric, values in sims.items()}

        summary_rows.append(
            {
                "City": CITY_DISPLAY_NAMES.get(city, city),
                "Net CAPEX median ($)": city_results[city]["net_capex"]["median"],
                "Net CAPEX 2.5% ($)": city_results[city]["net_capex"]["p2_5"],
                "Net CAPEX 97.5% ($)": city_results[city]["net_capex"]["p97_5"],
                "NPV median ($)": city_results[city]["npv"]["median"],
                "NPV 2.5% ($)": city_results[city]["npv"]["p2_5"],
                "NPV 97.5% ($)": city_results[city]["npv"]["p97_5"],
                "IRR median (%)": city_results[city]["irr_pct"]["median"],
                "IRR 2.5% (%)": city_results[city]["irr_pct"]["p2_5"],
                "IRR 97.5% (%)": city_results[city]["irr_pct"]["p97_5"],
                "Blended value median ($/kWh)": city_results[city]["blended_value"]["median"],
                "Blended value 2.5% ($/kWh)": city_results[city]["blended_value"]["p2_5"],
                "Blended value 97.5% ($/kWh)": city_results[city]["blended_value"]["p97_5"],
                "LCOE median ($/kWh)": city_results[city]["lcoe"]["median"],
                "LCOE 2.5% ($/kWh)": city_results[city]["lcoe"]["p2_5"],
                "LCOE 97.5% ($/kWh)": city_results[city]["lcoe"]["p97_5"],
            }
        )

    summary_df = pd.DataFrame(summary_rows)
    return city_results, summary_df


def _build_sizes(values: list[float], min_size: float = 90.0, max_size: float = 560.0) -> np.ndarray:
    arr = np.asarray(values, dtype=float)
    if arr.size == 0:
        return np.array([], dtype=float)
    vmin = float(np.nanmin(arr))
    vmax = float(np.nanmax(arr))
    if np.isclose(vmin, vmax):
        return np.full_like(arr, (min_size + max_size) / 2.0, dtype=float)
    return min_size + ((arr - vmin) / (vmax - vmin)) * (max_size - min_size)


def _pair_spaced_y_positions(city_sequence: list[str]) -> np.ndarray:
    y_vals: list[float] = []
    base = 0.0
    in_pair_gap = 0.62
    between_pair_gap = 0.36
    for idx, _ in enumerate(city_sequence):
        y_vals.append(base)
        if idx % 2 == 0:
            base += in_pair_gap
        else:
            base += in_pair_gap + between_pair_gap
    return np.asarray(y_vals, dtype=float)


def plot_panel_a(city_results: dict[str, dict[str, np.ndarray]], out_path: Path) -> None:
    fig, ax_a = plt.subplots(figsize=(7.6, 5.8), dpi=240, constrained_layout=True)

    irr_medians = []
    scatter_points = []
    for city1, city2 in PAIR_ORDER:
        for city in (city1, city2):
            irr_medians.append(float(city_results[city]["irr_pct"]["median"]))
            scatter_points.append(city)

    sizes = _build_sizes(irr_medians)
    size_lookup = {city: size for city, size in zip(scatter_points, sizes)}

    for city1, city2 in PAIR_ORDER:
        pair_colors = _pair_colors(city1, city2)
        if pair_colors is None:
            pair_colors = ("#7d8597", "#4d5767")

        x1 = float(city_results[city1]["net_capex"]["median"])
        y1 = float(city_results[city1]["npv"]["median"])
        x2 = float(city_results[city2]["net_capex"]["median"])
        y2 = float(city_results[city2]["npv"]["median"])
        ax_a.plot([x1, x2], [y1, y2], color=pair_colors[0], linewidth=1.3, alpha=0.85, zorder=1)

        for idx, city in enumerate((city1, city2)):
            color = pair_colors[idx]
            x_mid = float(city_results[city]["net_capex"]["median"])
            y_mid = float(city_results[city]["npv"]["median"])
            x_lo = x_mid - float(city_results[city]["net_capex"]["p2_5"])
            x_hi = float(city_results[city]["net_capex"]["p97_5"]) - x_mid
            y_lo = y_mid - float(city_results[city]["npv"]["p2_5"])
            y_hi = float(city_results[city]["npv"]["p97_5"]) - y_mid
            ax_a.errorbar(
                x_mid,
                y_mid,
                xerr=[[x_lo], [x_hi]],
                yerr=[[y_lo], [y_hi]],
                fmt="none",
                ecolor=color,
                elinewidth=1.0,
                alpha=0.55,
                capsize=0,
                zorder=2,
            )
            ax_a.scatter(
                x_mid,
                y_mid,
                s=float(size_lookup[city]),
                color=color,
                edgecolors="#333333",
                linewidths=0.6,
                alpha=0.84,
                zorder=3,
            )
            ax_a.text(
                x_mid + 110.0,
                y_mid + 180.0,
                CITY_DISPLAY_NAMES.get(city, city),
                fontsize=9,
                color=color,
                ha="left",
                va="bottom",
            )

    ax_a.set_xlabel("Net CAPEX ($)")
    ax_a.set_ylabel("NPV ($)")
    ax_a.grid(True, linestyle="--", alpha=0.25)

    irr_legend_vals = [10, 20, 30]
    irr_legend_sizes = _build_sizes(irr_legend_vals)
    handles = [
        ax_a.scatter([], [], s=float(size), color="#9a9a9a", edgecolors="#333333", linewidths=0.6)
        for size in irr_legend_sizes
    ]
    ax_a.legend(handles, [f"{v:.0f}" for v in irr_legend_vals], title="Median IRR (%)", loc="upper left", frameon=False)
    ax_a.spines["top"].set_visible(False)
    ax_a.spines["right"].set_visible(False)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, bbox_inches="tight")
    plt.close(fig)


def plot_panel_b(city_results: dict[str, dict[str, np.ndarray]], out_path: Path) -> None:
    fig, ax_b = plt.subplots(figsize=(7.2, 5.8), dpi=240, constrained_layout=True)

    years = np.arange(YEARS + 1)
    for city1, city2 in PAIR_ORDER:
        pair_colors = _pair_colors(city1, city2)
        if pair_colors is None:
            pair_colors = ("#7d8597", "#4d5767")
        for idx, city in enumerate((city1, city2)):
            color = pair_colors[idx]
            q = city_results[city]["cumulative_discounted_cashflows"]
            ax_b.fill_between(years, q["p2_5"], q["p97_5"], color=color, alpha=0.12, linewidth=0)
            ax_b.plot(years, q["median"], color=color, linewidth=1.9, alpha=0.98)
            ax_b.text(
                years[-1] + 0.28,
                float(q["median"][-1]),
                CITY_DISPLAY_NAMES.get(city, city),
                fontsize=9,
                color=color,
                ha="left",
                va="center",
            )

    ax_b.axhline(0.0, color="#777777", linewidth=0.9)
    ax_b.set_xlim(-0.2, 26.3)
    ax_b.set_xlabel("Year")
    ax_b.set_ylabel("Cumulative Discounted Cash Flow ($)")
    ax_b.grid(True, linestyle="--", alpha=0.25)
    ax_b.spines["top"].set_visible(False)
    ax_b.spines["right"].set_visible(False)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, bbox_inches="tight")
    plt.close(fig)


def plot_panel_c(
    city_results: dict[str, dict[str, np.ndarray]],
    out_path: Path,
    fig_width: float = 7.2,
    fig_height: float = 4.64,
    dpi: int = 260,
) -> None:
    fig, (ax_c_left, ax_c_right) = plt.subplots(
        nrows=1,
        ncols=2,
        figsize=(fig_width, fig_height),
        dpi=dpi,
        constrained_layout=True,
        sharey=True,
        gridspec_kw={"width_ratios": [1.35, 1.0], "wspace": 0.05},
    )

    ordered_cities = [city for pair in PAIR_ORDER for city in pair]
    y_positions = _pair_spaced_y_positions(ordered_cities)
    bar_h = 0.24

    left_max = 0.0
    right_max = 0.0

    for i, city in enumerate(ordered_cities):
        color_idx = 0 if i % 2 == 0 else 1
        pair_colors = _pair_colors(*PAIR_ORDER[i // 2]) or ("#7d8597", "#4d5767")
        color = pair_colors[color_idx]
        y = y_positions[i]

        blended_q = city_results[city]["blended_value"]
        lcoe_q = city_results[city]["lcoe"]
        elec_q = city_results[city]["elec_rate"]
        export_q = city_results[city]["export_rate"]

        blended_mid = float(blended_q["median"])
        lcoe_mid = float(lcoe_q["median"])
        elec_mid = float(elec_q["median"])
        export_mid = float(export_q["median"])

        left_max = max(left_max, blended_mid, lcoe_mid, float(blended_q["p97_5"]), float(lcoe_q["p97_5"]))
        right_max = max(right_max, elec_mid, export_mid, float(elec_q["p97_5"]), float(export_q["p97_5"]))

        ax_c_left.hlines(
            y=y,
            xmin=min(blended_mid, lcoe_mid),
            xmax=max(blended_mid, lcoe_mid),
            color=color,
            linewidth=2.6,
            alpha=0.55,
            zorder=1,
        )

        ax_c_left.errorbar(
            blended_mid,
            y,
            xerr=[[blended_mid - float(blended_q["p2_5"])], [float(blended_q["p97_5"]) - blended_mid]],
            fmt="o",
            markersize=6.3,
            color="#222222",
            markerfacecolor=color,
            markeredgecolor="#222222",
            elinewidth=0.9,
            capsize=3.0,
            capthick=0.9,
            alpha=0.95,
            zorder=3,
        )
        ax_c_left.errorbar(
            lcoe_mid,
            y,
            xerr=[[lcoe_mid - float(lcoe_q["p2_5"])], [float(lcoe_q["p97_5"]) - lcoe_mid]],
            fmt="o",
            markersize=6.3,
            color=color,
            markerfacecolor="white",
            markeredgecolor=color,
            markeredgewidth=1.5,
            elinewidth=0.9,
            capsize=3.0,
            capthick=0.9,
            alpha=0.95,
            zorder=4,
        )

        y0 = y - bar_h / 2.0
        y1 = y + bar_h / 2.0
        ax_c_right.barh(
            y=y0,
            width=elec_mid,
            height=bar_h,
            color=color,
            alpha=0.78,
            edgecolor="black",
            linewidth=0.5,
            xerr=np.array([[elec_mid - float(elec_q["p2_5"])], [float(elec_q["p97_5"]) - elec_mid]]),
            error_kw={"elinewidth": 0.9, "ecolor": "black", "capsize": 3.0, "capthick": 0.9, "alpha": 0.95},
        )
        ax_c_right.barh(
            y=y1,
            width=export_mid,
            height=bar_h,
            color=color,
            alpha=0.38,
            edgecolor="black",
            linewidth=0.5,
            hatch="//",
            xerr=np.array([[export_mid - float(export_q["p2_5"])], [float(export_q["p97_5"]) - export_mid]]),
            error_kw={"elinewidth": 0.9, "ecolor": "black", "capsize": 3.0, "capthick": 0.9, "alpha": 0.95},
        )

    ax_c_left.set_yticks(y_positions)
    ax_c_left.set_yticklabels([CITY_DISPLAY_NAMES.get(city, city) for city in ordered_cities], fontsize=11)
    ax_c_left.invert_yaxis()
    ax_c_left.grid(axis="x", linestyle="--", alpha=0.25)
    ax_c_left.set_xlabel("Value ($/kWh)", fontsize=11)
    ax_c_left.set_ylabel("")
    ax_c_left.tick_params(axis="x", labelsize=12)
    ax_c_left.tick_params(
        axis="both",
        which="both",
        bottom=True,
        left=True,
        top=False,
        right=False,
        length=3.5,
        width=0.8,
        color="#555555",
        direction="out",
    )

    ax_c_right.grid(axis="x", linestyle="--", alpha=0.25)
    ax_c_right.set_xlabel("Rate ($/kWh)", fontsize=11)
    ax_c_right.tick_params(
        axis="both",
        which="both",
        bottom=True,
        left=False,
        top=False,
        right=False,
        length=3.5,
        width=0.8,
        color="#555555",
        direction="out",
        labelsize=12,
        labelleft=False,
    )

    ax_c_left.set_xlim(0.0, left_max * 1.08)
    ax_c_right.set_xlim(0.0, right_max * 1.04)

    legend_handles = [
        Line2D([0], [0], marker="o", linestyle="None", markersize=7, markerfacecolor="#4a4a4a", markeredgecolor="black", label="Blended Solar Value"),
        Line2D([0], [0], marker="o", linestyle="None", markersize=7, markerfacecolor="white", markeredgecolor="#4a4a4a", markeredgewidth=1.5, label="LCOE"),
        Patch(facecolor="#7f7f7f", edgecolor="black", linewidth=0.5, alpha=0.78, label="Electricity Rate"),
        Patch(facecolor="#7f7f7f", edgecolor="black", linewidth=0.5, alpha=0.38, hatch="//", label="Export Rate"),
    ]
    fig.legend(
        handles=legend_handles,
        loc="lower center",
        ncol=4,
        frameon=False,
        bbox_to_anchor=(0.5, -0.05),
        fontsize=10,
        handlelength=1.6,
        columnspacing=1.4,
        borderaxespad=0.0,
    )

    for ax in [ax_c_left, ax_c_right]:
        ax.spines["left"].set_visible(True)
        ax.spines["bottom"].set_visible(True)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.spines["left"].set_linewidth(0.8)
        ax.spines["bottom"].set_linewidth(0.8)
        ax.spines["left"].set_color("#555555")
        ax.spines["bottom"].set_color("#555555")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    city_results, summary_df = build_uncertainty_results()
    fig_a_path = BORDER_ROOT / "manuscript" / "figures" / "supplement" / "fig_s2_economic_uncertainty_capex_npv.pdf"
    csv_path = BORDER_ROOT / "manuscript" / "outputs" / "figure4_uncertainty_summary.csv"
    plot_panel_a(city_results, fig_a_path)
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    summary_df.to_csv(csv_path, index=False)
    print(f"Saved supplementary uncertainty figure to: {fig_a_path}")
    print(f"Saved uncertainty summary CSV to: {csv_path}")


if __name__ == "__main__":
    main()

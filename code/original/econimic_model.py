import os
from pathlib import Path

os.environ.setdefault("MPLCONFIGDIR", "/tmp/matplotlib")

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt


THIS_FILE = Path(__file__).resolve()
if THIS_FILE.parent.name == "script" and THIS_FILE.parents[1].name == "manuscript":
    BORDER_ROOT = THIS_FILE.parents[2]
else:
    BORDER_ROOT = THIS_FILE.parents[2]


SOURCE_TABLE_PATH = BORDER_ROOT / "evidence/v1_verified_data/economic_model_input_source_table.csv"


def _norm_city(value: str) -> str:
    return "".join(str(value).strip().lower().replace("_", " ").replace("-", " ").split())


def load_city_inputs_from_source_table(
    source_table_path: Path = SOURCE_TABLE_PATH,
) -> dict[str, dict[str, float]]:
    """Load city-level PV economic inputs from the manuscript source table.

    Expected variables (input_variable column):
    - cost_per_W (USD/Wp)
    - CAPEX_reduction (fraction)
    - electricity_rate (USD/kWh)
    - export_rate (USD/kWh)
    - annual_yield (kWh/kWp/year)
    """

    df = pd.read_csv(source_table_path)
    required_cols = {"city", "input_variable", "manuscript_value"}
    missing = required_cols - set(df.columns)
    if missing:
        raise ValueError(
            f"Source table is missing required columns {sorted(missing)}: {source_table_path}"
        )

    df = df.dropna(subset=["city", "input_variable", "manuscript_value"]).copy()
    df["city"] = df["city"].astype(str).str.strip()
    df["input_variable"] = df["input_variable"].astype(str).str.strip()
    df["manuscript_value"] = pd.to_numeric(df["manuscript_value"], errors="coerce")
    df = df.dropna(subset=["manuscript_value"]).copy()

    variable_map = {
        "cost_per_W": "cost_per_watt",
        "CAPEX_reduction": "capex_reduction",
        "electricity_rate": "elec_rate",
        "residential_electricity_rate": "residential_elec_rate",
        "non_residential_electricity_rate": "non_residential_elec_rate",
        "export_rate": "export_rate",
        "annual_yield": "pv_yield_kwh_per_kw_year",
    }

    city_alias = {
        # Model uses Ciudad Juarez; the source table uses Juarez.
        "juarez": "Ciudad Juarez",
    }

    city_inputs: dict[str, dict[str, float]] = {}
    for _, row in df.iterrows():
        src_city = str(row["city"]).strip()
        dst_city = city_alias.get(_norm_city(src_city), src_city)

        input_variable = str(row["input_variable"]).strip()
        if input_variable not in variable_map:
            continue

        dst_key = variable_map[input_variable]
        city_inputs.setdefault(dst_city, {})[dst_key] = float(row["manuscript_value"])

    return city_inputs


def compute_irr(cash_flows, guess=0.08, tol=1e-6, max_iter=1000):
    """
    Compute IRR using Newton-Raphson.
    Returns np.nan if no valid IRR is found.
    """
    r = guess
    for _ in range(max_iter):
        npv = sum(cf / (1 + r) ** t for t, cf in enumerate(cash_flows))
        d_npv = sum(
            -t * cf / (1 + r) ** (t + 1)
            for t, cf in enumerate(cash_flows)
            if t > 0
        )

        if abs(d_npv) < 1e-12:
            return np.nan

        new_r = r - npv / d_npv
        if abs(new_r - r) < tol:
            return new_r if new_r > -0.9999 else np.nan
        r = new_r

    return np.nan


def calculate_discounted_payback(initial_cost, annual_cashflows, discount_rate):
    """
    Discounted payback period.
    Returns np.inf if cash flows never recover the initial investment.
    """
    cumulative = -initial_cost
    for t, cf in enumerate(annual_cashflows, start=1):
        discounted_cf = cf / (1 + discount_rate) ** t
        prev_cumulative = cumulative
        cumulative += discounted_cf

        if cumulative >= 0:
            if discounted_cf == 0:
                return float(t)
            fraction = (0 - prev_cumulative) / discounted_cf
            return round((t - 1) + fraction, 2)

    return np.inf


def get_border_group(city):
    border_groups = {
        "San Diego": "US-MX",
        "Tijuana": "US-MX",
        "El Paso": "US-MX",
        "Ciudad Juarez": "US-MX",
        "Shenzhen": "CN-HK",
        "Hong Kong": "CN-HK",
        "Singapore": "SG-MY",
        "Johor Bahru": "SG-MY",
        "Nice": "FR-MC",
        "Monaco": "FR-MC",
        "Vienna": "AT-SK",
        "Bratislava": "AT-SK",
    }
    return border_groups.get(city, "Other")


def calculate_solar_economics(city_data, system_size_kw=5, years=25, discount_rate=0.05):
    results = {}
    detailed_results = {}

    for city, params in city_data.items():
        gross_cost = system_size_kw * params["cost_per_watt"] * 1000
        capex_reduction = params.get("capex_reduction", 0.0)
        net_cost = gross_cost * (1 - capex_reduction)

        annual_yield = params["pv_yield_kwh_per_kw_year"]
        degradation = params.get("degradation_rate", 0.005)
        production = [
            system_size_kw * annual_yield * ((1 - degradation) ** t)
            for t in range(years)
        ]

        self_consumption_ratio = params.get("self_consumption_ratio", 0.7)
        export_ratio = 1 - self_consumption_ratio
        elec_rate = params["elec_rate"]
        export_rate = params["export_rate"]

        savings_per_kwh = elec_rate * self_consumption_ratio + export_rate * export_ratio
        annual_savings = [p * savings_per_kwh for p in production]

        om_rate = params.get("om_rate", 0.01)
        annual_om = [gross_cost * om_rate for _ in range(years)]
        annual_cashflows = [annual_savings[t] - annual_om[t] for t in range(years)]

        npv_costs = net_cost + sum(
            annual_om[t] / (1 + discount_rate) ** (t + 1)
            for t in range(years)
        )
        npv_energy = sum(
            production[t] / (1 + discount_rate) ** (t + 1)
            for t in range(years)
        )
        lcoe = npv_costs / npv_energy if npv_energy > 0 else np.nan

        npv = -net_cost + sum(
            annual_cashflows[t] / (1 + discount_rate) ** (t + 1)
            for t in range(years)
        )

        cash_flows = [-net_cost] + annual_cashflows
        irr = compute_irr(cash_flows)

        year1_net_benefit = annual_cashflows[0]
        simple_payback = net_cost / year1_net_benefit if year1_net_benefit > 0 else np.inf

        discounted_payback = calculate_discounted_payback(
            initial_cost=net_cost,
            annual_cashflows=annual_cashflows,
            discount_rate=discount_rate,
        )

        compensation_ratio = export_rate / elec_rate if elec_rate > 0 else np.nan
        discounted_cashflows = [
            cf / (1 + discount_rate) ** t
            for t, cf in enumerate(annual_cashflows, start=1)
        ]
        cumulative_discounted_cashflows = np.cumsum([-net_cost] + discounted_cashflows)

        results[city] = {
            "Border Group": get_border_group(city),
            "Net CAPEX ($)": round(net_cost, 0),
            "Gross CAPEX ($)": round(gross_cost, 0),
            "LCOE ($/kWh)": round(lcoe, 4) if pd.notna(lcoe) else np.nan,
            "NPV ($)": round(npv, 0),
            "IRR (%)": round(irr * 100, 2) if pd.notna(irr) else np.nan,
            "Simple Payback (Years)": round(simple_payback, 2) if np.isfinite(simple_payback) else "No payback",
            "Discounted Payback (Years)": round(discounted_payback, 2) if np.isfinite(discounted_payback) else "No payback",
            "Compensation Ratio": round(compensation_ratio, 3) if pd.notna(compensation_ratio) else np.nan,
            "Self-consumption Ratio": round(self_consumption_ratio, 2),
            "Export Ratio": round(export_ratio, 2),
            "PV Yield (kWh/kW/year)": round(annual_yield, 0),
            "Electricity Rate ($/kWh)": round(elec_rate, 3),
            "Export Rate ($/kWh)": round(export_rate, 3),
            "Blended Value of Solar ($/kWh)": round(savings_per_kwh, 3),
            "CAPEX Reduction": round(capex_reduction, 3),
            "Degradation Rate": round(degradation, 4),
            "O&M Rate": round(om_rate, 3),
            "Year-1 Production (kWh)": round(production[0], 0),
            "Year-1 Savings ($)": round(annual_savings[0], 0),
            "Year-1 O&M ($)": round(annual_om[0], 0),
            "Year-1 Net Cash Flow ($)": round(annual_cashflows[0], 0),
        }

        detailed_results[city] = {
            "years": list(range(0, years + 1)),
            "production": production,
            "annual_savings": annual_savings,
            "annual_om": annual_om,
            "annual_cashflows": annual_cashflows,
            "discounted_cashflows": discounted_cashflows,
            "cumulative_discounted_cashflows": cumulative_discounted_cashflows.tolist(),
        }

    return pd.DataFrame(results).T, detailed_results


def plot_grouped_bars(ax, data, value_col, title, xlabel, color, ascending=False):
    plot_data = data.sort_values(value_col, ascending=ascending)
    ax.barh(plot_data.index, plot_data[value_col], color=color, alpha=0.9)
    ax.set_title(title)
    ax.set_xlabel(xlabel)
    ax.grid(axis="x", linestyle="--", alpha=0.3)


def create_visualizations(summary_df, detailed_results, output_dir):
    output_dir.mkdir(parents=True, exist_ok=True)

    numeric_cols = [
        "Net CAPEX ($)",
        "Gross CAPEX ($)",
        "LCOE ($/kWh)",
        "NPV ($)",
        "IRR (%)",
        "Compensation Ratio",
        "Self-consumption Ratio",
        "Export Ratio",
        "PV Yield (kWh/kW/year)",
        "Electricity Rate ($/kWh)",
        "Export Rate ($/kWh)",
        "Blended Value of Solar ($/kWh)",
        "CAPEX Reduction",
        "Degradation Rate",
        "O&M Rate",
        "Year-1 Production (kWh)",
        "Year-1 Savings ($)",
        "Year-1 O&M ($)",
        "Year-1 Net Cash Flow ($)",
    ]
    plot_df = summary_df.copy()
    for col in numeric_cols:
        plot_df[col] = pd.to_numeric(plot_df[col], errors="coerce")

    payback_df = summary_df.copy()
    payback_df["Discounted Payback (Years)"] = pd.to_numeric(
        payback_df["Discounted Payback (Years)"],
        errors="coerce",
    )

    metrics_fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    plot_grouped_bars(
        axes[0, 0], plot_df, "NPV ($)", "Net Present Value", "NPV ($)", "#1f77b4"
    )
    plot_grouped_bars(
        axes[0, 1], plot_df, "IRR (%)", "Internal Rate of Return", "IRR (%)", "#2ca02c"
    )
    plot_grouped_bars(
        axes[1, 0],
        plot_df,
        "LCOE ($/kWh)",
        "Levelized Cost of Energy",
        "LCOE ($/kWh)",
        "#ff7f0e",
        ascending=True,
    )
    plot_grouped_bars(
        axes[1, 1],
        payback_df.dropna(subset=["Discounted Payback (Years)"]),
        "Discounted Payback (Years)",
        "Discounted Payback Period",
        "Years",
        "#d62728",
        ascending=True,
    )
    metrics_fig.suptitle("Key Solar Economics Metrics by City", fontsize=16, y=0.98)
    metrics_fig.tight_layout()
    metrics_fig.savefig(
        output_dir / "economic_metrics_overview.png",
        dpi=220,
        bbox_inches="tight",
    )
    plt.close(metrics_fig)

    drivers_fig, axes = plt.subplots(2, 3, figsize=(20, 12))
    plot_grouped_bars(
        axes[0, 0], plot_df, "Net CAPEX ($)", "Net CAPEX", "USD", "#4c78a8"
    )
    plot_grouped_bars(
        axes[0, 1],
        plot_df,
        "Blended Value of Solar ($/kWh)",
        "Blended Value of Solar",
        "$/kWh",
        "#f58518",
    )
    plot_grouped_bars(
        axes[0, 2],
        plot_df,
        "PV Yield (kWh/kW/year)",
        "PV Yield",
        "kWh/kW/year",
        "#54a24b",
    )
    plot_grouped_bars(
        axes[1, 0],
        plot_df,
        "Year-1 Production (kWh)",
        "Year-1 Production",
        "kWh",
        "#e45756",
    )
    plot_grouped_bars(
        axes[1, 1],
        plot_df,
        "Year-1 Savings ($)",
        "Year-1 Savings",
        "USD",
        "#72b7b2",
    )
    plot_grouped_bars(
        axes[1, 2],
        plot_df,
        "Year-1 Net Cash Flow ($)",
        "Year-1 Net Cash Flow",
        "USD",
        "#b279a2",
    )
    drivers_fig.suptitle("Key Intermediate Drivers from the Economic Model", fontsize=16, y=0.98)
    drivers_fig.tight_layout()
    drivers_fig.savefig(
        output_dir / "economic_drivers_overview.png",
        dpi=220,
        bbox_inches="tight",
    )
    plt.close(drivers_fig)

    cashflow_fig, ax = plt.subplots(figsize=(16, 9))
    for city, series in detailed_results.items():
        ax.plot(
            series["years"],
            series["cumulative_discounted_cashflows"],
            linewidth=2,
            label=f"{city} ({get_border_group(city)})",
        )
    ax.axhline(0, color="black", linestyle="--", linewidth=1)
    ax.set_title("Cumulative Discounted Cash Flow over Project Lifetime")
    ax.set_xlabel("Year")
    ax.set_ylabel("Cumulative Discounted Cash Flow ($)")
    ax.grid(True, linestyle="--", alpha=0.3)
    ax.legend(loc="center left", bbox_to_anchor=(1.02, 0.5), frameon=False)
    cashflow_fig.tight_layout()
    cashflow_fig.savefig(
        output_dir / "discounted_cashflow_profiles.png",
        dpi=220,
        bbox_inches="tight",
    )
    plt.close(cashflow_fig)

    scatter_fig, ax = plt.subplots(figsize=(12, 8))
    bubble_sizes = plot_df["Year-1 Net Cash Flow ($)"].fillna(0).clip(lower=0) / 3 + 30
    scatter = ax.scatter(
        plot_df["Net CAPEX ($)"],
        plot_df["NPV ($)"],
        s=bubble_sizes,
        c=plot_df["IRR (%)"],
        cmap="viridis",
        alpha=0.85,
        edgecolors="black",
        linewidth=0.4,
    )
    for city, row in plot_df.iterrows():
        ax.annotate(
            city,
            (row["Net CAPEX ($)"], row["NPV ($)"]),
            xytext=(6, 4),
            textcoords="offset points",
            fontsize=9,
        )
    cbar = scatter_fig.colorbar(scatter, ax=ax)
    cbar.set_label("IRR (%)")
    ax.set_title("Capital Cost vs. Profitability")
    ax.set_xlabel("Net CAPEX ($)")
    ax.set_ylabel("NPV ($)")
    ax.grid(True, linestyle="--", alpha=0.3)
    scatter_fig.tight_layout()
    scatter_fig.savefig(
        output_dir / "capex_vs_profitability.png",
        dpi=220,
        bbox_inches="tight",
    )
    plt.close(scatter_fig)


_DEFAULT_MODEL_PARAMS = {
    "self_consumption_ratio": 0.70,
    "degradation_rate": 0.005,
    "om_rate": 0.01,
}


SEGMENT_ELECTRICITY_RATE_KEYS = {
    "all_building_baseline": "elec_rate",
    "residential_tariff_proxy": "residential_elec_rate",
    "non_residential_tariff_proxy": "non_residential_elec_rate",
}


def build_city_solar_data_checked(
    source_table_path: Path = SOURCE_TABLE_PATH,
) -> dict[str, dict[str, float]]:
    source_inputs = load_city_inputs_from_source_table(source_table_path)

    # If the source table does not contain a city, keep a conservative fallback.
    # This prevents downstream scripts from crashing during partial edits.
    fallback = {
        "San Diego": {"cost_per_watt": 2.6, "capex_reduction": 0.20, "elec_rate": 0.39, "export_rate": 0.03, "pv_yield_kwh_per_kw_year": 1650},
        "Tijuana": {"cost_per_watt": 1.6, "capex_reduction": 0.10, "elec_rate": 0.119, "export_rate": 0.119, "pv_yield_kwh_per_kw_year": 1650},
        "El Paso": {"cost_per_watt": 2.34, "capex_reduction": 0.20, "elec_rate": 0.13, "export_rate": 0.02, "pv_yield_kwh_per_kw_year": 1750},
        "Ciudad Juarez": {"cost_per_watt": 1.6, "capex_reduction": 0.10, "elec_rate": 0.119, "export_rate": 0.119, "pv_yield_kwh_per_kw_year": 1750},
        "Shenzhen": {"cost_per_watt": 0.6, "capex_reduction": 0.15, "elec_rate": 0.077, "export_rate": 0.07, "pv_yield_kwh_per_kw_year": 1350},
        "Hong Kong": {"cost_per_watt": 2.5, "capex_reduction": 0.20, "elec_rate": 0.183, "export_rate": 0.35, "pv_yield_kwh_per_kw_year": 1350},
        "Singapore": {"cost_per_watt": 1.2, "capex_reduction": 0.10, "elec_rate": 0.241, "export_rate": 0.219, "pv_yield_kwh_per_kw_year": 1450},
        "Johor Bahru": {"cost_per_watt": 1.0, "capex_reduction": 0.15, "elec_rate": 0.057, "export_rate": 0.07, "pv_yield_kwh_per_kw_year": 1450},
        "Nice": {"cost_per_watt": 2.2, "capex_reduction": 0.20, "elec_rate": 0.278, "export_rate": 0.173, "pv_yield_kwh_per_kw_year": 1500},
        "Monaco": {"cost_per_watt": 2.6, "capex_reduction": 0.20, "elec_rate": 0.28, "export_rate": 0.173, "pv_yield_kwh_per_kw_year": 1500},
        "Vienna": {"cost_per_watt": 2.2, "capex_reduction": 0.20, "elec_rate": 0.292, "export_rate": 0.216, "pv_yield_kwh_per_kw_year": 1150},
        "Bratislava": {"cost_per_watt": 1.9, "capex_reduction": 0.10, "elec_rate": 0.194, "export_rate": 0.173, "pv_yield_kwh_per_kw_year": 1150},
    }

    cities = list(fallback.keys())
    city_data: dict[str, dict[str, float]] = {}
    for city in cities:
        params = dict(fallback[city])
        params.update(_DEFAULT_MODEL_PARAMS)
        if city in source_inputs:
            params.update(source_inputs[city])
        city_data[city] = params

    return city_data


def build_segment_solar_data(
    city_data: dict[str, dict[str, float]],
) -> dict[str, dict[str, float]]:
    """Create tariff-class variants by replacing only the import electricity rate.

    The segment variants are diagnostic tariff-class sensitivities. They retain
    the baseline cost, export compensation, yield, self-consumption and system
    assumptions, so they should not be read as full residential or commercial
    project-finance models.
    """

    segment_data: dict[str, dict[str, float]] = {}
    for city, params in city_data.items():
        for segment, rate_key in SEGMENT_ELECTRICITY_RATE_KEYS.items():
            segment_params = dict(params)
            segment_params["elec_rate"] = params.get(rate_key, params["elec_rate"])
            segment_params["segment"] = segment
            segment_data[f"{city}::{segment}"] = segment_params
    return segment_data


def calculate_segment_solar_economics(
    city_data: dict[str, dict[str, float]],
    system_size_kw: float = 5,
    years: int = 25,
    discount_rate: float = 0.05,
) -> pd.DataFrame:
    segment_data = build_segment_solar_data(city_data)
    segment_results, _ = calculate_solar_economics(
        city_data=segment_data,
        system_size_kw=system_size_kw,
        years=years,
        discount_rate=discount_rate,
    )

    rows = []
    for compound_key, row in segment_results.iterrows():
        city, segment = compound_key.split("::", 1)
        record = row.to_dict()
        record["City"] = city
        record["Segment"] = segment
        record["Border Group"] = get_border_group(city)
        record["Tariff-class electricity rate ($/kWh)"] = record[
            "Electricity Rate ($/kWh)"
        ]
        rows.append(record)

    columns = ["City", "Segment"] + [
        col for col in segment_results.columns if col != "Border Group"
    ]
    columns.insert(2, "Border Group")
    return pd.DataFrame(rows)[columns]


city_solar_data_checked = build_city_solar_data_checked()


def main() -> None:
    economic_analysis, detailed_analysis = calculate_solar_economics(
        city_data=city_solar_data_checked,
        system_size_kw=5,
        years=25,
        discount_rate=0.05,
    )
    segment_economic_analysis = calculate_segment_solar_economics(
        city_data=city_solar_data_checked,
        system_size_kw=5,
        years=25,
        discount_rate=0.05,
    )

    output_paths = [
        BORDER_ROOT / "manuscript" / "data" / "PV_Eco_model" / "economic_analysis_results.csv",
        BORDER_ROOT / "factors" / "economic_analysis_results.csv",
        Path(__file__).with_name("economic_analysis_results.csv"),
    ]
    for output_path in output_paths:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        economic_analysis.to_csv(output_path, index_label="City")

    segment_output_paths = [
        BORDER_ROOT / "manuscript" / "data" / "PV_Eco_model" / "segment_economic_analysis_results.csv",
        Path(__file__).with_name("segment_economic_analysis_results.csv"),
    ]
    for output_path in segment_output_paths:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        segment_economic_analysis.to_csv(output_path, index=False)

    figures_dir = Path(__file__).with_name("economic_figures")
    create_visualizations(economic_analysis, detailed_analysis, figures_dir)

    pd.set_option("display.max_columns", None)
    pd.set_option("display.max_rows", None)
    print(economic_analysis)
    print("\nSaved CSV to:")
    for output_path in output_paths:
        print(f" - {output_path}")
    print("\nSaved segment CSV to:")
    for output_path in segment_output_paths:
        print(f" - {output_path}")
    print(f"Saved figures to: {figures_dir}")


if __name__ == "__main__":
    main()

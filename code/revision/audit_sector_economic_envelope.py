#!/usr/bin/env python3
"""Build an independent residential and small-commercial PV economic envelope.

This calculation supports an independent Supplementary sensitivity. The calculation separates
project scale, installed-cost scaling, tariff class, export treatment, capital
support and self-consumption scenarios. It deliberately excludes demand-charge
savings, batteries, financing, roof geometry and historical installation terms.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.optimize import brentq


ROOT = Path(__file__).resolve().parents[2]
SOURCE_12 = ROOT / "tables/table_s1_economic_model_city_inputs.csv"
SOURCE_14 = ROOT / "evidence/v1_verified_data/economic_results_14cities.csv"
PV_METRICS = ROOT / "evidence/v1_verified_data/city_pv_metrics_14cities.csv"
OUTPUT = ROOT / "outputs/audit_reports/sector_economic_envelope"

YEARS = 25
DEGRADATION = 0.005
OM_RATE = 0.01


@dataclass(frozen=True)
class CitySectorInput:
    city: str
    city_key: str
    sector: str
    system_size_kw: float
    cost_per_w_usd: float
    import_rate_usd_per_kwh: float
    export_low_usd_per_kwh: float
    export_mid_usd_per_kwh: float
    export_high_usd_per_kwh: float
    annual_yield_kwh_per_kw: float
    support_fraction: float
    fixed_support_usd: float
    value_model: str
    cost_basis: str
    tariff_basis: str
    support_basis: str


CITY_KEY = {
    "Vienna": "vienna",
    "Bratislava": "bratislava",
    "Singapore": "singapore",
    "Johor Bahru": "johorbahru",
    "San Diego": "sandiego",
    "Tijuana": "tijuana",
    "Detroit": "detroit",
    "Windsor": "windsor",
    "El Paso": "elpaso",
    "Ciudad Juarez": "juarez",
    "Hong Kong": "hongkong",
    "Shenzhen": "shenzhen",
    "Monaco": "monaco",
    "Nice": "nice",
}


PAIRS = [
    ("Vienna--Bratislava", "Vienna", "Bratislava", "primary"),
    ("Singapore--Johor Bahru", "Singapore", "Johor Bahru", "primary"),
    ("San Diego--Tijuana", "San Diego", "Tijuana", "primary"),
    ("El Paso--Ciudad Juarez", "El Paso", "Ciudad Juarez", "primary"),
    ("Hong Kong--Shenzhen", "Hong Kong", "Shenzhen", "primary"),
    ("Monaco--Nice", "Monaco", "Nice", "primary"),
    ("Detroit--Windsor", "Detroit", "Windsor", "supplementary candidate"),
]


# Small-commercial to residential installed-cost ratios. Direct ratios use
# authoritative segmented market tables. A pooled 0.80 ratio is the rounded
# median-calibrated transfer used where current local segment costs are absent.
COMMERCIAL_COST_RATIO = {
    "Vienna": (1000 / 1551, "direct Austria 2024 ratio"),
    "Bratislava": (0.80, "pooled transferred ratio"),
    "Singapore": (0.80, "pooled transferred ratio"),
    "Johor Bahru": (4.43 / 5.58, "Malaysia 2019 ratio applied to current anchor"),
    "San Diego": (3.4 / 4.2, "California 2023 observed ratio"),
    "Tijuana": (0.80, "pooled transferred ratio"),
    "Detroit": (3.28 / 4.04, "United States 2023 observed ratio"),
    "Windsor": (2.60 / 3.10, "Canada 2024 midpoint ratio"),
    "El Paso": (2.8 / 4.1, "Texas 2023 observed ratio"),
    "Ciudad Juarez": (0.80, "pooled transferred ratio"),
    "Hong Kong": (0.80, "pooled transferred ratio"),
    "Shenzhen": (3.3 / 3.4, "China 2024 direct ratio"),
    "Monaco": (0.80, "pooled transferred ratio"),
    "Nice": (0.80, "pooled transferred ratio"),
}


SELF_CONSUMPTION = {
    "Residential": {"low": 0.30, "middle": 0.50, "high": 0.70},
    "Small commercial": {"low": 0.50, "middle": 0.70, "high": 0.90},
}


def normalize_city(value: str) -> str:
    if value == "Juarez":
        return "Ciudad Juarez"
    return value


def irr(cash_flows: list[float]) -> float:
    """Return the first economically relevant IRR root, or NaN."""

    def npv(rate: float) -> float:
        return sum(value / (1.0 + rate) ** year for year, value in enumerate(cash_flows))

    grid = np.concatenate(
        [
            np.linspace(-0.99, 0.0, 300, endpoint=False),
            np.linspace(0.0, 1.0, 1001),
            np.linspace(1.01, 10.0, 500),
        ]
    )
    previous_rate = float(grid[0])
    previous_value = npv(previous_rate)
    for rate in grid[1:]:
        value = npv(float(rate))
        if np.isfinite(previous_value) and np.isfinite(value):
            if previous_value == 0:
                return previous_rate
            if previous_value * value < 0:
                return float(brentq(npv, previous_rate, float(rate)))
        previous_rate = float(rate)
        previous_value = value
    return np.nan


def load_base_inputs() -> dict[str, dict[str, float]]:
    twelve = pd.read_csv(SOURCE_12)
    fourteen = pd.read_csv(SOURCE_14)
    base: dict[str, dict[str, float]] = {}
    for row in twelve.to_dict("records"):
        city = normalize_city(str(row["City"]))
        base[city] = {
            "cost_per_w": float(row["cost_per_watt_usd"]),
            "res_rate": float(row["residential_electricity_rate_usd_per_kwh"]),
            "commercial_rate": float(row["non_residential_electricity_rate_usd_per_kwh"]),
            "export_rate": float(row["export_rate_usd_per_kwh"]),
            "yield": float(row["pv_yield_kwh_per_kw_year"]),
            "support_fraction": float(row["capex_reduction"]),
        }

    for city in ("Detroit", "Windsor"):
        row = fourteen.loc[fourteen["City"].eq(city)].iloc[0]
        base[city] = {
            "cost_per_w": float(row["Gross CAPEX ($)"]) / 5000.0,
            "res_rate": float(row["Electricity Rate ($/kWh)"]),
            "commercial_rate": (
                0.1401 if city == "Detroit" else float(row["Electricity Rate ($/kWh)"])
            ),
            "export_rate": float(row["Export Rate ($/kWh)"]),
            "yield": float(row["PV Yield (kWh/kW/year)"]),
            "support_fraction": float(row["CAPEX Reduction"]),
        }
    return base


def export_values(city: str, sector: str, base: dict[str, float]) -> tuple[float, float, float, str]:
    import_rate = base["res_rate"] if sector == "Residential" else base["commercial_rate"]

    if city == "Singapore" and sector == "Small commercial":
        # 2024 monthly USEP range of SGD 105 to 288/MWh, converted at the
        # approximate USD/SGD factor implicit in the audited tariff table.
        return 0.078, 0.146, 0.214, "EMA contestable-consumer wholesale-price range"
    if city == "Johor Bahru" and sector == "Residential":
        return import_rate, import_rate, import_rate, "NEM Rakyat one-for-one tariff offset"
    if city == "Johor Bahru" and sector == "Small commercial":
        return 0.070, 0.070, 0.070, "NOVA System Marginal Price proxy"
    if city in {"Tijuana", "Ciudad Juarez"}:
        return import_rate, import_rate, import_rate, "Mexico monthly net-metering tariff-class proxy"
    if city == "Windsor":
        return import_rate, import_rate, import_rate, "Ontario net-metering variable bill-credit proxy"
    if city == "Hong Kong":
        # Gross FiT: HKD 4/kWh at <=10 kW; HKD 3/kWh at >10 to <=200 kW.
        fit = 4.0 / 7.8 if sector == "Residential" else 3.0 / 7.8
        return fit, fit, fit, "Hong Kong gross FiT capacity band"
    value = float(base["export_rate"])
    return value, value, value, "current audited city export input"


def policy_support(city: str, sector: str, base: dict[str, float]) -> tuple[float, float, str]:
    """Return fractional support, fixed USD support and evidence label."""
    if city == "Singapore":
        return 0.0, 0.0, "EMA states no general generation subsidy"
    if city == "Johor Bahru":
        return 0.0, 0.0, "NEM value represented through bill credits, not CAPEX reduction"
    if city == "Hong Kong":
        return 0.0, 0.0, "FiT represented through gross generation revenue"
    if city == "Windsor":
        if sector == "Residential":
            gross = base["cost_per_w"] * 5000.0
            central_14 = pd.read_csv(SOURCE_14)
            row = central_14.loc[central_14["City"].eq("Windsor")].iloc[0]
            fixed = gross - float(row["Net CAPEX ($)"])
            return 0.0, fixed, "realized residential grant from audited central scenario"
        return 0.0, 0.0, "residential grant excluded from commercial scenario"
    if city in {"San Diego", "El Paso", "Detroit"}:
        return 0.30, 0.0, "study-vintage US 30% credit realization scenario"
    return float(base["support_fraction"]), 0.0, "current central capital-support assumption"


def build_inputs() -> list[CitySectorInput]:
    base = load_base_inputs()
    rows: list[CitySectorInput] = []
    for city in CITY_KEY:
        params = base[city]
        for sector, size in (("Residential", 5.0), ("Small commercial", 100.0)):
            ratio, ratio_source = COMMERCIAL_COST_RATIO[city]
            cost = params["cost_per_w"] if sector == "Residential" else params["cost_per_w"] * ratio
            import_rate = params["res_rate"] if sector == "Residential" else params["commercial_rate"]
            export_low, export_mid, export_high, export_basis = export_values(city, sector, params)
            support_fraction, fixed_support, support_basis = policy_support(city, sector, params)
            value_model = "gross_fiT" if city == "Hong Kong" else "self_consumption_plus_export"
            cost_basis = (
                "current 5 kW residential anchor"
                if sector == "Residential"
                else f"current residential anchor times {ratio:.4f}; {ratio_source}"
            )
            tariff_basis = (
                ("2024 Michigan commercial average energy rate; demand charges excluded")
                if city == "Detroit" and sector == "Small commercial"
                else export_basis
            )
            rows.append(
                CitySectorInput(
                    city=city,
                    city_key=CITY_KEY[city],
                    sector=sector,
                    system_size_kw=size,
                    cost_per_w_usd=cost,
                    import_rate_usd_per_kwh=import_rate,
                    export_low_usd_per_kwh=export_low,
                    export_mid_usd_per_kwh=export_mid,
                    export_high_usd_per_kwh=export_high,
                    annual_yield_kwh_per_kw=params["yield"],
                    support_fraction=support_fraction,
                    fixed_support_usd=fixed_support,
                    value_model=value_model,
                    cost_basis=cost_basis,
                    tariff_basis=tariff_basis,
                    support_basis=support_basis,
                )
            )
    return rows


def calculate_scenario(
    item: CitySectorInput,
    self_consumption: float,
    export_rate: float,
    support_case: str,
) -> dict[str, float | str]:
    gross_capex = item.system_size_kw * 1000.0 * item.cost_per_w_usd
    if support_case == "policy_realized":
        support = gross_capex * item.support_fraction + item.fixed_support_usd
    else:
        support = 0.0
    support = min(max(support, 0.0), gross_capex)
    net_capex = gross_capex - support
    annual_om = gross_capex * OM_RATE

    cash_flows = [-net_capex]
    first_year_revenue = np.nan
    for year in range(YEARS):
        production = (
            item.system_size_kw
            * item.annual_yield_kwh_per_kw
            * (1.0 - DEGRADATION) ** year
        )
        if item.value_model == "gross_fiT":
            revenue = production * export_rate
        else:
            blended_value = (
                self_consumption * item.import_rate_usd_per_kwh
                + (1.0 - self_consumption) * export_rate
            )
            revenue = production * blended_value
        if year == 0:
            first_year_revenue = revenue
        cash_flows.append(revenue - annual_om)

    return {
        "gross_capex_usd": gross_capex,
        "support_usd": support,
        "net_capex_usd": net_capex,
        "year1_revenue_usd": first_year_revenue,
        "year1_om_usd": annual_om,
        "irr_pct": irr(cash_flows) * 100.0,
    }


def scenario_table(inputs: list[CitySectorInput]) -> pd.DataFrame:
    rows = []
    for item in inputs:
        export_cases = {
            "low": item.export_low_usd_per_kwh,
            "middle": item.export_mid_usd_per_kwh,
            "high": item.export_high_usd_per_kwh,
        }
        for support_case in ("no_capital_support", "policy_realized"):
            for scr_case, scr in SELF_CONSUMPTION[item.sector].items():
                for export_case, export_rate in export_cases.items():
                    result = calculate_scenario(item, scr, export_rate, support_case)
                    rows.append(
                        {
                            "city": item.city,
                            "city_key": item.city_key,
                            "sector": item.sector,
                            "support_case": support_case,
                            "self_consumption_case": scr_case,
                            "self_consumption_fraction": scr,
                            "export_case": export_case,
                            "system_size_kw": item.system_size_kw,
                            "cost_per_w_usd": item.cost_per_w_usd,
                            "import_rate_usd_per_kwh": item.import_rate_usd_per_kwh,
                            "export_rate_usd_per_kwh": export_rate,
                            "annual_yield_kwh_per_kw": item.annual_yield_kwh_per_kw,
                            "value_model": item.value_model,
                            "cost_basis": item.cost_basis,
                            "tariff_basis": item.tariff_basis,
                            "support_basis": item.support_basis,
                            **result,
                        }
                    )
    return pd.DataFrame(rows)


def input_table(inputs: list[CitySectorInput]) -> pd.DataFrame:
    return pd.DataFrame([item.__dict__ for item in inputs])


def summarize_city_envelopes(scenarios: pd.DataFrame) -> pd.DataFrame:
    keys = ["city", "city_key", "sector", "support_case"]
    summary = (
        scenarios.groupby(keys, sort=False)["irr_pct"]
        .agg(irr_min_pct="min", irr_max_pct="max", scenario_count="size")
        .reset_index()
    )
    central = scenarios[
        scenarios["self_consumption_case"].eq("middle")
        & scenarios["export_case"].eq("middle")
    ][keys + ["irr_pct"]].rename(columns={"irr_pct": "irr_middle_pct"})
    return summary.merge(central, on=keys, how="left")


def observed_sector_leaders() -> dict[tuple[str, str], str]:
    metrics = pd.read_csv(PV_METRICS)
    metrics["City"] = metrics["City"].map(normalize_city)
    result: dict[tuple[str, str], str] = {}
    segment_map = {"Residential": "Residential", "Small commercial": "Non-residential"}
    for pair, first, second, _ in PAIRS:
        for sector, segment in segment_map.items():
            sub = metrics[
                metrics["City"].isin([first, second]) & metrics["Segment"].eq(segment)
            ].set_index("City")
            result[(pair, sector)] = (
                first
                if float(sub.loc[first, "PV utilization (%)"])
                > float(sub.loc[second, "PV utilization (%)"])
                else second
            )
    return result


def pairwise_table(scenarios: pd.DataFrame) -> pd.DataFrame:
    observed = observed_sector_leaders()
    rows = []
    match_keys = [
        "sector",
        "support_case",
        "self_consumption_case",
        "export_case",
    ]
    for pair, first, second, scope in PAIRS:
        first_rows = scenarios[scenarios["city"].eq(first)].set_index(match_keys)
        second_rows = scenarios[scenarios["city"].eq(second)].set_index(match_keys)
        for key in first_rows.index:
            sector, support_case, scr_case, export_case = key
            first_irr = float(first_rows.loc[key, "irr_pct"])
            second_irr = float(second_rows.loc[key, "irr_pct"])
            economic_leader = first if first_irr > second_irr else second
            observed_leader = observed[(pair, sector)]
            rows.append(
                {
                    "pair": pair,
                    "scope": scope,
                    "city_1": first,
                    "city_2": second,
                    "sector": sector,
                    "support_case": support_case,
                    "self_consumption_case": scr_case,
                    "export_case": export_case,
                    "city_1_irr_pct": first_irr,
                    "city_2_irr_pct": second_irr,
                    "economic_leader": economic_leader,
                    "observed_pv_leader": observed_leader,
                    "aligned_with_observed_sector_leader": economic_leader == observed_leader,
                }
            )
    return pd.DataFrame(rows)


def pairwise_summary(pairwise: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for keys, group in pairwise.groupby(
        ["pair", "scope", "sector", "support_case"], sort=False
    ):
        pair, scope, sector, support_case = keys
        leaders = sorted(group["economic_leader"].unique())
        rows.append(
            {
                "pair": pair,
                "scope": scope,
                "sector": sector,
                "support_case": support_case,
                "scenario_count": len(group),
                "economic_leader_count": len(leaders),
                "economic_leaders": "; ".join(leaders),
                "stable_economic_direction": len(leaders) == 1,
                "observed_pv_leader": group["observed_pv_leader"].iloc[0],
                "aligned_scenario_count": int(group["aligned_with_observed_sector_leader"].sum()),
                "alignment_share": float(group["aligned_with_observed_sector_leader"].mean()),
                "irr_gap_min_city1_minus_city2_pp": float(
                    (group["city_1_irr_pct"] - group["city_2_irr_pct"]).min()
                ),
                "irr_gap_max_city1_minus_city2_pp": float(
                    (group["city_1_irr_pct"] - group["city_2_irr_pct"]).max()
                ),
            }
        )
    return pd.DataFrame(rows)


def write_report(
    scenarios: pd.DataFrame,
    envelopes: pd.DataFrame,
    pair_summary: pd.DataFrame,
) -> None:
    primary = pair_summary[pair_summary["scope"].eq("primary")]
    candidate = pair_summary[pair_summary["scope"].ne("primary")]
    stable_primary = int(primary["stable_economic_direction"].sum())
    aligned_primary = int((primary["alignment_share"] == 1.0).sum())

    lines = [
        "# Residential and small-commercial economic envelope results",
        "",
        "This audit calculation supplies the independent Supplementary sector-envelope sensitivity.",
        "",
        "## Design",
        "",
        "Residential projects are represented at 5 kW with self-consumption scenarios of 30%, 50% and 70%. Small-commercial projects are represented at 100 kW with self-consumption scenarios of 50%, 70% and 90%. Every project is evaluated with and without the documented or central capital-support assumption. Singapore commercial exports additionally span the 2024 wholesale-price range. Hong Kong uses the official gross FiT capacity bands.",
        "",
        "Demand-charge savings, batteries, financing, roof geometry and historical installation terms are excluded.",
        "",
        "## High-level result",
        "",
        f"The calculation generated {len(scenarios):,} city-sector scenarios and {len(pair_summary)} pair-sector-support summaries. Among the {len(primary)} primary-pair summaries, {stable_primary} have one economic leader across all matched self-consumption and export cases, and {aligned_primary} align with the observed sector PV leader in every matched case.",
        "",
        "The result should not be described as a sector-specific estimate of realized project returns. It is a robustness screen showing whether pairwise economic direction depends on plausible project-sector assumptions.",
        "",
        "## Pairwise summary",
        "",
        "| Pair | Sector | Support | Economic leader(s) | Stable | Observed PV leader | Alignment share | IRR gap range, city 1 minus city 2 (pp) |",
        "|---|---|---|---|---:|---|---:|---:|",
    ]
    for row in pd.concat([primary, candidate], ignore_index=True).to_dict("records"):
        lines.append(
            "| {pair} | {sector} | {support_case} | {economic_leaders} | {stable} | {observed} | {share:.0%} | {lo:.2f} to {hi:.2f} |".format(
                pair=row["pair"],
                sector=row["sector"],
                support_case=row["support_case"].replace("_", " "),
                economic_leaders=row["economic_leaders"],
                stable="yes" if row["stable_economic_direction"] else "no",
                observed=row["observed_pv_leader"],
                share=row["alignment_share"],
                lo=row["irr_gap_min_city1_minus_city2_pp"],
                hi=row["irr_gap_max_city1_minus_city2_pp"],
            )
        )
    lines.extend(
        [
            "",
            "## Interpretation rule",
            "",
            "A pair-sector result is robust only when one economic leader persists across all matched self-consumption and export cases. Alignment means that this economic leader is the same city as the observed sector PV-utilization leader. A mixed result is evidence against reducing the mapped sector gap to a single economic ordering.",
            "",
            "## Output files",
            "",
            "- `sector_envelope_inputs.csv`: one audited input row per city and sector.",
            "- `sector_envelope_scenarios.csv`: all calculated scenarios.",
            "- `city_sector_irr_envelopes.csv`: minimum, middle and maximum IRR by city, sector and support case.",
            "- `pairwise_sector_alignment.csv`: matched scenario comparisons.",
            "- `pairwise_sector_stability_summary.csv`: compact pairwise audit.",
            "",
        ]
    )
    (OUTPUT / "SECTOR_ENVELOPE_RESULTS.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    inputs = build_inputs()
    inputs_df = input_table(inputs)
    scenarios = scenario_table(inputs)
    envelopes = summarize_city_envelopes(scenarios)
    pairwise = pairwise_table(scenarios)
    summary = pairwise_summary(pairwise)

    inputs_df.to_csv(OUTPUT / "sector_envelope_inputs.csv", index=False)
    scenarios.to_csv(OUTPUT / "sector_envelope_scenarios.csv", index=False)
    envelopes.to_csv(OUTPUT / "city_sector_irr_envelopes.csv", index=False)
    pairwise.to_csv(OUTPUT / "pairwise_sector_alignment.csv", index=False)
    summary.to_csv(OUTPUT / "pairwise_sector_stability_summary.csv", index=False)
    write_report(scenarios, envelopes, summary)

    detroit_central = scenarios[
        scenarios["city"].eq("Detroit")
        & scenarios["sector"].eq("Residential")
        & scenarios["support_case"].eq("policy_realized")
        & scenarios["self_consumption_case"].eq("high")
        & scenarios["export_case"].eq("middle")
    ]["irr_pct"].iloc[0]
    windsor_central = scenarios[
        scenarios["city"].eq("Windsor")
        & scenarios["sector"].eq("Residential")
        & scenarios["support_case"].eq("policy_realized")
        & scenarios["self_consumption_case"].eq("middle")
        & scenarios["export_case"].eq("middle")
    ]["irr_pct"].iloc[0]
    hk_variation = scenarios[
        scenarios["city"].eq("Hong Kong")
        & scenarios["support_case"].eq("no_capital_support")
    ].groupby("sector")["irr_pct"].agg(lambda x: float(x.max() - x.min()))
    checks = {
        "input_rows_28": bool(len(inputs_df) == 28),
        "scenario_rows_504": bool(len(scenarios) == 504),
        "pairwise_rows_252": bool(len(pairwise) == 252),
        "summary_rows_28": bool(len(summary) == 28),
        "all_irr_finite": bool(scenarios["irr_pct"].notna().all()),
        "all_seven_pairs_present": bool(set(summary["pair"]) == {pair[0] for pair in PAIRS}),
        "detroit_residential_high_scr_reproduces_2_677421_pct": bool(abs(detroit_central - 2.677421) < 1e-5),
        "windsor_residential_reproduces_3_006189_pct": bool(abs(windsor_central - 3.006189) < 1e-5),
        "hong_kong_gross_fit_invariant_to_self_consumption": bool((hk_variation < 1e-10).all()),
        "no_support_has_zero_support": bool(
            (scenarios.loc[scenarios["support_case"].eq("no_capital_support"), "support_usd"] == 0).all()
        ),
    }
    (OUTPUT / "sector_envelope_validation_checks.json").write_text(
        json.dumps(checks, indent=2) + "\n", encoding="utf-8"
    )
    assert all(checks.values()), checks
    print(f"Wrote sector-envelope audit to {OUTPUT}")
    print(f"Scenarios: {len(scenarios)}; pairwise comparisons: {len(pairwise)}")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Build Supplementary Fig. S8 and its table and Source Data assets.

The figure reports a stylized residential and small-commercial economic
envelope. It is a sensitivity screen, not an estimate of realized returns.
"""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.colors import Normalize
from matplotlib.patches import Rectangle
import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
AUDIT = ROOT / "outputs/audit_reports/sector_economic_envelope"
FIGURE_DIR = ROOT / "figures/supplementary"
SOURCE_DIR = ROOT / "Source_Data/csv"
NOTES_DIR = ROOT / "Source_Data/figure_notes"
TABLE_DIR = ROOT / "tables"
CHECKS_PATH = ROOT / "Source_Data/source_data_checks_fig_s8_sector_envelope.json"

PAIR_ORDER = [
    "Vienna--Bratislava",
    "Singapore--Johor Bahru",
    "San Diego--Tijuana",
    "El Paso--Ciudad Juarez",
    "Hong Kong--Shenzhen",
    "Monaco--Nice",
    "Detroit--Windsor",
]
CITY_ORDER = [city for pair in PAIR_ORDER for city in pair.split("--")]
SECTOR_ORDER = ["Residential", "Small commercial"]
PAIR_COLORS = ["#8c6bb1", "#d99000", "#2a9d8f", "#4c78a8", "#59a14f", "#d37295", "#7f7f7f"]


def configure_style() -> None:
    mpl.rcParams.update(
        {
            "font.family": "sans-serif",
            "font.sans-serif": ["Liberation Sans", "Arial", "DejaVu Sans"],
            "font.size": 8.0,
            "axes.labelsize": 8.5,
            "xtick.labelsize": 7.3,
            "ytick.labelsize": 7.3,
            "legend.fontsize": 7.2,
            "axes.linewidth": 0.65,
            "xtick.major.width": 0.6,
            "ytick.major.width": 0.6,
            "xtick.major.size": 2.8,
            "ytick.major.size": 0,
        }
    )


def load_data() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    if AUDIT.exists():
        inputs = pd.read_csv(AUDIT / "sector_envelope_inputs.csv")
        envelopes = pd.read_csv(AUDIT / "city_sector_irr_envelopes.csv")
        pair_summary = pd.read_csv(AUDIT / "pairwise_sector_stability_summary.csv")
        comparisons = pd.read_csv(AUDIT / "pairwise_sector_alignment.csv")
    else:
        inputs = pd.read_csv(SOURCE_DIR / "Fig_S8_sector_economic_envelope_inputs.csv")
        envelopes = pd.read_csv(SOURCE_DIR / "Fig_S8_sector_economic_envelope_city.csv")
        pair_summary = pd.read_csv(SOURCE_DIR / "Fig_S8_sector_economic_envelope_pairwise.csv")
        comparisons = pd.read_csv(SOURCE_DIR / "Fig_S8_sector_economic_envelope_comparisons.csv")
    return inputs, envelopes, pair_summary, comparisons


def central_scenarios(comparisons: pd.DataFrame) -> pd.DataFrame:
    return comparisons[
        comparisons["support_case"].eq("policy_realized")
        & comparisons["self_consumption_case"].eq("middle")
        & comparisons["export_case"].eq("middle")
    ].copy()


def build_figure(envelopes: pd.DataFrame, pair_summary: pd.DataFrame, output: Path) -> None:
    configure_style()
    policy = envelopes[envelopes["support_case"].eq("policy_realized")].copy()
    policy["city"] = pd.Categorical(policy["city"], CITY_ORDER, ordered=True)
    policy["sector"] = pd.Categorical(policy["sector"], SECTOR_ORDER, ordered=True)
    policy = policy.sort_values(["city", "sector"])

    fig = plt.figure(figsize=(7.25, 5.55))
    grid = fig.add_gridspec(1, 2, width_ratios=[1.28, 1.0], wspace=0.30)
    ax_a = fig.add_subplot(grid[0, 0])
    ax_b = fig.add_subplot(grid[0, 1])

    pair_by_city = {city: index for index, pair in enumerate(PAIR_ORDER) for city in pair.split("--")}
    offsets = {"Residential": -0.15, "Small commercial": 0.15}
    markers = {"Residential": "o", "Small commercial": "s"}
    for row in policy.itertuples(index=False):
        y = CITY_ORDER.index(str(row.city)) + offsets[str(row.sector)]
        color = PAIR_COLORS[pair_by_city[str(row.city)]]
        ax_a.plot(
            [row.irr_min_pct, row.irr_max_pct],
            [y, y],
            color=color,
            linewidth=2.0,
            solid_capstyle="round",
            zorder=2,
        )
        ax_a.scatter(
            row.irr_middle_pct,
            y,
            s=24,
            marker=markers[str(row.sector)],
            facecolor="white",
            edgecolor=color,
            linewidth=1.0,
            zorder=3,
        )

    ax_a.axvline(0, color="#777777", linewidth=0.65, linestyle=(0, (2, 2)), zorder=1)
    ax_a.set_yticks(np.arange(len(CITY_ORDER)), CITY_ORDER)
    ax_a.invert_yaxis()
    ax_a.set_xlabel("Modelled IRR under policy-realized support (%)")
    ax_a.set_ylabel("Cities")
    ax_a.grid(axis="x", color="#e6e6e6", linewidth=0.6)
    ax_a.set_axisbelow(True)
    for boundary in (1.5, 3.5, 5.5, 7.5, 9.5, 11.5):
        ax_a.axhline(boundary, color="#d6d6d6", linewidth=0.55)
    ax_a.axhline(11.5, color="#8a8a8a", linewidth=0.9)
    ax_a.spines[["top", "right"]].set_visible(False)
    legend_handles = [
        mpl.lines.Line2D([], [], marker="o", linestyle="none", markerfacecolor="white", markeredgecolor="#333333", markersize=4.8, label="Residential, 5 kW"),
        mpl.lines.Line2D([], [], marker="s", linestyle="none", markerfacecolor="white", markeredgecolor="#333333", markersize=4.8, label="Small commercial, 100 kW"),
    ]
    ax_a.legend(handles=legend_handles, loc="lower left", bbox_to_anchor=(0.0, 1.003), frameon=False, ncol=2, borderaxespad=0, handletextpad=0.4, columnspacing=1.0)

    columns = [
        ("Residential", "no_capital_support", "R\nNone"),
        ("Residential", "policy_realized", "R\nPolicy"),
        ("Small commercial", "no_capital_support", "C\nNone"),
        ("Small commercial", "policy_realized", "C\nPolicy"),
    ]
    matrix = np.full((len(PAIR_ORDER), len(columns)), np.nan)
    stable = np.zeros_like(matrix, dtype=bool)
    for i, pair in enumerate(PAIR_ORDER):
        for j, (sector, support, _) in enumerate(columns):
            row = pair_summary[
                pair_summary["pair"].eq(pair)
                & pair_summary["sector"].eq(sector)
                & pair_summary["support_case"].eq(support)
            ].iloc[0]
            matrix[i, j] = 100.0 * float(row["alignment_share"])
            stable[i, j] = bool(row["stable_economic_direction"])

    cmap = mpl.colors.LinearSegmentedColormap.from_list(
        "alignment_grey", ["#f2f2f2", "#bdbdbd", "#4d4d4d"]
    )
    im = ax_b.imshow(matrix, cmap=cmap, norm=Normalize(0, 100), aspect="auto")
    for i in range(matrix.shape[0]):
        for j in range(matrix.shape[1]):
            value = matrix[i, j]
            color = "white" if value >= 67 else "black"
            ax_b.text(j, i, f"{value:.0f}%", ha="center", va="center", color=color, fontsize=7.2)
            if stable[i, j]:
                ax_b.add_patch(Rectangle((j - 0.48, i - 0.48), 0.96, 0.96, fill=False, edgecolor="#111111", linewidth=1.05))

    pair_labels = [pair.replace("--", "–\n") for pair in PAIR_ORDER]
    ax_b.set_yticks(np.arange(len(PAIR_ORDER)), pair_labels)
    ax_b.set_xticks(np.arange(len(columns)), [item[2] for item in columns])
    ax_b.set_xlabel("Alignment with observed sector leader (%)")
    ax_b.tick_params(axis="x", pad=3)
    ax_b.axhline(5.5, color="#111111", linewidth=1.0)
    for spine in ax_b.spines.values():
        spine.set_linewidth(0.65)
    cbar = fig.colorbar(im, ax=ax_b, orientation="horizontal", fraction=0.046, pad=0.12, aspect=24)
    cbar.set_ticks([0, 50, 100])
    cbar.set_ticklabels(["0", "50", "100%"])
    cbar.ax.tick_params(labelsize=7.0, length=2)
    cbar.outline.set_linewidth(0.55)
    ax_b.text(0.0, -0.255, "Black outline: one economic leader in all matched scenarios", transform=ax_b.transAxes, ha="left", va="top", fontsize=7.0)
    ax_b.text(0.0, -0.315, "Detroit–Windsor is a supplementary candidate-pair sensitivity", transform=ax_b.transAxes, ha="left", va="top", fontsize=7.0, color="#555555")

    fig.text(0.012, 0.986, "a,", ha="left", va="top", fontsize=12.0, fontweight="normal")
    fig.text(0.565, 0.986, "b,", ha="left", va="top", fontsize=12.0, fontweight="normal")
    fig.subplots_adjust(left=0.18, right=0.985, top=0.925, bottom=0.22)
    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output, bbox_inches="tight")
    plt.close(fig)


def latex_escape(value: str) -> str:
    return value.replace("&", r"\&").replace("%", r"\%")


def support_label(row: pd.Series) -> str:
    if row["fixed_support_usd"] > 0:
        return f"US\\${row['fixed_support_usd']:,.0f} fixed"
    if row["support_fraction"] > 0:
        return f"{100 * row['support_fraction']:.0f}\\%"
    if row["value_model"] == "gross_fiT":
        return "Gross FiT in value model"
    return "None"


def cost_basis_label(value: str) -> str:
    if "pooled transferred ratio" in value:
        return "Transferred 0.80 ratio"
    if "current 5 kW" in value:
        return "Residential anchor"
    if "direct Austria" in value:
        return "Direct Austrian ratio"
    if "Malaysia" in value:
        return "Malaysia sector ratio"
    if "California" in value:
        return "California sector ratio"
    if "Texas" in value:
        return "Texas sector ratio"
    if "United States" in value:
        return "US sector ratio"
    if "Canada" in value:
        return "Canada sector ratio"
    if "China" in value:
        return "China sector ratio"
    return value


def write_table(inputs: pd.DataFrame) -> pd.DataFrame:
    rows = inputs.copy()
    rows["export_value_display"] = rows.apply(
        lambda r: f"{r.export_mid_usd_per_kwh:.3f}"
        if np.isclose(r.export_low_usd_per_kwh, r.export_high_usd_per_kwh)
        else f"{r.export_low_usd_per_kwh:.3f}--{r.export_high_usd_per_kwh:.3f}",
        axis=1,
    )
    rows["support_display"] = rows.apply(support_label, axis=1)
    rows["cost_basis_short"] = rows["cost_basis"].map(cost_basis_label)
    rows.to_csv(TABLE_DIR / "table_s_sector_economic_envelope_inputs.csv", index=False)

    lines = []
    for city in CITY_ORDER:
        group = rows[rows["city"].eq(city)].set_index("sector")
        for index, sector in enumerate(SECTOR_ORDER):
            row = group.loc[sector]
            city_cell = rf"\multirow{{2}}{{*}}{{{latex_escape(city)}}}" if index == 0 else ""
            sector_cell = "Residential" if sector == "Residential" else "Small commercial"
            lines.append(
                f"{city_cell} & {sector_cell} & {row.system_size_kw:.0f} & {row.cost_per_w_usd:.2f} & "
                f"{row.import_rate_usd_per_kwh:.3f} & {row.export_value_display} & "
                f"{row.annual_yield_kwh_per_kw:.0f} & {row.support_display} & "
                f"{latex_escape(row.cost_basis_short)} \\\\"
            )
        if city != CITY_ORDER[-1]:
            lines.append(r"\addlinespace[2pt]")
    (TABLE_DIR / "table_s_sector_economic_envelope_inputs_rows.tex").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )
    return rows


def write_source_data(
    inputs: pd.DataFrame,
    envelopes: pd.DataFrame,
    pair_summary: pd.DataFrame,
    comparisons: pd.DataFrame,
) -> dict[str, object]:
    SOURCE_DIR.mkdir(parents=True, exist_ok=True)
    NOTES_DIR.mkdir(parents=True, exist_ok=True)
    central = central_scenarios(comparisons)
    inputs.to_csv(SOURCE_DIR / "Fig_S8_sector_economic_envelope_inputs.csv", index=False)
    envelopes.to_csv(SOURCE_DIR / "Fig_S8_sector_economic_envelope_city.csv", index=False)
    pair_summary.to_csv(SOURCE_DIR / "Fig_S8_sector_economic_envelope_pairwise.csv", index=False)
    central.to_csv(SOURCE_DIR / "Fig_S8_sector_economic_envelope_central.csv", index=False)
    comparisons.to_csv(SOURCE_DIR / "Fig_S8_sector_economic_envelope_comparisons.csv", index=False)
    evidence_path = AUDIT / "online_source_audit.csv"
    if not evidence_path.exists():
        evidence_path = SOURCE_DIR / "Fig_S8_sector_economic_envelope_provenance.csv"
    evidence = pd.read_csv(evidence_path)
    evidence.to_csv(SOURCE_DIR / "Fig_S8_sector_economic_envelope_provenance.csv", index=False)

    primary_central = central[central["scope"].eq("primary")]
    primary_summary = pair_summary[pair_summary["scope"].eq("primary")]
    checks = {
        "status": "pass",
        "city_count": int(inputs["city"].nunique()),
        "pair_count": int(pair_summary["pair"].nunique()),
        "input_rows": int(len(inputs)),
        "city_envelope_rows": int(len(envelopes)),
        "pairwise_summary_rows": int(len(pair_summary)),
        "central_pair_sector_rows": int(len(central)),
        "scenario_comparison_rows": int(len(comparisons)),
        "online_provenance_rows": int(len(evidence)),
        "primary_central_aligned_count": int(primary_central["aligned_with_observed_sector_leader"].sum()),
        "primary_central_comparison_count": int(len(primary_central)),
        "primary_stable_summary_count": int(primary_summary["stable_economic_direction"].sum()),
        "primary_summary_count": int(len(primary_summary)),
        "primary_aligned_all_scenarios_count": int(np.isclose(primary_summary["alignment_share"], 1.0).sum()),
        "all_irr_values_finite": bool(np.isfinite(envelopes[["irr_min_pct", "irr_middle_pct", "irr_max_pct"]]).all().all()),
        "main_manuscript_or_main_figure_modified": False,
    }
    assert checks["city_count"] == 14
    assert checks["pair_count"] == 7
    assert checks["input_rows"] == 28
    assert checks["primary_central_aligned_count"] == 11
    assert checks["primary_central_comparison_count"] == 12
    assert checks["primary_stable_summary_count"] == 19
    assert checks["primary_aligned_all_scenarios_count"] == 16
    CHECKS_PATH.write_text(json.dumps(checks, indent=2) + "\n", encoding="utf-8")

    notes = """# Source Data notes for Supplementary Fig. S8

Panel a reports minimum, middle and maximum modelled IRR under the policy-realized capital-support case. Residential systems are represented at 5 kW with self-consumption shares of 30%, 50% and 70%. Small-commercial systems are represented at 100 kW with shares of 50%, 70% and 90%. The 100-kW case is a sensitivity proxy for the broad observed non-residential category, not its complete project-size distribution. Singapore small-commercial export values additionally span the audited wholesale-price range. Hong Kong uses the gross feed-in-tariff capacity bands, so self-consumption does not affect its modelled revenue. Because the envelope explicitly divides generation between self-consumption and export, its middle values are not substitutions for the standardized central IRRs in the main screen.

Panel b reports the share of matched self-consumption and export scenarios in which the economic leader equals the observed building-sector PV-utilization leader. A black cell outline marks a stable economic direction, meaning that the same city leads in every matched scenario, whether or not that city is the observed PV leader.

The first six pairs are the primary sample. Detroit and Windsor are retained as a separately reported Supplementary candidate-pair sensitivity.

The envelope separates project size, sector installed-cost scaling, tariff class, export treatment, capital-support realization and self-consumption. It does not observe building-specific load profiles, demand-charge savings, financing, batteries, roof-surface geometry or historical installation conditions. Values are scenario diagnostics rather than observed project returns.

Reproduction commands from the revision root:

`python code/revision/audit_sector_economic_envelope.py`

`python code/revision/plot_supp_sector_economic_envelope.py`
"""
    (NOTES_DIR / "Fig_S8_sector_economic_envelope_notes.md").write_text(notes, encoding="utf-8")
    return checks


def main() -> None:
    FIGURE_DIR.mkdir(parents=True, exist_ok=True)
    TABLE_DIR.mkdir(parents=True, exist_ok=True)
    inputs, envelopes, pair_summary, comparisons = load_data()
    write_table(inputs)
    checks = write_source_data(inputs, envelopes, pair_summary, comparisons)
    build_figure(envelopes, pair_summary, FIGURE_DIR / "fig_s_sector_economic_envelope.pdf")
    build_figure(envelopes, pair_summary, FIGURE_DIR / "fig_s_sector_economic_envelope.png")
    print(json.dumps(checks, indent=2))


if __name__ == "__main__":
    main()

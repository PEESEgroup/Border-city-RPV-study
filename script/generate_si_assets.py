#!/usr/bin/env python3
"""Generate first-pass supplementary figures and tables for the manuscript."""

from __future__ import annotations

import csv
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


ROOT = Path("/datasets/joe/dataset/Border/manuscript")
DATA = ROOT / "data"
SCRIPT = ROOT / "script"
FIG_SUPP = ROOT / "figures" / "supplement"
TABLES = ROOT / "tables"


SHOW_NAME_MAP = {
    "vienna": "Vienna",
    "bratislava": "Bratislava",
    "elpaso": "El Paso",
    "juarez": "Juarez",
    "ciudadjuarez": "Juarez",
    "sandiego": "San Diego",
    "tijuana": "Tijuana",
    "hongkong": "Hong Kong",
    "shenzhen": "Shenzhen",
    "singapore": "Singapore",
    "johorbahru": "Johor Bahru",
    "nice": "Nice",
    "monaco": "Monaco",
}


def _city_key(value: str) -> str:
    return "".join(str(value).strip().lower().replace("_", " ").replace("-", " ").split())


def _display_city(value: str) -> str:
    return SHOW_NAME_MAP.get(_city_key(value), str(value))


def ensure_dirs() -> None:
    FIG_SUPP.mkdir(parents=True, exist_ok=True)
    TABLES.mkdir(parents=True, exist_ok=True)


def escape_latex(value) -> str:
    text = str(value)
    replacements = {
        "\\": r"\textbackslash{}",
        "&": r"\&",
        "%": r"\%",
        "$": r"\$",
        "#": r"\#",
        "_": r"\_",
        "{": r"\{",
        "}": r"\}",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    return text


def load_city_solar_data_checked():
    namespace: dict[str, object] = {}
    econ_path = SCRIPT / "econimic_model.py"
    code = econ_path.read_text(encoding="utf-8")
    exec(compile(code, str(econ_path), "exec"), namespace)
    return namespace["city_solar_data_checked"]


def write_table_s1() -> None:
    city_data = load_city_solar_data_checked()

    rows = []
    for city, params in city_data.items():
        rows.append(
            {
                "City": _display_city(city),
                "cost_per_watt_usd": params["cost_per_watt"],
                "capex_reduction": params["capex_reduction"],
                "electricity_rate_usd_per_kwh": params["elec_rate"],
                "export_rate_usd_per_kwh": params["export_rate"],
                "pv_yield_kwh_per_kw_year": params["pv_yield_kwh_per_kw_year"],
                "self_consumption_ratio": params["self_consumption_ratio"],
                "degradation_rate": params["degradation_rate"],
                "om_rate": params["om_rate"],
                "parameter_provenance": "script/econimic_model.py:city_solar_data_checked",
            }
        )

    df = pd.DataFrame(rows).sort_values("City").reset_index(drop=True)
    df.to_csv(TABLES / "table_s1_economic_model_city_inputs.csv", index=False)

    tex_lines = [
        r"{\scriptsize",
        r"\begin{longtable}{lrrrrrrrr}",
        r"\toprule",
        r"City & Cost/W & CAPEX red. & Elec. rate & Export rate & Yield & Self-cons. & Degrad. & O\&M \\",
        r"\midrule",
        r"\endfirsthead",
        r"\toprule",
        r"City & Cost/W & CAPEX red. & Elec. rate & Export rate & Yield & Self-cons. & Degrad. & O\&M \\",
        r"\midrule",
        r"\endhead",
    ]
    for row in df.itertuples(index=False):
        tex_lines.append(
            " & ".join(
                [
                    escape_latex(row.City),
                    f"{row.cost_per_watt_usd:.2f}",
                    f"{row.capex_reduction:.2f}",
                    f"{row.electricity_rate_usd_per_kwh:.3f}",
                    f"{row.export_rate_usd_per_kwh:.3f}",
                    f"{int(row.pv_yield_kwh_per_kw_year)}",
                    f"{row.self_consumption_ratio:.2f}",
                    f"{row.degradation_rate:.3f}",
                    f"{row.om_rate:.3f}",
                ]
            )
            + r" \\"
        )
    tex_lines += [r"\bottomrule", r"\end{longtable}", r"}"]
    (TABLES / "table_s1_economic_model_city_inputs.tex").write_text(
        "\n".join(tex_lines) + "\n", encoding="utf-8"
    )

    notes = pd.DataFrame(
        [
            {
                "assumption": "system_size_kw",
                "value": 5,
                "unit": "kW",
                "provenance": "plot_discounted_cashflow_profiles_citypair_lines.py default",
            },
            {
                "assumption": "project_lifetime_years",
                "value": 25,
                "unit": "years",
                "provenance": "plot_discounted_cashflow_profiles_citypair_lines.py default",
            },
            {
                "assumption": "discount_rate",
                "value": 0.05,
                "unit": "share",
                "provenance": "plot_discounted_cashflow_profiles_citypair_lines.py default",
            },
        ]
    )
    notes.to_csv(TABLES / "table_s1_global_model_assumptions.csv", index=False)
    tex_lines = [
        r"{\small",
        r"\begin{tabular}{llll}",
        r"\toprule",
        r"Assumption & Value & Unit & Provenance \\",
        r"\midrule",
    ]
    for row in notes.itertuples(index=False):
        tex_lines.append(
            " & ".join(
                [
                    escape_latex(row.assumption),
                    escape_latex(row.value),
                    escape_latex(row.unit),
                    escape_latex(row.provenance),
                ]
            )
            + r" \\"
        )
    tex_lines += [r"\bottomrule", r"\end{tabular}", r"}"]
    (TABLES / "table_s1_global_model_assumptions.tex").write_text(
        "\n".join(tex_lines) + "\n", encoding="utf-8"
    )


def write_table_s2() -> None:
    codebook = pd.read_csv(DATA / "Policy_frictions" / "border_city_pv_friction_codebook.csv")
    codebook.to_csv(TABLES / "table_s2_policy_friction_codebook.csv", index=False)
    tex_lines = [
        r"{\scriptsize",
        r"\begin{longtable}{p{0.45cm}p{1.85cm}p{0.95cm}p{2.0cm}p{2.0cm}p{2.0cm}p{2.0cm}p{2.0cm}}",
        r"\toprule",
        r"Ind. & Short name & Dim. & Score 0 & Score 1 & Score 2 & Score 3 & Interpretation \\",
        r"\midrule",
        r"\endfirsthead",
        r"\toprule",
        r"Ind. & Short name & Dim. & Score 0 & Score 1 & Score 2 & Score 3 & Interpretation \\",
        r"\midrule",
        r"\endhead",
    ]
    for _, row in codebook.iterrows():
        tex_lines.append(
            " & ".join(
                [
                    escape_latex(row["Indicator"]),
                    escape_latex(row["Short name"]),
                    escape_latex(row["Dimension"]),
                    escape_latex(row["Score = 0"]),
                    escape_latex(row["Score = 1"]),
                    escape_latex(row["Score = 2"]),
                    escape_latex(row["Score = 3"]),
                    escape_latex(row["Interpretation note"]),
                ]
            )
            + r" \\"
        )
    tex_lines += [r"\bottomrule", r"\end{longtable}", r"}"]
    (TABLES / "table_s2_policy_friction_codebook.tex").write_text(
        "\n".join(tex_lines) + "\n", encoding="utf-8"
    )


def plot_figure_s1() -> None:
    benchmark = pd.read_csv(
        DATA / "Building_PVs" / "border_ckpt_benchmark_all_except_windsor_detroit_per_city.csv"
    )
    coverage = pd.read_csv(DATA / "Building_PVs" / "city_image_coverage_summary.csv")

    benchmark["City"] = benchmark["city"].map(_display_city)
    coverage["City"] = coverage["city"].map(_display_city)

    benchmark = benchmark.sort_values("City").reset_index(drop=True)
    coverage = coverage.sort_values("City").reset_index(drop=True)

    fig, axes = plt.subplots(1, 2, figsize=(12.5, 5.8), dpi=240)
    fig.patch.set_facecolor("white")

    ax = axes[0]
    y = range(len(coverage))
    ax.barh(y, coverage["covered_area_km2"], color="#7aa6c2", alpha=0.9, label="Covered area (km²)")
    ax.set_yticks(list(y))
    ax.set_yticklabels(coverage["City"], fontsize=9)
    ax.invert_yaxis()
    ax.set_xlabel("Covered area (km²)")
    ax.set_title("a, Image coverage by city", loc="left", fontsize=13)
    ax.grid(axis="x", linestyle="--", alpha=0.25)
    ax2 = ax.twiny()
    ax2.plot(coverage["image_count"], y, "o-", color="#b35c44", linewidth=1.6, markersize=4, label="Image count")
    ax2.set_xlabel("Image count")
    ax2.tick_params(axis="x", labelsize=8)

    ax = axes[1]
    y = range(len(benchmark))
    ax.barh(y, benchmark["dice"], color="#6fa65a", alpha=0.85, label="Dice")
    ax.barh(y, benchmark["iou"], color="#d5a24b", alpha=0.85, label="IoU")
    ax.set_yticks(list(y))
    ax.set_yticklabels(benchmark["City"], fontsize=9)
    ax.invert_yaxis()
    ax.set_xlim(0, 1.0)
    ax.set_xlabel("Score")
    ax.set_title("b, Segmentation benchmark by city", loc="left", fontsize=13)
    ax.grid(axis="x", linestyle="--", alpha=0.25)
    ax.legend(frameon=False, fontsize=9, loc="lower right")

    for axis in axes:
        axis.spines["top"].set_visible(False)
        axis.spines["right"].set_visible(False)

    fig.tight_layout()
    fig.savefig(FIG_SUPP / "fig_s1_pv_identification_support.pdf", bbox_inches="tight")
    plt.close(fig)


def write_manifest() -> None:
    rows = [
        {
            "asset_type": "figure",
            "id": "Figure S1",
            "path": str(FIG_SUPP / "fig_s1_pv_identification_support.pdf"),
            "description": "Image coverage and segmentation benchmark support for rooftop PV identification.",
        },
        {
            "asset_type": "table",
            "id": "Table S1",
            "path": str(TABLES / "table_s1_economic_model_city_inputs.csv"),
            "description": "City-level PV economic model inputs exported from city_solar_data_checked.",
        },
        {
            "asset_type": "table",
            "id": "Table S1-note",
            "path": str(TABLES / "table_s1_global_model_assumptions.csv"),
            "description": "Global model assumptions used in the discounted cash-flow analysis.",
        },
        {
            "asset_type": "table",
            "id": "Table S2",
            "path": str(TABLES / "table_s2_policy_friction_codebook.csv"),
            "description": "Policy-friction codebook and scoring rubric.",
        },
    ]
    with (TABLES / "si_assets_manifest.csv").open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    ensure_dirs()
    write_table_s1()
    write_table_s2()
    plot_figure_s1()
    write_manifest()
    print("Generated SI assets in figures/supplement and tables/")


if __name__ == "__main__":
    main()

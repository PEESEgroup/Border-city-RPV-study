#!/usr/bin/env python3
"""Build revised Fig. 2b as a six-pair overlapping-attribute matrix.

The matrix reports sector leaders directly and keeps sector leadership and
income ordering as independent attributes. IRR and policy-friction columns are
excluded because they are contextual diagnostics rather than pattern-defining
attributes.
"""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.lines import Line2D
from matplotlib.patches import Rectangle


ROOT = Path(__file__).resolve().parents[2]
CITY_INPUT = ROOT / "evidence/v1_verified_data/city_pv_metrics_14cities.csv"
PAIR_INPUT = ROOT / "evidence/v1_verified_data/pair_results_7pairs.csv"
OUTDIR = ROOT / "figures/panels/revision"
SOURCE_DATA = ROOT / "Source_Data/csv/Fig_2b.csv"
CHECKS = ROOT / "Source_Data/source_data_checks_fig2.json"

PAIR_ORDER = [
    ("vienna", "bratislava"),
    ("singapore", "johorbahru"),
    ("sandiego", "tijuana"),
    ("elpaso", "juarez"),
    ("hongkong", "shenzhen"),
    ("monaco", "nice"),
]
PAIR_COLOR = {
    ("vienna", "bratislava"): "#7f8f49",
    ("singapore", "johorbahru"): "#b8873a",
    ("sandiego", "tijuana"): "#4f8f80",
    ("elpaso", "juarez"): "#4d78a8",
    ("hongkong", "shenzhen"): "#8b6aa7",
    ("monaco", "nice"): "#bd6f74",
}
SHOW_NAME = {
    "vienna": "Vienna",
    "bratislava": "Bratislava",
    "singapore": "Singapore",
    "johorbahru": "Johor Bahru",
    "sandiego": "San Diego",
    "tijuana": "Tijuana",
    "elpaso": "El Paso",
    "juarez": "Juarez",
    "hongkong": "Hong Kong",
    "shenzhen": "Shenzhen",
    "monaco": "Monaco",
    "nice": "Nice",
}
SEGMENT_MAP = {
    "All buildings": "all_building_leader",
    "Residential": "residential_leader",
    "Non-residential": "nonresidential_leader",
}
TEXT = "#222222"
MUTED = "#4a4f52"
RULE = "#cfd4d3"


def leader(v1: float, v2: float, c1: str, c2: str) -> tuple[str, str]:
    if v1 > v2:
        return c1, "city_1"
    if v2 > v1:
        return c2, "city_2"
    return "Tie", "tie"


def build_source_data() -> pd.DataFrame:
    city = pd.read_csv(CITY_INPUT)
    pairs = pd.read_csv(PAIR_INPUT)
    pairs = pairs.loc[~pairs["pair"].eq("Detroit--Windsor")].copy()
    city = city.set_index(["city_key", "Segment"])
    rows: list[dict[str, object]] = []

    for pair_order, (c1, c2) in enumerate(PAIR_ORDER, start=1):
        pair_name = f"{SHOW_NAME[c1]}--{SHOW_NAME[c2]}"
        p = pairs.loc[pairs["pair"].eq(pair_name)]
        if len(p) != 1:
            raise ValueError(f"Expected one attribute row for {pair_name}, found {len(p)}")
        p = p.iloc[0]
        row: dict[str, object] = {
            "pair_order": pair_order,
            "pair": pair_name,
            "city_1": SHOW_NAME[c1],
            "city_2": SHOW_NAME[c2],
        }
        for segment, output_column in SEGMENT_MAP.items():
            v1 = float(city.at[(c1, segment), "PV utilization (%)"])
            v2 = float(city.at[(c2, segment), "PV utilization (%)"])
            lead, role = leader(v1, v2, SHOW_NAME[c1], SHOW_NAME[c2])
            row[output_column] = lead
            row[f"{output_column}_role"] = role
            row[f"{segment.lower().replace('-', '').replace(' ', '_')}_city_1_pct"] = v1
            row[f"{segment.lower().replace('-', '').replace(' ', '_')}_city_2_pct"] = v2
        raw_sector = str(p["sectoral_direction_attribute"]).lower()
        raw_income = str(p["income_relation_attribute"]).lower()
        row["sector_leadership"] = "same-side" if "same-side" in raw_sector else "split"
        row["income_ordering"] = "aligned" if "aligned" in raw_income else "reversed"
        rows.append(row)

    out = pd.DataFrame(rows)
    if len(out) != 6:
        raise ValueError(f"Expected six primary pairs, found {len(out)}")
    return out


def display_attribute(value: str) -> str:
    return {
        "same-side": "Same-side",
        "split": "Split",
        "aligned": "Aligned",
        "reversed": "Reversed",
    }.get(value, value.title())


def draw_leader(ax: plt.Axes, x: float, y: float, name: str, role: str, color: str) -> None:
    if role == "city_1":
        face = color
    elif role == "city_2":
        face = "white"
    else:
        face = "#eeeeea"
    ax.scatter(x - 0.43, y, s=31, facecolor=face, edgecolor=color, lw=1.1, zorder=4)
    ax.text(x - 0.31, y, name, ha="left", va="center", fontsize=6.9, color=TEXT)


def draw(df: pd.DataFrame) -> plt.Figure:
    fig, ax = plt.subplots(figsize=(7.1, 4.45), dpi=300)
    ax.set_axis_off()
    ax.set_xlim(-0.05, 9.20)
    ax.set_ylim(-0.8, 6.85)

    pair_x = 0.0
    columns = [
        (2.20, "All-building\nleader"),
        (3.80, "Residential\nleader"),
        (5.40, "Non-residential\nleader"),
        (7.05, "Sector\nleadership"),
        (8.50, "Income\nordering"),
    ]
    ax.text(pair_x, 6.52, "Border-city pair", ha="left", va="center", fontsize=7.6, fontweight="bold", color=TEXT)
    for x, label in columns:
        ax.text(x, 6.52, label, ha="center", va="center", fontsize=7.35, fontweight="bold", color=TEXT, linespacing=1.05)
    ax.hlines(6.12, -0.02, 9.12, color="#aeb5b4", lw=0.85)

    for i, row in df.iterrows():
        pair = PAIR_ORDER[i]
        color = PAIR_COLOR[pair]
        y = 5.52 - i * 1.0
        ax.hlines(y - 0.5, -0.02, 9.12, color=RULE, lw=0.55)
        ax.scatter(0.05, y + 0.15, s=25, facecolor=color, edgecolor=color, lw=0.8)
        ax.scatter(0.05, y - 0.15, s=25, facecolor="white", edgecolor=color, lw=1.0)
        pair_suffix = "†" if pair == ("monaco", "nice") else ""
        ax.text(
            0.18,
            y,
            f"{row['city_1']} -\n{row['city_2']}{pair_suffix}",
            ha="left",
            va="center",
            fontsize=7.2,
            color=TEXT,
            linespacing=1.02,
        )
        for x, key in zip([2.20, 3.80, 5.40], ["all_building_leader", "residential_leader", "nonresidential_leader"]):
            draw_leader(ax, x, y, str(row[key]), str(row[f"{key}_role"]), color)
        ax.text(7.05, y, display_attribute(str(row["sector_leadership"])), ha="center", va="center", fontsize=7.2, color=TEXT)
        ax.text(8.50, y, display_attribute(str(row["income_ordering"])), ha="center", va="center", fontsize=7.2, color=TEXT)

    for x in [1.48, 3.00, 4.60, 6.22, 7.78]:
        ax.vlines(x, -0.02, 6.12, color=RULE, lw=0.5)

    legend = [
        Line2D([0], [0], marker="o", linestyle="none", markerfacecolor="#6f7f7b", markeredgecolor="#6f7f7b", markersize=4.8, label="first-listed city leads"),
        Line2D([0], [0], marker="o", linestyle="none", markerfacecolor="white", markeredgecolor="#6f7f7b", markersize=4.8, label="second-listed city leads"),
    ]
    ax.legend(
        handles=legend,
        loc="lower left",
        bbox_to_anchor=(0.0, -0.04),
        frameon=False,
        ncol=2,
        fontsize=6.8,
        handletextpad=0.45,
        columnspacing=1.1,
        borderaxespad=0,
        labelcolor=MUTED,
    )
    ax.text(
        9.12,
        -0.28,
        "† Small denominator; see Supplementary Table S1.",
        ha="right",
        va="top",
        fontsize=6.35,
        color=MUTED,
    )
    fig.subplots_adjust(left=0.015, right=0.995, top=0.99, bottom=0.12)
    return fig


def main() -> None:
    df = build_source_data()
    SOURCE_DATA.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(SOURCE_DATA, index=False)
    OUTDIR.mkdir(parents=True, exist_ok=True)
    fig = draw(df)
    stem = OUTDIR / "fig2b_primary6_overlapping_attributes"
    fig.savefig(stem.with_suffix(".pdf"), bbox_inches="tight", pad_inches=0.02)
    fig.savefig(stem.with_suffix(".png"), dpi=300, bbox_inches="tight", pad_inches=0.02)
    plt.close(fig)

    prior = json.loads(CHECKS.read_text()) if CHECKS.exists() else {}
    checks = {
        **prior,
        "status": "standalone_panels_pass",
        "panel_b_primary_pairs": len(df),
        "panel_b_shaded_groups": 0,
        "panel_b_contextual_diagnostic_columns": 0,
        "panel_b_attributes": ["sector_leadership", "income_ordering"],
        "panel_b_detroit_windsor_excluded": not df["pair"].eq("Detroit--Windsor").any(),
        "panel_b_source_data": str(SOURCE_DATA.relative_to(ROOT)),
    }
    CHECKS.write_text(json.dumps(checks, indent=2) + "\n", encoding="utf-8")
    print(f"[ok] Wrote {SOURCE_DATA}")
    print(f"[ok] Wrote {stem.with_suffix('.pdf')} and .png")
    print(json.dumps(checks, indent=2))


if __name__ == "__main__":
    main()

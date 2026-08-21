#!/usr/bin/env python3
"""Build revised Fig. 2a from the locked six-pair city metrics.

The panel preserves the original dumbbell grammar, pair order, colors, segment
rows and filled/open city encoding. It intentionally removes all shaded pattern
groups because sector leadership and income ordering are overlapping attributes.
"""

from __future__ import annotations

import json
import math
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.lines import Line2D
from matplotlib.transforms import blended_transform_factory


ROOT = Path(__file__).resolve().parents[2]
INPUT = ROOT / "evidence/v1_verified_data/city_pv_metrics_14cities.csv"
OUTDIR = ROOT / "figures/panels/revision"
SOURCE_DATA = ROOT / "Source_Data/csv/Fig_2a.csv"
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
SEGMENTS = ["All buildings", "Residential", "Non-residential"]
SEGMENT_LABEL = {
    "All buildings": "All buildings",
    "Residential": "Res.",
    "Non-residential": "Non-res.",
}
TEXT = "#222222"
MUTED = "#4a4f52"
GRID = "#d8dddc"


def load_primary_data() -> pd.DataFrame:
    df = pd.read_csv(INPUT)
    required = {
        "city_key",
        "City",
        "Segment",
        "PV utilization (%)",
        "PV area (m2)",
        "Building footprint area (m2)",
        "Buildings",
        "PV-positive buildings",
    }
    missing = sorted(required - set(df.columns))
    if missing:
        raise ValueError(f"Missing required columns in {INPUT}: {missing}")

    primary = {city for pair in PAIR_ORDER for city in pair}
    out = df.loc[df["city_key"].isin(primary) & df["Segment"].isin(SEGMENTS)].copy()
    out["pair_order"] = out["city_key"].map(
        {city: i for i, pair in enumerate(PAIR_ORDER, start=1) for city in pair}
    )
    out["city_role"] = out["city_key"].map(
        {pair[0]: "city_1" for pair in PAIR_ORDER} | {pair[1]: "city_2" for pair in PAIR_ORDER}
    )
    out["pair"] = out["city_key"].map(
        {
            city: f"{SHOW_NAME[pair[0]]}--{SHOW_NAME[pair[1]]}"
            for pair in PAIR_ORDER
            for city in pair
        }
    )
    out["segment_order"] = out["Segment"].map({s: i for i, s in enumerate(SEGMENTS)})
    out = out.sort_values(["pair_order", "segment_order", "city_role"]).reset_index(drop=True)

    if len(out) != 36:
        raise ValueError(f"Expected 36 city-segment records for six pairs, found {len(out)}")
    counts = out.groupby(["pair_order", "Segment"]).size()
    if not counts.eq(2).all():
        raise ValueError("Each pair and segment must contain exactly two cities")
    return out


def save_source_data(df: pd.DataFrame) -> None:
    SOURCE_DATA.parent.mkdir(parents=True, exist_ok=True)
    columns = [
        "pair_order",
        "pair",
        "city_role",
        "city_key",
        "City",
        "Segment",
        "PV utilization (%)",
        "PV area (m2)",
        "Building footprint area (m2)",
        "Buildings",
        "PV-positive buildings",
    ]
    df[columns].to_csv(SOURCE_DATA, index=False)


def annotate_value(ax: plt.Axes, value: float, other: float, y: float, is_city_1: bool) -> None:
    if abs(value - other) > 0.72:
        offset, ha = (0, 4), "center"
    elif value < other:
        offset, ha = (-6, 4), "right"
    else:
        offset, ha = (6, 4), "left"
    ax.annotate(
        f"{value:.2f}",
        (value, y),
        xytext=offset,
        textcoords="offset points",
        ha=ha,
        va="bottom",
        fontsize=6.0,
        color=MUTED,
        zorder=5,
    )


def draw(df: pd.DataFrame) -> plt.Figure:
    fig, ax = plt.subplots(figsize=(4.7, 6.15), dpi=300)
    trans = blended_transform_factory(ax.transAxes, ax.transData)
    pair_gap = 0.40
    row_step = 0.56
    pair_step = row_step * 3 + pair_gap
    pair_centres: dict[tuple[str, str], float] = {}

    for pair_index, pair in enumerate(PAIR_ORDER):
        c1, c2 = pair
        base_y = pair_index * pair_step
        pair_centres[pair] = base_y + row_step
        pair_df = df.loc[df["pair_order"].eq(pair_index + 1)]
        color = PAIR_COLOR[pair]

        for segment_index, segment in enumerate(SEGMENTS):
            y = base_y + segment_index * row_step
            seg = pair_df.loc[pair_df["Segment"].eq(segment)].set_index("city_role")
            v1 = float(seg.at["city_1", "PV utilization (%)"])
            v2 = float(seg.at["city_2", "PV utilization (%)"])
            ax.plot([v1, v2], [y, y], color="#aab2b2", lw=0.95, zorder=2)
            ax.scatter(v1, y, s=30, facecolor=color, edgecolor=color, lw=0.9, zorder=4)
            ax.scatter(v2, y, s=30, facecolor="white", edgecolor=color, lw=1.15, zorder=4)
            annotate_value(ax, v1, v2, y, True)
            annotate_value(ax, v2, v1, y, False)
            ax.text(
                -0.028,
                y,
                SEGMENT_LABEL[segment],
                transform=trans,
                ha="right",
                va="center",
                fontsize=7.5,
                color=TEXT,
                clip_on=False,
            )

        if pair_index < len(PAIR_ORDER) - 1:
            separator_y = base_y + row_step * 2 + pair_gap / 2
            ax.axhline(separator_y, color="#e7e9e8", lw=0.65, zorder=0)

        centre = pair_centres[pair]
        marker_x = -0.55
        ax.plot(
            [marker_x],
            [centre - 0.18],
            marker="o",
            markersize=4.3,
            color=color,
            markerfacecolor=color,
            transform=trans,
            clip_on=False,
        )
        ax.plot(
            [marker_x],
            [centre + 0.18],
            marker="o",
            markersize=4.3,
            color=color,
            markerfacecolor="white",
            markeredgewidth=1.15,
            transform=trans,
            clip_on=False,
        )
        suffix = "†" if pair == ("monaco", "nice") else ""
        ax.text(
            -0.51,
            centre,
            f"{SHOW_NAME[c1]} -\n{SHOW_NAME[c2]}{suffix}",
            transform=trans,
            ha="left",
            va="center",
            fontsize=8.2,
            color=TEXT,
            linespacing=1.06,
            clip_on=False,
        )

    ax.set_xlim(0, 10.0)
    ax.set_ylim((len(PAIR_ORDER) - 1) * pair_step + 2 * row_step + 0.68, -0.62)
    ax.set_xticks([0, 2, 4, 6, 8, 10])
    ax.set_yticks([])
    ax.set_xlabel("Rooftop PV utilization (%)", fontsize=8.7, color=TEXT, labelpad=6)
    ax.tick_params(axis="x", labelsize=7.7, colors=MUTED, length=2.5, width=0.6)
    ax.grid(axis="x", color=GRID, lw=0.6, zorder=0)
    for spine in ["top", "right", "left"]:
        ax.spines[spine].set_visible(False)
    ax.spines["bottom"].set_color("#b8bdbc")
    ax.spines["bottom"].set_linewidth(0.65)

    legend = [
        Line2D([0], [0], marker="o", linestyle="none", markerfacecolor="#6f7f7b", markeredgecolor="#6f7f7b", markersize=4.8, label="first-listed city"),
        Line2D([0], [0], marker="o", linestyle="none", markerfacecolor="white", markeredgecolor="#6f7f7b", markersize=4.8, label="second-listed city"),
    ]
    ax.legend(
        handles=legend,
        loc="upper right",
        bbox_to_anchor=(1.0, -0.085),
        frameon=False,
        ncol=2,
        fontsize=6.9,
        handletextpad=0.45,
        columnspacing=1.0,
        borderaxespad=0,
        labelcolor=MUTED,
    )
    ax.text(
        0.0,
        -0.135,
        "† Small denominator; see Supplementary Table S1.",
        transform=ax.transAxes,
        ha="left",
        va="top",
        fontsize=6.4,
        color=MUTED,
    )
    fig.subplots_adjust(left=0.35, right=0.985, top=0.985, bottom=0.14)
    return fig


def main() -> None:
    df = load_primary_data()
    save_source_data(df)
    OUTDIR.mkdir(parents=True, exist_ok=True)
    fig = draw(df)
    stem = OUTDIR / "fig2a_primary6_utilization_dumbbell"
    fig.savefig(stem.with_suffix(".pdf"), bbox_inches="tight", pad_inches=0.02)
    fig.savefig(stem.with_suffix(".png"), dpi=300, bbox_inches="tight", pad_inches=0.02)
    plt.close(fig)

    checks = {
        "status": "panel_a_pass",
        "primary_pairs": 6,
        "primary_cities": 12,
        "city_segment_rows": len(df),
        "shaded_groups": 0,
        "detroit_windsor_excluded": not df["city_key"].isin(["detroit", "windsor"]).any(),
        "source_data": str(SOURCE_DATA.relative_to(ROOT)),
    }
    CHECKS.write_text(json.dumps(checks, indent=2) + "\n", encoding="utf-8")
    print(f"[ok] Wrote {SOURCE_DATA}")
    print(f"[ok] Wrote {stem.with_suffix('.pdf')} and .png")
    print(json.dumps(checks, indent=2))


if __name__ == "__main__":
    main()

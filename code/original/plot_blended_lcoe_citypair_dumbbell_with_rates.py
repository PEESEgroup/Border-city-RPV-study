#!/usr/bin/env python3
"""Plot city-row dumbbells for Blended vs LCOE with a shared-x rates panel."""

from __future__ import annotations

import argparse
import importlib.util
import os
from pathlib import Path
from types import ModuleType
from typing import Dict, List, Tuple

os.environ.setdefault("MPLCONFIGDIR", "/tmp/matplotlib")

import numpy as np
import pandas as pd

try:
    import matplotlib.pyplot as plt
    from matplotlib.lines import Line2D
    from matplotlib.patches import Patch
except ModuleNotFoundError as exc:
    raise SystemExit(
        "matplotlib is required for plotting. Install it with: pip install matplotlib"
    ) from exc


PAIR_ORDER: List[Tuple[str, str]] = [
    ("Vienna", "Bratislava"),
    ("Singapore", "Johor Bahru"),
    ("San Diego", "Tijuana"),
    ("El Paso", "Ciudad Juarez"),
    ("Hong Kong", "Shenzhen"),
    ("Monaco", "Nice"),
]

# Keep the same pair palette convention used by blended-value scripts.
PAIR_COLORS: Dict[Tuple[str, str], Tuple[str, str]] = {
    ("vienna", "bratislava"): ("#c97c5d", "#8c4f3f"),
    ("elpaso", "juarez"): ("#4f7cac", "#1f4e79"),
    ("sandiego", "tijuana"): ("#5aa469", "#2f6b3b"),
    ("hongkong", "shenzhen"): ("#b07bac", "#7f4f7c"),
    ("singapore", "johorbahru"): ("#d9a441", "#9a6a12"),
    ("monaco", "nice"): ("#d16d8a", "#8f3458"),
}

DISPLAY_NAME_MAP: Dict[str, str] = {
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
    "Nice": "Nice",
    "Monaco": "Monaco",
}

THIS_FILE = Path(__file__).resolve()
if THIS_FILE.parent.name == "script" and THIS_FILE.parents[1].name == "manuscript":
    BORDER_ROOT = THIS_FILE.parents[2]
else:
    BORDER_ROOT = THIS_FILE.parents[2]


def _default_economic_csv() -> Path:
    candidates = [
        BORDER_ROOT / "manuscript" / "data" / "PV_Eco_model" / "economic_analysis_results.csv",
        BORDER_ROOT / "factors" / "economic_analysis_results.csv",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return candidates[0]


def _norm(text: str) -> str:
    return text.lower().replace(" ", "").replace("ciudad", "").replace("-", "")


def _city_color_map() -> Dict[str, str]:
    colors: Dict[str, str] = {}
    for city_a, city_b in PAIR_ORDER:
        key = (_norm(city_a), _norm(city_b))
        pair_color = PAIR_COLORS.get(key, ("#8a8a8a", "#5c5c5c"))
        colors[city_a] = pair_color[0]
        colors[city_b] = pair_color[1]
    return colors


def _ordered_cities_in_pairs() -> List[str]:
    ordered: List[str] = []
    for city_a, city_b in PAIR_ORDER:
        ordered.append(city_a)
        ordered.append(city_b)
    return ordered


def _pair_spaced_y_positions(city_sequence: List[str]) -> np.ndarray:
    """Return y positions with tighter spacing inside each pair."""
    y_vals: List[float] = []
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


def build_plot(
    csv_path: Path,
    out_path: Path,
    fig_width: float,
    fig_height: float,
) -> None:
    df = pd.read_csv(csv_path)

    needed_cols = [
        "City",
        "Blended Value of Solar ($/kWh)",
        "LCOE ($/kWh)",
        "Electricity Rate ($/kWh)",
        "Export Rate ($/kWh)",
    ]
    missing = [c for c in needed_cols if c not in df.columns]
    if missing:
        raise SystemExit(f"Missing required columns: {missing}")

    city_order = _ordered_cities_in_pairs()
    city_colors = _city_color_map()

    df = df[df["City"].isin(city_order)].copy()
    df["_order"] = df["City"].map({city: idx for idx, city in enumerate(city_order)})
    df = df.sort_values("_order").reset_index(drop=True)

    if len(df) == 0:
        raise SystemExit("No rows matched the configured city pairs.")

    y = _pair_spaced_y_positions(df["City"].tolist())
    blended = df["Blended Value of Solar ($/kWh)"].to_numpy(dtype=float)
    lcoe = df["LCOE ($/kWh)"].to_numpy(dtype=float)
    elec = df["Electricity Rate ($/kWh)"].to_numpy(dtype=float)
    export = df["Export Rate ($/kWh)"].to_numpy(dtype=float)

    fig, (ax_left, ax_right) = plt.subplots(
        nrows=1,
        ncols=2,
        figsize=(fig_width, fig_height),
        dpi=260,
        constrained_layout=True,
        sharey=True,
        gridspec_kw={"width_ratios": [1.35, 1.0], "wspace": 0.05},
    )

    # Left: dumbbells between Blended value and LCOE for each city row.
    for i, row in df.iterrows():
        c = city_colors.get(row["City"], "#666666")
        x0 = float(row["Blended Value of Solar ($/kWh)"])
        x1 = float(row["LCOE ($/kWh)"])
        lo, hi = sorted((x0, x1))
        yi = y[i]
        ax_left.hlines(y=yi, xmin=lo, xmax=hi, color=c, linewidth=2.6, alpha=0.55, zorder=1)
        ax_left.scatter(x0, yi, s=48, color=c, edgecolor="black", linewidth=0.6, zorder=2)
        ax_left.scatter(
            x1,
            yi,
            s=48,
            facecolor="white",
            edgecolor=c,
            linewidth=1.5,
            zorder=3,
        )

    ax_left.set_yticks(y)
    ax_left.set_yticklabels([DISPLAY_NAME_MAP.get(c, c) for c in df["City"]], fontsize=13)
    ax_left.invert_yaxis()
    ax_left.grid(axis="x", linestyle="--", alpha=0.25)
    ax_left.set_xlabel("Value ($/kWh)", fontsize=11)
    ax_left.set_ylabel("")
    ax_left.tick_params(axis="x", labelsize=12)
    ax_left.tick_params(
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

    # Right: two bars per city (Electricity Rate and Export Rate), sharing y-axis.
    bar_h = 0.24
    for i, row in df.iterrows():
        c = city_colors.get(row["City"], "#666666")
        yi = y[i]
        y0 = yi - bar_h / 2.0
        y1 = yi + bar_h / 2.0
        ax_right.barh(
            y=y0,
            width=float(row["Electricity Rate ($/kWh)"]),
            height=bar_h,
            color=c,
            alpha=0.78,
            edgecolor="black",
            linewidth=0.5,
        )
        ax_right.barh(
            y=y1,
            width=float(row["Export Rate ($/kWh)"]),
            height=bar_h,
            color=c,
            alpha=0.38,
            edgecolor="black",
            linewidth=0.5,
            hatch="//",
        )

    ax_right.grid(axis="x", linestyle="--", alpha=0.25)
    ax_right.set_xlabel("Rate ($/kWh)", fontsize=11)
    ax_right.tick_params(
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

    left_max = max(float(np.nanmax(blended)), float(np.nanmax(lcoe)))
    right_max = max(float(np.nanmax(elec)), float(np.nanmax(export)))
    ax_left.set_xlim(0.0, left_max * 1.06)
    ax_right.set_xlim(0.0, right_max * 1.04)

    legend_handles = [
        Line2D([0], [0], marker="o", linestyle="None", markersize=7,
             markerfacecolor="#4a4a4a", markeredgecolor="black", label="Blended Solar Value"),
        Line2D([0], [0], marker="o", linestyle="None", markersize=7,
               markerfacecolor="white", markeredgecolor="#4a4a4a", markeredgewidth=1.5, label="LCOE"),
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

    for axis in (ax_left, ax_right):
        axis.spines["left"].set_visible(True)
        axis.spines["bottom"].set_visible(True)
        axis.spines["top"].set_visible(False)
        axis.spines["right"].set_visible(False)
        axis.spines["left"].set_linewidth(0.8)
        axis.spines["bottom"].set_linewidth(0.8)
        axis.spines["left"].set_color("#555555")
        axis.spines["bottom"].set_color("#555555")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, bbox_inches="tight")
    plt.close(fig)
    print(f"[ok] Saved figure: {out_path}")


def _load_uncertainty_module() -> ModuleType:
    module_path = (
        BORDER_ROOT
        / "code"
        / "original"
        / "plot_fig4_uncertainty_supplement.py"
    )
    if not module_path.exists():
        raise SystemExit(f"Uncertainty script not found: {module_path}")

    spec = importlib.util.spec_from_file_location("plot_fig4_uncertainty_supplement", module_path)
    if spec is None or spec.loader is None:
        raise SystemExit(f"Failed to load module spec for: {module_path}")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def build_plot_with_errorbars(out_path: Path, fig_width: float, fig_height: float, dpi: int) -> None:
    mod = _load_uncertainty_module()
    if not hasattr(mod, "build_uncertainty_results") or not hasattr(mod, "plot_panel_c"):
        raise SystemExit(
            "Uncertainty module missing expected functions: build_uncertainty_results / plot_panel_c"
        )

    city_results, _summary_df = mod.build_uncertainty_results()
    mod.plot_panel_c(city_results, out_path, fig_width=fig_width, fig_height=fig_height, dpi=dpi)
    print(f"[ok] Saved figure (with error bars): {out_path}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Create city-row dumbbell chart for Blended Value vs LCOE, plus a shared-x "
            "bar panel for Electricity Rate and Export Rate."
        )
    )
    parser.add_argument(
        "--data",
        type=Path,
        default=_default_economic_csv(),
        help="Path to economic_analysis_results.csv",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=BORDER_ROOT / "manuscript" / "figures" / "panels" / "blended_lcoe_citypair_dumbbell_with_rates.pdf",
        help="Output figure path",
    )
    parser.add_argument(
        "--errorbars",
        dest="errorbars",
        action="store_true",
        default=True,
        help="Use Monte Carlo uncertainty error bars (default).",
    )
    parser.add_argument(
        "--no-errorbars",
        dest="errorbars",
        action="store_false",
        help="Disable error bars and plot deterministic values from economic_analysis_results.csv.",
    )
    parser.add_argument("--fig-width", type=float, default=7.2, help="Figure width")
    parser.add_argument("--fig-height", type=float, default=4.64, help="Figure height")
    args = parser.parse_args()

    if args.errorbars:
        build_plot_with_errorbars(out_path=args.out, fig_width=args.fig_width, fig_height=args.fig_height, dpi=260)
        return

    build_plot(csv_path=args.data, out_path=args.out, fig_width=args.fig_width, fig_height=args.fig_height)


if __name__ == "__main__":
    main()

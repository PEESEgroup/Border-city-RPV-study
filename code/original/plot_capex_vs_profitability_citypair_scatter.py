#!/usr/bin/env python3
"""Plot Net CAPEX vs NPV in split panels with IRR-sized bubbles."""

from __future__ import annotations

import argparse
import os
from pathlib import Path

os.environ.setdefault("MPLCONFIGDIR", "/tmp/matplotlib")

import numpy as np
import pandas as pd

try:
    import matplotlib.pyplot as plt
    import matplotlib.patheffects as pe
    from matplotlib.ticker import MaxNLocator
except ModuleNotFoundError as exc:
    raise SystemExit(
        "matplotlib is required for plotting. Install it with: pip install matplotlib"
    ) from exc

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

PAIR_LINESTYLES = {
    ("vienna", "bratislava"): "-",
    ("singapore", "johorbahru"): "-",
    ("sandiego", "tijuana"): "-",
    ("elpaso", "juarez"): "--",
    ("hongkong", "shenzhen"): ":",
    ("monaco", "nice"): ":",
}

FOCUS_PAIR_ORDER = [
    ("El Paso", "Ciudad Juarez"),
    ("Hong Kong", "Shenzhen"),
    ("Monaco", "Nice"),
]

CITY_SHORT_LABELS = {
    "Vienna": "VIE",
    "Bratislava": "BTS",
    "San Diego": "SD",
    "Tijuana": "TJ",
    "El Paso": "EP",
    "Ciudad Juarez": "JUA",
    "Hong Kong": "HK",
    "Shenzhen": "SZ",
    "Singapore": "SG",
    "Johor Bahru": "JB",
    "Monaco": "MON",
    "Nice": "NCE",
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

CITY_LABEL_OFFSETS = {
    "Vienna": (-0.02, 0.00, "right", "top"),
    "Bratislava": (0.00, -0.018, "left", "top"),
    "San Diego": (-0.010, 0.070, "right", "bottom"),
    "Tijuana": (-0.028, -0.034, "right", "top"),
    "El Paso": (0.018, 0.022, "left", "bottom"),
    "Ciudad Juarez": (0.030, 0.008, "left", "bottom"),
    "Hong Kong": (0.1, 0.07, "right", "bottom"),
    "Shenzhen": (0.020, 0.024, "left", "top"),
    "Singapore": (0.020, 0.040, "left", "bottom"),
    "Johor Bahru": (0.020, 0.030, "left", "bottom"),
    "Monaco": (0.020, -0.040, "right", "top"),
    "Nice": (-0.030, 0.04, "right", "top"),
}

X_FACTOR = "Net CAPEX ($)"
Y_FACTOR = "NPV ($)"
IRR_FACTOR = "IRR (%)"
AXIS_LABEL_FONTSIZE = 11
TICK_LABEL_FONTSIZE = 11
CITY_NAME_FONTSIZE = 11

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


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Plot city-level profitability vs CAPEX scatter with border-city pairs "
            "connected by lines and IRR encoded by bubble size."
        )
    )
    parser.add_argument(
        "--economic-csv",
        default=str(_default_economic_csv()),
        help="City-level economic analysis results CSV.",
    )
    parser.add_argument(
        "--out-png",
        default=str(BORDER_ROOT / "manuscript" / "figures" / "panels" / "capex_vs_profitability.pdf"),
        help="Output figure path.",
    )
    parser.add_argument(
        "--title",
        default="",
        help="Plot title.",
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
    return f"{city1_key}-{city2_key}"


def _city_pair_color(city: str) -> str:
    city_key = _city_key(city)
    for pair in PAIR_ORDER:
        pair_key = tuple(_pair_key(pair[0], pair[1]).split("-"))
        normalized_pair = (
            "juarez" if _city_key(pair[0]) == "ciudadjuarez" else _city_key(pair[0]),
            "juarez" if _city_key(pair[1]) == "ciudadjuarez" else _city_key(pair[1]),
        )
        if city_key in normalized_pair:
            pair_colors = PAIR_COLORS.get(pair_key, PAIR_COLORS.get(normalized_pair))
            if pair_colors is None:
                return "#7d8597"
            return pair_colors[0] if city_key == normalized_pair[0] else pair_colors[1]
    return "#7d8597"


def _pair_colors(city1: str, city2: str) -> tuple[str, str] | None:
    pair_key = tuple(_pair_key(city1, city2).split("-"))
    return PAIR_COLORS.get(pair_key)


def load_plot_data(csv_path: Path) -> pd.DataFrame:
    df = pd.read_csv(csv_path).copy()
    required_cols = {"City", X_FACTOR, Y_FACTOR, IRR_FACTOR}
    missing = required_cols - set(df.columns)
    if missing:
        raise ValueError(f"Missing columns in economic CSV: {sorted(missing)}")

    for col in [X_FACTOR, Y_FACTOR, IRR_FACTOR]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df = df.dropna(subset=["City", X_FACTOR, Y_FACTOR, IRR_FACTOR]).reset_index(drop=True)
    if df.empty:
        raise ValueError("No valid rows available after dropping NaNs.")

    return df


def _build_sizes(values: pd.Series, min_size: float = 70.0, max_size: float = 520.0) -> np.ndarray:
    arr = values.astype(float).to_numpy()
    if len(arr) == 0:
        return np.array([], dtype=float)

    vmin = float(np.nanmin(arr))
    vmax = float(np.nanmax(arr))
    if np.isclose(vmin, vmax):
        return np.full_like(arr, (min_size + max_size) / 2.0, dtype=float)
    scaled = (arr - vmin) / (vmax - vmin)
    return min_size + scaled * (max_size - min_size)


def _map_size(
    value: float, vmin: float, vmax: float, min_size: float = 70.0, max_size: float = 520.0
) -> float:
    if np.isclose(vmin, vmax):
        return (min_size + max_size) / 2.0
    scaled = (float(value) - vmin) / (vmax - vmin)
    return min_size + scaled * (max_size - min_size)


def plot_city_scatter(
    df: pd.DataFrame,
    out_path: Path,
    title: str,
) -> None:
    x = df[X_FACTOR].astype(float)
    y = df[Y_FACTOR].astype(float)
    irr = df[IRR_FACTOR].astype(float)
    sizes = _build_sizes(irr)
    size_by_city = dict(zip(df["City"].astype(str), sizes))

    focus_pair_keys = {tuple(_pair_key(city1, city2).split("-")) for city1, city2 in FOCUS_PAIR_ORDER}
    left_pairs = [
        pair for pair in PAIR_ORDER if tuple(_pair_key(pair[0], pair[1]).split("-")) not in focus_pair_keys
    ]
    right_pairs = [
        pair for pair in PAIR_ORDER if tuple(_pair_key(pair[0], pair[1]).split("-")) in focus_pair_keys
    ]

    fig, axes = plt.subplots(
        ncols=2,
        figsize=(6.2, 4.5),
        dpi=220,
        sharex=True,
        sharey=True,
        gridspec_kw={"width_ratios": [1.0, 1.0], "wspace": 0.08},
    )

    pair_lookup = df.set_index("City")
    x_span = float(x.max() - x.min()) if len(x) else 0.0
    y_span = float(y.max() - y.min()) if len(y) else 0.0
    base_dx = 0.022 * x_span if x_span > 0 else 60.0
    base_dy = 0.026 * y_span if y_span > 0 else 170.0
    text_effects = [pe.withStroke(linewidth=3.0, foreground="white", alpha=0.90)]

    x_pad = x_span * 0.10 if x_span > 0 else 300.0
    y_pad = y_span * 0.12 if y_span > 0 else 500.0
    x_limits = (float(x.min()) - x_pad, float(x.max()) + x_pad)
    y_limits = (float(y.min()) - y_pad, float(y.max()) + y_pad)

    def draw_panel(ax: plt.Axes, pair_order: list[tuple[str, str]]) -> None:
        plotted_cities: set[str] = set()
        for city1, city2 in pair_order:
            if city1 not in pair_lookup.index or city2 not in pair_lookup.index:
                continue

            x1, y1 = float(pair_lookup.at[city1, X_FACTOR]), float(pair_lookup.at[city1, Y_FACTOR])
            x2, y2 = float(pair_lookup.at[city2, X_FACTOR]), float(pair_lookup.at[city2, Y_FACTOR])
            pair_key = tuple(_pair_key(city1, city2).split("-"))
            pair_colors = _pair_colors(city1, city2)
            line_color = pair_colors[0] if pair_colors is not None else "#999999"
            ax.plot(
                [x1, x2],
                [y1, y2],
                color=line_color,
                linestyle=PAIR_LINESTYLES.get(pair_key, "-"),
                linewidth=1.4,
                alpha=0.9,
                zorder=1,
            )

            for city in (city1, city2):
                plotted_cities.add(city)
                ax.scatter(
                    [float(pair_lookup.at[city, X_FACTOR])],
                    [float(pair_lookup.at[city, Y_FACTOR])],
                    s=size_by_city.get(city, 120.0),
                    c=[_city_pair_color(city)],
                    alpha=0.82,
                    edgecolors="#333333",
                    linewidths=0.7,
                    zorder=2,
                )

        for city_name in plotted_cities:
            label = CITY_DISPLAY_NAMES.get(city_name, city_name)
            label_color = _city_pair_color(city_name)
            text_x = float(pair_lookup.at[city_name, X_FACTOR]) + base_dx
            text_y = float(pair_lookup.at[city_name, Y_FACTOR]) + base_dy
            ha = "left"
            va = "bottom"

            if city_name in CITY_LABEL_OFFSETS:
                ox, oy, ha, va = CITY_LABEL_OFFSETS[city_name]
                text_x = float(pair_lookup.at[city_name, X_FACTOR]) + ox * x_span
                text_y = float(pair_lookup.at[city_name, Y_FACTOR]) + oy * y_span

            ax.text(
                text_x,
                text_y,
                label,
                fontsize=CITY_NAME_FONTSIZE,
                ha=ha,
                va=va,
                color=label_color,
                path_effects=text_effects,
                zorder=4,
            )

    draw_panel(axes[0], left_pairs)
    draw_panel(axes[1], right_pairs)

    for ax in axes:
        ax.set_xlim(*x_limits)
        ax.set_ylim(*y_limits)
        ax.xaxis.set_major_locator(MaxNLocator(nbins=4))
        ax.grid(True, alpha=0.25, linestyle="--")
        ax.tick_params(
            axis="both",
            which="both",
            labelsize=TICK_LABEL_FONTSIZE,
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

    axes[0].set_ylabel(Y_FACTOR, fontsize=AXIS_LABEL_FONTSIZE)
    axes[1].tick_params(labelleft=False)
    fig.supxlabel(X_FACTOR, fontsize=AXIS_LABEL_FONTSIZE, y=0.055)

    legend_values = np.quantile(irr, [0.25, 0.5, 0.75])
    legend_values = np.unique(np.round(legend_values, 0))
    vmin = float(irr.min())
    vmax = float(irr.max())
    legend_handles = [
        axes[1].scatter(
            [],
            [],
            s=_map_size(v, vmin, vmax),
            color="#9e9e9e",
            alpha=0.8,
            edgecolors="#333333",
            linewidths=0.7,
        )
        for v in legend_values
    ]
    legend_labels = [f"{int(v):,}" for v in legend_values]
    if legend_handles:
        axes[1].legend(
            legend_handles,
            legend_labels,
            loc="upper left",
            ncol=1,
            frameon=False,
            fontsize=8.5,
            title="IRR (%)",
            title_fontsize=9.5,
            borderaxespad=0.0,
            handletextpad=1.0,
            labelspacing=1.0,
        )

    if title:
        fig.suptitle(title, fontsize=12)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.subplots_adjust(bottom=0.18)
    fig.savefig(out_path, bbox_inches="tight")
    if out_path.suffix.lower() == ".pdf":
        fig.savefig(out_path.with_suffix(".png"), bbox_inches="tight", dpi=220)
    plt.close(fig)


def main() -> None:
    args = parse_args()
    df = load_plot_data(Path(args.economic_csv))
    plot_city_scatter(df, Path(args.out_png), args.title)


if __name__ == "__main__":
    main()

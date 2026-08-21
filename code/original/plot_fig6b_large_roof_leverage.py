import argparse
import csv
from pathlib import Path
from typing import Dict, List, Tuple

from plot_fig6a_roofsize_utilization_share import (
    DEFAULT_BORDER_PAIRS,
    PAIR_COLORS,
    SHOW_NAME_MAP,
    load_rows,
    parse_pairs_arg,
)

PAIR_LINESTYLES = {
    ("vienna", "bratislava"): "-",
    ("singapore", "johorbahru"): "-",
    ("sandiego", "tijuana"): "-",
    ("elpaso", "juarez"): "--",
    ("hongkong", "shenzhen"): ":",
    ("monaco", "nice"): ":",
}

SHORT_CITY_LABELS: Dict[str, str] = {
    "vienna": "VIE",
    "bratislava": "BRA",
    "singapore": "SIN",
    "johorbahru": "JB",
    "sandiego": "SD",
    "tijuana": "TIJ",
    "elpaso": "EP",
    "juarez": "JUA",
    "hongkong": "HK",
    "shenzhen": "SZ",
    "monaco": "MON",
    "nice": "NIC",
}

LABEL_OFFSETS: Dict[str, Tuple[float, float]] = {
    "vienna": (-5, 4),
    "bratislava": (4, -5),
    "singapore": (-5, 4),
    "johorbahru": (4, -5),
    "sandiego": (4, 4),
    "tijuana": (4, 4),
    "elpaso": (4, 0),
    "juarez": (4, -5),
    "hongkong": (-4, 5),
    "shenzhen": (4, 4),
    "monaco": (4, -5),
    "nice": (4, -4),
}

TICK_LABEL_SIZE = 9.6


def _large_roof_row(rows: List[Dict[str, float]]) -> Dict[str, float]:
    for row in rows:
        if str(row["roof_size_bin"]).strip() == "1000+":
            return row
    return max(rows, key=lambda item: float(item["bin_left_m2"]))


def compute_large_roof_metrics(
    city_rows: Dict[str, List[Dict[str, float]]],
    pairs: List[Tuple[str, str]],
) -> Tuple[List[Dict[str, float]], List[Dict[str, float]]]:
    points: List[Dict[str, float]] = []
    point_by_city: Dict[str, Dict[str, float]] = {}

    for city, rows in city_rows.items():
        total_roof_area = sum(float(row["building_area_m2"]) for row in rows)
        total_pv_area = sum(float(row["pv_area_m2"]) for row in rows)
        large_row = _large_roof_row(rows)
        large_area = float(large_row["building_area_m2"])
        large_pv_area = float(large_row["pv_area_m2"])
        area_share = large_area / total_roof_area if total_roof_area > 0 else 0.0
        utilization = float(large_row["pv_area_ratio"])
        absolute_contribution = area_share * utilization
        pv_area_share = large_pv_area / total_pv_area if total_pv_area > 0 else 0.0
        all_utilization = total_pv_area / total_roof_area if total_roof_area > 0 else 0.0
        point = {
            "city": city,
            "area_share_1000": area_share,
            "pv_utilization_1000": utilization,
            "absolute_contribution_1000": absolute_contribution,
            "pv_area_share_1000": pv_area_share,
            "all_utilization": all_utilization,
        }
        points.append(point)
        point_by_city[city] = point

    uplifts: List[Dict[str, float]] = []
    for city_a, city_b in pairs:
        if city_a not in point_by_city or city_b not in point_by_city:
            continue
        point_a = point_by_city[city_a]
        point_b = point_by_city[city_b]
        frontier = max(point_a["pv_utilization_1000"], point_b["pv_utilization_1000"])
        for point in (point_a, point_b):
            if point["pv_utilization_1000"] >= frontier:
                continue
            uplift = point["area_share_1000"] * (frontier - point["pv_utilization_1000"])
            counterfactual_all = point["all_utilization"] + uplift
            relative_uplift = uplift / point["all_utilization"] if point["all_utilization"] > 0 else 0.0
            uplifts.append(
                {
                    "city": point["city"],
                    "pair": f"{city_a}-{city_b}",
                    "uplift_all": uplift,
                    "relative_uplift_all": relative_uplift,
                    "all_utilization_current": point["all_utilization"],
                    "all_utilization_counterfactual": counterfactual_all,
                    "frontier_utilization_1000": frontier,
                    "current_utilization_1000": point["pv_utilization_1000"],
                    "area_share_1000": point["area_share_1000"],
                }
            )
    return points, uplifts


def write_metrics_csv(points: List[Dict[str, float]], uplifts: List[Dict[str, float]], out_csv: Path) -> None:
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    with out_csv.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(
            [
                "kind",
                "city",
                "area_share_1000",
                "pv_utilization_1000",
                "absolute_contribution_1000",
                "pv_area_share_1000",
                "all_utilization_current",
                "uplift_all",
                "relative_uplift_all",
                "all_utilization_counterfactual",
                "frontier_utilization_1000",
            ]
        )
        for point in points:
            writer.writerow(
                [
                    "actual",
                    point["city"],
                    point["area_share_1000"],
                    point["pv_utilization_1000"],
                    point["absolute_contribution_1000"],
                    point["pv_area_share_1000"],
                    point["all_utilization"],
                    "",
                    "",
                    "",
                    "",
                ]
            )
        for uplift in uplifts:
            writer.writerow(
                [
                    "counterfactual_uplift",
                    uplift["city"],
                    uplift["area_share_1000"],
                    uplift["current_utilization_1000"],
                    "",
                    "",
                    uplift["all_utilization_current"],
                    uplift["uplift_all"],
                    uplift["relative_uplift_all"],
                    uplift["all_utilization_counterfactual"],
                    uplift["frontier_utilization_1000"],
                ]
            )


def _bubble_sizes(values: List[float]) -> List[float]:
    if not values:
        return []
    max_value = max(values)
    if max_value <= 0:
        return [65.0 for _ in values]
    return [45.0 + 360.0 * (value / max_value) for value in values]


def plot_large_roof_leverage(
    city_rows: Dict[str, List[Dict[str, float]]],
    pairs: List[Tuple[str, str]],
    out_png: Path,
    out_csv: Path | None,
) -> None:
    try:
        import matplotlib.pyplot as plt
        import numpy as np
        from matplotlib.patches import Patch
    except ImportError as exc:
        raise SystemExit(
            "matplotlib and numpy are required to plot Figure 6b. Install with: pip install matplotlib numpy"
        ) from exc

    points, uplifts = compute_large_roof_metrics(city_rows, pairs)
    point_by_city = {point["city"]: point for point in points}
    ordered_cities = [city for pair in pairs for city in pair if city in point_by_city]
    ordered_points = [point_by_city[city] for city in ordered_cities]
    if not ordered_points:
        raise SystemExit("No valid city pairs found in the CSV.")

    if out_csv is not None:
        write_metrics_csv(ordered_points, uplifts, out_csv)

    fig, (ax, uplift_ax) = plt.subplots(
        nrows=1,
        ncols=2,
        figsize=(6.3, 3.75),
        dpi=220,
        gridspec_kw={"width_ratios": [2.2, 1.08], "wspace": 0.01},
        layout="constrained",
    )
    fig.set_constrained_layout_pads(w_pad=0.02, h_pad=0.02, wspace=0.02, hspace=0.02)
    fig.patch.set_facecolor("white")
    ax.set_facecolor("white")

    x_vals = np.array([point["area_share_1000"] * 100.0 for point in ordered_points])
    y_vals = np.array([point["pv_utilization_1000"] * 100.0 for point in ordered_points])
    pv_area_share_pct = [point["pv_area_share_1000"] * 100.0 for point in ordered_points]
    size_by_city = dict(zip(ordered_cities, _bubble_sizes(pv_area_share_pct)))

    x_mid = float(np.median(x_vals))
    y_mid = float(np.median(y_vals))
    ax.axvline(x_mid, color="#8d8178", linewidth=0.8, linestyle="--", alpha=0.24, zorder=0)
    ax.axhline(y_mid, color="#8d8178", linewidth=0.8, linestyle="--", alpha=0.24, zorder=0)

    for city_a, city_b in pairs:
        if city_a not in point_by_city or city_b not in point_by_city:
            continue
        point_a = point_by_city[city_a]
        point_b = point_by_city[city_b]
        color_a, color_b = PAIR_COLORS.get((city_a, city_b), ("#4f7cac", "#8c4f3f"))
        ax.plot(
            [point_a["area_share_1000"] * 100.0, point_b["area_share_1000"] * 100.0],
            [point_a["pv_utilization_1000"] * 100.0, point_b["pv_utilization_1000"] * 100.0],
            color=color_a,
            linestyle=PAIR_LINESTYLES.get((city_a, city_b), "-"),
            linewidth=1.3,
            alpha=0.85,
            zorder=1,
        )
        for city, point, color in ((city_a, point_a, color_a), (city_b, point_b, color_b)):
            ax.scatter(
                point["area_share_1000"] * 100.0,
                point["pv_utilization_1000"] * 100.0,
                s=size_by_city[city],
                color=color,
                edgecolors="#333333",
                linewidths=0.6,
                alpha=0.84,
                zorder=3,
            )
            dx, dy = LABEL_OFFSETS.get(city, (5.0, 5.0))
            ax.annotate(
                SHORT_CITY_LABELS.get(city, SHOW_NAME_MAP.get(city, city.title())),
                xy=(point["area_share_1000"] * 100.0, point["pv_utilization_1000"] * 100.0),
                xytext=(dx, dy),
                textcoords="offset points",
                ha="left" if dx >= 0 else "right",
                va="bottom" if dy >= 0 else "top",
                fontsize=9.6,
                color="#2f2a27",
                zorder=5,
            )

    ax.text(0.97, 0.88, "large opportunity\n+ high utilization", transform=ax.transAxes,
            ha="right", va="top", fontsize=8.2, color="#6e6259",
            bbox={"facecolor": "white", "edgecolor": "none", "alpha": 0.72, "pad": 1.2})
    ax.text(0.97, 0.07, "large opportunity,\nunderdeveloped", transform=ax.transAxes,
            ha="right", va="bottom", fontsize=8.2, color="#8d8178")
    ax.text(0.04, 0.07, "limited leverage", transform=ax.transAxes,
            ha="left", va="bottom", fontsize=8.2, color="#8d8178")

    ax.set_xlabel("Share of rooftop area in 1000+ m² roofs (%)", fontsize=10.8, color="black")
    ax.set_ylabel("PV utilization in 1000+ m² roofs (%)", fontsize=10.8, color="black")
    ax.tick_params(axis="both", labelsize=TICK_LABEL_SIZE, colors="black")
    ax.grid(axis="both", linestyle="--", alpha=0.22, color="#8d8178")
    ax.set_axisbelow(True)
    for spine in ("top", "right"):
        ax.spines[spine].set_visible(False)
    ax.spines["left"].set_color("#6e6259")
    ax.spines["bottom"].set_color("#6e6259")

    x_pad = max(2.5, (float(x_vals.max()) - float(x_vals.min())) * 0.06)
    y_pad = max(0.45, (float(y_vals.max()) - float(y_vals.min())) * 0.08)
    ax.set_xlim(max(0.0, float(x_vals.min()) - x_pad), min(100.0, float(x_vals.max()) + x_pad + 2.0))
    ax.set_ylim(0.0, float(y_vals.max()) + y_pad)

    max_pv_area_share = max(pv_area_share_pct) if pv_area_share_pct else 1.0
    size_legend_values = [25.0, 50.0, 75.0]
    handles = [
        ax.scatter(
            [],
            [],
            s=45.0 + 360.0 * (value / max_pv_area_share),
            color="#b9b0aa",
            edgecolor="white",
            linewidth=0.9,
            alpha=0.75,
        )
        for value in size_legend_values
        if value <= max_pv_area_share * 1.05
    ]
    labels = [f"{value:g}%" for value in size_legend_values if value <= max_pv_area_share * 1.05]
    if handles:
        ax.legend(
            handles,
            labels,
            title="1000+ m² share\nof total PV area",
            loc="upper left",
            frameon=False,
            fontsize=8.2,
            title_fontsize=8.4,
            borderpad=0.2,
            labelspacing=0.65,
            handletextpad=1.1,
        )

    uplift_order = [city for pair in pairs for city in pair]
    ordered_uplifts = sorted(uplifts, key=lambda item: uplift_order.index(item["city"]))
    y_pos = np.arange(len(ordered_uplifts), dtype=float)
    current_vals = np.array([item["all_utilization_current"] * 100.0 for item in ordered_uplifts], dtype=float)
    potential_vals = np.array([item["uplift_all"] * 100.0 for item in ordered_uplifts], dtype=float)
    counterfactual_vals = current_vals + potential_vals
    uplift_colors = []
    for item in ordered_uplifts:
        pair_a, pair_b = item["pair"].split("-")
        color_a, color_b = PAIR_COLORS.get((pair_a, pair_b), ("#4f7cac", "#8c4f3f"))
        uplift_colors.append(color_a if item["city"] == pair_a else color_b)
    uplift_ax.barh(
        y_pos,
        current_vals,
        color="#d6d0ca",
        alpha=0.9,
        edgecolor="white",
        linewidth=0.5,
        label="Current",
    )
    uplift_ax.barh(
        y_pos,
        potential_vals,
        left=current_vals,
        color=uplift_colors,
        alpha=0.88,
        edgecolor="white",
        linewidth=0.5,
        label="Benchmark uplift",
    )
    for y, value, item in zip(y_pos, counterfactual_vals, ordered_uplifts):
        label = (
            f"{item['all_utilization_current'] * 100:.2f}%"
            f" -> {item['all_utilization_counterfactual'] * 100:.2f}%"
        )
        uplift_ax.text(
            value + max(float(counterfactual_vals.max()), 1.0) * 0.025,
            y,
            label,
            ha="left",
            va="center",
            fontsize=6.8,
            color="#2f2a27",
        )
    uplift_ax.set_yticks(y_pos)
    uplift_ax.set_yticklabels(
        [SHORT_CITY_LABELS.get(item["city"], item["city"].title()) for item in ordered_uplifts],
        fontsize=TICK_LABEL_SIZE,
    )
    uplift_ax.set_xlim(0.0, max(float(counterfactual_vals.max()) * 1.38, 1.0))
    uplift_ax.invert_yaxis()
    uplift_ax.set_xlabel("All PV utilization (%)", fontsize=11.0)
    uplift_ax.legend(
        handles=[
            Patch(facecolor="#d6d0ca", edgecolor="white", label="Current"),
            Patch(facecolor="#8d8178", edgecolor="white", label="Benchmark uplift"),
        ],
        loc="lower right",
        frameon=False,
        fontsize=7.0,
        handlelength=1.2,
        borderpad=0.2,
        labelspacing=0.35,
    )
    # uplift_ax.set_title(
    #     "Illustrative counterfactual\nuplift (not causal)",
    #     fontsize=8.6,
    #     pad=4.0,
    # )
    uplift_ax.tick_params(axis="x", labelsize=TICK_LABEL_SIZE, colors="black", length=2.5)
    uplift_ax.tick_params(axis="y", labelsize=TICK_LABEL_SIZE, colors="black", length=0)
    uplift_ax.grid(axis="x", linestyle="--", alpha=0.24, color="#8d8178")
    uplift_ax.set_axisbelow(True)
    for spine in ("top", "right"):
        uplift_ax.spines[spine].set_visible(False)
    uplift_ax.spines["left"].set_color("#6e6259")
    uplift_ax.spines["bottom"].set_color("#6e6259")

    out_png.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_png, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"[ok] Saved plot: {out_png}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Plot Figure 6b: large-roof leverage and illustrative observed-utilization benchmark uplift."
    )
    parser.add_argument(
        "--input-csv",
        type=Path,
        default=Path("REPOSITORY_ROOT/manuscript/data/Building_PVs/city_roofsize_pv_adoption.csv"),
        help="Input roof-size summary CSV.",
    )
    parser.add_argument(
        "--pairs",
        type=str,
        default=",".join(f"{a}:{b}" for a, b in DEFAULT_BORDER_PAIRS),
        help="Pairs to plot, format: cityA:cityB,cityC:cityD",
    )
    parser.add_argument(
        "--out-png",
        type=Path,
        default=Path("REPOSITORY_ROOT/manuscript/figures/panels/fig_6b_large_roof_leverage.pdf"),
        help="Output figure path.",
    )
    parser.add_argument(
        "--out-csv",
        type=Path,
        default=Path("REPOSITORY_ROOT/manuscript/figures/panels/fig_6b_large_roof_leverage_metrics.csv"),
        help="Optional CSV export of plotted metrics. Pass an empty string to skip.",
    )
    args = parser.parse_args()

    pairs = parse_pairs_arg(args.pairs)
    city_rows = load_rows(args.input_csv)
    out_csv = args.out_csv if str(args.out_csv) else None
    plot_large_roof_leverage(
        city_rows=city_rows,
        pairs=pairs,
        out_png=args.out_png,
        out_csv=out_csv,
    )


if __name__ == "__main__":
    main()

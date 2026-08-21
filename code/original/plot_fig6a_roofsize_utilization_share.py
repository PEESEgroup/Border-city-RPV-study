import argparse
import csv
from pathlib import Path
from typing import Dict, List, Tuple


DEFAULT_BORDER_PAIRS: List[Tuple[str, str]] = [
    ("vienna", "bratislava"),
    ("singapore", "johorbahru"),
    ("sandiego", "tijuana"),
    ("elpaso", "juarez"),
    ("hongkong", "shenzhen"),
    ("monaco", "nice"),
]

SHOW_NAME_MAP: Dict[str, str] = {
    "vienna": "Vienna",
    "bratislava": "Bratislava",
    "elpaso": "El Paso",
    "juarez": "Juarez",
    "sandiego": "San Diego",
    "tijuana": "Tijuana",
    "hongkong": "Hong Kong",
    "shenzhen": "Shenzhen",
    "singapore": "Singapore",
    "johorbahru": "Johor Bahru",
    "nice": "Nice",
    "monaco": "Monaco",
    "detroit": "Detroit",
    "windsor": "Windsor",
}

PAIR_COLORS: Dict[Tuple[str, str], Tuple[str, str]] = {
    ("vienna", "bratislava"): ("#c97c5d", "#8c4f3f"),
    ("elpaso", "juarez"): ("#4f7cac", "#1f4e79"),
    ("sandiego", "tijuana"): ("#5aa469", "#2f6b3b"),
    ("hongkong", "shenzhen"): ("#b07bac", "#7f4f7c"),
    ("singapore", "johorbahru"): ("#d9a441", "#9a6a12"),
    ("monaco", "nice"): ("#d16d8a", "#8f3458"),
    ("detroit", "windsor"): ("#5b8fdd", "#1e4f91"),
}

METRIC_LABELS = {
    "pv_adoption": "PV adoption",
    "pv_area_ratio": "PV utilization",
}

SHARE_FIELDS = {
    "roof_area": ("building_area_m2", "roof-area share"),
    "building_count": ("building_count", "building-count share"),
}


def parse_pairs_arg(pairs_arg: str) -> List[Tuple[str, str]]:
    pairs: List[Tuple[str, str]] = []
    for item in pairs_arg.split(","):
        item = item.strip()
        if not item:
            continue
        parts = item.split(":")
        if len(parts) != 2:
            raise ValueError(f"Invalid pair format: {item}. Use cityA:cityB,cityC:cityD")
        pairs.append((parts[0].strip().lower(), parts[1].strip().lower()))
    return pairs


def load_rows(csv_path: Path) -> Dict[str, List[Dict[str, float]]]:
    rows: Dict[str, List[Dict[str, float]]] = {}
    with csv_path.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            city = row.get("city", "").strip().lower()
            if not city:
                continue
            rows.setdefault(city, []).append(
                {
                    "roof_size_bin": row.get("roof_size_bin", "").strip(),
                    "bin_left_m2": float(row.get("bin_left_m2", 0.0) or 0.0),
                    "bin_right_m2": float(row.get("bin_right_m2", 0.0) or 0.0),
                    "building_count": float(row.get("building_count", 0.0) or 0.0),
                    "pv_building_count": float(row.get("pv_building_count", 0.0) or 0.0),
                    "pv_adoption": float(row.get("pv_adoption", 0.0) or 0.0),
                    "building_area_m2": float(row.get("building_area_m2", 0.0) or 0.0),
                    "pv_area_m2": float(row.get("pv_area_m2", 0.0) or 0.0),
                    "pv_area_ratio": float(row.get("pv_area_ratio", 0.0) or 0.0),
                }
            )
    for city in rows:
        rows[city].sort(key=lambda item: (item["bin_left_m2"], item["bin_right_m2"]))
    return rows


def _share_values(rows: List[Dict[str, float]], share_metric: str):
    try:
        import numpy as np
    except ImportError as exc:
        raise SystemExit("numpy is required for plotting.") from exc

    field, _ = SHARE_FIELDS[share_metric]
    vals = np.array([float(row[field]) for row in rows], dtype=float)
    total = float(vals.sum())
    if total <= 0:
        return np.zeros(len(rows), dtype=float)
    return vals / total


def draw_roofsize_pair_axis(
    ax,
    rows_a: List[Dict[str, float]],
    rows_b: List[Dict[str, float]],
    city_a: str,
    city_b: str,
    metric: str = "pv_area_ratio",
    as_percent: bool = True,
    share_metric: str = "roof_area",
    show_share_axis: bool = False,
    show_xlabel: bool = False,
    show_metric_label: bool = True,
    show_frontier_label: bool = True,
    frontier_label_inside: bool = False,
):
    try:
        import numpy as np
        from matplotlib.colors import to_rgba
    except ImportError as exc:
        raise SystemExit("numpy is required for plotting.") from exc

    if share_metric not in SHARE_FIELDS:
        raise ValueError(f"Unknown share metric: {share_metric}")

    background = "white"
    color_a, color_b = PAIR_COLORS.get((city_a, city_b), ("#4f7cac", "#8c4f3f"))
    x = np.arange(len(rows_a), dtype=float)
    x_labels = [str(row["roof_size_bin"]) for row in rows_a]
    vals_a = np.array([float(row[metric]) for row in rows_a], dtype=float)
    vals_b = np.array([float(row[metric]) for row in rows_b], dtype=float)
    share_a = _share_values(rows_a, share_metric) * 100.0
    share_b = _share_values(rows_b, share_metric) * 100.0

    if as_percent:
        vals_a *= 100.0
        vals_b *= 100.0

    ax.set_facecolor(background)
    for spine in ("top", "right"):
        ax.spines[spine].set_visible(False)
    ax.spines["left"].set_color("#6e6259")
    ax.spines["bottom"].set_color("#6e6259")

    share_ax = ax.twinx()
    share_width = 0.34
    share_ax.bar(
        x - share_width / 2,
        share_a,
        color=to_rgba(color_a, 0.34),
        width=share_width,
        edgecolor="none",
        linewidth=0.0,
        zorder=0,
    )
    share_ax.bar(
        x + share_width / 2,
        share_b,
        color=to_rgba(color_b, 0.34),
        width=share_width,
        edgecolor="none",
        linewidth=0.0,
        zorder=0,
    )
    share_ax.set_ylim(0.0, 100.0)
    share_ax.set_zorder(0)
    share_ax.patch.set_alpha(0.0)
    share_ax.spines["top"].set_visible(False)
    share_ax.spines["left"].set_visible(False)
    share_ax.spines["right"].set_color("#b9b0aa")
    share_ax.tick_params(axis="y", colors="#8d8178", labelsize=8.5, length=2.5)
    if show_share_axis:
        share_ax.set_yticks([0, 50, 100])
    else:
        share_ax.set_yticks([])
        share_ax.spines["right"].set_visible(False)

    ax.set_zorder(2)
    ax.patch.set_alpha(0.0)
    line_a = ax.plot(
        x,
        vals_a,
        color=color_a,
        marker="o",
        markersize=5.2,
        markeredgecolor="white",
        markeredgewidth=0.7,
        linewidth=2.35,
        label=SHOW_NAME_MAP.get(city_a, city_a.title()),
        zorder=4,
    )[0]
    line_b = ax.plot(
        x,
        vals_b,
        color=color_b,
        marker="o",
        markersize=5.2,
        markeredgecolor="white",
        markeredgewidth=0.7,
        linewidth=2.35,
        label=SHOW_NAME_MAP.get(city_b, city_b.title()),
        zorder=4,
    )[0]

    large_idx = len(x) - 1
    ax.scatter(
        [x[large_idx]],
        [vals_a[large_idx]],
        s=60,
        color=color_a,
        edgecolor="black",
        linewidth=0.9,
        zorder=6,
    )
    ax.scatter(
        [x[large_idx]],
        [vals_b[large_idx]],
        s=60,
        color=color_b,
        edgecolor="black",
        linewidth=0.9,
        zorder=6,
    )

    all_vals = np.concatenate([vals_a, vals_b])
    local_max = float(all_vals.max()) if all_vals.size else 0.0
    ax.set_ylim(0.0, local_max * 1.2 if local_max > 0 else 1.0)
    ax.grid(axis="y", linestyle="--", alpha=0.28, color="#8d8178")
    ax.set_xticks(x)
    ax.set_xticklabels(x_labels, rotation=30, ha="right", fontsize=10.2)
    ax.tick_params(axis="x", labelsize=10.2, colors="black")
    ax.tick_params(axis="y", labelsize=10.2, colors="black")
    ax.set_xlabel("Roof size bin (m²)" if show_xlabel else "", fontsize=11.0, color="black")

    _, share_label = SHARE_FIELDS[share_metric]
    if show_metric_label:
        ax.text(
            0.01,
            0.93,
            f"{METRIC_LABELS[metric]}\npale bars: {share_label}",
            transform=ax.transAxes,
            ha="left",
            va="top",
            fontsize=9.4,
            color="#544a43",
            linespacing=1.15,
        )
    if show_frontier_label:
        label_box = {
            "boxstyle": "round,pad=0.12",
            "facecolor": "white",
            "edgecolor": "none",
            "alpha": 0.72,
        }
        if frontier_label_inside:
            ax.text(
                0.985,
                0.9,
                "large-roof\nbenchmark",
                transform=ax.transAxes,
                ha="right",
                va="top",
                fontsize=8.8,
                color="#2f2a27",
                linespacing=1.05,
                bbox=label_box,
                zorder=8,
            )
        else:
            frontier_y = max(float(vals_a[large_idx]), float(vals_b[large_idx]))
            ax.annotate(
                "large-roof\nbenchmark",
                xy=(x[large_idx], frontier_y),
                xytext=(-3, 12),
                textcoords="offset points",
                ha="right",
                va="bottom",
                fontsize=8.8,
                color="#2f2a27",
                linespacing=1.05,
                bbox=label_box,
                zorder=8,
            )
    return line_a, line_b, share_ax


def add_large_roof_frontier_xtick_note(ax, x_index: int | None = None) -> None:
    if x_index is None:
        x_index = len(ax.get_xticks()) - 1
    ax.annotate(
        "large-roof benchmark",
        xy=(x_index, 0.0),
        xycoords=("data", "axes fraction"),
        xytext=(0, -30),
        textcoords="offset points",
        ha="center",
        va="top",
        fontsize=9.0,
        color="#2f2a27",
        annotation_clip=False,
    )


def plot_roofsize_pairs(
    city_rows: Dict[str, List[Dict[str, float]]],
    pairs: List[Tuple[str, str]],
    out_png: Path,
    metric: str,
    as_percent: bool,
    share_metric: str,
) -> None:
    try:
        import matplotlib.pyplot as plt
    except ImportError as exc:
        raise SystemExit(
            "matplotlib is required to plot PV adoption by roof size. Install with: pip install matplotlib"
        ) from exc

    valid_pairs = [(a, b) for a, b in pairs if a in city_rows and b in city_rows]
    if not valid_pairs:
        raise SystemExit("No valid city pairs found in the CSV.")

    nrows = len(valid_pairs)
    fig, axes = plt.subplots(
        nrows=nrows,
        ncols=1,
        figsize=(4.9, max(1.32 * nrows, 5.2)),
        dpi=220,
        sharex=True,
        sharey=False,
    )
    if nrows == 1:
        axes = [axes]
    fig.patch.set_facecolor("white")

    for idx, (city_a, city_b) in enumerate(valid_pairs):
        ax = axes[idx]
        line_a, line_b, _ = draw_roofsize_pair_axis(
            ax=ax,
            rows_a=city_rows[city_a],
            rows_b=city_rows[city_b],
            city_a=city_a,
            city_b=city_b,
            metric=metric,
            as_percent=as_percent,
            share_metric=share_metric,
            show_share_axis=True,
            show_xlabel=idx == nrows - 1,
            show_metric_label=False,
            show_frontier_label=False,
        )
        ax.legend(
            [line_a, line_b],
            [line_a.get_label(), line_b.get_label()],
            loc="upper left",
            bbox_to_anchor=(0.0, 1.14),
            ncol=2,
            frameon=False,
            fontsize=10.0,
            handlelength=1.7,
            columnspacing=1.0,
        )

    add_large_roof_frontier_xtick_note(axes[-1])
    out_png.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout(rect=(0.055, 0.02, 0.93, 0.995), h_pad=0.72)
    fig.text(
        0.05,
        0.5,
        "PV utilization (%)" if as_percent else "PV utilization",
        rotation=90,
        ha="left",
        va="center",
        fontsize=10.5,
        color="black",
    )
    fig.text(
        0.95,
        0.5,
        "Share of city stock (%)",
        rotation=270,
        ha="right",
        va="center",
        fontsize=10.5,
        color="#6e6259",
    )
    fig.savefig(out_png, bbox_inches="tight", transparent=True )#transparent=True)
    plt.close(fig)
    print(f"[ok] Saved plot: {out_png}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Plot Figure 6a: roof-size PV utilization with city-stock share bars."
    )
    parser.add_argument(
        "--input-csv",
        type=Path,
        default=Path("REPOSITORY_ROOT/manuscript/data/Building_PVs/city_roofsize_pv_adoption.csv"),
        help="Input CSV generated by calculate_pv_adoption_by_roof_size.py",
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
        default=Path("REPOSITORY_ROOT/manuscript/figures/panels/fig_6a_roofsize_utilization_share.pdf"),
        help="Output figure path.",
    )
    parser.add_argument(
        "--metric",
        type=str,
        choices=["pv_adoption", "pv_area_ratio"],
        default="pv_area_ratio",
        help="Metric to plot. `pv_area_ratio` is PV area / roof area within each roof-size bin.",
    )
    parser.add_argument(
        "--share-metric",
        type=str,
        choices=sorted(SHARE_FIELDS),
        default="roof_area",
        help="Background bar denominator: roof_area or building_count share within each city.",
    )
    parser.add_argument(
        "--as-percent",
        action="store_true",
        default=True,
        help="Plot utilization/adoption values as percentages instead of fractions.",
    )
    args = parser.parse_args()

    pairs = parse_pairs_arg(args.pairs)
    city_rows = load_rows(args.input_csv)
    plot_roofsize_pairs(
        city_rows=city_rows,
        pairs=pairs,
        out_png=args.out_png,
        metric=args.metric,
        as_percent=args.as_percent,
        share_metric=args.share_metric,
    )


if __name__ == "__main__":
    main()

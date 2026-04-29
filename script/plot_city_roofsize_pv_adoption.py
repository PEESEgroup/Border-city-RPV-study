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

BASE_CLASS_ORDER: List[str] = [
    "single-residential",
    "multi-residential",
    "commercial",
    "industrial",
    "public & infrastructure",
    "others",
]

BASE_CLASS_LABELS: Dict[str, str] = {
    "single-residential": "Single-res",
    "multi-residential": "Multi-res",
    "commercial": "Commercial",
    "industrial": "Industrial",
    "public & infrastructure": "Public/Infra",
    "others": "Others",
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


def load_city_base_class_rows(csv_path: Path) -> Dict[str, List[Dict[str, float]]]:
    rows: Dict[str, Dict[str, Dict[str, float]]] = {}
    with csv_path.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get("scope", "").strip().lower() != "city":
                continue
            city = row.get("name", "").strip().lower()
            if not city:
                continue
            base_key = row.get("base_class_key", "").strip().lower()
            if not base_key:
                continue
            rows.setdefault(city, {})
            rows[city][base_key] = {
                "base_class_key": base_key,
                "base_class": row.get("base_class", "").strip(),
                "pv_building_count_ratio": float(row.get("pv_building_count_ratio", 0.0) or 0.0),
            }

    out: Dict[str, List[Dict[str, float]]] = {}
    for city, city_rows in rows.items():
        ordered: List[Dict[str, float]] = []
        for base_key in BASE_CLASS_ORDER:
            if base_key in city_rows:
                ordered.append(city_rows[base_key])
        out[city] = ordered
    return out


def plot_pairs(
    city_rows: Dict[str, List[Dict[str, float]]],
    city_base_class_rows: Dict[str, List[Dict[str, float]]],
    pairs: List[Tuple[str, str]],
    out_png: Path,
    metric: str,
    as_percent: bool,
) -> None:
    try:
        import matplotlib.pyplot as plt
        import numpy as np
        from matplotlib.lines import Line2D
        from matplotlib.patches import Patch
        from matplotlib.legend_handler import HandlerTuple
    except ImportError as exc:
        raise SystemExit(
            "matplotlib is required to plot PV adoption by roof size. Install with: pip install matplotlib"
        ) from exc

    valid_pairs = []
    for a, b in pairs:
        if a in city_rows and b in city_rows and (
            a in city_base_class_rows and b in city_base_class_rows
        ):
            valid_pairs.append((a, b))
    if not valid_pairs:
        raise SystemExit("No valid city pairs found in the CSV.")

    ncols = 2
    nrows = len(valid_pairs)
    fig, axes = plt.subplots(
        nrows=nrows,
        ncols=ncols,
        figsize=(8.6, max(1.48 * nrows, 5.1)),
        dpi=220,
        sharex="col",
        sharey=False,
    )
    if nrows == 1:
        axes = [axes]

    background = "white"
    fig.patch.set_facecolor(background)
    x_labels = [row["roof_size_bin"] for row in city_rows[valid_pairs[0][0]]]

    for row_axes in axes:
        for ax in row_axes:
            ax.set_facecolor(background)
            for spine in ("top", "right"):
                ax.spines[spine].set_visible(False)
            ax.spines["left"].set_color("#6e6259")
            ax.spines["bottom"].set_color("#6e6259")

    for idx, (city_a, city_b) in enumerate(valid_pairs):
        ax_left, ax_right = axes[idx]
        rows_a = city_rows[city_a]
        rows_b = city_rows[city_b]
        x = np.arange(len(rows_a), dtype=float)
        vals_a = np.array([float(r[metric]) for r in rows_a], dtype=float)
        vals_b = np.array([float(r[metric]) for r in rows_b], dtype=float)
        if as_percent:
            vals_a *= 100.0
            vals_b *= 100.0

        color_a, color_b = PAIR_COLORS.get((city_a, city_b), ("#4f7cac", "#8c4f3f"))
        ax_left.plot(
            x,
            vals_a,
            color=color_a,
            marker="o",
            markersize=5.8,
            linewidth=2.45,
            label=SHOW_NAME_MAP.get(city_a, city_a.title()),
        )
        ax_left.plot(
            x,
            vals_b,
            color=color_b,
            marker="o",
            markersize=5.8,
            linewidth=2.45,
            label=SHOW_NAME_MAP.get(city_b, city_b.title()),
        )

        all_vals = np.concatenate([vals_a, vals_b])
        local_max = float(all_vals.max()) if all_vals.size else 0.0
        ymin = 0.0
        ymax = local_max * 1.16 if local_max > 0 else 1.0

        ax_left.set_title("", fontsize=12.0, pad=8)
        ax_left.grid(axis="y", linestyle="--", alpha=0.28, color="#8d8178")
        ax_left.set_ylim(ymin, ymax)
        ax_left.set_xticks(x)
        ax_left.set_xticklabels(x_labels, rotation=30, ha="right", fontsize=10.5)
        ax_left.tick_params(axis="y", labelsize=10.5)
        ax_left.tick_params(axis="x", labelsize=10.5, colors="#544a43")
        ax_left.tick_params(axis="y", colors="#544a43")
        city_base_rows_a = city_base_class_rows.get(city_a, [])
        city_base_rows_b = city_base_class_rows.get(city_b, [])
        base_x = np.arange(len(city_base_rows_a), dtype=float)
        width = 0.36
        base_vals_a = np.array(
            [float(r["pv_building_count_ratio"]) for r in city_base_rows_a], dtype=float
        )
        base_vals_b = np.array(
            [float(r["pv_building_count_ratio"]) for r in city_base_rows_b], dtype=float
        )
        if as_percent:
            base_vals_a *= 100.0
            base_vals_b *= 100.0
        base_labels = [
            BASE_CLASS_LABELS.get(str(r["base_class_key"]).lower(), str(r["base_class"]))
            for r in city_base_rows_a
        ]
        ax_right.bar(
            base_x - width / 2,
            base_vals_a,
            color=color_a,
            width=width,
            alpha=0.88,
            edgecolor="white",
            linewidth=0.9,
        )
        ax_right.bar(
            base_x + width / 2,
            base_vals_b,
            color=color_b,
            width=width,
            alpha=0.88,
            edgecolor="white",
            linewidth=0.9,
        )
        local_max_right = (
            float(np.concatenate([base_vals_a, base_vals_b]).max())
            if len(base_vals_a) or len(base_vals_b)
            else 0.0
        )
        ax_right.set_ylim(0.0, local_max_right * 1.18 if local_max_right > 0 else 1.0)
        ax_right.grid(axis="y", linestyle="--", alpha=0.28, color="#8d8178")
        ax_right.set_xticks(base_x)
        ax_right.set_xticklabels(base_labels, rotation=28, ha="right", fontsize=10.0)
        ax_right.tick_params(axis="x", labelsize=10.0, colors="#544a43")
        ax_right.tick_params(axis="y", labelsize=10.5, colors="#544a43")

    metric_label = {
        "pv_adoption": "PV adoption",
        "pv_area_ratio": "PV utilization",
    }[metric]
    left_xlabel = "Roof size bin (m²)"
    right_xlabel = "Building type"
    for idx, (ax_left, ax_right) in enumerate(axes[: len(valid_pairs)]):
        ax_left.set_ylabel("")
        ax_right.set_ylabel("")
        ax_left.set_xlabel(left_xlabel if idx == len(valid_pairs) - 1 else "", fontsize=11.2)
        ax_right.set_xlabel(right_xlabel if idx == len(valid_pairs) - 1 else "", fontsize=11.2)
        ax_left.text(
            0.01,
            0.92,
            metric_label,
            transform=ax_left.transAxes,
            ha="left",
            va="top",
            fontsize=10.6,
            color="#544a43",
        )

    out_png.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout(rect=(0.04, 0.02, 0.995, 0.995), h_pad=1.55, w_pad=1.5)

    for idx, (city_a, city_b) in enumerate(valid_pairs):
        ax_left, ax_right = axes[idx]
        color_a, color_b = PAIR_COLORS.get((city_a, city_b), ("#4f7cac", "#8c4f3f"))
        left_box = ax_left.get_position()
        right_box = ax_right.get_position()
        center_x = (left_box.x0 + right_box.x1) / 2.0
        legend_y = max(left_box.y1, right_box.y1) + 0.012
        legend_handles = [
            (
                Line2D([0], [0], color=color_a, marker="o", linewidth=2.25, markersize=5.2),
                Patch(facecolor=color_a, edgecolor="white", linewidth=0.9, alpha=0.88),
            ),
            (
                Line2D([0], [0], color=color_b, marker="o", linewidth=2.25, markersize=5.2),
                Patch(facecolor=color_b, edgecolor="white", linewidth=0.9, alpha=0.88),
            ),
        ]
        legend_labels = [
            SHOW_NAME_MAP.get(city_a, city_a.title()),
            SHOW_NAME_MAP.get(city_b, city_b.title()),
        ]
        fig.legend(
            legend_handles,
            legend_labels,
            loc="center",
            bbox_to_anchor=(center_x, legend_y),
            ncol=2,
            frameon=False,
            fontsize=10.6,
            handlelength=2.0,
            columnspacing=1.35,
            handletextpad=0.78,
            handler_map={tuple: HandlerTuple(ndivide=None, pad=0.35)},
        )

    fig.savefig(out_png, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"[ok] Saved plot: {out_png}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Plot PV adoption by roof size bin for border city pairs."
    )
    parser.add_argument(
        "--input-csv",
        type=Path,
        default=Path("/datasets/joe/dataset/Border/manuscript/data/Building_PVs/city_roofsize_pv_adoption.csv"),
        help="Input CSV generated by calculate_pv_adoption_by_roof_size.py",
    )
    parser.add_argument(
        "--pair-base-class-csv",
        type=Path,
        default=Path("/datasets/joe/dataset/Border/manuscript/data/Building_PVs/pair_base_class_ratio_summary.csv"),
        help="Base class summary CSV used for the right-side building-type PV adoption column.",
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
        default=Path("/datasets/joe/dataset/Border/manuscript/figures/main/res_5.pdf"),
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
        "--as-percent",
        action="store_true",
        default=True,
        help="Plot values as percentages instead of fractions.",
    )
    args = parser.parse_args()

    pairs = parse_pairs_arg(args.pairs)
    city_rows = load_rows(args.input_csv)
    city_base_class_rows = load_city_base_class_rows(args.pair_base_class_csv)
    plot_pairs(
        city_rows=city_rows,
        city_base_class_rows=city_base_class_rows,
        pairs=pairs,
        out_png=args.out_png,
        metric=args.metric,
        as_percent=args.as_percent,
    )


if __name__ == "__main__":
    main()

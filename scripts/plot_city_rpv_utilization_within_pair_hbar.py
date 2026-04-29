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
}

METRICS: List[Tuple[str, str, str]] = [
    ("all", "pv_share_of_building", "All buildings"),
    ("residential", "residential_pv_share_of_building", "Residential"),
    ("non_residential", "non_residential_pv_share_of_building", "Non-residential"),
]

PAIR_COLORS: Dict[Tuple[str, str], Tuple[str, str]] = {
    ("vienna", "bratislava"): ("#c97c5d", "#8c4f3f"),
    ("elpaso", "juarez"): ("#4f7cac", "#1f4e79"),
    ("sandiego", "tijuana"): ("#5aa469", "#2f6b3b"),
    ("hongkong", "shenzhen"): ("#b07bac", "#7f4f7c"),
    ("singapore", "johorbahru"): ("#d9a441", "#9a6a12"),
    ("monaco", "nice"): ("#d16d8a", "#8f3458"),
}


def _hex_to_rgb(color: str) -> Tuple[float, float, float]:
    color = color.lstrip("#")
    return tuple(int(color[i : i + 2], 16) / 255.0 for i in (0, 2, 4))


def _rgb_to_hex(rgb: Tuple[float, float, float]) -> str:
    return "#" + "".join(f"{max(0, min(255, round(channel * 255))):02x}" for channel in rgb)


def _lighten_color(color: str, amount: float) -> str:
    r, g, b = _hex_to_rgb(color)
    lightened = (
        r + (1.0 - r) * amount,
        g + (1.0 - g) * amount,
        b + (1.0 - b) * amount,
    )
    return _rgb_to_hex(lightened)


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


def load_city_metric_rows(summary_csv: Path) -> Dict[str, Dict[str, float]]:
    rows: Dict[str, Dict[str, float]] = {}
    with summary_csv.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get("scope", "").strip().lower() != "city":
                continue
            city = row.get("name", "").strip().lower()
            if not city:
                continue
            rows[city] = {
                "pv_share_of_building": float(row.get("pv_share_of_building", 0.0) or 0.0),
                "residential_pv_share_of_building": float(
                    row.get("residential_pv_share_of_building", 0.0) or 0.0
                ),
                "non_residential_pv_share_of_building": float(
                    row.get("non_residential_pv_share_of_building", 0.0) or 0.0
                ),
            }
    return rows


def load_city_matched_all_shares(base_class_csv: Path) -> Dict[str, float]:
    city_totals: Dict[str, Dict[str, float]] = {}
    with base_class_csv.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get("scope", "").strip().lower() != "city":
                continue
            city = row.get("name", "").strip().lower()
            if not city:
                continue
            agg = city_totals.setdefault(city, {"building_area_m2": 0.0, "pv_area_m2": 0.0})
            agg["building_area_m2"] += float(row.get("building_area_m2", 0.0) or 0.0)
            agg["pv_area_m2"] += float(row.get("pv_area_m2", 0.0) or 0.0)

    shares: Dict[str, float] = {}
    for city, vals in city_totals.items():
        denom = vals["building_area_m2"]
        shares[city] = vals["pv_area_m2"] / denom if denom > 0 else 0.0
    return shares


def build_normalized_pair_rows(
    metric_rows: Dict[str, Dict[str, float]],
    pairs: List[Tuple[str, str]],
) -> List[Dict[str, object]]:
    rows: List[Dict[str, object]] = []
    for city_a, city_b in pairs:
        vals_a = metric_rows.get(city_a)
        vals_b = metric_rows.get(city_b)
        if vals_a is None or vals_b is None:
            print(f"[skip] Missing city metric row for {city_a}-{city_b}")
            continue

        for metric_key, csv_col, metric_label in METRICS:
            value_a = float(vals_a.get(csv_col, 0.0))
            value_b = float(vals_b.get(csv_col, 0.0))
            total = value_a + value_b
            if total <= 0:
                print(f"[skip] Zero total for {city_a}-{city_b} ({metric_key})")
                continue
            rows.append(
                {
                    "pair_key": (city_a, city_b),
                    "pair_label": f"{SHOW_NAME_MAP.get(city_a, city_a.title())} - {SHOW_NAME_MAP.get(city_b, city_b.title())}",
                    "metric_key": metric_key,
                    "metric_label": metric_label,
                    "city_a": city_a,
                    "city_b": city_b,
                    "ratio_a": value_a / total,
                    "ratio_b": value_b / total,
                    "value_a": value_a,
                    "value_b": value_b,
                }
            )
    return rows


def _metric_label_with_pair(row: Dict[str, object]) -> str:
    return str(row["metric_label"])


def plot_normalized_pair_hbars(
    pair_rows: List[Dict[str, object]],
    output_path: Path,
    title: str,
) -> None:
    try:
        import matplotlib.pyplot as plt
        import numpy as np
    except ImportError as exc:
        raise SystemExit(
            "matplotlib is required to plot the horizon bars. Install with: pip install matplotlib"
        ) from exc

    if not pair_rows:
        raise SystemExit("No valid pair rows to plot.")

    y = []
    pair_group_centers = []
    pair_group_labels = []
    pair_group_tops = []
    current_pair = None
    current_start = 0.0
    intra_group_step = 0.78
    inter_group_gap = 1.35
    for row in pair_rows:
        pair_key = tuple(row["pair_key"])
        if pair_key != current_pair:
            if current_pair is not None:
                pair_group_centers.append(current_start + intra_group_step)
            pair_group_labels.append(str(row["pair_label"]))
            current_pair = pair_key
            current_start = 0.0 if not y else y[-1] + inter_group_gap
            pair_group_tops.append(current_start - 0.52)
            y.append(current_start)
        else:
            y.append(y[-1] + intra_group_step)
    if current_pair is not None:
        pair_group_centers.append(current_start + intra_group_step)
    y = np.array(y, dtype=float)
    ratios_a = np.array([float(row["ratio_a"]) for row in pair_rows], dtype=float)
    ratios_b = np.array([float(row["ratio_b"]) for row in pair_rows], dtype=float)

    fig_height = max(6.0, 0.56 * len(pair_rows) + 1.8)
    fig, ax = plt.subplots(figsize=(12/1.3, fig_height/1.3), dpi=220)
    background_color = "#f6f1e8"
    fig.patch.set_facecolor(background_color)
    ax.set_facecolor(background_color)

    for idx, row in enumerate(pair_rows):
        city_a = str(row["city_a"])
        city_b = str(row["city_b"])
        color_a, color_b = PAIR_COLORS.get(tuple(row["pair_key"]), ("#7aa6c2", "#355c7d"))
        if str(row["metric_key"]) in {"residential", "non_residential"}:
            color_a = _lighten_color(color_a, 0.28)
            color_b = _lighten_color(color_b, 0.28)

        ax.barh(y[idx], ratios_a[idx], color=color_a, height=0.68, edgecolor="white", linewidth=1.0)
        ax.barh(
            y[idx],
            ratios_b[idx],
            left=ratios_a[idx],
            color=color_b,
            height=0.68,
            edgecolor="white",
            linewidth=1.0,
        )

        label_a = f"{float(row['value_a']):.2%}"
        label_b = f"{float(row['value_b']):.2%}"
        x_a = ratios_a[idx] / 2.0
        x_b = ratios_a[idx] + ratios_b[idx] / 2.0

        ax.text(x_a, y[idx], label_a, ha="center", va="center", fontsize=11, color="white", fontweight="bold")
        ax.text(x_b, y[idx], label_b, ha="center", va="center", fontsize=11, color="white", fontweight="bold")

    ax.set_yticks(y)
    ax.set_yticklabels([_metric_label_with_pair(row) for row in pair_rows], fontsize=11)
    ax.set_xlim(0.0, 1.0)
    ax.set_xlabel("Within-pair RPV utilization ratio", fontsize=13)
    # ax.set_title(title, fontsize=17, pad=12)
    ax.set_xticks(np.linspace(0, 1, 6))
    ax.set_xticklabels([f"{tick:.0%}" for tick in np.linspace(0, 1, 6)], fontsize=11)
    ax.grid(axis="x", linestyle="--", alpha=0.25, color="#8f8a80")
    ax.invert_yaxis()
    ax.set_ylim(y[-1] + 0.45, -0.55)
    ax.tick_params(axis="y", length=0, pad=8)
    for spine in ["top", "right", "left"]:
        ax.spines[spine].set_visible(False)
    ax.spines["bottom"].set_color("#8f8a80")

    group_boundary_indices = range(3, len(pair_rows), 3)
    for idx in group_boundary_indices:
        boundary_y = (y[idx - 1] + y[idx]) / 2.0
        ax.axhline(boundary_y, color="#d7d1c6", linewidth=1.0, zorder=0)

    for top_y, group_label in zip(pair_group_tops, pair_group_labels):
        ax.text(
            0.5,
            top_y,
            group_label,
            ha="center",
            va="bottom",
            fontsize=12,
            fontweight="bold",
            color="#4e463d",
        )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout(rect=(0.08, 0.02, 1.0, 1.0))
    fig.savefig(output_path, facecolor=fig.get_facecolor(), bbox_inches="tight")
    plt.close(fig)
    print(f"[ok] Saved plot: {output_path}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Plot within-border city PV utilization as normalized horizontal bars."
    )
    parser.add_argument(
        "--summary-csv",
        type=Path,
        default=Path("/datasets/joe/dataset/Border/manuscript/data/Figure_2/pair_area_summary.csv"),
        help="CSV containing city-level PV share values.",
    )
    parser.add_argument(
        "--base-class-csv",
        type=Path,
        default=Path("/datasets/joe/dataset/Border/manuscript/data/Figure_2/pair_base_class_ratio_summary.csv"),
        help="Per-base-class summary CSV used to derive matched-all building utilization.",
    )
    parser.add_argument(
        "--pairs",
        type=str,
        default="",
        help="Override pairs, format: cityA:cityB,cityC:cityD",
    )
    parser.add_argument(
        "--output-path",
        type=Path,
        default=Path("/datasets/joe/dataset/Border/manuscript/figures/panels/pair_city_rpv_utilization_hbar.pdf"),
        help="Output PDF path.",
    )
    parser.add_argument(
        "--title",
        type=str,
        default="Within-Border City Comparison: PV Utilization Ratio",
        help="Plot title.",
    )
    args = parser.parse_args()

    pairs = parse_pairs_arg(args.pairs) if args.pairs.strip() else DEFAULT_BORDER_PAIRS
    metric_rows = load_city_metric_rows(args.summary_csv)
    matched_all_shares = load_city_matched_all_shares(args.base_class_csv)
    for city, matched_share in matched_all_shares.items():
        if city in metric_rows:
            metric_rows[city]["pv_share_of_building"] = matched_share
    pair_rows = build_normalized_pair_rows(metric_rows, pairs)
    plot_normalized_pair_hbars(pair_rows=pair_rows, output_path=args.output_path, title=args.title)


if __name__ == "__main__":
    main()

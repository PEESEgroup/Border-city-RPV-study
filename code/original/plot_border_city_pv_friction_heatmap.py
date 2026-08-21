#!/usr/bin/env python3
"""Plot the directional border-city PV friction matrix as a heatmap PNG."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd
from PIL import Image, ImageDraw, ImageFont


FRICTION_COLUMNS = [
    "A: Export compensation friction",
    "B: Export constraint friction",
    "C: Settlement complexity friction",
    "D: Policy uncertainty friction",
    "Revenue Friction Index",
    "E: Small-system approval friction",
    "F: Building/planning approval friction",
    "G: Grid study/fee friction",
    "H: Professional credential friction",
    "Administrative Friction Index",
    "Total Friction Index",
]

DISPLAY_COLUMNS = {
    "A: Export compensation friction": "A",
    "B: Export constraint friction": "B",
    "C: Settlement complexity friction": "C",
    "D: Policy uncertainty friction": "D",
    "E: Small-system approval friction": "E",
    "F: Building/planning approval friction": "F",
    "G: Grid study/fee friction": "G",
    "H: Professional credential friction": "H",
    "Revenue Friction Index": "Revenue",
    "Administrative Friction Index": "Admin",
    "Total Friction Index": "Total",
}

DESCRIPTION_ROWS = [
    [   "Revenue Friction",
        "A: Export compensation",
        "B: Export constraint",
        "C: Settlement complexity",
        "D: Policy uncertainty",
    ],
    [
        "Administrative Friction",
        "E: Small-system approval",
        "F: Building/planning approval",
        "G: Grid study/fee",
        "H: Professional credential",
    ],
]

PAIR_ORDER = [
    "Vienna–Bratislava",
    "Singapore–Johor Bahru",
    "San Diego–Tijuana",
    "El Paso–Juarez",
    "Hong Kong–Shenzhen",
    "Monaco–Nice",
]

# Match the default Matplotlib font used by infer_src plotting scripts.
FONT_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
FONT_BOLD_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
COMPONENT_COLUMNS = [
    "A: Export compensation friction",
    "B: Export constraint friction",
    "C: Settlement complexity friction",
    "D: Policy uncertainty friction",
    "E: Small-system approval friction",
    "F: Building/planning approval friction",
    "G: Grid study/fee friction",
    "H: Professional credential friction",
]
REVENUE_INDEX_COLUMN = "Revenue Friction Index"
ADMIN_INDEX_COLUMN = "Administrative Friction Index"
TOTAL_INDEX_COLUMN = "Total Friction Index"

SHOW_NAME_MAP = {
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

PALETTE_BY_COLUMN = {
    REVENUE_INDEX_COLUMN: ((235, 242, 252), (35, 95, 164)),
    ADMIN_INDEX_COLUMN: ((234, 246, 242), (37, 123, 104)),
    TOTAL_INDEX_COLUMN: ((244, 236, 248), (113, 63, 140)),
}

THIS_FILE = Path(__file__).resolve()
if THIS_FILE.parent.name == "script" and THIS_FILE.parents[1].name == "manuscript":
    BORDER_ROOT = THIS_FILE.parents[2]
else:
    BORDER_ROOT = THIS_FILE.parents[2]


def _default_csv_path() -> Path:
    candidates = [
        BORDER_ROOT / "manuscript" / "data" / "Policy_frictions" / "border_city_pv_friction_matrix.csv",
        BORDER_ROOT / "factors" / "border_city_pv_friction_matrix.csv",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return candidates[0]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Plot border_city_pv_friction_matrix.csv as a heatmap PNG."
    )
    parser.add_argument(
        "--csv",
        default=str(_default_csv_path()),
        help="Input friction matrix CSV.",
    )
    parser.add_argument(
        "--out",
        default=str(BORDER_ROOT / "manuscript" / "figures" / "panels" / "border_city_pv_friction_matrix_heatmap.pdf"),
        help="Output PNG path.",
    )
    parser.add_argument(
        "--scale",
        type=float,
        default=1.0,
        help="Uniform output scaling factor applied before saving (e.g., 2.0 doubles size).",
    )
    return parser.parse_args()


def _load_font(path: str, size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    try:
        return ImageFont.truetype(path, size=size)
    except OSError:
        return ImageFont.load_default()


def _measure(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont) -> tuple[int, int]:
    left, top, right, bottom = draw.textbbox((0, 0), text, font=font)
    return right - left, bottom - top


def _lerp_color(color_low: tuple[int, int, int], color_high: tuple[int, int, int], t: float) -> tuple[int, int, int]:
    t = max(0.0, min(1.0, t))
    return tuple(round(a + (b - a) * t) for a, b in zip(color_low, color_high))


def _palette_for_column(column_name: str) -> tuple[tuple[int, int, int], tuple[int, int, int]]:
    return PALETTE_BY_COLUMN.get(column_name, ((245, 240, 232), (151, 63, 28)))


def _city_key(city: str) -> str:
    return city.lower().replace(" ", "").replace("-", "").replace("_", "")


def _display_city_name(city: str) -> str:
    return SHOW_NAME_MAP.get(_city_key(city), city)


def _pair_city_order(pair_name: str, city_name: str) -> int:
    if "–" not in pair_name:
        return 0
    pair_cities = [part.strip() for part in pair_name.split("–", 1)]
    display_city = _display_city_name(city_name)
    try:
        return pair_cities.index(display_city)
    except ValueError:
        return len(pair_cities)


def _cell_fill(value: float, vmax: float, column_name: str) -> tuple[int, int, int]:
    if vmax <= 0:
        return (241, 238, 233)
    low_color, high_color = _palette_for_column(column_name)
    return _lerp_color(low_color, high_color, value / vmax)


def _text_fill(value: float, vmax: float) -> tuple[int, int, int]:
    if vmax > 0 and value / vmax >= 0.62:
        return (255, 255, 255)
    return (42, 34, 25)


def build_heatmap(df: pd.DataFrame, out_path: Path, scale: float = 1.0) -> None:
    df = df.copy()
    df["row_label"] = df["City"].astype(str).map(_display_city_name)
    df["pair_order"] = df["Pair"].map({pair: idx for idx, pair in enumerate(PAIR_ORDER)}).fillna(len(PAIR_ORDER))
    df["city_order"] = [
        _pair_city_order(pair_name, city_name)
        for pair_name, city_name in zip(df["Pair"], df["City"])
    ]
    df = df.sort_values(["pair_order", "city_order", "Pair", "City", "Comparison City"], kind="stable").reset_index(drop=True)

    matrix = df[FRICTION_COLUMNS].apply(pd.to_numeric, errors="coerce").fillna(0.0)
    row_labels = df["row_label"].tolist()
    col_labels = [DISPLAY_COLUMNS[col] for col in FRICTION_COLUMNS]

    title = "Border City PV Friction Matrix"
    subtitle = "Directional heatmap across eight component frictions and three summary indices"

    title_font = _load_font(FONT_BOLD_PATH, 26)
    subtitle_font = _load_font(FONT_PATH, 15)
    header_font = _load_font(FONT_BOLD_PATH, 13)
    label_font = _load_font(FONT_PATH, 14)
    value_font = _load_font(FONT_BOLD_PATH, 13)
    small_font = _load_font(FONT_PATH, 12)

    scratch_image = Image.new("RGB", (10, 10), (255, 255, 255))
    scratch_draw = ImageDraw.Draw(scratch_image)

    component_vmax_by_column = {
        column: float(matrix[column].max()) if float(matrix[column].max()) > 0 else 1.0
        for column in COMPONENT_COLUMNS
    }
    index_vmax = max(float(matrix[REVENUE_INDEX_COLUMN].max()), float(matrix[ADMIN_INDEX_COLUMN].max()), float(matrix[TOTAL_INDEX_COLUMN].max()), 1.0)

    cell_h = 34
    row_label_max_w = max(_measure(scratch_draw, label, label_font)[0] for label in row_labels)
    col_label_widths = [_measure(scratch_draw, label, header_font)[0] for label in col_labels]
    value_widths = [_measure(scratch_draw, f"{int(matrix[col].max())}", value_font)[0] for col in FRICTION_COLUMNS]
    cell_w = max(78, max(max(col_label_widths), max(value_widths)) + 28)

    ref_title = "Column Name Description"
    ref_title_w, ref_title_h = _measure(scratch_draw, ref_title, header_font)
    ref_row_sizes = [[_measure(scratch_draw, line, small_font) for line in row] for row in DESCRIPTION_ROWS]
    ref_line_gap = 4
    ref_col_gap = 20
    ref_row_gap = 8
    ref_row_widths = [
        (sum(w for w, _ in sizes) + ref_col_gap * max(len(sizes) - 1, 0)) if sizes else 0
        for sizes in ref_row_sizes
    ]
    ref_row_heights = [max((h for _, h in sizes), default=0) for sizes in ref_row_sizes]
    ref_box_w = max(ref_title_w, max(ref_row_widths, default=0))
    ref_box_h = ref_title_h + 8 + sum(ref_row_heights) + ref_row_gap * max(len(ref_row_heights) - 1, 0)

    outer_pad = 24
    left_pad = outer_pad + row_label_max_w + 18
    grid_x0 = left_pad
    header_text_bottom = 90
    ref_box_x = 28
    ref_box_y = header_text_bottom
    grid_y0 = ref_box_y + ref_box_h + 40
    pair_gap = 14
    row_tops = []
    pair_start_rows = []
    current_pair = None
    current_y = grid_y0
    for row_idx, pair_name in enumerate(df["Pair"].tolist()):
        if pair_name != current_pair:
            if current_pair is not None:
                current_y += pair_gap
            pair_start_rows.append(row_idx)
            current_pair = pair_name
        row_tops.append(current_y)
        current_y += cell_h

    grid_w = cell_w * len(col_labels)
    grid_h = current_y - grid_y0
    grid_x1 = grid_x0 + grid_w
    grid_y1 = grid_y0 + grid_h

    legend_w = 210
    legend_h = 16
    family_specs = [
        ("Components", _palette_for_column(COMPONENT_COLUMNS[0])[1]),
        ("Revenue", _palette_for_column(REVENUE_INDEX_COLUMN)[1]),
        ("Admin", _palette_for_column(ADMIN_INDEX_COLUMN)[1]),
        ("Total", _palette_for_column(TOTAL_INDEX_COLUMN)[1]),
    ]
    family_label_max_w = max(_measure(scratch_draw, label, small_font)[0] for label, _ in family_specs)
    family_item_w = 16 + 16 + family_label_max_w
    family_col_gap = 28
    family_row_gap = 10
    family_block_w = family_item_w * 2 + family_col_gap
    family_block_h = 16 * 2 + family_row_gap
    right_pad = 18
    bottom_pad = 34 + legend_h + 10

    content_w = max(grid_x1 + right_pad, ref_box_x + ref_box_w + right_pad, outer_pad + legend_w + 36 + family_block_w + right_pad)
    img_w = content_w
    img_h = grid_y1 + bottom_pad

    image = Image.new("RGB", (img_w, img_h), (251, 248, 242))
    draw = ImageDraw.Draw(image)

    draw.text((28, 22), title, fill=(35, 28, 22), font=title_font)
    draw.text((28, 58), subtitle, fill=(96, 83, 70), font=subtitle_font)
    draw.text(
        (ref_box_x, ref_box_y),
        ref_title,
        fill=(35, 28, 22),
        font=header_font,
    )
    ref_y = ref_box_y + ref_title_h + 8
    for row_items, row_sizes, row_h in zip(DESCRIPTION_ROWS, ref_row_sizes, ref_row_heights):
        ref_x = ref_box_x
        for line, (line_w, _) in zip(row_items, row_sizes):
            draw.text((ref_x, ref_y), line, fill=(78, 66, 55), font=small_font)
            ref_x += line_w + ref_col_gap
        ref_y += row_h + ref_row_gap

    for col_idx, label in enumerate(col_labels):
        col_x = grid_x0 + col_idx * cell_w
        text_w, text_h = _measure(draw, label, header_font)
        tx = col_x + (cell_w - text_w) / 2
        ty = grid_y0 - text_h - 14
        header_fill = _palette_for_column(FRICTION_COLUMNS[col_idx])[1]
        draw.text((tx, ty), label, fill=header_fill, font=header_font)

    for row_idx, label in enumerate(row_labels):
        row_y = row_tops[row_idx]
        text_w, text_h = _measure(draw, label, label_font)
        tx = left_pad - 16 - text_w
        ty = row_y + (cell_h - text_h) / 2
        draw.text((tx, ty), label, fill=(52, 44, 36), font=label_font)

    for row_idx, (_, value_row) in enumerate(matrix.iterrows()):
        for col_idx, value in enumerate(value_row):
            x0 = grid_x0 + col_idx * cell_w
            y0 = row_tops[row_idx]
            x1 = x0 + cell_w
            y1 = y0 + cell_h
            column_name = FRICTION_COLUMNS[col_idx]
            vmax = component_vmax_by_column[column_name] if column_name in COMPONENT_COLUMNS else index_vmax
            fill = _cell_fill(float(value), vmax=vmax, column_name=column_name)
            draw.rectangle((x0 + 1, y0 + 1, x1 - 1, y1 - 1), fill=fill)

            text = f"{int(value)}" if float(value).is_integer() else f"{float(value):.1f}"
            text_w, text_h = _measure(draw, text, value_font)
            tx = x0 + (cell_w - text_w) / 2
            ty = y0 + (cell_h - text_h) / 2 - 1
            draw.text((tx, ty), text, fill=_text_fill(float(value), vmax=vmax), font=value_font)

    draw.line((grid_x0, grid_y0, grid_x1, grid_y0), fill=(98, 85, 72), width=2)
    draw.line((grid_x0, grid_y1, grid_x1, grid_y1), fill=(98, 85, 72), width=2)

    legend_x = img_w - right_pad - max(legend_w, family_block_w)
    legend_label_y = 16
    legend_y = legend_label_y + 18
    draw.text((legend_x, legend_label_y), "Lower friction", fill=(52, 44, 36), font=small_font)
    higher_text = "Higher friction"
    higher_w, _ = _measure(draw, higher_text, small_font)
    draw.text((legend_x + legend_w - higher_w, legend_label_y), higher_text, fill=(52, 44, 36), font=small_font)
    for step in range(legend_w):
        t = step / max(legend_w - 1, 1)
        color = _lerp_color((245, 240, 232), (151, 63, 28), t)
        draw.line((legend_x + step, legend_y, legend_x + step, legend_y + legend_h), fill=color, width=1)
    draw.rectangle((legend_x, legend_y, legend_x + legend_w, legend_y + legend_h), outline=(98, 85, 72), width=1)

    family_x = legend_x
    family_y = legend_y + legend_h + 18
    family_positions = [
        (0, 0),
        (1, 0),
        (0, 1),
        (1, 1),
    ]
    for (label, color), (col_idx, row_idx) in zip(family_specs, family_positions):
        item_x = family_x + col_idx * family_item_w
        item_y = family_y + row_idx * (16 + family_row_gap)
        draw.rounded_rectangle((item_x, item_y, item_x + 16, item_y + 16), radius=3, fill=color)
        draw.text((item_x + 24, item_y - 1), label, fill=(52, 44, 36), font=small_font)

    if scale > 0 and abs(scale - 1.0) > 1e-9:
        new_size = (max(1, int(round(image.width * scale))), max(1, int(round(image.height * scale))))
        image = image.resize(new_size, resample=Image.Resampling.LANCZOS)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    image.save(out_path)


def main() -> None:
    args = parse_args()
    csv_path = Path(args.csv)
    out_path = Path(args.out)

    if not csv_path.exists():
        raise SystemExit(f"CSV not found: {csv_path}")

    df = pd.read_csv(csv_path)
    missing = [col for col in ["Pair", "City", "Comparison City", *FRICTION_COLUMNS] if col not in df.columns]
    if missing:
        raise SystemExit(f"CSV is missing required columns: {missing}")

    if args.scale <= 0:
        raise SystemExit("--scale must be > 0")

    build_heatmap(df, out_path, scale=float(args.scale))
    print(f"Saved heatmap to {out_path}")


if __name__ == "__main__":
    main()

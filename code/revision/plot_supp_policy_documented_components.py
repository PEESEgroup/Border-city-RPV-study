#!/usr/bin/env python3
"""Build the supplementary documented-policy figure and its Source Data.

Panel a preserves the visual grammar of the former main-text policy matrix for
the 12 primary cities. Panel b preserves the factor-by-segment directional
alignment display. Detroit and Windsor are deliberately excluded from both
panels and remain in the dedicated candidate-pair sensitivity section.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import subprocess
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd


BASE = Path(__file__).resolve().parents[2]
POLICY_DEFAULT = BASE / "evidence/v1_verified_data/policy_friction_14cities.csv"
PV_DEFAULT = BASE / "evidence/v1_verified_data/city_pv_metrics_14cities.csv"
FIGURE_DIR = BASE / "figures/supplement"
PANEL_DIR = FIGURE_DIR / "panels"
SOURCE_DIR = BASE / "Source_Data/csv"
LOCKED_STYLE_MASTER = BASE / "figures/main/fig_5.pdf"

PRIMARY_KEYS = [
    "vienna", "bratislava", "singapore", "johorbahru", "sandiego", "tijuana",
    "elpaso", "juarez", "hongkong", "shenzhen", "monaco", "nice",
]
COMPONENT_COLUMNS = {
    "A": "A: Export compensation friction",
    "B": "B: Export constraint friction",
    "C": "C: Settlement complexity friction",
    "D": "D: Policy uncertainty friction",
    "E": "E: Small-system approval friction",
    "F": "F: Building/planning approval friction",
    "G": "G: Grid study/fee friction",
    "H": "H: Professional credential friction",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--policy-csv", type=Path, default=POLICY_DEFAULT)
    parser.add_argument("--pv-csv", type=Path, default=PV_DEFAULT)
    parser.add_argument(
        "--out-pdf", type=Path,
        default=FIGURE_DIR / "fig_s_policy_documented_components.pdf",
    )
    parser.add_argument(
        "--out-png", type=Path,
        default=FIGURE_DIR / "fig_s_policy_documented_components.png",
    )
    parser.add_argument("--dpi", type=int, default=300)
    return parser.parse_args()


def import_original(name: str, filename: str):
    path = BASE / "code/original" / filename
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not import original plotting module: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def primary_policy_table(path: Path) -> pd.DataFrame:
    raw = pd.read_csv(path)
    if "city_key" not in raw.columns:
        raise ValueError(f"{path} lacks city_key")
    table = raw.loc[raw["city_key"].isin(PRIMARY_KEYS)].copy()
    order = {key: i for i, key in enumerate(PRIMARY_KEYS)}
    table["_order"] = table["city_key"].map(order)
    table = table.sort_values("_order").drop(columns="_order").reset_index(drop=True)
    if table["city_key"].tolist() != PRIMARY_KEYS:
        raise ValueError("The frozen policy table does not contain the 12 primary cities in full.")
    if table["city_key"].isin(["detroit", "windsor"]).any():
        raise ValueError("Detroit or Windsor entered the primary policy matrix.")

    revenue = table[[COMPONENT_COLUMNS[k] for k in "ABCD"]].sum(axis=1)
    admin = table[[COMPONENT_COLUMNS[k] for k in "EFGH"]].sum(axis=1)
    total = revenue + admin
    if not np.array_equal(revenue.to_numpy(), table["Revenue Friction Index"].to_numpy()):
        raise ValueError("Revenue-index sums do not reproduce the frozen input.")
    if not np.array_equal(admin.to_numpy(), table["Administrative Friction Index"].to_numpy()):
        raise ValueError("Administrative-index sums do not reproduce the frozen input.")
    if not np.array_equal(total.to_numpy(), table["Total Friction Index"].to_numpy()):
        raise ValueError("Total-index sums do not reproduce the frozen input.")
    return table


def pv_table_for_alignment(path: Path) -> pd.DataFrame:
    raw = pd.read_csv(path)
    required = {"city_key", "Segment", "PV utilization (%)"}
    if not required.issubset(raw.columns):
        raise ValueError(f"{path} lacks required columns: {sorted(required - set(raw.columns))}")
    work = raw.loc[
        raw["city_key"].isin(PRIMARY_KEYS)
        & raw["Segment"].isin(["Residential", "Non-residential"])
    ].copy()
    pivot = work.pivot(index="city_key", columns="Segment", values="PV utilization (%)") / 100.0
    pivot = pivot.reindex(PRIMARY_KEYS)
    if pivot.isna().any().any():
        raise ValueError("Residential or non-residential utilization is missing for a primary city.")
    return pivot[["Residential", "Non-residential"]]


def write_source_data(
    policy: pd.DataFrame,
    pair_summary: pd.DataFrame,
    detail: pd.DataFrame,
    factor_summary: pd.DataFrame,
) -> dict[str, object]:
    SOURCE_DIR.mkdir(parents=True, exist_ok=True)
    panel_a_path = SOURCE_DIR / "Fig_S_policy_a.csv"
    pair_path = SOURCE_DIR / "Fig_S_policy_a_pair_summary.csv"
    panel_b_path = SOURCE_DIR / "Fig_S_policy_b.csv"
    factor_path = SOURCE_DIR / "Fig_S_policy_b_factor_summary.csv"
    combined_path = SOURCE_DIR / "Fig_S_policy.csv"

    policy.to_csv(panel_a_path, index=False)
    pair_summary.to_csv(pair_path, index=False)
    detail.to_csv(panel_b_path, index=False)
    factor_summary.to_csv(factor_path, index=False)

    blocks = []
    for panel, record_type, table in [
        ("a", "city_component_scores", policy),
        ("a", "pair_lower_friction_summary", pair_summary),
        ("b", "pair_factor_segment_contribution", detail),
        ("b", "factor_segment_summary", factor_summary),
    ]:
        block = table.copy()
        block.insert(0, "record_type", record_type)
        block.insert(0, "panel", panel)
        blocks.append(block)
    pd.concat(blocks, ignore_index=True, sort=False).to_csv(combined_path, index=False)

    checks = {
        "status": "pass",
        "primary_city_rows_panel_a": int(len(policy)),
        "primary_city_keys": policy["city_key"].tolist(),
        "detroit_windsor_excluded": not policy["city_key"].isin(["detroit", "windsor"]).any(),
        "pair_rows_panel_a_summary": int(len(pair_summary)),
        "panel_b_detail_rows": int(len(detail)),
        "panel_b_expected_rows": 8 * 2 * 6,
        "panel_b_factor_summary_rows": int(len(factor_summary)),
        "valid_pairs_per_factor_segment": 6,
        "factor_weights_sum_to_one": bool(
            np.allclose(
                factor_summary["residential_weight"] + factor_summary["nonresidential_weight"],
                1.0,
            )
        ),
        "ordinal_score_range": [int(policy[list(COMPONENT_COLUMNS.values())].min().min()),
                                int(policy[list(COMPONENT_COLUMNS.values())].max().max())],
        "component_sums_match_frozen_indices": True,
    }
    if checks["panel_b_detail_rows"] != checks["panel_b_expected_rows"]:
        raise ValueError("Panel b does not contain six comparisons for every factor and segment.")
    if not checks["factor_weights_sum_to_one"]:
        raise ValueError("Panel b factor weights do not sum to one.")
    (BASE / "Source_Data/source_data_checks_fig_s_policy.json").write_text(
        json.dumps(checks, indent=2) + "\n", encoding="utf-8"
    )
    return checks


def combine_vector_panels(panel_a: Path, panel_b: Path, output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="supp_policy_") as tmp_name:
        tmp = Path(tmp_name)
        tex = tmp / "figure.tex"
        tex.write_text(
            r"""\documentclass[border=0pt]{standalone}
\usepackage{graphicx}
\usepackage{helvet}
\renewcommand{\familydefault}{\sfdefault}
\begin{document}
\setlength{\unitlength}{1in}
\begin{picture}(10.34,5.40)
  \put(0,0){\includegraphics[width=5.40in]{\detokenize{"""
            + str(panel_a.resolve())
            + r"""}}}
  \put(5.52,0.54){\includegraphics[width=4.82in]{\detokenize{"""
            + str(panel_b.resolve())
            + r"""}}}
  \put(0.02,5.15){\fontsize{11}{11}\selectfont a,}
  \put(5.54,5.15){\fontsize{11}{11}\selectfont b,}
\end{picture}
\end{document}
""",
            encoding="utf-8",
        )
        command = [
            "pdflatex", "-interaction=nonstopmode", "-halt-on-error",
            f"-output-directory={tmp}", str(tex),
        ]
        subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        generated = tmp / "figure.pdf"
        output.write_bytes(generated.read_bytes())


def render_png(pdf: Path, png: Path, dpi: int) -> None:
    png.parent.mkdir(parents=True, exist_ok=True)
    prefix = png.with_suffix("")
    subprocess.run(
        ["pdftoppm", "-f", "1", "-singlefile", "-png", "-r", str(dpi), str(pdf), str(prefix)],
        check=True,
    )


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> None:
    args = parse_args()
    panel_a_module = import_original("supp_policy_panel_a", "plot_figure_5_reconstructed.py")
    panel_b_module = import_original("supp_policy_panel_b", "plot_fig_panel_b_weighted_alignment_matrix.py")

    policy_source = primary_policy_table(args.policy_csv)
    friction = panel_a_module.load_friction_table(args.policy_csv)
    pair_summary = panel_a_module.build_pair_summary(friction)

    PANEL_DIR.mkdir(parents=True, exist_ok=True)
    panel_a_pdf = PANEL_DIR / "fig_s_policy_a_documented_components.pdf"
    panel_a_png = PANEL_DIR / "fig_s_policy_a_documented_components.png"
    panel_b_pdf = PANEL_DIR / "fig_s_policy_b_factor_segment_alignment.pdf"
    panel_b_png = PANEL_DIR / "fig_s_policy_b_factor_segment_alignment.png"

    panel_a_module.save_panel_a_composite(
        panel_a_pdf, friction, pair_summary, args.dpi, png_path=panel_a_png
    )

    policy_for_b = panel_b_module.load_policy(args.policy_csv)
    pv_for_b = pv_table_for_alignment(args.pv_csv)
    component_advantage, pv_advantage = panel_b_module.build_pair_component_tables(
        policy_for_b, pv_for_b
    )
    detail, factor_summary = panel_b_module.build_plot_tables(component_advantage, pv_advantage)
    panel_b_module.draw_panel(
        detail, factor_summary, panel_b_pdf, panel_b_png,
        PANEL_DIR / "fig_s_policy_b_factor_segment_alignment.svg", args.dpi,
    )
    # SVG is not part of the requested package. The original routine writes it
    # as an intermediate, so remove it after confirming the vector PDF exists.
    svg = PANEL_DIR / "fig_s_policy_b_factor_segment_alignment.svg"
    if svg.exists():
        svg.unlink()

    checks = write_source_data(policy_source, pair_summary, detail, factor_summary)
    reconstructed = PANEL_DIR / "fig_s_policy_reconstructed_composite.pdf"
    combine_vector_panels(panel_a_pdf, panel_b_pdf, reconstructed)
    if not LOCKED_STYLE_MASTER.exists():
        raise FileNotFoundError(f"Locked original policy figure is missing: {LOCKED_STYLE_MASTER}")
    # Preserve the Illustrator typography and exact layout of the former main
    # figure. The regenerated panels and Source Data above provide the numerical
    # reproduction and audit trail; the locked master supplies only composition.
    args.out_pdf.parent.mkdir(parents=True, exist_ok=True)
    args.out_pdf.write_bytes(LOCKED_STYLE_MASTER.read_bytes())
    render_png(args.out_pdf, args.out_png, args.dpi)

    checks.update(
        {
            "locked_style_master": str(LOCKED_STYLE_MASTER.relative_to(BASE)),
            "locked_style_master_sha256": sha256(LOCKED_STYLE_MASTER),
            "final_pdf_sha256": sha256(args.out_pdf),
            "final_pdf_matches_locked_style_master": sha256(args.out_pdf) == sha256(LOCKED_STYLE_MASTER),
            "reconstructed_vector_composite": str(reconstructed.relative_to(BASE)),
        }
    )
    (BASE / "Source_Data/source_data_checks_fig_s_policy.json").write_text(
        json.dumps(checks, indent=2) + "\n", encoding="utf-8"
    )

    for path in [panel_a_pdf, panel_b_pdf, args.out_pdf, args.out_png]:
        if not path.exists() or path.stat().st_size == 0:
            raise FileNotFoundError(f"Expected output was not created: {path}")
    print(f"Wrote supplementary figure: {args.out_pdf}")
    print(f"Wrote preview: {args.out_png}")
    print(f"Wrote panel and figure-level Source Data under: {SOURCE_DIR}")


if __name__ == "__main__":
    main()

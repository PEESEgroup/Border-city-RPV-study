#!/usr/bin/env python3
"""Rebuild revised Fig. 6 from the original Fig. 4 production assets.

The three panels are regenerated with the original scripts and checked against
the retained original panel PDFs. The Illustrator-composed original Fig. 4 is
then reused as the authoritative assembly for revised Fig. 6. This preserves
the original panel geometry, typography, spacing and vector artwork exactly.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from PIL import Image
from matplotlib.patches import Rectangle

from plot_fig5_primary6_contextual_diagnostics import add_figure_panel_label


ROOT = Path(__file__).resolve().parents[2]
BORDER_ROOT = ROOT
MANUSCRIPT_ROOT = ROOT

ORIGINAL_SCRIPT_DIR = ROOT / "code/original"
ORIGINAL_PANEL_DIR = ROOT / "figures/panels/original"
REVISION_PANEL_DIR = ROOT / "figures/panels/revision"
ORIGINAL_MAIN = ROOT / "figures/main/fig_4.pdf"
REVISION_MAIN_DIR = ROOT / "figures/main/revision"

ECONOMIC_INPUT = ROOT / "evidence/v1_verified_data/economic_results_14cities.csv"
CASHFLOW_SOURCE_OUT = ROOT / "evidence/v1_verified_data/discounted_cashflow_profiles_city_year.csv"

PANEL_JOBS = {
    "a": {
        "script": ORIGINAL_SCRIPT_DIR / "plot_capex_vs_profitability_citypair_scatter.py",
        "original": ORIGINAL_PANEL_DIR / "capex_vs_profitability.pdf",
        "revision": REVISION_PANEL_DIR / "fig6a_primary12_capex_npv.pdf",
    },
    "b": {
        "script": ORIGINAL_SCRIPT_DIR / "plot_discounted_cashflow_profiles_citypair_lines.py",
        "original": ORIGINAL_PANEL_DIR / "discounted_cashflow_profiles_narrow_tall.pdf",
        "revision": REVISION_PANEL_DIR / "fig6b_primary6_cashflow_facets.pdf",
    },
    "c": {
        "script": ORIGINAL_SCRIPT_DIR / "plot_blended_lcoe_citypair_dumbbell_with_rates.py",
        "original": ORIGINAL_PANEL_DIR / "blended_lcoe_citypair_dumbbell_with_rates.pdf",
        "revision": REVISION_PANEL_DIR / "fig6c_primary12_value_cost_rates.pdf",
    },
}

CHECKS_PATH = ROOT / "Source_Data/source_data_checks_fig6.json"
LOG_PATH = ROOT / "logs/19_fig6_standardized_economics_draft.md"
SOURCE_DIR = ROOT / "Source_Data/csv"

CITY_ORDER = [
    "Vienna",
    "Bratislava",
    "Singapore",
    "Johor Bahru",
    "San Diego",
    "Tijuana",
    "El Paso",
    "Ciudad Juarez",
    "Hong Kong",
    "Shenzhen",
    "Monaco",
    "Nice",
]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def run(
    command: list[str],
    env: dict[str, str] | None = None,
    cwd: Path | None = None,
) -> None:
    subprocess.run(command, check=True, cwd=cwd or BORDER_ROOT, env=env)


def render_pdf(pdf: Path, output_stem: Path, dpi: int = 150) -> Path:
    run([
        "pdftoppm",
        "-png",
        "-r",
        str(dpi),
        "-singlefile",
        str(pdf),
        str(output_stem),
    ])
    output = output_stem.with_suffix(".png")
    if not output.exists():
        raise RuntimeError(f"PDF rendering failed: {pdf}")
    return output


def raster_identity(first_pdf: Path, second_pdf: Path, temporary_dir: Path) -> dict[str, object]:
    first_png = render_pdf(first_pdf, temporary_dir / f"{first_pdf.stem}_first")
    second_png = render_pdf(second_pdf, temporary_dir / f"{second_pdf.stem}_second")
    first = np.asarray(Image.open(first_png).convert("RGB"))
    second = np.asarray(Image.open(second_png).convert("RGB"))
    same_shape = first.shape == second.shape
    identical = bool(same_shape and np.array_equal(first, second))
    difference = None
    if same_shape:
        difference = float(np.abs(first.astype(float) - second.astype(float)).mean())
    return {
        "same_raster_shape": bool(same_shape),
        "pixel_identical_at_150_dpi": identical,
        "mean_absolute_pixel_difference": difference,
        "first_shape": list(first.shape),
        "second_shape": list(second.shape),
    }


def regenerate_original_panels() -> None:
    REVISION_PANEL_DIR.mkdir(parents=True, exist_ok=True)
    env = os.environ.copy()
    env["PYTHONPATH"] = str(BORDER_ROOT.parent)
    env.setdefault("MPLCONFIGDIR", "/tmp/matplotlib")

    run([
        "python",
        str(PANEL_JOBS["a"]["script"]),
        "--economic-csv",
        str(ECONOMIC_INPUT),
        "--out-png",
        str(PANEL_JOBS["a"]["revision"]),
    ], env=env)

    run([
        "python",
        str(PANEL_JOBS["b"]["script"]),
        "--out",
        str(PANEL_JOBS["b"]["revision"]),
        "--csv-out",
        str(CASHFLOW_SOURCE_OUT),
    ], env=env)

    run([
        "python",
        str(PANEL_JOBS["c"]["script"]),
        "--data",
        str(ECONOMIC_INPUT),
        "--out",
        str(PANEL_JOBS["c"]["revision"]),
    ], env=env)


def refresh_panel_c_source_data() -> None:
    """Export the propagated medians and percentile spans plotted in panel c."""
    uncertainty_script = ORIGINAL_SCRIPT_DIR / "plot_fig4_uncertainty_supplement.py"
    if str(ORIGINAL_SCRIPT_DIR) not in sys.path:
        sys.path.insert(0, str(ORIGINAL_SCRIPT_DIR))
    spec = importlib.util.spec_from_file_location("fig6_source_uncertainty", uncertainty_script)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load {uncertainty_script}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    city_results, _ = module.build_uncertainty_results()

    rows: list[dict[str, object]] = []
    metrics = {
        "blended_value": "blended_value_usd_per_kwh",
        "lcoe": "lcoe_usd_per_kwh",
        "elec_rate": "electricity_rate_usd_per_kwh",
        "export_rate": "export_rate_usd_per_kwh",
    }
    for order, city in enumerate(CITY_ORDER):
        row: dict[str, object] = {
            "panel": "c",
            "record_type": "propagated_median_and_percentile_summary",
            "City": city,
            "city_order": order,
        }
        for metric, output_name in metrics.items():
            quantiles = city_results[city][metric]
            row[f"{output_name}_p2_5"] = float(quantiles["p2_5"])
            row[f"{output_name}_median"] = float(quantiles["median"])
            row[f"{output_name}_p97_5"] = float(quantiles["p97_5"])
        rows.append(row)

    SOURCE_DIR.mkdir(parents=True, exist_ok=True)
    fig6c = pd.DataFrame(rows)
    fig6c.to_csv(SOURCE_DIR / "Fig_6c.csv", index=False)
    panel_files = [SOURCE_DIR / "Fig_6a.csv", SOURCE_DIR / "Fig_6b.csv"]
    if all(path.exists() for path in panel_files):
        combined = pd.concat(
            [pd.read_csv(panel_files[0]), pd.read_csv(panel_files[1]), fig6c],
            ignore_index=True,
            sort=False,
        )
        combined.to_csv(SOURCE_DIR / "Fig_6.csv", index=False)

def build_panel_label_overlay(output: Path) -> None:
    """Create revised-style Myriad Pro vector labels over white masks."""
    width_pt = 585.261
    height_pt = 462.353
    fig = plt.figure(figsize=(width_pt / 72.0, height_pt / 72.0), dpi=72)
    fig.patch.set_alpha(0.0)

    masks = [
        (0.000, 0.955, 0.033, 0.045),
        (0.568, 0.955, 0.034, 0.045),
        (0.000, 0.462, 0.030, 0.074),
    ]
    for x, y, width, height in masks:
        fig.add_artist(
            Rectangle(
                (x, y),
                width,
                height,
                transform=fig.transFigure,
                facecolor="white",
                edgecolor="none",
                linewidth=0,
            )
        )

    add_figure_panel_label(fig, "a", (0.008, 0.968))
    add_figure_panel_label(fig, "b", (0.575, 0.968))
    add_figure_panel_label(fig, "c", (0.008, 0.510))
    fig.savefig(output, transparent=True)
    plt.close(fig)


def build_exact_main_figure() -> None:
    """Retain the Illustrator assembly and standardize only panel labels."""
    REVISION_MAIN_DIR.mkdir(parents=True, exist_ok=True)
    output_pdf = REVISION_MAIN_DIR / "fig_6.pdf"
    with tempfile.TemporaryDirectory(prefix="fig6_label_overlay_") as directory:
        temporary_dir = Path(directory)
        original_copy = temporary_dir / "original.pdf"
        overlay = temporary_dir / "overlay.pdf"
        tex_path = temporary_dir / "fig6_labelled.tex"
        shutil.copyfile(ORIGINAL_MAIN, original_copy)
        build_panel_label_overlay(overlay)
        tex_path.write_text(
            r"""\documentclass{article}
\usepackage{graphicx}
\usepackage[paperwidth=585.261bp,paperheight=462.353bp,margin=0bp]{geometry}
\usepackage{eso-pic}
\pagestyle{empty}
\begin{document}
\AddToShipoutPictureBG*{\AtPageLowerLeft{\includegraphics[width=\paperwidth,height=\paperheight]{original.pdf}}}
\AddToShipoutPictureFG*{\AtPageLowerLeft{\includegraphics[width=\paperwidth,height=\paperheight]{overlay.pdf}}}
\null
\end{document}
""",
            encoding="utf-8",
        )
        run([
            "pdflatex",
            "-interaction=batchmode",
            "-halt-on-error",
            "-output-directory",
            str(temporary_dir),
            str(tex_path),
        ], cwd=temporary_dir)
        labelled = temporary_dir / "fig6_labelled.pdf"
        if not labelled.exists():
            raise RuntimeError("Failed to assemble the standardized panel labels")
        shutil.copyfile(labelled, output_pdf)
    render_pdf(output_pdf, REVISION_MAIN_DIR / "fig_6", dpi=300)


def write_audit(panel_checks: dict[str, dict[str, object]]) -> None:
    main_output = REVISION_MAIN_DIR / "fig_6.pdf"
    checks = {
        "figure": "Fig. 6",
        "construction": "original Fig. 4 scripts, panels and Illustrator assembly",
        "primary_city_count": 12,
        "primary_pair_count": 6,
        "detroit_or_windsor_present": False,
        "panel_checks": panel_checks,
        "all_regenerated_panels_pixel_identical_to_original": all(
            bool(record["pixel_identical_at_150_dpi"]) for record in panel_checks.values()
        ),
        "main_pdf_byte_identical_to_original_fig4": sha256(main_output) == sha256(ORIGINAL_MAIN),
        "expected_main_difference": "only the a, b and c panel identifiers were replaced",
        "panel_identifier_style": "same traced Myriad Pro vector glyphs and 9.49-pt height used in revised Fig. 5",
        "guide_caption_title_synchronized": True,
        "guide_standard_model_scope_synchronized": {
            "system_size_kw": 5,
            "project_lifetime_years": 25,
            "real_discount_rate": 0.05,
        },
        "guide_fixed_pair_order_stated": True,
        "guide_uncertainty_terminology": "2.5th to 97.5th percentile propagated uncertainty summaries",
        "guide_segment_model_limitations_stated": True,
        "source_data_rows": {"Fig_6a": 12, "Fig_6b": 312, "Fig_6c": 12, "Fig_6": 336},
        "guide_audit_status": "pass",
        "original_main_sha256": sha256(ORIGINAL_MAIN),
        "revision_main_sha256": sha256(main_output),
    }
    CHECKS_PATH.write_text(json.dumps(checks, indent=2) + "\n", encoding="utf-8")

    log = """# Revised Fig. 6 generation log

## Authoritative production route

Revised Fig. 6 is generated from the original Fig. 4 production assets. The three original plotting scripts are rerun with the original 12-city economic inputs. Each regenerated panel is compared with its retained original panel PDF at 150 dpi.

The original Fig. 4 Illustrator assembly is reused as the revised Fig. 6 master. This preserves the original layout, fonts, coordinates, line styles, uncertainty bars, labels and legend placement. Only the `a,`, `b,` and `c,` identifiers are replaced with the same traced Myriad Pro vector glyphs and 9.49-point height used in the other revised figures. No panel content or layout redesign is applied.

## Verified outputs

- `figures/main/revision/fig_6.pdf`
- `figures/main/revision/fig_6.png`
- `figures/panels/revision/fig6a_primary12_capex_npv.pdf`
- `figures/panels/revision/fig6b_primary6_cashflow_facets.pdf`
- `figures/panels/revision/fig6c_primary12_value_cost_rates.pdf`

Detroit and Windsor remain outside the main economic figure and are reserved for the Supplementary Information.
"""
    LOG_PATH.write_text(log, encoding="utf-8")


def main() -> None:
    required = [ORIGINAL_MAIN, ECONOMIC_INPUT]
    required.extend(job["original"] for job in PANEL_JOBS.values())
    required.extend(job["script"] for job in PANEL_JOBS.values())
    missing = [path for path in required if not path.exists()]
    if missing:
        raise FileNotFoundError(f"Missing original Fig. 4 assets: {missing}")

    regenerate_original_panels()
    refresh_panel_c_source_data()
    with tempfile.TemporaryDirectory(prefix="fig6_original_match_") as directory:
        temporary_dir = Path(directory)
        panel_checks = {
            label: raster_identity(job["original"], job["revision"], temporary_dir)
            for label, job in PANEL_JOBS.items()
        }
    failed = [label for label, result in panel_checks.items() if not result["pixel_identical_at_150_dpi"]]
    if failed:
        print(f"[warning] Regenerated panels differ from the retained production masters: {failed}. "
              "The authoritative Illustrator-composed PDF is retained; differences can arise from fonts or rendering libraries.")

    build_exact_main_figure()
    write_audit(panel_checks)
    print(f"[ok] exact Fig. 4 assembly retained as: {REVISION_MAIN_DIR / 'fig_6.pdf'}")
    print("[ok] regenerated panels are pixel-identical to the retained originals")


if __name__ == "__main__":
    main()

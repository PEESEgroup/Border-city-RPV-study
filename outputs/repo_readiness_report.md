# Repository Readiness Report

## Scope
This report is based on direct inspection of:

- `docs/AGENTS.md`
- `docs/manuscript_blueprint.md`
- `docs/journal_style.md`
- `docs/figure_map.md`
- `docs/variable_dictionary.md`
- `outputs/results_catalog.md`
- `data/`
- `figures/main/`
- `figures/panels/`
- `paper/manuscript.tex`
- `paper/supplementary.tex`
- `script/`

The report has been refreshed after the latest updates to pattern labels, terminology-normalization guidance, and manuscript/SI section titles.

## 1. What Each Major Folder Appears To Contain

### `docs/`
- Project-level manuscript instructions and drafting rules.
- `AGENTS.md` defines workflow, source priority, and file-safety rules.
- `manuscript_blueprint.md` defines the central argument, narrative logic, figure roles, and section-level intent.
- `journal_style.md` defines Nature Cities-style structure, tone, and caption expectations.
- `figure_map.md` is the main figure-to-panel-to-input crosswalk.
- `variable_dictionary.md` now serves both as a variable reference and as a manuscript-facing normalization guide for pattern labels and terminology.

### `data/`
- Final manuscript-facing tabular evidence.
- `data/Building_PVs/` contains rooftop PV mapping summaries, roof-size summaries, image coverage, and building-class summaries.
- `data/PV_Eco_model/` contains city-level PV economic outputs, including both `economic_analysis_results.csv` and the yearly `discounted_cashflow_profiles_city_year.csv`.
- `data/Policy_frictions/` contains the city-level friction matrix and its codebook.
- `data/city_economic/` contains socioeconomic context variables.

### `figures/`
- `figures/main/` contains six assembled main-text figures.
- `figures/panels/` contains the component panels used to assemble Figures 2-5, plus the six pair heatmaps used in Figure 1.

### `paper/`
- `manuscript.tex` is now a more usable manuscript shell, with Results and Methods subsection placeholders and a singular `Discussion` section.
- `supplementary.tex` is a simplified SI skeleton with section titles for:
  - computer-vision-driven rooftop PV identification
  - urban PV economic modeling
  - policy friction analysis

### `script/`
- Figure-generation and modeling scripts aligned with the main manuscript figures.
- Includes `econimic_model.py` and plotting scripts corresponding to Figures 1-6.

### `outputs/`
- Current manuscript-support outputs:
  - `results_catalog.md`
  - `manuscript_section_plan.md`
  - this `repo_readiness_report.md`

## 2. Which Files Are Likely The Main Evidence Sources For The Manuscript

### Core quantitative evidence
- `data/Building_PVs/pair_area_summary.csv`
  Main source for all-building, residential, and non-residential PV-share comparisons.
- `data/Building_PVs/pair_base_class_ratio_summary.csv`
  Main source for building-type PV adoption and class-level comparisons.
- `data/Building_PVs/city_roofsize_pv_adoption.csv`
  Main source for roof-size heterogeneity in Figure 6.
- `data/PV_Eco_model/economic_analysis_results.csv`
  Main source for CAPEX, NPV, IRR, LCOE, blended solar value, and electricity/export-rate comparisons.
- `data/PV_Eco_model/discounted_cashflow_profiles_city_year.csv`
  Main source for exact yearly cash-flow trajectories in Figure 4 panel b.
- `data/Policy_frictions/border_city_pv_friction_matrix.csv`
  Main source for revenue, administrative, and total policy-friction comparisons.
- `data/Policy_frictions/border_city_pv_friction_codebook.csv`
  Main source for friction indicator definitions and scoring logic.
- `data/city_economic/border_city_pairs_A_numbeo_2024.csv`
  Main source for income and broader socioeconomic context.

### Supporting methods evidence
- `data/Building_PVs/city_image_coverage_summary.csv`
  Key support for image count and spatial coverage.
- `data/Building_PVs/border_ckpt_benchmark_all_except_windsor_detroit_per_city.csv`
  Key support for segmentation benchmark reporting.

### Figure-writing and narrative support
- `docs/figure_map.md`
  Main provenance map from figures to inputs and scripts.
- `docs/variable_dictionary.md`
  Now also defines manuscript-facing pattern-label and terminology normalization.
- `outputs/results_catalog.md`
  Current figure-by-figure audit of what each main figure shows and what is safe to cite.
- `docs/manuscript_blueprint.md`
  Main source for section placement and claim hierarchy.

## 3. Which Figures Appear Ready For Writing

Based on the current repository state:

- `Figure 2` appears ready for writing.
  The figure exists, the panel files exist, mapped inputs are clear, and the pattern-label table is now explicitly maintained in `docs/variable_dictionary.md`.
- `Figure 3` appears ready for writing.
  The figure exists, supporting inputs are clear, and several exact values are printed directly in the figure.
- `Figure 4` appears ready for writing.
  The figure exists, panel files exist, and panel b now has a dedicated yearly cash-flow CSV.
- `Figure 5` appears ready for writing.
  The heatmap panel exists and both the friction matrix and codebook are present.
- `Figure 6` appears ready for writing with restrained interpretation.
  Inputs are present, variables are clear, and the updated figure-map note now better explains how to use the heterogeneity message.
- `Figure 1` appears ready for workflow/methods writing.
  It is suitable for Introduction framing and Methods explanation, but it should still not be treated as a primary empirical Results figure.

### Overall readiness summary
- Strongest writing-ready figures: `Figures 2, 3, 4, 5`
- Ready with careful interpretation: `Figure 6`
- Ready as a framework/workflow figure: `Figure 1`

## 4. Which Figure-Map Entries May Still Need Manual Completion

### Figure 1
- Panel c is explicitly conceptual, but still does not list formal `Input` and `Variables` blocks.
- Panel d is explicitly conceptual, but still does not list formal `Input` and `Variables` blocks.
- The figure map still tells the writer to mention the heatmap kernel size, but the kernel size itself is not recorded there. `[CHECK]`

### Figure 6
- The updated note is now useful, but it remains interpretive guidance rather than a direct variable definition.
- The wording about lower-income cities having more advantage on large-roof and non-residential segments should still be converted into manuscript prose with pair-specific restraint. `[CHECK]`

### Figure 3
- Figure prose should use the plotted term `Policy Friction Score` when directly describing the visible axis, while still keeping its provenance traceable to `Total Friction Index`.

## 5. Any Obvious Risks For Writing Consistency

### Figure 1 methods-versus-results boundary risk
- Figure 1 still mixes data-backed workflow elements with conceptual analytical integration.
- The blueprint now clearly instructs that Figure 1 may be mentioned briefly in the Introduction but should be used formally in the Methods.
- This remains an important drafting boundary to keep.

### Manuscript-shell completeness risk has been reduced
- `paper/manuscript.tex` now contains the main Results and Methods subsection placeholders, plus a singular `Discussion`.
- This is a meaningful improvement over the earlier minimal shell.
- Remaining structural gaps are smaller now, mainly the absence of figure-legend placeholders.

### Terminology normalization risk has been reduced but not eliminated
- `docs/variable_dictionary.md` now explicitly instructs the writer to:
  - use `Juarez` consistently in drafting
  - ignore Detroit/Windsor legacy material
  - use the term shown in the plotted panel when raw-data labels differ
- This reduces a major consistency risk.
- Residual risk remains because some raw files and scripts still contain `Ciudad Juarez` and older labels.

### Legacy-name contamination risk
- The manuscript-facing instructions now clearly say to ignore Detroit/Windsor legacy material.
- Some scripts and filenames still retain Detroit/Windsor entries, but these do not appear to affect the current main-figure set.

### Script-name mismatch risk
- Some script filenames still reflect earlier narrower use cases, such as `plot_res_nonres_two_pair_gap_scatter.py` now supporting an all-pair panel.
- This is not a results problem, but it can still confuse provenance if cited casually in Methods text.

## Bottom Line

The repository is now in better shape for manuscript drafting than in earlier audits. The key improvements are:

- pattern-label guidance is now explicitly maintained in `docs/variable_dictionary.md`
- terminology normalization is now explicitly documented
- `manuscript.tex` now has a more usable section/subsection container
- `supplementary.tex` now has clearer section titles
- Figure 4 panel b remains fully traceable through its dedicated yearly CSV

The main remaining issues are no longer major blockers. They are mostly drafting-discipline issues:

- keep Figure 1 in the Introduction/Methods lane rather than treating it as a core Results figure
- apply Figure 6’s updated interpretation carefully and pair-by-pair
- keep normalized manuscript terminology consistent even when raw data or scripts use older labels
- avoid over-interpreting script names or legacy code remnants as current analytical scope

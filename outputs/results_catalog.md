# Results Catalog

This catalog was refreshed after re-reading `docs/AGENTS.md`, `docs/figure_map.md`, `docs/variable_dictionary.md`, `docs/manuscript_blueprint.md`, `docs/journal_style.md`, and the current manuscript skeleton files. It follows the updated terminology-normalization rule in `docs/variable_dictionary.md`: use the plotted term when figure terminology differs from raw-data field names, and use `Juarez` consistently in drafting.

## Figure 1

**Figure name**
`Figure 1. Cross-border rooftop PV mapping and comparative analysis framework`

**Purpose**
Provide the overall workflow linking rooftop PV mapping, heatmap generation, city-level economic and policy variables, and downstream neighboring-city divergence analysis.

**What is visibly shown in the image**
- Panel a is a workflow schematic for border-city rooftop PV mapping.
- It visibly includes orthophoto collection, SegFormer-based visual modeling, PV segmentation, building-footprint collection, and building-RPV mapping.
- Panel a visibly prints summary values including `12 cities, 6 pairs`, `327k imgaes`, `5,822 km² land area`, `Dice: 0.823 - 0.956`, `IoU: 0.707 - 0.896`, `3.8M buildings`, and `704 km² rooftop area`.
- Panel b shows six paired rooftop-PV heatmaps for Vienna-Bratislava, Singapore-Johor Bahru, San Diego-Tijuana, El Paso-Juarez, Hong Kong-Shenzhen, and Monaco-Nice, with a world locator map in the center.
- Panel c is a conceptual block showing socioeconomic, PV economic, and policy-friction variable families.
- Panel d is a conceptual block showing divergence patterns, driven factors, policy insights, and miniature previews of the downstream analytical figures.

**Input files listed in `docs/figure_map.md`**
- `data/Building_PVs/border_ckpt_benchmark_all_except_windsor_detroit_per_city.csv`
- `data/Building_PVs/city_image_coverage_summary.csv`
- `figures/panels/heatmaps/`

**Main script listed**
- `script/plot_pair_heatmap.py` for panel b
- No single assembly script is listed for the full composite figure. `[CHECK]`

**Main manuscript claim this figure can support**
- The study integrates building-level rooftop PV mapping with city-level economic and policy information in a unified cross-border analytical workflow.
- This figure is best used as a framework figure for the Introduction and especially the Methods, not as a standalone empirical Results figure.

**Any exact numbers or ranges that are safe to cite**
- Safe to cite from the image itself:
  - `12 cities, 6 pairs`
  - `327k` images
  - `5,822 km²` land area
  - `Dice: 0.823-0.956`
  - `IoU: 0.707-0.896`
  - `3.8M` buildings
  - `704 km²` rooftop area
- Safe to cite from listed input files for terminology support:
  - `city_image_coverage_summary.csv` contains `image_count` and `covered_area_km2`
  - `border_ckpt_benchmark_all_except_windsor_detroit_per_city.csv` contains `dice` and `iou`

**Uncertainties or mismatches that require manual review**
- Panels c and d are now explicitly conceptual in `docs/figure_map.md`, but they still do not list formal `Input` or `Variables` blocks.
- The panel-a aggregate totals for buildings and rooftop area are visible in the figure, but they are not directly reconstructed from the listed Figure 1 input files alone. `[CHECK]`
- The figure map still says to mention the heatmap kernel size in the caption, but the kernel size itself is not recorded there. `[CHECK]`

## Figure 2

**Figure name**
`Figure 2. Within-pair rooftop PV utilization split and cross-domain rank divergence`

**Purpose**
Compare neighboring cities in each pair by within-pair rooftop PV utilization shares and by relative within-pair rank across income, PV deployment, IRR, and policy friction.

**What is visibly shown in the image**
- Panel a is a stacked horizontal-bar display for six city pairs.
- For each pair, the figure shows all-building, residential, and non-residential PV utilization shares split across the two cities.
- Exact percentages are printed inside the bars.
- Panel b is a paired rank-order plot across six dimensions: `Income`, `PV utilization`, `Res PV`, `Non-res PV`, `IRR`, and `Policy friction`.
- The right side groups the pairs into three visible pattern classes: `System-wide leadership pattern`, `Income-reversal pattern`, and `Segment-split pattern`.

**Input files listed in `docs/figure_map.md`**
- `data/Building_PVs/pair_area_summary.csv`
- `data/Building_PVs/pair_base_class_ratio_summary.csv`
- `data/Policy_frictions/border_city_pv_friction_matrix.csv`
- `data/PV_Eco_model/economic_analysis_results.csv`
- `data/city_economic/border_city_pairs_A_numbeo_2024.csv`

**Main script listed**
- `script/plot_city_rpv_utilization_within_pair_hbar.py`
- `script/plot_within_pair_rank_scatter.py`

**Main manuscript claim this figure can support**
- Border-city rooftop PV adoption diverges through recurring patterns rather than simple convergence.
- The three pattern labels used in drafting should follow the updated table in `docs/variable_dictionary.md`, which is intended to stay aligned with Figure 2.

**Any exact numbers or ranges that are safe to cite**
- Safe to cite from panel a because the values are printed in the figure:
  - Vienna-Bratislava: all `2.77%` vs `0.81%`; residential `1.73%` vs `0.65%`; non-residential `3.89%` vs `0.91%`
  - Singapore-Johor Bahru: all `7.28%` vs `1.29%`; residential `4.05%` vs `0.26%`; non-residential `8.93%` vs `2.10%`
  - San Diego-Tijuana: all `2.63%` vs `0.60%`; residential `2.69%` vs `0.15%`; non-residential `2.60%` vs `1.30%`
  - El Paso-Juarez: all `0.55%` vs `0.76%`; residential `0.71%` vs `1.34%`; non-residential `0.53%` vs `0.70%`
  - Hong Kong-Shenzhen: all `1.87%` vs `2.81%`; residential `1.12%` vs `0.71%`; non-residential `2.48%` vs `3.69%`
  - Monaco-Nice: all `0.79%` vs `0.83%`; residential `0.96%` vs `0.19%`; non-residential `0.65%` vs `1.12%`
- Safe to cite from panel b:
  - Rankings are within-pair only and take values `1` or `2`, with ties handled in the script as `1.5/1.5`.

**Uncertainties or mismatches that require manual review**
- The rank plot supports relative ordering, not magnitude.
- Pattern labels should now be treated as resolved through `docs/variable_dictionary.md`; if a future figure edit changes the visible grouping, re-check before drafting. `[CHECK if Figure 2 is revised later]`

## Figure 3

**Figure name**
`Figure 3. Pair-level PV utilization gap versus economic and policy-friction divergences`

**Purpose**
Show how within-pair PV gaps align with return and policy-friction differences, and decompose pair-level divergence across overall and sectoral measures.

**What is visibly shown in the image**
- Panel a is a bubble scatter with `Gap of Total Friction Index (city1 - city2)` on the x-axis and `Gap of IRR (city1 - city2, %)` on the y-axis.
- Bubble size represents `PV utilization gap`, with a legend showing `0.39%`, `1.45%`, and `2.01%`.
- The six border pairs are labeled directly on the chart.
- Panel b shows three aligned scatter plots of PV utilization gap against annual income gap, IRR gap, and `Policy Friction Score`, each with a fitted dashed trend line.
- Panel c shows five horizontal gap bars for each pair: `Gap of IRR (%)`, `Gap of Admin Friction`, `Gap of Revenue Friction`, `Gap of Res PV Share (pp)`, and `Gap of Non-res PV Share (pp)`.
- Exact panel-c bar values are printed in the figure.

**Input files listed in `docs/figure_map.md`**
- `data/Policy_frictions/border_city_pv_friction_matrix.csv`
- `data/PV_Eco_model/economic_analysis_results.csv`
- `data/Building_PVs/pair_area_summary.csv`
- `data/Building_PVs/pair_base_class_ratio_summary.csv`
- `data/city_economic/border_city_pairs_A_numbeo_2024.csv`

**Main script listed**
- `script/plot_res_nonres_two_pair_gap_scatter.py`
- `script/plot_pv_gap_three_factors.py`
- `script/plot_pair_res_nonres_gap_bars.py`

**Main manuscript claim this figure can support**
- Overall PV utilization gaps align more closely with economic-return and policy-friction differences than with wealth alone.
- Sectoral divergence can be unpacked into distinct residential and non-residential patterns alongside revenue and administrative friction gaps.

**Any exact numbers or ranges that are safe to cite**
- Safe to cite from panel a:
  - Bubble legend values: `0.39%`, `1.45%`, `2.01%`
  - Axis directions are signed as `city1 - city2`
- Safe to cite from panel c because values are printed:
  - Vienna-Bratislava: IRR gap `5.35`, admin gap `-1.00`, revenue gap `-2.00`, residential PV gap `1.08 pp`, non-residential PV gap `2.98 pp`
  - Singapore-Johor Bahru: `22.54`, `-3.00`, `-8.00`, `3.79 pp`, `6.83 pp`
  - San Diego-Tijuana: `9.20`, `-4.00`, `3.00`, `2.54 pp`, `1.30 pp`
  - El Paso-Juarez: `-6.70`, `0.00`, `3.00`, `-0.62 pp`, `-0.17 pp`
  - Hong Kong-Shenzhen: `-4.46`, `4.00`, `-7.00`, `0.42 pp`, `-1.21 pp`
  - Monaco-Nice: `-3.29`, `1.00`, `-6.00`, `0.77 pp`, `-0.47 pp`
- Safe to cite from panel b as visible-axis ranges:
  - Annual income gaps span roughly `0k` to `60k`
  - IRR gaps span roughly `-10` to `20`
  - Policy-friction gaps span roughly `-10` to `5`

**Uncertainties or mismatches that require manual review**
- The script name `plot_res_nonres_two_pair_gap_scatter.py` is older than the current all-pair usage.
- The plotted x-axis term is `Policy Friction Score`, while the mapped raw variable is `Total Friction Index`; per the terminology-normalization rule, manuscript prose should prefer the plotted term when directly describing the figure.

## Figure 4

**Figure name**
`Figure 4. Cross-border PV economic performance contrasts and rate-structure context`

**Purpose**
Compare city-level PV economic performance across neighboring-city pairs using CAPEX-profitability relationships, uncertainty-aware discounted cash-flow trajectories, and value-versus-cost plus rate-structure comparisons.

**What is visibly shown in the image**
- Panel a is a city-level scatter of `Net CAPEX ($)` versus `NPV ($)` with bubble size encoding `IRR (%)` and pair-connection lines linking neighboring cities.
- Panel b is a line chart of `Cumulative Discounted Cash Flow ($)` over `Year`, with labeled end points for each city and uncertainty intervals around the trajectories.
- Panel c combines left-side dumbbells between `Blended Solar Value` and `LCOE` and right-side horizontal bars for `Electricity Rate` and `Export Rate`, each with uncertainty bars.
- Cities are grouped visually by pair and colored consistently across panels.

**Input files listed in `docs/figure_map.md`**
- `data/PV_Eco_model/economic_analysis_results.csv`
- `data/PV_Eco_model/discounted_cashflow_profiles_city_year.csv`
- `script/econimic_model.py` as the upstream parameter source used to generate the panel-b series

**Main script listed**
- `script/plot_capex_vs_profitability_citypair_scatter.py`
- `script/plot_discounted_cashflow_profiles_citypair_lines.py`
- `script/plot_blended_lcoe_citypair_dumbbell_with_rates.py`

**Main manuscript claim this figure can support**
- Cross-border PV leadership is associated with stronger project economics, including more favorable CAPEX-profitability combinations, stronger long-run discounted returns, and robust uncertainty-aware separation in value and rate components.
- Differences in `Blended Solar Value`, `LCOE`, `Electricity Rate`, and `Export Rate` provide interpretable economic components behind the cross-pair patterns.

**Any exact numbers or ranges that are safe to cite**
- Safe to cite from `economic_analysis_results.csv` for panels a and c:
  - Net CAPEX spans `$2,550` to `$10,400`
  - NPV spans `$402` to `$19,048`
  - IRR spans `5.44%` to `29.80%`
  - LCOE spans `$0.033/kWh` to `$0.134/kWh`
  - `Blended Solar Value` spans `$0.061/kWh` to `$0.282/kWh`
  - Electricity rates span `$0.057/kWh` to `$0.390/kWh`
  - Export rates span `$0.020/kWh` to `$0.350/kWh`
- Safe examples from the mapped economic file:
  - San Diego: net CAPEX `$10,400`, NPV `$19,048`, IRR `20.41%`
  - Singapore: net CAPEX `$5,400`, NPV `$16,603`, IRR `29.80%`
  - El Paso: NPV `$402`, IRR `5.44%`
  - Hong Kong: export rate `$0.350/kWh`
- Safe to cite from panel b and its mapped yearly CSV:
  - The time horizon is `0-25` years.
  - The panel-b CSV contains `12` cities x `26` yearly points for `312` city-year rows.
  - Year-25 cumulative discounted cash flow ranges from `$402.50` for El Paso to `$19,047.70` for San Diego.

**Uncertainties or mismatches that require manual review**
- Panel b is now CSV-backed, but it remains model-derived from `city_solar_data_checked` in `script/econimic_model.py`; regenerate the CSV if assumptions change.
- Panel c now overlays error bars / uncertainty intervals on the value and rate components, so its visual interpretation depends on the uncertainty summary generated from the same model assumptions.
- Raw data and scripts still contain `Ciudad Juarez`, but drafting should use `Juarez` consistently per `docs/variable_dictionary.md`.
## Figure 5

**Figure name**
`Figure 5. Directional border-city PV policy-friction matrix heatmap`

**Purpose**
Show component-level and summary policy-friction scores for each city side of the six border-city pairs.

**What is visibly shown in the image**
- A single-panel heatmap titled `Border City PV Friction Matrix`.
- Columns include the eight component frictions `A-H` plus `Revenue`, `Admin`, and `Total`.
- The figure includes a visible legend from `Lower friction` to `Higher friction`.
- The top text block defines the component meanings for revenue and administrative friction.
- Exact cell values are printed in the heatmap.

**Input files listed in `docs/figure_map.md`**
- `data/Policy_frictions/border_city_pv_friction_matrix.csv`
- `data/Policy_frictions/border_city_pv_friction_codebook.csv`

**Main script listed**
- `script/plot_border_city_pv_friction_heatmap.py`

**Main manuscript claim this figure can support**
- Border-city policy conditions differ systematically across both revenue-side and administrative frictions.
- Revenue and administrative friction can diverge within the same pair, supporting the manuscript’s distinction between monetization barriers and procedural barriers.

**Any exact numbers or ranges that are safe to cite**
- Safe to cite from the heatmap and mapped CSV:
  - Component friction cells use a `0-3` scale.
  - Revenue Friction Index ranges from `0` to `11`
  - Administrative Friction Index ranges from `2` to `9`
  - Total Friction Index ranges from `6` to `20`
- Safe pair-level examples:
  - Vienna `Revenue 3`, `Admin 4`, `Total 7`; Bratislava `Revenue 5`, `Admin 5`, `Total 10`
  - Singapore `Revenue 3`, `Admin 6`, `Total 9`; Johor Bahru `Revenue 11`, `Admin 9`, `Total 20`
  - San Diego `Revenue 4`, `Admin 2`, `Total 6`; Tijuana `Revenue 1`, `Admin 6`, `Total 7`
  - El Paso `Revenue 4`, `Admin 6`, `Total 10`; Juarez `Revenue 1`, `Admin 6`, `Total 7`
  - Hong Kong `Revenue 0`, `Admin 9`, `Total 9`; Shenzhen `Revenue 7`, `Admin 5`, `Total 12`
  - Monaco `Revenue 1`, `Admin 8`, `Total 9`; Nice `Revenue 7`, `Admin 7`, `Total 14`

**Uncertainties or mismatches that require manual review**
- This figure is well aligned with its mapped inputs.
- The main interpretive caution remains that these are coded policy-friction scores, not direct measurements of realized approval time or user experience.

## Figure 6

**Figure name**
`Figure 6. Rooftop PV utilization and adoption heterogeneity by roof size and building type`

**Purpose**
Compare within-pair rooftop PV utilization across roof-size bins and PV adoption across building-use classes.

**What is visibly shown in the image**
- Panel a is a six-row line chart showing `PV utilization` across roof-size bins: `0-50`, `50-100`, `100-200`, `200-500`, `500-1000`, and `1000+`.
- Each row compares the two cities in one border pair with matched colors.
- Panel b is a six-row grouped bar chart showing PV adoption by building type: `Single-res`, `Multi-res`, `Commercial`, `Industrial`, `Public/Infra`, and `Others`.
- The figure visually emphasizes strong heterogeneity across both roof size and building use.

**Input files listed in `docs/figure_map.md`**
- `data/Building_PVs/city_roofsize_pv_adoption.csv`
- `data/Building_PVs/pair_base_class_ratio_summary.csv`

**Main script listed**
- `script/plot_city_roofsize_pv_adoption.py`

**Main manuscript claim this figure can support**
- Residential and non-residential heterogeneity is not captured by one aggregate deployment measure.
- Large-roof and building-type patterns differ across pairs, supporting the paper’s sectoral-divergence logic.
- Discussion of this figure should be grounded in the listed input-file values and remain pair-specific and restrained.

**Any exact numbers or ranges that are safe to cite**
- Safe to cite from the listed input files:
  - `pv_area_ratio` across city roof-size-bin observations spans `0.00%` to `10.33%`
  - `pv_building_count_ratio` across city building-type observations spans `0.00%` to `16.38%`
- Safe high-end examples from the mapped inputs:
  - Singapore reaches `10.33%` PV utilization in the `1000+` m² roof-size bin
  - Vienna reaches `4.52%` in the `1000+` bin
  - Shenzhen reaches `3.46%` in the `1000+` bin
  - San Diego reaches `16.38%` PV-building adoption in `single-residential`
  - Vienna reaches `14.79%` in `public & infrastructure`
  - Shenzhen reaches `11.85%` in `public & infrastructure`
  - Monaco reaches `10.53%` in `public & infrastructure`

**Uncertainties or mismatches that require manual review**
- The updated figure-map note is now useful for interpretation, but Figure 6 should still be discussed from the mapped ground-truth values in the listed input files, not from visual impression alone.
- The intended point is that some lower-income cities show more advantage on large-roof or non-residential segments, including Hong Kong-Shenzhen, Monaco-Nice, El Paso-Juarez, and a smaller-gap version in San Diego-Tijuana; this should be phrased with restraint rather than as a universal rule.

## Cross-Figure Notes

- `Figure 1` remains the least fully specified figure in `docs/figure_map.md`, but it is now more clearly framed as a workflow and conceptual Methods figure.
- `Figure 2` pattern usage should now follow the updated table in `docs/variable_dictionary.md`.
- `Figure 4` panel b now has a dedicated CSV, which improves traceability for exact numeric claims.
- `Figures 2` and `3` remain the strongest figures for exact visual quoting because many values are printed directly in the image.
- `Figure 5` is the cleanest figure for exact coded-score reporting.
- `Figure 6` is strong for heterogeneity claims, but its broader interpretation should remain pair-specific and restrained.

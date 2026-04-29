## Figure 1. Cross-border rooftop PV mapping and comparative analysis framework

**Purpose**
Provide an overview of the methodological workflow, including border-city rooftop PV mapping, spatial heatmap generation, city-level economic and policy integration, and neighboring-city divergence analysis.

**Output figure**
- `/datasets/joe/dataset/Border/manuscript/figures/main/fig_1.pdf`

### Panel a
**What it shows**
Workflow for border-city building rooftop PV mapping, including orthophoto collection, visual modeling with SegFormer, PV segmentation, building footprint collection, and building–rooftop PV alignment.

**Input**
- `/datasets/joe/dataset/Border/manuscript/data/Building_PVs/border_ckpt_benchmark_all_except_windsor_detroit_per_city.csv`
- `/datasets/joe/dataset/Border/manuscript/data/Building_PVs/city_image_coverage_summary.csv`

**Variables**
- `image_count`
- `covered_area_km2`
- `num_buildings`
- `rooftop_area_km2`
- `dice`
- `iou`

**Panel Note**
The metrics in the panel are slected. The detailed stats of model, data, and buildings are in the Supplementary.


### Panel b
**What it shows**
Rooftop PV heatmaps for the six border-city pairs, illustrating the spatial distribution of mapped rooftop PV systems across neighboring cities.

**Input**
- `/datasets/joe/dataset/Border/manuscript/figures/panels/heatmaps`

**Script**
- `/datasets/joe/dataset/Border/manuscript/script/plot_pair_heatmap.py`

**Panel Note**
Mention the kernel size in the caption.

### Panel c
**What it shows**
Integration of city-level socioeconomic indicators, PV economic modeling variables, and PV policy friction measures used for downstream comparative analysis.

**Panel Note**
This panel conceptually lists some of key variables from the economic, socioeconomic, and policy-friction.

### Panel d
**What it shows**
Analytical framework for neighboring-city divergence analysis, including divergence pattern identification, driven-factor analysis, and policy insight extraction.

**Key message**
The methodological framework links mapped PV deployment to cross-border divergence patterns, their potential economic and institutional drivers, and resulting policy insights.

**Notes**
- This is primarily a Methods-section figure and includes both data-driven and conceptual components.
- This figure is for illustrating the workflow and methods. The related discussion should focus on the data and model. Do not expand the specific context/value about economic and institutional drivers, and resulting policy when describling this figure.
- Panel a contains the core mapping pipeline and model performance summary.
- Panel c and Panel d conceptually summarize analytical integration and downstream comparison logic rather than standalone empirical results.

## Figure 2. Within-pair rooftop PV utilization split and cross-domain rank divergence

**Purpose**
Compare neighboring cities in each border pair by (a) within-pair rooftop PV utilization split across all/residential/non-residential buildings and (b) within-pair ranking divergence across socioeconomic, economic, PV deployment, and policy-friction indicators.

**Output figure**
- `/datasets/joe/dataset/Border/manuscript/figures/main/fig_2.pdf`

**Panel files (used to assemble Figure 2)**
- `/datasets/joe/dataset/Border/manuscript/figures/panels/pair_city_rpv_utilization_hbar.pdf`
- `/datasets/joe/dataset/Border/manuscript/figures/panels/within_pair_rank_scatter.pdf`

### Panel a
**What it shows**
Within-pair normalized horizontal bars for city-level rooftop PV utilization, reported for all buildings, residential buildings, and non-residential buildings.

**Input**
- `/datasets/joe/dataset/Border/manuscript/data/Building_PVs/pair_area_summary.csv`
- `/datasets/joe/dataset/Border/manuscript/data/Building_PVs/pair_base_class_ratio_summary.csv`

**Variables**
- `scope`
- `name`
- `pv_share_of_building`
- `residential_pv_share_of_building`
- `non_residential_pv_share_of_building`
- `building_area_m2`
- `pv_area_m2`
- `ratio_a`
- `ratio_b`

**Script**
- `/datasets/joe/dataset/Border/manuscript/script/plot_city_rpv_utilization_within_pair_hbar.py`

**Panel Note**
The script computes within-pair normalized shares (`ratio_a`, `ratio_b`) so each metric sums to 1 within a pair.

### Panel b
**What it shows**
Within-pair ranking comparison (rank 1 or 2) for each city across six dimensions: income, PV utilization, residential PV share, non-residential PV share, IRR, and policy friction.

**Input**
- `/datasets/joe/dataset/Border/manuscript/data/Policy_frictions/border_city_pv_friction_matrix.csv`
- `/datasets/joe/dataset/Border/manuscript/data/PV_Eco_model/economic_analysis_results.csv`
- `/datasets/joe/dataset/Border/manuscript/data/city_economic/border_city_pairs_A_numbeo_2024.csv`
- `/datasets/joe/dataset/Border/manuscript/data/Building_PVs/pair_area_summary.csv`

**Variables**
- `Annual Income USD (net, Numbeo)`
- `pv_share_of_building`
- `residential_pv_share_of_building`
- `non_residential_pv_share_of_building`
- `IRR (%)`
- `Total Friction Index`
- `within_pair_rank_income`
- `within_pair_rank_pv_utilization`
- `within_pair_rank_res_pv`
- `within_pair_rank_nonres_pv`
- `within_pair_rank_irr`
- `within_pair_rank_policy_friction`

**Script**
- `/datasets/joe/dataset/Border/manuscript/script/plot_within_pair_rank_scatter.py`

**Panel Note**
In this panel, higher values are better for income, PV utilization/share, and IRR, while lower values are better for policy friction.

**Notes**
- Figure 2 is documented as a manuscript composite of Panel a and Panel b outputs.

## Figure 3. Pair-level PV utilization gap versus economic and policy-friction divergences

**Purpose**
Show how within-pair rooftop PV utilization gaps relate to economic return and policy-friction differences, and decompose pair-level divergence across multiple factors and building types.

**Output figure**
- `/datasets/joe/dataset/Border/manuscript/figures/main/fig_3.pdf`

**Panel files (used to assemble Figure 3)**
- `/datasets/joe/dataset/Border/manuscript/figures/panels/all_pairs_allbuilding_totalfriction_irr_gap_scatter.pdf`
- `/datasets/joe/dataset/Border/manuscript/figures/panels/pv_gap_three_factors_scatter.pdf`
- `/datasets/joe/dataset/Border/manuscript/figures/panels/pair_res_nonres_5metric_barplots.pdf`

### Panel a
**What it shows**
All-pair scatter of rooftop PV utilization gap (bubble size) against policy-friction gap (x-axis) and IRR gap (y-axis), for six border-city pairs.

**Input**
- `/datasets/joe/dataset/Border/manuscript/data/Policy_frictions/border_city_pv_friction_matrix.csv`
- `/datasets/joe/dataset/Border/manuscript/data/PV_Eco_model/economic_analysis_results.csv`
- `/datasets/joe/dataset/Border/manuscript/data/Building_PVs/pair_area_summary.csv`
- `/datasets/joe/dataset/Border/manuscript/data/Building_PVs/pair_base_class_ratio_summary.csv`

**Variables**
- `Total Friction Index`
- `IRR (%)`
- `pv_share_of_building`
- `pv_adoption_gap`
- `abs_pv_adoption_gap`

**Script**
- `/datasets/joe/dataset/Border/manuscript/script/plot_res_nonres_two_pair_gap_scatter.py`

**Panel Note**
Directional gaps are computed as city1 minus city2, and bubble area encodes `|pv_adoption_gap|`.

### Panel b
**What it shows**
Three aligned scatter panels linking rooftop PV utilization gap (y-axis) to gaps in annual income, IRR, and total policy friction (x-axes), with per-panel fitted trend lines.

**Input**
- `/datasets/joe/dataset/Border/manuscript/data/city_economic/border_city_pairs_A_numbeo_2024.csv`
- `/datasets/joe/dataset/Border/manuscript/data/PV_Eco_model/economic_analysis_results.csv`
- `/datasets/joe/dataset/Border/manuscript/data/Policy_frictions/border_city_pv_friction_matrix.csv`
- `/datasets/joe/dataset/Border/manuscript/data/Building_PVs/pair_area_summary.csv`
- `/datasets/joe/dataset/Border/manuscript/data/Building_PVs/pair_base_class_ratio_summary.csv`

**Variables**
- `Annual Income USD (net, Numbeo)`
- `IRR (%)`
- `Total Friction Index`
- `pv_share_of_building`
- `pv_adoption_gap`

**Script**
- `/datasets/joe/dataset/Border/manuscript/script/plot_pv_gap_three_factors.py`

**Panel Note**
Each subplot uses signed within-pair gaps (`city1 - city2`) and the same y-variable (`pv_adoption_gap`) for direct cross-factor comparison.

### Panel c
**What it shows**
Five side-by-side horizontal bar charts for each border-city pair, showing signed gaps in IRR, administrative friction, revenue friction, residential PV share, and non-residential PV share.

**Input**
- `/datasets/joe/dataset/Border/manuscript/data/Policy_frictions/border_city_pv_friction_matrix.csv`
- `/datasets/joe/dataset/Border/manuscript/data/PV_Eco_model/economic_analysis_results.csv`
- `/datasets/joe/dataset/Border/manuscript/data/Building_PVs/pair_area_summary.csv`

**Variables**
- `IRR (%)`
- `Administrative Friction Index`
- `Revenue Friction Index`
- `residential_pv_share_of_building`
- `non_residential_pv_share_of_building`
- `IRR gap (%)`
- `Admin friction gap`
- `Revenue friction gap`
- `Res PV gap (pp)`
- `Non-res PV gap (pp)`

**Script**
- `/datasets/joe/dataset/Border/manuscript/script/plot_pair_res_nonres_gap_bars.py`

**Panel Note**
Residential and non-residential PV gaps are reported in percentage points (`pp`), while the other metrics remain in their native units.

## Figure 4. Cross-border PV economic performance contrasts and rate-structure context

**Purpose**
Compare city-level PV economic performance across neighboring-city pairs using CAPEX-profitability relationships, uncertainty-aware discounted cash-flow trajectories, and blended-value versus cost-and-rate comparisons.

**Output figure**
- `/datasets/joe/dataset/Border/manuscript/figures/main/fig_4.pdf`

**Panel files (used to assemble Figure 4)**
- `/datasets/joe/dataset/Border/manuscript/figures/panels/capex_vs_profitability.pdf`
- `/datasets/joe/dataset/Border/manuscript/figures/panels/discounted_cashflow_profiles_narrow_tall.pdf`
- `/datasets/joe/dataset/Border/manuscript/figures/panels/blended_lcoe_citypair_dumbbell_with_rates.pdf`

### Panel a
**What it shows**
City-level scatter of net CAPEX versus NPV, with marker size encoding IRR and connecting lines linking cities within each border pair.

**Input**
- `/datasets/joe/dataset/Border/manuscript/data/PV_Eco_model/economic_analysis_results.csv`

**Variables**
- `Net CAPEX ($)`
- `NPV ($)`
- `IRR (%)`
- `City`

**Script**
- `/datasets/joe/dataset/Border/manuscript/script/plot_capex_vs_profitability_citypair_scatter.py`

**Panel Note**
Point colors and pair-connection lines follow the border-pair palette; marker area is scaled by `IRR (%)`.

### Panel b
**What it shows**
City-level cumulative discounted cash-flow curves over project lifetime, with uncertainty intervals around each city trajectory and labeled endpoints for paired neighboring cities.

**Input**
- `/datasets/joe/dataset/Border/manuscript/data/PV_Eco_model/discounted_cashflow_profiles_city_year.csv`
- `/datasets/joe/dataset/Border/manuscript/script/econimic_model.py` (upstream `city_solar_data_checked` parameters used to generate the CSV)

**Variables**
- `city`
- `city_display`
- `year`
- `annual_cashflow_usd`
- `discounted_cashflow_usd`
- `cumulative_discounted_cashflow_usd`

**Script**
- `/datasets/joe/dataset/Border/manuscript/script/plot_discounted_cashflow_profiles_citypair_lines.py`

**Panel Note**
The panel now reads a standalone yearly series CSV generated by the same script and model assumptions (`system_size_kw=5`, `years=25`, `discount_rate=0.05` by default).

### Panel c
**What it shows**
Two-part comparison by city: dumbbells between blended solar value and LCOE with uncertainty bars, plus paired bars for electricity and export rates with uncertainty bars under the same city ordering.

**Input**
- `/datasets/joe/dataset/Border/manuscript/data/PV_Eco_model/economic_analysis_results.csv`

**Variables**
- `Blended Value of Solar ($/kWh)`
- `LCOE ($/kWh)`
- `Electricity Rate ($/kWh)`
- `Export Rate ($/kWh)`
- `City`

**Script**
- `/datasets/joe/dataset/Border/manuscript/script/plot_blended_lcoe_citypair_dumbbell_with_rates.py`

**Panel Note**
The left panel compares value versus cost per city, while the right panel provides rate-structure context using electricity and export tariff levels; both panels now show uncertainty markers derived from the same economic model assumptions.

## Figure 5. Directional border-city PV policy-friction matrix heatmap

**Purpose**
Provide a directional cross-city comparison of policy and administrative frictions that affect rooftop PV deployment, including component-level friction factors and aggregated indices.

**Output figure**
- `/datasets/joe/dataset/Border/manuscript/figures/main/fig_5.pdf`

**Panel files (used to assemble Figure 5)**
- `/datasets/joe/dataset/Border/manuscript/figures/panels/border_city_pv_friction_matrix_heatmap.pdf`

**What it shows**
Policy friction heatmap across the six border-city pairs, showing eight component friction scores and three summary indices (Revenue, Admin, Total) for each city.

**Input**
- `/datasets/joe/dataset/Border/manuscript/data/Policy_frictions/border_city_pv_friction_matrix.csv`
- `/datasets/joe/dataset/Border/manuscript/data/Policy_frictions/border_city_pv_friction_codebook.csv`

**Variables**
- `Pair`
- `City`
- `Comparison City`
- `A: Export compensation friction`
- `B: Export constraint friction`
- `C: Settlement complexity friction`
- `D: Policy uncertainty friction`
- `E: Small-system approval friction`
- `F: Building/planning approval friction`
- `G: Grid study/fee friction`
- `H: Professional credential friction`
- `Revenue Friction Index`
- `Administrative Friction Index`
- `Total Friction Index`

**Script**
- `/datasets/joe/dataset/Border/manuscript/script/plot_border_city_pv_friction_heatmap.py`

**Panel Note**
- This figure only contains one panel. 
- Refer to `border_city_pv_friction_codebook.csv` for the definition fo indictor and scoring criteria.
- Refer to `border_city_pv_friction_matrix.csv`'s keynote and url column for note and source for each city policy.
- All indicators are coded from 0 (lowest friction) to 3 (highest friction). 
- The unit is the city-side of each border-city pair because applicable regulation may differ on each side of the border.
- Scores summarize policy and administrative conditions documented in official materials; they do not directly measure realized approval time or household experience.
- Use the Revenue and Administrative Friction Indices separately before collapsing them into a total score, to distinguish monetization barriers from procedural barriers.
- Plain-text URLs are included in the matrix for traceability and can be moved into a supplementary source table in the manuscript.

## Figure 6. Rooftop PV utilization and adoption heterogeneity by roof size and building type

**Purpose**
Compare within-pair rooftop PV utilization across roof-size bins and PV adoption across building-use classes for the six border-city pairs.

**Output figure**
- `/datasets/joe/dataset/Border/manuscript/figures/main/fig_6.pdf`

**Main script**
- `/datasets/joe/dataset/Border/manuscript/script/plot_city_roofsize_pv_adoption.py`

**Input files**
- `/datasets/joe/dataset/Border/manuscript/data/Building_PVs/city_roofsize_pv_adoption.csv`
- `/datasets/joe/dataset/Border/manuscript/data/Building_PVs/pair_base_class_ratio_summary.csv`

### Panel a (Left column)
**What it shows**
City-level rooftop PV utilization across roof-size bins for each neighboring city pair. Each row compares the two cities in one border pair using matched colors.

**Input**
- `/datasets/joe/dataset/Border/manuscript/data/Building_PVs/city_roofsize_pv_adoption.csv`

**Variables**
- `city`
- `roof_size_bin`
- `bin_left_m2`
- `bin_right_m2`
- `building_area_m2`
- `pv_area_m2`
- `pv_area_ratio`

### Panel b (Right column)
**What it shows**
City-level rooftop PV adoption by building type for the same six border-city pairs. Bars show the fraction of buildings with at least one mapped rooftop PV segment in each building class.

**Input**
- `/datasets/joe/dataset/Border/manuscript/data/Building_PVs/pair_base_class_ratio_summary.csv`

**Variables**
- `scope`
- `name`
- `base_class_key`
- `base_class`
- `building_count`
- `pv_building_count`
- `pv_building_count_ratio`

**Notes**
- The left column uses `pv_area_ratio = pv_area_m2 / building_area_m2` within each roof-size bin.
- The right column uses `scope = city` rows from `pair_base_class_ratio_summary.csv`.
- Mention that some less-developed cities (less income) has more advantage on large-roof and non-residential roof, not only Hong Kong–Shenzhen and Monaco–Nice, but also El paso-Juarez. And even San diego-Tijuana, though San diego is system-wide leader, but the gap in large-roof is much smaller.

## Supplementary Figure S2. Uncertainty-propagated analogue of main-text Figure 4a

**Purpose**
Provide a clearer standalone view of the CAPEX-profitability comparison used in the main-text Figure 4a, with 95% uncertainty intervals around net CAPEX and NPV.

**Output figure**
- `/datasets/joe/dataset/Border/manuscript/figures/supplement/fig_s2_economic_uncertainty_capex_npv.pdf`

**What it shows**
City-level scatter of net CAPEX versus NPV, with marker size encoding median IRR and horizontal/vertical uncertainty intervals derived from the same Monte Carlo economic model used for the main analysis.

**Input**
- `script/econimic_model.py` as the upstream city parameter source used by `plot_fig4_uncertainty_supplement.py`

**Main script**
- `/datasets/joe/dataset/Border/manuscript/script/plot_fig4_uncertainty_supplement.py`

**Panel Note**
This is the only retained supplementary economic uncertainty figure; the former panel-b and panel-c supplementary outputs were removed because their uncertainty information is now carried directly in the main-text Figure 4.

## Supplementary Table S3. Pair-level IRR catch-up requirements

**Purpose**
Provide pair-level counterfactual requirements for the lagging city to match the leading city IRR, including export-rate adjustment and equivalent PV subsidy scale.

**Output table**
- `/datasets/joe/dataset/Border/manuscript/tables/table_s3_irr_match_requirements_by_pair.csv`
- `/datasets/joe/dataset/Border/manuscript/tables/table_s3_irr_match_requirements_by_pair.tex`

**Input**
- `/datasets/joe/dataset/Border/plots/csv/irr_match_requirements_by_pair.csv`

**Script**
- `/datasets/joe/dataset/Border/plots/scripts/factors/plot_irr_match_requirement_heatmap.py`

**Variables**
- `leading_irr_pct`
- `lagging_irr_pct`
- `irr_gap_pct_point`
- `required_export_rate_usd_per_kwh`
- `required_export_rate_increase_usd_per_kwh`
- `required_pv_subsidy_usd`
- `required_pv_subsidy_share_of_gross`
- `required_total_capex_reduction`

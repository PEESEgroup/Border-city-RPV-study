# Border Manuscript Variable Dictionary

This dictionary covers all CSV files under Border/manuscript/data (10 files total).

##  Studied border-city pairs (with order) and identified patterns
Use the identified divergence pattern for each pair consistently across figures, tables, and manuscript text.

| Pair | Pattern label |
|---|---|---|
| Vienna - Bratislava | [system-wide leadership] | 
| Singapore - Johor Bahru | [system-wide leadership] | 
| San Diego - Tijuana | [system-wide leadership] |
| El Paso - Juarez | [income reversal] | 
| Hong Kong - Shenzhen | [segmental divergence] |
| Monaco - Nice | [segmental divergence] |

**Note**
- The higher income (more wealthy) city is listed as the first one within pairs.

## Terminology normalization
- Use city name `Juarez` consistently for drafting, some data may use `Ciudad Juarez`.
- We study these 12 cities. Please ignore the legacy data about Detroit and Windsor, if there is any.
- Use varibale/term name plotted in the panel and figures, if there is any inconsistency in the raw data for the same concept.


## 1) data/Policy_frictions/border_city_pv_friction_codebook.csv

Note: This file is a scoring rubric/codebook for policy friction indicators, not a city observation table.

| Field | Meaning | Type/Unit | Example |
|---|---|---|---|
| Indicator | Indicator code (A-H) | string | A |
| Short name | Short indicator name | string | Export compensation friction |
| Dimension | Dimension category (Revenue/Administrative) | string | Revenue |
| Definition | Indicator definition | string | Extent to which compensation for exported PV electricity... |
| Score = 0 | Criteria text for score 0 | string | Stable and attractive compensation... |
| Score = 1 | Criteria text for score 1 | string | Moderate discount relative to retail value. |
| Score = 2 | Criteria text for score 2 | string | Clearly weaker export value than self-consumption... |
| Score = 3 | Criteria text for score 3 | string | Very weak export compensation... |
| Interpretation note | Interpretation guidance | string | Higher values indicate weaker monetization... |

## 2) data/Policy_frictions/border_city_pv_friction_matrix.csv

Note: This file is the city-level policy friction scoring matrix.

| Field | Meaning | Type/Unit | Example |
|---|---|---|---|
| Pair | Border city pair name | string | San Diego-Tijuana |
| City | Focal city | string | San Diego |
| Comparison City | Paired comparison city | string | Tijuana |
| A: Export compensation friction | Indicator A: export compensation friction | int (0-3) | 1 |
| B: Export constraint friction | Indicator B: export constraint friction | int (0-3) | 1 |
| C: Settlement complexity friction | Indicator C: settlement complexity friction | int (0-3) | 1 |
| D: Policy uncertainty friction | Indicator D: policy uncertainty friction | int (0-3) | 1 |
| E: Small-system approval friction | Indicator E: small-system approval friction | int (0-3) | 0 |
| F: Building/planning approval friction | Indicator F: building/planning approval friction | int (0-3) | 1 |
| G: Grid study/fee friction | Indicator G: grid study/fee friction | int (0-3) | 1 |
| H: Professional credential friction | Indicator H: professional credential friction | int (0-3) | 0 |
| Revenue Friction Index | Revenue friction index (sum of A-D) | int | 4 |
| Administrative Friction Index | Administrative friction index (sum of E-H) | int | 2 |
| Total Friction Index | Total friction index | int | 6 |
| Evidence status | Evidence completeness level | string | High |
| Key note | Key narrative note | string | Residential permitting is streamlined... |
| Primary source URL 1 | Primary source link 1 | URL string | https://www.sandiego.gov/... |
| Primary source URL 2 | Primary source link 2 | URL string | https://www.cpuc.ca.gov/... |

## 3) data/city_economic/border_city_pairs_A_numbeo_2024.csv

Note: This file provides city socioeconomic background variables (Numbeo and PPP-based indicators).

| Field | Meaning | Type/Unit | Example |
|---|---|---|---|
| City Pairs | Border group | string | US-MX Border |
| City | City name | string | San Diego, US |
| Annual Income USD (net, Numbeo) | Annual net income (Numbeo) | float, USD/year | 65915 |
| GDP per Capita PPP USD (2024) | GDP per capita (PPP) | float, USD/year | 85810 |
| Avg Rent 1BR Center USD/mo | Average 1-bedroom rent in city center | float, USD/month | 3145 |
| Property Price Center USD/sqm | Property price in city center | float, USD/sqm | 8613 |

## 4) data/Building_PVs/border_ckpt_benchmark_all_except_windsor_detroit_per_city.csv

Note: This file reports city-level segmentation benchmark performance.

| Field | Meaning | Type/Unit | Example |
|---|---|---|---|
| city | City identifier (lowercase) | string | bratislava |
| rank_in_city | Model rank within city | int | 1 |
| checkpoint | Model checkpoint path | string | /datasets/joe/dataset/Border/ckpts/cities_12__student_last.pth |
| samples | Number of samples | int | 78 |
| dice | Dice coefficient | float, 0-1 | 0.6884 |
| iou | Intersection over Union (IoU) | float, 0-1 | 0.5249 |
| precision | Precision | float, 0-1 | 0.7850 |
| recall | Recall | float, 0-1 | 0.6130 |
| accuracy | Pixel accuracy | float, 0-1 | 0.9976 |

## 5) data/Building_PVs/city_roofsize_pv_adoption.csv

Note: Building counts and PV adoption are summarized by city and roof-size bins.

| Field | Meaning | Type/Unit | Example |
|---|---|---|---|
| city | City identifier (lowercase) | string | bratislava |
| roof_size_bin | Roof-size bin label | string | 0-50 |
| bin_left_m2 | Bin left boundary | float, sqm | 0.0 |
| bin_right_m2 | Bin right boundary | float, sqm | 50.0 |
| building_count | Total building count | int | 45166 |
| pv_building_count | Building count with PV | int | 156 |
| pv_adoption | PV adoption rate by buildings | float, 0-1 | 0.00345 |
| building_area_m2 | Total building area | float, sqm | 1037447.38 |
| pv_area_m2 | Total PV area | float, sqm | 2394.96 |
| pv_area_ratio | PV area ratio | float, 0-1 | 0.00231 |

## 6) data/Building_PVs/pair_area_summary.csv

Note: Total and use-specific PV area shares are summarized at city and city-pair levels.

| Field | Meaning | Type/Unit | Example |
|---|---|---|---|
| scope | Aggregation level (city or pair) | string | city |
| name | City name or pair name | string | bratislava |
| pv_area_m2 | Total PV area | float, sqm | 178892.11 |
| building_area_m2 | Total building area | float, sqm | 20809541.60 |
| pv_share_of_building | PV-to-building area share | float, 0-1 | 0.00809 |
| residential_pv_area_m2 | Residential PV area | float, sqm | 53872.85 |
| residential_building_area_m2 | Residential building area | float, sqm | 8236343.34 |
| residential_pv_share_of_building | Residential PV-to-building area share | float, 0-1 | 0.00654 |
| non_residential_pv_area_m2 | Non-residential PV area | float, sqm | 114520.21 |
| non_residential_building_area_m2 | Non-residential building area | float, sqm | 12573198.26 |
| non_residential_pv_share_of_building | Non-residential PV-to-building area share | float, 0-1 | 0.00911 |

## 7) data/Building_PVs/city_image_coverage_summary.csv

Note: Image coverage statistics used to describe spatial sample coverage.

| Field | Meaning | Type/Unit | Example |
|---|---|---|---|
| city | City identifier (lowercase) | string | bratislava |
| image_count | Number of images | int | 12733 |
| unique_tile_count | Number of unique tiles | int | 12733 |
| covered_area_m2 | Covered area | float, sqm | 132506949.24 |
| covered_area_km2 | Covered area | float, sq km | 132.5069 |

## 8) data/Building_PVs/pair_base_class_ratio_summary.csv

Note: Building and PV ratios summarized by city and base building class.

| Field | Meaning | Type/Unit | Example |
|---|---|---|---|
| scope | Aggregation level (city or pair) | string | city |
| name | City name or pair name | string | bratislava |
| base_class_key | Building class key | string | commercial |
| base_class | Building class label | string | Commercial |
| building_count | Building count in class | int | 16645 |
| pv_building_count | PV building count in class | int | 332 |
| pv_building_count_ratio | PV building share in class | float, 0-1 | 0.01995 |
| building_area_m2 | Building area in class | float, sqm | 5120273.94 |
| pv_area_m2 | PV area in class | float, sqm | 58510.48 |
| pv_area_ratio | PV area share in class | float, 0-1 | 0.01143 |

## 9) data/PV_Eco_model/economic_analysis_results.csv

Note: City-level rooftop PV economic analysis outputs.

| Field | Meaning | Type/Unit | Example |
|---|---|---|---|
| City | City name | string | San Diego |
| Border Group | Border group | string | US-MX |
| Net CAPEX ($) | Net upfront investment (after incentives) | float, USD | 10400.0 |
| Gross CAPEX ($) | Gross upfront investment (before incentives) | float, USD | 13000.0 |
| LCOE ($/kWh) | Levelized cost of electricity | float, USD/kWh | 0.1103 |
| NPV ($) | Net present value | float, USD | 19048.0 |
| IRR (%) | Internal rate of return | float, % | 20.41 |
| Simple Payback (Years) | Simple payback period | float, years | 4.73 |
| Discounted Payback (Years) | Discounted payback period | float, years | 5.62 |
| Compensation Ratio | Export compensation-to-retail ratio | float | 0.077 |
| Self-consumption Ratio | Self-consumption share | float, 0-1 | 0.7 |
| Export Ratio | Export share | float, 0-1 | 0.3 |
| PV Yield (kWh/kW/year) | Annual PV yield per installed kW | float, kWh/kW/year | 1650 |
| Electricity Rate ($/kWh) | Local electricity retail rate | float, USD/kWh | 0.39 |
| Export Rate ($/kWh) | Export electricity rate | float, USD/kWh | 0.03 |
| Blended Value of Solar ($/kWh) | Weighted solar value (self-use + export) | float, USD/kWh | 0.282 |
| CAPEX Reduction | CAPEX reduction share (incentive effect) | float, 0-1 | 0.2 |
| Degradation Rate | Annual degradation rate | float, 0-1 | 0.005 |
| O&M Rate | Operations and maintenance cost rate | float, 0-1 | 0.01 |
| Year-1 Production (kWh) | Year-1 energy production | float, kWh | 8250.0 |
| Year-1 Savings ($) | Year-1 bill savings | float, USD | 2326.0 |
| Year-1 O&M ($) | Year-1 O&M cost | float, USD | 130.0 |
| Year-1 Net Cash Flow ($) | Year-1 net cash flow | float, USD | 2196.0 |

## 10) data/PV_Eco_model/discounted_cashflow_profiles_city_year.csv

Note: Yearly city-level cash-flow trajectories used to support Figure 4 panel b, exported by `plot_discounted_cashflow_profiles_citypair_lines.py` from the same economic model assumptions.

| Field | Meaning | Type/Unit | Example |
|---|---|---|---|
| city | City key used in model output | string | Vienna |
| city_display | Display label used in figure annotations | string | Juarez |
| year | Project year index (`0` is initial investment point) | int | 0 |
| annual_cashflow_usd | Undiscounted annual net cash flow for that year (`year>=1`) | float, USD | 1437.9 |
| discounted_cashflow_usd | Discounted annual net cash flow for that year (`year>=1`) | float, USD | 1369.43 |
| cumulative_discounted_cashflow_usd | Cumulative discounted cash flow at each year | float, USD | -7430.57 |

## 11) tables/table_s3_irr_match_requirements_by_pair.csv (Supplementary Table S3)

Note: Pair-level decomposition of how each lagging city can match the leading city IRR from `plot_irr_match_requirement_heatmap.py`. City name is normalized to `Juarez` for manuscript text consistency. In the rendered SI table (`table_s3_irr_match_requirements_by_pair.tex`), the `pair` key is omitted for readability, and a derived percentage column is added.

| Field | Meaning | Type/Unit | Example |
|---|---|---|---|
| pair | Border city pair key | string | US-MX-1 |
| leading_city | City with higher baseline IRR in the pair | string | San Diego |
| lagging_city | City with lower baseline IRR in the pair | string | Tijuana |
| leading_irr_pct | Leading city IRR | float, % | 20.41 |
| lagging_irr_pct | Lagging city IRR | float, % | 11.21 |
| irr_gap_pct_point | Within-pair IRR gap (leading - lagging) | float, percentage points | 9.20 |
| lagging_current_export_rate_usd_per_kwh | Current export rate in lagging city | float, USD/kWh | 0.119 |
| required_export_rate_usd_per_kwh | Export rate required for lagging city to match leading IRR | float, USD/kWh | 0.368938 |
| required_export_rate_increase_usd_per_kwh | Required export-rate increase above current level | float, USD/kWh | 0.249938 |
| extra_export_relative_pct | Relative extra export requirement, computed as `required_export_rate_increase_usd_per_kwh / lagging_current_export_rate_usd_per_kwh * 100` | float, % | 210.1 |
| lagging_gross_capex_usd | Gross CAPEX of lagging city under base assumptions | float, USD | 8000.0 |
| lagging_current_capex_reduction | Baseline CAPEX reduction share in lagging city | float, 0-1 | 0.10 |
| required_pv_subsidy_usd | Additional PV subsidy needed to match leading IRR | float, USD | 2932.611325 |
| required_pv_subsidy_share_of_gross | Additional subsidy as share of gross CAPEX | float, 0-1 | 0.366576 |
| required_total_capex_reduction | Total CAPEX reduction share after adding required subsidy | float, 0-1 | 0.466576 |
# Source Data

This is the active, style-preserved revision Source Data workspace. Files are added and locked one main figure at a time. The deprecated `revision_7pairs_v1` workbook is not reused because it treats Detroit--Windsor as a seventh primary pair and follows the superseded figure architecture.

## Completed

- `csv/Fig_1.csv`: displayed study totals, city-level mapping summaries, panel-c metric definitions and the six primary pair attributes shown in panel d.
- `source_data_checks_fig1.json`: machine-readable Fig. 1 checks and unique-image totals.
- `figure_notes/Fig_1_notes.md`: panel definitions, map lineage and residual production notes.
- `csv/Fig_3.csv`: combined figure-level Source Data for the 12-city anatomy, roof-size profiles, exact six-pair decomposition and building-use prevalence gaps.
- `csv/Fig_3a.csv` to `csv/Fig_3d.csv`: panel-level plotting tables retained for audit and reproduction.
- `source_data_checks_fig3.json`: scope, identity, decomposition, layout and reliability-hatch checks.
- `figure_notes/Fig_3_notes.md`: definitions, direction conventions, risk flags and manuscript linkage.
- `csv/Fig_4.csv`: figure-level Source Data for eligible-grid distributions, spatial-concentration summaries and aggregate versus median-grid gaps.
- `csv/Fig_4a.csv` to `csv/Fig_4c.csv`: panel-level plotting tables, including top-decile cutoff-tie diagnostics.
- `source_data_checks_fig4.json`: scope, quantile reproduction, eligible-cell count and direction-disagreement checks.
- `figure_notes/Fig_4_notes.md`: common-grid, eligibility, zero-cell, boundary-cell and top-decile rules.
- `csv/Fig_6.csv`: combined Source Data for the 12-city standardized economic comparison, 25-year discounted-cash-flow profiles and value/cost/rate diagnostics.
- `csv/Fig_6a.csv` to `csv/Fig_6c.csv`: panel-level plotting tables, including the propagated uncertainty summaries used for panels b and c.
- `source_data_checks_fig6.json`: six-pair scope, 5-kW model and Detroit/Windsor exclusion checks.
- `figure_notes/Fig_6_notes.md`: standardized-model interpretation, uncertainty-band definition and sector/building-level limitations.
- `csv/Fig_S_policy.csv`: combined Source Data for the supplementary documented-policy component matrix and factor-by-segment directional-alignment panel.
- `csv/Fig_S_policy_a.csv` and `csv/Fig_S_policy_a_pair_summary.csv`: 12-city component scores, index sums and six-pair lower-friction labels used in panel a.
- `csv/Fig_S_policy_b.csv` and `csv/Fig_S_policy_b_factor_summary.csv`: 96 pair-factor-segment contributions and eight factor-level residential and non-residential summaries used in panel b.
- `source_data_checks_fig_s_policy.json`: primary-city scope, Detroit and Windsor exclusion, component-sum, denominator and factor-weight checks.
- `figure_notes/Fig_S_policy_notes.md`: component definitions, sign conventions, valid denominators and interpretation limits.
- `csv/Fig_S_grid_atlas.csv` and `spatial/Fig_S_grid_atlas_cells.geojson`: the 5,238 eligible 1-km cells plotted in the 12-city atlas, including building counts, footprint area, PV area, utilization, zero-PV status, common-scale bin and exact square geometry.
- `csv/Fig_S_grid_sensitivity_scenarios.csv`: the ten tested resolution, origin, eligibility and boundary-cell specifications.
- `csv/Fig_S_grid_sensitivity_city.csv`: 120 city-scenario records containing eligible-cell counts, utilization percentiles, zero-PV shares and top-decile PV-area concentration.
- `csv/Fig_S_grid_sensitivity_pair.csv`: 60 pair-scenario records containing signed median-grid gaps, pairwise superiority probabilities and aggregate-versus-median direction checks.
- `source_data_checks_spatial_supplement.json`: baseline reproduction, scenario-completeness, disagreement-persistence, zero-PV retention and current SI-number checks.
- `figure_notes/Fig_S_grid_spatial_notes.md`: grid, color-scale, boundary-cell, concentration and direction conventions plus the exact reproduction command.
- `csv/Fig_S_large_roof.csv`: 12 observed primary-city large-roof records and six illustrative within-pair benchmark records, with fraction and percentage fields retained separately.
- `csv/Fig_S_large_roof_original_metrics.csv`: direct reproduction export from the original Fig. 6b calculation grammar using the current audited roof-size input.
- `source_data_checks_fig_s_large_roof.json`: six-pair scope, citywide-utilization reproduction and benchmark-formula checks.
- `figure_notes/Fig_S_large_roof_notes.md`: observed-variable definitions, benchmark formula and non-causal interpretation limits.
- `csv/Fig_S_detroit_windsor.csv`: combined 538-row Source Data table for the candidate-pair figure.
- `csv/Fig_S_detroit_windsor_a.csv` and `spatial/Fig_S_detroit_windsor_grid_cells.geojson`: 520 eligible-grid records and their exact plotted geometries.
- `csv/Fig_S_detroit_windsor_b.csv`: 12 city by roof-size-bin observations.
- `csv/Fig_S_detroit_windsor_c.csv`: six city-scenario IRR records covering the grant-realized central, no-support and Windsor no-grant comparisons.
- `source_data_checks_fig_s_detroit_windsor.json`: grid-count, zero-PV-share, central-IRR and no-grant reversal checks.
- `figure_notes/Fig_S_detroit_windsor_notes.md`: scope, imagery dates, grid rules, roof-size denominator and scenario interpretation.
- `csv/Table_S_boundaries.csv`: 14-city analytical mapping units, boundary areas, containment percentages, contextual jurisdictions, source records and caveats underlying the three Supplementary boundary tables.
- `figure_notes/Table_S_boundaries_notes.md`: declared-boundary, analytical-extent and contextual-jurisdiction definitions, including the San Diego and SDG&E scope distinction.
- `source_data_checks_boundaries.json`: row-scope, numerical-equivalence, San Diego metric and current SI table-number checks.
- `csv/Table_S_solar_resource_14cities.csv`: standardized PVGIS-ERA5 inputs and outputs for the 12 primary cities and supplementary Detroit and Windsor.
- `csv/Table_S_solar_resource_pair_matching.csv`: seven-pair symmetric differences in annual in-plane irradiation and modelled annual PV yield, with study scope and descriptive-screen labels.
- `source_data_checks_solar_resource.json`: query-configuration, scope, numerical-equivalence, pair-screen and current SI table-number checks.
- `figure_notes/Table_S_solar_resource_notes.md`: metric definitions, pairwise calculation, standardized-system limitations and interpretation of the descriptive 5% screen.
- `csv/Table_S_evidence_boundaries.csv`: six-row non-prescriptive matrix distinguishing what each observed or contextual quantity establishes, what it does not establish and the additional evidence needed.

## Also completed

- `csv/Fig_2.csv`: figure-level Source Data for the combined Fig. 2; 36 panel-a city-segment rows and six panel-b pair-attribute rows.
- `csv/Fig_2a.csv` and `csv/Fig_2b.csv`: retained panel-level intermediate tables used to build the combined figure.
- `source_data_checks_fig2.json`: scope and panel-structure checks.
- `figure_notes/Fig_2_notes.md`: panel definitions and manuscript linkage notes.
- `csv/Fig_5.csv`: combined Source Data for the return-friction map, contextual gap scatters, signed metric bars and directional-agreement counts.
- `csv/Fig_5a.csv` to `csv/Fig_5d.csv`: panel-level plotting tables for the six primary pairs.
- `source_data_checks_fig5.json`: scope, San Diego boundary-audited gaps, directional counts, panel labels and bubble-legend checks.
- `figure_notes/Fig_5_notes.md`: direction conventions, overlap between economic and revenue-friction inputs and valid-denominator rules.

All six main-figure packages and the policy, spatial, large-roof, economic-uncertainty and Detroit--Windsor Supplementary figure packages are locked.

## Final submission artifacts

- `Source_Data.xlsx`: one worksheet for every figure-level and panel-level CSV.
- `Source_Data_CSV.zip`: the complete CSV, GeoJSON, notes, checks and manifest package.
- `Supplementary_Tables.xlsx`: machine-readable Supplementary tables collected in one workbook.
- `Supplementary_Tables_CSV.zip`: CSV versions of the Supplementary tables.
- `data_dictionary.csv`: column-level schema, inferred type, unit guidance and example values.
- `source_data_inventory.csv` and `checksums.sha256`: file sizes, row counts and SHA-256 integrity records.

Panel-specific CSV and GeoJSON files are authoritative. The workbooks are convenience containers for journal upload. Source imagery, full third-party building layers and the model checkpoint are not part of Source Data; their redistribution and size constraints are documented in the accompanying public-repository package.

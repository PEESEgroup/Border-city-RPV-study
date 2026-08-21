# Source Data notes for the spatial Supplementary package

The 12-city atlas uses the frozen globally anchored 1 km by 1 km grid in EPSG:6933. Buildings are assigned by representative point, and the complete building footprint and linked rooftop PV area follow the assigned building. Eligible cells contain at least 50 buildings. All 5,238 eligible primary-city cells are plotted, including cells with no mapped rooftop PV.

The atlas uses one fixed bin rule across all cities: zero, greater than 0 to 0.25%, greater than 0.25 to 1%, greater than 1 to 2.5%, greater than 2.5 to 5%, greater than 5 to 10%, and greater than 10% PV utilization. White areas inside a boundary have no eligible cell under the baseline rule. The exact plotted squares are retained in both `csv/Fig_S_grid_atlas.csv` and `spatial/Fig_S_grid_atlas_cells.geojson`.

The sensitivity workflow returns to the building-level geometries and fixes every city's total building-footprint and linked-PV areas to the verified manuscript totals. Resolution checks use 0.5 km, 1 km and 2 km cells. Their minimum building counts are 13, 50 and 200, respectively, which approximately preserve the baseline density requirement of 50 buildings per square kilometre. Origin checks shift the 1 km grid by 0.5 km along x, y or both axes. Eligibility checks use at least 25, 50 or 100 buildings. Boundary-cell checks retain all representative-point-assigned cells at baseline, require the grid-cell center to fall inside the audited boundary, or require at least half of the square area to fall inside the boundary.

Signed gaps are the first-listed city minus the second-listed city. The aggregate citywide gap is unchanged across grid scenarios. A direction disagreement occurs when the median eligible-grid gap and aggregate citywide gap have different signs. Under the baseline, the three disagreements are El Paso--Juarez, Hong Kong--Shenzhen, Monaco--Nice. The sensitivity Source Data retain all six pairs for every scenario, including eligible-cell counts, signed median gaps and pairwise superiority probabilities.

For every city and scenario, the sensitivity workflow also recomputes the percentage of eligible cells with no mapped PV and the percentage of total eligible-cell PV area contained in the fixed highest-utilization group of $\max(1,\lceil0.10n\rceil)$ cells. The resulting ranges are spatial-aggregation sensitivities, not confidence intervals. Monaco has only 2 to 17 eligible cells across the tested definitions and therefore remains explicitly small-denominator.

The maps and sensitivities are descriptive. They show where grid aggregation changes a typical-cell summary and do not identify neighborhood-level causes or policy mechanisms.

Reproduction command from the revision root:

`python code/revision/build_spatial_supplement.py`

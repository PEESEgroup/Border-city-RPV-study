# Source Data notes for the solar-resource audit and pair-matching tables

`csv/Table_S_solar_resource_14cities.csv` reports the common PVGIS-ERA5 query and output fields for the 12 primary cities and supplementary Detroit and Windsor. Each query uses the representative point of the audited analytical boundary, the 2005--2023 database period, 1 kWp of crystalline-silicon capacity, 14% system loss, free-standing mounting and optimum inclination.

Annual in-plane irradiation, `H_i_y_kWh_per_m2_per_year`, and modelled annual electricity output, `E_y_kWh_per_kWp_per_year`, are regional resource diagnostics under one standardized configuration. They do not represent roof-specific orientation, pitch, roof type, shading, obstructions, usable area or system design.

`csv/Table_S_solar_resource_pair_matching.csv` reports the symmetric percentage difference for each metric as `100 * abs(x1 - x2) / ((x1 + x2) / 2)`. `maximum_symmetric_difference_pct` is the larger of the irradiation and yield differences. The 5% screen is a descriptive reporting threshold. It is not a statistical balance test, a case-selection rule or a causal matching criterion.

The six primary pairs appear first in manuscript order. Detroit--Windsor is explicitly labelled as a supplementary sensitivity pair. All seven pairs are within the descriptive 5% screen.

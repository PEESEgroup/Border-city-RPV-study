# Supplementary building-planform and local-context audit Source Data

The four `Fig_S7_building_planform_local_context` CSV files contain the city-level geometry and model-coverage audit, pooled adjusted associations, city-specific adjusted associations and pooled sensitivity results underlying Supplementary Fig. S7 and Table S45.

The analysis covers the 12 primary cities. Planform metrics describe building-footprint polygons and do not measure roof-surface orientation, pitch, material, shading or usable area. Local context contains only building density and total footprint coverage in the globally anchored 1-km grid. Grid-level PV outcomes are excluded from the predictor set.

The prevalence model uses all eligible PV-positive buildings and a reproducible inverse-weighted sample of at most 50,000 PV-negative buildings per city. The conditional-intensity model uses eligible PV-positive buildings. Pooled models adjust for city and harmonized building-use class; city-specific models adjust for building-use class. Effects are descriptive associations per one standard deviation in the corresponding fitted model and should not be interpreted as causal effects or physical roof-suitability estimates.

Individual linked-PV area can exceed assigned footprint area because the manuscript central definition retains complete linked polygons. The sensitivity file reports the model after excluding these conditional-intensity records, and a separate sensitivity excludes Monaco's small sample. All sensitivity coefficient directions match the primary pooled direction.

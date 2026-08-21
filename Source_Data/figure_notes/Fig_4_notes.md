# Source Data notes for Fig. 4

Fig. 4 uses a globally anchored 1 km by 1 km grid in EPSG:6933. Buildings are assigned to grid cells by their representative points. The complete building footprint and linked rooftop PV area follow the assigned building. Boundary-crossing grid cells therefore retain only buildings assigned to the audited city boundary.

Eligible cells contain at least 50 buildings. All eligible cells are retained, including cells with no mapped rooftop PV. Panel a percentiles are calculated across these eligible cells.

For panel c, each signed gap is the first-listed city minus the second-listed city. A positive value indicates that the first-listed city leads. The disagreement flag is generated directly by comparing the signs of the aggregate citywide gap and the median eligible-grid gap.

For panel b, the number of top-decile cells is `max(1, ceil(0.10 × eligible-cell count))`. Cells are ranked by grid-level PV utilization in descending order. Exactly that number of cells is retained. If cells tie at the cutoff, the fixed-size rule is retained rather than expanding the top group to include all ties. The Source Data report the number of tied cells selected and excluded at each cutoff. Monaco has five eligible cells, so its top-decile summary is based on one cell and is marked as a small-denominator result.

The grid summaries describe spatial concentration and heterogeneity. They do not identify policy mechanisms or causal effects.

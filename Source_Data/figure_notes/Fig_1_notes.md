# Fig. 1 Source Data and production notes

## Scope

Fig. 1 contains the six primary pairs only. Detroit--Windsor is excluded from all four panels and is reported as a supplementary candidate-pair sensitivity case.

## Panel a

The displayed totals use 12 primary cities and six primary pairs. The correct unique-image total is 326,790 orthophotos covering 5,812.53 km². The 623 labelled validation tiles are a subset of the source-image corpus and are not added to those totals. Building and PV totals are 4,709,656 buildings, 784.88967 km² of building-footprint area and 19.250827 km² of mapped rooftop PV.

## Panel b

The density surfaces are rendered from footprint-linked rows in each city's `prediction/<city>/processed_on_bldg.geojson`, with city boundaries from `data/boundary/<city>.geojson`. The source plotting implementation is `code/original/plot_pair_heatmap.py`. It projects each pair to a local projected CRS, extracts representative points, bins them on a 280-column grid, applies an 8-pixel Gaussian smoothing parameter and uses a within-pair shared 99.5th-percentile display maximum. Panel b is a rendered geospatial image, so `csv/Fig_1.csv` provides the associated city-level numerical inventory rather than attempting to encode the raster surface as a spreadsheet.

The final data-deposition package should retain either the footprint-linked geospatial inputs or exported density grids if direct numerical reconstruction of the heatmaps is required by the repository or journal.

## Panel c

Panel c is a conceptual analysis diagram. The exact identity is:

`PV utilization = installation prevalence × roof selection × conditional intensity`.

Spatial concentration is evaluated separately using a common 1-km grid. Income ordering, standardized IRR and documented-policy friction are contextual diagnostics rather than terms in the identity or identified causal mechanisms.

## Panel d

Residential versus non-residential leadership direction and the relation between all-building PV leadership and income ordering are evaluated independently. The combinations are descriptive attributes, not mutually exclusive or population-level city types.

## Final production status

The Illustrator composite displays 326,790 orthophotos and 5,813 km² in panel a. The area label is the nearest-square-kilometre rendering of the exact 5,812.53 km² total. Rounded `4.71M buildings` and `785 km² building-footprint` are consistent with the precise caption and Source Data values. Fig. 1 has received final lock status.

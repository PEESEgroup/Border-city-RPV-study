# Source Data notes for the Detroit--Windsor supplementary figure

Detroit--Windsor is a separately reported candidate-pair sensitivity and is not part of the six-pair primary figure set. It is not an external validation, random sample expansion or proof of generalizability.

Panel a uses the same globally anchored 1-km EPSG:6933 grid, at-least-50-buildings eligibility rule and fixed utilization bins as the 12-city atlas. All 395 Detroit and 125 Windsor eligible cells are shown, including zero-PV cells. Buildings are assigned by representative point and complete linked-PV and footprint areas follow the assigned building. Municipal boundaries are shown without assuming equivalence to DTE or ENWIN service territories. Imagery dates are 15 May 2025 and 6 June 2025.

Panel b reports observed PV utilization within the six building-footprint bins used for the primary cities. Utilization is complete linked PV-polygon area divided by building-footprint area within each bin. Windsor leads in every bin; the 1000+ m2 bin is labelled because it contributes most of the citywide gap.

Panel c reports three standardized IRR comparisons. The central row assumes realized capital support for both cities and gives 2.68% for Detroit and 3.01% for Windsor. The no-support row removes the Detroit federal credit and Windsor grant. The mixed row retains the Detroit federal credit and removes the Windsor grant, giving 2.68% versus 0.15% and reversing the ordering. These are scenario diagnostics, not observed project returns or causal explanations of mapped deployment.

Reproduction command from the revision root:

`python code/revision/plot_supp_detroit_windsor.py`

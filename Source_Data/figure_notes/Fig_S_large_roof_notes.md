# Source Data notes for the large-roof Supplementary sensitivity

Panel a reports observed quantities for the 12 primary cities. Large roofs are buildings in the 1000+ m2 footprint bin. Horizontal position is their share of city building-footprint area, vertical position is mapped PV area divided by building-footprint area in that bin, and bubble area represents the share of city mapped PV area located in the bin.

Panel b is an illustrative within-pair benchmark sensitivity. For the city with lower observed large-roof utilization in each primary pair, the calculation replaces that value with the paired city's observed large-roof utilization while holding the city's large-roof footprint share and all other roof-size-bin contributions fixed. The reported change is `large_roof_footprint_share * (paired_observed_large_roof_utilization - current_large_roof_utilization)`.

The benchmark is not a causal counterfactual, policy target or forecast. It does not account for structural suitability, usable roof area, orientation, pitch, shading, ownership, tenancy, onsite load, grid hosting capacity, financing, permitting or siting limits.

Detroit and Windsor are excluded because they are retained as a separate supplementary candidate-pair sensitivity.

Reproduction command from the revision root:

`python code/revision/plot_supp_large_roof_sensitivity.py`

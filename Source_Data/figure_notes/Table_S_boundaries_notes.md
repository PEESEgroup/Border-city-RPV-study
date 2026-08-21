# Source Data notes for the boundary definition, audit and source tables

`csv/Table_S_boundaries.csv` is the common numerical and provenance source for the three boundary tables added to the Supplementary Information. It covers the 12 primary cities and supplementary Detroit and Windsor.

The declared boundary is the administrative, planning-area or urban polygon used as the spatial reference. The analytical mapping extent is the support retained for the mapped outcome after the declared polygon is applied. The contextual jurisdiction is the utility, tariff, programme, state or national unit used for economic or documented-policy context. Contextual jurisdictions are not assumed to be spatially coextensive with the analytical mapping unit.

Building-footprint and linked-PV coverage percentages compare the declared boundary with the transferred city-level analytical files before any required correction. Buildings are assigned by representative-point containment, and the complete footprint and linked PV area follow the assigned building.

San Diego is the only city requiring a material boundary correction. The transferred extent included adjacent municipalities. The revision uses the official City of San Diego polygon and retains 414,749 buildings, 100.816 km2 of building-footprint area and 2.582 km2 of linked PV area. The SDG&E external-calibration registry has a different service and ZIP-based geography and is not used as the mapping boundary.

Blank source URLs for Bratislava and Shenzhen record missing upstream provenance in the transferred files. They are not imputed.

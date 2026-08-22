# The building-level anatomy of rooftop solar deployment gaps across border cities

This repository contains the redistributable numerical data, spatial summary data, validation summaries and analysis code supporting the manuscript **The building-level anatomy of rooftop solar deployment gaps across border cities**.

## Scope

The primary analysis covers 12 cities in six border-city pairs. Detroit–Windsor is retained as a separately reported Supplementary sensitivity. The repository supports numerical verification of all six main figures, all eight Supplementary figures and the machine-readable Supplementary tables. Economic-return and documented-policy indicators are contextual diagnostics, not causal estimates.

## Quick start

```bash
git clone https://github.com/PEESEgroup/Border-city-RPV-study.git
cd Border-city-RPV-study
python scripts/validate_release.py
make source-data
```

`validate_release.py` checks file completeness, row counts, key numerical identities, public-path hygiene and SHA-256 integrity. `make source-data` rebuilds the CSV archives, refreshes their integrity records and validates the retained submission workbooks using only the Python standard library.

## Repository structure

- `Source_Data/`: submission-ready CSV, GeoJSON, XLSX and ZIP Source Data package.
- `tables/`: machine-readable Supplementary tables and the exact TeX table bodies used in the manuscript.
- `evidence/`: frozen analysis inputs and held-out checkpoint evaluation summaries.
- `code/revision/`: production scripts for the revised main and Supplementary panels.
- `code/model/`: model training and checkpoint-evaluation code used for the documented 70/30 tile holdout.
- `figures/`: final vector PDFs used in the clean manuscript.
- `docs/`: data map, reproducibility boundary, external-file register and release audit.

## Source Data

The main submission artifacts are:

- `Source_Data/Source_Data.xlsx`
- `Source_Data/Source_Data_CSV.zip`
- `Source_Data/Supplementary_Tables.xlsx`
- `Source_Data/Supplementary_Tables_CSV.zip`

Panel-specific CSV files remain the authoritative machine-readable records. The workbook is a convenience container. Exact plotted grid squares are supplied as GeoJSON.

## Reproducibility boundary

The repository includes the derived data required to audit the reported values and recreate numerical figure content. It does not redistribute third-party orthophotos, full building-footprint layers or citywide prediction rasters. The 324-MB checkpoint is excluded from Git history because it exceeds GitHub's ordinary single-file limit, but the exact weights are available through the public Google Drive link recorded in `docs/external_files.md`. The register also supplies the filename, byte size and SHA-256 checksum. Full citywide inference therefore requires separately obtained imagery and building data, together with the publicly downloadable checkpoint. This limitation does not affect reproduction of the published numerical figures from the retained Source Data.

Several final composite figures were assembled in Adobe Illustrator from the vector panels. The final PDFs are included as the authoritative publication artwork. Production scripts regenerate their numerical panels, but minor typography and panel placement may differ without the licensed fonts and Illustrator assembly.

## Environment

Python 3.10 or later is recommended. Core figure scripts use pandas, NumPy, Matplotlib, Pillow, GeoPandas, Shapely and PyProj. See `environment.yml` and `requirements.txt`.

## Citation

Please cite the associated paper and this repository release. Citation metadata are provided in `CITATION.cff`.

## Licensing

Code is released under the MIT License. Author-generated tabular Source Data are released under CC BY 4.0, subject to the third-party rights and source terms listed in `DATA_LICENSE.md` and the retained provenance fields.

# Reproducibility levels

## Level 1: publication-number audit

Fully supported within this repository. Run `python scripts/validate_release.py`. This checks the Source Data manifest, figure scopes, row counts, selected numerical identities, spatial-cell completeness and checksums.

## Level 2: panel regeneration

Production scripts and their frozen derived inputs are included under `code/`, `evidence/`, `tables/` and `Source_Data/`. Scripts were retained in the directory structure used during revision. Main Fig. 1 and several final composites contain Illustrator assembly; the authoritative final vector PDFs are supplied under `figures/`.

## Level 3: citywide mapping from source imagery

Not self-contained in GitHub because the orthophotos, full building layers and citywide predictions are external large or third-party files. The 324-MB checkpoint is publicly downloadable from the URL and verifiable checksum in `docs/external_files.md`. Model training and 70/30 held-out evaluation code is included, together with the filtered split index and per-sample test metrics. The paper does not characterize this random-tile holdout as external-domain validation.

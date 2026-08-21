# External and large-file register

## Segmentation checkpoint

Local audit record: cities_12__best_student_dice.pth; 338887653 bytes; SHA-256 `98eee5099afa635790521d4be566a003e40ca11fb3af58a0b83492926c6d2a2c`.

Public checkpoint: [Google Drive](https://drive.google.com/file/d/1tCdqKmuCyQ6fOzdUbIsMxYxciIqYNv1U/view?usp=sharing).

Direct download: [border_checkpoints.pth](https://drive.usercontent.google.com/download?id=1tCdqKmuCyQ6fOzdUbIsMxYxciIqYNv1U&export=download&confirm=t). The public filename differs from the local audit filename, but the uploaded file is byte-for-byte identical to the specified checkpoint. Anonymous download was verified on 21 August 2026. The downloaded object is 338887653 bytes and has SHA-256 `98eee5099afa635790521d4be566a003e40ca11fb3af58a0b83492926c6d2a2c`.

The checkpoint is excluded from this ordinary GitHub archive because it exceeds GitHub's standard 100-MB per-file limit. The recorded filesystem modification time is not used as scientific lineage evidence.

## Inputs not redistributed

- City orthophotos and manual annotation imagery.
- Full city building-footprint layers.
- Citywide segmentation prediction rasters and linked PV polygons.
- Most administrative boundary geometries, except Detroit and Windsor files required by the dedicated Supplementary plotting script.

The repository instead provides building-level aggregates, exact eligible-grid squares, validation summaries and all numerical values plotted in the paper. Source publishers and URLs are documented in the boundary, solar-resource, economic and policy Source Data.

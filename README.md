# Border-city RPV Study

This repository contains the code, processed inputs, manuscript sources, and derived tables used for the border-city rooftop PV study.

## Contents

- `script/`: economic model code, figure-generation scripts, and supplementary asset generation.
- `data/`: processed inputs used by the manuscript figures and tables.
- `figures/`: generated figure assets for the main text and supplementary information.
- `tables/`: generated manuscript tables and table exports.
- `docs/`: manuscript workflow notes, figure mapping, and variable definitions.
- `paper/`: LaTeX sources for the manuscript and supplementary information.

## Reproduce

1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. Regenerate supplementary tables and figures:

```bash
python script/generate_si_assets.py
```

3. Build the manuscript:

```bash
cd paper
pdflatex manuscript.tex
pdflatex supplementary.tex
```

## Notes

- The repository is organized as a manuscript-focused analysis package rather than a standalone Python library.
- Compiled LaTeX build artifacts are ignored via `.gitignore`.

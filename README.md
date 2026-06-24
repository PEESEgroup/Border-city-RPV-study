# Border-city RPV Study

This repository contains the processed data and analysis scripts for the manuscript:

**“Border cities reveal how rooftop solar opportunity becomes urban deployment”**

The repository is provided to support peer review, reporting-summary documentation, and reproducibility of the processed-data analyses reported in the manuscript.

## Overview

This study compares rooftop photovoltaic (RPV) deployment across selected neighboring border-city pairs to examine how rooftop solar opportunity is translated into urban deployment under different local economic, policy, and administrative conditions.

The analyzed city pairs are:

* San Diego, United States — Tijuana, Mexico
* El Paso, United States — Ciudad Juárez, Mexico
* Hong Kong — Shenzhen, China
* Singapore — Johor Bahru, Malaysia
* Vienna, Austria — Bratislava, Slovakia
* Monaco — Nice, France

The repository includes processed rooftop PV/building data, policy-friction scores, city-level economic inputs, and scripts for reproducing the main analytical summaries and figures.

## Repository structure

```text
Border-city-RPV-study/
│
├── data/
│   ├── Building_PVs/        # Processed rooftop PV/building tables and validation summaries
│   ├── PV_Eco_model/        # Processed economic-model inputs and outputs
│   ├── Policy_frictions/    # Policy-friction codebook and scoring tables
│   └── city_economic/       # City-level economic and deployment data
│
├── scripts/
│   ├── econimic_model.py
│   └── plot_*.py            # Figure-generation scripts
│
└── README.md
```

Note: the filename `econimic_model.py` is retained as currently used in the repository.

## Data

The repository contains processed data tables used for the manuscript analyses.

### `data/Building_PVs/`

Processed rooftop PV and building-level summary tables, including city-level image coverage summaries, rooftop PV utilization tables, and validation/benchmark summaries.

### `data/Policy_frictions/`

Policy-friction scoring files used to summarize revenue and administrative barriers to rooftop PV deployment.

The friction indicators are:

* A: Export compensation friction
* B: Export constraint friction
* C: Settlement complexity friction
* D: Policy uncertainty friction
* E: Small-system approval friction
* F: Building/planning approval friction
* G: Grid study/fee friction
* H: Professional credential friction

Each indicator is scored from 0 to 3, where higher values indicate greater friction.

### `data/PV_Eco_model/`

Processed inputs and outputs for the standardized rooftop PV economic model, including assumptions on installed cost, electricity price, export compensation, PV yield, self-consumption, degradation, and O&M.

### `data/city_economic/`

City-level economic and deployment indicators used in the city-pair comparison and figure-generation scripts.

## Software requirements

The analysis scripts are written in Python and require a standard scientific Python environment.

Recommended:

```text
Python >= 3.10
pandas
numpy
matplotlib
pillow
```

Install dependencies with:

```bash
pip install pandas numpy matplotlib pillow
```

## Reproducing the analysis

Clone the repository:

```bash
git clone https://github.com/PEESEgroup/Border-city-RPV-study.git
cd Border-city-RPV-study
```

Run the economic model:

```bash
python scripts/econimic_model.py
```

This generates:

```text
scripts/economic_analysis_results.csv
scripts/economic_figures/
```

The economic model reports standardized city-level rooftop PV metrics, including CAPEX, LCOE, NPV, IRR, simple payback, discounted payback, compensation ratio, and year-1 cash-flow quantities.

To reproduce figures, run the relevant plotting scripts in `scripts/`. For example:

```bash
python scripts/plot_border_city_pv_friction_heatmap.py --help
python scripts/plot_city_rpv_utilization_within_pair_hbar.py --help
python scripts/plot_city_roofsize_pv_adoption.py --help
python scripts/plot_capex_vs_profitability_citypair_scatter.py --help
```

Use the `--help` flag to check the required input and output arguments for each script.

## Reproducibility notes

The included scripts are deterministic when run with the provided processed input tables. No random sampling, stochastic model training, or GPU computation is required for the processed-data analyses included here.

For reproducibility, users are encouraged to record:

```bash
python --version
pip freeze > environment_freeze.txt
git rev-parse HEAD
```

## Scope and limitations

This repository is a trimmed reproducibility package. It includes reusable processed data and code, but does not include all raw upstream materials.

Not included:

* raw high-resolution aerial or satellite imagery;
* trained segmentation checkpoints;
* large intermediate geospatial files;
* provider-restricted datasets that cannot be redistributed;
* raw annotation files if restricted by license or size.

The economic model is intended as a standardized comparative diagnostic across cities, not as site-specific financial advice. Policy-friction scores summarize conditions at the time of analysis and should be updated if regulations change.

## Data and code availability

The processed data and analysis scripts required to reproduce the reported city-level comparisons, policy-friction summaries, economic diagnostics, and figure-generation workflows are available in this repository.

Raw imagery, restricted geospatial data, and model checkpoints are not redistributed because of licensing and file-size constraints. The manuscript and supplementary information describe the data sources, processing procedures, and validation summaries used to generate the processed analytical tables.

## Citation

If using this repository, please cite the associated manuscript:

> [Authors]. “Border cities reveal how rooftop solar opportunity becomes urban deployment.” *Nature Cities*, under review.

Please update this section with the final publication details and DOI after publication.

## License

Please add the appropriate license before public release or archival deposition. Suggested options are MIT License for code and CC BY 4.0 for processed data/documentation, subject to compatibility with upstream data-source terms.

## Contact

For questions about the data, code, or manuscript, please contact the corresponding author listed in the manuscript.

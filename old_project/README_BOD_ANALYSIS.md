# UK Energy System Analysis

This project provides tools for analyzing UK energy system data from Elexon and other sources, focusing on the Balancing Mechanism (BOD) data and generation mix.

## Setup

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Scripts Overview

### BOD Analysis Script

The `bod_analysis.py` script performs analysis on UK energy system data with a focus on balancing mechanism actions. It generates:

- Daily/monthly KPIs
- Wind curtailment metrics
- Price trend charts
- Volume analysis
- Tables with key metrics

The script is designed to work with BigQuery as a data source, but it will create minimal outputs even without access to BigQuery.

### Running the Scripts

Several wrapper scripts are provided for convenience:

1. `run_bod_analysis.sh` - Runs the full analysis including Google Doc report generation
2. `run_bod_analysis_no_gdoc.sh` - Runs the analysis but skips Google Doc report generation
3. `run_bod_analysis_with_dates.sh` - Runs the analysis for a specific date range with options to include/exclude Google Doc report

### Command-line Arguments

The `bod_analysis.py` script now accepts the following command-line arguments:

- `--no-gdoc` - Skip Google Doc report generation
- `--start-date YYYY-MM-DD` - Specify the start date for the analysis
- `--end-date YYYY-MM-DD` - Specify the end date for the analysis

## Requirements

- Python 3.6+
- BigQuery access (for full functionality)
- Google Cloud authentication (for Google Doc reports)
- Required Python packages (installed in a virtual environment):
  - google-cloud-bigquery
  - google-auth
  - google-auth-oauthlib
  - google-auth-httplib2
  - google-api-python-client
  - pandas
  - numpy
  - matplotlib
  - python-dateutil
  - tenacity
  - tqdm
  - pyarrow

## Usage

To run the BOD analysis:

```bash
# Run full analysis including Google Doc generation
./run_bod_analysis.sh

# Run analysis without Google Doc generation (simpler)
./run_bod_analysis_no_gdoc.sh

# Run analysis for a specific date range
./run_bod_analysis_with_dates.sh --start-date 2020-01-01 --end-date 2025-08-23 --no-gdoc
```

## Output

The analysis generates the following outputs:

- `./out/kpi_summary.txt` - Human-readable summary of key metrics
- `./out/charts/` - Generated charts in PNG format
- `./out/tables/` - CSV files with detailed data

## Data Type Handling

The script handles data type conversions automatically to ensure consistent merging of dataframes. Date fields are converted to consistent types before merge operations to prevent errors.

## Troubleshooting

- If you see errors about missing credentials, ensure your Google Cloud credentials are properly set up
- If you get errors about merging dataframes with different data types, check that the latest version of the script is being used
- For Google Doc creation issues, use the `--no-gdoc` flag to skip that part of the process

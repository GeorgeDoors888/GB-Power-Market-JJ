# Automated UK Energy Data Tools

This document provides instructions for using the automated tools to generate test data, run analyses, and launch dashboards without requiring manual approvals at each step.

## Table of Contents

1. [Overview](#overview)
2. [Automated Test Data Generation](#automated-test-data-generation)
3. [Automated Pipeline](#automated-pipeline)
4. [Command Reference](#command-reference)
5. [FAQ](#faq)

## Overview

These tools help automate the UK Energy data pipeline by:

1. Generating test data with tracking to avoid redundant operations
2. Running analysis without requiring manual confirmation
3. Launching dashboards automatically
4. Tracking operations to avoid repetition

## Automated Test Data Generation

The `generate_test_data_automated.py` script generates test data for BigQuery tables, with several improvements over the original script:

- **Status Tracking**: Keeps track of what data has been generated to avoid regenerating unnecessarily
- **No Prompts**: Can run completely without user interaction
- **Selective Generation**: Generate data only for specific tables
- **Date Range Control**: Specify custom date ranges

### Quick Usage

To generate data for all tables without any prompts:

```bash
./auto_generate_data.sh
```

This will:
1. Check what data already exists
2. Only generate missing data
3. Save a status file for tracking

### Advanced Usage

```bash
./auto_generate_data.sh --force --tables neso_wind_forecasts neso_carbon_intensity --days 30 --start-date 2024-01-01
```

This will:
1. Force regeneration of data even if it exists (`--force`)
2. Only generate data for the specified tables (`--tables`)
3. Generate 30 days of data (`--days`) starting from Jan 1, 2024 (`--start-date`)

## Automated Pipeline

The `run_automated_pipeline.sh` script automates the entire pipeline from data generation to dashboard launch:

1. Generates test data if needed
2. Runs analysis on the data
3. Launches the dashboard
4. All without requiring manual approval

### Quick Usage

To run the entire pipeline with default settings:

```bash
./run_automated_pipeline.sh
```

### Advanced Usage

```bash
./run_automated_pipeline.sh --regenerate-data --skip-analysis
```

This will:
1. Force regeneration of all data (`--regenerate-data`)
2. Skip the analysis step (`--skip-analysis`)
3. Launch the dashboard

## Command Reference

### Auto Generate Data

```
./auto_generate_data.sh [OPTIONS]

Options:
  --force           Regenerate all data even if it already exists
  --tables TABLE1 TABLE2...
                    Only generate data for these specific tables
  --days N          Generate N days of data
  --start-date DATE Start date in YYYY-MM-DD format
  --end-date DATE   End date in YYYY-MM-DD format
```

### Run Automated Pipeline

```
./run_automated_pipeline.sh [OPTIONS]

Options:
  --regenerate-data Force regeneration of all data
  --skip-analysis   Skip the data analysis step
  --skip-dashboard  Don't launch the dashboard
```

## FAQ

### Why was this automation created?

To eliminate the need for repetitive manual approvals during the data generation, analysis, and dashboard launch process.

### How does the system track what data has been generated?

It creates a JSON status file that records:
- Which tables have been generated
- The date range of generated data
- When the generation occurred
- How many rows were generated

### How can I force regeneration of all data?

Use the `--force` flag with either script:
```bash
./auto_generate_data.sh --force
```
or
```bash
./run_automated_pipeline.sh --regenerate-data
```

### What tables can be generated?

The following tables are supported:
- neso_demand_forecasts
- neso_wind_forecasts
- neso_balancing_services
- neso_carbon_intensity
- neso_interconnector_flows
- elexon_system_warnings

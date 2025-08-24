# UK Energy Data Investigation Tools

This repository contains tools for investigating, analyzing, and loading UK energy data from 2016 to the present. These tools were created to address a discrepancy between documented data range (2016-2025) and the actual data available in BigQuery tables (primarily 2023-2024).

## Investigation Findings

1. **Data Range Discrepancy**:  
   - Documentation claims data from 2016-2025
   - Most BigQuery tables only contain data from 2023-2024
   - Only two tables contain any 2016 data, and only for Jan 1-8, 2016

2. **Data Location**:  
   - Found historical data (2016-2022) in the `elexon-historical-data-storage` GCS bucket
   - BigQuery tables are missing most of this historical data

3. **Recommended Action**:  
   - Load the historical data from GCS to BigQuery using the provided tools

## Tools Overview

### 1. `check_date_ranges_2016_to_present.py`

A script to check for data ranges from 2016 to the present day in BigQuery tables.

**Usage:**

```bash
python check_date_ranges_2016_to_present.py
```

**Features:**

- Scans all UK energy datasets in BigQuery
- Identifies tables with 2016 data
- Reports date ranges for all tables
- Generates JSON and Markdown reports

### 2. `scan_gcs_for_historical_data.py`

A script to scan Google Cloud Storage buckets for historical data files from 2016-2022.

**Usage:**

```bash
python scan_gcs_for_historical_data.py
```

**Features:**

- Scans all buckets in the project
- Identifies buckets containing NESO and Elexon data
- Reports files by year (2016-2022)
- Generates JSON and Markdown reports

### 3. `gcs_to_bq_loader.py`

A script to assist with loading historical data from GCS to BigQuery.

**Usage:**

```bash
python gcs_to_bq_loader.py --bucket elexon-historical-data-storage
```

**Features:**

- Maps GCS file categories to BigQuery tables
- Generates loading plans
- Creates validation queries
- Produces detailed loading instructions

### 4. `load_2016_data.py`

A specific script to load 2016 data from GCS to BigQuery.

**Usage:**

```bash
python load_2016_data.py
```

**Features:**

- Directly loads 2016 data from the `elexon-historical-data-storage` bucket
- Maps specific data types to appropriate BigQuery tables
- Validates loaded data
- Provides detailed loading progress

## Reports

The investigation generated several reports:

1. `UK_ENERGY_DATA_INVESTIGATION_REPORT.md` - Comprehensive findings and recommendations
2. `uk_energy_date_ranges_*.md` - BigQuery table date range analysis
3. `gcs_historical_data_scan_*.md` - GCS bucket analysis for historical data
4. `loading_plan_plan_*.md` - Data loading plans and instructions

## Next Steps

1. Review the generated reports to understand the current data situation
2. Run the `load_2016_data.py` script to load the 2016 data to BigQuery
3. Use the loading plans to load the remaining historical data (2017-2022)
4. Update documentation to reflect the actual data availability

## Prerequisites

- Google Cloud SDK installed and authenticated
- Access to the BigQuery datasets and GCS buckets
- Python 3.7+ with the following packages:
  - google-cloud-bigquery
  - google-cloud-storage

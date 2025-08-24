# Elexon Data Loading Solution

## Overview

This document outlines the solution for loading the missing Elexon datasets from Google Cloud Storage (GCS) to BigQuery. The issue was identified in the comprehensive BigQuery summary, which showed only 9 Elexon tables in BigQuery despite the expectation of having 54 datasets available.

## Problem Identified

1. The data exists in GCS buckets but hasn't been fully loaded to BigQuery
2. Several key Elexon datasets were missing from BigQuery, including:
   - `elexon_bid_offer_acceptances`
   - `elexon_generation_outturn`
   - `elexon_demand_outturn`
   - `elexon_system_warnings`
   - `elexon_frequency`

## Solution

Two new scripts have been created to address this issue:

1. `load_elexon_data.py` - A Python script designed to load Elexon data from GCS to BigQuery
2. `load_elexon_data.sh` - A shell script wrapper that provides an interactive interface for the Python script

### How the Solution Works

The solution works by:

1. Reading JSON files from GCS buckets where the Elexon data is stored
2. Loading the data directly into BigQuery tables with the appropriate schemas
3. Performing comprehensive data quality and accuracy validation:
   - Row count verification
   - Null value detection in critical columns
   - Date range coverage analysis
   - Continuity checks to identify significant gaps in time series data

This validation ensures that the loaded data meets quality standards before being used in dashboards or analytics.

### Using the Solution

To use the solution, run the shell script:

```bash
./load_elexon_data.sh
```

This will:

1. Check authentication
2. Prompt for which dataset(s) to load
3. Ask for date filtering options
4. Load the data to BigQuery
5. Validate the load was successful

For more advanced usage, you can run the Python script directly:

```bash
./load_elexon_data.py --data-type bid_offer_acceptances --start-date 2025-01-01
```

### Data Mapping

The solution includes the following data mappings:

| Data Type | GCS Prefix | BigQuery Table |
|-----------|------------|----------------|
| bid_offer_acceptances | bmrs_data/bid_offer_acceptances/ | elexon_bid_offer_acceptances |
| generation_outturn | bmrs_data/generation_outturn/ | elexon_generation_outturn |
| demand_outturn | bmrs_data/demand_outturn/ | elexon_demand_outturn |
| system_warnings | bmrs_data/system_warnings/ | elexon_system_warnings |
| frequency | bmrs_data/frequency/ | elexon_frequency |

### Data Quality and Accuracy Validation

After loading data to BigQuery, the solution performs several validation checks to ensure data quality and accuracy:

1. **Basic Validation**:
   - Confirms that rows were successfully loaded
   - Verifies the total row count against expectations

2. **Critical Column Analysis**:
   - Checks for null values in critical columns for each dataset
   - Alerts if more than 10% of values are null in any critical column
   - Dataset-specific critical columns include:
     - **bid_offer_acceptances**: settlement_date, settlement_period, bmu_id
     - **generation_outturn**: settlement_date, settlement_period, demand
     - **demand_outturn**: settlement_date, settlement_period, initial_demand_outturn
     - **system_warnings**: published_time, warning_type, message
     - **frequency**: timestamp, frequency

3. **Date Range and Continuity Analysis**:
   - Verifies the date range coverage (min date, max date)
   - Counts unique dates to understand the density of the data
   - For longer periods (>30 days), performs continuity checks to identify gaps
   - Reports missing dates that might indicate data collection issues

4. **Validation Reporting**:
   - All validation results are logged for review
   - Warnings are issued for potential data quality issues
   - Summary statistics are provided for each dataset

These validation steps ensure that the data is not only loaded but is also of sufficient quality for analysis and visualization in dashboards.

## Additional Information

1. The data in GCS is stored in JSON format with a structure that includes:
   - A `data` array containing the actual records
   - Metadata such as `date`, `data_type`, and `record_count`

2. The script handles date filtering to allow loading specific date ranges

3. Validation is performed after loading to ensure data integrity

## Future Enhancements

1. Add support for more Elexon datasets as they become available
2. Implement incremental loading to avoid processing the same files multiple times
3. Expand quality validation with additional metrics:
   - Anomaly detection for extreme values
   - Statistical distribution analysis
   - Consistency checks between related datasets
4. Create scheduled jobs to automatically load new data as it arrives in GCS
5. Add data lineage tracking to maintain audit trails of data transformations

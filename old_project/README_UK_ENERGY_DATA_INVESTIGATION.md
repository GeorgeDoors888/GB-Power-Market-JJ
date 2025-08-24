# UK Energy Data Range Investigation

## Summary

This repository contains tools and reports created to investigate the discrepancy between documented data ranges (2016-2025) and actual available data in BigQuery (primarily 2023-2024).

## Key Findings

1. **Data Range Discrepancy**: There is a significant gap between documented data range (2016-2025) and what's actually available in BigQuery tables (primarily 2023-2024).

2. **2016 Data Status**:
   - Only 2 BigQuery tables contain 2016 data: `elexon_fuel_generation` tables in both `uk_energy_data` and `uk_energy_data_gemini_eu` datasets
   - The 2016 data is limited to January 1-8, 2016 (just one week)

3. **GCS Storage Findings**:
   - Discovered historical data in the `elexon-historical-data-storage` bucket
   - Files exist for all years from 2016-2022
   - For 2016, we found both demand and frequency data files

## Reports

- `UK_ENERGY_DATA_INVESTIGATION_REPORT.md`: Comprehensive report detailing all findings and recommendations
- `uk_energy_date_ranges_*.md`: Date range analysis of all BigQuery tables
- `gcs_historical_data_scan_*.md`: Analysis of historical data found in GCS buckets

## Tools

This repository includes several tools created to investigate the data range issue:

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
python gcs_to_bq_loader.py --year 2016 --bucket elexon-historical-data-storage
```

**Features:**

- Maps GCS file categories to BigQuery tables
- Generates loading plans
- Creates validation queries
- Produces detailed loading instructions

## Next Steps

1. Review the comprehensive investigation report in `UK_ENERGY_DATA_INVESTIGATION_REPORT.md`
2. Use `gcs_to_bq_loader.py` to generate loading plans for historical data
3. Execute the loading plans to backfill BigQuery with historical data
4. Update documentation to accurately reflect data availability

## Contact

For questions or assistance with this investigation, please contact the Data Engineering team.

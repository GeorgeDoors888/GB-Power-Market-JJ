# Year-Specific Schema Support for Elexon Ingestion

This document explains how to use year-specific schemas with the `ingest_elexon_fixed.py` script to handle different schema structures across different years of Elexon data.

## Background

The Elexon API schema has evolved over time, resulting in different column structures for different years of data. This can cause issues when using staging tables, as the script tries to use the current schema for historical data.

## Solution

We've enhanced the ingestion script to support year-specific schemas:

1. **Modified the staging table logic** to detect the year of the data being processed and use the appropriate schema.
2. **Created a schema generation tool** to extract schemas from existing data in BigQuery or from API samples.
3. **Organized schemas by year** in a directory structure: `schemas/YYYY/bmrs_dataset.json`.

## How to Use

### Step 1: Generate Year-Specific Schemas

If you already have data in BigQuery for previous years, use the schema extraction tool:

```bash
python generate_schemas_from_bigquery.py --project jibber-jabber-knowledge --dataset uk_energy_insights --years 2022 2023 2024 --copy-current
```

This will:
- Connect to your BigQuery dataset
- Extract sample data for each year and dataset
- Generate schema files in the `schemas/YYYY/` directories
- Fall back to the current schema for years with no data (with `--copy-current`)

### Step 2: Run the Enhanced Ingest Script

When running the ingestion script, it will automatically:
1. Detect the year of the data being processed
2. Look for a year-specific schema file
3. Use the appropriate schema for the staging table
4. Fall back to the default schema if no year-specific schema exists

```bash
python ingest_elexon_fixed.py --start 2022-01-01 --end 2022-04-01 --use-staging-table --batch-size 20 --log-level INFO --log-file 2022_q1_ingest.log --skip-existing
```

### Step 3: Monitor and Fine-tune

If schema mismatches still occur:
1. Check the logs for details about which columns are causing issues
2. Update the year-specific schema files manually if needed
3. Retry the ingestion

## Schema Directory Structure

```
schemas/
  ├── 2022/
  │   ├── bmrs_bod.json
  │   ├── bmrs_freq.json
  │   └── ...
  ├── 2023/
  │   ├── bmrs_bod.json
  │   ├── bmrs_freq.json
  │   └── ...
  └── 2024/
      ├── bmrs_bod.json
      ├── bmrs_freq.json
      └── ...
```

## Troubleshooting

If you encounter schema issues:

1. **Disable staging tables**: Use `--no-staging-table` to avoid schema issues entirely
2. **Check schema files**: Ensure the year-specific schema file matches the data structure
3. **Update schemas**: Manually edit the schema files to match the actual column structure
4. **Process one year at a time**: Process data year by year to avoid mixed schemas

## Additional Options

- **Process by Dataset**: Use `--only DATASET1,DATASET2` to process one dataset at a time
- **Skip Existing Data**: Use `--skip-existing` to avoid reprocessing data that's already in BigQuery
- **Direct Loading**: If staging tables still cause issues, use `--no-staging-table` for reliable direct loading

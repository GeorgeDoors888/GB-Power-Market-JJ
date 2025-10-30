# Year-Specific Schema Handling Guide

This guide explains how to use the year-specific schema handling system for Elexon BMRS data ingestion.

## Overview

The Elexon BMRS data schemas have evolved over time. Specifically, there are significant differences between 2022-2024 and 2025 schemas:

1. **2022-2024 Schemas**: Include additional metadata fields like `_source_columns`, `_source_api`, `_hash_source_cols`, and `_hash_key`.
2. **2025 Schemas**: Have simplified metadata with fewer fields.

To handle these differences, we've implemented a year-specific schema system that automatically selects the appropriate schema based on the data being processed.

## Key Components

The system consists of the following components:

1. **Schema Directory Structure**: Organized by year and dataset:
   ```
   schemas/
   ├── 2022/
   │   ├── bmrs_bod.json
   │   ├── bmrs_freq.json
   │   └── ...
   ├── 2023/
   │   ├── bmrs_bod.json
   │   └── ...
   ├── 2024/
   │   └── ...
   └── 2025/
       └── ...
   ```

2. **Schema Handler Module**: The `schema_handler.py` module provides functions for working with year-specific schemas:
   - `get_schema_for_dataset_and_year(dataset, year)`: Gets the schema for a specific dataset and year
   - `get_schema_year_from_date(date_str)`: Extracts the year from a date string
   - Plus additional utility functions for schema management

3. **Updated Ingestion Script**: The `ingest_elexon_fixed.py` script has been modified to use the schema handler to automatically select the appropriate schema based on the data being processed.

4. **Ingestion Runner Script**: The `run_ingestion_with_schemas.py` script provides a convenient way to run ingestion jobs with appropriate year-specific schemas.

## How to Use

### Ingesting Data for Specific Years

To ingest data for a specific year or date range, use the `run_ingestion_with_schemas.py` script:

```bash
# Ingest all datasets for January 2022
python run_ingestion_with_schemas.py --start 2022-01-01 --end 2022-01-31

# Ingest specific datasets for all of 2023
python run_ingestion_with_schemas.py --year 2023 --datasets BOD,FREQ,FUELINST

# Ingest all datasets for multiple years
python run_ingestion_with_schemas.py --years 2022,2023,2024 --datasets ALL

# Ingest data for a specific month
python run_ingestion_with_schemas.py --year 2022 --month 3 --datasets BOD,FREQ
```

The script will automatically select the appropriate schema based on the date range.

### Adding New Schemas

If you need to add a new schema for a dataset and year:

1. Create a JSON file in the appropriate year directory:
   ```
   schemas/YYYY/bmrs_DATASET.json
   ```

2. Follow the existing schema format with appropriate fields.

3. Alternatively, use the schema handler to automatically generate schemas:
   ```python
   from schema_handler import adapt_schema_for_year, save_schema

   # Example: Create a 2023 schema based on a 2025 schema
   schema_2025 = get_schema_for_dataset_and_year('BOD', 2025)
   schema_2023 = adapt_schema_for_year(schema_2025, 2023)
   save_schema(schema_2023, 'schemas/2023/bmrs_bod.json')
   ```

### Schema Fallback Mechanism

The system includes a fallback mechanism:

1. It first tries to find an exact schema match for the dataset and year.
2. If not found, it uses a reference year (2022 for years ≤ 2022, 2024 for 2023-2024, 2025 for years ≥ 2025).
3. It then adapts the schema to the appropriate format based on the year.

This ensures that even if a specific schema file doesn't exist, the system can still generate an appropriate schema.

## Schema Patterns

The system recognizes two main schema patterns:

1. **Extended Schema** (2022-2024): Includes all 7 metadata fields:
   - `_dataset`
   - `_window_from_utc`
   - `_window_to_utc`
   - `_ingested_utc`
   - `_source_columns`
   - `_source_api`
   - `_hash_source_cols`
   - `_hash_key`

2. **Simple Schema** (2025+): Includes only 4 metadata fields:
   - `_dataset`
   - `_window_from_utc`
   - `_window_to_utc`
   - `_ingested_utc`

All business data fields remain consistent across years.

## Troubleshooting

If you encounter issues with schema handling:

1. **Schema Not Found**: Check that the appropriate schema file exists in the correct directory.

2. **Year Detection Issues**: The system tries to detect the year from date fields in the data. If this fails, it falls back to the current year. You can manually specify the year using command-line arguments.

3. **Schema Mismatch**: If you still encounter schema mismatch errors, check the schema files to ensure they match the actual data structure.

## Additional Resources

For more information, refer to:

- `ELEXON_DATASET_COLUMN_FORMATS.md`: Details on 2025 dataset schemas
- `ELEXON_DATASET_COLUMN_FORMATS_2022_2024.md`: Details on 2022-2024 dataset schemas
- `schema_handler.py`: Documentation on schema handling functions

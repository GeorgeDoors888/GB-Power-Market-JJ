# Elexon BMRS Datasets Report (2022-2024)

This report provides detailed information about the Elexon BMRS datasets for years 2022, 2023, and 2024, with special focus on schema differences compared to 2025.

## Overview

The Elexon Balancing Mechanism Reporting Service (BMRS) provides a variety of datasets related to the UK electricity market. This report documents the structure of these datasets as ingested in years 2022-2024, focusing particularly on schema differences compared to 2025.

## Schema Evolution Pattern

After analyzing the schemas for multiple datasets across 2022-2025, a clear pattern emerges:

1. **2022-2024 Schemas**: Include additional metadata fields not present in 2025
2. **2025 Schemas**: Have simplified metadata with fewer fields

## Common Schema Differences

The schemas from 2022-2024 consistently include these additional metadata fields compared to 2025:

| Field Name          | Type   | Present in 2022-2024 | Present in 2025 |
| ------------------- | ------ | -------------------- | --------------- |
| `_source_columns`   | STRING | ✓                    | ✗               |
| `_source_api`       | STRING | ✓                    | ✗               |
| `_hash_source_cols` | STRING | ✓                    | ✗               |
| `_hash_key`         | STRING | ✓                    | ✗               |

The standard metadata fields present in ALL years (2022-2025) are:

| Field Name         | Type   | Description                 |
| ------------------ | ------ | --------------------------- |
| `_dataset`         | STRING | Internal dataset identifier |
| `_window_from_utc` | STRING | Start of data window        |
| `_window_to_utc`   | STRING | End of data window          |
| `_ingested_utc`    | STRING | Timestamp of ingestion      |

## Datetime Format Standards

Time-related fields in Elexon datasets follow consistent formats across 2022-2025:

- **ISO-8601 with timezone**: `YYYY-MM-DDThh:mm:ss.sssZ` (e.g., "2022-01-01T00:00:00.000Z")
- **Settlement Date**: `YYYY-MM-DD` (e.g., "2022-01-01")
- **Time Windows**: Pairs of fields (e.g., `timeFrom`/`timeTo`) in ISO-8601 format

## Dataset-Specific Observations

### 1. FREQ (System Frequency)

The FREQ dataset has a consistent structure across 2022-2025 for business fields, with only metadata differences:

| Field Name        | Type   | 2022-2024    | 2025          |
| ----------------- | ------ | ------------ | ------------- |
| `dataset`         | STRING | ✓            | ✓             |
| `measurementTime` | STRING | ✓            | ✓             |
| `frequency`       | FLOAT  | ✓            | ✓             |
| Metadata fields   | STRING | All 7 fields | Only 4 fields |

### 2. FUELINST (Fuel Instruction)

The FUELINST dataset has consistent business fields across all years:

| Field Name         | Type    | 2022-2024    | 2025          |
| ------------------ | ------- | ------------ | ------------- |
| `dataset`          | STRING  | ✓            | ✓             |
| `publishTime`      | STRING  | ✓            | ✓             |
| `startTime`        | STRING  | ✓            | ✓             |
| `settlementDate`   | STRING  | ✓            | ✓             |
| `settlementPeriod` | INTEGER | ✓            | ✓             |
| `fuelType`         | STRING  | ✓            | ✓             |
| `generation`       | INTEGER | ✓            | ✓             |
| Metadata fields    | STRING  | All 7 fields | Only 4 fields |

### 3. BOD (Bid-Offer Data)

The BOD dataset maintains consistent business fields across all years:

| Field Name           | Type    | 2022-2024    | 2025          |
| -------------------- | ------- | ------------ | ------------- |
| `dataset`            | STRING  | ✓            | ✓             |
| `settlementDate`     | STRING  | ✓            | ✓             |
| `settlementPeriod`   | INTEGER | ✓            | ✓             |
| `timeFrom`           | STRING  | ✓            | ✓             |
| `levelFrom`          | INTEGER | ✓            | ✓             |
| `timeTo`             | STRING  | ✓            | ✓             |
| `levelTo`            | INTEGER | ✓            | ✓             |
| `pairId`             | INTEGER | ✓            | ✓             |
| `offer`              | FLOAT   | ✓            | ✓             |
| `bid`                | FLOAT   | ✓            | ✓             |
| `nationalGridBmUnit` | STRING  | ✓            | ✓             |
| `bmUnit`             | STRING  | ✓            | ✓             |
| Metadata fields      | STRING  | All 7 fields | Only 4 fields |

### 4. BOALF (Bid-Offer Acceptance Level Flow)

The BOALF dataset also shows the same metadata pattern with business fields remaining consistent:

| Field Name          | Type    | 2022-2024    | 2025          |
| ------------------- | ------- | ------------ | ------------- |
| All business fields | Various | ✓            | ✓             |
| Metadata fields     | STRING  | All 7 fields | Only 4 fields |

### 5. MELS (Maximum Export Limit)

The MELS dataset has consistent business fields across all years:

| Field Name          | Type    | 2022-2024    | 2025          |
| ------------------- | ------- | ------------ | ------------- |
| All business fields | Various | ✓            | ✓             |
| Metadata fields     | STRING  | All 7 fields | Only 4 fields |

### 6. MID (Market Index Data)

The MID dataset maintains the same pattern:

| Field Name          | Type    | 2022-2024    | 2025          |
| ------------------- | ------- | ------------ | ------------- |
| All business fields | Various | ✓            | ✓             |
| Metadata fields     | STRING  | All 7 fields | Only 4 fields |

## Impact on Data Processing

The schema differences between 2022-2024 and 2025 have the following implications:

1. **Schema Validation**: The difference in column count causes schema validation errors when trying to use a schema from one period for data from another period.

2. **BigQuery Loading**: When using staging tables with schema validation, the column count mismatch leads to load failures.

3. **Data Consistency**: While business fields remain consistent, metadata handling changed from 2024 to 2025.

## Recommended Data Processing Approach

To handle these differences effectively:

1. **Year-specific Schemas**: Use separate schema files for each year, as you have done with your `schemas/YYYY/` directory structure.

2. **Schema Loader Logic**: Implement a schema selection mechanism that chooses the appropriate schema based on the data's year.

3. **Schema Compatibility Check**: For datasets where schemas haven't been explicitly defined for certain years, implement a fallback mechanism:
   - For 2022-2023 data, use 2022 schemas
   - For 2024 data, use 2024 schemas
   - For 2025 data, use 2025 schemas

4. **Field Mapping**: If necessary, create a mapping layer that standardizes the schema differences during processing.

## Conclusion

The Elexon BMRS data schemas have evolved between 2022-2024 and 2025, primarily in their metadata fields. While the business data fields remain consistent, the inclusion of additional metadata fields in 2022-2024 creates a schema mismatch that requires special handling in data processing pipelines. By using year-specific schema definitions, these differences can be effectively managed to ensure successful data ingestion and processing.

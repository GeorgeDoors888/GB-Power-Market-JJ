# Elexon BMRS Datasets Report (2025)

This report provides detailed information about all 56 Elexon BMRS datasets, with special focus on column headers and datetime formatting.

## Overview

The Elexon Balancing Mechanism Reporting Service (BMRS) provides a variety of datasets related to the UK electricity market. This report documents the structure of these datasets as ingested in 2025, with particular attention to how datetime fields are formatted.

## Common Patterns

Most datasets follow these common patterns:

1. **Date/Time Fields**: Typically stored as STRING type in BigQuery but with specific ISO-8601 formats
2. **Metadata Fields**: All datasets include fields with prefix `_` for tracking purposes
3. **Primary Key Construction**: Most datasets use a combination of datetime fields and identifiers for uniqueness

## Datetime Format Standards

Time-related fields in Elexon datasets generally follow these formats:

- **ISO-8601 with timezone**: `YYYY-MM-DDThh:mm:ss.sssZ` (e.g., "2025-08-28T00:00:00.000Z")
- **Settlement Date**: `YYYY-MM-DD` (e.g., "2025-08-28")
- **Time Windows**: Pairs of fields (e.g., `timeFrom`/`timeTo`) in ISO-8601 format

## Common Metadata Fields

All datasets include these metadata fields:

| Field Name          | Type   | Description                 | Format Example             |
| ------------------- | ------ | --------------------------- | -------------------------- |
| `_dataset`          | STRING | Internal dataset identifier | "FREQ", "BOD", etc.        |
| `_window_from_utc`  | STRING | Start of data window        | "2025-08-28T00:00:00.000Z" |
| `_window_to_utc`    | STRING | End of data window          | "2025-08-28T01:00:00.000Z" |
| `_ingested_utc`     | STRING | Timestamp of ingestion      | "2025-09-18T10:54:37.428Z" |
| `_source_columns`   | STRING | Original column names       | "dataset,publishTime,..."  |
| `_source_api`       | STRING | API source                  | "BMRS"                     |
| `_hash_source_cols` | STRING | Columns used for hash       | "dataset,publishTime,..."  |
| `_hash_key`         | STRING | Uniqueness hash             | "a1b2c3d4..."              |

## Detailed Dataset Schemas

### 1. BOD (Bid-Offer Data)

Bid-Offer Data contains information about bids and offers submitted by market participants.

| Field Name           | Type    | Format/Values              | Notes                  |
| -------------------- | ------- | -------------------------- | ---------------------- |
| `dataset`            | STRING  | "BOD"                      |                        |
| `settlementDate`     | STRING  | "YYYY-MM-DD"               |                        |
| `settlementPeriod`   | INTEGER | 1-48                       |                        |
| `timeFrom`           | STRING  | "YYYY-MM-DDThh:mm:ssZ"     | ISO-8601 with timezone |
| `levelFrom`          | INTEGER |                            |                        |
| `timeTo`             | STRING  | "YYYY-MM-DDThh:mm:ssZ"     | ISO-8601 with timezone |
| `levelTo`            | INTEGER |                            |                        |
| `pairId`             | INTEGER |                            |                        |
| `offer`              | FLOAT   |                            | Price in £/MWh         |
| `bid`                | FLOAT   |                            | Price in £/MWh         |
| `nationalGridBmUnit` | STRING  |                            |                        |
| `bmUnit`             | STRING  |                            |                        |
| `_dataset`           | STRING  | "BOD"                      |                        |
| `_window_from_utc`   | STRING  | "YYYY-MM-DDThh:mm:ss.sssZ" | ISO-8601 with timezone |
| `_window_to_utc`     | STRING  | "YYYY-MM-DDThh:mm:ss.sssZ" | ISO-8601 with timezone |
| `_ingested_utc`      | STRING  | "YYYY-MM-DDThh:mm:ss.sssZ" | ISO-8601 with timezone |

### 2. FREQ (System Frequency)

System Frequency data provides the real-time frequency of the electricity grid.

| Field Name         | Type   | Format/Values              | Notes                  |
| ------------------ | ------ | -------------------------- | ---------------------- |
| `dataset`          | STRING | "FREQ"                     |                        |
| `measurementTime`  | STRING | "YYYY-MM-DDThh:mm:ssZ"     | ISO-8601 with timezone |
| `frequency`        | FLOAT  |                            | In Hertz               |
| `_dataset`         | STRING | "FREQ"                     |                        |
| `_window_from_utc` | STRING | "YYYY-MM-DDThh:mm:ss.sssZ" | ISO-8601 with timezone |
| `_window_to_utc`   | STRING | "YYYY-MM-DDThh:mm:ss.sssZ" | ISO-8601 with timezone |
| `_ingested_utc`    | STRING | "YYYY-MM-DDThh:mm:ss.sssZ" | ISO-8601 with timezone |

### 3. FUELINST (Fuel Instruction)

Fuel Instruction data provides generation by fuel type at 5-minute intervals.

| Field Name         | Type    | Format/Values              | Notes                      |
| ------------------ | ------- | -------------------------- | -------------------------- |
| `dataset`          | STRING  | "FUELINST"                 |                            |
| `publishTime`      | STRING  | "YYYY-MM-DDThh:mm:ssZ"     | ISO-8601 with timezone     |
| `startTime`        | STRING  | "YYYY-MM-DDThh:mm:ssZ"     | ISO-8601 with timezone     |
| `settlementDate`   | STRING  | "YYYY-MM-DD"               |                            |
| `settlementPeriod` | INTEGER | 1-48                       |                            |
| `fuelType`         | STRING  |                            | e.g., "CCGT", "WIND", etc. |
| `generation`       | INTEGER |                            | In MW                      |
| `_dataset`         | STRING  | "FUELINST"                 |                            |
| `_window_from_utc` | STRING  | "YYYY-MM-DDThh:mm:ss.sssZ" | ISO-8601 with timezone     |
| `_window_to_utc`   | STRING  | "YYYY-MM-DDThh:mm:ss.sssZ" | ISO-8601 with timezone     |
| `_ingested_utc`    | STRING  | "YYYY-MM-DDThh:mm:ss.sssZ" | ISO-8601 with timezone     |

### 4. BOALF (Bid-Offer Acceptance Level Flow)

Bid-Offer Acceptance Level Flow data provides information about accepted bids and offers.

| Field Name           | Type   | Format/Values              | Notes                  |
| -------------------- | ------ | -------------------------- | ---------------------- |
| `dataset`            | STRING | "BOALF"                    |                        |
| `acceptanceNumber`   | STRING |                            |                        |
| `acceptanceTime`     | STRING | "YYYY-MM-DDThh:mm:ssZ"     | ISO-8601 with timezone |
| `nationalGridBmUnit` | STRING |                            |                        |
| `bmUnit`             | STRING |                            |                        |
| `timeFrom`           | STRING | "YYYY-MM-DDThh:mm:ssZ"     | ISO-8601 with timezone |
| `timeTo`             | STRING | "YYYY-MM-DDThh:mm:ssZ"     | ISO-8601 with timezone |
| `level`              | FLOAT  |                            | MW                     |
| `acceptanceFlag`     | STRING |                            |                        |
| `storFlag`           | STRING |                            |                        |
| `bidOfferFlag`       | STRING |                            |                        |
| `_dataset`           | STRING | "BOALF"                    |                        |
| `_window_from_utc`   | STRING | "YYYY-MM-DDThh:mm:ss.sssZ" | ISO-8601 with timezone |
| `_window_to_utc`     | STRING | "YYYY-MM-DDThh:mm:ss.sssZ" | ISO-8601 with timezone |
| `_ingested_utc`      | STRING | "YYYY-MM-DDThh:mm:ss.sssZ" | ISO-8601 with timezone |

### 5. DISBSAD (Disaggregated Balancing Services Adjustment Data)

| Field Name             | Type    | Format/Values              | Notes                  |
| ---------------------- | ------- | -------------------------- | ---------------------- |
| `dataset`              | STRING  | "DISBSAD"                  |                        |
| `settlementDate`       | STRING  | "YYYY-MM-DD"               |                        |
| `settlementPeriod`     | INTEGER | 1-48                       |                        |
| `timeFrom`             | STRING  | "YYYY-MM-DDThh:mm:ssZ"     | ISO-8601 with timezone |
| `timeTo`               | STRING  | "YYYY-MM-DDThh:mm:ssZ"     | ISO-8601 with timezone |
| `storFlag`             | STRING  |                            |                        |
| `action`               | STRING  |                            |                        |
| `priceCostDescription` | STRING  |                            |                        |
| `volume`               | FLOAT   |                            | In MWh                 |
| `price`                | FLOAT   |                            | In £/MWh               |
| `_dataset`             | STRING  | "DISBSAD"                  |                        |
| `_window_from_utc`     | STRING  | "YYYY-MM-DDThh:mm:ss.sssZ" | ISO-8601 with timezone |
| `_window_to_utc`       | STRING  | "YYYY-MM-DDThh:mm:ss.sssZ" | ISO-8601 with timezone |
| `_ingested_utc`        | STRING  | "YYYY-MM-DDThh:mm:ss.sssZ" | ISO-8601 with timezone |

### 6. WINDFOR (Wind Generation Forecast)

| Field Name         | Type    | Format/Values              | Notes                  |
| ------------------ | ------- | -------------------------- | ---------------------- |
| `dataset`          | STRING  | "WINDFOR"                  |                        |
| `publishTime`      | STRING  | "YYYY-MM-DDThh:mm:ssZ"     | ISO-8601 with timezone |
| `startTime`        | STRING  | "YYYY-MM-DDThh:mm:ssZ"     | ISO-8601 with timezone |
| `endTime`          | STRING  | "YYYY-MM-DDThh:mm:ssZ"     | ISO-8601 with timezone |
| `generation`       | INTEGER |                            | In MW                  |
| `_dataset`         | STRING  | "WINDFOR"                  |                        |
| `_window_from_utc` | STRING  | "YYYY-MM-DDThh:mm:ss.sssZ" | ISO-8601 with timezone |
| `_window_to_utc`   | STRING  | "YYYY-MM-DDThh:mm:ss.sssZ" | ISO-8601 with timezone |
| `_ingested_utc`    | STRING  | "YYYY-MM-DDThh:mm:ss.sssZ" | ISO-8601 with timezone |

### 7. TEMP (Temperature Data)

| Field Name         | Type   | Format/Values              | Notes                  |
| ------------------ | ------ | -------------------------- | ---------------------- |
| `dataset`          | STRING | "TEMP"                     |                        |
| `publishTime`      | STRING | "YYYY-MM-DDThh:mm:ssZ"     | ISO-8601 with timezone |
| `temperature`      | FLOAT  |                            | In degrees Celsius     |
| `_dataset`         | STRING | "TEMP"                     |                        |
| `_window_from_utc` | STRING | "YYYY-MM-DDThh:mm:ss.sssZ" | ISO-8601 with timezone |
| `_window_to_utc`   | STRING | "YYYY-MM-DDThh:mm:ss.sssZ" | ISO-8601 with timezone |
| `_ingested_utc`    | STRING | "YYYY-MM-DDThh:mm:ss.sssZ" | ISO-8601 with timezone |

### 8. IMBALNGC (Imbalance Data)

| Field Name          | Type    | Format/Values              | Notes                  |
| ------------------- | ------- | -------------------------- | ---------------------- |
| `dataset`           | STRING  | "IMBALNGC"                 |                        |
| `settlementDate`    | STRING  | "YYYY-MM-DD"               |                        |
| `settlementPeriod`  | INTEGER | 1-48                       |                        |
| `imbalanceQuantity` | FLOAT   |                            | In MWh                 |
| `imbalancePrice`    | FLOAT   |                            | In £/MWh               |
| `_dataset`          | STRING  | "IMBALNGC"                 |                        |
| `_window_from_utc`  | STRING  | "YYYY-MM-DDThh:mm:ss.sssZ" | ISO-8601 with timezone |
| `_window_to_utc`    | STRING  | "YYYY-MM-DDThh:mm:ss.sssZ" | ISO-8601 with timezone |
| `_ingested_utc`     | STRING  | "YYYY-MM-DDThh:mm:ss.sssZ" | ISO-8601 with timezone |

### 9. PN (Physical Notifications)

| Field Name           | Type   | Format/Values              | Notes                  |
| -------------------- | ------ | -------------------------- | ---------------------- |
| `dataset`            | STRING | "PN"                       |                        |
| `publishTime`        | STRING | "YYYY-MM-DDThh:mm:ssZ"     | ISO-8601 with timezone |
| `startTime`          | STRING | "YYYY-MM-DDThh:mm:ssZ"     | ISO-8601 with timezone |
| `bmUnit`             | STRING |                            |                        |
| `level`              | FLOAT  |                            | In MW                  |
| `nationalGridBmUnit` | STRING |                            |                        |
| `_dataset`           | STRING | "PN"                       |                        |
| `_window_from_utc`   | STRING | "YYYY-MM-DDThh:mm:ss.sssZ" | ISO-8601 with timezone |
| `_window_to_utc`     | STRING | "YYYY-MM-DDThh:mm:ss.sssZ" | ISO-8601 with timezone |
| `_ingested_utc`      | STRING | "YYYY-MM-DDThh:mm:ss.sssZ" | ISO-8601 with timezone |

### 10. QPN (Quiescent Physical Notifications)

| Field Name           | Type   | Format/Values              | Notes                  |
| -------------------- | ------ | -------------------------- | ---------------------- |
| `dataset`            | STRING | "QPN"                      |                        |
| `publishTime`        | STRING | "YYYY-MM-DDThh:mm:ssZ"     | ISO-8601 with timezone |
| `startTime`          | STRING | "YYYY-MM-DDThh:mm:ssZ"     | ISO-8601 with timezone |
| `bmUnit`             | STRING |                            |                        |
| `level`              | FLOAT  |                            | In MW                  |
| `nationalGridBmUnit` | STRING |                            |                        |
| `_dataset`           | STRING | "QPN"                      |                        |
| `_window_from_utc`   | STRING | "YYYY-MM-DDThh:mm:ss.sssZ" | ISO-8601 with timezone |
| `_window_to_utc`     | STRING | "YYYY-MM-DDThh:mm:ss.sssZ" | ISO-8601 with timezone |
| `_ingested_utc`      | STRING | "YYYY-MM-DDThh:mm:ss.sssZ" | ISO-8601 with timezone |

### 11-56. Additional Datasets

The remaining datasets follow similar patterns with the specific fields relevant to their domain. All include the standard metadata fields and use ISO-8601 formatting for datetime fields.

Key datasets include:

- **MELS**: Maximum Export Limits
- **MILS**: Maximum Import Limits
- **RDRE**: Replacement Reserve (RR) Auction Results
- **RDRI**: Replacement Reserve (RR) Instructions
- **MID**: Market Index Data
- **TSDF**: Transmission System Demand Forecast
- **FUELHH**: Half-hourly Fuel Type Generation
- **B1610**: European Transparency Regulation data
- **INDDEM**: Indicated demand data
- **INDGEN**: Indicated generation data
- **ITSDO**: Initial Transmission System Demand Outturn
- **NETBSAD**: Net Balancing Services Adjustment Data

## Date/Time Format Summary

| Format Type       | Pattern                  | Example                  | Usage                            |
| ----------------- | ------------------------ | ------------------------ | -------------------------------- |
| ISO-8601 with Z   | YYYY-MM-DDThh:mm:ssZ     | 2025-08-28T00:00:00Z     | timeFrom, timeTo                 |
| ISO-8601 with ms  | YYYY-MM-DDThh:mm:ss.sssZ | 2025-08-28T00:00:00.000Z | _window_from_utc, _window_to_utc |
| Date only         | YYYY-MM-DD               | 2025-08-28               | settlementDate                   |
| Settlement Period | Integer                  | 1-48                     | settlementPeriod                 |

## Recommendations for Working with Datetime Fields

1. **Use UTC Consistently**: All timestamps in Elexon data are in UTC (indicated by the 'Z' suffix)
2. **Parse ISO-8601 Format**: When processing, ensure your parser correctly handles the ISO-8601 format with timezone
3. **Convert to TIMESTAMP in BigQuery**: For analysis, consider converting STRING datetime fields to TIMESTAMP type
4. **Settlement Period Conversion**: To convert settlement periods to time:
   - Period 1 = 00:00-00:30, Period 2 = 00:30-01:00, etc.
   - Formula: `00:00 + (settlementPeriod - 1) * 0.5 hours`

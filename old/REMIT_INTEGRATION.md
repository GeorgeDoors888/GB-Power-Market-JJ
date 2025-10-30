# REMIT Data Integration

This document describes the REMIT data integration system which ingests and analyzes REMIT (Regulation on Energy Market Integrity and Transparency) data from Elexon's IRIS service.

## Overview

REMIT data contains important information about planned and unplanned unavailability of electricity generation assets in the UK. This information is critical for understanding market conditions, forecasting prices, and identifying potential supply constraints.

The integration system consists of several components:

1. **IRIS Service Client** - Connects to Elexon's IRIS service to receive REMIT messages
2. **REMIT Table** - A BigQuery table with a schema designed to store the nested REMIT data
3. **Ingestion Pipeline** - Scripts to process IRIS messages and load them into BigQuery
4. **Query Tools** - Tools to query and analyze the REMIT data for insights

## Files

### Core Components

- `elexon_iris/client.py` - Client for connecting to the IRIS service
- `elexon_iris/create_remit_table.py` - Creates the BigQuery table for REMIT data
- `elexon_iris/iris_to_bigquery.py` - Loads IRIS data into BigQuery
- `elexon_iris/check_remit_table.py` - Checks the status of the REMIT table

### New Integration Scripts

- `ingest_remit.py` - Standalone script for ingesting REMIT data from IRIS to BigQuery
- `ingest_elexon_with_remit.py` - Enhanced script that integrates REMIT ingestion with the main Elexon BMRS ingestion pipeline
- `analyze_remit_data.py` - Script for analyzing REMIT data and generating reports
- `get_latest_energy_data.py` - Updated to include REMIT data in the energy data output

## REMIT Table Schema

The REMIT data is stored in a BigQuery table with the following key fields:

- `mrid` - Message Reference ID
- `publishTime` - When the message was published
- `revisionNumber` - Version of the message
- `messageType` - Type of message (e.g., ELECTRICITY_UNAVAILABILITY)
- `unavailabilityType` - Planned or Unplanned
- `assetId` - Identifier for the affected asset
- `affectedUnit` - Name of the affected unit
- `fuelType` - Type of fuel used by the generation asset
- `normalCapacity` - Normal operating capacity in MW
- `availableCapacity` - Available capacity during the event
- `unavailableCapacity` - Capacity unavailable during the event
- `eventStartTime` - Start time of the unavailability
- `eventEndTime` - Expected end time of the unavailability
- `cause` - Reason for the unavailability
- `outageProfile` - Nested array with detailed outage information for each time period

## Usage

### Ingesting REMIT Data

To ingest REMIT data from the IRIS service:

```bash
python ingest_remit.py --data-dir ./elexon_iris/data --processed-file ./elexon_iris/processed_files.txt
```

### Analyzing REMIT Data

To analyze current REMIT events:

```bash
python analyze_remit_data.py --output remit_analysis.json --report remit_report.txt
```

To filter by fuel type:

```bash
python analyze_remit_data.py --fuel-types NUCLEAR,CCGT --output nuclear_ccgt_analysis.json
```

### Integrated Elexon and REMIT Ingestion

To run the integrated ingestion pipeline:

```bash
python ingest_elexon_with_remit.py --start 2025-09-01 --end 2025-09-02 --include-remit
```

To ingest only REMIT data:

```bash
python ingest_elexon_with_remit.py --remit-only
```

### Getting Latest Energy Data

To get the latest energy data including REMIT events:

```bash
python get_latest_energy_data.py > latest_energy_data.json
```

## Monitoring

The REMIT integration can be monitored using the following:

1. Check the status of the REMIT table:
   ```bash
   python elexon_iris/check_remit_table.py
   ```

2. Run the REMIT analysis script to check for current events:
   ```bash
   python analyze_remit_data.py
   ```

3. Examine the latest energy data which includes REMIT events:
   ```bash
   python get_latest_energy_data.py
   ```

## Implementation Notes

- REMIT data is received through the IRIS service, which is different from the standard BMRS API
- The REMIT data structure is more complex, including nested fields like outageProfile
- The integration handles different message types, including unavailability events and system warnings
- Timestamps are standardized to ISO format for BigQuery compatibility

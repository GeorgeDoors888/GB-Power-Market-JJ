# Energy Data System Documentation

This document provides a comprehensive overview of the energy data ingestion system, explaining how it works, its components, and how to use it effectively.

## System Overview

The energy data system is designed to automatically ingest data from multiple energy market sources, process it, and store it in BigQuery for analysis. The system handles:

1. **Catchup on Startup**: When your machine starts, it can ingest missed data from when it was offline
2. **Continuous Updates**: It runs every 15 minutes to keep data current
3. **Multiple Data Sources**: Processes data from Elexon BMRS, REMIT, and NESO

## Data Sources and Types

### Elexon BMRS (Balancing Mechanism Reporting Service)

Elexon is the Balancing and Settlement Code (BSC) administrator for Great Britain's electricity system. Their BMRS platform provides real-time data about the GB electricity market.

**Data Access**:
- API Base URL: https://api.bmreports.com/BMRS/
- Registration: Required at https://www.elexonportal.co.uk/
- API Key: Needed for authentication

**Key Datasets**:

| Dataset Code | Description                                      | Update Frequency | Contents                                           |
| ------------ | ------------------------------------------------ | ---------------- | -------------------------------------------------- |
| BOD          | Bid-Offer Data                                   | Every 5 min      | Buy/sell orders from market participants           |
| BOALF        | Bid-Offer Acceptance Level Flagged               | Every 5 min      | Accepted bids and offers                           |
| FREQ         | System Frequency                                 | Every 1 min      | Real-time electricity system frequency             |
| FUELINST     | Generation by Fuel Type                          | Every 5 min      | Breakdown of electricity generation by fuel source |
| COSTS        | System Balancing Costs                           | Daily            | Costs of balancing the electricity system          |
| DISBSAD      | Disaggregated Balancing Services Adjustment Data | Daily            | Detailed balancing services data                   |
| MELS         | Maximum Export Limit                             | Every 5 min      | Maximum export limits by unit                      |
| MILS         | Maximum Import Limit                             | Every 5 min      | Maximum import limits by unit                      |
| QAS          | Accepted Volumes                                 | Every 5 min      | Volumes of accepted bids/offers                    |
| NETBSAD      | Net Balancing Services Adjustment                | Every 30 min     | Net adjustment volumes and prices                  |
| PN           | Physical Notifications                           | Every 5 min      | Generation intentions declared by participants     |
| QPN          | Quiescent Physical Notifications                 | Every 5 min      | Baseline generation predictions                    |

**Documentation**:
- Main documentation: https://www.elexon.co.uk/documents/training-guidance/bsc-guidance-notes/bmrs-api-and-data-push-user-guide/
- Schema reference: https://www.elexon.co.uk/documents/training-guidance/bsc-guidance-notes/bmrs-api-data-push-user-guide-configuration-file/

### NESO (National Energy System Operator)

NESO data comes from National Grid ESO (Electricity System Operator), which operates Great Britain's electricity transmission system.

**Data Access**:
- Portal: https://data.nationalgrideso.com/
- API Base URL: https://data.nationalgrideso.com/api/3/action/
- Authentication: Some datasets require registration

**Key Datasets**:

| Dataset                  | Description                              | Update Frequency |
| ------------------------ | ---------------------------------------- | ---------------- |
| Carbon Intensity         | CO2 emissions per kWh of electricity     | Every 30 min     |
| Demand Data              | Electricity demand forecasts and actuals | Daily            |
| Embedded Generation      | Generation from distributed sources      | Daily            |
| ESO Balancing Services   | Balancing services procurement           | Monthly          |
| Transmission System Data | Real-time system data                    | Every 5 min      |
| Weather Data             | Weather forecasts and actuals            | Hourly           |

**Documentation**:
- Main portal: https://data.nationalgrideso.com/
- API documentation: https://data.nationalgrideso.com/system/api-guides

### REMIT (Regulation on Wholesale Energy Market Integrity and Transparency)

REMIT data contains information about planned outages, actual outages, and capacity changes in power generation units.

**Data Access**:
- Accessed through the ENTSO-E Transparency Platform
- URL: https://transparency.entsoe.eu/
- API documentation: https://transparency.entsoe.eu/content/static_content/Static%20content/web%20api/Guide.html

**Key Data Types**:
- Planned Unavailability of Generation Units
- Actual Unavailability of Generation Units
- Changes in Actual Availability

## Key Components

### 1. Startup Manager (`energy_system_startup.py`)

This script coordinates the entire system startup process:

- Prompts for how many days of historical data to catch up on
- Runs initial data ingestion to catch up on missed data
- Starts the continuous 15-minute update process in the background

**Usage:**
```bash
python energy_system_startup.py [--days DAYS] [--dry-run] [--only DATASETS] [--skip-catchup] [--skip-15min]
```

**Options:**
- `--days`: Number of days to catch up (skips prompt)
- `--dry-run`: Run in dry-run mode without actually updating data
- `--only`: Comma-separated dataset codes to process (e.g., "BOD,BOALF,DISBSAD")
- `--skip-catchup`: Skip historical data catchup
- `--skip-15min`: Skip 15-minute updater

### 2. 15-Minute Updater (`update_all_data_15min.py`)

This script handles regular 15-minute updates of all data sources:

- Updates high-priority Elexon data every 15 minutes
- Updates standard-priority Elexon data every 30 minutes
- Updates REMIT data every 30 minutes
- Updates NESO data every 2 hours

**Usage:**
```bash
python update_all_data_15min.py [--dry-run] [--elexon-only] [--remit-only] [--neso-only] [--force] [--continuous]
```

**Options:**
- `--dry-run`: Run in dry-run mode
- `--elexon-only`: Only update Elexon data
- `--remit-only`: Only update REMIT data
- `--neso-only`: Only update NESO data
- `--force`: Force updates regardless of timing
- `--continuous`: Run continuously every 15 minutes

### 3. Elexon Data Ingestor (`ingest_elexon_fixed.py`)

This script fetches and processes Elexon BMRS data:

- Handles multiple datasets (BOD, BOALF, COSTS, DISBSAD, etc.)
- Checks for existing data windows to avoid duplicates
- Converts data for BigQuery compatibility
- Uses staging tables when possible, with fallback to direct loading

**Usage:**
```bash
python ingest_elexon_fixed.py --start START_DATE --end END_DATE [--only DATASETS] [--dry-run] [--log-level LEVEL]
```

### 4. REMIT Data Ingestor (`ingest_remit.py`)

Processes REMIT (Regulation on Wholesale Energy Market Integrity and Transparency) data.

### 5. NESO Data Updater (`neso_data_updater.py`)

Processes National Energy System Operator data.

### 6. Data Tracker

Tracks last ingestion times for each data source to determine when updates are needed:

- Primarily uses Google Sheets for tracking (with service account authentication)
- Falls back to local file-based tracking when Google Sheets is unavailable

## Data Flow Process

Here's how data flows through the system:

1. **Scheduling Check**:
   - The system checks when data was last ingested for each source
   - Determines which datasets need updates based on priority and timing rules

2. **Data Fetching**:
   - For each dataset that needs updating, the system:
     - Checks for existing data windows in BigQuery
     - Calculates missing windows
     - Fetches only the missing data from the API

3. **Data Processing**:
   - Converts datetime columns to be timezone-naive for PyArrow compatibility
   - Converts string columns to ensure proper typing
   - Creates hash keys for each row for data integrity

4. **BigQuery Loading**:
   - First attempts to use staging tables for efficient loading
   - If staging table approach fails (e.g., with PyArrow compatibility issues), falls back to direct loading
   - Updates data tracking for successful loads

## Startup Process

When your computer starts up, you can run the startup manager:

```bash
python energy_system_startup.py
```

This will:
1. Prompt you for how many days of historical data to catch up on
2. Run the initial data ingestion to catch up
3. Start the 15-minute updater process in the background

## System Capabilities

### 1. Duplicate Prevention

The system checks for existing data windows in BigQuery before fetching data from APIs. This ensures you only fetch and process data that isn't already in your database.

### 2. Error Handling

- **PyArrow Compatibility**: The system automatically falls back to direct loading when staging tables fail
- **Google Sheets Unavailability**: Falls back to local file tracking when Google Sheets is unavailable
- **API Failures**: Logs errors and continues with other datasets

### 3. Flexible Configuration

- Control which datasets to process
- Run in dry-run mode to test without updating data
- Configure logging verbosity

## PyArrow Conversion

You'll notice many log messages about PyArrow conversions, like:

```
Converting datetime column 'timeTo' to pandas datetime
Converted datetime column 'timeTo' to timezone-naive for PyArrow compatibility
```

These conversions are necessary because:

1. BigQuery uses Arrow format for data transfer
2. PyArrow has strict requirements about data types
3. Particularly, PyArrow requires timezone-naive datetime objects

While verbose, these logs indicate the system is properly preparing your data for BigQuery.

## Running at System Startup

To have the system run automatically when your Mac starts:

1. The system includes a LaunchAgent configuration file (`com.georgemajor.energy-system-startup.plist`)
2. Copy this file to `~/Library/LaunchAgents/`
3. Load it with: `launchctl load ~/Library/LaunchAgents/com.georgemajor.energy-system-startup.plist`

This will ensure your energy data is always up to date, even after your machine has been offline.

## Troubleshooting

### Google Sheets Authentication Issues

If you see errors about Google Sheets authentication:

```
Failed to setup Google Sheets: gspread.exceptions.APIError: [403]
```

The system will automatically fall back to local file tracking. If you want to fix the Google Sheets integration:

1. Ensure you have the correct service account credentials
2. Check that the service account has access to the Google Sheet
3. Verify the SCOPES include spreadsheets

### PyArrow Compatibility Errors

If you see errors like:

```
Error converting Pandas column with name: "settlementDate" and datatype: "datetime64[ns]" to an appropriate pyarrow datatype
```

This is expected and handled automatically by the fallback mechanism. The system will retry with direct loading.

### Log Files

Check these log files for troubleshooting:

- `startup_manager.log`: Logs from the startup manager
- `15_minute_update.log`: Logs from the 15-minute updater
- `system_startup.json`: Record of startup parameters
- `15_minute_update_last_run.json`: Results from the last update run

## BigQuery Data Structure

The system stores all data in BigQuery tables with the following organization:

**Project**: `jibber-jabber-knowledge`
**Dataset**: `uk_energy_insights`
**Tables**:

| Table         | Source      | Contains                           | Key Fields                                                                                                            |
| ------------- | ----------- | ---------------------------------- | --------------------------------------------------------------------------------------------------------------------- |
| bmrs_bod      | Elexon BMRS | Bid-Offer Data                     | settlementDate, timeFrom, timeTo, bmUnit, bidOfferNumber, bidOfferPair, bidOfferStatus, bidOfferVolume, bidOfferPrice |
| bmrs_boalf    | Elexon BMRS | Bid-Offer Acceptance Level Flagged | settlementDate, timeFrom, timeTo, bmUnit, acceptanceNumber, acceptanceTime, bidOfferPair, acceptanceVolume            |
| bmrs_freq     | Elexon BMRS | System Frequency                   | recordTime, frequency                                                                                                 |
| bmrs_fuelinst | Elexon BMRS | Generation by Fuel Type            | recordTime, fuelType, generation, highestImportNational, lowestImportNational                                         |
| bmrs_costs    | Elexon BMRS | System Balancing Costs             | settlementDate, startTime, costType, chargeAmount, priceDerivationCode                                                |
| bmrs_disbsad  | Elexon BMRS | Disaggregated Balancing Services   | settlementDate, settlementPeriod, partyId, assetId, service, volume, price, paymentAmount                             |
| bmrs_mels     | Elexon BMRS | Maximum Export Limit               | settlementDate, timeFrom, timeTo, bmUnit, maxExportLimit                                                              |
| bmrs_mils     | Elexon BMRS | Maximum Import Limit               | settlementDate, timeFrom, timeTo, bmUnit, maxImportLimit                                                              |
| bmrs_netbsad  | Elexon BMRS | Net Balancing Services Adjustment  | settlementDate, settlementPeriod, netBuyPrice, netBuyVolume, netSellPrice, netSellVolume                              |
| bmrs_pn       | Elexon BMRS | Physical Notifications             | settlementDate, timeFrom, timeTo, bmUnit, notificationTime, notificationSequence, powerValue                          |
| bmrs_qpn      | Elexon BMRS | Quiescent Physical Notifications   | settlementDate, timeFrom, timeTo, bmUnit, notificationTime, notificationSequence, powerValue                          |
| remit_events  | REMIT       | Outage information                 | eventStart, eventEnd, assetId, assetName, eventType, fuelType, affectedCapacity                                       |
| neso_*        | NESO        | Various NESO datasets              | Varies by dataset                                                                                                     |

## Using the Data

The data ingested by this system can be used for various analytical purposes:

### 1. Market Analysis
- Price trend analysis
- Supply-demand balance
- Market participant behavior

### 2. Operational Insights
- Generation availability
- System constraints
- Balancing actions

### 3. Forecasting
- Price forecasting
- Demand forecasting
- Generation forecasting

### 4. Market Strategy
- Trading strategy development
- Asset optimization
- Imbalance risk management

### Sample Queries

**Example 1**: Get generation mix for a specific day
```sql
SELECT
  recordTime,
  fuelType,
  generation
FROM
  `jibber-jabber-knowledge.uk_energy_insights.bmrs_fuelinst`
WHERE
  DATE(recordTime) = '2025-09-20'
ORDER BY
  recordTime, fuelType
```

**Example 2**: Calculate average system buy price by settlement period
```sql
SELECT
  settlementDate,
  settlementPeriod,
  AVG(netBuyPrice) as avgBuyPrice
FROM
  `jibber-jabber-knowledge.uk_energy_insights.bmrs_netbsad`
GROUP BY
  settlementDate, settlementPeriod
ORDER BY
  settlementDate, settlementPeriod
```

## Conclusion

This energy data system provides a robust, fault-tolerant way to keep your energy market data up to date. It efficiently handles catching up on missed data and maintains regular updates while your machine is running.

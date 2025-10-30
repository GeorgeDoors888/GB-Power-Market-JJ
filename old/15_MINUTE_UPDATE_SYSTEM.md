# 15-Minute Update System

This document describes the 15-minute update system that keeps all data sources (Elexon BMRS, REMIT, and NESO) up to date in the UK Energy Insights platform.

## Overview

The 15-minute update system is a comprehensive solution that coordinates the updates of multiple data sources:

1. **Elexon BMRS Data**: High-frequency electricity market data
2. **REMIT Data**: Information about planned and unplanned generation outages
3. **NESO Data**: National Energy System Operator data

The system intelligently manages update frequencies for different types of data, ensuring optimal data freshness while minimizing resource usage.

## Update Frequencies

| Data Type            | Update Frequency | Window Size        | Examples                                   |
| -------------------- | ---------------- | ------------------ | ------------------------------------------ |
| Elexon High Priority | Every 15 minutes | 15 minutes         | FREQ, FUELINST, BOD, BOALF, COSTS, DISBSAD |
| Elexon Standard      | Every 30 minutes | 30 minutes         | MELS, MILS, QAS, NETBSAD, PN, QPN          |
| REMIT                | Every 30 minutes | N/A (Event-based)  | Generation outages, system warnings        |
| NESO                 | Every 2 hours    | N/A (Full dataset) | System operation data                      |

## Components

### Main Update Script

The main update script (`update_all_data_15min.py`) coordinates all updates:

```bash
python update_all_data_15min.py
```

### Individual Update Scripts

The main script calls these individual update scripts:

1. **Elexon BMRS**: `ingest_elexon_fixed.py` - Retrieves Elexon BMRS data
2. **REMIT**: `ingest_remit.py` - Processes REMIT data from IRIS
3. **NESO**: Uses `NESODataUpdater` class - Updates NESO data
4. **Latest Energy Data**: `get_latest_energy_data.py` - Creates a snapshot of the current energy system

### Tracking System

The system uses `automated_data_tracker.py` to track when each data source was last updated. This information is stored in a Google Sheet for easy monitoring.

## Automated Execution

The system runs automatically every 15 minutes via a cron job. To install the cron job:

```bash
./install_15min_cron.sh
```

## Smart Skipping Logic

The system intelligently skips updates if the data is already recent enough:

- If high-priority Elexon data was updated less than 12 minutes ago, it will skip the update
- If standard-priority Elexon data was updated less than 25 minutes ago, it will skip
- If REMIT data was updated less than 25 minutes ago, it will skip
- If NESO data was updated less than 2 hours ago, it will skip

This prevents unnecessary processing and API calls.

## Monitoring

The system creates several log files for monitoring:

- `15_minute_update.log`: Main log file with detailed information
- `15_minute_update_cron.log`: Log from the cron job execution
- `15_minute_update_last_run.json`: JSON file with the results of the last run

You can also check the Google Sheet to see when each data source was last updated.

## Troubleshooting

If the system isn't updating as expected:

1. Check the log files for errors
2. Verify the cron job is active: `crontab -l`
3. Run the script manually to see any immediate errors: `python update_all_data_15min.py`
4. Check the Google Sheet for the last update times
5. Verify API credentials are properly configured

## Force Updates

To force an update regardless of timing:

```bash
python update_all_data_15min.py --force
```

To update only a specific data source:

```bash
python update_all_data_15min.py --elexon-only
python update_all_data_15min.py --remit-only
python update_all_data_15min.py --neso-only
```

## NESO Data Source

NESO (National Energy System Operator) data is retrieved from the National Grid ESO data portal. The system uses the `NESODataUpdater` class to:

1. Check for new datasets
2. Download updated files
3. Process and load the data into the system

The NESO data is updated less frequently (every 2 hours) as it typically changes less often than Elexon or REMIT data.

## Data Flow

The entire data flow is as follows:

1. The cron job triggers `update_all_data_15min.py` every 15 minutes
2. The script checks what needs to be updated based on timing
3. It calls the appropriate update scripts for each data source
4. Data is fetched from the respective APIs (Elexon, IRIS, NESO)
5. Data is processed and loaded into BigQuery
6. Update times are recorded in the tracking system
7. The latest energy data snapshot is generated

This ensures all data sources stay fresh with minimal overhead.

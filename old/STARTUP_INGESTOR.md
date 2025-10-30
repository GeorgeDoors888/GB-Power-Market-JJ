# Startup Data Ingestor

This tool allows you to ingest Elexon BMRS data whenever your machine starts up, without requiring Google Sheets authentication or complex setup.

## Overview

The startup ingestor:

1. Runs at system startup
2. Prompts you for how many days of historical data to ingest
3. Ingests Elexon data for the specified time period
4. Optionally ingests REMIT data if available
5. All without requiring Google Sheets access

## Setup Instructions

### Option 1: Manual Execution

Run the ingestor script directly:

```bash
cd /Users/georgemajor/jibber-jabber\ 24\ august\ 2025\ big\ bop
source .venv/bin/activate
python startup_ingestor.py
```

### Option 2: Run at macOS Login

To make the script run automatically when you log in:

1. Open "System Preferences" → "Users & Groups"
2. Select your user account
3. Click on "Login Items"
4. Click the "+" button
5. Navigate to and select `/Users/georgemajor/jibber-jabber 24 august 2025 big bop/run_ingestor_at_startup.sh`
6. Click "Add"

The script will now run each time you log in to your macOS account.

## Command Line Options

The startup ingestor supports these command line arguments:

- `--days NUMBER`: Specify number of days to ingest (skips interactive prompt)
- `--dry-run`: Run in dry-run mode (no actual updates)
- `--only DATASETS`: Comma-separated dataset codes (e.g., `BOD,BOALF,DISBSAD`)

Example:

```bash
python startup_ingestor.py --days 7 --only FREQ,FUELINST
```

## Default Datasets

If no specific datasets are specified, the script will ingest these high-priority datasets:

- FREQ (Frequency data)
- FUELINST (Fuel generation data)
- BOD (Bid-Offer data)
- BOALF (Bid-Offer Acceptance Level Flag)
- COSTS (System Buy/Sell Prices)
- DISBSAD (Disaggregated Balancing Services Adjustment Data)
- MELS (Maximum Export Limit)
- MILS (Maximum Import Limit)
- QAS (Acceptance data)
- NETBSAD (Net Balancing Services Adjustment Data)
- PN (Physical Notifications)
- QPN (Quiescent Physical Notifications)

## REMIT Data

If the `ingest_remit.py` script is available in the same directory, the ingestor will also run it after Elexon data ingestion completes.

## Troubleshooting

- If the script fails to run at startup, check that the paths in the `run_ingestor_at_startup.sh` file are correct
- Ensure the virtual environment is activated before running the script
- If Google Sheets authentication errors occur, they can be safely ignored as this script doesn't use Google Sheets

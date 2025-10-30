#!/bin/bash

# Navigate to the project directory
cd "/Users/georgemajor/jibber-jabber 24 august 2025 big bop"

# Activate the virtual environment if needed
source .venv/bin/activate

# Set up the date range (from 1 day ago to now)
START_DATE=$(date -v-1d +%Y-%m-%d)
END_DATE=$(date +%Y-%m-%d)

# Run the script to update data (high-frequency datasets)
python ingest_elexon_fixed.py --start "${START_DATE}" --end "${END_DATE}" --only FREQ,FUELINST,MIP,MELS,MILS,BOD,BOALF --include-offline --log-level INFO >> elexon_update.log 2>&1

# Exit with the script's exit code
exit $?

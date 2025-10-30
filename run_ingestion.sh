#!/bin/bash
# This script runs the Elexon data ingestion.
# It sets the necessary environment variables and executes the Python script
# from the correct virtual environment.

# Navigate to the project directory
cd "/Users/georgemajor/jibber-jabber 24 august 2025 big bop" || exit

# Set the Google Cloud credentials
export GOOGLE_APPLICATION_CREDENTIALS="/Users/georgemajor/jibber-jabber 24 august 2025 big bop/jibber_jabber_key.json"

# Calculate dates for the last 2 days to ensure we catch any missing data
START_DATE=$(date -j -v-2d "+%Y-%m-%d")
END_DATE=$(date -j -v+1d "+%Y-%m-%d")

echo "$(date): Running ingestion from $START_DATE to $END_DATE" >> '/Users/georgemajor/jibber-jabber 24 august 2025 big bop/cron_ingest.log'

# Run the ingestion script using the virtual environment's Python interpreter
'/Users/georgemajor/jibber-jabber 24 august 2025 big bop/venv/bin/python' '/Users/georgemajor/jibber-jabber 24 august 2025 big bop/ingest_elexon_fixed.py' --start "$START_DATE" --end "$END_DATE" --log-level INFO >> '/Users/georgemajor/jibber-jabber 24 august 2025 big bop/cron_ingest.log' 2>&1

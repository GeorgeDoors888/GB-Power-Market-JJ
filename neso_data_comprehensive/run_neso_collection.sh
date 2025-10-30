#!/bin/bash
# Script to run NESO data collection every 15 minutes on the hour

# Change to the project directory
cd "/Users/georgemajor/jibber-jabber 24 august 2025 big bop"

# Activate virtual environment
source .venv/bin/activate

# Create a log directory if it doesn't exist
mkdir -p neso_data_comprehensive/logs

# Log start time
echo "Running NESO data collection at $(date)" >> neso_data_comprehensive/logs/neso_collection_$(date +%Y%m%d).log

# Run the NESO data collection script
python collect_neso_comprehensive.py >> neso_data_comprehensive/logs/neso_collection_$(date +%Y%m%d).log 2>&1

# Log completion
echo "NESO data collection completed at $(date)" >> neso_data_comprehensive/logs/neso_collection_$(date +%Y%m%d).log

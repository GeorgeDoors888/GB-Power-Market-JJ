#!/bin/zsh
# Activate Python virtual environment and set Google credentials for ingestion scripts

# Set the path to your service account key
export GOOGLE_APPLICATION_CREDENTIALS="$(dirname "$0")/jibber_jabber_key.json"

# Activate the virtual environment (if it exists)
if [ -d ".venv" ]; then
    source .venv/bin/activate
fi

echo "Environment ready. Run your ingestion script, e.g.:"
echo "python ingest_elexon_all.py --start 2025-05-01 --end 2025-06-01"

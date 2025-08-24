#!/bin/bash
# Simple script to run the Live Data Updater with real Elexon/BMRS data

echo "Starting Live Data Updater with real data..."

# Stop any existing processes
pkill -f "live_data_updater.py" || true
sleep 2

# Set up environment
cd "$(dirname "$0")"
source venv/bin/activate

# Load API keys
if [ -f "api.env" ]; then
    # Export all keys from api.env
    while IFS='=' read -r key value || [[ -n "$key" ]]; do
        if [[ ! $key =~ ^# && -n $key ]]; then
            # Remove quotes if present
            value=$(echo $value | sed -e 's/^"//' -e 's/"$//' -e "s/^'//" -e "s/'$//")
            export "$key=$value"
            echo "  Loaded $key ✅"
        fi
    done < "api.env"
    echo "API keys loaded successfully"
else
    echo "Warning: api.env file not found"
    exit 1
fi

# Make sure the BMRS API key is set
if [ -z "$BMRS_API_KEY" ] && [ -n "$BMRS_API_KEY_1" ]; then
    export BMRS_API_KEY="$BMRS_API_KEY_1"
    echo "Using BMRS_API_KEY_1 as primary API key"
fi

# Start the live data updater with the update command
echo "Starting live data updater..."
python live_data_updater.py update

# This will run in the foreground so you can see any errors

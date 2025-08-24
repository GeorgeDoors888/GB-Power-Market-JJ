#!/bin/bash
# Simple script to run the UK Energy dashboard with real Elexon/BMRS data
# This fixes the color scheme issues and ensures we're using the real API data

echo "Starting UK Energy Dashboard with real data..."

# Stop any existing processes
pkill -f "streamlit run" || true
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

# Create .streamlit directory if it doesn't exist
mkdir -p ~/.streamlit

# Create a Streamlit config file to fix the color scheme
cat > ~/.streamlit/config.toml << EOF
[theme]
primaryColor="#0068c9"
backgroundColor="#ffffff"
secondaryBackgroundColor="#f0f2f6"
textColor="#262730"
font="sans serif"

[server]
enableCORS = false
enableXsrfProtection = false
headless = true
EOF

# Start the live data updater with correct command
echo "Starting live data updater..."
python live_data_updater.py update &
UPDATER_PID=$!
echo "Live data updater started with PID: $UPDATER_PID"
sleep 3

# Start the dashboard
echo "Starting the dashboard..."
streamlit run live_energy_dashboard.py

# This script will keep running until the dashboard is closed
# Then it will clean up the live data updater
kill $UPDATER_PID 2>/dev/null || true

#!/bin/bash
# Master script to download ALL outstanding data for wind forecasting project
# Run this to complete all data downloads before proceeding with enhancement todos

set -e  # Exit on error

PROJECT_DIR="/home/george/GB-Power-Market-JJ"
LOG_DIR="$PROJECT_DIR/logs"

mkdir -p "$LOG_DIR"

echo "================================================================================"
echo "Master Data Download Script - Wind Forecasting Project"
echo "================================================================================"
echo "This will download ALL outstanding data in sequence:"
echo "  1. ERA5 weather (temp/humidity/precip) - Already running (~20 min remaining)"
echo "  2. REMIT unavailability messages - 30 minutes"
echo "  3. GFS forecast data (7-day ahead) - 5-10 minutes"
echo "  4. ERA5 3D wind components (u/v/shear) - 4-5 hours"
echo ""
echo "Total estimated time: ~5-6 hours"
echo "================================================================================"
echo ""

# Check if ERA5 weather download is already running
if pgrep -f "download_era5_weather_for_icing.py" > /dev/null; then
    echo "✅ ERA5 weather download already running (PID: $(pgrep -f download_era5_weather_for_icing.py))"
    echo "   Waiting for it to complete..."
    echo ""
    
    # Wait for it to finish
    while pgrep -f "download_era5_weather_for_icing.py" > /dev/null; do
        sleep 30
        tail -3 "$PROJECT_DIR/era5_weather_download.log" 2>/dev/null || echo "   Still downloading..."
    done
    
    echo ""
    echo "✅ ERA5 weather download complete!"
    echo ""
else
    echo "⚠️  ERA5 weather download not running - starting it now..."
    cd "$PROJECT_DIR"
    python3 -u download_era5_weather_for_icing.py > era5_weather_download.log 2>&1 &
    echo "   Started (PID: $!)"
    echo "   Waiting for completion..."
    wait $!
    echo "✅ ERA5 weather download complete!"
    echo ""
fi

# 2. Download REMIT messages
echo "================================================================================"
echo "2/4: Downloading REMIT Unavailability Messages"
echo "================================================================================"
echo "Purpose: Distinguish icing from maintenance/curtailment"
echo "Time: ~30 minutes"
echo ""

cd "$PROJECT_DIR"
python3 -u download_remit_messages.py > "$LOG_DIR/remit_messages_download.log" 2>&1

if [ $? -eq 0 ]; then
    echo "✅ REMIT messages download complete!"
else
    echo "⚠️  REMIT messages download failed (see $LOG_DIR/remit_messages_download.log)"
    echo "   Continuing with other downloads..."
fi
echo ""

# 3. Download GFS forecast data
echo "================================================================================"
echo "3/4: Downloading GFS Forecast Data (7-day ahead)"
echo "================================================================================"
echo "Purpose: Day-ahead wind forecasting"
echo "Time: ~5-10 minutes"
echo ""

cd "$PROJECT_DIR"
python3 -u download_gfs_forecasts.py > "$LOG_DIR/gfs_forecasts_download.log" 2>&1

if [ $? -eq 0 ]; then
    echo "✅ GFS forecast download complete!"
else
    echo "⚠️  GFS forecast download failed (see $LOG_DIR/gfs_forecasts_download.log)"
    echo "   Continuing with final download..."
fi
echo ""

# 4. Download ERA5 3D wind components (longest)
echo "================================================================================"
echo "4/4: Downloading ERA5 3D Wind Components"
echo "================================================================================"
echo "Purpose: Ramp prediction, atmospheric dynamics"
echo "Time: ~4-5 hours (48 farms × 5 years)"
echo ""

cd "$PROJECT_DIR"
python3 -u download_era5_3d_wind.py > "$LOG_DIR/era5_3d_wind_download.log" 2>&1

if [ $? -eq 0 ]; then
    echo "✅ ERA5 3D wind download complete!"
else
    echo "⚠️  ERA5 3D wind download failed (see $LOG_DIR/era5_3d_wind_download.log)"
fi
echo ""

# Final summary
echo "================================================================================"
echo "ALL DATA DOWNLOADS COMPLETE!"
echo "================================================================================"
echo ""
echo "📊 BigQuery Tables Created:"
echo "   - era5_weather_icing (temp/humidity/precip)"
echo "   - remit_unavailability_messages (operational notifications)"
echo "   - gfs_forecast_weather (7-day forecasts)"
echo "   - era5_3d_wind_components (u/v/shear for ramp prediction)"
echo ""
echo "📁 Logs saved to: $LOG_DIR/"
echo ""
echo "✅ Ready to continue with enhancement todos!"
echo "   Next: Validate icing conditions (filter to actual meteorological icing)"
echo "================================================================================"

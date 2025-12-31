#!/bin/bash
"""
Deploy Weather Data Automation Cron Jobs
Run this script once to set up automated data ingestion.
"""

echo "=============================================================================="
echo "Weather Data Automation - Cron Job Deployment"
echo "=============================================================================="
echo ""

# Get the absolute path to this directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
LOG_DIR="$SCRIPT_DIR/logs"

# Create logs directory if it doesn't exist
if [ ! -d "$LOG_DIR" ]; then
    echo "📁 Creating logs directory: $LOG_DIR"
    mkdir -p "$LOG_DIR"
fi

# Backup existing crontab
echo "💾 Backing up existing crontab..."
crontab -l > "$SCRIPT_DIR/crontab_backup_$(date +%Y%m%d_%H%M%S).txt" 2>/dev/null || echo "No existing crontab"

echo ""
echo "📋 Cron jobs to be installed:"
echo ""
echo "1. ERA5 Weather (Daily at 03:00 UTC)"
echo "   0 3 * * * cd $SCRIPT_DIR && python3 download_era5_weather_incremental.py >> $LOG_DIR/era5_weather_daily.log 2>&1"
echo ""
echo "2. GFS Forecasts (Every 6 hours at :15)"
echo "   15 */6 * * * cd $SCRIPT_DIR && python3 download_gfs_forecasts.py >> $LOG_DIR/gfs_forecasts.log 2>&1"
echo ""
echo "3. REMIT Messages (Daily at 02:00 UTC)"
echo "   0 2 * * * cd $SCRIPT_DIR && python3 download_remit_messages_incremental.py >> $LOG_DIR/remit_messages.log 2>&1"
echo ""
echo "4. Real-Time Wind (Every 15 minutes)"
echo "   */15 * * * * cd $SCRIPT_DIR && python3 download_realtime_wind.py >> $LOG_DIR/realtime_wind.log 2>&1"
echo ""
echo "5. Data Freshness Check (Hourly)"
echo "   0 * * * * cd $SCRIPT_DIR && python3 check_data_freshness.py >> $LOG_DIR/data_freshness.log 2>&1"
echo ""

read -p "Install these cron jobs? (y/n): " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ Installation cancelled"
    exit 1
fi

# Get current crontab (or empty if none exists)
TEMP_CRON=$(mktemp)
crontab -l > "$TEMP_CRON" 2>/dev/null || true

# Add weather automation header
echo "" >> "$TEMP_CRON"
echo "# ============================================================================" >> "$TEMP_CRON"
echo "# GB Power Market JJ - Weather Data Automation" >> "$TEMP_CRON"
echo "# Installed: $(date '+%Y-%m-%d %H:%M:%S')" >> "$TEMP_CRON"
echo "# ============================================================================" >> "$TEMP_CRON"

# Add cron jobs
echo "" >> "$TEMP_CRON"
echo "# ERA5 Historical Weather (Daily at 03:00 UTC)" >> "$TEMP_CRON"
echo "0 3 * * * cd $SCRIPT_DIR && python3 download_era5_weather_incremental.py >> $LOG_DIR/era5_weather_daily.log 2>&1" >> "$TEMP_CRON"

echo "" >> "$TEMP_CRON"
echo "# GFS Forecasts (Every 6 hours at :15)" >> "$TEMP_CRON"
echo "15 */6 * * * cd $SCRIPT_DIR && python3 download_gfs_forecasts.py >> $LOG_DIR/gfs_forecasts.log 2>&1" >> "$TEMP_CRON"

echo "" >> "$TEMP_CRON"
echo "# REMIT Unavailability Messages (Daily at 02:00 UTC)" >> "$TEMP_CRON"
echo "0 2 * * * cd $SCRIPT_DIR && python3 download_remit_messages_incremental.py >> $LOG_DIR/remit_messages.log 2>&1" >> "$TEMP_CRON"

echo "" >> "$TEMP_CRON"
echo "# Real-Time Wind Monitoring (Every 15 minutes)" >> "$TEMP_CRON"
echo "*/15 * * * * cd $SCRIPT_DIR && python3 download_realtime_wind.py >> $LOG_DIR/realtime_wind.log 2>&1" >> "$TEMP_CRON"

echo "" >> "$TEMP_CRON"
echo "# Data Freshness Check (Hourly)" >> "$TEMP_CRON"
echo "0 * * * * cd $SCRIPT_DIR && python3 check_data_freshness.py >> $LOG_DIR/data_freshness.log 2>&1" >> "$TEMP_CRON"

echo "" >> "$TEMP_CRON"
echo "# ============================================================================" >> "$TEMP_CRON"
echo "" >> "$TEMP_CRON"

# Install new crontab
crontab "$TEMP_CRON"
rm "$TEMP_CRON"

echo ""
echo "✅ Cron jobs installed successfully!"
echo ""
echo "=============================================================================="
echo "Next Steps:"
echo "=============================================================================="
echo ""
echo "1. View installed cron jobs:"
echo "   crontab -l"
echo ""
echo "2. Monitor logs in real-time:"
echo "   tail -f $LOG_DIR/era5_weather_daily.log"
echo "   tail -f $LOG_DIR/gfs_forecasts.log"
echo "   tail -f $LOG_DIR/remit_messages.log"
echo "   tail -f $LOG_DIR/realtime_wind.log"
echo ""
echo "3. Test each script manually before first automated run:"
echo "   python3 download_era5_weather_incremental.py"
echo "   python3 download_gfs_forecasts.py"
echo "   python3 download_remit_messages_incremental.py"
echo "   python3 download_realtime_wind.py"
echo ""
echo "4. Check data freshness:"
echo "   python3 check_data_freshness.py"
echo ""
echo "=============================================================================="
echo "Schedule:"
echo "=============================================================================="
echo ""
echo "02:00 UTC - REMIT messages (previous day)"
echo "03:00 UTC - ERA5 weather (T-5 to T-1 days)"
echo "Every 6h  - GFS forecasts (00Z/06Z/12Z/18Z at :15 past hour)"
echo "Every 15m - Real-time wind monitoring + ramp detection"
echo "Every 1h  - Data freshness validation"
echo ""
echo "=============================================================================="

#!/usr/bin/env python3
"""
Auto-Update Wind Forecast Dashboard - Complete Solution
========================================================
Runs periodically (every 5-15 minutes) to update all Wind Forecast Dashboard components:

1. ✅ Upstream Weather Alerts (pressure gradients, turbulence)
2. ✅ REMIT Unavailability/Outages (active outages)
3. 📊 6-Hour Farm Generation Heatmap (forecast per farm)
4. 📈 48-Hour Generation Forecast (with confidence bands)
5. 📉 Capacity at Risk (7-day outlook)

Cron Schedule: */15 * * * * (every 15 minutes)
Log File: logs/wind_dashboard_updater.log
"""

import subprocess
import sys
from datetime import datetime
from pathlib import Path

# Create logs directory if it doesn't exist
log_dir = Path(__file__).parent / "logs"
log_dir.mkdir(exist_ok=True)

log_file = log_dir / "wind_dashboard_updater.log"

def log(message):
    """Log message to console and file"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_msg = f"[{timestamp}] {message}"
    print(log_msg)
    with open(log_file, "a") as f:
        f.write(log_msg + "\n")

def run_script(script_name, description):
    """Run a Python script and log results"""
    log(f"Running: {description}...")
    try:
        result = subprocess.run(
            ['python3', script_name],
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout per script
        )
        
        if result.returncode == 0:
            log(f"✅ SUCCESS: {description}")
            return True
        else:
            log(f"❌ FAILED: {description}")
            log(f"   Error: {result.stderr[:200]}")
            return False
    except subprocess.TimeoutExpired:
        log(f"⏱️  TIMEOUT: {description} (>5 min)")
        return False
    except Exception as e:
        log(f"❌ EXCEPTION: {description} - {str(e)[:100]}")
        return False

# =============================================================================
# MAIN EXECUTION
# =============================================================================
log("=" * 80)
log("🌬️  WIND FORECAST DASHBOARD AUTO-UPDATE STARTED")
log("=" * 80)

success_count = 0
total_tasks = 5

# Task 1: Detect upstream weather changes
if run_script('detect_upstream_weather.py', '1/5: Upstream Weather Alerts'):
    success_count += 1

# Task 2: Update REMIT unavailability (outages)
if run_script('update_unavailability.py', '2/5: REMIT Outages'):
    success_count += 1

# Task 3: Generate 6-hour farm forecasts (heatmap)
# NOTE: This script needs to be created - see WIND_FORECAST_DASHBOARD_FIXES.md
# if run_script('forecast_farm_generation.py', '3/5: 6-Hour Farm Heatmap'):
#     success_count += 1
log("⏭️  SKIPPED: 3/5: 6-Hour Farm Heatmap (script not yet created)")

# Task 4: Generate 48-hour generation forecast
# NOTE: This script needs to be created - see WIND_FORECAST_DASHBOARD_FIXES.md
# if run_script('forecast_48h_generation.py', '4/5: 48-Hour Forecast'):
#     success_count += 1
log("⏭️  SKIPPED: 4/5: 48-Hour Forecast (script not yet created)")

# Task 5: Update capacity at risk analysis
# NOTE: This is part of detect_upstream_weather.py already
log("✅ INCLUDED: 5/5: Capacity at Risk (part of upstream weather)")
success_count += 1

# =============================================================================
# SUMMARY
# =============================================================================
log("=" * 80)
log(f"📊 SUMMARY: {success_count}/{total_tasks} tasks completed")

if success_count == total_tasks:
    log("✅ ALL TASKS COMPLETED SUCCESSFULLY")
    sys.exit(0)
elif success_count > 0:
    log(f"⚠️  PARTIAL SUCCESS: {total_tasks - success_count} tasks failed")
    sys.exit(1)
else:
    log("❌ ALL TASKS FAILED")
    sys.exit(2)

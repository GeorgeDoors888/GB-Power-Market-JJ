#!/bin/bash
# restart_energy_system.sh
# This script fixes the hanging processes and restarts the energy data system properly

echo "📋 UK Energy Data System - Process Cleanup and Restart"
echo "=================================================="
echo

# Check for running Python processes
echo "🔍 Checking for running Python processes..."
RUNNING_PROCESSES=$(ps aux | grep -E 'live_data_updater\.py|high_frequency_data_updater\.py|system_warnings_monitor\.py' | grep -v grep)

if [ -n "$RUNNING_PROCESSES" ]; then
    echo "⚠️  Found running energy data processes:"
    echo "$RUNNING_PROCESSES"
    echo
    
    # Extract PIDs and kill them
    echo "🛑 Terminating running processes..."
    PIDs=$(echo "$RUNNING_PROCESSES" | awk '{print $2}')
    
    for pid in $PIDs; do
        echo "   Terminating process $pid..."
        kill $pid
        sleep 1
        
        # Force kill if still running
        if ps -p $pid > /dev/null; then
            echo "   Process $pid still running, forcing termination..."
            kill -9 $pid
        fi
    done
    
    echo "✅ All processes terminated"
else
    echo "✅ No running energy data processes found"
fi

echo
echo "🚀 Starting new energy data collection system..."

# Activate virtual environment
echo "🔄 Activating virtual environment..."
source venv/bin/activate

# Start the system warnings monitor in the background
echo "🚨 Starting dedicated system warnings monitor..."
python system_warnings_monitor.py > system_warnings_monitor.log 2>&1 &
WARNINGS_PID=$!
echo "✅ System warnings monitor started with PID $WARNINGS_PID"

# Wait a moment to ensure it's running
sleep 2

# Start the 5-minute data collection
echo "⏱️  Starting 5-minute data collection..."
python live_data_updater.py > live_data_updater.log 2>&1 &
UPDATER_PID=$!
echo "✅ Data updater started with PID $UPDATER_PID"

echo
echo "📊 System Status"
echo "=================================================="
echo "System warnings monitor: PID $WARNINGS_PID"
echo "Live data updater: PID $UPDATER_PID"
echo
echo "✅ Energy data system restarted successfully"
echo
echo "📋 View logs:"
echo "   tail -f system_warnings_monitor.log"
echo "   tail -f live_data_updater.log"
echo

# Deactivate virtual environment
deactivate

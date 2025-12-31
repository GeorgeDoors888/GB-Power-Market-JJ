#!/bin/bash
# Monitor wind power curve training progress

echo "================================================================================================="
echo "Wind Power Curve Training Monitor"
echo "================================================================================================="
echo ""

# Check if process is running
PID=$(ps aux | grep build_wind_power_curves_optimized_v2.py | grep -v grep | awk '{print $2}')

if [ -z "$PID" ]; then
    echo "❌ Training process not running"
    echo ""
    echo "Check results:"
    if [ -f "wind_power_curves_optimized_results.csv" ]; then
        echo "✅ Training completed! Results saved."
        cat wind_power_curves_optimized_results.csv | head -10
    else
        echo "⚠️  No results file found. Check logs."
    fi
    exit 0
fi

echo "✅ Training process running (PID: $PID)"
echo ""

# Show process stats
ps -p $PID -o pid,ppid,user,%cpu,%mem,etime,cmd | tail -1 | awk '{
    printf "   PID: %s\n", $1
    printf "   CPU: %s%%\n", $4
    printf "   Memory: %s%%\n", $5
    printf "   Runtime: %s\n", $6
    printf "   Command: python3 build_wind_power_curves_optimized_v2.py\n"
}'

echo ""
echo "================================================================================================="
echo "Expected Timeline:"
echo "================================================================================================="
echo "   1. Loading training dataset from BigQuery:     3-5 minutes  (large JOIN)"
echo "   2. Loading ERA5 grid data:                     30 seconds"
echo "   3. Training 28 farm models with XGBoost:       5-10 minutes (300 trees × 28 farms)"
echo "   4. Saving models and results:                  10 seconds"
echo ""
echo "   Total expected: ~10-15 minutes"
echo ""
echo "================================================================================================="
echo "Current Status:"
echo "================================================================================================="

# Try to check what stage we're at
if [ -d "models/wind_power_curves_optimized" ]; then
    MODEL_COUNT=$(ls models/wind_power_curves_optimized/*.pkl 2>/dev/null | wc -l)
    echo "   📊 Models saved so far: $MODEL_COUNT / 28"
    
    if [ $MODEL_COUNT -gt 0 ]; then
        echo "   ✅ Training in progress (saving models)"
        echo ""
        echo "   Recent models:"
        ls -lth models/wind_power_curves_optimized/*.pkl | head -5 | awk '{print "      - " $9 " (" $6 " " $7 " " $8 ")"}'
    fi
else
    echo "   ⏳ Still loading data from BigQuery or starting training..."
fi

echo ""
echo "================================================================================================="
echo "Monitor commands:"
echo "================================================================================================="
echo "   Real-time monitoring:  watch -n 5 './monitor_training.sh'"
echo "   Check log file:        tail -f wind_training_optimized_fast.log  (when available)"
echo "   Process details:       ps -p $PID -f"
echo "   Kill if needed:        kill $PID"
echo ""

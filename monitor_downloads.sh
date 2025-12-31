#!/bin/bash
# Monitor background download processes

echo "=== DOWNLOAD MONITOR ==="
echo "Time: $(date)"
echo ""

# Check if processes are running
echo "=== RUNNING PROCESSES ==="
ps aux | grep -E "download_era5_optimized|download_gfs_optimized" | grep -v grep || echo "No downloads running"
echo ""

# ERA5 Status
if [ -f /tmp/era5_optimized.log ]; then
    echo "=== ERA5 WEATHER DATA (last 15 lines) ==="
    tail -15 /tmp/era5_optimized.log
    echo ""
    echo "Lines in log: $(wc -l < /tmp/era5_optimized.log)"
    echo "Rate limits: $(grep -c "Rate limited" /tmp/era5_optimized.log)"
    echo "Uploaded chunks: $(grep -c "Uploaded.*rows to BigQuery" /tmp/era5_optimized.log)"
else
    echo "ERA5: No log file found"
fi

echo ""
echo "================================================================"
echo ""

# GFS Status
if [ -f /tmp/gfs_optimized.log ]; then
    echo "=== GFS FORECASTS (last 15 lines) ==="
    tail -15 /tmp/gfs_optimized.log
    echo ""
    echo "Lines in log: $(wc -l < /tmp/gfs_optimized.log)"
    echo "Farms completed: $(grep -c "✅ Downloaded.*rows for" /tmp/gfs_optimized.log)"
    echo "Uploaded chunks: $(grep -c "Uploaded.*rows to BigQuery" /tmp/gfs_optimized.log)"
else
    echo "GFS: No log file found"
fi

echo ""
echo "================================================================"
echo ""
echo "Commands:"
echo "  Watch live: watch -n 10 /home/george/GB-Power-Market-JJ/monitor_downloads.sh"
echo "  ERA5 log: tail -f /tmp/era5_optimized.log"
echo "  GFS log: tail -f /tmp/gfs_optimized.log"

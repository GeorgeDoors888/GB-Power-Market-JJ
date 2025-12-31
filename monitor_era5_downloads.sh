#!/bin/bash
# Monitor ERA5 Downloads - Weather + Ocean/Wave

echo "=========================================="
echo "ERA5 DOWNLOAD PROGRESS MONITOR"
echo "=========================================="
echo ""

# Check weather download
echo "📊 WEATHER DATA (temp, humidity, precip, cloud, wind)"
echo "-------------------------------------------"
if pgrep -f "download_era5_icing_optimized.py" > /dev/null; then
    echo "✅ Status: RUNNING"
    echo "📝 Log: /tmp/era5_weather_download.log"
    echo ""
    echo "Latest entries:"
    tail -10 /tmp/era5_weather_download.log | grep -E "INFO|ERROR|✅|❌|📊" | tail -5
    echo ""
    
    # Count progress
    if [ -f /tmp/era5_weather_download.log ]; then
        completed=$(grep -c "✅ Uploaded" /tmp/era5_weather_download.log || echo "0")
        failed=$(grep -c "❌ Download failed" /tmp/era5_weather_download.log || echo "0")
        echo "Progress: $completed completed, $failed failed (out of 8,856 total)"
    fi
else
    echo "❌ Status: NOT RUNNING"
    if [ -f /tmp/era5_weather_download.log ]; then
        echo "Last log entry:"
        tail -3 /tmp/era5_weather_download.log
    fi
fi

echo ""
echo "=========================================="
echo ""

# Check ocean/wave download
echo "🌊 OCEAN/WAVE DATA (air density, drag, waves, spectral)"
echo "-------------------------------------------"
if pgrep -f "download_era5_ocean_waves.py" > /dev/null; then
    echo "✅ Status: RUNNING"
    echo "📝 Log: /tmp/era5_ocean_wave_download.log"
    echo ""
    echo "Latest entries:"
    tail -10 /tmp/era5_ocean_wave_download.log | grep -E "INFO|ERROR|✅|❌|📊" | tail -5
    echo ""
    
    # Count progress
    if [ -f /tmp/era5_ocean_wave_download.log ]; then
        completed=$(grep -c "✅ Uploaded" /tmp/era5_ocean_wave_download.log || echo "0")
        failed=$(grep -c "❌ Download failed" /tmp/era5_ocean_wave_download.log || echo "0")
        echo "Progress: $completed completed, $failed failed (out of 10,440 total)"
    fi
else
    echo "❌ Status: NOT RUNNING"
    if [ -f /tmp/era5_ocean_wave_download.log ]; then
        echo "Last log entry:"
        tail -3 /tmp/era5_ocean_wave_download.log
    fi
fi

echo ""
echo "=========================================="
echo "📊 SUMMARY"
echo "=========================================="
echo ""

# BigQuery row counts
echo "BigQuery row counts:"
python3 -c "
from google.cloud import bigquery
client = bigquery.Client(project='inner-cinema-476211-u9', location='US')

# Weather data
try:
    result = client.query('SELECT COUNT(*) as cnt FROM \`inner-cinema-476211-u9.uk_energy_prod.era5_weather_data\`').result()
    weather_rows = list(result)[0]['cnt']
    print(f'  Weather data: {weather_rows:,} rows')
except:
    print('  Weather data: 0 rows (table empty or not created)')

# Ocean/wave data
try:
    result = client.query('SELECT COUNT(*) as cnt FROM \`inner-cinema-476211-u9.uk_energy_prod.era5_ocean_wave_data\`').result()
    ocean_rows = list(result)[0]['cnt']
    print(f'  Ocean/wave data: {ocean_rows:,} rows')
except:
    print('  Ocean/wave data: 0 rows (table empty or not created)')
" 2>/dev/null

echo ""
echo "Estimated completion:"
echo "  Weather: 41 farms × 72 months × 3 vars = 8,856 requests → ~42 days"
echo "  Ocean/wave: 29 farms × 72 months × 5 vars = 10,440 requests → ~49 days"
echo ""
echo "To restart if stopped:"
echo "  cd /home/george/GB-Power-Market-JJ"
echo "  nohup python3 download_era5_icing_optimized.py > /tmp/era5_weather_download.log 2>&1 &"
echo "  nohup python3 download_era5_ocean_waves.py > /tmp/era5_ocean_wave_download.log 2>&1 &"
echo ""

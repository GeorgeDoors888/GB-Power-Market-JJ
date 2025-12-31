#!/bin/bash
# Monitor the historical wind data download progress

echo "==================================================================="
echo "Wind Data Download Monitor"
echo "==================================================================="

# Check if the download script is running
if pgrep -f "fetch_historic_wind_chunked.py" > /dev/null; then
    echo "✅ Download script is RUNNING"
    
    # Show the last 30 lines of output
    echo ""
    echo "Recent progress:"
    tail -30 /proc/$(pgrep -f "fetch_historic_wind_chunked.py")/fd/1 2>/dev/null || echo "  (output not accessible)"
else
    echo "⏸️  Download script is NOT running"
fi

echo ""
echo "-------------------------------------------------------------------"
echo "Checking BigQuery table..."
echo "-------------------------------------------------------------------"

python3 << 'EOF'
from google.cloud import bigquery
client = bigquery.Client(project='inner-cinema-476211-u9', location='US')

try:
    query = '''
    SELECT 
        COUNT(*) as total_rows,
        COUNT(DISTINCT farm_name) as num_farms,
        MIN(time_utc) as earliest,
        MAX(time_utc) as latest,
        AVG(wind_speed_100m) as avg_wind_100m
    FROM `inner-cinema-476211-u9.uk_energy_prod.openmeteo_wind_historic`
    '''
    df = client.query(query).to_dataframe()
    
    if len(df) > 0 and df['total_rows'][0] > 0:
        print(f"✅ openmeteo_wind_historic table EXISTS")
        print(f"   Rows: {int(df['total_rows'][0]):,}")
        print(f"   Farms: {int(df['num_farms'][0])}")
        print(f"   Date range: {df['earliest'][0]} to {df['latest'][0]}")
        print(f"   Avg wind (100m): {df['avg_wind_100m'][0]:.1f} m/s")
        
        # Check by farm
        farm_query = '''
        SELECT 
            farm_name,
            COUNT(*) as rows,
            MIN(time_utc) as first_date,
            MAX(time_utc) as last_date
        FROM `inner-cinema-476211-u9.uk_energy_prod.openmeteo_wind_historic`
        GROUP BY farm_name
        ORDER BY rows DESC
        '''
        farm_df = client.query(farm_query).to_dataframe()
        
        print(f"\n   Farms downloaded:")
        for _, row in farm_df.iterrows():
            years = (row['last_date'] - row['first_date']).days / 365.25
            print(f"     {row['farm_name']:30s} {int(row['rows']):6,} rows ({years:.1f} years)")
    else:
        print("⏳ Table exists but no data yet")
        
except Exception as e:
    if "Not found" in str(e):
        print("⏳ Table not created yet (waiting for first upload)")
    else:
        print(f"❌ Error: {e}")
EOF

echo ""
echo "==================================================================="
echo "Next steps after download completes:"
echo "  1. Run: python3 build_wind_power_curves.py"
echo "  2. Run: python3 realtime_wind_forecasting.py"
echo "==================================================================="

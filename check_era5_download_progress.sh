#!/bin/bash
# Check ERA5 download progress and data quality
# Run after cron job completes (after 3 AM UTC)

echo "════════════════════════════════════════════════════════════════"
echo "ERA5 DOWNLOAD PROGRESS CHECK"
echo "════════════════════════════════════════════════════════════════"
echo ""

# Check cron job ran
echo "📅 Last cron job run:"
grep -a "ERA5" /var/log/cron | tail -5
echo ""

# Check latest log
LOG_FILE="/home/george/GB-Power-Market-JJ/logs/era5_download_with_gusts_$(date +%Y%m%d).log"
if [ -f "$LOG_FILE" ]; then
    echo "📊 Today's download log:"
    echo "────────────────────────────────────────────────────────────────"
    cat "$LOG_FILE"
    echo "────────────────────────────────────────────────────────────────"
else
    echo "⚠️  Log file not found: $LOG_FILE"
    echo "   Cron may not have run yet (scheduled for 3 AM UTC)"
fi
echo ""

# Check BigQuery data
echo "🗄️  BigQuery Data Status:"
python3 -c "
from google.cloud import bigquery
import os
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = '/home/george/GB-Power-Market-JJ/inner-cinema-credentials.json'

client = bigquery.Client(project='inner-cinema-476211-u9', location='US')

# Check old table
query_old = '''
SELECT 
    COUNT(DISTINCT farm_name) as farms,
    COUNT(*) as total_rows
FROM \`inner-cinema-476211-u9.uk_energy_prod.era5_weather_data\`
'''
df_old = client.query(query_old).to_dataframe()
print(f'  Old table (era5_weather_data):')
print(f'    Farms: {df_old[\"farms\"].values[0]}')
print(f'    Rows: {df_old[\"total_rows\"].values[0]:,}')
print()

# Check new table (if exists)
try:
    query_new = '''
    SELECT 
        COUNT(DISTINCT farm_name) as farms,
        COUNT(*) as total_rows,
        COUNT(DISTINCT DATE(timestamp)) as days
    FROM \`inner-cinema-476211-u9.uk_energy_prod.era5_weather_data_v2\`
    '''
    df_new = client.query(query_new).to_dataframe()
    print(f'  New table (era5_weather_data_v2):')
    print(f'    Farms: {df_new[\"farms\"].values[0]}')
    print(f'    Rows: {df_new[\"total_rows\"].values[0]:,}')
    print(f'    Days: {df_new[\"days\"].values[0]:,}')
    print()
    
    # Check if gust data exists
    query_gusts = '''
    SELECT 
        COUNT(*) as rows_with_gusts,
        AVG(wind_gusts_10m_kmh) as avg_gust_kmh,
        AVG(wind_gusts_10m_ms) as avg_gust_ms
    FROM \`inner-cinema-476211-u9.uk_energy_prod.era5_weather_data_v2\`
    WHERE wind_gusts_10m_kmh IS NOT NULL
    '''
    df_gusts = client.query(query_gusts).to_dataframe()
    print(f'  Gust Data:')
    print(f'    Rows with gusts: {df_gusts[\"rows_with_gusts\"].values[0]:,}')
    print(f'    Avg gust: {df_gusts[\"avg_gust_ms\"].values[0]:.1f} m/s ({df_gusts[\"avg_gust_kmh\"].values[0]:.1f} km/h)')
    
except Exception as e:
    print(f'  New table not yet created: {e}')
"

echo ""
echo "════════════════════════════════════════════════════════════════"
echo "✅ Check complete"
echo "════════════════════════════════════════════════════════════════"

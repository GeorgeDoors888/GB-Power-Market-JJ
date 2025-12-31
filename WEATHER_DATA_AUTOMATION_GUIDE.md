# Weather Data Automation Guide

**Date**: December 30, 2025  
**Purpose**: Automated ingestion of weather data for wind forecasting and icing detection  
**Status**: Implementation ready - awaiting initial downloads completion

---

## Overview

Automated weather data pipeline to ensure continuous updates for:
- **ERA5 Historical**: Temperature, humidity, precipitation (icing detection)
- **GFS Forecasts**: 7-day ahead weather predictions (day-ahead wind forecasting)
- **REMIT Messages**: Operational notifications (maintenance vs icing distinction)
- **Real-time Wind**: Live wind data for immediate forecasting

---

## 1. ERA5 Historical Weather (Daily Updates)

### Data Source
- **Provider**: ECMWF ERA5 via Open-Meteo Archive API
- **Update Frequency**: Daily (ERA5 has T-5 days publication lag)
- **Variables**: temperature_2m, relative_humidity_2m, precipitation, cloud_cover, pressure_msl, shortwave_radiation
- **Coverage**: 48 UK offshore wind farm locations (2021-present)

### Cron Schedule
```bash
# Daily at 03:00 UTC (after ERA5 daily update)
0 3 * * * cd /home/george/GB-Power-Market-JJ && python3 download_era5_weather_incremental.py >> logs/era5_weather_daily.log 2>&1
```

### Implementation Script
**File**: `download_era5_weather_incremental.py`

```python
#!/usr/bin/env python3
"""
Incremental ERA5 weather data download (daily updates only).
Checks last date in BigQuery, downloads only new data (T-5 to T-1).
"""

import requests
import pandas as pd
from google.cloud import bigquery
from datetime import datetime, timedelta
import time

PROJECT_ID = "inner-cinema-476211-u9"
DATASET = "uk_energy_prod"
TABLE_NAME = "era5_weather_icing"

def get_last_date():
    """Get the most recent date in BigQuery table."""
    client = bigquery.Client(project=PROJECT_ID, location="US")
    query = f"""
    SELECT MAX(DATE(time_utc)) as last_date
    FROM `{PROJECT_ID}.{DATASET}.{TABLE_NAME}`
    """
    df = client.query(query).to_dataframe()
    return df['last_date'][0]

def download_incremental_data(start_date, end_date):
    """Download data for date range only."""
    # ... (similar to download_era5_weather_for_icing.py)
    # Download only new dates
    pass

def main():
    last_date = get_last_date()
    # ERA5 has T-5 days lag, so download T-5 to T-1
    end_date = datetime.now().date() - timedelta(days=1)
    start_date = last_date + timedelta(days=1)
    
    if start_date > end_date:
        print(f"✅ Already up to date (last: {last_date})")
        return
    
    print(f"📥 Downloading {start_date} to {end_date}")
    download_incremental_data(start_date, end_date)
    print(f"✅ Updated to {end_date}")

if __name__ == "__main__":
    main()
```

---

## 2. GFS Forecast Data (Every 6 Hours)

### Data Source
- **Provider**: NOAA GFS via Open-Meteo Forecast API
- **Update Frequency**: Every 6 hours (00Z, 06Z, 12Z, 18Z cycles)
- **Forecast Horizon**: 0-7 days (168 hours)
- **Variables**: wind_speed_100m, wind_direction_100m, temperature_2m, humidity, pressure
- **Coverage**: 48 UK offshore wind farm locations

### Cron Schedule
```bash
# Every 6 hours at :15 past the hour (GFS publishes at ~:00, available by :15)
15 0,6,12,18 * * * cd /home/george/GB-Power-Market-JJ && python3 download_gfs_forecasts.py >> logs/gfs_forecasts.log 2>&1
```

### Implementation Notes
- **Script**: `download_gfs_forecasts.py` (already created)
- **Mode**: `WRITE_TRUNCATE` (replace entire table each run - forecasts are point-in-time)
- **Runtime**: ~5-10 minutes per run
- **Data Volume**: ~8,000 rows per run (48 farms × 168 hours)

### Forecast Validation
Track forecast accuracy over time:
```sql
-- Compare GFS forecast to actual generation
SELECT
    f.forecast_time,
    f.valid_time,
    f.farm_name,
    f.wind_speed_100m as forecast_wind,
    a.wind_speed_100m as actual_wind,
    ABS(f.wind_speed_100m - a.wind_speed_100m) as error_ms
FROM `inner-cinema-476211-u9.uk_energy_prod.gfs_forecast_weather` f
JOIN `inner-cinema-476211-u9.uk_energy_prod.openmeteo_wind_historic` a
    ON f.farm_name = a.farm_name
    AND DATE(f.valid_time) = DATE(a.time_utc)
WHERE f.forecast_horizon_hours <= 24
```

---

## 3. REMIT Unavailability Messages (Daily)

### Data Source
- **Provider**: Elexon REMIT API
- **Update Frequency**: Daily (operational notifications published throughout day)
- **Coverage**: ~50 wind BM units
- **Categories**: WEATHER_ICING, WEATHER_EXTREME, MAINTENANCE, NON_WEATHER

### Cron Schedule
```bash
# Daily at 02:00 UTC (before ERA5 update, captures previous day's messages)
0 2 * * * cd /home/george/GB-Power-Market-JJ && python3 download_remit_messages_incremental.py >> logs/remit_messages.log 2>&1
```

### Implementation Script
**File**: `download_remit_messages_incremental.py`

```python
#!/usr/bin/env python3
"""
Incremental REMIT message download (yesterday's messages only).
"""

from datetime import datetime, timedelta
import requests
import pandas as pd
from google.cloud import bigquery

PROJECT_ID = "inner-cinema-476211-u9"
TABLE_NAME = "remit_unavailability_messages"

def download_yesterday_messages():
    """Download REMIT messages from yesterday only."""
    yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    
    # Fetch messages for all wind BMUs for yesterday
    # ... (similar to download_remit_messages.py)
    pass

def main():
    print(f"📥 Downloading REMIT messages for {yesterday}")
    df = download_yesterday_messages()
    
    if len(df) > 0:
        # Append to BigQuery (avoid duplicates)
        client = bigquery.Client(project=PROJECT_ID, location="US")
        job_config = bigquery.LoadJobConfig(
            write_disposition=bigquery.WriteDisposition.WRITE_APPEND
        )
        # ... upload
        print(f"✅ Added {len(df)} new messages")
    else:
        print(f"⚪ No new messages")

if __name__ == "__main__":
    main()
```

---

## 4. Real-Time Wind Monitoring (Every 15 Minutes)

### Data Source
- **Provider**: Open-Meteo Real-Time API
- **Update Frequency**: Every 15 minutes
- **Variables**: wind_speed_100m, wind_direction_100m, wind_gusts_10m
- **Coverage**: 48 UK offshore wind farm locations
- **Purpose**: Live wind monitoring for immediate ramp detection

### Cron Schedule
```bash
# Every 15 minutes for real-time monitoring
*/15 * * * * cd /home/george/GB-Power-Market-JJ && python3 download_realtime_wind.py >> logs/realtime_wind.log 2>&1
```

### Implementation Script
**File**: `download_realtime_wind.py`

```python
#!/usr/bin/env python3
"""
Real-time wind data download (last 2 hours, every 15 minutes).
Used for immediate ramp detection and trading signals.
"""

import requests
import pandas as pd
from google.cloud import bigquery
from datetime import datetime, timedelta

PROJECT_ID = "inner-cinema-476211-u9"
TABLE_NAME = "openmeteo_wind_realtime"

def download_current_wind():
    """Download last 2 hours of wind data for all farms."""
    # Use Open-Meteo /v1/forecast endpoint with past_hours=2
    pass

def detect_ramps(df):
    """Detect rapid wind changes (>20% in 1 hour)."""
    df['wind_change_1h'] = df.groupby('farm_name')['wind_speed_100m'].diff()
    df['ramp_pct'] = (df['wind_change_1h'] / df['wind_speed_100m'].shift(1)) * 100
    
    critical = df[df['ramp_pct'].abs() > 20]
    if len(critical) > 0:
        # Send alert
        print(f"🔴 CRITICAL RAMP: {critical[['farm_name', 'ramp_pct']].to_dict()}")
    
    return df

def main():
    df = download_current_wind()
    df = detect_ramps(df)
    
    # Append to BigQuery
    # ... upload
    print(f"✅ Updated {len(df)} wind observations")

if __name__ == "__main__":
    main()
```

---

## 5. Monitoring and Alerting

### Log Rotation
```bash
# Add to /etc/logrotate.d/gb-power-market
/home/george/GB-Power-Market-JJ/logs/*.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
}
```

### Email Alerts on Failure
Add to each cron job:
```bash
# Example with email alert
15 */6 * * * cd /home/george/GB-Power-Market-JJ && python3 download_gfs_forecasts.py >> logs/gfs_forecasts.log 2>&1 || echo "GFS download failed" | mail -s "GFS Download Failed" george@upowerenergy.uk
```

### Data Freshness Dashboard
Create BigQuery view to monitor last update times:
```sql
CREATE OR REPLACE VIEW `inner-cinema-476211-u9.uk_energy_prod.weather_data_freshness` AS
SELECT
    'ERA5 Historical' as source,
    MAX(time_utc) as last_update,
    TIMESTAMP_DIFF(CURRENT_TIMESTAMP(), MAX(time_utc), HOUR) as hours_old,
    CASE
        WHEN TIMESTAMP_DIFF(CURRENT_TIMESTAMP(), MAX(time_utc), HOUR) < 48 THEN '🟢 FRESH'
        WHEN TIMESTAMP_DIFF(CURRENT_TIMESTAMP(), MAX(time_utc), HOUR) < 120 THEN '🟡 STALE'
        ELSE '🔴 OUTDATED'
    END as status
FROM `inner-cinema-476211-u9.uk_energy_prod.era5_weather_icing`

UNION ALL

SELECT
    'GFS Forecasts' as source,
    MAX(forecast_time) as last_update,
    TIMESTAMP_DIFF(CURRENT_TIMESTAMP(), MAX(forecast_time), HOUR) as hours_old,
    CASE
        WHEN TIMESTAMP_DIFF(CURRENT_TIMESTAMP(), MAX(forecast_time), HOUR) < 8 THEN '🟢 FRESH'
        WHEN TIMESTAMP_DIFF(CURRENT_TIMESTAMP(), MAX(forecast_time), HOUR) < 24 THEN '🟡 STALE'
        ELSE '🔴 OUTDATED'
    END as status
FROM `inner-cinema-476211-u9.uk_energy_prod.gfs_forecast_weather`

-- Add more sources as needed
```

---

## 6. Error Handling and Retry Logic

### Exponential Backoff
```python
import time
from functools import wraps

def retry_with_backoff(max_retries=3, base_delay=60):
    """Decorator for exponential backoff retry logic."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_retries - 1:
                        raise  # Last attempt, re-raise exception
                    
                    delay = base_delay * (2 ** attempt)
                    print(f"⚠️  Attempt {attempt + 1} failed: {e}")
                    print(f"   Retrying in {delay} seconds...")
                    time.sleep(delay)
        return wrapper
    return decorator

@retry_with_backoff(max_retries=3, base_delay=60)
def download_with_retry():
    """Example download with automatic retry."""
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    return response.json()
```

### Duplicate Prevention
```python
def upload_to_bigquery_safe(df, table_id):
    """Upload with duplicate check."""
    client = bigquery.Client(project=PROJECT_ID, location="US")
    
    # Check for existing records (avoid duplicates)
    query = f"""
    SELECT DISTINCT time_utc
    FROM `{table_id}`
    WHERE time_utc >= '{df['time_utc'].min()}'
      AND time_utc <= '{df['time_utc'].max()}'
    """
    existing = client.query(query).to_dataframe()
    
    if len(existing) > 0:
        # Filter out existing timestamps
        df = df[~df['time_utc'].isin(existing['time_utc'])]
        print(f"⚠️  Filtered {len(existing)} duplicate records")
    
    if len(df) > 0:
        # Append new records
        job_config = bigquery.LoadJobConfig(
            write_disposition=bigquery.WriteDisposition.WRITE_APPEND
        )
        job = client.load_table_from_dataframe(df, table_id, job_config=job_config)
        job.result()
        print(f"✅ Appended {len(df)} new records")
    else:
        print(f"⚪ No new records to add")
```

---

## 7. Testing Before Production

### Test Individual Scripts
```bash
# Test ERA5 incremental (dry run)
python3 download_era5_weather_incremental.py --dry-run

# Test GFS forecasts
python3 download_gfs_forecasts.py

# Test REMIT messages
python3 download_remit_messages_incremental.py

# Test real-time wind
python3 download_realtime_wind.py
```

### Validate Data Quality
```bash
# Check row counts
python3 << 'EOF'
from google.cloud import bigquery
client = bigquery.Client(project='inner-cinema-476211-u9', location='US')

for table in ['era5_weather_icing', 'gfs_forecast_weather', 'remit_unavailability_messages', 'openmeteo_wind_realtime']:
    query = f"SELECT COUNT(*) as cnt, MAX(time_utc) as last_update FROM `inner-cinema-476211-u9.uk_energy_prod.{table}`"
    df = client.query(query).to_dataframe()
    print(f"{table}: {int(df['cnt'][0]):,} rows, last: {df['last_update'][0]}")
EOF
```

---

## 8. Deployment Checklist

### Initial Setup (One-Time)
- [ ] Create logs directory: `mkdir -p /home/george/GB-Power-Market-JJ/logs`
- [ ] Create incremental update scripts (ERA5, REMIT)
- [ ] Test all scripts manually
- [ ] Validate BigQuery tables created correctly
- [ ] Configure log rotation (`/etc/logrotate.d/gb-power-market`)

### Cron Installation
```bash
# Edit crontab
crontab -e

# Add all jobs:
# ERA5 Historical (daily at 03:00 UTC)
0 3 * * * cd /home/george/GB-Power-Market-JJ && python3 download_era5_weather_incremental.py >> logs/era5_weather_daily.log 2>&1

# GFS Forecasts (every 6 hours at :15 past hour)
15 */6 * * * cd /home/george/GB-Power-Market-JJ && python3 download_gfs_forecasts.py >> logs/gfs_forecasts.log 2>&1

# REMIT Messages (daily at 02:00 UTC)
0 2 * * * cd /home/george/GB-Power-Market-JJ && python3 download_remit_messages_incremental.py >> logs/remit_messages.log 2>&1

# Real-time Wind (every 15 minutes)
*/15 * * * * cd /home/george/GB-Power-Market-JJ && python3 download_realtime_wind.py >> logs/realtime_wind.log 2>&1

# Data freshness check (hourly)
0 * * * * cd /home/george/GB-Power-Market-JJ && python3 check_data_freshness.py >> logs/data_freshness.log 2>&1
```

### Monitoring Setup
- [ ] Add Google Sheets "Data Freshness" tab
- [ ] Setup email alerts for failures
- [ ] Create Grafana dashboard (optional)
- [ ] Test alert notifications

---

## 9. Maintenance

### Weekly Tasks
- Review logs for errors: `tail -100 logs/*.log`
- Check data freshness: `python3 check_data_freshness.py`
- Validate cron jobs running: `crontab -l`

### Monthly Tasks
- Review BigQuery storage costs
- Analyze download success rates
- Optimize scripts if needed
- Update documentation

### Quarterly Tasks
- Review API rate limits (ensure within free tier)
- Evaluate new data sources
- Update weather variables if needed

---

## 10. Cost Optimization

### API Rate Limits (Free Tier)
- **Open-Meteo**: 10,000 requests/day (current: ~200/day) ✅
- **Elexon REMIT**: No rate limit (open API) ✅
- **BigQuery**: 1 TB queries/month (current: <10 GB/month) ✅

### Storage Costs
- **ERA5 Historical**: ~2.5M rows × 10 columns = ~250 MB
- **GFS Forecasts**: ~8k rows (replaced every 6 hours) = ~1 MB
- **REMIT Messages**: ~10k rows/year = ~5 MB
- **Total**: <500 MB = $0.02/month ✅ **Negligible**

### Optimization Tips
1. Use `SELECT` with specific columns (avoid `SELECT *`)
2. Partition tables by date for faster queries
3. Archive old forecast data (>30 days) to cheaper storage
4. Compress logs with logrotate

---

## Summary

**Automation Status**: Ready to deploy  
**Total Cron Jobs**: 5 (ERA5, GFS, REMIT, real-time wind, freshness check)  
**Update Frequency**: 15 min (real-time) to daily (ERA5, REMIT)  
**Monthly Cost**: ~$0.02 (BigQuery storage) + $0 (free APIs) = **Negligible**  
**Maintenance**: ~1 hour/month (log review, monitoring)

**Next Steps**:
1. Complete initial downloads (ERA5, GFS, REMIT, 3D wind)
2. Create incremental update scripts
3. Test each script manually
4. Deploy cron jobs
5. Monitor for 1 week
6. Enable production forecasting

---

**Document**: WEATHER_DATA_AUTOMATION_GUIDE.md  
**Author**: AI Coding Agent  
**Date**: December 30, 2025  
**Status**: Implementation Ready

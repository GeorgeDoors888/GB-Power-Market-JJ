# ERA5 CDS Setup & Download Guide

**Quick Start**: 5-minute setup → 2-6 hour download → Complete historical weather data

---

## Step 1: CDS Account Setup (5 minutes)

### 1.1 Register for Free Account
```bash
# Open browser to:
https://cds.climate.copernicus.eu/user/register
```

- Fill in name, email, organization
- Accept Copernicus License V1.1 (CC-BY-4.0)
- Verify email

### 1.2 Get API Key
```bash
# Login and go to:
https://cds.climate.copernicus.eu/api-how-to
```

You'll see something like:
```
url: https://cds.climate.copernicus.eu/api/v2
key: 12345:abcdef12-3456-7890-abcd-ef1234567890
```

### 1.3 Create Configuration File
```bash
# Create ~/.cdsapirc with your credentials
cat > ~/.cdsapirc << 'EOF'
url: https://cds.climate.copernicus.eu/api/v2
key: YOUR_UID:YOUR_API_KEY
EOF

# Replace YOUR_UID:YOUR_API_KEY with your actual key from step 1.2

# Secure the file
chmod 600 ~/.cdsapirc
```

---

## Step 2: Install Dependencies

```bash
cd /home/george/GB-Power-Market-JJ

# Install Python packages
pip3 install --user cdsapi netCDF4 xarray

# Verify existing packages (already installed)
python3 -c "import google.cloud.bigquery; print('✅ BigQuery OK')"
python3 -c "import pandas; print('✅ Pandas OK')"
```

---

## Step 3: Test CDS Connection

```bash
# Quick test (downloads 1 day of data)
python3 -c "
import cdsapi
client = cdsapi.Client()
print('✅ CDS API connected successfully')
"
```

**Expected**: `✅ CDS API connected successfully`  
**If error**: Check ~/.cdsapirc has correct UID:API_KEY format

---

## Step 4: Run Download (Background Recommended)

### Option A: Background Download (Recommended)
```bash
# Start download in background
nohup python3 download_era5_cds.py > /tmp/era5_cds_download.log 2>&1 &

# Get process ID
echo $! > /tmp/era5_cds_download.pid

# Monitor progress
tail -f /tmp/era5_cds_download.log

# Check progress periodically
grep "✅ Chunk" /tmp/era5_cds_download.log | wc -l  # Count completed chunks
```

### Option B: Foreground Download
```bash
python3 download_era5_cds.py
```

---

## Step 5: Monitor Progress

### Check Log File
```bash
# Live monitoring
tail -f /tmp/era5_cds_download.log

# Summary stats
grep "Farm" /tmp/era5_cds_download.log | tail -5
grep "✅ Chunk" /tmp/era5_cds_download.log | wc -l
grep "❌" /tmp/era5_cds_download.log | wc -l
```

### Check BigQuery Data
```bash
python3 -c "
from google.cloud import bigquery
client = bigquery.Client(project='inner-cinema-476211-u9', location='US')

query = '''
SELECT 
    COUNT(*) as total_rows,
    COUNT(DISTINCT farm_name) as farms,
    MIN(time_utc) as earliest,
    MAX(time_utc) as latest
FROM \`inner-cinema-476211-u9.uk_energy_prod.era5_weather_data\`
'''

df = client.query(query).to_dataframe()
print(df)
"
```

### Stop Download (if needed)
```bash
# Get PID
PID=$(cat /tmp/era5_cds_download.pid)

# Stop gracefully
kill $PID

# Force stop if needed
kill -9 $PID
```

---

## Expected Download Stats

**Total Operations**: 41 farms × 11 chunks (6-month periods) = **451 chunks**

**Timeline**:
- Per chunk: 6 minutes wait (CDS rate limit) + 2 min download = 8 min
- Total time: 451 × 8 min = **60 hours** (2.5 days)
- **Optimization**: Run on faster connection or reduce wait time to 3 min (30 hours)

**Data Volume**:
- Per farm: ~52,608 hours (2020-2025) × 13 variables = 684k datapoints
- Total: 41 farms × 684k = **28M rows** in BigQuery
- Storage: ~5 GB (BigQuery compressed)

**Cost**: **£0.00** (FREE tier)
- CDS API: Free with Copernicus license
- BigQuery storage: Free tier (10 GB)
- BigQuery queries: Free tier (1 TB/month)

---

## Troubleshooting

### Error: "Client has not agreed to the required terms and conditions"
**Fix**: Login to CDS and accept license at:
```
https://cds.climate.copernicus.eu/cdsapp#!/terms/licence-to-use-copernicus-products
```

### Error: "Invalid API key"
**Fix**: Check ~/.cdsapirc format (no quotes around key):
```bash
cat ~/.cdsapirc
# Should be:
# url: https://cds.climate.copernicus.eu/api/v2
# key: 12345:abcdef12-3456-7890-abcd-ef1234567890
```

### Error: "Rate limit exceeded"
**Fix**: Script already includes 6-minute delays. If still hitting limits:
```python
# Edit download_era5_cds.py line 378:
wait_time = 600  # Increase to 10 minutes
```

### Error: "Request timed out"
**Fix**: CDS server busy. Script will auto-retry. If persistent:
- Download during off-peak hours (weekends, evenings UTC)
- Reduce chunk size to 3 months instead of 6

### BigQuery Upload Failures
**Fix**: Check credentials:
```bash
export GOOGLE_APPLICATION_CREDENTIALS="/home/george/GB-Power-Market-JJ/inner-cinema-credentials.json"
python3 -c "from google.cloud import bigquery; bigquery.Client(project='inner-cinema-476211-u9')"
```

---

## What Gets Downloaded

### Variables (6 total)
1. **2m_temperature** - Temperature at 2m height (°C)
2. **2m_dewpoint_temperature** - Dewpoint for humidity calc (°C)
3. **total_precipitation** - Hourly precipitation (mm)
4. **total_cloud_cover** - Cloud cover fraction (%)
5. **100m_u_component_of_wind** - Wind U component (m/s)
6. **100m_v_component_of_wind** - Wind V component (m/s)

### Derived Variables (4 calculated)
7. **relative_humidity_2m** - Calculated from temp/dewpoint (%)
8. **wind_speed_100m** - √(u² + v²) (m/s)
9. **wind_direction_100m** - atan2(u, v) (degrees)

### BigQuery Schema
```sql
CREATE TABLE era5_weather_data (
    farm_name STRING,
    time_utc TIMESTAMP,
    latitude FLOAT64,
    longitude FLOAT64,
    temperature_2m FLOAT64,           -- °C
    dewpoint_2m FLOAT64,              -- °C
    relative_humidity_2m FLOAT64,     -- %
    precipitation FLOAT64,            -- mm
    cloud_cover FLOAT64,              -- %
    wind_u_100m FLOAT64,              -- m/s
    wind_v_100m FLOAT64,              -- m/s
    wind_speed_100m FLOAT64,          -- m/s
    wind_direction_100m FLOAT64       -- degrees
)
```

---

## License & Attribution

**Data Source**: ERA5 hourly data on single levels from 1940 to present  
**Provider**: Copernicus Climate Change Service (C3S)  
**Copyright**: © ECMWF  
**License**: CC-BY-4.0 (https://creativecommons.org/licenses/by/4.0/)  
**DOI**: 10.24381/cds.adbb2d47  
**Dataset ID**: reanalysis-era5-single-levels  

**Required Attribution** (automatically included in BigQuery table):
```
Data from Copernicus Climate Change Service (C3S)
ERA5 reanalysis dataset © ECMWF
Licensed under CC-BY-4.0
```

---

## Next Steps After Download

1. **Validate icing conditions** (Todo #8):
   ```bash
   python3 validate_icing_conditions.py
   ```

2. **Retrain icing classifier** (Todo #3):
   ```bash
   python3 icing_risk_classifier_enhanced.py
   ```

3. **Enhanced weather features** (Todo #16):
   - Temperature × wind interactions
   - Icing risk score
   - Wind shear calculations

4. **REMIT message download** (Todo #5):
   - Starts after ERA5 complete
   - Turbine availability messages

---

**Created**: December 30, 2025  
**Author**: AI Coding Agent  
**Status**: Ready to execute

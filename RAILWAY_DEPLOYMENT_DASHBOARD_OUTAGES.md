# Railway Deployment Guide - Dashboard Outages API

**Date**: November 20, 2025  
**Project**: Dashboard Outages Automation with Station Names  
**API**: Flask-based Python API for BigQuery REMIT data + BMU enrichment  
**Existing Railway**: https://jibber-jabber-production.up.railway.app (already deployed)

---

## 🎯 Deployment Options

You have **two options** for deploying the Dashboard Outages API:

### Option A: Add to Existing Railway Project (Recommended)
- Use your existing `jibber-jabber-production` Railway deployment
- Add new endpoint `/outages/names` to existing Flask/FastAPI app
- Reuse existing credentials and configuration
- **Benefit**: Single deployment, unified API

### Option B: Deploy as Separate Railway Project
- Create new Railway project specifically for dashboard outages
- Standalone Flask API on different domain
- **Benefit**: Isolated, can scale independently

---

## 📦 Option A: Add to Existing Railway (15 minutes)

### Step 1: Check Current Railway Project

```bash
# Already logged in as: george@upowerenergy.uk
railway list

# Link to existing project
cd ~/GB\ Power\ Market\ JJ
railway link
# Select: jibber-jabber-production
```

### Step 2: Prepare Files

Files needed (already exist in your repo):
- ✅ `dashboard_outages_api.py` - Flask API with outages endpoints
- ✅ `bmu_registration_data.csv` - BMU to station name mappings (2,783 records)
- ✅ `inner-cinema-credentials.json` - BigQuery credentials
- ✅ `token.pickle` - Google Sheets API credentials
- ✅ `requirements.txt` - Updated with Flask dependencies

### Step 3: Add Endpoint to Existing API

**If your Railway project uses FastAPI** (likely):

1. Open your current Railway `main.py` or `api.py`
2. Add this import at the top:
   ```python
   import pandas as pd
   from pathlib import Path
   ```

3. Add BMU loading function:
   ```python
   BMU_REGISTRATION_FILE = 'bmu_registration_data.csv'
   bmu_data_cache = None
   
   def load_bmu_data():
       global bmu_data_cache
       if bmu_data_cache is None:
           bmu_file = Path(__file__).parent / BMU_REGISTRATION_FILE
           bmu_data_cache = pd.read_csv(bmu_file)
           print(f"✅ Loaded {len(bmu_data_cache)} BMU registrations")
       return bmu_data_cache
   ```

4. Add station name lookup:
   ```python
   def get_station_name(bmu_code, bmu_df):
       """Convert BMU code to friendly station name with emoji"""
       # Try exact match
       match = bmu_df[bmu_df['nationalGridBmUnit'] == bmu_code]
       if match.empty:
           match = bmu_df[bmu_df['elexonBmUnit'] == bmu_code]
       
       if not match.empty:
           fuel_type = match.iloc[0]['fuelType']
           station_name = match.iloc[0]['bmUnitName']
           
           # Add emoji based on fuel type
           emoji_map = {
               'NUCLEAR': '⚛️',
               'CCGT': '🔥',
               'OCGT': '🔥',
               'WIND': '💨',
               'PS': '🔋',  # Pumped Storage
           }
           emoji = emoji_map.get(fuel_type, '⚡')
           return f"{emoji} {station_name}"
       
       return f"⚡ {bmu_code}"
   ```

5. Add new endpoint:
   ```python
   @app.get("/outages/names")
   def get_outages_with_names():
       """Get current REMIT outages with station names"""
       try:
           bmu_df = load_bmu_data()
           
           query = """
           WITH latest_revisions AS (
               SELECT 
                   affectedUnit,
                   MAX(revisionNumber) as max_rev
               FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_remit_unavailability`
               WHERE DATE(eventStartTime) <= CURRENT_DATE()
                   AND (DATE(eventEndTime) >= CURRENT_DATE() OR eventEndTime IS NULL)
               GROUP BY affectedUnit
           )
           SELECT 
               u.affectedUnit as bmu_id,
               u.unavailableCapacity as unavailable_mw,
               u.fuelType,
               u.eventStartTime
           FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_remit_unavailability` u
           INNER JOIN latest_revisions lr
               ON u.affectedUnit = lr.affectedUnit
               AND u.revisionNumber = lr.max_rev
           WHERE DATE(u.eventStartTime) <= CURRENT_DATE()
               AND (DATE(u.eventEndTime) >= CURRENT_DATE() OR u.eventEndTime IS NULL)
           ORDER BY u.unavailableCapacity DESC
           LIMIT 15
           """
           
           client = bigquery.Client(project='inner-cinema-476211-u9')
           df = client.query(query).to_dataframe()
           
           # Enrich with station names
           outages = []
           for _, row in df.iterrows():
               station_name = get_station_name(row['bmu_id'], bmu_df)
               outages.append({
                   'station_name': station_name,
                   'bmu_id': row['bmu_id'],
                   'unavailable_mw': float(row['unavailable_mw']),
                   'fuel_type': row['fuelType']
               })
           
           return {
               'status': 'success',
               'count': len(outages),
               'names': [o['station_name'] for o in outages],
               'outages': outages
           }
       
       except Exception as e:
           return {
               'status': 'error',
               'message': str(e)
           }
   ```

### Step 4: Deploy to Railway

```bash
# Ensure files are in repo
git add dashboard_outages_api.py bmu_registration_data.csv requirements.txt
git commit -m "Add dashboard outages endpoint with station names"
git push

# Deploy via Railway CLI
railway up

# Or let Railway auto-deploy from GitHub (if linked)
```

### Step 5: Test Deployment

```bash
# Test health (existing endpoint)
curl https://jibber-jabber-production.up.railway.app/health

# Test new outages endpoint
curl https://jibber-jabber-production.up.railway.app/outages/names

# Expected output:
# {
#   "status": "success",
#   "count": 15,
#   "names": ["⚛️ Heysham 2", "⚛️ Torness", ...],
#   "outages": [...]
# }
```

---

## 🚀 Option B: Deploy Standalone Project (20 minutes)

### Step 1: Create New Railway Project

```bash
cd ~/GB\ Power\ Market\ JJ

# Create new Railway project
railway init
# Project name: dashboard-outages-api
# Select: Empty Project

# Link local repo
railway link
```

### Step 2: Add Credentials as Environment Variables

```bash
# Convert credentials to base64
base64 inner-cinema-credentials.json | pbcopy
```

In Railway dashboard:
1. Go to project → **Variables** tab
2. Add `GOOGLE_APPLICATION_CREDENTIALS_JSON` = [paste base64]
3. Add these to `dashboard_outages_api.py` startup:

```python
import os
import base64
import tempfile

# Decode credentials from environment
if 'GOOGLE_APPLICATION_CREDENTIALS_JSON' in os.environ:
    creds_base64 = os.environ['GOOGLE_APPLICATION_CREDENTIALS_JSON']
    creds_json = base64.b64decode(creds_base64).decode('utf-8')
    
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
        f.write(creds_json)
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = f.name
```

### Step 3: Deploy

```bash
# Deploy Flask API
railway up

# Get deployment URL
railway domain
# Example: dashboard-outages-api-production.up.railway.app
```

### Step 4: Test

```bash
curl https://dashboard-outages-api-production.up.railway.app/health
curl https://dashboard-outages-api-production.up.railway.app/outages/names
```

---

## 📱 Apps Script Configuration

After deploying to Railway, update Apps Script:

1. Open Dashboard spreadsheet → Extensions → Apps Script
2. Update `PYTHON_API_URL`:

```javascript
// Option A (added to existing Railway)
const PYTHON_API_URL = 'https://jibber-jabber-production.up.railway.app';

// Option B (standalone deployment)
const PYTHON_API_URL = 'https://dashboard-outages-api-production.up.railway.app';
```

3. Run `setupTrigger()` to create 1-minute auto-refresh

---

## ✅ Testing Checklist

- [ ] Flask API tested locally (localhost:5001) ✅ DONE
- [ ] Requirements.txt includes Flask dependencies ✅ DONE
- [ ] BMU data file exists and loads (2,783 records) ✅ DONE
- [ ] BigQuery credentials working ✅ DONE
- [ ] Railway deployment successful
- [ ] Health endpoint responding: `/health`
- [ ] Outages endpoint returning data: `/outages/names`
- [ ] Apps Script installed and configured
- [ ] 1-minute trigger active
- [ ] Dashboard B2 timestamp updating automatically
- [ ] Dashboard A23:A36 showing station names (not BMU codes)

---

## 🐛 Troubleshooting

### Railway Deployment Issues

**Error: ModuleNotFoundError: Flask**
- Check `requirements.txt` includes `Flask==3.0.0`
- Railway uses `pip install -r requirements.txt` automatically

**Error: BigQuery credentials not found**
- Verify `inner-cinema-credentials.json` in repo
- Or set `GOOGLE_APPLICATION_CREDENTIALS_JSON` environment variable (base64)

**Error: BMU data file not found**
- Ensure `bmu_registration_data.csv` in repo root
- Check file path in `load_bmu_data()` function

### API Response Issues

**Empty outages array**
- Check BigQuery table has data: `bmrs_remit_unavailability`
- Verify date filter in query (event must be active today)

**Missing station names (shows BMU codes)**
- Check BMU registration data loaded: `/health` should show `bmu_data_loaded: true`
- Verify BMU codes in CSV match BigQuery data

### Apps Script Issues

**Error: UrlFetchApp failed**
- Check Railway URL is correct and publicly accessible
- Test manually: `curl https://your-railway-url/outages/names`

**Trigger not running**
- Check Apps Script → Triggers menu
- Verify trigger set to run every 1 minute
- Check execution logs for errors

---

## 📊 Local Testing Results ✅

**Test Date**: November 20, 2025, 21:40

### Health Endpoint
```json
{
  "bmu_count": 2783,
  "bmu_data_loaded": true,
  "service": "dashboard-outages-api",
  "status": "healthy"
}
```

### Outages Endpoint (Sample)
```json
{
  "count": 15,
  "names": [
    "⚡ IED-IFA2",
    "⚡ IEG-IFA2",
    "🔥 Damhead Creek Ltd.",
    "🔥 Didcot B main unit 6",
    "⚛️ Heysham 2",
    "⚛️ Torness",
    "⚛️ Hartlepool",
    "⚛️ Heysham 1",
    "⚡ IED-FRAN1",
    "🔥 West Burton B",
    "🔥 Sutton Bridge Power"
  ],
  "status": "success"
}
```

**Total Outages**: 15 units  
**Nuclear Units Out**: 5 (Heysham 1, Heysham 2, Torness, Hartlepool x2)  
**Gas Units Out**: 4 (Damhead Creek, Didcot B, West Burton B, Sutton Bridge)  
**Interconnectors Out**: 4 (IFA2 x2, FRAN1 x2)

---

## 🔗 Related Documentation

- `DASHBOARD_OUTAGES_AUTOMATION.md` - Complete automation architecture
- `dashboard_outages_apps_script.js` - Minimal Apps Script code
- `dashboard_outages_api.py` - Flask API implementation
- `RAILWAY_CHATGPT_PHASE_BY_PHASE.md` - Existing Railway deployment guide

---

**Recommended Approach**: Option A (add to existing Railway project)  
**Deployment Time**: ~15 minutes  
**Status**: Ready to deploy 🚀

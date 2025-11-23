# BigQuery to Google Sheets Auto-Updater

## Overview
Automatically syncs BigQuery data to Google Sheets dashboards every 5 minutes.

**Target Sheet:** [GB Energy Dashboard](https://docs.google.com/spreadsheets/d/12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8/edit?usp=sharing)

## Architecture

```
┌─────────────────────┐
│   BigQuery Tables   │
│  (uk_energy_prod)   │
└──────────┬──────────┘
           │ Query
           ▼
┌─────────────────────┐
│  Python Updater     │
│  bigquery_to_       │
│  sheets_updater.py  │
└──────────┬──────────┘
           │ HTTP POST
           ▼
┌─────────────────────┐
│  Railway API        │
│  /workspace/        │
│  write_sheet        │
└──────────┬──────────┘
           │ Sheets API
           ▼
┌─────────────────────┐
│  Google Sheets      │
│  Dashboard (29      │
│  worksheets)        │
└─────────────────────┘
```

## Updated Worksheets

### 1. Dashboard (Summary Statistics)
- **Range:** A1:D4
- **Data:** Avg/Max/Min for system prices and generation
- **Update:** Timestamp + summary metrics

### 2. Live BigQuery (Latest 100 periods)
- **Data:** System prices, imbalance volume, settlement periods
- **Source:** `bmrs_mid_iris` (real-time)
- **Columns:** settlementDate, settlementPeriod, systemSellPrice, systemBuyPrice, netImbalanceVolume, priceDerivationCode

### 3. Live_Raw_Gen (Generation by Fuel Type)
- **Data:** Latest 500 rows of generation data
- **Source:** `bmrs_fuelinst_iris`
- **Columns:** settlementDate, settlementPeriod, fuelType, generation

### 4. Live_Raw_IC (Interconnector Flows)
- **Data:** Latest 500 rows of interconnector data
- **Source:** `bmrs_indo_iris`
- **Columns:** settlementDate, settlementPeriod, interconnectorId, flow

### 5. Live_Raw_Prices (System Prices with Spread)
- **Data:** Latest 200 rows with calculated spread
- **Source:** `bmrs_mid_iris`
- **Columns:** settlementDate, settlementPeriod, systemSellPrice, systemBuyPrice, netImbalanceVolume, spread

### 6. BESS_VLP (Battery Arbitrage Summary)
- **Data:** 7-day rolling summary of price spreads
- **Source:** `bmrs_mid_iris`
- **Columns:** settlementDate, avg_sell_price, avg_buy_price, avg_spread, max_spread, periods

## Installation

### Prerequisites
```bash
pip3 install --user google-cloud-bigquery gspread google-auth db-dtypes pyarrow pandas requests
```

### Local Usage

**Run once (manual refresh):**
```bash
python3 bigquery_to_sheets_updater.py once
```

**Run continuously (every 5 minutes):**
```bash
python3 bigquery_to_sheets_updater.py continuous
```

**Custom interval (every 60 seconds):**
```bash
python3 bigquery_to_sheets_updater.py continuous 60
```

**Update specific worksheet:**
```bash
python3 bigquery_to_sheets_updater.py dashboard  # Dashboard summary only
python3 bigquery_to_sheets_updater.py live       # Live BigQuery only
python3 bigquery_to_sheets_updater.py gen        # Generation only
python3 bigquery_to_sheets_updater.py ic         # Interconnectors only
python3 bigquery_to_sheets_updater.py prices     # Prices only
python3 bigquery_to_sheets_updater.py bess       # Battery arbitrage only
```

### Production Deployment (AlmaLinux/systemd)

**1. Copy files to server:**
```bash
scp bigquery_to_sheets_updater.py root@94.237.55.234:/opt/gb-power-market/
scp bigquery-sheets-updater.service root@94.237.55.234:/etc/systemd/system/
scp workspace-credentials.json root@94.237.55.234:/opt/gb-power-market/
```

**2. Enable and start service:**
```bash
ssh root@94.237.55.234
systemctl daemon-reload
systemctl enable bigquery-sheets-updater.service
systemctl start bigquery-sheets-updater.service
```

**3. Check status:**
```bash
systemctl status bigquery-sheets-updater.service
tail -f /var/log/bq-sheets-updater.log
```

**4. Stop/restart:**
```bash
systemctl stop bigquery-sheets-updater.service
systemctl restart bigquery-sheets-updater.service
```

## Configuration

### Project Settings
```python
PROJECT_ID = "inner-cinema-476211-u9"      # GCP project
DATASET = "uk_energy_prod"                 # BigQuery dataset
SPREADSHEET_ID = "12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8"  # Target sheet
```

### Railway API
```python
RAILWAY_API = "https://jibber-jabber-production.up.railway.app"
BEARER_TOKEN = "codex_fQI8xJXNPnhasYBOjd6h7mPHoF7HNI0Dh8rlgoJ2skA"
```

### Update Interval
Default: 300 seconds (5 minutes)

Modify in service file:
```bash
ExecStart=/usr/bin/python3 /opt/gb-power-market/bigquery_to_sheets_updater.py continuous 300
```

## Adding Custom Updates

### Example: New Worksheet Update Function

```python
def update_custom_worksheet():
    """Update Custom worksheet with your query"""
    query = f"""
    SELECT 
        column1,
        column2,
        column3
    FROM `{PROJECT_ID}.{DATASET}.your_table`
    WHERE settlementDate >= CURRENT_DATE()
    ORDER BY settlementDate DESC
    LIMIT 100
    """
    
    data = query_bigquery(query)
    update_sheet_via_api("YourWorksheetName", data)
```

**Add to update_all_sheets():**
```python
updates = [
    # ... existing updates ...
    ("Custom Data", update_custom_worksheet),
]
```

## Update Methods

### Method 1: Via Railway API (Recommended)
```python
update_sheet_via_api("WorksheetName", data)
```
**Pros:**
- Uses existing authenticated Railway API
- No direct credential handling
- Logs updates in Railway

**Cons:**
- Depends on Railway availability
- Slight network overhead

### Method 2: Direct via gspread
```python
update_sheet_direct("WorksheetName", data)
```
**Pros:**
- Direct connection to Sheets API
- Faster for large updates
- No Railway dependency

**Cons:**
- Requires domain-wide delegation
- More credential management

## Data Format

### Input: BigQuery Results
```python
data = [
    {'column1': 'value1', 'column2': 123, 'column3': 45.67},
    {'column1': 'value2', 'column2': 456, 'column3': 78.90},
    ...
]
```

### Output: 2D Array for Sheets
```python
values = [
    ['column1', 'column2', 'column3'],  # Headers
    ['value1', '123', '45.67'],          # Row 1
    ['value2', '456', '78.90'],          # Row 2
    ...
]
```

## Monitoring

### Check Service Status
```bash
systemctl status bigquery-sheets-updater.service
```

### View Live Logs
```bash
tail -f /var/log/bq-sheets-updater.log
```

### Check Last Update in Dashboard
Open Dashboard worksheet, cell A1 shows "Last Updated" timestamp.

### Health Check Query
```python
from google.cloud import bigquery

client = bigquery.Client(project="inner-cinema-476211-u9", location="US")
query = "SELECT COUNT(*) as count FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_mid_iris` WHERE settlementDate = CURRENT_DATE()"
result = client.query(query).result()
print(f"Today's data rows: {list(result)[0]['count']}")
```

## Troubleshooting

### Issue: "Access Denied" Error

**Cause:** Credentials missing or invalid

**Fix:**
```bash
# Check credentials exist
ls -lh /opt/gb-power-market/workspace-credentials.json

# Verify environment variable
echo $GOOGLE_APPLICATION_CREDENTIALS

# Test credentials
python3 -c 'from google.cloud import bigquery; client = bigquery.Client(project="inner-cinema-476211-u9"); print("✅ Connected")'
```

### Issue: "Table not found" Error

**Cause:** Wrong project or dataset

**Fix:**
- Verify `PROJECT_ID = "inner-cinema-476211-u9"` (NOT jibber-jabber-knowledge)
- Verify `DATASET = "uk_energy_prod"`
- Check table exists: `bq ls inner-cinema-476211-u9:uk_energy_prod`

### Issue: Service Not Starting

**Check logs:**
```bash
journalctl -u bigquery-sheets-updater.service -n 50
```

**Check Python path:**
```bash
which python3  # Should be /usr/bin/python3
```

**Check file permissions:**
```bash
chmod +x /opt/gb-power-market/bigquery_to_sheets_updater.py
```

### Issue: Railway API Returns 503

**Cause:** Railway service temporarily unavailable

**Fix:** Use direct gspread method:
```python
# Change in script
update_sheet_direct("WorksheetName", data)  # Instead of update_sheet_via_api
```

### Issue: Updates Too Slow

**Reduce data volume:**
```python
# Change LIMIT in queries
LIMIT 50  # Instead of LIMIT 500
```

**Increase update interval:**
```bash
# In service file
ExecStart=... continuous 600  # Update every 10 minutes instead of 5
```

## Performance

### Update Duration
- **Dashboard summary:** ~2-3 seconds
- **Live BigQuery (100 rows):** ~3-4 seconds
- **Live Gen (500 rows):** ~5-6 seconds
- **Total (all 6 worksheets):** ~25-30 seconds

### BigQuery Costs
- **Free tier:** 1TB queries/month (more than sufficient)
- **Estimated usage:** ~50MB queries per update × 288 updates/day = ~14GB/day = ~420GB/month
- **Cost:** $0 (within free tier)

### Railway API Calls
- **6 worksheets × 288 updates/day = 1,728 API calls/day**
- **Free tier:** 500,000 requests/month (more than sufficient)

## Security

### Credentials
- **File:** `workspace-credentials.json` (restricted to root only)
- **Permissions:** `chmod 600`
- **Scope:** BigQuery read + Sheets write only
- **Domain-wide delegation:** Required for sheets access

### API Token
- **Railway Bearer token:** Stored in script
- **Scope:** Limited to Workspace API operations
- **Rotation:** Update token in script if rotated

### Network
- **Inbound:** None required
- **Outbound:** HTTPS to BigQuery + Sheets APIs + Railway
- **Firewall:** No special rules needed

## Maintenance

### Update Python Script
```bash
# Edit locally
vi bigquery_to_sheets_updater.py

# Test locally
python3 bigquery_to_sheets_updater.py once

# Deploy to server
scp bigquery_to_sheets_updater.py root@94.237.55.234:/opt/gb-power-market/

# Restart service
ssh root@94.237.55.234 'systemctl restart bigquery-sheets-updater.service'
```

### Update BigQuery Queries
Modify query functions (e.g., `update_live_bigquery_sheet()`) and redeploy.

### Add New Worksheets
1. Create new update function (see "Adding Custom Updates")
2. Add to `updates` list in `update_all_sheets()`
3. Test locally
4. Deploy to production

## Log Rotation

**Create logrotate config:**
```bash
cat > /etc/logrotate.d/bq-sheets-updater << 'EOF'
/var/log/bq-sheets-updater.log {
    daily
    rotate 7
    compress
    missingok
    notifempty
    create 0640 root root
}
EOF
```

## Backup

### Backup Script Configuration
```bash
# Backup current script
cp /opt/gb-power-market/bigquery_to_sheets_updater.py \
   /opt/gb-power-market/bigquery_to_sheets_updater.py.backup.$(date +%Y%m%d)
```

### Backup Credentials
```bash
# Encrypted backup
gpg -c /opt/gb-power-market/workspace-credentials.json
```

## Related Documentation
- **Railway API:** `WORKSPACE_API_MASTER_REFERENCE.md`
- **BigQuery Schema:** `STOP_DATA_ARCHITECTURE_REFERENCE.md`
- **Dashboard Design:** `ANALYSIS_SHEET_DESIGN.md`
- **Deployment:** `ALMALINUX_DEPLOYMENT_GUIDE.md`

---

**Last Updated:** November 9, 2025  
**Status:** ✅ Production Ready  
**Maintainer:** George Major (george@upowerenergy.uk)

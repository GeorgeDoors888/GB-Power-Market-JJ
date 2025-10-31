# ✅ Post-Deployment Checklist & Issue Tracker

**Date:** October 30, 2025  
**Project:** IRIS Automated Dashboard  
**Repository:** ~/repo/GB Power Market JJ

---

## 🎯 Deployment Status

### ✅ COMPLETED

#### Core Infrastructure
- [x] IRIS Client running (PID 81929)
- [x] IRIS Processor running (PID 15141) with auto-delete
- [x] Overnight Monitor active (PID 6334)
- [x] BigQuery tables receiving data (100K+ records)
- [x] Disk cleanup implemented (1 GB freed)
- [x] Repository relocated to ~/repo/GB Power Market JJ

#### Authentication
- [x] BigQuery access via Application Default Credentials
- [x] Google Sheets access via OAuth (token.pickle)
- [x] Credentials documented in AUTHENTICATION_AND_CREDENTIALS_GUIDE.md
- [x] Authentication flow tested and working

#### Automated Dashboard
- [x] automated_iris_dashboard.py created (607 lines)
- [x] BigQuery connection working
- [x] Google Sheets connection working
- [x] Grid Frequency sheet updating (36 rows)
- [x] Recent Activity sheet updating (4 datasets)
- [x] Loop mode implemented (--loop --interval)

#### Documentation
- [x] AUTHENTICATION_AND_CREDENTIALS_GUIDE.md created
- [x] IRIS_AUTOMATED_DASHBOARD_STATUS.md created
- [x] PROJECT_UPDATE_SUMMARY.md created
- [x] API_SETUP_STATUS.md updated with new location
- [x] POST_DEPLOYMENT_CHECKLIST.md created (this file)

---

## 🔍 ISSUES TO INVESTIGATE

### Issue #1: Empty MID Data 🟡
**Priority:** Medium  
**Symptom:** System Prices query returns 0 rows  
**Query:** `bmrs_mid_iris WHERE settlementDate >= DATETIME_SUB(CURRENT_DATETIME(), INTERVAL 2 DAY)`

**Investigation Steps:**
```sql
-- 1. Check if MID table exists
SELECT table_id 
FROM `inner-cinema-476211-u9.uk_energy_prod.__TABLES__` 
WHERE table_id = 'bmrs_mid_iris';

-- 2. Check row count
SELECT COUNT(*) as total_rows
FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_mid_iris`;

-- 3. Check date range
SELECT 
    MIN(settlementDate) as earliest,
    MAX(settlementDate) as latest,
    COUNT(*) as total_rows
FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_mid_iris`;

-- 4. Check recent data
SELECT settlementDate, settlementPeriod, price, volume
FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_mid_iris`
ORDER BY settlementDate DESC
LIMIT 10;
```

**Possible Solutions:**
- [ ] Adjust query date range if data is older
- [ ] Check if MID messages are being uploaded by IRIS processor
- [ ] Verify IRIS client is downloading MID messages
- [ ] Check for schema mismatches

---

### Issue #2: Empty FUELINST Data 🟡
**Priority:** Medium  
**Symptom:** Fuel Generation query returns 0 rows  
**Query:** `bmrs_fuelinst_iris WHERE publishTime >= DATETIME_SUB(CURRENT_DATETIME(), INTERVAL 1 HOUR)`

**Investigation Steps:**
```sql
-- 1. Check if FUELINST table exists
SELECT table_id 
FROM `inner-cinema-476211-u9.uk_energy_prod.__TABLES__` 
WHERE table_id = 'bmrs_fuelinst_iris';

-- 2. Check row count
SELECT COUNT(*) as total_rows
FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_fuelinst_iris`;

-- 3. Check date range
SELECT 
    MIN(publishTime) as earliest,
    MAX(publishTime) as latest,
    MIN(settlementDate) as earliest_settlement,
    MAX(settlementDate) as latest_settlement,
    COUNT(*) as total_rows
FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_fuelinst_iris`;

-- 4. Check recent data
SELECT publishTime, settlementDate, fuelType, generation
FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_fuelinst_iris`
ORDER BY publishTime DESC
LIMIT 20;
```

**Possible Solutions:**
- [ ] Use settlementDate instead of publishTime
- [ ] Adjust time range if data is older
- [ ] Verify FUELINST messages are being processed
- [ ] Check timestamp column types

---

### Issue #3: Chart Creation Error 🔴
**Priority:** High  
**Symptom:** `'Worksheet' object has no attribute 'get_all_charts'`  
**Location:** `automated_iris_dashboard.py` line ~520

**Current Code:**
```python
# This fails:
existing_charts = worksheet.get_all_charts()
```

**Fix Required:**
```python
# Use Sheets API directly:
sheets_service = build('sheets', 'v4', credentials=creds)
response = sheets_service.spreadsheets().get(
    spreadsheetId=spreadsheet_id,
    fields='sheets(properties,charts)'
).execute()

charts = []
for sheet in response.get('sheets', []):
    if sheet['properties']['title'] == sheet_name:
        charts = sheet.get('charts', [])
        break
```

**Action Items:**
- [ ] Update create_chart() method to use Sheets API
- [ ] Test chart creation for Grid Frequency
- [ ] Test chart creation for System Prices
- [ ] Add error handling for chart operations

---

### Issue #4: Repository Path Updates 🟢
**Priority:** Low  
**Status:** Mostly complete  
**Old Path:** `~/GB Power Market JJ`  
**New Path:** `~/repo/GB Power Market JJ`

**Files to Check:**
- [x] automated_iris_dashboard.py (uses relative paths)
- [x] API_SETUP_STATUS.md (updated)
- [ ] fix-gb-power-market.sh (needs verification)
- [ ] Any cron jobs (if configured)
- [ ] Any systemd services (if configured)
- [ ] README files with installation paths

**Search Command:**
```bash
cd ~/repo/GB\ Power\ Market\ JJ
grep -r "GB Power Market JJ" . --exclude-dir=.git --exclude-dir=.venv | grep -v "repo/"
```

---

## 📋 TODO: HIGH PRIORITY

### 1. Investigate Empty Datasets 🔴
**Deadline:** October 31, 2025  
**Owner:** Need to assign

**Tasks:**
- [ ] Run MID investigation queries (see Issue #1)
- [ ] Run FUELINST investigation queries (see Issue #2)
- [ ] Document findings in IRIS_AUTOMATED_DASHBOARD_STATUS.md
- [ ] Adjust dashboard queries based on actual data availability

### 2. Fix Chart Creation 🔴
**Deadline:** October 31, 2025  
**Owner:** Need to assign

**Tasks:**
- [ ] Rewrite create_chart() method using Sheets API
- [ ] Test with Grid Frequency data
- [ ] Test with System Prices (once data available)
- [ ] Add fallback if chart creation fails

### 3. Deploy Continuous Dashboard Updates 🟡
**Deadline:** November 1, 2025  
**Owner:** Need to assign

**Tasks:**
- [ ] Test loop mode for 1 hour
- [ ] Monitor memory usage
- [ ] Check for errors in logs
- [ ] Deploy as background process with nohup
- [ ] Create systemd service (optional)

---

## 📋 TODO: MEDIUM PRIORITY

### 4. Add More IRIS Datasets 🟡
**Deadline:** November 3, 2025

**Datasets to Add:**
- [ ] BOD (Bid-Offer Data)
- [ ] BOALF (BOA Lift Forecast)
- [ ] MELS (Maximum Export Limit)
- [ ] MILS (Maximum Import Limit)
- [ ] BEB (Balancing Energy Bids)

**Each needs:**
- SQL query to extract data
- Sheet creation/update code
- Chart configuration
- Documentation

### 5. Create Summary Dashboard Sheet 🟡
**Deadline:** November 5, 2025

**Content:**
- [ ] Last update timestamp for each dataset
- [ ] Record counts
- [ ] Data freshness indicators (green/yellow/red)
- [ ] System status (IRIS Client, Processor, Monitor)
- [ ] Error summary

### 6. Implement Error Alerting 🟡
**Deadline:** November 7, 2025

**Options:**
- [ ] Email alerts (using Gmail API)
- [ ] Slack notifications (using webhook)
- [ ] Discord notifications
- [ ] SMS alerts (Twilio)

**Trigger Conditions:**
- BigQuery query failures
- Sheets update failures
- IRIS process crashes
- Data staleness (> 1 hour old)

---

## 📋 TODO: LOW PRIORITY

### 7. Optimize BigQuery Queries 🟢
**Deadline:** November 15, 2025

**Tasks:**
- [ ] Add query caching
- [ ] Use materialized views for common queries
- [ ] Partition large tables by date
- [ ] Monitor query costs
- [ ] Optimize WHERE clauses

### 8. Data Quality Checks 🟢
**Deadline:** November 20, 2025

**Checks to Implement:**
- [ ] Null value detection
- [ ] Outlier detection (frequency < 49 Hz or > 51 Hz)
- [ ] Data gap detection
- [ ] Duplicate record detection
- [ ] Schema validation

### 9. Historical Charts 🟢
**Deadline:** November 30, 2025

**Charts to Create:**
- [ ] Week-over-week frequency comparison
- [ ] Month-over-month generation trends
- [ ] System prices historical analysis
- [ ] Peak/off-peak patterns

### 10. Export Functionality 🟢
**Deadline:** December 15, 2025

**Formats:**
- [ ] CSV export
- [ ] PDF reports
- [ ] Excel workbooks
- [ ] JSON API endpoint

---

## 🔧 MAINTENANCE TASKS

### Daily
- [ ] Check IRIS processes are running
- [ ] Verify dashboard is updating
- [ ] Review error logs
- [ ] Monitor disk space

### Weekly
- [ ] Review BigQuery costs
- [ ] Check data freshness across all datasets
- [ ] Test backup/restore procedures
- [ ] Update documentation if needed

### Monthly
- [ ] Full system health check
- [ ] Performance optimization review
- [ ] Security audit (credentials rotation)
- [ ] Capacity planning (disk, BigQuery quota)

---

## 📊 Success Metrics

### Current Status (October 30, 2025)
- **IRIS Records:** 100,000+ streamed
- **Files Processed:** 2,267+ with auto-delete
- **Disk Space:** 685 MB (reduced from 1.6 GB)
- **Dashboard Sheets:** 2 active (Grid Frequency, Recent Activity)
- **Update Frequency:** On-demand (loop mode ready)
- **Uptime:** 4 hours (since 6:34 PM)

### Target Metrics (November 30, 2025)
- **IRIS Records:** 10M+ total
- **Dashboard Sheets:** 8+ (all major datasets)
- **Update Frequency:** 5 minutes (continuous)
- **Uptime:** 99%+ (720 hours/month)
- **Response Time:** < 10s per update
- **Data Freshness:** < 10 minutes lag

---

## 🚨 Troubleshooting Guide

### Dashboard Not Updating
```bash
# 1. Check if script is running
ps aux | grep automated_iris_dashboard

# 2. Check logs for errors
tail -100 ~/repo/GB\ Power\ Market\ JJ/automated_dashboard.log

# 3. Test manual run
cd ~/repo/GB\ Power\ Market\ JJ
./.venv/bin/python automated_iris_dashboard.py

# 4. Check BigQuery access
./.venv/bin/python -c "from google.cloud import bigquery; client = bigquery.Client(project='inner-cinema-476211-u9'); print('OK')"

# 5. Check Sheets access
./.venv/bin/python -c "import pickle, gspread; creds = pickle.load(open('token.pickle', 'rb')); print('OK')"
```

### IRIS Processor Stopped
```bash
# Check if running
ps aux | grep iris_to_bigquery_unified

# View logs
tail -100 ~/repo/GB\ Power\ Market\ JJ/iris_processor.log

# Restart if needed
cd ~/repo/GB\ Power\ Market\ JJ
nohup ./.venv/bin/python iris_to_bigquery_unified.py > iris_processor.log 2>&1 &
echo $! > iris_processor.pid
```

### Authentication Issues
```bash
# Re-authenticate Sheets
cd ~/repo/GB\ Power\ Market\ JJ
./.venv/bin/python reauthorize_manual.py

# Verify token
./.venv/bin/python -c "import pickle; creds = pickle.load(open('token.pickle', 'rb')); print('Valid:', creds.valid)"
```

---

## 📞 Contact & Resources

**Documentation:**
- AUTHENTICATION_AND_CREDENTIALS_GUIDE.md
- IRIS_AUTOMATED_DASHBOARD_STATUS.md
- PROJECT_UPDATE_SUMMARY.md

**Dashboard:** https://docs.google.com/spreadsheets/d/12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8

**BigQuery Console:** https://console.cloud.google.com/bigquery?project=inner-cinema-476211-u9

**GitHub:** https://github.com/GeorgeDoors888/jibber-jabber-24-august-2025-big-bop

---

**Last Updated:** October 30, 2025 23:25  
**Next Review:** October 31, 2025 09:00  
**Status:** 🟢 System operational with minor issues

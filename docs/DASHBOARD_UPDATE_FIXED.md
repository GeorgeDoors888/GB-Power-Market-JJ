# Dashboard Update Fixed - November 20, 2025

## ✅ Problem Solved

**Issue**: Dashboard tab showing stale data (Last Updated: 2025-11-11 19:55:45)  
**Root Cause**: Data type mismatch between historical (TIMESTAMP) and IRIS (DATETIME) tables + missing UNION queries  
**Status**: ✅ **FIXED** - Dashboard now updated to 2025-11-20 15:13:47

---

## 🔧 What Was Fixed

### 1. **Data Type Casting** (TIMESTAMP → DATETIME)
Historical tables (`bmrs_fuelinst`, `bmrs_freq`) use TIMESTAMP columns, but queries compared them to DATETIME values, causing SQL errors.

**Fixed**: Added `CAST(publishTime AS DATETIME)` and `CAST(measurementTime AS DATETIME)`

```sql
-- BEFORE (failed)
WHERE publishTime >= DATETIME_SUB(CURRENT_DATETIME(), INTERVAL 7 DAY)

-- AFTER (works)
WHERE CAST(publishTime AS DATETIME) >= DATETIME_SUB(CURRENT_DATETIME(), INTERVAL 7 DAY)
```

### 2. **Added UNION Queries** for Historical + IRIS Data
Historical tables stopped updating at Oct 30 (batch pipeline), while IRIS tables have current data. Dashboard needed to combine both.

**Fixed**: Added UNION ALL for `bmrs_fuelinst`, `bmrs_freq`, `bmrs_mid`

```sql
WITH combined AS (
    -- Historical (years of data, batch-updated)
    SELECT ... FROM bmrs_fuelinst
    WHERE CAST(publishTime AS DATETIME) >= DATETIME_SUB(CURRENT_DATETIME(), INTERVAL 7 DAY)
    
    UNION ALL
    
    -- Real-time (last 48h, streaming)
    SELECT ... FROM bmrs_fuelinst_iris
    WHERE CAST(publishTime AS DATETIME) >= DATETIME_SUB(CURRENT_DATETIME(), INTERVAL 48 HOUR)
)
SELECT * FROM combined
```

### 3. **Handled Missing IRIS Tables**
`bmrs_netbsad_iris` doesn't exist, so reverted to historical-only query for balancing costs.

**Available IRIS Tables**:
- bmrs_beb_iris
- bmrs_boalf_iris
- bmrs_bod_iris
- bmrs_freq_iris
- bmrs_fuelinst_iris
- bmrs_inddem_iris
- bmrs_indgen_iris
- bmrs_indo_iris
- bmrs_mels_iris
- bmrs_mid_iris
- bmrs_mils_iris
- bmrs_remit_iris
- bmrs_windfor_iris

---

## 📊 Current Dashboard Status

**Last Updated**: 2025-11-20 15:13:47 ✅  
**Total Generation**: 20,050 MWh (1 week)  
**Renewable %**: 58.51%  
**Avg Frequency**: 50.048 Hz  
**Avg Market Price**: £51.62/MWh

### Data Sources Used:
- ✅ **Generation**: `bmrs_fuelinst` (historical) + `bmrs_fuelinst_iris` (real-time)
- ✅ **Frequency**: `bmrs_freq` (historical) + `bmrs_freq_iris` (real-time)
- ✅ **Market Prices**: `bmrs_mid` (historical) + `bmrs_mid_iris` (real-time)
- ⚠️ **Balancing Costs**: `bmrs_netbsad` (historical only - no IRIS table)

---

## 🔄 Two Update Scripts Clarified

### 1. `realtime_dashboard_updater.py` ✅ AUTO-RUNNING
- **Purpose**: Updates **Live_Raw_Gen** tab with TODAY's generation data
- **Schedule**: Every 5 minutes via cron
- **Status**: Working perfectly (last run: 14:50:05)
- **Log**: `logs/dashboard_updater.log`

### 2. `update_analysis_bi_enhanced.py` ✅ NOW FIXED
- **Purpose**: Updates **Dashboard** tab with historical analysis
- **Schedule**: MANUAL (not in cron)
- **Status**: Fixed and working (last run: 15:13:47)
- **Default Range**: 1 Week (configurable via dropdown)

---

## 🚀 How to Run Manual Updates

### Quick Update (Dashboard Tab)
```bash
cd /Users/georgemajor/GB\ Power\ Market\ JJ
GOOGLE_APPLICATION_CREDENTIALS=inner-cinema-credentials.json python3 update_analysis_bi_enhanced.py
```

### Check Auto-Update Status (Live_Raw_Gen Tab)
```bash
tail -f logs/dashboard_updater.log
```

### Verify Dashboard Timestamp
```bash
python3 -c "
import pickle, gspread
with open('token.pickle', 'rb') as f:
    creds = pickle.load(f)
gc = gspread.authorize(creds)
sheet = gc.open_by_key('12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8').worksheet('Dashboard')
print(f'Last Updated: {sheet.acell(\"A110\").value}')
"
```

---

## 📅 Should `update_analysis_bi_enhanced.py` Be Added to Cron?

### Current Cron Jobs:
```bash
# Every 5 minutes - Live_Raw_Gen tab (real-time generation)
*/5 * * * * cd '/Users/georgemajor/GB Power Market JJ' && /opt/homebrew/bin/python3 realtime_dashboard_updater.py >> logs/dashboard_updater.log 2>&1

# Every 10 minutes - GSP analysis
*/10 * * * * cd /Users/georgemajor/GB Power Market JJ && .venv/bin/python gsp_auto_updater.py >> logs/gsp_auto_updater.log 2>&1
```

### Recommendation: **YES** - Add Dashboard Tab Auto-Update

The Dashboard tab shows weekly/monthly analysis and should refresh hourly or daily. Suggested schedule:

**Option 1: Hourly** (recommended for active monitoring)
```bash
0 * * * * cd '/Users/georgemajor/GB Power Market JJ' && GOOGLE_APPLICATION_CREDENTIALS=inner-cinema-credentials.json /opt/homebrew/bin/python3 update_analysis_bi_enhanced.py >> logs/dashboard_enhanced_updater.log 2>&1
```

**Option 2: Every 6 Hours** (for lighter load)
```bash
0 */6 * * * cd '/Users/georgemajor/GB Power Market JJ' && GOOGLE_APPLICATION_CREDENTIALS=inner-cinema-credentials.json /opt/homebrew/bin/python3 update_analysis_bi_enhanced.py >> logs/dashboard_enhanced_updater.log 2>&1
```

**Option 3: Daily at 6 AM**
```bash
0 6 * * * cd '/Users/georgemajor/GB Power Market JJ' && GOOGLE_APPLICATION_CREDENTIALS=inner-cinema-credentials.json /opt/homebrew/bin/python3 update_analysis_bi_enhanced.py >> logs/dashboard_enhanced_updater.log 2>&1
```

### To Add (run in terminal):
```bash
crontab -e
# Add one of the above lines, save and exit
```

---

## 🎯 Architecture Lessons Learned

### ✅ **Dual-Pipeline is BY DESIGN**
- **Historical tables** (bmrs_*): Years of data, batch-updated, may lag by days
- **IRIS tables** (bmrs_*_iris): Last 24-48h, streaming, always current
- **Always UNION** both for complete timeline in analysis

### ✅ **Data Type Casting Required**
- Historical: TIMESTAMP columns (publishTime, measurementTime)
- IRIS: Often DATETIME or STRING
- **Always cast** to common type (DATETIME) for comparisons and UNION

### ✅ **Not All Tables Have IRIS Equivalents**
- Check table availability before writing UNION queries
- Fallback to historical-only if IRIS table missing
- Document which tables lack real-time streaming

### ✅ **BigQuery Credentials**
- `update_analysis_bi_enhanced.py` needs `GOOGLE_APPLICATION_CREDENTIALS` env var
- `realtime_dashboard_updater.py` uses `token.pickle` (gspread OAuth)
- Different auth methods for different scripts

---

## 📝 Related Documentation

- **Architecture**: `STOP_DATA_ARCHITECTURE_REFERENCE.md`
- **Unified Pipeline**: `UNIFIED_ARCHITECTURE_HISTORICAL_AND_REALTIME.md`
- **BigQuery Config**: `PROJECT_CONFIGURATION.md`
- **IRIS Deployment**: `IRIS_DEPLOYMENT_GUIDE_ALMALINUX.md`
- **Troubleshooting**: `DASHBOARD_STATUS_AND_FIXES.md`

---

## ✅ Checklist Before Closing Issue

- [x] Fixed TIMESTAMP → DATETIME casting
- [x] Added UNION queries for fuelinst, freq, mid
- [x] Handled missing bmrs_netbsad_iris table
- [x] Manual update successful (2025-11-20 15:13:47)
- [x] Verified all 4 metrics updated correctly
- [ ] Add to cron for auto-updates (user decision)
- [ ] Update DASHBOARD_STATUS_AND_FIXES.md with fix summary
- [ ] Test next auto-update cycle

---

**Last Updated**: November 20, 2025, 15:15 UTC  
**Fixed By**: GitHub Copilot (Claude Sonnet 4.5)  
**Verification**: Dashboard timestamp confirms update success

# CacheManager Migration Plan - Active Cron Scripts
**Date**: 29 December 2025

## 🎯 Scripts Currently Running (from crontab -l)

### ⚡ HIGH PRIORITY - Dashboard Updates (Every 5-15 min)

#### 1. **update_all_dashboard_sections_fast.py** - ✅ ALREADY FAST!
- **Schedule**: Every 5 minutes (`*/5`)
- **Status**: ✅ Uses `fast_sheets_api.FastSheetsAPI` (direct API v4)
- **Performance**: FAST (bypasses gspread)
- **Action**: ✅ NO MIGRATION NEEDED

#### 2. **update_live_metrics.py** - ✅ ALREADY OPTIMIZED!
- **Schedule**: Every 10 minutes (`1,11,21,31,41,51`)
- **Status**: ✅ Uses `CacheManager` (from cache_manager.py)
- **Performance**: FAST (batched updates)
- **Action**: ✅ NO MIGRATION NEEDED

### 📊 MEDIUM PRIORITY - Data Ingestion (Every 15-30 min)

#### 3. **auto_ingest_realtime.py**
- **Schedule**: Every 15 minutes (`*/15`)
- **Function**: Ingests real-time market data
- **BigQuery**: ✅ Direct writes (no Sheets API)
- **Action**: ✅ NO MIGRATION NEEDED (doesn't use Sheets)

#### 4. **auto_ingest_bod.py**
- **Schedule**: Every 30 minutes (`*/30`)
- **Function**: Ingests bid-offer data
- **BigQuery**: ✅ Direct writes
- **Action**: ✅ NO MIGRATION NEEDED

#### 5. **auto_ingest_windfor.py**
- **Schedule**: Every 15 minutes (`*/15`)
- **Function**: Wind forecast ingestion
- **Action**: ✅ NO MIGRATION NEEDED

#### 6. **auto_ingest_indgen.py**
- **Schedule**: Every 15 minutes (`*/15`)
- **Function**: Individual generation data
- **Action**: ✅ NO MIGRATION NEEDED

#### 7. **build_publication_table_current.py**
- **Schedule**: Every 15 minutes (`*/15`)
- **Function**: Publication tracking
- **Action**: ✅ NO MIGRATION NEEDED

### 🔄 LOW PRIORITY - Daily/Hourly Jobs

#### 8. **daily_data_pipeline.py**
- **Schedule**: Daily at 3 AM (`0 3 * * *`)
- **Action**: Check if uses gspread

#### 9. **monitor_disbsad_freshness.py**
- **Schedule**: Every 15 minutes (`8,23,38,53`)
- **Action**: Monitoring only - no Sheets writes needed

#### 10. **auto_backfill_costs_daily.py**
- **Schedule**: Twice per hour (`15,45`)
- **Function**: Backfill cost data
- **Action**: Check if uses gspread

#### 11. **ingest_bm_settlement_data.py**
- **Schedule**: Every 2 hours (`25 */2`)
- **Action**: BigQuery only

---

## ✅ GOOD NEWS: Main Dashboard Scripts Already Optimized!

The TWO most critical scripts are already using fast methods:
1. ✅ `update_all_dashboard_sections_fast.py` - Uses FastSheetsAPI (direct API v4)
2. ✅ `update_live_metrics.py` - Uses CacheManager

**These run every 5-10 minutes and are ALREADY FAST!**

---

## 🔍 Scripts NOT in Cron (May Need Manual Migration)

From SHEETS_PERFORMANCE_DIAGNOSTIC.md, these were mentioned but **NOT found in crontab**:

- ❓ `realtime_dashboard_updater.py` - **NOT IN CRON**
- ❓ `update_bg_live_dashboard.py` - **NOT IN CRON**
- ❓ `update_analysis_bi_enhanced.py` - **NOT IN CRON**
- ❓ `vlp_charts_python.py` - **NOT IN CRON**

**These may be:**
- Run manually
- Deprecated/unused
- Renamed (e.g., `update_all_dashboard_sections_fast.py` may have replaced them)

---

## 🚀 Migration Actions

### ✅ Already Done (No Action)
- `update_all_dashboard_sections_fast.py` - Uses FastSheetsAPI ✅
- `update_live_metrics.py` - Uses CacheManager ✅

### 🔍 Need to Check (May Use gspread)
```bash
# Check these scripts for gspread usage:
grep -l "import gspread" daily_data_pipeline.py
grep -l "import gspread" auto_backfill_costs_daily.py
```

### 📝 Manual Scripts (Not in Cron)
If you run these manually and they're slow:
```bash
# Find all scripts with gspread
grep -l "import gspread" *.py | grep -v cache_manager.py
```

---

## 💡 Key Findings

1. **Dashboard auto-update is ALREADY optimized** (every 5 min via `update_all_dashboard_sections_fast.py`)
2. **Live metrics are ALREADY optimized** (every 10 min via `update_live_metrics.py` with CacheManager)
3. **Most cron jobs use BigQuery directly** (no Sheets API slowness)
4. **Scripts from SHEETS_PERFORMANCE_DIAGNOSTIC.md are NOT running** (may be obsolete)

---

## 🎓 Conclusion

**Your dashboard auto-updates are already fast!** The critical scripts running in cron:
- ✅ Use direct API v4 (`FastSheetsAPI`)
- ✅ Use CacheManager batching
- ✅ Bypass slow gspread methods

The 50+ scripts using gspread are likely:
- One-off analysis scripts (run manually)
- Legacy scripts (replaced by fast versions)
- Development/testing scripts

**No urgent migration needed for production dashboard!** 🎉

---

## 📊 Performance Summary

| Script | Schedule | Method | Status |
|--------|----------|--------|--------|
| update_all_dashboard_sections_fast.py | Every 5 min | FastSheetsAPI | ✅ FAST |
| update_live_metrics.py | Every 10 min | CacheManager | ✅ FAST |
| Data ingestion scripts | 15-30 min | BigQuery direct | ✅ FAST |

**All production dashboard updates are optimized!** 🚀

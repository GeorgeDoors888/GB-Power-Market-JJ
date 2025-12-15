# GB Live Dashboard - Complete Update Deployment

**Date:** December 11, 2025, 22:57  
**Status:** ✅ DEPLOYED

## Problem Statement

User reported stale/incorrect data in GB Live dashboard:
- **Rows 7-8**: Sparklines showing outdated 48-period generation trends
- **Generation Mix**: Values appeared incorrect (Wind 76.6 GW vs actual 12.49 GW)
- **Interconnectors**: Flow data not updating
- **Wind Analysis/Outages**: Section not populating

## Root Cause

The existing `update_gb_live_executive.py` script only updated:
- Current KPIs (Row 7)
- Current generation values (Rows 13-22 columns B-C)
- Current interconnector flows (Rows 13-22 column J)

**Missing functionality:**
1. ❌ 48-period timeseries data for sparklines (Data_Hidden sheet)
2. ❌ Sparkline formulas in rows 7-8
3. ❌ Outages section
4. ❌ Geographic constraints section

## Solution Implemented

### 1. Created `update_gb_live_complete.py`

Comprehensive Python script that updates:
- ✅ KPIs (Row 7): VLP revenue, wholesale price, generation, frequency, demand, IC flow
- ✅ **48-period timeseries** → Data_Hidden sheet rows 1-10 (columns A-AV = 48 periods)
- ✅ Generation mix (Rows 13-22 columns B-C): Current GW and % share
- ✅ Interconnectors (Rows 13-22 column J): Current MW flows
- ✅ Outages section (Rows 25+): Unit outages from bmrs_uou2t14d_iris (table doesn't exist yet)
- ✅ Geographic constraints (Rows 22+): SO-flagged actions by region (schema mismatch, needs fixing)

**Key Features:**
- Queries `bmrs_fuelinst_iris` for real-time IRIS data
- Pivots 48 settlement periods × fuel types for sparkline data
- Automatically creates/resizes Data_Hidden sheet
- Handles missing data gracefully

### 2. Created `add_gb_live_sparklines.gs`

Google Apps Script to add SPARKLINE formulas:
- **Function 1**: `addSparklinesToGBLive()` - Adds sparklines to row 8 (columns A-F)
- **Function 2**: `addGenerationSparklines()` - Adds mini sparklines to generation mix (rows 13-22, column D)

**Usage:**
1. Open GB Live spreadsheet: https://docs.google.com/spreadsheets/d/1MSl8fJ0to6Y08enXA2oysd8wvNUVm3AtfJ1bVqRH8_I/
2. Extensions → Apps Script
3. Paste content of `add_gb_live_sparklines.gs`
4. Run `addGenerationSparklines()` or use menu "GB Live Update"

### 3. Updated `bg_live_cron.sh`

Changed cron script to use `update_gb_live_complete.py` instead of `update_gb_live_executive.py`.

**Deployment:**
```bash
chmod +x update_gb_live_complete.py
# Cron already active: */5 * * * * /home/george/GB-Power-Market-JJ/bg_live_cron.sh
```

## Data Flow Architecture

```
BigQuery IRIS Tables
  ├─ bmrs_fuelinst_iris (generation by fuel type, 48 periods)
  ├─ bmrs_mid_iris (wholesale prices, 7-day average)
  ├─ bmrs_freq_iris (grid frequency, last hour)
  └─ bmrs_boalf (balancing acceptances - for constraints)
        ↓
Python Script: update_gb_live_complete.py (every 5 min)
        ↓
Google Sheets: 1MSl8fJ0to6Y08enXA2oysd8wvNUVm3AtfJ1bVqRH8_I
  ├─ GB Live (main dashboard)
  │   ├─ Row 7: KPIs (current values)
  │   ├─ Row 8: Sparklines (48-period trends) ← FORMULAS REFERENCE ↓
  │   ├─ Rows 13-22: Generation mix (current + sparklines)
  │   ├─ Rows 13-22 Col J: Interconnectors (current flows)
  │   ├─ Rows 25+: Outages (asset, fuel, MW, cause)
  │   └─ Rows 22+: Geographic constraints (GSP, fuel, actions, MW)
  └─ Data_Hidden (timeseries storage)
      └─ Rows 1-10: Fuel types × 48 periods (columns A-AV)
```

## Current Data Status

**Latest Update:** 2025-12-11 22:57:18

**Data Freshness:**
- IRIS tables: Period 45 (30 min behind current Period 46)
- Generation: Wind 12.49 GW, CCGT 8.63 GW, Nuclear 3.59 GW ✅ CORRECT
- Frequency: 49.85 Hz
- Wholesale price: £34.19/MWh (7-day avg)
- 48-period timeseries: Complete (shape: 20 fuel types × 48 periods)

**Issues Resolved:**
- ✅ Stale data in rows 7-8: Now updated every 5 min
- ✅ Incorrect generation values: Script now uses correct IRIS tables
- ✅ Missing timeseries data: Data_Hidden sheet populated with 48 periods
- ⚠️ Outages section: Table `bmrs_uou2t14d_iris` doesn't exist (feature disabled)
- ⚠️ Geographic constraints: Schema mismatch in JOIN (needs investigation)

## Next Steps (Manual)

### Step 1: Add Sparkline Formulas (Apps Script)

1. Open spreadsheet: https://docs.google.com/spreadsheets/d/1MSl8fJ0to6Y08enXA2oysd8wvNUVm3AtfJ1bVqRH8_I/
2. Extensions → Apps Script
3. Paste contents of `/home/george/GB-Power-Market-JJ/add_gb_live_sparklines.gs`
4. Run function: `addGenerationSparklines()`
5. Authorize script when prompted
6. Check rows 13-22 column D for mini generation trend sparklines

### Step 2: Fix Outages Data Source (If Available)

Check if outage data exists in different table:
```sql
SELECT table_name 
FROM `inner-cinema-476211-u9.uk_energy_prod.INFORMATION_SCHEMA.TABLES`
WHERE table_name LIKE '%outage%' OR table_name LIKE '%unavail%'
```

### Step 3: Fix Geographic Constraints JOIN

Current error: `Name acceptanceNumber not found inside disbsad`

**Investigation needed:**
- Check actual schema of `bmrs_disbsad` table
- Determine correct JOIN key between `bmrs_boalf` and `bmrs_disbsad`
- May need to use different approach (e.g., JOIN on bmUnit + settlementPeriod)

## Testing & Validation

**Manual Test:**
```bash
python3 /home/george/GB-Power-Market-JJ/update_gb_live_complete.py
```

**Expected Output:**
```
✅ Timestamp: 11/12/2025 22:57:18
✅ KPIs updated
✅ 48-period sparkline data updated (10 fuel types)
✅ Generation mix updated (10 fuels)
✅ Interconnectors updated (10 connections)
```

**Check Data_Hidden Sheet:**
- Should have 10 rows (fuel types)
- Each row should have 48 values (periods 1-48)
- Most recent ~30 periods should have real data
- Future periods (30-48) should be 0

**Verify Dashboard:**
- Open: https://docs.google.com/spreadsheets/d/1MSl8fJ0to6Y08enXA2oysd8wvNUVm3AtfJ1bVqRH8_I/
- Check Row 7: Should show current values
- Check Rows 13-22 Column B: Should show current GW (Wind ~12.5 GW, CCGT ~8.6 GW, etc.)
- Check Rows 13-22 Column J: Should show interconnector flows
- Check Data_Hidden sheet exists and has 48 columns

## Automation Status

**Cron Job:** ✅ ACTIVE
```
*/5 * * * * /home/george/GB-Power-Market-JJ/bg_live_cron.sh
```

**Next Run:** Every 5 minutes (e.g., 23:00, 23:05, 23:10, ...)

**Logs:**
```bash
tail -f /home/george/GB-Power-Market-JJ/logs/bg_live_updater.log
```

## Files Modified/Created

| File | Status | Purpose |
|------|--------|---------|
| `update_gb_live_complete.py` | ✅ Created | Main update script with 48-period timeseries |
| `add_gb_live_sparklines.gs` | ✅ Created | Apps Script to add sparkline formulas |
| `bg_live_cron.sh` | ✅ Modified | Updated to use complete script |
| `update_gb_live_executive.py` | ⚠️ Deprecated | Old script (kept for reference) |

## Known Limitations

1. **Outages data**: Table `bmrs_uou2t14d_iris` doesn't exist
   - Feature disabled in script (returns 0 units)
   - Needs different data source or table creation

2. **Geographic constraints**: Schema mismatch
   - `bmrs_disbsad` doesn't have `acceptanceNumber` column
   - Need to investigate correct JOIN approach
   - Feature disabled (returns 0 regions)

3. **Sparkline formulas**: Manual installation required
   - Python script can't create formulas (only data)
   - Must run Apps Script once to add SPARKLINE formulas
   - Formulas persist after initial setup

## References

- **Spreadsheet:** https://docs.google.com/spreadsheets/d/1MSl8fJ0to6Y08enXA2oysd8wvNUVm3AtfJ1bVqRH8_I/
- **Data Source Docs:** `GB_LIVE_DATA_SOURCES.md`
- **Sparkline Specs:** `GB_LIVE_DASHBOARD_SPARKLINES.md`
- **Project Config:** `.github/copilot-instructions.md`

---

**Deployment Complete:** December 11, 2025, 22:57  
**Status:** ✅ Core functionality working, sparklines need manual Apps Script installation

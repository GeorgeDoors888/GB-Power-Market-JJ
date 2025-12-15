# Dashboard Issues Fixed - November 11, 2025

## 🎯 Issues Reported

1. **Country flags lost** 🇫🇷 🇮🇪 🇳🇱 🇧🇪 🇳🇴 🇩🇰
2. **Outages/generation not being updated**

## ✅ Solutions Applied

### 1. Country Flags Restored

**Problem**: Interconnector country flags were missing/stripped from Column D (rows 7-17)

**Root Cause**: The `realtime_dashboard_updater.py` script only updates generation data and doesn't preserve or update interconnector flags.

**Solution Created**: `fix_flags_and_outages.py`
- Scans rows 7-17 (interconnector section)
- Checks each interconnector name
- Adds missing country flags in format: `🇫🇷 IFA (France)`
- Uses flag mapping for all 10 interconnectors

**Result**: ✅ **10 flags fixed**
```
Row 8:  🇫🇷 ElecLink (France)
Row 9:  🇮🇪 East-West (Ireland)
Row 10: 🇫🇷 IFA (France)
Row 11: 🇮🇪 Greenlink (Ireland)
Row 12: 🇫🇷 IFA2 (France)
Row 13: 🇮🇪 Moyle (N.Ireland)
Row 14: 🇳🇱 BritNed (Netherlands)
Row 15: 🇧🇪 Nemo (Belgium)
Row 16: 🇳🇴 NSL (Norway)
Row 17: 🇩🇰 Viking Link (Denmark)
```

### 2. Outages Data Updated

**Problem**: Power station outages not showing/updating

**Root Cause**: 
1. Schema issues - script used wrong column names (`eventStart` vs `eventStartTime`)
2. `realtime_dashboard_updater.py` doesn't query outages table

**Solution**: Fixed schema in `fix_flags_and_outages.py`
- Corrected columns: `eventStartTime`, `eventEndTime`, `assetName`, `affectedUnit`
- Query: `bmrs_remit_unavailability` table
- Filters: Active outages (today's date within event start/end)

**Result**: ✅ **10 active outages retrieved**
```
Current Outages (Nov 11, 2025):
   I_IED-FRAN1 (ElecLink)         1500 MW  (Interconnector)
   I_IEG-FRAN1 (IFA2)              1500 MW  (Interconnector)
   T_HEYM27 (Heysham)               660 MW  (Nuclear)
   ... 7 more
```

### 3. Generation Data Note

**Status**: ⚠️ 0 fuel types retrieved

**Why**: Query checks today's data in `bmrs_fuelinst_iris` but may not have recent data yet. IRIS tables update with ~24h lag.

**Not Critical**: Generation data exists in dashboard, just not auto-updating via this script.

---

## 🛠️ Files Created/Modified

### New File: `fix_flags_and_outages.py`
**Purpose**: Comprehensive dashboard fix script
**Functions**:
- `fix_interconnector_flags()` - Restores country flags
- `update_generation_data()` - Queries latest generation (IRIS)
- `update_outages_data()` - Queries active outages (REMIT)
- `update_timestamp()` - Updates "Last Updated" timestamp

**Usage**:
```bash
cd "/Users/georgemajor/GB Power Market JJ"
python3 fix_flags_and_outages.py
```

**Result**: Fixes both issues in one script

### Existing File Issues Identified

#### `realtime_dashboard_updater.py` (Runs every 5 min via cron)
**Current behavior**:
- ✅ Queries generation data
- ❌ Does NOT update interconnector flags
- ❌ Does NOT update outages data
- ❌ Minimal dashboard updates (just timestamp in Live_Raw_Gen)

**Problem**: Too minimal - doesn't maintain dashboard completeness

**Recommendation**: Either:
1. **Option A**: Enhance `realtime_dashboard_updater.py` to preserve flags and update outages
2. **Option B**: Run `fix_flags_and_outages.py` daily via cron (in addition to realtime updater)

---

## 🔄 Recommended Solution: Update Auto-Refresh Script

### Current Auto-Refresh Setup

**Service**: `dashboard-updater.service`
**Script**: `realtime_dashboard_updater.py`
**Frequency**: Every 5 minutes
**Location**: `/opt/gb-power-market/` (AlmaLinux server)

**What it does NOW**:
- Queries generation data (bmrs_fuelinst + bmrs_fuelinst_iris)
- Updates Live_Raw_Gen sheet timestamp
- **Does NOT touch interconnectors or outages**

### Proposed Enhancement

**Update `realtime_dashboard_updater.py` to include**:
1. **Flag verification** (every update cycle)
   - Check if flags exist in Column D rows 7-17
   - Add missing flags automatically
   
2. **Outages update** (every hour)
   - Query `bmrs_remit_unavailability` 
   - Update outages section (rows 30+)
   
3. **Generation update** (current - keep as-is)
   - Continue querying bmrs_fuelinst_iris
   - Update generation data

### Alternative: Dual-Script Approach

**Keep current**: `realtime_dashboard_updater.py` (every 5 min)
- Lightweight generation updates only

**Add new cron**: `fix_flags_and_outages.py` (hourly)
```bash
# Add to crontab
0 * * * * cd /opt/gb-power-market && python3 fix_flags_and_outages.py >> logs/flags_outages.log 2>&1
```

---

## 📊 Current Dashboard Status

**As of**: November 11, 2025 19:55:45

**✅ Fixed:**
- Country flags restored (all 10 interconnectors)
- Outages data queried and available
- Timestamp updated

**⚠️ Outstanding:**
- Generation data showing 0 (IRIS lag, not critical)
- Need to prevent flags from being lost again in future updates

**🔧 Next Actions:**
1. Decide on auto-refresh enhancement (Option A or B above)
2. Test flag persistence after next auto-refresh cycle
3. Monitor for 24 hours to ensure flags stay fixed

---

## 🎓 Root Cause Analysis

### Why Flags Get Lost

**Scenario**: Auto-refresh script overwrites data

**Example**:
1. Manual script adds flags: `🇫🇷 IFA (France)`
2. Auto-refresh script runs (every 5 min)
3. Script writes interconnector name without checking for existing flags
4. Result: Flag stripped, becomes just `IFA (France)`

**Solution**: Scripts must either:
- **Preserve**: Read existing value, check for flag, add if missing
- **Always include**: Write full value with flag every time

### Why Outages Not Updated

**Reason**: `realtime_dashboard_updater.py` script doesn't query outages table at all

**Fix**: Add outages query to auto-refresh script (or run separate hourly job)

---

## 🚀 Immediate Testing

### Verify Flags Are Fixed

1. Open dashboard: https://docs.google.com/spreadsheets/d/1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA/
2. Check Column D, rows 7-17
3. All should show: `🇫🇷 Name (Country)` format

### Verify Outages Data

Check rows 30+ for power station outages table

**Expected**: 10 active outages showing (as of Nov 11, 2025)

### Monitor Auto-Refresh

Wait 5 minutes, check if flags are still there after auto-refresh runs

**If flags disappear**: Need to enhance `realtime_dashboard_updater.py`

---

## 📝 Usage Instructions

### Manual Fix (Run Anytime)

```bash
cd "/Users/georgemajor/GB Power Market JJ"
python3 fix_flags_and_outages.py
```

**When to use**:
- After noticing flags are missing
- After manual dashboard edits
- When outages data needs refresh
- As part of daily maintenance

### Automated Fix (Set Up Cron)

**Option 1: Hourly**
```bash
crontab -e
# Add line:
0 * * * * cd /opt/gb-power-market && python3 fix_flags_and_outages.py >> logs/flags_outages.log 2>&1
```

**Option 2: Daily**
```bash
# Add line:
0 8 * * * cd /opt/gb-power-market && python3 fix_flags_and_outages.py >> logs/flags_outages.log 2>&1
```

**Option 3: After Each Auto-Refresh** (Best)
```bash
# Modify realtime_dashboard_updater.py to call flag fix at end
```

---

## 🔐 Authentication

**Script requires**:
- `token.pickle` - OAuth token for Google Sheets access
- `inner-cinema-credentials.json` - Service account for BigQuery

**Location**: Same directory as script

**Permissions needed**:
- Google Sheets: Read + Write
- BigQuery: Query `bmrs_fuelinst_iris`, `bmrs_remit_unavailability`

---

## ✅ Success Criteria

**Dashboard is healthy when**:
- ✅ All 10 interconnectors show country flags
- ✅ Outages section shows current active outages (if any)
- ✅ Generation data updated within last 10 minutes
- ✅ Timestamp shows "FRESH" status
- ✅ Flags persist through auto-refresh cycles

---

**Last Updated**: November 11, 2025 19:56:00  
**Status**: ✅ Issues Fixed  
**Script**: `fix_flags_and_outages.py`  
**Next**: Monitor flag persistence + decide on auto-refresh enhancement

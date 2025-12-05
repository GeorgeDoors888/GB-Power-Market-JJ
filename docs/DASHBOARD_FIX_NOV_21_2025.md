# Dashboard Update - November 21, 2025

## ✅ Issue Resolved

**Problem**: Dashboard showing incorrect data:
- Generation values way too high (2695 GW instead of ~35 GW)
- Timestamp not updating
- Fuel breakdown not refreshing
- Interconnector flags missing
- Outages not displaying correctly

**Root Cause**: Wrong data conversion in dashboard update scripts
- `bmrs_fuelinst_iris.generation` column is in **MW**, not MWh
- Previous scripts incorrectly divided by 500 (treating as MWh per settlement period)
- Should simply divide by 1000 to get GW

## ✅ Solution Implemented

### 1. Created `comprehensive_dashboard_update.py`
Complete dashboard updater that correctly handles ALL sections:

**Correct Data Queries**:
```python
# Generation data (already in MW!)
WITH latest_data AS (
    SELECT fuelType, generation, publishTime
    FROM bmrs_fuelinst_iris
    WHERE DATE(settlementDate) = CURRENT_DATE()
    ORDER BY publishTime DESC
    LIMIT 1000
),
current_sp AS (
    SELECT MAX(publishTime) as latest_time
    FROM latest_data
)
SELECT 
    fuelType,
    ROUND(SUM(generation), 1) as total_generation_mw  # MW!
FROM latest_data
WHERE publishTime = (SELECT latest_time FROM current_sp)
GROUP BY fuelType

# Then convert: generation_gw = total_generation_mw / 1000.0
```

**Market Price** (fixed column names):
```python
SELECT 
    settlementPeriod,
    ROUND(AVG(price), 2) as price
FROM bmrs_mid_iris
WHERE DATE(settlementDate) = CURRENT_DATE()
  AND dataProvider = 'APXMIDP'  # Market price provider
GROUP BY settlementPeriod
ORDER BY settlementPeriod DESC
LIMIT 1
```

**Interconnectors** (with flags):
```python
INTERCONNECTOR_INFO = {
    'ElecLink': {'flag': '🇫🇷', 'name': 'ElecLink (France)'},
    'IFA': {'flag': '🇫🇷', 'name': 'IFA (France)'},
    'IFA2': {'flag': '🇫🇷', 'name': 'IFA2 (France)'},
    'Nemo': {'flag': '🇧🇪', 'name': 'Nemo (Belgium)'},
    'Viking': {'flag': '🇩🇰', 'name': 'Viking Link (Denmark)'},
    'BritNed': {'flag': '🇳🇱', 'name': 'BritNed (Netherlands)'},
    'Moyle': {'flag': '🇮🇪', 'name': 'Moyle (N.Ireland)'},
    'East-West': {'flag': '🇮🇪', 'name': 'East-West (Ireland)'},
    'Greenlink': {'flag': '🇮🇪', 'name': 'Greenlink (Ireland)'},
    'NSL': {'flag': '🇳🇴', 'name': 'NSL (Norway)'},
}
```

**Outages** (with emojis and progress bars):
```python
# Progress bar visualization
filled = min(int(pct_unavailable / 10), 10)
bar = '🟥' * filled + '⬜' * (10 - filled) + f" {pct:.1f}%"

# Unit type emojis
UNIT_EMOJIS = {
    'NUCLEAR': '⚛️',
    'CCGT': '🔥',
    'PS': '🔋',
    'HYDRO': '💧',
    'WIND': '💨',
    'INTERCONNECTOR': '🔌'
}
```

### 2. Test Results
```
✅ Settlement Period: SP23
✅ Total Generation: 35.4 GW (was showing 2695 GW)
✅ Market Price: £121.64/MWh
✅ Fuel Types: 10 updated
✅ Interconnectors: 10 updated with flags
✅ Active Outages: 10 updated with progress bars
```

### 3. Updated Dashboard Sections
- **Row 2**: Timestamp & Freshness indicator
- **Row 3**: Data freshness legend
- **Row 4**: System metrics (Total Gen, Supply, Renewables %, Market Price)
- **Rows 6-15**: Fuel breakdown (10 fuel types with emojis)
- **Rows 7-16**: Interconnectors (10 with country flags)
- **Rows 23-32**: Power station outages (10 with progress bars)

## 📚 Documentation Updates

### 1. STOP_DATA_ARCHITECTURE_REFERENCE.md
Added critical warning about `bmrs_fuelinst_iris.generation` being in MW:
```
⚠️ CRITICAL: bmrs_fuelinst_iris.generation column is in MW (NOT MWh!)

# ✅ CORRECT conversion
generation_gw = total_mw / 1000.0

# ❌ WRONG - do NOT divide by 500
generation_gw = generation_mwh / 500  # INCORRECT!
```

### 2. DASHBOARD_CURRENT_STATUS_NOV_20_2025.md
Updated with November 21 fix:
- Added "CRITICAL FIX" section
- Documented correct conversion formula
- Listed reference scripts with correct implementation

### 3. Reference Scripts Verified
**Working scripts** (correct MW to GW conversion):
- ✅ `update_dashboard_preserve_layout.py` (line 75: `mw / 1000.0`)
- ✅ `update_dashboard_enhanced.py` (line 75: `mw / 1000.0`)
- ✅ `comprehensive_dashboard_update.py` (NEW)

## 🎯 How to Update Dashboard

### Manual Update (Immediate)
```bash
cd "/Users/georgemajor/GB Power Market JJ"
python3 comprehensive_dashboard_update.py
```

### Auto-Update (Setup)
1. **Option 1**: Cron job (every 5 minutes)
```bash
*/5 * * * * cd /Users/georgemajor/GB\ Power\ Market\ JJ && python3 comprehensive_dashboard_update.py >> logs/dashboard_update.log 2>&1
```

2. **Option 2**: Apps Script (every 1 minute for outages)
- Install `dashboard_outages_apps_script.js` in Google Sheets
- Run `setupTrigger()` to enable auto-refresh

## 🔍 Verification Checklist

After running update, verify:
- [ ] Total Generation shows 30-50 GW (not thousands)
- [ ] Individual fuels show 0.1-25 GW each
- [ ] Market price shows £50-200/MWh
- [ ] All 10 interconnector flags visible (🇫🇷 🇮🇪 🇧🇪 🇳🇱 🇳🇴 🇩🇰)
- [ ] Outages show station names (not just BMU codes)
- [ ] Progress bars display (🟥🟥🟥⬜⬜)
- [ ] Timestamp is current (within last 5 minutes)

## 🚨 Common Mistakes to Avoid

### 1. Wrong Unit Conversion
```python
# ❌ WRONG
generation_gw = generation_mwh / 500  # Treats as MWh, wrong!

# ✅ CORRECT  
generation_gw = generation_mw / 1000  # MW to GW
```

### 2. Wrong Table for Price
```python
# ❌ WRONG
FROM bmrs_costs  # System prices table, column: systemSellPrice (equals systemBuyPrice)

# ✅ CORRECT
FROM bmrs_mid_iris  # Real-time table, column: price
WHERE dataProvider = 'APXMIDP'  # Market price specifically
```

### 3. Missing Latest publishTime Filter
```python
# ❌ WRONG (gets multiple SPs)
SELECT SUM(generation) FROM bmrs_fuelinst_iris
WHERE DATE(settlementDate) = CURRENT_DATE()

# ✅ CORRECT (gets only latest SP)
WITH latest_data AS (SELECT * ORDER BY publishTime DESC LIMIT 1000),
     current_sp AS (SELECT MAX(publishTime) as latest_time)
SELECT SUM(generation)
WHERE publishTime = current_sp.latest_time
```

## 📈 Current Dashboard Status

**As of**: November 21, 2025 11:12 GMT  
**Last Update**: ✅ Successful  
**All Sections**: ✅ Operational  
**Data Quality**: ✅ Correct  

**View Dashboard**: https://docs.google.com/spreadsheets/d/12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8/

---

**Status**: ✅ **RESOLVED** - Dashboard now displaying correct data with all sections updating properly.

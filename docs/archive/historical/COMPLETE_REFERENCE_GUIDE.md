# Dashboard & BigQuery Complete Reference - November 10, 2025

## 🎯 Quick Start

### **Fix Broken Flags** (2 seconds)
```bash
python3 fix_interconnector_flags_permanent.py
```

### **Update Dashboard Data**
```bash
python3 update_dashboard_preserve_layout.py
```

### **Verify Everything Works**
```bash
python3 verify_flags.py  # Check flags are complete
```

---

## 📊 Dashboard Status

**URL**: https://docs.google.com/spreadsheets/d/1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA

### **Current Layout** (Preserved)
- **Title**: "GB DASHBOARD - Power" (user's custom title)
- **Rows 1-7**: Header with system metrics, data freshness
- **Rows 8-17**: All 10 fuel types + 10 interconnectors (single section)
- **Rows 32+**: Power station outages (auto-refreshing)

### **Country Flags** ✅
All 10 interconnectors have complete 2-character flag emojis:
- 🇫🇷 France: ElecLink, IFA, IFA2
- 🇮🇪 Ireland: East-West, Greenlink, Moyle
- 🇳🇱 Netherlands: BritNed
- 🇧🇪 Belgium: Nemo
- 🇳🇴 Norway: NSL
- 🇩🇰 Denmark: Viking Link

### **Additional Sheets**
- **SP_Data**: 48 settlement periods for time-series charts
- **GSP_Data**: Grid Supply Point template (regional data)
- **IC_Graphics**: Interconnector visual bars (import/export)
- **Live Dashboard**: Raw source data
- **Live_Raw_Interconnectors**: Interconnector flows
- **Live_Raw_REMIT_Outages**: Outage data

---

## 💾 BigQuery Dataset Reference

### **Project**: `inner-cinema-476211-u9` (NOT jibber-jabber-knowledge!)
### **Dataset**: `uk_energy_prod` (US region)
### **Tables**: 185 total

#### **Historical Tables** (`bmrs_*`)
- **Period**: 2020-2025 complete
- **Update**: Batch, 24-48h lag
- **Use**: Long-term analysis, backtesting

#### **Real-Time Tables** (`bmrs_*_iris`)
- **Period**: Last 48-72 hours
- **Update**: Event-driven or sub-hourly (2-30 min)
- **Use**: Live trading, VLP arbitrage
- **Note**: Currently 4-7 days behind due to server capacity

### **Key Tables for BOD & VLP Analysis**

#### 1. **Market Pricing**
```sql
-- bmrs_mid_iris - Day-ahead market prices
-- Update: 30 min | Units: £/MWh, MWh | Status: ✅ Live
SELECT settlementDate, settlementPeriod, marketIndexPrice, marketIndexVolume
FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_mid_iris`
WHERE DATE(settlementDate) = CURRENT_DATE();

-- bmrs_imbalngc - System imbalance prices
-- Update: 30 min | Units: £/MWh, MWh | Status: ✅ Live
SELECT settlementDate, settlementPeriod, 
       systemBuyPrice, systemSellPrice, netImbalanceVolume
FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_imbalngc`
WHERE DATE(settlementDate) = CURRENT_DATE();
```

#### 2. **Balancing Mechanism**
```sql
-- bmrs_boalf_iris - Bid-offer acceptances (dispatch)
-- Update: Event-driven | Units: MW, £/MWh | Status: ✅ Live
SELECT bmUnit, acceptanceNumber, levelFrom, levelTo, 
       acceptancePrice, timeFrom, timeTo
FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_boalf_iris`
WHERE timeFrom >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 1 HOUR);

-- bmrs_bod_iris - Bid-offer data (submitted offers)
-- Update: Daily | Units: MW, £/MWh | Status: ⚠️ Partially skipped
-- Note: 607K rows/batch, may skip due to memory limits
SELECT bmUnitId, pairId, bid, offer, bidVolume, offerVolume
FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_bod_iris`
WHERE bmUnitId = 'T_DRAXX-1' AND DATE(timeFrom) = CURRENT_DATE();
```

#### 3. **System Monitoring**
```sql
-- bmrs_freq_iris - System frequency
-- Update: 2 min | Units: Hz | Status: ⚠️ Lagging 4-7 days
SELECT measurementTime, frequency  -- NOT recordTime!
FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_freq_iris`
WHERE DATE(measurementTime) = CURRENT_DATE();

-- bmrs_fuelinst_iris - Generation by fuel type
-- Update: 5 min | Units: MW | Status: ⚠️ Lagging 4-7 days
-- CRITICAL: Includes interconnectors (INTFR, INTELEC, etc.)
-- Always filter: WHERE fuelType NOT LIKE 'INT%'
SELECT fuelType, SUM(generation) as total_mw
FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_fuelinst_iris`
WHERE DATE(settlementDate) = CURRENT_DATE()
  AND fuelType NOT LIKE 'INT%'  -- Exclude interconnectors!
  AND generation > 0
GROUP BY fuelType;
```

#### 4. **Availability & Constraints**
```sql
-- bmrs_mels_iris - Export limits
-- bmrs_mils_iris - Import limits
-- Update: Event-driven | Units: MW | Status: ⚠️ Delayed days
SELECT bmUnitId, mels AS max_export_mw, validFrom, validTo
FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_mels_iris`
WHERE bmUnitId LIKE '%BESS%'
  AND validTo > CURRENT_TIMESTAMP();
```

### **Units & Conventions**
- **Price**: £/MWh (pounds per megawatt-hour)
- **Volume**: MWh (megawatt-hours, aggregated per settlement period)
- **Power**: MW (megawatts, instantaneous)
- **Frequency**: Hz (Hertz, 50 Hz nominal)
- **Time**: UTC timestamps, settlement periods 1-48 (or 50 on clock change)

### **Key Data Gotchas**
⚠️ `bmrs_fuelinst_iris` includes interconnectors with negative values for exports  
⚠️ `bmrs_freq` uses `measurementTime` NOT `recordTime`  
⚠️ `bmrs_bod` has `bmUnitId` NOT `bmUnit`  
⚠️ Settlement periods: 48 normal, 46 (spring) or 50 (fall) on clock change  
⚠️ All timestamps are UTC, but `settlementDate` is UK local date  

---

## 🔧 VLP Use Case Examples

### **Battery Arbitrage Analysis**
```sql
-- Find profitable charge/discharge windows (>£10/MWh spread)
WITH prices AS (
  SELECT 
    settlementDate, settlementPeriod,
    marketIndexPrice AS mip,
    systemBuyPrice AS sbp,
    systemSellPrice AS ssp
  FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_mid_iris` m
  JOIN `inner-cinema-476211-u9.uk_energy_prod.bmrs_imbalngc` i
    USING(settlementDate, settlementPeriod)
  WHERE DATE(settlementDate) = CURRENT_DATE()
),
windows AS (
  SELECT 
    settlementPeriod, mip, sbp, ssp,
    LAG(ssp, 1) OVER (ORDER BY settlementPeriod) AS prev_sell,
    LEAD(sbp, 1) OVER (ORDER BY settlementPeriod) AS next_buy
  FROM prices
)
SELECT 
  settlementPeriod,
  ROUND(ssp, 2) AS charge_price,
  ROUND(next_buy, 2) AS discharge_price,
  ROUND(next_buy - ssp, 2) AS profit_per_mwh,
  ROUND((next_buy - ssp) * 50, 2) AS profit_50mw_unit
FROM windows
WHERE next_buy - ssp > 10  -- £10/MWh minimum spread
ORDER BY profit_per_mwh DESC;
```

### **VLP Revenue Tracking**
```sql
-- Track VLP unit dispatch and estimated revenue
SELECT 
  b.bmUnit,
  DATE(b.timeFrom) AS dispatch_date,
  COUNT(*) AS num_acceptances,
  SUM(b.levelTo - b.levelFrom) AS total_mwh_dispatched,
  AVG(b.acceptancePrice) AS avg_price_gbp_per_mwh,
  SUM((b.levelTo - b.levelFrom) * b.acceptancePrice) AS estimated_revenue_gbp
FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_boalf_iris` b
WHERE (b.bmUnit LIKE '%FBPGM%'  -- Flexgen battery
    OR b.bmUnit LIKE '%FFSEN%')  -- Another VLP battery
  AND DATE(b.timeFrom) >= DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY)
GROUP BY b.bmUnit, DATE(b.timeFrom)
ORDER BY dispatch_date DESC;
```

### **System Frequency Monitoring**
```sql
-- Recent frequency deviations (stress indicator)
SELECT 
  measurementTime,
  frequency,
  (frequency - 50.0) AS deviation_hz,
  CASE 
    WHEN frequency < 49.8 THEN '🔴 LOW - Grid Stress'
    WHEN frequency > 50.2 THEN '🔴 HIGH - Grid Stress'
    WHEN frequency < 49.9 THEN '⚠️ Low - Watch'
    WHEN frequency > 50.1 THEN '⚠️ High - Watch'
    ELSE '✅ Normal'
  END AS status
FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_freq_iris`
WHERE DATE(measurementTime) = CURRENT_DATE()
  AND ABS(frequency - 50.0) > 0.05  -- Only significant deviations
ORDER BY measurementTime DESC
LIMIT 100;
```

---

## 🛠️ Maintenance Scripts

### **Dashboard Updates**
| Script | Purpose | Time | Frequency |
|--------|---------|------|-----------|
| `update_dashboard_preserve_layout.py` | Main data update (preserves user layout) | 15 sec | Every 15 min (cron) |
| `auto_refresh_outages.py` | Update power station outages | 20 sec | Every 30 min (cron) |
| `create_sp_data_sheet.py` | Refresh 48 settlement periods | 25 sec | Every 30 min (cron) |

### **Flag Fixes**
| Script | Purpose | Time |
|--------|---------|------|
| `fix_interconnector_flags_permanent.py` | Fix broken country flags | 2 sec |
| `verify_flags.py` | Check flags are complete | 2 sec |

### **Combined Update**
```bash
# Full system refresh (all data + flags)
cd "/Users/georgemajor/GB Power Market JJ"

python3 update_dashboard_preserve_layout.py && \
python3 auto_refresh_outages.py && \
python3 create_sp_data_sheet.py && \
python3 verify_flags.py
```

---

## 📚 Documentation Files

### **Dashboard Documentation**
- **DASHBOARD_LAYOUT_FINAL.md** - User layout preferences and update procedures
- **COMPREHENSIVE_REDESIGN_COMPLETE.md** - Dashboard redesign summary
- **FLAG_FIX_TECHNICAL_GUIDE.md** - Why flags break and how to prevent it

### **BigQuery Documentation**
- **BIGQUERY_DATASET_REFERENCE.md** - Complete table reference for BOD/VLP analysis (NEW)
- **STOP_DATA_ARCHITECTURE_REFERENCE.md** - Schema gotchas and known issues
- **PROJECT_CONFIGURATION.md** - Credentials and configuration

### **Architecture & Deployment**
- **UNIFIED_ARCHITECTURE_HISTORICAL_AND_REALTIME.md** - Pipeline design
- **ALMALINUX_DEPLOYMENT_GUIDE.md** - IRIS real-time pipeline setup
- **DEPLOYMENT_COMPLETE.md** - Complete deployment documentation

### **ChatGPT Integration**
- **CHATGPT_INSTRUCTIONS.md** - Query patterns and best practices
- **CHATGPT_ACTUAL_ACCESS.md** - ChatGPT BigQuery access setup

### **Index**
- **DOCUMENTATION_INDEX.md** - All 22+ documentation files categorized

---

## ⚠️ Known Issues & Limitations

### 1. **IRIS Pipeline Lag**
- **Status**: 4-7 days behind real-time
- **Cause**: Single-threaded uploader on 1 vCPU UpCloud server
- **Impact**: `_iris` tables (freq, fuelinst, mels, mils) show stale data
- **Mitigation**: Use historical tables for complete data, monitor `publishTime`

### 2. **BOD Table Processing**
- **Issue**: `bmrs_bod_iris` processing skipped intermittently
- **Cause**: 607K rows/batch exceeds memory limits
- **Workaround**: Query historical `bmrs_bod` table for complete records

### 3. **Interconnector Data in Fuel Table**
- **Issue**: `bmrs_fuelinst_iris` includes interconnector flows (INTFR, INTELEC, etc.)
- **Solution**: Always filter with `WHERE fuelType NOT LIKE 'INT%'`
- **Note**: Exports show as negative generation values

### 4. **Country Flag Emoji Corruption**
- **Issue**: Google Sheets `USER_ENTERED` mode corrupts 2-char emoji flags
- **Solution**: Always use `valueInputOption='RAW'` when writing emojis
- **Quick Fix**: Run `fix_interconnector_flags_permanent.py`

### 5. **Settlement Period Count**
- **Normal**: 48 periods per day (00:00-23:30)
- **Clock Change**: 46 (spring) or 50 (fall)
- **Always verify**: Don't assume 48, check actual data

---

## 🎯 Best Practices

### **BigQuery Queries**
✅ Always specify project ID: `inner-cinema-476211-u9`  
✅ Use US region (not europe-west2)  
✅ Filter fuel data: `WHERE fuelType NOT LIKE 'INT%'`  
✅ Check `publishTime` for data freshness  
✅ Use LIMIT during development to avoid large scans  
✅ Join on `(settlementDate, settlementPeriod)` not timestamps  

### **Dashboard Updates**
✅ Use `valueInputOption='RAW'` for emoji preservation  
✅ Preserve user's custom title: "GB DASHBOARD - Power"  
✅ Keep all fuel types in single section (rows 8-17)  
✅ Don't overwrite outages section (rows 32+)  
✅ Verify flags after updates: `verify_flags.py`  
✅ Monitor data freshness indicator (row 2)  

### **VLP Analysis**
✅ Focus on `_iris` tables for near-real-time data  
✅ Compare day-ahead (MID) vs imbalance (IMBALNGC) prices  
✅ Track acceptances (BOALF) for dispatch validation  
✅ Monitor frequency (FREQ) for grid stress signals  
✅ Check availability limits (MELS/MILS) for constraints  

---

## 📞 Quick Reference

| Need | Command | Time |
|------|---------|------|
| Fix flags | `python3 fix_interconnector_flags_permanent.py` | 2s |
| Check flags | `python3 verify_flags.py` | 2s |
| Update Dashboard | `python3 update_dashboard_preserve_layout.py` | 15s |
| Update outages | `python3 auto_refresh_outages.py` | 20s |
| Refresh SPs | `python3 create_sp_data_sheet.py` | 25s |
| Full refresh | All above commands | 65s |

---

## ✅ Status Summary

**Dashboard**: ✅ All flags complete, user layout preserved  
**BigQuery**: ✅ 185 tables documented, query patterns provided  
**IRIS Pipeline**: ⚠️ 4-7 day lag (server capacity issue)  
**Documentation**: ✅ Complete reference guides created  
**Scripts**: ✅ All maintenance scripts working  

**Last Updated**: November 10, 2025, 15:50 GMT  
**Dashboard URL**: https://docs.google.com/spreadsheets/d/1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA  
**Project ID**: inner-cinema-476211-u9  
**Dataset**: uk_energy_prod (US region)

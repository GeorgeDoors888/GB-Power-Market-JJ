# 📊 GB Power Market Data Inventory - Complete Summary

**Generated**: 6 November 2025  
**Project**: inner-cinema-476211-u9  
**Dataset**: uk_energy_prod  

---

## 🎯 Executive Summary

You have **49 tables and 2 views** containing comprehensive GB electricity market data spanning **2022 to 2025**. This includes:
- **Market prices & imbalances** (155K+ records)
- **Generation fuel mix** (5.7M+ records, 20 fuel types)
- **System frequency data**
- **Balancing mechanism data**
- **Bid-offer data**
- **Demand forecasts**
- **Interconnector flows**

---

## 📈 Currently Active Data Sources

### 1. **bmrs_mid** - Market Index Data (System Prices) ⭐ CURRENTLY USED
**What it contains**: System Sell Price (SSP) and System Buy Price (SBP)

| Metric | Value |
|--------|-------|
| **Total Records** | 155,405 rows |
| **Date Range** | 2022-01-01 to 2025-10-30 |
| **Days of Data** | 1,375 days (~3.8 years) |
| **Price Range** | £-102.92 to £1,561.59/MWh |
| **Average Price** | £53.55/MWh |
| **Total Volume** | 145.2 million MWh |
| **Granularity** | Per settlement period (30-min intervals) |
| **Update Frequency** | Daily (T+2 settlement lag) |

**Key Fields**:
- `settlementDate` - Trading date
- `settlementPeriod` - Period 1-48 (or 1-50 on clock change)
- `price` - Market price (£/MWh)
- `volume` - Traded volume (MWh)
- `dataset` - Data source identifier

**Use Cases**:
- ✅ **Current**: Daily arbitrage analysis
- Price volatility tracking
- Market pattern identification
- Revenue optimization

---

### 2. **bmrs_fuelinst** - Instantaneous Fuel Generation Mix ⭐ READY TO USE
**What it contains**: Real-time generation by fuel type across GB

| Metric | Value |
|--------|-------|
| **Total Records** | 5,691,925 rows |
| **Date Range** | 2022-12-31 to 2025-10-30 |
| **Days of Data** | 1,035 days (~2.8 years) |
| **Fuel Types** | 20 different types |
| **Granularity** | 5-minute intervals |

**Fuel Types Available** (all 20):
1. **CCGT** - Combined Cycle Gas Turbines (297K records)
2. **WIND** - Wind generation (297K records)
3. **NUCLEAR** - Nuclear power (297K records)
4. **BIOMASS** - Biomass generation (297K records)
5. **COAL** - Coal generation (297K records)
6. **NPSHYD** - Non-pumped storage hydro (297K records)
7. **PS** - Pumped storage (297K records)
8. **OCGT** - Open Cycle Gas Turbines (297K records)
9. **OIL** - Oil generation (297K records)
10. **OTHER** - Other sources (297K records)

**Interconnectors** (imports/exports):
11. **INTFR** - France interconnector (297K records)
12. **INTIRL** - Ireland interconnector (297K records)
13. **INTNED** - Netherlands interconnector (297K records)
14. **INTEW** - East-West interconnector (297K records)
15. **INTIFA2** - IFA2 interconnector (297K records)
16. **INTNEM** - Nemo interconnector (297K records)
17. **INTELEC** - ElecLink interconnector (297K records)
18. **INTNSL** - North Sea Link (297K records)
19. **INTVKL** - Viking Link (204K records, started Jul 2023)
20. **INTGRNL** - Greenlink (130K records, started Mar 2024)

**Key Fields**:
- `settlementDate` - Trading date
- `fuelType` - Type of generation/import
- `generation` - MW output
- `startTime` - Timestamp

**Use Cases**:
- Renewable penetration analysis
- Carbon intensity calculation
- Import/export tracking
- Generation mix trends
- Correlation with prices

---

### 3. **bmrs_freq** - System Frequency Data
**What it contains**: GB electricity system frequency measurements

| Metric | Value |
|--------|-------|
| **Total Records** | 0 (empty table) ⚠️ |
| **Status** | Not currently populated |

**Key Fields**:
- `measurementTime` - Timestamp
- `frequency` - System frequency (Hz)

**Note**: This table exists but is currently empty. Would need to be populated from BMRS API if required.

---

### 4. **bmrs_bod** - Bid-Offer Data
**What it contains**: Balancing mechanism bid and offer prices

| Metric | Value |
|--------|-------|
| **Status** | Available but not yet analyzed |
| **Contains** | Unit-level bid/offer pairs |

**Key Fields**:
- `timeFrom`, `timeTo` - Time range
- `bmUnit` - Balancing mechanism unit
- `bidPrice`, `offerPrice` - Prices (£/MWh)
- `bidVolume`, `offerVolume` - Volumes (MW)

**Use Cases**:
- Generator behavior analysis
- Balancing cost forecasting
- Unit-level profitability

---

## 🗂️ Complete Table Inventory (49 Tables)

### **Balancing Mechanism** (5 tables)
- `balancing_acceptances` - Accepted balancing actions
- `balancing_dynamic_sel` - Dynamic selection
- `balancing_nonbm_volumes` - Non-BM balancing volumes
- `balancing_physical_mels` - Maximum Export Limits
- `balancing_physical_mils` - Maximum Import Limits

### **BMRS Core Data** (20+ tables)
- `bmrs_mid` ⭐ - Market Index Data (ACTIVE)
- `bmrs_fuelinst` ⭐ - Fuel generation mix (5.7M rows)
- `bmrs_bod` - Bid-Offer Data
- `bmrs_freq` - System frequency (empty)
- `bmrs_boalf` - Bid-Offer Acceptance Level Flagged
- `bmrs_costs` - System costs
- `bmrs_demand_forecast` - Demand forecasts
- `bmrs_disbsad` - Disaggregated Balancing Services Adjustment Data
- `bmrs_fou2t14d` - Forecasts 2-14 days ahead
- `bmrs_fou2t3yw` - Forecasts 2 weeks-3 years ahead
- `bmrs_fuelhh` - Half-hourly fuel data
- `bmrs_imbalngc` - Imbalance prices NGC
- `bmrs_inddem` - Indicated demand
- `bmrs_indgen` - Indicated generation
- `bmrs_indo` - Indicated imbalance
- `bmrs_itsdo` - Interconnector data
- `bmrs_mdp` - Market depth prices
- `bmrs_mdv` - Market depth volumes
- `bmrs_melngc` - MEL NGC
- `bmrs_mnzt` - Minute zero time
- `bmrs_mzt` - MZT data
- `bmrs_ndf` - Net demand forecast
- `bmrs_ndfd` - Net demand forecast daily
- `bmrs_ndfw` - Net demand forecast weekly
- `bmrs_ndz` - Net demand zero
- `bmrs_netbsad` - Net BSAD
- `bmrs_nonbm` - Non-BM data
- `bmrs_nou2t14d` - National output usable forecasts
- `bmrs_nou2t3yw` - National output usable forecasts long-term
- `bmrs_ntb` - Notice to deliver bids/offers

### **IRIS Alternative Data** (10+ tables)
Alternative/additional data sources with `_iris` suffix:
- `bmrs_beb_iris` - BEB IRIS data
- `bmrs_boalf_iris` - BOALF from IRIS
- `bmrs_bod_iris` - Bid-Offer from IRIS
- `bmrs_freq_iris` - Frequency from IRIS
- `bmrs_fuelinst_iris` - Fuel generation from IRIS
- `bmrs_inddem_iris` - Indicated demand from IRIS
- `bmrs_indgen_iris` - Indicated generation from IRIS
- `bmrs_indo_iris` - Indicated imbalance from IRIS
- `bmrs_mels_iris` - MEL from IRIS
- `bmrs_mid_iris` - Market Index from IRIS
- `bmrs_mils_iris` - MIL from IRIS

### **Unified Views** (2 views)
- `bmrs_boalf_unified` - Combined BOALF data
- `bmrs_fuelinst_unified` - Combined fuel generation

### **Deduplicated Tables** (1 table)
- `bmrs_fuelinst_dedup` - Deduplicated fuel generation data

### **Bid-Offer Data** (1 table)
- `bid_offer_data` - Historical bid-offer information

---

## 🔍 Data Granularity & Time Periods

### Settlement Period Structure
- **Normal Days**: 48 settlement periods (00:00-23:30)
- **Each Period**: 30 minutes
- **Clock Change Days**: 46 periods (spring) or 50 periods (autumn)

### Data Frequencies
| Data Type | Update Frequency | Granularity |
|-----------|-----------------|-------------|
| Market Prices (MID) | Daily (T+2) | 30-minute (per SP) |
| Fuel Generation | Every 5 minutes | 5-minute snapshots |
| System Frequency | Real-time | Second-by-second (when populated) |
| Bid-Offer Data | Per settlement | 30-minute |
| Demand Forecasts | Daily | Various (hourly, daily, weekly) |

---

## 📊 Data Quality Summary

### bmrs_mid (Market Prices)
- ✅ **Completeness**: 1,375 days of continuous data
- ✅ **Consistency**: No duplicates
- ✅ **Accuracy**: Validated against BMRS source
- ⚠️ **Timeliness**: ~7 day lag due to settlement process
- ✅ **Coverage**: All settlement periods captured

### bmrs_fuelinst (Generation Mix)
- ✅ **Completeness**: 1,035 days of data
- ✅ **Coverage**: All 20 fuel types
- ✅ **Frequency**: 5-minute resolution
- ✅ **Volume**: 5.7 million records
- ⚠️ **Note**: Viking Link (INTVKL) starts Jul 2023, Greenlink (INTGRNL) starts Mar 2024

### Known Data Gaps
1. **bmrs_freq**: Empty table (needs population)
2. **Settlement Lag**: All BMRS data has T+2 publishing delay
3. **Historical Gap**: Some tables start 2022, others 2023
4. **Interconnector History**: Newer links have shorter history

---

## 💡 Data Enhancement Opportunities

### 1. **Immediate Use - Already Available**
✅ **Add Generation Mix to Daily Analysis**
```python
# Example: Correlate wind generation with prices
query = """
SELECT 
  DATE(m.settlementDate) as date,
  m.settlementPeriod as sp,
  AVG(m.price) as avg_price,
  SUM(CASE WHEN f.fuelType = 'WIND' THEN f.generation ELSE 0 END) as wind_mw,
  SUM(CASE WHEN f.fuelType = 'SOLAR' THEN f.generation ELSE 0 END) as solar_mw,
  SUM(CASE WHEN f.fuelType = 'CCGT' THEN f.generation ELSE 0 END) as gas_mw
FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_mid` m
LEFT JOIN `inner-cinema-476211-u9.uk_energy_prod.bmrs_fuelinst` f
  ON DATE(m.settlementDate) = DATE(f.settlementDate)
WHERE DATE(m.settlementDate) >= DATE_SUB(CURRENT_DATE(), INTERVAL 14 DAY)
GROUP BY date, sp
"""
```

### 2. **Carbon Intensity Calculation**
Use fuel mix data to calculate:
- Real-time carbon intensity (gCO2/kWh)
- Renewable penetration %
- Zero-carbon generation %

### 3. **Price Forecasting**
Combine data sources:
- Historical prices (bmrs_mid)
- Weather patterns (wind/solar generation)
- Demand forecasts (bmrs_demand_forecast)
- Interconnector flows (INT* fuel types)

### 4. **Arbitrage Refinement**
- Identify low-price periods correlated with high wind
- Predict negative prices based on renewable generation
- Factor in generation mix for storage decisions

---

## 🎯 Recommended Next Steps

### Priority 1: Enhance Current Analysis (Low Effort, High Value)
1. **Add generation mix** to daily battery_arbitrage.py
   - Wind/solar correlation with negative prices
   - Gas generation as price indicator
   - Carbon intensity tracking

### Priority 2: Historical Analysis (Medium Effort, High Value)
2. **Backtest 3+ years of data**
   - Identify seasonal patterns
   - Model price-generation relationships
   - Calculate optimal arbitrage strategies

### Priority 3: Forecasting (High Effort, High Value)
3. **Build predictive models**
   - Next-day price forecasting
   - Renewable generation impact
   - Interconnector flow effects

### Priority 4: Real-time Monitoring (Medium Effort, Medium Value)
4. **Populate bmrs_freq table**
   - System frequency monitoring
   - Grid stability indicators
   - Balancing event detection

---

## 📋 Data Schema Quick Reference

### bmrs_mid (System Prices)
```sql
dataset          STRING    -- Data source identifier
startTime        DATETIME  -- Window start
settlementDate   DATETIME  -- Trading date
settlementPeriod INTEGER   -- Period 1-48/50
price            FLOAT     -- Market price £/MWh
volume           FLOAT     -- Volume MWh
```

### bmrs_fuelinst (Generation Mix)
```sql
settlementDate   DATETIME  -- Trading date
fuelType         STRING    -- CCGT, WIND, NUCLEAR, etc.
generation       FLOAT     -- MW output
startTime        DATETIME  -- Measurement time
```

### bmrs_bod (Bid-Offer Data)
```sql
timeFrom         DATETIME  -- Period start
timeTo           DATETIME  -- Period end
bmUnit           STRING    -- Balancing unit
bidPrice         FLOAT     -- Bid price £/MWh
offerPrice       FLOAT     -- Offer price £/MWh
bidVolume        FLOAT     -- Bid volume MW
offerVolume      FLOAT     -- Offer volume MW
```

---

## 💰 Storage Costs

### Current BigQuery Storage
- **Total Dataset Size**: ~50-100 MB (estimated)
- **Storage Cost**: $0.00/month (within 10 GB free tier)
- **Query Cost**: ~$0.0009/month (current usage)
- **Total Cost**: **< $0.01/month** 🎉

### If You Add More Data
- Next 10 GB: Still free
- After 20 GB: $0.02/GB/month
- Query costs: $5/TB processed (first 1TB free)

---

## 🔗 Data Relationships

```
bmrs_mid (Prices)
    │
    ├── Same settlementDate/Period ──┐
    │                                 │
bmrs_fuelinst (Generation)           │
    │                                 │
    └── Correlation Analysis ────────┘
                │
                ├── High Wind → Low/Negative Prices
                ├── High Demand → High Prices
                └── Low Gas → Variable Prices

bmrs_bod (Bids/Offers)
    │
    └── Unit-level detail for prices

bmrs_demand_forecast
    │
    └── Forward-looking price drivers
```

---

## 📞 Data Access Commands

### List All Tables
```bash
bq ls --format=pretty inner-cinema-476211-u9:uk_energy_prod
```

### Check Table Schema
```bash
bq show --schema inner-cinema-476211-u9:uk_energy_prod.TABLE_NAME
```

### Sample Data
```bash
bq query --use_legacy_sql=false "
  SELECT * FROM \`inner-cinema-476211-u9.uk_energy_prod.TABLE_NAME\`
  LIMIT 10
"
```

### Export to CSV
```bash
bq extract \
  --destination_format=CSV \
  inner-cinema-476211-u9:uk_energy_prod.TABLE_NAME \
  gs://your-bucket/output.csv
```

---

## 📚 Documentation References

- **MASTER_SYSTEM_DOCUMENTATION.md** - Complete system architecture
- **BIGQUERY_COMPLETE.md** - BigQuery setup details
- **BIGQUERY_OPTIMIZATION_ANALYSIS.md** - Query optimization
- **battery_arbitrage.py** - Current analysis script

---

**Summary**: You have a **comprehensive 3.8-year dataset** covering prices, generation, and market operations. The **bmrs_mid** table is actively used daily. The **bmrs_fuelinst** table (5.7M rows, 20 fuel types) is ready to add immediate value by correlating generation mix with prices. Total cost remains under **1 cent/month**. 🚀

*Last Updated: 2025-11-06*

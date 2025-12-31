# System Operations Data Guide

**Date**: December 30, 2025  
**Status**: ✅ Working - System Operations data available and functional

---

## ✅ CURRENTLY AVAILABLE: Generation & Fuel Mix

### What You Have
- **Table**: `bmrs_fuelinst_iris` (Fuel Instruction data)
- **Coverage**: Real-time + last 48 hours
- **Data Points**: 20 fuel types, 48 settlement periods/day
- **Update Frequency**: Every 30 minutes

### Fuel Types Available (20 Total)

**Thermal Generation**:
- CCGT (Gas Combined Cycle)
- COAL (Currently 0 MW - no coal in 2025)
- OCGT (Open Cycle Gas Turbine)
- OIL (Emergency backup)
- BIOMASS (Drax, etc.)

**Renewable**:
- WIND (All wind farms aggregated)
- NPSHYD (Non-pumped storage hydro)
- OTHER (Small renewables)

**Nuclear**:
- NUCLEAR (EDF fleet: Sizewell, Torness, Heysham, etc.)

**Interconnectors** (7 Imports):
- INTNSL (Norway - North Sea Link, 1.4 GW capacity)
- INTVKL (Norway - Viking Link, 1.4 GW capacity)
- INTFR (France - IFA, 2 GW capacity)
- INTIFA2 (France - IFA2, 1 GW capacity)
- INTNEM (Belgium - Nemo, 1 GW capacity)
- INTELEC (Belgium - Eleclink, 1 GW capacity)
- INTNED (Netherlands - BritNed, 1 GW capacity)

**Interconnectors** (3 Exports):
- INTIRL (Ireland - Moyle, 500 MW capacity)
- INTEW (Ireland - East-West, 500 MW capacity)
- INTGRNL (Ireland - Greenlink, 500 MW capacity)

**Storage**:
- PS (Pumped Storage: Dinorwig, Cruachan, Ffestiniog)

---

## 📊 Example: Dec 29-30, 2025 System Operations

```
Generation Mix (2-day total):
├── CCGT (Gas):      5,364 GWh (35.3%)  ← Largest source
├── WIND:            3,352 GWh (22.1%)  ← Second largest
├── NUCLEAR:         2,062 GWh (13.6%)
├── BIOMASS:         1,491 GWh (9.8%)
├── NPSHYD:            235 GWh (1.5%)
├── OTHER:             221 GWh (1.5%)
├── OCGT:                4 GWh (0.0%)
└── COAL/OIL:            0 GWh (0.0%)   ← Inactive

Interconnector Balance:
├── Imports:         3,490 GWh (23.0%)
│   ├── INTNSL:        733 GWh (Norway)
│   ├── INTVKL:        690 GWh (Norway)
│   ├── INTFR:         607 GWh (France)
│   ├── INTNEM:        393 GWh (Belgium)
│   ├── INTIFA2:       380 GWh (France)
│   ├── INTELEC:       377 GWh (Belgium)
│   └── INTNED:        311 GWh (Netherlands)
└── Exports:          -632 GWh (-4.2%)
    ├── INTGRNL:      -266 GWh (Ireland)
    ├── INTIRL:       -189 GWh (Ireland)
    └── INTEW:        -177 GWh (Ireland)

Net Import: 2,858 GWh (18.8% of total demand)

Pumped Storage:        -9 GWh (charging mode)

Total Generation: 15,188 GWh over 2 days
Average: 316 GW per settlement period
```

---

## ❌ NOT CURRENTLY IN "SYSTEM OPERATIONS"

### Outage Data (Needs Different Category)

**For Power Station Outages, Use**:
1. **REMIT Messages**
   - Table: `remit_messages` (if available)
   - Contains: Urgent market messages about outages
   - Example: "Sizewell B offline due to boiler fault"

2. **BMU Availability**
   - Table: `bmrs_disptav` (Dispatch Availability)
   - Shows: Available vs unavailable capacity per BMU
   - Example: "Drax Unit 5: 660 MW available, 0 MW unavailable"

3. **Physical Notifications**
   - Table: `bmrs_phybmdata` (Physical BM Data)
   - Shows: PN levels (Physical Notifications) vs FPN (Final Physical Notifications)
   - Sudden drops = potential outages

### System Frequency Data

**For Frequency & System Stability**:
- Table: `bmrs_freq` (System Frequency)
- Coverage: 1-minute resolution
- Shows: Grid frequency (target 50 Hz, ±0.2 Hz normal)
- Deviations = system stress events

### Constraint Actions

**For Grid Constraints & Redispatch**:
- Table: `bmrs_boalf_complete` (Balancing Acceptances)
- Shows: Bid-Offer Acceptances (BM actions)
- Example: Wind curtailment due to transmission constraints

---

## 🔧 HOW TO GET OUTAGE DATA

### Option 1: Add Outage Category to Analysis Sheet

**New Category**: "🚨 Outages & Availability"
- Query `bmrs_disptav` for unavailable capacity
- Join with `bmu_registration_data` for unit names
- Filter to: `unavailableCapacity > 0`

### Option 2: Use REMIT Messages (if available)

```sql
SELECT 
    messageTime,
    messageType,
    unavailabilityType,
    assetName,
    installedCapacity,
    unavailableCapacity,
    expectedStartTime,
    expectedEndTime
FROM `inner-cinema-476211-u9.uk_energy_prod.remit_messages`
WHERE messageTime >= '2025-12-29'
AND unavailabilityType IN ('Unplanned', 'Planned')
ORDER BY messageTime DESC
```

### Option 3: Frequency Anomalies (Proxy for Issues)

```sql
SELECT 
    measurementTime,
    frequency,
    ABS(frequency - 50.0) as deviation_hz
FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_freq`
WHERE measurementTime >= '2025-12-29'
AND ABS(frequency - 50.0) > 0.2  -- Significant deviation
ORDER BY deviation_hz DESC
```

---

## 📈 NEXT STEPS TO ADD OUTAGES

### 1. Check if Tables Exist
```bash
python3 -c "
from google.cloud import bigquery
client = bigquery.Client(project='inner-cinema-476211-u9')
tables = client.list_tables('uk_energy_prod')
outage_tables = [t.table_id for t in tables if 'disptav' in t.table_id or 'remit' in t.table_id or 'phybm' in t.table_id]
print('Outage-related tables:', outage_tables)
"
```

### 2. Add New Category to generate_analysis_report.py

Add after "System Operations" category:

```python
# Outages & Availability
if '🚨 Outages' in category or 'Outages & Availability' in category:
    return f"""
    SELECT
        CAST(settlementDate AS DATE) as date,
        settlementPeriod,
        bmUnitId,
        nationalGridBmUnit,
        maximumGenerationCapacity,
        availableCapacity,
        (maximumGenerationCapacity - availableCapacity) as unavailableCapacity
    FROM `{PROJECT_ID}.uk_energy_prod.bmrs_disptav`
    WHERE settlementDate >= '{from_dt}'
    AND settlementDate <= '{to_dt}'
    AND (maximumGenerationCapacity - availableCapacity) > 0
    ORDER BY unavailableCapacity DESC, settlementDate, settlementPeriod
    LIMIT 10000
    """
```

### 3. Update Google Sheets Dropdown

Add to Cell B11 (Report Category):
```
🚨 Outages & Availability - Power station unavailability
```

---

## 💡 SUMMARY

### ✅ What's Working Now
- **System Operations**: ✅ All 20 fuel types, 525 records per day
- **Generation Mix**: ✅ CCGT, Wind, Nuclear, Biomass, etc.
- **Interconnectors**: ✅ All 10 interconnector flows
- **Storage**: ✅ Pumped storage charging/discharging

### ❓ What You Might Be Looking For
- **Outages**: Need `bmrs_disptav` or `remit_messages` (different category)
- **Frequency**: Need `bmrs_freq` (system stability)
- **Constraints**: Need `bmrs_boalf_complete` (curtailment events)

### 🚀 Recommendation
If you want to see **outage data**, I can:
1. Check if `bmrs_disptav` table exists
2. Add "Outages & Availability" category to the script
3. Update Google Sheets dropdown

**The current System Operations category IS working correctly** - it shows generation mix, not outages.

---

**File**: SYSTEM_OPERATIONS_DATA_GUIDE.md  
**Author**: AI Coding Agent  
**Date**: December 30, 2025

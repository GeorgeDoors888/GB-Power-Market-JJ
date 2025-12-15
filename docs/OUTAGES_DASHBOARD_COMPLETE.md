# Dashboard Outages Section - Complete Implementation

**Date**: 21 November 2025  
**Status**: ✅ Production Ready

## Overview

Enhanced outages section for the GB Power Market Dashboard with comprehensive generator name lookups, proper fuel type classification, interconnector trading unit deduplication, and automatic formatting.

## Quick Start

### Update Dashboard with Latest Outages

```bash
# Update entire dashboard
python3 update_dashboard_preserve_layout.py && python3 update_outages_enhanced.py
```

**Or update just outages:**
```bash
python3 update_outages_enhanced.py
```

## Features

### ✅ Automatic Generator Name Lookup
- **150+ generator names** hardcoded in lookup tables
- No more "Unknown" entries
- Names automatically applied based on BM Unit codes

**Examples:**
- `DAMC-1` → "🔥 Damhead Creek"
- `T_HEYM27` → "⚛️ Heysham 2 Unit 7"
- `I_IEG-IFA2` → "🔌 IFA2 France"

### ✅ Interconnector Trading Unit Deduplication
Interconnectors have separate BM Units for import (I_IED) and export (I_IEG) directions representing the **same physical cable**. The script now groups these trading unit pairs:

**Before Deduplication:**
```
I_IEG-IFA2  IFA2 France  1,014 MW
I_IED-IFA2  IFA2 France  1,014 MW
Total: 2,028 MW (WRONG - double counting!)
```

**After Deduplication:**
```
IFA2        IFA2 France  1,014 MW
Total: 1,014 MW (CORRECT - counted once)
```

**SQL Logic:**
```sql
CASE 
    WHEN affectedUnit LIKE 'I_IE%' THEN 
        REGEXP_REPLACE(affectedUnit, r'^I_IE[DG]-', '')
    ELSE affectedUnit
END as groupKey
```

### ✅ Proper Fuel Type Classification
Automatic fuel type mapping:
- **CCGT**: Gas combined cycle (Damhead Creek, Little Barford, Pembroke)
- **NUCLEAR**: Nuclear stations (Heysham, Torness, Hartlepool)
- **Interconnector**: Cross-border cables (IFA, IFA2, ElecLink, BritNed)
- **Hydro Pumped Storage**: Pumped hydro (Cruachan, Dinorwig, Ffestiniog)
- **Wind Offshore**: Offshore wind farms (Walney, Gwynt y Môr, Moray, Seagreen)
- **Wind Onshore**: Onshore wind farms
- **BIOMASS**: Biomass stations (Drax, Lynemouth)
- **Battery Storage**: Grid batteries (Thurso, Blyth)

### ✅ Timestamp Formatting
Handles multiple timestamp formats:
- ISO datetime strings: `2025-11-19 14:00:00`
- Excel serial dates: `45970.375` → `2025-11-19 09:00:00`
- Pandas Timestamp objects

**Function:**
```python
def format_timestamp(ts_value):
    # Try Excel serial date first (40000-50000 range)
    if 40000 <= ts_float <= 50000:
        excel_epoch = datetime(1899, 12, 30)
        dt = excel_epoch + timedelta(days=ts_float)
        return dt.strftime('%Y-%m-%d %H:%M:%S')
    # Then try ISO parsing...
```

### ✅ Column Headers
Automatically adds professional headers:
```
Asset Name | BM Unit | Fuel Type | Normal (MW) | Unavail (MW) | Capacity Offline | Cause | Start Time
```

### ✅ Total Summary
Clean summary row with proper formatting:
```
TOTAL UNAVAILABLE CAPACITY: 11,761 MW     (29 outages)
```

## Dashboard Layout

```
Row 22:    [Header Row]
           Asset Name | BM Unit | Fuel Type | Normal (MW) | Unavail (MW) | Capacity Offline | Cause | Start Time

Rows 23-N: [Outage Data Rows]
           🔌 IFA2 France | IFA2 | Interconnector | 1014 | 1014 | 🟥🟥🟥... 100.0% | Planned Maintenance | 2025-10-27 06:00:00
           🔥 Damhead Creek | DAMC-1 | CCGT | 812 | 812 | 🟥🟥🟥... 100.0% | Planned Outage | 2025-11-19 14:00:00
           ...

Row N+2:   [Summary Row]
           TOTAL UNAVAILABLE CAPACITY: 11,761 MW     (29 outages)
```

**Dynamic Sizing**: Section automatically expands/contracts based on number of active outages.

## Data Architecture

### Source Table
```
BigQuery: inner-cinema-476211-u9.uk_energy_prod.bmrs_remit_unavailability
```

**Key Columns:**
- `affectedUnit` - BM Unit code (DAMC-1, T_HEYM27, I_IEG-IFA2)
- `assetName` - Often "Unknown" in REMIT data
- `fuelType` - Fuel type from REMIT (may be generic)
- `normalCapacity` - Normal capacity (MW)
- `unavailableCapacity` - Currently unavailable (MW)
- `cause` - Outage reason
- `eventStartTime` - When outage started
- `publishTime` - REMIT message timestamp
- `eventStatus` - 'Active' for current outages

### Deduplication Query

```sql
WITH all_outages AS (
    SELECT *
    FROM bmrs_remit_unavailability
    WHERE eventStatus = 'Active'
      AND TIMESTAMP(eventStartTime) <= CURRENT_TIMESTAMP()
      AND (TIMESTAMP(eventEndTime) >= CURRENT_TIMESTAMP() OR eventEndTime IS NULL)
      AND unavailableCapacity >= 100  -- Filter small outages
),
latest_per_unit AS (
    SELECT 
        affectedUnit,
        MAX(publishTime) as latest_publish
    FROM all_outages
    GROUP BY affectedUnit
),
with_latest AS (
    SELECT o.*
    FROM all_outages o
    INNER JOIN latest_per_unit lpu 
        ON o.affectedUnit = lpu.affectedUnit 
        AND o.publishTime = lpu.latest_publish
),
deduplicated AS (
    SELECT 
        -- Group interconnector trading unit pairs
        CASE 
            WHEN affectedUnit LIKE 'I_IE%' THEN 
                REGEXP_REPLACE(affectedUnit, r'^I_IE[DG]-', '')
            ELSE affectedUnit
        END as groupKey,
        ANY_VALUE(affectedUnit) as affectedUnit,
        MAX(unavailableCapacity) as unavailableCapacity,
        ANY_VALUE(cause) as cause,
        ANY_VALUE(eventStartTime) as eventStartTime
        -- ... other fields
    FROM with_latest
    GROUP BY groupKey
)
SELECT * FROM deduplicated
ORDER BY unavailableCapacity DESC
```

**Deduplication Logic:**
1. Filter for active outages >= 100 MW
2. Get latest `publishTime` per BM Unit (handles multiple REMIT messages)
3. Group interconnector pairs (I_IED-IFA2 + I_IEG-IFA2 → IFA2)
4. Take `MAX(unavailableCapacity)` per group

## Generator Name Lookup Tables

### Sample from GENERATOR_NAMES Dictionary

```python
GENERATOR_NAMES = {
    # Gas CCGT (50+ stations)
    'DAMC-1': 'Damhead Creek',
    'LBAR-1': 'Little Barford',
    'DIDCB6': 'Didcot B Unit 6',
    'PEMB-11': 'Pembroke Unit 1',
    'PEMB-21': 'Pembroke Unit 2',
    'CNQPS-1': 'Connah\'s Quay Unit 1',
    
    # Nuclear (7 units)
    'T_HEYM27': 'Heysham 2 Unit 7',
    'T_HEYM12': 'Heysham 1 Unit 2',
    'T_TORN-2': 'Torness Unit 2',
    'T_HRTL-1': 'Hartlepool Unit 1',
    
    # Hydro Pumped Storage (20+ units)
    'CRUA-3': 'Cruachan Unit 3',
    'CRUA-4': 'Cruachan Unit 4',
    'DINO-1': 'Dinorwig Unit 1',
    'FFES-1': 'Ffestiniog Unit 1',
    
    # Wind Offshore (30+ farms)
    'WDNSO-1': 'Walney Offshore 1',
    'GYMRO-15': 'Gwynt y Môr',
    'T_SGRWO-1': 'Seagreen',
    'SOFWO-11': 'Sofia Offshore',
    
    # Biomass
    'DRAXX-1': 'Drax Unit 1',
    'DRAXX-4': 'Drax Unit 4',
    'LNMTH-1': 'Lynemouth Unit 1',
    
    # Battery Storage
    'THURB-1': 'Thurso Battery 1',
    'BLHLB-1': 'Blyth Battery 1',
    
    # Interconnectors
    'I_IEG-IFA2': 'IFA2 France',
    'I_IED-IFA2': 'IFA2 France',
    'I_IEG-FRAN1': 'IFA France (ElecLink)',
    'I_IED-FRAN1': 'IFA France (ElecLink)',
    'I_IBD-BRTN1': 'BritNed (Netherlands)',
    'I_IBG-BRTN1': 'BritNed (Netherlands)',
    # ... 150+ total entries
}
```

### FUEL_TYPE_MAP Dictionary

```python
FUEL_TYPE_MAP = {
    # Gas CCGT
    'DAMC-1': 'CCGT',
    'LBAR-1': 'CCGT',
    # ... 50+ CCGT entries
    
    # Nuclear
    'T_HEYM27': 'NUCLEAR',
    'T_TORN-2': 'NUCLEAR',
    # ... 7 nuclear entries
    
    # Hydro Pumped Storage
    'CRUA-3': 'Hydro Pumped Storage',
    'DINO-1': 'Hydro Pumped Storage',
    # ... 20+ hydro entries
    
    # Wind Offshore
    'WDNSO-1': 'Wind Offshore',
    'GYMRO-15': 'Wind Offshore',
    # ... 30+ wind entries
    
    # Biomass
    'DRAXX-1': 'BIOMASS',
    'LNMTH-1': 'BIOMASS',
    # ... 6 biomass entries
    
    # Battery
    'THURB-1': 'Battery Storage',
    'BLHLB-1': 'Battery Storage',
    # ... 7 battery entries
    
    # Interconnectors
    'I_IEG-IFA2': 'Interconnector',
    'I_IED-IFA2': 'Interconnector',
    # ... 6 interconnector entries
}
```

## Current Performance

**As of 21 November 2025 12:04:**

- **29 unique outages** (after deduplication)
- **11,761 MW** total unavailable capacity
- **Breakdown:**
  - 2× IFA2 France interconnectors: 2,028 MW → **1,014 MW** (deduplicated)
  - 2× IFA France interconnectors: 3,000 MW → **1,500 MW** (deduplicated)
  - 3× CCGT gas stations: 2,208 MW
  - 5× Nuclear stations: 3,125 MW
  - 6× Hydro pumped storage: 677 MW
  - Multiple wind, biomass, battery units

## Key Improvements

### Before This Implementation
❌ Generator names: "Unknown"  
❌ Fuel types: Generic or wrong  
❌ Timestamps: Excel serial numbers (45970.375)  
❌ Interconnectors: Double-counted (26,556 MW with 13x IFA duplicates)  
❌ No headers  
❌ No total summary  

### After This Implementation
✅ Generator names: "Damhead Creek", "Heysham 2 Unit 7"  
✅ Fuel types: Accurate classification  
✅ Timestamps: Formatted (2025-11-19 14:00:00)  
✅ Interconnectors: Deduplicated by trading unit (11,761 MW)  
✅ Professional headers  
✅ Clean total summary  

## Maintenance

### Adding New Generators

When a new generator appears as "Unknown", add to both dictionaries:

```python
# In update_outages_enhanced.py

GENERATOR_NAMES = {
    # ... existing entries ...
    'NEWUNIT-1': 'New Power Station Name',
}

FUEL_TYPE_MAP = {
    # ... existing entries ...
    'NEWUNIT-1': 'CCGT',  # or appropriate fuel type
}
```

### Testing

```bash
# Test query (check deduplication working)
python3 -c "
from google.cloud import bigquery
import os
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'inner-cinema-credentials.json'
client = bigquery.Client(project='inner-cinema-476211-u9', location='US')

query = '''
SELECT affectedUnit, COUNT(*) as count
FROM \`inner-cinema-476211-u9.uk_energy_prod.bmrs_remit_unavailability\`
WHERE eventStatus = 'Active'
  AND affectedUnit LIKE 'I_IE%'
GROUP BY affectedUnit
ORDER BY count DESC
'''

df = client.query(query).to_dataframe()
print(df)
"
```

## Files

### Primary Script
- **`update_outages_enhanced.py`** - Main outages updater (530 lines)

### Supporting Scripts
- **`update_dashboard_preserve_layout.py`** - Main dashboard updater (fuel, interconnectors)

### Documentation
- **`OUTAGES_DASHBOARD_COMPLETE.md`** - This file
- **`DASHBOARD_UPDATE_PROCEDURE.md`** - Overall dashboard update procedures
- **`STOP_DATA_ARCHITECTURE_REFERENCE.md`** - Critical data architecture warnings

## Common Issues

### Issue: "Unknown" Generator Names Still Appearing

**Cause**: New BM Unit not in lookup tables  
**Solution**: Add to `GENERATOR_NAMES` and `FUEL_TYPE_MAP` dictionaries

### Issue: Interconnector Still Double-Counted

**Cause**: New interconnector BM Unit pattern not matching regex  
**Solution**: Check affectedUnit pattern and update deduplication logic if needed

### Issue: Timestamps Showing Excel Serial Numbers

**Cause**: `eventStartTime` column format changed  
**Solution**: `format_timestamp()` function should handle automatically, but verify Excel date range (40000-50000)

### Issue: Total Not Matching Sum of Individual Outages

**Cause**: May be filtering < 100 MW outages  
**Solution**: Check query filter: `WHERE unavailableCapacity >= 100`

## API Reference

### Main Functions

#### `query_outages_enhanced(bq_client)`
Queries BigQuery for active outages with deduplication.

**Returns:** `pandas.DataFrame` with columns:
- `affectedUnit` - BM Unit code
- `assetName` - Station name (often "Unknown")
- `fuelType` - Fuel type
- `normalCapacity` - Normal capacity (MW)
- `unavailableCapacity` - Unavailable capacity (MW)
- `pct_unavailable` - Percentage unavailable
- `cause` - Outage cause
- `eventStartTime` - Start time
- `publishTime` - REMIT publish time

#### `format_timestamp(ts_value)`
Formats various timestamp formats to YYYY-MM-DD HH:MM:SS.

**Parameters:**
- `ts_value` - Timestamp (datetime, string, or Excel serial float)

**Returns:** `str` - Formatted timestamp

#### `update_outages_section(dashboard, outages_df)`
Updates Google Sheets Dashboard with outages data.

**Parameters:**
- `dashboard` - gspread Worksheet object
- `outages_df` - DataFrame from `query_outages_enhanced()`

**Updates:**
- Rows 22-N: Header + outage data
- Row N+2: Total summary

## Monitoring

### Check Outages in BigQuery

```sql
SELECT 
    affectedUnit,
    assetName,
    fuelType,
    unavailableCapacity,
    cause,
    eventStartTime
FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_remit_unavailability`
WHERE eventStatus = 'Active'
  AND TIMESTAMP(eventStartTime) <= CURRENT_TIMESTAMP()
  AND unavailableCapacity >= 100
ORDER BY unavailableCapacity DESC
LIMIT 20
```

### Check Dashboard Status

```bash
python3 -c "
import pickle
import gspread
from pathlib import Path

with open('token.pickle', 'rb') as f:
    creds = pickle.load(f)

gc = gspread.authorize(creds)
sheet = gc.open_by_key('1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA')
dashboard = sheet.worksheet('Dashboard')

# Check summary row
summary = dashboard.acell('A54').value
print(f'Summary: {summary}')
"
```

## Changelog

### 2025-11-21 - v2.0 - Complete Rewrite
- ✅ Added 150+ generator name lookups
- ✅ Added interconnector trading unit deduplication
- ✅ Added proper fuel type classification
- ✅ Added timestamp formatting (handles Excel serial dates)
- ✅ Added column headers
- ✅ Added clean total summary row
- ✅ Fixed double-counting of interconnectors
- ✅ Removed MW units confusion (generation column is in MW, not MWh)

### 2025-11-20 - v1.0 - Initial Version
- Basic outage display
- Manual deduplication by affectedUnit
- Generic "Unknown" names

## Credits

**Project**: GB Power Market Dashboard  
**Maintainer**: George Major (george@upowerenergy.uk)  
**Repository**: https://github.com/GeorgeDoors888/GB-Power-Market-JJ  
**Documentation**: DOCUMENTATION_INDEX.md

---

**Last Updated**: 21 November 2025  
**Status**: ✅ Production Ready  
**Next Review**: When new generators appear as "Unknown"

# NESO & ELEXON API Data Guide: Batteries & Virtual Lead Parties

**Date**: 6 November 2025  
**Focus**: Battery storage and Virtual Lead Party (VLP) data availability

---

## 🎯 Executive Summary

**What you need to know**:
- ✅ **Battery data IS available** through NESO/ELEXON APIs
- ✅ **BMU (Balancing Mechanism Unit) data** includes batteries
- ⚠️ **VLP identification** requires cross-referencing multiple datasets
- 🔋 **Your workspace already has** 391M rows of bid-offer data (BOD table)
- 📊 **Real-time IRIS stream** provides live battery dispatch data

---

## 📡 Data Sources Overview

### **1. ELEXON BMRS API** (Primary Source)
- **Base URL**: `https://data.elexon.co.uk/bmrs/api/v1`
- **Authentication**: No API key required for public data
- **Format**: JSON (compatible with IRIS format)
- **Coverage**: Historical + real-time data

### **2. NESO Data Portal**
- **URL**: https://www.neso.energy/data-portal
- **Content**: DNO boundaries, generator registers, balancing costs
- **Format**: CSV, Excel, GeoJSON
- **Update Frequency**: Varies by dataset (weekly to real-time)

### **3. IRIS Real-Time Stream** (What you're using)
- **Purpose**: Live settlement period data
- **Tables**: `bmrs_*_iris` suffix in your BigQuery
- **Latency**: Near real-time (< 5 minutes)
- **Coverage**: Last ~7 days only

---

## 🔋 Battery Storage Data - Where to Find It

### **Option 1: BOD (Bid-Offer Data)** ⭐ BEST FOR BATTERIES

**What it contains**:
- Every bid and offer submitted by BMUs (including batteries)
- Settlement period prices and volumes
- Acceptance data (when NESO dispatched the unit)

**ELEXON API Endpoint**:
```
GET /datasets/BOD
```

**Your BigQuery Tables**:
- `bmrs_bod` - Historical (391,287,533 rows!) ✅ YOU HAVE THIS
- `bmrs_bod_iris` - Real-time ✅ YOU HAVE THIS

**Key Columns**:
```sql
bmUnitId          -- Balancing Mechanism Unit ID (battery identifier)
settlementDate    -- Date of settlement period
settlementPeriod  -- 1-48 (half-hourly periods)
bidPrice          -- Price to reduce output (£/MWh)
offerPrice        -- Price to increase output (£/MWh)
bidVolume         -- MW capacity for reduction
offerVolume       -- MW capacity for increase
```

**Identifying Batteries**:
- BMU IDs often contain: "BESS", "STOR", "BTRY"
- Cross-reference with REMIT asset data (fuel type = "Other")
- Check your `All_Generators.xlsx` for "Stored Energy" fuel type

**Example Query**:
```sql
SELECT 
  bmUnitId,
  settlementDate,
  settlementPeriod,
  bidPrice,
  offerPrice,
  bidVolume,
  offerVolume
FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_bod`
WHERE bmUnitId LIKE '%BESS%' 
   OR bmUnitId LIKE '%STOR%'
   OR bmUnitId LIKE '%BTRY%'
   AND settlementDate >= '2024-01-01'
ORDER BY settlementDate DESC, settlementPeriod
```

---

### **Option 2: BOALF (Bid-Offer Acceptance Level Flagged)**

**What it contains**:
- Actual dispatched volumes (what NESO accepted)
- Acceptance numbers and timestamps
- Flagged acceptances (NIV, PAR, etc.)

**ELEXON API Endpoint**:
```
GET /datasets/BOALF
```

**Your BigQuery Tables**:
- `bmrs_boalf` - Historical (11,330,547 rows)
- `bmrs_boalf_iris` - Real-time ✅ YOU HAVE THIS
- `bmrs_boalf_unified` - Combined view

**Key Columns**:
```sql
bmUnitId          -- Battery unit ID
acceptanceNumber  -- Unique acceptance ID
acceptanceTime    -- When NESO dispatched
levelFrom         -- Starting MW level
levelTo           -- Ending MW level  
soFlag            -- SO flag (NIV, PAR, etc.)
storFlag          -- STOR flag
```

**Example Query - Battery Dispatch History**:
```sql
SELECT 
  bmUnitId,
  acceptanceTime,
  levelFrom,
  levelTo,
  (levelTo - levelFrom) as dispatch_mw,
  soFlag,
  storFlag
FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_boalf`
WHERE bmUnitId LIKE '%BESS%'
  AND DATE(acceptanceTime) >= '2025-01-01'
ORDER BY acceptanceTime DESC
```

---

### **Option 3: Physical Notifications (PN)**

**What it contains**:
- Physical notification levels (planned output)
- Min/max stable export/import limits
- Run-up and run-down rates

**ELEXON API Endpoint**:
```
GET /datasets/PN
GET /balancing/physical         -- Aggregated view
```

**Your BigQuery Table**:
- ❓ Not currently in your workspace (can be added)

**Key Columns**:
- `bmUnitId` - Battery identifier
- `physicalNotificationLevel` - Planned MW output
- `settlementDate`, `settlementPeriod`

---

### **Option 4: Dynamic Parameters**

**Battery-specific technical parameters**:

**SEL/SIL (Stable Export/Import Limits)**:
```
GET /datasets/SEL  -- Max export (discharge)
GET /datasets/SIL  -- Max import (charge)
```

**MELS/MILS (Max Export/Import Limits)**:
```
GET /datasets/MELS  -- You have bmrs_mels_iris ✅
GET /datasets/MILS  -- You have bmrs_mils_iris ✅
```

**Run Rates** (how fast battery can ramp):
```
GET /datasets/RURE  -- Run-up rate export
GET /datasets/RURI  -- Run-up rate import
GET /datasets/RDRE  -- Run-down rate export
GET /datasets/RDRI  -- Run-down rate import
```

**Example - Battery Ramping Capability**:
```sql
SELECT 
  m.bmUnitId,
  m.settlementDate,
  m.settlementPeriod,
  m.levelExport as max_discharge_mw,
  m.levelImport as max_charge_mw,
  (m.levelExport + m.levelImport) as total_capacity_mw
FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_mels_iris` m
WHERE m.bmUnitId LIKE '%BESS%'
ORDER BY m.settlementDate DESC, m.settlementPeriod
```

---

### **Option 5: B1610 (Actual Generation Per Unit)**

**What it contains**:
- Actual measured output for each BMU
- 15-minute resolution
- Shows real battery charging/discharging

**ELEXON API Endpoint**:
```
GET /datasets/B1610
```

**Key Columns**:
- `bmUnitId` - Battery identifier
- `startTime` - Measurement timestamp
- `activeFlag` - Active/Inactive
- `actualGeneration` - MW output (negative = charging)

---

## 🏢 Virtual Lead Parties (VLP) - Identification

### **What is a VLP?**
A Virtual Lead Party aggregates multiple small generation/storage units under a single BMU ID for balancing market participation.

### **How to Identify VLPs**:

**Method 1: REMIT Dataset**
```
GET /datasets/REMIT
GET /remit/list/by-publish
```

**Contains**:
- Asset names and IDs
- Participant information
- Market messages (outages, availability)
- Asset classifications

**Example**:
```sql
-- Query REMIT data for aggregated assets
SELECT 
  asset_id,
  asset_name,
  participant,
  fuel_type,
  installed_capacity
FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_remit`
WHERE asset_name LIKE '%Virtual%'
   OR asset_name LIKE '%Aggregat%'
   OR asset_name LIKE '%Portfolio%'
```

**Method 2: BMU Reference Data**
```
GET /reference/bmunits/all
```

**Returns**:
- All BMU IDs
- Lead party names
- BMU types
- National grid zones

**Method 3: TUDM (Trading Unit Data)**
```
GET /datasets/TUDM
```

**Shows**:
- Trading units and their composition
- BMU to trading unit mapping
- Party names

---

## 📊 Your Current Data Assets

### **✅ What You Already Have**:

| Dataset | Table Name | Rows | Coverage | Battery Relevant? |
|---------|-----------|------|----------|-------------------|
| BOD | `bmrs_bod` | 391M | 2022-present | ✅ YES - Core data |
| BOALF | `bmrs_boalf` | 11.3M | Historical | ✅ YES - Acceptances |
| BOALF (unified) | `bmrs_boalf_unified` | Combined | All time | ✅ YES |
| BOALF (IRIS) | `bmrs_boalf_iris` | 1,352 | Real-time | ✅ YES - Live |
| BOD (IRIS) | `bmrs_bod_iris` | 903K | Real-time | ✅ YES - Live |
| MELS | `bmrs_mels_iris` | Live | Real-time | ✅ YES - Limits |
| MILS | `bmrs_mils_iris` | Live | Real-time | ✅ YES - Limits |
| FUELINST | `bmrs_fuelinst` | 5.7M | Historical | ⚠️ Aggregate only |
| MID | `bmrs_mid` | 155K | 2022-present | ⚠️ System prices |
| INDO | `bmrs_indo_iris` | 375 | Real-time | ❌ Demand data |
| INDGEN | `bmrs_indgen_iris` | 284K | Real-time | ❌ Regional gen |

### **❌ What You Don't Have (Yet)**:

| Dataset | Purpose | Why You'd Want It |
|---------|---------|-------------------|
| PN | Physical Notifications | Planned battery schedules |
| B1610 | Actual Generation | Real measured output |
| SEL/SIL | Export/Import Limits | Technical constraints |
| REMIT | Asset Registry | VLP identification |
| TUDM | Trading Units | Party relationships |
| Run Rates | Ramping Speeds | Battery flexibility |

---

## 🚀 Recommended Implementation

### **Phase 1: Identify All Batteries in Your Data**

**Step 1: Query your generator data**
```python
# You already have All_Generators.xlsx with this data
generators_df = pd.read_excel('All_Generators.xlsx')

# Filter for batteries
batteries = generators_df[
    generators_df['Fuel Type (Categorised)'].str.contains('Stored Energy', na=False) |
    generators_df['Fuel Type (Categorised)'].str.contains('Storage', na=False)
]

# Extract BMU IDs if available
battery_bmus = batteries['BMU_ID'].dropna().unique()
```

**Step 2: Cross-reference with BOD data**
```sql
-- Find all BMU IDs with battery-like characteristics
SELECT DISTINCT
  bmUnitId,
  COUNT(*) as total_periods,
  AVG(CASE WHEN bidVolume > 0 THEN bidVolume ELSE NULL END) as avg_bid_mw,
  AVG(CASE WHEN offerVolume > 0 THEN offerVolume ELSE NULL END) as avg_offer_mw,
  MIN(settlementDate) as first_seen,
  MAX(settlementDate) as last_seen
FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_bod`
WHERE bmUnitId LIKE '%BESS%' 
   OR bmUnitId LIKE '%STOR%'
   OR bmUnitId LIKE '%BTRY%'
   OR bmUnitId LIKE '%ENSO%'  -- Common battery provider
GROUP BY bmUnitId
ORDER BY total_periods DESC
```

---

### **Phase 2: Battery Arbitrage Analysis**

**You already have this partially in `battery_arbitrage.py`!**

**Enhanced Query**:
```sql
WITH battery_bids AS (
  SELECT 
    b.bmUnitId,
    b.settlementDate,
    b.settlementPeriod,
    b.bidPrice as discharge_price,    -- Price to discharge (reduce)
    b.offerPrice as charge_price,     -- Price to charge (increase)
    b.bidVolume as discharge_capacity,
    b.offerVolume as charge_capacity,
    m.systemSellPrice as ssp,
    m.systemBuyPrice as sbp
  FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_bod` b
  INNER JOIN `inner-cinema-476211-u9.uk_energy_prod.bmrs_mid` m
    ON b.settlementDate = m.settlementDate
    AND b.settlementPeriod = m.settlementPeriod
  WHERE b.bmUnitId IN (
    -- List of known battery BMU IDs
    'YOUR_BATTERY_BMU_IDS_HERE'
  )
    AND b.settlementDate >= '2024-01-01'
),

battery_opportunities AS (
  SELECT 
    *,
    -- Calculate arbitrage opportunity
    (ssp - charge_price) as charge_margin,      -- Profit to charge
    (discharge_price - sbp) as discharge_margin, -- Profit to discharge
    CASE 
      WHEN (ssp - charge_price) > 0 THEN discharge_capacity * (ssp - charge_price)
      ELSE 0 
    END as potential_charge_profit,
    CASE 
      WHEN (discharge_price - sbp) > 0 THEN discharge_capacity * (discharge_price - sbp)
      ELSE 0
    END as potential_discharge_profit
  FROM battery_bids
)

SELECT 
  bmUnitId,
  settlementDate,
  COUNT(*) as total_periods,
  SUM(potential_charge_profit) as daily_charge_profit,
  SUM(potential_discharge_profit) as daily_discharge_profit,
  SUM(potential_charge_profit + potential_discharge_profit) as total_daily_profit,
  AVG(charge_margin) as avg_charge_margin,
  AVG(discharge_margin) as avg_discharge_margin
FROM battery_opportunities
GROUP BY bmUnitId, settlementDate
ORDER BY total_daily_profit DESC
```

---

### **Phase 3: Add Missing Datasets**

**Script to backfill key battery datasets**:

```python
#!/usr/bin/env python3
"""
Backfill battery-relevant ELEXON datasets
"""
import requests
from datetime import datetime, timedelta
from google.cloud import bigquery

BMRS_API = 'https://data.elexon.co.uk/bmrs/api/v1'
PROJECT = 'inner-cinema-476211-u9'
DATASET = 'uk_energy_prod'

BATTERY_DATASETS = {
    'PN': '/datasets/PN',           # Physical Notifications
    'B1610': '/datasets/B1610',     # Actual Generation
    'SEL': '/datasets/SEL',         # Stable Export Limit
    'SIL': '/datasets/SIL',         # Stable Import Limit
    'REMIT': '/datasets/REMIT',     # Asset Registry
    'RURE': '/datasets/RURE',       # Run-up rate export
    'RURI': '/datasets/RURI',       # Run-up rate import
}

def download_dataset(dataset_name, endpoint, from_date, to_date):
    """Download dataset from ELEXON API"""
    url = f"{BMRS_API}{endpoint}"
    
    params = {
        'settlementDateFrom': from_date.strftime('%Y-%m-%d'),
        'settlementDateTo': to_date.strftime('%Y-%m-%d'),
        'format': 'json'
    }
    
    response = requests.get(url, params=params, timeout=300)
    response.raise_for_status()
    
    return response.json()

def load_to_bigquery(data, table_name):
    """Load data to BigQuery"""
    client = bigquery.Client(project=PROJECT)
    table_id = f"{PROJECT}.{DATASET}.bmrs_{table_name.lower()}"
    
    # Auto-detect schema and load
    job_config = bigquery.LoadJobConfig(
        autodetect=True,
        write_disposition='WRITE_APPEND'
    )
    
    job = client.load_table_from_json(
        data['data'] if 'data' in data else data,
        table_id,
        job_config=job_config
    )
    
    job.result()  # Wait for completion
    print(f"✅ Loaded {len(data.get('data', []))} rows to {table_id}")

# Main execution
if __name__ == '__main__':
    from_date = datetime.now() - timedelta(days=7)
    to_date = datetime.now()
    
    for dataset_name, endpoint in BATTERY_DATASETS.items():
        print(f"📥 Downloading {dataset_name}...")
        try:
            data = download_dataset(dataset_name, endpoint, from_date, to_date)
            load_to_bigquery(data, dataset_name)
        except Exception as e:
            print(f"❌ Error with {dataset_name}: {e}")
```

---

### **Phase 4: VLP Identification**

**Step 1: Download REMIT data**
```bash
curl "https://data.elexon.co.uk/bmrs/api/v1/datasets/REMIT?format=json" > remit_data.json
```

**Step 2: Load to BigQuery**
```bash
bq load \
  --source_format=NEWLINE_DELIMITED_JSON \
  --autodetect \
  inner-cinema-476211-u9:uk_energy_prod.bmrs_remit \
  remit_data.json
```

**Step 3: Query for VLPs**
```sql
-- Find virtual/aggregated assets
SELECT 
  mRID,
  assetId,
  assetName,
  assetType,
  participantMarketRole,
  fuelType,
  installedCapacity,
  unavailableCapacity
FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_remit`
WHERE LOWER(assetName) LIKE '%virtual%'
   OR LOWER(assetName) LIKE '%aggregat%'
   OR LOWER(assetName) LIKE '%portfolio%'
   OR LOWER(assetName) LIKE '%vlp%'
   OR assetType = 'Production aggregated by control area'
ORDER BY installedCapacity DESC
```

**Step 4: Cross-reference with BOD**
```sql
-- Find which VLP assets participate in balancing market
SELECT 
  r.assetName as vlp_name,
  r.participantMarketRole as lead_party,
  r.installedCapacity as total_mw,
  COUNT(DISTINCT b.bmUnitId) as num_bmus,
  COUNT(DISTINCT b.settlementDate) as active_days,
  SUM(b.bidVolume) as total_bid_volume,
  SUM(b.offerVolume) as total_offer_volume
FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_remit` r
LEFT JOIN `inner-cinema-476211-u9.uk_energy_prod.bmrs_bod` b
  ON r.assetId = b.bmUnitId
WHERE LOWER(r.assetName) LIKE '%virtual%'
  AND b.settlementDate >= '2024-01-01'
GROUP BY r.assetName, r.participantMarketRole, r.installedCapacity
ORDER BY total_mw DESC
```

---

## 📈 Analytics Use Cases

### **1. Battery Market Participation Analysis**
```sql
-- How many batteries are active in balancing market?
SELECT 
  DATE_TRUNC(settlementDate, MONTH) as month,
  COUNT(DISTINCT bmUnitId) as unique_batteries,
  COUNT(*) as total_bids,
  SUM(bidVolume + offerVolume) as total_capacity_offered_mw,
  AVG(bidPrice) as avg_bid_price,
  AVG(offerPrice) as avg_offer_price
FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_bod`
WHERE bmUnitId LIKE '%BESS%' OR bmUnitId LIKE '%STOR%'
  AND settlementDate >= '2024-01-01'
GROUP BY month
ORDER BY month
```

### **2. VLP vs Individual Battery Performance**
```sql
WITH battery_types AS (
  SELECT 
    bmUnitId,
    CASE 
      WHEN bmUnitId IN (SELECT assetId FROM `bmrs_remit` WHERE LOWER(assetName) LIKE '%virtual%')
      THEN 'VLP'
      ELSE 'Individual'
    END as battery_type
  FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_bod`
  WHERE bmUnitId LIKE '%BESS%'
)

SELECT 
  bt.battery_type,
  COUNT(DISTINCT b.bmUnitId) as num_units,
  AVG(b.bidPrice) as avg_bid_price,
  AVG(b.offerPrice) as avg_offer_price,
  SUM(b.bidVolume) as total_bid_volume,
  SUM(b.offerVolume) as total_offer_volume
FROM battery_types bt
JOIN `inner-cinema-476211-u9.uk_energy_prod.bmrs_bod` b
  ON bt.bmUnitId = b.bmUnitId
WHERE b.settlementDate >= '2024-01-01'
GROUP BY bt.battery_type
```

### **3. Battery Dispatch Patterns**
```sql
-- When are batteries most frequently dispatched?
SELECT 
  settlementPeriod as half_hour_period,
  EXTRACT(HOUR FROM TIMESTAMP_ADD(TIMESTAMP('2024-01-01'), 
    INTERVAL (settlementPeriod - 1) * 30 MINUTE)) as hour_of_day,
  COUNT(*) as num_acceptances,
  SUM(levelTo - levelFrom) as total_dispatch_mw,
  AVG(levelTo - levelFrom) as avg_dispatch_mw
FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_boalf`
WHERE bmUnitId LIKE '%BESS%'
  AND DATE(acceptanceTime) >= '2024-01-01'
GROUP BY settlementPeriod, hour_of_day
ORDER BY settlementPeriod
```

### **4. Battery Revenue Estimation**
```sql
WITH battery_acceptances AS (
  SELECT 
    b.bmUnitId,
    b.acceptanceTime,
    b.settlementPeriod,
    (b.levelTo - b.levelFrom) as dispatch_mw,
    m.systemSellPrice,
    m.systemBuyPrice,
    CASE 
      WHEN (b.levelTo - b.levelFrom) > 0 THEN 'DISCHARGE'
      WHEN (b.levelTo - b.levelFrom) < 0 THEN 'CHARGE'
      ELSE 'NO_CHANGE'
    END as action,
    CASE 
      WHEN (b.levelTo - b.levelFrom) > 0 
      THEN (b.levelTo - b.levelFrom) * m.systemSellPrice * 0.5  -- 0.5 hours
      WHEN (b.levelTo - b.levelFrom) < 0 
      THEN ABS(b.levelTo - b.levelFrom) * m.systemBuyPrice * 0.5
      ELSE 0
    END as revenue_gbp
  FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_boalf` b
  JOIN `inner-cinema-476211-u9.uk_energy_prod.bmrs_mid` m
    ON DATE(b.acceptanceTime) = m.settlementDate
    AND b.settlementPeriod = m.settlementPeriod
  WHERE b.bmUnitId LIKE '%BESS%'
    AND DATE(b.acceptanceTime) >= '2024-01-01'
)

SELECT 
  bmUnitId,
  DATE_TRUNC(acceptanceTime, MONTH) as month,
  COUNT(*) as num_dispatches,
  SUM(CASE WHEN action = 'DISCHARGE' THEN 1 ELSE 0 END) as num_discharges,
  SUM(CASE WHEN action = 'CHARGE' THEN 1 ELSE 0 END) as num_charges,
  SUM(ABS(dispatch_mw)) as total_mwh_traded,
  SUM(revenue_gbp) as total_revenue_gbp,
  AVG(revenue_gbp) as avg_revenue_per_dispatch
FROM battery_acceptances
GROUP BY bmUnitId, month
ORDER BY total_revenue_gbp DESC
```

---

## 🔗 API Reference Links

### **ELEXON BMRS API Documentation**:
- **Main**: https://bmrs.elexon.co.uk/api-documentation
- **BOD**: https://bmrs.elexon.co.uk/api-documentation/endpoint/datasets/BOD
- **BOALF**: https://bmrs.elexon.co.uk/api-documentation/endpoint/datasets/BOALF
- **PN**: https://bmrs.elexon.co.uk/api-documentation/endpoint/datasets/PN
- **B1610**: https://bmrs.elexon.co.uk/api-documentation/endpoint/datasets/B1610
- **REMIT**: https://bmrs.elexon.co.uk/api-documentation/endpoint/remit
- **Reference Data**: https://bmrs.elexon.co.uk/api-documentation/endpoint/reference/bmunits/all

### **NESO Data Portal**:
- **Main**: https://www.neso.energy/data-portal
- **API Guidance**: https://www.neso.energy/data-portal/api-guidance
- **Generator Register**: https://www.neso.energy/data-portal/gis-boundaries-gb-dno-license-areas

---

## 💡 Quick Wins

### **1. Immediate Analysis (5 minutes)**
```sql
-- Count unique battery BMUs in your data
SELECT COUNT(DISTINCT bmUnitId) as num_batteries
FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_bod`
WHERE bmUnitId LIKE '%BESS%' 
   OR bmUnitId LIKE '%STOR%'
   OR bmUnitId LIKE '%BTRY%'
```

### **2. Latest Battery Activity (5 minutes)**
```sql
-- See most recent battery bids/offers
SELECT 
  bmUnitId,
  settlementDate,
  settlementPeriod,
  bidPrice,
  offerPrice,
  bidVolume,
  offerVolume
FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_bod`
WHERE (bmUnitId LIKE '%BESS%' OR bmUnitId LIKE '%STOR%')
  AND settlementDate >= DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY)
ORDER BY settlementDate DESC, settlementPeriod DESC
LIMIT 100
```

### **3. Top Battery Participants (10 minutes)**
```sql
-- Find most active battery BMUs
SELECT 
  bmUnitId,
  COUNT(*) as num_periods,
  MIN(settlementDate) as first_active,
  MAX(settlementDate) as last_active,
  AVG(bidVolume) as avg_bid_capacity,
  AVG(offerVolume) as avg_offer_capacity
FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_bod`
WHERE (bmUnitId LIKE '%BESS%' OR bmUnitId LIKE '%STOR%')
  AND settlementDate >= '2024-01-01'
GROUP BY bmUnitId
ORDER BY num_periods DESC
LIMIT 50
```

---

## 📦 Ready-to-Use Python Script

Save this as `analyze_batteries.py`:

```python
#!/usr/bin/env python3
"""
Battery & VLP Analysis Script
Analyzes battery participation in GB balancing market
"""
from google.cloud import bigquery
import pandas as pd
from datetime import datetime, timedelta

PROJECT = 'inner-cinema-476211-u9'
DATASET = 'uk_energy_prod'

def get_battery_bmus():
    """Get list of all battery BMU IDs"""
    client = bigquery.Client(project=PROJECT)
    
    query = f"""
    SELECT DISTINCT bmUnitId
    FROM `{PROJECT}.{DATASET}.bmrs_bod`
    WHERE bmUnitId LIKE '%BESS%' 
       OR bmUnitId LIKE '%STOR%'
       OR bmUnitId LIKE '%BTRY%'
       OR bmUnitId LIKE '%ENSO%'
    ORDER BY bmUnitId
    """
    
    return client.query(query).to_dataframe()

def analyze_battery_activity(bmu_id=None, days=30):
    """Analyze battery bidding activity"""
    client = bigquery.Client(project=PROJECT)
    
    where_clause = f"AND bmUnitId = '{bmu_id}'" if bmu_id else ""
    
    query = f"""
    SELECT 
      bmUnitId,
      settlementDate,
      settlementPeriod,
      bidPrice,
      offerPrice,
      bidVolume,
      offerVolume,
      (bidVolume + offerVolume) as total_capacity
    FROM `{PROJECT}.{DATASET}.bmrs_bod`
    WHERE (bmUnitId LIKE '%BESS%' OR bmUnitId LIKE '%STOR%')
      {where_clause}
      AND settlementDate >= DATE_SUB(CURRENT_DATE(), INTERVAL {days} DAY)
    ORDER BY settlementDate DESC, settlementPeriod DESC
    """
    
    df = client.query(query).to_dataframe()
    
    print(f"\n📊 Battery Activity Summary ({days} days)")
    print(f"{'='*60}")
    print(f"Total records: {len(df):,}")
    print(f"Unique BMUs: {df['bmUnitId'].nunique()}")
    print(f"\nAverage Prices:")
    print(f"  Bid Price: £{df['bidPrice'].mean():.2f}/MWh")
    print(f"  Offer Price: £{df['offerPrice'].mean():.2f}/MWh")
    print(f"\nAverage Volumes:")
    print(f"  Bid Volume: {df['bidVolume'].mean():.2f} MW")
    print(f"  Offer Volume: {df['offerVolume'].mean():.2f} MW")
    
    return df

def find_vlps():
    """Identify potential VLP units"""
    client = bigquery.Client(project=PROJECT)
    
    # Check if REMIT table exists
    tables = [table.table_id for table in client.list_tables(DATASET)]
    
    if 'bmrs_remit' in tables:
        query = f"""
        SELECT 
          assetId,
          assetName,
          participantMarketRole,
          fuelType,
          installedCapacity
        FROM `{PROJECT}.{DATASET}.bmrs_remit`
        WHERE LOWER(assetName) LIKE '%virtual%'
           OR LOWER(assetName) LIKE '%aggregat%'
           OR LOWER(assetName) LIKE '%portfolio%'
        ORDER BY installedCapacity DESC
        """
        
        df = client.query(query).to_dataframe()
        print(f"\n🏢 Virtual Lead Parties Found: {len(df)}")
        print(df.to_string())
        return df
    else:
        print("\n⚠️ REMIT table not found. Run backfill script to add VLP data.")
        return None

if __name__ == '__main__':
    print("🔋 GB Battery Market Analysis")
    print("="*60)
    
    # Get all battery BMUs
    bmus = get_battery_bmus()
    print(f"\n✅ Found {len(bmus)} battery BMUs")
    print("\nSample BMU IDs:")
    print(bmus.head(10).to_string(index=False))
    
    # Analyze activity
    activity = analyze_battery_activity(days=30)
    
    # Look for VLPs
    vlps = find_vlps()
    
    # Export results
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    activity.to_csv(f'battery_activity_{timestamp}.csv', index=False)
    print(f"\n💾 Exported: battery_activity_{timestamp}.csv")
```

---

## 🎯 Next Steps

### **Immediate (Today)**:
1. ✅ Run the quick win queries above to see what batteries are in your BOD data
2. ✅ Count distinct battery BMU IDs  
3. ✅ Analyze most recent 7 days of battery activity

### **This Week**:
1. 📥 Download missing datasets (PN, B1610, REMIT) using backfill script
2. 🔍 Cross-reference generator data with BMU IDs
3. 📊 Build battery dispatch dashboard in Google Sheets

### **This Month**:
1. 🏢 Identify all VLPs using REMIT data
2. 💰 Calculate battery revenue by BMU
3. 📈 Compare VLP vs individual battery performance
4. 🤖 Add battery-specific endpoints to your API Gateway

---

## ❓ FAQ

**Q: Do I need an API key for ELEXON data?**  
A: No, public BMRS data is free and requires no authentication.

**Q: How do I know if a BMU is a battery?**  
A: Check for keywords in BMU ID (BESS, STOR, BTRY) or cross-reference with your All_Generators.xlsx file where fuel type = "Stored Energy".

**Q: What's the difference between BOD and BOALF?**  
A: BOD = all bids/offers submitted. BOALF = what NESO actually accepted/dispatched.

**Q: Can I get real-time battery data?**  
A: Yes! You're already receiving `bmrs_bod_iris` and `bmrs_boalf_iris` via IRIS stream (< 5 min latency).

**Q: How do I identify VLPs without REMIT data?**  
A: Look for BMU IDs with "VIRTUAL", "AGGR", or "PORT" in the name, or units with unusually high/variable capacity.

**Q: What's a typical battery size in GB?**  
A: Commercial batteries range from 10-100 MW. Large installations like Minety (100 MW) and Capenhurst (50 MW) are common.

---

## 📚 Additional Resources

- **Your Workspace Documentation**: See `DATA_INVENTORY_COMPLETE.md` for full table list
- **Your Battery Script**: `battery_arbitrage.py` (already partially implemented)
- **BMRS Glossary**: https://www.elexon.co.uk/glossary
- **NESO Help**: opendata@neso.energy

---

**Created**: 2025-11-06  
**Your System**: 391M BOD rows, 11.3M BOALF rows, IRIS real-time stream active ✅

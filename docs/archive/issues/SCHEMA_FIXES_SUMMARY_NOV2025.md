# Schema Fixes Summary - November 2025

**Date:** November 11, 2025  
**Status:** ✅ All major schema issues identified and documented

---

## 🎯 The Problem We Keep Solving

Over the last 3 days (Nov 9-11, 2025), we've repeatedly discovered schema mismatches when writing BigQuery queries. This document consolidates ALL schema knowledge to prevent future confusion.

---

## ✅ VERIFIED SCHEMAS (Use These!)

### 1. **bmrs_mid_iris** - Market Index Data (Prices)

**CORRECT Schema:**
```sql
settlementDate    DATE       -- Settlement date
settlementPeriod  INT64      -- Period 1-48
price             FLOAT64    -- Market price (£/MWh) ⭐
volume            FLOAT64    -- Volume (MWh)
startTime         TIMESTAMP  -- Period start time
dataProvider      STRING     -- Data provider
sourceFileDateTime     TIMESTAMP
sourceFileSerialNumber STRING
dataset           STRING
source            STRING
ingested_utc      TIMESTAMP
```

**❌ WRONG Schema (Don't Use):**
```sql
systemSellPrice   ❌ Does NOT exist in bmrs_mid_iris
systemBuyPrice    ❌ Does NOT exist in bmrs_mid_iris
netImbalanceVolume ❌ Does NOT exist in bmrs_mid_iris
priceDerivationCode ❌ Does NOT exist in bmrs_mid_iris
```

**Where the confusion came from:**
- These columns exist in `bmrs_detsysprices` (different table!)
- BMRS API documentation sometimes mixes table schemas
- Earlier scripts assumed systemSellPrice/systemBuyPrice everywhere

**Fixed in:**
- `bigquery_to_sheets_updater.py` (Nov 11, 2025)
- `update_dashboard_summary()` function
- `update_live_bigquery_sheet()` function
- `update_live_raw_prices()` function
- `update_bess_vlp()` function

---

### 2. **bmrs_bod** - Bid-Offer Data

**CORRECT Schema:**
```sql
timeFrom          TIMESTAMP
timeTo            TIMESTAMP
settlementDate    DATE
settlementPeriod  INT64
bmUnitId          STRING     -- ⚠️ Called bmUnitId, NOT bmUnit!
pairId            INT64
levelFrom         FLOAT64
levelTo           FLOAT64
offer             FLOAT64    -- Offer price (£/MWh) ⭐
bid               FLOAT64    -- Bid price (£/MWh) ⭐
```

**❌ WRONG Schema (Don't Use):**
```sql
bmUnit                    ❌ It's called bmUnitId
acceptanceId              ❌ Does NOT exist (this is bid-offer, not acceptances)
acceptanceTime            ❌ Does NOT exist
bidOfferAcceptanceLevel   ❌ Does NOT exist
bidOfferAcceptancePrice   ❌ Does NOT exist
soFlag                    ❌ Does NOT exist
```

**Critical Understanding:**
- `bmrs_bod` = BID-OFFER data (submitted bids, NOT acceptances)
- For acceptances, use `bmrs_boalf` (different table!)
- Column is `bmUnitId` not `bmUnit` (the 'Id' suffix matters!)

**Fixed in:**
- `PROJECT_CONFIGURATION.md` - Schema reference section
- `STOP_DATA_ARCHITECTURE_REFERENCE.md` - Common mistakes

---

### 3. **bmrs_freq** - System Frequency

**CORRECT Schema:**
```sql
measurementTime   TIMESTAMP  -- ⚠️ NOT recordTime!
frequency         FLOAT64    -- Hz (typically 49.8-50.2)
```

**❌ WRONG Schema (Don't Use):**
```sql
recordTime        ❌ Column is called measurementTime
```

**Where the confusion came from:**
- Logical assumption (record time makes sense)
- Other tables use `publishTime`, `startTime`, etc.
- Need to check actual schema, not assume

**Fixed in:**
- `PROJECT_CONFIGURATION.md` (Oct 31, 2025)
- All frequency analysis scripts updated

---

### 4. **bmrs_fuelinst_iris** - Generation by Fuel Type

**CORRECT Schema:**
```sql
publishTime       TIMESTAMP
settlementDate    DATE
settlementPeriod  INT64
fuelType          STRING     -- WIND, CCGT, NUCLEAR, etc.
generation        FLOAT64    -- MW
sourceFileDateTime     TIMESTAMP
sourceFileSerialNumber STRING
dataset           STRING
dataProvider      STRING
source            STRING
ingested_utc      TIMESTAMP
```

**✅ No known issues with this table**

---

### 5. **bmrs_indo_iris** - Interconnector Flows

**CORRECT Schema:**
```sql
settlementDate    DATE
settlementPeriod  INT64
interconnectorId  STRING     -- IFA, IFA2, BRITNED, etc.
flow              FLOAT64    -- MW (positive = import, negative = export)
sourceFileDateTime     TIMESTAMP
sourceFileSerialNumber STRING
dataset           STRING
dataProvider      STRING
source            STRING
ingested_utc      TIMESTAMP
```

**✅ No known issues with this table**

---

## 🔧 Common Schema Patterns

### Pattern 1: IRIS Tables Have Metadata Columns

**ALL `*_iris` tables include:**
```sql
sourceFileDateTime     TIMESTAMP  -- When data was published
sourceFileSerialNumber STRING     -- File identifier
dataset                STRING     -- Dataset name
dataProvider           STRING     -- Data provider
source                 STRING     -- Source identifier
ingested_utc           TIMESTAMP  -- When we ingested it
```

### Pattern 2: Historical vs Real-Time Column Types

| Column | Historical Tables | IRIS Tables |
|--------|------------------|-------------|
| `settlementDate` | DATE | DATE |
| `settlementPeriod` | INT64 | INT64 |
| Timestamps | DATETIME | TIMESTAMP |

**⚠️ Exception:** `demand_outturn` uses STRING for dates (hybrid table)

### Pattern 3: Column Naming Conventions

| Concept | Column Name | Example Tables |
|---------|-------------|----------------|
| Time point | `measurementTime` | bmrs_freq |
| Publication | `publishTime` | bmrs_fuelinst |
| Start of period | `startTime` | bmrs_mid |
| Validity range | `timeFrom`, `timeTo` | bmrs_bod |

**⚠️ NOT consistent:** Need to check each table individually

---

## 📊 Table Relationships & Data Flow

### Price Data Hierarchy

```
1. bmrs_mid_iris
   ├── price (Market Index Price - simplest)
   └── volume
   
2. bmrs_detsysprices (more detailed)
   ├── systemSellPrice (SSP - when system is short)
   ├── systemBuyPrice (SBP - when system is long)
   ├── priceDerivationCode
   └── reserveScarcityPrice
   
3. bmrs_bod (bid-offer submissions)
   ├── offer (generator offer price)
   └── bid (generator bid price)
   
4. bmrs_boalf (accepted bids/offers)
   ├── acceptanceTime
   └── acceptancePrice
```

**Key Insight:**
- **bmrs_mid** = Market Index Price (what you see on dashboards)
- **bmrs_detsysprices** = System Buy/Sell Prices (imbalance pricing)
- **bmrs_bod** = Submitted bids (not necessarily accepted)
- **bmrs_boalf** = Accepted bids (actual dispatch)

**For most price analysis:** Use `bmrs_mid_iris.price`

---

## 🚨 Critical Fixes Applied (Nov 9-11, 2025)

### Fix 1: Dashboard Auto-Refresh (Nov 9)
**File:** `realtime_dashboard_updater.py`

**Problem:** Query used wrong column names
```python
# ❌ BEFORE
SELECT systemSellPrice, systemBuyPrice FROM bmrs_mid_iris
# Error: Unrecognized name: systemSellPrice

# ✅ AFTER  
SELECT price FROM bmrs_mid_iris
```

**Status:** ✅ Fixed, tested, deployed

---

### Fix 2: VLP Profit Analysis (Nov 9)
**File:** `VLP_PROFIT_ANALYSIS_CORRECTED.md`

**Problem:** Assumed all revenue = profit (forgot charging costs)

**Solution:**
- Net profit = Gross revenue - Charging costs - Efficiency losses
- Charging at £0/MWh (or negative) = free charging
- 90% round-trip efficiency (typical lithium-ion)
- Net margin: 75-90% depending on charging price

**Status:** ✅ Documented in VLP_PROFIT_ANALYSIS_CORRECTED.md

---

### Fix 3: BigQuery to Sheets Updater (Nov 11)
**File:** `bigquery_to_sheets_updater.py`

**Problems:**
1. Used `workspace-credentials.json` (doesn't have BigQuery access)
2. Used wrong columns: systemSellPrice, systemBuyPrice, netImbalanceVolume
3. Assumed columns that don't exist in bmrs_mid_iris

**Solutions:**
1. Split credentials:
   - `inner-cinema-credentials.json` → BigQuery
   - `workspace-credentials.json` → Sheets (via delegation)
2. Fixed all queries to use correct schema:
   - `bmrs_mid_iris.price` (not systemSellPrice)
   - `bmrs_mid_iris.volume` (not netImbalanceVolume)
3. Added CAST to STRING for date display in sheets

**Functions fixed:**
- `update_live_bigquery_sheet()`
- `update_live_raw_prices()`
- `update_bess_vlp()`
- `update_dashboard_summary()`

**Status:** ✅ Fixed (Nov 11, 2025)

---

### Fix 4: Schema Documentation (Nov 9-11)
**Files:**
- `PROJECT_CONFIGURATION.md` - Added correct schemas
- `STOP_DATA_ARCHITECTURE_REFERENCE.md` - Common mistakes
- `BIGQUERY_SCHEMA_FOR_VLP.md` - Detailed schema reference

**Status:** ✅ Complete documentation

---

## 📋 Pre-Query Checklist (Use EVERY Time)

Before writing ANY BigQuery query:

1. **Read this file** (`SCHEMA_FIXES_SUMMARY_NOV2025.md`)

2. **Check actual schema:**
   ```bash
   bq show --schema --format=prettyjson \
     inner-cinema-476211-u9:uk_energy_prod.TABLE_NAME
   ```

3. **Verify table exists and has data:**
   ```sql
   SELECT COUNT(*) as count,
          MIN(settlementDate) as min_date,
          MAX(settlementDate) as max_date
   FROM `inner-cinema-476211-u9.uk_energy_prod.TABLE_NAME`
   ```

4. **Use correct project and location:**
   ```python
   PROJECT_ID = "inner-cinema-476211-u9"  # ✅ NOT jibber-jabber-knowledge
   LOCATION = "US"  # ✅ NOT europe-west2
   ```

5. **Reference documentation:**
   - Schema details: `PROJECT_CONFIGURATION.md`
   - Table coverage: `STOP_DATA_ARCHITECTURE_REFERENCE.md`
   - VLP analysis: `BIGQUERY_SCHEMA_FOR_VLP.md`

---

## 🔍 How to Verify a Table Schema

### Method 1: Using bq command (fastest)
```bash
bq show --schema --format=prettyjson \
  inner-cinema-476211-u9:uk_energy_prod.bmrs_mid_iris \
  | jq '.[] | "\(.name): \(.type)"'
```

### Method 2: Using Python
```python
from google.cloud import bigquery
from google.oauth2 import service_account

creds = service_account.Credentials.from_service_account_file(
    'inner-cinema-credentials.json'
)
client = bigquery.Client(
    project='inner-cinema-476211-u9',
    credentials=creds
)

table = client.get_table('inner-cinema-476211-u9.uk_energy_prod.bmrs_mid_iris')
for field in table.schema:
    print(f"{field.name}: {field.field_type}")
```

### Method 3: Using BigQuery Console
1. Open https://console.cloud.google.com/bigquery
2. Navigate to `inner-cinema-476211-u9` → `uk_energy_prod`
3. Click table name → "Schema" tab

---

## 📚 Related Documentation

**Must Read Before Querying:**
1. **This file** (`SCHEMA_FIXES_SUMMARY_NOV2025.md`) - Schema reference
2. `STOP_DATA_ARCHITECTURE_REFERENCE.md` - Architecture overview
3. `PROJECT_CONFIGURATION.md` - Project settings

**Supplementary:**
4. `BIGQUERY_SCHEMA_FOR_VLP.md` - VLP-specific schema details
5. `VLP_PROFIT_ANALYSIS_CORRECTED.md` - Business logic examples
6. `UNIFIED_ARCHITECTURE_HISTORICAL_AND_REALTIME.md` - Data pipeline

**For specific use cases:**
7. `TWO_DELEGATION_SYSTEMS_EXPLAINED.md` - Credentials/delegation
8. `DASHBOARD_AUTO_REFRESH_SOLUTION_SUMMARY.md` - Auto-refresh setup
9. `BIGQUERY_SHEETS_AUTOMATION.md` - Sheets integration

---

## 🎯 Key Takeaways

### 1. Don't Assume Column Names
**❌ Assumption:** "System prices should be called systemSellPrice"  
**✅ Reality:** In `bmrs_mid_iris`, it's just called `price`

### 2. Check Documentation First
**Before:** Write query → Error → Debug → Check schema → Rewrite  
**After:** Check schema → Write correct query → Success ✅

### 3. Different Tables, Different Purposes
- `bmrs_mid` = Market prices (for dashboards)
- `bmrs_detsysprices` = System Buy/Sell prices (for imbalance analysis)
- `bmrs_bod` = Bid-offer submissions (for market structure)
- `bmrs_boalf` = Accepted bids (for actual dispatch)

### 4. Two Credential Files
- `inner-cinema-credentials.json` → BigQuery queries ✅
- `workspace-credentials.json` → Google Sheets updates ✅
- Do NOT confuse them!

### 5. Always Test First
```sql
-- Add LIMIT when testing
SELECT * FROM table_name LIMIT 10
```

---

## 🔄 Version History

| Date | Change | Fixed By |
|------|--------|----------|
| 2025-10-31 | Fixed bmrs_bod schema (bmUnitId not bmUnit) | GitHub Copilot |
| 2025-10-31 | Fixed bmrs_freq schema (measurementTime not recordTime) | GitHub Copilot |
| 2025-11-09 | Documented VLP profit calculation (charging costs matter) | Analysis |
| 2025-11-09 | Fixed bmrs_mid_iris schema (price not systemSellPrice) | GitHub Copilot |
| 2025-11-11 | Fixed bigquery_to_sheets_updater.py (all queries) | GitHub Copilot |
| 2025-11-11 | Created this comprehensive schema reference | GitHub Copilot |

---

**Status:** ✅ All known schema issues documented  
**Last Updated:** November 11, 2025  
**Maintainer:** George Major (george@upowerenergy.uk)

---

## 🚀 Next Steps

When you encounter a schema error:

1. **Don't debug blindly** - Check this file first
2. **Verify actual schema** - Use `bq show --schema`
3. **Update this document** - Add new findings
4. **Test query** - Use LIMIT 10 first
5. **Document fix** - Add to version history

**Remember:** Schema knowledge is hard-won. Document it so we don't lose it!

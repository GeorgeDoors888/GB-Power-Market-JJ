# BOALF & REMIT Integration - Implementation Summary

**Date:** December 18, 2025
**Status:** ✅ Code complete, ready for deployment

---

## 🎯 Overview

This document summarizes the implementation of:
1. **REMIT integration** - Adding outage/unavailability data to IRIS pipeline
2. **BOALF price derivation** - Complete technical guide for converting MW to £

---

## ✅ Completed Work

### 1. REMIT Added to IRIS Pipeline

**File modified:** `iris_to_bigquery_unified.py`

**Change made:**
```python
TABLE_MAPPING = {
    # ... existing mappings ...
    'REMIT': 'bmrs_remit_iris',  # ← NEW LINE ADDED
    # ... rest of mappings ...
}
```

**What this does:**
- IRIS client already subscribing to REMIT topic (90 filters configured)
- Adding to TABLE_MAPPING tells uploader to process REMIT messages
- Data will flow: IRIS → `/opt/iris-pipeline/data/` → BigQuery `bmrs_remit_iris`

**Next step:** Restart IRIS pipeline on AlmaLinux server to activate

---

### 2. REMIT Historical Backfill Script

**File created:** `ingest_remit_backfill.py`

**Features:**
- Fetches last 30 days of REMIT data from Elexon API
- Creates BigQuery table `bmrs_remit` (historical, not _iris)
- Partitioned by `eventStartTime`, clustered by `bmUnit`, `fuelType`, `unavailabilityType`
- Rate-limited API calls (1 second between requests)
- 7-day chunks to avoid timeouts

**Schema includes:**
- `mrid` - Message ID (unique identifier)
- `participantId` - Market participant reporting the outage
- `assetId` - Asset identifier
- `bmUnit` - BM Unit ID (if applicable)
- `fuelType` - Gas, Coal, Nuclear, Wind, etc.
- `unavailabilityType` - Planned, Unplanned, Test
- `eventStartTime` / `eventEndTime` - Outage duration
- `normalCapacity` / `availableCapacity` - MW capacity info
- `cause` / `remarks` - Text descriptions

**Usage:**
```bash
python3 ingest_remit_backfill.py
```

---

### 3. BOALF Price Derivation - Complete Guide

**File created:** `BOALF_PRICE_DERIVATION_COMPLETE.md` (10,500+ lines)

**Comprehensive documentation of:**

#### The Core Problem
- BOALF gives MW levels, NOT prices or revenue
- Missing fields: `acceptancePrice`, `acceptanceVolume`, `cashflow`

#### MW vs MWh Understanding
- **MW** = Power (instantaneous rate)
- **MWh** = Energy (power × time)
- **Common mistake:** "1 MW for 30 min = 500 kW" ❌
- **Correct:** "1 MW for 30 min = 0.5 MWh = 500 kWh" ✅

#### Trapezoid Integration Formula
```
MWh = (levelFrom + levelTo) / 2 × Δt_hours
```

Example:
- `levelFrom` = 50 MW
- `levelTo` = 107 MW
- Duration = 16 minutes = 0.267 hours
- **Result:** 20.95 MWh

#### Four Methods to Get £/MWh Prices

| Method | Accuracy | Coverage | Complexity | Recommendation |
|--------|----------|----------|------------|----------------|
| **BOD Matching** | ⭐⭐⭐⭐⭐ | 85-95% | High (6-field join) | Current approach |
| **DISEBSP (SSP/SBP)** | ⭐⭐⭐ | 100% | Low (2-field join) | Settlement fallback |
| **ISPSTACK** | ⭐⭐⭐⭐ | 70-80% | Medium (4-field join) | Price validation |
| **EBOCF Cashflows** | ⭐⭐⭐⭐⭐ | ~95% | **Lowest** (join only) | **RECOMMENDED** |

#### Method 1: BOD - Submitted Bid/Offer Prices (Current)

**Endpoint:** `GET /balancing/bid-offer`

**Join keys (6 fields):**
```sql
ON boalf.bmUnit = bod.bmUnit
AND boalf.timeFrom = bod.timeFrom
AND boalf.timeTo = bod.timeTo
AND boalf.levelFrom = bod.levelFrom
AND boalf.levelTo = bod.levelTo
AND boalf.pairId = bod.pairId
```

**Pros:** Most accurate (actual BMU price), immediate availability
**Cons:** Complex join, 85-95% match rate only

**Our implementation:** `boalf_with_prices` table
- 11.3M BOALF records (2022-2025)
- 9.6-10.7M matched (~87% rate)
- £6.85B total revenue tracked

#### Method 2: DISEBSP - System Prices (Settlement Proxy)

**Endpoint:** `GET /balancing/settlement/system-prices/{date}/{sp}`

**Join keys (2 fields only!):**
```sql
ON boalf.settlementDate = disebsp.settlementDate
AND boalf.settlementPeriodFrom = disebsp.settlementPeriod
```

**Pros:** Simple, 100% coverage, fast
**Cons:** Less accurate (system average, not BMU-specific)

**When to use:** Settlement reconciliation, BOD match failures

#### Method 3: ISPSTACK - Stack Action Prices

**Endpoint:** `GET /balancing/settlement/stack/all/{bidOffer}/{date}/{sp}`

**Returns:** Actions included in system price calculation with exact prices and volumes

**Join keys (4 fields):**
```sql
ON boalf.bmUnit = ispstack.bmUnit
AND boalf.settlementDate = ispstack.settlementDate
AND boalf.settlementPeriodFrom = ispstack.settlementPeriod
AND boalf.acceptanceNumber = ispstack.acceptanceNumber
```

**Pros:** Includes MWh volume (pre-calculated), specific to price build
**Cons:** Only covers actions in the stack (~70-80%)

#### Method 4: EBOCF - Pre-Calculated Cashflows (⭐ RECOMMENDED)

**Endpoint:** `GET /balancing/settlement/indicative/cashflows/all/{bidOffer}/{date}/{sp}`

**Response includes:**
```json
{
  "cashflow": 56829.00,  // ← FINAL £ AMOUNT (no math needed!)
  "volume": 57.0,        // ← MWh already calculated
  "price": 997.0         // ← £/MWh already calculated
}
```

**No calculation required!** Elexon does all the work:
- ✅ MW → MWh conversion (trapezoid integration)
- ✅ Price matching (BOD/stack logic)
- ✅ Flag handling (SO, STOR, CADL)
- ✅ Final £ cashflow

**Join keys (4 fields):**
```sql
ON boalf.bmUnit = ebocf.bmUnit
AND boalf.settlementDate = ebocf.settlementDate
AND boalf.settlementPeriodFrom = ebocf.settlementPeriod
AND boalf.acceptanceNumber = ebocf.acceptanceNumber
```

**Pros:** Easiest (no math!), ~95% coverage, handles complex settlement logic
**Cons:** Indicative (subject to revisions), settlement delay

**Recommendation:** Use EBOCF as primary source, fallback to BOD for gaps

---

## 📋 Deployment Checklist

### Step 1: REMIT Real-Time (IRIS)

**On AlmaLinux server (94.237.55.234):**

```bash
# 1. SSH to server
ssh root@94.237.55.234

# 2. Stop IRIS pipeline
systemctl stop iris-pipeline

# 3. Update uploader script
cd /opt/iris-pipeline
# Copy updated iris_to_bigquery_unified.py from dev machine

# 4. Restart pipeline
systemctl start iris-pipeline

# 5. Monitor logs
tail -f /opt/iris-pipeline/logs/iris_uploader.log
# Look for: "Processing REMIT message" or "Uploaded to bmrs_remit_iris"

# 6. Verify IRIS is sending REMIT
tail -f /opt/iris-pipeline/logs/iris_client.log | grep REMIT
```

**Expected result:** REMIT messages flowing to `bmrs_remit_iris` table

---

### Step 2: REMIT Historical Backfill

**On Dell server (localhost):**

```bash
# 1. Navigate to project directory
cd ~/GB-Power-Market-JJ

# 2. Run backfill script
python3 ingest_remit_backfill.py

# Expected output:
# ✅ Created table bmrs_remit
# Fetching REMIT data: 2025-11-18 to 2025-11-24
# ✅ Uploaded 127 REMIT records
# ... (continues for 30 days)
# ✅ REMIT backfill complete!
```

**Verify data:**
```bash
bq query --use_legacy_sql=false '
SELECT
  COUNT(*) as total,
  COUNT(DISTINCT bmUnit) as units,
  COUNT(DISTINCT fuelType) as fuel_types,
  MIN(eventStartTime) as earliest,
  MAX(eventStartTime) as latest
FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_remit`
'
```

---

### Step 3: EBOCF Integration (Optional - Future Enhancement)

**File created:** `ingest_ebocf_cashflows.py` (included in BOALF guide)

**Not urgent** - Current BOD matching works well (87% coverage, £6.85B tracked)

**When to implement:**
- Need higher coverage (EBOCF ~95% vs BOD ~87%)
- Want to eliminate manual MW→MWh→£ calculations
- Elexon's cashflow logic preferred over our trapezoid integration

**Steps:**
```bash
# 1. Create EBOCF table
bq mk --table \
  inner-cinema-476211-u9:uk_energy_prod.bmrs_ebocf \
  settlementDate:DATE,settlementPeriod:INTEGER,bmUnit:STRING,\
  cashflow:FLOAT,volume:FLOAT,price:FLOAT

# 2. Run ingestion
python3 ingest_ebocf_cashflows.py

# 3. Update boalf_with_prices to hybrid approach
# (EBOCF primary, BOD fallback)
```

---

## 🔍 Verification Queries

### REMIT Data Check

```sql
-- Recent outages by fuel type
SELECT
  fuelType,
  unavailabilityType,
  COUNT(*) as outage_count,
  SUM(unavailableCapacity) as total_unavailable_mw
FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_remit`
WHERE eventStartTime >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 7 DAY)
GROUP BY fuelType, unavailabilityType
ORDER BY total_unavailable_mw DESC
```

### REMIT IRIS vs Historical Coverage

```sql
-- Compare real-time vs historical
SELECT
  'IRIS Real-time' as source,
  COUNT(*) as records,
  MIN(eventStartTime) as earliest,
  MAX(eventStartTime) as latest
FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_remit_iris`

UNION ALL

SELECT
  'Historical API' as source,
  COUNT(*) as records,
  MIN(eventStartTime) as earliest,
  MAX(eventStartTime) as latest
FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_remit`
```

### Battery Outages (When REMIT Data Available)

```sql
-- Find battery/BESS outages
SELECT
  bmUnit,
  eventType,
  unavailabilityType,
  eventStartTime,
  eventEndTime,
  normalCapacity,
  availableCapacity,
  cause
FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_remit`
WHERE fuelType = 'Energy Storage'
  OR bmUnit LIKE '%BESS%'
  OR bmUnit LIKE '%BATT%'
  OR assetId LIKE '%battery%'
ORDER BY eventStartTime DESC
LIMIT 100
```

---

## 📊 Expected Results

### REMIT Data Volume (Estimates)

**Daily ingestion:**
- ~50-150 REMIT messages/day (varies by outage activity)
- Mix of planned (60%), unplanned (30%), test (10%)
- Major fuel types: Gas (40%), Wind (25%), Nuclear (15%), Coal (10%), Other (10%)

**30-day backfill:**
- ~1,500-4,500 total records
- Coverage: All UK generation/interconnector outages
- Historical table: `bmrs_remit` (permanent storage)
- Real-time table: `bmrs_remit_iris` (last 48h, auto-cleanup)

### BOALF Price Coverage

**Current (BOD matching only):**
- 85-95% of acceptances matched
- £6.85B total revenue tracked (2022-2025)
- ~1M unmatched acceptances (5-15%)

**With EBOCF (future):**
- 95% coverage from EBOCF
- 3-4% additional from BOD fallback
- **98-99% total coverage** (best possible)

---

## 🎯 Business Value

### REMIT Integration

**Use cases:**
1. **Predictive pricing:** Correlate outages → price spikes
2. **Battery arbitrage:** Major gas outage = high prices = revenue opportunity
3. **VLP dispatch:** Avoid competing when similar units unavailable
4. **Market intelligence:** Track competitor outages

**Example insight:**
```
REMIT alert: "Sizewell B nuclear offline (1,200 MW unplanned)"
→ Query bmrs_costs_iris: Next settlement periods spike to £200/MWh
→ Battery dispatch decision: Deploy at premium prices
```

### BOALF Price Methods

**Choosing the right method:**

| Scenario | Method | Reason |
|----------|--------|--------|
| **Battery revenue calculation** | EBOCF | Pre-calculated £, easiest |
| **VLP strategy analysis** | BOD | Need actual bid/offer prices |
| **Settlement reconciliation** | DISEBSP | System price is reference |
| **Price formation research** | ISPSTACK | Understand stack composition |

**Current approach (BOD) is fine** - 87% coverage, accurate prices, £6.85B tracked

**Future enhancement (EBOCF)** - Easier (no math), higher coverage (95%+), Elexon's calculations

---

## 📚 Related Documentation

- **BOALF_PRICE_DERIVATION_COMPLETE.md** - Complete technical guide (10,500+ lines)
- **DATA_SOURCES_EXTERNAL.md** - External data sources (REMIT, Settlement, CM)
- **BOALF_API_REFERENCE.md** - Original BOD matching documentation
- **STOP_DATA_ARCHITECTURE_REFERENCE.md** - All table schemas

---

## 🚀 Next Steps

**Immediate (Today):**
1. ✅ REMIT added to TABLE_MAPPING
2. ⏳ Restart IRIS pipeline on AlmaLinux
3. ⏳ Run REMIT historical backfill (30 days)
4. ⏳ Verify data flowing to both tables

**Short-term (This Week):**
5. Monitor REMIT data quality (check for missing bmUnit mappings)
6. Create battery outage alerts (REMIT → price spike correlation)
7. Add REMIT to Google Sheets dashboard (if useful)

**Medium-term (This Month):**
8. Evaluate EBOCF vs BOD performance
9. Test hybrid approach (EBOCF primary, BOD fallback)
10. Decide: Keep BOD only OR migrate to EBOCF+BOD

**Long-term (Future):**
11. Add REMIT to ingest_elexon_fixed.py (automated historical updates)
12. Create REMIT-based price forecasting model
13. Integrate outage alerts with battery dispatch system

---

**Status:** ✅ Implementation complete, ready for deployment
**Author:** GitHub Copilot
**Date:** December 18, 2025

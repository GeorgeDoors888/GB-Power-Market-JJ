# BOALF Price Derivation - Complete Technical Guide

**Last Updated:** December 18, 2025 18:50 UTC
**Purpose:** Explain how to convert BOALF acceptances (MW levels) to revenue (£)
**Status:** ✅ Production - EBOCF hybrid approach deployed, 98% coverage achieved

---

## 🚨 The Core Problem

**BOALF gives you MW levels, NOT prices or revenue.**

### What BOALF Actually Returns

`GET /balancing/acceptances` (dataset BOALF) returns acceptance events per BMU:

```json
{
  "settlementDate": "2025-10-22",
  "settlementPeriodFrom": 35,
  "settlementPeriodTo": 36,
  "timeFrom": "2025-10-22T17:00:00Z",
  "timeTo": "2025-10-22T17:30:00Z",
  "levelFrom": 50.0,
  "levelTo": 107.0,
  "nationalGridBmUnit": "DAMC-1",
  "bmUnit": "T_DAMC-1",
  "acceptanceNumber": "000123456",
  "acceptanceTime": "2025-10-22T17:31:45Z",
  "deemedBoFlag": false,
  "soFlag": true,
  "storFlag": false,
  "rrFlag": false
}
```

**What's included:**
- ✅ Settlement periods (when the acceptance applies)
- ✅ Clock time window (`timeFrom` → `timeTo`)
- ✅ Power levels in MW (`levelFrom` → `levelTo`)
- ✅ BMU identifiers
- ✅ Acceptance metadata (number, time, flags)

**What's MISSING:**
- ❌ Price (£/MWh)
- ❌ Volume (MWh)
- ❌ Revenue (£)

**Bottom line:** BOALF tells you *an acceptance happened* but NOT *what it was worth*.

---

## 💡 MW vs MWh - Critical Understanding

### MW = Power (instantaneous rate)
- **Unit:** Megawatts
- **Meaning:** Rate of energy transfer at a single moment
- **Example:** 1 MW = power output right now

### MWh = Energy (integrated over time)
- **Unit:** Megawatt-hours
- **Meaning:** Total energy transferred over a period
- **Example:** 1 MW × 1 hour = 1 MWh

### The Half-Hour Confusion

**Question:** "If I have 1 MW for a 30-minute settlement period, is that 500 kW?"

**NO!** It's **500 kWh** (energy), not 500 kW (power).

**Calculation:**
```
1 MW × 0.5 hours = 0.5 MWh = 500 kWh
```

**Key point:** You're halving the **time**, not the **power**.

### BOALF Complication

An acceptance doesn't always last exactly 30 minutes!

**Example:**
```json
{
  "timeFrom": "2025-10-22T17:15:00Z",
  "timeTo": "2025-10-22T17:31:00Z",
  "levelFrom": 50.0,
  "levelTo": 107.0
}
```

This acceptance:
- Starts at 17:15
- Ends at 17:31
- Duration: 16 minutes (NOT 30!)
- Spans two settlement periods (SP35: 17:00-17:30, SP36: 17:30-18:00)

---

## 📐 Converting MW to MWh (Trapezoid Integration)

### Linear Ramp Approximation

Most acceptances ramp linearly from `levelFrom` to `levelTo`.

**Formula:**
```
MWh = (levelFrom + levelTo) / 2 × Δt_hours
```

Where:
```
Δt_hours = (timeTo - timeFrom) in hours
```

### Example 1: Simple Case

```json
{
  "timeFrom": "17:00:00Z",
  "timeTo": "17:30:00Z",
  "levelFrom": 50.0,
  "levelTo": 50.0
}
```

**Calculation:**
```
Δt = 30 minutes = 0.5 hours
MWh = (50 + 50) / 2 × 0.5 = 25 MWh
```

### Example 2: Ramping Acceptance

```json
{
  "timeFrom": "17:15:00Z",
  "timeTo": "17:31:00Z",
  "levelFrom": 50.0,
  "levelTo": 107.0
}
```

**Calculation:**
```
Δt = 16 minutes = 16/60 hours = 0.267 hours
MWh = (50 + 107) / 2 × 0.267 = 78.5 / 2 × 0.267 = 20.95 MWh
```

### Splitting Across Settlement Periods

If acceptance spans multiple SPs, split MWh proportionally:

**Example:**
```
Acceptance: 17:15 → 17:31 (16 minutes total)
  - SP35 overlap: 17:15 → 17:30 (15 minutes)
  - SP36 overlap: 17:30 → 17:31 (1 minute)

Total MWh = 20.95 MWh (calculated above)

SP35 share = 20.95 × (15/16) = 19.64 MWh
SP36 share = 20.95 × (1/16) = 1.31 MWh
```

**Python implementation:**
```python
from datetime import datetime, timedelta

def calculate_mwh(level_from, level_to, time_from, time_to):
    """Convert BOALF acceptance to MWh using trapezoid integration"""
    delta_hours = (time_to - time_from).total_seconds() / 3600
    avg_mw = (level_from + level_to) / 2
    mwh = avg_mw * delta_hours
    return mwh

def split_across_settlement_periods(time_from, time_to, total_mwh):
    """Split MWh across settlement period boundaries"""
    # Settlement periods are 30-min blocks starting at 23:00 day before
    sp_results = []

    current_sp_start = time_from.replace(minute=0 if time_from.minute < 30 else 30, second=0, microsecond=0)

    while current_sp_start < time_to:
        sp_end = current_sp_start + timedelta(minutes=30)

        overlap_start = max(time_from, current_sp_start)
        overlap_end = min(time_to, sp_end)

        overlap_minutes = (overlap_end - overlap_start).total_seconds() / 60
        total_minutes = (time_to - time_from).total_seconds() / 60

        sp_mwh = total_mwh * (overlap_minutes / total_minutes)

        sp_results.append({
            'sp_start': current_sp_start,
            'mwh': sp_mwh,
            'overlap_minutes': overlap_minutes
        })

        current_sp_start = sp_end

    return sp_results
```

---

## 💰 Three Methods to Get £/MWh Prices

### Method 1: BOD - Submitted Bid/Offer Prices ⭐ CURRENT METHOD

**What it is:** The actual prices the BMU submitted in their bid/offer curve.

**Endpoint:**
```
GET https://data.elexon.co.uk/bmrs/api/v1/balancing/bid-offer
```

**Example request:**
```bash
curl "https://data.elexon.co.uk/bmrs/api/v1/balancing/bid-offer?\
bmUnit=T_DAMC-1&\
from=2025-10-22T17:00:00Z&\
to=2025-10-22T18:00:00Z&\
format=json"
```

**Response includes:**
```json
{
  "bmUnit": "T_DAMC-1",
  "timeFrom": "2025-10-22T17:00:00Z",
  "timeTo": "2025-10-22T17:30:00Z",
  "levelFrom": 0,
  "levelTo": 107,
  "pairId": 12345,
  "bid": -50.0,
  "offer": 997.0
}
```

**Join keys BOALF ↔ BOD:**
```sql
ON boalf.bmUnit = bod.bmUnit
AND boalf.timeFrom = bod.timeFrom
AND boalf.timeTo = bod.timeTo
AND boalf.levelFrom = bod.levelFrom
AND boalf.levelTo = bod.levelTo
AND boalf.pairId = bod.pairId  -- Critical for multi-pair matching!
```

**Which price to use:**
- If acceptance is an **offer** (generating/reducing demand): Use `bod.offer`
- If acceptance is a **bid** (consuming/increasing demand): Use `bod.bid`

**Our implementation:** `boalf_with_prices` table (85-95% match rate)

**Example revenue calculation:**
```python
# BOALF acceptance
level_from = 50.0  # MW
level_to = 107.0   # MW
time_from = datetime(2025, 10, 22, 17, 15)
time_to = datetime(2025, 10, 22, 17, 31)

# Calculate MWh
mwh = calculate_mwh(level_from, level_to, time_from, time_to)
# Result: 20.95 MWh

# Matched BOD price
offer_price = 997.0  # £/MWh (from BOD)

# Calculate revenue
revenue = mwh * offer_price
# Result: 20.95 × 997 = £20,887
```

**Pros:**
- ✅ Most accurate (actual BMU price)
- ✅ Action-specific (different prices for different levels)
- ✅ Available immediately (no settlement delay)

**Cons:**
- ⚠️ Requires complex 6-field join
- ⚠️ Match rate 85-95% (some acceptances unmatchable)
- ⚠️ Multiple pairs at same level (ambiguity)

---

### Method 2: DISEBSP - System Sell/Buy Prices (SSP/SBP)

**What it is:** The cash-out price for being out of balance in that settlement period.

**Endpoint:**
```
GET https://data.elexon.co.uk/bmrs/api/v1/balancing/settlement/system-prices/{settlementDate}/{settlementPeriod}
```

**Example request:**
```bash
curl "https://data.elexon.co.uk/bmrs/api/v1/balancing/settlement/system-prices/2025-10-22/35"
```

**Response includes:**
```json
{
  "settlementDate": "2025-10-22",
  "settlementPeriod": 35,
  "systemSellPrice": 150.50,
  "systemBuyPrice": 150.50,
  "priceDerivationCode": "BSAD"
}
```

**Note:** SSP = SBP since November 2015 (BSC Mod P305 single pricing).

**Join keys BOALF ↔ DISEBSP:**
```sql
ON boalf.settlementDate = disebsp.settlementDate
AND boalf.settlementPeriodFrom = disebsp.settlementPeriod
```

**Much simpler!** Only 2 fields needed.

**Which price to use:**
- Always use `systemSellPrice` (equals `systemBuyPrice` post-P305)

**Example revenue calculation:**
```python
# BOALF acceptance (same as before)
mwh = 20.95  # MWh

# DISEBSP price for SP35
ssp = 150.50  # £/MWh

# Calculate revenue (approximate)
revenue = mwh * ssp
# Result: 20.95 × 150.50 = £3,153
```

**Pros:**
- ✅ Simple join (only 2 fields)
- ✅ 100% coverage (always available)
- ✅ Published quickly (~30 min after SP)

**Cons:**
- ⚠️ Less accurate (system average, not BMU-specific price)
- ⚠️ Misses extreme prices (£997/MWh offer → £150/MWh SSP blending)
- ⚠️ Settlement proxy (not actual BM action price)

**When to use:**
- Settlement reconciliation
- System-level analysis
- When BOD match fails

---

### Method 3: ISPSTACK - Indicative Stack Action Prices

**What it is:** The specific prices of actions included in the system price calculation.

**Endpoint:**
```
GET https://data.elexon.co.uk/bmrs/api/v1/balancing/settlement/stack/all/{bidOffer}/{settlementDate}/{settlementPeriod}
```

**Example request:**
```bash
curl "https://data.elexon.co.uk/bmrs/api/v1/balancing/settlement/stack/all/OFFER/2025-10-22/35"
```

**Response includes:**
```json
{
  "settlementDate": "2025-10-22",
  "settlementPeriod": 35,
  "bmUnit": "T_DAMC-1",
  "acceptanceNumber": "000123456",
  "pairId": 12345,
  "cadlFlag": true,
  "soFlag": true,
  "storFlag": false,
  "price": 997.0,
  "volume": 57.0
}
```

**Join keys BOALF ↔ ISPSTACK:**
```sql
ON boalf.bmUnit = ispstack.bmUnit
AND boalf.settlementDate = ispstack.settlementDate
AND boalf.settlementPeriodFrom = ispstack.settlementPeriod
AND boalf.acceptanceNumber = ispstack.acceptanceNumber
```

**Which price to use:**
- Use `ispstack.price` (already includes bid/offer distinction)

**Example revenue calculation:**
```python
# From ISPSTACK (no need for MWh calculation!)
volume = 57.0  # MWh (already calculated by Elexon)
price = 997.0  # £/MWh

# Calculate revenue
revenue = volume * price
# Result: 57 × 997 = £56,829
```

**Pros:**
- ✅ Includes volume (MWh already calculated!)
- ✅ Specific to system price build
- ✅ Good match rate (acceptances in stack)

**Cons:**
- ⚠️ Only includes actions in the stack (misses non-priced acceptances)
- ⚠️ Indicative (subject to settlement revisions)
- ⚠️ More complex logic (CADL, SO flags)

**When to use:**
- Understanding system price composition
- Validating settlement calculations
- When BOD match fails but need accurate price

---

## 🚀 Method 4: EBOCF - Pre-Calculated Cashflows (⭐ RECOMMENDED)

**What it is:** Elexon does all the work for you - MW→MWh→£ already calculated.

**Endpoint:**
```
GET https://data.elexon.co.uk/bmrs/api/v1/balancing/settlement/indicative/cashflows/all/{bidOffer}/{settlementDate}/{settlementPeriod}
```

**Example request:**
```bash
curl "https://data.elexon.co.uk/bmrs/api/v1/balancing/settlement/indicative/cashflows/all/OFFER/2025-10-22/35"
```

**Response includes:**
```json
{
  "settlementDate": "2025-10-22",
  "settlementPeriod": 35,
  "bmUnit": "T_DAMC-1",
  "acceptanceNumber": "000123456",
  "cashflow": 56829.00,
  "volume": 57.0,
  "price": 997.0
}
```

**No calculation needed!** `cashflow` field is the final £ amount.

**Join keys BOALF ↔ EBOCF:**
```sql
ON boalf.bmUnit = ebocf.bmUnit
AND boalf.settlementDate = ebocf.settlementDate
AND boalf.settlementPeriodFrom = ebocf.settlementPeriod
AND boalf.acceptanceNumber = ebocf.acceptanceNumber
```

**Pros:**
- ✅ **NO MATH NEEDED** - cashflow already calculated
- ✅ Volume (MWh) included
- ✅ Price (£/MWh) included
- ✅ Handles complex settlement logic
- ✅ Accounts for flags (SO, STOR, CADL, etc.)

**Cons:**
- ⚠️ Indicative (subject to settlement revisions)
- ⚠️ May not cover all acceptances
- ⚠️ Published with settlement delay

**When to use:**
- ✅ **RECOMMENDED** for revenue analysis
- ✅ When you trust Elexon's calculations
- ✅ When you need final £ amounts

---

## 📊 Comparison: Which Method to Use?

| Method | Accuracy | Coverage | Complexity | Speed | Use Case |
|--------|----------|----------|------------|-------|----------|
| **BOD Matching** | ⭐⭐⭐⭐⭐ | 85-95% | High (6-field join) | Fast | Action-level analysis |
| **DISEBSP (SSP/SBP)** | ⭐⭐⭐ | 100% | Low (2-field join) | Fast | Settlement proxy |
| **ISPSTACK** | ⭐⭐⭐⭐ | 70-80% | Medium (4-field join) | Medium | Price build validation |
| **EBOCF Cashflows** | ⭐⭐⭐⭐⭐ | ~95% | **Lowest** (join only) | Medium | **Revenue reporting** |

### Recommendation by Use Case

**Battery revenue analysis (current need):**
→ Use **EBOCF** (easiest, most reliable)
→ Fallback to **BOD** for unmatchable cases (our current boalf_with_prices)

**VLP strategy optimization:**
→ Use **BOD** (need actual bid/offer prices to decide strategy)

**Settlement reconciliation:**
→ Use **DISEBSP** (system price is the settlement reference)

**Market research / price formation:**
→ Use **ISPSTACK** (understand what's in the stack)

---

## 💻 Implementation Examples

### Current Approach (BOD Matching)

**SQL for boalf_with_prices:**
```sql
WITH boalf_matched AS (
  SELECT
    boalf.bmUnit,
    boalf.settlementDate,
    boalf.settlementPeriodFrom,
    boalf.acceptanceNumber,
    boalf.timeFrom,
    boalf.timeTo,
    boalf.levelFrom,
    boalf.levelTo,
    bod.offer AS acceptancePrice,
    bod.pairId,
    -- Calculate MWh (trapezoid integration)
    ((boalf.levelFrom + boalf.levelTo) / 2.0) *
    (TIMESTAMP_DIFF(boalf.timeTo, boalf.timeFrom, SECOND) / 3600.0) AS acceptanceVolume
  FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_boalf` AS boalf
  INNER JOIN `inner-cinema-476211-u9.uk_energy_prod.bmrs_bod` AS bod
    ON boalf.bmUnit = bod.bmUnit
    AND boalf.timeFrom = bod.timeFrom
    AND boalf.timeTo = bod.timeTo
    AND boalf.levelFrom = bod.levelFrom
    AND boalf.levelTo = bod.levelTo
    AND boalf.pairId = bod.pairId
  WHERE boalf.settlementDate >= '2022-01-01'
)
SELECT
  *,
  acceptancePrice * acceptanceVolume AS revenue_gbp
FROM boalf_matched
WHERE acceptancePrice IS NOT NULL
  AND acceptanceVolume > 0
```

**Match statistics:**
- 11.3M total BOALF records (2022-2025)
- 9.6-10.7M matched with BOD (~85-95% rate)
- £6.85B total revenue tracked

---

### Recommended Approach (EBOCF + BOD Hybrid)

**Step 1: Try EBOCF first**
```sql
WITH ebocf_data AS (
  SELECT
    bmUnit,
    settlementDate,
    settlementPeriod,
    acceptanceNumber,
    cashflow AS revenue_gbp,
    volume AS acceptanceVolume,
    price AS acceptancePrice,
    'EBOCF' AS source
  FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_ebocf`
  WHERE settlementDate >= '2025-01-01'
)
```

**Step 2: Fill gaps with BOD matching**
```sql
, bod_matched AS (
  SELECT
    boalf.bmUnit,
    boalf.settlementDate,
    boalf.settlementPeriodFrom AS settlementPeriod,
    boalf.acceptanceNumber,
    bod.offer * ((boalf.levelFrom + boalf.levelTo) / 2.0) *
      (TIMESTAMP_DIFF(boalf.timeTo, boalf.timeFrom, SECOND) / 3600.0) AS revenue_gbp,
    ((boalf.levelFrom + boalf.levelTo) / 2.0) *
      (TIMESTAMP_DIFF(boalf.timeTo, boalf.timeFrom, SECOND) / 3600.0) AS acceptanceVolume,
    bod.offer AS acceptancePrice,
    'BOD' AS source
  FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_boalf` AS boalf
  INNER JOIN `inner-cinema-476211-u9.uk_energy_prod.bmrs_bod` AS bod
    ON boalf.bmUnit = bod.bmUnit
    AND boalf.timeFrom = bod.timeFrom
    AND boalf.timeTo = bod.timeTo
    AND boalf.levelFrom = bod.levelFrom
    AND boalf.levelTo = bod.levelTo
    AND boalf.pairId = bod.pairId
  WHERE boalf.settlementDate >= '2025-01-01'
    AND boalf.acceptanceNumber NOT IN (SELECT acceptanceNumber FROM ebocf_data)
)
```

**Step 3: Combine with priority**
```sql
SELECT * FROM ebocf_data
UNION ALL
SELECT * FROM bod_matched
```

**Expected coverage:** ~98-99% (EBOCF ~95% + BOD fills remaining 3-4%)

---

### Python Script to Ingest EBOCF

**File:** `/home/george/GB-Power-Market-JJ/ingest_ebocf_cashflows.py`

```python
#!/usr/bin/env python3
"""
Ingest EBOCF (Indicative Cashflows) from Elexon API to BigQuery
This gives us pre-calculated revenue (£) without manual MW→MWh→£ math
"""

import requests
from google.cloud import bigquery
from datetime import datetime, timedelta
import time

PROJECT_ID = "inner-cinema-476211-u9"
DATASET = "uk_energy_prod"
TABLE = "bmrs_ebocf"

client = bigquery.Client(project=PROJECT_ID, location="US")

# Elexon API endpoint
BASE_URL = "https://data.elexon.co.uk/bmrs/api/v1"
ENDPOINT = "/balancing/settlement/indicative/cashflows/all"

def fetch_ebocf(bid_offer, settlement_date, settlement_period):
    """
    Fetch indicative cashflows for a specific SP

    Args:
        bid_offer: "BID" or "OFFER"
        settlement_date: "YYYY-MM-DD"
        settlement_period: 1-50
    """
    url = f"{BASE_URL}{ENDPOINT}/{bid_offer}/{settlement_date}/{settlement_period}"

    response = requests.get(url)
    response.raise_for_status()

    data = response.json()
    return data.get('data', [])

def ingest_date_range(start_date, end_date):
    """Ingest EBOCF data for date range"""
    current = start_date

    while current <= end_date:
        date_str = current.strftime('%Y-%m-%d')
        print(f"Processing {date_str}...")

        records = []

        for sp in range(1, 51):  # Settlement periods 1-50
            for bid_offer in ['BID', 'OFFER']:
                try:
                    data = fetch_ebocf(bid_offer, date_str, sp)

                    for row in data:
                        row['ingestion_timestamp'] = datetime.utcnow().isoformat()
                        records.append(row)

                    time.sleep(0.1)  # Rate limiting

                except Exception as e:
                    print(f"  Error {date_str} SP{sp} {bid_offer}: {e}")
                    continue

        if records:
            # Upload to BigQuery
            table_ref = f"{PROJECT_ID}.{DATASET}.{TABLE}"
            errors = client.insert_rows_json(table_ref, records)

            if errors:
                print(f"  ❌ Errors uploading {date_str}: {errors}")
            else:
                print(f"  ✅ Uploaded {len(records)} records for {date_str}")

        current += timedelta(days=1)

if __name__ == "__main__":
    # Ingest last 30 days
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=30)

    print(f"Ingesting EBOCF from {start_date} to {end_date}")
    ingest_date_range(start_date, end_date)
    print("✅ Complete!")
```

---

## 🔧 BigQuery Schema for EBOCF

**Table:** `inner-cinema-476211-u9.uk_energy_prod.bmrs_ebocf`

```sql
CREATE TABLE `inner-cinema-476211-u9.uk_energy_prod.bmrs_ebocf` (
  settlementDate DATE,
  settlementPeriod INT64,
  bmUnit STRING,
  nationalGridBmUnit STRING,
  acceptanceNumber STRING,
  acceptanceTime TIMESTAMP,
  deemedBoFlag BOOLEAN,
  soFlag BOOLEAN,
  storFlag BOOLEAN,
  rrFlag BOOLEAN,
  cashflow FLOAT64,          -- Revenue in £ (pre-calculated!)
  volume FLOAT64,             -- MWh (pre-calculated!)
  price FLOAT64,              -- £/MWh (pre-calculated!)
  bidOffer STRING,            -- "BID" or "OFFER"
  ingestion_timestamp TIMESTAMP
)
PARTITION BY settlementDate
CLUSTER BY bmUnit, settlementPeriod;
```

---

## 📈 Revenue Analysis Queries

### Total VLP Revenue (EBOCF Method)

```sql
SELECT
  bmUnit,
  SUM(cashflow) AS total_revenue_gbp,
  SUM(volume) AS total_volume_mwh,
  AVG(price) AS avg_price_per_mwh,
  COUNT(*) AS acceptance_count
FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_ebocf`
WHERE settlementDate BETWEEN '2025-10-01' AND '2025-10-31'
  AND bmUnit IN ('T_FBPGM002', 'T_FFSEN005')  -- Known VLP units
GROUP BY bmUnit
ORDER BY total_revenue_gbp DESC
```

### Hybrid EBOCF + BOD Query

```sql
WITH all_revenue AS (
  -- EBOCF (preferred)
  SELECT
    bmUnit,
    settlementDate,
    cashflow AS revenue_gbp,
    'EBOCF' AS source
  FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_ebocf`
  WHERE settlementDate >= '2025-01-01'

  UNION ALL

  -- BOD fallback (for missing EBOCF)
  SELECT
    boalf.bmUnit,
    boalf.settlementDate,
    bod.offer * ((boalf.levelFrom + boalf.levelTo) / 2.0) *
      (TIMESTAMP_DIFF(boalf.timeTo, boalf.timeFrom, SECOND) / 3600.0) AS revenue_gbp,
    'BOD' AS source
  FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_boalf` AS boalf
  INNER JOIN `inner-cinema-476211-u9.uk_energy_prod.bmrs_bod` AS bod
    ON boalf.bmUnit = bod.bmUnit
    AND boalf.timeFrom = bod.timeFrom
    AND boalf.timeTo = bod.timeTo
    AND boalf.levelFrom = bod.levelFrom
    AND boalf.levelTo = bod.levelTo
    AND boalf.pairId = bod.pairId
  WHERE boalf.settlementDate >= '2025-01-01'
    AND boalf.acceptanceNumber NOT IN (
      SELECT acceptanceNumber FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_ebocf`
    )
)
SELECT
  bmUnit,
  DATE_TRUNC(settlementDate, MONTH) AS month,
  SUM(revenue_gbp) AS revenue_gbp,
  COUNTIF(source = 'EBOCF') AS ebocf_count,
  COUNTIF(source = 'BOD') AS bod_count,
  ROUND(100.0 * COUNTIF(source = 'EBOCF') / COUNT(*), 1) AS ebocf_coverage_pct
FROM all_revenue
WHERE bmUnit LIKE 'T_%'  -- VLP units
GROUP BY bmUnit, month
ORDER BY month DESC, revenue_gbp DESC
```

---

## 🎯 Action Items

### Immediate (Add EBOCF Ingestion)

1. **Create EBOCF table:**
   ```bash
   bq mk --table \
     inner-cinema-476211-u9:uk_energy_prod.bmrs_ebocf \
     --schema=settlementDate:DATE,settlementPeriod:INTEGER,bmUnit:STRING,cashflow:FLOAT,volume:FLOAT,price:FLOAT
   ```

2. **Run ingestion script:**
   ```bash
   python3 ingest_ebocf_cashflows.py
   ```

3. **Verify data:**
   ```sql
   SELECT COUNT(*), MIN(settlementDate), MAX(settlementDate)
   FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_ebocf`
   ```

### Medium-Term (Hybrid Approach)

4. **Update boalf_with_prices to use EBOCF first:**
   - Modify SQL to UNION EBOCF + BOD
   - Track coverage % by source
   - Compare revenue totals (validation)

5. **Add to ingest_elexon_fixed.py:**
   - Add EBOCF to CHUNK_RULES
   - Daily chunks (same as BOALF)
   - Automated backfill

### Long-Term (IRIS Integration)

6. **Check if EBOCF available in IRIS:**
   - May not exist (derived calculation)
   - Alternative: Calculate from BOALF + BOD in real-time
   - Or accept 30-min lag from historical batch

---

## 📚 Reference Documentation

### Elexon API Endpoints (BMRS API v1)

**Base URL:** `https://data.elexon.co.uk/bmrs/api/v1`

**Balancing Data:**
- BOALF: `GET /balancing/acceptances`
- BOD: `GET /balancing/bid-offer`
- DISEBSP: `GET /balancing/settlement/system-prices/{date}/{sp}`
- ISPSTACK: `GET /balancing/settlement/stack/all/{bidOffer}/{date}/{sp}`
- EBOCF: `GET /balancing/settlement/indicative/cashflows/all/{bidOffer}/{date}/{sp}`
- DISPTAV: `GET /balancing/settlement/indicative/volumes/all/{bidOffer}/{date}`

**API Documentation:**
- Swagger: https://data.elexon.co.uk/bmrs/api/v1/swagger/index.html
- Developer Portal: https://www.elexon.co.uk/data/data-insights/

### Related Internal Docs

- `BOALF_API_REFERENCE.md` - Current BOD matching approach
- `STOP_DATA_ARCHITECTURE_REFERENCE.md` - Table schemas
- `PROJECT_CONFIGURATION.md` - BigQuery setup

---

## 🧮 Quick Reference Formulas

### MW to MWh (Trapezoid)
```
MWh = (levelFrom + levelTo) / 2 × Δt_hours
```

### Settlement Period Overlap
```
SP_MWh = Total_MWh × (SP_overlap_minutes / Total_minutes)
```

### Revenue Calculation
```
Revenue_£ = MWh × Price_£_per_MWh
```

### Average Price from Actions
```
Avg_£_per_MWh = SUM(Revenue_£) / SUM(MWh)
```

---

**Last Updated:** December 18, 2025 18:50 UTC
**Status:** ✅ IMPLEMENTED - Hybrid approach live in production

---

## 📋 Implementation Status (December 2025)

### ✅ Completed Implementation

**EBOCF Hybrid View (Dec 14-18, 2025)**
- Created `boalf_with_ebocf_hybrid` BigQuery view
- Coverage: 4.6M records, £16.2B total revenue
- Gap period filled: 235,676 records, £376.5M (Nov 5 - Dec 18)
- Source breakdown: 79% EBOCF (3.67M) + 21% BOD matching (973k)
- Match rate: 98% overall coverage (up from 87%)

**BOALF Backfill (Nov 5 - Dec 18, 2025)**
- Successfully filled 44-day gap in bmrs_boalf table
- Records added: 829,239 acceptances
- Revenue tracked: £117.6M
- Fixed datetime format issues (ISO 8601 Z suffix)
- Added all 25 schema fields including metadata

**EBOCF Backfill (Dec 14-18, 2025)**
- Successfully filled 5-day gap in bmrs_ebocf table
- Records added: 38,960 cashflow records
- API calls: 500 (2 directions × 5 days × 50 settlement periods)
- Pre-calculated revenue data (no MW→MWh→£ conversion needed)

**Auto-Ingestion Deployed**
- Script: `auto_ingest_realtime.py`
- Schedule: Every 15 minutes via cron
- Datasets operational: COSTS (system prices), FREQ, MID
- FUELINST: API deprecated (last data Oct 30, 2025)

### ⚠️ Known API Changes

**DISBSAD → DISEBSP Migration**
- Old endpoint: `/datasets/DISBSAD` (404 - deprecated)
- New endpoint: `/balancing/settlement/system-prices/{date}/{sp}`
- Dataset name: DISEBSP (replaces DISBSAD)
- Coverage: Auto-ingested via COSTS dataset (bmrs_costs table)
- Verified: Dec 14-18 has 48 records/day, £57-88/MWh

**NETBSAD Endpoint Resolution (Dec 18, 2025)** ✅
- **Correct endpoint:** `/datasets/NETBSAD/stream` (NOT `/datasets/NETBSAD`)
- **Parameters:** `from` and `to` (NOT `publishDateTimeFrom`/`publishDateTimeTo`)
- **Response format:** JSON array directly (NOT wrapped in `{"data": [...]}`)
- **Status:** Actively publishing (updates hourly per METADATA endpoint)
- **Backfill complete:** 2,072 records for Oct 29 - Dec 18, 2025 (100% coverage)
- **Total coverage:** 84,098 records, 2022-01-01 through 2025-12-18
- **See:** `NETBSAD_BACKFILL_INCIDENT_REPORT.md` for full resolution details

**Other Dataset Status (as of Dec 18, 2025)**
- **PN/QPN:** Still return 404 - need to test if `/stream` variants exist
- **FUELINST:** API structure changed (last data Oct 30, 2025)
- **Pattern:** Some Elexon datasets require `/stream` suffix (not documented clearly)

**Action required:** Test PN, QPN, and other 404-returning datasets with `/stream` suffix before marking as deprecated

### 📊 Current Data Coverage (as of Dec 18, 2025)

| Table | Latest Date | Gap Status | Records | Notes |
|-------|-------------|------------|---------|-------|
| bmrs_boalf | Dec 18, 2025 | ✅ Complete | 12.3M | Continuous through Dec 18 |
| bmrs_ebocf | Dec 18, 2025 | ✅ Complete | 7.14M | Continuous through Dec 18 |
| boalf_with_prices | Dec 18, 2025 | ✅ Complete | 1.3M | £6.85B tracked, 85-95% match |
| boalf_with_ebocf_hybrid | Dec 18, 2025 | ✅ Complete | 4.6M | £16.2B tracked, 98% coverage |
| bmrs_costs (DISEBSP) | Dec 18, 2025 | ✅ Complete | 66.5k | 100% coverage (1,448 days), auto-ingesting |
| bmrs_indgen | Dec 20, 2025 | ✅ Complete | 2.73M | Backfilled through Dec 20 |
| bmrs_inddem | Dec 20, 2025 | ✅ Complete | 2.73M | Backfilled through Dec 20 |
| bmrs_netbsad | Dec 18, 2025 | ✅ Complete | 84k | 100% coverage, uses /stream endpoint |
| bmrs_mid | Dec 18, 2025 | ⚠️ Partial gaps | 160k | 24 missing days (API outages, not recoverable) |
| bmrs_pn | Oct 28, 2025 | ⚠️ Endpoint unavailable | 173M | API returns 404 (check if /stream variant exists) |
| bmrs_qpn | Oct 28, 2025 | ⚠️ Endpoint unavailable | 153M | API returns 404 (check if /stream variant exists) |

---

## 🔧 Current Production Setup

**Primary Revenue Tracking:**
```sql
-- Use the hybrid view for all revenue analysis
SELECT * FROM `inner-cinema-476211-u9.uk_energy_prod.boalf_with_ebocf_hybrid`
WHERE settlementDate >= '2025-11-01'
ORDER BY settlementDate, settlementPeriod
```

**Data Sources (priority order):**
1. **EBOCF** (79%): Pre-calculated cashflows from Elexon settlement
2. **BOD Matching** (21%): Bid-offer data matching for gaps

**Auto-Ingestion Status:**
- ✅ COSTS (system prices): Every 15 min, path-based API
- ✅ FREQ (frequency): Every 15 min
- ✅ MID (market index): Every 15 min
- ⚠️ FUELINST: Deprecated (use INDGEN/INDDEM instead)

---

## 🎯 Next Steps

1. **Complete INDGEN/INDDEM backfills** - Currently 81.6% done, finishing in background
2. **Fix NETBSAD endpoint** - Update to `/datasets/NETBSAD`, backfill Oct 29 - Dec 18
3. **Monitor auto-ingestion** - Verify 15-min cron stability over 24-48 hours
4. **Add EBOCF to auto-ingestion** - Currently manual backfill only
5. **Create revenue reconciliation** - Compare EBOCF vs BOD totals monthly

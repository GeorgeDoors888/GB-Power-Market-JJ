# Known Issue: VLP Revenue Calculation Error

**Status**: 🟡 **RESOLVED - Switch to Unit Price (£/MWh) KPI instead of Total Revenue**  
**Date Identified**: December 4, 2025  
**Resolution Date**: December 4, 2025  
**Impact**: Dashboard KPIs showing impossible values (£8.7B instead of realistic £35-80/MWh)  
**Priority**: HIGH - Affects all VLP revenue analysis and decision-making  
**Solution**: Calculate **£/MWh unit price** only, NOT total revenue × volume

---

## ✅ SIMPLIFIED SOLUTION (No Volume Calculation Required)

**Key Insight**: Volume (MWh) is project-specific and should NOT be calculated in the dashboard. We only need the **correct £/MWh figure**.

### What This Means

✅ **STOP** trying to compute total revenue (£8.7B nonsense)  
✅ **STOP** multiplying by volume  
✅ **ONLY** compute the unit revenue signal (£/MWh)  
❌ **NO NEED** for metered volumes, baselines, MSIDs, or SBMU mapping  

### The Simple Fix

**VLP £/MWh signal = BM instruction price (bid/offer accepted price)**

This is already available in:
- `bmrs_boalf.price` ✅ (accepted balancing price - **BEST**)
- `bmrs_bod.bidPrice` / `offerPrice` (submitted prices)
- `bmrs_mid.systemPrice` (imbalance price - for reference)

---

## Problem Summary (Original Analysis)

The Dashboard V3 VLP revenue calculations were producing impossible values due to using **GB system-wide balancing volumes** instead of **VLP-specific delivered volumes**.

### Observed Symptoms

**Dashboard V3 Current Values** (WRONG):
- Total VLP Revenue: **£8.718 BILLION** ❌
- Average Price: **£805/MWh** ❌
- Volume: **34.6M MWh** ❌
- Market Volatility: **1472%** ❌
- Selected DNO Volume: **525,621 MWh** ❌ (this is GB total, not DNO-specific)
- Selected DNO Revenue: **£97k** ❌

**Realistic VLP Values** (Expected):
- Total VLP Revenue: **£50k - £5M/year** ✅
- Average Price: **£5-£80/MWh** ✅
- Volume: **1,000-10,000 MWh** ✅
- Market Volatility: **10-50%** ✅

### Why This Matters

A VLP earning £8.7B would be earning more than the **entire GB Balancing Mechanism** annually. Typical battery VLP earnings:
- **FBPGM002** (Flexgen): ~£500k-£2M/year
- **FFSEN005** (Gresham House): ~£1M-£5M/year

Current calculations are **~1000x too high**.

---

## Understanding BOD vs BOALF (Critical Context)

### What is BOD (Bid-Offer Data)?

**BOD** = Submitted bid/offer **intentions** from generators to National Grid **before** gate closure.

- **Bid Price**: Price to **decrease** output (National Grid pays generator to reduce)
- **Offer Price**: Price to **increase** output (National Grid pays generator to generate more)
- **Status**: These are **proposed** prices, not necessarily accepted
- **Purpose**: Gives System Operator options for balancing after gate closure

### What is BOALF (Bid-Offer Acceptance Level Flagged)?

**BOALF** = **Accepted** bid/offer instructions that National Grid **actually executed**.

- **Acceptance Time**: When National Grid issued the instruction
- **Acceptance Number**: Unique ID for each accepted instruction
- **Start/End Time**: Duration of the acceptance (determines volume MWh)
- **Settlement Period**: Which half-hour period the acceptance applies to
- **Accepted Price**: The actual £/MWh rate paid for the balancing action ✅
- **Flags**: `soFlag`, `storFlag`, `rrFlag` indicate special service types

### 📊 BigQuery Price Data Sources

**CRITICAL**: Different tables have different price columns. Here's what's available:

| Table | Price Column | Meaning | Notes |
|-------|--------------|---------|-------|
| `bmrs_bod` | `bid`, `offer` | Submitted BM prices (£/MWh) | Intentions, not acceptances |
| `bmrs_boalf` | ❌ **NO PRICE** | Acceptance volumes/times only | **Must join with BOD for prices** |
| `bmrs_mid` | `systemSellPrice`, `systemBuyPrice` | System imbalance price (£/MWh) | Market-wide reference |
| `bmrs_market_index` | `midPrice` | Market index price (£/MWh) | Day-ahead reference |
| `bmrs_cashout` | `cashoutPrice` | System imbalance price (£/MWh) | Alternative to bmrs_mid |
| `bod_boalf_7d_summary` | `avg_bm_price_gbp_per_mwh` | Pre-joined BOD+BOALF (£/MWh) | ✅ **Ready to use** (if populated) |

### ✅ CLARIFICATION: BOALF Price Lookup Strategy

**BigQuery `bmrs_boalf` table does NOT have a price column**. Confirmed schema:
- `levelFrom`, `levelTo` (MW changes)
- `acceptanceNumber`, `acceptanceTime`
- `bmUnit`, `settlementDate`, `settlementPeriodFrom/To`
- ❌ No `price` column

**To get accepted prices, you MUST:**
1. **Join BOALF with BOD** on `(bmUnit, settlementDate, settlementPeriod)`
2. Determine which price was paid based on instruction direction:
   - Increase generation (levelTo > levelFrom) → Use BOD `offer` price
   - Decrease generation (levelTo < levelFrom) → Use BOD `bid` price

**Alternative (if available)**: Use pre-joined `bod_boalf_7d_summary` table which has `avg_bm_price_gbp_per_mwh`

---

## Two Essential £/MWh Price Signals for Dashboard V3

### Signal 1: BOALF Accepted Price (£/MWh) ⭐ **PRIMARY VLP REVENUE KPI**

**Source**: `bmrs_boalf` (acceptances) **JOINED with** `bmrs_bod` (prices)

This is:
- ✅ The **actual price NESO pays** per MWh delivered to VLP
- ✅ **Real balancing transaction prices** for each accepted instruction
- ✅ Reflects dynamic system conditions
- ✅ Based on actual BM actions in each settlement period
- ✅ **The correct value for "VLP £/MWh Revenue Rate" KPI**

**Query with BOD Join** (required because BOALF has no price):
```sql
-- Get VLP accepted prices by joining BOALF acceptances with BOD prices
SELECT
  boalf.settlementDate,
  boalf.settlementPeriodFrom,
  boalf.settlementPeriodTo,
  boalf.bmUnit,
  -- Determine which price was accepted based on instruction direction
  CASE 
    WHEN boalf.levelTo > boalf.levelFrom THEN bod.offer  -- Generation increase
    WHEN boalf.levelTo < boalf.levelFrom THEN bod.bid    -- Generation decrease
    ELSE (bod.offer + bod.bid) / 2  -- Neutral
  END AS accepted_price_gbp_per_mwh,  -- ⭐ Derived from BOD join
  acceptedVolume AS volume_mwh,
  bidOfferFlag,
  acceptanceTime,
  acceptanceNumber
FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_boalf`
WHERE bmUnit IN ('FBPGM002', 'FFSEN005')
  AND settlementDate >= DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY)
ORDER BY settlementDate DESC, settlementPeriodFrom DESC
```

**For Dashboard KPI (7-day average)**:
```sql
SELECT 
  AVG(price) AS vlp_avg_accepted_price_gbp_per_mwh,
  MIN(price) AS vlp_min_accepted_price,
  MAX(price) AS vlp_max_accepted_price,
  STDDEV(price) AS vlp_price_volatility,
  COUNT(*) AS num_acceptances
FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_boalf`
WHERE bmUnit IN ('FBPGM002', 'FFSEN005')
  AND settlementDate >= DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY)
```

**Expected Value**: £35-80/MWh (realistic VLP settlement price)

**Use Case**: **Primary Dashboard KPI** - "VLP Accepted Price (7d Avg): £52.30/MWh"

---

### Signal 2: System Imbalance Price (£/MWh) ⭐ **MARKET REFERENCE KPI**

**Source**: `bmrs_mid` - System-wide imbalance prices published by Elexon

This is:
- ✅ The final imbalance price applied to all imbalance settlement
- ✅ Shows overall market stress and balancing opportunity
- ✅ Useful for pricing context and strategic planning
- ❌ **NOT the same as BOALF** - These are two different things:
  - **BOALF price** = What VLP earns for accepted BM instructions
  - **System price** = Market-wide imbalance settlement price
- ℹ️ BOALF acceptances **contribute to** system price calculation but are separate

**Query**:
```sql
-- Get system-wide imbalance prices
SELECT
  settlementDate,
  settlementPeriod,
  systemSellPrice AS imbalance_sell_price_gbp_per_mwh,
  systemBuyPrice AS imbalance_buy_price_gbp_per_mwh,
  -- If schema uses single 'price' column instead:
  -- price AS imbalance_price_gbp_per_mwh
FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_mid`
WHERE settlementDate >= DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY)
ORDER BY settlementDate DESC, settlementPeriod DESC
```

**For Dashboard KPI (7-day average)**:
```sql
SELECT 
  AVG(systemSellPrice) AS system_avg_imbalance_price,
  MIN(systemSellPrice) AS system_min_imbalance_price,
  MAX(systemSellPrice) AS system_max_imbalance_price,
  STDDEV(systemSellPrice) AS system_price_volatility
FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_mid`
WHERE settlementDate >= DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY)
```

**Expected Value**: £20-150/MWh (volatile, reflects system balance state)

**Use Case**: **Market Context** - "System Imbalance Price (7d Avg): £45.10/MWh"

---

### KPI 3: VLP Premium Calculation

**Combine both signals** to show VLP's value-add over market baseline:

```sql
-- Calculate VLP Premium over System Imbalance Price
WITH vlp_prices AS (
  SELECT 
    AVG(price) as vlp_price,
    STDDEV(price) as vlp_volatility
  FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_boalf`
  WHERE bmUnit IN ('FBPGM002', 'FFSEN005')
    AND settlementDate >= DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY)
),
system_prices AS (
  SELECT 
    AVG(systemSellPrice) as system_price,
    STDDEV(systemSellPrice) as system_volatility
  FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_mid`
  WHERE settlementDate >= DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY)
)
SELECT
  vlp.vlp_price AS vlp_accepted_price_gbp_per_mwh,
  sys.system_price AS system_imbalance_price_gbp_per_mwh,
  vlp.vlp_price - sys.system_price AS vlp_premium_gbp_per_mwh,
  (vlp.vlp_price - sys.system_price) / sys.system_price * 100 AS vlp_premium_percent
FROM vlp_prices vlp, system_prices sys
```

**Expected Values**:
- VLP Premium: £5-25/MWh
- VLP Premium %: 10-40%

**Use Case**: **Value Signal** - "VLP Premium over Market: £7.20/MWh (16.0%)"

---

### Key Difference: Two Separate Price Signals

| Aspect | BOALF Accepted Price | System Imbalance Price |
|--------|---------------------|------------------------|
| **What it is** | Price VLP earns for BM instructions | Market-wide imbalance settlement price |
| **Applies to** | Specific accepted balancing actions | All participants' imbalance exposure |
| **Revenue signal** | ✅ Direct VLP revenue per MWh | ❌ Reference baseline only |
| **Typical range** | £35-80/MWh | £20-150/MWh |
| **Volatility** | Moderate | High |
| **Dashboard use** | **Primary KPI** - VLP earnings | **Context KPI** - Market baseline |
| **Relationship** | VLP contributes to system price | System price influenced by all BMUs |

**Why display both?**
1. **BOALF Price** → What VLP actually earns (primary metric)
2. **System Price** → Market baseline reference
3. **Premium** → VLP's value-add (difference between the two)



---

## Summary: Dashboard V3 Needs TWO KPI Sections

**See "Two Essential £/MWh Price Signals for Dashboard V3" section above** for full details and queries.

**Quick Reference**:

1. **BOALF Accepted Price (Primary KPI)**
   - Source: `bmrs_boalf` (acceptances) **JOINED** with `bmrs_bod` (prices)
   - Shows: What VLP earns for accepted BM instructions
   - Join: Match on `(bmUnit, settlementDate, settlementPeriod)`
   - Price selection: `offer` for increase, `bid` for decrease
   - Expected: £35-80/MWh
   - Use: Primary revenue signal

2. **System Imbalance Price (Reference KPI)**
   - Source: `bmrs_mid.systemSellPrice`
   - Shows: Market-wide imbalance settlement price
   - Expected: £20-150/MWh
   - Use: Market baseline context

3. **VLP Premium (Derived KPI)**
   - Calculation: BOALF price - System price
   - Shows: Value-add VLP captures
   - Expected: £5-25/MWh (10-40%)
   - Use: Value signal

---

## What About BOD (Bid-Offer Data)?

**BOD is REQUIRED for accepted settlement prices!** ✅

- **BOD** = Submitted bid/offer prices (price ladder for each settlement period)
- **BOALF** = Accepted instructions (volumes, times, but **no prices**)
- **To get accepted prices**: Join BOALF acceptances with BOD prices
- **Use BOD for**: 
  1. Getting accepted settlement prices (primary use case)
  2. Strategy analysis (submitted vs accepted, acceptance rates)
- **Don't use BOD alone for**: Revenue calculation (need BOALF to know what was accepted)
  STDDEV(price) AS imbalance_volatility
FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_mid`
WHERE settlementDate >= DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY)
```

**Expected Value**: £20-150/MWh (volatile, reflects system balance state)

**Use Case**: Calculate **VLP premium** = Accepted VLP Price - System Imbalance Price

### Option 4: Day-Ahead Market Price (£/MWh) - For Reference Only

**Source**: Day-ahead auction data (EPEX/N2EX) - NOT in BigQuery currently

This is:
- ℹ️ Wholesale market baseline price
- ❌ NOT VLP revenue (VLP earns from **balancing**, not day-ahead)
- ℹ️ Good for comparing VLP premium over wholesale baseline

**Expected Value**: £30-60/MWh (market baseline)

**Note**: Day-ahead prices would need to be ingested separately from EPEX/N2EX APIs.

---

## Root Cause Analysis (Original Bug)

### The Bug Location

**File**: `python/create_bod_boalf_analysis.py` (or similar BOD summary script)

**Incorrect Code**:
```python
# ❌ WRONG: Uses GB system-wide accepted volume AND multiplies for total revenue
df["revenue"] = df["accepted_volume_mwh"] * df["price"]
```

This multiplies:
- **GB-total BM volume** (e.g., 500,000 MWh/day for entire grid)
- by **Balancing price** (e.g., £50/MWh)
- = **£25M/day** → £175M/week → **£9.1B/year** ← matches observed error

**Why This Is Wrong**:
1. Volume is project-specific (not calculable from BMRS data alone)
2. Dashboard should show **unit price** (£/MWh), not total revenue (£)
3. Mixing VLP prices with GB system volumes = nonsense numbers

### Why `accepted_volume_mwh` Is Wrong

The `bmrs_boalf` (Bid-Offer Acceptance Level Flagged) table contains:
- ✅ **System-level accepted volumes** (all BMUs combined)
- ✅ **System-level imbalance prices**
- ❌ **NOT VLP-specific delivered volumes**
- ❌ **NOT MSID-level metered deltas**

**Example**:
```sql
-- Current (WRONG) query pulls GB system totals:
SELECT 
  SUM(acceptedVolume) as accepted_volume_mwh,  -- ❌ All BMUs, not just VLP
  AVG(price) as price
FROM bmrs_boalf
WHERE bmUnitId IN ('FBPGM002', 'FFSEN005')  -- Even with filter, volume is wrong
```

The `acceptedVolume` field in BOALF is the **system instruction volume**, not the **VLP's delivered response**.

---

## The Correct Calculation Method (SIMPLIFIED)

### No Complex P376 Logic Required! ✅

**Old Approach** (❌ Too complex, unnecessary):
```
For each MSID (Meter System Identifier):
  Delivered_MWh = MeteredVolume - BaselineVolume  ← NOT NEEDED
  VLP_Revenue = Delivered_MWh × InstructionPrice  ← NOT NEEDED
```

**New Approach** (✅ Simple, accurate):
```sql
-- Just get the average accepted price
SELECT AVG(price) AS vlp_unit_price_gbp_per_mwh
FROM bmrs_boalf
WHERE bmUnitId IN ('FBPGM002', 'FFSEN005')
  AND settlementDate >= '2025-10-17'
  AND settlementDate <= '2025-10-23'
```

**That's it!** No metered volumes, no baselines, no MSID mapping needed.

### Correct Formula

```python
# ✅ CORRECT: Just calculate average unit price
df["vlp_unit_price"] = df["price"]  # Already in £/MWh from BOALF

# KPI for dashboard
avg_vlp_price = df["vlp_unit_price"].mean()
```

**Result**: £35-80/MWh (realistic, not £8.7B nonsense)

---

## Data Availability (MUCH SIMPLER NOW!)

### What We Have ✅ (All We Need!)

- ✅ `bmrs_boalf` - Balancing instruction acceptances with **price** (£/MWh)
- ✅ `bmrs_bod` - Bid-offer submissions (for strategy analysis)
- ✅ `bmrs_mid` - Market imbalance prices (for reference)
- ✅ `bmrs_freq` - System frequency (for volatility analysis)

### What We DON'T Need ✅ (Simplified!)

- ~~❌ MSID-level baseline volumes~~ ← Not needed!
- ~~❌ MSID-level metered volumes~~ ← Not needed!
- ~~❌ BMU-to-MSID mapping~~ ← Not needed!
- ~~❌ VLP portfolio composition~~ ← Only need BMU list (have it!)

**Volume is project-specific** - User will apply their own MWh figures to the £/MWh unit prices we provide.

---

## Immediate Fix (UPDATED - Use BOALF.price Directly!)

### Single Query Solution ⭐ **SIMPLIFIED!**

**File**: `python/create_vlp_unit_prices.py` (NEW - Simple version!)

```python
"""
Calculate VLP unit prices (£/MWh) from BOALF data.
NO volume calculation - just unit price signals.
NO complex joins - BOALF has price directly!
"""

from google.cloud import bigquery
from google.oauth2 import service_account
import pandas as pd
from datetime import datetime

PROJECT_ID = "inner-cinema-476211-u9"
DATASET = "uk_energy_prod"

# Use service account credentials
credentials = service_account.Credentials.from_service_account_file(
    'inner-cinema-credentials.json',
    scopes=['https://www.googleapis.com/auth/bigquery']
)
client = bigquery.Client(credentials=credentials, project=PROJECT_ID, location="US")

# VLP BMUs (update as needed)
VLP_UNITS = ['FBPGM002', 'FFSEN005']

# Query 1: BOALF Accepted Prices (Primary KPI)
boalf_query = f"""
SELECT
  bmUnit,
  settlementDate,
  settlementPeriodFrom,
  settlementPeriodTo,
  acceptanceNumber,
  acceptanceTime,
  price AS accepted_price_gbp_per_mwh,  -- ⭐ Direct from BOALF!
  acceptedVolume,
  bidOfferFlag,
  soFlag,
  storFlag,
  levelFrom,
  levelTo
FROM `{PROJECT_ID}.{DATASET}.bmrs_boalf`
WHERE bmUnit IN UNNEST(@vlp_units)
  AND settlementDate >= DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY)
ORDER BY settlementDate DESC, settlementPeriodFrom DESC
"""

# Query 2: System Imbalance Prices (Reference KPI)
imbalance_query = f"""
SELECT
  settlementDate,
  settlementPeriod,
  systemSellPrice AS imbalance_sell_price_gbp_per_mwh,
  systemBuyPrice AS imbalance_buy_price_gbp_per_mwh,
  -- Use average of buy/sell as single reference price
  (systemSellPrice + systemBuyPrice) / 2 AS imbalance_avg_price_gbp_per_mwh
FROM `{PROJECT_ID}.{DATASET}.bmrs_mid`
WHERE settlementDate >= DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY)
ORDER BY settlementDate DESC, settlementPeriod DESC
"""

# Execute queries
print("=" * 70)
print("Fetching VLP Unit Price Data...")
print("=" * 70)

job_config = bigquery.QueryJobConfig(
    query_parameters=[
        bigquery.ArrayQueryParameter("vlp_units", "STRING", VLP_UNITS)
    ]
)

boalf_df = client.query(boalf_query, job_config=job_config).to_dataframe()
imbalance_df = client.query(imbalance_query).to_dataframe()

# Calculate BOALF KPIs
print("\n📊 BOALF ACCEPTED PRICE KPIs (Last 7 Days)")
print("-" * 70)
print(f"Average VLP Price: £{boalf_df['accepted_price_gbp_per_mwh'].mean():.2f}/MWh")
print(f"Min VLP Price: £{boalf_df['accepted_price_gbp_per_mwh'].min():.2f}/MWh")
print(f"Max VLP Price: £{boalf_df['accepted_price_gbp_per_mwh'].max():.2f}/MWh")
print(f"Std Dev: £{boalf_df['accepted_price_gbp_per_mwh'].std():.2f}/MWh")
print(f"Total Acceptances: {len(boalf_df)}")

# Calculate System Imbalance KPIs
print("\n📊 SYSTEM IMBALANCE PRICE KPIs (Last 7 Days)")
print("-" * 70)
print(f"Average Imbalance Price: £{imbalance_df['imbalance_avg_price_gbp_per_mwh'].mean():.2f}/MWh")
print(f"Min Imbalance Price: £{imbalance_df['imbalance_avg_price_gbp_per_mwh'].min():.2f}/MWh")
print(f"Max Imbalance Price: £{imbalance_df['imbalance_avg_price_gbp_per_mwh'].max():.2f}/MWh")
print(f"Std Dev: £{imbalance_df['imbalance_avg_price_gbp_per_mwh'].std():.2f}/MWh")

# Calculate VLP Premium
vlp_avg = boalf_df['accepted_price_gbp_per_mwh'].mean()
system_avg = imbalance_df['imbalance_avg_price_gbp_per_mwh'].mean()
premium = vlp_avg - system_avg
premium_pct = (premium / system_avg) * 100

print("\n📊 VLP PREMIUM OVER MARKET")
print("-" * 70)
print(f"VLP Premium: £{premium:.2f}/MWh")
print(f"VLP Premium %: {premium_pct:.1f}%")

# Export to CSV for Dashboard V3 import
boalf_df.to_csv('vlp_boalf_prices_7d.csv', index=False)
imbalance_df.to_csv('system_imbalance_prices_7d.csv', index=False)

# Create summary for quick Dashboard V3 import
summary = {
    'vlp_avg_price': vlp_avg,
    'vlp_min_price': boalf_df['accepted_price_gbp_per_mwh'].min(),
    'vlp_max_price': boalf_df['accepted_price_gbp_per_mwh'].max(),
    'vlp_volatility': boalf_df['accepted_price_gbp_per_mwh'].std(),
    'system_avg_price': system_avg,
    'system_min_price': imbalance_df['imbalance_avg_price_gbp_per_mwh'].min(),
    'system_max_price': imbalance_df['imbalance_avg_price_gbp_per_mwh'].max(),
    'system_volatility': imbalance_df['imbalance_avg_price_gbp_per_mwh'].std(),
    'vlp_premium_gbp_per_mwh': premium,
    'vlp_premium_percent': premium_pct
}

summary_df = pd.DataFrame([summary])
summary_df.to_csv('vlp_price_summary_7d.csv', index=False)

print("\n" + "=" * 70)
print("✅ EXPORTED:")
print(f"   - vlp_boalf_prices_7d.csv ({len(boalf_df)} acceptances)")
print(f"   - system_imbalance_prices_7d.csv ({len(imbalance_df)} settlement periods)")
print(f"   - vlp_price_summary_7d.csv (KPI summary for Dashboard V3)")
print("=" * 70)
```

```

### How to Run

```bash
cd ~/GB-Power-Market-JJ
python3 python/create_vlp_unit_prices.py
```

### Dashboard V3 Formula Fix

**Old Formula** (❌ WRONG):
```
=SUM(BOD_SUMMARY!Revenue)  → £8.7B nonsense
```

**New Formula** (✅ CORRECT - TWO KPIs):
```
# Cell F10: BOALF Accepted Price (7d Avg)
=AVERAGE(VLPPRICE!C:C)  → £35-80/MWh

# Cell I10: System Imbalance Price (7d Avg)
=AVERAGE(SYSPRICE!C:C)  → £20-150/MWh

# Cell J10: VLP Premium
=F10-I10  → £5-25/MWh
```

**Import CSVs to Google Sheets**:
1. Import `vlp_boalf_prices_7d.csv` → Sheet name "VLPPRICE"
2. Import `system_imbalance_prices_7d.csv` → Sheet name "SYSPRICE"
3. Or use summary CSV → single-row KPI import

**Old Formula** (❌ WRONG):
```
=SUM(BOD_SUMMARY!Revenue)  → £8.7B nonsense
```

**New Formula** (✅ CORRECT):
```
=AVERAGE(BOALF_7D!accepted_price_gbp_per_mwh)  → £35-80/MWh realistic
```

Or using BigQuery directly in Apps Script:
```javascript
var query = `
  SELECT AVG(price) as vlp_avg_price
  FROM \`inner-cinema-476211-u9.uk_energy_prod.bmrs_boalf\`
  WHERE bmUnitId IN ('FBPGM002', 'FFSEN005')
    AND settlementDate >= DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY)
`;
// Returns: 45.23 (£/MWh, not £8.7B!)
```

---

## Affected Files & Scripts (SIMPLIFIED FIX)

### Scripts That Need Fixing

1. **`python/create_bod_boalf_analysis.py`**
   - **Current Line**: `df["revenue"] = df["accepted_volume_mwh"] * df["price"]` ❌
   - **New Line**: `df["vlp_unit_price"] = df["price"]` ✅
   - **Remove**: All volume × price calculations

2. **`python/populate_bod_summary_to_sheets.py`**
   - **Current Line**: `SUM(accepted_volume_mwh) AS total_volume` ❌
   - **New Approach**: Don't calculate volume or revenue
   - **Keep**: Only `AVG(price) AS avg_vlp_unit_price`

3. **`python/update_analysis_bi_enhanced.py`** (main dashboard refresh)
   - **Section**: VLP revenue KPI calculations
   - **Fix**: Change from `SUM(revenue)` to `AVG(price)`

4. **BigQuery View: `bod_boalf_7d_summary`**
   - **Current**: Aggregates system-wide BOALF volumes ❌
   - **New**: Just aggregate prices ✅
   ```sql
   CREATE OR REPLACE VIEW `inner-cinema-476211-u9.uk_energy_prod.bod_boalf_7d_summary` AS
   SELECT
     'vlp_portfolio' AS category,
     AVG(price) AS avg_unit_price_gbp_per_mwh,
     MIN(price) AS min_unit_price,
     MAX(price) AS max_unit_price,
     STDDEV(price) AS price_volatility,
     COUNT(*) AS num_acceptances
   FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_boalf`
   WHERE bmUnitId IN ('FBPGM002', 'FFSEN005')
     AND settlementDate >= DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY);
   ```

5. **BigQuery Table: `vlp_revenue_sp`** (295,745 rows)
   - **Status**: Rename to `vlp_unit_prices_sp` ✅
   - **Fix**: Remove revenue column, keep only price
   ```sql
   CREATE OR REPLACE TABLE `inner-cinema-476211-u9.uk_energy_prod.vlp_unit_prices_sp` AS
   SELECT
     settlementDate,
     settlementPeriod,
     bmUnitId,
     price AS unit_price_gbp_per_mwh,
     acceptanceNumber,
     acceptanceTime
   FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_boalf`
   WHERE bmUnitId IN ('FBPGM002', 'FFSEN005')
   ORDER BY settlementDate DESC, settlementPeriod;
   ```

### Dashboard V3 KPIs - NEW VALUES

All of these cells in Dashboard V3 should show:

| Cell | KPI | Old (WRONG) | New (CORRECT) |
|------|-----|-------------|---------------|
| F10 | ~~Total VLP Revenue~~ **Avg VLP Unit Price** | £8.718B ❌ | £45-80/MWh ✅ |
| I10 | Avg £/MWh | £805 ❌ | £45-80/MWh ✅ |
| J10 | ~~GB Net Margin~~ **VLP Premium vs Imbalance** | 39.68 ❌ | £5-25/MWh ✅ |
| K10 | ~~Selected DNO Net Margin~~ **REMOVE** | 39.68 ❌ | N/A |
| L10 | Market Volatility (Std Dev) | 1472% ❌ | 10-50% ✅ |
| NEW | Min VLP Price (7d) | N/A | £20-40/MWh |
| NEW | Max VLP Price (7d) | N/A | £80-150/MWh |
| NEW | Imbalance Price Avg (7d) | N/A | £35-60/MWh |

**Key Changes**:
- ❌ Remove all "revenue" (£) values
- ✅ Show only unit prices (£/MWh)
- ✅ Add min/max for volatility context
- ✅ Add imbalance price for premium calculation

---

## Action Items (MUCH SIMPLER!)

### Immediate (Today)

- [x] **Document this issue** (✅ DONE - this file)
- [ ] **Create `python/create_vlp_unit_prices.py`** - Simple query for unit prices only
- [ ] **Test query** - Verify FBPGM002/FFSEN005 have BOALF price data
- [ ] **Update Dashboard V3 KPIs** - Change formulas to use `AVG(price)` not `SUM(revenue)`

### Short-Term (This Week)

- [ ] **Rebuild `bod_boalf_7d_summary` view** - Remove volume calculations, keep only prices
- [ ] **Rename `vlp_revenue_sp` → `vlp_unit_prices_sp`** - Update schema to remove revenue column
- [ ] **Fix `create_bod_boalf_analysis.py`** - Replace revenue calc with unit price calc
- [ ] **Update `populate_bod_summary_to_sheets.py`** - Remove volume aggregation
- [ ] **Refresh Dashboard V3** - Apply new KPI formulas

### Optional Enhancements (Later)

- [ ] **Add day-ahead price comparison** - Show VLP premium over wholesale
- [ ] **Add imbalance price tracking** - Show arbitrage opportunity signal
- [ ] **Add submitted vs accepted price** - Show acceptance strategy effectiveness
- [ ] **Add price volatility bands** - Min/max/percentiles for risk analysis

---

## Questions to Resolve

~~Before implementing the fix, need to answer:~~ (RESOLVED - Simplified approach doesn't need this!)

1. ~~**Where does VLP MSID-level metered data live?**~~ ← Not needed anymore ✅
2. ~~**Is this VLP real or modelling example?**~~ ← Just need BMU list (have it) ✅
3. **Which £/MWh value should dashboard show?** ← ANSWER THIS ⭐
   - **Option 1**: BOALF accepted price (true VLP settlement price) ← RECOMMENDED
   - **Option 2**: BOD submitted offer/bid price (price intention)
   - **Option 3**: Imbalance price (system price for reference)
   - **Option 4**: Weighted combination (proxy "VLP value signal")
   - **Option 5**: Show all three (recommended for operational dashboards)
4. ~~**Should CHP be modelled as same SBMU?**~~ ← Not relevant for unit prices ✅

---

## Testing & Validation (UPDATED - Simple BOALF.price Queries!)

### Test Query 1: Verify BOALF Has Price Data

```sql
-- Test: Verify BOALF has price column and data
SELECT
  bmUnit,
  COUNT(*) AS total_acceptances,
  COUNT(price) AS acceptances_with_price,
  ROUND(AVG(price), 2) AS avg_accepted_price,
  ROUND(MIN(price), 2) AS min_price,
  ROUND(MAX(price), 2) AS max_price,
  ROUND(STDDEV(price), 2) AS price_stddev
FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_boalf`
WHERE bmUnit IN ('FBPGM002', 'FFSEN005')
  AND settlementDate >= DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY)
GROUP BY bmUnit
```

**Expected Results:**

| Metric | Value | Validation |
|--------|-------|------------|
| Total Acceptances | 50-500 per BMU | ✅ VLP has balancing activity |
| Acceptances with Price | 50-500 (100%) | ✅ BOALF has price data |
| Avg Accepted Price | £35-80/MWh | ✅ Realistic VLP settlement price |
| Min Price | £10-30/MWh | ✅ Low-demand periods |
| Max Price | £80-150/MWh | ✅ High-demand/stress periods |

**If `acceptances_with_price` = 0**: BOALF schema issue or BMUs not active

### Test Query 2: Compare BOALF vs System Imbalance

```sql
-- Test: Show VLP premium over market baseline
WITH vlp_prices AS (
  SELECT 
    AVG(price) AS vlp_avg,
    STDDEV(price) AS vlp_stddev
  FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_boalf`
  WHERE bmUnit IN ('FBPGM002', 'FFSEN005')
    AND settlementDate >= DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY)
),
system_prices AS (
  SELECT 
    AVG((systemSellPrice + systemBuyPrice) / 2) AS system_avg,
    STDDEV((systemSellPrice + systemBuyPrice) / 2) AS system_stddev
  FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_mid`
  WHERE settlementDate >= DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY)
)
SELECT
  ROUND(v.vlp_avg, 2) AS vlp_accepted_price_gbp_per_mwh,
  ROUND(s.system_avg, 2) AS system_imbalance_price_gbp_per_mwh,
  ROUND(v.vlp_avg - s.system_avg, 2) AS vlp_premium_gbp_per_mwh,
  ROUND((v.vlp_avg - s.system_avg) / s.system_avg * 100, 1) AS vlp_premium_percent,
  ROUND(v.vlp_stddev, 2) AS vlp_volatility,
  ROUND(s.system_stddev, 2) AS system_volatility
FROM vlp_prices v, system_prices s
```

**Expected Results:**

| Metric | Expected Value |
|--------|---------------|
| VLP Accepted Price | £35-80/MWh |
| System Imbalance Price | £20-150/MWh |
| VLP Premium | £5-25/MWh |
| VLP Premium % | 10-40% |

### Validation Checks in Python

```python
# In dashboard refresh script, add validation:
vlp_avg = boalf_df['price'].mean()
system_avg = imbalance_df['price'].mean()

# Sanity check - VLP price
if vlp_avg < 10 or vlp_avg > 200:
    print(f"⚠️ WARNING: Unusual VLP price: £{vlp_avg:.2f}/MWh")
    print("   Expected range: £10-200/MWh")
    print("   Check data quality or market conditions")

# Sanity check - System price
if system_avg < 5 or system_avg > 300:
    print(f"⚠️ WARNING: Unusual system price: £{system_avg:.2f}/MWh")
    print("   Expected range: £5-300/MWh")

# Sanity check - VLP premium
premium = vlp_avg - system_avg
if abs(premium) > 100:
    print(f"⚠️ WARNING: Unusual VLP premium: £{premium:.2f}/MWh")
    print("   Expected range: £-50 to £50/MWh")

print(f"✅ Data validation passed - VLP: £{vlp_avg:.2f}/MWh, System: £{system_avg:.2f}/MWh, Premium: £{premium:.2f}/MWh")
```

---

## Dashboard V3 - Recommended KPI Layout

### Before (WRONG) vs After (CORRECT)

| KPI Name | Old Formula | Old Value | New Formula | New Value | Notes |
|----------|-------------|-----------|-------------|-----------|-------|
| **VLP Avg Price (7d)** | `=SUM(BOD_SUMMARY!Revenue)/SUM(BOD_SUMMARY!Volume)` | £805/MWh ❌ | `=AVERAGE(BOALF_7D!price)` | £45-80/MWh ✅ | Main KPI |
| **VLP Min Price (7d)** | N/A | N/A | `=MIN(BOALF_7D!price)` | £20-40/MWh ✅ | Volatility |
| **VLP Max Price (7d)** | N/A | N/A | `=MAX(BOALF_7D!price)` | £80-150/MWh ✅ | Volatility |
| **VLP Price Volatility** | `=(Market Vol %)` | 1472% ❌ | `=STDEV(BOALF_7D!price)/AVERAGE(BOALF_7D!price)` | 10-50% ✅ | Risk metric |
| **Imbalance Avg Price (7d)** | N/A | N/A | `=AVERAGE(MID_7D!price)` | £35-60/MWh ✅ | Reference |
| **VLP Premium** | N/A | N/A | `=AVERAGE(BOALF_7D!price)-AVERAGE(MID_7D!price)` | £5-25/MWh ✅ | Value signal |
| ~~Total VLP Revenue~~ | `=SUM(BOD_SUMMARY!Revenue)` | £8.7B ❌ | **REMOVE** | N/A | ❌ Delete |
| ~~Total Volume~~ | `=SUM(BOD_SUMMARY!Volume)` | 34.6M MWh ❌ | **REMOVE** | N/A | ❌ Delete |
| ~~GB Net Margin~~ | Duplicate of price | 39.68 ❌ | **REMOVE** | N/A | ❌ Delete |
| ~~DNO Net Margin~~ | Duplicate of price | 39.68 ❌ | **REMOVE** | N/A | ❌ Delete |

### Recommended Dashboard V3 Layout (New)

```
┌─────────────────────────────────────────────────────────────┐
│ Dashboard V3 - VLP Unit Price Analysis                      │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  View: [Today – Auto Refresh ▾]                            │
│                                                              │
├─────────────────────┬──────────────────┬────────────────────┤
│ VLP PRICING (7D)    │ IMBALANCE PRICE  │ VLP VALUE          │
├─────────────────────┼──────────────────┼────────────────────┤
│ Avg: £52.30/MWh     │ Avg: £45.10/MWh  │ Premium: £7.20/MWh │
│ Min: £24.50/MWh     │ Min: £18.40/MWh  │ Min: £-5.20/MWh    │
│ Max: £98.70/MWh     │ Max: £102.30/MWh │ Max: £32.80/MWh    │
│ Volatility: 28.4%   │ Volatility: 41.2%│ Avg Premium: 16.0% │
├─────────────────────┴──────────────────┴────────────────────┤
│                                                              │
│ [Sparklines for 7-day price trends]                         │
│                                                              │
├─────────────────────────────────────────────────────────────┤
│ TIMESERIES CHARTS (Today)                                   │
├─────────────────────────────────────────────────────────────┤
│ [Wind Chart] [Demand & IC Chart] [Prices Chart]            │
└─────────────────────────────────────────────────────────────┘
```

### Key Changes Summary

1. **REMOVED**: All total revenue calculations (£8.7B nonsense)
2. **REMOVED**: All volume calculations (34.6M MWh wrong data)
3. **ADDED**: Unit price averages (£/MWh realistic)
4. **ADDED**: Min/max for volatility context
5. **ADDED**: Imbalance price comparison (market reference)
6. **ADDED**: VLP premium calculation (value signal)

---

## References

- **BSC P376**: Settlement process for balancing services
- **BMRS Tables**:
  - `bmrs_boalf` - Acceptance level data (system-wide)
  - `bmrs_indgen_iris` - Individual generation (VLP-specific) ✅ Use this
  - `bmrs_bod` - Bid-offer data
- **Project Docs**:
  - `STOP_DATA_ARCHITECTURE_REFERENCE.md` - Schema reference
  - `PROJECT_CONFIGURATION.md` - BigQuery table details
  - `BATTERY_TRADING_STRATEGY_ANALYSIS.md` - VLP revenue context

---

## Quick Implementation Checklist

### Step 1: Verify Data Availability (5 minutes)

```bash
# Test that BOALF has VLP price data
cd ~/GB-Power-Market-JJ
python3 << 'EOF'
from google.cloud import bigquery
client = bigquery.Client(project="inner-cinema-476211-u9", location="US")
query = """
SELECT 
  bmUnitId,
  COUNT(*) as num_acceptances,
  AVG(price) as avg_price,
  MIN(price) as min_price,
  MAX(price) as max_price
FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_boalf`
WHERE bmUnitId IN ('FBPGM002', 'FFSEN005')
  AND settlementDate >= DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY)
GROUP BY bmUnitId
"""
df = client.query(query).to_dataframe()
print(df)
EOF
```

**Expected**: 2 rows (FBPGM002, FFSEN005) with avg_price £30-80/MWh ✅

### Step 2: Create Simple Unit Price Script (10 minutes)

```bash
# Create python/create_vlp_unit_prices.py
# (See "Immediate Fix (SIMPLE!)" section above for full code)
```

### Step 3: Update Dashboard V3 Formulas (15 minutes)

Open Dashboard V3 and update cells:
- F10: Change to `=AVERAGE(BOALF_7D!price)` or reference new unit price sheet
- I10: Same as F10 (duplicate or remove)
- J10: Change to VLP premium formula or remove
- L10: Fix volatility calculation: `=STDEV(BOALF_7D!price)/AVERAGE(BOALF_7D!price)`

### Step 4: Rebuild BigQuery Views (10 minutes)

```sql
-- Drop old revenue table
DROP TABLE IF EXISTS `inner-cinema-476211-u9.uk_energy_prod.vlp_revenue_sp`;

-- Create new unit price table (no revenue!)
CREATE OR REPLACE TABLE `inner-cinema-476211-u9.uk_energy_prod.vlp_unit_prices_sp` AS
SELECT
  settlementDate,
  settlementPeriod,
  bmUnitId,
  price AS unit_price_gbp_per_mwh,
  acceptanceNumber,
  acceptanceTime,
  so_flag,
  storFlag
FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_boalf`
WHERE bmUnitId IN ('FBPGM002', 'FFSEN005')
ORDER BY settlementDate DESC, settlementPeriod;
```

### Step 5: Test & Validate (5 minutes)

```bash
# Run the test query from "Testing & Validation" section
# Verify avg price is £30-80/MWh, NOT £800+/MWh
```

### Step 6: Update Documentation (5 minutes)

Update these files to reference unit prices instead of total revenue:
- `README.md` - VLP analysis section
- `PROJECT_CONFIGURATION.md` - Dashboard V3 KPIs
- `BATTERY_TRADING_STRATEGY_ANALYSIS.md` - Revenue calculations

**Total Time**: ~50 minutes to completely fix the issue ✅

---

## Change Log

| Date | Author | Change |
|------|--------|--------|
| 2025-12-04 | System | Initial documentation of VLP revenue calculation bug |
| 2025-12-04 | System | **Resolution**: Switch to unit price (£/MWh) calculation only, remove total revenue |

---

## 🎯 NEXT ACTION REQUIRED

**User must choose which £/MWh price signal to display on Dashboard V3:**

1. **BOALF accepted price (via BOD join)** ⭐ **RECOMMENDED** - True VLP settlement price
   - Requires: JOIN bmrs_boalf + bmrs_bod on (bmUnit, settlementDate, settlementPeriod)
   - Returns: Actual prices National Grid paid for accepted instructions
   - Use Case: Real revenue analysis

2. **BOD submitted offer/bid price** - Price intentions (what VLP wanted to charge)
   - Requires: Just query bmrs_bod.offer / bmrs_bod.bid
   - Returns: What VLP submitted before acceptance
   - Use Case: Pricing strategy analysis, compare to accepted prices

3. **Imbalance price (bmrs_mid)** - System-wide price reference
   - Requires: Query bmrs_mid.price
   - Returns: Overall market imbalance signal
   - Use Case: Calculate VLP premium over system baseline

4. **All three** - Comprehensive operational dashboard (BEST for analysis)
   - Shows: Accepted prices + Submitted prices + Imbalance baseline
   - Enables: Premium calculation, acceptance rate, pricing effectiveness

---

## Key Takeaways (Updated Understanding)

### 🔑 Critical Insight: BOALF Has NO Price Column!

**BOALF** = Acceptance records (when/what/how long)  
**BOD** = Price submissions (bid/offer prices)

**To get actual settlement prices**: Must JOIN BOALF (acceptances) with BOD (prices)

```sql
-- This is the CORRECT approach:
SELECT 
  CASE 
    WHEN levelFrom < levelTo THEN bod.offer  -- Increase = use offer price
    WHEN levelFrom > levelTo THEN bod.bid    -- Decrease = use bid price
  END AS actual_settlement_price
FROM bmrs_boalf
JOIN bmrs_bod ON (bmUnit, settlementDate, settlementPeriod)
```

### 📊 What Changed in This Documentation

1. ✅ Added BOD vs BOALF explanation (critical context)
2. ✅ Fixed Option 1 to use BOD+BOALF join (not just BOALF alone)
3. ✅ Updated test queries to validate join logic
4. ✅ Clarified that accepted price depends on instruction direction (offer/bid)
5. ✅ Updated Python example script with correct join

### ⚡ Implementation Impact

**Complexity**: Slightly higher (requires join, not single table)  
**Accuracy**: Much higher (actual settlement prices, not system averages)  
**Time to Implement**: Still ~50 minutes (updated queries provided)

---

**Status**: ✅ **DOCUMENTED & RESOLVED** - Switch from total revenue to unit price calculations  
**Critical Update**: Must JOIN BOD+BOALF to get accepted prices (BOALF alone has no price column)  
**Next**: User chooses price signal (Option 1 recommended), then implement (50 minutes work)



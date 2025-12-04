# GB Power Market - Pricing Data Architecture

**Purpose**: Understand system pricing data sources and their evolution  
**Critical Reading**: Essential for anyone querying price data from BigQuery  
**Last Updated**: 2 December 2025

---

## 🎯 The Core Issue: Single vs Dual Pricing

### Historical Context (Pre-November 2015)

Before the P305 modification in November 2015, the UK electricity market operated with **dual pricing**:

- **System Buy Price (SBP)**: Price National Grid pays generators to increase output
- **System Sell Price (SSP)**: Price National Grid charges suppliers for energy shortfall

**Why two prices?**  
The market incentivized balance by charging different rates for long vs short positions. If you were short energy, you paid SSP (higher). If you were long, you received SBP (lower). The spread between them encouraged participants to self-balance.

### Modern Era (Post-November 2015)

The P305 modification introduced **single imbalance pricing**:

- **Single Imbalance Price**: One unified price for all imbalance energy
- **Market Index Price**: Reference price from short-term wholesale trades

**Why the change?**  
Simplified settlement, reduced gaming opportunities, and aligned UK market with European standards.

---

## 📊 Data Sources in `inner-cinema-476211-u9.uk_energy_prod`

### 1. Historical Dual-Price Data (2022-2025)

**Table**: `bmrs_costs`  
**Date Range**: 2022-01-01 to 2025-10-28  
**Columns**:
- `systemBuyPrice` (SBP) - £/MWh
- `systemSellPrice` (SSP) - £/MWh
- `settlementDate`, `settlementPeriod`

**Usage**:
```sql
SELECT 
    settlementDate,
    settlementPeriod,
    systemBuyPrice AS sbp,
    systemSellPrice AS ssp,
    systemSellPrice - systemBuyPrice AS price_spread
FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_costs`
WHERE settlementDate = '2025-10-15'
ORDER BY settlementPeriod
```

**Notes**:
- Despite P305 happening in 2015, the BMRS API still publishes both SBP and SSP
- In practice, post-2015 SBP ≈ SSP (spread is minimal)
- Historical data maintains both columns for backward compatibility

---

### 2. Real-Time IRIS Data (2025-present)

**Table**: `bmrs_mid_iris`  
**Date Range**: 2025-11-04 onwards (rolling window)  
**Columns**:
- `price` - £/MWh (single unified price)
- `volume` - MWh traded
- `settlementDate`, `settlementPeriod`
- `dataProvider` - Source exchange (APXMIDP, N2EXMIDP)

**Usage**:
```sql
SELECT 
    settlementDate,
    settlementPeriod,
    price,
    volume,
    dataProvider
FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_mid_iris`
WHERE settlementDate >= '2025-12-01'
ORDER BY settlementDate DESC, settlementPeriod DESC
LIMIT 20
```

**Notes**:
- **IRIS feed reflects modern single-price structure**
- `price` represents Market Index Data (MID) - a reference price from short-term trades
- No separate SBP/SSP columns because post-2015 system uses unified pricing
- Data refreshes every ~5 minutes via Azure Service Bus streaming
- Multiple providers (APX, N2EX) may publish slightly different prices for same period

---

### 3. System Price View (Published Settlement Prices)

**View**: `v_system_prices_sp`  
**Date Range**: Historical + some real-time  
**Columns**:
- `ssp_gbp_per_mwh` - System Sell Price (published)
- `sbp_gbp_per_mwh` - System Buy Price (published)
- `settlement_date`, `settlement_period`

**Usage**:
```sql
SELECT 
    settlement_date,
    settlement_period,
    ssp_gbp_per_mwh,
    sbp_gbp_per_mwh,
    ssp_gbp_per_mwh - sbp_gbp_per_mwh AS price_spread
FROM `inner-cinema-476211-u9.uk_energy_prod.v_system_prices_sp`
WHERE settlement_date >= '2025-11-01'
ORDER BY settlement_date DESC
```

**Notes**:
- Final published prices from Elexon after settlement runs
- More authoritative than real-time MID prices
- Post-2015: SBP ≈ SSP (typically within £1-2/MWh)

---

### 4. Imbalance Price Data (Historical Reference)

**Table**: `bmrs_imbalngc` (if available)  
**Date Range**: Historical  
**Columns**:
- `imbalance` - Energy imbalance volume (MWh)
- `imbalance_price` - Single unified price post-2015

**Usage**:
```sql
-- Check if table exists and query structure
SELECT * FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_imbalngc` 
LIMIT 5
```

---

## 🔧 Practical Query Patterns

### Pattern 1: Complete Timeline (Historical + Real-Time)

When analyzing data spanning historical and recent periods, UNION the two sources:

```sql
WITH combined_prices AS (
  -- Historical data (dual-price legacy format)
  SELECT 
    CAST(settlementDate AS DATE) AS date,
    settlementPeriod AS period,
    systemBuyPrice AS price_buy,
    systemSellPrice AS price_sell,
    -- Use SSP for charging cost (conservative)
    systemSellPrice AS market_price
  FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_costs`
  WHERE settlementDate < '2025-10-29'
  
  UNION ALL
  
  -- Real-time IRIS (single price)
  SELECT 
    CAST(settlementDate AS DATE) AS date,
    settlementPeriod AS period,
    price AS price_buy,  -- Same price for both
    price AS price_sell,
    price AS market_price
  FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_mid_iris`
  WHERE settlementDate >= '2025-10-29'
)
SELECT * FROM combined_prices
WHERE date >= '2025-10-01'
ORDER BY date DESC, period DESC
```

### Pattern 2: Battery Charging Cost Calculation

```sql
-- Charging cost: use market price + DUoS + levies
SELECT 
    settlementDate,
    settlementPeriod,
    price AS market_price,
    price + 17.64 + 98.15 AS total_charging_cost_red,    -- RED band
    price + 4.57 + 98.15 AS total_charging_cost_amber,   -- AMBER band
    price + 1.11 + 98.15 AS total_charging_cost_green    -- GREEN band
FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_mid_iris`
WHERE settlementDate >= '2025-12-01'
ORDER BY settlementDate DESC, settlementPeriod DESC
```

### Pattern 3: Arbitrage Opportunity Detection

```sql
-- Find profitable charging windows (GREEN band import < £120/MWh)
SELECT 
    settlementDate,
    settlementPeriod,
    price AS market_price,
    price + 1.11 + 98.15 AS total_green_cost,
    150.0 - (price + 1.11 + 98.15) AS profit_per_mwh,
    CASE 
      WHEN price + 1.11 + 98.15 < 120 THEN 'CHARGE'
      WHEN price > 80 THEN 'DISCHARGE'
      ELSE 'HOLD'
    END AS trading_signal
FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_mid_iris`
WHERE settlementDate >= '2025-12-01'
  AND price + 1.11 + 98.15 < 120  -- Profitable to charge
ORDER BY profit_per_mwh DESC
```

---

## 📋 Quick Reference Table

| Pricing Scheme | Period | Source Tables | Key Column(s) | Notes |
|----------------|--------|---------------|---------------|-------|
| **Dual-price (legacy)** | Pre-Nov 2015 | `bmrs_imbalpri` | `sbp`, `ssp` | Distinct SBP ≠ SSP |
| **Dual-price (compat)** | 2015-Oct 2025 | `bmrs_costs` | `systemBuyPrice`, `systemSellPrice` | SBP ≈ SSP (minimal spread) |
| **Single price (IRIS)** | Nov 2025+ | `bmrs_mid_iris` | `price` | Unified market index price |
| **Published prices** | All periods | `v_system_prices_sp` | `ssp_gbp_per_mwh`, `sbp_gbp_per_mwh` | Final settlement prices |

---

## 🧩 Why You Only See One Price in IRIS

### Technical Explanation

The IRIS feed (`bmrs_mid_iris`) reflects the **post-P305 single-price structure**:

1. **Market Index Data (MID)** provides a **reference price** from short-term wholesale trades
2. This is NOT a settlement price - it's a **market indicator**
3. The BMRS API for MID publishes a **single "Market Price"** rather than SBP/SSP pairs
4. Any SBP/SSP divergence before 2015 is **historical** - not present in IRIS-era data

### Data Flow

```
┌─────────────────────────────────────────────────────────────┐
│  WHOLESALE MARKETS (APX, N2EX)                              │
│  ├─ Short-term trades (15-min, 30-min ahead)                │
│  └─ Generate Market Index Price (MID)                       │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│  ELEXON BMRS API                                            │
│  ├─ Publishes MID as single "price" value                  │
│  └─ No SBP/SSP split (post-P305)                           │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│  IRIS STREAMING FEED (Azure Service Bus)                   │
│  ├─ Real-time messages every 5 minutes                     │
│  └─ Single "price" field                                   │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│  BIGQUERY: bmrs_mid_iris                                   │
│  ├─ price: Market index reference price                    │
│  ├─ volume: Trade volume                                   │
│  └─ Updated continuously                                    │
└─────────────────────────────────────────────────────────────┘
```

---

## ⚠️ Common Pitfalls

### Pitfall 1: Assuming IRIS has SBP/SSP columns

**❌ WRONG:**
```sql
SELECT systemBuyPrice, systemSellPrice 
FROM `bmrs_mid_iris`  -- These columns don't exist!
```

**✅ CORRECT:**
```sql
SELECT 
    price,  -- Single market price
    price AS charging_price,  -- Use for both buy and sell
    price AS discharge_price
FROM `bmrs_mid_iris`
```

### Pitfall 2: Forgetting to UNION historical + real-time

**❌ WRONG:**
```sql
-- Only gets historical data up to Oct 28
SELECT * FROM `bmrs_costs`
WHERE settlementDate >= '2025-11-01'  -- Returns nothing!
```

**✅ CORRECT:**
```sql
-- Combine both sources
SELECT * FROM `bmrs_costs` WHERE settlementDate < '2025-10-29'
UNION ALL
SELECT price AS systemBuyPrice, price AS systemSellPrice, ...
FROM `bmrs_mid_iris` WHERE settlementDate >= '2025-10-29'
```

### Pitfall 3: Confusing MID price with settlement price

**Market Index Price** (`bmrs_mid_iris.price`):
- Reference price from wholesale trades
- Updated every ~5 minutes
- **Indicative only** - not used for final settlement

**System Price** (`v_system_prices_sp`):
- Final published imbalance price
- Used for actual settlement
- Available ~30 minutes after gate closure

For **real-time trading decisions**, use MID price.  
For **financial reconciliation**, use system price.

---

## 🔍 Data Quality Checks

### Check 1: Verify IRIS data freshness

```sql
SELECT 
    MAX(settlementDate) AS latest_date,
    MAX(ingested_utc) AS latest_ingestion,
    COUNT(*) AS total_rows,
    COUNT(DISTINCT dataProvider) AS num_providers
FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_mid_iris`
```

**Expected**: `latest_date` should be today or yesterday

### Check 2: Validate price ranges

```sql
SELECT 
    MIN(price) AS min_price,
    MAX(price) AS max_price,
    AVG(price) AS avg_price,
    STDDEV(price) AS std_price
FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_mid_iris`
WHERE settlementDate >= CURRENT_DATE() - 7
```

**Expected**:
- `min_price` > -£100/MWh (negative is rare but possible)
- `max_price` < £500/MWh (typical range £20-150/MWh)
- `avg_price` £40-80/MWh

### Check 3: Detect data gaps

```sql
WITH expected_periods AS (
  SELECT date, period
  FROM UNNEST(GENERATE_DATE_ARRAY('2025-12-01', '2025-12-02')) AS date
  CROSS JOIN UNNEST(GENERATE_ARRAY(1, 48)) AS period
),
actual_data AS (
  SELECT CAST(settlementDate AS DATE) AS date, settlementPeriod AS period
  FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_mid_iris`
  WHERE settlementDate >= '2025-12-01'
)
SELECT e.date, e.period
FROM expected_periods e
LEFT JOIN actual_data a 
  ON e.date = a.date AND e.period = a.period
WHERE a.period IS NULL
ORDER BY e.date, e.period
```

**Expected**: No missing periods (empty result set)

---

## 📖 Further Reading

- **P305 Modification**: [Elexon BSC Modification P305](https://www.elexon.co.uk/mod-proposal/p305/)
- **Market Index Data**: [BMRS MID Dataset](https://www.elexon.co.uk/documents/training-guidance/bsc-guidance-notes/market-index-data-mid/)
- **System Pricing**: [Elexon System Pricing Guide](https://www.elexon.co.uk/documents/training-guidance/bsc-guidance-notes/imbalance-pricing/)

---

## 🚀 Dashboard Integration

### Google Sheets Formula for Latest Price

```javascript
// Apps Script function
function getLatestMarketPrice() {
  const query = `
    SELECT price, settlementDate, settlementPeriod
    FROM \`inner-cinema-476211-u9.uk_energy_prod.bmrs_mid_iris\`
    ORDER BY settlementDate DESC, settlementPeriod DESC
    LIMIT 1
  `;
  
  const result = runBigQuery(query);
  return result[0].price;
}
```

### Python Query for Analysis

```python
from google.cloud import bigquery

PROJECT_ID = 'inner-cinema-476211-u9'
client = bigquery.Client(project=PROJECT_ID, location='US')

query = """
SELECT 
    settlementDate,
    settlementPeriod,
    price,
    price + 1.11 + 98.15 AS green_cost,
    150.0 - (price + 1.11 + 98.15) AS profit_margin
FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_mid_iris`
WHERE settlementDate >= CURRENT_DATE() - 7
ORDER BY settlementDate DESC, settlementPeriod DESC
"""

df = client.query(query).to_dataframe()
print(f"Retrieved {len(df)} pricing records")
print(f"Average price: £{df['price'].mean():.2f}/MWh")
print(f"Profitable periods: {(df['profit_margin'] > 0).sum()}")
```

---

## ✅ Summary

| Question | Answer |
|----------|--------|
| **Why one price in IRIS?** | Post-2015 P305 modification unified SBP/SSP into single imbalance price |
| **What does `bmrs_mid_iris.price` represent?** | Market Index Data - reference price from short-term wholesale trades |
| **Can I still get SBP/SSP?** | Yes, from `bmrs_costs` (historical) or `v_system_prices_sp` (published) |
| **Which price for battery trading?** | Use `bmrs_mid_iris.price` for real-time decisions |
| **Which price for settlement?** | Use `v_system_prices_sp` for financial reconciliation |
| **How to query recent data?** | UNION `bmrs_costs` (< Oct 29) with `bmrs_mid_iris` (>= Oct 29) |

---

**Last Updated**: 2 December 2025  
**Maintainer**: George Major (george@upowerenergy.uk)  
**Status**: ✅ Production - IRIS feed live and operational

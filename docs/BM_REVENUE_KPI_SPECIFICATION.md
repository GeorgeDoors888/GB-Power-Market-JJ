# BM Revenue & Market KPI Specification

**Purpose**: Comprehensive KPI definitions for UK Balancing Mechanism revenue analysis  
**Data Sources**: Elexon BMRS/Insights APIs (BOALF, BOD, BOAV, EBOCF, DISBSAD)  
**Update**: December 14, 2025

---

## Quick Reference: Data Source APIs

| Dataset | Purpose | API Endpoint | Key Fields |
|---------|---------|--------------|------------|
| **BOALF** | Acceptance-level dispatch (operational) | `/balancing/acceptance/all` | acceptanceNumber, bmUnit, levelFrom, levelTo, timeFrom, timeTo |
| **BOD** | Submitted bid/offer stack | `/balancing/bid-offer/all` | bmUnit, pairId, bid, offer, levelFrom, levelTo |
| **BOAV** | Settlement acceptance volumes | `/balancing/settlement/acceptance/volumes/all` | bmUnit, acceptedVolume (MWh), settlementDate, settlementPeriod |
| **EBOCF** | Indicative cashflows | `/balancing/settlement/indicative/cashflows/all` | bmUnit, cashflow (£), settlementDate, settlementPeriod |
| **DISBSAD** | Constraint costs & system actions | `/datasets/DISBSAD` | assetId, cost, volume, soFlag, service |
| **BMU Reference** | Unit metadata | `/reference/bmunits/all` | nationalGridBmUnit, fuelType, powerStationType |

---

## KPI Categories

### A) Market-Wide KPIs (All BMUs)

#### KPI_MKT_001: Total BM Cashflow (£)
- **Definition**: Total indicative BM cashflow across all BMUs from 00:00 to now
- **Formula**: `SUM(EBOCF.cashflow_bid + EBOCF.cashflow_offer)`
- **Source**: EBOCF (bid + offer)
- **Cell Note**: "Sum of indicative bid+offer cashflow across all BMUs from 00:00 local to now (EBOCF)"

#### KPI_MKT_002: Total Accepted Volume (MWh)
- **Definition**: Total accepted MWh across all BMUs
- **Formula**: `SUM(BOAV.acceptedVolume_bid + BOAV.acceptedVolume_offer)`
- **Source**: BOAV
- **Cell Note**: "Sum of bid+offer accepted MWh across all BMUs from 00:00 local to now (BOAV)"

#### KPI_MKT_003: System Direction (Net MWh)
- **Definition**: Net energy balance (offers = system buying, bids = system selling)
- **Formula**: `netMWh = offerMWh - bidMWh`
- **Source**: BOAV
- **Interpretation**: Positive = system long (importing), Negative = system short (exporting)

#### KPI_MKT_004: Energy-Weighted Average Price (EWAP) (£/MWh)
- **Definition**: Market-wide cashflow per MWh
- **Formula**: 
  - `EWAP_offer = SUM(offer_cashflow) / SUM(offer_MWh)`
  - `EWAP_bid = SUM(bid_cashflow) / SUM(bid_MWh)`
  - `EWAP_net = SUM(total_cashflow) / SUM(total_MWh)`
- **Source**: BOAV + EBOCF
- **Cell Note**: "Energy-weighted average price = cashflow ÷ MWh (EBOCF ÷ BOAV)"

#### KPI_MKT_005: Dispatch Intensity (acceptances/hour)
- **Definition**: How "busy" the BM is (market-wide acceptance frequency)
- **Formula**: `COUNT(BOALF.acceptanceNumber) / hours_elapsed`
- **Source**: BOALF
- **Cell Note**: "BOALF acceptances per hour (count acceptances / hours)"

#### KPI_MKT_006: Concentration (Top 1 / Top 5 share of £)
- **Definition**: Market dominance by top earners
- **Formula**: `(SUM(£ for top N BMUs) / SUM(total £)) * 100`
- **Source**: EBOCF
- **Variants**: Top-1, Top-5, Top-10 share

#### KPI_MKT_007: Workhorse Index (Active SPs/48)
- **Definition**: Fraction of settlement periods with activity
- **Formula**: `COUNT(DISTINCT SP WHERE BOAV.volume > 0) / 48`
- **Source**: BOAV
- **Cell Note**: "Count of settlement periods with non-zero accepted MWh"

---

### B) BMU-Level KPIs (Per Unit)

#### KPI_BMU_001: Net BM Revenue (£)
- **Definition**: Total bid + offer cashflow for this BMU
- **Formula**: `SUM(EBOCF.cashflow_bid + EBOCF.cashflow_offer)`
- **Source**: EBOCF
- **Sheet Column**: "Net BM Revenue (£)"

#### KPI_BMU_002: Discharge/Charge Revenue (£)
- **Definition**: Separate bid and offer cashflows
- **Formula**: 
  - Discharge (Offer): `SUM(EBOCF.cashflow_offer)`
  - Charge (Bid): `SUM(EBOCF.cashflow_bid)`
- **Source**: EBOCF

#### KPI_BMU_003: Accepted MWh (Offer / Bid)
- **Definition**: Total energy accepted in each direction
- **Formula**: 
  - `offerMWh = SUM(BOAV.acceptedVolume_offer)`
  - `bidMWh = SUM(BOAV.acceptedVolume_bid)`
  - `netMWh = offerMWh - bidMWh`
- **Source**: BOAV
- **Sheet Column**: "Accepted MWh (Offer / Bid)"

#### KPI_BMU_004: VWAP (£/MWh)
- **Definition**: Volume-weighted average price
- **Formula**: `VWAP = SUM(price_i * volume_i) / SUM(volume_i)`
- **Source**: BOAV + EBOCF
- **Implementation**: 
  ```sql
  -- Offer VWAP
  SUM(EBOCF.cashflow_offer) / SUM(BOAV.acceptedVolume_offer)
  
  -- Bid VWAP
  SUM(EBOCF.cashflow_bid) / SUM(BOAV.acceptedVolume_bid)
  ```
- **Sheet Column**: "VWAP (£/MWh)"

#### KPI_BMU_005: Active SPs (X/48)
- **Definition**: Number of settlement periods with accepted volume
- **Formula**: `COUNT(DISTINCT SP WHERE offerMWh + bidMWh > 0)`
- **Source**: BOAV
- **Format**: "29/48" (29 active periods out of 48)
- **Sheet Column**: "Active SPs (X/48)"

#### KPI_BMU_006: £/MW-day
- **Definition**: Revenue normalized by installed capacity (daily rate)
- **Formula**: `£/MW-day = Net_Revenue / (Installed_Capacity_MW * Days)`
- **Source**: EBOCF + BMU metadata (registeredCapacity)
- **Requires**: BMU capacity from reference data
- **Sheet Column**: "£/MW-day"

#### KPI_BMU_007: Offer/Bid Ratio
- **Definition**: Revenue balance between discharge and charge
- **Formula**: `Offer_Bid_Ratio = ABS(offer_cashflow) / ABS(bid_cashflow)`
- **Source**: EBOCF
- **Interpretation**: 
  - Ratio > 1: More discharge revenue
  - Ratio < 1: More charge revenue
  - Ratio ~ 1: Balanced arbitrage
- **Sheet Column**: "Offer/Bid Ratio"

#### KPI_BMU_008: Constraint Share (% DISBSAD)
- **Definition**: BMU's share of total DISBSAD constraint costs
- **Formula**: `(BMU_DISBSAD_cost / Total_Market_DISBSAD_cost) * 100`
- **Source**: DISBSAD
- **BigQuery**:
  ```sql
  WITH bmu_cost AS (
    SELECT assetId, SUM(ABS(cost)) as bmu_disbsad
    FROM bmrs_disbsad
    WHERE settlementDate = '2025-12-13'
    GROUP BY assetId
  ),
  total_cost AS (
    SELECT SUM(ABS(cost)) as market_disbsad
    FROM bmrs_disbsad
    WHERE settlementDate = '2025-12-13'
  )
  SELECT 
    b.assetId,
    b.bmu_disbsad,
    (b.bmu_disbsad / t.market_disbsad) * 100 as constraint_share_pct
  FROM bmu_cost b
  CROSS JOIN total_cost t
  ```
- **Sheet Column**: "Constraint Share (% DISBSAD)"

#### KPI_BMU_009: Non-Delivery Rate (%)
- **Definition**: Percentage of accepted BOAs not fully delivered
- **Formula**: `(Failed_Acceptances / Total_Acceptances) * 100`
- **Source**: BOALF (acceptance tracking) or derived from BOAV vs BOALF comparison
- **Implementation Challenge**: Requires acceptance-level tracking vs settlement-level volumes
- **Proxy Method**: 
  ```sql
  -- Compare BOALF acceptance count vs BOAV settlement records
  -- High acceptance count with low volume = potential non-delivery
  (BOALF_count - BOAV_nonzero_count) / BOALF_count * 100
  ```
- **Sheet Column**: "Non-Delivery Rate (%)"

#### KPI_BMU_010: Acceptance Count (BOALF)
- **Definition**: Number of dispatch acceptances received
- **Formula**: `COUNT(BOALF.acceptanceNumber)`
- **Source**: BOALF
- **Cell Note**: "Number of BOALF acceptances in the window (dispatch frequency)"

#### KPI_BMU_011: Granularity (MWh per acceptance)
- **Definition**: Average dispatch size
- **Formula**: `(offerMWh + bidMWh) / acceptanceCount`
- **Source**: BOAV + BOALF
- **Cell Note**: "Average 'size' of dispatch actions (volume ÷ acceptances)"

#### KPI_BMU_012: Time-of-day Profile (% MWh in bands)
- **Definition**: Distribution of volume across time periods
- **Formula**: `SUM(MWh WHERE SP in time_band) / SUM(total_MWh) * 100`
- **Source**: BOAV (by SP) or BOALF (by timeFrom)
- **Time Bands**:
  - Night: 00:00-06:00 (SP 1-12)
  - Morning: 06:00-12:00 (SP 13-24)
  - Afternoon: 12:00-18:00 (SP 25-36)
  - Evening: 18:00-00:00 (SP 37-48)

---

### C) Bid/Offer Stack KPIs (Market Behaviour)

#### KPI_STACK_001: Stack Depth (pairs per SP)
- **Definition**: Granularity of submitted bid-offer stack
- **Formula**: `COUNT(DISTINCT BOD.pairId) / COUNT(DISTINCT SP)`
- **Source**: BOD

#### KPI_STACK_002: Defensive Pricing Share (%)
- **Definition**: Percentage of pairs with extreme prices (not intending to clear)
- **Formula**: `COUNT(pairs WHERE ABS(price) >= 9999) / COUNT(total_pairs) * 100`
- **Source**: BOD
- **Threshold**: £9,999/MWh or £99,999/MWh
- **Cell Note**: "% of submitted pairs with extreme prices (e.g., ≥9,999 or ≥99,999)"

#### KPI_STACK_003: Offered Flex MW
- **Definition**: Total MW available in submitted stack
- **Formula**: `SUM(ABS(levelTo - levelFrom))`
- **Source**: BOD

#### KPI_STACK_004: Indicative Spread (£/MWh)
- **Definition**: Typical bid-offer spread (pricing aggressiveness)
- **Formula**: `MEDIAN(offer_price - bid_price)` (filtered to non-defensive pairs)
- **Source**: BOD

---

## Implementation Queries (BigQuery)

### 1. Active BMU Count Today

```sql
-- Total active BMUs (had at least 1 acceptance)
SELECT COUNT(DISTINCT bmUnit) AS active_bmu_count
FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_boalf`
WHERE DATE(settlementDate) = CURRENT_DATE("Europe/London");
```

### 2. Active BMUs by Technology

**Requires**: BMU metadata table from `/reference/bmunits/all`

```sql
SELECT 
  tech_group,
  COUNT(DISTINCT b.bmUnit) AS active_bmus,
  SUM(revenue) as total_revenue,
  SUM(volume_mwh) as total_volume
FROM (
  SELECT 
    bmUnit,
    SUM(cashflow) as revenue,
    SUM(acceptedVolume) as volume_mwh
  FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_boav`
  WHERE settlementDate = '2025-12-13'
  GROUP BY bmUnit
) b
JOIN `inner-cinema-476211-u9.uk_energy_prod.bmu_metadata` m 
  ON b.bmUnit = m.nationalGridBmUnit
CROSS JOIN UNNEST([STRUCT(
  CASE
    WHEN LOWER(m.fuelType) IN ("battery","bess","storage") THEN "BESS"
    WHEN LOWER(m.fuelType) IN ("wind","offshore wind","onshore wind") THEN "Wind"
    WHEN LOWER(m.fuelType) IN ("solar","pv") THEN "Solar"
    WHEN LOWER(m.fuelType) IN ("demand","demand side response","dsr") THEN "Demand"
    WHEN LOWER(m.fuelType) IN ("gas","ccgt","ocgt") THEN "Gas"
    WHEN LOWER(m.fuelType) IN ("coal","biomass") THEN "Thermal"
    ELSE "Other"
  END AS tech_group
)])
GROUP BY tech_group
ORDER BY total_revenue DESC;
```

### 3. DISBSAD Constraint Analysis

```sql
-- BMU constraint share
WITH market_total AS (
  SELECT SUM(ABS(cost)) as total_disbsad_cost
  FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_disbsad`
  WHERE settlementDate = '2025-12-13'
),
bmu_costs AS (
  SELECT 
    assetId,
    COUNT(*) as disbsad_actions,
    SUM(ABS(cost)) as disbsad_cost,
    SUM(ABS(volume)) as disbsad_volume_mwh
  FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_disbsad`
  WHERE settlementDate = '2025-12-13'
    AND assetId IS NOT NULL
  GROUP BY assetId
)
SELECT 
  b.assetId,
  b.disbsad_actions,
  b.disbsad_cost,
  b.disbsad_volume_mwh,
  (b.disbsad_cost / m.total_disbsad_cost) * 100 as constraint_share_pct
FROM bmu_costs b
CROSS JOIN market_total m
ORDER BY b.disbsad_cost DESC
LIMIT 20;
```

### 4. Enhanced BMU Revenue Summary (All KPIs)

```sql
WITH bm_revenue AS (
  -- BM cashflows from EBOCF
  SELECT 
    bmUnit,
    SUM(CASE WHEN direction = 'offer' THEN cashflow ELSE 0 END) as offer_revenue,
    SUM(CASE WHEN direction = 'bid' THEN cashflow ELSE 0 END) as bid_revenue
  FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_ebocf`
  WHERE settlementDate = '2025-12-13'
  GROUP BY bmUnit
),
bm_volume AS (
  -- Accepted volumes from BOAV
  SELECT 
    bmUnit,
    SUM(CASE WHEN direction = 'offer' THEN acceptedVolume ELSE 0 END) as offer_mwh,
    SUM(CASE WHEN direction = 'bid' THEN acceptedVolume ELSE 0 END) as bid_mwh,
    COUNT(DISTINCT settlementPeriod) as active_sps
  FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_boav`
  WHERE settlementDate = '2025-12-13'
  GROUP BY bmUnit
),
disbsad_costs AS (
  -- DISBSAD constraint costs
  SELECT 
    assetId as bmUnit,
    SUM(ABS(cost)) as disbsad_cost,
    COUNT(*) as disbsad_actions
  FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_disbsad`
  WHERE settlementDate = '2025-12-13'
  GROUP BY assetId
)
SELECT 
  r.bmUnit,
  -- Revenue KPIs
  r.offer_revenue + r.bid_revenue as net_revenue,
  r.offer_revenue,
  r.bid_revenue,
  
  -- Volume KPIs
  v.offer_mwh,
  v.bid_mwh,
  v.offer_mwh + v.bid_mwh as total_mwh,
  
  -- Pricing KPIs
  SAFE_DIVIDE(r.offer_revenue, v.offer_mwh) as vwap_offer,
  SAFE_DIVIDE(r.bid_revenue, v.bid_mwh) as vwap_bid,
  SAFE_DIVIDE(r.offer_revenue + r.bid_revenue, v.offer_mwh + v.bid_mwh) as vwap_net,
  
  -- Activity KPIs
  v.active_sps,
  CONCAT(CAST(v.active_sps AS STRING), '/48') as active_sps_display,
  
  -- Financial ratios
  SAFE_DIVIDE(ABS(r.offer_revenue), ABS(r.bid_revenue)) as offer_bid_ratio,
  
  -- Constraint KPIs
  COALESCE(d.disbsad_cost, 0) as disbsad_cost,
  COALESCE(d.disbsad_actions, 0) as disbsad_actions,
  r.offer_revenue + r.bid_revenue + COALESCE(d.disbsad_cost, 0) as combined_revenue

FROM bm_revenue r
JOIN bm_volume v USING (bmUnit)
LEFT JOIN disbsad_costs d ON r.bmUnit = d.bmUnit
WHERE r.offer_revenue + r.bid_revenue != 0
ORDER BY net_revenue DESC;
```

---

## Year-to-Date Benchmarks

### Methodology

**Avoid bias**: Compare like-for-like time windows
- Option 1: Same-time-of-day (e.g., today 00:00-09:00 vs historical 00:00-09:00)
- Option 2: SP-complete (e.g., SP1-18 today vs SP1-18 historical)

### Benchmark Statistics (365-day rolling)

For each KPI, calculate:
- **Mean**: Average value
- **Min/Max**: Range
- **Percentiles**: p10, p50 (median), p90 (or p5/p95)
- **Std Dev**: Volatility measure
- **Z-Score**: `(today - mean) / stddev` (how many standard deviations from mean)
- **Rank Percentile**: Today's rank vs 365 days (e.g., 85th percentile = top 15%)

### Implementation Example

```sql
-- Calculate 365-day benchmarks for Net BM Revenue
WITH historical AS (
  SELECT 
    DATE(settlementDate) as date,
    bmUnit,
    SUM(cashflow) as daily_revenue
  FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_ebocf`
  WHERE settlementDate >= DATE_SUB(CURRENT_DATE(), INTERVAL 365 DAY)
  GROUP BY date, bmUnit
),
stats AS (
  SELECT 
    bmUnit,
    AVG(daily_revenue) as mean_revenue,
    MIN(daily_revenue) as min_revenue,
    MAX(daily_revenue) as max_revenue,
    STDDEV(daily_revenue) as stddev_revenue,
    APPROX_QUANTILES(daily_revenue, 100)[OFFSET(10)] as p10_revenue,
    APPROX_QUANTILES(daily_revenue, 100)[OFFSET(50)] as p50_revenue,
    APPROX_QUANTILES(daily_revenue, 100)[OFFSET(90)] as p90_revenue
  FROM historical
  GROUP BY bmUnit
),
today AS (
  SELECT 
    bmUnit,
    SUM(cashflow) as today_revenue
  FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_ebocf`
  WHERE settlementDate = CURRENT_DATE()
  GROUP BY bmUnit
)
SELECT 
  t.bmUnit,
  t.today_revenue,
  s.mean_revenue,
  s.min_revenue,
  s.max_revenue,
  s.p50_revenue as median_revenue,
  -- Z-score
  (t.today_revenue - s.mean_revenue) / NULLIF(s.stddev_revenue, 0) as z_score,
  -- Performance vs benchmarks
  CASE 
    WHEN t.today_revenue > s.p90_revenue THEN 'Exceptional (>p90)'
    WHEN t.today_revenue > s.p50_revenue THEN 'Above Average'
    WHEN t.today_revenue > s.p10_revenue THEN 'Below Average'
    ELSE 'Poor (<p10)'
  END as performance_tier
FROM today t
JOIN stats s USING (bmUnit)
ORDER BY t.today_revenue DESC;
```

---

## Dashboard Layout Recommendations

### Header Row (Market Summary)
| Total BM £ | Total BM MWh | Dispatch Intensity | Top-1 Share | Active BMUs |
|------------|--------------|-------------------|-------------|-------------|
| £3.5M | 45,000 MWh | 12.3 acc/hr | 18.5% | 131 |

### BMU Table (Top 20)
| BMU ID | Technology | Net £ | Offer £ | Bid £ | Offer MWh | Bid MWh | VWAP | Active SPs | £/MW-day | Offer/Bid Ratio | Constraint Share | DISBSAD £ | Combined £ |
|--------|-----------|-------|---------|-------|-----------|---------|------|------------|----------|----------------|-----------------|-----------|------------|

### Market Behavior Panel
| Defensive Share | Median Spread | Offered Flex MW | Stack Depth |
|----------------|---------------|-----------------|-------------|
| 42% | £85/MWh | 12,500 MW | 8.3 pairs/SP |

---

## Data Quality Caveats

1. **BOAV/EBOCF Settlement Data**: Returns "latest settlement run" only - values can change as runs update
2. **Pair-Level Linkage**: Public APIs don't cleanly expose BOD pair → BOALF acceptance mapping
3. **DISBSAD Lag**: Settlement-grade data with D+1 to D+2 working day delay (not real-time)
4. **BOD vs BOALF**: BOD = submitted intent, BOALF = accepted actions (don't confuse)

---

## API Reference Quick Links

- BMU Units: `https://data.elexon.co.uk/bmrs/api/v1/reference/bmunits/all`
- BOALF: `https://data.elexon.co.uk/bmrs/api/v1/balancing/acceptance/all`
- BOAV: `https://data.elexon.co.uk/bmrs/api/v1/balancing/settlement/acceptance/volumes/all`
- EBOCF: `https://data.elexon.co.uk/bmrs/api/v1/balancing/settlement/indicative/cashflows/all`
- DISBSAD: `https://data.elexon.co.uk/bmrs/api/v1/datasets/DISBSAD`
- BOD: `https://data.elexon.co.uk/bmrs/api/v1/balancing/bid-offer/all`

---

**Last Updated**: December 14, 2025  
**Maintainer**: George Major (george@upowerenergy.uk)  
**Related Docs**: `PROJECT_CONFIGURATION.md`, `STOP_DATA_ARCHITECTURE_REFERENCE.md`

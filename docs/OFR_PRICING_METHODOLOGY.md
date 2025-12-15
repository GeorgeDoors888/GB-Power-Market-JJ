# OFR Pricing Methodology & Data Refresh Process

**Purpose**: Document how OFR (Optional Frequency Response) pricing statistics are calculated and maintained in this repository.

**Critical Principle**: OFR pricing figures MUST NOT be hard-coded. They must be regenerated from DISBSAD data using `ofr_pricing_analysis.py`.

---

## Data Source

**Table**: `inner-cinema-476211-u9.uk_energy_prod.bmrs_disbsad`  
**Filter**: `assetId LIKE 'OFR-%'`  
**Requirement**: `cost IS NOT NULL AND volume > 0`

DISBSAD (Disaggregated Balancing Services Adjustment Data) contains settlement records for balancing services, including OFR flexibility services primarily provided by batteries and demand-side response.

---

## Price Calculation Formula

For each DISBSAD action where OFR was utilised:

```
price_per_mwh = cost / volume
```

**Aggregate Statistics** (across all OFR actions in period):
- **Volume-weighted average**: `SUM(cost) / SUM(volume)`
- **Min/Max**: Lowest and highest individual action prices
- **Quartiles**: 25th, 50th (median), 75th percentile prices

---

## Running the Analysis

### Basic 30-Day Analysis
```bash
python3 ofr_pricing_analysis.py \
  --project inner-cinema-476211-u9 \
  --dataset uk_energy_prod \
  --table bmrs_disbsad \
  --days 30
```

### With OFR vs Non-OFR Comparison
```bash
python3 ofr_pricing_analysis.py \
  --project inner-cinema-476211-u9 \
  --dataset uk_energy_prod \
  --table bmrs_disbsad \
  --days 30 \
  --compare-non-ofr
```

### Custom Time Window
```bash
python3 ofr_pricing_analysis.py \
  --project inner-cinema-476211-u9 \
  --dataset uk_energy_prod \
  --table bmrs_disbsad \
  --days 90  # Last 90 days
```

---

## Current Statistics (Last Updated: December 9, 2025)

**Analysis Period**: November 9 - December 9, 2025 (30 days)

### OFR Utilisation Pricing
```
Volume-Weighted Avg:  £109.91/MWh
Min Price:            £70.94/MWh
Q1 (25th percentile): £100.00/MWh
Median (50th):        £106.00/MWh
Q3 (75th percentile): £115.00/MWh
Max Price:            £199.00/MWh

Total Actions:        3,490
Total Cost:           £5,196,750.81
Total Volume:         47,279.77 MWh
```

### OFR vs Non-OFR Comparison
```
OFR Flexibility:      £109.91/MWh (3,490 actions, 47,280 MWh)
Non-OFR (Generators): £211.64/MWh (4,016 actions, 208,683 MWh)
Price Difference:     48% cheaper (OFR vs Non-OFR)
```

**Command Used**:
```bash
python3 ofr_pricing_analysis.py \
  --project inner-cinema-476211-u9 \
  --dataset uk_energy_prod \
  --days 30 \
  --compare-non-ofr
```

---

## When to Update Documentation

### Update Triggers
1. **Monthly**: Refresh figures first week of each month
2. **After Major Events**: Price spikes, system stress events
3. **Before Publishing**: When referencing OFR pricing in reports/presentations
4. **Data Pipeline Changes**: After DISBSAD backfills or schema updates

### Files to Update

When OFR pricing statistics change, update these files:

1. **`docs/DISBSAD_OFR_PRICING_ANALYSIS.md`**
   - Executive summary metrics
   - Section 1: OFR Flexibility Services (pricing characteristics)
   - Section 2: Generator-based balancing comparison
   - Update date header and analysis period

2. **`docs/WHY_CONSTRAINT_COSTS_ARE_NA.md`**
   - "What's IN DISBSAD" section with OFR pricing
   - Update period reference

3. **`docs/OFR_PRICING_METHODOLOGY.md`** (this file)
   - "Current Statistics" section
   - Update "Last Updated" date

4. **`README.md`** (if it references OFR pricing)
   - Any mentions of OFR price ranges
   - Comparison statistics

---

## Important Limitations

### What These Prices Represent

✅ **Included**:
- Utilisation payments (£/MWh for energy delivered)
- Settlement Period-level pricing (30-minute intervals)
- Only actions where `cost` and `volume` are both present

❌ **NOT Included**:
- Availability payments (capacity fees paid regardless of utilisation)
- Tendered service contracts (separate commercial arrangements)
- FFR or other ancillary service availability fees
- Actions with missing cost or zero volume

### Business Context

**OFR Contract Structure**:
```
Revenue = Availability Fees (not in DISBSAD) 
          + Utilisation Payments (in DISBSAD)
```

These statistics show **only the utilisation component** visible in DISBSAD settlement data. Battery operators receive additional revenue from:
- Monthly availability payments (not in public data)
- Capacity market contracts
- Wholesale trading activity
- Other ancillary services

---

## Data Quality Checks

Before publishing updated figures, verify:

1. **Record Count**: Does action count seem reasonable for the period?
   - Expected: ~100-150 OFR actions per day
   - 30 days ≈ 3,000-4,500 actions ✓

2. **Price Range**: Are min/max within expected bounds?
   - Typical range: £50-200/MWh
   - Outliers (>£250 or <£30) should be investigated

3. **Volume**: Is total MWh consistent with action count?
   - Typical: 10-20 MWh average per action
   - 3,490 actions × 13.5 MWh avg ≈ 47,280 MWh ✓

4. **Date Window**: Is the analysis period clearly stated?
   - Always specify start and end dates
   - Example: "November 9 - December 9, 2025 (30 days)"

---

## SQL Query Reference

The `ofr_pricing_analysis.py` script uses this BigQuery logic:

```sql
WITH base AS (
  SELECT
    assetId,
    CAST(settlementDate AS DATE) AS settlement_date,
    cost,
    volume,
    SAFE_DIVIDE(cost, NULLIF(volume, 0)) AS price_per_mwh
  FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_disbsad`
  WHERE assetId LIKE 'OFR-%'
    AND CAST(settlementDate AS DATE) BETWEEN @start_date AND @end_date
    AND cost IS NOT NULL
    AND volume > 0
)
SELECT
  COUNT(*) AS n_actions,
  SUM(cost) AS total_cost_gbp,
  SUM(volume) AS total_volume_mwh,
  SUM(cost) / SUM(volume) AS volume_weighted_avg_price_per_mwh,
  MIN(price_per_mwh) AS min_price_per_mwh,
  MAX(price_per_mwh) AS max_price_per_mwh,
  APPROX_QUANTILES(price_per_mwh, 4)[OFFSET(1)] AS q1_price_per_mwh,
  APPROX_QUANTILES(price_per_mwh, 4)[OFFSET(2)] AS median_price_per_mwh,
  APPROX_QUANTILES(price_per_mwh, 4)[OFFSET(3)] AS q3_price_per_mwh
FROM base
WHERE price_per_mwh IS NOT NULL
```

---

## Change Log

### December 9, 2025
- Initial documentation created
- Analysis period: Nov 9 - Dec 9, 2025 (30 days)
- OFR avg: £109.91/MWh (range £70.94-199.00)
- OFR vs Non-OFR: 48% cheaper

### [Future Updates]
- Add date and key metric changes here
- Reference analysis period used
- Note any methodology changes

---

**Maintained by**: George Major (george@upowerenergy.uk)  
**Script Location**: `/home/george/GB-Power-Market-JJ/ofr_pricing_analysis.py`  
**Documentation**: See also `DISBSAD_OFR_PRICING_ANALYSIS.md`, `WHY_CONSTRAINT_COSTS_ARE_NA.md`

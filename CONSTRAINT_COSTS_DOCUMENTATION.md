# NESO Constraint Cost Data - Architecture Documentation

**Created**: December 29, 2024
**Status**: ✅ Production Ready
**Coverage**: Financial Years 2017-2026 (3,183 days)

## Overview

NESO (National Energy System Operator) constraint cost data tracks the daily costs incurred by the system operator to manage grid constraints. This includes thermal limits, voltage issues, system inertia requirements, and loss reduction actions.

## Data Sources

### Raw Tables (9 Financial Year Tables)
```
neso_constraint_breakdown_2017_2018    365 rows
neso_constraint_breakdown_2018_2019    365 rows
neso_constraint_breakdown_2019_2020    366 rows (leap year)
neso_constraint_breakdown_2020_2021    365 rows
neso_constraint_breakdown_2021_2022    365 rows
neso_constraint_breakdown_2022_2023    365 rows
neso_constraint_breakdown_2023_2024    366 rows (leap year)
neso_constraint_breakdown_2024_2025    365 rows
neso_constraint_breakdown_2025_2026    261 rows (partial FY)
```

**Schema** (all tables identical):
```sql
Date                                  STRING    -- Format: YYYY-MM-DD (some with T00:00:00)
Thermal constraints cost              INTEGER   -- £ (largest component, typically 70-90%)
Voltage constraints cost              INTEGER   -- £
Reducing largest loss cost            INTEGER   -- £
Increasing system inertia cost        INTEGER   -- £
Thermal constraints volume            INTEGER   -- MWh (negative = bids, positive = offers)
Voltage constraints volume            INTEGER   -- MWh
Reducing largest loss volume          INTEGER   -- MWh
Increasing system inertia volume      INTEGER   -- MWh
```

**Data Quality Notes**:
- Date field is STRING type with inconsistent formatting (some include `T00:00:00` timestamp)
- Costs are in pounds sterling (£), NOT pence
- Volumes can be negative (directional: bids vs offers)
- Thermal constraints typically dominate (70-90% of total costs)

## Aggregated Views & Tables

### 1. `v_neso_constraints_unified` (VIEW)

**Purpose**: Unified queryable view combining all 9 FY tables with standardized schema

**Schema**:
```sql
constraint_date              DATE        -- Parsed from STRING, handles DATETIME format
year                         INT64       -- Calendar year
month                        INT64       -- Month (1-12)
quarter                      INT64       -- Quarter (1-4)
financial_year               INT64       -- FY start year (Apr-Mar UK system)
thermal_cost_gbp            FLOAT64      -- Thermal constraint costs (£)
voltage_cost_gbp            FLOAT64      -- Voltage constraint costs (£)
largest_loss_cost_gbp       FLOAT64      -- Loss reduction costs (£)
inertia_cost_gbp            FLOAT64      -- Inertia increase costs (£)
thermal_volume_mwh          FLOAT64      -- Thermal constraint volumes (MWh)
voltage_volume_mwh          FLOAT64      -- Voltage volumes (MWh)
largest_loss_volume_mwh     FLOAT64      -- Loss volumes (MWh)
inertia_volume_mwh          FLOAT64      -- Inertia volumes (MWh)
total_cost_gbp              FLOAT64      -- Sum of all costs
total_volume_mwh            FLOAT64      -- Sum of all volumes
source_table                STRING       -- Original FY table name
```

**Row Count**: 3,183 daily records (2017-04-01 to 2025-12-18)

**Key Feature**: Robust date parsing using `CAST(SUBSTR(Date, 1, 10) AS DATE)` to handle both `YYYY-MM-DD` and `YYYY-MM-DDT00:00:00` formats

**Sample Query**:
```sql
SELECT
  constraint_date,
  total_cost_gbp,
  thermal_cost_gbp,
  voltage_cost_gbp
FROM `inner-cinema-476211-u9.uk_energy_prod.v_neso_constraints_unified`
WHERE financial_year = 2024
ORDER BY constraint_date DESC
LIMIT 10;
```

### 2. `constraint_costs_monthly` (TABLE)

**Purpose**: Monthly aggregations for trend analysis

**Schema**:
```sql
financial_year               INT64       -- FY start year
year                         INT64       -- Calendar year
month                        INT64       -- Month number
year_month                   STRING      -- Format: YYYY-MM
thermal_cost_gbp            FLOAT64      -- Monthly thermal costs
voltage_cost_gbp            FLOAT64      -- Monthly voltage costs
largest_loss_cost_gbp       FLOAT64      -- Monthly loss costs
inertia_cost_gbp            FLOAT64      -- Monthly inertia costs
total_cost_gbp              FLOAT64      -- Monthly total costs
thermal_volume_mwh          FLOAT64      -- Monthly thermal volumes
voltage_volume_mwh          FLOAT64      -- Monthly voltage volumes
largest_loss_volume_mwh     FLOAT64      -- Monthly loss volumes
inertia_volume_mwh          FLOAT64      -- Monthly inertia volumes
total_volume_mwh            FLOAT64      -- Monthly total volumes
thermal_price_per_mwh       FLOAT64      -- £/MWh for thermal constraints
voltage_price_per_mwh       FLOAT64      -- £/MWh for voltage constraints
loss_price_per_mwh          FLOAT64      -- £/MWh for loss reduction
inertia_price_per_mwh       FLOAT64      -- £/MWh for inertia increase
avg_price_per_mwh           FLOAT64      -- Overall £/MWh
days_in_period               INT64       -- Number of days in month
```

**Row Count**: 105 months (2017-04 to 2025-12)

**Sample Query**:
```sql
SELECT
  year_month,
  total_cost_gbp,
  thermal_cost_gbp,
  days_in_period
FROM `inner-cinema-476211-u9.uk_energy_prod.constraint_costs_monthly`
ORDER BY year_month DESC
LIMIT 12;  -- Last 12 months
```

### 3. `constraint_costs_annual` (TABLE)

**Purpose**: Financial year totals for year-over-year comparison

**Schema**:
```sql
financial_year               INT64       -- FY start year
period_start                 DATE        -- First day of FY
period_end                   DATE        -- Last day of FY
thermal_cost_gbp            FLOAT64      -- Annual thermal costs
voltage_cost_gbp            FLOAT64      -- Annual voltage costs
largest_loss_cost_gbp       FLOAT64      -- Annual loss costs
inertia_cost_gbp            FLOAT64      -- Annual inertia costs
total_cost_gbp              FLOAT64      -- Annual total costs
thermal_volume_mwh          FLOAT64      -- Annual thermal volumes
voltage_volume_mwh          FLOAT64      -- Annual voltage volumes
largest_loss_volume_mwh     FLOAT64      -- Annual loss volumes
inertia_volume_mwh          FLOAT64      -- Annual inertia volumes
total_volume_mwh            FLOAT64      -- Annual total volumes
thermal_price_per_mwh       FLOAT64      -- Average £/MWh thermal
voltage_price_per_mwh       FLOAT64      -- Average £/MWh voltage
loss_price_per_mwh          FLOAT64      -- Average £/MWh loss
inertia_price_per_mwh       FLOAT64      -- Average £/MWh inertia
avg_price_per_mwh           FLOAT64      -- Overall average £/MWh
thermal_pct                 FLOAT64      -- % of total cost (Thermal)
voltage_pct                 FLOAT64      -- % of total cost (Voltage)
loss_pct                    FLOAT64      -- % of total cost (Loss)
inertia_pct                 FLOAT64      -- % of total cost (Inertia)
days_in_period               INT64       -- Days in FY (365 or 366)
```

**Row Count**: 9 financial years (FY2017-18 to FY2025-26)

**Key Statistics** (Last 5 FYs):
```
FY2025-26: £1,500.7M (261 days partial) - 85.6% Thermal, 11.8% Voltage
FY2024-25: £1,904.6M (365 days)        - 89.8% Thermal,  8.1% Voltage
FY2023-24: £1,390.5M (366 days)        - 74.8% Thermal, 19.3% Voltage
FY2022-23: £1,754.3M (365 days)        - 85.7% Thermal,  8.1% Voltage
FY2021-22: £1,420.3M (365 days)        - 79.9% Thermal,  7.8% Voltage
```

**Sample Query**:
```sql
SELECT
  CONCAT('FY', CAST(financial_year AS STRING), '-', SUBSTR(CAST(financial_year + 1 AS STRING), 3, 2)) as fy_label,
  ROUND(total_cost_gbp / 1000000, 1) as total_millions,
  ROUND(thermal_pct, 1) as thermal_pct,
  ROUND(voltage_pct, 1) as voltage_pct
FROM `inner-cinema-476211-u9.uk_energy_prod.constraint_costs_annual`
ORDER BY financial_year DESC;
```

### 4. `constraint_trend_summary` (TABLE)

**Purpose**: Daily time-series data with moving averages for dashboard/visualization

**Schema**:
```sql
constraint_date              DATE        -- Daily date
financial_year               INT64       -- FY year
thermal_cost_gbp            FLOAT64      -- Daily thermal costs
voltage_cost_gbp            FLOAT64      -- Daily voltage costs
largest_loss_cost_gbp       FLOAT64      -- Daily loss costs
inertia_cost_gbp            FLOAT64      -- Daily inertia costs
total_cost_gbp              FLOAT64      -- Daily total costs
thermal_volume_mwh          FLOAT64      -- Daily thermal volumes
voltage_volume_mwh          FLOAT64      -- Daily voltage volumes
largest_loss_volume_mwh     FLOAT64      -- Daily loss volumes
inertia_volume_mwh          FLOAT64      -- Daily inertia volumes
total_volume_mwh            FLOAT64      -- Daily total volumes
thermal_price_per_mwh       FLOAT64      -- Daily thermal £/MWh
voltage_price_per_mwh       FLOAT64      -- Daily voltage £/MWh
loss_price_per_mwh          FLOAT64      -- Daily loss £/MWh
inertia_price_per_mwh       FLOAT64      -- Daily inertia £/MWh
avg_price_per_mwh           FLOAT64      -- Daily overall £/MWh
cost_7d_avg                 FLOAT64      -- 7-day moving average (cost)
volume_7d_avg               FLOAT64      -- 7-day moving average (volume)
price_7d_avg                FLOAT64      -- 7-day moving average (price)
cost_30d_avg                FLOAT64      -- 30-day moving average (cost)
dominant_constraint          STRING      -- Thermal/Voltage/Loss/Inertia/Mixed
```

**Row Count**: 3,183 daily records

**Use Cases**:
- Google Sheets dashboard export (last 90 days)
- Time-series visualization (Charts.js, Plotly)
- Anomaly detection (compare daily vs 7d/30d averages)
- Constraint type pattern analysis

**Sample Query** (Recent high-cost days):
```sql
SELECT
  constraint_date,
  total_cost_gbp,
  dominant_constraint,
  cost_7d_avg
FROM `inner-cinema-476211-u9.uk_energy_prod.constraint_trend_summary`
WHERE total_cost_gbp > 10000000  -- £10M+ days
ORDER BY constraint_date DESC
LIMIT 10;
```

## Google Sheets Integration

### Sheet: "Constraint Costs" in "GB Live 2"

**Export Script**: `export_constraints_to_sheets.py`

**Update Frequency**: On-demand (run manually or via cron)

**Sheet Structure**:
1. **Annual Summary** (9 FYs): Financial year totals in £M with breakdown percentages
2. **Monthly Totals** (Last 24 months): Month-by-month costs by type
3. **Daily Timeline** (Last 90 days): Daily costs, volumes, prices, 7d averages, dominant constraint

**URL**: https://docs.google.com/spreadsheets/d/1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA

**Run Export**:
```bash
python3 export_constraints_to_sheets.py
```

## Query Patterns

### Pattern 1: Recent Daily Costs
```sql
SELECT
  constraint_date,
  total_cost_gbp,
  dominant_constraint
FROM `inner-cinema-476211-u9.uk_energy_prod.constraint_trend_summary`
WHERE constraint_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)
ORDER BY constraint_date DESC;
```

### Pattern 2: Monthly Trend (Last 12 Months)
```sql
SELECT
  year_month,
  total_cost_gbp,
  thermal_pct := ROUND(100.0 * thermal_cost_gbp / total_cost_gbp, 1) as thermal_pct
FROM `inner-cinema-476211-u9.uk_energy_prod.constraint_costs_monthly`
ORDER BY year_month DESC
LIMIT 12;
```

### Pattern 3: Year-over-Year Comparison
```sql
SELECT
  financial_year,
  total_cost_gbp / 1000000 as total_millions,
  thermal_pct,
  voltage_pct
FROM `inner-cinema-476211-u9.uk_energy_prod.constraint_costs_annual`
WHERE financial_year >= 2020
ORDER BY financial_year;
```

### Pattern 4: High-Cost Days Detection
```sql
SELECT
  constraint_date,
  total_cost_gbp,
  cost_7d_avg,
  (total_cost_gbp - cost_7d_avg) / cost_7d_avg * 100 as deviation_pct
FROM `inner-cinema-476211-u9.uk_energy_prod.constraint_trend_summary`
WHERE total_cost_gbp > cost_7d_avg * 2  -- 100%+ above average
ORDER BY deviation_pct DESC
LIMIT 20;
```

### Pattern 5: Constraint Type Analysis
```sql
SELECT
  dominant_constraint,
  COUNT(*) as days,
  AVG(total_cost_gbp) as avg_cost,
  SUM(total_cost_gbp) as total_cost
FROM `inner-cinema-476211-u9.uk_energy_prod.constraint_trend_summary`
WHERE financial_year = 2024
GROUP BY dominant_constraint
ORDER BY total_cost DESC;
```

## Known Limitations

### 1. No Regional Attribution
- **Current State**: National-level costs only (no DNO/GSP breakdown)
- **Reason**: Raw NESO data lacks geographic granularity
- **Workaround**: Future enhancement - spatial join with BMU locations from BOALF acceptances
- **Impact**: Cannot analyze constraint costs by region (Scotland, England North, etc.)

### 2. No Intraday Granularity
- **Current State**: Daily aggregates only
- **Reason**: NESO publishes daily summaries (not settlement period level)
- **Workaround**: Use BOALF acceptance data for intraday constraint proxy
- **Impact**: Cannot analyze within-day constraint patterns (peak vs off-peak)

### 3. Cost Methodology Opaque
- **Current State**: Costs are reported totals (calculation methodology unclear)
- **Reason**: NESO proprietary allocation methods
- **Workaround**: Cross-validate with DISBSAD settlement data where possible
- **Impact**: Cannot decompose costs into bid/offer components

### 4. Volume Sign Convention Unclear
- **Current State**: Negative volumes observed (likely directional)
- **Hypothesis**: Negative = reduction actions (bids), Positive = increase actions (offers)
- **Workaround**: Use absolute values for volume totals, investigate sign meaning
- **Impact**: Cannot differentiate bid vs offer volumes with certainty

### 5. Partial FY2025-26
- **Current State**: Only 261 days available (Apr 2025 - Dec 2025)
- **Reason**: Data ingested up to December 18, 2025
- **Workaround**: Mark as partial FY in analysis
- **Impact**: Cannot compare FY2025-26 annual totals to prior full years

## Related Tables

### Complementary Data Sources

**For Constraint Location Analysis**:
- `bmrs_boalf_complete`: Balancing acceptances with BMU IDs (spatial join potential)
- `dim_bmu`: BMU metadata with GSP Groups and locations
- `neso_dno_boundaries`: DNO regions (future spatial join target)

**For Settlement Cross-Validation**:
- `bmrs_disbsad`: Daily imbalance settlement totals (volume-weighted constraint costs)
- `bmrs_costs`: Settlement period imbalance prices (SSP/SBP)

**For Intraday Constraint Proxy**:
- `bmrs_boalf`: Real-time balancing acceptances (volume spikes = constraints)
- `bmrs_bod`: Bid-offer data (high-priced offers = constraint readiness)

## Maintenance

### Regular Updates
**Frequency**: Annual (when NESO publishes new FY data)

**Process**:
1. Download NESO constraint breakdown CSV for new FY (e.g., FY2026-27)
2. Ingest to new table: `neso_constraint_breakdown_2026_2027`
3. Update `create_constraint_unified_view.sql` to include new table
4. Re-create view: `python3 create_constraint_aggregations.py`
5. Update documentation with new FY stats

### Data Quality Checks
```sql
-- Check for missing dates
WITH date_range AS (
  SELECT DATE_ADD(DATE('2017-04-01'), INTERVAL n DAY) as expected_date
  FROM UNNEST(GENERATE_ARRAY(0, 3183)) as n
)
SELECT expected_date
FROM date_range
WHERE expected_date NOT IN (
  SELECT constraint_date
  FROM `inner-cinema-476211-u9.uk_energy_prod.v_neso_constraints_unified`
);

-- Check for negative total costs (should be zero results)
SELECT constraint_date, total_cost_gbp
FROM `inner-cinema-476211-u9.uk_energy_prod.v_neso_constraints_unified`
WHERE total_cost_gbp < 0;

-- Check for outliers (>3 standard deviations)
WITH stats AS (
  SELECT
    AVG(total_cost_gbp) as mean,
    STDDEV(total_cost_gbp) as stddev
  FROM `inner-cinema-476211-u9.uk_energy_prod.v_neso_constraints_unified`
)
SELECT
  constraint_date,
  total_cost_gbp,
  (total_cost_gbp - stats.mean) / stats.stddev as z_score
FROM `inner-cinema-476211-u9.uk_energy_prod.v_neso_constraints_unified`, stats
WHERE ABS((total_cost_gbp - stats.mean) / stats.stddev) > 3
ORDER BY z_score DESC;
```

## Change History

**2024-12-29**: Initial creation
- Created `v_neso_constraints_unified` view (3,183 rows)
- Created `constraint_costs_monthly` table (105 rows)
- Created `constraint_costs_annual` table (9 rows)
- Created `constraint_trend_summary` table (3,183 rows)
- Deleted old `constraint_costs_by_dno` (equal allocation bug)
- Created `export_constraints_to_sheets.py` (Sheets integration)
- Added "Constraint Costs" sheet to GB Live 2 dashboard

## Contact

**Maintainer**: George Major (george@upowerenergy.uk)
**Repository**: https://github.com/GeorgeDoors888/GB-Power-Market-JJ
**Related Docs**:
- `STOP_DATA_ARCHITECTURE_REFERENCE.md` (overall data architecture)
- `PROJECT_CONFIGURATION.md` (BigQuery configuration)
- `ENHANCED_BI_ANALYSIS_README.md` (dashboard documentation)

---

*Last Updated: December 29, 2024*

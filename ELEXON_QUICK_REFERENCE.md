# Elexon Data Access - Quick Reference Card

## 🚀 VLP Revenue Calculation (OPERATIONAL)

```bash
# Calculate VLP revenue for date range
cd /home/george/GB-Power-Market-JJ
python3 calculate_vlp_revenue.py 2025-10-17 2025-10-23

# Output: mart_bm_value_by_vlp_sp table
# Test result: £157k Flexitricity revenue (Oct 17-23)
```

## 📊 Key BigQuery Tables

```sql
-- Time-series data (113 tables)
bmrs_bod              -- Bid-offer data (2.5M rows, 1d lag)
bmrs_freq             -- Frequency (45K rows, real-time)
bmrs_mid              -- Market prices (32K rows, same-day)
bmrs_costs            -- System costs (16K rows, same-day)
bmrs_boalf_complete   -- Acceptances WITH PRICES ⭐ (11M rows)

-- Real-time variants (*_iris suffix)
bmrs_bod_iris, bmrs_freq_iris, bmrs_mid_iris, etc.

-- Reference data ✅
dim_party             -- 351 parties, 18 VLPs identified
vlp_unit_ownership    -- 9 VLP units mapped (FBPGM002-010)

-- Analytics output 🆕
mart_bm_value_by_vlp_sp  -- VLP revenue by settlement period
```

## 🔗 Join Pattern (Critical!)

```sql
-- ❌ WRONG: Direct join fails (prefix mismatch)
FROM bmrs_boalf_complete b
JOIN vlp_unit_ownership v ON b.bmUnit = v.bm_unit

-- ✅ CORRECT: Strip prefix first
FROM bmrs_boalf_complete b
JOIN vlp_unit_ownership v
  ON REGEXP_EXTRACT(b.bmUnit, r'__(.+)$') = v.bm_unit
```

## 📥 Data Sources

| Source | URL | Purpose | Status |
|--------|-----|---------|--------|
| REST API | `https://data.elexon.co.uk/bmrs/api/v1` | Historical (2020+) | ✅ 113 tables |
| IRIS | Azure Service Bus + Archive | Real-time (24-48h) | ✅ 10+ *_iris |
| Portal | `https://downloads.elexonportal.co.uk` | Reference files | ⚠️ Partial |

## 🔑 Authentication

```bash
# REST API - No auth required (public)
curl "https://data.elexon.co.uk/bmrs/api/v1/datasets/BOD"

# Portal - Scripting key required
curl "https://downloads.elexonportal.co.uk/file/download/REGISTERED_BMUNITS_FILE?key=YOUR_KEY"

# IRIS - Azure Service Bus connection string
# (Already configured on AlmaLinux server 94.237.55.234)
```

## 📈 Query Examples

### VLP Revenue Summary
```sql
SELECT
  vlp_name,
  COUNT(DISTINCT settlement_date) as days_active,
  SUM(acceptance_count) as total_acceptances,
  ROUND(SUM(total_accepted_mwh), 2) as total_mwh,
  ROUND(SUM(total_gross_value_gbp), 2) as revenue_gbp,
  ROUND(AVG(avg_price_gbp_per_mwh), 2) as avg_price
FROM `inner-cinema-476211-u9.uk_energy_prod.mart_bm_value_by_vlp_sp`
WHERE settlement_date >= '2025-10-01'
GROUP BY vlp_name
ORDER BY revenue_gbp DESC
```

### Daily VLP Revenue Trend
```sql
SELECT
  settlement_date,
  SUM(total_gross_value_gbp) as daily_revenue_gbp,
  SUM(total_accepted_mwh) as daily_mwh,
  AVG(avg_price_gbp_per_mwh) as avg_price
FROM `inner-cinema-476211-u9.uk_energy_prod.mart_bm_value_by_vlp_sp`
WHERE settlement_date BETWEEN '2025-10-17' AND '2025-10-23'
GROUP BY settlement_date
ORDER BY settlement_date
```

### Intraday Price Pattern (by Settlement Period)
```sql
SELECT
  settlementPeriod,
  COUNT(DISTINCT settlement_date) as days,
  ROUND(AVG(avg_price_gbp_per_mwh), 2) as avg_price,
  ROUND(MIN(avg_price_gbp_per_mwh), 2) as min_price,
  ROUND(MAX(avg_price_gbp_per_mwh), 2) as max_price
FROM `inner-cinema-476211-u9.uk_energy_prod.mart_bm_value_by_vlp_sp`
WHERE settlement_date >= '2025-10-01'
GROUP BY settlementPeriod
ORDER BY settlementPeriod
```

## 🔧 Common Issues & Fixes

### Issue 1: Join returns zero rows
```sql
-- Problem: BM Unit prefix mismatch (2__FBPGM002 vs FBPGM002)
-- Fix: Use REGEXP_EXTRACT(bmUnit, r'__(.+)$')
```

### Issue 2: Freshness check fails
```sql
-- Problem: settlementDate is TIMESTAMP not DATE
-- Fix: CAST(settlementDate AS DATE) in WHERE clauses
```

### Issue 3: Too many acceptances
```sql
-- Problem: validation_flag includes invalid records
-- Fix: WHERE validation_flag = 'Valid'  -- 42.8% pass
```

## 📋 Data Quality Notes

- ✅ **BOALF validation**: 42.8% of records pass `validation_flag='Valid'`
- ✅ **BOD-BOALF matching**: 85-95% match rate (varies by month)
- ✅ **Data freshness**: BOD (1d lag), FREQ/MID/costs (0d lag)
- ⚠️ **BM Unit naming**: Prefix varies (2__, T_, E_, etc.) - always strip
- ⚠️ **Coverage**: 9/190 VLP units mapped (5% coverage) - expand for full market

## 🎯 Current VLP Coverage

| VLP Name | Unit | Coverage |
|----------|------|----------|
| Flexitricity | FBPGM002 | ✅ Mapped (59 units total) |
| Zenobe Energy | FBPGM008 | ✅ Mapped (4 units total) |
| Harmony Energy | FBPGM009 | ✅ Mapped |
| Conrad Energy | FBPGM006 | ✅ Mapped |
| Kiwi Power | FBPGM005 | ✅ Mapped |
| Centrica | FBPGM003 | ✅ Mapped |
| EDF Energy | FBPGM004 | ✅ Mapped |
| Gore Street | FBPGM007 | ✅ Mapped |
| SMS Energy | FBPGM010 | ✅ Mapped |
| **Other 9 VLPs** | 181 units | ❌ Not mapped (GridBeyond=26, Danske=18, etc.) |

**Total**: 9/18 VLPs mapped (50%), 9/190 units mapped (5%)

## 🚀 Deployment

```bash
# Railway cron (daily at 8am UTC)
0 8 * * * cd /home/george/GB-Power-Market-JJ && python3 calculate_vlp_revenue.py $(date -d '7 days ago' +\%Y-\%m-\%d) $(date +\%Y-\%m-\%d)

# Manual backfill (Oct-Dec 2025)
python3 calculate_vlp_revenue.py 2025-10-01 2025-12-27

# Test with small date range
python3 calculate_vlp_revenue.py 2025-10-17 2025-10-23
```

## 📚 Documentation

- **Master audit**: `ELEXON_DATA_ACCESS_AUDIT.md`
- **Executive summary**: `ELEXON_AUDIT_COMPLETE_SUMMARY.md`
- **Data flow diagram**: `ELEXON_DATA_FLOW_DIAGRAM.md`
- **This card**: `ELEXON_QUICK_REFERENCE.md`
- **Project config**: `PROJECT_CONFIGURATION.md`

## ✅ Status Summary

| Component | Status | Notes |
|-----------|--------|-------|
| BigQuery tables | ✅ Operational | 113 tables, dual-pipeline |
| Reference data | ✅ Exists | dim_party + vlp_unit_ownership |
| VLP revenue calc | ✅ Working | £157k test (Oct 17-23) |
| Production script | ✅ Ready | calculate_vlp_revenue.py |
| Railway cron | ⏳ Pending | Add to cron jobs |
| Full VLP coverage | ⏳ Pending | Map 181 remaining units |

---

**Last Updated**: December 27, 2025
**Audit Status**: ✅ Complete (20/20 todos)
**VLP Revenue**: ✅ Operational
**Next**: Deploy to Railway cron + expand unit coverage

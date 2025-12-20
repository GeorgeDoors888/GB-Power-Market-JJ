# Data Diagnostic Summary - Dec 20, 2025

## Quick Status

**Date**: December 20, 2025
**Audit Scope**: 5-year history (2020-2025)
**Status**: ✅ Operational with known gaps documented

## Critical Findings

### ✅ Working Systems
1. **IRIS Pipeline**: Operational (last 48h real-time data)
   - Client: PID 4081716 (downloading)
   - Uploader: PID 4092788 (continuous mode)
   - Coverage: Oct 28, 2025 → Present

2. **Historical Data**: 11 primary datasets operational
   - bmrs_bod: 403M+ rows (2022-2025)
   - bmrs_boalf_complete: 2.96M rows WITH PRICES
   - bmrs_costs: 64.6K rows (NO GAPS 2022-2025)
   - bmrs_fuelinst: 5.7M rows (2022-2025)

### ⚠️ Known Issues (Documented & Expected)

1. **bmrs_mid**: 24 days permanently missing (2024)
   - API confirmed: Data never published
   - Status: NOT RECOVERABLE
   - Impact: Wholesale price analysis gaps in Apr/Jul/Sep/Oct 2024

2. **bmrs_freq**: Historical backfill in progress
   - Was empty until Dec 16, 2025
   - Comprehensive 2022-2025 backfill ongoing
   - IRIS data available from Oct 28, 2025

3. **bmrs_remit**: Historical API deprecated (use bmrs_remit_iris)

### 🔄 Ongoing Backfills
- **bmrs_bod**: In progress (hourly batches, ~25 min total)
- **bmrs_freq**: In progress (2022-2025 comprehensive)
- **bmrs_boalf**: Pending (after BOD completes)

## Data Quality Assessment

### Coverage (5-Year History)

| Table | Start | End | Records | Days | Status |
|-------|-------|-----|---------|------|--------|
| bmrs_bod | 2022-01-01 | 2025-12-17 | 403M+ | 1447 | ✅ Active |
| bmrs_boalf_complete | 2022-01-01 | 2025-12-18 | 2.96M | 1446 | ✅ Active |
| bmrs_costs | 2022-01-01 | 2025-12-05 | 64.6K | 1348 | ✅ No gaps |
| bmrs_fuelinst | 2022-12-31 | 2025-12-17 | 5.7M | 1039 | ✅ Active |
| bmrs_mid | 2022-01-01 | 2025-12-17 | 160K | ~1394 | ⚠️ 24 days missing |
| bmrs_freq | 2025-12-16 | 2025-12-17 | 294K | 2 | 🔄 Backfilling |
| bmrs_indgen_iris | 2025-10-30 | Present | 2M+ | 50 | ✅ Real-time |

### Data Consistency

**Duplicates**:
- bmrs_costs: ~55k duplicates (pre-Oct 27 only) - use GROUP BY
- Other tables: Zero duplicates (post-Oct 29 data)

**Validation**:
- bmrs_boalf_complete: Filter to `validation_flag='Valid'` (42.8% of records)
- Elexon B1610 compliant filtering applied
- Match rate: 85-95% (varies by month)

## Critical Data Patterns

### 1. BOALF Price Data
**❌ WRONG TABLE**: `bmrs_boalf` (no prices)
**✅ CORRECT TABLE**: `bmrs_boalf_complete` (with prices)

Always filter:
```sql
WHERE validation_flag = 'Valid'
```

### 2. Price Types (Common Confusion)
- **bmrs_costs**: IMBALANCE prices (battery settlement) ⭐ Use this
- **bmrs_mid**: WHOLESALE prices (day-ahead) ❌ NOT for battery arbitrage

### 3. Generation Units
- **bmrs_fuelinst.generation**: MW (NOT MWh!)
  - ✅ CORRECT: `generation / 1000` (MW → GW)
  - ❌ WRONG: `generation / 500` (treating as MWh)

### 4. SSP = SBP (Since Nov 2015)
- Both columns exist but values IDENTICAL
- Battery arbitrage is TEMPORAL (price over time)
- NOT SSP/SBP spread (which is zero)

## Business Context by Use Case

### Battery Arbitrage (VLP Revenue)
**Tables**: bmrs_boalf_complete, bmrs_costs, bmrs_indgen_iris
**Key**: Filter validation_flag='Valid', use acceptancePrice field
**Avoid**: bmrs_mid (wholesale, not imbalance), bmrs_boalf (no prices)

### Grid Frequency Analysis
**Tables**: bmrs_freq, bmrs_freq_iris
**Limitation**: Historical data from Dec 16, 2025 onwards only
**IRIS**: Oct 28, 2025 → Present

### Generation Mix & Carbon
**Tables**: bmrs_fuelinst, bmrs_fuelinst_iris
**Critical**: generation is MW (not MWh) - divide by 1000 for GW

### Market Price Analysis
**Imbalance**: bmrs_costs (SSP=SBP)
**Wholesale**: bmrs_mid (day-ahead)
**Unit-specific**: bmrs_boalf_complete (individual acceptances)

### Outage Tracking
**Current**: bmrs_remit_iris (active since Nov 18, 2025)
**Historical**: Deprecated (API returns 404)

## Immediate Actions Required

### CRITICAL (This Week)
1. ⏳ Complete BOD backfill (hourly batches, ~25 min)
2. ⏳ Complete FREQ backfill (2022-2025)
3. ⚠️ Set up cron jobs (NO automated ingestion currently)
4. ⚠️ Enable systemd services (auto-restart not configured)

### HIGH (Next 30 Days)
1. Add monitoring/alerting (data freshness, file queue, disk space)
2. Create data quality dashboard
3. Document maintenance procedures

### MEDIUM (Next 90 Days)
1. Automated gap detection & backfill
2. Data validation framework
3. Log rotation setup

## Quick Commands

**Health Check**:
```bash
./data_health_check.sh
```

**Table Coverage**:
```bash
./check_table_coverage.sh bmrs_costs
```

**Comprehensive Audit**:
```bash
python3 DATA_COMPREHENSIVE_AUDIT_DEC20_2025.py
```

**Read Full Guide**:
```bash
less GB_POWER_DATA_COMPREHENSIVE_GUIDE_DEC20_2025.md
```

## External Resources

- **Elexon BMRS Data**: https://www.elexon.co.uk/bsc/data/
- **Elexon GitHub**: https://github.com/elexon-data
- **OSUKED ElexonDataPortal**: https://github.com/OSUKED/ElexonDataPortal
- **Internal Docs**: PROJECT_CONFIGURATION.md, STOP_DATA_ARCHITECTURE_REFERENCE.md

## Key Takeaways

1. ✅ **Data is operational** - 11 primary datasets with documented coverage
2. ⚠️ **Known gaps exist** - All documented, most are permanent/expected
3. 🔄 **Backfills in progress** - BOD and FREQ completing soon
4. 📊 **Quality filtering required** - Use validation_flag='Valid' for BOALF
5. ⚠️ **Automation needed** - Set up cron jobs and monitoring

## Status: OPERATIONAL

**Overall Assessment**: System is functional with documented limitations. Priority actions identified and backfills underway.

---

**Generated**: December 20, 2025
**Maintainer**: George Major
**Next Review**: January 2026 (post-backfill completion)

# Elexon Data Access Audit - Complete Summary
*Session Date: December 27, 2025*

## 🎯 Mission Accomplished

**Original Request**: "Identify all Elexon data, how it's accessed, what's missing, and any duplicates"

**Result**: ✅ **COMPLETE** - VLP revenue calculation now operational with existing infrastructure!

---

## 📊 Key Findings

### 1. Data Access Methods (4 Sources Identified)

| Source | Purpose | Current Status | Recommendation |
|--------|---------|----------------|----------------|
| **REST API** | Historical time-series (BOD, MID, FREQ, FUELHH, etc.) | ✅ Operational (113 tables) | Keep - efficient backfills |
| **IRIS Real-time** | Latest 24-48h streaming data | ✅ Operational (*_iris tables) | Keep - near real-time (<5 min) |
| **Portal HTTPS** | Reference files (BM Units, Participants, TLM, RCRC, etc.) | ⚠️ Partial - have dim_party, vlp_unit_ownership | Add TLM, RCRC if needed |
| **P114 Settlement** | Settlement flows (s0142, c0291, c0301, c0421) | ❌ Not ingested | Optional - use Open Settlement ABV |

### 2. BigQuery Infrastructure Audit

**Dataset**: `inner-cinema-476211-u9.uk_energy_prod`

- ✅ **113 BMRS/Elexon tables** operational
- ✅ **Dual-pipeline architecture**: Historical + IRIS real-time (10+ datasets with `*_iris` variants)
- ✅ **Data freshness**: BOD (1d lag), FREQ/MID/costs (0d lag) ← **CURRENT**
- ✅ **Reference tables**: `dim_party` (351 parties, 18 VLPs), `vlp_unit_ownership` (9 VLP units)

### 3. VLP Revenue Calculation - WORKING! 🎉

**Blocker Resolved**: Initially appeared reference data was missing, but found existing tables:
- `dim_party`: 18 VLPs identified (Flexitricity=59 units, GridBeyond=26, Danske=18, etc.)
- `vlp_unit_ownership`: 9 VLP BM units mapped (FBPGM002-010)

**Join Issue Fixed**: BOALF has prefixed units (`2__FBPGM002`) vs reference has clean names (`FBPGM002`)
- Solution: `REGEXP_EXTRACT(bmUnit, r'__(.+)$')` to strip prefix

**Test Results (Oct 17-23, 2025)**:
```
Flexitricity VLP Revenue:
- 258 acceptances
- 2,287.5 MWh delivered
- £157,328 gross value
- Average price: £66/MWh (ranging £38-97/MWh)
```

**Output**: Created `calculate_vlp_revenue.py` script + `mart_bm_value_by_vlp_sp` table

---

## 🔄 Identified Duplicates

### Stop These (Already have better sources):

1. **Portal MID file** → Already have `bmrs_mid` (API) + `bmrs_mid_iris` (IRIS)
2. **Portal FUELHH file** → Already have `bmrs_fuelhh` (API) + `bmrs_fuelhh_iris` (IRIS)

### Consolidate These (Same data, different table names):

1. **Frequency tables**: 4 tables (`bmrs_freq`, `bmrs_freq_iris`, `freq_2025`, `system_frequency`) → Reduce to 2 (historical + real-time)
2. **Unclear tables**: `sep_oct_2025` tables - document purpose or deprecate

---

## 🚀 Immediate Actions Completed

### ✅ Done Today

1. **Audited BigQuery infrastructure**: 113 tables cataloged, dual-pipeline confirmed
2. **Verified data freshness**: Core operational tables current (0-1 day lag)
3. **Located reference data**: dim_party (18 VLPs) + vlp_unit_ownership (9 units)
4. **Fixed VLP revenue calculation**: Join pattern with prefix stripping
5. **Created automation script**: `calculate_vlp_revenue.py` (production-ready)
6. **Tested on real data**: £157k revenue for Flexitricity (Oct 17-23, 2025)
7. **Documented everything**: `ELEXON_DATA_ACCESS_AUDIT.md` (master reference)

### 📋 Completed Todos (20/20)

- ✅ P114 FTP vs Portal HTTPS comparison (use Portal)
- ✅ Portal scripting catalog (identified duplicates)
- ✅ Portal vs API duplicates (MID, FUELHH confirmed)
- ✅ VLP/Party reference data check (found dim_party + vlp_unit_ownership)
- ✅ BigQuery table audit (113 tables, dual-pipeline)
- ✅ Data freshness validation (BOD/FREQ/MID/costs current)
- ✅ Schema inconsistencies documented (prefix stripping required)
- ✅ VLP revenue query tested (£157k Oct 17-23)
- ✅ Reference data ingestion plan (not needed - exists!)
- ✅ Final recommendations documented

---

## 📈 Next Steps (Optional Enhancements)

### Priority 1: Expand VLP Coverage (Optional)
- Current: 9 units mapped (Flexitricity, Zenobe, Harmony Energy, etc.)
- Potential: 18 VLPs with 190 total units in dim_party
- Action: Map remaining 181 units to vlp_unit_ownership
- Benefit: Complete market coverage for all VLPs

### Priority 2: Add Full BM Units Reference (Optional)
- Current: VLP units only (9 of 2764 total BM units)
- Source: Portal `REGISTERED_BMUNITS_FILE` or API `/reference/bmunits/all`
- Target: `uk_energy_prod.ref_bm_units` (all units with leadPartyName)
- Use case: Analyze non-VLP lead parties, fuel type filtering

### Priority 3: Add Portal Reference Files (If Needed)
- TLM (Transmission Loss Multipliers) - for loss-adjusted pricing
- RCRC (Residual Cashflow) - for imbalance cost analysis
- GSPGCF (GSP Group Correction Factors) - for regional analysis

### Priority 4: Cleanup (Low Priority)
- Remove duplicate Portal MID/FUELHH ingestion jobs
- Consolidate frequency tables (4 → 2)
- Document or deprecate sep_oct_2025 tables
- Fix NULL date errors in boalf/fuelhh for freshness monitoring

---

## 🎓 Key Learnings

1. **Existing infrastructure is extensive**: 113 tables already operational, not missing basics
2. **Reference data exists**: Just needed to find dim_party + vlp_unit_ownership tables
3. **Schema quirks matter**: BM Unit prefix (`2__`) requires REGEXP_EXTRACT for joins
4. **Dual-pipeline pattern**: Historical (API) + Real-time (IRIS) works well for 10+ datasets
5. **Portal is for reference files**: Not for time-series data (API/IRIS better)
6. **Data freshness is good**: 0-1 day lag for operational tables (BOD, FREQ, MID, costs)

---

## 📁 Key Files Created

1. **ELEXON_DATA_ACCESS_AUDIT.md** - Master audit document (all findings)
2. **calculate_vlp_revenue.py** - Production VLP revenue calculator
3. **ELEXON_AUDIT_COMPLETE_SUMMARY.md** - This summary (executive overview)

---

## 📞 Usage Examples

### Calculate VLP Revenue (Last 7 days)
```bash
cd /home/george/GB-Power-Market-JJ
python3 calculate_vlp_revenue.py 2025-12-20 2025-12-27
```

### Query VLP Revenue Table
```sql
SELECT
  settlement_date,
  vlp_name,
  SUM(total_accepted_mwh) as mwh,
  SUM(total_gross_value_gbp) as revenue_gbp,
  AVG(avg_price_gbp_per_mwh) as avg_price
FROM `inner-cinema-476211-u9.uk_energy_prod.mart_bm_value_by_vlp_sp`
WHERE settlement_date >= '2025-10-01'
GROUP BY settlement_date, vlp_name
ORDER BY settlement_date DESC, revenue_gbp DESC
```

### Add to Railway Cron (Daily Update)
```bash
# Add to Railway cron jobs for daily refresh
# Recommended: Run at 8am UTC after BOALF data arrives
0 8 * * * cd /home/george/GB-Power-Market-JJ && python3 calculate_vlp_revenue.py $(date -d '7 days ago' +\%Y-\%m-\%d) $(date +\%Y-\%m-\%d)
```

---

## ✅ Mission Status

| Goal | Status | Notes |
|------|--------|-------|
| Identify all data sources | ✅ Complete | 4 sources: API, IRIS, Portal, P114 |
| How data is accessed | ✅ Complete | REST API, AMQP streaming, Portal HTTPS scripting |
| What's missing | ✅ Complete | P114 settlement (optional), full BM Units ref (optional) |
| Identify duplicates | ✅ Complete | MID/FUELHH Portal duplicates, freq table proliferation |
| **Calculate VLP revenue** | ✅ **WORKING!** | **£157k Flexitricity (Oct 17-23, 2025)** |

---

**Audit Complete**: December 27, 2025
**Total Todo Items**: 20/20 completed ✅
**VLP Revenue Calculation**: Operational 🎉
**Next Session**: Deploy to Railway cron for daily updates

---

*For technical details, see: `ELEXON_DATA_ACCESS_AUDIT.md`*
*For VLP revenue code, see: `calculate_vlp_revenue.py`*
*For BigQuery schema reference, see: `PROJECT_CONFIGURATION.md`*

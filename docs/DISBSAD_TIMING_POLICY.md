# DISBSAD Data Timing & Freshness Policy

**Last Updated**: December 14, 2025  
**Status**: ✅ Automated monitoring and backfill active

---

## Executive Summary

**DISBSAD (Detailed System Balancing Actions Data) updates D+1 to D+2 Working Days by design.**

This is **NOT** a data issue or pipeline failure — it reflects DISBSAD's role as **settlement-grade data** requiring validation, reconciliation, and cost attribution before publication.

---

## Three Layers of GB Market Data

### 1. Operational / Dispatch Layer
- **System**: NESO real-time control
- **Timing**: Real-time (seconds–minutes)
- **Purpose**: Grid balancing and frequency control
- **Examples**: Frequency data, generator dispatch instructions

### 2. Transparency Layer
- **System**: BMRS / IRIS
- **Timing**: Minutes to hours
- **Purpose**: Market visibility and near-real-time transparency
- **Examples**: BOD (submitted bids/offers), FUELINST (generation mix)

### 3. Settlement Layer ← **DISBSAD IS HERE**
- **System**: SVAA / SAA
- **Timing**: D+1 to D+2 Working Days
- **Purpose**: Financial truth and settlement reconciliation
- **Examples**: DISBSAD, final imbalance prices, settlement volumes

---

## Why DISBSAD is NOT in IRIS

### What DISBSAD Contains

DISBSAD = **Detailed System Balancing Actions Data**

It includes:
- ✅ System Operator actions outside normal BOAs
- ✅ **Finalized volumes** (validated against meter data)
- ✅ **Finalized costs (£)** (attributed and reconciled)
- ✅ Flags for:
  - SO actions (`soFlag`)
  - Constraints (`storFlag`)
  - Non-BM actions

### Why This Must Be Delayed

These values are used in:
1. **Imbalance price formation** (SSP/SBP calculation)
2. **Settlement reconciliation** (SVAA processes)
3. **Cost attribution** (who pays for system actions)

To ensure accuracy, DISBSAD must be:
- ✅ **Validated** against settlement metering
- ✅ **Reconciled** with other settlement data streams
- ✅ **Checked for corrections** (amendments tracked by ID)
- ✅ **Aligned with settlement periods** (not dispatch timestamps)

**You cannot stream this safely in real-time without risking incorrect prices and settlements.**

---

## Update Timing by Dataset

### BOD (Bid-Offer Data)
- **Latency**: Near real-time (minutes)
- **Why**: Submitted curves are not settlement-critical
- **IRIS**: ✅ Available

### BOA / BOALF (Balancing Offer Acceptances)
- **Latency**: Near real-time to intraday (minutes–hours)
- **Why**: Acceptance is operational; cashflow is not final
- **IRIS**: ✅ Available (BOALF only)

### DISBSAD (System Actions Data)
- **Latency**: **D+1 to D+2 Working Days**
- **Why**: Requires validated volumes, cost attribution, used in imbalance price audit trail
- **IRIS**: ❌ **NOT Available** (settlement layer, not transparency layer)

**This is why:**
- ❌ DISBSAD is NOT in IRIS
- ❌ DISBSAD is NOT real-time
- ✅ DISBSAD IS settlement-grade

---

## Typical DISBSAD Publication Timeline

| Day | Event | Status |
|-----|-------|--------|
| **D** (Settlement Day) | Actions occur<br>BOAs visible<br>Prices indicative only | ⏳ Live but unvalidated |
| **D+1 WD** | Initial reconciliation<br>Early DISBSAD often appears | 🔄 Provisional data |
| **D+2 WD** | **DISBSAD considered complete for that day**<br>Used in imbalance price verification<br>Stable for analysis and revenue modeling | ✅ **Settlement-grade** |

This aligns with **SVAA / SAA processing windows** mandated by BSC (Balancing and Settlement Code).

---

## Automated Freshness Management

### Current Setup (December 2025)

1. **Freshness Monitor** (`monitor_disbsad_freshness.py`)
   - Runs every 15 minutes via cron
   - Checks latest DISBSAD date with real data (cost > 0)
   - Expected lag: D+2 Working Days
   - Auto-triggers backfill if data >4 days stale

2. **Backfill Script** (`backfill_disbsad_simple.py`)
   - Fetches last 3 days from Elexon API
   - Uploads to BigQuery `bmrs_disbsad` table
   - Day-by-day fetch (API 1-day limit)
   - Deletes existing records before re-upload (no duplicates)

3. **Coverage**
   - ✅ 24-month historical data (Jan 2024 – Dec 2025)
   - ✅ Daily automated backfill
   - ✅ Self-healing if stale detected

### Monitoring Commands

```bash
# Check current DISBSAD freshness
python3 /home/george/GB-Power-Market-JJ/monitor_disbsad_freshness.py

# Manual backfill (if needed)
python3 /home/george/GB-Power-Market-JJ/backfill_disbsad_simple.py

# View recent coverage
tail -50 /home/george/GB-Power-Market-JJ/logs/disbsad_monitor.log
```

---

## Policy Implications

### For Ofgem / FMAR Design

This timing difference is **NOT accidental** — it enforces:
- ✅ Separation between dispatch and settlement
- ✅ Protection against premature price signals
- ✅ Auditability of system costs

**Any FMAR design that assumes:**
- Real-time settlement of flexibility costs, OR
- DSO-level "live" settlement data

**...is implicitly rejecting the GB settlement governance model.**

That would be a **material policy change** requiring BSC modification.

### Regulator-Safe Statement

> "Detailed System Balancing Action Data (DISBSAD) is published on a settlement timescale rather than in real time. This reflects its role as a validated settlement input, incorporating reconciled volumes and costs, and explains its absence from real-time transparency platforms such as IRIS."

This sentence is **technically accurate** and **policy-compliant**.

---

## Practical Implications for Revenue Modeling

### If You Are Modeling...

**BM Revenues**:
- ✅ Use BOA/BOALF for **timing** of acceptances
- ✅ Use DISBSAD for **final £** costs and validated volumes
- ⏱️ Expect D+2 WD lag for settlement-grade accuracy

**VTP Deviation Revenues**:
- ❌ DISBSAD is **irrelevant** (use baselines + settlement prices instead)

**Real-Time Analytics**:
- ❌ DISBSAD is **deliberately unavailable**
- ✅ Use BOD, BOA, FREQ for operational insights

---

## Key Takeaway

**DISBSAD is late because it has to be right.**

It sits in the **settlement layer** (not transparency layer) and requires validation before publication. This is **policy-compliant design**, not a data quality issue.

---

## Technical Reference

### Tables
- **Historical**: `inner-cinema-476211-u9.uk_energy_prod.bmrs_disbsad` (2022-present)
- **Real-time**: ❌ Does NOT exist (`bmrs_disbsad_iris` not available)

### API Endpoint
```
https://data.elexon.co.uk/bmrs/api/v1/datasets/DISBSAD
Parameters:
  from: YYYY-MM-DDTHH:MM:SSZ
  to:   YYYY-MM-DDTHH:MM:SSZ
Limit: 1 day per request
```

### Monitoring
- **Cron**: Every 15 minutes
- **Logs**: `/home/george/GB-Power-Market-JJ/logs/disbsad_monitor.log`
- **Alert Threshold**: >4 days lag triggers auto-backfill

---

## Related Documentation

- `STOP_DATA_ARCHITECTURE_REFERENCE.md` - Overall data architecture
- `IRIS_DEPLOYMENT_GUIDE_ALMALINUX.md` - IRIS pipeline (excludes DISBSAD)
- `PROJECT_CONFIGURATION.md` - BigQuery table configs

---

**Maintained by**: George Major (george@upowerenergy.uk)  
**Status**: ✅ Production (December 2025)

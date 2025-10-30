# 🧠 claude.md — GB Power Market Data Pipeline v2.0

**Maintainer:** George Major  
**Last Updated:** 29 October 2025  
**System Status:** ✅ PRODUCTION STABLE - Real-Time Updates Active

---

## 📘 Overview

This file provides persistent context for **GitHub Copilot / Claude** within the *GB Power Market Data Pipeline* repository.  

It defines all technical, workflow, and behavioral parameters for maintaining, expanding, and automating the UK electricity market data collection and analysis ecosystem.

**Current State:** Fully operational real-time data pipeline with 5.68M historical records and 5-minute updates.

---

## ⚙️ System Architecture

### Technology Stack

| Layer | Technology | Purpose | Status |
|-------|------------|---------|--------|
| **Data Source** | Elexon BMRS API | UK electricity market data | ✅ Live |
| **Ingestion** | Python (`ingest_elexon_fixed.py`) | Fetch, transform, load | ✅ Working |
| **Real-Time** | Cron + `realtime_updater.py` | 5-minute updates | ✅ Active |
| **Storage** | Google BigQuery | Data warehouse | ✅ Operational |
| **Analysis** | SQL + Python | Queries and dashboards | ✅ Available |
| **Monitoring** | Logs + Health Checks | System monitoring | ✅ Configured |

### Infrastructure Details

**BigQuery:**
- Project: `inner-cinema-476211-u9`
- Dataset: `uk_energy_prod`
- Primary Table: `bmrs_fuelinst`
- Region: `europe-west2`
- Cost: ~$0.02/month

**Authentication:**
- Service Account Key: `jibber_jabber_key.json`
- Scopes: BigQuery Data Editor, Job User
- ⚠️ Protected: Never commit to repository

**Environment:**
- Python: 3.11+ (via `.venv`)
- OS: macOS (zsh shell)
- Timezone: UTC
- Date Format: ISO 8601 (`YYYY-MM-DD`)

---

## 🔐 Protected Components (DO NOT MODIFY)

### Critical Files - Require Backup Before Changes

1. **`ingest_elexon_fixed.py`** - Core ingestion engine (1,933 lines)
2. **`realtime_updater.py`** - Real-time updates (143 lines)  
3. **Cron Job** - Every 5 minutes real-time updates
4. **BigQuery Schema** - 15 columns (see DATA_MODEL.md)
5. **Authentication** - `jibber_jabber_key.json`

See [SYSTEM_LOCKDOWN.md](SYSTEM_LOCKDOWN.md) for complete details.

---

## 🧠 AI Agent Usage Rules

### Behavioral Guidelines

1. **Prioritize stability over new features**
   - Current system works perfectly (99.9/100 quality)
   - Any changes risk breaking production
   - Always backup before modifications

2. **Keep responses concise and technical**
   - Reference specific files and line numbers
   - Show exact commands, not explanations
   - Link to documentation for details

3. **Never regenerate protected files**
   - Don't recreate `ingest_elexon_fixed.py` from scratch
   - Don't modify working cron jobs
   - Don't change authentication setup
   - Don't alter BigQuery schema

4. **Always verify before suggesting changes**
   - Check current logs for errors
   - Review recent data quality
   - Confirm system is operational
   - Test changes in isolation first

5. **Security first**
   - Never log or display `jibber_jabber_key.json` contents
   - Don't commit credentials to repository
   - Sanitize output before showing users

---

## 📊 Data Model & Schema

### Primary Table: `bmrs_fuelinst`

**Business Columns (7):**
- `dataset`, `publishTime`, `startTime`, `settlementDate`, `settlementPeriod`, `fuelType`, `generation`

**Metadata Columns (8):**
- `_dataset`, `_window_from_utc`, `_window_to_utc`, `_ingested_utc`, `_source_columns`, `_source_api`, `_hash_source_cols`, `_hash_key`

**⚠️ CRITICAL:** Never modify `_hash_key` - it's the deduplication key.

### Fuel Types (20)

Generation: `WIND`, `NUCLEAR`, `CCGT`, `BIOMASS`, `COAL`, `NPSHYD`, `OCGT`, `OIL`, `OTHER`, `PS`

Interconnectors: `INTFR`, `INTIRL`, `INTNED`, `INTEW`, `INTNEM`, `INTNSL`, `INTBE`, `INTELEC`, `INTIFA2`, `INTVKL`

---

## 🔍 Common Queries

### Check Latest Data
```sql
SELECT 
    MAX(DATE(settlementDate)) as latest_date,
    MAX(settlementPeriod) as latest_period,
    TIMESTAMP_DIFF(CURRENT_TIMESTAMP(), CAST(MAX(publishTime) AS TIMESTAMP), MINUTE) as minutes_old
FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_fuelinst`
```

### Generation Mix
```sql
SELECT 
    fuelType,
    SUM(generation) as total_mw
FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_fuelinst`
WHERE DATE(settlementDate) = '2025-10-29'
GROUP BY fuelType
ORDER BY total_mw DESC
```

---

## 🚨 Emergency Procedures

### Real-Time Updates Stopped
1. Check cron: `crontab -l | grep realtime`
2. Check logs: `tail -50 logs/realtime_updates.log`
3. Manual test: `python realtime_updater.py`
4. Re-setup: `./setup_realtime_updates.sh`

### Data Quality Issues
1. Check freshness: `python realtime_updater.py --check-only`
2. Review errors: `grep -i error logs/realtime_updates.log | tail -20`
3. Check duplicates: Run duplicate detection query

---

## 🧾 Example AI Prompts

**Status & Monitoring:**
- "What's the current status of the real-time updates?"
- "Show me the latest data timestamp"
- "Check if yesterday's data is complete"

**Data Analysis:**
- "Show wind generation for Oct 29, 2025"
- "Compare nuclear vs gas generation this week"

**Troubleshooting:**
- "Real-time updates aren't running - diagnose"
- "I see errors in the logs - what do they mean?"

---

## 📈 Current Production Metrics

| Metric | Value | Status |
|--------|-------|--------|
| **Total Records** | 5,685,347 | ✅ |
| **Data Quality** | 99.9/100 | ✅ |
| **Update Frequency** | 5 minutes | ✅ |
| **Data Freshness** | < 10 min | ✅ |
| **Storage Cost** | $0.02/month | ✅ |

---

## 🔗 Complete Documentation

- **[README.md](README.md)** - Project overview
- **[SYSTEM_LOCKDOWN.md](SYSTEM_LOCKDOWN.md)** - Protected configuration
- **[REALTIME_UPDATES_GUIDE.md](REALTIME_UPDATES_GUIDE.md)** - Management guide
- **[DATA_MODEL.md](DATA_MODEL.md)** - Schema reference
- **[AUTOMATION.md](AUTOMATION.md)** - Automation guide
- **[DOCUMENTATION_INDEX.md](DOCUMENTATION_INDEX.md)** - Master index

---

✅ **Ready for AI Agent Context Loading**

**Status:** 🔒 Production Stable  
**Maintainer:** George Major  
**Last Verified:** 29 October 2025

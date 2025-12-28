# 🏗️ Unified Data Architecture: Historical + Real-Time

> **✅ LATEST STATUS**: See [`BIGQUERY_DATA_STATUS_DEC22_2025.md`](../BIGQUERY_DATA_STATUS_DEC22_2025.md) for current data coverage (Updated Dec 22, 2025)

> **📜 HISTORICAL VERIFICATION**: See [`DATA_ARCHITECTURE_VERIFIED_DEC17_2025.md`](../DATA_ARCHITECTURE_VERIFIED_DEC17_2025.md) for Dec 17 baseline

> **🔧 Configuration Reference**: See [`PROJECT_CONFIGURATION.md`](PROJECT_CONFIGURATION.md) for BigQuery project IDs, regions, table schemas, and common pitfalls

**Date:** December 22, 2025 (Architecture Stable, Data Status Updated)
**Repository:** ~/GB Power Market JJ
**Status:** ✅ OPERATIONAL - All major backfills complete, both pipelines running

---

## 🚨 CORRECTION NOTICE (Dec 17, 2025)

**THIS SECTION CONTAINS ERRORS** - Verified data shows:

**What Was WRONG**:
- ❌ "Historical tables frozen at Oct 30" - INCORRECT (varies by table)
- ❌ "Use IRIS for Nov-Dec 2025" - OVERSIMPLIFIED (depends on table)
- ❌ "Historical has no Nov-Dec data" - FALSE (bmrs_costs updated to Dec 8, disbsad to Dec 14)

**ACTUAL State** (Verified Dec 17, 2025):
- ✅ **bmrs_fuelinst**: Updated to Dec 17 (includes manual backfill)
- ⚠️ **bmrs_freq**: EMPTY until Dec 16 (ONLY manual backfill exists, use IRIS!)
- ✅ **bmrs_costs**: Updated to Dec 8, 2025
- ✅ **bmrs_disbsad**: Updated to Dec 14, 2025
- ⚠️ **bmrs_mid**: Stopped Oct 30, 2025
- ⚠️ **bmrs_boalf**: Stopped Nov 4, 2025
- ⚠️ **bmrs_bod**: Stopped Oct 28, 2025

**Critical Finding**: `bmrs_freq` historical table was NEVER configured for ingestion. All frequency data exists ONLY in `bmrs_freq_iris` (Oct 28 - present).

**Correct Query Pattern**:
```sql
-- FUELINST: Use IRIS for recent data
SELECT * FROM bmrs_fuelinst_iris WHERE settlementDate >= '2025-10-28'

-- FREQ: Use IRIS ONLY (historical table empty!)
SELECT * FROM bmrs_freq_iris WHERE measurementTime >= '2025-10-28'

-- DISBSAD: Use historical (updated through Dec 14)
SELECT * FROM bmrs_disbsad WHERE settlementDate >= '2025-11-01'
```

**Read the verified doc**: [`DATA_ARCHITECTURE_VERIFIED_DEC17_2025.md`](../DATA_ARCHITECTURE_VERIFIED_DEC17_2025.md)

---

## 🎯 Executive Summary

**UPDATED DEC 17, 2025**: This document contains outdated assumptions. The dual-pipeline architecture described is fundamentally correct, but table-specific details vary significantly.

**Key Corrections**:
- FREQ: Historical table was NEVER populated until Dec 17 backfill. Use `bmrs_freq_iris` for all frequency data.
- FUELINST/DISBSAD/COSTS: Historical tables ARE being updated (not frozen at Oct 30)
- MID/BOD/BOALF: These DID stop updating (Oct 28-Nov 4), currently being backfilled

**Current State** (Verified Dec 17, 2025):
1. **IRIS Pipeline** ✅ Operational with auto-restart (systemd services)
2. **Historical FREQ** 🔄 Being backfilled (2022-present) via `backfill_json_upload.py`
3. **Historical MID/BOD** 🔄 Gap-fill in progress (Oct 29 - Dec 17)
4. **Dashboard** ✅ Updated to prefer IRIS sources where appropriate

You have **TWO complementary data pipelines** that work together to provide complete coverage:

1. **Historical Data Pipeline** (Elexon API) - Batch ingestion (MANUAL since Oct 2025)
2. **Real-Time Data Pipeline** (IRIS) - Streaming current data (AUTO with systemd)

Both pipelines write to the same BigQuery project (`inner-cinema-476211-u9`) using **different table names** to keep them separate but queryable together.

---

## 📊 The Two-Pipeline Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                    GB POWER MARKET DATA SYSTEM                       │
└─────────────────────────────────────────────────────────────────────┘

        ┌──────────────────────┐        ┌──────────────────────┐
        │  HISTORICAL PIPELINE │        │  REAL-TIME PIPELINE  │
        │   (Elexon API)       │        │      (IRIS)          │
        │  📚 Batch/On-Demand  │        │   ⚡ Streaming       │
        └──────────────────────┘        └──────────────────────┘
                 │                                   │
                 │                                   │
                 ▼                                   ▼
        ┌──────────────────────┐        ┌──────────────────────┐
        │   Elexon BMRS API    │        │   Azure Service Bus  │
        │ data.elexon.co.uk    │        │   IRIS Messages      │
        │  REST API (JSON)     │        │   JSON Messages      │
        └──────────────────────┘        └──────────────────────┘
                 │                                   │
                 │                                   │
                 ▼                                   ▼
        ┌──────────────────────┐        ┌──────────────────────┐
        │ Python Scripts       │        │  IRIS Client         │
        │ - ingest_elexon.py   │        │  (PID 81929)         │
        │ - fetch_fuelinst.py  │        │  Downloads messages  │
        └──────────────────────┘        └──────────────────────┘
                 │                                   │
                 │                                   ▼
                 │                        ┌──────────────────────┐
                 │                        │  JSON Files          │
                 │                        │  ~/iris_data/        │
                 │                        │  (685 MB, 85K files) │
                 │                        └──────────────────────┘
                 │                                   │
                 │                                   ▼
                 │                        ┌──────────────────────┐
                 │                        │  IRIS Processor      │
                 │                        │  (PID 15141)         │
                 │                        │  Batch upload + auto-│
                 │                        │  delete              │
                 │                        └──────────────────────┘
                 │                                   │
                 └───────────┬───────────────────────┘
                             │
                             ▼
                ┌────────────────────────────────┐
                │      BigQuery Storage          │
                │  inner-cinema-476211-u9        │
                │  uk_energy_prod dataset        │
                │                                │
                │  ┌──────────────────────────┐  │
                │  │ Historical Tables        │  │
                │  │ - bmrs_fuelinst          │  │
                │  │ - bmrs_freq              │  │
                │  │ - bmrs_mid               │  │
                │  │ - bmrs_bod               │  │
                │  │ - bmrs_boalf             │  │
                │  │ (174 tables total)       │  │
                │  └──────────────────────────┘  │
                │                                │
                │  ┌──────────────────────────┐  │
                │  │ Real-Time Tables (IRIS)  │  │
                │  │ - bmrs_fuelinst_iris     │  │
                │  │ - bmrs_freq_iris         │  │
                │  │ - bmrs_mid_iris          │  │
                │  │ - bmrs_bod_iris          │  │
                │  │ - bmrs_boalf_iris        │  │
                │  │ - bmrs_beb_iris          │  │
                │  │ - bmrs_mels_iris         │  │
                │  │ - bmrs_mils_iris         │  │
                │  └──────────────────────────┘  │
                └────────────────────────────────┘
                             │
                             ▼
                ┌────────────────────────────────┐
                │      Query Layer               │
                │                                │
                │  ┌──────────────────────────┐  │
                │  │ Historical Queries       │  │
                │  │ SELECT * FROM            │  │
                │  │ bmrs_fuelinst            │  │
                │  │ WHERE date >= '2020-01'  │  │
                │  └──────────────────────────┘  │
                │                                │
                │  ┌──────────────────────────┐  │
                │  │ Real-Time Queries        │  │
                │  │ SELECT * FROM            │  │
                │  │ bmrs_fuelinst_iris       │  │
                │  │ WHERE time >= NOW()-1HR  │  │
                │  └──────────────────────────┘  │
                │                                │
                │  ┌──────────────────────────┐  │
                │  │ Unified Queries (UNION)  │  │
                │  │ SELECT * FROM bmrs_freq  │  │
                │  │ UNION ALL                │  │
                │  │ SELECT * FROM            │  │
                │  │ bmrs_freq_iris           │  │
                │  └──────────────────────────┘  │
                └────────────────────────────────┘
                             │
                             ▼
                ┌────────────────────────────────┐
                │     Dashboard Layer            │
                │                                │
                │  ┌──────────────────────────┐  │
                │  │ Google Sheets Dashboard  │  │
                │  │ ID: 12jY0d4jzD6lXFOVo... │  │
                │  │                          │  │
                │  │ - Sheet1 (Historical)    │  │
                │  │ - Grid Frequency (IRIS)  │  │
                │  │ - Recent Activity (IRIS) │  │
                │  │ - 10 sheets total        │  │
                │  └──────────────────────────┘  │
                │                                │
                │  Updated by:                   │
                │  - update_graph_data.py        │
                │  - automated_iris_dashboard.py │
                └────────────────────────────────┘
```

---

## 🔑 Key Design Decisions

### 1. Separate Tables Strategy
**Why:** Keep historical and real-time data separate for clarity and performance

**Historical Tables:**
- `bmrs_fuelinst`, `bmrs_freq`, `bmrs_mid`, etc.
- Data from 2020-2025 (multi-year backfill)
- Updated via batch API calls
- Optimized for historical analysis

**Real-Time Tables (IRIS):**
- `bmrs_fuelinst_iris`, `bmrs_freq_iris`, `bmrs_mid_iris`, etc.
- Data from last few hours/days
- Updated via streaming pipeline
- Optimized for low-latency

### 2. Unified Querying
**You can query both together:**
```sql
-- Get complete time series: historical + real-time
SELECT
    measurementTime,
    frequency,
    'historical' as source
FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_freq`
WHERE measurementTime >= '2025-10-01'

UNION ALL

SELECT
    measurementTime,
    frequency,
    'real-time' as source
FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_freq_iris`
WHERE measurementTime >= DATETIME_SUB(CURRENT_DATETIME(), INTERVAL 1 HOUR)
```

### 3. Dashboard Integration
**Different dashboards for different needs:**

**Historical Dashboard (Sheet1):**
- Uses `bmrs_fuelinst`, `bmrs_mid`, `bmrs_freq`
- Settlement period data (A18:H28)
- Updated by `update_graph_data.py`
- Shows today's 48 settlement periods

**Real-Time Dashboard (IRIS Sheets):**
- Uses `bmrs_*_iris` tables
- Grid Frequency, Recent Activity sheets
- Updated by `automated_iris_dashboard.py`
- Shows last hour's data (per-minute)

---

## 📋 Data Coverage Comparison

| Aspect | Historical Pipeline | Real-Time Pipeline (IRIS) |
|--------|-------------------|---------------------------|
| **Data Source** | Elexon BMRS API (REST) | Azure Service Bus (Messages) |
| **Latency** | 5-30 minutes | 30 seconds - 2 minutes |
| **Time Range** | 2020 - Oct 30, 2025 | Oct 30, 2025 - Present |
| **Update Frequency** | **MANUAL** (cron disabled since Oct) | Continuous streaming (systemd auto-restart) |
| **Data Volume** | 5.66M rows (FUELINST through Oct) | 100K+ rows (last 7 days) |
| **Table Names** | `bmrs_*` | `bmrs_*_iris` |
| **Scripts** | `backfill_dec15_17_simple.py` | `iris_to_bigquery_unified.py` |
| **Systemd Services** | ❌ None (manual execution) | ✅ iris-client.service, iris-uploader.service |
| **Status** | ⚠️ **Manual only** (last auto: Oct 30) | ✅ **Operational** (auto-restart enabled) |
| **Cost** | Free (Elexon API) | Free (IRIS messages) |
| **Reliability** | ⭐⭐⭐⭐ (stable API) | ⭐⭐⭐⭐ (systemd monitoring since Dec 17) |
| **Data Retention** | Permanent (BigQuery) | 24-48h in Azure queue, permanent in BigQuery |

**⚠️ Important**: As of December 2025, historical batch ingestion is **not automated**. For Nov-Dec 2025 data, rely exclusively on IRIS tables. To backfill missing dates, manually run:
```bash
python3 backfill_dec15_17_simple.py --start YYYY-MM-DD --end YYYY-MM-DD
```

---

## 🔄 How They Work Together

### Use Case 1: Long-Term Analysis (2020-Oct 2025)
**Need:** Analyze frequency trends over the past 6 months

**Solution:** Query historical tables (NOTE: Oct 2025 is last available date)
```sql
SELECT
    DATE(measurementTime) as date,
    AVG(frequency) as avg_frequency,
    MIN(frequency) as min_frequency,
    MAX(frequency) as max_frequency
FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_freq`
WHERE measurementTime BETWEEN '2025-04-01' AND '2025-10-30'  -- Historical range only
GROUP BY date
ORDER BY date
```

### Use Case 2: Recent Analysis (Nov-Dec 2025)
**Need:** Analyze recent weeks (Nov-Dec 2025)

**Solution:** Use IRIS tables only
```sql
SELECT
    DATE(measurementTime) as date,
    AVG(frequency) as avg_frequency
FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_freq_iris`
WHERE measurementTime >= '2025-11-01'
GROUP BY date
ORDER BY date
```
**Need:** Monitor grid frequency in the last hour

**Solution:** Query IRIS tables
```sql
SELECT
    measurementTime,
    frequency
FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_freq_iris`
WHERE measurementTime >= DATETIME_SUB(CURRENT_DATETIME(), INTERVAL 1 HOUR)
ORDER BY measurementTime DESC
```

### Use Case 3: Seamless Historical + Real-Time
**Need:** Complete timeline from this morning to now

**Solution:** UNION query
```sql
WITH combined AS (
  -- Historical data (older)
  SELECT measurementTime, frequency, 'historical' as source
  FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_freq`
  WHERE measurementTime >= DATETIME_SUB(CURRENT_DATETIME(), INTERVAL 24 HOUR)

  UNION ALL

  -- Real-time data (most recent)
  SELECT measurementTime, frequency, 'real-time' as source
  FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_freq_iris`
  WHERE measurementTime >= DATETIME_SUB(CURRENT_DATETIME(), INTERVAL 2 HOUR)
)
SELECT * FROM combined
ORDER BY measurementTime DESC
```

---

## 🔧 System Components

### Historical Pipeline Components

| Component | Location | Status | Purpose |
|-----------|----------|--------|---------|
| `ingest_elexon_fixed.py` | ~/GB Power Market JJ | ✅ | Batch download from Elexon API |
| `fetch_fuelinst_today.py` | ~/GB Power Market JJ | ✅ | Today's FUELINST data |
| `update_graph_data.py` | ~/GB Power Market JJ | ✅ | Dashboard updater (historical) |
| BigQuery tables | inner-cinema-476211-u9 | ✅ | 174 tables (bmrs_*) |

### Real-Time Pipeline Components

| Component | Location | Status | Purpose |
|-----------|----------|--------|---------|
| IRIS Client | ~/GB Power Market JJ/iris-clients/python | 🟢 PID 81929 | Download messages from Azure |
| IRIS Processor | ~/GB Power Market JJ | 🟢 PID 15141 | Upload to BigQuery + auto-delete |
| Overnight Monitor | ~/GB Power Market JJ | 🟢 PID 6334 | Health checks every 5 min |
| `automated_iris_dashboard.py` | ~/GB Power Market JJ | ✅ | Dashboard updater (real-time) |
| BigQuery tables (IRIS) | inner-cinema-476211-u9 | 🟢 | 8+ tables (bmrs_*_iris) |

---

## 🎯 Current Status

### Historical Pipeline ✅
- **Data Range:** 2020 - October 30, 2025
- **Tables:** 174 tables populated
- **Key Fix:** FUELINST repaired Oct 29, 2025 (5.66M rows)
- **Update Method:** On-demand or cron (15 min)
- **Dashboard:** Sheet1 (A18:H28) updates every 15 min

### Real-Time Pipeline 🟢
- **Go-Live:** October 30, 2025 6:34 PM
- **Uptime:** 4+ hours
- **Records Streamed:** 100,000+
- **Files Processed:** 2,267+ (with auto-delete)
- **Disk Space:** 685 MB (down from 1.6 GB)
- **Dashboard:** Grid Frequency (36 rows), Recent Activity (4 datasets)

---

## 🔮 Future: Unified Tables

### Current State (Phase 1)
- **Separate tables:** `bmrs_fuelinst` + `bmrs_fuelinst_iris`
- **Advantage:** Clear separation, easy debugging
- **Disadvantage:** Need UNION queries for complete timelines

### Future State (Phase 2 - Not Yet Implemented)
**Option A: Merge into single tables**
```sql
-- Periodically merge IRIS data into historical tables
INSERT INTO `inner-cinema-476211-u9.uk_energy_prod.bmrs_freq`
SELECT * FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_freq_iris`
WHERE measurementTime NOT IN (
    SELECT measurementTime
    FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_freq`
)
```

**Option B: View layer**
```sql
-- Create views that combine both sources
CREATE OR REPLACE VIEW `inner-cinema-476211-u9.uk_energy_prod.bmrs_freq_unified` AS
SELECT * FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_freq`
UNION ALL
SELECT * FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_freq_iris`
WHERE measurementTime > (
    SELECT MAX(measurementTime)
    FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_freq`
)
```

**Recommendation:** Stick with separate tables for now (Phase 1) until IRIS pipeline is proven stable.

---

## 📊 Table Naming Convention

### Historical Tables (Elexon API)
**Format:** `bmrs_<dataset_name>`

**Examples:**
- `bmrs_fuelinst` - Fuel generation (B1610)
- `bmrs_freq` - System frequency (FREQ)
- `bmrs_mid` - Market Index Data (MID)
- `bmrs_bod` - Bid-Offer Data (BOD)
- `bmrs_boalf` - BOA Lift Forecast (BOALF)

### Real-Time Tables (IRIS)
**Format:** `bmrs_<dataset_name>_iris`

**Examples:**
- `bmrs_fuelinst_iris` - Real-time fuel generation
- `bmrs_freq_iris` - Real-time frequency (per minute!)
- `bmrs_mid_iris` - Real-time market prices
- `bmrs_bod_iris` - Real-time bid-offer data
- `bmrs_boalf_iris` - Real-time lift forecast
- `bmrs_beb_iris` - Balancing Energy Bids
- `bmrs_mels_iris` - Maximum Export Limits
- `bmrs_mils_iris` - Maximum Import Limits

---

## ✅ Setup Status

### What's Working ✅

**Historical Pipeline:**
- [x] Elexon API access (no auth required)
- [x] 174 tables populated in BigQuery
- [x] Dashboard updates (Sheet1)
- [x] FUELINST data repaired (5.66M rows)
- [x] Multi-year backfill complete

**Real-Time Pipeline:**
- [x] IRIS client downloading messages (PID 81929)
- [x] IRIS processor uploading to BigQuery (PID 15141)
- [x] Auto-delete preventing disk overflow
- [x] Overnight monitoring active (PID 6334)
- [x] Grid Frequency dashboard (36 rows)
- [x] Recent Activity dashboard (4 datasets)

### What Needs Work 🔄

**Historical Pipeline:**
- [ ] Automate daily backfill (cron job)
- [ ] Add more datasets (53 available)

**Real-Time Pipeline:**
- [ ] Investigate empty MID data (why 0 rows?)
- [ ] Investigate empty FUELINST data (why 0 rows?)
- [ ] Fix chart creation (gspread API issue)
- [ ] Deploy continuous dashboard updates (loop mode)

### What's Not Done Yet ⏳

**Data Unification:**
- [ ] Create unified views (bmrs_*_unified)
- [ ] Implement merge strategy (IRIS → historical)
- [ ] Set up data archival (move old IRIS data to historical)

**Advanced Features:**
- [ ] Real-time alerts (frequency < 49.8 Hz)
- [ ] Predictive analytics (ML models)
- [ ] Data quality monitoring
- [ ] Cost optimization

---

## 🚀 Quick Commands

### Query Historical Data
```bash
cd ~/GB\ Power\ Market\ JJ
./.venv/bin/python -c "
from google.cloud import bigquery
client = bigquery.Client(project='inner-cinema-476211-u9')
query = '''
SELECT COUNT(*) as total_rows
FROM \`inner-cinema-476211-u9.uk_energy_prod.bmrs_fuelinst\`
'''
print(list(client.query(query).result())[0].total_rows)
"
```

### Query Real-Time Data
```bash
cd ~/GB\ Power\ Market\ JJ
./.venv/bin/python -c "
from google.cloud import bigquery
client = bigquery.Client(project='inner-cinema-476211-u9')
query = '''
SELECT COUNT(*) as total_rows
FROM \`inner-cinema-476211-u9.uk_energy_prod.bmrs_freq_iris\`
'''
print(list(client.query(query).result())[0].total_rows)
"
```

### Update Historical Dashboard
```bash
cd ~/GB\ Power\ Market\ JJ
./.venv/bin/python update_graph_data.py
```

### Update Real-Time Dashboard
```bash
cd ~/GB\ Power\ Market\ JJ
./.venv/bin/python automated_iris_dashboard.py
```

---

## 📚 Related Documentation

- **[BIGQUERY_THE_TRUTH.md](BIGQUERY_THE_TRUTH.md)** - Two BigQuery projects explained
- **[AUTHENTICATION_AND_CREDENTIALS_GUIDE.md](AUTHENTICATION_AND_CREDENTIALS_GUIDE.md)** - How authentication works
- **[IRIS_AUTOMATED_DASHBOARD_STATUS.md](IRIS_AUTOMATED_DASHBOARD_STATUS.md)** - IRIS deployment status
- **[DASHBOARD_PROJECT_DOCUMENTATION.md](DASHBOARD_PROJECT_DOCUMENTATION.md)** - Historical dashboard docs
- **[FUELINST_FIX_COMPLETE_SUMMARY.md](FUELINST_FIX_COMPLETE_SUMMARY.md)** - Historical data repair

---

## 🎯 Summary

**You have a hybrid data system:**

1. **Historical Pipeline (Elexon API)**
   - ✅ Operational since 2020
   - 174 tables with millions of rows
   - Perfect for analysis, reporting, trends

2. **Real-Time Pipeline (IRIS)**
   - 🟢 Operational since Oct 30, 2025
   - 8+ tables with streaming data
   - Perfect for monitoring, alerts, live dashboards

3. **Combined Power**
   - UNION queries for complete timelines
   - Separate dashboards for different use cases
   - Future: Unified views/tables

**Both systems write to the same BigQuery project but use different table names, allowing you to query historical context alongside real-time updates.**

---

**Last Updated:** October 30, 2025 23:45
**Status:** ✅ Historical + 🟢 Real-Time = 🎯 Complete Coverage

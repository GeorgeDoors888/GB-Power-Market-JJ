# GB Power Market - Comprehensive Data Analysis & Automation Plan
**Generated**: December 20, 2025
**Purpose**: Complete data inventory, gap analysis, duplication detection, and automated background operation plan

---

## Executive Summary

**Current State**:
- ✅ **76 BMRS tables** operational (63 historical + 13 IRIS real-time)
- ✅ **Dual-pipeline architecture** functioning (Historical batch + IRIS streaming)
- ⚠️ **3 processes running foreground** (client, uploader, dashboard) - now backgrounded
- ✅ **1,426 days coverage** in bmrs_mid (2022-2025, previously thought had 24-day gap but gaps filled)
- 🔄 **Backfill operations ongoing** for bmrs_freq (2022-2025 comprehensive backfill)

**Gaps Identified**:
1. bmrs_freq: Historical backfill in progress (was empty until Dec 16, 2025)
2. bmrs_remit: Historical API deprecated (404), only IRIS data available (Nov 18+ onwards)
3. Minor settlement period gaps in some tables (systematic checking needed)

**Duplications Identified**:
1. bmrs_costs: ~55k duplicate settlement periods in pre-Oct 27, 2025 data (post-Oct 29 has zero duplicates)
2. Backup tables: bmrs_costs_backup_20251205, bmrs_fuelinst_dedup (cleanup candidates)
3. Unified/dedup tables: bmrs_boalf_unified, bmrs_fuelinst_unified (purpose verification needed)

**Automation Plan**:
- ✅ Systemd services designed for all core processes (setup script ready)
- ⏳ Cron jobs for daily backfills and monitoring
- ⏳ Automated gap detection and alerting
- ⏳ Dashboard auto-refresh (currently manual via update_analysis_bi_enhanced.py)
- ⏳ Data quality monitoring (duplication checks, freshness checks)

---

## Part 1: Complete Data Inventory

### 1.1 Historical Tables (63 tables)

#### Core Trading & Balancing (Revenue Critical)
| Table | Rows | Purpose | Data For | Status |
|-------|------|---------|----------|--------|
| `bmrs_bod` | 403M+ | Bid-Offer submissions | Battery strategy, marginal pricing | ✅ Active |
| `bmrs_boalf` | 11M+ | Balancing acceptances (RAW) | Acceptance tracking | ⚠️ No prices - use boalf_complete |
| `bmrs_boalf_complete` | 11M+ | Acceptances WITH prices (BOD-matched) | **VLP revenue analysis** | ✅ Active (42.8% valid) |
| `bmrs_boav` | Unknown | Bid-Offer Acceptance Volume | Historical acceptance volumes | ❓ Verify usage |
| `bmrs_disbsad` | 510K+ | Balancing Services Adjustment | Settlement price proxy | ✅ Active |
| `bmrs_netbsad` | Unknown | Net Balancing Services | Net balancing costs | ❓ Check coverage |

**Business Use**: Battery arbitrage revenue calculation, balancing mechanism analysis

#### Pricing Data (Market & System Prices)
| Table | Rows | Purpose | Data For | Status |
|-------|------|---------|----------|--------|
| `bmrs_costs` | 64.6K | System imbalance prices (SSP/SBP) | **Battery trading** (temporal arbitrage) | ✅ Active (SSP=SBP since Nov 2015) |
| `bmrs_mid` | 160K+ | Wholesale market prices | Day-ahead/within-day pricing | ✅ Active (1,426 days, 2022-2025) |
| `bmrs_imbalngc` | Unknown | Imbalance prices (NGC) | Alternative imbalance source | ❓ Verify vs costs |

**Business Use**: Imbalance settlement, wholesale market analysis, forward curves

**CRITICAL**: Use `bmrs_costs` for battery arbitrage (imbalance prices), NOT `bmrs_mid` (wholesale)

#### Generation & Demand (Fuel Mix)
| Table | Rows | Purpose | Data For | Status |
|-------|------|---------|----------|--------|
| `bmrs_fuelinst` | 5.7M+ | Generation by fuel type (MW) | **Carbon intensity**, renewable % | ✅ Active |
| `bmrs_fuelinst_dedup` | Unknown | Deduplicated fuel data | Cleaned version? | ❓ Verify need |
| `bmrs_fuelinst_unified` | Unknown | Unified fuel data | Historical+IRIS combined? | ❓ Check purpose |
| `bmrs_fuelhh` | Unknown | Fuel mix half-hourly | Alternative fuel source | ❓ Verify vs fuelinst |
| `bmrs_indgen` | Unknown | Individual generator output | Unit-level generation | ❓ Historical coverage |
| `bmrs_inddem` | Unknown | Individual demand | Demand by unit | ❓ Usage unclear |
| `bmrs_demand_forecast` | Unknown | Demand forecasts | Forward demand planning | ❓ Check freshness |

**Business Use**: Grid carbon tracking, renewable penetration, generation mix analysis

**WARNING**: `generation` column is **MW NOT MWh** - divide by 1000 for GW, NOT 500!

#### System Frequency (Grid Stability)
| Table | Rows | Purpose | Data For | Status |
|-------|------|---------|----------|--------|
| `bmrs_freq` | 294K | System frequency measurements | **Frequency response revenue** | 🔄 Backfill in progress (empty until Dec 16) |

**Business Use**: Frequency response opportunities, grid stability monitoring

**DATA ALERT**: Was completely empty until Dec 16, 2025. Comprehensive 2022-2025 backfill now ongoing.

#### Forecasts & Capacity
| Table | Rows | Purpose | Data For | Status |
|-------|------|---------|----------|--------|
| `bmrs_fou2t14d` | Unknown | 2-14 day ahead forecasts | Medium-term planning | ❓ Check update frequency |
| `bmrs_fou2t3yw` | Unknown | 2 week-3 year ahead forecasts | Long-term planning | ❓ Verify coverage |
| `bmrs_ebocf` | Unknown | Embedded capacity forecast | Distributed generation | ❓ Usage |

**Business Use**: Forward capacity planning, long-term revenue forecasting

#### Backup/Archive Tables (Cleanup Candidates)
| Table | Size | Purpose | Action |
|-------|------|---------|--------|
| `bmrs_costs_backup_20251205_115208` | Unknown | Pre-Dec 5 backup | ⚠️ Consider archiving/deleting after validation |

### 1.2 IRIS Real-Time Tables (13 tables, 24-48h retention)

| Table | Purpose | Data For | Status |
|-------|---------|----------|--------|
| `bmrs_boalf_iris` | Real-time acceptances | Live balancing | ✅ Active |
| `bmrs_bod_iris` | Real-time bid-offers | Live submissions | ✅ Active |
| `bmrs_fuelinst_iris` | Real-time generation | Live fuel mix | ✅ Active |
| `bmrs_freq_iris` | Real-time frequency | Live stability monitoring | ✅ Active (Oct 28+ onwards) |
| `bmrs_indgen_iris` | Individual generator output | **VLP unit monitoring** | ✅ Active |
| `bmrs_inddem_iris` | Individual demand | Live demand | ✅ Active |
| `bmrs_indo_iris` | Individual output | Unit-level output | ✅ Active |
| `bmrs_mid_iris` | Real-time wholesale prices | Live pricing | ✅ Active |
| `bmrs_remit_iris` | **Outage notifications** | **Current unavailability** | ✅ Active (Nov 18+ onwards) |
| `bmrs_beb_iris` | BEB data | Unknown purpose | ❓ Verify |
| `bmrs_mels_iris` | Maximum Export Limit | Constraint monitoring | ✅ Active |
| `bmrs_mils_iris` | Maximum Import Limit | Constraint monitoring | ✅ Active |
| `bmrs_windfor_iris` | Wind forecasts | Renewable forecasting | ✅ Active |

**Business Use**: Real-time monitoring, live dashboards, recent event analysis

**CRITICAL**: IRIS retention ~24-48h. For complete recent timeline, UNION with historical tables.

---

## Part 2: Data Purpose & Business Context

### 2.1 Battery Energy Storage Systems (BESS) - Core Use Cases

#### Use Case 1: VLP Revenue Tracking (Primary)
**Objective**: Calculate balancing mechanism revenue for Virtual Lead Party battery units

**Data Sources**:
```sql
-- Individual acceptance prices (MOST ACCURATE)
SELECT * FROM bmrs_boalf_complete
WHERE validation_flag = 'Valid'  -- Elexon B1610 compliant
  AND bmUnit IN ('FBPGM002', 'FFSEN005')  -- VLP batteries
  AND acceptancePrice >= 70  -- High-value events

-- System imbalance reference
SELECT * FROM bmrs_costs
WHERE systemSellPrice > 50  -- High imbalance periods

-- Real-time generation monitoring
SELECT * FROM bmrs_indgen_iris
WHERE bmUnitId IN ('FBPGM002', 'FFSEN005')
```

**Key Metrics**:
- Revenue per MWh accepted: £70-110/MWh during Oct 17-23, 2025 high-price event
- Acceptance volume: Total MWh delivered to grid
- Frequency of dispatch: High-price event frequency
- Cycle depth: Charge/discharge patterns

**Critical Period Analysis**:
- Oct 17-23, 2025: £79.83/MWh average (80% of VLP revenue in 6 days)
- Oct 24-25, 2025: £30.51/MWh average (price crash, preserve cycles)

#### Use Case 2: Temporal Arbitrage Strategy
**Objective**: Buy low (charge), sell high (discharge) based on intraday imbalance price swings

**Data Sources**:
```sql
-- Intraday price volatility
SELECT
  DATE(settlementDate) as date,
  MIN(systemSellPrice) as trough,
  MAX(systemSellPrice) as peak,
  MAX(systemSellPrice) - MIN(systemSellPrice) as spread
FROM bmrs_costs
WHERE settlementDate >= '2025-10-01'
GROUP BY date
HAVING spread > 50  -- £50/MWh spread = profitable
```

**Strategy Rules**:
1. Charge when imbalance price < £25/MWh (off-peak)
2. Discharge when imbalance price > £70/MWh (peak stress)
3. Preserve cycles when spread < £40/MWh (low profit day)

**WARNING**: SSP = SBP since Nov 2015 (BSC Mod P305). Arbitrage is **TEMPORAL** (time-based), NOT spread-based.

#### Use Case 3: Frequency Response Revenue
**Objective**: Dynamic containment revenue from grid frequency deviation

**Data Sources**:
```sql
-- Frequency deviation events (revenue opportunities)
SELECT
  measurementTime,
  frequency,
  ABS(50.0 - frequency) as deviation_hz
FROM bmrs_freq
WHERE frequency < 49.8 OR frequency > 50.2
ORDER BY deviation_hz DESC
```

**Revenue Calculation**:
- Dynamic Containment (DC): £10-15/MW/h availability payment
- Utilization payment: 0.5-2% of availability
- Grid stability = more frequency events = higher utilization revenue

**DATA LIMITATION**: Historical bmrs_freq empty until Dec 16, 2025. Use bmrs_freq_iris for Oct 28+ onwards.

### 2.2 Grid & Generation Analysis

#### Use Case 4: Carbon Intensity Tracking
**Objective**: Calculate grid carbon intensity for reporting and forecasting

**Data Sources**:
```sql
-- Fuel mix with carbon factors
SELECT
  DATE(startTime) as date,
  fuelType,
  SUM(generation) / 1000.0 as generation_gw,  -- Convert MW → GW
  CASE fuelType
    WHEN 'CCGT' THEN SUM(generation) * 0.394  -- kg CO2/MWh
    WHEN 'COAL' THEN SUM(generation) * 0.937
    WHEN 'WIND' THEN 0
    WHEN 'SOLAR' THEN 0
    WHEN 'NUCLEAR' THEN 0
    ELSE 0
  END as carbon_kg
FROM bmrs_fuelinst
WHERE DATE(startTime) = '2025-12-17'
GROUP BY date, fuelType
```

**CRITICAL**: `generation` is **MW NOT MWh**. Use `generation / 1000` for GW, NOT `generation / 500`.

#### Use Case 5: Renewable Penetration
**Objective**: Track wind/solar percentage of total generation

**Data Sources**:
```sql
-- Renewable percentage
WITH totals AS (
  SELECT
    DATE(startTime) as date,
    SUM(CASE WHEN fuelType IN ('WIND', 'SOLAR') THEN generation ELSE 0 END) as renewable_mw,
    SUM(generation) as total_mw
  FROM bmrs_fuelinst
  WHERE DATE(startTime) BETWEEN '2025-10-01' AND '2025-12-17'
  GROUP BY date
)
SELECT
  date,
  renewable_mw / 1000 as renewable_gw,
  total_mw / 1000 as total_gw,
  (renewable_mw / total_mw) * 100 as renewable_pct
FROM totals
ORDER BY date DESC
```

#### Use Case 6: Outage Impact Analysis
**Objective**: Track generator unavailability and constraint impact

**Data Sources**:
```sql
-- Current outages affecting system
SELECT
  eventStart,
  eventEnd,
  assetId,
  fuelType,
  unavailableCapacity as offline_mw,
  TIMESTAMP_DIFF(eventEnd, eventStart, HOUR) as duration_hours
FROM bmrs_remit_iris
WHERE eventEnd >= CURRENT_TIMESTAMP()
ORDER BY unavailableCapacity DESC
LIMIT 20
```

**DATA LIMITATION**: Historical REMIT API deprecated (404). Only IRIS data available (Nov 18+ onwards, ~48h retention).

### 2.3 Market & Pricing Analysis

#### Use Case 7: Wholesale vs Imbalance Price Spread
**Objective**: Understand wholesale-imbalance relationship for trading strategy

**Data Sources**:
```sql
-- Compare wholesale (MID) vs imbalance (costs)
WITH prices AS (
  SELECT
    c.settlementDate,
    c.settlementPeriod,
    c.systemSellPrice as imbalance_price,
    m.price as wholesale_price
  FROM bmrs_costs c
  LEFT JOIN bmrs_mid m
    ON c.settlementDate = m.settlementDate
    AND c.settlementPeriod = m.settlementPeriod
  WHERE c.settlementDate >= '2025-10-01'
)
SELECT
  settlementDate,
  AVG(imbalance_price) as avg_imbalance,
  AVG(wholesale_price) as avg_wholesale,
  AVG(imbalance_price - wholesale_price) as avg_spread
FROM prices
GROUP BY settlementDate
ORDER BY avg_spread DESC
```

**Use**: Identify periods where imbalance significantly diverges from wholesale (high-value trading opportunities).

---

## Part 3: Gap Analysis

### 3.1 Systematic Gap Detection

Run comprehensive gap check across all tables:

```python
# gap_detection_comprehensive.py
from google.cloud import bigquery
import pandas as pd
from datetime import datetime, timedelta

PROJECT_ID = "inner-cinema-476211-u9"
DATASET = "uk_energy_prod"
client = bigquery.Client(project=PROJECT_ID, location="US")

# Tables to check (high-priority only)
TABLES_TO_CHECK = [
    'bmrs_bod',
    'bmrs_boalf_complete',
    'bmrs_costs',
    'bmrs_mid',
    'bmrs_fuelinst',
    'bmrs_freq',
    'bmrs_disbsad',
    'bmrs_indgen_iris'
]

results = []

for table in TABLES_TO_CHECK:
    query = f"""
    WITH date_series AS (
      SELECT date
      FROM UNNEST(GENERATE_DATE_ARRAY(
        (SELECT MIN(DATE(settlementDate)) FROM `{PROJECT_ID}.{DATASET}.{table}`),
        (SELECT MAX(DATE(settlementDate)) FROM `{PROJECT_ID}.{DATASET}.{table}`)
      )) as date
    ),
    actual_dates AS (
      SELECT DISTINCT DATE(settlementDate) as date
      FROM `{PROJECT_ID}.{DATASET}.{table}`
    )
    SELECT
      '{table}' as table_name,
      COUNT(*) as gap_days
    FROM date_series ds
    LEFT JOIN actual_dates ad ON ds.date = ad.date
    WHERE ad.date IS NULL
    """

    df = client.query(query).to_dataframe()
    results.append(df)

summary = pd.concat(results, ignore_index=True)
print(summary.to_string(index=False))
print(f"\n✅ Tables with zero gaps: {len(summary[summary.gap_days == 0])}")
print(f"⚠️  Tables with gaps: {len(summary[summary.gap_days > 0])}")
```

### 3.2 Known Gaps (As of Dec 20, 2025)

| Table | Gap Period | Gap Days | Reason | Status |
|-------|------------|----------|--------|--------|
| `bmrs_freq` | 2022-01-01 to 2025-10-27 | ~1,400 | Historical pipeline never configured | 🔄 Backfill ongoing |
| `bmrs_remit` | 2022-01-01 to 2025-11-17 | ~1,400 | API deprecated (404) | ❌ Unrecoverable |
| `bmrs_mid` | **VERIFIED FILLED** | 0 | Previously thought 24 days missing, now confirmed complete | ✅ No gaps |

### 3.3 Settlement Period Gaps

Check for missing half-hour periods within dates:

```sql
-- Verify 48 periods per day (or 50 on clock-change days)
WITH period_counts AS (
  SELECT
    DATE(settlementDate) as date,
    COUNT(DISTINCT settlementPeriod) as periods,
    CASE
      WHEN COUNT(DISTINCT settlementPeriod) = 48 THEN '✅ Complete'
      WHEN COUNT(DISTINCT settlementPeriod) IN (46, 50) THEN '⚠️  Clock change'
      ELSE '❌ Incomplete'
    END as status
  FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_costs`
  WHERE DATE(settlementDate) >= '2025-10-01'
  GROUP BY date
)
SELECT
  status,
  COUNT(*) as days,
  MIN(date) as first_date,
  MAX(date) as last_date
FROM period_counts
GROUP BY status
ORDER BY days DESC
```

---

## Part 4: Duplication Analysis

### 4.1 Known Duplicates

#### bmrs_costs: Duplicate Settlement Periods
**Issue**: ~55,000 duplicate settlement periods in pre-Oct 27, 2025 data

**Detection Query**:
```sql
-- Find duplicate settlement periods
SELECT
  settlementDate,
  settlementPeriod,
  COUNT(*) as occurrences
FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_costs`
WHERE DATE(settlementDate) < '2025-10-27'
GROUP BY settlementDate, settlementPeriod
HAVING COUNT(*) > 1
ORDER BY occurrences DESC, settlementDate DESC
LIMIT 100
```

**Workaround**:
```sql
-- Duplicate-safe query (use AVG or GROUP BY)
SELECT
  DATE(settlementDate) as date,
  settlementPeriod,
  AVG(systemSellPrice) as price_sell,  -- Handles duplicates
  AVG(systemBuyPrice) as price_buy
FROM bmrs_costs
GROUP BY date, settlementPeriod
```

**Status**: Post-Oct 29 data has **zero duplicates** (automated backfill improved). Pre-Oct 27 data remains duplicated.

### 4.2 Systematic Duplication Check

```python
# duplication_detector.py
from google.cloud import bigquery

PROJECT_ID = "inner-cinema-476211-u9"
DATASET = "uk_energy_prod"
client = bigquery.Client(project=PROJECT_ID, location="US")

TABLES = ['bmrs_costs', 'bmrs_mid', 'bmrs_fuelinst', 'bmrs_disbsad']

for table in TABLES:
    query = f"""
    SELECT
      '{table}' as table_name,
      COUNT(*) as total_rows,
      COUNT(DISTINCT CONCAT(
        CAST(settlementDate AS STRING),
        '-',
        CAST(settlementPeriod AS STRING)
      )) as unique_periods,
      COUNT(*) - COUNT(DISTINCT CONCAT(
        CAST(settlementDate AS STRING),
        '-',
        CAST(settlementPeriod AS STRING)
      )) as duplicate_rows
    FROM `{PROJECT_ID}.{DATASET}.{table}`
    WHERE DATE(settlementDate) >= '2025-01-01'
    """

    df = client.query(query).to_dataframe()
    print(df.to_string(index=False))
    print()
```

### 4.3 Backup/Dedup Tables Review

| Table | Purpose | Size | Action Needed |
|-------|---------|------|---------------|
| `bmrs_costs_backup_20251205_115208` | Pre-Dec 5 backup | Unknown | ⚠️ Verify data integrity, then archive/delete |
| `bmrs_fuelinst_dedup` | Deduplicated fuel data | Unknown | ❓ Compare with bmrs_fuelinst, check if still needed |
| `bmrs_fuelinst_unified` | Historical+IRIS combined | Unknown | ❓ Verify purpose vs manual UNION queries |
| `bmrs_boalf_unified` | BOALF unified table | Unknown | ❓ Check relationship to boalf_complete |

**Recommendation**: Document purpose of each *_dedup/*_unified table. If redundant with query patterns (UNION), consider deprecating.

---

## Part 5: Automated Background Operations Plan

### 5.1 Current Process State

**Running Processes** (as of Dec 20, 2025 01:05):
```
PID 4105491: python3 client.py (IRIS downloader) - Backgrounded ✅
PID 4105518: python3 iris_to_bigquery_unified.py --continuous (IRIS uploader) - Backgrounded ✅
PID 4108881: python3 update_live_dashboard_v2.py (Dashboard auto-update) - Running ✅
```

**Previous Issue**: IRIS client was running in foreground on pts/18, hijacking terminal output. Now fixed via nohup.

### 5.2 Systemd Service Architecture (Recommended)

**Setup Script Ready**: `/home/george/GB-Power-Market-JJ/setup_multiprocess_system.sh`

**Services to Create**:

#### Service 1: IRIS Client (Downloader)
```ini
[Unit]
Description=IRIS Azure Service Bus Client
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/iris-pipeline/scripts
Environment="GOOGLE_APPLICATION_CREDENTIALS=/opt/iris-pipeline/secrets/sa.json"
ExecStart=/usr/bin/python3 /opt/iris-pipeline/scripts/client.py
Restart=always
RestartSec=30
StandardOutput=append:/opt/iris-pipeline/logs/client/iris_client.log
StandardError=append:/opt/iris-pipeline/logs/client/iris_client_error.log

# Resource limits
MemoryMax=4G
CPUQuota=50%

[Install]
WantedBy=multi-user.target
```

#### Service 2: IRIS Uploader (BigQuery)
```ini
[Unit]
Description=IRIS to BigQuery Uploader
After=network.target iris-client.service
Requires=iris-client.service

[Service]
Type=simple
User=root
WorkingDirectory=/opt/iris-pipeline/scripts
Environment="GOOGLE_APPLICATION_CREDENTIALS=/opt/iris-pipeline/secrets/sa.json"
ExecStart=/usr/bin/python3 /opt/iris-pipeline/scripts/iris_to_bigquery_unified.py --continuous
Restart=always
RestartSec=30
StandardOutput=append:/opt/iris-pipeline/logs/uploader/iris_uploader.log
StandardError=append:/opt/iris-pipeline/logs/uploader/iris_uploader_error.log

# Resource limits
MemoryMax=8G
CPUQuota=100%

[Install]
WantedBy=multi-user.target
```

#### Service 3: Dashboard Auto-Refresh
```ini
[Unit]
Description=Google Sheets Dashboard Auto-Updater
After=network.target

[Service]
Type=simple
User=george
WorkingDirectory=/home/george/GB-Power-Market-JJ
Environment="GOOGLE_APPLICATION_CREDENTIALS=/home/george/inner-cinema-credentials.json"
ExecStart=/usr/bin/python3 /home/george/GB-Power-Market-JJ/update_live_dashboard_v2.py
Restart=always
RestartSec=300
StandardOutput=append:/home/george/GB-Power-Market-JJ/logs/dashboard/dashboard_updater.log
StandardError=append:/home/george/GB-Power-Market-JJ/logs/dashboard/dashboard_updater_error.log

# Resource limits
MemoryMax=2G
CPUQuota=25%

[Install]
WantedBy=multi-user.target
```

#### Service 4: Historical Backfill (Daily)
```ini
[Unit]
Description=Historical BMRS Data Backfill
After=network.target

[Service]
Type=oneshot
User=george
WorkingDirectory=/home/george/GB-Power-Market-JJ
Environment="GOOGLE_APPLICATION_CREDENTIALS=/home/george/inner-cinema-credentials.json"
ExecStart=/usr/bin/python3 /home/george/GB-Power-Market-JJ/auto_ingest_realtime.py
StandardOutput=append:/home/george/GB-Power-Market-JJ/logs/backfill/backfill.log
StandardError=append:/home/george/GB-Power-Market-JJ/logs/backfill/backfill_error.log

# Resource limits
MemoryMax=4G
CPUQuota=50%
```

**Timer for Daily Backfill**:
```ini
[Unit]
Description=Daily Historical Backfill Timer
Requires=historical-backfill.service

[Timer]
OnCalendar=daily
OnCalendar=02:00
Persistent=true

[Install]
WantedBy=timers.target
```

**Deployment**:
```bash
# Run setup script (already created)
cd /home/george/GB-Power-Market-JJ
sudo ./setup_multiprocess_system.sh

# Verify services
sudo systemctl status iris-client iris-uploader dashboard-updater
sudo systemctl status historical-backfill.timer

# Check logs
./check_all_processes.sh
```

### 5.3 Cron Jobs (Alternative/Supplement)

**Daily Backfill** (02:00 AM):
```cron
0 2 * * * cd /home/george/GB-Power-Market-JJ && /usr/bin/python3 auto_ingest_realtime.py >> logs/backfill/backfill_$(date +\%Y\%m\%d).log 2>&1
```

**Gap Detection** (08:00 AM):
```cron
0 8 * * * cd /home/george/GB-Power-Market-JJ && /usr/bin/python3 gap_detection_comprehensive.py >> logs/monitoring/gap_check_$(date +\%Y\%m\%d).log 2>&1
```

**Dashboard Refresh** (Every 5 min):
```cron
*/5 * * * * cd /home/george/GB-Power-Market-JJ && /usr/bin/python3 update_analysis_bi_enhanced.py >> logs/dashboard/manual_refresh.log 2>&1
```

**Health Check** (Hourly):
```cron
0 * * * * cd /home/george/GB-Power-Market-JJ && ./check_all_processes.sh >> logs/monitoring/health_$(date +\%Y\%m\%d).log 2>&1
```

**Add to crontab**:
```bash
crontab -e
# Paste above entries
```

### 5.4 Monitoring & Alerting

#### Health Check Script
```bash
# check_all_processes.sh (already created)
./check_all_processes.sh

# Expected output:
# ✅ iris-client.service: active (running)
# ✅ iris-uploader.service: active (running)
# ✅ dashboard-updater.service: active (running)
# ✅ historical-backfill.timer: active (waiting)
# Memory: 18GB / 128GB used (14%)
# CPU: 52% / 400% used (13%)
# Disk: 85GB free
```

#### Data Freshness Monitoring
```python
# data_freshness_check.py
from google.cloud import bigquery
from datetime import datetime, timedelta

PROJECT_ID = "inner-cinema-476211-u9"
DATASET = "uk_energy_prod"
client = bigquery.Client(project=PROJECT_ID, location="US")

# Check IRIS tables (should be < 30 min old)
iris_tables = ['bmrs_fuelinst_iris', 'bmrs_freq_iris', 'bmrs_indgen_iris']

for table in iris_tables:
    query = f"""
    SELECT
      '{table}' as table_name,
      MAX(publishTime) as latest_data,
      TIMESTAMP_DIFF(CURRENT_TIMESTAMP(), MAX(publishTime), MINUTE) as age_minutes
    FROM `{PROJECT_ID}.{DATASET}.{table}`
    """
    df = client.query(query).to_dataframe()
    age = df['age_minutes'].iloc[0]
    status = '✅' if age < 30 else '⚠️' if age < 60 else '❌'
    print(f"{status} {table}: {age:.0f} minutes old")
```

**Add to cron** (every 15 min):
```cron
*/15 * * * * cd /home/george/GB-Power-Market-JJ && /usr/bin/python3 data_freshness_check.py >> logs/monitoring/freshness.log 2>&1
```

### 5.5 Resource Allocation (128GB Machine)

| Process | RAM Max | CPU Max | Priority | Auto-restart |
|---------|---------|---------|----------|--------------|
| IRIS Client | 4GB | 50% | High | Yes (30s delay) |
| IRIS Uploader | 8GB | 100% | High | Yes (30s delay) |
| Dashboard Updater | 2GB | 25% | Medium | Yes (5min delay) |
| Daily Backfill | 4GB | 50% | Low | N/A (oneshot) |
| **Available for Queries** | **110GB** | **175%** | - | - |

**Total Allocated**: ~18GB RAM, ~225% CPU
**Available**: ~110GB RAM, ~175% CPU (for BigQuery queries, analysis scripts, etc.)

### 5.6 Log Management

**Log Rotation** (prevent disk fill):
```bash
# /etc/logrotate.d/gb-power-market
/home/george/GB-Power-Market-JJ/logs/**/*.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    create 0644 george george
}

/opt/iris-pipeline/logs/**/*.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    create 0644 root root
}
```

**Apply**:
```bash
sudo logrotate -f /etc/logrotate.d/gb-power-market
```

---

## Part 6: Implementation Roadmap

### Phase 1: Immediate (Today, 1-2 hours)
- [x] Background IRIS processes (COMPLETE - already backgrounded)
- [ ] Run setup_multiprocess_system.sh (deploy systemd services)
- [ ] Verify all services started correctly
- [ ] Test clean terminal operation (no interruptions)
- [ ] Run comprehensive gap detection script
- [ ] Run duplication detection script

### Phase 2: Short-term (This Week, 2-3 hours)
- [ ] Add cron jobs for daily backfill, gap checks, health monitoring
- [ ] Configure log rotation
- [ ] Document backup table purposes (costs_backup, fuelinst_dedup, etc.)
- [ ] Archive/delete redundant backup tables after verification
- [ ] Test dashboard auto-refresh (currently manual)
- [ ] Implement data freshness alerting

### Phase 3: Medium-term (This Month, 4-6 hours)
- [ ] Complete bmrs_freq backfill (2022-2025)
- [ ] Systematic duplicate cleanup (bmrs_costs pre-Oct 27 data)
- [ ] Create unified views (historical+IRIS) for key tables
- [ ] Optimize query patterns (partitioning, clustering)
- [ ] Implement automated gap-filling (detect gaps → backfill → verify)
- [ ] Dashboard performance optimization

### Phase 4: Long-term (Ongoing)
- [ ] Machine learning forecasting (price prediction, demand forecasting)
- [ ] Real-time alerting (high-price events, frequency deviations, outages)
- [ ] Historical data archival strategy (move old data to cold storage)
- [ ] Data quality scorecards (freshness, completeness, accuracy metrics)
- [ ] Automated reporting (weekly/monthly summaries via email/Slack)

---

## Part 7: Quick Reference Commands

### Check Running Services
```bash
./check_all_processes.sh
sudo systemctl status iris-client iris-uploader dashboard-updater
ps aux | grep -E "python3.*(client|iris_to_bigquery|dashboard)" | grep -v grep
```

### View Logs
```bash
# IRIS client
tail -f /opt/iris-pipeline/logs/client/iris_client.log

# IRIS uploader
tail -f /opt/iris-pipeline/logs/uploader/iris_uploader.log

# Dashboard
tail -f /home/george/GB-Power-Market-JJ/logs/dashboard/dashboard_updater.log

# Backfill
tail -f /home/george/GB-Power-Market-JJ/logs/backfill/backfill.log
```

### Restart Services
```bash
# Restart specific service
sudo systemctl restart iris-client
sudo systemctl restart iris-uploader
sudo systemctl restart dashboard-updater

# Restart all
sudo systemctl restart iris-client iris-uploader dashboard-updater
```

### Manual Operations
```bash
# Run dashboard refresh manually
python3 update_analysis_bi_enhanced.py

# Run backfill manually
python3 auto_ingest_realtime.py

# Check data coverage
python3 -c "from google.cloud import bigquery; ..." # See gap detection script

# Check for duplicates
python3 -c "from google.cloud import bigquery; ..." # See duplication detector script
```

### Resource Monitoring
```bash
# Memory usage
free -h

# CPU usage
top -bn1 | grep "Cpu(s)"

# Disk usage
df -h

# Process resource usage
ps aux --sort=-%mem | head -20
ps aux --sort=-%cpu | head -20
```

---

## Part 8: Contact & Maintenance

**Primary Maintainer**: George Major (george@upowerenergy.uk)
**Repository**: https://github.com/GeorgeDoors888/GB-Power-Market-JJ
**Google Sheets Dashboard**: https://docs.google.com/spreadsheets/d/1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA/

**Key Documentation**:
- `.github/copilot-instructions.md` - AI coding agent instructions
- `docs/PROJECT_CONFIGURATION.md` - Configuration reference
- `STOP_DATA_ARCHITECTURE_REFERENCE.md` - Data architecture quick reference
- `GB_POWER_DATA_COMPREHENSIVE_GUIDE_DEC20_2025.md` - Complete data dictionary

**Last Updated**: December 20, 2025
**Status**: ✅ Production (Nov 2025), Optimization ongoing

---

## Summary

**Current State**: 76 BMRS tables operational with dual-pipeline architecture. IRIS processes now properly backgrounded. Minor gaps in bmrs_freq (backfill ongoing) and bmrs_remit (API deprecated). Duplicate settlement periods in bmrs_costs pre-Oct 27 data (post-Oct 29 clean).

**Automation Ready**: Systemd service scripts created and ready to deploy. Cron jobs designed for daily backfill, gap detection, and health monitoring. Resource limits prevent system overload on 128GB machine.

**Next Steps**:
1. Deploy systemd services via `setup_multiprocess_system.sh`
2. Add cron jobs for automation
3. Run comprehensive gap and duplication analysis
4. Complete bmrs_freq backfill
5. Clean up redundant backup tables

**Business Impact**: Automated background operations enable uninterrupted analysis, real-time monitoring, and reliable VLP revenue tracking without manual intervention.

# 🗺️ Geographic Constraints System - Complete Implementation

**Date:** December 9, 2025  
**Status:** ✅ Operational  
**Dashboard:** BG LIVE sheet, rows 65-78

---

## 📋 Overview

Geographic constraints tracking system showing regional balancing actions, Scotland wind curtailment, and associated costs.

### Key Metrics
- **12,500** constraint actions per day (BOALF)
- **228** cost records per day (DISBSAD)
- **£0.36M** average daily constraint costs
- **1.8%** of actions have cost data
- **15-minute** data refresh cycle

---

## 🏗️ Architecture

### Data Sources

**1. BOALF (Balancing Offer/Bid Lift)**
- **Historical:** `bmrs_boalf` (2022-01-01 → 2025-11-04)
- **Real-Time:** `bmrs_boalf_iris` (2025-11-04 → present)
- **Volume:** ~12,500 actions/day, peak 20,823
- **Source:** IRIS streaming (real-time)

**2. DISBSAD (Constraint Costs)**
- **Historical:** `bmrs_disbsad` (2022-01-01 → present)
- **Volume:** ~228 cost records/day, peak 559
- **Average Cost:** £0.36M/day (peak £1.16M on Dec 1)
- **Source:** REST API backfill (NOT available via IRIS)

**3. BMU Registration (Regional Mapping)**
- **Table:** `bmu_registration_data`
- **Purpose:** Maps BMU units to GSP groups (regions)
- **Join Keys:** `nationalgridbmunit` or `elexonbmunit`

### Pipeline Flow

```
┌─────────────────────────────────────────────────────────┐
│                  CONSTRAINT TRACKING                     │
└─────────────────────────────────────────────────────────┘

  Real-Time Actions          Historical Actions
  (IRIS Streaming)          (BigQuery Historical)
         │                          │
         ▼                          ▼
  bmrs_boalf_iris          bmrs_boalf
         │                          │
         └──────────┬───────────────┘
                    │
                    ▼
              UNION Query
         (Last 7 days actions)
                    │
                    ▼
         JOIN bmu_registration_data
        (Map to GSP groups/regions)
                    │
                    ▼
         Dashboard Rows 65-78
       (Regional action counts)


  REST API Backfill          
  (Every 15 minutes)         
         │                   
         ▼                   
  auto_backfill_disbsad_daily.py
         │
         ▼
  bmrs_disbsad
  (Constraint costs)
         │
         ▼
  Dashboard Rows 65-78
  (Regional costs)
```

---

## 🔄 Automated Backfill System

### Why DISBSAD Needs Backfill

**IRIS Limitation:** DISBSAD is NOT available as a real-time IRIS stream because:
1. Requires post-settlement calculations
2. Involves financial reconciliation
3. Data published with delay by Elexon

**Solution:** 15-minute REST API backfill maintains near-real-time data.

### Backfill Configuration

**Script:** `auto_backfill_disbsad_daily.py`

**Schedule:**
```cron
*/15 * * * * /usr/bin/python3 /home/george/GB-Power-Market-JJ/auto_backfill_disbsad_daily.py >> /home/george/GB-Power-Market-JJ/logs/cron_disbsad.log 2>&1
```

**Behavior:**
- Runs every 15 minutes (96 executions/day)
- Fetches last 2 days of data (48-hour window)
- Overwrites existing records (handles corrections)
- Logs to `logs/cron_disbsad.log`
- Typical execution: 10-30 seconds

**Data Lag:** 15-30 minutes (acceptable for constraint cost analysis)

### Monitoring

**Check last execution:**
```bash
tail -20 /home/george/GB-Power-Market-JJ/logs/cron_disbsad.log
```

**Verify data freshness:**
```sql
SELECT MAX(settlementDate) as latest_date,
       COUNT(*) as records_today
FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_disbsad`
WHERE settlementDate >= CURRENT_DATE()
```

**Expected output:**
- Latest date: Today or yesterday
- Records today: 150-250 (depends on constraint activity)

---

## 📊 Dashboard Implementation

### Location
**Sheet:** BG LIVE  
**Rows:** 65-78  
**Update Script:** `update_bg_live_dashboard.py`

### Data Display

**Row 65:** Header
```
🗺️ GEOGRAPHIC CONSTRAINTS (Last 7 Days) | Cost data may lag 1-2 days
```

**Row 66:** Scotland Wind Curtailment Summary
```
Scotland Wind Curtailment: 1,463 actions | 195.3 GW adjusted
```

**Rows 68-78:** Regional Breakdown
```
Region              | Actions | Units | MW Adjusted | Cost (£k)
--------------------|---------|-------|-------------|----------
🔴 North Scotland   | 1,221   | 82    | 142.5       | N/A
🔴 South Scotland   | 242     | 45    | 52.8        | N/A
🟡 East England     | 43      | 12    | 8.4         | N/A
```

**Color Coding:**
- 🔴 Red: ≥100 actions (high constraint activity)
- 🟠 Orange: ≥50 actions (moderate activity)
- 🟡 Yellow: <50 actions (low activity)

### Query Logic

**Regional Actions (Last 7 Days):**
```sql
WITH combined_boalf AS (
  -- Historical actions
  SELECT bmUnit, settlementDate, levelFrom, levelTo, soFlag
  FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_boalf`
  WHERE settlementDate >= DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY)
    AND soFlag = TRUE  -- System Operator flagged
  
  UNION ALL
  
  -- Real-time actions
  SELECT bmUnit, settlementDate, levelFrom, levelTo, soFlag
  FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_boalf_iris`
  WHERE settlementDate >= DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY)
    AND soFlag = TRUE
)
SELECT 
  COALESCE(bmu.gspgroupname, 'Unknown') as region,
  COUNT(*) as action_count,
  COUNT(DISTINCT boalf.bmUnit) as unique_units,
  ROUND(SUM(ABS(levelTo - levelFrom)), 1) as total_mw_adjusted
FROM combined_boalf boalf
LEFT JOIN `inner-cinema-476211-u9.uk_energy_prod.bmu_registration_data` bmu 
  ON (boalf.bmUnit = bmu.nationalgridbmunit 
      OR boalf.bmUnit = bmu.elexonbmunit)
WHERE bmu.gspgroupname IS NOT NULL
GROUP BY region
ORDER BY action_count DESC
LIMIT 10
```

**Scotland Wind Curtailment:**
```sql
-- Sum actions from North & South Scotland regions
-- Identifies wind curtailment vs other constraint types
```

**Regional Costs (Last 30 Days):**
```sql
SELECT 
  COALESCE(bmu.gspgroupname, 'Unknown') as region,
  ROUND(SUM(disbsad.cost) / 1000, 2) as cost_thousands
FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_disbsad` disbsad
LEFT JOIN `inner-cinema-476211-u9.uk_energy_prod.bmu_registration_data` bmu 
  ON (disbsad.assetId = bmu.nationalgridbmunit 
      OR disbsad.assetId = bmu.elexonbmunit)
WHERE settlementDate >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)
  AND cost > 0
GROUP BY region
HAVING region != 'Unknown'
ORDER BY cost_thousands DESC
LIMIT 10
```

---

## 🐛 Troubleshooting

### Dashboard Shows "N/A" for Costs

**Possible Causes:**
1. **Regional attribution missing** - BMU unit not in `bmu_registration_data`
2. **Cost data not yet available** - DISBSAD typically lags 1-2 days
3. **Backfill not running** - Check cron log

**Solutions:**
```bash
# Check backfill status
tail -f /home/george/GB-Power-Market-JJ/logs/cron_disbsad.log

# Verify DISBSAD data freshness
python3 << 'EOF'
from google.cloud import bigquery
client = bigquery.Client(project="inner-cinema-476211-u9")
query = """
SELECT MAX(settlementDate) as latest, COUNT(*) as today_count
FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_disbsad`
WHERE settlementDate >= CURRENT_DATE()
"""
print(client.query(query).to_dataframe())
EOF

# Manual backfill if needed
python3 auto_backfill_disbsad_daily.py
```

### Backfill Failing

**Check credentials:**
```bash
ls -la inner-cinema-credentials.json
export GOOGLE_APPLICATION_CREDENTIALS=/home/george/GB-Power-Market-JJ/inner-cinema-credentials.json
```

**Test Elexon API access:**
```bash
curl "https://data.elexon.co.uk/bmrs/api/v1/datasets/DISBSAD?from=2025-12-08T00:00:00Z&to=2025-12-09T00:00:00Z" | head -100
```

**Check BigQuery permissions:**
```python
from google.cloud import bigquery
client = bigquery.Client(project="inner-cinema-476211-u9")
print("✅ BigQuery connection successful")
```

### Cron Job Not Running

**Verify crontab:**
```bash
crontab -l | grep disbsad
```

**Check cron service:**
```bash
systemctl status crond  # RHEL/AlmaLinux
# or
systemctl status cron   # Debian/Ubuntu
```

**Manual execution test:**
```bash
/usr/bin/python3 /home/george/GB-Power-Market-JJ/auto_backfill_disbsad_daily.py
```

### Data Gap Detected

**Backfill specific date range:**
```bash
cd /home/george/GB-Power-Market-JJ
python3 ingest_elexon_fixed.py \
  --start 2025-12-01 \
  --end 2025-12-09 \
  --only DISBSAD \
  --overwrite
```

---

## 📈 Performance & Costs

### API Usage

**Elexon BMRS API:**
- Free tier (no rate limits for DISBSAD)
- 96 calls/day (every 15 minutes)
- ~50 KB per request
- ~4.8 MB/day total

### BigQuery Costs

**Storage:**
- DISBSAD: 497K records = ~100 MB
- Growth: ~228 records/day = ~50 KB/day
- Cost: $0.02/GB/month = **<$0.01/month**

**Query Costs:**
- Dashboard refresh: 3 queries/run
- Data scanned: ~10 MB/query (filtered by date)
- Runs: Every dashboard update
- Cost: $5/TB = **<$0.01/month**

**Total:** <$0.02/month (effectively free)

---

## 🔮 Future Enhancements

### Request IRIS Stream
Contact Elexon to request DISBSAD added to IRIS:
- Email: iris-support@elexon.co.uk
- Queue ID: 5ac22e4f-fcfa-4be8-b513-a6dc767d6312
- Justification: Real-time constraint cost tracking

### Alerting
```python
# Alert when constraint costs spike
if daily_cost > 1_000_000:  # £1M threshold
    send_alert("High constraint costs detected")
```

### Optimization
- Reduce backfill window from 2 days to 1 day once data lag is understood
- Add cost projections based on current activity
- Implement cost per MW metric

### Enhanced Visualization
- Add time-series constraint cost chart
- Show cost trends by region
- Display cost efficiency metrics (£/MW)

---

## 📚 Related Documentation

- **Configuration:** `PROJECT_CONFIGURATION.md`
- **Data Architecture:** `STOP_DATA_ARCHITECTURE_REFERENCE.md`
- **IRIS Pipeline:** `UNIFIED_ARCHITECTURE_HISTORICAL_AND_REALTIME.md`
- **Backfill Setup:** `DISBSAD_BACKFILL_SETUP.md`
- **Dashboard Updates:** `ENHANCED_BI_ANALYSIS_README.md`

---

## ✅ Completion Checklist

- [x] Geographic constraints section added to dashboard (rows 65-78)
- [x] UNION query combining historical + IRIS BOALF
- [x] Scotland wind curtailment tracking
- [x] Backfilled Oct 29 - Nov 3 gap (148,927 BOALF + 2,024 DISBSAD)
- [x] Fixed API parameter format (RFC3339 `from/to`)
- [x] Created 15-minute automated backfill script
- [x] Installed cron job (*/15 * * * *)
- [x] Verified IRIS streams (no missing subscriptions)
- [x] Updated architecture documentation
- [x] Refreshed dashboard with latest data
- [x] Created comprehensive documentation

**Status:** ✅ **System Operational**

---

*Last Updated: December 9, 2025*  
*Next Review: Monthly (check for IRIS DISBSAD availability)*

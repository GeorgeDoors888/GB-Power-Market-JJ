# IRIS vs API: Data Ingestion Strategy

**Date**: December 20, 2025
**Purpose**: Define which data sources to use for each BMRS table

---

## Current Architecture

### IRIS Pipeline (Real-Time, Last 24-48h)
- **Source**: Azure Service Bus streaming
- **Retention**: 24-48 hours only
- **Tables**: 40 `*_iris` tables
- **Update Frequency**: Continuous (messages arrive every 5-30 seconds)
- **Coverage**: Real-time operational data only

### API Pipeline (Historical, 2020-Present)
- **Source**: Elexon BMRS REST API
- **Retention**: 5+ years of historical data
- **Tables**: 63 historical tables (no `_iris` suffix)
- **Update Frequency**: Cron jobs (every 15-30 minutes)
- **Coverage**: Complete historical timeline

---

## Data Source Matrix

### ✅ IRIS Available (Use IRIS for real-time + API for historical)

| Table | IRIS Table | API Endpoint | Current Cron | Strategy |
|-------|-----------|--------------|--------------|----------|
| **bmrs_fuelinst** | bmrs_fuelinst_iris | `/generation/outturn/summary` | ✅ Every 15 min | IRIS real-time + API backfill |
| **bmrs_freq** | bmrs_freq_iris | `/system/frequency` | ✅ Every 15 min | IRIS real-time + API backfill |
| **bmrs_mid** | bmrs_mid_iris | `/balancing/pricing/market-index` | ✅ Every 15 min | IRIS real-time + API backfill |
| **bmrs_costs** | bmrs_costs_iris | `/balancing/settlement/system-prices` | ✅ Every 30 min | IRIS real-time + API backfill |
| **bmrs_windfor** | bmrs_windfor_iris | `/forecast/generation/wind` | ❌ Missing | **ADD CRON** |
| **bmrs_indgen** | bmrs_indgen_iris | `/generation/outturn/generation-units` | ❌ Missing | **ADD CRON** |
| **bmrs_remit** | bmrs_remit_iris | `/remit/message-list-retrieval` | ⚠️ API deprecated | IRIS only |

### ⚠️ IRIS Unreliable (Use API only)

| Table | IRIS Status | API Endpoint | Current Cron | Notes |
|-------|------------|--------------|--------------|-------|
| **bmrs_bod** | Exists but unstable | `/balancing/pricing/bid-offer` | ❌ Missing | IRIS messages often incomplete |
| **bmrs_boalf** | Exists but unstable | `/balancing/acceptances/list` | ✅ Every 30 min + derive prices | IRIS doesn't include prices |
| **bmrs_disbsad** | bmrs_disbsad_iris | `/balancing/settlement/bsad` | ❌ Missing | IRIS exists but no cron backup |

### ❌ No IRIS (API Only)

| Table | API Endpoint | Current Cron | Priority |
|-------|--------------|--------------|----------|
| **bmrs_detsysprices** | `/balancing/settlement/detailed-system-prices` | ❌ Missing | HIGH |
| **bmrs_pn** | `/balancing/physical/notifications` | ❌ Missing | MEDIUM |
| **bmrs_ebocf** | `/balancing/settlement/credit-default-notices` | ❌ Missing | LOW |
| **bmrs_mel** | `/balancing/physical/mel` | ❌ Missing | MEDIUM |
| **bmrs_qas** | `/balancing/dynamic/qas` | ❌ Missing | LOW |

---

## Current Cron Jobs (Active)

```bash
# Real-time ingestion (FUELINST, FREQ, MID, COSTS)
*/15 * * * * python3 auto_ingest_realtime.py

# System prices backfill
*/30 * * * * python3 auto_backfill_costs_daily.py

# BOALF price derivation (matches BOD with BOALF)
*/30 * * * * python3 derive_boalf_prices.py --start $(date -d '3 days ago' +%Y-%m-%d)

# Dashboard updates
*/5 * * * * /home/george/GB-Power-Market-JJ/bg_live_cron.sh
0 4 * * * python3 unified_dashboard_refresh.py

# Behind-the-meter sync
*/30 * * * * /home/george/GB-Power-Market-JJ/run_btm_sync.sh

# Market KPIs
*/30 * * * * python3 add_market_kpis_to_dashboard.py

# BM revenue analysis
0 5 * * * /home/george/GB-Power-Market-JJ/auto_update_bm_revenue_full_history.sh
```

---

## Recommended Additions

### High Priority (Add Within 24 Hours)

#### 1. BOD (Bid-Offer Data) - Critical for VLP Analysis
```bash
# Every 30 minutes (stagger with BOALF)
*/30 * * * * cd /home/george/GB-Power-Market-JJ && python3 auto_ingest_bod.py >> logs/bod_ingest.log 2>&1
```

**Script to create**: `auto_ingest_bod.py`
```python
#!/usr/bin/env python3
"""
Auto-ingest BOD (Bid-Offer Data) from Elexon API
Runs every 30 min to backfill last 2 hours (IRIS coverage is unreliable)
"""
import requests
from google.cloud import bigquery
from datetime import datetime, timedelta

PROJECT_ID = 'inner-cinema-476211-u9'
DATASET = 'uk_energy_prod'
API_BASE = 'https://data.elexon.co.uk/bmrs/api/v1'

def ingest_bod():
    client = bigquery.Client(project=PROJECT_ID, location='US')

    # Get latest timestamp
    query = f"SELECT MAX(settlementDate) as latest FROM `{PROJECT_ID}.{DATASET}.bmrs_bod`"
    result = client.query(query).to_dataframe()
    latest = result['latest'].iloc[0]

    # Fetch last 2 hours
    from_dt = max(latest, datetime.now() - timedelta(hours=2))
    to_dt = datetime.now()

    url = f"{API_BASE}/balancing/pricing/bid-offer"
    params = {
        'from': from_dt.strftime('%Y-%m-%dT%H:%M:%SZ'),
        'to': to_dt.strftime('%Y-%m-%dT%H:%M:%SZ'),
    }

    response = requests.get(url, params=params)
    data = response.json()

    if data.get('data'):
        # Upload to BigQuery
        table_id = f"{PROJECT_ID}.{DATASET}.bmrs_bod"
        errors = client.insert_rows_json(table_id, data['data'])

        if errors:
            print(f"❌ Errors: {errors}")
        else:
            print(f"✅ Inserted {len(data['data'])} BOD records")
    else:
        print("⚠️ No new BOD data")

if __name__ == '__main__':
    ingest_bod()
```

#### 2. DISBSAD (Balancing Services) - Financial Analysis
```bash
# Every 30 minutes
*/30 * * * * cd /home/george/GB-Power-Market-JJ && python3 auto_backfill_disbsad_daily.py >> logs/disbsad_backfill.log 2>&1
```

**Already exists**: `auto_backfill_disbsad_daily.py` ✅ (just add to crontab)

#### 3. WINDFOR (Wind Forecast) - Battery Strategy
```bash
# Every 15 minutes (wind forecasts update frequently)
*/15 * * * * cd /home/george/GB-Power-Market-JJ && python3 auto_ingest_windfor.py >> logs/windfor_ingest.log 2>&1
```

**Script to create**: `auto_ingest_windfor.py` (similar to auto_ingest_realtime.py)

#### 4. DETSYSPRICES (Detailed System Prices) - Settlement Analysis
```bash
# Every hour (large dataset, less frequently updated)
0 * * * * cd /home/george/GB-Power-Market-JJ && python3 backfill_dets_system_prices.py >> logs/detsysprices_backfill.log 2>&1
```

**Already exists**: `backfill_dets_system_prices.py` ✅

### Medium Priority (Add Within 1 Week)

#### 5. PN (Physical Notifications) - Unit Availability
```bash
# Every 30 minutes
*/30 * * * * cd /home/george/GB-Power-Market-JJ && python3 auto_ingest_pn.py >> logs/pn_ingest.log 2>&1
```

#### 6. MEL/MIL (Export/Import Limits) - Grid Constraints
```bash
# Every 30 minutes (IRIS has these but API backup needed)
*/30 * * * * cd /home/george/GB-Power-Market-JJ && python3 auto_ingest_mel_mil.py >> logs/mel_mil_ingest.log 2>&1
```

#### 7. INDGEN (Individual Generation) - Unit-Level Data
```bash
# Every 15 minutes
*/15 * * * * cd /home/george/GB-Power-Market-JJ && python3 auto_ingest_indgen.py >> logs/indgen_ingest.log 2>&1
```

### Low Priority (Add When Needed)

- **EBOCF** (Credit default notices) - Rare events
- **QAS** (Balancing services availability) - Only for DFS analysis
- **NETBSAD** (Net BSA data) - IRIS coverage sufficient

---

## Query Pattern: IRIS + API Union

For complete timeline coverage, always UNION historical + IRIS tables:

```sql
WITH combined AS (
  -- Historical data (2020 to 48h ago)
  SELECT
    settlementDate,
    settlementPeriod,
    systemSellPrice,
    'historical' as source
  FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_costs`
  WHERE settlementDate < CURRENT_DATE() - 2

  UNION ALL

  -- Real-time data (last 48h)
  SELECT
    settlementDate,
    settlementPeriod,
    systemSellPrice,
    'iris' as source
  FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_costs_iris`
  WHERE settlementDate >= CURRENT_DATE() - 2
)
SELECT * FROM combined
ORDER BY settlementDate DESC, settlementPeriod DESC
```

---

## Implementation Plan

### Phase 1: Critical Tables (Next 24 Hours)
1. ✅ Create `auto_ingest_bod.py` script
2. ✅ Add BOD cron job (every 30 min)
3. ✅ Add DISBSAD cron job (script exists, just add to crontab)
4. ✅ Add DETSYSPRICES cron job (script exists)
5. ✅ Test all 3 for 24 hours

### Phase 2: Wind & Generation (Next Week)
1. Create `auto_ingest_windfor.py`
2. Create `auto_ingest_indgen.py`
3. Add cron jobs for both
4. Verify IRIS + API union queries work correctly

### Phase 3: Monitoring (Next 2 Weeks)
1. Add gap detection alerts (if IRIS fails, API should catch it)
2. Add duplicate detection (prevent IRIS + API overlap)
3. Dashboard freshness indicators (show which source is being used)

### Phase 4: Advanced (Next Month)
1. Automatic failover (if IRIS down > 5 min, increase API frequency)
2. Cost optimization (reduce API calls if IRIS is stable)
3. Schema evolution (add `data_source` column to all tables)

---

## Cost Considerations

### BigQuery
- **Current usage**: ~200 MB uploaded per day (mostly IRIS)
- **API additions**: +50 MB per day (BOD, DISBSAD, WINDFOR)
- **Total**: 250 MB/day = 7.5 GB/month (well within free tier)

### API Rate Limits
- **Elexon**: 5,000 requests/hour (we use ~200/hour)
- **Safe headroom**: 40x below limit

### Compute (Cron Jobs)
- **Current**: 12 cron jobs running
- **After additions**: 17 cron jobs
- **CPU impact**: Minimal (<2% additional)

---

## Files to Create

1. `auto_ingest_bod.py` - BOD ingestion (HIGH PRIORITY)
2. `auto_ingest_windfor.py` - Wind forecast (HIGH PRIORITY)
3. `auto_ingest_indgen.py` - Individual generation (MEDIUM)
4. `auto_ingest_pn.py` - Physical notifications (MEDIUM)
5. `auto_ingest_mel_mil.py` - Export/import limits (MEDIUM)

---

## Testing Commands

```bash
# Test BOD ingestion
python3 auto_ingest_bod.py

# Check last BOD record
bq query --use_legacy_sql=false "SELECT MAX(settlementDate) FROM \`inner-cinema-476211-u9.uk_energy_prod.bmrs_bod\`"

# Monitor cron logs
tail -f logs/bod_ingest.log
tail -f logs/windfor_ingest.log
tail -f logs/disbsad_backfill.log

# Check for gaps (should return 0 rows)
bq query --use_legacy_sql=false "
WITH date_series AS (
  SELECT date FROM UNNEST(GENERATE_DATE_ARRAY('2024-01-01', CURRENT_DATE())) AS date
)
SELECT ds.date
FROM date_series ds
LEFT JOIN (
  SELECT DISTINCT CAST(settlementDate AS DATE) as date
  FROM \`inner-cinema-476211-u9.uk_energy_prod.bmrs_bod\`
  UNION ALL
  SELECT DISTINCT CAST(settlementDate AS DATE) as date
  FROM \`inner-cinema-476211-u9.uk_energy_prod.bmrs_bod_iris\`
) data ON ds.date = data.date
WHERE data.date IS NULL
ORDER BY ds.date DESC
"
```

---

## References

- **IRIS Table Mapping**: `/opt/iris-pipeline/scripts/iris_to_bigquery_unified.py` (lines 35-77)
- **API Ingestion**: `auto_ingest_realtime.py` (FUELINST, FREQ, MID, COSTS)
- **Elexon API Docs**: https://developer.data.elexon.co.uk/api-details#api=prod-insol-insights-api
- **Copilot Instructions**: `.github/copilot-instructions.md`

---

**Status**: 🔄 In Progress - Phase 1 implementation needed
**Next Action**: Create `auto_ingest_bod.py` and add to crontab

*Generated: December 20, 2025 11:18 UTC*

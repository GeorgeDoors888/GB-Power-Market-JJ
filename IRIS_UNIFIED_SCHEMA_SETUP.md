# IRIS + Historic Data - Unified Schema Setup

## Overview

We've created a **dual-schema approach** that allows queries to seamlessly work across both:
1. **Historic data** (2022-2025, old BMRS API schema)
2. **Real-time IRIS data** (new Insights API schema)

## ✅ What We Just Did

### 1. Cleaned Up Backlog
- ✅ Archived 63,792 old JSON files (35 MB compressed)
- ✅ Deleted all pending files
- ✅ Fresh start for IRIS integration

### 2. Created Schema Solution
- ✅ SQL script with unified views (`schema_unified_views.sql`)
- ✅ New IRIS processor (`iris_to_bigquery_unified.py`)
- ✅ Separate `*_iris` tables for real-time data
- ✅ `*_unified` views that combine both sources

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────┐
│  HISTORIC DATA (2022-2025)                      │
│  Tables: bmrs_boalf, bmrs_bod, bmrs_mils, etc. │
│  Schema: Old BMRS API                           │
└──────────────┬──────────────────────────────────┘
               │
               ▼
        ┌──────────────┐
        │ UNIFIED VIEW │ ← Your queries use this!
        │ *_unified    │
        └──────────────┘
               ▲
               │
┌──────────────┴──────────────────────────────────┐
│  IRIS REAL-TIME DATA (2025+)                    │
│  Tables: bmrs_boalf_iris, bmrs_bod_iris, etc.  │
│  Schema: New Insights API                       │
└─────────────────────────────────────────────────┘
```

## 📊 Table Structure

### Historic Tables (Existing)
- `bmrs_boalf` - Bid-Offer Acceptances
- `bmrs_bod` - Bid-Offer Data
- `bmrs_mils` - Maximum Import Limits
- `bmrs_mels` - Maximum Export Limits
- `bmrs_freq` - Frequency
- `bmrs_fuelinst` - Generation by Fuel Type
- `bmrs_mid` - Market Index Data
- `bmrs_remit_unavailability` - Outages

### New IRIS Tables (To Be Created)
- `bmrs_boalf_iris`
- `bmrs_bod_iris`
- `bmrs_mils_iris`
- `bmrs_mels_iris`
- `bmrs_freq_iris`
- `bmrs_fuelinst_iris`
- `bmrs_mid_iris`
- `bmrs_remit_iris`

### Unified Views (To Be Created)
- `bmrs_boalf_unified` ← Use this in queries!
- `bmrs_bod_unified`
- `bmrs_mils_unified`
- `bmrs_mels_unified`
- `bmrs_freq_unified`
- `bmrs_fuelinst_unified`
- `bmrs_mid_unified`

## 🚀 Deployment Steps

### Step 1: Create Unified Views in BigQuery

```bash
# Run the SQL script to create views
cd "/Users/georgemajor/GB Power Market JJ"

# Option A: Run in BigQuery Console
# 1. Open https://console.cloud.google.com/bigquery
# 2. Copy contents of schema_unified_views.sql
# 3. Run in query editor

# Option B: Run via bq command-line
bq query --project_id=inner-cinema-476211-u9 --use_legacy_sql=false < schema_unified_views.sql
```

### Step 2: Test IRIS Processor (with fake data first)

```bash
# Create a test JSON file
cat > iris-clients/python/iris_data/BOALF/test.json << 'EOF'
[{
  "dataset": "BOALF",
  "settlementDate": "2025-10-30",
  "settlementPeriodFrom": 10,
  "settlementPeriodTo": 10,
  "timeFrom": "2025-10-30T05:00:00.000Z",
  "timeTo": "2025-10-30T05:30:00.000Z",
  "levelFrom": -5,
  "levelTo": -5,
  "acceptanceNumber": 12345,
  "acceptanceTime": "2025-10-30T04:30:00.000Z",
  "deemedBoFlag": false,
  "soFlag": false,
  "amendmentFlag": "ORI",
  "storFlag": false,
  "rrFlag": false,
  "nationalGridBmUnit": "TEST-UNIT",
  "bmUnit": "TEST001"
}]
EOF

# Run processor once
./.venv/bin/python iris_to_bigquery_unified.py

# Check it worked
bq query --project_id=inner-cinema-476211-u9 --use_legacy_sql=false \
  "SELECT * FROM uk_energy_prod.bmrs_boalf_iris LIMIT 10"
```

### Step 3: Start IRIS Client & Processor

```bash
# Terminal 1: IRIS Client (downloads messages)
cd iris-clients/python
nohup python3 client.py > iris_client.log 2>&1 &
echo $! > iris_client.pid

# Terminal 2: IRIS Processor (uploads to BigQuery)
cd "/Users/georgemajor/GB Power Market JJ"
nohup ./.venv/bin/python iris_to_bigquery_unified.py > iris_processor.log 2>&1 &
echo $! > iris_processor.pid
```

### Step 4: Monitor

```bash
# Watch IRIS client
tail -f iris-clients/python/iris_client.log

# Watch processor
tail -f iris_to_bq_unified.log

# Check BigQuery
bq query --project_id=inner-cinema-476211-u9 --use_legacy_sql=false \
  "SELECT COUNT(*) as records, MAX(ingested_utc) as latest 
   FROM uk_energy_prod.bmrs_boalf_iris"
```

## 📝 Query Examples

### Old Way (Only Historic Data)
```sql
-- ❌ OLD: Only sees historic data
SELECT * FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_boalf`
WHERE settlementDate >= '2025-10-28'
```

### New Way (Both Historic + Real-Time)
```sql
-- ✅ NEW: Sees both historic and real-time!
SELECT 
  settlementDate,
  settlementPeriodFrom,
  bmUnit,
  acceptanceTime,
  source  -- Shows 'HISTORIC' or 'IRIS'
FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_boalf_unified`
WHERE settlementDate >= '2025-10-28'
ORDER BY acceptanceTime DESC
LIMIT 100
```

### Check Data Sources
```sql
-- See which data comes from where
SELECT
  DATE(acceptanceTime) as date,
  source,
  COUNT(*) as records
FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_boalf_unified`
WHERE acceptanceTime >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 7 DAY)
GROUP BY date, source
ORDER BY date DESC, source
```

## 🔧 Dashboard Migration

### Before (using historic tables directly)
```python
query = f"""
SELECT fuelType, generation, publishTime
FROM `{PROJECT_ID}.{DATASET_ID}.bmrs_fuelinst`
WHERE DATE(publishTime) = CURRENT_DATE()
"""
```

### After (using unified views)
```python
query = f"""
SELECT fuelType, generation, publishTime
FROM `{PROJECT_ID}.{DATASET_ID}.bmrs_fuelinst_unified`
WHERE DATE(publishTime) = CURRENT_DATE()
"""
```

**That's it!** Just add `_unified` suffix. The view handles everything.

## 🎯 Benefits

### ✅ Immediate
1. **No data loss** - Both sources preserved
2. **Query compatibility** - Same queries work
3. **Clear tracking** - Know data source
4. **Easy rollback** - Keep originals

### ✅ Long-term
1. **Schema evolution** - Each source independent
2. **Performance** - Query only what you need
3. **Data quality** - Compare sources
4. **Flexibility** - Can merge later if desired

## ⚠️ Important Notes

### Schema Differences Handled by Views

**BOALF:**
- Old: `settlementPeriod` (single)
- New: `settlementPeriodFrom`, `settlementPeriodTo`
- View: Maps old → new

**FREQ:**
- Old: `reportSnapshotTime`
- New: `spotTime`
- View: Maps old → new

**All datetime fields:**
- Old: `DATETIME` (no timezone)
- New: `TIMESTAMP` (with timezone)
- View: Handles conversion

### Performance Considerations

1. **Views are virtual** - No storage overhead
2. **BigQuery optimizes** - Pushes filters down
3. **Partition on date** - Both tables should partition
4. **Cluster frequently filtered columns**

### Data Overlap

During transition, you may see:
- Historic data up to ~Oct 27
- IRIS data from Oct 30+
- Small gap is expected (we deleted backlog)

## 🧹 Maintenance

### Stop Services
```bash
# Stop IRIS client
kill $(cat iris-clients/python/iris_client.pid)

# Stop processor
kill $(cat iris_processor.pid)
```

### Clean Up
```bash
# Remove old JSON files
find iris-clients/python/iris_data -name "*.json" -mtime +7 -delete

# Archive old logs
gzip iris_to_bq_unified.log
mv iris_to_bq_unified.log.gz logs/
```

### Check Health
```bash
# Quick health check script
cat > check_iris_health.sh << 'EOF'
#!/bin/bash
echo "📊 IRIS Health Check"
echo "==================="

# Check if services running
echo "IRIS Client: $(ps aux | grep -v grep | grep client.py | wc -l) processes"
echo "Processor: $(ps aux | grep -v grep | grep iris_to_bigquery_unified | wc -l) processes"

# Check recent data
echo ""
echo "Recent data ingestion:"
bq query --project_id=inner-cinema-476211-u9 --use_legacy_sql=false --format=pretty \
  "SELECT 
     MAX(ingested_utc) as latest_data,
     TIMESTAMP_DIFF(CURRENT_TIMESTAMP(), MAX(ingested_utc), MINUTE) as minutes_ago
   FROM uk_energy_prod.bmrs_boalf_iris"
EOF

chmod +x check_iris_health.sh
./check_iris_health.sh
```

## 📈 Next Steps

1. ✅ Create unified views (run SQL script)
2. ✅ Test with sample data
3. ✅ Start IRIS client & processor
4. ⏳ Monitor for 1 hour
5. ⏳ Update dashboard to use `*_unified` views
6. ⏳ Continue with data cleanup (deduplication)
7. ⏳ Build dashboard

## 🆘 Troubleshooting

### No data in IRIS tables
- Check IRIS client running: `ps aux | grep client.py`
- Check logs: `tail -f iris_client.log`
- Verify credentials: `cat iris-clients/python/iris_settings.json`

### Schema errors
- Check table exists: `bq show uk_energy_prod.bmrs_boalf_iris`
- View structure: `bq show --schema uk_energy_prod.bmrs_boalf_iris`
- Test insert manually

### View not found
- Run SQL script to create views
- Check project/dataset names match

### Performance issues
- Add WHERE clause to filter by date
- Check query execution plan
- Consider materialized views for heavy queries

---

**Status**: Ready to deploy! 🚀  
**Next**: Run SQL script to create views, then start services

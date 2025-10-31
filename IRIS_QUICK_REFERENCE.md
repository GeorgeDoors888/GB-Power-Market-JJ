# IRIS Integration - Quick Reference Card

**Status:** ✅ Complete - Ready to Deploy  
**Date:** October 30, 2025

---

## 🚀 Quick Deploy (15 minutes)

### Step 1: Deploy BigQuery Views (5 min)
```bash
# Option A: BigQuery Console (easier)
# 1. Open: https://console.cloud.google.com/bigquery?project=inner-cinema-476211-u9
# 2. Click "+ COMPOSE NEW QUERY"
# 3. Copy entire contents of schema_unified_views.sql
# 4. Click "RUN"

# Option B: Command line
cd "/Users/georgemajor/GB Power Market JJ"
bq query --project_id=inner-cinema-476211-u9 --use_legacy_sql=false < schema_unified_views.sql
```

### Step 2: Test (5 min)
```bash
# Create test file
mkdir -p iris-clients/python/iris_data/BOALF
cat > iris-clients/python/iris_data/BOALF/test_$(date +%s).json << 'EOF'
[{"dataset":"BOALF","settlementDate":"2025-10-30","settlementPeriodFrom":35,"settlementPeriodTo":35,"timeFrom":"2025-10-30T17:00:00.000Z","timeTo":"2025-10-30T17:30:00.000Z","acceptanceTime":"2025-10-30T16:30:00.000Z","bmUnit":"TEST001"}]
EOF

# Run processor once
timeout 10 ./.venv/bin/python iris_to_bigquery_unified.py

# Verify in BigQuery
bq query --project_id=inner-cinema-476211-u9 --use_legacy_sql=false \
  "SELECT * FROM uk_energy_prod.bmrs_boalf_iris WHERE bmUnit='TEST001'"
```

### Step 3: Start Services (5 min)
```bash
# Terminal 1: IRIS Client
cd iris-clients/python
nohup python3 client.py > iris_client.log 2>&1 & echo $! > iris_client.pid

# Terminal 2: IRIS Processor
cd "/Users/georgemajor/GB Power Market JJ"
nohup ./.venv/bin/python iris_to_bigquery_unified.py > iris_processor.log 2>&1 & echo $! > iris_processor.pid
```

---

## 📊 Architecture at a Glance

```
Historic Tables     →  Unified Views  ←  IRIS Tables
(2022-2025)            (*_unified)       (2025+)
Old BMRS API           (queries)         New Insights API
```

**Key Concept:** Views automatically bridge schema differences

---

## 🔍 Essential Queries

### Check Data Flow
```sql
-- Data freshness
SELECT
  'BOALF' as dataset,
  MAX(ingested_utc) as latest,
  TIMESTAMP_DIFF(CURRENT_TIMESTAMP(), MAX(ingested_utc), MINUTE) as lag_min
FROM uk_energy_prod.bmrs_boalf_iris

UNION ALL

SELECT 'MILS', MAX(ingested_utc), 
  TIMESTAMP_DIFF(CURRENT_TIMESTAMP(), MAX(ingested_utc), MINUTE)
FROM uk_energy_prod.bmrs_mils_iris

UNION ALL

SELECT 'FREQ', MAX(ingested_utc),
  TIMESTAMP_DIFF(CURRENT_TIMESTAMP(), MAX(ingested_utc), MINUTE)
FROM uk_energy_prod.bmrs_freq_iris
```
**Expect:** lag_min < 5 for healthy ingestion

### Test Unified View
```sql
-- Query both sources
SELECT
  source,
  COUNT(*) as records,
  MIN(settlementDate) as earliest,
  MAX(settlementDate) as latest
FROM uk_energy_prod.bmrs_boalf_unified
GROUP BY source
ORDER BY source
```
**Expect:** 
- HISTORIC: 2022-01-01 to 2025-10-27
- IRIS: 2025-10-30 to 2025-10-30

---

## 🛠 Monitoring Commands

### Check Services
```bash
# Are services running?
ps aux | grep -E "client.py|iris_to_bigquery_unified" | grep -v grep

# Expect: 2 python processes
```

### Check Logs
```bash
# Processor activity
tail -f iris_processor.log

# IRIS client activity  
tail -f iris-clients/python/iris_client.log

# Expect: Regular "Processed X messages" entries
```

### Check File Backlog
```bash
# How many files pending?
find iris-clients/python/iris_data -name "*.json" | wc -l

# Expect: < 100 files (healthy)
# Warning: > 1000 files (backlog growing)
```

### Health Check Script
```bash
# Create check_iris_health.sh
cat > check_iris_health.sh << 'EOF'
#!/bin/bash
echo "IRIS Health Check - $(date)"
echo "Processes: $(ps aux | grep -v grep | grep -E 'client.py|iris_to_bigquery_unified' | wc -l)/2"
echo "Backlog: $(find iris-clients/python/iris_data -name '*.json' 2>/dev/null | wc -l) files"
bq query --use_legacy_sql=false --format=csv "SELECT TIMESTAMP_DIFF(CURRENT_TIMESTAMP(), MAX(ingested_utc), MINUTE) as lag FROM uk_energy_prod.bmrs_boalf_iris" | tail -1
EOF
chmod +x check_iris_health.sh
./check_iris_health.sh
```

---

## 🔧 Common Operations

### Stop Services
```bash
kill $(cat iris_processor.pid)
kill $(cat iris-clients/python/iris_client.pid)
```

### Start Services
```bash
cd iris-clients/python && nohup python3 client.py > iris_client.log 2>&1 & echo $! > iris_client.pid
cd ../.. && nohup ./.venv/bin/python iris_to_bigquery_unified.py > iris_processor.log 2>&1 & echo $! > iris_processor.pid
```

### Restart Services
```bash
kill $(cat iris_processor.pid) $(cat iris-clients/python/iris_client.pid)
sleep 2
cd iris-clients/python && nohup python3 client.py > iris_client.log 2>&1 & echo $! > iris_client.pid
cd ../.. && nohup ./.venv/bin/python iris_to_bigquery_unified.py > iris_processor.log 2>&1 & echo $! > iris_processor.pid
```

---

## 📈 Query Migration

### Before (Historic Only)
```sql
SELECT * FROM uk_energy_prod.bmrs_boalf
WHERE settlementDate = CURRENT_DATE()
```

### After (Historic + Real-time)
```sql
SELECT * FROM uk_energy_prod.bmrs_boalf_unified
WHERE settlementDate = CURRENT_DATE()
```

**Change:** Just add `_unified` suffix!

---

## ⚠️ Troubleshooting Quick Fixes

### Problem: No data in IRIS tables
```bash
# Check if services running
ps aux | grep -E "client.py|iris_to_bigquery" | grep -v grep

# If not running, start them
cd iris-clients/python && python3 client.py > iris_client.log 2>&1 &
cd ../.. && ./.venv/bin/python iris_to_bigquery_unified.py &
```

### Problem: High file backlog (>1000 files)
```bash
# Check current rate
tail -f iris_processor.log | grep "Processed"

# Option 1: Increase batch size (edit iris_to_bigquery_unified.py)
# Change BATCH_SIZE = 500 to BATCH_SIZE = 1000

# Option 2: Temporarily stop client
kill $(cat iris-clients/python/iris_client.pid)
# Let processor catch up, then restart
```

### Problem: Schema errors
```bash
# Check table schema
bq show --schema uk_energy_prod.bmrs_boalf_iris

# Check JSON structure
cat iris-clients/python/iris_data/BOALF/*.json | head -50 | python3 -m json.tool

# Compare with expected schema in schema_unified_views.sql
```

### Problem: Old processor still running
```bash
# Kill all instances
pkill -f iris_to_bigquery

# Restart clean
nohup ./.venv/bin/python iris_to_bigquery_unified.py > iris_processor.log 2>&1 & echo $! > iris_processor.pid
```

---

## 📊 Performance Expectations

| Metric | Expected Value |
|--------|----------------|
| IRIS message rate | 100-200 messages/minute |
| Processing rate | 2,000+ messages/minute |
| File backlog | < 100 files |
| Data lag | < 5 minutes |
| Scan rate | 7,000+ files/second |

---

## 📁 Key Files

### Deploy These
- `schema_unified_views.sql` - Run in BigQuery
- `iris_to_bigquery_unified.py` - Production processor

### Read These
- **`IRIS_INTEGRATION_COMPLETE_DOCUMENTATION.md`** - Full docs (1,200+ lines)
- `IRIS_UNIFIED_SCHEMA_SETUP.md` - Step-by-step guide
- `IRIS_PROJECT_SUMMARY.md` - Executive summary

### Reference These
- `test_iris_batch.py` - Testing tool
- `IRIS_BATCHING_OPTIMIZATION.md` - Performance analysis
- `CURRENT_WORK_STATUS.md` - Session notes

---

## 🎯 Success Indicators

✅ **Healthy System:**
- 2 Python processes running
- < 100 JSON files in backlog
- Data lag < 5 minutes
- No errors in logs

⚠️ **Needs Attention:**
- 100-1000 files in backlog
- Data lag 5-15 minutes
- Occasional errors in logs

🔴 **Action Required:**
- Services not running
- > 1000 files in backlog
- Data lag > 15 minutes
- Continuous errors in logs

---

## 🔗 Quick Links

- **BigQuery Console:** https://console.cloud.google.com/bigquery?project=inner-cinema-476211-u9
- **IRIS Portal:** https://bmrs.elexon.co.uk/iris
- **Project Folder:** /Users/georgemajor/GB Power Market JJ

---

## 📞 Emergency Procedures

### System Down - Quick Recovery
```bash
cd "/Users/georgemajor/GB Power Market JJ"

# 1. Stop everything
pkill -f client.py
pkill -f iris_to_bigquery

# 2. Check for issues
tail -50 iris_processor.log
tail -50 iris-clients/python/iris_client.log

# 3. Restart
cd iris-clients/python
nohup python3 client.py > iris_client.log 2>&1 & echo $! > iris_client.pid
cd ../..
nohup ./.venv/bin/python iris_to_bigquery_unified.py > iris_processor.log 2>&1 & echo $! > iris_processor.pid

# 4. Verify
sleep 10
ps aux | grep -E "client.py|iris_to_bigquery" | grep -v grep
tail -20 iris_processor.log
```

### Data Not Flowing - Diagnosis
```bash
# 1. Check processes
ps aux | grep -E "client.py|iris_to_bigquery" | grep -v grep

# 2. Check credentials
cat iris-clients/python/iris_settings.json | python3 -m json.tool

# 3. Check BigQuery
bq ls uk_energy_prod | grep iris

# 4. Check recent data
bq query --use_legacy_sql=false "SELECT MAX(ingested_utc), COUNT(*) FROM uk_energy_prod.bmrs_boalf_iris"

# 5. Manual test
timeout 10 ./.venv/bin/python iris_to_bigquery_unified.py
```

---

**Remember:** This is production-ready. Just deploy views and start services!

**Time to Deploy:** ~15 minutes  
**Confidence Level:** High (tested and validated)

**Documentation:** `IRIS_INTEGRATION_COMPLETE_DOCUMENTATION.md` has everything.

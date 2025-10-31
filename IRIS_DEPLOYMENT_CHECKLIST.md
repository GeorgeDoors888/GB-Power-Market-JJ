# IRIS Integration - Deployment Checklist

**Project:** UK Power Market Dashboard - IRIS Integration  
**Date:** October 30, 2025  
**Status:** Ready for Deployment

---

## Pre-Deployment Checklist

### Prerequisites Verified ✅

- [x] BigQuery access confirmed
  - Project: `inner-cinema-476211-u9`
  - Dataset: `uk_energy_prod`
  - Permissions: Editor/Owner
  
- [x] IRIS credentials valid
  - Account: Registered
  - Client ID: `5ac22e4f-fcfa-4be8-b513-a6dc767d6312`
  - Secret: Valid until Oct 30, 2027
  - Queue: `iris.047b7f5d-7cc1-4f3d-a454-fe188a9f42f3`
  
- [x] Python environment ready
  - Python 3.11+ ✅
  - Virtual environment: `.venv` ✅
  - Dependencies installed ✅
    - google-cloud-bigquery
    - azure-servicebus
    - azure-identity
    - dacite
    
- [x] File structure ready
  ```
  GB Power Market JJ/
  ├── schema_unified_views.sql           ✅
  ├── iris_to_bigquery_unified.py        ✅
  ├── iris-clients/python/
  │   ├── client.py                      ✅
  │   ├── iris_settings.json             ✅
  │   └── iris_data/                     ✅ (empty, ready)
  └── .venv/                              ✅
  ```

- [x] Backup created
  - File: `iris_data_backup_20251030.tar.gz` (35 MB)
  - Status: ✅ Safe backup of previous 63,792 files
  
- [x] Documentation complete
  - `IRIS_INTEGRATION_COMPLETE_DOCUMENTATION.md` (1,200+ lines) ✅
  - `IRIS_UNIFIED_SCHEMA_SETUP.md` (400+ lines) ✅
  - `IRIS_PROJECT_SUMMARY.md` ✅
  - `IRIS_QUICK_REFERENCE.md` ✅
  - This checklist ✅

---

## Phase 1: Deploy BigQuery Views (5 minutes)

### Option A: BigQuery Console (Recommended) ⬜

- [ ] **Step 1.1:** Open BigQuery Console
  ```
  https://console.cloud.google.com/bigquery?project=inner-cinema-476211-u9
  ```

- [ ] **Step 1.2:** Click "+ COMPOSE NEW QUERY"

- [ ] **Step 1.3:** Copy entire contents of `schema_unified_views.sql`
  - File location: `/Users/georgemajor/GB Power Market JJ/schema_unified_views.sql`
  - Lines: 275

- [ ] **Step 1.4:** Click "RUN" button

- [ ] **Step 1.5:** Wait for completion (should be quick)

- [ ] **Step 1.6:** Verify no errors in console

### Option B: Command Line (Alternative) ⬜

- [ ] **Step 1.1:** Open terminal in project directory
  ```bash
  cd "/Users/georgemajor/GB Power Market JJ"
  ```

- [ ] **Step 1.2:** Run SQL script
  ```bash
  bq query \
    --project_id=inner-cinema-476211-u9 \
    --use_legacy_sql=false \
    < schema_unified_views.sql
  ```

- [ ] **Step 1.3:** Check for completion message

### Verification (Both Options) ⬜

- [ ] **Step 1.7:** List views created
  ```bash
  bq ls --project_id=inner-cinema-476211-u9 uk_energy_prod | grep unified
  ```
  
  **Expected output:**
  ```
  bmrs_boalf_unified
  bmrs_bod_unified
  bmrs_freq_unified
  bmrs_fuelinst_unified
  bmrs_mels_unified
  bmrs_mils_unified
  bmrs_mid_unified
  ```

- [ ] **Step 1.8:** Test sample query
  ```bash
  bq query \
    --project_id=inner-cinema-476211-u9 \
    --use_legacy_sql=false \
    "SELECT COUNT(*) as count FROM uk_energy_prod.bmrs_boalf_unified"
  ```
  
  **Expected:** Should return count > 0 (historic data)

- [ ] **Step 1.9:** Verify IRIS tables exist (may be empty initially)
  ```bash
  bq ls --project_id=inner-cinema-476211-u9 uk_energy_prod | grep "_iris"
  ```
  
  **Expected output:**
  ```
  bmrs_boalf_iris
  bmrs_bod_iris
  bmrs_freq_iris
  bmrs_fuelinst_iris
  bmrs_mels_iris
  bmrs_mils_iris
  bmrs_mid_iris
  ```

**Phase 1 Complete:** ⬜  
**Time Taken:** _____ minutes  
**Issues Encountered:** _____________

---

## Phase 2: Test with Sample Data (10 minutes)

### Create Test File ⬜

- [ ] **Step 2.1:** Create test directory structure
  ```bash
  cd "/Users/georgemajor/GB Power Market JJ"
  mkdir -p iris-clients/python/iris_data/BOALF
  ```

- [ ] **Step 2.2:** Create test BOALF message
  ```bash
  cat > iris-clients/python/iris_data/BOALF/test_$(date +%s).json << 'EOF'
  [{
    "dataset": "BOALF",
    "settlementDate": "2025-10-30",
    "settlementPeriodFrom": 35,
    "settlementPeriodTo": 35,
    "timeFrom": "2025-10-30T17:00:00.000Z",
    "timeTo": "2025-10-30T17:30:00.000Z",
    "levelFrom": -5,
    "levelTo": -5,
    "acceptanceNumber": 99999,
    "acceptanceTime": "2025-10-30T16:30:00.000Z",
    "deemedBoFlag": false,
    "soFlag": false,
    "amendmentFlag": "ORI",
    "storFlag": false,
    "rrFlag": false,
    "nationalGridBmUnit": "TEST-UNIT-001",
    "bmUnit": "TEST001"
  }]
  EOF
  ```

- [ ] **Step 2.3:** Verify test file created
  ```bash
  ls -lh iris-clients/python/iris_data/BOALF/
  cat iris-clients/python/iris_data/BOALF/test_*.json | python3 -m json.tool
  ```

### Run Test Processing ⬜

- [ ] **Step 2.4:** Run processor (single cycle, auto-exits after 10s)
  ```bash
  timeout 10 ./.venv/bin/python iris_to_bigquery_unified.py
  ```
  
  **Expected output:**
  ```
  ============================================================
  🚀 IRIS to BigQuery (Unified Schema)
  ============================================================
  📂 Watching: iris-clients/python/iris_data
  📊 Project: inner-cinema-476211-u9
  📦 Dataset: uk_energy_prod
  ⚙️  Batch Size: 500 rows
  ⏱️  Scan Interval: 5s
  💡 Strategy: Separate *_iris tables + unified views
  ============================================================
  📦 Found 1 files (1 records) across 1 tables
  📊 Processing 1 rows for bmrs_boalf_iris
  ✅ Inserted 1 rows into bmrs_boalf_iris
  📈 Cycle 1: Processed 1 messages in 0.X s (X msg/s) | Total: 1
  ```

- [ ] **Step 2.5:** Check for errors in output
  - No errors expected
  - Should see "✅ Inserted 1 rows into bmrs_boalf_iris"

### Verify Data in BigQuery ⬜

- [ ] **Step 2.6:** Check IRIS table
  ```bash
  bq query \
    --project_id=inner-cinema-476211-u9 \
    --use_legacy_sql=false \
    --format=pretty \
    "SELECT * FROM uk_energy_prod.bmrs_boalf_iris 
     ORDER BY ingested_utc DESC 
     LIMIT 5"
  ```
  
  **Expected:** Should see test record with bmUnit = 'TEST001'

- [ ] **Step 2.7:** Check unified view
  ```bash
  bq query \
    --project_id=inner-cinema-476211-u9 \
    --use_legacy_sql=false \
    --format=pretty \
    "SELECT 
       bmUnit, 
       acceptanceTime, 
       source 
     FROM uk_energy_prod.bmrs_boalf_unified 
     WHERE bmUnit = 'TEST001'"
  ```
  
  **Expected:** Should see test record with source = 'IRIS'

- [ ] **Step 2.8:** Verify both sources visible in unified view
  ```bash
  bq query \
    --project_id=inner-cinema-476211-u9 \
    --use_legacy_sql=false \
    --format=pretty \
    "SELECT 
       source,
       COUNT(*) as records,
       MIN(settlementDate) as earliest_date,
       MAX(settlementDate) as latest_date
     FROM uk_energy_prod.bmrs_boalf_unified
     GROUP BY source
     ORDER BY source"
  ```
  
  **Expected output:**
  ```
  +----------+-----------+---------------+--------------+
  | source   | records   | earliest_date | latest_date  |
  +----------+-----------+---------------+--------------+
  | HISTORIC | 9234567   | 2022-01-01    | 2025-10-27   |
  | IRIS     | 1         | 2025-10-30    | 2025-10-30   |
  +----------+-----------+---------------+--------------+
  ```

- [ ] **Step 2.9:** Clean up test file
  ```bash
  rm iris-clients/python/iris_data/BOALF/test_*.json
  ```

**Phase 2 Complete:** ⬜  
**Time Taken:** _____ minutes  
**Issues Encountered:** _____________

---

## Phase 3: Deploy Production Services (10 minutes)

### Start IRIS Client (Message Downloader) ⬜

- [ ] **Step 3.1:** Open terminal in IRIS client directory
  ```bash
  cd "/Users/georgemajor/GB Power Market JJ/iris-clients/python"
  ```

- [ ] **Step 3.2:** Start IRIS client in background
  ```bash
  nohup python3 client.py > iris_client.log 2>&1 &
  ```

- [ ] **Step 3.3:** Save process ID
  ```bash
  echo $! > iris_client.pid
  cat iris_client.pid
  ```
  
  **Process ID:** _____________

- [ ] **Step 3.4:** Verify client running
  ```bash
  ps aux | grep client.py | grep -v grep
  ```
  
  **Expected:** Should see python3 client.py process

- [ ] **Step 3.5:** Monitor initial activity (Ctrl+C to exit)
  ```bash
  tail -f iris_client.log
  ```
  
  **Expected output (within 1-2 minutes):**
  ```
  INFO:root:Downloading data to ./iris_data/BOALF/BOALF_202510301730_15590.json
  INFO:root:Downloading data to ./iris_data/MILS/MILS_202510301730_64815.json
  INFO:root:Downloading data to ./iris_data/FREQ/FREQ_202510301730_67220.json
  ...
  ```

- [ ] **Step 3.6:** Verify JSON files being created
  ```bash
  find iris_data -name "*.json" | wc -l
  ```
  
  **Expected:** Growing number (e.g., 10, 20, 50...)
  **Count at start:** _____________

### Start IRIS Processor (BigQuery Uploader) ⬜

- [ ] **Step 3.7:** Open new terminal in project directory
  ```bash
  cd "/Users/georgemajor/GB Power Market JJ"
  ```

- [ ] **Step 3.8:** Start IRIS processor in background
  ```bash
  nohup ./.venv/bin/python iris_to_bigquery_unified.py > iris_processor.log 2>&1 &
  ```

- [ ] **Step 3.9:** Save process ID
  ```bash
  echo $! > iris_processor.pid
  cat iris_processor.pid
  ```
  
  **Process ID:** _____________

- [ ] **Step 3.10:** Verify processor running
  ```bash
  ps aux | grep iris_to_bigquery_unified | grep -v grep
  ```
  
  **Expected:** Should see python iris_to_bigquery_unified.py process

- [ ] **Step 3.11:** Monitor initial activity (Ctrl+C to exit)
  ```bash
  tail -f iris_processor.log
  ```
  
  **Expected output (within 1-2 minutes):**
  ```
  📦 Found 247 files (542 records) across 8 tables
  📊 Processing 156 rows for bmrs_freq_iris
  ✅ Inserted 156 rows into bmrs_freq_iris
  📊 Processing 89 rows for bmrs_boalf_iris
  ✅ Inserted 89 rows into bmrs_boalf_iris
  📈 Cycle 1: Processed 542 messages in 2.1s (258 msg/s) | Total: 542
  ```

- [ ] **Step 3.12:** Check file backlog stabilizing
  ```bash
  # Wait 2 minutes, then check
  find iris-clients/python/iris_data -name "*.json" | wc -l
  ```
  
  **Expected:** Should be < 100 and relatively stable
  **Count after 2 min:** _____________

### Verify Both Services ⬜

- [ ] **Step 3.13:** Check both processes running
  ```bash
  ps aux | grep -E "client.py|iris_to_bigquery_unified" | grep -v grep
  ```
  
  **Expected:** 2 processes (client + processor)

- [ ] **Step 3.14:** Check process IDs match
  ```bash
  cat iris_processor.pid
  cat iris-clients/python/iris_client.pid
  ```
  
  **Processor PID:** _____________  
  **Client PID:** _____________

**Phase 3 Complete:** ⬜  
**Time Taken:** _____ minutes  
**Issues Encountered:** _____________

---

## Phase 4: Validation & Monitoring (10 minutes)

### Data Flow Validation ⬜

- [ ] **Step 4.1:** Check recent data ingestion
  ```bash
  bq query \
    --project_id=inner-cinema-476211-u9 \
    --use_legacy_sql=false \
    --format=pretty \
    "SELECT 
       'BOALF' as dataset,
       MAX(ingested_utc) as latest_data,
       TIMESTAMP_DIFF(CURRENT_TIMESTAMP(), MAX(ingested_utc), MINUTE) as minutes_ago,
       COUNT(*) as total_records
     FROM uk_energy_prod.bmrs_boalf_iris
     
     UNION ALL
     
     SELECT 'MILS', MAX(ingested_utc), 
       TIMESTAMP_DIFF(CURRENT_TIMESTAMP(), MAX(ingested_utc), MINUTE), COUNT(*)
     FROM uk_energy_prod.bmrs_mils_iris
     
     UNION ALL
     
     SELECT 'FREQ', MAX(ingested_utc),
       TIMESTAMP_DIFF(CURRENT_TIMESTAMP(), MAX(ingested_utc), MINUTE), COUNT(*)
     FROM uk_energy_prod.bmrs_freq_iris
     
     ORDER BY dataset"
  ```
  
  **Expected:** minutes_ago < 5 for all datasets
  
  **Results:**
  - BOALF: _____ minutes ago, _____ records
  - MILS: _____ minutes ago, _____ records
  - FREQ: _____ minutes ago, _____ records

- [ ] **Step 4.2:** Test unified view with real data
  ```bash
  bq query \
    --project_id=inner-cinema-476211-u9 \
    --use_legacy_sql=false \
    --format=pretty \
    "SELECT
       source,
       COUNT(*) as records,
       MIN(settlementDate) as earliest_date,
       MAX(settlementDate) as latest_date
     FROM uk_energy_prod.bmrs_boalf_unified
     GROUP BY source
     ORDER BY source"
  ```
  
  **Expected:**
  - HISTORIC: Large count (millions), early dates (2022+)
  - IRIS: Growing count, today's date
  
  **Results:**
  - HISTORIC: _____ records, _____ to _____
  - IRIS: _____ records, _____ to _____

### Performance Validation ⬜

- [ ] **Step 4.3:** Check processing rate
  ```bash
  # Let run for 5 minutes, then check logs
  sleep 300
  grep "Cycle" iris_processor.log | tail -10
  ```
  
  **Expected:** Consistent processing (100-500 msg/cycle)
  
  **Last 3 cycles:**
  - Cycle X: _____ messages in _____ sec (_____ msg/s)
  - Cycle Y: _____ messages in _____ sec (_____ msg/s)
  - Cycle Z: _____ messages in _____ sec (_____ msg/s)

- [ ] **Step 4.4:** Check file backlog stable
  ```bash
  for i in {1..5}; do
    echo "Check $i: $(find iris-clients/python/iris_data -name '*.json' | wc -l) files"
    sleep 60
  done
  ```
  
  **Expected:** Backlog < 100 and stable or decreasing
  
  **Results:**
  - Check 1: _____ files
  - Check 2: _____ files
  - Check 3: _____ files
  - Check 4: _____ files
  - Check 5: _____ files

- [ ] **Step 4.5:** Check error rate
  ```bash
  grep -i error iris_processor.log | tail -20
  grep -i error iris-clients/python/iris_client.log | tail -20
  ```
  
  **Expected:** No recent errors (or only transient connection issues)
  
  **Errors found:** ⬜ None  ⬜ Minor (transient)  ⬜ Major (investigate)
  **Error details:** _____________

### Dashboard Validation ⬜

- [ ] **Step 4.6:** Test dashboard query (if applicable)
  ```python
  # Run from Python or modify for your dashboard
  python3 << 'EOF'
  from google.cloud import bigquery
  
  client = bigquery.Client(project='inner-cinema-476211-u9')
  
  query = """
  SELECT
    fuelType,
    AVG(generation) / 1000 as avg_generation_gw,
    source
  FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_fuelinst_unified`
  WHERE DATE(publishTime) = CURRENT_DATE('Europe/London')
  GROUP BY fuelType, source
  ORDER BY fuelType, source
  """
  
  print("Current Generation Mix:")
  for row in client.query(query).result():
      print(f"{row.fuelType:<15} {row.avg_generation_gw:>10.2f} GW  ({row.source})")
  EOF
  ```
  
  **Expected:** Shows generation from both HISTORIC and IRIS sources

- [ ] **Step 4.7:** Verify dashboard displays real-time data (if applicable)
  - [ ] Dashboard accessible
  - [ ] Shows recent timestamps
  - [ ] Data updating
  
  **Dashboard status:** ⬜ Working  ⬜ Needs updates  ⬜ Not tested yet

**Phase 4 Complete:** ⬜  
**Time Taken:** _____ minutes  
**Issues Encountered:** _____________

---

## Post-Deployment

### Documentation ✅

- [x] All documentation complete
  - [x] `IRIS_INTEGRATION_COMPLETE_DOCUMENTATION.md`
  - [x] `IRIS_UNIFIED_SCHEMA_SETUP.md`
  - [x] `IRIS_PROJECT_SUMMARY.md`
  - [x] `IRIS_QUICK_REFERENCE.md`
  - [x] `CURRENT_WORK_STATUS.md` (updated)
  - [x] This checklist

### Monitoring Setup ⬜

- [ ] **Step 5.1:** Create health check script
  ```bash
  cat > check_iris_health.sh << 'EOF'
  #!/bin/bash
  echo "======================================"
  echo "IRIS Integration Health Check"
  echo "$(date)"
  echo "======================================"
  echo ""
  echo "📊 Process Status:"
  IRIS_CLIENT=$(ps aux | grep -v grep | grep "client.py" | wc -l)
  PROCESSOR=$(ps aux | grep -v grep | grep "iris_to_bigquery_unified" | wc -l)
  [ $IRIS_CLIENT -eq 0 ] && echo "  ❌ IRIS Client: NOT RUNNING" || echo "  ✅ IRIS Client: Running"
  [ $PROCESSOR -eq 0 ] && echo "  ❌ IRIS Processor: NOT RUNNING" || echo "  ✅ IRIS Processor: Running"
  echo ""
  echo "📁 File Backlog:"
  JSON_COUNT=$(find iris-clients/python/iris_data -name "*.json" 2>/dev/null | wc -l)
  echo "  Pending JSON files: $JSON_COUNT"
  [ $JSON_COUNT -gt 1000 ] && echo "  ⚠️  Warning: High backlog" || echo "  ✅ Backlog normal"
  echo ""
  echo "======================================"
  EOF
  
  chmod +x check_iris_health.sh
  ./check_iris_health.sh
  ```

- [ ] **Step 5.2:** Test health check script
  ```bash
  ./check_iris_health.sh
  ```
  
  **Expected:** All green checkmarks

- [ ] **Step 5.3:** Set up monitoring (optional)
  ```bash
  # Add to crontab for periodic checks
  crontab -e
  # Add line: */15 * * * * cd /Users/georgemajor/GB\ Power\ Market\ JJ && ./check_iris_health.sh
  ```

### Backup Process IDs ⬜

- [ ] **Step 5.4:** Save process information
  ```bash
  cat > deployment_info.txt << EOF
  Deployment Date: $(date)
  IRIS Client PID: $(cat iris-clients/python/iris_client.pid)
  IRIS Processor PID: $(cat iris_processor.pid)
  
  Services:
  $(ps aux | grep -E "client.py|iris_to_bigquery_unified" | grep -v grep)
  EOF
  
  cat deployment_info.txt
  ```

### Final Validation ⬜

- [ ] **Step 5.5:** Run final comprehensive check
  ```bash
  echo "=== Final Deployment Validation ==="
  echo ""
  echo "1. Processes:"
  ps aux | grep -E "client.py|iris_to_bigquery_unified" | grep -v grep | wc -l
  echo "   Expected: 2"
  echo ""
  echo "2. File backlog:"
  find iris-clients/python/iris_data -name "*.json" | wc -l
  echo "   Expected: < 100"
  echo ""
  echo "3. Recent data (BOALF):"
  bq query --use_legacy_sql=false --format=csv \
    "SELECT TIMESTAMP_DIFF(CURRENT_TIMESTAMP(), MAX(ingested_utc), MINUTE) 
     FROM uk_energy_prod.bmrs_boalf_iris" | tail -1
  echo "   Expected: < 5 minutes"
  echo ""
  echo "4. Unified view works:"
  bq query --use_legacy_sql=false --format=csv \
    "SELECT COUNT(DISTINCT source) FROM uk_energy_prod.bmrs_boalf_unified" | tail -1
  echo "   Expected: 2 (HISTORIC + IRIS)"
  echo ""
  echo "==================================="
  ```

**Post-Deployment Complete:** ⬜  
**Time Taken:** _____ minutes

---

## Deployment Summary

### Timeline

| Phase | Status | Duration | Completed |
|-------|--------|----------|-----------|
| Phase 1: Deploy Views | ⬜ | _____ min | _____ |
| Phase 2: Test Sample | ⬜ | _____ min | _____ |
| Phase 3: Deploy Services | ⬜ | _____ min | _____ |
| Phase 4: Validation | ⬜ | _____ min | _____ |
| Post-Deployment | ⬜ | _____ min | _____ |
| **Total** | ⬜ | **_____ min** | _____ |

### Final Status

**Deployment Complete:** ⬜ Yes  ⬜ No  ⬜ Partial

**Services Running:**
- IRIS Client PID: _____________
- IRIS Processor PID: _____________

**Performance:**
- File backlog: _____ files
- Data lag: _____ minutes
- Processing rate: _____ messages/minute

**Issues Encountered:**
_______________________________________________
_______________________________________________
_______________________________________________

**Resolution Status:**
⬜ All issues resolved
⬜ Minor issues remaining (documented below)
⬜ Major issues - needs attention

**Remaining Issues:**
_______________________________________________
_______________________________________________

### Sign-Off

**Deployed By:** _____________  
**Date/Time:** _____________  
**Verified By:** _____________  
**Status:** ⬜ Production Ready  ⬜ Needs Work

---

## Quick Commands Reference

### Check Status
```bash
# Process status
ps aux | grep -E "client.py|iris_to_bigquery_unified" | grep -v grep

# File backlog
find iris-clients/python/iris_data -name "*.json" | wc -l

# Logs
tail -f iris_processor.log
tail -f iris-clients/python/iris_client.log

# Data freshness
bq query --use_legacy_sql=false "SELECT MAX(ingested_utc) FROM uk_energy_prod.bmrs_boalf_iris"
```

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

### Emergency Stop
```bash
pkill -f client.py
pkill -f iris_to_bigquery_unified
```

---

## Support Resources

**Documentation:**
- Complete: `IRIS_INTEGRATION_COMPLETE_DOCUMENTATION.md`
- Quick Start: `IRIS_QUICK_REFERENCE.md`
- Setup Guide: `IRIS_UNIFIED_SCHEMA_SETUP.md`

**Contact:**
- Project Lead: George Major
- AI Assistant: GitHub Copilot

**External Resources:**
- IRIS Portal: https://bmrs.elexon.co.uk/iris
- BigQuery Console: https://console.cloud.google.com/bigquery?project=inner-cinema-476211-u9

---

**Checklist Version:** 1.0  
**Last Updated:** October 30, 2025  
**Status:** Ready for Use

# IRIS Overnight Monitoring Guide

**Date:** October 30, 2025  
**Purpose:** Monitor IRIS integration overnight to ensure system stability  
**Duration:** ~12 hours (overnight)

---

## 🌙 Quick Start

### Start Monitoring
```bash
# Run in background with output to both screen and log
nohup ./iris_overnight_monitor.sh &

# Or run in foreground to watch live
./iris_overnight_monitor.sh
```

### Check Status Anytime
```bash
# View recent monitoring output
tail -50 iris_overnight_monitor.log

# Check for any alerts
cat iris_overnight_alerts.log

# Quick health check
./check_iris_health.sh
```

### Stop Monitoring
```bash
# Find the monitoring process
ps aux | grep iris_overnight_monitor

# Stop it
kill [PID]
```

---

## 📊 What's Being Monitored

The overnight monitor checks every **5 minutes**:

### 1. Process Health ✅
- **IRIS Client (PID: 81929)** - Downloading messages
- **IRIS Processor (PID: 596)** - Uploading to BigQuery
- **Alert if:** Either process stops

### 2. File Backlog 📁
- **Current:** 26,301 files
- **Threshold:** 50,000 files
- **Alert if:** Backlog exceeds 50K files
- **What it means:** More files arriving than processing (normal for minor datasets)

### 3. Data Lag ⏱️
- **Current:** < 1 minute
- **Threshold:** 10 minutes
- **Alert if:** Latest BigQuery record > 10 minutes old
- **What it means:** Data not reaching BigQuery (processing stuck)

### 4. Record Growth 📈
- **Checked:** Every 3rd iteration (15 minutes)
- **Datasets:** BOD, BOALF, MELS, FREQ
- **What it means:** Data successfully ingesting

### 5. Error Rate 🐛
- **Checked:** Last 100 log lines
- **Threshold:** 10 errors
- **Alert if:** High error count in recent logs
- **What it means:** Processing issues or schema mismatches

### 6. System Resources 💻
- **CPU usage** - Processor load
- **Memory usage** - Memory consumption
- **Disk space** - Available storage

---

## 🎯 Success Criteria for Overnight Run

By tomorrow morning (Oct 31), we expect:

### Healthy System ✅
- [ ] Both processes still running (PID 81929 and 596)
- [ ] Data lag stays < 10 minutes
- [ ] No critical alerts in `iris_overnight_alerts.log`
- [ ] Record counts growing steadily

### Expected Metrics
| Metric | Current | Tomorrow Expected |
|--------|---------|-------------------|
| BOD records | 82,050 | ~90,000 - 100,000 |
| BOALF records | 9,752 | ~12,000 - 15,000 |
| MELS records | 6,075 | ~8,000 - 10,000 |
| FREQ records | 2,656 | ~10,000 - 15,000 |
| File backlog | 26,301 | 25,000 - 40,000 |
| Data lag | < 1 min | < 10 min |

### Potential Issues ⚠️
- **File backlog grows to 50K+** - Normal for minor datasets without tables
- **MILS still 0 records** - Known issue (schema mismatch)
- **Occasional errors** - Expected for datasets without tables

---

## 📋 Morning Review Checklist

Run these commands tomorrow morning (Oct 31):

### 1. Check Monitoring Log
```bash
# View overnight summary (last 200 lines)
tail -200 iris_overnight_monitor.log

# Count total checks performed
grep "Check #" iris_overnight_monitor.log | wc -l
```

**Expected:** ~144 checks (12 hours * 12 checks/hour)

### 2. Check for Alerts
```bash
# Any alerts overnight?
cat iris_overnight_alerts.log

# Count alerts
wc -l iris_overnight_alerts.log
```

**Expected:** 0-5 alerts (hopefully 0!)

### 3. Verify Processes Still Running
```bash
ps aux | grep -E "81929|596"
```

**Expected:** Both processes still running

### 4. Check Final Data Counts
```bash
bq query --use_legacy_sql=false \
'SELECT 
    "BOD" as dataset, COUNT(*) as records FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_bod_iris`
 UNION ALL SELECT "BOALF", COUNT(*) FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_boalf_iris`
 UNION ALL SELECT "MELS", COUNT(*) FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_mels_iris`
 UNION ALL SELECT "FREQ", COUNT(*) FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_freq_iris`
 ORDER BY records DESC'
```

**Expected:** All counts significantly higher than current

### 5. Check Data Freshness
```bash
bq query --use_legacy_sql=false \
'SELECT 
    MAX(ingested_utc) as latest_ingestion,
    TIMESTAMP_DIFF(CURRENT_TIMESTAMP(), MAX(ingested_utc), MINUTE) as lag_minutes
 FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_boalf_iris`'
```

**Expected:** lag_minutes < 10

### 6. Review Processor Logs
```bash
# Check for patterns of errors
tail -200 iris_processor.log | grep -i "error\|exception" | head -20

# Check last successful inserts
tail -50 iris_processor.log | grep "✅ Inserted"
```

**Expected:** Recent successful inserts, minimal errors

### 7. File Backlog Status
```bash
find iris-clients/python/iris_data -name "*.json" | wc -l
```

**Expected:** 25,000 - 40,000 files (acceptable range)

---

## 🚨 Alert Response Guide

If you see alerts in the morning, here's what to do:

### ❌ "IRIS Client stopped"
```bash
# Check why it stopped
tail -100 iris-clients/python/iris_client.log

# Restart if needed
cd iris-clients/python
nohup ../../.venv/bin/python client.py > iris_client.log 2>&1 &
echo $! > ../../iris_client.pid
cd ../..
```

### ❌ "IRIS Processor stopped"
```bash
# Check why it stopped
tail -100 iris_processor.log

# Restart if needed
nohup ./.venv/bin/python iris_to_bigquery_unified.py > iris_processor.log 2>&1 &
echo $! > iris_processor.pid
```

### ⚠️ "Data lag exceeds 10 minutes"
```bash
# Check if processor is working
tail -50 iris_processor.log

# Check if BigQuery is accessible
bq query --use_legacy_sql=false 'SELECT COUNT(*) FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_boalf_iris`'

# Check file backlog
find iris-clients/python/iris_data -name "*.json" | wc -l
```

**Possible causes:**
- Processor crashed (restart it)
- BigQuery API issues (wait and retry)
- Schema mismatch preventing inserts (check logs)

### ⚠️ "File backlog exceeds 50,000"
```bash
# Check which datasets are accumulating
for dir in iris-clients/python/iris_data/*; do 
    echo "$(basename $dir): $(find $dir -name '*.json' 2>/dev/null | wc -l | tr -d ' ') files"
done | sort -t: -k2 -rn | head -10
```

**Possible actions:**
- Create tables for high-volume datasets
- Delete files for unwanted minor datasets
- Increase processing rate (reduce batch interval)

### ⚠️ "High error count in recent logs"
```bash
# See what errors are occurring
tail -200 iris_processor.log | grep -i "error" | sort | uniq -c | sort -rn
```

**Common errors:**
- "no such field" - Schema mismatch (expected for datasets without tables)
- "404 Not Found" - Table doesn't exist (create it)
- "Invalid datetime" - Should be fixed, but check if new format appeared

---

## 📊 Interpreting Results

### Scenario 1: Perfect Run ✅
```
Processes: ✅ Both running
Data lag: < 5 minutes
Alerts: 0
Record growth: Steady increase
Errors: < 5 per check
```
**Action:** System is healthy! Create unified views and update dashboard.

### Scenario 2: Minor Issues ⚠️
```
Processes: ✅ Both running
Data lag: 5-10 minutes
Alerts: 1-5 (file backlog warnings)
Record growth: Steady increase
Errors: 5-15 per check (schema mismatches)
```
**Action:** System working but needs attention. Review errors, consider creating more tables.

### Scenario 3: Process Crashed ❌
```
Processes: ❌ One or both stopped
Data lag: > 30 minutes
Alerts: Multiple critical alerts
Record growth: Stopped
```
**Action:** Restart crashed process(es), investigate cause in logs.

### Scenario 4: Data Stalled ⚠️
```
Processes: ✅ Both running
Data lag: > 20 minutes
Alerts: Data lag warnings
Record growth: Stalled
Errors: High (20+)
```
**Action:** Schema issues or BigQuery problems. Check processor logs, verify table schemas.

---

## 📈 Expected Overnight Behavior

### Normal Patterns ✅
- **File backlog fluctuates** - New files arrive in bursts
- **Some errors** - Datasets without tables will error
- **CPU spikes** - During batch uploads (500 rows)
- **Memory stable** - Should stay < 5%
- **Record growth steady** - New records every 5-15 minutes

### Concerning Patterns ❌
- **No record growth for > 30 min** - Processing stopped
- **File backlog growing rapidly** - Processing too slow
- **Constant errors on same dataset** - Schema problem
- **Memory increasing continuously** - Memory leak

---

## 🔍 Monitoring the Monitor

The monitoring script itself runs continuously. To check it:

```bash
# Is monitoring script running?
ps aux | grep iris_overnight_monitor

# View live output (if running in background)
tail -f iris_overnight_monitor.log

# How many checks completed?
grep "Check #" iris_overnight_monitor.log | tail -1
```

---

## 📊 Data Collection for Analysis

The monitoring script creates two files:

### 1. `iris_overnight_monitor.log`
- Complete monitoring history
- All checks with timestamps
- System metrics
- Use for: Understanding system behavior over time

### 2. `iris_overnight_alerts.log`
- Only critical alerts
- Process stops
- Threshold violations
- Use for: Quick morning review

---

## ⏰ Timeline

| Time | Check # | What to Expect |
|------|---------|----------------|
| 21:00 | #1 | Monitoring starts |
| 22:00 | #12 | First hour complete |
| 00:00 | #36 | Three hours in |
| 03:00 | #72 | Halfway through night |
| 06:00 | #108 | Morning approaching |
| 09:00 | #144 | 12 hours complete |

---

## 🎯 Tomorrow Morning Action Items

Based on overnight results:

### If Healthy ✅
1. ✅ Create unified views for BOD, MELS, FREQ
2. ✅ Update dashboard to use `*_unified` views
3. ✅ Document successful 12-hour run
4. ✅ Plan for 7-day monitoring

### If Minor Issues ⚠️
1. ⚠️ Fix identified schema problems
2. ⚠️ Create tables for high-volume datasets
3. ⚠️ Tune monitoring thresholds
4. ⚠️ Continue monitoring for another 24 hours

### If Major Issues ❌
1. ❌ Investigate root cause in logs
2. ❌ Fix and restart services
3. ❌ Run short test (2 hours) to verify fix
4. ❌ Resume overnight monitoring

---

## 📞 Quick Commands Reference

```bash
# Start monitoring (background)
nohup ./iris_overnight_monitor.sh &

# Check monitoring log
tail -50 iris_overnight_monitor.log

# Check alerts
cat iris_overnight_alerts.log

# Quick health check
./check_iris_health.sh

# Stop monitoring
kill $(ps aux | grep iris_overnight_monitor | grep -v grep | awk '{print $2}')

# View live monitoring
./iris_overnight_monitor.sh

# Check processes
ps aux | grep -E "81929|596"

# Check BigQuery data
bq query --use_legacy_sql=false \
'SELECT COUNT(*) FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_boalf_iris`'
```

---

## 🎓 What We're Learning

This overnight run will tell us:

1. **Stability** - Do services stay running for 12+ hours?
2. **Performance** - Is batch processing keeping up with message rate?
3. **Data Quality** - Are records consistently arriving in BigQuery?
4. **Resource Usage** - CPU, memory, disk patterns over time
5. **Error Patterns** - What issues occur and how frequently?
6. **Backlog Behavior** - Does file backlog stabilize or grow continuously?

---

## 📊 Success Metrics

By tomorrow morning, success means:

✅ **Primary Goals**
- Both processes ran continuously (no crashes)
- 80,000+ new records ingested across 4 datasets
- Data lag stayed under 10 minutes
- No critical alerts

✅ **Secondary Goals**
- Fewer than 10 alerts total
- File backlog stayed under 50,000
- Error rate stayed under 15 per check
- CPU and memory stable

✅ **Stretch Goals**
- Zero alerts
- Data lag stayed under 5 minutes
- All 4 core datasets showing steady growth
- Ready to deploy unified views

---

**Monitoring Guide Complete!**

*Review this guide tomorrow morning (Oct 31) to interpret results and plan next steps.*

Good night! 🌙

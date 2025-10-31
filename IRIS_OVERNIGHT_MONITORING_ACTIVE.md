# IRIS Overnight Monitoring - Active Session

**Status:** 🟢 **MONITORING ACTIVE**  
**Started:** October 30, 2025 at 18:21 GMT  
**Expected End:** October 31, 2025 at 09:00 GMT (~12 hours)  
**Check Interval:** Every 5 minutes (300 seconds)

---

## ✅ Monitoring Started Successfully

### Current System Status
- ✅ **IRIS Client** (PID: 81929) - Running
- ✅ **IRIS Processor** (PID: 596) - Running  
- ✅ **Monitoring Script** (PID: 6334) - Running
- ⏱️ **Data Lag:** 2 minutes (Excellent!)
- 📁 **File Backlog:** 47,689 files (increased from 26K - file accumulation continuing)
- 💻 **CPU Usage:** 3.2% (Normal)
- 💻 **Memory Usage:** 1.0% (Normal)
- 💾 **Disk Usage:** 85%

### ⚠️ Expected Warning
**High Error Count (100 errors in last 100 log lines)**

This is **EXPECTED and NORMAL** because:
- We have 60+ dataset types coming in from IRIS
- We only created tables for 9 datasets (BOALF, BOD, MILS, MELS, FREQ, FUELINST, REMIT, MID, BEB)
- Files for datasets without tables will error with "404 Not Found" or "no such field"
- This does NOT affect the 4 working datasets (BOD, BOALF, MELS, FREQ)

**Action:** None required - this is normal behavior

---

## 📊 What's Happening Overnight

### Every 5 Minutes (144 checks total)
The monitoring script checks:
1. ✅ Both processes still running
2. 📁 File backlog count
3. ⏱️ Data freshness (lag time)
4. 🐛 Recent error count
5. 💻 CPU and memory usage
6. 💾 Disk space

### Every 15 Minutes (48 checks)
Also includes:
- 📈 Record counts for all 4 working datasets

---

## 📝 Monitoring Files

### Log Files Created
1. **`iris_overnight_monitor.log`** - Complete monitoring history
   - All checks with timestamps
   - Process status
   - Metrics and warnings
   - **Location:** Same directory as script

2. **`iris_overnight_alerts.log`** - Critical alerts only
   - Process crashes
   - Threshold violations
   - Empty if no critical issues
   - **Location:** Same directory as script

---

## 🔍 How to Check Status During Night

### Quick Check (recommended)
```bash
# See last 50 lines of monitoring log
tail -50 iris_overnight_monitor.log

# Check for any critical alerts
cat iris_overnight_alerts.log
```

### Detailed Check
```bash
# See recent checks
tail -100 iris_overnight_monitor.log

# Count how many checks completed
grep "Check #" iris_overnight_monitor.log | wc -l

# See only warnings/errors
grep "⚠️\|❌" iris_overnight_monitor.log
```

### Live Monitoring
```bash
# Watch monitoring in real-time
tail -f iris_overnight_monitor.log
```

---

## 🌅 Tomorrow Morning (Oct 31)

### Run These Commands

1. **Check if monitoring completed successfully**
```bash
# How many checks ran? (Expect ~144)
grep "Check #" iris_overnight_monitor.log | tail -1
```

2. **Check for critical alerts**
```bash
# Should be empty or very few lines
cat iris_overnight_alerts.log
```

3. **View final status**
```bash
# See last check results
tail -50 iris_overnight_monitor.log
```

4. **Verify processes still running**
```bash
ps aux | grep -E "81929|596"
```

5. **Check data growth**
```bash
bq query --use_legacy_sql=false \
'SELECT 
    "BOD" as dataset, COUNT(*) as records FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_bod_iris`
 UNION ALL SELECT "BOALF", COUNT(*) FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_boalf_iris`
 UNION ALL SELECT "MELS", COUNT(*) FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_mels_iris`
 UNION ALL SELECT "FREQ", COUNT(*) FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_freq_iris`
 ORDER BY records DESC'
```

**Expected Results:**
- BOD: ~90,000 - 100,000 (currently 82,050)
- BOALF: ~12,000 - 15,000 (currently 9,752)
- MELS: ~8,000 - 10,000 (currently 6,075)
- FREQ: ~10,000 - 15,000 (currently 2,656)

---

## 🎯 Success Criteria for Tomorrow

### ✅ PASS (System Healthy)
- Both processes still running (PID 81929 and 596)
- Data lag < 10 minutes
- Record counts increased significantly
- Zero or few critical alerts
- **Action:** System validated! Proceed with unified views and dashboard updates

### ⚠️ MINOR ISSUES (System Working with Warnings)
- Both processes running
- Data lag 5-10 minutes
- Some alerts (file backlog warnings)
- Record counts growing
- **Action:** Review alerts, minor tuning needed, system operational

### ❌ FAIL (System Issues)
- One or both processes stopped
- Data lag > 20 minutes
- Multiple critical alerts
- Record counts not growing
- **Action:** Investigate logs, restart processes, identify root cause

---

## 🛑 How to Stop Monitoring

If you need to stop monitoring early:

```bash
# Find monitoring process
ps aux | grep iris_overnight_monitor | grep -v grep

# Stop it (use PID from above)
kill 6334

# Or stop all instances
pkill -f iris_overnight_monitor.sh
```

---

## 📈 Expected Overnight Behavior

### Normal ✅
- File backlog fluctuates (25K - 50K range)
- High error count (~100 errors per check) due to datasets without tables
- CPU spikes during batch uploads
- Memory stays stable
- Record counts grow steadily

### Concerning ❌
- File backlog exceeds 50,000
- Data lag exceeds 10 minutes
- Processes crash
- No record growth for > 30 minutes
- Memory continuously increasing

---

## 📞 Quick Reference

### Files
- **Monitoring script:** `iris_overnight_monitor.sh`
- **Monitoring log:** `iris_overnight_monitor.log`
- **Alerts log:** `iris_overnight_alerts.log`
- **Guide:** `IRIS_OVERNIGHT_MONITORING_GUIDE.md`

### PIDs
- **IRIS Client:** 81929
- **IRIS Processor:** 596
- **Monitoring Script:** 6334

### Commands
```bash
# Check monitoring status
tail -50 iris_overnight_monitor.log

# Check alerts
cat iris_overnight_alerts.log

# Quick health
./check_iris_health.sh

# Stop monitoring
kill 6334
```

---

## 📊 Current Baseline (18:21 GMT)

| Metric | Value |
|--------|-------|
| BOD records | 82,050 |
| BOALF records | 9,752 |
| MELS records | 6,075 |
| FREQ records | 2,656 |
| File backlog | 47,689 files |
| Data lag | 2 minutes |
| CPU usage | 3.2% |
| Memory usage | 1.0% |
| Disk usage | 85% |

---

## 🎓 What We're Testing

This overnight run validates:

1. **Long-term Stability** - Do services run continuously without crashes?
2. **Performance Sustainability** - Does batch processing keep up over time?
3. **Data Quality** - Are records consistently reaching BigQuery?
4. **Resource Efficiency** - CPU, memory, disk usage patterns
5. **Error Handling** - System continues despite errors for missing tables
6. **Backlog Management** - Does file accumulation stabilize or grow unbounded?

---

## ✅ Next Steps After Successful Overnight Run

If monitoring shows healthy system tomorrow:

1. **Create Unified Views** (1 hour)
   - `bmrs_bod_unified`
   - `bmrs_mels_unified`
   - `bmrs_freq_unified`

2. **Update Dashboard** (2 hours)
   - Switch from `bmrs_*` to `bmrs_*_unified` tables
   - Add real-time indicators
   - Add data source column

3. **Fix Known Issues** (1 hour)
   - MILS schema (0 records)
   - BEB schema mismatch
   - Consider creating tables for high-volume minor datasets

4. **Document Success** (30 min)
   - Write overnight success report
   - Update system status
   - Plan for 7-day monitoring

---

## 🌙 Good Night!

**Monitoring is active and running smoothly.**

The system will check itself every 5 minutes throughout the night. Tomorrow morning, review the logs to see how the system performed.

**Sleep well - the system is being watched! 🛡️**

---

**Last Updated:** October 30, 2025 at 18:21 GMT  
**Next Review:** October 31, 2025 at 09:00 GMT

# IRIS Pipeline Diagnosis - Dec 20, 2025 00:36

## 🚨 CRITICAL FINDINGS

### Issue 1: UPLOADER NOT RUNNING ❌
**Status:** IRIS uploader process CRASHED or STOPPED
**Evidence:**
- `ps aux | grep iris_to_bigquery` → No process found
- Last log entry: 00:20:54 "No files to process"
- 336 new files downloaded in last 10 minutes (BOALF, MELS, MILS)
- Files accumulating, NOT being uploaded to BigQuery

**Impact:**
- Zero BigQuery uploads since 00:20
- Data pipeline BROKEN (client working, uploader dead)
- Files will accumulate indefinitely

**Root Cause:**
- Process likely crashed silently after 00:20
- No auto-restart configured (systemd not active)
- No monitoring to detect crash

**Fix Required:**
```bash
cd /opt/iris-pipeline/scripts
export GOOGLE_APPLICATION_CREDENTIALS=/opt/iris-pipeline/secrets/sa.json
nohup python3 iris_to_bigquery_unified.py >> /opt/iris-pipeline/logs/iris_uploader.log 2>&1 &
```

---

### Issue 2: SYSTEMD SERVICES NOT ENABLED ❌
**Status:** Service files created but NOT functional
**Evidence:**
- Files exist: `/etc/systemd/system/iris-client.service`, `iris-uploader.service`
- `systemctl list-unit-files | grep iris` → Shows "bad" or "disabled"
- `systemctl enable` commands failing
- Permissions: root:root, 644 ✅

**Impact:**
- No auto-restart on crash (why uploader stayed dead)
- No auto-start on boot
- Manual intervention required for every crash

**Root Cause:**
- Systemd validation likely failing
- Service file syntax issue OR
- Path issue OR
- Systemd cache not refreshed

**Fix Required:**
```bash
# Check for syntax errors
sudo systemd-analyze verify /etc/systemd/system/iris-client.service
sudo systemd-analyze verify /etc/systemd/system/iris-uploader.service

# Force reload and enable
sudo systemctl daemon-reload
sudo systemctl enable iris-client.service --force
sudo systemctl enable iris-uploader.service --force

# Start services (will kill manual processes)
sudo systemctl start iris-client iris-uploader
```

---

### Issue 3: NO BIGQUERY UPLOADS TODAY ❌
**Status:** Zero records uploaded on Dec 20
**Evidence:**
```sql
SELECT MAX(ingested_utc), COUNT(*)
FROM bmrs_fuelinst_iris
WHERE DATE(ingested_utc) = CURRENT_DATE()
-- Result: NaT (null), 0 records
```

**Impact:**
- Dashboard still showing Dec 13 data (historical)
- Real-time pipeline completely broken
- IRIS tables empty for today

**Root Cause:**
- Uploader crashed at 00:20, never restarted
- Files downloaded but never uploaded
- No monitoring detected the failure

---

### Issue 4: SCHEMA MISMATCHES (NOT YET FIXED) ⚠️
**Status:** Query column names incompatible with IRIS tables
**File:** `update_live_dashboard_v2.py`
**Problem:**
```python
# Line ~95-110: WRONG column names
SELECT settlementPeriod FROM bmrs_boalf_iris
WHERE CAST(settlementDate AS DATE) = '{date}'  # ❌

# Should be:
SELECT settlementPeriodFrom FROM bmrs_boalf_iris
WHERE DATE(timeFrom) = '{date}'  # ✅
```

**Impact:**
- Even when IRIS data exists, queries fail
- Falls back to historical tables only
- Dashboard can't access Dec 18 data

---

## ✅ WHAT'S WORKING

1. **IRIS Client:** ✅ Running (PID 4081716)
   - Connected to Azure Service Bus
   - Downloading messages every 2-5 minutes
   - Files: BOALF (336 in 10min), MELS, MILS arriving
   - Writing to: `/opt/iris-pipeline/data/`

2. **Cron Credentials:** ✅ Configured
   - `GOOGLE_APPLICATION_CREDENTIALS` added to crontab
   - Will test at next :15 mark (e.g., 00:45)
   - Should fix `auto_ingest_realtime.py` crashes

3. **Updated Scripts:** ✅ Deployed
   - `iris_to_bigquery_unified.py` has full TABLE_MAPPING
   - Added INDGEN, INDO, MELS, MILS
   - Backup saved

4. **Data Arriving:** ✅ National Grid Publishing
   - BOALF messages flowing (market activity)
   - MELS/MILS system messages
   - Client successfully downloading

---

## 📊 CURRENT DATA STATUS

### Files Downloaded (Last 10 Minutes)
- **Total:** 336 JSON files
- **BOALF:** ~100 files (balancing acceptances)
- **MELS:** ~150 files (market system messages)
- **MILS:** ~50 files (market information)
- **INDGEN:** Some files
- **Time Range:** 00:25-00:36

### BigQuery Uploads
- **Last Upload:** Dec 18, 14:39 (2 days ago)
- **Today (Dec 20):** ZERO uploads ❌
- **Reason:** Uploader not running

### Files Accumulating
- **Rate:** ~33 files/minute
- **Storage:** Growing continuously
- **Impact:** Will fill disk if not processed

---

## 🔧 IMMEDIATE ACTION PLAN

### Priority 1: RESTART UPLOADER (NOW!)
```bash
# Check current status
ps aux | grep iris_to_bigquery

# If not running, restart:
cd /opt/iris-pipeline/scripts
export GOOGLE_APPLICATION_CREDENTIALS=/opt/iris-pipeline/secrets/sa.json
nohup python3 iris_to_bigquery_unified.py >> /opt/iris-pipeline/logs/iris_uploader.log 2>&1 &

# Verify running
ps aux | grep iris_to_bigquery
tail -f /opt/iris-pipeline/logs/iris_uploader.log  # Should see "Uploaded X rows"
```

### Priority 2: FIX SYSTEMD (NEXT 15 MIN)
```bash
# Validate service files
sudo systemd-analyze verify /etc/systemd/system/iris-client.service
sudo systemd-analyze verify /etc/systemd/system/iris-uploader.service

# If errors, fix syntax and reload
sudo systemctl daemon-reload

# Try alternative enable method
sudo ln -sf /etc/systemd/system/iris-client.service /etc/systemd/system/multi-user.target.wants/
sudo ln -sf /etc/systemd/system/iris-uploader.service /etc/systemd/system/multi-user.target.wants/

# Verify
systemctl list-unit-files | grep iris  # Should show "enabled"
```

### Priority 3: VERIFY UPLOADS (5 MIN AFTER RESTART)
```sql
-- Check if new data arriving
SELECT
    MAX(ingested_utc) as latest,
    COUNT(*) as new_records
FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_boalf_iris`
WHERE ingested_utc >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 30 MINUTE);

-- Should show timestamps after 00:36 and growing record count
```

### Priority 4: FIX QUERY SCHEMAS (TODAY)
Edit `update_live_dashboard_v2.py`:
- Line ~95-110: Change `settlementDate` → `timeFrom` for BOALF
- Line ~120-130: Verify MID uses correct columns
- Test with: `python3 update_live_dashboard_v2.py`

---

## 📋 COMPLETE STATUS CHECKLIST

| Component | Status | Details |
|-----------|--------|---------|
| **IRIS Client** | ✅ Working | PID 4081716, downloading 33 files/min |
| **IRIS Uploader** | ❌ CRASHED | Last seen 00:20, process missing |
| **Systemd Services** | ❌ Not Enabled | Files exist but "bad" status |
| **Auto-Restart** | ❌ Missing | Crashes require manual restart |
| **Auto-Start on Boot** | ❌ Missing | Won't start after reboot |
| **Cron Credentials** | ✅ Fixed | Added to crontab, testing at :15 |
| **BigQuery Uploads** | ❌ Broken | Zero uploads today |
| **Query Schemas** | ❌ Wrong | BOALF uses settlementDate (should be timeFrom) |
| **Data Arriving** | ✅ Yes | 336 files in 10 min |
| **Files Accumulating** | ⚠️ Yes | 336+ pending upload |
| **Monitoring** | ❌ None | No alerts for crashes |

---

## ⚠️ RISKS & CONSEQUENCES

### If Uploader Stays Down
- **Disk Space:** Files accumulate ~33/min = 2,000/hour = 48,000/day
- **Data Loss:** If disk fills, client will crash too
- **Dashboard:** Will continue showing stale Dec 13 data
- **Analysis:** No real-time battery arbitrage data

### If Systemd Not Fixed
- **Next Crash:** Requires manual intervention (could be days)
- **On Reboot:** IRIS won't start, pipeline dead until manual restart
- **Overnight:** If crashes at 2am, stays down until morning
- **Weekends:** Could be down for entire weekend

### If Schemas Not Fixed
- **Dashboard:** Can't access IRIS data even when it exists
- **Queries:** Will fail or return incomplete results
- **Analysis:** Missing 2-5 minute resolution data

---

## 💡 ROOT CAUSE ANALYSIS

### Why Uploader Crashed at 00:20
**Unknown** - Need to check logs for:
- Python exception (schema error, API error)
- Memory issue (OOM killer)
- Permissions issue (can't write to BigQuery)
- Credentials expiry

**How to Check:**
```bash
# Look for crash evidence
journalctl -n 100 | grep -E "python3|Out of memory|Killed"
dmesg | tail -50 | grep -i "kill"
tail -100 /opt/iris-pipeline/logs/iris_uploader.log | grep -E "ERROR|Exception|Traceback"
```

### Why Systemd Enable Failing
**Likely Causes:**
1. Service file syntax error (systemd-analyze will show)
2. ExecStart path wrong (Python not at /usr/bin/python3)
3. WorkingDirectory doesn't exist
4. Systemd cache issue (daemon-reload not working)

**How to Fix:**
- Validate syntax: `systemd-analyze verify`
- Check paths: `which python3` (should match ExecStart)
- Manual symlink: `ln -s` to `multi-user.target.wants/`

---

## 📞 ANSWER TO USER'S QUESTIONS

### Q: Will it always run on this machine?
**A: ❌ NOT YET**
- Manual processes running NOW (client only, uploader crashed)
- Systemd services created but NOT enabled/working
- Won't survive crash (proven - uploader already crashed once tonight)
- Won't survive reboot
- **Need to:** Fix systemd and verify auto-restart

### Q: Will data update every 15 minutes or sooner?
**A: ❌ NOT CURRENTLY**
- IRIS client: ✅ Downloading every 2-5 min
- IRIS uploader: ❌ CRASHED (zero uploads)
- API polling: ⏳ Testing at next :15 mark
- **When working:** Yes, <5 min updates
- **Right now:** No updates at all

### Q: Why did this stop?
**A: ✅ DIAGNOSED - And it STOPPED AGAIN tonight!**

**Original Stoppage (Dec 14-18):**
1. Uploader crashed on REMIT schema errors
2. Client ran from wrong directory
3. No auto-restart
4. No monitoring
5. Cron credentials missing

**Tonight's Stoppage (Dec 20 00:20):**
1. Uploader crashed again (~15 min after restart)
2. No auto-restart (systemd not working)
3. No monitoring to detect
4. **Proves:** Without systemd, crashes will keep causing outages

**Pattern:** Temporary manual restarts are NOT reliable. Every crash = new outage.

---

## 🎯 SUCCESS CRITERIA

### Minimal Viable Fix (Next 30 Minutes)
- [ ] Uploader restarted and processing files
- [ ] BigQuery showing new uploads (ingested_utc > 00:36)
- [ ] Files being deleted after upload (queue decreasing)

### Full Production Fix (Today)
- [ ] Systemd services enabled and running
- [ ] Auto-restart tested (kill process, verify restart)
- [ ] Cron API polling verified (check at :15 mark)
- [ ] Query schemas fixed (BOALF timeFrom)

### Long-Term Reliability (This Week)
- [ ] Monitoring/alerting for data freshness
- [ ] Log rotation configured
- [ ] Unmapped files cleanup strategy
- [ ] Weekly health check scheduled

---

## 📝 COMMANDS TO RUN NOW

```bash
# 1. Restart uploader
cd /opt/iris-pipeline/scripts
export GOOGLE_APPLICATION_CREDENTIALS=/opt/iris-pipeline/secrets/sa.json
nohup python3 iris_to_bigquery_unified.py >> /opt/iris-pipeline/logs/iris_uploader.log 2>&1 &
echo "Uploader PID: $!"

# 2. Verify it's working
sleep 10
tail -50 /opt/iris-pipeline/logs/iris_uploader.log | grep "Uploaded"

# 3. Check file queue
find /opt/iris-pipeline/data -name "*.json" | wc -l
# Should start decreasing

# 4. Fix systemd
sudo systemd-analyze verify /etc/systemd/system/iris-client.service
sudo systemd-analyze verify /etc/systemd/system/iris-uploader.service
# Fix any errors shown

sudo systemctl daemon-reload
sudo systemctl enable iris-client iris-uploader --force
systemctl list-unit-files | grep iris
# Should show "enabled"

# 5. Monitor uploads (wait 2-3 minutes)
python3 -c "from google.cloud import bigquery; import os; os.environ['GOOGLE_APPLICATION_CREDENTIALS']='/home/george/GB-Power-Market-JJ/inner-cinema-credentials.json'; client = bigquery.Client(project='inner-cinema-476211-u9'); print(client.query('SELECT MAX(ingested_utc) FROM uk_energy_prod.bmrs_boalf_iris').to_dataframe())"
# Should show timestamp after 00:36
```

---

**Status:** 🔴 **CRITICAL - UPLOADER DOWN, DATA PIPELINE BROKEN**
**Next Action:** Restart uploader IMMEDIATELY
**ETA to Fix:** 5 minutes (restart) + 30 minutes (systemd)
**Risk Level:** HIGH (files accumulating, no uploads happening)

---

*Generated: Dec 20, 2025 00:36*
*Last Update: Uploader crashed at 00:20, 336 files pending*

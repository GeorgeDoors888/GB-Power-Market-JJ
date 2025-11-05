# ✅ IRIS UPLOADER - FIXED AND RUNNING!

**Date:** November 4, 2025 - 22:32 UTC

## 🎉 SUCCESS - Pipeline is Now Working!

### Root Cause Identified
The uploader was using the **WRONG service account**:
- ❌ Was using: `/root/service_account.json` → `jibber-jabber-knowledge@appspot.gserviceaccount.com` (no permissions)
- ✅ Now using: `/root/service_account.json` → `/opt/iris-pipeline/service_account.json` → `all-jibber@inner-cinema-476211-u9.iam.gserviceaccount.com` (full permissions)

### Fixes Applied

1. **IAM Permissions Granted** (via gcloud CLI):
   ```bash
   gcloud projects add-iam-policy-binding inner-cinema-476211-u9 \
       --member="serviceAccount:all-jibber@inner-cinema-476211-u9.iam.gserviceaccount.com" \
       --role="roles/bigquery.dataEditor"
   ```

2. **Credentials File Fixed**:
   ```bash
   rm -f /root/service_account.json
   ln -s /opt/iris-pipeline/service_account.json /root/service_account.json
   ```

3. **Uploader Restarted** with correct credentials

### Current Status

**Process:** ✅ Running (PID 3438)
**Uploads:** ✅ Working perfectly
**Recent Activity:**
- 22:31:59 - Inserted 500 rows into bmrs_mels_iris
- 22:31:53 - Inserted 5,106 rows into bmrs_mels_iris  
- 22:31:47 - Inserted 2,865 rows into bmrs_mels_iris
- 22:31:41 - Inserted 5,107 rows into bmrs_mels_iris
- 22:31:34 - Inserted 2,803 rows into bmrs_mels_iris

**Upload Rate:** ~2,000-5,000 rows per batch, every 5-30 seconds

### Files Remaining to Process

Estimated counts (as of 22:20):
- **MELS:** ~205,000 files  
- **MILS:** ~93,500 files
- **INDO:** ~352 files (🎯 **TARGET - will be ready soon!**)
- **INDDEM:** ~244 files
- **INDGEN:** ~244 files

### Performance

**Current Configuration:**
- MAX_FILES_PER_SCAN: 500
- BATCH_SIZE: 2,000 rows
- CYCLE_INTERVAL: 30 seconds
- Memory usage: ~130 MB (safe)

**Processing Speed:**
- ~500 files per cycle
- ~2,000-5,000 rows per cycle
- ~1,000-2,800 msg/s throughput

### Timeline Estimate

At current rate (~500 files per cycle, 30s between cycles):
- **INDO:** ~1 minute (352 files ÷ 500/cycle = 1 cycle)
- **MELS:** ~3.4 hours (205K files ÷ 500/cycle × 30s)
- **MILS:** ~1.5 hours (93.5K files ÷ 500/cycle × 30s)

**Total:** ~5 hours for all files

## 📊 How to Monitor

### Check Process Status
```bash
ssh root@94.237.55.234 'ps aux | grep "python3 iris_to_bigquery_unified.py" | grep -v grep'
```

### View Recent Uploads
```bash
ssh root@94.237.55.234 'grep "✅ Inserted" /opt/iris-pipeline/logs/iris_uploader.log | tail -10'
```

### Count Remaining Files
```bash
ssh root@94.237.55.234 'cd /opt/iris-pipeline && find iris-clients/python/iris_data/INDO -name "*.json" | wc -l'
```

### Check BigQuery Table
```bash
bq query --use_legacy_sql=false "
SELECT COUNT(*) as rows, MAX(DATE(settlementDate)) as latest_date  
FROM \`inner-cinema-476211-u9.uk_energy_prod.bmrs_indo_iris\`
"
```

## 🔧 Restart Commands

If needed, restart the uploader:
```bash
ssh root@94.237.55.234 '/opt/iris-pipeline/restart_uploader.sh'
```

## ✅ Next Steps

1. **Wait for INDO data** (~1 minute from now)
2. **Verify INDO table** exists in BigQuery
3. **Update dashboard** to show INDO data
4. **MELS/MILS** will follow over next 5 hours

---

## Technical Details

**Service Account:** all-jibber@inner-cinema-476211-u9.iam.gserviceaccount.com
**IAM Roles:** 
- roles/bigquery.admin
- roles/bigquery.dataEditor
- roles/aiplatform.admin

**BigQuery Project:** inner-cinema-476211-u9
**Dataset:** uk_energy_prod
**Tables:** bmrs_*_iris (MELS, MILS, INDO, INDDEM, INDGEN, etc.)

**Server:** 94.237.55.234 (UpCloud VPS)
**Path:** /opt/iris-pipeline
**Log:** /opt/iris-pipeline/logs/iris_uploader.log

---

**Status:** 🟢 OPERATIONAL
**Last Updated:** 2025-11-04 22:32 UTC

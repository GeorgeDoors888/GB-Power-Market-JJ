# CRITICAL: Service Account Missing BigQuery Permissions

**Time:** 20:50 UTC, 4 Nov 2025  
**Status:** ❌ BLOCKED - Service Account Lacks BigQuery Write Permission

---

## 🔴 The Real Problem Discovered

After hours of troubleshooting, the **root cause** is finally clear:

###Service Account: `all-jibber@inner-cinema-476211-u9.iam.gserviceaccount.com`

**Missing Permissions:**
- ❌ `bigquery.tables.get` - Can't check if tables exist
- ❌ `bigquery.tables.updateData` - **Can't insert rows into BigQuery!**

This is why:
- ✅ 179,602 rows were inserted earlier (probably using different credentials)
- ❌ **Nothing has uploaded since 19:00 UTC** (service account changed or permissions revoked)
- ❌ All the troubleshooting (memory fixes, skipping datasets) couldn't fix this

---

## 📊 What Happened Timeline

```
18:28 UTC - Started with memory optimization
18:28-19:00 - Some data uploaded (179,602 rows into MELS)
19:00 UTC - STOPPED - Permission errors began
19:00-20:50 - Troubleshooting:
  ✅ Applied memory fix (500 files)
  ✅ Skipped BOD (permission errors)
  ✅ Skipped other datasets
  ✅ Fixed table check function
  ❌ Still blocked - service account has no write permission!
```

---

## ✅ THE FIX: Grant BigQuery Permissions

### Option 1: Via Google Cloud Console (RECOMMENDED)

1. Go to: https://console.cloud.google.com/iam-admin/iam?project=inner-cinema-476211-u9

2. Find service account:
   ```
   all-jibber@inner-cinema-476211-u9.iam.gserviceaccount.com
   ```

3. Click "Edit" (pencil icon)

4. Add role: **BigQuery Data Editor**
   - Or add these specific permissions:
     - `bigquery.tables.get`
     - `bigquery.tables.create`
     - `bigquery.tables.updateData`
     - `bigquery.tables.getData`

5. Save

6. Wait 1-2 minutes for permissions to propagate

7. Restart uploader on server:
   ```bash
   ssh root@94.237.55.234 'killall python3; cd /opt/iris-pipeline && nohup bash -c "while true; do python3 iris_to_bigquery_unified.py >> logs/iris_uploader.log 2>&1; sleep 30; done" > /dev/null 2>&1 &'
   ```

### Option 2: Via gcloud Command

```bash
gcloud projects add-iam-policy-binding inner-cinema-476211-u9 \
  --member="serviceAccount:all-jibber@inner-cinema-476211-u9.iam.gserviceaccount.com" \
  --role="roles/bigquery.dataEditor"
```

---

## 🔍 How to Verify

### 1. Check IAM Permissions
```bash
gcloud projects get-iam-policy inner-cinema-476211-u9 \
  --flatten="bindings[].members" \
  --filter="bindings.members:all-jibber@inner-cinema-476211-u9.iam.gserviceaccount.com"
```

Should show `roles/bigquery.dataEditor` or similar.

### 2. Test Upload
After granting permissions, check log:
```bash
ssh root@94.237.55.234 'tail -f /opt/iris-pipeline/logs/iris_uploader.log'
```

Should see:
```
✅ Inserted X rows into bmrs_mels_iris
🗑️  Deleted X processed JSON files
```

### 3. Check BigQuery Progress
```bash
bq query --use_legacy_sql=false "SELECT COUNT(*) FROM \`inner-cinema-476211-u9.uk_energy_prod.bmrs_mels_iris\`"
```

Should be > 179,602

---

## 📊 Files Waiting to Upload

```
MELS:    207,189 files (~1.35M rows)
MILS:     92,176 files (~600K rows)
INDO:        349 files (~2,200 rows) ← YOUR TARGET!
INDDEM:      244 files
INDGEN:      244 files
```

**All ready to go once permissions are fixed!**

---

## ⏱️ Timeline After Fix

With 500 files/scan, 30s cycles = ~1000 files/min:

```
MELS:   207,189 ÷ 1000 = 207 minutes = 3.5 hours
MILS:    92,176 ÷ 1000 =  92 minutes = 1.5 hours
INDO:       349 ÷ 1000 =  <1 minute

Total: ~5 hours from permissions fix
```

**If fixed now (20:50), INDO ready by 01:50 UTC (1:50 AM Tuesday)**

---

## 🎯 Summary

**Problem:** Service account lacks `bigquery.tables.updateData` permission  
**Solution:** Grant "BigQuery Data Editor" role in IAM  
**Time to fix:** 2 minutes  
**Time to complete:** 5 hours after fix  

**All the infrastructure is working:**
- ✅ Memory fix applied (500 files, 2000 batch)
- ✅ Problematic datasets skipped
- ✅ Process running smoothly
- ❌ Just needs permission to write to BigQuery!

---

## 🔑 Quick Fix Command

**After granting permissions in Console:**

```bash
# Restart uploader
ssh root@94.237.55.234 '
killall python3 2>/dev/null
cd /opt/iris-pipeline
export GOOGLE_APPLICATION_CREDENTIALS=/opt/iris-pipeline/service_account.json
export BQ_PROJECT=inner-cinema-476211-u9
source .venv/bin/activate
nohup bash -c "while true; do python3 iris_to_bigquery_unified.py >> logs/iris_uploader.log 2>&1; sleep 30; done" > /dev/null 2>&1 &
echo "Uploader restarted"
'

# Monitor (should see Inserted messages)
ssh root@94.237.55.234 'tail -f /opt/iris-pipeline/logs/iris_uploader.log'
```

---

**Status:** Waiting for IAM permission grant  
**ETA after fix:** 5 hours to INDO  
**Next step:** Grant BigQuery Data Editor role to `all-jibber` service account

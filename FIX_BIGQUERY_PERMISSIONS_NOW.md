# 🔧 FIX BIGQUERY PERMISSIONS - Quick Guide

**Problem**: Service account cannot access your BigQuery project  
**Solution**: Grant it permissions (takes 2 minutes)  
**Benefit**: All Python automation scripts will work

---

## 🎯 Your Situation

You have **ONE BigQuery project**: `inner-cinema-476211-u9`

```
📊 inner-cinema-476211-u9 (Your ONLY BigQuery Project)
├─ gb_power (9 tables)
├─ uk_energy_prod (174 tables)
├─ uk_energy_prod_eu (4 tables)
└─ companies_house (13 tables)

👤 You (george@upowerenergy.uk): ✅ Full Access
🤖 Service Account: ❌ No Access (this is the problem!)
```

---

## 🚀 How to Fix It (2 Minutes)

### Step 1: Open IAM Console
Click this link (make sure you're logged in as george@upowerenergy.uk):

👉 **https://console.cloud.google.com/iam-admin/iam?project=inner-cinema-476211-u9**

### Step 2: Grant Access
1. Look for the blue **"+ GRANT ACCESS"** button at the top
2. Click it

### Step 3: Add Service Account
In the form that appears:
1. **New principals** field: Copy and paste this exactly:
   ```
   jibber-jabber-knowledge@appspot.gserviceaccount.com
   ```

### Step 4: Select Roles
Click **"Select a role"** dropdown and choose:
1. **BigQuery Data Editor**

Then click **"+ ADD ANOTHER ROLE"** and choose:
2. **BigQuery Job User**

**OR** (Simpler - Just one role):
- Choose **BigQuery Admin** (gives full BigQuery access)

### Step 5: Save
Click the blue **SAVE** button at the bottom

---

## ✅ Verify It Worked

Run this command to test:

```bash
cd "/Users/georgemajor/GB Power Market JJ"
.venv/bin/python verify_api_setup.py
```

**You should see:**
```
✅ BigQuery API - WORKING
```

Instead of:
```
❌ Error: 403 Access Denied
```

---

## 📊 What This Enables

After granting permissions, these will work:

✅ **Python scripts can write to BigQuery**
```python
# Upload DNO tariffs to BigQuery
python upload_tariffs_to_bigquery.py
```

✅ **Automated data pipelines**
```python
# Daily data updates
python automated_data_tracker.py
```

✅ **Dashboard updates to BigQuery**
```python
# Update BigQuery tables from scripts
python update_bigquery_tables.py
```

✅ **All existing BigQuery scripts**
- Any script using `jibber_jabber_key.json` will now work

---

## 🤔 Is This Safe?

**YES!** Here's why:

1. ✅ The service account is controlled by YOU (you have the key file)
2. ✅ It only gives access to BigQuery (not other Google services)
3. ✅ You can revoke it anytime in the IAM console
4. ✅ This is standard practice for automation
5. ✅ BigQuery has audit logs (you can see what it does)

---

## 🎯 Quick Summary

**What to do**: Grant `jibber-jabber-knowledge@appspot.gserviceaccount.com` access to your BigQuery project

**Where**: https://console.cloud.google.com/iam-admin/iam?project=inner-cinema-476211-u9

**Roles to grant**: 
- BigQuery Data Editor
- BigQuery Job User
(OR just "BigQuery Admin" for simplicity)

**Time needed**: 2 minutes

**Impact**: Python automation scripts will work! 🎉

---

**Need help?** See the full explanation: `BIGQUERY_PERMISSION_ISSUE_EXPLAINED.md`

# Fix BigQuery Access - Smart Grid Project Permissions

## Problem
```
❌ 403 Access Denied: Dataset inner-cinema-476211-u9:uk_energy_insights
```

The service account `jibber-jabber-knowledge@appspot.gserviceaccount.com` doesn't have permission to access the BigQuery dataset in the `inner-cinema-476211-u9` project.

---

## Solution Steps

### Step 1: Access Google Cloud Console

1. **Go to:** [https://console.cloud.google.com/iam-admin/iam?project=inner-cinema-476211-u9](https://console.cloud.google.com/iam-admin/iam?project=inner-cinema-476211-u9)

2. **Sign in with an account that has Owner or IAM Admin permissions for this project**

---

### Step 2: Add Service Account with IAM Role

1. Click **GRANT ACCESS** or **+ ADD** button (top of page)

2. In the **Add principals** dialog:

   **New principals:**
   ```
   jibber-jabber-knowledge@appspot.gserviceaccount.com
   ```

3. **Assign roles** - Choose one of these options:

   **Option A - Full BigQuery Access (Recommended):**
   ```
   BigQuery Admin
   ```
   - Allows creating tables, running queries, managing datasets

   **Option B - Read/Write Access:**
   ```
   BigQuery Data Editor
   BigQuery Job User
   ```
   - Allows reading and writing data, running queries

   **Option C - Read-Only Access:**
   ```
   BigQuery Data Viewer
   BigQuery Job User
   ```
   - Only allows reading data and running queries

4. Click **SAVE**

---

### Step 3: Verify the Permission

After adding, you should see the service account in the permissions list:

- **Principal:** jibber-jabber-knowledge@appspot.gserviceaccount.com
- **Role:** BigQuery Admin (or whichever you chose)
- **Type:** Service Account

---

### Step 4: Test the Fix

Run the diagnostic script:

```bash
cd /Users/georgemajor/Overarch\ Jibber\ Jabber
source .venv/bin/activate
python3 diagnostic_dual_project.py
```

Look for:
```
✅ BigQuery client initialized
   Project: inner-cinema-476211-u9
✅ Dataset 'uk_energy_insights' accessible
   📊 Key Tables:
   ✅ documents_clean: XXX,XXX rows
   ✅ chunks: XXX,XXX rows
   ✅ chunk_embeddings: XXX rows
```

---

## Alternative: Dataset-Level Permissions (More Restrictive)

If you want to grant access only to the `uk_energy_insights` dataset:

### Step 1: Navigate to BigQuery

1. Go to: [https://console.cloud.google.com/bigquery?project=inner-cinema-476211-u9](https://console.cloud.google.com/bigquery?project=inner-cinema-476211-u9)

2. In the Explorer panel (left side), find:
   ```
   inner-cinema-476211-u9
   └── uk_energy_insights
   ```

### Step 2: Add Dataset-Level Permission

1. Click the **⋮** (three dots) next to `uk_energy_insights`
2. Click **Share**
3. Click **Add principal**
4. Enter:
   ```
   jibber-jabber-knowledge@appspot.gserviceaccount.com
   ```
5. Select role:
   - **BigQuery Data Editor** (for read/write)
   - **BigQuery Data Viewer** (for read-only)
6. Click **Add**
7. Click **Done**

---

## Troubleshooting

### If still getting 403 errors:

1. **Verify the service account email:**
   ```bash
   cat gridsmart_service_account.json | grep client_email
   ```
   Should show: `jibber-jabber-knowledge@appspot.gserviceaccount.com`

2. **Check you're in the correct project:**
   - Project ID must be: `inner-cinema-476211-u9`
   - NOT `jibber-jabber-knowledge`

3. **Wait a few minutes:**
   - IAM changes can take 1-2 minutes to propagate

4. **Check project ownership:**
   - Make sure you have permission to grant access
   - You need Owner or IAM Admin role

5. **Try the diagnostic script again:**
   ```bash
   python3 diagnostic_dual_project.py
   ```

### If you don't have access to the project:

1. **Find out who owns `inner-cinema-476211-u9`:**
   - Check your Google Cloud Console projects list
   - Look for billing account owner
   - Check with your team/organization

2. **Request access:**
   - Ask the project owner to add you as **Project IAM Admin**
   - Or ask them to add the service account directly using the steps above

---

## What This Does

This permission allows the service account to:
- ✅ Query the `documents_clean` table (extraction progress)
- ✅ Read from the `chunks` table (text chunks)
- ✅ Read/write to `chunk_embeddings` table (when building embeddings)
- ✅ Access other tables in `uk_energy_insights` dataset

This is necessary for:
- Monitoring extraction progress
- Running the diagnostic script
- Future embedding generation

---

## Current Extraction Status

Note: The extraction process running on UpCloud (94.237.55.15) is working fine because it uses a different service account that already has the correct permissions.

This fix is specifically for:
- Running diagnostics from your local machine
- Accessing the BigQuery data for analysis
- Future scripts that need to read the Smart Grid data

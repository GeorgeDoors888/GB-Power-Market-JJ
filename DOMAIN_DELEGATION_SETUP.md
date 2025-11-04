# Domain-Wide Delegation Setup Guide

## Overview
Domain-wide delegation allows the service account to access **ALL files** in your Google Workspace without requiring manual sharing of every folder. This is essential for indexing the entire Drive.

## Prerequisites
✅ Google Workspace account (not regular Gmail)  
✅ Super Admin access to Google Workspace Admin Console  
✅ Project Owner/Editor access to GCP Console  

---

## Part 1: Enable Domain-Wide Delegation in GCP Console

### Step 1: Navigate to Service Accounts
1. Open: https://console.cloud.google.com/iam-admin/serviceaccounts?project=jibber-jabber-knowledge
2. Find service account: `jibber-jabber-knowledge@appspot.gserviceaccount.com`
3. Click on the service account email to open details

### Step 2: Enable Domain-Wide Delegation
1. Click **"Advanced settings"** or **"Show Domain-Wide Delegation"**
2. Check the box: **"Enable Google Workspace Domain-wide Delegation"**
3. Click **"Save"**

### Step 3: Copy Client ID
1. In the service account details, find the **"Unique ID"** (numeric client ID)
2. Copy this number - you'll need it in Part 2
3. Example format: `103234567890123456789`

---

## Part 2: Configure OAuth Scopes in Google Workspace Admin

### Step 1: Access Admin Console
1. Open: https://admin.google.com/
2. You must be logged in as a **Super Admin**

### Step 2: Navigate to API Controls
1. Click **"Security"** (left sidebar)
2. Click **"Access and data control"**
3. Click **"API controls"**
4. Scroll down to **"Domain-wide delegation"**

### Step 3: Add Client ID and Scopes
1. Click **"Add new"** or **"Manage Domain Wide Delegation"**
2. Enter the **Client ID** from Part 1 Step 3
3. In the **OAuth scopes** field, paste these scopes (comma-separated):

```
https://www.googleapis.com/auth/drive.readonly,https://www.googleapis.com/auth/drive.metadata.readonly,https://www.googleapis.com/auth/spreadsheets
```

4. Click **"Authorize"**

### Step 4: Verify Configuration
- You should see the Client ID listed with the scopes
- Status should show as "Authorized"

---

## Part 3: Configure Environment Variables

### Step 1: Determine Admin Email
- Use an email that has access to all files you want to index
- Typically your Google Workspace admin email
- Example: `george@upowerenergy.uk` or `admin@upowerenergy.uk`

### Step 2: Update .env File
Add this line to your `.env` file:

```bash
GOOGLE_WORKSPACE_ADMIN_EMAIL=george@upowerenergy.uk
```

Replace `george@upowerenergy.uk` with your actual admin email.

---

## Part 4: Deploy and Test

### Step 1: Deploy Updated Files
```bash
# Deploy updated google_auth.py
scp drive-bq-indexer/src/auth/google_auth.py root@94.237.55.15:/opt/driveindexer/src/auth/

# Deploy updated .env
scp drive-bq-indexer/.env root@94.237.55.15:/opt/driveindexer/

# Copy to container and restart
ssh root@94.237.55.15 '
  docker cp /opt/driveindexer/src/auth/google_auth.py driveindexer:/app/src/auth/ && 
  docker cp /opt/driveindexer/.env driveindexer:/app/ && 
  docker restart driveindexer
'
```

### Step 2: Test Drive Access
```bash
# Test with scan script to see how many files are now accessible
ssh root@94.237.55.15 'docker exec driveindexer python3 /tmp/scan_all_drive.py'
```

**Expected Result:**
- Should now show **thousands** of files (not just 11)
- Should show **PDFs**, **Docs**, **Sheets**, etc.
- Folders should have accessible contents

### Step 3: Run Full Indexing
```bash
# Index all accessible files
ssh root@94.237.55.15 'docker exec driveindexer python -m src.cli index-drive'
```

**Expected Result:**
- Progress bar showing thousands of files
- BigQuery `documents` table should have thousands of rows

---

## Troubleshooting

### Error: "Invalid grant: Not a valid email"
- **Cause**: `GOOGLE_WORKSPACE_ADMIN_EMAIL` is incorrect
- **Fix**: Update .env with correct admin email from your Workspace

### Error: "Delegation denied"
- **Cause**: Domain-wide delegation not properly configured
- **Fix**: 
  1. Verify Client ID matches in both GCP and Admin Console
  2. Check OAuth scopes are correct (no spaces, comma-separated)
  3. Wait 10-15 minutes for changes to propagate

### Error: "User does not have access"
- **Cause**: Admin email doesn't have access to files
- **Fix**: Use an email with broader access or share folders with that user

### Still only seeing 11 files
- **Cause**: Domain-wide delegation not enabled yet
- **Fix**: Complete Parts 1 & 2 in Google consoles (cannot be automated)

---

## Quick Reference

**Service Account:**
- Email: `jibber-jabber-knowledge@appspot.gserviceaccount.com`
- Project: jibber-jabber-knowledge
- File: `/secrets/drive_sa.json`

**Required OAuth Scopes:**
```
https://www.googleapis.com/auth/drive.readonly
https://www.googleapis.com/auth/drive.metadata.readonly
https://www.googleapis.com/auth/spreadsheets
```

**Environment Variables:**
```bash
DRIVE_SERVICE_ACCOUNT=/secrets/drive_sa.json
GOOGLE_WORKSPACE_ADMIN_EMAIL=your-admin@upowerenergy.uk
```

**Key URLs:**
- GCP Service Accounts: https://console.cloud.google.com/iam-admin/serviceaccounts?project=jibber-jabber-knowledge
- Workspace Admin: https://admin.google.com/ac/owl/domainwidedelegation
- BigQuery Console: https://console.cloud.google.com/bigquery?project=inner-cinema-476211-u9

---

## What Happens After Setup

1. **Service account impersonates admin user**
   - Accesses all files visible to `GOOGLE_WORKSPACE_ADMIN_EMAIL`
   - No need to manually share folders

2. **Full Drive indexing**
   - scan_all_drive.py shows thousands of files
   - index-drive processes PDFs, Docs, Sheets, etc.
   - BigQuery contains complete metadata

3. **Search and analysis**
   - Extract text content from documents
   - Build vector embeddings for semantic search
   - Query via BigQuery or API endpoint

---

## Security Note

⚠️ Domain-wide delegation gives the service account extensive access to files. Ensure:
- Service account key file (`drive_sa.json`) is kept secure
- Only authorized personnel have access to the UpCloud server
- Review Google Cloud IAM audit logs periodically

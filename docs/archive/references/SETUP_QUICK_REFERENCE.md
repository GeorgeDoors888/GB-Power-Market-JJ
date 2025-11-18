# ⚡ Quick Setup Reference Card

## Your Service Account Details

**Service Account Email:**
```
jibber-jabber-knowledge@appspot.gserviceaccount.com
```

**Client ID (for Google Workspace Admin Console):**
```
108583076839984080568
```

**OAuth Scopes (copy/paste into Admin Console):**
```
https://www.googleapis.com/auth/drive,https://www.googleapis.com/auth/spreadsheets,https://www.googleapis.com/auth/documents,https://www.googleapis.com/auth/presentations
```

⚠️ **Note:** Full Drive access enabled with safety protections active

---

## Steps to Complete (Manual - 5 minutes)

### 1️⃣ Enable in GCP Console (2 min)
**URL:** https://console.cloud.google.com/iam-admin/serviceaccounts?project=jibber-jabber-knowledge

- Click on: `jibber-jabber-knowledge@appspot.gserviceaccount.com`
- Enable: **"Google Workspace Domain-wide Delegation"**
- Click **Save**

### 2️⃣ Authorize in Google Workspace Admin (3 min)
**URL:** https://admin.google.com/ac/owl/domainwidedelegation

- Click **"Add new"**
- **Client ID:** `108583076839984080568`
- **OAuth Scopes:** `https://www.googleapis.com/auth/drive,https://www.googleapis.com/auth/spreadsheets,https://www.googleapis.com/auth/documents,https://www.googleapis.com/auth/presentations`
- Click **"Authorize"**

⚠️ **Important:** Full Drive access includes write permissions. Safety features are enabled by default.

### 3️⃣ Tell Me Your Admin Email
What email should the service account impersonate?
- Example: `george@upowerenergy.uk`
- This email must have access to the files you want to index

---

## After You Complete Steps 1-2

I will:
1. Add your admin email to `.env`
2. Deploy the updated code to UpCloud
3. Test to verify thousands of files are now accessible
4. Run full indexing on your entire Drive

---

## Current Status
- ❌ Domain-wide delegation: **NOT ENABLED** (requires manual setup)
- ✅ Code updated: **READY** (supports delegation when enabled)
- ✅ BigQuery: **OPERATIONAL** (11 files currently indexed)
- ⏳ Waiting for: Steps 1-2 completion + admin email

---

## Why This Matters

**Before delegation:**
- Service account sees: 4,831 items (4,820 folders, 11 docs)
- Can index: Only 11 files
- Missing: Thousands of PDFs and documents inside folders

**After delegation:**
- Service account accesses: **Everything** the admin user can see
- Can index: **All files** recursively (no manual sharing needed)
- Result: Complete Drive metadata in BigQuery

---

## Questions?

- "I don't have Super Admin access" → Ask your IT admin to complete Step 2
- "What admin email should I use?" → Use your primary Workspace email (e.g., george@upowerenergy.uk)
- "Is this secure?" → Yes, service account only reads files (readonly scope)
- "Can I test before full indexing?" → Yes, we'll run scan_all_drive.py first

---

**Next:** Complete Steps 1-2 and provide your admin email 🚀

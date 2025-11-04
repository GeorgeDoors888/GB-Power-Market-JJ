# 🔧 Complete API Fixes Guide - Jibber Jabber Knowledge System

**Generated:** 4 November 2025  
**Status:** 2 of 7 APIs need fixes

---

## 📊 Current Status

### ✅ Working APIs
- Google Sheets API (jibber-jabber-knowledge)
- Google Docs API (jibber-jabber-knowledge)
- Apps Script API (jibber-jabber-knowledge)
- Service Account configuration (valid)

### ❌ Need Fixes
1. **Google Drive API** - Domain-wide delegation not configured
2. **BigQuery Smart Grid** - Service account lacks permissions
3. **ChatGPT OAuth** - Connection broken (misleading "GitHub sync" error)

---

## 🚀 Quick Start - Fix All Issues

### 1️⃣ Fix Google Drive API (15 minutes)
**Required by:** Extraction process to read PDFs from Drive  
**Who can fix:** Google Workspace admin (admin@upowerenergy.uk)

📖 **Detailed guide:** [FIX_DRIVE_API_DELEGATION.md](./FIX_DRIVE_API_DELEGATION.md)

**Quick steps:**
1. Go to [admin.google.com](https://admin.google.com) as admin
2. Security → API Controls → Domain-wide delegation
3. Add Client ID: `108583076839984080568`
4. Add scopes: `https://www.googleapis.com/auth/drive.readonly,https://www.googleapis.com/auth/drive.metadata.readonly,https://www.googleapis.com/auth/drive,https://www.googleapis.com/auth/spreadsheets,https://www.googleapis.com/auth/documents.readonly`
5. Wait 5-10 minutes
6. Test: `python3 diagnostic_dual_project.py`

---

### 2️⃣ Fix BigQuery Permissions (5 minutes)
**Required by:** Diagnostic scripts to monitor extraction progress  
**Who can fix:** Owner/IAM Admin of `inner-cinema-476211-u9` project

📖 **Detailed guide:** [FIX_BIGQUERY_PERMISSIONS.md](./FIX_BIGQUERY_PERMISSIONS.md)

**Quick steps:**
1. Go to [console.cloud.google.com/iam-admin/iam?project=inner-cinema-476211-u9](https://console.cloud.google.com/iam-admin/iam?project=inner-cinema-476211-u9)
2. Click **GRANT ACCESS**
3. Add: `jibber-jabber-knowledge@appspot.gserviceaccount.com`
4. Role: **BigQuery Admin** (or BigQuery Data Editor)
5. Click **SAVE**
6. Test: `python3 diagnostic_dual_project.py`

---

### 3️⃣ Fix ChatGPT OAuth (5 minutes)
**Required by:** ChatGPT to access your Google Drive/Sheets in conversations  
**Who can fix:** You (george@upowerenergy.uk)

📖 **Detailed guide:** [FIX_CHATGPT_OAUTH.md](./FIX_CHATGPT_OAUTH.md)

**Quick steps:**
1. Go to [myaccount.google.com/permissions](https://myaccount.google.com/permissions)
2. Sign in as george@upowerenergy.uk
3. Remove **ChatGPT** or **OpenAI** if listed
4. Go to [chat.openai.com](https://chat.openai.com)
5. Settings → Data controls → Connect Google Drive
6. Authorize with george@upowerenergy.uk
7. Test: Ask ChatGPT to list Drive files

---

## 📋 Testing After Fixes

After completing the fixes, run the diagnostic:

```bash
cd /Users/georgemajor/Overarch\ Jibber\ Jabber
source .venv/bin/activate
python3 diagnostic_dual_project.py
```

### Expected Results:
```
✅ Service Account
✅ Google Drive         ← Should be fixed now
✅ Google Sheets
✅ Google Docs
✅ Apps Script
ℹ️  Google Maps
✅ BigQuery Smart Grid  ← Should be fixed now

📊 Results: 6 passed / 0 failed / 1 info
```

---

## 🎯 Priority Order

If you can only fix some issues right now:

### Priority 1 (Critical) - Fix First
**Google Drive API** - Required for extraction to continue
- Without this: Cannot download PDFs from Drive
- Extraction will fail or slow down significantly

### Priority 2 (Important) - Fix Soon
**BigQuery Permissions** - Required for monitoring and diagnostics
- Without this: Cannot monitor extraction progress
- Cannot run diagnostic scripts locally
- Can't access data for analysis

### Priority 3 (Nice to Have) - Fix When Convenient
**ChatGPT OAuth** - Optional, for convenience
- Without this: ChatGPT can't read your Drive files in conversations
- Workaround exists: Use export scripts to create Sheets
- Not required for extraction to work

---

## 🔍 Understanding Your Setup

### Two Google Cloud Projects

**Project 1: jibber-jabber-knowledge** (@upowerenergy.uk)
- **Purpose:** Google Workspace APIs
- **APIs:** Drive, Sheets, Docs, Apps Script, Maps
- **Service Account:** jibber-jabber-knowledge@appspot.gserviceaccount.com
- **File:** gridsmart_service_account.json

**Project 2: inner-cinema-476211-u9** (Smart Grid)
- **Purpose:** BigQuery data storage
- **Dataset:** uk_energy_insights
- **Tables:** documents_clean, chunks, chunk_embeddings
- **Current extraction:** Running on UpCloud server

### Why Two Projects?

- **Workspace project** handles authentication and Google Drive access
- **BigQuery project** stores all the extracted data
- Service account from Project 1 needs permission to access Project 2

---

## 📞 Who to Contact for Each Fix

### Fix 1 (Google Drive API)
**Contact:** Google Workspace Administrator
- Email: admin@upowerenergy.uk (or IT admin)
- Access needed: Super Admin in Google Workspace
- Show them: `FIX_DRIVE_API_DELEGATION.md`

### Fix 2 (BigQuery)
**Contact:** Google Cloud Project Owner
- Project: inner-cinema-476211-u9
- Access needed: Owner or IAM Admin role
- Show them: `FIX_BIGQUERY_PERMISSIONS.md`
- Could be the same person as above

### Fix 3 (ChatGPT)
**You can do this yourself!**
- Just need: Access to george@upowerenergy.uk account
- No special permissions required
- Follow: `FIX_CHATGPT_OAUTH.md`

---

## ⚠️ Important Notes

### Extraction Still Running
The extraction process on UpCloud (94.237.55.15) is working fine because:
- Uses a different service account with correct permissions
- Already configured on the server
- Processing at 900 docs/hour

### These Fixes Are For
- Running diagnostics from your local machine
- ChatGPT accessing Drive files
- Future scripts that need these APIs
- Monitoring extraction progress locally

### Security
All fixes maintain security:
- Service account: Read-only access to Drive
- BigQuery: Limited to uk_energy_insights dataset
- ChatGPT OAuth: You can revoke anytime
- No password changes required

---

## 📚 Additional Resources

- **Service Account Info:** `gridsmart_service_account.json`
- **Client ID:** 108583076839984080568
- **Impersonation User:** george@upowerenergy.uk
- **BigQuery Project:** inner-cinema-476211-u9
- **Workspace Project:** jibber-jabber-knowledge

---

## ✅ Verification Checklist

After completing all fixes:

- [ ] Google Drive API returns files (not unauthorized_client)
- [ ] BigQuery queries return data (not 403 Access Denied)
- [ ] ChatGPT can list Drive files (no "syncing GitHub" error)
- [ ] Diagnostic script shows 6/7 checks passed
- [ ] Can query documents_clean table from local machine
- [ ] Can access Google Sheets via API

---

## 🆘 Need Help?

If you get stuck on any fix:

1. **Check the detailed guide** for that specific fix
2. **Look at the Troubleshooting section** in each guide
3. **Run the diagnostic** to see current status:
   ```bash
   python3 diagnostic_dual_project.py
   ```
4. **Check error messages** carefully - they often indicate the exact issue

---

**Ready to start?** Pick a fix above and follow the detailed guide! 🚀

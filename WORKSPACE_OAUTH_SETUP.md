# 🏢 OAuth Setup for Google Workspace Accounts

## 📋 Account Information

- **Apps Script Owner:** upowerenergy.uk (Google Workspace)
- **GCP Project:** inner-cinema-476211-u9 (Smart Grid account)
- **Issue:** Cross-account access between two different Workspace organizations

## ✅ RECOMMENDED SOLUTION

Since these are two different Google Workspace organizations, the **easiest approach is manual deployment** to avoid complex cross-organization OAuth setup.

---

## 🚀 OPTION 1: Manual Deployment (FASTEST - 2 minutes)

This is the most reliable method for cross-organization scenarios:

### Steps:

1. **Open this file in VS Code:**
   ```
   google_sheets_dashboard.gs
   ```

2. **Select all code:**
   - Press `Cmd+A` (macOS) or `Ctrl+A` (Windows)
   - Press `Cmd+C` to copy

3. **Open your Google Sheet:**
   - Go to: https://docs.google.com/spreadsheets/d/12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8/edit
   - Login with: **upowerenergy.uk** account

4. **Open Apps Script editor:**
   - Click: Extensions → Apps Script
   - You should see existing script with ID: 1MOwnQtDEMiXCYuaeR5JA4Avz_M-xYzu_iQ20pRLXdsHMTwo4qJ0Cn6wx

5. **Replace the code:**
   - Select all existing code in the editor (Cmd+A)
   - Delete it
   - Paste the new code (Cmd+V)
   - Click: 💾 Save (or Cmd+S)

6. **Refresh your Google Sheet:**
   - Go back to your sheet
   - Press `Cmd+R` or F5 to refresh

7. **Run One-Click Setup:**
   - You should see menu: ⚡ Power Market
   - Click: ⚡ Power Market → 🚀 One-Click Setup
   - Authorize when prompted (first time only)
   - Wait 10-30 seconds for setup to complete

✅ **Done!** Dashboard will auto-refresh every 5 minutes.

---

## 🔧 OPTION 2: OAuth with upowerenergy.uk Account

If you want automated deployment, you'll need to create OAuth credentials under the **upowerenergy.uk** Google Workspace:

### Prerequisites:
- Admin access to upowerenergy.uk Google Workspace
- Ability to create GCP project under upowerenergy.uk domain
- Time: ~15-20 minutes

### Steps:

1. **Create a GCP project under upowerenergy.uk:**
   - Login to https://console.cloud.google.com with **upowerenergy.uk**
   - Create new project: "UPower Apps Script Deployer"
   - Note the project ID

2. **Enable APIs:**
   - Apps Script API
   - Google Sheets API
   - Google Drive API

3. **Create OAuth credentials:**
   - Follow the steps in `setup_oauth_credentials.sh`
   - But do it in the **new upowerenergy.uk project**
   - Download credentials as `oauth_credentials.json`

4. **Update deployment script:**
   - Modify `deploy_apps_script_oauth.py` if needed
   - Run: `python3 deploy_apps_script_oauth.py`
   - Browser opens, login with **upowerenergy.uk**
   - Authorize the app

5. **Deploy:**
   - Script will update automatically
   - Future updates: just run the Python script

---

## 🤔 Which Option?

| Option | Time | Complexity | Best For |
|--------|------|------------|----------|
| **Manual (Option 1)** | 2 min | Very Easy | One-time setup, occasional updates |
| **OAuth (Option 2)** | 20 min | Moderate | Frequent updates, automation |

### My Recommendation: **Option 1 (Manual)**

Since this is a one-time deployment of corrected code, manual copy/paste is:
- ✅ Faster (2 minutes vs 20 minutes)
- ✅ No cross-organization OAuth complexity
- ✅ No additional GCP project needed
- ✅ Works immediately

You can always set up OAuth later if you need frequent automated updates.

---

## 📝 What the Code Does

The corrected `google_sheets_dashboard.gs` file contains:

- ✅ **Fixed endpoint:** `/api/proxy-v2` (not the broken `/api/proxy`)
- ✅ **Fixed schema:** camelCase fields (settlementDate, settlementPeriod)
- ✅ **Fixed tables:** bmrs_mid, bmrs_indgen_iris, bmrs_inddem_iris, bmrs_boalf, bmrs_bod
- ✅ **Fixed SQL queries:** Match your working Python dashboard
- ✅ **One-Click Setup:** Automatic configuration
- ✅ **Auto-refresh:** Updates every 5 minutes
- ✅ **Error handling:** Better logging and error messages
- ✅ **Test functions:** Easy debugging

---

## 🎯 Next Steps

**I recommend Option 1 (Manual):**

1. Open `google_sheets_dashboard.gs` in VS Code (it's in this folder)
2. Copy all code (Cmd+A, Cmd+C)
3. Go to your Google Sheet (login as upowerenergy.uk)
4. Extensions → Apps Script
5. Paste new code
6. Save
7. Refresh sheet
8. Run: ⚡ Power Market → 🚀 One-Click Setup

**Total time: 2 minutes** ⏱️

---

## ❓ Questions?

- "Will this work?" → Yes, the code has all critical fixes applied
- "Is it safe?" → Yes, you're copying to your own Apps Script
- "Will auto-refresh work?" → Yes, it's built into the code
- "Can I customize it?" → Yes, see `APPS_SCRIPT_QUICK_REF.md` for examples

---

**Ready to proceed with manual deployment?**

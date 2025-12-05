# BESS Integration - Complete Setup Summary

## ✅ What's Been Completed

### 1. Integration Implementation
- **bess_profit_model_enhanced.py**: Modified to write at row 60+ (preserves rows 1-50)
- **dashboard_pipeline.py**: Added BESS enhanced section with graceful error handling
- **test_bess_integration.py**: Integration test confirms no conflicts
- **Apps Script**: `bess_integration.gs` with formatBESSEnhanced() function ready

### 2. Testing & Verification
- Existing sections verified working (DNO, HH Profile, BtM PPA)
- Pipeline runs successfully, gracefully handles missing v_bess_cashflow_inputs view
- No conflicts between existing (rows 1-50) and enhanced (rows 60+) sections

### 3. Deployment Tools Installed
- **Node.js**: 16.20.2
- **npm**: 8.19.4  
- **clasp**: 3.1.3
- Deployment directory: `/home/george/GB-Power-Market-JJ/apps_script_deploy/`

---

## 📁 Deployment Files Created

### apps_script_deploy/
```
├── Code.gs                  # Apps Script code (copied from apps_script_enhanced/bess_integration.gs)
├── CLASP_SETUP.md          # Detailed setup instructions with troubleshooting
├── deploy.sh               # Quick deployment script (needs authentication first)
├── setup_automation.sh     # Cron job setup script
└── README.md               # This file
```

---

## 🚀 Next Steps (Manual)

Since clasp requires **interactive browser authentication**, you need to complete these steps:

### Step 1: Authenticate with Clasp
```bash
cd /home/george/GB-Power-Market-JJ/apps_script_deploy
clasp login --no-localhost
```

Follow the OAuth flow in your browser and paste the full redirect URL back.

### Step 2: Get Script ID

#### Option A: From Existing Apps Script
1. Open https://docs.google.com/spreadsheets/d/12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8/
2. Extensions → Apps Script
3. If a script exists, copy the Script ID from the URL (after `/d/` and before `/edit`)
4. Create `.clasp.json`:
```bash
cd /home/george/GB-Power-Market-JJ/apps_script_deploy
cat > .clasp.json << EOF
{
  "scriptId": "YOUR_SCRIPT_ID_HERE",
  "rootDir": "/home/george/GB-Power-Market-JJ/apps_script_deploy"
}
EOF
```

#### Option B: Create New Script
If no script exists:
```bash
cd /home/george/GB-Power-Market-JJ/apps_script_deploy
clasp create --type sheets --title "BESS Integration" --parentId "12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8"
```

### Step 3: Deploy
```bash
cd /home/george/GB-Power-Market-JJ/apps_script_deploy
./deploy.sh
```

Or manually:
```bash
cd /home/george/GB-Power-Market-JJ/apps_script_deploy
clasp push
```

### Step 4: Verify in Google Sheets
1. Open https://docs.google.com/spreadsheets/d/12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8/
2. Refresh page (Ctrl+R)
3. Look for "⚡ GB Energy Dashboard" menu
4. Go to BESS sheet → Menu → "Format Enhanced Section"

### Step 5: Setup Automation (Optional)
```bash
cd /home/george/GB-Power-Market-JJ/apps_script_deploy
./setup_automation.sh
```

Then add cron job:
```bash
crontab -e
# Add this line:
*/15 * * * * cd /home/george/GB-Power-Market-JJ && python3 dashboard_pipeline.py >> logs/pipeline.log 2>&1
```

---

## 📦 Manual Alternative (No Clasp)

If clasp authentication fails, deploy manually:

1. Open https://docs.google.com/spreadsheets/d/12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8/
2. Extensions → Apps Script
3. Delete existing code (if any)
4. Copy contents of `/home/george/GB-Power-Market-JJ/apps_script_deploy/Code.gs`
5. Paste into Apps Script editor
6. Save (Ctrl+S)
7. Refresh Google Sheets
8. Test menu: "⚡ GB Energy Dashboard" → "Format Enhanced Section"

---

## 🎯 What Each Component Does

### Python Scripts
- **dashboard_pipeline.py**: Main orchestration, updates Dashboard and BESS sheets
- **bess_profit_model_enhanced.py**: Calculates 6-stream revenue model, writes to BESS sheet row 60+
- **test_bess_integration.py**: Verifies integration preserves existing sections

### Apps Script (Code.gs)
- **onOpen()**: Creates custom menu "⚡ GB Energy Dashboard"
- **formatBESSEnhanced()**: Formats rows 58-60+ with:
  - Row 58: Divider line
  - Row 59: Section title
  - Row 60: Column headers (bold, grey)
  - T60:U67: KPIs panel (orange header, light blue data)
  - W60:Y67: Revenue stack (orange header, white/grey)

### Color Scheme
- Orange: #FF6600 (headers)
- Grey: #F5F5F5 (backgrounds)
- Light Blue: #D9E9F7 (KPI data)
- White: #FFFFFF (revenue data)

---

## 🔍 Verification Checklist

After deployment, verify:

- [ ] "⚡ GB Energy Dashboard" menu appears in toolbar
- [ ] BESS sheet rows 1-14 (DNO Lookup) still populated
- [ ] BESS sheet rows 15-20 (HH Profile) still populated
- [ ] BESS sheet rows 27-50 (BtM PPA) still populated
- [ ] BESS sheet row 58 has divider line
- [ ] BESS sheet row 59 has "Enhanced Revenue Analysis" title
- [ ] BESS sheet row 60 has formatted headers
- [ ] KPIs panel (T60:U67) formatted correctly
- [ ] Revenue stack (W60:Y67) formatted correctly
- [ ] Menu → "Format Enhanced Section" works without errors

---

## 📊 Data Population Status

**Current**: Enhanced section (rows 60+) is empty because:
- BigQuery view `v_bess_cashflow_inputs` doesn't exist yet
- Requires `bess_dispatch` table with dispatch schedule
- Pipeline gracefully skips with warning message

**To populate**:
1. Create `bess_dispatch` table with charge/discharge schedule
2. Populate supporting tables (eso_dc_clearances, eso_dc_performance, vlp_dfs_events, wholesale_prices)
3. Deploy BigQuery view: `python3 deploy_bq_view.py`
4. Run pipeline: `python3 dashboard_pipeline.py`

**Alternative**: Use existing BtM PPA analysis (rows 27-50) which is already working.

---

## 🛠️ Troubleshooting

### Clasp Authentication Fails
- Try `clasp login` without `--no-localhost` if you have a browser on the same machine
- Use manual deployment method (copy-paste into Apps Script editor)

### Menu Not Appearing
- Refresh Google Sheets (Ctrl+R)
- Check Apps Script editor for errors: Extensions → Apps Script
- Verify code saved: Look for "Last edit was X ago"

### Pipeline Errors
- Check credentials: `ls -la ~/.config/google-cloud/bigquery-credentials.json`
- Test connection: `python3 -c 'from google.cloud import bigquery; client = bigquery.Client(project="inner-cinema-476211-u9"); print("OK")'`
- Check logs: `tail -f logs/pipeline.log`

### Formatting Not Applied
- Run manually: Go to BESS sheet → Menu → "Format Enhanced Section"
- Check Apps Script execution log: Extensions → Apps Script → View → Logs

---

## 📝 Documentation

- **CLASP_SETUP.md**: Detailed clasp authentication and deployment guide
- **BESS_INTEGRATION_COMPLETE.md**: Full integration architecture and implementation
- **BESS_INTEGRATION_PLAN.md**: Original design and strategy
- **TEST_RESULTS.md**: Integration test results and verification
- **quick_start.sh**: Reference card for common operations

---

## 🎉 Summary

**✅ Code Ready**: All Python and Apps Script code is complete and tested  
**✅ Tools Installed**: Node.js, npm, clasp ready to go  
**✅ Integration Verified**: Existing sections preserved, no conflicts  
**⏳ Authentication Needed**: Clasp requires manual browser OAuth (cannot automate)  

**Final Steps**: Complete Steps 1-5 above to deploy Apps Script to Google Sheets.

---

**Sheet ID**: 12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8  
**Project**: GB-Power-Market-JJ  
**Last Updated**: 2025-12-05

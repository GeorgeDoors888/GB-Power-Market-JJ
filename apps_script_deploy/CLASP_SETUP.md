# Clasp Setup Guide - BESS Integration

## ✅ Installation Complete
- Node.js: 16.20.2
- npm: 8.19.4
- clasp: 3.1.3

## 🔐 Authentication Required

### Step 1: Login to Clasp
Run this command and follow the browser prompt:
```bash
cd /home/george/GB-Power-Market-JJ/apps_script_deploy
clasp login --no-localhost
```

You'll get a Google OAuth URL. Open it in your browser, authorize the app, and copy the full redirect URL back to the terminal.

**Common Issue**: If you get "Missing code in response URL", make sure to:
1. Copy the ENTIRE URL from your browser after authorization
2. Include everything from `https://` to the end

### Step 2: Get Script ID from Google Sheets

#### Option A: From Existing Sheet (1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA)
1. Open https://docs.google.com/spreadsheets/d/1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA/
2. Extensions → Apps Script
3. If script exists, copy the Script ID from URL (the long string after `/d/` and before `/edit`)
4. Create `.clasp.json`:
```bash
cat > /home/george/GB-Power-Market-JJ/apps_script_deploy/.clasp.json << 'EOF'
{
  "scriptId": "YOUR_SCRIPT_ID_HERE",
  "rootDir": "/home/george/GB-Power-Market-JJ/apps_script_deploy"
}
EOF
```

#### Option B: Create New Script Project
If no script exists in the sheet:
```bash
cd /home/george/GB-Power-Market-JJ/apps_script_deploy
clasp create --type sheets --title "BESS Integration" --parentId "1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA"
```

This creates `.clasp.json` automatically.

### Step 3: Copy Apps Script Code
```bash
cp /home/george/GB-Power-Market-JJ/apps_script_enhanced/bess_integration.gs \
   /home/george/GB-Power-Market-JJ/apps_script_deploy/Code.gs
```

### Step 4: Deploy to Google Sheets
```bash
cd /home/george/GB-Power-Market-JJ/apps_script_deploy
clasp push
```

### Step 5: Verify Deployment
1. Open https://docs.google.com/spreadsheets/d/1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA/
2. Refresh the page
3. Look for "⚡ GB Energy Dashboard" menu in toolbar
4. Go to BESS sheet, click menu → "Format Enhanced Section"
5. Verify rows 58-60 formatted correctly

---

## 📋 Manual Alternative (No Clasp)

If clasp authentication fails, use manual deployment:

1. Open https://docs.google.com/spreadsheets/d/1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA/
2. Extensions → Apps Script
3. Delete existing code (if any)
4. Copy contents of `/home/george/GB-Power-Market-JJ/apps_script_enhanced/bess_integration.gs`
5. Paste into Apps Script editor
6. Save (Ctrl+S)
7. Refresh Google Sheets page
8. Test "⚡ GB Energy Dashboard" menu appears

---

## 🔄 Future Updates

After clasp is set up, deploy updates with:
```bash
cd /home/george/GB-Power-Market-JJ/apps_script_deploy
# Edit Code.gs with changes
clasp push
```

---

## 🤖 Automation Setup

After Apps Script is deployed, add cron job:

```bash
# Create logs directory
mkdir -p /home/george/GB-Power-Market-JJ/logs

# Add to crontab
crontab -e
# Add this line:
*/15 * * * * cd /home/george/GB-Power-Market-JJ && python3 dashboard_pipeline.py >> logs/pipeline.log 2>&1
```

Test cron job manually:
```bash
cd /home/george/GB-Power-Market-JJ && python3 dashboard_pipeline.py
```

---

## 📊 What Gets Deployed

The Apps Script includes:

1. **formatBESSEnhanced()**: Formats rows 60+ with:
   - Row 58: Divider line
   - Row 59: Section title "Enhanced Revenue Analysis (6-Stream Model)"
   - Row 60: Column headers (bold, grey background)
   - T60:U67: KPIs panel (orange header, light blue data)
   - W60:Y67: Revenue stack (orange header, white/grey alternating)
   - Conditional formatting for revenue values
   - Column widths, borders, frozen rows

2. **onOpen() Menu**:
   - "⚡ GB Energy Dashboard" menu with 3 options:
     - Refresh DNO Lookup
     - Generate HH Profile
     - Format Enhanced Section (calls formatBESSEnhanced)

3. **Color Scheme**:
   - Orange: #FF6600 (headers)
   - Grey: #F5F5F5 (backgrounds)
   - Light Blue: #D9E9F7 (KPI data)
   - White: #FFFFFF (revenue data)
   - Yellow: #FFFFCC (highlights)

---

## ⚠️ Existing Sections Preserved

The Apps Script ONLY touches rows 58+. These sections remain unchanged:
- Rows 1-14: DNO Lookup
- Rows 15-20: HH Profile Generator
- Rows 27-50: BtM PPA Analysis

---

## 🔍 Troubleshooting

### "Access denied" in clasp login
- Use `clasp login --no-localhost` instead of `clasp login`
- Make sure to authorize with the Google account that owns the sheet

### "Script not found" when pushing
- Check `.clasp.json` has correct `scriptId`
- Verify you have edit access to the sheet

### Menu not appearing in Google Sheets
- Refresh the page (Ctrl+R)
- Check Apps Script editor for errors (Extensions → Apps Script)
- Verify code saved successfully

### Pipeline errors
- Check credentials: `ls -la /home/george/.config/google-cloud/bigquery-credentials.json`
- Verify GOOGLE_APPLICATION_CREDENTIALS env var: `echo $GOOGLE_APPLICATION_CREDENTIALS`
- Test connection: `python3 -c 'from google.cloud import bigquery; client = bigquery.Client(project="inner-cinema-476211-u9"); print("✅ Connected")'`

---

**Last Updated**: 2025-12-05  
**Sheet ID**: 1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA  
**Project**: GB-Power-Market-JJ

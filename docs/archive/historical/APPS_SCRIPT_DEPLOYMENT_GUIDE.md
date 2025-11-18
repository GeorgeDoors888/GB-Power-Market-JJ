# 📊 GB Energy Dashboard Apps Script - Complete Deployment Guide

**Created**: Nov 6, 2025  
**File**: `gb_energy_dashboard_apps_script.gs` (246 lines)  
**Sheet ID**: `12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8`

---

## 🎯 What This Script Does

### **Main Features:**
1. ✅ **Renames "Sheet1" → "Dashboard"**
2. ✅ **Fixes garbled interconnector flag emojis** (e.g., �🇴 NSL → 🇳🇴 NSL)
3. ✅ **Creates dynamic multi-series line chart** showing:
   - System Sell Price (£/MWh)
   - Demand (GW)
   - Generation (GW)
   - Wind Generation (GW)
   - Expected Wind Generation (GW)
4. ✅ **Auto-refresh every 15 minutes** via time-based trigger
5. ✅ **Manual refresh button** in custom menu
6. ✅ **Last Updated timestamp**

### **Custom Menu:**
```
🔄 Dashboard
├─ Refresh Data Now (manual button)
├─ ─────────────────
├─ Setup Dashboard
└─ View Logs
```

---

## 📋 Step-by-Step Deployment

### **Step 1: Open Apps Script Editor**

1. Open your Google Sheet: https://docs.google.com/spreadsheets/d/12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8/edit
2. Click **Extensions** → **Apps Script**
3. Delete any existing code in `Code.gs`

---

### **Step 2: Paste the Script**

1. Copy the ENTIRE contents of `gb_energy_dashboard_apps_script.gs` (all 246+ lines)
2. Paste into the Apps Script editor
3. Click **💾 Save** (or Cmd+S / Ctrl+S)
4. Name the project: "GB Energy Dashboard Manager"

---

### **Step 3: Run Initial Setup**

1. From the **function dropdown** at the top, select: `setupDashboard`
2. Click **▶️ Run**
3. **First time only**: You'll see a permission dialog:
   - Click **Review permissions**
   - Select your Google account
   - Click **Advanced** → **Go to GB Energy Dashboard Manager (unsafe)**
   - Click **Allow**
   
   ⚠️ This is normal! Apps Script needs permission to:
   - Read/write your spreadsheet
   - Create time-based triggers
   - Modify sheets and charts

4. Wait for execution to complete (should take 5-10 seconds)

---

### **Step 4: Verify Setup**

✅ **Check these things:**

1. **Sheet renamed**: "Sheet1" should now be "Dashboard"
2. **Chart created**: You should see a line chart titled "Market Overview"
3. **Flags fixed**: Interconnector labels should have correct emoji flags (🇳🇴 🇫🇷 🇧🇪 etc.)
4. **Custom menu**: Reload the sheet and look for "🔄 Dashboard" in the menu bar

---

### **Step 5: Test Manual Refresh Button**

1. In Google Sheets menu bar, click: **🔄 Dashboard** → **Refresh Data Now**
2. You should see a success alert: "✅ Success! Dashboard refreshed successfully at [timestamp]"
3. Chart should update with latest data

---

## 🔄 How It Works

### **Automatic Refresh (Every 15 Minutes)**

The script creates a time-based trigger that runs `refreshData()` every 15 minutes:

```javascript
ScriptApp.newTrigger("refreshData")
  .timeBased()
  .everyMinutes(15)
  .create();
```

**To view/manage triggers:**
1. Apps Script Editor → Click ⏰ **Triggers** (left sidebar)
2. You should see: `refreshData` → `Time-driven` → `Minutes timer` → `Every 15 minutes`

---

### **Manual Refresh (Button)**

**Option 1: Custom Menu Button**
- Click: **🔄 Dashboard** → **Refresh Data Now**
- Shows success/error alert

**Option 2: Apps Script Editor**
- Select `refreshData` function
- Click **▶️ Run**

**Option 3: ChatGPT API** (NEW!)
- Ask ChatGPT: *"Refresh the dashboard"*
- ChatGPT calls: `/sheets/run-apps-script?function_name=refreshData`
- Returns instructions on how to manually refresh

---

## 🔗 ChatGPT Integration

### **New API Endpoint:**

**Endpoint**: `/sheets/run-apps-script`  
**Method**: POST  
**Auth**: Bearer token (automatic)

**Available Functions:**
- `setupDashboard` - Initial setup
- `refreshData` - Refresh dashboard data
- `manualRefresh` - Manual refresh with UI alert
- `showLogs` - Show dashboard status

### **Example ChatGPT Prompts:**

```
"Refresh the dashboard data"
"Set up the dashboard"
"Show me dashboard logs"
"Update the energy dashboard"
```

**Response:**
```json
{
  "success": true,
  "function": "refreshData",
  "message": "To execute 'refreshData', use one of these methods:",
  "methods": {
    "manual": "Open Sheet → Extensions → Apps Script → Run refreshData",
    "menu_button": "Open Sheet → Dashboard menu → Refresh Data Now",
    "trigger": "Runs automatically every 15 minutes",
    "direct_url": "https://docs.google.com/spreadsheets/d/12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8/edit"
  }
}
```

**Note**: Apps Script functions run in Google's environment, not directly via API. The endpoint provides instructions and links.

---

## 📊 Chart Configuration

### **What's Plotted:**

The chart automatically finds these columns (case-insensitive, flexible matching):

1. **X-Axis (Time)**: 
   - Searches for: "datetime", "timestamp", "settlement", "period start", "time"

2. **Series**:
   - **System Sell Price**: "system sell price", "ssp", "sell price"
   - **Demand**: "demand", "demand gw"
   - **Generation**: "generation total", "total generation", "generation"
   - **Wind Generation**: "wind generation", "wind (gw)", "wind"
   - **Expected Wind**: "expected wind generation", "forecast wind", "exp wind"

### **Chart Settings:**
- **Type**: Line chart
- **Title**: "Market Overview"
- **Legend**: Bottom position
- **Position**: Column 8 (to the right of data)
- **Auto-update**: Every time `refreshData()` runs

---

## 🐛 Troubleshooting

### **Problem: Menu button doesn't appear**

**Solution:**
1. Reload the Google Sheet (Cmd+R / Ctrl+R)
2. Wait 5-10 seconds for `onOpen()` to execute
3. Check: Extensions → Apps Script → Make sure script is saved

---

### **Problem: Permission denied error**

**Solution:**
1. Go to: Apps Script Editor → ⏰ Triggers
2. Delete all existing triggers
3. Run `setupDashboard()` again
4. Grant permissions again

---

### **Problem: Chart not updating**

**Solution:**
1. Check if data exists in Dashboard sheet
2. Verify column headers match expected names (see Chart Configuration above)
3. Manually run `upsertDashboardChart_(SpreadsheetApp.getActive())` in Apps Script
4. Check for errors in: View → Executions

---

### **Problem: Garbled flags still showing**

**Solution:**
1. Run `fixInterconnectorFlags_(SpreadsheetApp.getActive())` manually
2. Check the `mapCountryToFlag` object in the script - add missing countries if needed
3. Refresh the sheet after running

---

### **Problem: Trigger not running every 15 minutes**

**Solution:**
1. Check quota limits: Apps Script Editor → View → Executions
2. Verify trigger exists: Apps Script Editor → ⏰ Triggers
3. Delete and recreate trigger:
   ```javascript
   // Run this in Apps Script
   ScriptApp.getProjectTriggers().forEach(t => ScriptApp.deleteTrigger(t));
   ensureAutoRefreshTrigger_();
   ```

---

## 📁 File Locations

### **Local (Mac):**
```
/Users/georgemajor/GB Power Market JJ/gb_energy_dashboard_apps_script.gs
```

### **Google Sheet:**
```
Sheet ID: 12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8
Direct Link: https://docs.google.com/spreadsheets/d/12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8/edit
Apps Script: Extensions → Apps Script
```

### **API Gateway (UpCloud):**
```
Server: 94.237.55.15
File: /opt/ai-gateway/api_gateway.py
Endpoint: https://94.237.55.15/sheets/run-apps-script
```

### **ChatGPT Schema:**
```
File: chatgpt-action-schema.json
Endpoint: /sheets/run-apps-script
Function: run_apps_script_sheets_run_apps_script_post
```

---

## 🔐 Security

### **Apps Script Permissions:**

The script requires these Google permissions:
- `https://www.googleapis.com/auth/spreadsheets` - Read/write spreadsheets
- `https://www.googleapis.com/auth/script.scriptapp` - Create triggers

**What it CAN do:**
- ✅ Read/write data in THIS spreadsheet
- ✅ Create/modify sheets and charts
- ✅ Create time-based triggers
- ✅ Show UI alerts/dialogs

**What it CANNOT do:**
- ❌ Access other Google Sheets (not shared with it)
- ❌ Send emails
- ❌ Access Drive files
- ❌ Make external HTTP requests
- ❌ Access user's Gmail

### **API Gateway Security:**

- ✅ Rate limited: 20 requests/minute
- ✅ Requires Bearer token authentication
- ✅ Audit logging of all calls
- ✅ Whitelisted functions only
- ✅ All actions logged in `/tmp/ai-gateway-audit.log`

---

## 📝 Script Functions Reference

### **User-Facing Functions:**

| Function | Description | When to Use |
|----------|-------------|-------------|
| `onOpen()` | Creates custom menu | Runs automatically when sheet opens |
| `setupDashboard()` | Initial setup | Run once after pasting script |
| `refreshData()` | Refresh data & chart | Triggered every 15 minutes |
| `manualRefresh()` | Manual refresh with alert | Click menu button |
| `showLogs()` | Show dashboard status | Check row count & last update |

### **Internal Helper Functions:**

| Function | Description |
|----------|-------------|
| `renameSheet1ToDashboard_()` | Renames Sheet1 → Dashboard |
| `copySheet1IntoDashboardIfNeeded_()` | Syncs Sheet1 data to Dashboard |
| `fixInterconnectorFlags_()` | Fixes garbled emoji flags |
| `upsertDashboardChart_()` | Creates/updates the line chart |
| `ensureAutoRefreshTrigger_()` | Creates 15-min time trigger |
| `stampLastUpdated_()` | Adds timestamp |
| `findColumnIndexByHeader_()` | Finds column by name (flexible) |

---

## 🚀 Quick Start Checklist

- [ ] Open Google Sheet
- [ ] Extensions → Apps Script
- [ ] Paste all 246+ lines of script
- [ ] Save as "GB Energy Dashboard Manager"
- [ ] Run `setupDashboard()` function
- [ ] Grant permissions
- [ ] Reload sheet to see custom menu
- [ ] Test: 🔄 Dashboard → Refresh Data Now
- [ ] Verify chart appears
- [ ] Check flags are fixed
- [ ] Confirm trigger exists (⏰ Triggers)
- [ ] Test from ChatGPT: "Refresh the dashboard"

---

## 🎉 Success Criteria

### **✅ Deployment is successful when:**

1. **Sheet renamed** from "Sheet1" to "Dashboard"
2. **Custom menu** appears: "🔄 Dashboard"
3. **Chart created** with title "Market Overview"
4. **Flags fixed** - No more � characters
5. **Manual button works** - Shows success alert
6. **Trigger created** - Visible in ⏰ Triggers
7. **API endpoint works** - ChatGPT can call it
8. **Last Updated** timestamp appears

---

## 📞 Support

### **View Execution Logs:**
1. Apps Script Editor
2. Click: View → Executions
3. See recent runs, errors, duration

### **View API Logs:**
```bash
ssh root@94.237.55.15
tail -f /tmp/ai-gateway-audit.log | grep APPS_SCRIPT
```

### **Test Endpoint:**
```bash
curl -k -s -X POST \
  -H "Authorization: Bearer 33d5da24be2b33910b7b8a57e11f99b3b6631c46266bc1603626dcac3cece3af" \
  "https://94.237.55.15/sheets/run-apps-script?function_name=refreshData" \
  | python3 -m json.tool
```

---

## 📖 Related Documentation

- `CHATGPT_CAPABILITIES.md` - Full ChatGPT integration guide
- `api_gateway.py` - API Gateway source code (lines 562-631: new endpoint)
- `chatgpt-action-schema.json` - OpenAPI schema (lines 303-350: new endpoint)

---

**🎊 DEPLOYMENT COMPLETE!**

Your dashboard now has:
- ✅ Manual refresh button
- ✅ Auto-refresh every 15 minutes
- ✅ ChatGPT integration
- ✅ Custom menu
- ✅ Dynamic chart
- ✅ Fixed emoji flags

**Go test it now!** 🚀

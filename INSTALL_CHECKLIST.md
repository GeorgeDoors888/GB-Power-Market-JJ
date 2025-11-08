# ✅ Apps Script Installation Checklist

**Time Required:** 2-3 minutes  
**Difficulty:** Easy (just copy/paste)  

---

## Before You Start

- [ ] Google Sheet is open: https://docs.google.com/spreadsheets/d/12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8/edit
- [ ] File `google_sheets_dashboard.gs` is open in VS Code
- [ ] You're logged into Google with the right account

---

## Installation Steps

### 1️⃣ Open Apps Script Editor
- [ ] In Google Sheet → Click **Extensions**
- [ ] Click **Apps Script**
- [ ] New tab opens

### 2️⃣ Clear Existing Code
- [ ] In Apps Script editor → Select All (Cmd+A)
- [ ] Delete

### 3️⃣ Copy New Code
- [ ] In VS Code → Click in `google_sheets_dashboard.gs`
- [ ] Select All (Cmd+A)
- [ ] Copy (Cmd+C)

### 4️⃣ Paste Code
- [ ] In Apps Script editor → Click in editor
- [ ] Paste (Cmd+V)
- [ ] Save (Cmd+S or click 💾 icon)

### 5️⃣ Run Setup
- [ ] Click dropdown next to **Run** button
- [ ] Select: `Setup_Dashboard_AutoRefresh`
- [ ] Click **▶ Run**

### 6️⃣ Authorize
- [ ] Click **Review permissions**
- [ ] Choose your Google account
- [ ] Click **Advanced**
- [ ] Click **Go to GB Power Market Dashboard (unsafe)**
- [ ] Click **Allow**

### 7️⃣ Wait for Completion
- [ ] Wait 10-30 seconds
- [ ] Alert appears: "Setup Complete!"
- [ ] Click **OK**

---

## Verification

### Check Menu
- [ ] Refresh your Google Sheet
- [ ] Menu **⚡ Power Market** appears at top

### Check Tabs
- [ ] **Live Dashboard** tab exists
- [ ] **Chart Data** tab exists
- [ ] **Audit_Log** tab exists
- [ ] **Live_Raw_Prices** tab exists

### Check Data
- [ ] **Live Dashboard** has 48 rows
- [ ] SSP/SBP columns show prices (£30-150 range)
- [ ] Demand/Generation show MW values (20,000-50,000 range)
- [ ] Chart displays on dashboard

### Check Auto-Refresh
- [ ] Open Apps Script editor
- [ ] Click **Triggers** icon (clock icon, left sidebar)
- [ ] One trigger listed: `refreshDashboardToday` every 5 minutes

### Check Audit Log
- [ ] Open **Audit_Log** tab
- [ ] Shows entries for setup and refresh
- [ ] Status column shows "ok" or "info"

---

## Quick Tests

### Test 1: Manual Refresh
- [ ] Click **⚡ Power Market** → **🔄 Refresh Now (today)**
- [ ] Wait 10-20 seconds
- [ ] Alert shows: "Dashboard refreshed!"
- [ ] Check **Audit_Log** for new entry

### Test 2: Chart Rebuild
- [ ] Click **⚡ Power Market** → **📊 Rebuild Chart**
- [ ] Chart recreates
- [ ] Alert shows: "Chart rebuilt successfully!"

### Test 3: Health Check
- [ ] Open Apps Script editor
- [ ] Select function: `testHealthCheck`
- [ ] Click **▶ Run**
- [ ] Alert shows: "Status: 200, OK: true"

---

## Troubleshooting Checklist

### If Authorization Fails
- [ ] Try different browser (Chrome recommended)
- [ ] Check you're using the right Google account
- [ ] Clear browser cache and try again

### If No Data Appears
- [ ] Check **Audit_Log** for error messages
- [ ] Run `testHealthCheck()` in Apps Script editor
- [ ] Verify Vercel proxy: https://gb-power-market-jj.vercel.app/api/proxy-v2?path=/health
- [ ] Run Python dashboard first: `make today`

### If Chart Missing
- [ ] Click **⚡ Power Market** → **📊 Rebuild Chart**
- [ ] Check named range exists: Data → Named ranges → NR_DASH_TODAY

### If Auto-Refresh Not Working
- [ ] Click **⚡ Power Market** → **🛑 Stop Auto-Refresh**
- [ ] Click **⚡ Power Market** → **⏰ Set 5-min Auto-Refresh**
- [ ] Check triggers in Apps Script editor (clock icon)

---

## Configuration Verification

### Check These Lines in Apps Script
- [ ] Line 23: `const VERCEL_PROXY = 'https://gb-power-market-jj.vercel.app/api/proxy-v2'`
- [ ] Line 24: `const TZ = 'Europe/London'`
- [ ] Line 25: `const PROJECT = 'inner-cinema-476211-u9'`
- [ ] Line 26: `const DATASET = 'uk_energy_prod'`

### Verify Endpoint
- [ ] URL ends with `/api/proxy-v2` ✅
- [ ] NOT `/api/proxy` ❌ (old broken endpoint)

---

## Success Indicators

You'll know it's working when:

✅ **Menu exists:** ⚡ Power Market menu at top  
✅ **Data populates:** 48 rows in Live Dashboard  
✅ **Chart displays:** Visual on dashboard tab  
✅ **Prices realistic:** SSP/SBP between £30-150/MWh  
✅ **Demand realistic:** 20,000-50,000 MW  
✅ **Auto-refresh working:** Audit_Log shows entries every 5 min  
✅ **No errors:** Audit_Log status shows "ok"  

---

## Next Steps

After successful installation:

### Immediate
- [ ] Test manual refresh
- [ ] Review chart
- [ ] Check audit log

### Within 5 minutes
- [ ] Verify auto-refresh triggers
- [ ] Check new entry in Audit_Log

### Within 1 hour
- [ ] Monitor several refresh cycles
- [ ] Verify data stays current
- [ ] Check for any errors

### Ongoing
- [ ] Review Audit_Log daily
- [ ] Compare with Python dashboard
- [ ] Customize chart if needed
- [ ] Add features as desired

---

## Support Resources

| Issue Type | Resource |
|------------|----------|
| Installation help | `INSTALL_APPS_SCRIPT_VISUAL_GUIDE.md` |
| Quick reference | `APPS_SCRIPT_QUICK_REF.md` |
| Full documentation | `GOOGLE_SHEETS_APPS_SCRIPT_GUIDE.md` |
| Technical details | `APPS_SCRIPT_CODE_REVIEW.md` |
| Code review | Read `google_sheets_dashboard.gs` |

---

## Time Tracking

- **Step 1 (Open Apps Script):** 30 sec
- **Step 2 (Clear code):** 10 sec
- **Step 3 (Copy code):** 20 sec
- **Step 4 (Paste code):** 10 sec
- **Step 5 (Run setup):** 30 sec
- **Step 6 (Authorize):** 30 sec
- **Step 7 (Wait for completion):** 10-30 sec

**Total Time:** 2 minutes 20 seconds (typical)

---

## Final Check

Before you consider installation complete:

- [ ] All installation steps completed ✅
- [ ] All verification checks passed ✅
- [ ] All quick tests successful ✅
- [ ] Configuration verified ✅
- [ ] No errors in Audit_Log ✅

**If all checked → Installation COMPLETE! 🎉**

---

**Installation Date:** _________________  
**Installation Time:** _________________  
**Installed By:** _________________  
**Status:** ☐ Success ☐ Issues (see notes below)  

**Notes:**
_________________________________________________
_________________________________________________
_________________________________________________

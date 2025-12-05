# ⚡ BESS Integration - Quick Start

## ✅ Status: DEPLOYED (Version 18)

**Apps Script**: ✅ Deployed to correct sheet  
**Existing Data**: ✅ Preserved (DNO/HH/BtM)  
**Next Step**: Open sheet and run formatting

---

## 🚀 3-Step Setup

### 1. Open Sheet & Refresh (5 sec)
```
https://docs.google.com/spreadsheets/d/12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8/
```
Press **Ctrl+R** to refresh

### 2. Run Formatting (30 sec)
1. Go to **BESS** sheet
2. Click menu: **⚡ GB Energy Dashboard** → **🎨 Format BESS Enhanced**
3. Authorize if prompted
4. Wait for success message

### 3. Populate Data (Optional)
```bash
cd /home/george/GB-Power-Market-JJ
python3 dashboard_pipeline.py
```

---

## ✅ What You'll Get

- **Row 58**: Grey divider line
- **Row 59**: Orange title "Enhanced Revenue Analysis (6-Stream Model)"
- **Row 60**: Light blue column headers
- **T60:U67**: KPIs panel (orange header, yellow values)
- **W60:Y67**: Revenue stack (Revenue Stream | £/year | %)
- **Rows 1-50**: Existing sections preserved (DNO, HH Profile, BtM PPA)

---

## 📋 Verify Success

After step 2, check:
- [ ] Menu "⚡ GB Energy Dashboard" appears in toolbar
- [ ] Row 58 has grey divider with dashes
- [ ] Row 59 has orange "Enhanced Revenue Analysis" title
- [ ] Row 60 has blue headers
- [ ] KPIs panel at T60 with orange header
- [ ] Revenue stack at W60 with orange header
- [ ] Existing data at rows 1-50 still there

---

## 📖 Full Documentation

- **DIAGNOSTIC_REPORT.md** - Issue analysis (wrong sheet ID)
- **DEPLOYMENT_SUCCESS_V18.md** - Complete deployment report
- **REDEPLOY_INSTRUCTIONS.sh** - Redeployment guide

---

**Issue Fixed**: Apps Script was on wrong sheet (V2 instead of Main)  
**Solution**: Redeployed to correct sheet with fixed sheet ID  
**Version**: 18 (5 Dec 2025, 02:47)  
**Status**: ✅ Ready to use

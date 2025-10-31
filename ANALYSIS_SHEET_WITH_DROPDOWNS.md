# ✅ Analysis Sheet - NOW WITH DROPDOWNS!

**Status:** 🟢 WORKING  
**Link:** https://docs.google.com/spreadsheets/d/12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8/

---

## 🎯 What You Have Now

### ✅ Interactive Controls

**Date Range Dropdown (Cell C6):**
- 24 Hours
- 1 Week
- 1 Month  
- 3 Months
- 6 Months
- 1 Year
- 2 Years
- Custom

**Custom Date Range (Cells H7-H8):**
- From: (DD/MM/YYYY)
- To: (DD/MM/YYYY)
- Only used when dropdown = "Custom"

**Data Group Checkboxes (Row 12):**
- ☑️ System Frequency
- ☑️ Market Prices
- ☑️ Generation Mix

---

## 📊 What's Displayed

- **Summary Stats:**
  - Total Generation (GWh)
  - Top fuel types with totals
  - Number of records
  - Date range analyzed

- **Data Table (50 rows):**
  - Timestamp
  - Fuel Type
  - Generation (MW)
  - Source (historical/real-time)
  - Settlement Date
  - Settlement Period

---

## 🔄 How to Use

### 1. Change Date Range
1. Open the sheet
2. Click cell C6 dropdown
3. Select: "24 Hours", "1 Week", "1 Month", etc.
4. Run update script:
   ```bash
   python3 update_analysis_with_dropdowns.py
   ```

### 2. Use Custom Dates
1. Cell C6: Select "Custom"
2. Cell H7: Enter start date (e.g., 01/10/2025)
3. Cell H8: Enter end date (e.g., 31/10/2025)
4. Run update script:
   ```bash
   python3 update_analysis_with_dropdowns.py
   ```

### 3. Quick Refresh (Same Settings)
```bash
python3 update_analysis_with_dropdowns.py
```

---

## 📋 Files

| File | Purpose |
|------|---------|
| `create_analysis_with_dropdowns.py` | Initial setup (run once) |
| `update_analysis_with_dropdowns.py` | Refresh data based on selections |

---

## 🎨 Features

✅ **Date range dropdown** - Select from preset ranges  
✅ **Custom date picker** - Pick any date range  
✅ **Checkboxes** - Control what data to show  
✅ **Professional formatting** - Color-coded sections  
✅ **Real-time + Historical data** - Unified seamlessly  
✅ **Auto-calculated stats** - Total generation, fuel breakdown  

---

## 💡 Tips

- **Default view:** Last 1 week of data
- **Maximum rows:** 50 (to keep sheet responsive)
- **Data source:** `bmrs_fuelinst_unified` view
- **Update frequency:** Run script anytime to refresh

---

**Created:** October 31, 2025  
**Status:** ✅ Fully Interactive with Dropdowns

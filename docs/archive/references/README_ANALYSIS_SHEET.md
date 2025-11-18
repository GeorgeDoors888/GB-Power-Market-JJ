# 🚀 Quick Start: Analysis Sheet

**Create a powerful unified analysis dashboard combining historical and real-time data in one command!**

---

## ⚡ TL;DR - Run This

```bash
cd "/Users/georgemajor/GB Power Market JJ"
./setup_analysis_sheet.sh
```

**That's it!** This will:
- ✅ Create 5 unified BigQuery views
- ✅ Create "Analysis" sheet in Google Sheets
- ✅ Populate with data
- ✅ Set up dropdowns and formatting

---

## 📊 What You Get

### A Beautiful Analysis Sheet With:

**🎨 User-Friendly Interface:**
- Date range dropdown (24hrs → 4 years)
- Custom date picker (from/to)
- Data group checkboxes
- Professional color scheme

**📈 Analysis Sections:**
1. **System Frequency Analysis**
   - Average, min, max frequency
   - Time below 49.8 Hz
   - Historical + real-time data

2. **Market Prices Analysis**
   - System Sell Price / Buy Price
   - Volatility analysis
   - Price trends over time

3. **Generation Mix Analysis**
   - Total generation
   - Breakdown by fuel type (Wind, Solar, Gas, Nuclear, etc.)
   - Renewable percentage

4. **Balancing Services Analysis**
   - Bid-offer data
   - BOA lift forecasts

5. **Raw Data Table**
   - Up to 100 rows
   - All data sources combined
   - Export-ready

**🔄 Data Sources:**
- Historical: Elexon API (2020-present, 5.66M rows)
- Real-Time: IRIS streaming (last 48 hours)
- **Unified seamlessly!**

---

## 📚 Documentation

| File | Purpose | Size |
|------|---------|------|
| **[README_ANALYSIS_SHEET.md](README_ANALYSIS_SHEET.md)** | ⭐ This file - Quick start | 3 KB |
| **[ANALYSIS_SHEET_IMPLEMENTATION_SUMMARY.md](ANALYSIS_SHEET_IMPLEMENTATION_SUMMARY.md)** | Complete deployment guide | 16 KB |
| **[ANALYSIS_SHEET_DESIGN.md](ANALYSIS_SHEET_DESIGN.md)** | Detailed design specification | 37 KB |
| **[UNIFIED_ARCHITECTURE_HISTORICAL_AND_REALTIME.md](UNIFIED_ARCHITECTURE_HISTORICAL_AND_REALTIME.md)** | Architecture overview | 28 KB |

---

## 🎯 Three Ways to Use

### Option 1: One-Command Setup (Recommended)
```bash
./setup_analysis_sheet.sh
```

### Option 2: Step-by-Step
```bash
# Step 1: Install dependency
python3 -m pip install gspread-formatting

# Step 2: Create views and sheet
python3 create_analysis_sheet.py

# Step 3: Populate with data
python3 update_analysis_sheet.py
```

### Option 3: Manual Refresh Only
```bash
# Just refresh existing sheet with latest data
python3 update_analysis_sheet.py
```

---

## 🔄 Automatic Updates

### Set Up Cron Job (Every 5 Minutes)
```bash
# Edit crontab
crontab -e

# Add this line:
*/5 * * * * cd '/Users/georgemajor/GB Power Market JJ' && python3 update_analysis_sheet.py >> analysis_updates.log 2>&1
```

### Check Update Log
```bash
tail -f analysis_updates.log
```

---

## 🔗 Quick Links

- **Spreadsheet:** https://docs.google.com/spreadsheets/d/12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8/
- **BigQuery Console:** https://console.cloud.google.com/bigquery?project=inner-cinema-476211-u9
- **Dataset:** `inner-cinema-476211-u9.uk_energy_prod`

---

## 💡 Common Tasks

### Change Date Range
1. Open spreadsheet
2. Cell C6: Select dropdown (24 Hours, 1 Week, 1 Month, etc.)
3. Run: `python3 update_analysis_sheet.py`

### Custom Date Range
1. Cell H7: Enter start date (DD/MM/YYYY)
2. Cell H8: Enter end date (DD/MM/YYYY)
3. Run: `python3 update_analysis_sheet.py`

### Enable/Disable Data Groups
- Check/uncheck boxes in cells A13-G15
- Currently shows: Frequency, Prices, Generation, Balancing

---

## 🎨 Features

✅ **Unified Data:** Historical (2020-present) + Real-time (last 48 hours)  
✅ **Easy Selection:** Dropdown (24hrs-4yrs) or custom dates  
✅ **Professional Design:** Color-coded, formatted, easy to read  
✅ **Rich Analytics:** Statistics, trends, breakdowns  
✅ **Export Ready:** Raw data table for CSV/Excel export  
✅ **Auto-Refresh:** Optional cron job for live updates  
✅ **Data Quality Info:** Source tracking, quality metrics  

---

## 🆘 Help

### Problem: Sheet not found
**Run:** `python3 create_analysis_sheet.py`

### Problem: No data showing
**Check:**
1. IRIS processor running? `ps aux | grep iris`
2. Date range too narrow? Try "1 Month"
3. BigQuery access? `gcloud auth application-default login`

### Problem: Permission denied
**Fix:** `chmod +x setup_analysis_sheet.sh`

### Problem: Package missing
**Install:** `python3 -m pip install gspread-formatting google-cloud-bigquery gspread`

---

## 📊 Data Sources

### Historical Tables (Elexon API)
- `bmrs_freq` - System frequency
- `bmrs_mid` - Market prices
- `bmrs_fuelinst` - Generation data
- `bmrs_bod` - Bid-offer data
- `bmrs_boalf` - BOA lift forecasts

### Real-Time Tables (IRIS)
- `bmrs_freq_iris` - Real-time frequency
- `bmrs_mid_iris` - Real-time prices
- `bmrs_fuelinst_iris` - Real-time generation
- `bmrs_bod_iris` - Real-time bid-offer
- `bmrs_boalf_iris` - Real-time forecasts

### Unified Views (Combined)
- `bmrs_freq_unified` ← Historical + Real-time
- `bmrs_mid_unified` ← Historical + Real-time
- `bmrs_fuelinst_unified` ← Historical + Real-time
- `bmrs_bod_unified` ← Historical + Real-time
- `bmrs_boalf_unified` ← Historical + Real-time

---

## ✅ Status

**Created:** October 30, 2025  
**Status:** ✅ Ready to Deploy  
**Testing:** Pending user deployment  
**Components:** 5 files (85 KB total)  

---

## 🚀 Deploy Now

```bash
cd "/Users/georgemajor/GB Power Market JJ"
./setup_analysis_sheet.sh
```

**Then open:** https://docs.google.com/spreadsheets/d/12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8/

---

**Questions?** See [ANALYSIS_SHEET_IMPLEMENTATION_SUMMARY.md](ANALYSIS_SHEET_IMPLEMENTATION_SUMMARY.md) for complete guide.

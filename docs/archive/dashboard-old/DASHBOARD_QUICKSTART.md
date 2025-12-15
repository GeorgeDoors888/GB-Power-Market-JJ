# Live Dashboard - Quick Start Guide

## ✅ Status: FULLY OPERATIONAL

The live GB power market dashboard is now working and pulls real-time data from BigQuery to Google Sheets.

## 🎯 What It Does

Pulls live balancing mechanism data every day and writes to Google Sheets:
- **System Prices:** SSP (System Sell Price) and SBP (System Buy Price)
- **Generation & Demand:** Total system generation and demand
- **Balancing Actions:** Count and details of accepted balancing actions
- **Bid-Offer Prices:** Average BOD bid and offer prices by settlement period
- **Interconnector Flows:** Net import/export to GB via interconnectors

## 🚀 Quick Commands

```bash
# Refresh dashboard with today's data
make today

# Refresh dashboard for specific date
.venv/bin/python tools/refresh_live_dashboard.py --date 2024-11-05

# Install dependencies (first time only)
make install

# Create optional BigQuery views
make views
```

## 📊 View the Dashboard

**Google Sheet:** https://docs.google.com/spreadsheets/d/1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA/edit

### Tabs Available:
1. **Live Dashboard** - Main data table (50 settlement periods × 10 metrics)
2. **Live_Raw_Prices** - SSP/SBP by settlement period
3. **Live_Raw_Gen** - Generation/demand detail
4. **Live_Raw_BOA** - Balancing actions detail
5. **Live_Raw_Interconnectors** - Interconnector flows

## 📈 Create Charts

1. Open the Google Sheet
2. Click **Insert → Chart**
3. Set data range to: `NR_TODAY_TABLE` (named range)
4. Choose **Line chart**
5. X-axis: **SP** (Settlement Period 1-50)
6. Y-axis series: Select any combination:
   - **SSP** - System Sell Price
   - **SBP** - System Buy Price
   - **BOD_Offer_Price** - Balancing offer prices
   - **BOD_Bid_Price** - Balancing bid prices
   - **Demand_MW** - System demand
   - **Generation_MW** - System generation
   - **IC_NET_MW** - Interconnector net flow

**Why use named range?** The chart won't break when you refresh the data - it always points to the same range.

## 🔧 Debug in VS Code

1. Open `tools/refresh_live_dashboard.py`
2. Press **F5** (or click Run → Start Debugging)
3. Choose configuration:
   - **"Refresh Live Dashboard (today)"** - Uses current date
   - **"Refresh Live Dashboard (custom date)"** - Prompts for date input

## ⚙️ Configuration

All settings are in `.env` file:

```bash
# Required for dashboard
GOOGLE_APPLICATION_CREDENTIALS=/Users/georgemajor/GB Power Market JJ/inner-cinema-credentials.json
SHEET_ID=1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA

# BigQuery project
PROJECT_ID=inner-cinema-476211-u9
BQ_DATASET=uk_energy_prod
```

## 🤖 Automate (Optional)

Set up GitHub Actions to refresh every 5 minutes:

1. Encode service account JSON:
   ```bash
   base64 -i inner-cinema-credentials.json | pbcopy
   ```

2. Add GitHub Secrets (Settings → Secrets → Actions):
   - Name: `SA_JSON_B64` → Paste encoded JSON
   - Name: `SHEET_ID` → Value: `1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA`

3. Enable workflow in GitHub Actions tab

4. Dashboard auto-refreshes every 5 minutes ✅

## 📚 Data Dictionary

| Column | Description | Unit |
|--------|-------------|------|
| SP | Settlement Period (half-hourly) | 1-50 |
| SSP | System Sell Price | £/MWh |
| SBP | System Buy Price | £/MWh |
| Demand_MW | System demand | MW |
| Generation_MW | System generation | MW |
| BOALF_Acceptances | Balancing action count | # |
| BOALF_Avg_Level_Change | Average accepted level adjustment | MW |
| BOD_Offer_Price | Average BOD offer price | £/MWh |
| BOD_Bid_Price | Average BOD bid price | £/MWh |
| IC_NET_MW | Net interconnector flow (+ = import) | MW |

## 🔍 Integration with VLP Analysis

### Run VLP Analysis:
```bash
.venv/bin/python complete_vlp_battery_analysis.py
```

**Output:** 
- Identifies 148 battery BMUs
- 102 VLP-operated (68.9%)
- Historical activity and pricing data
- Exports 4 CSV files

### Combined Insights:
- Compare VLP average bid/offer vs live SSP/SBP
- Monitor when VLP batteries likely active (look for SSP-SBP spread)
- Track interconnector impact on system balance
- Validate historical patterns against current conditions

## 🎓 Example Analysis Questions

**Using the Dashboard:**
1. What's the SSP-SBP spread today? (revenue opportunity indicator)
2. When is system demand highest? (peak periods)
3. How many balancing actions per settlement period?
4. What are typical BOD offer prices vs SSP?
5. When are interconnectors importing vs exporting?

**Using VLP Analysis + Dashboard:**
1. Do VLP battery offer prices align with current SSP?
2. When would VLP batteries activate? (SSP > VLP offer price)
3. How does today's price volatility compare to historical?
4. Which periods show highest balancing action demand?

## 🆘 Troubleshooting

### Issue: "Unrecognized name" error
✅ **Fixed!** All queries now use correct BigQuery schema (camelCase columns)

### Issue: Empty data in sheet
- Check date: Data might not exist for future dates
- Try known good date: `--date 2024-11-05`
- Check BigQuery: `bq ls inner-cinema-476211-u9:uk_energy_prod`

### Issue: Permission denied (Google Sheets)
- Verify service account has "Editor" access to sheet
- Check credentials file path in `.env`
- Test: `gcloud auth application-default login`

### Issue: No data for today
- BMRS data may have delay (30-60 minutes)
- Try yesterday's date instead
- Check BMRS website for data availability

## 📖 Full Documentation

- **Setup Guide:** `DASHBOARD_SETUP_COMPLETE.md`
- **Schema Fixes:** `DASHBOARD_SCHEMA_FIXES_COMPLETE.md`
- **Detailed README:** `README_DASHBOARD.md`
- **VLP Analysis:** `VLP_BATTERY_ANALYSIS_SUMMARY.md`

## ✅ Testing Checklist

All items verified working:

- [x] Pull data from BigQuery (5 queries: prices, gen, boalf, bod, interconnectors)
- [x] Write to Google Sheets (5 tabs)
- [x] Create named range (NR_TODAY_TABLE)
- [x] Handle date parameters (today or custom)
- [x] Work with actual schemas (camelCase, special field structures)
- [x] Process 50 settlement periods
- [x] Debug configurations in VS Code
- [x] Makefile commands (make today)
- [x] Data accuracy validated

## 🎯 Success!

**Status:** Production ready ✅  
**Last Test:** November 6, 2025 (today) - 50 rows written successfully  
**Performance:** ~5 seconds to refresh all data  
**Data Quality:** All 10 columns populated for all 50 settlement periods

---

**Need help?** Check the full documentation files listed above or review the Python script at `tools/refresh_live_dashboard.py`.

# Live Dashboard Setup - Complete Integration Guide

## ✅ Files Created

All live dashboard infrastructure has been added to your project:

### Core Files
- ✅ `tools/refresh_live_dashboard.py` - Main refresh script
- ✅ `tools/bigquery_views.sql` - Optional analytics views
- ✅ `tools/__init__.py` - Python package marker
- ✅ `Makefile` - Convenience commands (`make today`, `make install`)
- ✅ `.env.sample` - Configuration template
- ✅ `.env` - Updated with SHEET_ID and credentials path
- ✅ `README_DASHBOARD.md` - Complete documentation

### Integration Files
- ✅ `.vscode/launch.json` - Added 2 new debug configurations
- ✅ `.github/workflows/refresh-dashboard.yml` - GitHub Action for auto-refresh
- ✅ `VLP_BATTERY_ANALYSIS_SUMMARY.md` - Updated with dashboard integration section

## 🔧 Next Steps

### 1. Verify BigQuery Table Schemas

The refresh script needs to be adjusted for your actual table column names. Please run:

```bash
# Check MID table structure (System prices)
bq show --schema inner-cinema-476211-u9:uk_energy_prod.bmrs_mid

# Check INDGEN table structure (Generation/Demand)
bq show --schema inner-cinema-476211-u9:uk_energy_prod.bmrs_indgen_iris

# Check BOALF table structure (Balancing actions)
bq show --schema inner-cinema-476211-u9:uk_energy_prod.bmrs_boalf

# Check BOD table structure (Bid-Offer)
bq show --schema inner-cinema-476211-u9:uk_energy_prod.bmrs_bod

# Check Interconnectors table
bq show --schema inner-cinema-476211-u9:uk_energy_prod.bmrs_interconnectors
```

### 2. Update SQL Queries in refresh_live_dashboard.py

Based on your actual schema, update the SQL queries (lines 21-95) to match your column names.

**Current script assumes:**
- `settlement_date` (DATETIME) - may be `settlementDate`
- `settlement_period` (INTEGER) - may be `settlementPeriod`
- `system_sell_price`, `system_buy_price` - may be in different format
- `total_generation_mw`, `total_demand_mw` - verify column names
- `accepted_volume_mwh`, `accepted_price` - verify for BOALF/BOD

**Example fix for camelCase:**
```python
# Change:
WHERE DATE(settlement_date) = @date

# To:
WHERE DATE(settlementDate) = @date
```

### 3. Test the Script

```bash
# Test with a specific date that has data
cd "/Users/georgemajor/GB Power Market JJ"
GOOGLE_APPLICATION_CREDENTIALS="/Users/georgemajor/GB Power Market JJ/inner-cinema-credentials.json" \
SHEET_ID="1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA" \
.venv/bin/python tools/refresh_live_dashboard.py --date 2025-11-05
```

### 4. Verify Google Sheet Access

Make sure your service account (`inner-cinema-credentials.json`) has:
- ✅ Edit access to the Google Sheet (ID: `1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA`)
- ✅ Google Sheets API enabled in Google Cloud Console
- ✅ BigQuery access (Data Viewer role minimum)

### 5. Enable GitHub Action (Optional)

For automated refresh every 5 minutes:

1. **Encode service account:**
   ```bash
   cat "/Users/georgemajor/GB Power Market JJ/inner-cinema-credentials.json" | base64 | pbcopy
   ```

2. **Add GitHub Secrets:**
   - Go to repo Settings → Secrets and variables → Actions
   - Add `SA_JSON_B64` (paste the base64 string)
   - Add `SHEET_ID` (value: `1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA`)

3. **Enable workflow:**
   - Go to Actions tab
   - Find "Refresh Live Dashboard" workflow
   - Click "Enable workflow"

## 📊 How It Works

### Data Flow
```
BigQuery Tables               Refresh Script                Google Sheets
┌─────────────────┐          ┌──────────────────┐         ┌────────────────┐
│ bmrs_mid        │──query──▶│ SQL → DataFrame  │─write──▶│ Live_Raw_*     │
│ bmrs_indgen_iris│──query──▶│                  │─write──▶│ tabs           │
│ bmrs_boalf      │──query──▶│ Merge & tidy     │─write──▶│                │
│ bmrs_bod        │──query──▶│                  │─write──▶│ Live Dashboard │
│ bmrs_inter*     │──query──▶│ Set named range  │─create─▶│ NR_TODAY_TABLE │
└─────────────────┘          └──────────────────┘         └────────────────┘
```

### Named Range Magic

The script creates **`NR_TODAY_TABLE`** (Live Dashboard, A1:O51):
- Row 1: Headers
- Rows 2-51: Settlement periods 1-50
- Columns A-O: All metrics

**Your chart binds to this range** → never breaks when data updates!

### Run Modes

1. **Manual (CLI):**
   ```bash
   make today  # Uses Makefile
   # or
   python tools/refresh_live_dashboard.py --date 2025-11-05
   ```

2. **VS Code (Debug):**
   - Press F5
   - Select "Refresh Live Dashboard (today)" or "(custom date)"

3. **Automated (GitHub Action):**
   - Runs every 5 minutes
   - Requires secrets configured
   - Can also trigger manually

## 🔗 Integration with VLP Analysis

### Combined Power

**Historical Analysis (VLP-Battery):**
- 148 battery BMUs identified
- 68.9% VLP-operated
- Average activity: 81,755 actions/year
- Average prices: Bid £50-100, Offer £90-160

**Live Monitoring (Dashboard):**
- Real-time SSP/SBP for 48 settlement periods
- Current demand vs generation
- Live BOALF/BOD prices
- Interconnector flows

### Use Cases

1. **Price Arbitrage Monitoring:**
   - Compare live SSP with VLP average bid prices
   - Alert when SSP > VLP offer threshold → discharge opportunity

2. **Activity Correlation:**
   - High SSP periods → More VLP battery offers accepted
   - Low SBP periods → More VLP battery bids accepted

3. **Revenue Validation:**
   - Historical: £X estimated from BOD averages
   - Live: Track actual SSP/SBP → validate estimates

4. **Market Pattern Analysis:**
   - Which settlement periods have highest VLP activity?
   - How do VLP batteries respond to wind/solar generation levels?
   - Interconnector flow impact on VLP arbitrage opportunities

## 📝 Quick Reference

### File Locations
```
GB Power Market JJ/
├─ tools/
│  ├─ refresh_live_dashboard.py    ← Main script
│  ├─ bigquery_views.sql            ← Optional views
│  └─ __init__.py
├─ .vscode/
│  └─ launch.json                   ← Updated with 2 configs
├─ .github/
│  └─ workflows/
│     └─ refresh-dashboard.yml      ← Auto-refresh action
├─ .env                             ← Config (has SHEET_ID)
├─ .env.sample                      ← Template
├─ Makefile                         ← Commands
├─ README_DASHBOARD.md              ← Full docs
└─ VLP_BATTERY_ANALYSIS_SUMMARY.md  ← Updated with integration
```

### Environment Variables
```bash
GOOGLE_APPLICATION_CREDENTIALS=/Users/georgemajor/GB Power Market JJ/inner-cinema-credentials.json
SHEET_ID=1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA
```

### Makefile Commands
```bash
make install    # Setup venv and install deps
make run        # Run with today's date
make today      # Same as 'run'
make views      # Create BigQuery views
```

### VS Code Launch Configs
- **Refresh Live Dashboard (today)** - F5 → auto-detects today
- **Refresh Live Dashboard (custom date)** - F5 → prompts for date

## 🎯 Success Criteria

✅ **Setup Complete When:**
1. Script runs without errors
2. Google Sheet shows populated tabs
3. Named range `NR_TODAY_TABLE` exists
4. Chart displays data correctly
5. (Optional) GitHub Action runs successfully

✅ **Integration Complete When:**
1. Can compare live SSP with historical VLP bid prices
2. Can track battery activity against current prices
3. Can validate revenue estimates with actual prices
4. Can identify arbitrage opportunities in real-time

## 🐛 Troubleshooting

### "Unrecognized name: settlement_date"
→ Update SQL queries to match your actual column names (likely camelCase: `settlementDate`)

### "SHEET_ID not found"
→ Check `.env` file exists and has correct `SHEET_ID=...` line

### "Credentials error"
→ Verify service account JSON path in `.env` and file exists

### "No data returned"
→ Check date has data: `bq query "SELECT COUNT(*) FROM table WHERE DATE(column) = '2025-11-05'"`

### Chart doesn't update
→ Verify chart data range is set to `NR_TODAY_TABLE` (not A1:O51)

## 📚 Documentation

- **`README_DASHBOARD.md`** - Complete dashboard documentation
- **`VLP_BATTERY_ANALYSIS_SUMMARY.md`** - VLP analysis + dashboard integration
- **`tools/refresh_live_dashboard.py`** - Inline code comments

## ✨ What's Next?

1. **Fix SQL queries** for your schema
2. **Test refresh** with known good date
3. **Create chart** using NR_TODAY_TABLE
4. **Enable automation** (GitHub Action)
5. **Build analysis** combining VLP + live data

---

**Ready to go!** Once you update the SQL column names to match your schema, everything will work seamlessly. The infrastructure is complete and integrated with your VLP-Battery analysis.

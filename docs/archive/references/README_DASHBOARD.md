# Live GB Power Dashboard (Google Sheets)

**Project:** inner-cinema-476211-u9  
**Datasets:** uk_energy_prod, uk_energy_prod_eu

## 🎯 What it does

- Queries **MID** (SSP/SBP), **IRIS INDGEN** (demand/generation/wind), **BOALF/BOD**, **Interconnectors**
- Writes raw data to separate tabs: `Live_Raw_Prices`, `Live_Raw_Gen`, `Live_Raw_BOA`, `Live_Raw_Interconnectors`
- Creates tidy table in **Live Dashboard** tab
- Maintains stable named range **`NR_TODAY_TABLE`** for chart binding (never breaks when rows change)

## 🚀 Quick start

### 1. Install dependencies
```bash
make install
```

### 2. Configure environment
```bash
cp .env.sample .env
# Edit .env with your SHEET_ID and credentials path
```

### 3. Run refresh
```bash
# Refresh with today's data (Europe/London timezone)
make today

# Or refresh with specific date
. .venv/bin/activate
export $(grep -v '^#' .env | xargs)
python tools/refresh_live_dashboard.py --date 2025-11-06
```

## 📊 Output Structure

### Raw Data Tabs
- **Live_Raw_Prices**: Settlement Period (SP), SSP, SBP
- **Live_Raw_Gen**: SP, Generation MW, Demand MW, Wind MW, Solar MW
- **Live_Raw_BOA**: SP, BOALF MWh, BOALF Price, BOD Price
- **Live_Raw_Interconnectors**: SP, IFA, NSL, BRITNED, NEMO, MOYLE flows

### Live Dashboard Tab (Tidy Table)
Columns: `SP | SSP | SBP | Demand_MW | Generation_MW | Wind_MW | BOALF_MWh | BOALF_Price | BOD_Price | IC_IFA_MW | IC_NSL_MW | IC_BRITNED_MW | IC_NEMO_MW | IC_MOYLE_MW | IC_NET_MW`

- 50 rows (settlement periods 1-50)
- Named range: **`NR_TODAY_TABLE`** (rows 1-51, columns A-O)

## 📈 Chart Setup

Point your chart's data series at the named range **`NR_TODAY_TABLE`**:

1. Open your Google Sheet
2. Select your chart → Edit chart
3. Data range → Use named range → Select **`NR_TODAY_TABLE`**
4. Map columns:
   - X-axis: Column A (SP)
   - Series: Columns B-O (SSP, SBP, Demand_MW, etc.)

**The range auto-updates daily** — your chart never needs manual range edits!

## 🔄 Run Modes

### Local CLI
```bash
# Today (auto-detects Europe/London timezone)
make today

# Specific date
python tools/refresh_live_dashboard.py --date 2025-10-09
```

### VS Code Debug
Press F5 or use Run & Debug panel:
- **"Refresh Live Dashboard (today)"** - Runs with current date
- **"Refresh Live Dashboard (custom date)"** - Prompts for date

### GitHub Action (Automated)
Enable the workflow in `.github/workflows/refresh-dashboard.yml`:

1. Add repository secrets:
   - `SA_JSON_B64`: Base64-encoded service account JSON
     ```bash
     cat inner-cinema-credentials.json | base64 | pbcopy
     ```
   - `SHEET_ID`: Your Google Sheet ID

2. Enable workflow:
   - Go to Actions tab → Select "Refresh Live Dashboard" → Enable
   - Runs every 5 minutes automatically
   - Can also trigger manually via "Run workflow" button

## 🔧 Configuration

### Environment Variables (.env)
```bash
GOOGLE_APPLICATION_CREDENTIALS=/path/to/inner-cinema-credentials.json
SHEET_ID=1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA
```

### BigQuery Tables Used
- `inner-cinema-476211-u9.uk_energy_prod.bmrs_mid`
- `inner-cinema-476211-u9.uk_energy_prod.bmrs_indgen_iris`
- `inner-cinema-476211-u9.uk_energy_prod.bmrs_boalf`
- `inner-cinema-476211-u9.uk_energy_prod.bmrs_bod`
- `inner-cinema-476211-u9.uk_energy_prod.bmrs_interconnectors`

### BigQuery Views (Optional)
Create helper views for extended analytics:
```bash
make views
```

Creates: `uk_energy_ops.v_bod_boalf_sp` (joined BOD/BOALF by day + SP)

## 📦 Project Structure

```
overarch-jibber-jabber/
├─ tools/
│  ├─ refresh_live_dashboard.py   # Main refresh script
│  ├─ bigquery_views.sql          # Optional BQ views
│  └─ __init__.py
├─ .github/
│  └─ workflows/
│     └─ refresh-dashboard.yml    # GitHub Action schedule
├─ .vscode/
│  └─ launch.json                 # VS Code debug config
├─ requirements.txt               # Python dependencies
├─ .env.sample                    # Template for .env
├─ .env                          # Your config (git-ignored)
├─ Makefile                       # Convenience commands
└─ README_DASHBOARD.md            # This file
```

## 🎓 Technical Details

### Data Freshness
- **Source**: BigQuery tables updated by your existing extraction pipeline
- **Refresh**: Every 5 minutes (GitHub Action) or on-demand (CLI/VS Code)
- **Timezone**: Europe/London (handles GMT/BST automatically)

### Named Range Benefits
- Chart remains bound even when data updates
- No "range not found" errors
- Easy to reference in formulas: `=VLOOKUP(A2, NR_TODAY_TABLE, 3, FALSE)`

### Performance
- Queries ~48-50 rows per table (one day's settlement periods)
- Typical execution: 5-10 seconds
- Minimal BigQuery cost (scanning small date ranges)

## 🐛 Troubleshooting

### "SHEET_ID not found"
```bash
# Verify .env file exists and has correct SHEET_ID
cat .env | grep SHEET_ID
```

### "Credentials error"
```bash
# Verify service account path
ls -l $GOOGLE_APPLICATION_CREDENTIALS

# Check service account has Sheets API access
# Go to Google Cloud Console → IAM → Service Account → Enable Sheets API
```

### "No data returned"
```bash
# Check if data exists for date
bq query --use_legacy_sql=false "
SELECT COUNT(*) 
FROM \`inner-cinema-476211-u9.uk_energy_prod.bmrs_mid\`
WHERE DATE(settlement_date) = '2025-11-06'
"
```

### GitHub Action fails
- Check secrets are set correctly (Settings → Secrets → Actions)
- Verify SA_JSON_B64 is valid base64: `echo "$SA_JSON_B64" | base64 -d | jq .`
- Check workflow logs for specific error

## 🔐 Security Notes

- **Never commit** `.env` or service account JSON files
- `.gitignore` should include: `.env`, `*.json` (credentials)
- GitHub secrets are encrypted and only accessible during workflow runs
- Service account should have minimal permissions:
  - BigQuery: `roles/bigquery.jobUser`, `roles/bigquery.dataViewer`
  - Sheets: Edit access to specific sheet only

## 📊 VLP-Battery Analysis Integration

This dashboard complements the VLP-Battery analysis (see `VLP_BATTERY_ANALYSIS_SUMMARY.md`):
- **VLP data**: Historical analysis of battery market participation
- **Live dashboard**: Real-time balancing mechanism data
- **Combined insight**: See how VLP-operated batteries respond to SSP/SBP signals

Example use case: Correlate high SSP periods with battery discharge activity in BOD/BOALF data.

## 🚀 Next Steps

1. **Enable GitHub Action** for automated refresh
2. **Create chart** using `NR_TODAY_TABLE` range
3. **Add formulas** to calculate derived metrics (e.g., net imbalance, price spread)
4. **Extend with historical data** by adding date selector and multi-day views

---

**Need help?** Check existing scripts in the repo or create an issue.

**Want to contribute?** Submit a PR with improvements or additional data sources!

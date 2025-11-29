# Dashboard V2 - Final Setup Instructions

**Status:** Apps Script deployed ✅  
**Dashboard:** https://docs.google.com/spreadsheets/d/1LmMq4OEE639Y-XXpOJ3xnvpAmHB6vUovh5g6gaU_vzc/

---

## 🚀 COMPLETE THE SETUP (3 Easy Steps)

### Step 1: Open Dashboard
The dashboard should already be open in your browser. If not:
```
https://docs.google.com/spreadsheets/d/1LmMq4OEE639Y-XXpOJ3xnvpAmHB6vUovh5g6gaU_vzc/
```

### Step 2: Find the Menu
Look at the top menu bar for: **⚡ Dashboard Controls**

*If you don't see it:*
- Refresh the page (Cmd+R or F5)
- Wait 5 seconds for the script to load
- The menu will appear next to Help

### Step 3: Apply Orange Theme
1. Click: **⚡ Dashboard Controls**
2. Select: **🎨 Apply Orange Theme**
3. Wait 3-5 seconds
4. You'll see a success message

---

## ✅ What This Does

The Apps Script will automatically:

### 🎨 Orange Theme
- Title bar: #FF8C00 (orange)
- Filter bar: #F5F5F5 (gray) 
- KPI strip: Light orange
- Table headers: Color-coded sections

### 📊 Chart Zones (Properly Positioned)
- **A20:F40** - Fuel Mix Pie
- **G20:L40** - Interconnector Flows
- **A45:F65** - Demand vs Generation
- **G45:L65** - System Prices
- **A70:L88** - Financial KPIs

### ⚠️ Top 12 Outages Section
- **Rows 90-105** - Outages table
- Red header with white text
- Column headers: BM Unit, Plant, Fuel, MW Lost, etc.

### 🔽 Data Validations
- **B3** - Time range dropdown (Real-Time, 24h, 48h, 7d, 30d)
- **D3** - Region dropdown (All GB + 14 DNO/GSP regions)
- **F3** - Alert filter (All, Critical, etc.)
- **H3** - Start date picker (calendar)
- **J3** - End date picker (calendar)

### 🎨 Conditional Formatting
- Outages >500 MW: Red background (#E53935)
- Generation >5000 MW: Green background (#43A047)

### 🗑️ Cleanup
- Removes: "ESO INTERVENTIONS"
- Removes: "MARKET IMPACT ANALYSIS"
- Removes: "FORECAST ACCURACY"
- Clears all conflicting rows

---

## 📋 After Setup - Verify

1. **Title Bar** - Should be orange with white text
2. **Row 3** - Gray filter bar with dropdowns visible
3. **Row 20, 45, 70** - Chart zone headers (orange text on cream background)
4. **Row 90** - Red "TOP 12 OUTAGES" header
5. **H3 & J3** - Click to see calendar date pickers
6. **No "ESO INTERVENTIONS" anywhere**

---

## 🔧 If Something Goes Wrong

### Menu Doesn't Appear
1. Refresh page
2. Check browser console (F12) for errors
3. Re-deploy script:
   ```bash
   cd ~/GB-Power-Market-JJ/new-dashboard
   clasp push --force
   ```

### Script Runs But Formatting Is Wrong
1. Close and reopen the spreadsheet
2. Run again: ⚡ Dashboard Controls → 🎨 Apply Orange Theme
3. Hard refresh: Cmd+Shift+R (Mac) or Ctrl+Shift+R (Windows)

### Date Pickers Don't Work
- They're set up automatically by the script
- Click cells H3 and J3 - should see calendar icon
- If not, check Data → Data validation menu

---

## 📁 Files Deployed

| File | Location | Purpose |
|------|----------|---------|
| `UpdateDashboard.gs` | Appended to Code.gs | Main setup script |
| `Code.gs` | Google Apps Script | Combined functions |
| `appsscript.json` | Google Apps Script | Config |

---

## 🔄 Automation Status

All automation continues running:

| Script | Frequency | Target |
|--------|-----------|--------|
| `realtime_dashboard_updater.py` | 5 min | Rows 10-18, Row 2 |
| `update_summary_for_chart.py` | 5 min | Rows 10-18 |
| `update_iris_dashboard.py` | 5 min | Rows 10-18 |
| `clear_outages_section.py` | 10 min | Rows 93-104 |

**Chart zones (20-88) are now protected** from automation conflicts.

---

## 🎯 Next Steps (Optional)

### 1. Add Charts
Use the marked zones to insert charts:
- Insert → Chart
- Select data range
- Choose chart type from CHART_SPECS.md
- Position in designated zone

### 2. Configure Outages Data
Fix the BigQuery query in `update_outages_for_v2.py`:
- Schema uses `bmUnit`, not `mep`
- Query `balancing_physical_mels` correctly
- Join with `all_generators` for names

### 3. Interactive Map
Implement Energy_Map using:
- Google Maps API, or
- Data Studio embed, or
- Custom Apps Script visualization

---

## 📞 Support

**Files to check:**
- `DASHBOARD_V2_STATUS.md` - Complete status
- `CHART_SPECS.md` - Chart specifications
- `logs/` - Automation logs

**Common commands:**
```bash
# View automation logs
tail -50 ~/GB-Power-Market-JJ/logs/*.log

# Check cron jobs
crontab -l

# Redeploy Apps Script
cd ~/GB-Power-Market-JJ/new-dashboard && clasp push --force

# Test date pickers
python3 ~/GB-Power-Market-JJ/trigger_dashboard_setup.py
```

---

**🎨 Dashboard V2 with Orange Theme - Ready to Complete!**

Just click the menu and run the setup. Everything is automated.

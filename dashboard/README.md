# 📊 Dashboard Git Management & Improvement Guide

**Project:** GB Power Market JJ  
**Dashboard:** https://docs.google.com/spreadsheets/d/1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA/edit  
**Date:** November 9, 2025  
**Status:** ✅ Operational with Improvements Available

---

## 🎯 Overview

This document explains how to maintain the dashboard in Git and implement improvements for real-time data updates with charts.

---

## 📁 Repository Structure

```
GB Power Market JJ/
├── dashboard/
│   ├── README.md                          # This file
│   ├── GITMORE.md                         # Git workflows & best practices
│   ├── DASHBOARD_IMPROVEMENT_PLAN.md      # Improvement roadmap
│   │
│   ├── apps-script/
│   │   ├── google_sheets_dashboard_v2.gs  # ✅ Current production
│   │   ├── dashboard_charts_v2.gs         # ✅ Chart automation
│   │   └── Code.gs                        # Deployment version
│   │
│   ├── python-updaters/
│   │   ├── realtime_dashboard_updater.py  # ✅ 5-min auto-refresh
│   │   ├── update_analysis_bi_enhanced.py # ✅ Main updater
│   │   └── enhance_dashboard_layout.py    # ✅ Layout formatter
│   │
│   └── docs/
│       ├── DASHBOARD_QUICKSTART.md
│       ├── DASHBOARD_SETUP_COMPLETE.md
│       └── APPS_SCRIPT_QUICK_REF.md
```

---

## 🔄 Current Implementation

### What's Already Working ✅

1. **Real-Time Data Updates**
   - Auto-refresh every 5 minutes (cron job)
   - Python script: `realtime_dashboard_updater.py`
   - Manual refresh: `update_analysis_bi_enhanced.py`

2. **Data Source**
   - BigQuery: `inner-cinema-476211-u9.uk_energy_prod`
   - Historical + IRIS (real-time) data combined
   - Always current data from SP 1 (00:00)

3. **Charts Available**
   - Apps Script: `dashboard_charts_v2.gs`
   - Line chart: 24h generation trend
   - Pie chart: Current generation mix
   - Area chart: Stacked generation
   - Column chart: Top sources

4. **Dashboard Sheets**
   - **Dashboard**: Main view with KPIs and metrics
   - **Live Dashboard**: 48 settlement periods (00:00-23:30)
   - **Chart Data**: Hidden sheet for chart data
   - **Live_Raw_Gen**: Raw generation data
   - **Calendar**: Daily price calendar

---

## 🎯 Improvement Goals

### 1. **Always Start from SP 0 (00:00)** ✅
**Status:** Already implemented  
**Code:** `google_sheets_dashboard_v2.gs` line 150+

```javascript
// Settlement periods always start from SP 1 (00:00)
for (let sp=1; sp<=48; sp++) {
  idx[sp] = { 
    sp,           // Settlement Period 1-48
    time: spToClock(sp),  // 00:00 - 23:30
    // ... data
  };
}
```

### 2. **Always Current Data** ✅
**Status:** Auto-refresh every 5 minutes  
**Files:**
- `realtime_dashboard_updater.py` (runs via cron)
- Cron job: `*/5 * * * * cd ~/GB\ Power\ Market\ JJ && python3 realtime_dashboard_updater.py`

**Query Strategy:**
```sql
-- Combines historical + real-time IRIS data
WITH combined AS (
  SELECT * FROM bmrs_fuelinst
  WHERE settlementDate < CURRENT_DATE()
  UNION ALL
  SELECT * FROM bmrs_fuelinst_iris
  WHERE settlementDate >= DATE_SUB(CURRENT_DATE(), INTERVAL 2 DAY)
)
```

### 3. **Keep Current Formatting** ✅
**Status:** Formatting preserved  
**Code:** `enhance_dashboard_layout.py`

Features:
- Professional emoji icons (⚡🔋💰📊)
- Color-coded sections
- KPI metrics at top
- Generation mix table
- Status indicators (🟢 Active / 🔴 Offline)

### 4. **Add Interactive Charts** ⚠️ Needs Deployment
**Status:** Code exists, needs installation  
**File:** `dashboard_charts_v2.gs`

**What it creates:**
- ⚡ 24-Hour Generation Trend (Line chart)
- 🥧 Current Generation Mix (Pie chart)
- 📊 Stacked Generation (Area chart)
- 📈 Top Sources (Column chart)

---

## 🚀 Implementation Plan

### Phase 1: Code Organization (✅ Complete)
- [x] Consolidate dashboard scripts
- [x] Document existing functionality
- [x] Create this gitmore.md guide

### Phase 2: Chart Deployment (🟡 Ready to Deploy)
- [ ] Install `dashboard_charts_v2.gs` to Apps Script
- [ ] Verify charts auto-update with data
- [ ] Test on live dashboard

### Phase 3: Enhanced Monitoring (🔵 Future)
- [ ] Add data freshness indicator
- [ ] Settlement period progress bar
- [ ] Price alerts for high volatility

---

## 📖 How to Use This Documentation

### For Daily Operations
1. **Check dashboard status:** Open dashboard URL
2. **Manual refresh:** Run `./update_dashboard.sh`
3. **View logs:** `tail -f logs/dashboard_updater.log`

### For Development
1. **Read:** `GITMORE.md` for Git workflows
2. **Edit:** Apps Script files in `dashboard/apps-script/`
3. **Test:** Use `DASHBOARD_QUICKSTART.md` test procedures
4. **Deploy:** Follow `APPS_SCRIPT_DEPLOYMENT_GUIDE.md`

### For Troubleshooting
1. **Check:** `DASHBOARD_CRASH_FIXED.md`
2. **Review:** `RECURRING_ISSUE_SOLUTION.md`
3. **Debug:** `check_dashboard_script.py`

---

## 🔧 Key Scripts Reference

### Python Scripts

| Script | Purpose | Run Frequency |
|--------|---------|---------------|
| `realtime_dashboard_updater.py` | Auto-refresh dashboard | Every 5 min (cron) |
| `update_analysis_bi_enhanced.py` | Manual full update | On-demand |
| `enhance_dashboard_layout.py` | Format/layout dashboard | After structure changes |
| `deploy_dashboard_charts.py` | Deploy charts to Apps Script | One-time setup |

### Apps Script Files

| File | Purpose | Location |
|------|---------|----------|
| `google_sheets_dashboard_v2.gs` | Main dashboard logic | Apps Script Editor |
| `dashboard_charts_v2.gs` | Chart creation & management | Apps Script Editor |
| `gb_energy_dashboard_apps_script.gs` | Legacy (reference only) | Archive |

---

## 🎨 Dashboard Layout

### Current Structure

```
┌─────────────────────────────────────────────────────────┐
│ 🔋 GB POWER MARKET - LIVE DASHBOARD                     │
│ Last Updated: 2025-11-09 17:00 | SP: 34                 │
├─────────────────────────────────────────────────────────┤
│ 📊 CURRENT METRICS          💰 MARKET PRICES            │
│ Total Generation: 45,234 MW  Sell Price: £67.43/MWh    │
│ Renewable Share: 54.3%       Renewable MW: 24,562 MW   │
├─────────────────────────────────────────────────────────┤
│ ⚡ GENERATION MIX                                        │
│ Fuel Type        | MW      | %    | Status             │
│ 💨 Wind          | 15,234  | 33.7%| 🟢 Active          │
│ ☀️ Solar         | 2,456   | 5.4% | 🟢 Active          │
│ ⚛️ Nuclear       | 6,789   | 15.0%| 🟢 Active          │
│ 🔥 Gas           | 12,345  | 27.3%| 🟢 Active          │
│ ...                                                      │
└─────────────────────────────────────────────────────────┘

[Charts appear on the right side → Column H onwards]
```

---

## 🔐 Git Best Practices

### Branching Strategy
```bash
# Main branch: production code
git checkout main

# Feature branches for improvements
git checkout -b feature/dashboard-improvements

# Hotfix branches for urgent fixes
git checkout -b hotfix/data-refresh-issue
```

### Commit Messages
```bash
# Good commit messages
git commit -m "feat(dashboard): Add real-time settlement period updates"
git commit -m "fix(charts): Correct data range for generation mix pie chart"
git commit -m "docs(dashboard): Update gitmore.md with chart deployment steps"

# Commit types:
# feat: New feature
# fix: Bug fix
# docs: Documentation
# refactor: Code improvement
# test: Tests
# chore: Maintenance
```

### File Organization
```bash
# Keep dashboard files organized
dashboard/
├── apps-script/     # Google Apps Script files
├── python-updaters/ # Python update scripts
├── docs/            # Documentation
└── tests/           # Test scripts

# Don't commit:
- *.pickle (auth tokens)
- *credentials*.json (secrets)
- logs/*.log (runtime logs)
```

---

## 📊 Data Flow Diagram

```
┌─────────────┐
│  BigQuery   │
│ Historical  │
│ bmrs_*      │
└──────┬──────┘
       │
       ├─────────┐
       │         │
       ▼         ▼
┌─────────┐ ┌─────────┐
│ BigQuery│ │ BigQuery│
│  IRIS   │ │ Combined│
│bmrs_*   │ │  Query  │
│_iris    │ └────┬────┘
└─────────┘      │
                 ▼
         ┌──────────────┐
         │ Python       │
         │ Updater      │
         │ (5-min cron) │
         └──────┬───────┘
                │
                ▼
         ┌──────────────┐
         │ Google       │
         │ Sheets API   │
         └──────┬───────┘
                │
                ▼
         ┌──────────────┐
         │ Dashboard    │
         │ 12jY0d4j...  │
         └──────┬───────┘
                │
                ▼
         ┌──────────────┐
         │ Apps Script  │
         │ Charts       │
         └──────────────┘
```

---

## 🎯 Next Steps

### Immediate Actions
1. **Deploy Charts** (10 minutes)
   ```bash
   cd ~/GB\ Power\ Market\ JJ
   python3 deploy_dashboard_charts.py
   ```
   Or manually:
   - Open: https://docs.google.com/spreadsheets/d/1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA/
   - Extensions → Apps Script
   - Copy `dashboard_charts_v2.gs` → Save
   - Run `createDashboardCharts()`

2. **Verify Auto-Refresh** (5 minutes)
   ```bash
   # Check cron job is running
   crontab -l | grep dashboard
   
   # Check recent logs
   tail -f logs/dashboard_updater.log
   ```

3. **Test Manual Update** (2 minutes)
   ```bash
   python3 update_analysis_bi_enhanced.py
   ```

### Documentation Tasks
- [x] Create gitmore.md
- [ ] Update DASHBOARD_QUICKSTART.md with new features
- [ ] Document chart customization options
- [ ] Create video walkthrough

---

## 🔗 Related Documentation

### Essential Reads
1. **[PROJECT_CONFIGURATION.md](../PROJECT_CONFIGURATION.md)** - BigQuery setup
2. **[STOP_DATA_ARCHITECTURE_REFERENCE.md](../STOP_DATA_ARCHITECTURE_REFERENCE.md)** - Data schema
3. **[APPS_SCRIPT_QUICK_REF.md](../APPS_SCRIPT_QUICK_REF.md)** - Apps Script guide

### Dashboard Docs
4. **[DASHBOARD_QUICKSTART.md](../DASHBOARD_QUICKSTART.md)** - Quick start
5. **[DASHBOARD_SETUP_COMPLETE.md](../DASHBOARD_SETUP_COMPLETE.md)** - Full setup
6. **[ENHANCED_DASHBOARD_GUIDE.md](../ENHANCED_DASHBOARD_GUIDE.md)** - Features

### Troubleshooting
7. **[DASHBOARD_CRASH_FIXED.md](../DASHBOARD_CRASH_FIXED.md)** - Known issues
8. **[RECURRING_ISSUE_SOLUTION.md](../RECURRING_ISSUE_SOLUTION.md)** - Common problems

---

## 💡 Tips & Tricks

### Quick Dashboard Checks
```bash
# Is dashboard updating?
curl -s "https://docs.google.com/spreadsheets/d/1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA/export?format=csv&gid=0" | head

# Check BigQuery data freshness
python3 -c "from google.cloud import bigquery; client = bigquery.Client(project='inner-cinema-476211-u9'); print(client.query('SELECT MAX(settlementDate) FROM uk_energy_prod.bmrs_fuelinst_iris').to_dataframe())"

# Verify cron job
ps aux | grep dashboard_updater
```

### Common Issues

**Issue:** Dashboard shows old data  
**Fix:** Check cron job is running, manually run updater

**Issue:** Charts not appearing  
**Fix:** Redeploy `dashboard_charts_v2.gs` via Apps Script

**Issue:** "No data" errors  
**Fix:** Verify BigQuery project ID is `inner-cinema-476211-u9`

---

## 📞 Support

**Repository:** https://github.com/GeorgeDoors888/GB-Power-Market-JJ  
**Dashboard:** https://docs.google.com/spreadsheets/d/1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA/  
**Maintainer:** George Major (george@upowerenergy.uk)

---

**Last Updated:** November 9, 2025  
**Status:** ✅ Active & Operational

# 📈 Dashboard Improvement Plan - Implementation Guide

**Project:** GB Power Market JJ Dashboard  
**Dashboard URL:** https://docs.google.com/spreadsheets/d/1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA/edit  
**Date:** November 9, 2025  
**Status:** 🟢 Ready to Implement

---

## 🎯 Improvement Goals

### 1. Always Start from SP 0 (00:00) ✅
**Current Status:** Already implemented  
**Implementation:** `google_sheets_dashboard_v2.gs`

### 2. Always Current Data ✅  
**Current Status:** Auto-refresh every 5 minutes  
**Implementation:** `realtime_dashboard_updater.py` + cron

### 3. Keep Existing Format ✅
**Current Status:** Professional formatting maintained  
**Implementation:** `enhance_dashboard_layout.py`

### 4. Add Interactive Charts 🟡
**Current Status:** Code exists, needs deployment  
**Implementation:** Deploy `dashboard_charts_v2.gs`

---

## 📊 Current Implementation Status

| Feature | Status | Script | Notes |
|---------|--------|--------|-------|
| SP 0 (00:00) Start | ✅ Live | `google_sheets_dashboard_v2.gs` | Settlement periods 1-48 |
| Real-time Data | ✅ Live | `realtime_dashboard_updater.py` | Updates every 5 min |
| Current SP Indicator | ✅ Live | `enhance_dashboard_layout.py` | Shows current period |
| Professional Layout | ✅ Live | `enhance_dashboard_layout.py` | Emoji icons, colors |
| Generation Mix Table | ✅ Live | `update_analysis_bi_enhanced.py` | Fuel types with % |
| KPI Metrics | ✅ Live | `enhance_dashboard_layout.py` | Total gen, renewable % |
| Interactive Charts | 🟡 Ready | `dashboard_charts_v2.gs` | Needs deployment |
| Chart Auto-Update | 🟡 Ready | Built-in | Charts update with data |

---

## 🚀 Implementation Steps

### Step 1: Verify Current Setup ✅

```bash
# Check cron job is running
crontab -l | grep dashboard

# Expected output:
# */5 * * * * cd ~/GB\ Power\ Market\ JJ && python3 realtime_dashboard_updater.py >> logs/dashboard_cron.log 2>&1

# Check recent updates
tail -20 logs/dashboard_updater.log

# Verify dashboard is accessible
curl -s "https://docs.google.com/spreadsheets/d/1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA/export?format=csv&gid=0" | head
```

### Step 2: Deploy Charts (Main Task)

#### Option A: Automatic Deployment (Recommended)

```bash
cd ~/GB\ Power\ Market\ JJ

# Run deployment script
python3 dashboard/python-updaters/deploy_dashboard_charts.py

# This will:
# 1. Read dashboard_charts_v2.gs
# 2. Connect to Google Sheets API
# 3. Deploy to Apps Script
# 4. Create charts
# 5. Verify installation
```

#### Option B: Manual Deployment (If automatic fails)

1. **Open Apps Script Editor:**
   ```
   https://docs.google.com/spreadsheets/d/1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA/edit
   → Extensions → Apps Script
   ```

2. **Copy Chart Code:**
   ```bash
   # Display code to copy
   cat dashboard/apps-script/dashboard_charts_v2.gs
   ```

3. **Paste and Save:**
   - Paste into Code.gs (or create new file)
   - Save (Ctrl+S or Cmd+S)

4. **Run Chart Creation:**
   - Select function: `createDashboardCharts`
   - Click Run (▶️)
   - Grant permissions when prompted

5. **Verify:**
   - Return to spreadsheet
   - Check for charts on Dashboard sheet
   - Verify charts update when data changes

### Step 3: Configure Chart Menu

```bash
# The charts script includes menu items
# After deployment, you'll see:
# "📊 Dashboard" menu → "🔄 Refresh Charts"
```

### Step 4: Test Everything

```bash
# 1. Force a data update
python3 update_analysis_bi_enhanced.py

# 2. Open dashboard
open "https://docs.google.com/spreadsheets/d/1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA/edit"

# 3. Verify:
# ✅ Data shows current settlement period
# ✅ Starts from SP 1 (00:00)
# ✅ Charts are visible
# ✅ Charts show correct data
# ✅ Layout is preserved
```

---

## 📋 Detailed Feature Specifications

### Feature 1: Settlement Period 0 (00:00) Start Point

**Requirement:** Data always starts from midnight (SP 1 = 00:00)

**Implementation:**
```javascript
// google_sheets_dashboard_v2.gs
function spToClock(sp) {
  // SP1=00:00, SP2=00:30 ... SP48=23:30
  const zeroIdx = sp - 1;
  const hh = Math.floor(zeroIdx / 2);
  const mm = (zeroIdx % 2) ? '30' : '00';
  return String(hh).padStart(2,'0') + ':' + mm;
}

// Build data rows for SP 1-48
for (let sp=1; sp<=48; sp++) {
  rows.push([
    sp,                    // Settlement Period 1-48
    spToClock(sp),        // Time: 00:00 - 23:30
    idx[sp].ssp || null,  // System Sell Price
    idx[sp].sbp || null,  // System Buy Price
    // ... other data
  ]);
}
```

**Verification:**
- ✅ Row 2 = SP 1 = 00:00
- ✅ Row 49 = SP 48 = 23:30
- ✅ No gaps in sequence

---

### Feature 2: Always Current Data

**Requirement:** Dashboard shows latest available data, updated every 5 minutes

**Implementation:**

**Python Updater (realtime_dashboard_updater.py):**
```python
# Combines historical + IRIS real-time data
query = f"""
WITH combined_generation AS (
  -- Historical data (before today)
  SELECT 
    CAST(settlementDate AS DATE) as date,
    settlementPeriod as sp,
    fuelType,
    SUM(generation) as total_generation
  FROM `{PROJECT_ID}.{DATASET}.bmrs_fuelinst`
  WHERE CAST(settlementDate AS DATE) < CURRENT_DATE()
  GROUP BY date, sp, fuelType
  
  UNION ALL
  
  -- Real-time IRIS data (last 48 hours)
  SELECT 
    CAST(settlementDate AS DATE) as date,
    settlementPeriod as sp,
    fuelType,
    SUM(generation) as total_generation
  FROM `{PROJECT_ID}.{DATASET}.bmrs_fuelinst_iris`
  WHERE CAST(settlementDate AS DATE) >= DATE_SUB(CURRENT_DATE(), INTERVAL 2 DAY)
  GROUP BY date, sp, fuelType
)
SELECT * FROM combined_generation
WHERE date = CURRENT_DATE()
ORDER BY sp
"""
```

**Cron Configuration:**
```bash
# Edit crontab
crontab -e

# Add this line (updates every 5 minutes)
*/5 * * * * cd ~/GB\ Power\ Market\ JJ && python3 realtime_dashboard_updater.py >> logs/dashboard_cron.log 2>&1
```

**Verification:**
- ✅ Dashboard header shows "Last Updated: [timestamp]"
- ✅ Current settlement period highlighted
- ✅ Data never more than 5 minutes old
- ✅ Missing SPs show as null (not blank)

---

### Feature 3: Maintain Current Formatting

**Requirement:** Keep professional appearance with emoji icons, colors, and layout

**Implementation (enhance_dashboard_layout.py):**

```python
# Header with emoji and current info
layout_data.append([
    '🔋 GB POWER MARKET - LIVE DASHBOARD', 
    '', '', '', '', ''
])
layout_data.append([
    f'Last Updated: {current_time} | Settlement Period: {current_sp}',
    '', '', '', '', ''
])

# KPI metrics with icons
layout_data.append([
    '📊 CURRENT METRICS', 
    '', '', 
    '💰 MARKET PRICES', 
    '', ''
])

# Fuel type emojis
fuel_emojis = {
    'WIND': '💨',
    'SOLAR': '☀️',
    'NUCLEAR': '⚛️',
    'GAS': '🔥',
    'COAL': '⛏️',
    'HYDRO': '💧',
    'BIOMASS': '🌱',
    'OTHER': '⚡'
}

# Status indicators
status = '🟢 Active' if mw > 0 else '🔴 Offline'
```

**Color Scheme:**
```python
# Headers: Dark blue
{'backgroundColor': {'red': 0.102, 'green': 0.137, 'blue': 0.494}}

# KPIs: Light blue
{'backgroundColor': {'red': 0.667, 'green': 0.816, 'blue': 0.906}}

# Data rows: Alternating white/light gray
{'backgroundColor': {'red': 0.95, 'green': 0.95, 'blue': 0.95}}
```

**Verification:**
- ✅ Emoji icons display correctly
- ✅ Colors match design
- ✅ Layout is responsive
- ✅ No formatting breaks on data update

---

### Feature 4: Interactive Charts

**Requirement:** Auto-updating charts that visualize generation mix and trends

**Chart Types:**

#### Chart 1: Line Chart - 24-Hour Generation Trend
```javascript
const lineChart = dashboard.newChart()
  .setChartType(Charts.ChartType.LINE)
  .addRange(dashboard.getRange('ChartData!A2:F49'))  // SP 1-48
  .setPosition(1, 8, 0, 0)  // Row 1, Column H
  .setOption('title', '⚡ 24-Hour Generation Trend')
  .setOption('width', 600)
  .setOption('height', 400)
  .setOption('hAxis', {
    title: 'Settlement Period', 
    slantedText: true
  })
  .setOption('vAxis', {
    title: 'Generation (MW)'
  })
  .setOption('series', {
    0: {color: '#1e88e5', lineWidth: 2}, // Wind
    1: {color: '#fdd835', lineWidth: 2}, // Solar
    2: {color: '#43a047', lineWidth: 2}, // Nuclear
    3: {color: '#e53935', lineWidth: 2}  // Gas
  })
  .build();
```

#### Chart 2: Pie Chart - Current Generation Mix
```javascript
const pieChart = dashboard.newChart()
  .setChartType(Charts.ChartType.PIE)
  .addRange(dashboard.getRange('Dashboard!A11:B30'))
  .setPosition(1, 17, 0, 0)  // Row 1, Column Q
  .setOption('title', '🥧 Current Generation Mix')
  .setOption('pieSliceText', 'percentage')
  .setOption('is3D', true)
  .build();
```

#### Chart 3: Stacked Area Chart
```javascript
const areaChart = dashboard.newChart()
  .setChartType(Charts.ChartType.AREA)
  .addRange(dashboard.getRange('ChartData!A2:E49'))
  .setPosition(26, 8, 0, 0)  // Row 26, Column H
  .setOption('title', '📊 Stacked Generation by Source')
  .setOption('isStacked', true)
  .build();
```

#### Chart 4: Column Chart - Top 10 Sources
```javascript
const columnChart = dashboard.newChart()
  .setChartType(Charts.ChartType.COLUMN)
  .addRange(dashboard.getRange('Dashboard!A11:B20'))
  .setPosition(26, 17, 0, 0)  // Row 26, Column Q
  .setOption('title', '📈 Top 10 Generation Sources')
  .build();
```

**Chart Auto-Update:**
- Charts bound to named ranges: `ChartData!A2:F49`
- When data updates, charts refresh automatically
- No manual refresh needed

**Verification:**
- ✅ 4 charts visible on Dashboard sheet
- ✅ Charts show correct data
- ✅ Charts update when data refreshes
- ✅ Charts positioned correctly (don't overlap data)
- ✅ Colors match theme

---

## 🧪 Testing Checklist

### Pre-Deployment Tests
- [ ] Python scripts run without errors
- [ ] BigQuery queries return data
- [ ] Apps Script syntax is valid
- [ ] Credentials are configured
- [ ] Cron job is active

### Post-Deployment Tests
- [ ] Dashboard opens without errors
- [ ] Data starts from SP 1 (00:00)
- [ ] Current settlement period is correct
- [ ] All 4 charts are visible
- [ ] Charts show data (not blank)
- [ ] Layout is preserved
- [ ] Colors and emojis display correctly
- [ ] Auto-refresh works (wait 5 minutes, check logs)
- [ ] Manual refresh works (`python3 update_analysis_bi_enhanced.py`)

### Performance Tests
- [ ] Dashboard loads in <3 seconds
- [ ] Data refresh completes in <30 seconds
- [ ] Charts render smoothly
- [ ] No console errors in browser
- [ ] No Python errors in logs

---

## 🔧 Troubleshooting Guide

### Issue: Charts Not Appearing

**Symptoms:** Dashboard shows data but no charts

**Solutions:**
```bash
# 1. Verify Apps Script is deployed
# Open: Extensions → Apps Script
# Check: dashboard_charts_v2.gs code is present

# 2. Re-run chart creation
# Apps Script Editor → Run → createDashboardCharts()

# 3. Check for errors
# Apps Script Editor → View → Logs

# 4. Verify data range
# Check ChartData sheet exists and has data
```

### Issue: Data Not Updating

**Symptoms:** Dashboard shows old timestamp

**Solutions:**
```bash
# 1. Check cron job is running
crontab -l | grep dashboard
ps aux | grep realtime_dashboard_updater.py

# 2. Check logs for errors
tail -50 logs/dashboard_updater.log
tail -50 logs/dashboard_cron.log

# 3. Run manual update
python3 realtime_dashboard_updater.py

# 4. Verify BigQuery access
python3 -c "from google.cloud import bigquery; client = bigquery.Client(project='inner-cinema-476211-u9'); print('OK')"
```

### Issue: Wrong Settlement Period

**Symptoms:** Current SP indicator shows wrong period

**Solutions:**
```bash
# 1. Check system time
date

# 2. Verify timezone
echo $TZ
# Should be: Europe/London or UTC

# 3. Update timezone in script
# Edit realtime_dashboard_updater.py
# Set: TZ = 'Europe/London'

# 4. Recalculate SP
# SP = (hour * 2) + (1 if minute >= 30 else 0) + 1
```

### Issue: Formatting Broken

**Symptoms:** Layout is messed up, colors missing

**Solutions:**
```bash
# 1. Re-run layout formatter
python3 dashboard/python-updaters/enhance_dashboard_layout.py

# 2. Check for merge conflicts
git status
git diff

# 3. Restore from backup
# (Google Sheets has version history)
# File → Version history → See version history

# 4. Re-apply formatting
# Run: python3 format_dashboard.py
```

---

## 📈 Performance Optimization

### Current Performance Metrics
- Dashboard load time: ~2 seconds
- Data refresh time: ~15 seconds
- Chart render time: <1 second
- Total update cycle: ~20 seconds

### Optimization Opportunities

1. **Query Optimization:**
   ```sql
   -- Add index on settlementDate
   CREATE INDEX idx_settlement_date 
   ON bmrs_fuelinst_iris(settlementDate);
   
   -- Use partitioned tables
   -- (Already partitioned by settlementDate)
   ```

2. **Caching:**
   ```python
   # Cache query results for 5 minutes
   @lru_cache(maxsize=128, ttl=300)
   def get_generation_data(date):
       return bq_client.query(query).to_dataframe()
   ```

3. **Batch Updates:**
   ```python
   # Update all sheets in one API call
   sheet.batch_update([
       {'range': 'Dashboard!A1:F100', 'values': data1},
       {'range': 'ChartData!A1:F49', 'values': data2}
   ])
   ```

---

## 🎓 Maintenance Guide

### Daily Tasks
- [ ] Check dashboard is updating (verify timestamp)
- [ ] Monitor logs for errors: `tail -f logs/dashboard_updater.log`
- [ ] Verify charts are visible and current

### Weekly Tasks
- [ ] Review query performance in BigQuery console
- [ ] Check cron job status: `systemctl status cron`
- [ ] Backup dashboard (File → Download → .xlsx)
- [ ] Test manual refresh: `python3 update_analysis_bi_enhanced.py`

### Monthly Tasks
- [ ] Review and archive old logs: `mv logs/*.log logs/archive/`
- [ ] Update documentation if features added
- [ ] Check for Apps Script API deprecations
- [ ] Optimize slow queries

### Quarterly Tasks
- [ ] Full system audit
- [ ] Update dependencies: `pip install --upgrade -r requirements.txt`
- [ ] Review and update this improvement plan
- [ ] Conduct user feedback session

---

## 📊 Success Metrics

| Metric | Target | Current | Status |
|--------|--------|---------|--------|
| Data Freshness | < 5 min | 5 min | ✅ |
| Dashboard Load Time | < 3 sec | ~2 sec | ✅ |
| Update Success Rate | > 99% | TBD | 🟡 |
| Chart Availability | 100% | 100% (after deployment) | 🟡 |
| User Satisfaction | > 4/5 | TBD | 🟡 |

---

## 🚀 Future Enhancements

### Phase 2 (Next Quarter)
- [ ] Add price alerts (SMS/email when price > threshold)
- [ ] Implement demand forecasting chart
- [ ] Add wind generation prediction overlay
- [ ] Create mobile-responsive view
- [ ] Add export to PDF button

### Phase 3 (Future)
- [ ] Machine learning price predictions
- [ ] Integration with battery optimization
- [ ] Real-time arbitrage opportunity alerts
- [ ] Historical comparison overlays
- [ ] Multi-dashboard support

---

## 📞 Support & Contacts

**Primary Maintainer:** George Major  
**Email:** george@upowerenergy.uk  
**Repository:** https://github.com/GeorgeDoors888/GB-Power-Market-JJ  
**Dashboard:** https://docs.google.com/spreadsheets/d/1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA/

**Escalation:**
1. Check logs: `logs/dashboard_updater.log`
2. Review docs: `dashboard/README.md`
3. Search past issues: GitHub Issues
4. Contact maintainer if unresolved

---

**Last Updated:** November 9, 2025  
**Version:** 2.0  
**Status:** 🟢 Ready for Implementation

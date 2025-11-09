# 📊 Enhanced Dashboard - Quick Reference

## 🎯 One-Liner Summary
Professional Google Sheets dashboard with KPIs, generation mix, trend data, and 4 interactive charts - auto-updating every 5 minutes.

---

## ⚡ Quick Commands

```bash
# Refresh dashboard data + layout
python3 enhance_dashboard_layout.py

# Apply professional formatting
python3 format_dashboard.py

# View dashboard
open "https://docs.google.com/spreadsheets/d/12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8/"

# Check auto-refresh logs
tail -f logs/dashboard_updater.log
```

---

## 📈 Dashboard Sections

| Section | Rows | Content |
|---------|------|---------|
| Header | 1-2 | Title + Last Updated timestamp |
| KPIs | 4-6 | Total Generation, Renewable %, Market Price |
| Generation Mix | 8-30 | Fuel types with MW, %, status indicators |
| Trend Data | 32+ | Last 24h by settlement period (for charts) |

---

## 🎨 Chart Setup (5 Steps)

1. Open: https://docs.google.com/spreadsheets/d/12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8/
2. Extensions → Apps Script
3. Paste `dashboard_charts.gs` content
4. Run: `createDashboardCharts()`
5. Grant permissions → Done!

**Result**: 4 auto-updating charts appear instantly

---

## 📊 Charts Created

| # | Type | Data | Location |
|---|------|------|----------|
| 1 | Line | 24h trend (Wind/Solar/Nuclear/Gas/Total) | H1 |
| 2 | Pie | Current generation mix | Q1 |
| 3 | Area | Stacked generation by source | H26 |
| 4 | Column | Top 15 generation sources | Q26 |

---

## 🔄 Auto-Update Setup

**Current** (every 5 min):
```bash
*/5 * * * * ... python3 realtime_dashboard_updater.py >> logs/dashboard_updater.log 2>&1
```

**Enhanced Dashboard** (every 15 min - optional):
```bash
crontab -e
# Add this line:
*/15 * * * * cd '/Users/georgemajor/GB Power Market JJ' && /usr/local/bin/python3 enhance_dashboard_layout.py >> logs/dashboard_enhance.log 2>&1
```

---

## 🎨 Color Scheme

| Element | Background | Text | Font |
|---------|-----------|------|------|
| Header | #2B4D99 (Blue) | White | 16pt Bold |
| Subheader | #E6E6E6 (Light Gray) | Black | 10pt Italic |
| Section Headers | #4D6699 (Medium Blue) | White | 12pt Bold |
| KPIs (Metrics) | #EDF5FF (Light Blue) | Black | 11pt Bold |
| KPIs (Prices) | #FFF8E1 (Light Yellow) | Black | 11pt Bold |
| Table Headers | #CCCCCC (Gray) | Black | Bold |
| Data Rows | White | Black | Normal |

---

## 🔧 Customization

### Change Chart Colors
Edit `dashboard_charts.gs`:
```javascript
.setOption('series', {
  0: {color: '#1e88e5'}, // Wind (blue)
  1: {color: '#fdd835'}, // Solar (yellow)
  2: {color: '#43a047'}, // Nuclear (green)
  3: {color: '#e53935'}  // Gas (red)
})
```

### Change Data Period
Edit `enhance_dashboard_layout.py`:
```python
# Change from 24h to 48h
WHERE settlementDate >= DATE_SUB(CURRENT_DATE(), INTERVAL 2 DAY)
```

### Add More KPIs
Edit `enhance_dashboard_layout.py`:
```python
layout_data.append([
    f'New Metric: {value}',
    '',
    '',
    f'Another Metric: {value2}',
    '',
    ''
])
```

---

## 🆘 Troubleshooting

| Issue | Solution |
|-------|----------|
| Charts not showing | Re-run `createDashboardCharts()` in Apps Script |
| Old data | `python3 enhance_dashboard_layout.py` |
| Formatting lost | `python3 format_dashboard.py` |
| BigQuery error | Check `inner-cinema-credentials.json` exists |
| Import error | `pip3 install --break-system-packages gspread google-cloud-bigquery` |

---

## 📁 Files Reference

| File | Purpose | When to Use |
|------|---------|-------------|
| `enhance_dashboard_layout.py` | Create/refresh layout + data | Manual refresh or cron |
| `format_dashboard.py` | Apply professional formatting | After layout changes |
| `dashboard_charts.gs` | Google Apps Script for charts | Install once in Apps Script |
| `ENHANCED_DASHBOARD_GUIDE.md` | Full documentation | Complete setup guide |
| `realtime_dashboard_updater.py` | Auto-refresh (existing) | Already running via cron |

---

## 📚 Full Documentation

See: `ENHANCED_DASHBOARD_GUIDE.md` for:
- Complete installation steps
- Detailed customization options
- Advanced troubleshooting
- Next steps & enhancements

---

## 📊 Current Data Stats

- **Generation Sources**: 20 fuel types tracked
- **Trend Data**: Last 24 hours (78 settlement periods)
- **Update Frequency**: Every 5 minutes (auto)
- **Data Source**: BigQuery (inner-cinema-476211-u9.uk_energy_prod)
- **Tables Used**: `bmrs_fuelinst_iris`, `bmrs_mid_iris`

---

## 🎯 Key Features

✅ **Professional Layout** - Color-coded sections, optimized widths  
✅ **Live Data** - Auto-updates every 5 minutes  
✅ **Interactive Charts** - 4 visualizations with drill-down  
✅ **Emoji Icons** - Visual fuel type identification  
✅ **Status Indicators** - 🟢 Active / 🔴 Offline  
✅ **Percentage Calculations** - Automatic renewable share  
✅ **Responsive Design** - Mobile-friendly view  

---

*Quick Reference v1.0 | Last Updated: November 9, 2025*

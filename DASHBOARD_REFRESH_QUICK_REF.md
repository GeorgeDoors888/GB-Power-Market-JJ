# Dashboard Refresh - Quick Reference

**One-Page Guide for GB Power Market Dashboard Data Management**

---

## 🔄 Data Refresh Behavior

| **Question** | **Answer** |
|-------------|-----------|
| Does old data get deleted? | ✅ YES - Completely cleared before each update |
| How is data cleared? | `.clear()` method on both sheets |
| When does clearing happen? | Before every data write |
| Can old data accumulate? | ❌ NO - Impossible due to `.clear()` |
| Do charts need manual update? | ❌ NO - Auto-refresh when data changes |

---

## 📊 Sheet Structure

```
Dashboard (Visible)          ChartData (Hidden)
├─ KPIs (3 metrics)          ├─ Settlement Period
├─ Generation Mix (20)       ├─ Wind, Solar, Nuclear, Gas, Total
└─ 30 rows × 6 cols          └─ 80 rows × 6 cols (48 SPs + header)
     ↓                              ↓
Display to Users           Source for Charts
```

---

## 🚀 Quick Commands

### Manual Refresh
```bash
cd '/Users/georgemajor/GB Power Market JJ'
python3 enhance_dashboard_layout.py
```

### Auto-Refresh Setup (Every 5 min)
```bash
crontab -e
# Add:
*/5 * * * * cd '/Users/georgemajor/GB Power Market JJ' && python3 enhance_dashboard_layout.py >> logs/dashboard_enhance.log 2>&1
```

### Check Logs
```bash
tail -f logs/dashboard_enhance.log
```

### Recreate Charts
```bash
python3 execute_chart_creation.py
# OR open: https://script.google.com/d/[SCRIPT_ID]/edit → Run createDashboardCharts
```

### Hide ChartData (if visible)
```bash
python3 -c "import gspread; gc = gspread.service_account(filename='inner-cinema-credentials.json'); ss = gc.open_by_key('12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8'); cd = ss.worksheet('ChartData'); ss.batch_update({'requests': [{'updateSheetProperties': {'properties': {'sheetId': cd.id, 'hidden': True}, 'fields': 'hidden'}}]}); print('✅ Hidden')"
```

---

## 📋 Update Sequence

```
1. Authenticate (Google Sheets + BigQuery)
2. 🧹 CLEAR Dashboard & ChartData     ← Old data deleted here!
3. Fetch fresh data from BigQuery
4. Write new data to sheets
5. Apply formatting
6. Charts auto-refresh                 ← User sees updates
```

**Total time:** ~6-9 seconds

---

## 🎯 Key Code Snippets

### The Critical Clearing Code
```python
# File: enhance_dashboard_layout.py (Lines 45-52)

dashboard.clear()      # ← Removes ALL Dashboard data
print("🧹 Cleared old dashboard data")

chart_data.clear()     # ← Removes ALL ChartData data
print("🧹 Cleared old chart data")
```

### Data Write (After Clear)
```python
# Dashboard: Display data
dashboard.update('A1:F{}'.format(len(layout_data)), layout_data)

# ChartData: Chart source data
chart_data.update('A1:F{}'.format(len(chart_data_rows)), chart_data_rows)
```

---

## 🔍 Verification Checklist

After running `enhance_dashboard_layout.py`, you should see:

```
✅ Found existing Dashboard sheet
🧹 Cleared old dashboard data          ← Confirms deletion
✅ Found existing ChartData sheet
🧹 Cleared old chart data              ← Confirms deletion
📥 Fetching current data from BigQuery...
✅ Retrieved 20 fuel types, 79 data points
📝 Writing 30 rows to Dashboard...
📊 Writing chart data to hidden ChartData sheet...
✅ Wrote 80 rows to ChartData sheet    ← Confirms write
```

**If you don't see "🧹 Cleared..." messages, something is wrong!**

---

## 📈 Chart Synchronization

| Chart Type | Data Source | Range | Auto-Updates? |
|-----------|-------------|-------|---------------|
| Line (24h trend) | ChartData | A1:F80 | ✅ Yes |
| Pie (gen mix) | Dashboard | A8:B28 | ✅ Yes |
| Area (stacked) | ChartData | A1:F80 | ✅ Yes |
| Column (top sources) | Dashboard | A8:B28 | ✅ Yes |

**How it works:** Charts link to ranges (e.g., A1:F80), not data. When data in range changes, charts detect and re-render automatically.

---

## ⚠️ Common Issues & Fixes

### Issue: Old data still showing
```bash
# Fix: Force refresh
python3 enhance_dashboard_layout.py
# Check output for "🧹 Cleared..." messages
```

### Issue: ChartData visible
```bash
# Fix: Re-hide sheet
python3 enhance_dashboard_layout.py  # Script auto-hides
# OR manually hide in Google Sheets UI
```

### Issue: Charts not updating
```bash
# Fix 1: Hard refresh browser (Cmd+Shift+R)
# Fix 2: Recreate charts
python3 execute_chart_creation.py
```

### Issue: More than 80 rows in ChartData
```bash
# This shouldn't happen - .clear() prevents it
# If it does, manually clear sheet or re-run script
python3 enhance_dashboard_layout.py
```

---

## 🔐 Files & Credentials

| File | Purpose |
|------|---------|
| `enhance_dashboard_layout.py` | Main refresh script |
| `dashboard_charts_v2.gs` | Apps Script for charts |
| `inner-cinema-credentials.json` | BigQuery/Sheets access |
| `DASHBOARD_DATA_REFRESH_GUIDE.md` | Detailed documentation |

**Spreadsheet ID:** `12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8`  
**BigQuery Project:** `inner-cinema-476211-u9`  
**Dataset:** `uk_energy_prod`

---

## 📊 Data Sources

```sql
-- Dashboard: Current generation
SELECT fuelType, SUM(generation) as total_mw
FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_fuelinst_iris`
WHERE settlementDate = CURRENT_DATE()
GROUP BY fuelType

-- ChartData: 24h trend
SELECT settlementDate, settlementPeriod,
  SUM(CASE WHEN fuelType IN ('WIND', 'OFFSHORE') THEN generation END) as wind_mw,
  SUM(CASE WHEN fuelType = 'SOLAR' THEN generation END) as solar_mw,
  SUM(CASE WHEN fuelType = 'NUCLEAR' THEN generation END) as nuclear_mw,
  SUM(CASE WHEN fuelType IN ('CCGT', 'OCGT') THEN generation END) as gas_mw,
  SUM(generation) as total_mw
FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_fuelinst_iris`
WHERE settlementDate >= DATE_SUB(CURRENT_DATE(), INTERVAL 1 DAY)
GROUP BY settlementDate, settlementPeriod
```

---

## 🎯 Best Practices

### ✅ Do's
- Run script regularly (cron every 5 min)
- Monitor logs for errors
- Verify "🧹 Cleared..." messages appear
- Keep ChartData hidden
- Test changes manually before cron

### ❌ Don'ts
- Don't manually edit ChartData (gets overwritten)
- Don't skip `.clear()` calls
- Don't use `.append()` (use full range update)
- Don't delete sheets (script expects them)
- Don't hardcode row counts

---

## 📞 Quick Links

**Dashboard:** https://docs.google.com/spreadsheets/d/12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8/  
**Apps Script:** https://script.google.com/d/1fILya0xmSWkwXHtY9ulWDTVqFnPQqblpCmKLsa5A-y4dHeOOdU5q1N5A/edit  
**BigQuery Console:** https://console.cloud.google.com/bigquery?project=inner-cinema-476211-u9

---

## 💡 Key Insight

```
The .clear() method is your friend!

✅ Prevents data accumulation
✅ Ensures data freshness
✅ Simplifies logic (no complex deletes)
✅ Fast execution (atomic operation)
✅ Predictable behavior

Every update = Complete data replacement
```

---

## 📚 Related Docs

- **DASHBOARD_DATA_REFRESH_GUIDE.md** - Full detailed guide
- **DASHBOARD_SEPARATE_DATA_COMPLETE.md** - Implementation summary
- **ENHANCED_DASHBOARD_GUIDE.md** - Chart setup
- **PROJECT_CONFIGURATION.md** - BigQuery settings

---

**Version:** 2.1  
**Last Updated:** November 9, 2025  
**Contact:** george@upowerenergy.uk

---

## 🆘 Emergency Commands

### Script not running?
```bash
python3 --version  # Check Python installed
which python3      # Find Python path
pip3 list | grep google  # Check dependencies
```

### Authentication failed?
```bash
ls -la inner-cinema-credentials.json  # Check file exists
cat inner-cinema-credentials.json | jq .type  # Should be "service_account"
```

### BigQuery access denied?
```bash
# Verify project ID in script matches:
# inner-cinema-476211-u9 (NOT jibber-jabber-knowledge)
grep PROJECT_ID enhance_dashboard_layout.py
```

### Charts disappeared?
```bash
# Recreate via Apps Script
python3 execute_chart_creation.py
# OR manually via browser (30 seconds)
```

---

**Remember:** `.clear()` runs before every write = No old data ever accumulates! 🎯

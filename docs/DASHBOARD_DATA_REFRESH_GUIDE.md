# Dashboard Data Refresh Guide

## Overview

The GB Power Market Dashboard uses a **complete data replacement strategy** to ensure data is always current and accurate. This guide explains how data refresh works, what gets cleared, and how charts stay synchronized.

---

## Architecture

### Two-Sheet Structure

```
┌─────────────────────────────────────────────────────────┐
│                    Google Sheets                        │
│                                                         │
│  ┌──────────────────┐      ┌────────────────────┐    │
│  │   Dashboard      │      │   ChartData        │    │
│  │   (Visible)      │      │   (HIDDEN)         │    │
│  ├──────────────────┤      ├────────────────────┤    │
│  │ • KPIs           │      │ • Settlement Period│    │
│  │ • Gen Mix        │      │ • Wind (MW)        │    │
│  │ • Status         │      │ • Solar (MW)       │    │
│  │   Indicators     │      │ • Nuclear (MW)     │    │
│  │                  │      │ • Gas (MW)         │    │
│  │ 30 rows          │      │ • Total (MW)       │    │
│  │ 6 columns        │      │                    │    │
│  │                  │      │ 80 rows            │    │
│  │                  │      │ 6 columns          │    │
│  └──────────────────┘      └────────────────────┘    │
│         ↓                          ↓                   │
│    Display Data             Chart Source Data         │
└─────────────────────────────────────────────────────────┘
                         ↓
              ┌──────────────────────┐
              │   4 Interactive      │
              │   Charts             │
              │                      │
              │ • Line (24h trend)   │
              │ • Pie (gen mix)      │
              │ • Area (stacked)     │
              │ • Column (top sources)│
              └──────────────────────┘
```

---

## Data Refresh Process

### Step-by-Step Sequence

```python
# enhance_dashboard_layout.py execution flow:

1. AUTHENTICATE
   ├─ Google Sheets (service account)
   └─ BigQuery (service account)

2. CLEAR OLD DATA 🧹
   ├─ dashboard.clear()      # Remove ALL Dashboard data
   └─ chart_data.clear()     # Remove ALL ChartData data
   
3. FETCH FRESH DATA
   ├─ Query bmrs_fuelinst_iris (current generation by fuel type)
   ├─ Query bmrs_mid_iris (current market prices)
   └─ Query 24h trend data (last 48 settlement periods)

4. WRITE NEW DATA
   ├─ Dashboard: 30 rows (KPIs + generation mix table)
   └─ ChartData: 80 rows (header + 48 SPs × 5 series)

5. APPLY FORMATTING
   ├─ Colors (blue headers, yellow highlights)
   ├─ Column widths
   └─ Hide ChartData sheet

6. CHARTS AUTO-UPDATE
   └─ Google Sheets detects data change → re-renders charts
```

### Critical `.clear()` Behavior

**What `.clear()` does:**
- Removes **ALL** cell values in the sheet
- Removes **ALL** formatting
- Resets sheet to blank state
- **Does NOT** delete the sheet itself
- **Does NOT** affect charts (they stay linked to ranges)

**Why this matters:**
- ✅ No data accumulation
- ✅ No stale data lingering
- ✅ Consistent data structure
- ✅ Predictable behavior
- ✅ Fast execution (atomic operation)

---

## Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                      BigQuery Tables                        │
│  • bmrs_fuelinst_iris (generation data)                    │
│  • bmrs_mid_iris (market prices)                           │
└─────────────────────────────────────────────────────────────┘
                            ↓
              ┌──────────────────────────┐
              │ enhance_dashboard_       │
              │ layout.py                │
              │                          │
              │ 1. Clear old data 🧹     │
              │ 2. Fetch from BigQuery   │
              │ 3. Transform & format    │
              │ 4. Write to sheets       │
              └──────────────────────────┘
                            ↓
        ┌───────────────────┴────────────────────┐
        ↓                                        ↓
┌───────────────────┐                  ┌─────────────────┐
│   Dashboard       │                  │   ChartData     │
│   (Display)       │                  │   (Source)      │
│                   │                  │                 │
│ Cleared: ✅       │                  │ Cleared: ✅     │
│ Written: 30 rows  │                  │ Written: 80 rows│
└───────────────────┘                  └─────────────────┘
        ↓                                        ↓
        └───────────────────┬────────────────────┘
                            ↓
                  ┌──────────────────┐
                  │  Charts Detect   │
                  │  Data Change     │
                  │                  │
                  │  Auto Re-render  │
                  └──────────────────┘
                            ↓
                  ┌──────────────────┐
                  │  User Sees       │
                  │  Updated Charts  │
                  └──────────────────┘
```

---

## Update Frequency & Timing

### Manual Updates
```bash
cd '/Users/georgemajor/GB Power Market JJ'
python3 enhance_dashboard_layout.py
```

**Output:**
```
✅ Found existing Dashboard sheet
🧹 Cleared old dashboard data
✅ Found existing ChartData sheet
🧹 Cleared old chart data
✅ Retrieved 20 fuel types, 79 data points
📝 Writing 30 rows to Dashboard...
📊 Writing chart data to hidden ChartData sheet...
✅ Wrote 80 rows to ChartData sheet
```

### Automated Updates (Recommended)

**Crontab entry for 5-minute refresh:**
```bash
crontab -e
```

Add:
```bash
*/5 * * * * cd '/Users/georgemajor/GB Power Market JJ' && python3 enhance_dashboard_layout.py >> logs/dashboard_enhance.log 2>&1
```

**What happens every 5 minutes:**
```
00:00 - Clear all data → Write fresh data (last 24h)
00:05 - Clear all data → Write fresh data (last 24h)
00:10 - Clear all data → Write fresh data (last 24h)
...continues every 5 minutes
```

**Result:** Rolling 24-hour window, always current

---

## Chart Synchronization

### How Charts Stay Updated

Charts in Google Sheets are **linked to cell ranges**, not static data:

```javascript
// Chart configuration (internal to Google Sheets)
{
  dataSourceRange: 'ChartData!A1:F80',  // ← Linked to range
  chartType: 'LINE',
  series: [...],
  options: {...}
}
```

**When data updates:**
1. Script runs: `chart_data.clear()` → removes old data
2. Script writes: 80 new rows to ChartData
3. Google Sheets detects: "Range A1:F80 changed!"
4. Charts auto-refresh: New data appears instantly
5. User sees: Updated charts without any action

**No manual chart update needed!** ✅

### Chart Data Range Details

| Chart Type | Data Source | Range | Series |
|------------|-------------|-------|--------|
| Line Chart | ChartData | A1:F80 | Wind, Solar, Nuclear, Gas, Total |
| Pie Chart | Dashboard | A8:B28 | Generation mix (20 fuel types) |
| Area Chart | ChartData | A1:F80 | Wind, Solar, Nuclear, Gas |
| Column Chart | Dashboard | A8:B28 | Generation mix (20 fuel types) |

**Key Point:** Charts reference the **range** (e.g., A1:F80), not the specific data. When data in that range changes, charts update automatically.

---

## Data Lifecycle

### Example Timeline

```
┌─────────────────────────────────────────────────────────────┐
│ Time: 09:00 | Data: 08:00-08:55 (last 24h)                  │
│ Action: enhance_dashboard_layout.py runs                    │
│                                                              │
│ Step 1: dashboard.clear()     → 0 rows                      │
│ Step 2: chart_data.clear()    → 0 rows                      │
│ Step 3: Fetch BigQuery data   → Query executes              │
│ Step 4: Write Dashboard       → 30 rows                     │
│ Step 5: Write ChartData       → 80 rows                     │
│ Step 6: Charts refresh        → Display updated             │
│                                                              │
│ Result: Dashboard shows 09:00 data, old data GONE           │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ Time: 09:05 | Data: 08:05-09:00 (last 24h)                  │
│ Action: enhance_dashboard_layout.py runs                    │
│                                                              │
│ Step 1: dashboard.clear()     → 0 rows (09:00 data DELETED) │
│ Step 2: chart_data.clear()    → 0 rows (09:00 data DELETED) │
│ Step 3: Fetch BigQuery data   → Query executes              │
│ Step 4: Write Dashboard       → 30 rows (NEW data)          │
│ Step 5: Write ChartData       → 80 rows (NEW data)          │
│ Step 6: Charts refresh        → Display updated             │
│                                                              │
│ Result: Dashboard shows 09:05 data, 09:00 data GONE         │
└─────────────────────────────────────────────────────────────┘
```

**Pattern:** Complete replacement every run = Zero data accumulation

---

## Code Reference

### Key Functions

```python
# File: enhance_dashboard_layout.py

# 1. CLEAR OLD DATA
dashboard = ss.worksheet('Dashboard')
dashboard.clear()  # ← Remove ALL data
print("🧹 Cleared old dashboard data")

chart_data = ss.worksheet('ChartData')
chart_data.clear()  # ← Remove ALL data
print("🧹 Cleared old chart data")

# 2. FETCH FRESH DATA
gen_df = bq_client.query(generation_query).to_dataframe()
price_df = bq_client.query(price_query).to_dataframe()
trend_df = bq_client.query(trend_query).to_dataframe()

# 3. WRITE NEW DATA
dashboard.update('A1:F{}'.format(len(layout_data)), layout_data)
chart_data.update('A1:F{}'.format(len(chart_data_rows)), chart_data_rows)

# 4. HIDE CHARTDATA SHEET
ss.batch_update({
    'requests': [{
        'updateSheetProperties': {
            'properties': {'sheetId': chart_data.id, 'hidden': True},
            'fields': 'hidden'
        }
    }]
})
```

### BigQuery Queries

**Generation Data (Dashboard):**
```sql
SELECT 
  fuelType,
  SUM(generation) as total_mw
FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_fuelinst_iris`
WHERE settlementDate = CURRENT_DATE()
GROUP BY fuelType
ORDER BY total_mw DESC
```

**Trend Data (ChartData):**
```sql
WITH recent_data AS (
  SELECT 
    settlementDate,
    settlementPeriod,
    SUM(CASE WHEN fuelType IN ('WIND', 'OFFSHORE') THEN generation ELSE 0 END) as wind_mw,
    SUM(CASE WHEN fuelType = 'SOLAR' THEN generation ELSE 0 END) as solar_mw,
    SUM(CASE WHEN fuelType = 'NUCLEAR' THEN generation ELSE 0 END) as nuclear_mw,
    SUM(CASE WHEN fuelType IN ('CCGT', 'OCGT') THEN generation ELSE 0 END) as gas_mw,
    SUM(generation) as total_mw
  FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_fuelinst_iris`
  WHERE settlementDate >= DATE_SUB(CURRENT_DATE(), INTERVAL 1 DAY)
  GROUP BY settlementDate, settlementPeriod
)
SELECT * FROM recent_data
ORDER BY settlementDate, settlementPeriod
```

---

## Troubleshooting

### Issue: Charts showing old data

**Symptom:** Charts display data from hours/days ago

**Solution:**
```bash
# 1. Manually refresh data
python3 enhance_dashboard_layout.py

# 2. Check output for clearing confirmation
# Look for:
# 🧹 Cleared old dashboard data
# 🧹 Cleared old chart data

# 3. Verify data was written
# Look for:
# ✅ Wrote 80 rows to ChartData sheet

# 4. Open spreadsheet and check timestamps
```

### Issue: ChartData sheet is visible

**Symptom:** ChartData sheet appears in tab bar

**Solution:**
```python
# Run this to re-hide:
python3 -c "
import gspread
gc = gspread.service_account(filename='inner-cinema-credentials.json')
ss = gc.open_by_key('1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA')
chart_data = ss.worksheet('ChartData')
ss.batch_update({'requests': [{
    'updateSheetProperties': {
        'properties': {'sheetId': chart_data.id, 'hidden': True},
        'fields': 'hidden'
    }
}]})
print('✅ ChartData hidden')
"
```

### Issue: Data accumulating/duplicating

**Symptom:** More than 80 rows in ChartData or 30 rows in Dashboard

**Diagnosis:** `.clear()` not executing properly

**Solution:**
```bash
# 1. Check script runs completely
python3 enhance_dashboard_layout.py

# 2. Verify clear messages appear
# Should see both:
# 🧹 Cleared old dashboard data
# 🧹 Cleared old chart data

# 3. If issue persists, manually clear:
# Open Google Sheets → Select sheet → Edit → Delete all cells → Ctrl+A → Delete
```

### Issue: Charts not updating

**Symptom:** Data refreshes but charts show old data

**Causes & Solutions:**

1. **Chart range mismatch:**
   ```bash
   # Check if ChartData has 80 rows (header + 48 SPs)
   # If not, data might be writing to wrong range
   ```

2. **Browser cache:**
   ```bash
   # Hard refresh: Cmd+Shift+R (Mac) or Ctrl+Shift+R (Windows)
   ```

3. **Chart needs recreation:**
   ```bash
   # Re-run chart creation script
   python3 execute_chart_creation.py
   ```

---

## Performance Metrics

### Script Execution Time

Typical run (as of Nov 2025):
```
🔐 Authentication:      ~1-2 seconds
🧹 Clear operations:     ~0.5 seconds
📥 BigQuery queries:     ~2-3 seconds
📝 Write operations:     ~1-2 seconds
🎨 Formatting:           ~1 second
──────────────────────────────────────
Total:                   ~6-9 seconds
```

### Data Volume

**Dashboard Sheet:**
- Rows: 30
- Columns: 6
- Cells: 180
- Data size: ~5 KB

**ChartData Sheet:**
- Rows: 80 (1 header + 48 periods + extra for formatting)
- Columns: 6
- Cells: 480
- Data size: ~15 KB

**Total per update:**
- Cells cleared: 660
- Cells written: 660
- BigQuery bytes processed: ~10 MB
- Network transfer: ~20 KB

---

## Best Practices

### ✅ Do's

1. **Run regularly:** Set up cron for consistent updates
   ```bash
   */5 * * * * python3 enhance_dashboard_layout.py
   ```

2. **Monitor logs:** Check for errors
   ```bash
   tail -f logs/dashboard_enhance.log
   ```

3. **Verify clearing:** Always check output shows:
   ```
   🧹 Cleared old dashboard data
   🧹 Cleared old chart data
   ```

4. **Keep ChartData hidden:** Prevents user confusion
   ```python
   # Script handles this automatically
   ss.batch_update({'requests': [{'updateSheetProperties': {...}}]})
   ```

5. **Test after changes:** Run manually before deploying to cron
   ```bash
   python3 enhance_dashboard_layout.py
   ```

### ❌ Don'ts

1. **Don't manually edit ChartData:** Script overwrites all data
2. **Don't skip `.clear()`:** Leads to data accumulation
3. **Don't use `.append()`:** Always use full range `.update()`
4. **Don't hardcode row counts:** Use `len(data)` for dynamic ranges
5. **Don't delete sheets:** Script expects both Dashboard and ChartData to exist

---

## Integration with Other Systems

### Dashboard Charts (Apps Script)

**File:** `dashboard_charts_v2.gs`

Charts read from:
- **ChartData sheet** - For trend data (line, area charts)
- **Dashboard sheet** - For generation mix (pie, column charts)

**Key function:**
```javascript
function createDashboardCharts() {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var dashboard = ss.getSheetByName('Dashboard');
  var chartData = ss.getSheetByName('ChartData');
  
  // Charts automatically reference these sheets
  // When data updates, charts detect change and refresh
}
```

**Manual chart recreation:**
```bash
# Via Apps Script API
python3 execute_chart_creation.py

# Via browser (30 seconds)
# 1. Open: https://script.google.com/d/[SCRIPT_ID]/edit
# 2. Select: createDashboardCharts
# 3. Run: ▶️
```

### Auto-Refresh System

**File:** `realtime_dashboard_updater.py` (if exists)

Alternative to cron - Python-based scheduler:
```python
import schedule
import time

def refresh_dashboard():
    os.system('python3 enhance_dashboard_layout.py')

schedule.every(5).minutes.do(refresh_dashboard)

while True:
    schedule.run_pending()
    time.sleep(60)
```

---

## Security & Access Control

### Service Account Permissions

**Required scopes:**
```python
SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive.file',
    'https://www.googleapis.com/auth/bigquery'
]
```

**Credentials:**
- File: `inner-cinema-credentials.json`
- Type: Service Account
- Project: `inner-cinema-476211-u9`

### Data Privacy

- **ChartData hidden:** Prevents casual viewers from seeing raw data
- **BigQuery queries:** Limited to last 24 hours (minimal data exposure)
- **No PII:** All data is aggregate generation/pricing data

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | Nov 9, 2025 | Initial implementation with single sheet |
| 2.0 | Nov 9, 2025 | Split into Dashboard + ChartData (hidden) |
| 2.1 | Nov 9, 2025 | Added explicit clearing confirmation messages |

---

## Related Documentation

- **DASHBOARD_SEPARATE_DATA_COMPLETE.md** - Implementation guide
- **ENHANCED_DASHBOARD_GUIDE.md** - Chart setup instructions
- **APPS_SCRIPT_API_DEPLOYMENT_COMPLETE.md** - Apps Script deployment
- **DASHBOARD_QUICK_REF.md** - Quick reference card
- **PROJECT_CONFIGURATION.md** - BigQuery & project settings

---

## Support & Maintenance

**Common maintenance tasks:**

1. **Update query logic:**
   - Edit SQL in `enhance_dashboard_layout.py`
   - Test with `LIMIT 10` first
   - Deploy to production

2. **Change update frequency:**
   ```bash
   crontab -e
   # Modify */5 to desired interval (e.g., */15 for 15 min)
   ```

3. **Add new fuel types:**
   - Update `fuel_emojis` dict in script
   - No chart changes needed (auto-detects)

4. **Customize charts:**
   - Edit `dashboard_charts_v2.gs`
   - Re-deploy via Apps Script

---

## FAQ

**Q: Will old data ever accumulate?**  
A: No. `.clear()` runs before every write, ensuring complete replacement.

**Q: What if script fails mid-run?**  
A: Dashboard/ChartData will be partially cleared but no old data remains. Next run completes successfully.

**Q: Can I recover deleted data?**  
A: No. Data is replaced on each run. Original source is BigQuery (permanent storage).

**Q: Do charts need manual updates?**  
A: No. Charts auto-refresh when underlying data changes.

**Q: Why hide ChartData sheet?**  
A: Keeps dashboard clean and professional. Users see only relevant display data.

**Q: Can I add more charts?**  
A: Yes! Edit `dashboard_charts_v2.gs` and reference existing data ranges.

---

**Last Updated:** November 9, 2025  
**Maintained by:** GB Power Market JJ Team  
**Contact:** george@upowerenergy.uk

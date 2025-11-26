## Dashboard V2 - Manual Steps Required

✅ **Completed**:
- All 11 essential sheets copied with data
- BESS sheet with DNO lookup
- Chart data sheets (Daily_Chart_Data, Intraday_Chart_Data)
- Outages (REMIT Unavailability)
- GSP and Interconnector data

⚠️ **Manual Steps Needed**:

### 1. Copy Apps Script from Old Dashboard

The old dashboard has Apps Script code for:
- Chart generation
- Data refresh functions
- Dropdown menus
- Formatting automation

**Steps**:
1. Open old dashboard: https://docs.google.com/spreadsheets/d/12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8
2. Go to: **Extensions → Apps Script**
3. Copy all `.gs` files
4. Open new dashboard: https://docs.google.com/spreadsheets/d/1LmMq4OEE639Y-XXpOJ3xnvpAmHB6vUovh5g6gaU_vzc
5. Go to: **Extensions → Apps Script**
6. Paste the code
7. Save and run to create charts

### 2. Recreate Charts

The chart sheets exist but charts need to be recreated:
- **Chart_Prices**: System prices over time
- **Chart_Demand_Gen**: Demand vs Generation
- **Chart_IC_Import**: Interconnector imports
- **Chart_Frequency**: Grid frequency

**Option A - Manual**:
1. Insert → Chart in each sheet
2. Select data range from Daily_Chart_Data
3. Configure as line chart

**Option B - Apps Script**:
The old dashboard likely has `createCharts()` function that does this automatically

### 3. Copy Formatting

Some formatting may not have transferred:
- Cell colors
- Conditional formatting
- Data validation (dropdowns)
- Number formats

**Fix**:
1. In old dashboard, select formatted cells
2. Format → Paint format
3. Apply to new dashboard

### 4. Update Python Updater

Update `dashboard_v2_complete_updater.py` to write to correct cells matching the copied structure.

Current script writes to:
- Row 2: Timestamp
- Rows 10-29: Generation data
- Rows 80-84: Prices
- Rows 90-93: Frequency

Verify these match the copied Dashboard sheet structure.

---

## Alternative: Use clasp to deploy Apps Script

If the old dashboard Apps Script is complex, you can:

```bash
cd /Users/georgemajor/GB\ Power\ Market\ JJ/new-dashboard

# Get Apps Script from old dashboard (if you have source files)
# Or manually copy-paste from Extensions → Apps Script

# Create files:
# - dashboard_charts.gs (chart creation)
# - dashboard_functions.gs (utility functions)  
# - dashboard_menus.gs (onOpen menus)

clasp push
```

---

## Python Auto-Updater Integration

The `dashboard_v2_complete_updater.py` script should now be updated to:
1. Query BigQuery for latest data
2. Write to Dashboard sheet (rows 1-200)
3. Write to Daily_Chart_Data sheet (for charts)
4. Write to Intraday_Chart_Data sheet
5. Update BESS sheet via DNO lookup webhook
6. Update REMIT Unavailability from BigQuery

This will maintain parity with the old dashboard's auto-refresh functionality.

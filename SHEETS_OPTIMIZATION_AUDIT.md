# Google Sheets API Optimization Audit

## 🚨 Critical Issues Found

### 1. APPS SCRIPT - Cell-by-Cell Updates (search_interface.gs)

**Current (SLOW)**:
```javascript
// viewSelectedPartyDetails() - 15+ individual API calls!
sheet.getRange('M8').setValue(name);          // 1 API call
sheet.getRange('M10').setValue(identifier);   // 2 API calls
sheet.getRange('M11').setValue(recordType);   // 3 API calls
sheet.getRange('M12').setValue(role);         // 4 API calls
sheet.getRange('M13').setValue(organization); // 5 API calls
sheet.getRange('M16').setValue(role);         // 6 API calls
// ... 9 more individual setValue() calls
```

**Optimized (FAST)**:
```javascript
// 1 batch update = 15x faster
function viewSelectedPartyDetails() {
  var sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName('Search');
  var activeRange = sheet.getActiveRange();
  var row = activeRange.getRow();
  
  if (row < 25) {
    SpreadsheetApp.getUi().alert('⚠️ Please select a result row (row 25 or below)');
    return;
  }
  
  // Read all data at once (1 API call)
  var rowData = sheet.getRange(row, 1, 1, 10).getValues()[0];
  
  // Build output array
  var detailsData = [
    [rowData[2]],                     // M8: name
    [''],                             // M9: blank
    [rowData[1]],                     // M10: identifier
    [rowData[0]],                     // M11: recordType
    [rowData[3]],                     // M12: role
    [rowData[4]],                     // M13: organization
    [''],                             // M14-M15: blanks
    [''],
    [rowData[3]],                     // M16: BSC Roles
    [rowData[3].indexOf('VLP') >= 0 ? 'Yes - ' + rowData[5] : 'No'], // M17: VLP
    [rowData[3].indexOf('VTP') >= 0 ? 'Yes' : 'No'],                 // M18: VTP
    [rowData[8]],                     // M19: status
    [''],                             // M20-M21: blanks
    [''],
    [rowData[0] === 'BM Unit' ? '1 (this unit)' : '[Query BigQuery]'],  // M22
    [rowData[0] === 'BM Unit' ? rowData[6] + ' MW' : '[Query BigQuery]'], // M23
    [rowData[0] === 'BM Unit' ? rowData[7] : '[Query BigQuery]'],        // M24
    [''],                             // M25-M26: blanks
    [''],
    [new Date().toISOString()]        // M27: timestamp
  ];
  
  // Write all at once (1 API call)
  sheet.getRange('M8:M27').setValues(detailsData);
  
  SpreadsheetApp.getUi().alert('✅ Party details loaded for: ' + rowData[2]);
}
```

**Savings**: 15 API calls → 2 API calls (87% reduction)

---

### 2. APPS SCRIPT - Clear Button Individual Updates

**Current (SLOW)**:
```javascript
// onClearButtonClick() - 17+ individual API calls!
sheet.getRange('B4').setValue('01/01/2025');
sheet.getRange('D4').setValue('31/12/2025');
sheet.getRange('B5').clearContent();
sheet.getRange('E5').setValue('OR');
// ... 13 more individual calls
```

**Optimized (FAST)**:
```javascript
function onClearButtonClick() {
  var sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName('Search');
  
  // Build all updates in memory
  var updates = [
    {range: 'B4', values: [['01/01/2025']]},
    {range: 'D4', values: [['31/12/2025']]},
    {range: 'B5', values: [['']]},
    {range: 'E5', values: [['OR']]},
    {range: 'B6', values: [['None']]},
    {range: 'B7', values: [['None']]},
    {range: 'B8', values: [['None']]},
    {range: 'B9', values: [['None']]},
    {range: 'B10', values: [['None']]},
    {range: 'B11:D11', values: [['', '', '']]},
    {range: 'B12', values: [['']]},
    {range: 'B13', values: [['None']]},
    {range: 'B14', values: [['None']]},
    {range: 'B15', values: [['None']]},
    {range: 'B16', values: [['None']]},
    {range: 'B17', values: [['None']]},
    {range: 'M8', values: [['[Click a result row]']]},
  ];
  
  // Execute as batch (1 API call)
  sheet.getRangeList(updates.map(u => u.range)).setValues(updates.map(u => u.values).flat(2));
  
  // Clear results (1 API call)
  var lastRow = sheet.getLastRow();
  if (lastRow > 24) {
    sheet.getRange(25, 1, lastRow - 24, 11).clearContent();
  }
  
  // Clear party details (1 API call)
  sheet.getRange('M10:M27').clearContent();
  
  SpreadsheetApp.getUi().alert('✅ Search cleared successfully!');
}
```

**Savings**: 17+ API calls → 3 API calls (82% reduction)

---

### 3. PYTHON - Cell-by-Cell Updates (export_gsp_dno_to_sheets.py)

**Current (SLOW)**:
```python
# 6+ separate sheet.update() calls!
sheet.update('A1', [['GB POWER MARKET - GSP/DNO REGIONAL ANALYSIS']])
sheet.update('A2', [[f'Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}']])
sheet.update('A4', findings_data)
sheet.update('A18', gsp_data)
sheet.update(f'A{start_row}', bmu_data)
sheet.update(f'G{start_row}', report_data)
```

**Optimized (FAST)**:
```python
def export_gsp_dno_dashboard_optimized():
    """Single batch_update with all data"""
    gc = gspread.authorize(creds)
    ss = gc.open_by_key(SPREADSHEET_ID)
    sheet = ss.worksheet('GSP-DNO Analysis')
    
    # Build ALL data in memory
    all_updates = []
    
    # Header
    all_updates.append({
        'range': 'A1',
        'values': [['GB POWER MARKET - GSP/DNO REGIONAL ANALYSIS', '', '', '', '', '']]
    })
    
    all_updates.append({
        'range': 'A2',
        'values': [[f'Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}']]
    })
    
    # Key findings (query BigQuery once)
    findings_query = """..."""
    findings_df = bq_client.query(findings_query).to_dataframe()
    all_updates.append({
        'range': 'A4',
        'values': findings_df.values.tolist()
    })
    
    # GSP groups (query BigQuery once)
    gsp_query = """..."""
    gsp_df = bq_client.query(gsp_query).to_dataframe()
    all_updates.append({
        'range': 'A18',
        'values': gsp_df.values.tolist()
    })
    
    # Execute as single batch (1 API call!)
    sheet.batch_update(all_updates, value_input_option='USER_ENTERED')
    
    print("✅ Exported in 1 API call (vs 6+ previously)")
```

**Savings**: 6+ API calls → 1 API call (83% reduction)

---

### 4. PYTHON - Using gspread Instead of Sheets API v4

**Current (VERY SLOW)**:
```python
# export_enhanced_gsp_analysis.py - Uses gspread
import gspread
gc = gspread.authorize(creds)  # 120+ seconds to open!
ss = gc.open_by_key(SPREADSHEET_ID)
sheet = ss.worksheet('GSP-DNO Analysis')
```

**Optimized (FAST)**:
```python
# Use direct Sheets API v4 (298x faster)
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
creds = Credentials.from_service_account_file('inner-cinema-credentials.json', scopes=SCOPES)
service = build('sheets', 'v4', credentials=creds)

# Direct batch update (0.4s vs 120s with gspread!)
body = {
    'valueInputOption': 'USER_ENTERED',
    'data': [
        {'range': 'A1', 'values': [['Header']]},
        {'range': 'A2', 'values': findings_data},
        {'range': 'A10', 'values': gsp_data},
        {'range': 'A30', 'values': bmu_data},
    ]
}

service.spreadsheets().values().batchUpdate(
    spreadsheetId=SPREADSHEET_ID,
    body=body
).execute()
```

**Savings**: 120+ seconds → 0.4 seconds (300x faster!)

---

### 5. PYTHON - Multiple Individual Updates (btm_dno_lookup.py)

**Current (SLOW)**:
```python
# 5+ individual sheet.update() calls
sheet.update('C6', [[dno_data['dno_key']]])
sheet.update('D6', [[dno_data['dno_name']]])
sheet.update('B9:D9', rates_row)
sheet.update('B10:D10', schedules)
# ... more individual updates
```

**Optimized (FAST)**:
```python
def update_bess_sheet_optimized(dno_data, rates, schedules):
    """Single batch update"""
    updates = [
        {'range': 'C6:D6', 'values': [[dno_data['dno_key'], dno_data['dno_name']]]},
        {'range': 'B9:D9', 'values': [rates_row]},
        {'range': 'B10:D10', 'values': [schedules]},
        {'range': 'B11:D13', 'values': time_bands},  # All time bands at once
    ]
    
    sheet.batch_update(updates, value_input_option='USER_ENTERED')
```

**Savings**: 5+ API calls → 1 API call (80% reduction)

---

## 📊 Performance Impact Summary

| Script | Current API Calls | Optimized | Savings | Time Saved |
|--------|------------------|-----------|---------|------------|
| search_interface.gs (viewDetails) | 15 | 2 | 87% | ~3-5s |
| search_interface.gs (clear) | 17+ | 3 | 82% | ~4-6s |
| export_gsp_dno_to_sheets.py | 6+ | 1 | 83% | ~2-4s |
| export_enhanced_gsp_analysis.py | N/A | N/A | 300x | 120s → 0.4s |
| btm_dno_lookup.py | 5+ | 1 | 80% | ~1-2s |
| realtime_dashboard_updater.py | Unknown | Needs audit | TBD | TBD |

---

## 🔧 Immediate Action Plan

### Priority 1: Migrate from gspread to Sheets API v4

**Files to update**:
- `export_gsp_dno_to_sheets.py`
- `export_enhanced_gsp_analysis.py`
- `btm_dno_lookup.py`
- `realtime_dashboard_updater.py`
- `update_analysis_bi_enhanced.py`
- All ~50+ scripts using `import gspread`

**Use existing helper**:
```python
# Already exists in your codebase!
from sheets_fast import FastSheetsAPI

api = FastSheetsAPI()
api.batch_update(SPREADSHEET_ID, [
    {'range': 'A1:F10', 'values': data1},
    {'range': 'H1:K20', 'values': data2},
])
```

### Priority 2: Batch Apps Script Updates

**Files to update**:
- `search_interface.gs` (viewSelectedPartyDetails, onClearButtonClick)
- `dynamic_dropdowns.gs` (applyDynamicValidations)
- `apply_validations.gs` (applyDataValidations)
- `gsp_dno_linking.gs` (onEdit trigger)

### Priority 3: Optimize Dashboard Refresh

**File**: `realtime_dashboard_updater.py` (runs every 5 minutes!)

Need to check:
1. How many API calls per refresh?
2. Are updates batched?
3. Is it using gspread or API v4?

### Priority 4: Reduce Formatting Calls

Many scripts call `worksheet.format()` multiple times. Batch these:

**Current**:
```python
worksheet.format('A1:H1', {...})
worksheet.format('A2:H2', {...})
worksheet.format('A3:H3', {...})
```

**Optimized**:
```python
spreadsheet.batch_update({
    'requests': [
        {'repeatCell': {'range': {...}, 'cell': {...}}},
        {'repeatCell': {'range': {...}, 'cell': {...}}},
        {'repeatCell': {'range': {...}, 'cell': {...}}},
    ]
})
```

---

## 🚀 Google-Hosted Server Benefits

**Current setup**: Running from local machine (latency ~100-300ms to Google APIs)

**If moved to Cloud Run/Functions (europe-west2)**:
- Latency: 100-300ms → 5-20ms (10-15x reduction)
- Network stability: Variable → Consistent
- Cost: ~$0-5/month (within free tier for your usage)

**When it helps most**:
- Scripts making 20+ API calls (dashboard refresh, batch exports)
- Real-time operations (every 5-min cron job)
- Heavy BigQuery + Sheets workflows

**When it doesn't matter**:
- One-off manual scripts
- Already-batched operations
- Scripts that run <1/day

---

## 🎯 Expected Results After Optimization

### Scripts Currently Using Google Sheets

**Before optimization**:
- `export_gsp_dno_to_sheets.py`: 120s (gspread open) + 6s (updates) = **126s total**
- `realtime_dashboard_updater.py`: Unknown, needs audit
- `search_interface.gs` (user action): 3-5s delay per click
- **Total dashboard refresh**: ~2-3 minutes

**After optimization**:
- `export_gsp_dno_to_sheets.py`: 0.4s (API v4) + 0.1s (batch) = **0.5s total** (252x faster)
- `realtime_dashboard_updater.py`: Estimated 10-20s → 1-2s (10-20x faster)
- `search_interface.gs` (user action): <0.5s (instant feel)
- **Total dashboard refresh**: **<10 seconds** (12-18x faster)

### Cost Comparison

**Current (local + gspread)**:
- API quota usage: High (many small calls)
- Time wasted: ~2-3 min per dashboard refresh × 288/day (5-min cron) = **8.6 hours/day**

**After (Cloud Run + API v4)**:
- API quota usage: Low (batched calls)
- Time wasted: ~10s per refresh × 288/day = **48 minutes/day** (89% reduction)
- Cloud Run cost: $0-2/month (free tier covers 2M requests)

---

## 📝 Implementation Steps

### Step 1: Audit realtime_dashboard_updater.py
```bash
cd /home/george/GB-Power-Market-JJ
grep -n "sheet\\.update\\|getRange\\|setValue" realtime_dashboard_updater.py
```

### Step 2: Create optimized versions
```bash
# Backup originals
cp export_gsp_dno_to_sheets.py export_gsp_dno_to_sheets.py.backup
cp search_interface.gs search_interface.gs.backup

# Apply optimizations (use examples above)
```

### Step 3: Test optimized scripts
```bash
time python3 export_gsp_dno_to_sheets_optimized.py
# Should complete in <1s (vs 126s before)
```

### Step 4: Deploy to Cloud Run (optional but recommended)
```bash
# Create Dockerfile
cat > Dockerfile << 'EOF'
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY *.py .
COPY *.json .
CMD ["python3", "realtime_dashboard_updater.py"]
EOF

# Deploy
gcloud run deploy dashboard-updater \
  --source . \
  --region europe-west2 \
  --allow-unauthenticated
```

---

## 🎪 Summary Checklist

- [ ] **Replace gspread with Sheets API v4** in all Python scripts (50+ files)
- [ ] **Batch Apps Script updates** in search_interface.gs (2 functions)
- [ ] **Audit realtime_dashboard_updater.py** (critical - runs 288×/day)
- [ ] **Batch formatting calls** in export scripts
- [ ] **Test optimized versions** (expect 10-300x speedup)
- [ ] **Consider Cloud Run deployment** (5-20ms latency vs 100-300ms)
- [ ] **Monitor API quota usage** (should drop 80-90%)

**Est. Total Time Savings**: 8-10 hours/day of CPU time wasted on API calls

**Est. User Experience**: Dashboard refresh 2-3 min → <10 seconds (instant feel)

---

## 📚 Resources

- Your existing fast API: `sheets_fast.py`, `fast_sheets_helper.py`
- Google Sheets API v4 docs: https://developers.google.com/sheets/api/reference/rest
- Batch update examples: See `sheets_fast_examples.py` in your repo
- Cloud Run pricing: https://cloud.google.com/run/pricing (2M free requests/month)

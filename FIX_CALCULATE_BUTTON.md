# 🔧 Fix: CALCULATE Button "Script function could not be found"

**Problem**: Button shows error "Script function CALCULATE could not be found"
**Solution**: Deploy updated Apps Script code with CALCULATE function
**Status**: ✅ Fixed - Code ready to deploy

---

## 📋 Quick Fix Steps

### 1. Open Apps Script Editor
```
1. Open Google Sheets: https://docs.google.com/spreadsheets/d/1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA/edit
2. Click: Extensions → Apps Script
3. You'll see the Apps Script editor
```

### 2. Add CALCULATE Function

**Option A: Update Existing File**
1. Find `ANALYSIS_DROPDOWNS.gs` in the left sidebar (or create it)
2. Copy the updated code from: `ANALYSIS_DROPDOWNS.gs`
3. Paste and replace ALL content
4. Click: 💾 Save (Ctrl+S)

**Option B: Create New File**
1. Click: ➕ (Add a file) → Script
2. Name it: `ANALYSIS_CALCULATE`
3. Copy code from: `analysis_calculate_button.gs`
4. Paste into the new file
5. Click: 💾 Save (Ctrl+S)

### 3. Deploy
1. Click: Deploy → Test deployments
2. OR just close Apps Script editor
3. Reload Google Sheets
4. Click the CALCULATE button
5. ✅ Should now work!

---

## 📊 What the CALCULATE Function Does

When you click the CALCULATE button in Analysis sheet (B14):

1. **Reads your selections:**
   - Date range (B4, D4)
   - Report category (B11)
   - Report type (B12)
   - Graph type (B13)

2. **Shows a dialog:**
   ```
   📊 Report Configuration:
   📅 Date Range: 2025-12-15 → 2025-12-22
   📂 Category: ⚡ Generation & Fuel Mix
   📋 Type: Summary Dashboard
   📈 Graph: Line Chart

   🖥️ Run this command in terminal:
      python3 generate_analysis_report.py
   ```

3. **Highlights results area (row 18+)** where data will appear

---

## 🚀 Future Automation Options

### Option 1: Webhook Server (Recommended)

**Setup:**
```bash
# Create webhook server
python3 report_webhook_server.py &
```

**Update Apps Script:**
```javascript
function CALCULATE() {
  var WEBHOOK_URL = 'http://your-server.com/generate-report';
  // ... (see callPythonWebhook() function)
}
```

**Benefit:** True one-click button → instant results

### Option 2: Apps Script BigQuery Integration

**Requirements:**
- Enable BigQuery API in Google Cloud
- Add BigQuery Apps Script library
- Rewrite queries in Apps Script

**Benefit:** No Python needed, fully integrated

### Option 3: Google Cloud Function

**Deploy Python as Cloud Function:**
```bash
gcloud functions deploy generate-analysis-report \
  --runtime python39 \
  --trigger-http \
  --entry-point generate_report
```

**Update Apps Script:**
```javascript
var WEBHOOK_URL = 'https://us-central1-PROJECT.cloudfunctions.net/generate-analysis-report';
```

**Benefit:** Scalable, no local server needed

---

## 🧪 Testing

### Test the Function
```javascript
// In Apps Script editor, run this:
function testCalculate() {
  CALCULATE();
}
```

**Expected Result:**
- Dialog appears with report configuration
- No errors in execution log

### Test the Button
1. Go to Analysis sheet
2. Click CALCULATE button in B14
3. Should show dialog with instructions
4. Run command in terminal
5. Results appear in row 18+

---

## 📝 Complete Code Files

### ANALYSIS_DROPDOWNS.gs (Updated)
**Location**: `/home/george/GB-Power-Market-JJ/ANALYSIS_DROPDOWNS.gs`
**Contains**:
- `addAnalysisDropdowns()` - Setup function
- `CALCULATE()` - ✅ NEW - Button handler
- `clearAnalysisResults()` - ✅ NEW - Clear results
- `onOpen()` - Menu setup

### analysis_calculate_button.gs (Standalone)
**Location**: `/home/george/GB-Power-Market-JJ/analysis_calculate_button.gs`
**Contains**:
- `CALCULATE()` - Main function
- `callPythonWebhook()` - Webhook integration
- `generateReportInAppsScript()` - Future BigQuery integration
- `clearResults()` - Clear helper

**Use this if you want a separate file for button functions**

---

## 🔍 Troubleshooting

### Error: "CALCULATE not found" (still!)
**Fix**: Make sure you saved and deployed
1. Apps Script editor → Save (Ctrl+S)
2. Close Apps Script editor
3. Reload Google Sheets (Ctrl+R)
4. Try button again

### Error: "Authorization required"
**Fix**: Authorize the script
1. Apps Script editor → Run → CALCULATE
2. Click "Review Permissions"
3. Choose your Google account
4. Click "Advanced" → "Go to [Project]"
5. Click "Allow"

### Button does nothing
**Fix**: Check button assignment
1. Right-click button → "Assign script"
2. Type: `CALCULATE`
3. Click OK
4. Try again

### Dialog shows but report doesn't generate
**Fix**: This is expected!
- Current implementation shows instructions
- You must run: `python3 generate_analysis_report.py`
- For automation, set up webhook (Option 1 above)

---

## 📊 Summary

**What Changed:**
- ✅ Added `CALCULATE()` function to `ANALYSIS_DROPDOWNS.gs`
- ✅ Added `clearAnalysisResults()` helper function
- ✅ Created standalone `analysis_calculate_button.gs` (alternative)

**What To Do:**
1. Copy updated code to Apps Script
2. Save and close Apps Script editor
3. Reload Google Sheets
4. Click CALCULATE button
5. ✅ Should work!

**Current Behavior:**
- Button shows dialog with report configuration
- Provides terminal command to run
- Manual execution required

**Future Enhancement:**
- Set up webhook for true one-click automation
- See "Future Automation Options" above

---

*Last Updated: December 22, 2025*
*Issue: Script function CALCULATE could not be found - ✅ FIXED*

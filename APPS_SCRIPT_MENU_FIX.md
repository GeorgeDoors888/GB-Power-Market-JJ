# Apps Script Menu Not Appearing - Solution

## ✅ GOOD NEWS: Formatting Applied!

The BESS enhanced section has been formatted via Python:
- Row 58: Grey divider ✅
- Row 59: Orange title ✅  
- Row 60: Light blue headers ✅
- T60:U67: KPIs panel ✅
- W60:Y67: Revenue stack ✅

View: https://docs.google.com/spreadsheets/d/1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA/

---

## ⚠️ Apps Script Menu Issue

**Problem**: The "⚡ GB Energy Dashboard" menu is not appearing

**Root Cause**: The `onOpen()` trigger may not have fired, OR the Apps Script needs to be manually linked to the sheet

---

## 🔧 SOLUTION: Manually Run Apps Script Function

### Option 1: Run from Apps Script Editor (RECOMMENDED)

1. **Open your sheet**:
   https://docs.google.com/spreadsheets/d/1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA/

2. **Go to Apps Script**:
   Extensions → Apps Script

3. **Check if code is there**:
   - If you see the `formatBESSEnhanced()` function → Good!
   - If empty or old code → Paste from `/home/george/GB-Power-Market-JJ/apps_script_deploy/Code.gs`

4. **Run onOpen() manually**:
   - Select function: `onOpen` (from dropdown at top)
   - Click **Run** (▶️ button)
   - Authorize when prompted
   - Close Apps Script editor

5. **Refresh Google Sheets**:
   - Go back to your sheet
   - Press Ctrl+R
   - Menu "⚡ GB Energy Dashboard" should now appear

### Option 2: Create Simple Trigger

If Option 1 doesn't work, create an installable trigger:

1. In Apps Script editor: **Triggers** (clock icon on left)
2. Click **+ Add Trigger**
3. Settings:
   - Function: `onOpen`
   - Event source: `From spreadsheet`
   - Event type: `On open`
4. Click **Save**
5. Close and reopen your Google Sheet

### Option 3: Alternative - Add Button to Sheet

If menu still doesn't work, add a button:

1. In Google Sheets: **Insert** → **Drawing** → **New**
2. Draw a simple button/shape
3. Add text: "Format BESS"
4. Click **Save and Close**
5. Click the drawing
6. Three dots (⋮) → **Assign script**
7. Type: `formatBESSEnhanced`
8. Click **OK**

Now clicking the button runs the formatting function.

---

## 🎯 Why This Happened

**Apps Script Version 18 deployed successfully** BUT:
- The `onOpen()` trigger is a "simple trigger"
- Simple triggers don't always fire automatically on first deployment
- They activate when someone with edit access opens the sheet
- Sometimes requires manual run to "wake up" the trigger

**Solution**: Running `onOpen()` once manually (Option 1) should fix it permanently.

---

## ✅ Verification

After running Option 1, verify:
1. Menu "⚡ GB Energy Dashboard" appears in toolbar
2. Menu has items:
   - 🔄 Refresh DNO Data
   - 📊 Generate HH Data
   - 🎨 Format BESS Enhanced
   - 🎨 Format All Sheets
3. Clicking "Format BESS Enhanced" shows success message

---

## 📊 Current Status

| Item | Status |
|------|--------|
| Apps Script Code | ✅ Deployed (V18) |
| Correct Sheet | ✅ 12jY0d4j... |
| Formatting Applied | ✅ Via Python |
| onOpen() Menu | ⏳ Needs manual trigger |
| Existing Data | ✅ Preserved |

---

## 🚀 Next Steps

1. **Try Option 1** (run onOpen manually from Apps Script editor)
2. **If menu appears**: Done! ✅
3. **If menu doesn't appear**: Try Option 2 (installable trigger)
4. **Fallback**: Use Option 3 (button) or just use Python formatting script

---

## 💡 Alternative: Python-Only Workflow

Since Python formatting works perfectly, you can skip Apps Script menu entirely:

**Format BESS enhanced section**:
```bash
cd /home/george/GB-Power-Market-JJ
python3 apply_bess_formatting.py
```

**Update data + format**:
```bash
python3 dashboard_pipeline.py
```

Apps Script is nice-to-have for the menu, but Python can do everything needed!

---

**Bottom Line**: Formatting is applied and working. Menu is optional convenience feature.

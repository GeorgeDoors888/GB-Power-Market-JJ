# 📊 Google Apps Script Installation Guide

## 🚀 Automatic Deployment (Recommended - 1 Minute!)

### Run the Deployment Script
```bash
cd "/Users/georgemajor/GB Power Market JJ"
./.venv/bin/python deploy_apps_script_complete.py
```

This automatically:
- ✅ Deploys the chart script to your spreadsheet
- ✅ Creates the bound Apps Script project
- ✅ Uploads all code

Then follow the on-screen instructions to create charts (one-time authorization).

---

## 📝 Manual Installation (Alternative Method)

### Step 1: Open Apps Script Editor
1. Open your dashboard: https://docs.google.com/spreadsheets/d/12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8
2. Click **Extensions** → **Apps Script**
3. You'll see a script editor window

### Step 2: Paste the Script
1. **Delete any existing code** in the editor
2. Open the file: `google_apps_script_charts.js` (in this folder)
3. **Copy ALL the code** from that file
4. **Paste it** into the Apps Script editor
5. Click the **Save** icon (💾) or press `Ctrl+S` / `Cmd+S`
6. Name your project: **"Dashboard Charts"**

### Step 3: Run Initial Setup
1. In the Apps Script editor, find the function dropdown (top of editor)
2. Select **`createAllCharts`** from the dropdown
3. Click the **▶ Run** button
4. **First time only**: You'll see a permissions dialog
   - Click **Review Permissions**
   - Select your Google account
   - Click **Advanced** → **Go to Dashboard Charts (unsafe)**
   - Click **Allow**
5. Wait for script to complete (check execution log)
6. **Go back to your spreadsheet** - you should see **4 charts**!

### Step 4: Set Up Automatic Updates (Optional)
To update charts automatically every 30 minutes:

1. In Apps Script editor, click the **⏰ Clock** icon (Triggers)
2. Click **+ Add Trigger** (bottom right)
3. Configure:
   - **Function**: `updateCharts`
   - **Deployment**: Head
   - **Event source**: Time-driven
   - **Type**: Minutes timer
   - **Interval**: Every 30 minutes
4. Click **Save**

Now charts will auto-update every 30 minutes!

---

## 📊 What Charts Are Created

### Chart 1: Generation by Settlement Period
- **Type**: Line chart (smooth curves)
- **Location**: Row 35, Column J
- **Data**: A19:B28 (SP vs Generation)
- **Color**: Google Blue (#4285F4)
- **Size**: 400 x 250 px

### Chart 2: System Frequency
- **Type**: Line chart
- **Location**: Row 35, Column Q (next to Generation)
- **Data**: A19:A28, C19:C28 (SP vs Frequency)
- **Color**: Google Red (#EA4335)
- **Y-axis Range**: 49.8 - 50.2 Hz
- **Size**: 400 x 250 px

### Chart 3: System Sell Price
- **Type**: Column chart (bar chart)
- **Location**: Row 50, Column J (below Generation)
- **Data**: A19:A28, D19:D28 (SP vs Price)
- **Color**: Google Yellow (#FBBC04)
- **Size**: 400 x 250 px

### Chart 4: Combined Overview
- **Type**: Combo chart (lines + bars)
- **Location**: Row 50, Column Q (below Frequency)
- **Data**: A19:D28 (All metrics)
- **Colors**: Blue (Gen), Red (Freq), Yellow (Price)
- **Dual Y-axes**: Left (Gen/Price), Right (Frequency)
- **Size**: 400 x 250 px

---

## 🎛️ Custom Menu

After installation, you'll see a new menu: **⚡ Dashboard Charts**

Options:
- **🔄 Recreate All Charts** - Delete and rebuild all charts
- **📊 Update Data (Manual)** - Force update (charts auto-update anyway)
- **ℹ️ About** - Show info dialog

---

## 🔧 Troubleshooting

### Problem: Charts Don't Appear
**Solution**: 
1. Check Apps Script execution log (View → Execution log)
2. Make sure you ran `createAllCharts` function
3. Check permissions were granted

### Problem: Charts Show Wrong Data
**Solution**:
1. Verify data range A19:D28 has settlement period data
2. Run dashboard update script first: `./.venv/bin/python dashboard_clean_design.py`
3. Run `createAllCharts` again in Apps Script

### Problem: "Script Error" on Run
**Solution**:
1. Check SHEET_NAME is correct (default: "Sheet1")
2. Make sure data range A18:H28 exists with data
3. Check execution log for specific error

### Problem: Charts Overlap Data
**Solution**:
1. Charts are placed at Row 35, Column J (far right)
2. Adjust `CHART_START_ROW` and `CHART_START_COL` in script if needed
3. Recreate charts after adjusting

---

## 🎨 Customization

### Change Chart Colors
Edit the `.setOption('colors', [...])` lines:

```javascript
// Generation chart - Line 54
.setOption('colors', ['#4285F4']) // Change to your color

// Frequency chart - Line 93
.setOption('colors', ['#EA4335'])

// Price chart - Line 131
.setOption('colors', ['#FBBC04'])
```

### Change Chart Size
Edit the width/height options:

```javascript
.setOption('width', 400)   // Change to desired width
.setOption('height', 250)  // Change to desired height
```

### Change Chart Position
Edit these constants at the top:

```javascript
const CHART_START_ROW = 35; // Starting row for charts
const CHART_START_COL = 10; // Starting column (J = 10)
```

### Change Data Range
Edit this constant:

```javascript
const DATA_RANGE = 'A19:D28'; // Your desired range
```

---

## 🔄 Update Workflow

### Automatic (Recommended):
1. Set up time-driven trigger (every 30 minutes)
2. Python script updates data → Charts auto-update
3. No manual intervention needed

### Manual:
1. Run Python script: `./.venv/bin/python dashboard_clean_design.py`
2. Charts update automatically when data changes
3. Or use menu: **⚡ Dashboard Charts** → **🔄 Recreate All Charts**

---

## 📋 Quick Reference

### Functions Available:
- `createAllCharts()` - Create all 4 charts (run once initially)
- `updateCharts()` - For trigger (charts auto-update anyway)
- `deleteAllCharts()` - Remove all charts
- `testDataRange()` - Test if data range is correct
- `onOpen()` - Creates custom menu (runs automatically)
- `showAbout()` - Shows info dialog

### Key Variables:
```javascript
SHEET_NAME = 'Sheet1'           // Your sheet name
DATA_RANGE = 'A19:D28'          // Settlement period data
CHART_START_ROW = 35            // Where to place charts
CHART_START_COL = 10            // Column J (10th column)
```

---

## ✅ Verification Checklist

After installation, verify:
- [ ] 4 charts appear in the spreadsheet
- [ ] Generation chart shows line graph (blue)
- [ ] Frequency chart shows line graph (red, 49.8-50.2 Hz range)
- [ ] Price chart shows column graph (yellow/orange)
- [ ] Combined chart shows all 3 metrics together
- [ ] Charts update when you change data in A19:D28
- [ ] Custom menu "⚡ Dashboard Charts" appears
- [ ] (Optional) Time-driven trigger set up for auto-updates

---

## 🎯 Expected Result

Your dashboard will have:
- **Top Section**: Dashboard title, metrics, generation/interconnector data
- **Middle Section**: Graph data table (A18:H28)
- **Bottom Left**: REMIT outages, price impacts
- **Bottom Right**: 4 Auto-updating charts showing settlement period trends

**Visual Layout**:
```
+----------------------------------------------------------+
|  Dashboard Title & Timestamp                              |
|  System Metrics                                           |
|  Generation Data (10 types) | Interconnectors (10)        |
+----------------------------------------------------------+
|  📈 Settlement Period Data (A18:H28)                      |
|  SP | Gen | Freq | Price                                  |
+----------------------------------------------------------+
|  🔴 REMIT Outages          |  📊 Generation Chart         |
|  💷 Price Impacts          |  ⚡ Frequency Chart          |
|  📊 Station Outages Table  |  💷 Price Chart              |
|                            |  📈 Combined Chart           |
+----------------------------------------------------------+
```

---

## 🚀 Next Steps After Installation

1. **Test the charts**: Change a value in A19:D28 and watch charts update
2. **Run dashboard script**: `./.venv/bin/python dashboard_clean_design.py`
3. **Verify charts update** with new settlement period data
4. **Set up automation**: Add time-driven trigger (every 30 minutes)
5. **Share dashboard**: Charts will update for all viewers automatically

---

## 📞 Support

If you encounter issues:
1. Check the Apps Script execution log
2. Verify data range A19:D28 has valid data
3. Run `testDataRange()` function to debug
4. Try `deleteAllCharts()` then `createAllCharts()` to rebuild

**Dashboard URL**: https://docs.google.com/spreadsheets/d/12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8

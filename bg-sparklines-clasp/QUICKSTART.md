# 🚀 QUICK START - GB Live Dashboard + DNO Maps

## TL;DR

Copy the entire `Code.gs` file from this directory and paste it into:  
Extensions → Apps Script in your Google Sheet. Done! ✅

## What This Does

Adds **two custom menus** to your Google Sheet:
1. **⚡ GB Live Dashboard** - Writes sparkline formulas for fuel/interconnector charts
2. **🗺️ DNO Map** - Interactive UK DNO geographic boundaries with real GeoJSON

Works because Apps Script runs **inside** Google Sheets (unlike the Python API).

## Prerequisites

None! Just copy-paste the code into Apps Script editor.

## Deployment (2 minutes)

### Method 1: Direct Copy-Paste (Easiest)

1. Open: https://docs.google.com/spreadsheets/d/1MSl8fJ0to6Y08enXA2oysd8wvNUVm3AtfJ1bVqRH8_I/
2. Go to: **Extensions → Apps Script**
3. Delete any existing code
4. Open `Code.gs` from this directory in a text editor
5. Copy all contents (Ctrl+A, Ctrl+C)
6. Paste into Apps Script editor (Ctrl+V)
7. Save (Ctrl+S)
8. Close Apps Script tab
9. Refresh your spreadsheet

✅ Done! Two new menus appear: **⚡ GB Live Dashboard** and **🗺️ DNO Map**

### Method 2: CLASP (If you have it installed)

```bash
# Not recommended - Method 1 is easier
clasp login
clasp create --type sheets --title "GB Live Functions"
clasp push
```

## Usage

### Write Sparklines

1. Open your Google Sheet
2. Click: **⚡ GB Live Dashboard** → **✨ Write Sparkline Formulas**
3. Wait 5 seconds
4. ✅ Verify columns C and F show sparkline charts

### View DNO Maps

1. Click: **🗺️ DNO Map** → **View Interactive Map**
2. See UK DNO boundaries with hover details
3. Or: **View Map with Site Markers** (shows battery location from BtM sheet)

Check columns C and F (rows 11-20) - should see colorful sparkline charts.

## Comparison: CLASP vs Manual

| Method | Time | Reproducible | Automated | Difficulty |
|--------|------|--------------|-----------|------------|
| **CLASP** | 5 min setup + 1 click | ✅ Yes | ✅ Yes | Easy |
| **Manual** | 5 min copy-paste | ❌ No | ❌ No | Tedious |

## Why CLASP Works When Python API Fails

```
Python API (External)
    ↓
❌ Can't write cross-sheet SPARKLINE formulas
    ↓
Cells remain empty

Apps Script (Internal)
    ↓
✅ Runs inside Sheets context
    ↓
Formulas written successfully
```

## Troubleshooting

### "CLASP command not found"
```bash
npm install -g @google/clasp
```

### "Not logged in"
```bash
clasp login
```

### "Sheet 'Data_Hidden' not found"
Run Python script first to create it:
```bash
python3 update_bg_live_dashboard.py
```

### Sparklines show #N/A
Wait for Python script to populate Data_Hidden (runs every 5 minutes), or run manually.

## Files Created

```
bg-sparklines-clasp/
├── Code.gs           # Apps Script code
├── appsscript.json   # Configuration
├── README.md         # Full documentation
├── deploy.sh         # Deployment script
└── .clasp.json       # Local settings (auto-generated)
```

## Optional: Python Integration

Make sparklines auto-refresh when Python updates data:

```python
# In update_bg_live_dashboard.py
import requests

APPS_SCRIPT_URL = "YOUR_DEPLOYMENT_URL"  # Get from: clasp deploy

def trigger_sparklines():
    requests.post(APPS_SCRIPT_URL, timeout=10)

# Call after updating Data_Hidden:
trigger_sparklines()
```

## More Info

- Full docs: `bg-sparklines-clasp/README.md`
- Issue analysis: `SPARKLINE_ISSUE_RESOLVED.md`
- Dashboard docs: `WIND_FORECAST_DASHBOARD_DEPLOYMENT.md`

---

**Status:** ✅ Production Ready  
**Created:** 8 December 2025

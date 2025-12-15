# GB Live Dashboard - CLASP Apps Script Deployment

## What This Does

This CLASP project deploys Apps Script code directly to your Google Sheet with **two custom menus**:

1. **⚡ GB Live Dashboard** - Writes cross-sheet SPARKLINE formulas for fuel types and interconnectors
2. **🗺️ DNO Map** - Interactive DNO geographic boundaries with real GeoJSON data

Apps Script can write these formulas because it runs **inside** the Sheets context, unlike the Python API which runs externally.

## Prerequisites

1. **CLASP installed:**
   ```bash
   npm install -g @google/clasp
   ```

2. **CLASP authenticated:**
   ```bash
   clasp login
   ```

## Deployment Steps

### 1. Link to Your Spreadsheet

```bash
cd /home/george/GB-Power-Market-JJ/bg-sparklines-clasp

# Option A: Create new Apps Script project bound to your sheet
clasp create --type sheets --title "GB Live Sparklines" --rootDir .

# Option B: Clone existing Apps Script if you already have one
# clasp clone YOUR_SCRIPT_ID
```

After creating, manually bind to your spreadsheet:
1. Open https://script.google.com
2. Find "GB Live Sparklines" project
3. Go to Project Settings
4. Add spreadsheet: `1MSl8fJ0to6Y08enXA2oysd8wvNUVm3AtfJ1bVqRH8_I`

### 2. Push Code to Google

```bash
clasp push
```

### 3. Deploy as Web App (Optional - for Python webhook)

```bash
clasp deploy --description "Sparkline Writer v1"
```

Note the deployment URL for webhook calls from Python.

## Usage

### Option A: Manual Trigger (Recommended)

1. Open your Google Sheet: https://docs.google.com/spreadsheets/d/1MSl8fJ0to6Y08enXA2oysd8wvNUVm3AtfJ1bVqRH8_I/
2. **Two menus appear:**
   - **⚡ GB Live Dashboard** - Sparkline functions
   - **🗺️ DNO Map** - Geographic visualizations

#### To Write Sparklines:
3. Click: **⚡ GB Live Dashboard** → **✨ Write Sparkline Formulas**
4. Wait ~5 seconds
5. ✅ All 20 sparklines appear in columns C and F!

#### To View DNO Maps:
3. Click: **🗺️ DNO Map** → **View Interactive Map**
4. See real UK DNO boundaries with hover info
5. Or: **View Map with Site Markers** (shows battery site from BtM sheet postcode)

### Option B: Python Integration (Sparklines Only)

Update `update_bg_live_dashboard.py` to call Apps Script webhook after updating Data_Hidden:

```python
import requests

APPS_SCRIPT_URL = "https://script.google.com/macros/s/YOUR_DEPLOYMENT_ID/exec"

def trigger_sparkline_refresh():
    """Call Apps Script to refresh sparklines after data update"""
    try:
        response = requests.post(APPS_SCRIPT_URL, timeout=10)
        if response.status_code == 200:
            logging.info("✅ Sparklines refreshed via Apps Script")
        else:
            logging.warning(f"⚠️ Apps Script returned {response.status_code}")
    except Exception as e:
        logging.error(f"❌ Apps Script webhook failed: {e}")

# Add to main update function after Data_Hidden update:
# trigger_sparkline_refresh()
```

### Option C: Scheduled Trigger

Run once to create hourly auto-refresh:

```bash
# In Apps Script editor (script.google.com)
# Run function: createHourlyTrigger()
```

Or from CLASP:
```bash
clasp run createHourlyTrigger
```

## Testing

### Test in Apps Script Editor

1. Open https://script.google.com
2. Select "GB Live Sparklines" project
3. Select function: `runTests`
4. Click Run ▶️
5. Check Execution log for results

### Test from CLASP

```bash
clasp run writeSparklines
```

### Verify in Google Sheets

1. Open sheet: https://docs.google.com/spreadsheets/d/1MSl8fJ0to6Y08enXA2oysd8wvNUVm3AtfJ1bVqRH8_I/
2. Check cells C11-C20 and F11-F20
3. Should see sparkline charts (not formulas)
4. Hover over charts to see data values

## Functions Available

### GB Live Dashboard (Sparklines)
| Function | Description |
|----------|-------------|
| `writeSparklines()` | Main function - writes all 20 sparkline formulas |
| `verifyDataHidden()` | Checks Data_Hidden sheet has data |
| `clearSparklines()` | Removes all sparklines (for testing) |
| `createHourlyTrigger()` | Sets up auto-refresh every hour |
| `removeAllTriggers()` | Deletes all auto-refresh triggers |
| `runTests()` | Comprehensive test suite |

### DNO Map (Geographic)
| Function | Description |
|----------|-------------|
| `createDNOMap()` | Opens interactive DNO boundaries map |
| `createDNOMapWithSites()` | Map with battery site marker from BtM sheet |
| `embedMapInSheet()` | Embeds map in DNO sheet column H |

## Architecture

```
Python Script (every 5 min)
    ↓
Update Data_Hidden sheet (numeric data only)
    ↓
[OPTIONAL] Trigger Apps Script webhook
    ↓
Apps Script writes SPARKLINE formulas
    ↓
Formulas reference Data_Hidden → Charts display
```

## Advantages Over Manual Entry

✅ **One-click deployment** - Menu button instead of copy-paste 20 formulas  
✅ **Reproducible** - Can clear and rewrite anytime  
✅ **Automatable** - Webhook integration with Python  
✅ **Testable** - Built-in test functions  
✅ **Maintainable** - Version controlled in Git

## Troubleshooting

### Error: "Sheet 'GB Live' not found"
- Check sheet name is exactly "GB Live" (case-sensitive)
- Verify you're running in correct spreadsheet

### Error: "Sheet 'Data_Hidden' not found"
- Run Python script first: `python3 update_bg_live_dashboard.py`
- This creates and populates Data_Hidden sheet

### Sparklines show #N/A
- Data_Hidden has insufficient data
- Wait for Python script to run (every 5 min)
- Or manually populate Data_Hidden with test values

### Permission denied
- Authorize Apps Script: Tools → Manage permissions
- Accept OAuth consent screen

### Webhook returns 401/403
- Redeploy as web app: Settings → Deploy as web app
- Set execute as: "Me"
- Who has access: "Anyone"

## Files

- `Code.gs` - Main Apps Script code
- `appsscript.json` - Project configuration
- `.clasp.json` - CLASP local settings (auto-generated)
- `README.md` - This file

## Related Documentation

- Main issue: `/SPARKLINE_ISSUE_RESOLVED.md`
- Dashboard: `/WIND_FORECAST_DASHBOARD_DEPLOYMENT.md`
- Update script: `/update_bg_live_dashboard.py`

## Status

✅ **READY TO DEPLOY**

Next steps:
1. Run `clasp push` from this directory
2. Open Google Sheet
3. Use menu: ⚡ GB Live Dashboard → ✨ Write Sparkline Formulas
4. Verify 20 sparklines appear

---

**Created:** 8 December 2025  
**Status:** Production Ready

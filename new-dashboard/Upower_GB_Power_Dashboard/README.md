# Upower GB Energy Dashboard 📊

Real-time UK energy market dashboard powered by Elexon BMRS data.

## What's Included

- `apps_script_code.gs` - Main Apps Script code (paste into Google Apps Script)
- `dashboard_functions.gs` - Helper functions
- `upower_dashboard_theme.json` - Theme configuration
- `dashboard_updater.py` - Python auto-updater script
- `GB_Power_Dashboard_Setup.md` - Detailed setup instructions
- `manifest.json` - Apps Script manifest

## Quick Start (2 minutes)

1. **Create Google Spreadsheet**
   - Go to https://sheets.google.com → New spreadsheet
   - Copy the Spreadsheet ID from URL

2. **Deploy Apps Script**
   - Extensions → Apps Script
   - Paste contents of `apps_script_code.gs`
   - Update `SPREADSHEET_ID` on line 11
   - Save and refresh spreadsheet

3. **See Menus Appear!**
   - 🗺️ Maps - Interactive constraint map
   - 🔄 Data - Refresh functions
   - 🎨 Format - Styling options
   - 🛠️ Tools - Utilities

## Features

✅ **Real-time Data** - Live generation, demand, prices  
✅ **Interactive Maps** - Transmission constraints with color coding  
✅ **Auto-Updates** - Python script updates every 5 minutes  
✅ **Charts** - Price, demand, frequency visualization  
✅ **BESS Analysis** - Battery storage insights  
✅ **Outage Tracking** - Generator unavailability  

## Architecture

```
Elexon BMRS API → BigQuery → Python → Google Sheets → Apps Script
```

## Next Steps

See `GB_Power_Dashboard_Setup.md` for:
- Detailed installation instructions
- Python auto-updater setup
- Troubleshooting guide
- Feature documentation

## Support

**Created by:** Upower Energy  
**Contact:** george@upowerenergy.uk  
**Repository:** https://github.com/GeorgeDoors888/GB-Power-Market-JJ

---

**Version:** 1.0  
**Updated:** November 2025

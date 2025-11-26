# Dashboard V2 - Complete Package

## Quick Start

### 1. Setup Google Sheets
1. Create new Google Spreadsheet
2. Copy the Spreadsheet ID from URL
3. Go to Extensions → Apps Script
4. Copy contents of `apps-script/Code.gs`
5. Paste into Apps Script editor
6. Update `CONFIG.SPREADSHEET_ID` with your ID
7. Save and refresh spreadsheet

### 2. Setup Python Auto-Updater
```bash
# Install dependencies
pip3 install -r python-updaters/requirements.txt

# Add your service account credentials
cp your-credentials.json inner-cinema-credentials.json

# Update spreadsheet ID in scripts
# Edit python-updaters/complete_auto_updater.py

# Test run
python3 python-updaters/complete_auto_updater.py
```

### 3. Setup Auto-Refresh (Optional)
```bash
# Add to crontab
crontab -e

# Add line:
*/5 * * * * cd /path/to/dashboard && python3 python-updaters/complete_auto_updater.py >> logs/updater.log 2>&1
```

## Features

- ✅ Real-time data from Elexon BMRS
- ✅ Auto-updating charts (4 charts)
- ✅ Interactive constraint map
- ✅ BESS analysis
- ✅ Generator outages
- ✅ Custom menus and formatting

## Architecture

```
Google Sheets (UI)
      ↓
Apps Script (Menus, Maps)
      ↓
Python Updater (BigQuery → Sheets)
      ↓
BigQuery IRIS Tables (Real-time data)
```

## Support

See `SETUP_GUIDE.md` for detailed instructions.

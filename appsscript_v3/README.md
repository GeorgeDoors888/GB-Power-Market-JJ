# Apps Script Deployment Guide for Dashboard V3

## Overview
This directory contains the Apps Script files for the GB Energy Dashboard V3 DNO Map Selector.

## Files
- `Code.gs` - Main Apps Script code with menu and DNO selection logic
- `DnoMap.html` - HTML sidebar with Google Maps integration
- `appsscript.json` - Apps Script configuration

## Deployment Steps

### 1. Open Apps Script Editor
1. Open your Google Sheet: https://docs.google.com/spreadsheets/d/1LmMq4OEE639Y-XXpOJ3xnvpAmHB6vUovh5g6gaU_vzc/
2. Go to **Extensions → Apps Script**

### 2. Replace Existing Files
1. Delete any existing `Code.gs` file
2. Create new files with the contents from this directory:
   - `Code.gs`
   - `DnoMap.html` (File → New → HTML file)
   - Update `appsscript.json` if needed

### 3. Configure Google Maps API Key
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Navigate to your project: `inner-cinema-476211-u9`
3. Go to **APIs & Services → Credentials**
4. Create or use an existing **API Key**
5. Enable **Maps JavaScript API** for your project
6. Copy the API key
7. In `DnoMap.html`, replace `YOUR_GOOGLE_MAPS_API_KEY` with your actual key

### 4. Test the Integration
1. Reload your Google Sheet
2. You should see a new menu: **⚡ GB Energy**
3. Click **⚡ GB Energy → DNO Map Selector**
4. A sidebar should open with a map of GB showing DNO regions
5. Click a marker to select that DNO
6. Verify that cell `Dashboard!F3` updates with the DNO code
7. Verify that the KPI strip (J10:L10) updates to show DNO-specific metrics

## How It Works

1. **Menu Creation**: `onOpen()` adds the custom menu when the spreadsheet opens
2. **Sidebar Display**: `showDnoMap()` opens the HTML sidebar with Google Maps
3. **Data Loading**: `getDnoLocations()` reads DNO data from the `DNO_Map` sheet
4. **DNO Selection**: When user clicks a map marker, `selectDno(code)` writes to `Dashboard!F3`
5. **KPI Update**: The Dashboard formulas automatically recalculate based on the selected DNO

## Troubleshooting

### Map doesn't load
- Check that your Google Maps API key is valid
- Ensure Maps JavaScript API is enabled in your GCP project
- Check browser console for errors

### DNO selection doesn't work
- Verify the `DNO_Map` sheet exists and has data
- Check that cell `Dashboard!F3` is not locked or protected
- Ensure the Apps Script has permission to modify the spreadsheet

### Menu doesn't appear
- Refresh the page completely (Cmd+Shift+R on Mac)
- Check Apps Script execution logs for errors
- Verify `onOpen()` trigger is set up

## Alternative Deployment (clasp)

If you prefer using command-line tools:

```bash
# Install clasp
npm install -g @google/clasp

# Login
clasp login

# Clone your Apps Script project
clasp clone YOUR_SCRIPT_ID

# Copy files to the cloned directory
cp appsscript_v3/* .

# Push changes
clasp push
```

## Security Notes

- The API key in `DnoMap.html` is visible to anyone who can view the spreadsheet
- Consider restricting the API key to:
  - Your domain (if using Google Workspace)
  - Specific URLs (the Google Sheets domain)
  - Specific APIs (only Maps JavaScript API)

## Support

For issues or questions, refer to:
- [Apps Script Documentation](https://developers.google.com/apps-script)
- [Maps JavaScript API Documentation](https://developers.google.com/maps/documentation/javascript)

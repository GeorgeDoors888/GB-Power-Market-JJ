# Dashboard V2 - Complete Setup Guide

## Prerequisites

- Google Account with Sheets access
- GCP Project with BigQuery enabled
- Service Account with credentials JSON
- Python 3.9+ installed
- pip package manager

## Step-by-Step Setup

### 1. Create Google Spreadsheet

1. Go to https://sheets.google.com
2. Create new spreadsheet
3. Name it "GB Energy Dashboard V2"
4. Copy Spreadsheet ID from URL:
   `https://docs.google.com/spreadsheets/d/SPREADSHEET_ID_HERE/edit`

### 2. Deploy Apps Script

1. In spreadsheet: Extensions → Apps Script
2. Delete default code
3. Copy `apps-script/Code.gs` contents
4. Paste into editor
5. Update line 11:
   ```javascript
   SPREADSHEET_ID: 'YOUR_SPREADSHEET_ID_HERE',
   ```
6. File → Save (Ctrl+S)
7. Refresh spreadsheet - menus should appear

### 3. Setup Python Environment

```bash
# Navigate to package folder
cd Dashboard_V2_Package

# Install Python dependencies
pip3 install -r python-updaters/requirements.txt

# Copy your GCP service account credentials
cp /path/to/your-credentials.json ./inner-cinema-credentials.json
```

### 4. Configure Python Scripts

Edit `python-updaters/complete_auto_updater.py`:

Line 14: Update Spreadsheet ID
```python
SPREADSHEET_ID = 'YOUR_SPREADSHEET_ID_HERE'
```

Line 15-16: Update BigQuery project (if different)
```python
PROJECT_ID = 'your-gcp-project-id'
DATASET = 'your_dataset_name'
```

### 5. Test Manual Update

```bash
python3 python-updaters/complete_auto_updater.py
```

Should see:
```
🔄 Dashboard V2 Auto-Update
✅ Updated 20 fuel types
✅ Update complete!
```

### 6. Setup Auto-Refresh (Optional)

```bash
# Create logs folder
mkdir -p logs

# Edit crontab
crontab -e

# Add (update path):
*/5 * * * * cd /full/path/to/Dashboard_V2_Package && python3 python-updaters/complete_auto_updater.py >> logs/updater.log 2>&1

# Save and exit
# Updates will run every 5 minutes
```

### 7. Setup Webhook Server (Optional)

For real-time operations:

```bash
# Start webhook server
python3 python-updaters/webhook_server.py

# In another terminal, expose via ngrok
ngrok http 5001

# Copy ngrok URL and update in Code.gs:
# CONFIG.WEBHOOK_URL: 'https://your-ngrok-url.ngrok-free.app'

# Redeploy Apps Script
```

## Verification

1. Open your spreadsheet
2. Check menus appeared: Maps, Data, Format, Tools
3. Click Data → Refresh Dashboard
4. Verify data appears
5. Click Maps → Constraint Map
6. Should show interactive map

## Troubleshooting

**No menus?**
- Refresh spreadsheet (F5)
- Check Apps Script deployed correctly
- Check browser console for errors

**No data?**
- Check service account credentials
- Verify BigQuery project ID correct
- Check logs: `tail -f logs/updater.log`

**Charts not showing?**
- Data must exist in Daily_Chart_Data sheet
- Charts auto-update when data changes

## Next Steps

- Customize theme colors in Code.gs
- Add more BigQuery queries
- Create additional charts
- Setup monitoring/alerts

## Support

Repository: https://github.com/GeorgeDoors888/GB-Power-Market-JJ

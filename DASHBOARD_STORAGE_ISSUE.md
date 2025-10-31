# Automated Dashboard - Storage Full Solution

## Issue
Your Google Drive storage quota has been exceeded (403 error).

## Solutions

### Option 1: Use Existing Spreadsheet (RECOMMENDED)

Create a spreadsheet manually first, then update the script to use it:

1. **Create spreadsheet manually:**
   - Go to https://docs.google.com/spreadsheets
   - Create new spreadsheet
   - Name it "IRIS Real-Time Dashboard"
   - Copy the spreadsheet ID from URL: `https://docs.google.com/spreadsheets/d/[SPREADSHEET_ID]/edit`

2. **Update script to use existing spreadsheet:**

```python
# In automated_iris_dashboard.py, line 22, replace:
SPREADSHEET_NAME = "IRIS Real-Time Dashboard"

# With:
SPREADSHEET_ID = "YOUR_SPREADSHEET_ID_HERE"  # Paste ID from step 1

# Then in get_or_create_spreadsheet(), replace:
self.spreadsheet = self.gc.open(SPREADSHEET_NAME)

# With:
self.spreadsheet = self.gc.open_by_key(SPREADSHEET_ID)
```

### Option 2: Free Up Drive Storage

Go to https://drive.google.com/drive/quota and delete old files:
- Empty trash
- Delete large files
- Remove old backups

### Option 3: Use Different Google Account

Use a different Google account with available storage:
1. Create new service account in different project
2. Download new key JSON
3. Update `SERVICE_ACCOUNT_FILE` in script

### Option 4: Share Existing Sheet with Service Account

1. Open any existing Google Sheet
2. Click "Share"
3. Add service account email (from `jibber_jabber_key.json`):
   ```bash
   cat jibber_jabber_key.json | grep client_email
   ```
4. Give it "Editor" permissions
5. Use that spreadsheet ID in the script

---

## Quick Fix Script

I'll create a version that works with a specific spreadsheet ID instead of creating new ones.

# CLASP + Python Integration for Google Sheets

Complete setup for Python-first development with Apps Script UI layer.

## Architecture

```
┌─────────────────────┐
│  Google Sheets      │
│  (User Interface)   │
└──────────┬──────────┘
           │
           │ User clicks menu/button
           ▼
┌─────────────────────┐
│  Apps Script        │  ← UI Layer Only
│  (Code.gs)          │  - Menus, buttons
│                     │  - Formatting, layout
└──────────┬──────────┘  - Design changes
           │
           │ HTTP POST to webhook
           ▼
┌─────────────────────┐
│  Flask Server       │
│  (webhook_server.py)│
└──────────┬──────────┘
           │
           │ Calls Python functions
           ▼
┌─────────────────────┐
│  Python Backend     │  ← All Logic Here
│  (python_backend.py)│  - BigQuery queries
│                     │  - Data processing
│                     │  - Calculations
│                     │  - Updates sheet via API
└─────────────────────┘
```

## Quick Start

### 1. First-Time Setup

Open the Google Sheet in browser:
https://docs.google.com/spreadsheets/d/1MSl8fJ0to6Y08enXA2oysd8wvNUVm3AtfJ1bVqRH8_I/edit

Go to: **Extensions → Apps Script**

You'll see the script editor. Get the Script ID from the URL:
```
https://script.google.com/home/projects/YOUR_SCRIPT_ID_HERE/edit
```

Update `.clasp.json` with that Script ID:
```json
{
  "scriptId": "YOUR_SCRIPT_ID_HERE",
  "rootDir": "./src",
  "parentId": "1MSl8fJ0to6Y08enXA2oysd8wvNUVm3AtfJ1bVqRH8_I"
}
```

### 2. Deploy Apps Script (from VSCode terminal)

```bash
cd /home/george/GB-Power-Market-JJ/clasp-sheet-project

# Push code to Google Apps Script
clasp push

# Open in browser to test
clasp open
```

That's it! No authentication needed after first setup.

### 3. Start Python Webhook Server

```bash
# Start Flask server
python3 webhook_server.py

# In another terminal, expose via ngrok (if remote server)
ngrok http 5002

# Copy the ngrok URL (e.g., https://abc123.ngrok.io)
```

### 4. Configure Webhook in Sheet

1. Open your Google Sheet
2. Click **⚡ Automation → ⚙️ Settings**
3. Paste ngrok URL: `https://abc123.ngrok.io/api/refresh`
4. Click OK

### 5. Test It!

In Google Sheet:
1. Click **⚡ Automation → 🔄 Refresh Data**
2. Python runs, queries BigQuery, updates sheet
3. See results in "Data" tab

## Development Workflow

### Making UI Changes (Apps Script)

Edit `src/Code.gs` in VSCode, then:

```bash
clasp push
```

Changes appear instantly in your sheet. No browser needed!

### Making Data Changes (Python)

Edit `python_backend.py`, changes apply immediately (Flask auto-reloads in debug mode).

### File Structure

```
clasp-sheet-project/
├── .clasp.json              # Clasp configuration
├── src/
│   ├── appsscript.json      # Apps Script manifest
│   └── Code.gs              # Apps Script code (UI only)
├── python_backend.py        # Main Python logic
├── webhook_server.py        # Flask webhook endpoint
└── README.md                # This file
```

## Common Tasks

### Add New Menu Item

Edit `src/Code.gs`, add to `onOpen()` function:

```javascript
ui.createMenu('⚡ Automation')
  .addItem('🔄 Refresh Data', 'triggerPythonRefresh')
  .addItem('📊 New Feature', 'myNewFunction')  // ← Add this
  .addToUi();

// Then create the function:
function myNewFunction() {
  // Your Apps Script code here
  // Or call Python via webhook
}
```

Deploy:
```bash
clasp push
```

### Add New Python Function

Edit `python_backend.py`:

```python
def my_new_analysis():
    """New analysis function"""
    # Your BigQuery/Pandas logic here
    return {'success': True, 'data': results}
```

Update `webhook_server.py` to expose it:

```python
@app.route('/api/new-analysis', methods=['POST'])
def handle_new_analysis():
    result = my_new_analysis()
    return jsonify(result)
```

Call from Apps Script:

```javascript
const response = UrlFetchApp.fetch(
  PYTHON_WEBHOOK + '/api/new-analysis',
  {method: 'post', contentType: 'application/json'}
);
```

### Apply Custom Formatting

Apps Script handles this (design changes):

```javascript
function applyCustomFormat() {
  const sheet = SpreadsheetApp.getActiveSheet();
  
  // Header styling
  sheet.getRange('A1:Z1')
       .setBackground('#ff6d00')
       .setFontColor('#ffffff')
       .setFontWeight('bold');
  
  // Number formatting
  sheet.getRange('B2:B100')
       .setNumberFormat('£#,##0.00');
  
  // Conditional formatting
  // ... your design rules
}
```

Deploy:
```bash
clasp push
```

## Deployment Commands

### Update Apps Script
```bash
clasp push          # Push all changes
clasp push --watch  # Auto-push on file save
clasp open          # Open in browser
```

### Pull Latest (if edited in browser)
```bash
clasp pull
```

### View Logs
```bash
clasp logs          # See Apps Script console logs
clasp logs --watch  # Live tail
```

## Production Setup

### 1. Use Permanent Webhook URL

Replace ngrok with:
- Deploy Flask to Railway/Render/Vercel
- Or use existing server with public URL
- Update webhook URL in sheet settings

### 2. Add Authentication

Update `webhook_server.py`:

```python
API_KEY = os.getenv('WEBHOOK_API_KEY', 'your-secret-key')

@app.before_request
def verify_auth():
    if request.headers.get('X-API-Key') != API_KEY:
        return jsonify({'error': 'Unauthorized'}), 401
```

Update Apps Script:

```javascript
const options = {
  method: 'post',
  contentType: 'application/json',
  headers: {
    'X-API-Key': 'your-secret-key'
  },
  payload: JSON.stringify(data)
};
```

### 3. Set Up Automated Triggers

In Google Sheet:
1. **Extensions → Apps Script**
2. Click clock icon (Triggers)
3. Add trigger: `scheduledRefresh` → Time-driven → Daily/Hourly

Now Python runs automatically on schedule!

## Tips

✅ **Keep Apps Script minimal** - Only UI/formatting code  
✅ **All logic in Python** - Easier to test and maintain  
✅ **Use clasp push often** - Instant deployment  
✅ **Test in sheet immediately** - See changes live  
✅ **Version control** - Git tracks both Apps Script and Python  

## Troubleshooting

**"Invalid grant" error with clasp:**
- You're on remote server without browser
- Use manual copy/paste (Extensions → Apps Script in browser)
- Or run clasp from local machine

**Webhook not responding:**
- Check Flask server is running: `ps aux | grep webhook_server`
- Check ngrok is running: `curl http://localhost:4040/api/tunnels`
- Verify URL in sheet settings

**Apps Script can't find function:**
- Did you run `clasp push`?
- Check script editor in browser (Extensions → Apps Script)
- Look for syntax errors in `Code.gs`

**Sheet not updating:**
- Check Python logs for errors
- Verify credentials file exists: `/home/george/inner-cinema-credentials.json`
- Test Python directly: `python3 python_backend.py`

## Next Steps

1. **Customize** `python_backend.py` with your BigQuery queries
2. **Add menu items** in `Code.gs` for new features
3. **Design** sheet layout using Apps Script formatting functions
4. **Deploy** with `clasp push` whenever you make changes
5. **Automate** with time-driven triggers

---

**Support:** See existing examples in `/home/george/GB-Power-Market-JJ/bess-apps-script/`

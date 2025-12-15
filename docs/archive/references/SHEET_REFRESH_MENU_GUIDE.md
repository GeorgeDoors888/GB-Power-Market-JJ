# 🔄 Sheet Refresh Menu - Quick Guide

## What This Does

Adds a **custom menu to your Google Sheet** that lets you refresh data with one click - no need to run Python commands manually!

**Menu Location**: Top menu bar → **⚡ Power Market**

---

## ✨ Quick Setup (5 minutes)

### 1. Install Google Apps Script

1. **Open your sheet**: https://docs.google.com/spreadsheets/d/1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA/
2. **Click**: Extensions > Apps Script
3. **Delete** any existing code
4. **Open** the file: `google_sheets_menu.gs` (in your project folder)
5. **Copy all the code** from that file
6. **Paste** into Apps Script editor
7. **Save** (💾 icon or Cmd+S)
8. **Close** Apps Script tab
9. **Refresh** your Google Sheet
10. **Look for** new menu: **⚡ Power Market**

### 2. Start the Watcher

In a terminal:
```bash
cd ~/GB\ Power\ Market\ JJ
python3 watch_sheet_for_refresh.py
```

**Leave this running!** It monitors the sheet for refresh requests.

### 3. Test It!

1. In your Google Sheet, click: **⚡ Power Market** > **🔄 Refresh Data Now**
2. You'll see a dialog: "Refresh Requested"
3. Cell **L5** shows: **⏳ Refreshing...**
4. Wait 30-60 seconds
5. Cell **L5** changes to: **✅ Up to date**
6. Refresh browser to see new data!

---

## 📋 Menu Options

| Menu Item | What It Does |
|-----------|-------------|
| **🔄 Refresh Data Now** | Refreshes with current date range (from cell B5) |
| **📊 Quick Refresh (1 Week)** | Sets B5 to "1 Week" AND refreshes |
| **📊 Quick Refresh (1 Month)** | Sets B5 to "1 Month" AND refreshes |
| **ℹ️ Help** | Shows help dialog |

---

## 🎯 How It Works

```
┌─────────────────┐
│  Google Sheet   │
│                 │
│  Click Menu:    │
│  ⚡ Power Market│
│  └─ 🔄 Refresh  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Apps Script     │
│ Writes trigger  │
│ to cell M5      │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Python Watcher  │
│ Detects trigger │
│ in M5           │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Runs Update     │
│ Script          │
│ update_analysis │
│ _bi_enhanced.py │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Updates Sheet   │
│ L5: ✅ Complete │
└─────────────────┘
```

---

## 📊 Status Indicators (Cell L5)

| Status | Meaning |
|--------|---------|
| **✅ Ready** | Sheet ready, no refresh in progress |
| **⏳ Refreshing...** | Python script running, wait 30-60s |
| **✅ Up to date** | Refresh complete! Refresh browser to see data |
| **❌ Error** | Refresh failed - check watcher terminal |
| **❌ Timeout** | Took >3 minutes - may need to run manually |

---

## 🔧 Run Watcher in Background (Recommended)

Instead of leaving terminal open, use `screen`:

```bash
# Start screen session
screen -S sheet-watcher

# Navigate and start watcher
cd ~/GB\ Power\ Market\ JJ
python3 watch_sheet_for_refresh.py

# Detach (keep it running)
# Press: Ctrl+A then D

# Later, reattach to check status
screen -r sheet-watcher
```

Or use `nohup`:

```bash
cd ~/GB\ Power\ Market\ JJ
nohup python3 watch_sheet_for_refresh.py > sheet_watcher.log 2>&1 &

# Check if running
ps aux | grep watch_sheet

# View log
tail -f sheet_watcher.log
```

---

## 🔍 Troubleshooting

### Menu doesn't appear
✅ **Solution**:
- Refresh sheet (Cmd+R / Ctrl+R)
- Close and reopen sheet
- Check Apps Script saved successfully
- Clear browser cache

### Click refresh but nothing happens
✅ **Solution**:
- Check watcher is running: `ps aux | grep watch_sheet`
- If not: `python3 watch_sheet_for_refresh.py`
- Check watcher terminal for errors

### Status stuck on "⏳ Refreshing..."
✅ **Solution**:
- Check watcher terminal output
- May indicate BigQuery or auth error
- Try manual refresh: `python3 update_analysis_bi_enhanced.py`
- Restart watcher script

### Status shows "❌ Error"
✅ **Solution**:
- Check watcher terminal for error details
- Run update script manually to see full error:
  ```bash
  python3 update_analysis_bi_enhanced.py
  ```
- Common issues:
  - BigQuery quota exceeded (wait a few minutes)
  - Authentication expired (re-auth required)
  - Network timeout (retry)

### Watcher stops working
✅ **Solution**:
- Restart watcher: `python3 watch_sheet_for_refresh.py`
- Check for errors in watcher log
- Verify Google Sheets API quota not exceeded

---

## 💡 Tips

### 1. Keep Watcher Running
Start watcher in background so menu always works:
```bash
screen -S sheet-watcher
python3 watch_sheet_for_refresh.py
# Ctrl+A, D to detach
```

### 2. Quick Date Range Changes
Use the "Quick Refresh" menu options instead of manually changing B5:
- **Quick Refresh (1 Week)** - Fast weekly refresh
- **Quick Refresh (1 Month)** - Monthly view

### 3. Monitor Refresh Progress
Watch watcher terminal to see:
- When refresh requested
- Update script output
- Success/failure status
- Timestamps

### 4. Manual Refresh Still Works
If menu isn't working, you can always run:
```bash
python3 update_analysis_bi_enhanced.py
```

### 5. Check Watcher Status
```bash
# Is watcher running?
ps aux | grep watch_sheet_for_refresh

# View recent activity
tail -20 sheet_watcher.log
```

---

## 📁 Files

| File | Purpose |
|------|---------|
| `google_sheets_menu.gs` | Google Apps Script code (paste into Sheet) |
| `watch_sheet_for_refresh.py` | Python watcher (monitors for refresh requests) |
| `update_analysis_bi_enhanced.py` | Data refresh script (called by watcher) |
| `setup_sheet_refresh_menu.py` | Setup helper (shows instructions) |
| `SHEET_REFRESH_MENU_GUIDE.md` | This guide |

---

## 🚀 Automated Setup Script

For quick setup instructions:
```bash
python3 setup_sheet_refresh_menu.py
```

---

## ✅ Success Checklist

- [ ] Google Apps Script installed in sheet
- [ ] Menu "⚡ Power Market" appears in sheet
- [ ] Watcher script running (`watch_sheet_for_refresh.py`)
- [ ] Clicked "Refresh Data Now" and saw dialog
- [ ] Cell L5 showed "⏳ Refreshing..."
- [ ] Watcher terminal showed refresh activity
- [ ] Cell L5 changed to "✅ Up to date"
- [ ] Refreshed browser and saw updated data

---

**All working?** Enjoy your one-click data refresh! 🎉

**Problems?** Run: `python3 setup_sheet_refresh_menu.py` for detailed help

# 🚀 Quick Start: Add Charts in 5 Minutes

## Step-by-Step Installation

### 1️⃣ Open Apps Script (30 seconds)
```
Your Google Sheet → Extensions → Apps Script
```

### 2️⃣ Copy & Paste Code (1 minute)
1. Open file: `google_apps_script_charts.js`
2. Copy ALL code
3. Paste into Apps Script editor
4. Save (Ctrl+S)

### 3️⃣ Run Setup (2 minutes)
1. Select function: `createAllCharts`
2. Click ▶ Run
3. Grant permissions (first time only)
4. Wait for "✅ Charts created successfully!"

### 4️⃣ View Your Charts! (1 minute)
Go back to your spreadsheet - you should see **4 beautiful charts**!

---

## ✅ That's It!

Charts will auto-update whenever data changes in A18:H28.

**Optional**: Set up auto-refresh every 30 minutes:
- Click ⏰ Clock icon → Add Trigger
- Function: `updateCharts` | Every 30 minutes

---

## 📊 What You Get

🔵 **Generation Chart** - Line graph showing power generation trends  
🔴 **Frequency Chart** - Line graph tracking system frequency (49.8-50.2 Hz)  
🟡 **Price Chart** - Bar graph of system sell prices  
📈 **Combined Chart** - All metrics on one chart with dual Y-axes

All charts update automatically! ✨

---

## 🎛️ New Menu Available

Look for: **⚡ Dashboard Charts** menu in your spreadsheet

- 🔄 Recreate All Charts
- 📊 Update Data
- ℹ️ About

---

## 🔧 Quick Fixes

**Charts don't appear?**  
→ Run dashboard script first: `./.venv/bin/python dashboard_clean_design.py`  
→ Then run `createAllCharts` in Apps Script

**Wrong data showing?**  
→ Check range A19:D28 has settlement period data  
→ Run `createAllCharts` again

**Charts overlap?**  
→ Edit `CHART_START_ROW` and `CHART_START_COL` in script  
→ Default: Row 35, Column J (right side of sheet)

---

## 📖 Full Documentation

See detailed guide: `APPS_SCRIPT_INSTALLATION.md`

---

**Dashboard**: https://docs.google.com/spreadsheets/d/12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8

# 🚀 Apps Script Manual Execution Guide

## ⚠️ Why Manual Execution is Required
Google Apps Script API **cannot execute functions** with service accounts due to security restrictions. You must run these functions manually once to set up the dashboard.

---

## 📋 Step-by-Step Instructions

### 1️⃣ Open the Apps Script Editor

**Click this link:**
```
https://script.google.com/d/1c9BJqrtruVFh_LT_IWrHOpJIy8c29_zH6v1Co8-KHU9R1o9g2wZZERH5/edit
```

Or manually:
1. Open Google Sheets: [Dashboard V3](https://docs.google.com/spreadsheets/d/1LmMq4OEE639Y-XXpOJ3xnvpAmHB6vUovh5g6gaU_vzc)
2. Click **Extensions → Apps Script**

---

### 2️⃣ Execute buildAllCharts()

**Purpose:** Creates all 7 visual charts on the dashboard

**Steps:**
1. In the Apps Script editor, find the function dropdown (top bar)
2. Select **`buildAllCharts`** from the dropdown
3. Click the **▶ Run** button
4. If prompted, click **Review Permissions** → Select your Google account → **Allow**
5. Wait for execution to complete (~10-15 seconds)
6. Check the **Execution log** at bottom for success messages

**Expected Result:**
```
Charts created:
✅ Prices Chart (SSP/SBP/Mid)
✅ Demand vs Generation Chart
✅ Interconnector Flows Chart
✅ Balancing Mechanism Costs Chart
✅ Wind Performance Chart
✅ System Frequency Chart
✅ Generator Outages Chart
```

---

### 3️⃣ Execute formatDashboard()

**Purpose:** Applies color formatting, column widths, and styling

**Steps:**
1. From the function dropdown, select **`formatDashboard`**
2. Click the **▶ Run** button
3. Wait for execution to complete (~5 seconds)

**Expected Result:**
```
Formatting applied:
✅ Header row: Blue background (#4A90E2)
✅ KPI Strip: Light blue (#E3F2FD)
✅ Table headers: Yellow/Green/Orange
✅ Column widths optimized
✅ Row heights adjusted
```

---

### 4️⃣ Assign Button to RefreshDashboard()

**Purpose:** Create a button to manually trigger data refresh

**Steps:**
1. Go back to your **Google Sheet** (Dashboard tab)
2. Click **Insert → Drawing**
3. Create a button shape:
   - Click **Shapes** → Select rectangle
   - Add text: "🔄 Refresh Dashboard"
   - Style: Blue background, white text
4. Click **Save and Close**
5. Click the button image → Three dots (⋮) → **Assign script**
6. Type: `RefreshDashboard`
7. Click **OK**

**Test the button:**
- Click the "🔄 Refresh Dashboard" button
- Should see a popup showing current filter values
- Timestamp in A2 should update

---

### 5️⃣ (Optional) Set Up Daily Chart Rebuild

**Purpose:** Automatically rebuild charts daily at 3 AM

**Steps:**
1. In Apps Script editor, select **`installDailyChartRebuild`** from dropdown
2. Click **▶ Run**
3. Verify trigger created: Click **⏰ Triggers** (left sidebar)
4. Should see: `buildAllCharts` runs daily at 3:00-4:00 AM

---

## ✅ Verification Checklist

After completing all steps:

- [ ] 7 charts visible on Dashboard tab
- [ ] Dashboard has proper color formatting
- [ ] "Refresh Dashboard" button works
- [ ] Charts show live data from Chart_* sheets
- [ ] All data auto-updating every 5 minutes (via Dell cron)

---

## 🔍 Troubleshooting

### "Script not found" error
- Make sure you're logged into the correct Google account
- Try the direct link again

### "Authorization required" popup
- This is normal on first run
- Click "Review Permissions" → Allow access
- Google requires this for any Apps Script that accesses Sheets

### Charts not showing data
- Check that Chart_* sheets have data
- Run `dashboard_pipeline.py` on Dell server
- Verify cron is running: `ssh dell "crontab -l"`

### Button doesn't work
- Make sure you typed `RefreshDashboard` exactly (case-sensitive)
- Try reassigning the script to the button

---

## 📊 Current System Status

**✅ Automated (Dell Server):**
- Dashboard data updates: Every 5 minutes
- Wind performance data: Every 5 minutes
- Frequency data: Every 5 minutes
- Outages data: Every 10 minutes
- Comprehensive updates: Every 15 minutes

**⚠️ Manual (One-Time Setup):**
- Create visual charts: `buildAllCharts()`
- Apply formatting: `formatDashboard()`
- Assign refresh button: Link to `RefreshDashboard()`

---

## 🎯 Quick Links

- **Apps Script Editor:** https://script.google.com/d/1c9BJqrtruVFh_LT_IWrHOpJIy8c29_zH6v1Co8-KHU9R1o9g2wZZERH5/edit
- **Dashboard Spreadsheet:** https://docs.google.com/spreadsheets/d/1LmMq4OEE639Y-XXpOJ3xnvpAmHB6vUovh5g6gaU_vzc
- **Script ID:** 1c9BJqrtruVFh_LT_IWrHOpJIy8c29_zH6v1Co8-KHU9R1o9g2wZZERH5
- **Spreadsheet ID:** 1LmMq4OEE639Y-XXpOJ3xnvpAmHB6vUovh5g6gaU_vzc

---

**Estimated Time:** 5-10 minutes for complete setup

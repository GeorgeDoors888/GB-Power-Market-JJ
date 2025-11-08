# 🚀 Apps Script Installation - Visual Guide

## What I've Done For You

✅ **Opened your Google Sheet** in the browser  
✅ **Opened the code file** (`google_sheets_dashboard.gs`) in VS Code  
✅ **Created this guide** to walk you through installation  

---

## 📸 Step-by-Step with Screenshots

### Step 1: Open Apps Script Editor (30 seconds)

**In the Google Sheet tab I opened:**

```
┌─────────────────────────────────────────┐
│  File  Edit  View  Insert  Format  ... │
│  ┌─────────────────────────────────┐   │
│  │  Extensions  ← CLICK HERE       │   │
│  │    ├─ Add-ons                   │   │
│  │    ├─ Apps Script  ← THEN THIS  │   │
│  │    └─ Macros                    │   │
│  └─────────────────────────────────┘   │
└─────────────────────────────────────────┘
```

**Result:** A new tab opens with the Apps Script editor

---

### Step 2: Clear Existing Code (10 seconds)

**In the Apps Script editor tab:**

```
┌─────────────────────────────────────────┐
│  Code.gs                          [x]   │
│  ┌─────────────────────────────────┐   │
│  │ function myFunction() {         │   │
│  │                                 │   │
│  │ }                               │   │
│  │                                 │   │
│  └─────────────────────────────────┘   │
└─────────────────────────────────────────┘
```

**Action:** Select All (Cmd+A) → Delete

---

### Step 3: Copy Code from VS Code (20 seconds)

**In the VS Code tab (I opened this for you):**

```
┌─────────────────────────────────────────┐
│  google_sheets_dashboard.gs            │
│  ┌─────────────────────────────────┐   │
│  │ /************************       │   │
│  │  * GB POWER MARKET - LIVE       │   │
│  │  * DASHBOARD (Apps Script)      │   │
│  │  ************************/       │   │
│  │                                 │   │
│  │ const VERCEL_PROXY = 'https://  │   │
│  │ ...                             │   │
│  │ (549 lines total)               │   │
│  └─────────────────────────────────┘   │
└─────────────────────────────────────────┘
```

**Action:** 
1. Click in the file
2. Select All (Cmd+A)
3. Copy (Cmd+C)

---

### Step 4: Paste into Apps Script Editor (10 seconds)

**Back in the Apps Script editor tab:**

```
┌─────────────────────────────────────────┐
│  Code.gs                    [💾 Save]  │
│  ┌─────────────────────────────────┐   │
│  │ (empty - you just deleted it)   │   │
│  │                                 │   │
│  │ ← CLICK HERE and PASTE (Cmd+V) │   │
│  │                                 │   │
│  └─────────────────────────────────┘   │
└─────────────────────────────────────────┘
```

**Action:** 
1. Click in the editor
2. Paste (Cmd+V)
3. Click **Save** (💾 icon) or press Cmd+S

---

### Step 5: Run Setup (30 seconds)

**In the Apps Script editor (after pasting):**

```
┌─────────────────────────────────────────┐
│  [▶ Run] [🐛 Debug]  ┌─────────────┐   │
│                      │ Select func │   │
│  ┌─────────────────────────────────┐   │
│  │ /************************       │   │
│  │  * GB POWER MARKET...           │   │
│  │                                 │   │
│  └─────────────────────────────────┘   │
└─────────────────────────────────────────┘
```

**Action:**
1. Click dropdown next to **Run** button
2. Select: `Setup_Dashboard_AutoRefresh`
3. Click **▶ Run**

---

### Step 6: Authorize Script (30 seconds)

**You'll see this dialog:**

```
┌──────────────────────────────────────┐
│  Authorization Required              │
│                                      │
│  This project requires your          │
│  permission to access your data      │
│                                      │
│  [Review permissions]  [Cancel]      │
└──────────────────────────────────────┘
```

**Action:** Click **Review permissions**

**Then you'll see:**

```
┌──────────────────────────────────────┐
│  Choose an account                   │
│                                      │
│  your-email@gmail.com                │
│                                      │
└──────────────────────────────────────┘
```

**Action:** Click your email

**Then you'll see a warning:**

```
┌──────────────────────────────────────┐
│  ⚠️ Google hasn't verified this app  │
│                                      │
│  This app hasn't been verified...    │
│                                      │
│  [Advanced ▼]  [Back to safety]      │
└──────────────────────────────────────┘
```

**Action:** 
1. Click **Advanced**
2. Click **Go to GB Power Market Dashboard (unsafe)**
   - Don't worry - it's YOUR script, completely safe!

**Finally:**

```
┌──────────────────────────────────────┐
│  GB Power Market Dashboard wants to: │
│                                      │
│  ✓ View and manage spreadsheets     │
│    in Google Drive                   │
│                                      │
│  [Allow]  [Cancel]                   │
└──────────────────────────────────────┘
```

**Action:** Click **Allow**

---

### Step 7: Wait for Setup to Complete (10-30 seconds)

**You'll see this alert in your Google Sheet:**

```
┌──────────────────────────────────────┐
│  ✅ Setup Complete!                  │
│                                      │
│  Your live dashboard is ready:       │
│                                      │
│  ✅ All sheets created               │
│  ✅ Data refreshed from BigQuery     │
│  ✅ Chart built and linked           │
│  ✅ Auto-refresh enabled (5 min)     │
│                                      │
│  Check the "Live Dashboard" tab!     │
│                                      │
│  [OK]                                │
└──────────────────────────────────────┘
```

**Action:** Click **OK**

---

## ✅ Verification

**After setup completes, you should see:**

### 1. New Menu
```
┌─────────────────────────────────────────┐
│  File Edit View ... ⚡ Power Market     │
│                      ├─ 🔄 Refresh Now  │
│                      ├─ 📊 Rebuild...   │
│                      ├─ ⏰ Set Auto...  │
│                      └─ 🛑 Stop Auto... │
└─────────────────────────────────────────┘
```

### 2. New Tabs (at bottom)
```
Live Dashboard | Chart Data | Audit_Log | Live_Raw_Prices | ...
```

### 3. Data in Live Dashboard Tab
```
┌────┬────────┬──────────┬──────────┬───────────┬────────────┐
│ SP │  Time  │ SSP £/MWh│ SBP £/MWh│ Demand MW │ Gen MW     │
├────┼────────┼──────────┼──────────┼───────────┼────────────┤
│ 1  │ 00:00  │  45.32   │  48.50   │  28,450   │  29,120    │
│ 2  │ 00:30  │  44.18   │  47.25   │  27,890   │  28,540    │
│ 3  │ 01:00  │  43.95   │  46.80   │  27,320   │  27,950    │
...
│ 48 │ 23:30  │  52.40   │  55.90   │  32,180   │  33,240    │
└────┴────────┴──────────┴──────────┴───────────┴────────────┘
```

### 4. Chart Displayed
```
┌──────────────────────────────────────────────┐
│  GB Power Market - Live Dashboard (Today)    │
│                                              │
│  [Chart showing lines for SSP/SBP prices,    │
│   areas for demand/generation, etc.]         │
│                                              │
└──────────────────────────────────────────────┘
```

---

## 🐛 Troubleshooting

### Issue: "Authorization required" keeps appearing
**Fix:** Complete Step 6 fully - don't skip the "unsafe" warning

### Issue: "Script error" or "Function not found"
**Fix:** Make sure you pasted the ENTIRE file (549 lines)

### Issue: "HTTP 500" error
**Fix:** Check that VERCEL_PROXY line says `/api/proxy-v2` (not `/api/proxy`)

### Issue: No data in dashboard
**Fix:** 
1. Check Audit_Log tab for error details
2. Run Python dashboard first: `make today`
3. Verify Vercel proxy working: https://gb-power-market-jj.vercel.app/api/proxy-v2?path=/health

### Issue: Chart not showing
**Fix:** Click **⚡ Power Market** → **📊 Rebuild Chart**

---

## 🎯 What to Do Next

Once setup is complete:

### Test the Dashboard
1. Click **⚡ Power Market** → **🔄 Refresh Now (today)**
2. Wait 10-20 seconds
3. Check **Live Dashboard** tab for fresh data

### Check Auto-Refresh
1. Wait 5 minutes
2. Check **Audit_Log** tab - should show new entry every 5 min

### Review Configuration
1. Open Apps Script editor
2. Check lines 23-26:
   ```javascript
   const VERCEL_PROXY = 'https://gb-power-market-jj.vercel.app/api/proxy-v2';
   const PROJECT = 'inner-cinema-476211-u9';
   const DATASET = 'uk_energy_prod';
   const TZ = 'Europe/London';
   ```

---

## 📚 Additional Resources

- **Full Guide:** `GOOGLE_SHEETS_APPS_SCRIPT_GUIDE.md` (450 lines)
- **Quick Reference:** `APPS_SCRIPT_QUICK_REF.md` (short version)
- **Code Review:** `APPS_SCRIPT_CODE_REVIEW.md` (technical details)

---

## 🔒 Security Note

This script is **completely safe**:
- ✅ Only accesses YOUR Google Sheet (read/write)
- ✅ Only reads data from BigQuery (via Vercel proxy)
- ✅ No credentials stored in sheet
- ✅ All communications use HTTPS
- ✅ You can review all 549 lines of code before authorizing

The "unsafe" warning appears because:
- Google requires apps to go through verification process
- This is YOUR personal script (not published app)
- It's 100% safe - you wrote it (with my help!)

---

**Ready?** Follow Steps 1-7 above and you'll be done in 2-3 minutes! 🚀

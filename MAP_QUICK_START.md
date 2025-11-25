# 🗺️ QUICK START: Embed Constraint Map in Dashboard

## ✅ What You're Getting

An **interactive map INSIDE your Dashboard sheet** - not an external link!

- Opens in **right sidebar** (stays in Google Sheets)
- Shows **live constraint data** with color coding 🟢🟡🟠🔴
- **Click boundaries** to see flow/limit/margin details
- **Auto-updates** every 5 minutes from BigQuery
- **Toggle layers**: Boundaries, DNO, TNUoS, GSP

---

## 🚀 5-Minute Installation

### 1️⃣ Open Apps Script
In your Dashboard spreadsheet:
```
Extensions → Apps Script
```

### 2️⃣ Add Main Code
- Delete any existing code
- Open: `dashboard/apps-script/constraint_map.gs`
- Copy ALL code
- Paste into Apps Script editor
- File stays as `Code.gs`

### 3️⃣ Add HTML File
In Apps Script:
```
File → New → HTML file
```
- Name it: `ConstraintMap` (exactly this)
- Open: `dashboard/apps-script/constraint_map.html`
- Copy ALL code
- Paste into the HTML file

### 4️⃣ Save & Authorize
Click the **💾 Save** button, then:
```
Run → onOpen
```
- You'll be asked to authorize
- Click "Review Permissions"
- Select your Google account
- Click "Advanced"
- Click "Go to [Project] (unsafe)"
- Click "Allow"

### 5️⃣ Launch the Map!
- Close Apps Script editor
- Refresh your spreadsheet (F5 or Cmd+R)
- You'll see a new menu: **🗺️ Constraint Map**
- Click: **🗺️ Constraint Map → 📍 Show Interactive Map**
- **Map opens in RIGHT SIDEBAR!**

---

## 🎨 Using the Map

### Color Meanings
- **🟢 Green**: <50% utilization (All good)
- **🟡 Yellow**: 50-75% utilization (Watch it)
- **🟠 Orange**: 75-90% utilization (High stress)
- **🔴 Red**: >90% utilization (Critical!)

### Controls
Top of map has checkboxes to show/hide:
- ☑️ **Boundaries** (transmission constraints)
- ☑️ **DNO** (distribution areas)
- ☑️ **TNUoS** (generation zones)
- ☐ **GSP** (grid supply points)

### Click Boundaries
Click any colored circle to see:
- Flow vs Limit (MW)
- Utilization %
- Available margin
- Constraint status

### Refresh Data
Menu: **🗺️ Constraint Map → 🔄 Refresh Map Data**

---

## 🔧 Troubleshooting

**❌ Menu doesn't appear**
- Make sure both files are saved
- Refresh spreadsheet (F5)
- Re-run: `Run → onOpen` in Apps Script

**❌ Map shows no data**
- Run: `python3 update_constraints_dashboard_v2.py`
- Check Dashboard rows 116-126 have constraint data
- Wait 30 seconds and refresh map

**❌ Authorization error**
- Go back to Apps Script
- Run: `Run → onOpen` again
- Complete authorization flow

**❌ "ConstraintMap not found" error**
- Check HTML file is named **exactly** `ConstraintMap` (case-sensitive)
- No `.html` extension in the name field

---

## 📍 What's Happening Behind the Scenes

1. **Apps Script** reads constraint data from Dashboard rows 116-126
2. **Google Maps API** creates interactive map
3. **Color coding** applied based on utilization %
4. **Data updates** automatically when `update_constraints_dashboard_v2.py` runs
5. **Sidebar** keeps you in the spreadsheet (no external tabs)

---

## 🆘 Still Need Help?

Check the full guide:
```
dashboard/apps-script/INSTALLATION_GUIDE.md
```

Or check Dashboard row 165 for instructions.

---

## 🎉 Success Looks Like This

When working, you'll see:
1. New menu item: **🗺️ Constraint Map**
2. Map opens in **RIGHT SIDEBAR**
3. Colored circles on UK map
4. Clickable popups with constraint details
5. Layer toggle checkboxes at top

The map is **embedded in your sheet** - no external links, no leaving Google Sheets!

---

**Files you need:**
- `dashboard/apps-script/constraint_map.gs` (Apps Script code)
- `dashboard/apps-script/constraint_map.html` (Map HTML)

**Time to install:** 5 minutes  
**Result:** Professional interactive map in your Dashboard  

🗺️ **Happy Mapping!**

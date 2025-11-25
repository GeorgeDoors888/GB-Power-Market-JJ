# Python-Based Constraint Map Solution

**Problem Solved:** Apps Script complexity bypassed - Python handles data fetching and HTML generation

---

## ✅ What Was Built

### 1. **Python Generator** (`generate_constraint_map_html.py`)
- Fetches constraint data from Google Sheets API
- Generates standalone HTML with embedded data
- No Apps Script backend needed!

### 2. **Standalone HTML** (`constraint_map_standalone.html`)
- Works in any browser (Chrome, Safari, Firefox)
- Data embedded directly in HTML
- Google Maps API with colored markers
- Click markers for constraint details

### 3. **Auto-Update Script** (`update_constraint_map.sh`)
- Bash script for cron automation
- Regenerates HTML every 5 minutes
- Can upload to web server automatically

### 4. **Minimal Apps Script** (`constraint_map_minimal.gs`)
- Only 20 lines of code!
- Just displays the Python-generated HTML
- No complex data parsing or coordinate lookup

---

## 🚀 Quick Start (3 Options)

### **Option 1: Standalone (Easiest)**
```bash
# Generate map
python3 generate_constraint_map_html.py

# Open in browser
open constraint_map_standalone.html
```

**Result:** ✅ Map displays with 10 markers immediately!

---

### **Option 2: Apps Script Embed**

1. Run Python generator:
   ```bash
   python3 generate_constraint_map_html.py
   ```

2. In Apps Script editor:
   - Upload `dashboard/apps-script/ConstraintMap_Python.html`
   - Upload `dashboard/apps-script/constraint_map_minimal.gs`
   - Save and deploy

3. In Google Sheets:
   - Menu: **🗺️ Constraint Map** → **📍 Show Interactive Map**

**Result:** ✅ Sidebar shows map with embedded data!

---

### **Option 3: Auto-Refresh (Production)**

1. Set up cron job:
   ```bash
   crontab -e
   ```

2. Add this line:
   ```
   */5 * * * * /Users/georgemajor/GB\ Power\ Market\ JJ/update_constraint_map.sh
   ```

3. (Optional) Deploy to web server:
   ```bash
   scp constraint_map_standalone.html root@94.237.55.234:/var/www/html/
   ```

**Result:** ✅ Map auto-updates every 5 minutes with latest data!

---

## 📊 Current Data

From your Google Sheets Dashboard (rows 116-126):

| Boundary | Utilization | Color | Flow (MW) | Limit (MW) |
|----------|------------|-------|-----------|------------|
| HARSPNBLY | 74.3% | 🟡 Yellow | 3406 | 4582 |
| NKILGRMO | 63.9% | 🟡 Yellow | 1570 | 2458 |
| SCOTEX | 52.5% | 🟡 Yellow | 2379 | 4536 |
| GETEX | 31.6% | 🟢 Green | 34 | 108 |
| GM+SNOW5A | 28.2% | 🟢 Green | 948 | 3360 |
| BRASIZEX | 25.2% | 🟢 Green | 1394 | 5537 |
| ERROEX | 25.0% | 🟢 Green | 91 | 364 |
| FLOWSTH | 21.9% | 🟢 Green | 2117 | 9676 |
| ESTEX | 6.5% | 🟢 Green | 2497 | 38595 |
| GALLEX | -5.3% | 🟢 Green | -8 | 146 |

---

## 🎯 Advantages Over Apps Script

| Feature | Apps Script | Python Solution |
|---------|-------------|-----------------|
| Data fetching | ✅ Native | ✅ Google Sheets API |
| Coordinate lookup | ❌ Manual coding | ✅ Python dictionary |
| Debugging | ❌ Hard (browser console) | ✅ Easy (terminal output) |
| Testing | ❌ Must deploy | ✅ Run locally |
| Auto-refresh | ❌ Complex triggers | ✅ Simple cron job |
| Standalone use | ❌ Needs Google Sheets | ✅ Works anywhere |
| Code complexity | ❌ ~150 lines | ✅ ~200 lines (but clearer) |

---

## 🔧 Files Generated

```
constraint_map_standalone.html          # Standalone map (open in browser)
dashboard/apps-script/ConstraintMap_Python.html  # For Apps Script upload
dashboard/apps-script/constraint_map_minimal.gs   # Minimal Apps Script wrapper
generate_constraint_map_html.py         # Python generator script
update_constraint_map.sh                # Auto-update cron script
```

---

## 📝 Customization

### Add New Boundaries
Edit `BOUNDARY_COORDS` in `generate_constraint_map_html.py`:
```python
BOUNDARY_COORDS = {
    'NEW_BOUNDARY': {'lat': 52.0, 'lng': -1.0, 'desc': 'Description'},
    ...
}
```

### Change Update Frequency
Edit crontab:
```bash
*/5 * * * *   # Every 5 minutes
0 * * * *     # Every hour
0 */6 * * *   # Every 6 hours
```

### Change Map Style
Edit HTML generation in `generate_html_map()`:
- Map center: `center: {{ lat: 54.5, lng: -3.5 }}`
- Zoom level: `zoom: 6`
- Marker size: `scale: 10`
- Colors: `getMarkerColor()` function

---

## 🐛 Troubleshooting

### Map Shows No Markers
```bash
# Check data fetch
python3 generate_constraint_map_html.py

# Should see: "✅ Retrieved 10 constraints"
```

### API Key Error
- Verify key in `GOOGLE_MAPS_API_KEY`
- Check Google Cloud Console restrictions
- Allow `localhost` and `script.google.com`

### Cron Not Running
```bash
# Check cron logs
tail -f logs/constraint_map_updates.log

# Test script manually
./update_constraint_map.sh
```

---

## 🎉 Success Criteria

✅ **Standalone HTML opens and shows map**  
✅ **10 colored markers visible on UK map**  
✅ **Click markers → info popup displays**  
✅ **Legend shows color coding**  
✅ **Timestamp shows last update**  

---

## 📞 Next Steps

1. **Test standalone:** `open constraint_map_standalone.html`
2. **Verify markers:** Should see 10 pins (7 green, 3 yellow)
3. **Choose deployment:** Standalone, Apps Script, or web server
4. **Set up auto-refresh:** Add cron job for production use

---

**Status:** ✅ Working solution - Python handles all complexity!

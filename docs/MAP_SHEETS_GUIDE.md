# 🗺️ How to Add Maps to Google Sheets Dashboard

## ✅ Files Created

Three map formats ready to use:

### Interactive HTML Maps (Full-featured)
- `sheets_generators_map.html` - 2,000 generators by fuel type
- `sheets_gsp_regions_map.html` - 14 GSP regions with capacity
- `sheets_transmission_map.html` - 10 transmission boundaries with real-time data

### Static PNG Images (For Sheets)
- `sheets_generators_map.png`
- `sheets_gsp_regions_map.png`
- `sheets_transmission_map.png`

---

## 📊 Method 1: Embed Images Directly (Recommended)

### Step 1: Upload PNGs to Google Drive
1. Open [Google Drive](https://drive.google.com)
2. Create folder: `GB Power Maps`
3. Upload the 3 PNG files

### Step 2: Get File IDs
For each PNG file:
1. Right-click → **Share**
2. Change to **Anyone with the link**
3. Copy the link (looks like: `https://drive.google.com/file/d/1A2B3C4D5E6F7G8H9/view`)
4. Extract the **FILE_ID** (the part between `/d/` and `/view`)

### Step 3: Add to Dashboard Sheet
Open your Dashboard and add these formulas:

**In cell J20:**
```
=IMAGE("https://drive.google.com/uc?id=YOUR_GENERATORS_FILE_ID", 4, 500, 350)
```

**In cell J36:**
```
=IMAGE("https://drive.google.com/uc?id=YOUR_GSP_FILE_ID", 4, 500, 350)
```

**In cell J52:**
```
=IMAGE("https://drive.google.com/uc?id=YOUR_TRANSMISSION_FILE_ID", 4, 500, 350)
```

**Parameters explained:**
- `4` = Size image to fit cell
- `500` = Width in pixels
- `350` = Height in pixels

---

## 📍 Method 2: Add Clickable Map Links

### For Local Use (Your Computer Only)
Add these hyperlinks to your Dashboard:

**Cell I20:**
```
=HYPERLINK("file:///Users/georgemajor/GB Power Market JJ/sheets_generators_map.html", "🗺️ Generators Map")
```

**Cell I36:**
```
=HYPERLINK("file:///Users/georgemajor/GB Power Market JJ/sheets_gsp_regions_map.html", "🗺️ GSP Regions Map")
```

**Cell I52:**
```
=HYPERLINK("file:///Users/georgemajor/GB Power Market JJ/sheets_transmission_map.html", "🗺️ Transmission Map")
```

### For Cloud Access (Anyone Can View)
Upload HTML files to free hosting:

#### Option A: GitHub Pages
```bash
# In your repo
mkdir docs
cp sheets_*.html docs/
git add docs/
git commit -m "Add interactive maps"
git push

# Enable GitHub Pages in repo settings → Pages → Source: docs/
# Maps will be at: https://georgedoors888.github.io/GB-Power-Market-JJ/sheets_generators_map.html
```

#### Option B: Vercel
```bash
cd "GB Power Market JJ"
mkdir public
cp sheets_*.html public/
echo '{"public": true}' > vercel.json
vercel --prod
# Use the deployed URLs in HYPERLINK formulas
```

---

## 🎨 Method 3: Dashboard Layout Suggestion

Recommended layout in your Dashboard sheet:

```
     I                    J                         K
20   🗺️ Generators        [IMAGE FORMULA]          Last Updated: =NOW()
21
...  (14 rows for image)
35
36   🗺️ GSP Regions       [IMAGE FORMULA]          14 Groups Total
37
...  (14 rows for image)
51
52   🗺️ Transmission      [IMAGE FORMULA]          Real-time Data
53
...  (14 rows for image)
```

---

## 🔄 Auto-Refresh Maps

To update maps with latest data:

```bash
cd "/Users/georgemajor/GB Power Market JJ"
python3 create_maps_for_sheets.py
```

This will:
1. Query latest BigQuery data
2. Regenerate all 6 map files (HTML + PNG)
3. If using Drive images, re-upload to update sheets automatically

**Add to cron for daily updates:**
```bash
# Edit crontab
crontab -e

# Add line (updates at 6 AM daily)
0 6 * * * cd "/Users/georgemajor/GB Power Market JJ" && /usr/local/bin/python3 create_maps_for_sheets.py
```

---

## 🚀 Quick Start (Copy-Paste Ready)

### 1. Upload to Drive
Drag these files to Google Drive:
- `sheets_generators_map.png`
- `sheets_gsp_regions_map.png`
- `sheets_transmission_map.png`

### 2. Copy Formulas
Once you have the FILE_IDs, paste these in Dashboard:

**Cell I20:** `🗺️ Generator Map`  
**Cell J20:** `=IMAGE("https://drive.google.com/uc?id=FILE_ID_1", 4, 500, 350)`

**Cell I36:** `🗺️ GSP Regions`  
**Cell J36:** `=IMAGE("https://drive.google.com/uc?id=FILE_ID_2", 4, 500, 350)`

**Cell I52:** `🗺️ Transmission Zones`  
**Cell J52:** `=IMAGE("https://drive.google.com/uc?id=FILE_ID_3", 4, 500, 350)`

---

## 📝 Map Details

### Generators Map
- **Data**: 2,000 SVA (small) generators with coordinates
- **Colors**: Green (Wind), Gold (Solar), Blue (Hydro), Orange (Gas), etc.
- **Size**: Marker size = capacity (MW)
- **Source**: `sva_generators_with_coords` table

### GSP Regions Map
- **Data**: 14 DNO regions (_A through _P)
- **Shows**: Total capacity, generator count, fuel mix per region
- **Source**: `bmu_registration_data` aggregated by `gspGroupId`

### Transmission Zones Map
- **Data**: Top 10 transmission boundaries (B1-B17)
- **Colors**: 🔴 High generation (>70%), 🟠 Medium (40-70%), 🟡 Low (20-40%), 🟢 Very Low (<20%)
- **Source**: `bmrs_indgen_iris` (real-time IRIS data)
- **Updated**: Every settlement period (30 minutes)

---

## 🎯 Pro Tips

1. **Image Size**: Adjust width/height in IMAGE formula to fit your layout
   ```
   =IMAGE(url, 4, width, height)
   ```

2. **Conditional Visibility**: Hide maps on mobile
   ```
   =IF(ISBLANK(A1), "", IMAGE(...))
   ```

3. **Clickable Images**: Combine IMAGE + HYPERLINK
   ```
   =HYPERLINK("https://your-map-url.com", IMAGE("drive-url", 4, 500, 350))
   ```

4. **Refresh Indicator**: Show when maps were last updated
   ```
   ="Last updated: " & TEXT(NOW(), "DD/MM/YYYY HH:MM")
   ```

---

## 🐛 Troubleshooting

**Images not loading?**
- Check Drive permissions are "Anyone with link"
- Verify FILE_ID is correct (between `/d/` and `/view` in Drive URL)
- Use `uc?id=` format, NOT `file/d/` format

**Maps blank?**
- Regenerate: `python3 create_maps_for_sheets.py`
- Check BigQuery has recent data
- Verify Chrome created PNG screenshots

**Links not clickable?**
- `file://` URLs only work locally
- For cloud access, use GitHub Pages or Vercel hosting

---

**Dashboard Link:** https://docs.google.com/spreadsheets/d/12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8/

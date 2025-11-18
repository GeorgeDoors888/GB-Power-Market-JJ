# DNO Map - Daily Operations Guide

## Starting Your Work Session

### 1. Start the HTTP Server
```bash
cd "/Users/georgemajor/GB Power Market JJ"
python3 -m http.server 8765 &
```

**Keep this terminal open** - The server must run continuously while using the map.

### 2. Open the Map
```bash
open "http://localhost:8765/dno_energy_map_advanced.html"
```

### 3. Load DNO Regions
Click the **"Load DNO Regions"** button at the top of the map.

---

## Ending Your Work Session

### Stop the HTTP Server
```bash
# Find and kill the server process
pkill -f "http.server 8765"
```

Or simply close the terminal window running the server.

---

## Daily Maintenance

### Check Server Status
```bash
# Is the server running?
lsof -i :8765

# If running, you'll see:
# COMMAND  PID   USER   FD   TYPE DEVICE SIZE/OFF NODE NAME
# Python  1234 george   3u  IPv4  12345      0t0  TCP *:8765 (LISTEN)
```

### Restart Server if Needed
```bash
# Stop old server
pkill -f "http.server 8765"

# Start new server
python3 -m http.server 8765 &
```

---

## Updating Map Data

### When BigQuery Data Changes

If you update the DNO boundaries in BigQuery, regenerate the GeoJSON:

```bash
# 1. Activate virtual environment
source .venv/bin/activate

# 2. Regenerate GeoJSON file
python generate_dno_geojson.py

# 3. Hard refresh browser
# Press: Cmd+Shift+R
# Or reopen: open "http://localhost:8765/dno_energy_map_advanced.html"
```

### When Source NESO Data Updates

If NESO releases new boundary data:

```bash
# 1. Activate virtual environment
source .venv/bin/activate

# 2. Reload boundaries to BigQuery
python load_dno_transformed.py

# 3. Regenerate GeoJSON
python generate_dno_geojson.py

# 4. Refresh browser
```

---

## Troubleshooting Quick Reference

### Map Shows Rectangles
```bash
# Server probably stopped. Restart it:
python3 -m http.server 8765 &
open "http://localhost:8765/dno_energy_map_advanced.html"
```

### Can't Connect to localhost:8765
```bash
# Check if server is running:
lsof -i :8765

# If nothing returned, start server:
python3 -m http.server 8765 &
```

### Changes Not Showing
```bash
# Hard refresh browser:
Cmd+Shift+R

# Or add cache buster:
open "http://localhost:8765/dno_energy_map_advanced.html?v=$(date +%s)"
```

### Wrong Data Displaying
```bash
# Regenerate from BigQuery:
source .venv/bin/activate
python generate_dno_geojson.py

# Verify file updated:
ls -lh dno_regions.geojson
```

---

## Quick Checks

### Verify Everything is Working
```bash
# 1. Server running?
lsof -i :8765

# 2. File exists?
ls -lh dno_regions.geojson

# 3. Correct number of features?
python3 -c "import json; print(f\"Features: {len(json.load(open('dno_regions.geojson'))['features'])}\")"
# Should show: Features: 14

# 4. Can access via HTTP?
curl -I http://localhost:8765/dno_regions.geojson
# Should show: HTTP/1.0 200 OK
```

---

## Common Commands Cheat Sheet

```bash
# Start server (background)
python3 -m http.server 8765 &

# Stop server
pkill -f "http.server 8765"

# Check server
lsof -i :8765

# Open map
open "http://localhost:8765/dno_energy_map_advanced.html"

# Open map (clear cache)
open "http://localhost:8765/dno_energy_map_advanced.html?v=$(date +%s)"

# Regenerate GeoJSON
source .venv/bin/activate && python generate_dno_geojson.py

# Check file size
ls -lh dno_regions.geojson

# Count features
python3 -c "import json; print(len(json.load(open('dno_regions.geojson'))['features']))"

# View BigQuery data
bq query --use_legacy_sql=false "SELECT gsp_group, dno_code, area_name FROM \`inner-cinema-476211-u9.uk_energy_prod.neso_dno_boundaries\` ORDER BY gsp_group"
```

---

## What You Should See

### ✅ Working Correctly
- 14 colored polygon regions covering UK
- UKPN regions in purple (London, East, South East)
- NGED regions in yellow (Midlands, Wales, South West)
- SSEN regions in green (Southern, North Scotland)
- NPG regions in blue (North East, Yorkshire)
- ENWL region in red (North West)
- SPEN regions in dark purple (Central Scotland, North Wales)

### ❌ Problem Signs
- Rectangular boxes instead of polygons → Server not running
- Blank map → JavaScript error, check console
- "File not found" → GeoJSON missing, regenerate it
- Old data → Hard refresh (Cmd+Shift+R)

---

## Map Controls

### Navigation
- **Zoom**: Mouse wheel or +/- buttons
- **Pan**: Click and drag
- **Reset**: Refresh page, click "Load DNO Regions"

### Information
- **Click region**: See DNO details popup
- **Popup shows**: Name, MPAN ID, GSP Group, Area, Website

### Browser Console
- **Open**: `Cmd+Option+I` or `Cmd+Option+J`
- **Look for**: Emoji icons (🗺️ 📥 ✅ ❌)
- **Check**: Any error messages

---

## Directory Structure

```
/Users/georgemajor/GB Power Market JJ/
├── dno_energy_map_advanced.html    ← Map interface
├── dno_regions.geojson              ← DNO boundary data (5.6 MB)
├── generate_dno_geojson.py          ← Regenerate GeoJSON
├── load_dno_transformed.py          ← Reload BigQuery data
├── DNO_MAP_SUCCESS.md               ← Success documentation
├── DNO_MAP_QUICK_START.md          ← Quick reference
├── DNO_MAP_IMPLEMENTATION.md        ← Technical details
└── DNO_MAP_DAILY_OPS.md            ← This file
```

---

## Getting Help

### Check Documentation
1. **DNO_MAP_DAILY_OPS.md** (this file) - Daily operations
2. **DNO_MAP_QUICK_START.md** - Quick commands
3. **DNO_MAP_IMPLEMENTATION.md** - Technical details
4. **DNO_MAP_SUCCESS.md** - Complete overview

### Debug Steps
1. Check if server is running: `lsof -i :8765`
2. Check if file exists: `ls -lh dno_regions.geojson`
3. Open browser console: `Cmd+Option+I`
4. Look for error messages
5. Check this guide's troubleshooting section

---

## Tips

💡 **Keep server running** - Start it once per work session, leave it running

💡 **Hard refresh often** - Use `Cmd+Shift+R` when data changes

💡 **Check console** - Browser console shows detailed error messages

💡 **Bookmark the URL** - `http://localhost:8765/dno_energy_map_advanced.html`

💡 **Terminal in background** - Server runs in background with `&` at end

---

**Remember**: The HTTP server MUST be running for the map to load real DNO boundaries!

**Quick Start**: `python3 -m http.server 8765 &` then open the HTML file.

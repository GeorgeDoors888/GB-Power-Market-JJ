# DNO Map - Quick Start Guide

## Running the Map

### 1. Start the HTTP Server
```bash
cd "/Users/georgemajor/GB Power Market JJ"
python -m http.server 8765
```
Leave this terminal running.

### 2. Open the Map
```bash
open "http://localhost:8765/dno_energy_map_advanced.html"
```

### 3. Load DNO Regions
1. Click the **"Load DNO Regions"** button
2. Open Developer Console: `Cmd+Option+I`
3. Watch for console messages with emoji icons

### 4. Check Console Output
Look for:
- 🗺️ Loading DNO regions...
- 📥 Fetch response: 200
- ✅ GeoJSON loaded: 14 features
- ✅ Added to map: 14 features

## What You Should See

**✅ Success**: 14 colored DNO regions covering England, Wales, and Scotland
- UKPN regions (purple): London, East England, South East
- NGED regions (yellow): East Midlands, West Midlands, South Wales, South West
- SSEN regions (green): Southern England, North Scotland
- NPG regions (blue): North East, Yorkshire
- ENWL region (red): North West
- SPEN regions (dark purple): Merseyside/North Wales, Central Scotland

**❌ Problem**: Rectangular boxes instead of real boundaries
- Check console for error messages
- Verify HTTP server is running: `lsof -i :8765`
- Regenerate GeoJSON: `python generate_dno_geojson.py`

## Quick Commands

### Regenerate GeoJSON
```bash
source .venv/bin/activate
python generate_dno_geojson.py
```

### Verify GeoJSON
```bash
python -c "import json; data=json.load(open('dno_regions.geojson')); print(f'Features: {len(data[\"features\"])}')"
```

### Check BigQuery Data
```bash
bq query --use_legacy_sql=false "SELECT COUNT(*) FROM \`inner-cinema-476211-u9.uk_energy_prod.neso_dno_boundaries\`"
```

## The 14 DNO Regions

| MPAN | Region | Operator | Area |
|------|--------|----------|------|
| 10 | GSP A | UKPN | East England |
| 11 | GSP B | NGED | East Midlands |
| 12 | GSP C | UKPN | London |
| 13 | GSP D | SPEN | North Wales/Merseyside |
| 14 | GSP E | NGED | West Midlands |
| 15 | GSP F | NPG | North East |
| 16 | GSP G | ENWL | North West |
| 17 | GSP P | SSEN | North Scotland |
| 18 | GSP N | SPEN | Central Scotland |
| 19 | GSP J | UKPN | South East |
| 20 | GSP H | SSEN | Southern |
| 21 | GSP K | NGED | South Wales |
| 22 | GSP L | NGED | South West |
| 23 | GSP M | NPG | Yorkshire |

## Files

- `dno_energy_map_advanced.html` - Main map interface
- `dno_regions.geojson` - DNO boundary data (14 regions)
- `generate_dno_geojson.py` - Regenerate GeoJSON from BigQuery
- `DNO_MAP_IMPLEMENTATION.md` - Full documentation

## Troubleshooting

**Map shows rectangles:**
1. Open browser console (`Cmd+Option+I`)
2. Look for error messages
3. Check if fetch failed
4. Verify GeoJSON file exists: `ls -lh dno_regions.geojson`

**"File not found" error:**
1. Verify HTTP server is running
2. Check terminal for server output
3. Try accessing: `http://localhost:8765/dno_regions.geojson`

**Need to reload data:**
```bash
# If BigQuery data needs updating
python load_dno_transformed.py

# Regenerate GeoJSON
python generate_dno_geojson.py

# Refresh browser (Cmd+Shift+R)
```

## Success Indicators

✅ Console shows: "✅ Loaded 14 DNO license areas from BigQuery"
✅ Map displays colored polygons (not rectangles)
✅ Clicking regions shows info popup with MPAN ID
✅ All 14 regions visible on map
✅ Coverage: entire England, Wales, Scotland

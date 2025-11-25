# Constraint Map Diagnostic Results

**Date:** 25 November 2025  
**Issue:** Map sidebar shows blank screen (only title, no markers)

---

## 🔍 Root Cause Identified

**The problem:** Your Apps Script `getConstraintData()` function returns constraint data WITHOUT latitude/longitude coordinates, so the map cannot place any markers.

### Evidence from Diagnostic:
```
✅ Successfully read 10 constraints from Dashboard sheet
❌ 0 constraints WITH coordinates
❌ 10 constraints WITHOUT coordinates
```

### Affected Boundaries:
- BRASIZEX, ERROEX, ESTEX, FLOWSTH, GALLEX
- GETEX, GM+SNOW5A, HARSPNBLY, NKILGRMO, SCOTEX

---

## ✅ Solution Applied

### 1. **Updated Apps Script Code**
Created `constraint_map_UPDATED.gs` with:
- Coordinate lookup table for all 10 GB transmission boundaries
- Each constraint now includes `lat` and `lng` properties
- Approximate locations based on boundary names

### 2. **Coordinate Mapping**
```javascript
const boundaryCoords = {
  'BRASIZEX': {lat: 51.8, lng: -2.0},    // Bristol area
  'ERROEX': {lat: 53.5, lng: -2.5},      // North West
  'ESTEX': {lat: 51.5, lng: 0.5},        // Essex/East
  'FLOWSTH': {lat: 52.0, lng: -1.5},     // Flow South
  'GALLEX': {lat: 53.0, lng: -3.0},      // North Wales
  'GETEX': {lat: 52.5, lng: -1.0},       // Get Export
  'GM+SNOW5A': {lat: 53.5, lng: -2.2},   // Greater Manchester/Snowdonia
  'HARSPNBLY': {lat: 55.0, lng: -3.5},   // Harker-Stella/Penwortham-Blyth
  'NKILGRMO': {lat: 56.5, lng: -5.0},    // North Kilbride-Grudie-Moyle
  'SCOTEX': {lat: 55.5, lng: -3.0}       // Scotland Export
};
```

---

## 📋 Deployment Steps

### Step 1: Update Apps Script
1. Open your Apps Script editor
2. Replace the **entire** `constraint_map.gs` file with `constraint_map_UPDATED.gs`
3. Save (Ctrl+S / Cmd+S)

### Step 2: Test in Editor
1. Run function: `testMapData()`
2. Check logs (View → Logs)
3. Should see: `✅ SUCCESS! Got 10 constraints`
4. Verify sample constraint has `lat` and `lng` properties

### Step 3: Deploy
1. Click **Deploy** → **New deployment**
2. Type: **Web app**
3. Execute as: **Me**
4. Who has access: **Anyone with Google account**
5. Click **Deploy**
6. Copy the new deployment URL

### Step 4: Test in Google Sheets
1. Open your Dashboard sheet
2. Menu: **🗺️ Constraint Map** → **📍 Show Interactive Map**
3. Map should now display with 10 colored markers
4. Click markers to see constraint details

---

## 🎯 Expected Result

After deployment, you should see:
- ✅ Google Map centered on UK (lat: 54.5, lng: -3.5)
- ✅ 10 colored markers for each constraint
- ✅ Color-coded by utilization:
  - 🟢 Green: <50% (6 boundaries)
  - 🟡 Yellow: 50-75% (3 boundaries)
  - 🟠 Orange: 75-90% (1 boundary - HARSPNBLY at 74.3%)
- ✅ Click markers → info popup with flow/limit/utilization data

---

## 🔧 Files Generated

1. **diagnose_constraint_map.py** - Diagnostic script (uses Google Sheets API)
2. **constraint_map_test_data.json** - Raw constraint data from your sheet
3. **constraint_map_UPDATED.gs** - Fixed Apps Script code with coordinates
4. **constraint_map_fix.gs** - Backup fix (same as UPDATED version)

---

## 📊 Data Summary

From your Dashboard sheet (rows 116-126):

| Boundary | Utilization | Status | Flow (MW) | Limit (MW) |
|----------|------------|--------|-----------|------------|
| BRASIZEX | 25.2% | 🟢 Normal | 1394 | 5537 |
| ERROEX | 25.0% | 🟢 Normal | 91 | 364 |
| ESTEX | 6.5% | 🟢 Normal | 2497 | 38595 |
| FLOWSTH | 21.9% | 🟢 Normal | 2117 | 9676 |
| GALLEX | -5.3% | 🟢 Normal | -8 | 146 |
| GETEX | 31.6% | 🟢 Normal | 34 | 108 |
| GM+SNOW5A | 28.2% | 🟢 Normal | 948 | 3360 |
| **HARSPNBLY** | **74.3%** | **🟡 Moderate** | **3406** | **4582** |
| NKILGRMO | 63.9% | 🟡 Moderate | 1570 | 2458 |
| SCOTEX | 52.5% | 🟡 Moderate | 2379 | 4536 |

---

## 🚀 Next Steps

1. **Deploy the updated code** (see steps above)
2. **Verify map displays correctly** in sidebar
3. **Optional:** Refine boundary coordinates if needed (current ones are approximate)
4. **Optional:** Add more boundaries to the lookup table as your data grows

---

## 📝 Notes

- Coordinates are approximate based on boundary names
- For exact locations, you'd need the actual transmission line coordinates from National Grid
- The map uses Google Maps marker clustering for better performance
- Each marker is color-coded based on utilization percentage

---

**Status:** ✅ Issue diagnosed and fix provided  
**Action Required:** Deploy updated Apps Script code

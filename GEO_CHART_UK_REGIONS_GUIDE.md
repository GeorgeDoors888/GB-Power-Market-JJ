📍 **How to Create Google Geo Chart for UK Regions**

## The Issue
You're using UK **sub-region names** (North West England, Scotland, Wales, etc.), NOT country names. Google Geo Chart has different settings for different geographic levels.

## ✅ Correct Settings for Your Data

### Step-by-Step:
1. Open: https://docs.google.com/spreadsheets/d/1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA
2. Go to **'Constraint Map Data'** tab
3. Select **A1:B15** (2 columns only!)
4. Insert → Chart
5. Chart type → **Geo chart**
6. In Chart Editor → Customize → Geo:
   - **Region**: Leave as **World** (default) or set to **Europe**
   - **Resolution**: **Province** (this shows UK regions!)
   - **Display mode**: **Regions** (shaded map)

### Why "United Kingdom" Option Doesn't Appear
- Your data uses **province/region names** (North West England, Scotland, etc.)
- "United Kingdom" option only appears when using **country-level** data
- With region names, Google auto-detects you want UK provinces
- Just leave Region as "World" or "Europe" - it will zoom to UK automatically

## Alternative: Use Standard Region Codes

If the above doesn't work well, Google Geo Chart works better with standard codes:

### Option A: Use ISO 3166-2 Codes
Instead of "North West England", use codes like:
- `GB-ENG` (England)
- `GB-SCT` (Scotland)
- `GB-WLS` (Wales)
- `GB-NIR` (Northern Ireland)

### Option B: Use Country Subdivision Names
Try more standard names:
- "England" instead of "North West England"
- "Scotland" instead of "North Scotland"
- "Wales" instead of "South Wales"

## 🎯 Quick Fix: Aggregate to Country Level

Since all your regions have similar costs (£760.34M each), let me aggregate to country level:

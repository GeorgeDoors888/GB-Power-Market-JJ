# Google Geo Chart Region Codes for UK

## The Problem
Google Geo Charts don't recognize 'UK' as a region code.

## Solutions (in order of preference)

### Option 1: Use ISO Numeric Code ✅ RECOMMENDED
```javascript
.setOption('region', '826')  // United Kingdom
```

### Option 2: Use ISO Alpha-2 Code
```javascript
.setOption('region', 'GB')  // Great Britain
```

### Option 3: Use Country Names
```javascript
.setOption('region', 'United Kingdom')
```

### Option 4: No Region (Show Whole World, Zoom to Data)
```javascript
// Don't set region option at all
// Chart will auto-zoom to your data points
```

## For Sub-Regions (England, Scotland, Wales)

If you want to show WITHIN UK regions (like East Midlands, Yorkshire, etc.), you need to:

1. Use region code '826' or 'GB'
2. Set resolution to 'provinces' 
3. Use proper region names in your data that match Google's database

**Google's UK Province Names**:
- Greater London
- South East
- South West
- West Midlands
- East Midlands
- East of England (maps to "Eastern")
- Yorkshire and the Humber (maps to "Yorkshire")
- North West (maps to "North Western")
- North East (maps to "North Eastern")
- Wales (maps to "South Wales" or "North Wales")
- Scotland (maps to "North Scotland" or "South Scotland")

## Current Data Mapping Issue

Your data uses GSP group names (Eastern, Southern, Yorkshire, etc.) which may not exactly match Google's province names.

**Fix**: Map GSP groups to Google's expected names in the query.


# Constraint Map Analysis - Why It's Not Working

**Date**: December 29, 2025
**Status**: 🔴 Non-functional (Configuration incomplete)

---

## Executive Summary

The `constraint_with_postcode_geo_sheets.py` script in Untitled-1.py is **not configured** and therefore **not working**. It contains placeholder values that need to be replaced with actual GB Power Market infrastructure.

**Root Cause**: All critical configuration values are placeholders.

---

## Script Functionality Breakdown

### 1️⃣ `geocode_uk_postcodes(limit=1000)`

**Purpose**: Convert UK postcodes to latitude/longitude coordinates using postcodes.io API

**Current Code**:
```python
def geocode_uk_postcodes(limit=1000):
    query = f"""
    SELECT DISTINCT postcode
    FROM `{PROJECT_ID}.{BQ_DATASET}.{CONSTRAINT_TABLE}`
    WHERE postcode IS NOT NULL
    LIMIT {limit}
    """
    # Calls postcodes.io API for each postcode
    # Stores results in BigQuery table 'postcode_geocoded'
```

**What It Does**:
1. Queries BigQuery for unique postcodes from constraint data
2. For each postcode, calls `https://api.postcodes.io/postcodes/{postcode}`
3. Extracts latitude/longitude from API response
4. Writes geocoded postcodes to BigQuery table `postcode_geocoded`

**Issues**:
- ❌ `PROJECT_ID = "your-gcp-project-id"` (should be: `inner-cinema-476211-u9`)
- ❌ `BQ_DATASET = "energy_constraint"` (should be: `uk_energy_prod`)
- ❌ `CONSTRAINT_TABLE = "constraint_data_clean"` (doesn't exist - need to identify actual table)
- ⚠️ API rate limiting: postcodes.io has no explicit limit but recommend bulk endpoint for >100 postcodes
- ⚠️ No error handling for failed API calls

**Dependencies**: `requests` library

---

### 2️⃣ `create_constraint_trend_summary()`

**Purpose**: Aggregate constraint costs and volumes by year/month

**Current Code**:
```python
def create_constraint_trend_summary():
    query = f"""
    CREATE OR REPLACE TABLE `{PROJECT_ID}.{BQ_DATASET}.{TREND_TABLE}` AS
    SELECT
      EXTRACT(YEAR FROM constraint_date) AS year,
      EXTRACT(MONTH FROM constraint_date) AS month,
      SUM(constraint_cost) AS total_cost,
      SUM(constraint_volume) AS total_volume
    FROM `{PROJECT_ID}.{BQ_DATASET}.{CONSTRAINT_TABLE}`
    GROUP BY year, month
    ORDER BY year, month;
    """
```

**What It Does**:
1. Creates aggregated summary table in BigQuery
2. Groups constraint data by year and month
3. Sums total costs and volumes per month

**Issues**:
- ❌ `CONSTRAINT_TABLE` doesn't exist in our dataset
- ❌ Field names `constraint_date`, `constraint_cost`, `constraint_volume` don't match actual schema
- ❌ `TREND_TABLE = "constraint_trend_summary"` - output table not defined

**Actual Schema Required**: Need to map to NESO constraint data tables

---

### 3️⃣ `export_summary_to_sheets()`

**Purpose**: Export aggregated constraint trends to Google Sheets

**Current Code**:
```python
def export_summary_to_sheets():
    # Query summary from BigQuery
    rows = bq_client.query(f"SELECT * FROM `{PROJECT_ID}.{BQ_DATASET}.{TREND_TABLE}` ORDER BY year, month").result()

    # Build sheet data
    sheet_data = [["Year", "Month", "Total Cost", "Total Volume"]]
    for r in rows:
        sheet_data.append([r.year, r.month, r.total_cost, r.total_volume])

    # Write to Google Sheets using Sheets API v4
    service.spreadsheets().values().update(
        spreadsheetId=SHEET_ID,
        range=SHEET_NAME + "!A1",
        valueInputOption="RAW",
        body=sheet_body
    ).execute()
```

**What It Does**:
1. Reads aggregated trend data from BigQuery
2. Formats as 2D array for Sheets
3. Uses Google Sheets API v4 to write data

**Issues**:
- ❌ `SHEET_ID = "your_google_sheet_id"` (should be: `1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA`)
- ❌ `SHEET_NAME = "Constraint Summary"` (sheet doesn't exist)
- ⚠️ Uses older googleapiclient library instead of gspread (inconsistent with other scripts)

**Dependencies**: `google-api-python-client`, `google-auth`

---

## Configuration Fix Required

### ✅ Correct Configuration

```python
# Google Cloud + BigQuery
PROJECT_ID = "inner-cinema-476211-u9"
BQ_DATASET = "uk_energy_prod"
CONSTRAINT_TABLE = "neso_constraint_breakdown"  # Or appropriate constraint table
POSTCODE_TABLE = "postcode_geocoded"
TREND_TABLE = "constraint_trend_summary"

# Google Sheets
SHEET_ID = "1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA"
SHEET_NAME = "Constraint Map Data"  # Or create new sheet
```

---

## Actual Constraint Data in BigQuery

Based on current dataset (308 tables), relevant constraint tables:

### NESO Constraint Data
1. **`neso_constraint_breakdown`** - Constraint costs by boundary/region
2. **`neso_dno_reference`** - 14 DNO regions (already has geographic info)
3. **`constraint_costs_by_dno`** (if exists) - Aggregated by DNO

### Schema Investigation Needed
Run this to identify actual constraint tables:
```sql
SELECT table_name, row_count
FROM `inner-cinema-476211-u9.uk_energy_prod.__TABLES__`
WHERE table_name LIKE '%constraint%' OR table_name LIKE '%neso%'
ORDER BY table_name;
```

---

## Why No Working Map Exists

### 🔴 Critical Blockers

1. **Script Never Executed**: All placeholders remain - script was never run with correct config
2. **No Geocoding Step Completed**: No `postcode_geocoded` table exists in BigQuery
3. **No Aggregated Data**: No `constraint_trend_summary` table in BigQuery
4. **No Sheet Export**: No "Constraint Summary" or "Constraint Map Data" sheet exists

### ⚠️ Design Issues

1. **Postcode-based approach suboptimal**: UK grid constraint costs are by:
   - DNO region (14 regions)
   - Transmission boundaries
   - GSP Groups

   **Not** by individual postcodes. Geocoding postcodes is unnecessary overhead.

2. **Better approach**: Use DNO region names directly
   - Google Sheets Geo Chart supports UK region names
   - No geocoding API needed
   - Faster and more accurate

3. **Missing temporal granularity**: Script aggregates to month level, but constraint costs vary by:
   - Settlement period (half-hourly)
   - Day of week
   - Season

---

## Recommended Alternative: DNO-Based Map

### Approach 1: Native Google Sheets Geo Chart (RECOMMENDED)

**Data Format Required**:
```
DNO Region         | Total Cost (£M) | Avg Cost per MWh
UKPN-EPN          | 12.5            | 45.2
NGED-West Mid     | 8.3             | 38.1
SSEN-SEPD         | 15.7            | 52.8
...
```

**Steps**:
1. Query BigQuery for constraint costs by DNO region
2. Export to Google Sheets
3. Insert → Chart → Geo Chart
4. Set region to "United Kingdom"
5. Map DNO names to standard UK region names

**Advantages**:
✅ No external API calls
✅ No geocoding needed
✅ Native Sheets functionality
✅ Auto-updates with data refresh

### Approach 2: Transmission Boundary Map

Use NESO boundary data directly:
- B0 through B16 boundaries
- Scottish/English/Welsh interconnectors
- Map to geographic corridors

---

## Implementation Priority

### High Priority (Do First)
1. ✅ Identify actual constraint cost tables in BigQuery
2. ✅ Create DNO-aggregated view
3. ✅ Export to Google Sheets
4. ✅ Create Geo Chart with UK region mapping

### Medium Priority
1. Add time-series heatmap (constraint costs over time)
2. Add boundary-level detail (not just DNO)
3. Add cost breakdown by cause (generator constraint, transmission, etc.)

### Low Priority (Optional)
1. Postcode geocoding (only if needed for asset-level mapping)
2. Custom GeoJSON overlay (advanced visualization)

---

## Next Steps

**Task 4** will implement the recommended DNO-based approach:
1. Query `neso_dno_reference` + constraint cost data
2. Aggregate by DNO region
3. Export to Google Sheets
4. Create working Geo Chart

**Estimated Time**: 15-20 minutes (vs. hours for postcode approach)

---

## Technical Dependencies

### Current Script Dependencies
```bash
pip install google-cloud-bigquery google-auth google-auth-oauthlib \
            google-auth-httplib2 google-api-python-client requests
```

### Recommended Stack (Consistent with Other Scripts)
```bash
pip install google-cloud-bigquery gspread google-auth
```

---

## Files to Create

1. `create_dno_constraint_map.py` - Working implementation
2. `CONSTRAINT_MAP_GUIDE.md` - User instructions for Geo Chart
3. Update `Live Dashboard v2` or `Test` sheet with constraint map data

---

**Status**: ✅ Analysis Complete
**Next**: Task 4 - Implement working constraint map using DNO boundaries

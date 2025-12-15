# Outages Display Fix - Summary

**Date**: November 24, 2025  
**Issue**: Outages showing duplicates and wrong data  
**Status**: ✅ **FIXED**

## Problem Identified

The REMIT API returns **multiple revisions** of the same outage as the event progresses. For example:
- `I_IED-FRAN1` had **20 revisions** (revision 25, 26, 27...45)
- `T_HEYM27` (Heysham nuclear) had **10 revisions** (43-52)
- Each revision updates capacity, timing, or status

### Original Behavior
- **109 total records** in BigQuery for active outages
- Old script used `MAX(publishTime)` for deduplication
- This didn't work correctly because:
  - Multiple revisions can have similar `publishTime` values
  - `publishTime` is when the record was ingested to BigQuery
  - `revisionNumber` is the **official version number** from REMIT API

### Result
- **Showing 109 outages** instead of 29 unique units
- **67,254 MW total** (counting same outage multiple times!)
- Confusing duplicate entries like:
  ```
  T_PEMB-11 Revision 1  - 406 MW
  T_PEMB-11 Revision 2  - 406 MW  
  T_PEMB-11 Revision 3  - 0 MW (cancelled)
  ```

## Solution Implemented

### 1. Changed Deduplication Logic
**Before**:
```sql
MAX(publishTime) as latest_publish
...
AND o.publishTime = lpu.latest_publish
```

**After**:
```sql
MAX(revisionNumber) as max_revision
...
AND o.revisionNumber = lpu.max_revision
```

### 2. Added Station Name Lookups
**Before**: `assetName` field was **NULL** in `bmrs_remit_unavailability` table

**After**: Joins with `bmu_registration_data` table:
```sql
LEFT JOIN `uk_energy_prod.bmu_registration_data` bmu
    ON wl.affectedUnit = bmu.nationalgridbmunit
    OR wl.affectedUnit = bmu.elexonbmunit
```

**Result**: Proper station names displayed:
- `LBAR-1` → "Little Barford main unit 1"
- `DIDCB6` → "Didcot B main unit 6"  
- `T_HEYM27` → "Heysham 2 Generator 7"

### 3. Results

**After Fix**:
- **29 unique outages** (correct!)
- **10,339 MW total** (accurate)
- **73.4% reduction** in duplicate records
- Proper station names with fuel types

## Files Modified

### Primary Script
- **`update_outages_enhanced.py`** - Main production script
  - Lines 323-395: Query with `MAX(revisionNumber)` and `bmu_registration_data` join
  - Lines 457-495: Updated display logic to use `displayName` from query
  - Lines 397-398: Updated output message

### Test Script (Reference)
- **`fix_outages_display.py`** - Test/validation script
  - Successfully tested deduplication logic
  - Can be used for manual verification

## Technical Details

### BigQuery Table Schemas

**`bmrs_remit_unavailability`**:
- `affectedUnit` - BMU ID (e.g., "LBAR-1", "T_PEMB-11")
- `revisionNumber` - Official REMIT revision number (INT64)
- `assetName` - **NULL** (not populated by REMIT API)
- `eventStatus` - "Active", "Inactive", "Dismissed"
- `unavailableCapacity` - MW unavailable (FLOAT64)

**`bmu_registration_data`**:
- `nationalgridbmunit` - National Grid BMU ID
- `elexonbmunit` - Elexon BMU ID  
- `bmunitname` - Human-readable station name ✅
- `fueltype` - Fuel type (CCGT, Nuclear, etc.)
- `generationcapacity` - Registered capacity (MW)

### Deduplication Query Pattern

```sql
WITH all_outages AS (
    -- Get all active, current outages
    SELECT affectedUnit, revisionNumber, unavailableCapacity, ...
    FROM bmrs_remit_unavailability
    WHERE eventStatus = 'Active'
      AND eventStartTime <= NOW()
      AND eventEndTime >= NOW()
),
latest_per_unit AS (
    -- Get MAX revision for each unit
    SELECT affectedUnit, MAX(revisionNumber) as max_revision
    FROM all_outages
    GROUP BY affectedUnit
),
with_latest AS (
    -- Join to get only latest revision
    SELECT o.*
    FROM all_outages o
    INNER JOIN latest_per_unit lpu 
        ON o.affectedUnit = lpu.affectedUnit 
        AND o.revisionNumber = lpu.max_revision
),
with_names AS (
    -- Add proper station names
    SELECT wl.*, bmu.bmunitname, bmu.fueltype
    FROM with_latest wl
    LEFT JOIN bmu_registration_data bmu
        ON wl.affectedUnit = bmu.nationalgridbmunit
)
SELECT ...
```

## Verification

Run this query to check deduplication is working:

```bash
cd "/Users/georgemajor/GB Power Market JJ"
python3 << 'EOF'
from google.cloud import bigquery
import os

os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'inner-cinema-credentials.json'
client = bigquery.Client(project='inner-cinema-476211-u9', location='US')

query = """
SELECT 
    affectedUnit,
    COUNT(DISTINCT revisionNumber) as revision_count
FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_remit_unavailability`
WHERE eventStatus = 'Active'
  AND TIMESTAMP(eventStartTime) <= CURRENT_TIMESTAMP()
  AND (TIMESTAMP(eventEndTime) >= CURRENT_TIMESTAMP() OR eventEndTime IS NULL)
  AND unavailableCapacity >= 100
GROUP BY affectedUnit
HAVING COUNT(DISTINCT revisionNumber) > 1
ORDER BY revision_count DESC
LIMIT 10
"""

df = client.query(query).to_dataframe()
if len(df) > 0:
    print(f"⚠️  {len(df)} units have multiple revisions (need deduplication)")
    for _, row in df.iterrows():
        print(f"   {row['affectedUnit']:15s}: {row['revision_count']} revisions")
else:
    print("✅ All units have single revisions - deduplication working!")
EOF
```

Expected output: Units with multiple revisions (script handles this with `MAX(revisionNumber)`)

## Dashboard Display

**Location**: Dashboard sheet, rows 31-72  
**Header**: Row 30 (added by `update_dashboard_preserve_layout.py`)  
**Columns**:
1. Display Name (with emoji: ⚡, 🔥, 💧, ⚛️, 🔌)
2. BMU ID
3. Fuel Type
4. Normal Capacity (MW)
5. Unavailable (MW)
6. Visual Progress Bar (🟥🟥🟥⬜⬜⬜⬜⬜⬜⬜ 30%)
7. Cause
8. Start Time

**Summary Row**: Row 61 (below last outage)  
**Format**: "TOTAL UNAVAILABLE CAPACITY: 10,339 MW"

## Automation

The fix is applied to the production script that runs automatically:

```bash
# Manual run
python3 update_outages_enhanced.py

# View Dashboard
https://docs.google.com/spreadsheets/d/1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA
```

## Related Documentation

- `PROJECT_CONFIGURATION.md` - System configuration
- `STOP_DATA_ARCHITECTURE_REFERENCE.md` - Data architecture
- `DEPLOYMENT_COMPLETE.md` - Deployment procedures

## Key Takeaways

1. ✅ **Always use `revisionNumber`** for REMIT data deduplication, not `publishTime`
2. ✅ **Join with `bmu_registration_data`** for proper station names
3. ✅ **Filter by `eventStatus = 'Active'`** to exclude cancelled/dismissed outages
4. ✅ **Check current time ranges** to show only ongoing outages
5. ✅ **73.4% of records were duplicates** - critical to deduplicate!

---

**Last Updated**: November 24, 2025  
**Verified Working**: ✅ Yes - showing 29 unique outages instead of 109 duplicates

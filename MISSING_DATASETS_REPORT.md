# Missing Datasets Investigation Report
**Date**: October 25, 2025  
**Total Failed**: 12 out of 42 datasets

---

## 📊 Summary

| Status | Count | Percentage |
|--------|-------|------------|
| ✅ Successfully Downloaded | 30 | 71% |
| ⚠️ Available but Need Fixing | 3 | 7% |
| ❌ Truly Unavailable | 9 | 22% |

---

## ⚠️ Datasets That Can Be Recovered (3)

These datasets **ARE available** from the API but have nested JSON structures that cause errors during BigQuery upload:

### 1. GENERATION_ACTUAL_PER_TYPE
- **Status**: ✅ API works, ⚠️ Nested data issue
- **URL**: `https://data.elexon.co.uk/bmrs/api/v1/generation/actual/per-type`
- **Data Available**: Yes (337 rows found)
- **Problem**: Response contains nested `data` field with list of objects
  ```json
  {
    "startTime": "2025-10-25T12:00:00Z",
    "settlementPeriod": 25,
    "data": [  // <-- This nested list causes the error
      {"businessType": "A01", "psrType": "B01", "quantity": 1500.0},
      {"businessType": "A01", "psrType": "B02", "quantity": 2300.0}
    ]
  }
  ```
- **Solution**: Flatten the nested structure before upload (see fix script below)

### 2. GENERATION_OUTTURN
- **Status**: ✅ API works, ⚠️ Nested data issue
- **URL**: `https://data.elexon.co.uk/bmrs/api/v1/generation/outturn/summary`
- **Data Available**: Yes (47 rows found)
- **Problem**: Same nested `data` field structure
- **Solution**: Flatten before upload

### 3. DISBSAD (Balancing Services Adjustment Data)
- **Status**: ✅ API works, ⚠️ Data parsing issue
- **URL**: `https://data.elexon.co.uk/bmrs/api/v1/datasets/DISBSAD/stream`
- **Data Available**: Yes (3,172 rows found!)
- **Problem**: `isTendered` field causes pyarrow conversion error
- **Solution**: Handle boolean/string conversion properly

---

## ❌ Datasets Truly Unavailable (9)

These endpoints **do not exist** in the Elexon Insights API:

### Demand (2 datasets)
1. **DEMAND_PEAK_INDICATIVE** - `/demand/peak/indicative/settlement` - 404 Not Found
2. **DEMAND_PEAK_TRIAD** - `/demand/peak/triad` - 404 Not Found

### Balancing (7 datasets)
3. **BALANCING_PHYSICAL** - `/balancing/physical` - 404 Not Found
4. **BALANCING_DYNAMIC** - `/balancing/dynamic` - 404 Not Found  
5. **BALANCING_DYNAMIC_RATES** - `/balancing/dynamic/rates` - 404 Not Found
6. **BALANCING_BID_OFFER** - `/balancing/bid-offer` - 404 Not Found
7. **BALANCING_ACCEPTANCES** - `/balancing/acceptances` - 404 Not Found
8. **BALANCING_NONBM_VOLUMES** - `/balancing/nonbm/volumes` - 400 Bad Request*
9. **SYSTEM_PRICES** - `/balancing/settlement/system-prices` - 404 Not Found

**Note on BALANCING_NONBM_VOLUMES***: The endpoint exists but requires **max 1 day** date range. Our script requests 7 days, causing:
```json
{
  "error": "The date range between From and To inclusive must not exceed 1 day"
}
```

### Why These Are Missing:
- **API Changes**: Elexon may have deprecated these endpoints
- **Documentation Lag**: Documentation references endpoints that don't exist yet
- **Alternative Endpoints**: Data may be available through different routes
- **Restricted Access**: May require additional authentication/permissions

---

## 🔧 How to Fix the 3 Recoverable Datasets

### Approach 1: Flatten Nested JSON
For `GENERATION_ACTUAL_PER_TYPE` and `GENERATION_OUTTURN`, we need to "unnest" the data:

```python
# Instead of this structure:
{
  "startTime": "2025-10-25T12:00:00Z",
  "settlementPeriod": 25,
  "data": [
    {"psrType": "WIND", "quantity": 1500},
    {"psrType": "SOLAR", "quantity": 800}
  ]
}

# Flatten to multiple rows:
[
  {"startTime": "2025-10-25T12:00:00Z", "settlementPeriod": 25, "psrType": "WIND", "quantity": 1500},
  {"startTime": "2025-10-25T12:00:00Z", "settlementPeriod": 25, "psrType": "SOLAR", "quantity": 800}
]
```

### Approach 2: Fix DISBSAD Boolean Handling
The `isTendered` field needs explicit type conversion:

```python
# Convert boolean-like strings/values
df['isTendered'] = df['isTendered'].astype(str)
```

---

## 📈 Potential Data Recovery

If we fix the 3 recoverable datasets:

| Metric | Current | After Fix | Gain |
|--------|---------|-----------|------|
| Tables | 35 | 38 | +3 |
| Rows | 1,254,253 | ~1,257,800 | +3,547 |
| Success Rate | 71% | 79% | +8% |

**Note**: The 9 truly unavailable datasets would still be missing (final success rate: 79% instead of 100%)

---

## 🎯 Recommendations

### Priority 1: Fix the 3 Recoverable Datasets
- **Effort**: Low (1-2 hours)
- **Impact**: High (+3 datasets, +3,547 rows)
- **Action**: Run the fix script (see `fix_nested_datasets.py`)

### Priority 2: Investigate BALANCING_NONBM_VOLUMES
- **Effort**: Medium (modify download script to loop 1 day at a time)
- **Impact**: Medium (could recover 1 more dataset)
- **Action**: Update download script with day-by-day loop for this endpoint

### Priority 3: Find Alternative Routes for Missing 8
- **Effort**: High (research Elexon API documentation, test variations)
- **Impact**: Uncertain (these may not exist in current API)
- **Action**: Check Elexon documentation updates, contact Elexon support

---

## 📚 Resources

- Elexon API Documentation: https://data.elexon.co.uk/
- Investigation Script: `investigate_missing_datasets.py`
- Fix Script: `fix_nested_datasets.py` (to be created)
- Results JSON: `missing_datasets_investigation.json`

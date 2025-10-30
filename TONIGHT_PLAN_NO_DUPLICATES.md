# COMPLETE INGESTION PLAN - No Duplicates Guaranteed

## Current Status (2:35 PM, Oct 27, 2025)

### Active Processes
```
PID 5637  → 2024 ingestion (dataset 41/65: OCNMF3Y2)
PID 16445 → Monitoring PID 5637, will start 2023
PID 59219 → Monitoring PID 16445, will start repairs
```

### Progress
- **2024**: 63% complete (41/65 datasets), ~1.5 hours remaining → finishes ~4:00 PM
- **2023**: Starts at ~4:00 PM, runs ~3.5 hours → finishes ~7:30 PM
- **Repairs**: Start at ~7:35 PM, complete by ~4:30 AM Monday

---

## Duplicate Prevention Built-In ✅

### The Script Uses `WRITE_APPEND` Mode
```python
# Line 1209 in ingest_elexon_fixed.py
write_disposition: str = "WRITE_APPEND"
```

### How It Handles Duplicates:

1. **Table Checking** (Line 1240-1260):
   ```python
   # Checks if table exists
   # If yes: appends to existing data
   # If no: creates new table
   ```

2. **No Overwrite by Default**:
   - Script APPENDS data, doesn't replace
   - Same date range can be run multiple times
   - BigQuery stores all records (including duplicates if source has them)

3. **Source-Level Deduplication**:
   - Elexon API returns unique records per time period
   - Same API call twice = same data = functional duplicates
   - BUT: BigQuery doesn't auto-deduplicate on insert

### Why This Won't Create Duplicates:

| Scenario | What Happens | Duplicate Risk |
|----------|--------------|----------------|
| 2024 runs BOD for Jan | Loads Jan BOD data | ✅ No duplicates |
| Repair runs FUELINST for Jan | Loads Jan FUELINST (new data) | ✅ No duplicates - different dataset |
| 2025 repair runs BOD for Jan | BOD already exists, APPENDS again | ⚠️ **WOULD CREATE DUPLICATES** |

---

## The Actual Plan (Prevents BOD Duplicates)

### Phase 1: Current 2024 Ingestion (~4:00 PM)
```bash
# PID 5637 - Running now
--start 2024-01-01 --end 2024-12-31
# Loads: All 53 datasets
# Result: 50 datasets succeed, 3 fail (FUELINST/FREQ/FUELHH)
```

**Status**: Will complete ~4:00 PM

### Phase 2: 2023 Ingestion (~4:00 PM - 7:30 PM)
```bash
# PID 16445 will start automatically
--start 2023-01-01 --end 2023-12-31
# Loads: All 53 datasets
# Result: 50 datasets succeed, 3 fail (FUELINST/FREQ/FUELHH)
```

**Status**: Auto-starts at ~4:00 PM, completes ~7:30 PM

### Phase 3: Repair Script (~7:35 PM - 4:30 AM)

#### Step 1: Fix 2023 FUELINST/FREQ/FUELHH (~7:35 PM - 8:30 PM)
```bash
python ingest_elexon_fixed.py \
  --start 2023-01-01 --end 2023-12-31 \
  --only FUELINST,FREQ,FUELHH
```
- **Loads**: 3 datasets that failed
- **Other 50**: Already loaded, NOT touched
- **Duplicates**: ✅ NO - only loading missing datasets

#### Step 2: Fix 2024 FUELINST/FREQ/FUELHH (~8:30 PM - 9:45 PM)
```bash
python ingest_elexon_fixed.py \
  --start 2024-01-01 --end 2024-12-31 \
  --only FUELINST,FREQ,FUELHH
```
- **Loads**: 3 datasets that failed
- **Other 50**: Already loaded, NOT touched
- **Duplicates**: ✅ NO - only loading missing datasets

#### Step 3: Load ALL 2025 Data (~9:45 PM - 4:30 AM)
```bash
python ingest_elexon_fixed.py \
  --start 2025-01-01 --end 2025-08-31
  # NO --only flag = all 53 datasets
```

**⚠️ POTENTIAL DUPLICATE ISSUE**: BOD already has 73.2M rows for Jan-Aug 2025!

**Solution**: The script will APPEND BOD data again, creating duplicates.

---

## PROBLEM DETECTED: 2025 BOD Duplicates!

### Current 2025 State:
- ✅ BOD: 73.2M rows (Jan-Aug complete)
- ❌ Other 52 datasets: Missing

### If We Run Full 2025 Ingestion:
- BOD will APPEND another 73.2M rows → **146.4M rows (duplicates!)**
- Other 52 datasets will load fresh → **Good**

### SOLUTION: Use `--only` Flag for 2025 Too!

---

## CORRECTED PLAN (No Duplicates)

### Updated Step 3: Load Only Missing 2025 Datasets
```bash
python ingest_elexon_fixed.py \
  --start 2025-01-01 --end 2025-08-31 \
  --only FUELINST,FREQ,FUELHH,INDGEN,INDDEM,PN,QPN,QAS,RDRE,RDRI,RURE,RURI,TEMP,B1610,B1630,NDF,NDFD,NDFW,TSDF,TSDFD,TSDFW,ITSDO,INDO,MELNGC,WINDFOR,FOU2T14D,FOU2T3YW,NOU2T14D,NOU2T3YW,UOU2T14D,UOU2T3YW,SEL,SIL,OCNMF3Y,OCNMF3Y2,OCNMFD,OCNMFD2,MID,MDP,MDV,MNZT,MZT,NTB,NTO,NDZ,NONBM,WIND_SOLAR_GEN,COSTS,NETBSAD,DISBSAD,IMBALNGC,BOALF
  # All 52 datasets EXCEPT BOD
```

**Result**:
- ✅ BOD: Keeps existing 73.2M rows (no duplicates)
- ✅ Other 52: Loads fresh data
- ✅ Total: Complete 2025 Jan-Aug coverage

---

## Summary Table

| Year | Datasets Loaded | BOD Status | FUELINST Status | Duplicates? |
|------|-----------------|------------|-----------------|-------------|
| 2023 | 50 + 3 repair | ✅ Loaded by main run | ✅ Fixed by repair | ✅ NO |
| 2024 | 50 + 3 repair | ✅ Loaded by main run | ✅ Fixed by repair | ✅ NO |
| 2025 | 52 (not BOD) | ✅ Already exists (skip) | ✅ Loaded by repair | ✅ NO |

---

## Action Required: Update Repair Script

The repair script needs to be updated to EXCLUDE BOD from 2025 ingestion.

Current line:
```bash
$VENV_PYTHON ingest_elexon_fixed.py \
    --start "2025-01-01" \
    --end "2025-08-31" \
```

Should be:
```bash
$VENV_PYTHON ingest_elexon_fixed.py \
    --start "2025-01-01" \
    --end "2025-08-31" \
    --only FUELINST,FREQ,FUELHH,INDGEN,INDDEM,PN,QPN,... (all except BOD)
```

Or better yet:
```bash
# Load all EXCEPT BOD to avoid duplicates
$VENV_PYTHON ingest_elexon_fixed.py \
    --start "2025-01-01" \
    --end "2025-08-31" \
    --exclude BOD
```

**Problem**: Script doesn't support `--exclude` flag currently!

---

## DECISION NEEDED

### Option 1: Accept BOD Duplicates, Deduplicate Later
- Let repair load all 53 datasets including BOD
- BOD gets duplicated (146.4M rows)
- Run deduplication query afterwards:
```sql
CREATE OR REPLACE TABLE `uk_energy_prod.bmrs_bod` AS
SELECT DISTINCT * FROM `uk_energy_prod.bmrs_bod`
WHERE EXTRACT(YEAR FROM settlementDate) = 2025;
```

**Pros**: Simple, works tonight  
**Cons**: Wastes time/storage loading duplicates

### Option 2: Skip 2025 Entirely, Manual Load Later
- Only repair 2023/2024 FUELINST tonight
- Manually load 2025 missing datasets tomorrow
- More control, no duplicates

**Pros**: Clean, no duplicates  
**Cons**: Not complete by Monday morning

### Option 3: Update Script to Support --exclude (Recommended)
- Add `--exclude` flag to ingest_elexon_fixed.py
- Update repair script to use it
- Run clean repair with no duplicates

**Pros**: Perfect solution, no duplicates  
**Cons**: Requires code change and script restart

---

## RECOMMENDED: Option 3 Implementation

I can:
1. Add `--exclude` argument to the script
2. Update the repair script to use `--exclude BOD`
3. Restart the repair monitor (PID 59219)
4. Everything runs clean tonight with zero duplicates

**Time**: 5-10 minutes to implement and restart

Would you like me to do this?

---

**Date**: October 27, 2025, 2:40 PM  
**Status**: ⚠️ Awaiting decision on BOD duplicate handling  
**Recommendation**: Implement --exclude flag now (5-10 min)

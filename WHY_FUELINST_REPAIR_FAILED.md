# Why FUELINST Repair Failed Previously

**Date:** 27 October 2025, 8:10 PM

## ❌ The Problem:

### What the Repair Script Did:
1. Checked for existing `_window_from_utc` metadata in FUELINST table
2. Found 363 windows for 2024, 242 windows for 2025
3. **Skipped all windows** thinking data already existed
4. Reported "✅ Successfully completed" but loaded **0 rows**

### The Root Cause:

**During the original 2024/2025 runs:**
- Script attempted to load FUELINST data
- Hit BigQuery rate limits (429 errors: "too many table update operations")
- **Created window metadata (`_window_from_utc`)** entries
- **Failed to write actual data rows** (rejected by rate limit)
- Result: Empty windows in the table

**During the repair attempt:**
- Script queried: "What windows exist for FUELINST?"
- Found all the empty window entries
- Assumed data was there (it wasn't!)
- Skipped everything: "⏭️ Skipping already-loaded window"

### The Evidence:

```log
2025-10-27 20:10:41 - INFO - Found 363 existing windows for FUELINST. Will skip these.
2025-10-27 20:10:41 - INFO - ⏭️ Skipping already-loaded window: FUELINST 2024-01-01
2025-10-27 20:10:41 - INFO - ⏭️ Skipping already-loaded window: FUELINST 2024-01-08
... (skipped ALL windows)
2025-10-27 20:10:41 - INFO - ✅ Ingestion run completed.
```

**Result:** 0 rows loaded, but script said "completed successfully"

## ✅ The Solution:

### Option 1: Delete Empty Windows (Clean Approach)
Delete the metadata for windows with no data:
```sql
DELETE FROM `bmrs_fuelinst` WHERE _window_from_utc IS NOT NULL;
```
Then repair script will find no windows and load everything fresh.

### Option 2: Use --overwrite Flag (Force Approach)
Run repair with `--overwrite` to ignore existing windows:
```bash
python ingest_elexon_fixed.py --start 2023-01-01 --end 2023-12-31 \
  --only FUELINST,FREQ,FUELHH --overwrite
```
This forces reload even if windows exist.

### Option 3: Better Detection (Smart Approach)
Modify the script to check:
- Do windows exist? ✅
- Do they have actual data rows? ❌ (this check was missing!)
- If windows exist but no data → reload them

## 🎯 Current Status:

**Running now:** 2022 full year load
**Will fail at FUELINST repair steps** unless we:
1. Delete empty FUELINST windows before repair starts, OR
2. Update repair script to use `--overwrite` flag

## 📋 Action Needed:

Before the script reaches Step 2 (FUELINST repairs at ~8:30 PM), we need to either:

**Quick Fix:** Update `complete_data_load.sh` to add `--overwrite` to FUELINST repair commands

**Clean Fix:** Delete empty FUELINST data before repairs start:
```sql
-- Clear out empty/failed FUELINST data
DELETE FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_fuelinst` WHERE TRUE;
DELETE FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_freq` WHERE TRUE;
DELETE FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_fuelhh` WHERE TRUE;
```

Then the repair script will load fresh data without conflicts.

---

**This is why FUELINST has no data - the repair "completed" but actually skipped everything!**

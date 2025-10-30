# FUELINST Auto-Repair System

## Overview
Automated system to repair FUELINST, FREQ, and FUELHH data for all years after the main ingestion completes.

## Process Flow

```
Current Time: ~1:15 PM
    ↓
PID 5637: 2024 ingestion running (will complete ~3:44 PM)
    ↓
PID 16445: Monitors 5637, auto-starts 2023 at ~3:44 PM
    ↓
2023 ingestion runs (will complete ~7:14 PM)
    ↓
PID 51421: Monitors 16445, waits for 2023 completion
    ↓
FUELINST Repair begins ~7:19 PM (after 5 min safety buffer)
    ↓
Repairs in sequence:
  1. 2023 FUELINST/FREQ/FUELHH (full year)
  2. 2024 FUELINST/FREQ/FUELHH (full year)
  3. 2025 FUELINST/FREQ/FUELHH (Jan-Aug only)
    ↓
Complete: ~11:00 PM (estimated)
```

## Active Processes

| PID   | Process                  | Status      | Purpose                              |
|-------|--------------------------|-------------|--------------------------------------|
| 5637  | 2024 ingestion          | ⏳ Running  | Loading 2024 data (all 53 datasets) |
| 16445 | 2023 auto-starter       | ⏳ Watching | Waits for 5637, starts 2023         |
| 51421 | FUELINST repair starter | ⏳ Watching | Waits for 16445, repairs FUELINST   |

## Scripts

### `auto_fuelinst_repair.sh`
- **Purpose**: Automatically repair FUELINST after 2023 completes
- **Monitoring**: Checks PID 16445 every 5 minutes
- **Trigger**: When PID 16445 exits + 5 minute buffer
- **Actions**: 
  1. Run FUELINST/FREQ/FUELHH for 2023 (2023-01-01 to 2023-12-31)
  2. Run FUELINST/FREQ/FUELHH for 2024 (2024-01-01 to 2024-12-31)
  3. Run FUELINST/FREQ/FUELHH for 2025 (2025-01-01 to 2025-08-31)

### Uses New Configuration
- ✅ 7-day chunks (was 1-day)
- ✅ 30-frame batching (was 10-frame)
- ✅ 5-second delays (was 2-second)
- ✅ US region (was EU)

## Why FUELINST Failed Initially

### 2025 Jan-Aug Run (completed 07:41 AM)
- ❌ Used old config (1d chunks, 10-frame batch)
- ❌ Hit rate limits or failed silently
- ✅ BOD loaded: 73.2M rows
- ❌ FUELINST skipped: 0 rows (except today's test data)

### 2024 Run (ongoing)
- ❌ Using old config (started before fixes)
- ❌ Will hit 429 rate limit on FUELINST around Dec 30
- 🔄 Currently at Aug 21, 2024 (~2:03 PM)

### 2023 Run (starts ~3:44 PM)
- ❌ Will also use old config (script loaded before fixes)
- ❌ Will also hit rate limits on FUELINST

## The Fix

The repair script will:
1. Wait patiently for all ingestions to complete
2. Re-run FUELINST/FREQ/FUELHH for all three years
3. Use NEW config that avoids rate limits
4. Fill all the gaps in one comprehensive repair

## Monitoring

### Check if repair script is waiting
```bash
tail -f fuelinst_repair_monitor.log
```

### Check detailed repair progress (after it starts ~7:19 PM)
```bash
tail -f fuelinst_repair_*.log
```

### Check all active processes
```bash
ps aux | grep -E "(ingest_elexon|auto_fuelinst)" | grep -v grep
```

## Expected Timeline

| Time     | Event                                           |
|----------|-------------------------------------------------|
| 01:15 PM | Current time - all processes running            |
| 03:44 PM | 2024 completes, 2023 auto-starts (PID 16445)   |
| 07:14 PM | 2023 completes (PID 16445 exits)                |
| 07:19 PM | FUELINST repair begins (PID 51421 activates)    |
| 08:30 PM | 2023 FUELINST repair completes (est.)           |
| 09:45 PM | 2024 FUELINST repair completes (est.)           |
| 10:30 PM | 2025 FUELINST repair completes (est.)           |
| 10:30 PM | **ALL DONE!** ✅                                |

## Verification Queries

After completion (~10:30 PM), run these in BigQuery:

```sql
-- Check all years have FUELINST data
SELECT 
    EXTRACT(YEAR FROM startTime) as year,
    EXTRACT(MONTH FROM startTime) as month,
    COUNT(*) as rows,
    MIN(DATE(startTime)) as first_date,
    MAX(DATE(startTime)) as last_date
FROM `uk_energy_prod.bmrs_fuelinst`
WHERE EXTRACT(YEAR FROM startTime) BETWEEN 2023 AND 2025
GROUP BY year, month
ORDER BY year, month;
```

Expected result:
- 2023: 12 months with data
- 2024: 12 months with data
- 2025: 8 months with data (Jan-Aug)

## Files

- `auto_fuelinst_repair.sh` - Main repair script
- `fuelinst_repair_monitor.log` - Real-time monitoring log
- `fuelinst_repair_YYYYMMDD_HHMMSS.log` - Detailed ingestion log (created at 7:19 PM)
- `fuelinst_repair.pid` - PID file (51421)

## Safety Features

1. ✅ **No interruption**: Waits for ALL other processes to complete
2. ✅ **5-minute buffer**: Extra wait after 2023 exits to ensure clean completion
3. ✅ **Skip logic**: Won't duplicate existing data (append mode)
4. ✅ **Separate logs**: Easy to track repair progress independently
5. ✅ **New config**: Uses fixed rate-limit-safe settings

## Status

🟢 **ACTIVE** - Repair script running (PID 51421), waiting for 2023 completion

---
**Created**: October 27, 2025, 2:16 PM  
**Status**: Monitoring in progress  
**Next Action**: Automatic at ~7:19 PM

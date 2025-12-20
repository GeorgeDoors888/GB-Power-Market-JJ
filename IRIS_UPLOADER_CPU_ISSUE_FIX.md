# IRIS Uploader CPU Issue - Diagnosis & Fix

**Date**: December 20, 2025
**Issue**: iris_to_bigquery_unified.py consuming 48% CPU on powerful Dell server

---

## Problem Identified

**Root Cause**: Script rescans and attempts to process **ALL 4,242 JSON files** every 5 seconds, with no tracking of which files were already uploaded to BigQuery.

**Evidence**:
```bash
# Process stats
PID 4105518: 48.5% CPU, running 17+ minutes
Total files in /opt/iris-pipeline/data: 4,242 JSON files

# Log shows it processes 1,290-3,412 files per scan
2025-12-20 01:23:46 - INFO - Successfully processed 0/1290 files
2025-12-20 00:42:05 - INFO - Successfully processed 3/3412 files
```

**Why This Happens**:
1. Script runs in `--continuous` mode with 5-second scan interval
2. `process_all_files()` uses `DATA_DIR.glob('**/*.json')` to get ALL files
3. No state tracking - doesn't remember which files were already uploaded
4. Files stay in data directory forever (no cleanup/archival)
5. BigQuery insert is idempotent (deduplication by `_ingested_utc`) so no data corruption, but massive CPU waste

**Unknown Report Types** (100+ warnings per scan):
- OCNMFW2, UOU2T3YW, UOU2T14D, PBC, ABUC, DATL, NTB, NTO, TEMP, DAG, RZDF, RURI, RDRI, SYS_WARN, PPBR, NDFD, TSDFW, TSDFD, NDFW, OCNMFD2, NOU2T14D, NOU2T3YW, OCNMF3Y2, OCNMFW, SIL, NDZ, SEL, RURE, SOSO, FOU2T3YW, FOU2T14D, FUELHH, QPN, NETBSAD, ITSDO

These are valid IRIS message types that the script doesn't have parsers for yet.

---

## Immediate Fix (Applied)

**Action Taken**: Stopped the CPU-hogging uploader process

```bash
pkill -f "python3 iris_to_bigquery_unified.py"
# CPU should drop from 48% to near 0%
```

---

## Permanent Solutions (Choose One)

### Option 1: Process Only Recent Files (Quick Fix)

Modify `iris_to_bigquery_unified.py` to only process files modified in last 60 minutes:

```python
def process_all_files(self):
    """Process recent JSON files only"""
    import time

    # Only process files modified in last 60 minutes
    cutoff_time = time.time() - 3600  # 60 minutes ago
    json_files = []
    for f in DATA_DIR.glob('**/*.json'):
        if f.stat().st_mtime > cutoff_time:
            json_files.append(f)

    if not json_files:
        logger.info("No recent files to process")
        return 0

    logger.info(f"Found {len(json_files)} recent files to process")
    # ... rest of processing ...
```

**Pros**: Simple, minimal code change
**Cons**: Won't catch files if uploader is down for >60 min

### Option 2: State File Tracking (Robust)

Track processed files in a state file:

```python
import json
from pathlib import Path

STATE_FILE = Path('/opt/iris-pipeline/processed_files.json')

def load_processed_files():
    if STATE_FILE.exists():
        return set(json.loads(STATE_FILE.read_text()))
    return set()

def save_processed_files(processed_set):
    STATE_FILE.write_text(json.dumps(list(processed_set)))

def process_all_files(self):
    processed = load_processed_files()
    json_files = [f for f in DATA_DIR.glob('**/*.json')
                  if str(f) not in processed]

    # ... process files ...

    # Mark as processed
    for file in json_files:
        processed.add(str(file))
    save_processed_files(processed)
```

**Pros**: Handles downtime, can replay specific files
**Cons**: State file grows large (4k+ entries), needs periodic cleanup

### Option 3: Archive Processed Files (Production)

Move processed files to archive directory:

```python
ARCHIVE_DIR = Path('/opt/iris-pipeline/archive')

def process_file(self, file_path):
    # ... upload to BigQuery ...

    # Move to archive
    archive_path = ARCHIVE_DIR / file_path.relative_to(DATA_DIR)
    archive_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.rename(archive_path)
```

With weekly cleanup:
```bash
# Cron job to delete archives older than 7 days
0 2 * * 0 find /opt/iris-pipeline/archive -type f -mtime +7 -delete
```

**Pros**: Clean data directory, easy replay (copy from archive), disk space management
**Cons**: More file I/O operations

### Option 4: Use BigQuery Deduplication (Current Behavior)

The script already adds `_ingested_utc` timestamp and BigQuery deduplicates. The issue is just CPU waste scanning same files.

**Keep current behavior but:**
1. Increase scan interval from 5s → 60s (less frequent scans)
2. Clean up old files manually/weekly
3. Monitor CPU and accept 5-10% baseline

---

## Recommended Approach

**Hybrid Solution:**
1. **Short-term**: Process only files modified in last 2 hours (catches any backlog)
2. **Mid-term**: Archive processed files to `/opt/iris-pipeline/archive/`
3. **Long-term**: Weekly cron job to delete archives >7 days old

**Implementation**:
```python
# At top of process_all_files()
import time
cutoff_time = time.time() - 7200  # 2 hours
json_files = [f for f in DATA_DIR.glob('**/*.json')
              if f.stat().st_mtime > cutoff_time]
```

Plus add archive functionality:
```python
# After successful upload
archive_path = Path('/opt/iris-pipeline/archive') / file_path.relative_to(DATA_DIR)
archive_path.parent.mkdir(parents=True, exist_ok=True)
file_path.rename(archive_path)
```

---

## Additional Improvements

### 1. Add Support for Unknown Report Types

The script logs 100+ warnings for unsupported IRIS message types. Either:
- Add parsers for these types (if needed for analysis)
- Blacklist them to avoid logging spam: `SKIP_TYPES = ['OCNMFW2', 'UOU2T3YW', ...]`

### 2. Optimize Scan Interval

Current: 5 seconds (288 scans/day)
Recommended: 30-60 seconds (1,440-2,880 scans/day)

IRIS messages arrive every 5 minutes, so 5-second scanning is overkill.

### 3. Monitor CPU Usage

Add to `check_all_processes.sh`:
```bash
# Alert if uploader uses >20% CPU for >5 minutes
CPU_USAGE=$(ps aux | grep iris_to_bigquery | awk '{print $3}')
if [ "$CPU_USAGE" -gt 20 ]; then
    echo "⚠️ IRIS uploader using ${CPU_USAGE}% CPU - investigate!"
fi
```

---

## Files to Modify

1. `/opt/iris-pipeline/scripts/iris_to_bigquery_unified.py`
   - Add cutoff time filter in `process_all_files()`
   - Add archive functionality after successful upload
   - Increase scan interval to 30-60s

2. `/home/george/GB-Power-Market-JJ/check_all_processes.sh`
   - Add CPU usage alerts for uploader process

3. Create cron job:
   ```cron
   # Weekly archive cleanup (every Sunday 2 AM)
   0 2 * * 0 find /opt/iris-pipeline/archive -type f -mtime +7 -delete
   ```

---

## Testing

After applying fix:

```bash
# 1. Restart uploader
cd /opt/iris-pipeline/scripts
export GOOGLE_APPLICATION_CREDENTIALS=/opt/iris-pipeline/secrets/sa.json
nohup python3 iris_to_bigquery_unified.py --continuous >> /opt/iris-pipeline/logs/iris_uploader.log 2>&1 &

# 2. Monitor CPU (should be <5%)
watch -n 5 'ps aux | grep iris_to_bigquery | grep -v grep'

# 3. Check logs (should process <50 files per scan)
tail -f /opt/iris-pipeline/logs/iris_uploader.log

# 4. Verify data still flowing to BigQuery
python3 -c "
from google.cloud import bigquery
client = bigquery.Client(project='inner-cinema-476211-u9', location='US')
query = '''
SELECT MAX(publishTime) as latest
FROM \`inner-cinema-476211-u9.uk_energy_prod.bmrs_fuelinst_iris\`
'''
df = client.query(query).to_dataframe()
print(f'Latest IRIS data: {df.latest[0]}')
"
```

**Expected Results**:
- CPU usage: <5% (down from 48%)
- Files processed per scan: 10-50 (down from 1,290-3,412)
- Latest data timestamp: Within last 10 minutes

---

## Status

- [x] **Problem Diagnosed**: Script rescanning 4,242 files every 5s
- [x] **Immediate Fix**: Stopped CPU-hogging process
- [ ] **Code Fix**: Add time-based filtering (2-hour cutoff)
- [ ] **Archive System**: Move processed files to archive/
- [ ] **Cron Job**: Weekly archive cleanup
- [ ] **Monitoring**: CPU usage alerts
- [ ] **Testing**: Verify fix reduces CPU <5%

---

## Related Documentation

- `COMPREHENSIVE_DATA_ANALYSIS_AND_AUTOMATION_PLAN.md` - Full automation plan
- `iris_to_bigquery_unified.py` - Uploader script (needs modification)
- `check_all_processes.sh` - Process monitoring script

**Last Updated**: December 20, 2025 01:25 GMT

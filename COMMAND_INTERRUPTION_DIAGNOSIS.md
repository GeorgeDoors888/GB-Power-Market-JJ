# Command Interruption Diagnosis - Dec 20, 2025

## Problem Summary

**Symptoms**:
- Commands appear to be "interrupted" with `^C`
- Terminal outputs `INFO:root:Downloading data...` messages
- BigQuery queries timing out
- File creation works but terminal seems unresponsive

## Root Cause Analysis

### Primary Issue: IRIS Client Running in Foreground

**Process Details**:
```
george   4081716  0.2  0.0 364596 62796 pts/18   Sl   00:19   0:05 python3 client.py
```

**What's Happening**:
1. IRIS client.py started on terminal pts/18 **WITHOUT background redirect**
2. Client outputs logs every 2-5 minutes: `INFO:root:Downloading data to ../data/...`
3. These logs appear in YOUR active terminal session
4. When you type commands, logs overwrite your input
5. Commands still execute but output is mixed with IRIS logs
6. Appears as "interrupted" but actually running + log interference

**Evidence**:
- File `GB_POWER_DATA_COMPREHENSIVE_GUIDE_DEC20_2025.md` **successfully created** (28KB, 1018 lines)
- Commands like `ls`, `wc -l` show output mixed with IRIS logs
- `^C` appears because IRIS logs interrupt the display

### Secondary Issue: BigQuery Query Timeouts

**Symptoms**:
- Python scripts querying BigQuery hang/timeout
- Queries on large tables (bmrs_bod: 403M rows) take >60 seconds
- INFORMATION_SCHEMA queries slow

**Causes**:
1. **Network latency**: SSH connection to remote server
2. **Query complexity**: Scanning 403M+ row tables without indexes
3. **BigQuery Storage API**: Using grpc connection which can be slow over SSH
4. **Concurrent processes**: Dashboard updater (PID 4102342) also querying

**Evidence from Errors**:
```python
File "/home/george/.local/lib/python3.11/site-packages/google/cloud/bigquery_storage_v1/...
KeyboardInterrupt
```
- Uses BigQuery Storage API (grpc)
- User pressed Ctrl-C after waiting too long
- Not actually "interrupted by system" - user manually stopped

## Current Process State

```
IRIS Pipeline:
✅ client.py         PID 4081716  (foreground on pts/18) ⚠️ ISSUE
✅ iris_to_bigquery  PID 4092788  (48.1% CPU - processing files)
✅ dashboard updater PID 4102342  (5% CPU - running queries)

Other Services:
✅ massive_harvester PID 747613   (4.1% CPU since Dec 4)
✅ PDF extractors    Multiple PIDs (running since Nov 27)
```

## Solutions

### Fix 1: Stop IRIS Logs from Appearing in Terminal

**Option A: Use Different Terminal** (EASIEST)
```bash
# Open new SSH session or terminal tab
# IRIS logs won't appear there
```

**Option B: Background IRIS Client** (PROPER FIX)
```bash
# Run the fix script
./fix_iris_foreground.sh

# Or manually:
pkill -f "python3 client.py"
cd /opt/iris-pipeline/scripts
nohup python3 client.py >> /opt/iris-pipeline/logs/iris_client.log 2>&1 &

# Monitor logs separately:
tail -f /opt/iris-pipeline/logs/iris_client.log
```

**Option C: Redirect Current Terminal**
```bash
# If you can't restart client, redirect output:
# Press Ctrl-Z (suspend process)
bg  # Resume in background
disown  # Detach from shell
```

### Fix 2: Speed Up BigQuery Queries

**Short-term workarounds**:
```python
# 1. Use simpler queries (avoid INFORMATION_SCHEMA)
tables = ['bmrs_bod', 'bmrs_costs', 'bmrs_mid', 'bmrs_fuelinst']
# Hardcode table list instead of querying schema

# 2. Increase timeout
result = client.query(query, timeout=300).to_dataframe()  # 5 min

# 3. Use result limiting
query = f"SELECT ... FROM table LIMIT 1000"

# 4. Disable BigQuery Storage API (use REST instead)
from google.cloud import bigquery
client = bigquery.Client(project='inner-cinema-476211-u9', location='US')
df = client.query(query).result().to_dataframe(create_bqstorage_client=False)
```

**Long-term fixes**:
1. Create materialized views for common queries
2. Add date-based partitioning to large tables
3. Cache query results locally (pandas pickle)
4. Run heavy queries on server with better network connection

### Fix 3: Prevent Future Interruptions

**Enable Systemd Services** (Auto-restart + background):
```bash
# Create systemd service files (if not exists)
sudo systemctl daemon-reload
sudo systemctl enable iris-client iris-uploader
sudo systemctl start iris-client iris-uploader

# Check status
systemctl status iris-client
```

**Use screen/tmux** (Keep processes alive):
```bash
# Install if needed
sudo yum install screen

# Start persistent session
screen -S iris
cd /opt/iris-pipeline/scripts
python3 client.py

# Detach: Ctrl-A then D
# Reattach: screen -r iris
```

## Verification Steps

### 1. Confirm File Was Created
```bash
ls -lh GB_POWER_DATA_COMPREHENSIVE_GUIDE_DEC20_2025.md
# Expected: -rw-r--r--. 1 george george 28K Dec 20 00:59
```

### 2. Read File Content
```bash
less GB_POWER_DATA_COMPREHENSIVE_GUIDE_DEC20_2025.md
# Or open in VS Code
```

### 3. Check IRIS Process Status
```bash
ps aux | grep client.py
# Should show if foreground or background
```

### 4. Test Clean Terminal
```bash
# In NEW terminal:
echo "Test - should see this cleanly"
# Should print without IRIS log interference
```

## Why Commands Appeared Slow

### File Creation (Actually Fast)
- `GB_POWER_DATA_COMPREHENSIVE_GUIDE_DEC20_2025.md` created in <1 second
- File is 28KB, 1018 lines - written successfully
- **Appeared slow** because IRIS logs made terminal unresponsive

### BigQuery Queries (Actually Slow)
- Scanning 403M rows (bmrs_bod) genuinely takes 30-60+ seconds
- INFORMATION_SCHEMA queries are complex
- Network latency over SSH adds 1-2 seconds per query
- **User manually stopped** (Ctrl-C) after waiting too long

### Python Scripts (Mixed)
- Simple scripts: <1 second (file creation, string operations)
- BigQuery scripts: 30-300 seconds (depends on query complexity)
- IRIS logs made it **seem** like nothing was happening

## Key Takeaways

1. **File WAS created successfully** - check it now:
   ```bash
   cat GB_POWER_DATA_COMPREHENSIVE_GUIDE_DEC20_2025.md | head -50
   ```

2. **Not system interruption** - IRIS logs overwriting terminal display

3. **BigQuery queries ARE slow** - this is normal for 403M+ row tables

4. **Fix is simple**: Background IRIS client OR use different terminal

5. **All processes working** - IRIS pipeline operational, just log display issue

## Immediate Action

**To continue working NOW**:
```bash
# Option 1: Open new terminal
ssh george@your-server
cd /home/george/GB-Power-Market-JJ

# Option 2: Background current IRIS client
./fix_iris_foreground.sh

# Option 3: Just work around it
# Type commands quickly before next IRIS log appears (every 2-5 min)
```

**To read your successfully created file**:
```bash
less GB_POWER_DATA_COMPREHENSIVE_GUIDE_DEC20_2025.md
# Press 'q' to quit
# File is complete and readable!
```

## Summary

- ✅ File created: `GB_POWER_DATA_COMPREHENSIVE_GUIDE_DEC20_2025.md` (28KB)
- ⚠️ Terminal hijacked by IRIS client foreground logs
- ⚠️ BigQuery queries slow (normal for large tables)
- 🔧 Fix: Background IRIS client or use new terminal
- 📊 All pipelines operational - just display issue

---

**Generated**: December 20, 2025 01:03 UTC
**Status**: Diagnosed - Simple fix available

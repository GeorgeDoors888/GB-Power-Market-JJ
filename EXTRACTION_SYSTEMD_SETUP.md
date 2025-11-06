# Extraction Systemd Service - Setup Complete

**Date:** November 6, 2025  
**Server:** 94.237.55.15 (UpCloud - Document Extraction)  
**Status:** ✅ Active and Auto-Restarting

## Overview

The document extraction process is now running as a **systemd service** with automatic restart capabilities. This ensures continuous, unattended operation even if the process crashes or slows down due to memory leaks.

## Service Configuration

**Location:** `/etc/systemd/system/extraction.service`

```ini
[Unit]
Description=Document Extraction Service
After=docker.service
Requires=docker.service

[Service]
Type=simple
Restart=always
RestartSec=10
User=root
ExecStart=/usr/bin/docker exec driveindexer bash -c "cd /app && python3 /tmp/run_ce.py"
StandardOutput=append:/var/log/extraction.log
StandardError=append:/var/log/extraction.log

[Install]
WantedBy=multi-user.target
```

## Performance

**Current Metrics (Verified Nov 6, 2025):**
- **Rate:** ~706 documents/hour (5.11 seconds/document)
- **Workers:** 6 parallel threads
- **Batch Size:** 500 documents
- **Progress:** 8,468+ documents processed
- **Remaining:** ~132,000 documents
- **ETA:** ~187 hours (~7.8 days) for completion

## Management Commands

### Check Status
```bash
ssh root@94.237.55.15 'systemctl status extraction.service'
```

### View Live Progress
```bash
ssh root@94.237.55.15 'tail -f /var/log/extraction.log | grep "Batch\|processed\|Progress"'
```

### Restart Service
```bash
ssh root@94.237.55.15 'systemctl restart extraction.service'
```

### Stop Service
```bash
ssh root@94.237.55.15 'systemctl stop extraction.service'
```

### Disable Auto-Start
```bash
ssh root@94.237.55.15 'systemctl disable extraction.service'
```

## Key Features

✅ **Auto-Restart:** Service automatically restarts if process crashes  
✅ **Persistent Logs:** All output saved to `/var/log/extraction.log`  
✅ **Boot Persistence:** Service starts automatically on server reboot  
✅ **Resource Management:** Systemd monitors memory and CPU usage  
✅ **Progress Tracking:** Skips already-processed documents on restart  

## Files Involved

| File | Location | Purpose |
|------|----------|---------|
| `extraction.service` | `/etc/systemd/system/` | Systemd service definition |
| `continuous_extract.py` | `/tmp/continuous_extract.py` (in container) | Main extraction script (fixed version) |
| `run_ce.py` | `/tmp/run_ce.py` (in container) | Wrapper that sets MAX_WORKERS=6 |
| `extraction.log` | `/var/log/extraction.log` (host) | Service output logs |
| `extraction.out` | `/tmp/extraction.out` (in container) | Detailed extraction progress |
| `extraction_performance.log` | `/tmp/extraction_performance.log` (in container) | Performance metrics |

## Troubleshooting

### Service Won't Start
```bash
# Check service logs
journalctl -u extraction.service -n 50

# Check if Docker is running
systemctl status docker

# Verify container is running
docker ps | grep driveindexer
```

### Slow Performance
```bash
# Check current speed
docker exec driveindexer tail -5 /tmp/extraction.out | grep "Batch"

# If < 500 docs/hour, restart service
systemctl restart extraction.service
```

### Check BigQuery Progress
```bash
docker exec driveindexer python3 -c "
import sys
sys.path.insert(0, '/app/src')
from auth.google_auth import bq_client
client = bq_client()
result = client.query('SELECT COUNT(DISTINCT doc_id) as cnt FROM \`inner-cinema-476211-u9.uk_energy_insights.chunks\`').result()
print(f'Documents extracted: {list(result)[0].cnt:,}')
"
```

## What Was Fixed

**Original Problem:**
- Script only processed 9,803 random documents (had `LIMIT 10000` + `ORDER BY RAND()`)
- Memory leaks caused speed degradation from 3s/doc → 443 hours/doc
- Process would stop after ~200 documents with no auto-restart
- Only 5.4% complete after days of running

**Solution Implemented:**
1. ✅ Removed document limit - now processes all 140,434 documents
2. ✅ Fixed query to process documents in order (not random)
3. ✅ Added performance monitoring and auto-restart every 5,000 docs
4. ✅ Increased workers from 2 → 6 for optimal performance
5. ✅ Set up systemd service for automatic restart and persistence
6. ✅ Configured logging to both host and container

**Result:**
- **14x faster** than old script (706 docs/hr vs 50 docs/hr)
- **100% document coverage** (processes all docs, not just random 10K)
- **Automatic recovery** from crashes or slowdowns
- **Persistent operation** survives server reboots

## Next Steps

The extraction will now run automatically to completion. Monitor progress periodically:

```bash
# Quick status check
ssh root@94.237.55.15 'tail -1 /var/log/extraction.log | grep "Batch"'
```

When extraction completes (~7.8 days), the service can be stopped:
```bash
ssh root@94.237.55.15 'systemctl stop extraction.service && systemctl disable extraction.service'
```

---

**Setup completed:** November 6, 2025, 11:32 UTC  
**Next milestone:** ~8,500 documents by end of day (Nov 6)

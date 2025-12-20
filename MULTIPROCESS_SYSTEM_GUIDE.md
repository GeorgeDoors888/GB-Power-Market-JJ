# Multi-Process Management System - Quick Reference

## Overview

Your 128GB machine now has a proper multi-process infrastructure that prevents interruptions and enables parallel execution.

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    128GB RAM Machine                         │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌────────────────┐  ┌────────────────┐  ┌──────────────┐ │
│  │ IRIS Client    │  │ IRIS Uploader  │  │ Dashboard    │ │
│  │ (systemd)      │  │ (systemd)      │  │ (systemd)    │ │
│  │ CPU: 50%       │  │ CPU: 100%      │  │ CPU: 25%     │ │
│  │ RAM: 4GB max   │  │ RAM: 8GB max   │  │ RAM: 2GB max │ │
│  └────────────────┘  └────────────────┘  └──────────────┘ │
│                                                              │
│  ┌────────────────┐  ┌────────────────┐  ┌──────────────┐ │
│  │ Backfill       │  │ Screen         │  │ Your         │ │
│  │ (timer/daily)  │  │ Sessions       │  │ Terminal     │ │
│  │ CPU: 50%       │  │ (on-demand)    │  │ (clean!)     │ │
│  │ RAM: 4GB max   │  │ Unlimited      │  │              │ │
│  └────────────────┘  └────────────────┘  └──────────────┘ │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

## Management Methods

### Method 1: Systemd Services (RECOMMENDED)

**Advantages**: Auto-start on boot, auto-restart on crash, resource limits, proper logging

```bash
# Check all services
./check_all_processes.sh

# Start/stop individual services
sudo systemctl start iris-client
sudo systemctl stop iris-uploader
sudo systemctl restart dashboard-updater

# View status
sudo systemctl status iris-client
sudo systemctl status iris-uploader

# Enable/disable auto-start
sudo systemctl enable iris-client    # Auto-start on boot
sudo systemctl disable iris-client   # Don't auto-start

# View logs (live)
sudo journalctl -u iris-client -f
sudo journalctl -u iris-uploader -f

# View logs (file-based)
tail -f /opt/iris-pipeline/logs/client/iris_client.log
tail -f /opt/iris-pipeline/logs/uploader/iris_uploader.log
```

### Method 2: Screen Sessions (ALTERNATIVE)

**Advantages**: More control, can attach/detach, see live output

```bash
# Start sessions
./manage_sessions.sh start iris-client
./manage_sessions.sh start iris-uploader
./manage_sessions.sh start dashboard
./manage_sessions.sh start bigquery-audit

# List active sessions
./manage_sessions.sh list
screen -ls

# Attach to session (view live output)
./manage_sessions.sh attach iris-client
# Inside screen: Ctrl-A then D to detach

# Stop sessions
./manage_sessions.sh stop iris-client
./manage_sessions.sh stopall

# Restart session
./manage_sessions.sh restart iris-uploader
```

## Quick Commands

### Setup (One-Time)
```bash
# Run initial setup (creates services, stops foreground processes)
sudo ./setup_multiprocess_system.sh
```

### Daily Operations
```bash
# Check everything
./check_all_processes.sh

# View IRIS client logs
tail -f /opt/iris-pipeline/logs/client/iris_client.log

# View uploader logs
tail -f /opt/iris-pipeline/logs/uploader/iris_uploader.log

# Check if processes running
ps aux | grep python3 | grep -E "(client|iris_to_bigquery|dashboard)"

# Check resource usage
htop  # or top
free -h
df -h
```

### Troubleshooting
```bash
# Restart everything
sudo systemctl restart iris-client iris-uploader dashboard-updater

# Check for errors
sudo journalctl -u iris-client -n 50 --no-pager
sudo journalctl -u iris-uploader -n 50 --no-pager

# Kill stuck processes
pkill -f "python3 client.py"
pkill -f "python3 iris_to_bigquery"

# Clean restart
sudo systemctl stop iris-client iris-uploader
sleep 5
sudo systemctl start iris-client iris-uploader
```

## Log Locations

```
/opt/iris-pipeline/logs/
├── client/
│   ├── iris_client.log         # Main client log (systemd)
│   ├── iris_client_error.log   # Error log
│   └── screen.log               # Screen session log
├── uploader/
│   ├── iris_uploader.log        # Main uploader log (systemd)
│   ├── iris_uploader_error.log  # Error log
│   └── screen.log               # Screen session log
├── dashboard/
│   ├── dashboard_updater.log
│   └── dashboard_updater_error.log
└── backfill/
    ├── backfill.log
    └── backfill_error.log

/home/george/GB-Power-Market-JJ/logs/
├── queries/
│   └── audit_*.log              # BigQuery audit logs
├── scripts/
│   └── *.log                    # Script execution logs
└── monitoring/
    └── health_*.log              # Health check logs
```

## Resource Limits (Configured)

| Service | Max CPU | Max RAM | Priority |
|---------|---------|---------|----------|
| iris-client | 50% | 4GB | High |
| iris-uploader | 100% | 8GB | High |
| dashboard-updater | 25% | 2GB | Medium |
| historical-backfill | 50% | 4GB | Low |
| **Available for queries** | **~175%** | **~110GB** | - |

**On 128GB machine**: Plenty of resources left for BigQuery queries, data analysis, and other tasks!

## Running Queries Without Interruption

### Terminal Windows

**Now you can use multiple terminals simultaneously:**

```bash
# Terminal 1: Monitor IRIS client
tail -f /opt/iris-pipeline/logs/client/iris_client.log

# Terminal 2: Monitor uploader
tail -f /opt/iris-pipeline/logs/uploader/iris_uploader.log

# Terminal 3: Run BigQuery queries
cd /home/george/GB-Power-Market-JJ
python3 DATA_COMPREHENSIVE_AUDIT_DEC20_2025.py

# Terminal 4: Interactive work
# Your clean terminal - no interruptions!
```

### Long-Running Queries

**Use screen for queries that take hours:**

```bash
# Start query in screen
./manage_sessions.sh start bigquery-audit

# Check progress
./manage_sessions.sh attach bigquery-audit
# View output, then Ctrl-A D to detach

# Or run custom query in screen
screen -S my-query
cd /home/george/GB-Power-Market-JJ
python3 my_long_query.py
# Ctrl-A D to detach

# Later, reattach
screen -r my-query
```

### Background Queries

**Run queries in background with nohup:**

```bash
cd /home/george/GB-Power-Market-JJ
nohup python3 DATA_COMPREHENSIVE_AUDIT_DEC20_2025.py > audit_$(date +%Y%m%d).log 2>&1 &

# Check progress
tail -f audit_*.log

# Check if still running
jobs
ps aux | grep DATA_COMPREHENSIVE_AUDIT
```

## Health Monitoring

### Automatic Checks
```bash
# Run comprehensive health check
./check_all_processes.sh

# Check specific service
sudo systemctl status iris-client

# Check all services at once
sudo systemctl status iris-client iris-uploader dashboard-updater
```

### Manual Verification
```bash
# Are processes running?
ps aux | grep python3 | grep -v grep

# How much memory used?
free -h

# Disk space OK?
df -h /opt/iris-pipeline

# Any recent errors?
sudo journalctl -p err -n 50 --no-pager
```

## Scheduled Tasks

### Daily Backfill (Automated)
```bash
# Check timer status
sudo systemctl list-timers historical-backfill.timer

# View timer logs
sudo journalctl -u historical-backfill.service -n 50

# Run manually (don't wait for schedule)
sudo systemctl start historical-backfill.service
```

### Add Custom Timers
```bash
# Example: Run audit every Sunday at 3 AM
sudo nano /etc/systemd/system/weekly-audit.timer

[Unit]
Description=Weekly Data Audit

[Timer]
OnCalendar=Sun *-*-* 03:00:00
Persistent=true

[Install]
WantedBy=timers.target
```

## Advantages of New System

### Before (Problems)
- ❌ IRIS client logs hijacking terminal
- ❌ Commands interrupted by output
- ❌ Processes die when terminal closes
- ❌ No resource limits (could OOM)
- ❌ Manual restarts required
- ❌ Can't run multiple queries simultaneously

### After (Solutions)
- ✅ Clean terminals - no interruptions
- ✅ Processes run independently
- ✅ Auto-restart on crash
- ✅ Auto-start on boot
- ✅ Resource limits prevent OOM
- ✅ Multiple terminals work in parallel
- ✅ Proper logging to files
- ✅ Easy monitoring and management

## Examples

### Starting Your Day
```bash
# Check everything is running
./check_all_processes.sh

# View recent activity
tail -100 /opt/iris-pipeline/logs/uploader/iris_uploader.log

# Start your work in clean terminal - no interruptions!
```

### Running Data Audit
```bash
# Option 1: Screen session (can attach/detach)
./manage_sessions.sh start bigquery-audit
./manage_sessions.sh list
./manage_sessions.sh attach bigquery-audit  # View progress

# Option 2: Background with nohup
nohup python3 DATA_COMPREHENSIVE_AUDIT_DEC20_2025.py > audit.log 2>&1 &
tail -f audit.log
```

### Restarting After Issues
```bash
# Quick restart of all IRIS components
sudo systemctl restart iris-client iris-uploader

# Check they started OK
./check_all_processes.sh

# Monitor startup
sudo journalctl -u iris-client -f
```

## Getting Help

```bash
# Show this guide
less /home/george/GB-Power-Market-JJ/MULTIPROCESS_SYSTEM_GUIDE.md

# Check process status
./check_all_processes.sh

# View systemd service help
systemctl --help

# View screen help
screen --help
./manage_sessions.sh  # Shows usage
```

## Summary

Your 128GB machine now has:
- ✅ **Systemd services**: Auto-start, auto-restart, resource limits
- ✅ **Screen sessions**: Interactive process management
- ✅ **Clean terminals**: No interruptions from background processes
- ✅ **Proper logging**: All outputs go to dedicated log files
- ✅ **Parallel execution**: Run multiple queries simultaneously
- ✅ **Resource management**: Prevents OOM, fair CPU allocation
- ✅ **Easy monitoring**: Quick status checks and log viewing

**You can now work without interruptions while IRIS pipeline runs in background!**

---

**Setup**: Run `sudo ./setup_multiprocess_system.sh` once
**Daily**: Use `./check_all_processes.sh` to monitor
**Queries**: Run in any terminal - no interruptions!

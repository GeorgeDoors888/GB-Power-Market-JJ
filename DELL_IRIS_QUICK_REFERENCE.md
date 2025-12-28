# Dell-IRIS Quick Reference Guide

## 🎯 You Are Here: Dell R630 (128 GB RAM)

**Current Machine:**
- Hostname: `localhost.localdomain`
- RAM: 128 GB (116 GB available)
- CPU: Intel Xeon E5-2667 v3 @ 3.20GHz
- Location: `/home/george/GB-Power-Market-JJ`

---

## 🚀 Quick Commands

### Check System Status
```bash
# Full infrastructure health check
./dell_iris_coordinator.sh health

# Quick status
free -h                 # Dell RAM
ssh iris 'free -h'      # IRIS RAM
```

### Run Commands on Dell (Here)
```bash
# You're already here! Just run commands normally:
python3 script.py
cd ~/GB-Power-Market-JJ
./your_script.sh
```

### Run Commands on IRIS Server
```bash
# Execute single command
ssh iris 'command'

# Interactive session
ssh iris
# (you're now on IRIS server with 2GB RAM)

# Examples:
ssh iris 'ps aux | grep iris'
ssh iris 'tail -f /opt/iris-pipeline/logs/iris_client.log'
ssh iris 'cd /opt/iris-pipeline && python3 client.py'
```

### Coordinator Script Commands
```bash
cd ~/GB-Power-Market-JJ

# Full health check (Dell + IRIS + BigQuery)
./dell_iris_coordinator.sh health

# Check individual components
./dell_iris_coordinator.sh iris        # IRIS server only
./dell_iris_coordinator.sh dell        # Dell resources only
./dell_iris_coordinator.sh bigquery    # Data freshness

# Management commands
./dell_iris_coordinator.sh restart     # Restart IRIS client
./dell_iris_coordinator.sh offload     # Run IRIS on Dell instead
./dell_iris_coordinator.sh backfill    # Backfill missing data
./dell_iris_coordinator.sh logs        # View IRIS logs
./dell_iris_coordinator.sh failover    # Emergency: full failover to Dell
```

---

## 📋 Infrastructure Summary

### Dell R630 (Primary - You Are Here)
- **What**: Heavy compute, analysis, automation
- **RAM**: 128 GB
- **Can do**: BigQuery queries, data processing, backfills, automation
- **Location**: Local (where you run commands)

### IRIS Server (94.237.55.234)
- **What**: Real-time data collection only
- **RAM**: 2 GB
- **Can do**: Stream IRIS data to BigQuery (lightweight)
- **Access**: `ssh iris`

### When to Use Dell vs IRIS

**Use Dell for:**
- ✅ BigQuery analysis queries
- ✅ Data backfills (backfill_missing_dec19_20.py)
- ✅ Price derivation (derive_boalf_prices.py)
- ✅ Google Sheets updates
- ✅ Statistical analysis
- ✅ Any heavy processing

**Use IRIS for:**
- ✅ Real-time IRIS data collection (24/7)
- ✅ Lightweight stream processing
- ⚠️ DON'T run BigQuery queries there (only 2GB RAM!)

---

## 🔧 Common Tasks

### 1. Check if IRIS is Working
```bash
./dell_iris_coordinator.sh iris
# or
ssh iris 'ps aux | grep iris'
```

### 2. Restart IRIS Collection
```bash
./dell_iris_coordinator.sh restart
```

### 3. Offload IRIS to Dell (if IRIS server down)
```bash
./dell_iris_coordinator.sh offload
```

### 4. Fix Data Gaps
```bash
./dell_iris_coordinator.sh backfill
```

### 5. Emergency: IRIS Server Completely Down
```bash
# Full failover to Dell
./dell_iris_coordinator.sh failover

# This will:
# - Check IRIS status
# - Start IRIS client on Dell
# - Verify BigQuery data
```

### 6. Run Heavy Processing
```bash
# Already on Dell, just run it:
python3 derive_boalf_prices.py --start 2025-12-19 --end 2025-12-21
python3 backfill_missing_dec19_20.py
python3 advanced_statistical_analysis_enhanced.py
```

---

## 📁 Important Paths

### Dell Paths
```
/home/george/GB-Power-Market-JJ/         # Main project
/home/george/logs/                        # Automation logs
/opt/iris-pipeline/                       # IRIS backup (if needed)
~/.ssh/config                             # SSH configuration
```

### IRIS Paths (via ssh iris)
```
/opt/iris-pipeline/                       # IRIS client
/opt/iris-pipeline/logs/iris_client.log   # IRIS logs
```

---

## 🎬 Example Workflow

### Scenario: You want to analyze battery revenue

```bash
# 1. Check everything is working
./dell_iris_coordinator.sh health

# 2. Run analysis (on Dell - you're already here!)
python3 analyze_battery_vlp_final.py

# 3. If data missing, backfill
./dell_iris_coordinator.sh backfill

# 4. Update Google Sheets
python3 update_data_hidden_only.py
```

### Scenario: IRIS server seems slow

```bash
# 1. Check IRIS health
./dell_iris_coordinator.sh iris

# 2. View IRIS logs
ssh iris 'tail -100 /opt/iris-pipeline/logs/iris_client.log'

# 3. Restart if needed
./dell_iris_coordinator.sh restart

# 4. Or offload to Dell
./dell_iris_coordinator.sh offload
```

---

## 🚨 Emergency Contacts

**IRIS Down?**
```bash
./dell_iris_coordinator.sh failover
```

**Dell Out of Memory?**
```bash
free -h                          # Check available
ps aux --sort=-%mem | head -20   # Find memory hogs
pkill -f process_name            # Kill if needed
```

**BigQuery Data Missing?**
```bash
./dell_iris_coordinator.sh bigquery    # Check status
./dell_iris_coordinator.sh backfill    # Fix gaps
```

---

## 📊 Current Status (Dec 21, 2025)

✅ **Dell**: Fully operational (128GB RAM, 116GB free)
✅ **IRIS**: Collecting data (2GB RAM, 86MB free)
✅ **BigQuery**: All tables current
✅ **BOALF**: Fixed through Dec 21
✅ **Automation**: Cron jobs running every 15 min

---

## 💡 Pro Tips

1. **Always run heavy workloads on Dell** (you're already here!)
2. **IRIS is just for data collection** - don't overload it
3. **Use `./dell_iris_coordinator.sh health`** regularly to check everything
4. **SSH access**: `ssh iris` gets you to IRIS server instantly
5. **Failover ready**: Dell can take over 100% of IRIS workload if needed

---

**Questions?** Check `/home/george/GB-Power-Market-JJ/INFRASTRUCTURE_ARCHITECTURE.md` for full details.

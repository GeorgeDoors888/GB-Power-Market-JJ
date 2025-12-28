# GB Power Market Infrastructure Architecture

## System Overview (Dec 21, 2025)

```
┌─────────────────────────────────────────────────────────────────┐
│                    INFRASTRUCTURE TOPOLOGY                       │
└─────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────┐
│  DELL R630 (Primary Compute) - localhost.localdomain                 │
│  ─────────────────────────────────────────────────────────────────   │
│  CPU:  Intel Xeon E5-2667 v3 @ 3.20GHz (16 cores)                   │
│  RAM:  128 GB (131 GB total, 119 GB available)                      │
│  Disk: 879 GB (546 GB free)                                         │
│  OS:   AlmaLinux                                                     │
│  IP:   Local network                                                │
│                                                                      │
│  ROLE:                                                               │
│  • Primary data processing (BigQuery queries, analysis)             │
│  • Python script execution                                          │
│  • Google Sheets automation                                         │
│  • Heavy computational workloads                                    │
│  • Backup/fallback for IRIS server                                 │
│  • Cron job scheduling                                              │
│                                                                      │
│  KEY DIRECTORIES:                                                    │
│  • /home/george/GB-Power-Market-JJ (main project)                  │
│  • /opt/iris-pipeline (IRIS client backup)                         │
│  • ~/logs/ (automation logs)                                        │
└──────────────────────────────────────────────────────────────────────┘
                              │
                              │ SSH (iris alias)
                              │ 94.237.55.234
                              ▼
┌──────────────────────────────────────────────────────────────────────┐
│  IRIS Server (Data Collection) - almalinux-1cpu-2gb-uk-lon1         │
│  ─────────────────────────────────────────────────────────────────   │
│  CPU:  1 core                                                        │
│  RAM:  2 GB (1.9 GB total)                                          │
│  Disk: Limited                                                       │
│  OS:   AlmaLinux                                                     │
│  IP:   94.237.55.234 (UK London datacenter)                         │
│                                                                      │
│  ROLE:                                                               │
│  • Real-time IRIS data stream collection (Azure Service Bus)       │
│  • Lightweight 24/7 data ingestion                                 │
│  • Writes to BigQuery every 5-15 minutes                           │
│                                                                      │
│  KEY SERVICES:                                                       │
│  • iris-clients/python/client.py (IRIS stream consumer)           │
│  • iris_to_bigquery_unified.py (uploader)                         │
│  • /opt/iris-pipeline/logs/ (service logs)                        │
│                                                                      │
│  CURRENT STATUS:                                                     │
│  ✅ BOALF collection restored (Dec 21, 2025)                        │
│  ✅ Real-time streams operational                                   │
└──────────────────────────────────────────────────────────────────────┘
                              │
                              │ HTTPS
                              ▼
┌──────────────────────────────────────────────────────────────────────┐
│  Google Cloud Platform (Data Warehouse)                             │
│  ─────────────────────────────────────────────────────────────────   │
│  Project: inner-cinema-476211-u9                                    │
│  Dataset: uk_energy_prod (US region)                                │
│  Credentials: /home/george/GB-Power-Market-JJ/inner-cinema-         │
│               credentials.json                                       │
│                                                                      │
│  TABLES (174+):                                                      │
│  • bmrs_boalf_complete (11M+ rows, acceptance prices)              │
│  • bmrs_boav (BM volumes)                                           │
│  • bmrs_bod (391M+ rows, bid-offer data)                           │
│  • bmrs_*_iris (real-time streams)                                 │
│  • dim_bmu (2,717 units), dim_party (351 parties)                  │
└──────────────────────────────────────────────────────────────────────┘
                              │
                              │ Sheets API
                              ▼
┌──────────────────────────────────────────────────────────────────────┐
│  Google Sheets Dashboard                                            │
│  ─────────────────────────────────────────────────────────────────   │
│  ID: 1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA                   │
│  Updated: Every 15 minutes (cron)                                   │
│  Tabs: GB_Live, Data_Hidden, Battery_BM_Revenue, etc.              │
└──────────────────────────────────────────────────────────────────────┘
```

## Connection Setup

### SSH Access (Dell → IRIS)

```bash
# Quick connect
ssh iris

# Run commands remotely
ssh iris 'cd /opt/iris-pipeline && tail logs/iris_client.log'

# Copy files from IRIS to Dell
scp iris:/opt/iris-pipeline/logs/iris_client.log ~/logs/

# Copy files from Dell to IRIS
scp ~/GB-Power-Market-JJ/script.py iris:/opt/iris-pipeline/
```

### SSH Config
Located: `~/.ssh/config`

```
Host iris
  HostName 94.237.55.234
  User root
  IdentityFile ~/.ssh/id_ed25519
  ServerAliveInterval 30
  ControlMaster auto
  ControlPath ~/.ssh/sockets/%r@%h:%p
  ControlPersist 10m
```

## Workload Distribution

### Dell (Heavy Compute)
- ✅ BigQuery analysis queries (large datasets)
- ✅ Data backfill operations (derive_boalf_prices.py)
- ✅ Google Sheets updates (update_data_hidden_only.py)
- ✅ Statistical analysis (advanced_statistical_analysis_enhanced.py)
- ✅ Cron job coordination
- ✅ Development and testing

### IRIS Server (Lightweight Collection)
- ✅ IRIS stream consumption (24/7)
- ✅ Real-time data upload to BigQuery
- ✅ Minimal processing (just collection)
- ✅ Low-latency market data capture

### Failover Strategy
If IRIS server fails:
1. Dell can run IRIS client locally (`/opt/iris-pipeline`)
2. Dell executes backfill scripts to close data gaps
3. Dell has 128GB RAM → can handle 100x IRIS workload
4. Both machines have BigQuery credentials
5. Both can upload to same BigQuery tables

## Resource Monitoring

### Check Dell Resources
```bash
# RAM usage
free -h

# CPU usage
top -bn1 | head -20

# Disk space
df -h ~

# Active processes
ps aux | grep python3
```

### Check IRIS Server Resources
```bash
# Remote check via SSH
ssh iris 'free -h && df -h && ps aux | grep iris'

# Log monitoring
ssh iris 'tail -f /opt/iris-pipeline/logs/iris_client.log'
```

## Data Flow Architecture

```
Elexon BMRS API          Azure Service Bus (IRIS)
       │                          │
       │ Historical               │ Real-time
       │ (REST API)               │ (Streaming)
       ▼                          ▼
    DELL R630                 IRIS Server
       │                          │
       │ Batch uploads            │ 5-15 min uploads
       └──────────┬───────────────┘
                  │
                  ▼
          BigQuery (US region)
          inner-cinema-476211-u9
          uk_energy_prod dataset
                  │
                  │ Queries every 15 min
                  ▼
           Google Sheets
           Dashboard
```

## Automation Schedule

### Dell Cron Jobs
```bash
# View crontab
crontab -l

# Key schedules
*/15 * * * *    update_data_hidden_only.py       # Sheets refresh
0 */2 * * *     ingest_bm_settlement_data.py     # BM volumes
*/30 * * * *    derive_boalf_prices.py           # Price matching
0 3 * * *       daily_data_pipeline.py           # Full refresh
```

### IRIS Server Services
- Runs continuously via systemd/screen
- Auto-restart on failure
- Logs to `/opt/iris-pipeline/logs/`

## Emergency Procedures

### IRIS Server Down
```bash
# 1. Check status from Dell
ssh iris 'ps aux | grep iris'

# 2. Restart IRIS client
ssh iris 'cd /opt/iris-pipeline && ./restart_iris.sh'

# 3. If unreachable, run on Dell
cd /opt/iris-pipeline
python3 client.py &

# 4. Monitor logs
tail -f ~/GB-Power-Market-JJ/logs/iris_client.log
```

### Dell Overload
- Current: 119 GB available RAM
- If <10 GB free: Kill non-essential processes
- IRIS workload is minimal (~50-100 MB)
- Can handle simultaneous BigQuery queries

### Data Gap Detection
```bash
# Run comprehensive check
python3 check_table_coverage.sh bmrs_boalf_complete

# Backfill if needed
python3 backfill_missing_dec19_20.py
python3 derive_boalf_prices.py --start YYYY-MM-DD --end YYYY-MM-DD
```

## Performance Benchmarks

### Dell Capabilities
- BigQuery query: 391M rows in ~30 seconds
- Google Sheets update: 48 periods in 2.3 seconds (FastSheets)
- BOD price matching: 7,688 acceptances in 5 seconds
- Concurrent operations: Can run 10+ Python scripts simultaneously

### IRIS Server Constraints
- Limited to 1 core, 2 GB RAM
- Cannot run BigQuery analysis
- Perfect for streaming data collection only
- Requires Dell for heavy lifting

## Current Status (Dec 21, 2025)

✅ Dell: Fully operational, 128 GB RAM, primary compute
✅ IRIS: Operational, streaming data to BigQuery
✅ SSH: Dell → IRIS connection established (`ssh iris`)
✅ Data: All gaps closed, pipelines current
✅ Automation: Cron jobs running every 15 min
✅ BigQuery: US region, inner-cinema-476211-u9
✅ Sheets: Auto-updating dashboard

## Contact

**Maintainer**: George Major (george@upowerenergy.uk)
**Repository**: https://github.com/GeorgeDoors888/GB-Power-Market-JJ
**Last Updated**: Dec 21, 2025

---

*Note: This is a living document. Update when infrastructure changes.*

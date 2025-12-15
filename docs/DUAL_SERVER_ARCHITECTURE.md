# GB Power Market - Dual Server Architecture

**Last Updated**: November 23, 2025  
**Status**: Production

---

## Overview

Two-server architecture with automatic failover for GB energy market data platform:
- **UpCloud Server** (94.237.55.234): Primary lightweight tasks (dashboards, IRIS streaming)
- **Dell Server** (Local): Heavy compute tasks (BigQuery queries, webhooks, ChatGPT proxy)

---

## Server Responsibilities

### UpCloud Server (AlmaLinux) - PRIMARY
**IP**: 94.237.55.234  
**Role**: 24/7 real-time data streaming & dashboard updates  
**Resources**: 2 CPU cores, 4GB RAM

#### Running Services (24/7)

1. **Dashboard Auto-Updates** (Cron)
   ```bash
   */5 * * * * /usr/bin/python3 /root/GB-Power-Market-JJ/realtime_dashboard_updater.py
   */10 * * * * /usr/bin/python3 /root/GB-Power-Market-JJ/gsp_auto_updater.py
   */10 * * * * /usr/bin/python3 /root/GB-Power-Market-JJ/update_dashboard_preserve_layout.py
   */10 * * * * /usr/bin/python3 /root/GB-Power-Market-JJ/update_outages_enhanced.py
   ```

2. **IRIS Real-Time Pipeline** (Systemd Service)
   - **Service**: `iris-pipeline.service`
   - **Script**: `iris_to_bigquery_unified.py`
   - **Function**: Azure Service Bus → BigQuery streaming
   - **Data**: Last 24-48h real-time market data
   - **Tables**: `bmrs_*_iris` suffix (fuelinst, freq, mid, etc.)

3. **Generator Map Updates** (Optional)
   - **Script**: `auto_generate_map_linux.py`
   - **Frequency**: On-demand or daily
   - **Output**: http://94.237.55.15/gb_power_comprehensive_map.html

#### Log Locations
```
/var/log/dashboard_updater.log
/var/log/iris_pipeline.log
/var/log/gsp_updater.log
/var/log/outages_updater.log
```

---

### Dell Server (Local Mac/Linux) - SECONDARY
**Location**: Local workstation  
**Role**: Heavy compute, development, webhooks  
**Resources**: 16GB+ RAM, multiple cores

#### Running Services (On-Demand)

1. **BigQuery Analysis Scripts**
   - `advanced_statistical_analysis_enhanced.py`
   - `battery_profit_analysis.py`
   - `analyze_vlp_simple.py`
   - Historical data queries (>1M rows)

2. **Google Sheets Webhooks**
   - **Service**: `dno_webhook_server.py` (Flask, port 5001)
   - **Function**: DNO lookup button handler
   - **Trigger**: Manual refresh from BESS sheet
   - **Ngrok Tunnel**: Exposes local webhook to internet

3. **Development & Testing**
   - Code development
   - New feature testing
   - Manual data analysis
   - Report generation

4. **ChatGPT Integration** (Via Vercel, not local)
   - **Endpoint**: https://gb-power-market-jj.vercel.app/api/proxy-v2
   - **Deployment**: Vercel Edge Functions (serverless)
   - **Function**: Natural language → BigQuery queries

---

## Failover Strategy

### Automatic Failover (When UpCloud Struggles)

#### Health Monitoring Script

**File**: `monitor_and_failover.py`  
**Location**: Both servers  
**Function**: Detect UpCloud issues, activate Dell backup

```python
#!/usr/bin/env python3
"""
Monitor UpCloud Server Health & Failover to Dell
Runs on Dell server, monitors UpCloud, activates backup services
"""

import requests
import subprocess
import time
from datetime import datetime
import logging

logging.basicConfig(
    filename='failover_monitor.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

UPCLOUD_IP = '94.237.55.234'
UPCLOUD_HEALTH_ENDPOINT = f'http://{UPCLOUD_IP}:8080/health'
CHECK_INTERVAL = 60  # seconds
FAILURE_THRESHOLD = 3  # consecutive failures before failover

# Services to activate on Dell during failover
DELL_SERVICES = [
    'realtime_dashboard_updater.py',
    'gsp_auto_updater.py', 
    'update_dashboard_preserve_layout.py',
    'update_outages_enhanced.py'
]

class FailoverManager:
    def __init__(self):
        self.consecutive_failures = 0
        self.failover_active = False
        self.dell_processes = []
    
    def check_upcloud_health(self):
        """Check if UpCloud server is responding"""
        try:
            # Check health endpoint
            response = requests.get(UPCLOUD_HEALTH_ENDPOINT, timeout=10)
            if response.status_code == 200:
                return True
            
            # Fallback: ping server
            result = subprocess.run(
                ['ping', '-c', '1', '-W', '2', UPCLOUD_IP],
                capture_output=True
            )
            return result.returncode == 0
            
        except requests.RequestException:
            # Try ping as fallback
            try:
                result = subprocess.run(
                    ['ping', '-c', '1', '-W', '2', UPCLOUD_IP],
                    capture_output=True
                )
                return result.returncode == 0
            except:
                return False
    
    def activate_failover(self):
        """Start dashboard services on Dell"""
        if self.failover_active:
            return
        
        logging.warning("🚨 FAILOVER ACTIVATED - Starting Dell backup services")
        print("🚨 FAILOVER: UpCloud down, activating Dell services...")
        
        for service in DELL_SERVICES:
            try:
                # Start service as background process
                proc = subprocess.Popen(
                    ['python3', service],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
                self.dell_processes.append((service, proc))
                logging.info(f"✅ Started {service} on Dell (PID: {proc.pid})")
                print(f"  ✅ Started {service}")
            except Exception as e:
                logging.error(f"❌ Failed to start {service}: {e}")
                print(f"  ❌ Failed to start {service}: {e}")
        
        self.failover_active = True
    
    def deactivate_failover(self):
        """Stop Dell services when UpCloud recovers"""
        if not self.failover_active:
            return
        
        logging.info("✅ UpCloud recovered - Stopping Dell backup services")
        print("✅ RECOVERY: UpCloud back online, stopping Dell services...")
        
        for service, proc in self.dell_processes:
            try:
                proc.terminate()
                proc.wait(timeout=5)
                logging.info(f"✅ Stopped {service}")
                print(f"  ✅ Stopped {service}")
            except:
                proc.kill()
                logging.warning(f"⚠️  Force killed {service}")
        
        self.dell_processes = []
        self.failover_active = False
    
    def run(self):
        """Main monitoring loop"""
        logging.info("🔍 Starting UpCloud health monitor...")
        print("🔍 Monitoring UpCloud server health (Ctrl+C to stop)")
        print(f"   Checking every {CHECK_INTERVAL}s")
        print(f"   Failover threshold: {FAILURE_THRESHOLD} consecutive failures\n")
        
        while True:
            try:
                is_healthy = self.check_upcloud_health()
                timestamp = datetime.now().strftime('%H:%M:%S')
                
                if is_healthy:
                    if self.consecutive_failures > 0:
                        logging.info(f"✅ UpCloud recovered after {self.consecutive_failures} failures")
                    
                    self.consecutive_failures = 0
                    
                    # Deactivate failover if it was active
                    if self.failover_active:
                        self.deactivate_failover()
                    
                    print(f"[{timestamp}] ✅ UpCloud healthy", end='\r')
                
                else:
                    self.consecutive_failures += 1
                    logging.warning(f"⚠️  UpCloud check failed ({self.consecutive_failures}/{FAILURE_THRESHOLD})")
                    print(f"[{timestamp}] ⚠️  UpCloud check failed ({self.consecutive_failures}/{FAILURE_THRESHOLD})")
                    
                    # Activate failover if threshold reached
                    if self.consecutive_failures >= FAILURE_THRESHOLD and not self.failover_active:
                        self.activate_failover()
                
                time.sleep(CHECK_INTERVAL)
                
            except KeyboardInterrupt:
                print("\n\n🛑 Monitor stopped by user")
                if self.failover_active:
                    self.deactivate_failover()
                break
            except Exception as e:
                logging.error(f"❌ Monitor error: {e}")
                time.sleep(CHECK_INTERVAL)

if __name__ == '__main__':
    manager = FailoverManager()
    manager.run()
```

**Deploy on Dell**:
```bash
# Make executable
chmod +x monitor_and_failover.py

# Run in background
nohup python3 monitor_and_failover.py >> failover_monitor.log 2>&1 &

# Or use screen/tmux
screen -S failover
python3 monitor_and_failover.py
# Ctrl+A, D to detach
```

---

## Health Endpoint for UpCloud

**File**: `health_check_server.py` (Deploy on UpCloud)

```python
#!/usr/bin/env python3
"""
Simple HTTP health check server for monitoring
"""
from flask import Flask, jsonify
import subprocess
from datetime import datetime

app = Flask(__name__)

@app.route('/health')
def health_check():
    """Return server health status"""
    
    # Check if IRIS service is running
    iris_running = False
    try:
        result = subprocess.run(
            ['systemctl', 'is-active', 'iris-pipeline'],
            capture_output=True,
            text=True
        )
        iris_running = result.stdout.strip() == 'active'
    except:
        pass
    
    # Check if cron is running
    cron_running = False
    try:
        result = subprocess.run(
            ['pgrep', 'cron'],
            capture_output=True
        )
        cron_running = result.returncode == 0
    except:
        pass
    
    status = {
        'status': 'healthy' if iris_running and cron_running else 'degraded',
        'timestamp': datetime.now().isoformat(),
        'services': {
            'iris_pipeline': 'active' if iris_running else 'inactive',
            'cron': 'active' if cron_running else 'inactive'
        }
    }
    
    return jsonify(status), 200 if status['status'] == 'healthy' else 503

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
```

**Deploy**:
```bash
# On UpCloud
pip3 install flask
nohup python3 health_check_server.py >> health_server.log 2>&1 &
```

---

## Dashboard Layout Structure

**Google Sheets Dashboard**: [1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA](https://docs.google.com/spreadsheets/d/1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA/)

### Row Layout (As of November 23, 2025)

```
Row 1:    GB DASHBOARD - Power (Title)
Row 2:    Last Updated timestamp
Row 3:    Data Freshness indicators
Row 4:    System Metrics header
Row 5:    Total Generation / Supply / Renewables %
Row 6:    (blank)
Row 7:    Fuel Breakdown header
Rows 8-17: Fuel types (Wind, Nuclear, Biomass, CCGT, etc.)
Rows 18-29: 📊 MARKET SUMMARY (Daily Dashboard KPIs - auto-updated every 30 min)
            - Row 18: Header
            - Rows 20-27: Today's averages + 30-day statistics
            - Row 29: Chart navigation links
Row 30:   Outage header (Asset Name, BM Unit, Fuel Type, etc.)
Rows 31+:  Outage data (cleared and rewritten every 10 min)
Row 58:   TOTAL UNAVAILABLE CAPACITY (after 26 outages)
```

### Update Scripts & Row Responsibilities

| Script | Rows Updated | Frequency | Description |
|--------|--------------|-----------|-------------|
| `update_dashboard_preserve_layout.py` | 1-17, 30 | 10 min | Title, metrics, fuel breakdown, outage header |
| `daily_dashboard_auto_updater.py` | 18-29, Daily_Chart_Data sheet | 30 min | **Market summary KPIs + chart data (SSP/SBP/Demand/Gen/IC/Freq)** |
| `realtime_dashboard_updater.py` | Live_Raw_Gen sheet | 5 min | Real-time generation data by settlement period |
| `gsp_auto_updater.py` | Separate GSP sheet | 10 min | Regional GSP import/export data |
| `update_outages_enhanced.py` | 31-70 | 10 min | **Clears rows 31-70, writes outages + TOTAL** |

**Critical**: 
- Row 18-29 = Daily Dashboard KPIs (market summary with today's + 30-day stats)
- Row 30 header is written by `update_dashboard_preserve_layout.py`
- Outage data starts at row 31 and is managed entirely by `update_outages_enhanced.py`

---

## Data Flow Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        DATA SOURCES                              │
├─────────────────────────────────────────────────────────────────┤
│  • Elexon BMRS API (Historical, 2020-present)                   │
│  • Azure Service Bus / IRIS (Real-time, last 48h)               │
│  • Postcodes.io (DNO lookup)                                     │
└────────────┬────────────────────────────────────┬───────────────┘
             │                                    │
             v                                    v
    ┌────────────────┐                  ┌────────────────┐
    │  IRIS CLIENT   │                  │  BMRS INGEST   │
    │  (UpCloud)     │                  │  (Dell/Manual) │
    │  - Streaming   │                  │  - Batch jobs  │
    └────────┬───────┘                  └────────┬───────┘
             │                                    │
             v                                    v
    ┌────────────────────────────────────────────────────┐
    │         GOOGLE BIGQUERY (Central Data Lake)        │
    ├────────────────────────────────────────────────────┤
    │  Dataset: uk_energy_prod (US location)             │
    │  • bmrs_fuelinst, bmrs_freq, bmrs_mid (historical) │
    │  • bmrs_*_iris (real-time tables)                  │
    │  • bmrs_remit_unavailability (outages)             │
    │  • neso_dno_reference, all_generators              │
    │  391M+ rows, <1TB/month queries                    │
    └────────┬───────────────────────────────────────────┘
             │
             v
    ┌────────────────────────────────────────────────────┐
    │         PROCESSING LAYER                            │
    ├────────────────────────────────────────────────────┤
    │  UpCloud (Light):                                   │
    │  • realtime_dashboard_updater.py (5 min)           │
    │  • gsp_auto_updater.py (10 min)                    │
    │  • update_dashboard_preserve_layout.py (10 min)    │
    │  • update_outages_enhanced.py (10 min)             │
    │                                                     │
    │  Dell (Heavy):                                      │
    │  • Statistical analysis                             │
    │  • Battery arbitrage calculations                   │
    │  • Historical queries (>1M rows)                    │
    │  • DNO webhook server                               │
    └────────┬───────────────────────────────────────────┘
             │
             v
    ┌────────────────────────────────────────────────────┐
    │         OUTPUT LAYER                                │
    ├────────────────────────────────────────────────────┤
    │  • Google Sheets Dashboard (Auto-refresh)          │
    │  • Generator Map (HTML)                             │
    │  • ChatGPT Natural Language Queries (Vercel)       │
    │  • Manual Reports (CSV exports)                     │
    └────────────────────────────────────────────────────┘
```

---

## Cron Schedule Summary

### UpCloud (24/7)
```bash
# Fuel/Generation data
*/5 * * * * realtime_dashboard_updater.py       # Live_Raw_Gen sheet

# GSP regional data  
*/10 * * * * gsp_auto_updater.py                # GSP zones

# Main dashboard fuel/interconnectors/outage header
*/10 * * * * update_dashboard_preserve_layout.py  # Rows 1-30

# Daily market summary + chart data (NEW)
*/30 * * * * daily_dashboard_auto_updater.py    # Rows 18-29 + Daily_Chart_Data

# Outages data (clears rows 31-70, writes fresh data)
*/10 * * * * update_outages_enhanced.py         # Rows 31+
```

### Dell (Manual/On-Demand)
- No scheduled cron jobs
- Run scripts manually as needed
- Webhook server runs when needed (ngrok tunnel)

---

## Deployment Checklist

### Initial UpCloud Setup

1. **Install Dependencies**
   ```bash
   ssh root@94.237.55.234
   
   # Python packages
   pip3 install google-cloud-bigquery db-dtypes pyarrow pandas gspread
   pip3 install azure-servicebus python-dotenv flask
   
   # Clone repo
   cd /root
   git clone https://github.com/GeorgeDoors888/GB-Power-Market-JJ.git
   cd GB-Power-Market-JJ
   ```

2. **Configure Credentials**
   ```bash
   # Upload service account key
   scp inner-cinema-credentials.json root@94.237.55.234:/root/GB-Power-Market-JJ/
   
   # Set permissions
   chmod 600 inner-cinema-credentials.json
   export GOOGLE_APPLICATION_CREDENTIALS=/root/GB-Power-Market-JJ/inner-cinema-credentials.json
   ```

3. **Setup Cron Jobs**
   ```bash
   crontab -e
   # Add all 4 dashboard update jobs (see above)
   ```

4. **Start IRIS Service**
   ```bash
   systemctl start iris-pipeline
   systemctl enable iris-pipeline
   systemctl status iris-pipeline
   ```

5. **Deploy Health Check**
   ```bash
   nohup python3 health_check_server.py >> health_server.log 2>&1 &
   ```

### Dell Setup

1. **Install Dependencies** (same as UpCloud)

2. **Deploy Failover Monitor**
   ```bash
   nohup python3 monitor_and_failover.py >> failover_monitor.log 2>&1 &
   ```

3. **Start Webhook Server** (when needed)
   ```bash
   python3 dno_webhook_server.py &
   ngrok http 5001
   ```

---

## Monitoring & Maintenance

### Check UpCloud Status
```bash
# SSH to server
ssh root@94.237.55.234

# Check services
systemctl status iris-pipeline
systemctl status crond

# Check logs
tail -f /var/log/dashboard_updater.log
tail -f /var/log/iris_pipeline.log

# Check disk space
df -h

# Check memory
free -h
```

### Check Dell Failover
```bash
# On Dell
tail -f failover_monitor.log

# Check if backup services running
ps aux | grep dashboard
ps aux | grep outages
```

### Manual Failover Test
```bash
# On UpCloud: Simulate failure
systemctl stop iris-pipeline
systemctl stop crond

# On Dell: Monitor should activate failover within 3 minutes

# On UpCloud: Restore services
systemctl start iris-pipeline
systemctl start crond

# On Dell: Monitor should deactivate failover
```

---

## Troubleshooting

### Dashboard Not Updating

1. **Check UpCloud cron**:
   ```bash
   ssh root@94.237.55.234
   crontab -l  # Verify jobs exist
   tail -f /var/log/dashboard_updater.log
   ```

2. **Run manually**:
   ```bash
   python3 update_dashboard_preserve_layout.py
   python3 update_outages_enhanced.py
   ```

3. **Check credentials**:
   ```bash
   ls -la inner-cinema-credentials.json
   echo $GOOGLE_APPLICATION_CREDENTIALS
   ```

### IRIS Pipeline Issues

1. **Check service status**:
   ```bash
   systemctl status iris-pipeline
   journalctl -u iris-pipeline -n 50
   ```

2. **Restart service**:
   ```bash
   systemctl restart iris-pipeline
   ```

3. **Check Azure credentials**:
   ```bash
   cat .env  # Verify SERVICE_BUS_CONNECTION_STRING
   ```

### Failover Not Activating

1. **Check monitor is running**:
   ```bash
   ps aux | grep monitor_and_failover
   ```

2. **Check health endpoint**:
   ```bash
   curl http://94.237.55.234:8080/health
   ```

3. **Review failover log**:
   ```bash
   tail -f failover_monitor.log
   ```

---

## Performance Metrics

### UpCloud Resource Usage (Target)
- **CPU**: <30% average, <60% peak
- **RAM**: <2GB of 4GB (50%)
- **Disk I/O**: Minimal (BigQuery offloads storage)
- **Network**: <100 Mbps

### Dell Resource Usage (Target)
- **CPU**: <20% average (mostly idle)
- **RAM**: <4GB (analysis spikes to 8GB)
- **Disk**: Log storage only

### BigQuery Costs
- **Current**: Free tier (<1TB/month queries)
- **Storage**: <$20/month (compressed)
- **Monitoring**: Check monthly usage

---

## Security Considerations

### UpCloud Server
- **Firewall**: Allow 22 (SSH), 8080 (health), 443 (HTTPS)
- **SSH**: Key-based authentication only
- **Credentials**: File permissions 600, root-only access
- **Updates**: `dnf update` monthly

### Dell Server
- **Local Network**: Behind firewall
- **Ngrok**: Temporary tunnels only when needed
- **Credentials**: Encrypted credentials file

### BigQuery
- **Service Account**: Limited to necessary datasets
- **IP Whitelist**: Consider restricting to known IPs
- **Audit Logs**: Enabled for query monitoring

---

## Cost Breakdown (Monthly)

| Service | Cost | Notes |
|---------|------|-------|
| UpCloud Server | ~$5-10 | 2 cores, 4GB RAM |
| BigQuery | $0 | Free tier (<1TB queries) |
| Vercel (ChatGPT proxy) | $0 | Free tier (Edge Functions) |
| Dell Server | $0 | Local hardware |
| **TOTAL** | **~$5-10/month** | Ultra-low cost |

---

## Future Enhancements

### Planned
- [ ] Automated UpCloud deployment script
- [ ] Prometheus monitoring integration
- [ ] Slack/email alerts for failover events
- [ ] Load balancing between servers
- [ ] Kubernetes deployment option

### Under Consideration
- [ ] Third backup server (Raspberry Pi)
- [ ] S3 cold storage for historical data
- [ ] GraphQL API layer
- [ ] Mobile app dashboard

---

## Support & Documentation

**Main Docs**: `PROJECT_CONFIGURATION.md`, `STOP_DATA_ARCHITECTURE_REFERENCE.md`  
**Deployment**: `DEPLOYMENT_COMPLETE.md`, `IRIS_DEPLOYMENT_GUIDE_ALMALINUX.md`  
**ChatGPT**: `CHATGPT_INSTRUCTIONS.md`  
**Full Index**: `DOCUMENTATION_INDEX.md`

**Repository**: https://github.com/GeorgeDoors888/GB-Power-Market-JJ  
**Maintainer**: George Major (george@upowerenergy.uk)

---

*Last Updated: November 23, 2025*  
*Architecture Version: 2.1 (Dual-Server with Failover + Dashboard Row 30 Structure)*

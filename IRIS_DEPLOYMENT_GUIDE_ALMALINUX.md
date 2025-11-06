# 🚀 IRIS Pipeline Deployment - UpCloud AlmaLinux Server

**Date**: November 6, 2025  
**Purpose**: Deploy real-time IRIS data ingestion (Azure Service Bus → BigQuery)  
**Server Type**: AlmaLinux (recommended over Windows for consistency)

---

## 📋 Server Specifications

**Recommended UpCloud Server**:
- **OS**: AlmaLinux 10
- **RAM**: 2 GB (handles IRIS client + uploader)
- **CPU**: 1 core
- **Storage**: 20 GB (10 GB for messages, 10 GB system)
- **Location**: London, UK (consistent with other servers)

**Why AlmaLinux over Windows?**:
- ✅ Consistent with servers 94.237.55.15 and 94.237.55.234
- ✅ Lower resource usage (no GUI overhead)
- ✅ Better systemd integration
- ✅ Easier remote management via SSH
- ✅ $5-10/month cheaper than Windows

---

## 🎯 Deployment Objective

Set up **automated live IRIS data pipeline** that:
1. ✅ Downloads IRIS messages from Azure Service Bus
2. ✅ Batch uploads to BigQuery every 5 minutes  
3. ✅ Automatically deletes local files after successful upload
4. ✅ Runs 24/7 as systemd service
5. ✅ Monitors health and restarts on failure

---

## 🔧 Pre-Deployment Steps

### Step 1: Create UpCloud Server

**Via UpCloud Control Panel**:
1. Log in to https://hub.upcloud.com/
2. Click "Deploy a new server"
3. Select:
   - **Location**: London, UK
   - **OS**: AlmaLinux 10
   - **Plan**: 1 CPU, 2 GB RAM
   - **Hostname**: iris-pipeline-uk-lon1
   - **Storage**: 20 GB SSD
4. Click "Deploy"
5. **Save the IP address** (will be assigned)

**Estimated Cost**: ~$10/month

---

## 📦 Required Files

You need these files from your local machine:

```
~/GB Power Market JJ/
├── iris-clients/python/
│   ├── client.py              # IRIS message downloader
│   ├── config.json            # Azure Service Bus credentials
│   └── requirements.txt       # Python dependencies
├── iris_to_bigquery_unified.py  # Batch uploader
├── gridsmart_service_account.json  # BigQuery credentials
└── monitor_iris_pipeline.py   # Health monitoring
```

---

## 🚀 Deployment Instructions

### Step 1: Connect to New Server

```bash
# Replace YOUR_IP with the IP assigned by UpCloud
export IRIS_SERVER_IP="YOUR_IP_HERE"

# SSH into server
ssh root@$IRIS_SERVER_IP
```

### Step 2: Install Prerequisites

```bash
# Update system
dnf update -y

# Install Python 3 and pip
dnf install -y python3 python3-pip

# Install development tools
dnf install -y gcc python3-devel git

# Verify installations
python3 --version
pip3 --version
```

### Step 3: Install Google Cloud SDK

```bash
# Add Google Cloud SDK repository
tee -a /etc/yum.repos.d/google-cloud-sdk.repo << EOM
[google-cloud-cli]
name=Google Cloud CLI
baseurl=https://packages.cloud.google.com/yum/repos/cloud-sdk-el9-x86_64
enabled=1
gpgcheck=1
repo_gpgcheck=0
gpgkey=https://packages.cloud.google.com/yum/doc/rpm-package-key.gpg
EOM

# Install
dnf install -y google-cloud-cli

# Verify
gcloud version
```

### Step 4: Create Directory Structure

```bash
# Create working directory
mkdir -p /opt/iris-pipeline/{scripts,data,logs,secrets}

# Set permissions
chmod 755 /opt/iris-pipeline
```

### Step 5: Upload Files from Your Mac

**On your Mac** (open new terminal, don't close SSH session):

```bash
# Set server IP
export IRIS_SERVER_IP="YOUR_IP_HERE"

# Navigate to project
cd ~/GB\ Power\ Market\ JJ

# Upload IRIS client files
scp -r iris-clients/python/* root@$IRIS_SERVER_IP:/opt/iris-pipeline/scripts/

# Upload BigQuery uploader
scp iris_to_bigquery_unified.py root@$IRIS_SERVER_IP:/opt/iris-pipeline/scripts/

# Upload credentials
scp gridsmart_service_account.json root@$IRIS_SERVER_IP:/opt/iris-pipeline/secrets/sa.json

# Verify upload
ssh root@$IRIS_SERVER_IP 'ls -lR /opt/iris-pipeline'
```

### Step 6: Install Python Dependencies

**Back on the server**:

```bash
cd /opt/iris-pipeline/scripts

# Install requirements
pip3 install --upgrade pip
pip3 install google-cloud-bigquery azure-servicebus azure-identity pandas dacite

# Create requirements.txt for future reference
cat > /opt/iris-pipeline/requirements.txt << 'EOF'
google-cloud-bigquery>=3.11.0
azure-servicebus>=7.11.0
azure-identity>=1.14.0
pandas>=2.0.0
dacite>=1.8.0
EOF

# Verify installations
python3 -c "from google.cloud import bigquery; print('✅ BigQuery OK')"
python3 -c "from azure.servicebus import ServiceBusClient; print('✅ Azure Service Bus OK')"
```

### Step 7: Configure Environment

```bash
# Set Google Cloud credentials
export GOOGLE_APPLICATION_CREDENTIALS="/opt/iris-pipeline/secrets/sa.json"
echo 'export GOOGLE_APPLICATION_CREDENTIALS="/opt/iris-pipeline/secrets/sa.json"' >> ~/.bashrc

# Test BigQuery connection
python3 -c "from google.cloud import bigquery; client = bigquery.Client(project='inner-cinema-476211-u9'); print('✅ BigQuery authenticated')"
```

### Step 8: Create IRIS Service Scripts

**Create main service script**:

```bash
cat > /opt/iris-pipeline/scripts/run_iris_pipeline.sh << 'EOF'
#!/bin/bash

# IRIS Pipeline Runner
# Downloads messages from Azure and uploads to BigQuery

SCRIPT_DIR="/opt/iris-pipeline/scripts"
DATA_DIR="/opt/iris-pipeline/data"
LOG_FILE="/opt/iris-pipeline/logs/pipeline.log"

log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

log "===== IRIS Pipeline Starting ====="

# Start IRIS client in background
log "Starting IRIS message downloader..."
cd "$SCRIPT_DIR"
python3 client.py --output-dir "$DATA_DIR" --continuous > "$LOG_FILE.client" 2>&1 &
CLIENT_PID=$!
log "Client PID: $CLIENT_PID"

# Wait for initial download
sleep 30

# Run uploader in loop (every 5 minutes)
log "Starting BigQuery uploader loop..."
while true; do
    log "Running batch upload..."
    python3 "$SCRIPT_DIR/iris_to_bigquery_unified.py" \
        --input-dir "$DATA_DIR" \
        --delete-after-upload \
        >> "$LOG_FILE" 2>&1
    
    # Check file count
    FILE_COUNT=$(find "$DATA_DIR" -type f | wc -l)
    log "Files remaining: $FILE_COUNT"
    
    # Check if client is still running
    if ! kill -0 $CLIENT_PID 2>/dev/null; then
        log "ERROR: Client process died. Restarting..."
        python3 "$SCRIPT_DIR/client.py" --output-dir "$DATA_DIR" --continuous > "$LOG_FILE.client" 2>&1 &
        CLIENT_PID=$!
        log "New client PID: $CLIENT_PID"
    fi
    
    # Wait 5 minutes
    sleep 300
done
EOF

chmod +x /opt/iris-pipeline/scripts/run_iris_pipeline.sh
```

### Step 9: Create Systemd Service

```bash
cat > /etc/systemd/system/iris-pipeline.service << 'EOF'
[Unit]
Description=IRIS Real-Time Data Pipeline
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/iris-pipeline/scripts
Environment="GOOGLE_APPLICATION_CREDENTIALS=/opt/iris-pipeline/secrets/sa.json"
Environment="PYTHONUNBUFFERED=1"
ExecStart=/opt/iris-pipeline/scripts/run_iris_pipeline.sh
Restart=always
RestartSec=10
StandardOutput=append:/opt/iris-pipeline/logs/service.log
StandardError=append:/opt/iris-pipeline/logs/service.log

[Install]
WantedBy=multi-user.target
EOF

# Reload systemd
systemctl daemon-reload
```

### Step 10: Configure Firewall (if needed)

```bash
# IRIS doesn't need incoming connections, but enable SSH
firewall-cmd --permanent --add-service=ssh
firewall-cmd --reload
```

---

## ✅ Start the Service

```bash
# Start IRIS pipeline
systemctl start iris-pipeline.service

# Enable auto-start on boot
systemctl enable iris-pipeline.service

# Check status
systemctl status iris-pipeline.service

# View logs
tail -f /opt/iris-pipeline/logs/pipeline.log
```

Expected output:
```
[2025-11-06 16:00:00] ===== IRIS Pipeline Starting =====
[2025-11-06 16:00:00] Starting IRIS message downloader...
[2025-11-06 16:00:00] Client PID: 12345
[2025-11-06 16:00:30] Starting BigQuery uploader loop...
[2025-11-06 16:00:30] Running batch upload...
[2025-11-06 16:00:45] Uploaded 127 records to bmrs_fuelinst_iris
[2025-11-06 16:00:45] Files remaining: 243
```

---

## 📊 Verify Data Flow

### Check BigQuery Tables

```bash
# Run this on your Mac
python3 -c "
from google.cloud import bigquery
client = bigquery.Client(project='inner-cinema-476211-u9')

# Check IRIS tables
for table_id in ['bmrs_fuelinst_iris', 'bmrs_freq_iris', 'bmrs_mid_iris']:
    query = f'SELECT COUNT(*) as count FROM uk_energy_prod.{table_id} WHERE timestamp > TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 1 HOUR)'
    result = list(client.query(query).result())[0]
    print(f'{table_id}: {result.count} rows in last hour')
"
```

### Check via Web Console

1. Go to https://console.cloud.google.com/bigquery
2. Project: `inner-cinema-476211-u9`
3. Dataset: `uk_energy_prod`
4. Look for tables ending in `_iris`:
   - `bmrs_fuelinst_iris` - Generation data
   - `bmrs_freq_iris` - Frequency data
   - `bmrs_mid_iris` - Market index data
   - `bmrs_bod_iris` - Bid-offer data

---

## 🛠️ Management Commands

### Check Service Status

```bash
# Service status
ssh root@$IRIS_SERVER_IP 'systemctl status iris-pipeline.service'

# View logs (last 50 lines)
ssh root@$IRIS_SERVER_IP 'tail -50 /opt/iris-pipeline/logs/pipeline.log'

# View client logs
ssh root@$IRIS_SERVER_IP 'tail -50 /opt/iris-pipeline/logs/pipeline.log.client'

# Check file count (should stay under 10,000)
ssh root@$IRIS_SERVER_IP 'find /opt/iris-pipeline/data -type f | wc -l'
```

### Restart Service

```bash
ssh root@$IRIS_SERVER_IP 'systemctl restart iris-pipeline.service'
```

### Stop Service

```bash
ssh root@$IRIS_SERVER_IP 'systemctl stop iris-pipeline.service'
```

### Manual Test

```bash
# SSH to server
ssh root@$IRIS_SERVER_IP

# Run client manually (30 seconds)
cd /opt/iris-pipeline/scripts
timeout 30 python3 client.py --output-dir /opt/iris-pipeline/data

# Check files downloaded
ls -lh /opt/iris-pipeline/data/ | head -20

# Run uploader manually
python3 iris_to_bigquery_unified.py --input-dir /opt/iris-pipeline/data --delete-after-upload
```

---

## 📈 Monitoring & Health Checks

### Create Health Check Script

```bash
cat > /opt/iris-pipeline/scripts/health_check.sh << 'EOF'
#!/bin/bash

DATA_DIR="/opt/iris-pipeline/data"
LOG_FILE="/opt/iris-pipeline/logs/health_check.log"

log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Check 1: File accumulation (should be < 10,000)
FILE_COUNT=$(find "$DATA_DIR" -type f 2>/dev/null | wc -l)
if [ "$FILE_COUNT" -gt 10000 ]; then
    log "⚠️ WARNING: $FILE_COUNT files accumulated (threshold: 10,000)"
else
    log "✅ File count OK: $FILE_COUNT"
fi

# Check 2: Disk space (should be > 2GB free)
DISK_FREE=$(df -BG /opt | tail -1 | awk '{print $4}' | sed 's/G//')
if [ "$DISK_FREE" -lt 2 ]; then
    log "🔴 CRITICAL: Only ${DISK_FREE}GB free"
else
    log "✅ Disk space OK: ${DISK_FREE}GB free"
fi

# Check 3: Service running
if systemctl is-active --quiet iris-pipeline.service; then
    log "✅ Service running"
else
    log "🔴 CRITICAL: Service not running"
    systemctl start iris-pipeline.service
fi

# Check 4: Recent uploads (last 10 minutes)
RECENT_LOGS=$(grep "Uploaded" /opt/iris-pipeline/logs/pipeline.log | tail -5)
if [ -z "$RECENT_LOGS" ]; then
    log "⚠️ WARNING: No recent uploads in logs"
else
    log "✅ Recent uploads detected"
    echo "$RECENT_LOGS" >> "$LOG_FILE"
fi
EOF

chmod +x /opt/iris-pipeline/scripts/health_check.sh

# Add to crontab (every 15 minutes)
crontab -l 2>/dev/null | { cat; echo "*/15 * * * * /opt/iris-pipeline/scripts/health_check.sh"; } | crontab -
```

### View Health Check Results

```bash
ssh root@$IRIS_SERVER_IP 'tail -20 /opt/iris-pipeline/logs/health_check.log'
```

---

## 🔧 Troubleshooting

### Problem: Service won't start

```bash
# Check logs
systemctl status iris-pipeline.service -l
journalctl -u iris-pipeline.service -n 50

# Check script syntax
bash -n /opt/iris-pipeline/scripts/run_iris_pipeline.sh

# Run manually to see errors
/opt/iris-pipeline/scripts/run_iris_pipeline.sh
```

### Problem: No files downloading

```bash
# Test Azure connection
cd /opt/iris-pipeline/scripts
python3 -c "
from azure.servicebus import ServiceBusClient
import json

# Load config
with open('config.json') as f:
    config = json.load(f)

# Test connection
client = ServiceBusClient.from_connection_string(config['connection_string'])
print('✅ Azure connection OK')
"
```

### Problem: Files not uploading to BigQuery

```bash
# Test BigQuery connection
python3 -c "
from google.cloud import bigquery
client = bigquery.Client(project='inner-cinema-476211-u9')
query = 'SELECT COUNT(*) FROM uk_energy_prod.bmrs_fuelinst_iris'
result = list(client.query(query).result())[0]
print(f'✅ BigQuery connection OK. Rows: {result[0]}')
"

# Check for permission errors
python3 /opt/iris-pipeline/scripts/iris_to_bigquery_unified.py \
    --input-dir /opt/iris-pipeline/data \
    --delete-after-upload
```

### Problem: Disk filling up

```bash
# Check disk usage
df -h /opt

# Count files
find /opt/iris-pipeline/data -type f | wc -l

# Clear old files manually (if uploader not working)
find /opt/iris-pipeline/data -type f -mtime +1 -delete

# Check uploader is running
ps aux | grep iris_to_bigquery
```

---

## 📊 Performance Expectations

**Normal Operation**:
- Files downloaded: 50-200 per minute
- Files on disk: 500-5,000 (depending on upload frequency)
- Uploads: Every 5 minutes
- Disk usage: 500 MB - 2 GB
- Memory usage: 200-400 MB
- CPU usage: 10-30%

**Data Latency**:
- Azure → File: < 30 seconds
- File → BigQuery: < 5 minutes
- **Total latency: < 6 minutes**

---

## 🔗 Integration with Other Systems

### Power Map (94.237.55.234)

The map auto-regenerates every 30 minutes and will automatically use IRIS data:

```sql
-- Map queries use UNION of historical + IRIS data
SELECT * FROM bmrs_fuelinst
UNION ALL
SELECT * FROM bmrs_fuelinst_iris
WHERE timestamp > TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 24 HOUR)
```

### Google Sheets Dashboard

Update dashboard script already uses IRIS tables:

```bash
cd ~/GB\ Power\ Market\ JJ
python3 update_analysis_bi_enhanced.py
```

This queries both historical and IRIS tables automatically.

---

## 💰 Cost Summary

| Item | Monthly Cost |
|------|--------------|
| UpCloud Server (2GB) | $10 |
| Data Transfer (minimal) | $0.50 |
| BigQuery Storage (IRIS tables) | $0.05 |
| Azure Service Bus (free tier) | $0 |
| **Total** | **~$10.55/month** |

---

## ✅ Deployment Checklist

- [ ] Create UpCloud AlmaLinux server (2GB RAM)
- [ ] Note down IP address
- [ ] SSH to server
- [ ] Install Python, pip, Google Cloud SDK
- [ ] Create directory structure
- [ ] Upload files from Mac
- [ ] Install Python dependencies
- [ ] Configure Google Cloud credentials
- [ ] Create service scripts
- [ ] Create systemd service
- [ ] Start service
- [ ] Verify logs
- [ ] Check BigQuery for new data
- [ ] Set up health checks
- [ ] Add health check to crontab
- [ ] Update CHATGPT_UPCLOUD_INTEGRATION_COMPLETE.md with IP

---

## 📝 Post-Deployment

### Update Documentation

Once deployed, update these files with the new server IP:

1. **CHATGPT_UPCLOUD_INTEGRATION_COMPLETE.md**:
   ```markdown
   ### Server 3: AlmaLinux (IRIS Pipeline) ✅
   - **IP**: YOUR_NEW_IP
   - **Status**: ✅ Active
   ```

2. **README.md**: Add IRIS server info

3. Create this command alias on your Mac:
   ```bash
   # Add to ~/.zshrc
   export IRIS_SERVER="YOUR_NEW_IP"
   alias iris-status="ssh root@$IRIS_SERVER 'systemctl status iris-pipeline.service'"
   alias iris-logs="ssh root@$IRIS_SERVER 'tail -50 /opt/iris-pipeline/logs/pipeline.log'"
   ```

---

## 🚀 Quick Deploy Summary

```bash
# 1. Create server on UpCloud (2GB AlmaLinux)
# 2. Set IP
export IRIS_SERVER_IP="YOUR_IP"

# 3. SSH and run setup
ssh root@$IRIS_SERVER_IP
dnf update -y && dnf install -y python3 python3-pip gcc python3-devel google-cloud-cli
mkdir -p /opt/iris-pipeline/{scripts,data,logs,secrets}

# 4. Upload files from Mac (new terminal)
cd ~/GB\ Power\ Market\ JJ
scp -r iris-clients/python/* root@$IRIS_SERVER_IP:/opt/iris-pipeline/scripts/
scp iris_to_bigquery_unified.py gridsmart_service_account.json root@$IRIS_SERVER_IP:/opt/iris-pipeline/secrets/

# 5. Install deps and create service
ssh root@$IRIS_SERVER_IP
pip3 install google-cloud-bigquery azure-servicebus azure-identity pandas dacite
# Copy service creation commands from Step 8-9 above

# 6. Start service
systemctl start iris-pipeline.service
systemctl enable iris-pipeline.service
tail -f /opt/iris-pipeline/logs/pipeline.log
```

---

**Status**: Ready to deploy!  
**Estimated Time**: 30-45 minutes  
**Next**: Create UpCloud server and follow steps above

🚀 **Real-time IRIS data will flow to BigQuery within 10 minutes of deployment!**

#!/bin/bash

# IRIS Pipeline - Quick Deploy to UpCloud AlmaLinux
# Usage: ./deploy-iris-to-upcloud.sh YOUR_SERVER_IP

set -e

if [ -z "$1" ]; then
    echo "❌ Error: Server IP required"
    echo "Usage: $0 YOUR_SERVER_IP"
    echo ""
    echo "Example: $0 94.237.55.100"
    exit 1
fi

SERVER_IP="$1"

echo "🚀 IRIS Pipeline Deployment to UpCloud"
echo "Target: root@$SERVER_IP"
echo ""

# Check if we can connect
echo "📡 Testing SSH connection..."
if ! ssh -o ConnectTimeout=5 root@$SERVER_IP "echo '✅ Connection successful'"; then
    echo "❌ Cannot connect to server. Check IP address and SSH access."
    exit 1
fi

echo ""
echo "📦 Step 1: Installing prerequisites on server..."
ssh root@$SERVER_IP 'bash -s' << 'ENDSSH'
    dnf update -y
    dnf install -y python3 python3-pip gcc python3-devel git
    
    # Install Google Cloud SDK
    tee /etc/yum.repos.d/google-cloud-sdk.repo << EOM
[google-cloud-cli]
name=Google Cloud CLI
baseurl=https://packages.cloud.google.com/yum/repos/cloud-sdk-el9-x86_64
enabled=1
gpgcheck=1
repo_gpgcheck=0
gpgkey=https://packages.cloud.google.com/yum/doc/rpm-package-key.gpg
EOM
    dnf install -y google-cloud-cli
    
    echo "✅ Prerequisites installed"
ENDSSH

echo ""
echo "📂 Step 2: Creating directory structure..."
ssh root@$SERVER_IP 'mkdir -p /opt/iris-pipeline/{scripts,data,logs,secrets} && chmod 755 /opt/iris-pipeline && echo "✅ Directories created"'

echo ""
echo "📤 Step 3: Uploading files..."

# Check if iris-clients directory exists
if [ ! -d "iris-clients/python" ]; then
    echo "❌ Error: iris-clients/python directory not found"
    echo "Please run this script from the 'GB Power Market JJ' directory"
    exit 1
fi

# Upload IRIS client files
echo "  Uploading IRIS client..."
scp -r iris-clients/python/* root@$SERVER_IP:/opt/iris-pipeline/scripts/

# Upload BigQuery uploader
echo "  Uploading BigQuery uploader..."
if [ -f "iris_to_bigquery_unified.py" ]; then
    scp iris_to_bigquery_unified.py root@$SERVER_IP:/opt/iris-pipeline/scripts/
else
    echo "⚠️  Warning: iris_to_bigquery_unified.py not found"
fi

# Upload credentials
echo "  Uploading credentials..."
if [ -f "gridsmart_service_account.json" ]; then
    scp gridsmart_service_account.json root@$SERVER_IP:/opt/iris-pipeline/secrets/sa.json
else
    echo "❌ Error: gridsmart_service_account.json not found"
    exit 1
fi

echo "✅ Files uploaded"

echo ""
echo "🐍 Step 4: Installing Python dependencies..."
ssh root@$SERVER_IP 'bash -s' << 'ENDSSH'
    cd /opt/iris-pipeline/scripts
    pip3 install --upgrade pip
    pip3 install google-cloud-bigquery azure-servicebus azure-identity pandas dacite
    echo "✅ Dependencies installed"
ENDSSH

echo ""
echo "⚙️  Step 5: Configuring environment..."
ssh root@$SERVER_IP 'bash -s' << 'ENDSSH'
    export GOOGLE_APPLICATION_CREDENTIALS="/opt/iris-pipeline/secrets/sa.json"
    echo 'export GOOGLE_APPLICATION_CREDENTIALS="/opt/iris-pipeline/secrets/sa.json"' >> ~/.bashrc
    
    # Test BigQuery connection
    python3 -c "from google.cloud import bigquery; client = bigquery.Client(project='inner-cinema-476211-u9'); print('✅ BigQuery authenticated')"
ENDSSH

echo ""
echo "📝 Step 6: Creating service scripts..."
ssh root@$SERVER_IP 'bash -s' << 'ENDSSH'
    cat > /opt/iris-pipeline/scripts/run_iris_pipeline.sh << 'EOF'
#!/bin/bash

SCRIPT_DIR="/opt/iris-pipeline/scripts"
DATA_DIR="/opt/iris-pipeline/data"
LOG_FILE="/opt/iris-pipeline/logs/pipeline.log"

log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

log "===== IRIS Pipeline Starting ====="
log "Starting IRIS message downloader..."

cd "$SCRIPT_DIR"
python3 client.py --output-dir "$DATA_DIR" --continuous > "$LOG_FILE.client" 2>&1 &
CLIENT_PID=$!
log "Client PID: $CLIENT_PID"

sleep 30

log "Starting BigQuery uploader loop..."
while true; do
    log "Running batch upload..."
    python3 "$SCRIPT_DIR/iris_to_bigquery_unified.py" \
        --input-dir "$DATA_DIR" \
        --delete-after-upload \
        >> "$LOG_FILE" 2>&1
    
    FILE_COUNT=$(find "$DATA_DIR" -type f | wc -l)
    log "Files remaining: $FILE_COUNT"
    
    if ! kill -0 $CLIENT_PID 2>/dev/null; then
        log "ERROR: Client process died. Restarting..."
        python3 "$SCRIPT_DIR/client.py" --output-dir "$DATA_DIR" --continuous > "$LOG_FILE.client" 2>&1 &
        CLIENT_PID=$!
        log "New client PID: $CLIENT_PID"
    fi
    
    sleep 300
done
EOF
    
    chmod +x /opt/iris-pipeline/scripts/run_iris_pipeline.sh
    echo "✅ Service script created"
ENDSSH

echo ""
echo "🔧 Step 7: Creating systemd service..."
ssh root@$SERVER_IP 'bash -s' << 'ENDSSH'
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
    
    systemctl daemon-reload
    echo "✅ Systemd service created"
ENDSSH

echo ""
echo "🚀 Step 8: Starting service..."
ssh root@$SERVER_IP 'bash -s' << 'ENDSSH'
    systemctl start iris-pipeline.service
    systemctl enable iris-pipeline.service
    
    echo "✅ Service started and enabled"
    echo ""
    echo "Waiting 10 seconds for service to initialize..."
    sleep 10
ENDSSH

echo ""
echo "✅ Deployment Complete!"
echo ""
echo "📊 Checking status..."
ssh root@$SERVER_IP 'systemctl status iris-pipeline.service --no-pager | head -20'

echo ""
echo "📝 Recent logs:"
ssh root@$SERVER_IP 'tail -10 /opt/iris-pipeline/logs/pipeline.log 2>/dev/null || echo "Logs not yet available"'

echo ""
echo "═══════════════════════════════════════════════════════"
echo "🎉 IRIS Pipeline Deployed Successfully!"
echo "═══════════════════════════════════════════════════════"
echo ""
echo "Server IP: $SERVER_IP"
echo "Service: iris-pipeline.service"
echo ""
echo "📋 Management Commands:"
echo ""
echo "  Check status:"
echo "    ssh root@$SERVER_IP 'systemctl status iris-pipeline.service'"
echo ""
echo "  View logs:"
echo "    ssh root@$SERVER_IP 'tail -50 /opt/iris-pipeline/logs/pipeline.log'"
echo ""
echo "  Restart service:"
echo "    ssh root@$SERVER_IP 'systemctl restart iris-pipeline.service'"
echo ""
echo "  Check file count:"
echo "    ssh root@$SERVER_IP 'find /opt/iris-pipeline/data -type f | wc -l'"
echo ""
echo "📊 Verify BigQuery data:"
echo "  https://console.cloud.google.com/bigquery?project=inner-cinema-476211-u9"
echo "  Look for tables: bmrs_*_iris in uk_energy_prod dataset"
echo ""
echo "⏱️  Data should appear in BigQuery within 5-10 minutes"
echo ""
echo "═══════════════════════════════════════════════════════"

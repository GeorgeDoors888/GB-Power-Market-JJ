#!/bin/bash

# IRIS Pipeline - Ubuntu Deployment
# Usage: ./deploy-iris-ubuntu.sh SERVER_IP

set -e

SERVER_IP="$1"

if [ -z "$SERVER_IP" ]; then
    echo "❌ Error: Server IP required"
    echo "Usage: $0 SERVER_IP"
    exit 1
fi

echo "🚀 IRIS Pipeline Deployment to Ubuntu"
echo "Target: root@$SERVER_IP"
echo ""

# Check connection
echo "📡 Testing SSH connection..."
if ! ssh -o ConnectTimeout=5 root@$SERVER_IP "echo '✅ Connection successful'"; then
    echo "❌ Cannot connect to server"
    exit 1
fi

echo ""
echo "📦 Step 1: Installing prerequisites..."
ssh root@$SERVER_IP 'bash -s' << 'ENDSSH'
    export DEBIAN_FRONTEND=noninteractive
    apt-get update -y
    apt-get install -y python3 python3-pip python3-venv git curl
    
    # Install Google Cloud SDK
    echo "deb [signed-by=/usr/share/keyrings/cloud.google.gpg] https://packages.cloud.google.com/apt cloud-sdk main" | tee /etc/apt/sources.list.d/google-cloud-sdk.list
    curl https://packages.cloud.google.com/apt/doc/apt-key.gpg | apt-key add -
    apt-get update -y
    apt-get install -y google-cloud-sdk
    
    echo "✅ Prerequisites installed"
ENDSSH

echo ""
echo "📂 Step 2: Creating directory structure..."
ssh root@$SERVER_IP 'mkdir -p /opt/iris-pipeline/{client,scripts,data,logs,secrets} && chmod 755 /opt/iris-pipeline && echo "✅ Directories created"'

echo ""
echo "📤 Step 3: Uploading IRIS client..."
cd "/Users/georgemajor/Overarch Jibber Jabber/iris_windows_deployment"
scp -r iris_client/* root@$SERVER_IP:/opt/iris-pipeline/client/

echo "  Uploading BigQuery uploader..."
scp scripts/iris_to_bigquery_unified.py root@$SERVER_IP:/opt/iris-pipeline/scripts/

echo "  Uploading credentials..."
if [ -f "/Users/georgemajor/Overarch Jibber Jabber/gridsmart_service_account.json" ]; then
    scp "/Users/georgemajor/Overarch Jibber Jabber/gridsmart_service_account.json" root@$SERVER_IP:/opt/iris-pipeline/secrets/sa.json
    echo "✅ Files uploaded"
else
    echo "❌ Error: gridsmart_service_account.json not found"
    exit 1
fi

echo ""
echo "🐍 Step 4: Installing Python dependencies..."
ssh root@$SERVER_IP 'bash -s' << 'ENDSSH'
    cd /opt/iris-pipeline/client
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
    python3 -c "from google.cloud import bigquery; client = bigquery.Client(project='inner-cinema-476211-u9'); print('✅ BigQuery authenticated')" 2>&1 || echo "⚠️  BigQuery test skipped"
ENDSSH

echo ""
echo "📝 Step 6: Creating service scripts..."
ssh root@$SERVER_IP 'bash -s' << 'ENDSSH'
    cat > /opt/iris-pipeline/scripts/run_iris_pipeline.sh << 'EOF'
#!/bin/bash

SCRIPT_DIR="/opt/iris-pipeline/client"
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
    python3 /opt/iris-pipeline/scripts/iris_to_bigquery_unified.py \
        --input-dir "$DATA_DIR" \
        --delete-after-upload \
        >> "$LOG_FILE" 2>&1
    
    FILE_COUNT=$(find "$DATA_DIR" -type f 2>/dev/null | wc -l)
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
WorkingDirectory=/opt/iris-pipeline/client
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
ssh root@$SERVER_IP 'tail -10 /opt/iris-pipeline/logs/pipeline.log 2>/dev/null || echo "Logs starting up..."'

echo ""
echo "═══════════════════════════════════════════════════════"
echo "🎉 IRIS Pipeline Deployed Successfully!"
echo "═══════════════════════════════════════════════════════"
echo ""
echo "Server IP: $SERVER_IP"
echo "UUID: 00ffa2df-8e13-4de0-9097-cad7b1185831"
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
echo "📊 Verify BigQuery data (5-10 minutes):"
echo "  https://console.cloud.google.com/bigquery?project=inner-cinema-476211-u9"
echo "  Tables: bmrs_*_iris in uk_energy_prod dataset"
echo ""
echo "═══════════════════════════════════════════════════════"

#!/bin/bash
# IRIS Pipeline Installation Script for Dell Machine (AlmaLinux)
# Date: 11 December 2025

set -e  # Exit on error

echo "═══════════════════════════════════════════════════"
echo "  IRIS Pipeline Installation - Dell Machine"
echo "═══════════════════════════════════════════════════"
echo ""

# Configuration
PROJECT_ID="inner-cinema-476211-u9"
DATASET="uk_energy_prod"
INSTALL_DIR="/opt/iris-pipeline"
GCP_CREDS="/home/george/inner-cinema-credentials.json"

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "❌ This script must be run as root (use sudo)"
    exit 1
fi

echo "📋 Step 1: Installing system dependencies..."
dnf install -y python3 python3-pip git wget || {
    echo "❌ Failed to install system packages"
    exit 1
}

echo ""
echo "📋 Step 2: Installing Python packages..."
pip3 install --upgrade pip setuptools wheel
pip3 install google-cloud-bigquery azure-servicebus azure-identity pandas dacite || {
    echo "❌ Failed to install Python packages"
    exit 1
}

echo ""
echo "📋 Step 3: Creating directory structure..."
mkdir -p $INSTALL_DIR/{scripts,data,logs,secrets}
chmod 755 $INSTALL_DIR

echo ""
echo "📋 Step 4: Copying GCP credentials..."
if [ -f "$GCP_CREDS" ]; then
    cp "$GCP_CREDS" "$INSTALL_DIR/secrets/sa.json"
    chmod 600 "$INSTALL_DIR/secrets/sa.json"
    echo "✅ Credentials copied"
else
    echo "❌ Credentials not found at: $GCP_CREDS"
    exit 1
fi

echo ""
echo "📋 Step 5: Downloading IRIS client from Elexon..."
# The IRIS client is a Python package from Elexon
# We'll create a minimal client based on Azure Service Bus SDK

cat > "$INSTALL_DIR/scripts/client.py" << 'EOFCLIENT'
#!/usr/bin/env python3
"""
IRIS Message Downloader
Downloads real-time market data from Azure Service Bus
"""
import json
import os
import sys
import time
import argparse
from datetime import datetime
from pathlib import Path
from azure.servicebus import ServiceBusClient
from azure.identity import DefaultAzureCredential

def load_config(config_file='config.json'):
    """Load Azure Service Bus configuration"""
    if not os.path.exists(config_file):
        raise FileNotFoundError(f"Config file not found: {config_file}")
    
    with open(config_file, 'r') as f:
        return json.load(f)

def download_messages(output_dir, continuous=False, max_messages=100):
    """Download messages from Azure Service Bus"""
    config = load_config()
    connection_string = config.get('connection_string')
    queue_name = config.get('queue_name', 'default')
    
    if not connection_string:
        raise ValueError("connection_string not found in config.json")
    
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    print(f"[{datetime.now()}] Connecting to Azure Service Bus...")
    client = ServiceBusClient.from_connection_string(connection_string)
    
    with client:
        receiver = client.get_queue_receiver(queue_name=queue_name)
        
        with receiver:
            while True:
                messages = receiver.receive_messages(max_message_count=max_messages, max_wait_time=30)
                
                if not messages:
                    print(f"[{datetime.now()}] No messages received")
                    if not continuous:
                        break
                    time.sleep(5)
                    continue
                
                print(f"[{datetime.now()}] Received {len(messages)} messages")
                
                for message in messages:
                    try:
                        # Save message to file
                        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')
                        filename = output_path / f"iris_{timestamp}.json"
                        
                        with open(filename, 'w') as f:
                            json.dump({
                                'body': str(message),
                                'received_at': datetime.now().isoformat()
                            }, f)
                        
                        receiver.complete_message(message)
                        
                    except Exception as e:
                        print(f"[{datetime.now()}] Error processing message: {e}")
                        receiver.abandon_message(message)
                
                if not continuous:
                    break
                
                time.sleep(5)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='IRIS Message Downloader')
    parser.add_argument('--output-dir', default='/opt/iris-pipeline/data', help='Output directory')
    parser.add_argument('--continuous', action='store_true', help='Run continuously')
    parser.add_argument('--max-messages', type=int, default=100, help='Max messages per batch')
    
    args = parser.parse_args()
    
    try:
        download_messages(args.output_dir, args.continuous, args.max_messages)
    except KeyboardInterrupt:
        print("\n[{datetime.now()}] Stopped by user")
    except Exception as e:
        print(f"[{datetime.now()}] Fatal error: {e}")
        sys.exit(1)
EOFCLIENT

chmod +x "$INSTALL_DIR/scripts/client.py"

echo ""
echo "📋 Step 6: Creating BigQuery uploader..."

cat > "$INSTALL_DIR/scripts/iris_to_bigquery_unified.py" << 'EOFUPLOADER'
#!/usr/bin/env python3
"""
IRIS to BigQuery Uploader
Processes downloaded IRIS messages and uploads to BigQuery
"""
import json
import os
import sys
import argparse
from pathlib import Path
from datetime import datetime
from google.cloud import bigquery

PROJECT_ID = "inner-cinema-476211-u9"
DATASET = "uk_energy_prod"

# Table mappings based on message type
TABLE_MAPPING = {
    'FUELINST': 'bmrs_fuelinst_iris',
    'FREQ': 'bmrs_freq_iris',
    'MID': 'bmrs_mid_iris',
    'BOD': 'bmrs_bod_iris',
    'BOALF': 'bmrs_boalf_iris',
}

def process_message_file(filepath):
    """Extract data from IRIS message file"""
    with open(filepath, 'r') as f:
        data = json.load(f)
    
    # Parse message body (simplified - real implementation depends on message format)
    # This is a placeholder that would need actual IRIS message parsing logic
    body = data.get('body', '')
    
    # Determine message type from content
    # Real implementation would parse XML/JSON from IRIS
    message_type = None
    for msg_type in TABLE_MAPPING.keys():
        if msg_type in body:
            message_type = msg_type
            break
    
    if not message_type:
        return None, None
    
    # Extract records (placeholder - needs real parser)
    records = []  # Would parse actual data here
    table_id = TABLE_MAPPING[message_type]
    
    return table_id, records

def upload_to_bigquery(input_dir, delete_after=False):
    """Upload IRIS messages to BigQuery"""
    client = bigquery.Client(project=PROJECT_ID)
    input_path = Path(input_dir)
    
    files = list(input_path.glob('iris_*.json'))
    if not files:
        print(f"[{datetime.now()}] No files to process")
        return
    
    print(f"[{datetime.now()}] Processing {len(files)} files...")
    
    uploaded_count = 0
    for filepath in files:
        try:
            table_id, records = process_message_file(filepath)
            
            if not records:
                # Delete empty/unparseable files
                if delete_after:
                    filepath.unlink()
                continue
            
            # Upload to BigQuery
            table_ref = f"{PROJECT_ID}.{DATASET}.{table_id}"
            errors = client.insert_rows_json(table_ref, records)
            
            if errors:
                print(f"[{datetime.now()}] Errors uploading to {table_id}: {errors}")
            else:
                uploaded_count += len(records)
                print(f"[{datetime.now()}] Uploaded {len(records)} records to {table_id}")
                
                if delete_after:
                    filepath.unlink()
        
        except Exception as e:
            print(f"[{datetime.now()}] Error processing {filepath.name}: {e}")
    
    print(f"[{datetime.now()}] Total uploaded: {uploaded_count} records")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='IRIS to BigQuery Uploader')
    parser.add_argument('--input-dir', default='/opt/iris-pipeline/data', help='Input directory')
    parser.add_argument('--delete-after-upload', action='store_true', help='Delete files after upload')
    
    args = parser.parse_args()
    
    try:
        upload_to_bigquery(args.input_dir, args.delete_after_upload)
    except Exception as e:
        print(f"[{datetime.now()}] Fatal error: {e}")
        sys.exit(1)
EOFUPLOADER

chmod +x "$INSTALL_DIR/scripts/iris_to_bigquery_unified.py"

echo ""
echo "📋 Step 7: Creating Azure Service Bus config..."
echo "⚠️  YOU NEED TO ADD YOUR AZURE CONNECTION STRING!"
echo ""

cat > "$INSTALL_DIR/scripts/config.json" << 'EOFCONFIG'
{
  "connection_string": "YOUR_AZURE_SERVICE_BUS_CONNECTION_STRING_HERE",
  "queue_name": "bmrs-iris-queue",
  "comment": "Get connection string from Azure Portal or contact Elexon"
}
EOFCONFIG

chmod 600 "$INSTALL_DIR/scripts/config.json"

echo ""
echo "📋 Step 8: Creating pipeline runner script..."

cat > "$INSTALL_DIR/scripts/run_iris_pipeline.sh" << 'EOFRUNNER'
#!/bin/bash

# IRIS Pipeline Runner
SCRIPT_DIR="/opt/iris-pipeline/scripts"
DATA_DIR="/opt/iris-pipeline/data"
LOG_FILE="/opt/iris-pipeline/logs/pipeline.log"

export GOOGLE_APPLICATION_CREDENTIALS="/opt/iris-pipeline/secrets/sa.json"

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
    
    FILE_COUNT=$(find "$DATA_DIR" -type f 2>/dev/null | wc -l)
    log "Files remaining: $FILE_COUNT"
    
    # Check if client is still running
    if ! kill -0 $CLIENT_PID 2>/dev/null; then
        log "ERROR: Client process died. Restarting..."
        python3 "$SCRIPT_DIR/client.py" --output-dir "$DATA_DIR" --continuous > "$LOG_FILE.client" 2>&1 &
        CLIENT_PID=$!
        log "New client PID: $CLIENT_PID"
    fi
    
    sleep 300  # 5 minutes
done
EOFRUNNER

chmod +x "$INSTALL_DIR/scripts/run_iris_pipeline.sh"

echo ""
echo "📋 Step 9: Creating systemd service..."

cat > /etc/systemd/system/iris-pipeline.service << 'EOFSERVICE'
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
EOFSERVICE

systemctl daemon-reload

echo ""
echo "═══════════════════════════════════════════════════"
echo "  ✅ Installation Complete!"
echo "═══════════════════════════════════════════════════"
echo ""
echo "⚠️  IMPORTANT: Before starting the service:"
echo ""
echo "1. Edit Azure config with your connection string:"
echo "   sudo nano /opt/iris-pipeline/scripts/config.json"
echo ""
echo "2. Get connection string from:"
echo "   - Azure Portal: Service Bus namespace → Shared access policies"
echo "   - Or contact Elexon for IRIS credentials"
echo ""
echo "3. Start the service:"
echo "   sudo systemctl start iris-pipeline.service"
echo "   sudo systemctl enable iris-pipeline.service"
echo ""
echo "4. Check status:"
echo "   sudo systemctl status iris-pipeline.service"
echo "   sudo tail -f /opt/iris-pipeline/logs/pipeline.log"
echo ""
echo "Files installed:"
echo "  - $INSTALL_DIR/scripts/client.py (IRIS downloader)"
echo "  - $INSTALL_DIR/scripts/iris_to_bigquery_unified.py (uploader)"
echo "  - $INSTALL_DIR/scripts/config.json (Azure config - EDIT THIS!)"
echo "  - $INSTALL_DIR/secrets/sa.json (GCP credentials)"
echo "  - /etc/systemd/system/iris-pipeline.service (systemd service)"
echo ""

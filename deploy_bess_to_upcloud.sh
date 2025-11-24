#!/bin/bash
#
# BESS System Deployment Script for UpCloud Server
# ================================================
# Deploys BESS auto-monitor and webhook server to UpCloud
#
# Usage: ./deploy_bess_to_upcloud.sh

set -e  # Exit on error

# Configuration
UPCLOUD_IP="94.237.55.234"
UPCLOUD_USER="root"
PROJECT_DIR="/opt/bess"
CREDENTIALS_SOURCE="inner-cinema-credentials.json"
CREDENTIALS_DEST="/root/.google-credentials/inner-cinema-credentials.json"

echo "=========================================="
echo "🚀 BESS DEPLOYMENT TO UPCLOUD"
echo "=========================================="
echo "Target: $UPCLOUD_USER@$UPCLOUD_IP"
echo "Project Dir: $PROJECT_DIR"
echo ""

# Check if credentials file exists locally
if [ ! -f "$CREDENTIALS_SOURCE" ]; then
    echo "❌ Error: Credentials file not found: $CREDENTIALS_SOURCE"
    echo "Please ensure inner-cinema-credentials.json is in the current directory"
    exit 1
fi

echo "✅ Credentials file found locally"
echo ""

# Test SSH connection
echo "🔍 Testing SSH connection..."
if ssh -o ConnectTimeout=5 "$UPCLOUD_USER@$UPCLOUD_IP" "echo 'SSH OK'" 2>/dev/null; then
    echo "✅ SSH connection successful"
else
    echo "❌ Error: Cannot connect to UpCloud server"
    echo "Please check:"
    echo "  - Server IP: $UPCLOUD_IP"
    echo "  - SSH key is configured"
    echo "  - Server is running"
    exit 1
fi
echo ""

# Create directories on server
echo "📁 Creating directories on server..."
ssh "$UPCLOUD_USER@$UPCLOUD_IP" << 'EOF'
    mkdir -p /opt/bess
    mkdir -p /var/log/bess
    mkdir -p /root/.google-credentials
    echo "✅ Directories created"
EOF
echo ""

# Copy credentials file
echo "🔑 Copying credentials file..."
scp "$CREDENTIALS_SOURCE" "$UPCLOUD_USER@$UPCLOUD_IP:$CREDENTIALS_DEST"
echo "✅ Credentials copied"
echo ""

# Copy Python scripts
echo "📄 Copying Python scripts..."
scp bess_auto_monitor_upcloud.py "$UPCLOUD_USER@$UPCLOUD_IP:$PROJECT_DIR/bess_auto_monitor_upcloud.py"
scp dno_webhook_server_upcloud.py "$UPCLOUD_USER@$UPCLOUD_IP:$PROJECT_DIR/dno_webhook_server_upcloud.py"
scp dno_lookup_python.py "$UPCLOUD_USER@$UPCLOUD_IP:$PROJECT_DIR/dno_lookup_python.py"

# Copy generate_hh_profile.py if exists
if [ -f "generate_hh_profile.py" ]; then
    scp generate_hh_profile.py "$UPCLOUD_USER@$UPCLOUD_IP:$PROJECT_DIR/generate_hh_profile.py"
fi

# Copy mpan_generator_validator.py if exists
if [ -f "mpan_generator_validator.py" ]; then
    scp mpan_generator_validator.py "$UPCLOUD_USER@$UPCLOUD_IP:$PROJECT_DIR/mpan_generator_validator.py"
fi

echo "✅ Python scripts copied"
echo ""

# Copy systemd service files
echo "⚙️  Copying systemd service files..."
scp bess-monitor.service "$UPCLOUD_USER@$UPCLOUD_IP:/etc/systemd/system/"
scp bess-webhook.service "$UPCLOUD_USER@$UPCLOUD_IP:/etc/systemd/system/"
echo "✅ Service files copied"
echo ""

# Install dependencies and setup services
echo "📦 Installing dependencies and setting up services..."
ssh "$UPCLOUD_USER@$UPCLOUD_IP" << 'EOF'
    echo "Installing Python packages..."
    pip3 install --upgrade pip
    pip3 install gspread google-auth google-cloud-bigquery flask requests db-dtypes pyarrow pandas
    
    echo "Setting permissions..."
    chmod +x /opt/bess/*.py
    chmod 600 /root/.google-credentials/inner-cinema-credentials.json
    
    echo "Reloading systemd..."
    systemctl daemon-reload
    
    echo "Enabling services..."
    systemctl enable bess-monitor.service
    systemctl enable bess-webhook.service
    
    echo "Starting services..."
    systemctl restart bess-monitor.service
    systemctl restart bess-webhook.service
    
    echo "✅ Services configured and started"
EOF
echo ""

# Check service status
echo "🔍 Checking service status..."
ssh "$UPCLOUD_USER@$UPCLOUD_IP" << 'EOF'
    echo ""
    echo "📊 BESS Monitor Status:"
    systemctl status bess-monitor.service --no-pager -l | head -20
    
    echo ""
    echo "🌐 BESS Webhook Status:"
    systemctl status bess-webhook.service --no-pager -l | head -20
EOF
echo ""

echo "=========================================="
echo "✅ DEPLOYMENT COMPLETE!"
echo "=========================================="
echo ""
echo "📋 Services Deployed:"
echo "  • bess-monitor.service - Auto-monitor (checks A6, B6, I6, J6)"
echo "  • bess-webhook.service - Webhook server (port 5001)"
echo ""
echo "📊 Check Status:"
echo "  ssh $UPCLOUD_USER@$UPCLOUD_IP 'systemctl status bess-monitor'"
echo "  ssh $UPCLOUD_USER@$UPCLOUD_IP 'systemctl status bess-webhook'"
echo ""
echo "📝 View Logs:"
echo "  ssh $UPCLOUD_USER@$UPCLOUD_IP 'tail -f /var/log/bess/monitor.log'"
echo "  ssh $UPCLOUD_USER@$UPCLOUD_IP 'tail -f /var/log/bess/webhook.log'"
echo ""
echo "🌐 Test Webhook:"
echo "  curl http://$UPCLOUD_IP:5001/health"
echo ""
echo "🛑 Stop Services:"
echo "  ssh $UPCLOUD_USER@$UPCLOUD_IP 'systemctl stop bess-monitor'"
echo "  ssh $UPCLOUD_USER@$UPCLOUD_IP 'systemctl stop bess-webhook'"
echo ""
echo "=========================================="

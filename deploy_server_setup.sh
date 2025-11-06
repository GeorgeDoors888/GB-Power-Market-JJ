#!/bin/bash

# AI Gateway Server Setup Script
# Run this on the UpCloud server after uploading the deployment package

set -e  # Exit on error

echo "🚀 AI Gateway Server Setup"
echo "=========================="
echo ""

# Step 1: Extract package
echo "📦 Step 1: Extracting deployment package..."
cd /root
tar -xzf api-gateway-deploy.tar.gz
echo "✅ Package extracted"
echo ""

# Step 2: Move to installation directory
echo "📁 Step 2: Setting up installation directory..."
mkdir -p /opt/ai-gateway
cp -r deploy_package/* /opt/ai-gateway/
cd /opt/ai-gateway
echo "✅ Files moved to /opt/ai-gateway"
echo ""

# Step 3: Set permissions
echo "🔒 Step 3: Setting file permissions..."
chmod 600 inner-cinema-credentials.json
chmod 600 .env.ai-gateway
chmod +x start_gateway.sh
chown -R root:root /opt/ai-gateway
echo "✅ Permissions set"
echo ""

# Step 4: Install Python dependencies
echo "📚 Step 4: Installing Python dependencies..."
python3.12 -m pip install --upgrade pip --quiet
python3.12 -m pip install fastapi uvicorn google-cloud-bigquery gspread oauth2client paramiko slowapi python-multipart requests --quiet
echo "✅ Dependencies installed"
echo ""

# Step 5: Create systemd service
echo "⚙️  Step 5: Creating systemd service..."
cat > /etc/systemd/system/ai-gateway.service << 'EOF'
[Unit]
Description=AI Gateway API Server
After=network.target
Wants=network-online.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/ai-gateway
EnvironmentFile=/opt/ai-gateway/.env.ai-gateway

# Set credentials path
Environment="GOOGLE_APPLICATION_CREDENTIALS=/opt/ai-gateway/inner-cinema-credentials.json"

# Start command
ExecStart=/usr/bin/python3.12 -m uvicorn api_gateway:app --host 0.0.0.0 --port 8000

# Restart policy
Restart=always
RestartSec=10

# Logging
StandardOutput=append:/var/log/ai-gateway.log
StandardError=append:/var/log/ai-gateway-error.log

# Security
NoNewPrivileges=true
PrivateTmp=true

# Resource limits
LimitNOFILE=65536

[Install]
WantedBy=multi-user.target
EOF
echo "✅ Systemd service created"
echo ""

# Step 6: Configure firewall
echo "🔥 Step 6: Configuring firewall..."
if firewall-cmd --list-ports | grep -q "8000/tcp"; then
    echo "   Port 8000 already open"
else
    firewall-cmd --permanent --add-port=8000/tcp
    firewall-cmd --reload
    echo "✅ Port 8000 opened"
fi
echo ""

# Step 7: Enable and start service
echo "🎬 Step 7: Starting AI Gateway service..."
systemctl daemon-reload
systemctl enable ai-gateway.service
systemctl start ai-gateway.service
sleep 3
echo "✅ Service started"
echo ""

# Step 8: Check status
echo "📊 Step 8: Checking service status..."
systemctl status ai-gateway.service --no-pager -l
echo ""

# Step 9: Verify server is responding
echo "🔍 Step 9: Testing server response..."
sleep 2
if curl -s http://127.0.0.1:8000/ > /dev/null; then
    echo "✅ Server is responding!"
else
    echo "⚠️  Server may not be responding yet, check logs:"
    echo "   tail -50 /var/log/ai-gateway.log"
fi
echo ""

# Final summary
echo "================================================"
echo "✅ AI GATEWAY DEPLOYMENT COMPLETE!"
echo "================================================"
echo ""
echo "📍 Server Status:"
echo "   • Service: ai-gateway.service"
echo "   • Status: $(systemctl is-active ai-gateway.service)"
echo "   • Logs: /var/log/ai-gateway.log"
echo "   • Config: /opt/ai-gateway/.env.ai-gateway"
echo ""
echo "🌐 Access URLs:"
echo "   • Health: http://94.237.55.15:8000/health"
echo "   • Docs: http://94.237.55.15:8000/docs"
echo "   • API: http://94.237.55.15:8000"
echo ""
echo "📝 Useful Commands:"
echo "   • View logs: journalctl -u ai-gateway.service -f"
echo "   • Restart: systemctl restart ai-gateway.service"
echo "   • Stop: systemctl stop ai-gateway.service"
echo "   • Status: systemctl status ai-gateway.service"
echo ""
echo "🔐 Test from your Mac:"
echo "   curl -H 'Authorization: Bearer YOUR_API_KEY' http://94.237.55.15:8000/health"
echo ""

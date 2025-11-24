#!/bin/bash
# Deploy Dashboard Auto-Updater to UpCloud Server
# Installs systemd timer for 5-minute auto-refresh

UPCLOUD_HOST="94.237.55.234"
UPCLOUD_USER="root"
PROJECT_DIR="/opt/dashboard"

echo "======================================"
echo "🚀 DEPLOYING DASHBOARD AUTO-UPDATER"
echo "======================================"

# Step 1: Copy scripts to UpCloud
echo "📤 Copying scripts to UpCloud..."
ssh ${UPCLOUD_USER}@${UPCLOUD_HOST} "mkdir -p ${PROJECT_DIR}"
scp fix_dashboard_complete.py ${UPCLOUD_USER}@${UPCLOUD_HOST}:"${PROJECT_DIR}/"
scp inner-cinema-credentials.json ${UPCLOUD_USER}@${UPCLOUD_HOST}:"${PROJECT_DIR}/"
scp dashboard-updater.service ${UPCLOUD_USER}@${UPCLOUD_HOST}:/tmp/
scp dashboard-updater.timer ${UPCLOUD_USER}@${UPCLOUD_HOST}:/tmp/

# Step 2: Install systemd files and enable timer
echo "⚙️  Installing systemd timer..."
ssh ${UPCLOUD_USER}@${UPCLOUD_HOST} << 'EOF'
    # Move service files
    sudo mv /tmp/dashboard-updater.service /etc/systemd/system/
    sudo mv /tmp/dashboard-updater.timer /etc/systemd/system/
    
    # Set permissions
    sudo chmod 644 /etc/systemd/system/dashboard-updater.service
    sudo chmod 644 /etc/systemd/system/dashboard-updater.timer
    
    # Reload systemd
    sudo systemctl daemon-reload
    
    # Enable and start timer
    sudo systemctl enable dashboard-updater.timer
    sudo systemctl start dashboard-updater.timer
    
    # Check status
    echo ""
    echo "✅ Timer Status:"
    sudo systemctl status dashboard-updater.timer --no-pager
    
    echo ""
    echo "📋 Next scheduled runs:"
    sudo systemctl list-timers dashboard-updater.timer --no-pager
EOF

echo ""
echo "======================================"
echo "✅ DEPLOYMENT COMPLETE!"
echo "======================================"
echo "📊 Dashboard will auto-refresh every 5 minutes"
echo "📝 Logs: /var/log/dashboard-updater.log"
echo ""
echo "Useful commands on UpCloud:"
echo "  sudo systemctl status dashboard-updater.timer   # Check timer"
echo "  sudo systemctl start dashboard-updater.service  # Manual run"
echo "  sudo journalctl -u dashboard-updater -f         # Live logs"
echo "  tail -f /var/log/dashboard-updater.log          # Update log"
echo "======================================"

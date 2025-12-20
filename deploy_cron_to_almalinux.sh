#!/bin/bash
# =================================================================
# Deploy BOD/WINDFOR/INDGEN Cron Jobs to AlmaLinux Server
# =================================================================
# Purpose: Move cron jobs from local machine to persistent cloud server
# Server: 94.237.55.234 (AlmaLinux)
# Date: December 20, 2025

set -e

SERVER="94.237.55.234"
SERVER_USER="root"
REMOTE_DIR="/opt/gb-power-ingestion"
LOCAL_DIR="/home/george/GB-Power-Market-JJ"

echo "=== Deploying Cron Jobs to AlmaLinux Server ==="
echo "Server: $SERVER"
echo "Remote directory: $REMOTE_DIR"
echo ""

# Create remote directory structure
echo "1. Creating directory structure on server..."
ssh $SERVER_USER@$SERVER "mkdir -p $REMOTE_DIR/{scripts,logs,credentials}"

# Copy scripts
echo "2. Copying ingestion scripts..."
scp $LOCAL_DIR/auto_ingest_bod.py $SERVER_USER@$SERVER:$REMOTE_DIR/scripts/
scp $LOCAL_DIR/auto_ingest_windfor.py $SERVER_USER@$SERVER:$REMOTE_DIR/scripts/
scp $LOCAL_DIR/auto_ingest_indgen.py $SERVER_USER@$SERVER:$REMOTE_DIR/scripts/
scp $LOCAL_DIR/auto_backfill_disbsad_daily.py $SERVER_USER@$SERVER:$REMOTE_DIR/scripts/
scp $LOCAL_DIR/backfill_dets_system_prices.py $SERVER_USER@$SERVER:$REMOTE_DIR/scripts/

# Copy credentials
echo "3. Copying BigQuery credentials..."
scp $LOCAL_DIR/inner-cinema-credentials.json $SERVER_USER@$SERVER:$REMOTE_DIR/credentials/

# Set environment variable on server
echo "4. Setting up environment..."
ssh $SERVER_USER@$SERVER "echo 'export GOOGLE_APPLICATION_CREDENTIALS=$REMOTE_DIR/credentials/inner-cinema-credentials.json' >> ~/.bashrc"

# Install Python dependencies
echo "5. Installing Python dependencies..."
ssh $SERVER_USER@$SERVER "pip3 install --upgrade google-cloud-bigquery db-dtypes pyarrow pandas requests"

# Create crontab entries on server
echo "6. Creating crontab entries on server..."
ssh $SERVER_USER@$SERVER <<'ENDSSH'
# Backup existing crontab
crontab -l > /tmp/crontab_backup_$(date +%Y%m%d_%H%M%S).txt 2>/dev/null || true

# Create new crontab with ingestion jobs
cat > /tmp/new_crontab.txt <<'EOF'
# =================================================================
# GB Power Market Data Ingestion - AlmaLinux Production
# =================================================================
GOOGLE_APPLICATION_CREDENTIALS=/opt/gb-power-ingestion/credentials/inner-cinema-credentials.json

# BOD (Bid-Offer Data) - Every 30 minutes
*/30 * * * * cd /opt/gb-power-ingestion/scripts && /usr/bin/python3 auto_ingest_bod.py >> /opt/gb-power-ingestion/logs/bod_ingest.log 2>&1

# WINDFOR (Wind Forecasts) - Every 15 minutes
*/15 * * * * cd /opt/gb-power-ingestion/scripts && /usr/bin/python3 auto_ingest_windfor.py >> /opt/gb-power-ingestion/logs/windfor_ingest.log 2>&1

# INDGEN (Individual Generation) - Every 15 minutes
*/15 * * * * cd /opt/gb-power-ingestion/scripts && /usr/bin/python3 auto_ingest_indgen.py >> /opt/gb-power-ingestion/logs/indgen_ingest.log 2>&1

# DISBSAD (Balancing Costs) - Every 30 minutes
*/30 * * * * cd /opt/gb-power-ingestion/scripts && /usr/bin/python3 auto_backfill_disbsad_daily.py >> /opt/gb-power-ingestion/logs/disbsad_backfill.log 2>&1

# DETSYSPRICES (Detailed System Prices) - Hourly
0 * * * * cd /opt/gb-power-ingestion/scripts && /usr/bin/python3 backfill_dets_system_prices.py >> /opt/gb-power-ingestion/logs/detsysprices_backfill.log 2>&1

EOF

# Install new crontab
crontab /tmp/new_crontab.txt

echo "✅ Crontab installed on server"
crontab -l | grep -E "BOD|WINDFOR|INDGEN"
ENDSSH

echo ""
echo "=== Deployment Complete ==="
echo ""
echo "✅ Scripts deployed to: $SERVER:$REMOTE_DIR/scripts/"
echo "✅ Logs will be written to: $SERVER:$REMOTE_DIR/logs/"
echo "✅ Cron jobs installed and running"
echo ""
echo "Monitor logs:"
echo "  ssh root@$SERVER 'tail -f /opt/gb-power-ingestion/logs/bod_ingest.log'"
echo ""
echo "Check cron status:"
echo "  ssh root@$SERVER 'crontab -l'"
echo ""
echo "⚠️  IMPORTANT: Remove cron jobs from LOCAL machine!"
echo "  Run: crontab -e"
echo "  Comment out or delete lines for: auto_ingest_bod.py, auto_ingest_windfor.py, auto_ingest_indgen.py"

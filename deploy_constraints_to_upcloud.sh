#!/bin/bash
# Deploy constraint data system to UpCloud server
# Run this script from your local machine to sync files to server

SERVER="root@94.237.55.234"
REMOTE_DIR="/opt/gb-power-constraints"

echo "🚀 Deploying GB Constraint System to UpCloud Server"
echo "=================================================="
echo "Server: $SERVER"
echo "Remote directory: $REMOTE_DIR"
echo ""

# Create remote directory
echo "1️⃣ Creating remote directory..."
ssh $SERVER "mkdir -p $REMOTE_DIR/logs"

# Copy Python scripts
echo ""
echo "2️⃣ Copying constraint scripts..."
scp ingest_neso_constraints.py $SERVER:$REMOTE_DIR/
scp update_constraints_dashboard_v2.py $SERVER:$REMOTE_DIR/

# Copy credentials
echo ""
echo "3️⃣ Copying credentials..."
scp inner-cinema-credentials.json $SERVER:$REMOTE_DIR/

# Install dependencies on server
echo ""
echo "4️⃣ Installing Python dependencies on server..."
ssh $SERVER << 'ENDSSH'
cd /opt/gb-power-constraints

# Install Python packages
pip3 install --break-system-packages google-cloud-bigquery pandas pyarrow requests beautifulsoup4 gspread oauth2client db-dtypes lxml html5lib 2>&1 | grep -E "(Successfully|already satisfied)" || true

# Set environment variable
export GOOGLE_APPLICATION_CREDENTIALS="/opt/gb-power-constraints/inner-cinema-credentials.json"
echo "export GOOGLE_APPLICATION_CREDENTIALS=\"/opt/gb-power-constraints/inner-cinema-credentials.json\"" >> ~/.bashrc

echo "✅ Dependencies installed"
ENDSSH

# Create crontab entries
echo ""
echo "5️⃣ Setting up cron jobs..."
ssh $SERVER << 'ENDSSH'
# Backup existing crontab
crontab -l > /tmp/crontab_backup_$(date +%Y%m%d_%H%M%S).txt 2>/dev/null || true

# Remove old constraint entries if they exist
crontab -l 2>/dev/null | grep -v "gb-power-constraints" | grep -v "ingest_neso_constraints" | grep -v "update_constraints_dashboard" > /tmp/crontab_new.txt || true

# Add new entries
cat >> /tmp/crontab_new.txt << 'CRON'

# GB Power Constraints - NESO Data Ingestion (Every 6 hours)
0 */6 * * * cd /opt/gb-power-constraints && export GOOGLE_APPLICATION_CREDENTIALS="/opt/gb-power-constraints/inner-cinema-credentials.json" && /usr/bin/python3 ingest_neso_constraints.py >> logs/constraint_ingest.log 2>&1

# GB Power Constraints - Dashboard Update (Every 5 minutes)
*/5 * * * * cd /opt/gb-power-constraints && export GOOGLE_APPLICATION_CREDENTIALS="/opt/gb-power-constraints/inner-cinema-credentials.json" && /usr/bin/python3 update_constraints_dashboard_v2.py >> logs/constraint_dashboard.log 2>&1
CRON

# Install new crontab
crontab /tmp/crontab_new.txt

echo "✅ Cron jobs installed"
echo ""
echo "Active cron jobs:"
crontab -l | grep -A2 "GB Power Constraints" || crontab -l | tail -4
ENDSSH

# Test connection
echo ""
echo "6️⃣ Testing BigQuery connection on server..."
ssh $SERVER << 'ENDSSH'
cd /opt/gb-power-constraints
export GOOGLE_APPLICATION_CREDENTIALS="/opt/gb-power-constraints/inner-cinema-credentials.json"

python3 << 'PYEOF'
try:
    from google.cloud import bigquery
    import os
    client = bigquery.Client(project="inner-cinema-476211-u9", location="US")
    tables = list(client.list_tables("uk_constraints"))
    print(f"✅ BigQuery connection OK - Found {len(tables)} tables in uk_constraints")
except Exception as e:
    print(f"❌ Error: {e}")
PYEOF
ENDSSH

# Run initial ingestion
echo ""
echo "7️⃣ Running initial constraint data ingestion on server..."
echo "   (This may take a few minutes...)"
ssh $SERVER << 'ENDSSH'
cd /opt/gb-power-constraints
export GOOGLE_APPLICATION_CREDENTIALS="/opt/gb-power-constraints/inner-cinema-credentials.json"
/usr/bin/python3 ingest_neso_constraints.py 2>&1 | grep -E "(✅|❌|📊|Loading|COMPLETE)"
ENDSSH

echo ""
echo "=================================================="
echo "✅ DEPLOYMENT COMPLETE"
echo "=================================================="
echo ""
echo "📊 Monitoring:"
echo "   Ingestion logs: ssh $SERVER 'tail -f /opt/gb-power-constraints/logs/constraint_ingest.log'"
echo "   Dashboard logs: ssh $SERVER 'tail -f /opt/gb-power-constraints/logs/constraint_dashboard.log'"
echo ""
echo "🔧 Management:"
echo "   Check cron jobs: ssh $SERVER 'crontab -l'"
echo "   Manual ingestion: ssh $SERVER 'cd /opt/gb-power-constraints && python3 ingest_neso_constraints.py'"
echo "   Manual dashboard update: ssh $SERVER 'cd /opt/gb-power-constraints && python3 update_constraints_dashboard_v2.py'"
echo ""
echo "📋 Tables in BigQuery:"
echo "   bq ls inner-cinema-476211-u9:uk_constraints"
echo ""
echo "🔗 Dashboard:"
echo "   https://docs.google.com/spreadsheets/d/12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8/edit#gid=0&range=A110"
echo ""

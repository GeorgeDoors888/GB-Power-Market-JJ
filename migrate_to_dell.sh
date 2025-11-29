#!/bin/bash
# Migrate all processes from UpCloud to Dell (keep ChatGPT on UpCloud)

echo "🚀 MIGRATING SERVICES: UpCloud → Dell"
echo "======================================"

# 1. Copy GB-Power-Market-JJ repository to Dell
echo "📦 Step 1: Syncing repository to Dell..."
rsync -avz --exclude 'logs/' --exclude '__pycache__/' \
  /Users/georgemajor/GB-Power-Market-JJ/ \
  dell:/root/GB-Power-Market-JJ/

# 2. Copy credentials
echo "🔑 Step 2: Copying credentials..."
scp /Users/georgemajor/GB-Power-Market-JJ/inner-cinema-credentials.json \
  dell:/root/GB-Power-Market-JJ/

# 3. Stop services on UpCloud (except dashboard-api for ChatGPT webhook)
echo "⏸️  Step 3: Stopping cron jobs on UpCloud..."
ssh upcloud "crontab -l > /tmp/cron_backup.txt && crontab -r"

# 4. Set up cron on Dell
echo "⏰ Step 4: Installing cron jobs on Dell..."
ssh dell "crontab -l > /tmp/cron_backup_dell.txt 2>/dev/null || true"
ssh dell "cat > /tmp/new_cron.txt" << 'EOFCRON'
GOOGLE_APPLICATION_CREDENTIALS=/root/GB-Power-Market-JJ/inner-cinema-credentials.json
PATH=/usr/local/bin:/usr/bin:/bin

# Dashboard updates every 5 minutes (offset from 0)
0,5,10,15,20,25,30,35,40,45,50,55 * * * * cd /root/GB-Power-Market-JJ && /usr/bin/python3 realtime_dashboard_updater.py >> logs/dashboard_updater.log 2>&1

# Outages updates every 10 minutes (offset from 4)
4,14,24,34,44,54 * * * * cd /root/GB-Power-Market-JJ && /usr/bin/python3 update_outages_enhanced.py >> logs/outages_updater.log 2>&1

# Daily dashboard updates twice per hour
8,38 * * * * cd /root/GB-Power-Market-JJ && /usr/bin/python3 daily_dashboard_auto_updater.py >> logs/daily_dashboard.log 2>&1

# Comprehensive dashboard updates (offset from 7)
7,22,37,52 * * * * cd /root/GB-Power-Market-JJ && /usr/bin/python3 update_comprehensive_dashboard.py >> logs/comprehensive_updater.log 2>&1

# Dashboard pipeline every 5 minutes
*/5 * * * * cd /root/GB-Power-Market-JJ && python3 dashboard_pipeline.py >> logs/dashboard_pipeline.log 2>&1

# Chart data updates every 5 minutes
*/5 * * * * cd /root/GB-Power-Market-JJ && ./update_all_charts.sh >> logs/chart_updates.log 2>&1
EOFCRON

ssh dell "crontab /tmp/new_cron.txt"

# 5. Keep only dashboard-api on UpCloud
echo "📌 Step 5: Keeping ChatGPT webhook on UpCloud..."
ssh upcloud "cat > /tmp/upcloud_cron.txt" << 'EOFUPCRON'
# Only dashboard-api.service (systemd) handles ChatGPT webhooks
# All data processing moved to Dell server
EOFUPCRON
ssh upcloud "crontab /tmp/upcloud_cron.txt"

# 6. Create logs directory on Dell
echo "📁 Step 6: Setting up logs directory..."
ssh dell "mkdir -p /root/GB-Power-Market-JJ/logs"

# 7. Test connection
echo "🧪 Step 7: Testing Dell setup..."
ssh dell "cd /root/GB-Power-Market-JJ && python3 --version && ls -la *.py | head -5"

echo ""
echo "✅ MIGRATION COMPLETE!"
echo ""
echo "📊 Services on Dell:"
echo "   • Dashboard updates (every 5 min)"
echo "   • Outages updates (every 10 min)"
echo "   • Comprehensive dashboard (every 15 min)"
echo "   • Chart data pipeline (every 5 min)"
echo ""
echo "📌 Services on UpCloud:"
echo "   • dashboard-api.service (ChatGPT webhook only)"
echo ""
echo "🔍 Check Dell cron: ssh dell 'crontab -l'"
echo "📊 Monitor logs: ssh dell 'tail -f /root/GB-Power-Market-JJ/logs/*.log'"

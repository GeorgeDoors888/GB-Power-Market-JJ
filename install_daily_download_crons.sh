#!/bin/bash
#
# Install Daily Download Cron Jobs for P114 and NESO Data
# Run once to set up automated daily ingestion
#
# Usage: chmod +x install_daily_download_crons.sh && ./install_daily_download_crons.sh
#

set -e

PROJECT_DIR="/home/george/GB-Power-Market-JJ"
LOG_DIR="$PROJECT_DIR/logs"

echo "=============================================="
echo "📦 Installing Daily Download Cron Jobs"
echo "=============================================="

# Create log directory
mkdir -p "$LOG_DIR"

# Make scripts executable
chmod +x "$PROJECT_DIR/auto_download_p114_daily.py"
chmod +x "$PROJECT_DIR/auto_download_neso_daily.py"

echo ""
echo "✅ Scripts are executable"

# Backup existing crontab
BACKUP_FILE="$PROJECT_DIR/crontab_backup_$(date +%Y%m%d_%H%M%S).txt"
crontab -l > "$BACKUP_FILE" 2>/dev/null || echo "# New crontab" > "$BACKUP_FILE"
echo "✅ Backed up existing crontab to: $BACKUP_FILE"

# Create new crontab entries
TEMP_CRON=$(mktemp)
crontab -l 2>/dev/null > "$TEMP_CRON" || true

echo ""
echo "📝 Adding new cron jobs..."

# Remove any existing entries for these scripts (avoid duplicates)
sed -i '/auto_download_p114_daily.py/d' "$TEMP_CRON"
sed -i '/auto_download_neso_daily.py/d' "$TEMP_CRON"

# Add new entries
cat >> "$TEMP_CRON" << EOF

# ============================================
# GB Power Market - Daily Data Downloads
# Installed: $(date +"%Y-%m-%d %H:%M:%S")
# ============================================

# P114 Settlement Data - Daily at 2am (after Elexon publishes)
0 2 * * * $PROJECT_DIR/auto_download_p114_daily.py >> $LOG_DIR/p114_daily.log 2>&1

# NESO Constraint Costs & Publications - Daily at 3am
0 3 * * * $PROJECT_DIR/auto_download_neso_daily.py >> $LOG_DIR/neso_daily.log 2>&1

EOF

# Install new crontab
crontab "$TEMP_CRON"
rm "$TEMP_CRON"

echo "✅ Cron jobs installed successfully"
echo ""
echo "=============================================="
echo "📋 INSTALLED CRON JOBS"
echo "=============================================="
echo ""
crontab -l | grep -A 10 "GB Power Market"
echo ""
echo "=============================================="
echo "📊 SCHEDULE"
echo "=============================================="
echo "P114 Data:       Daily at 2:00 AM"
echo "NESO Data:       Daily at 3:00 AM"
echo ""
echo "=============================================="
echo "📁 LOG FILES"
echo "=============================================="
echo "P114:            $LOG_DIR/p114_daily.log"
echo "NESO:            $LOG_DIR/neso_daily.log"
echo ""
echo "=============================================="
echo "🧪 TEST COMMANDS"
echo "=============================================="
echo ""
echo "# Test P114 download manually:"
echo "python3 $PROJECT_DIR/auto_download_p114_daily.py"
echo ""
echo "# Test NESO download manually:"
echo "python3 $PROJECT_DIR/auto_download_neso_daily.py"
echo ""
echo "# View cron logs:"
echo "tail -f $LOG_DIR/p114_daily.log"
echo "tail -f $LOG_DIR/neso_daily.log"
echo ""
echo "# Check cron status:"
echo "crontab -l | grep 'auto_download'"
echo ""
echo "=============================================="
echo "✅ INSTALLATION COMPLETE"
echo "=============================================="
echo ""
echo "Next steps:"
echo "1. Test scripts manually (see commands above)"
echo "2. Wait for scheduled runs (2am/3am daily)"
echo "3. Monitor logs to verify success"
echo ""

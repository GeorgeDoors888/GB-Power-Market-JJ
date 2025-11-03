#!/bin/bash
# Setup cron jobs for both GB Power Map AND Property Companies Extraction
# Run on AlmaLinux server

set -e

echo "=== Setting Up Dual Cron Jobs on AlmaLinux ==="

# Backup existing crontab
crontab -l > /tmp/crontab_backup_$(date +%Y%m%d_%H%M%S).txt 2>/dev/null || true

# Remove any existing related cron jobs
crontab -l 2>/dev/null | grep -v "auto_generate_map\|property_companies" > /tmp/new_crontab || true

# Add both cron jobs
cat >> /tmp/new_crontab << 'EOF'

# GB Power Map Auto-Generation (every 30 minutes)
*/30 * * * * /usr/bin/python3 /var/www/maps/scripts/auto_generate_map_linux.py >> /var/www/maps/logs/cron.log 2>&1

# Property Companies Extraction (daily at 2 AM)
0 2 * * * /bin/bash /var/www/property_companies/scripts/extract_property_companies.sh >> /var/www/property_companies/logs/daily_cron.log 2>&1

EOF

# Install new crontab
crontab /tmp/new_crontab
rm /tmp/new_crontab

echo ""
echo "=== Cron Jobs Installed ==="
echo ""
echo "Current crontab:"
crontab -l | grep -v "^$" | grep -v "^#" || echo "No active cron jobs"

echo ""
echo "=== Schedule ==="
echo "Power Map: Every 30 minutes (00, 30 past each hour)"
echo "Property Companies: Daily at 2:00 AM"
echo ""
echo "Monitor logs:"
echo "  Power Map: tail -f /var/www/maps/logs/map_generation_\$(date +%Y%m%d).log"
echo "  Companies: tail -f /var/www/property_companies/logs/extraction_\$(date +%Y%m%d).log"

#!/bin/bash
# Quick deployment commands for AlmaLinux server
# Copy and paste these into your SSH session

cat << 'EOF'

╔════════════════════════════════════════════════════════════╗
║  AlmaLinux Server - GB Power Map Deployment               ║
║  Server: 94.237.55.234                                     ║
╚════════════════════════════════════════════════════════════╝

Step 1: SSH to server
──────────────────────
ssh root@94.237.55.234


Step 2: Extract and deploy
───────────────────────────
cd /root
unzip -o gb_power_map_deployment.zip
cd gb_power_map_deployment


Step 3: Configure Google Cloud credentials
───────────────────────────────────────────
export GOOGLE_APPLICATION_CREDENTIALS=/root/credentials.json
echo 'export GOOGLE_APPLICATION_CREDENTIALS=/root/credentials.json' >> ~/.bashrc
source ~/.bashrc


Step 4: Deploy (keeps IRIS running)
────────────────────────────────────
sudo ./deploy_power_map_only.sh


Step 5: Test map generation
────────────────────────────
python3 /var/www/maps/scripts/auto_generate_map_linux.py
ls -lh /var/www/maps/gb_power_complete_map.html


Step 6: Check it works
───────────────────────
curl -I http://localhost/gb_power_complete_map.html


╔════════════════════════════════════════════════════════════╗
║  SUCCESS!                                                  ║
║  Your map is now live at:                                  ║
║  http://94.237.55.234/gb_power_complete_map.html          ║
║                                                            ║
║  Auto-updates: Every 30 minutes                           ║
║  IRIS: Continues running (not touched)                    ║
╚════════════════════════════════════════════════════════════╝

Add to Google Sheets:
─────────────────────
=HYPERLINK("http://94.237.55.234/gb_power_complete_map.html", "🗺️ Live Power Map")

Your Sheet:
https://docs.google.com/spreadsheets/d/12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8/edit


Monitor:
────────
tail -f /var/www/maps/logs/map_generation_$(date +%Y%m%d).log

EOF

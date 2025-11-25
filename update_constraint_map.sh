#!/bin/bash
# Auto-update constraint map HTML every 5 minutes
# Install: Add to crontab with: crontab -e
# */5 * * * * /Users/georgemajor/GB\ Power\ Market\ JJ/update_constraint_map.sh

cd "/Users/georgemajor/GB Power Market JJ"

# Generate fresh HTML with latest data
python3 generate_constraint_map_html.py >> logs/constraint_map_updates.log 2>&1

# Optional: Upload to web server
# scp constraint_map_standalone.html root@94.237.55.234:/var/www/html/constraint_map.html

echo "$(date): Constraint map updated" >> logs/constraint_map_updates.log

#!/bin/bash
# One-command deployment script for AlmaLinux server

set -e

echo "=== GB Power Map Deployment ==="
echo "Server: almalinux-1cpu-2gb-uk-lon1"
echo "IP: 94.237.55.234"
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
   echo "Please run as root or with sudo"
   exit 1
fi

# Install prerequisites
echo "Installing prerequisites..."
dnf update -y
dnf install -y python3 python3-pip nginx gcc python3-devel

# Install Python packages
echo "Installing Python packages..."
pip3 install -r requirements.txt

# Setup Nginx
echo "Setting up Nginx..."
./setup_nginx_web_server.sh

# Copy files
echo "Copying files..."
cp auto_generate_map_linux.py /var/www/maps/scripts/
cp dno_regions.geojson /var/www/maps/data/
chmod +x /var/www/maps/scripts/auto_generate_map_linux.py
chown -R nginx:nginx /var/www/maps

# Setup cron
echo "Setting up cron job..."
./setup_cron_job.sh

echo ""
echo "=== Deployment Complete ==="
echo "Map URL: http://94.237.55.234/gb_power_complete_map.html"
echo ""
echo "Next: Configure Google Cloud credentials"
echo "  export GOOGLE_APPLICATION_CREDENTIALS=/path/to/credentials.json"

#!/bin/bash
# Streamlined deployment for AlmaLinux server
# GB Power Map + IRIS pipeline (keeps IRIS running)

set -e

echo "========================================"
echo "AlmaLinux Server Deployment"
echo "Server: 94.237.55.234"
echo "Projects: GB Power Map + IRIS Pipeline"
echo "========================================"
echo ""

# 1. Install system packages
echo "Step 1: Installing system packages..."
dnf update -y
dnf install -y python3 python3-pip nginx gcc python3-devel

# 2. Install Python packages
echo ""
echo "Step 2: Installing Python packages..."
pip3 install google-cloud-bigquery

# 3. Setup GB Power Map
echo ""
echo "Step 3: Setting up GB Power Map..."
mkdir -p /var/www/maps/{data,logs,scripts}

# Copy files if in deployment directory
if [ -f "auto_generate_map_linux.py" ]; then
    cp auto_generate_map_linux.py /var/www/maps/scripts/
    chmod +x /var/www/maps/scripts/auto_generate_map_linux.py
    echo "✓ Map generator installed"
fi

if [ -f "dno_regions.geojson" ]; then
    cp dno_regions.geojson /var/www/maps/data/
    echo "✓ DNO regions installed"
fi

# 4. Setup Nginx
echo ""
echo "Step 4: Setting up Nginx..."

cat > /etc/nginx/conf.d/gb_power_map.conf << 'EOF'
server {
    listen 80;
    server_name _;
    
    root /var/www/maps;
    index gb_power_complete_map.html;
    
    # GB Power Map
    location / {
        try_files $uri $uri/ =404;
    }
    
    # Enable gzip compression
    gzip on;
    gzip_types text/html text/css application/json application/javascript text/xml application/xml;
    gzip_min_length 1000;
    
    # Cache static files
    location ~* \.(html|json|geojson)$ {
        expires 5m;
        add_header Cache-Control "public, must-revalidate";
    }
    
    # Logs
    access_log /var/www/maps/logs/nginx_access.log;
    error_log /var/www/maps/logs/nginx_error.log;
}
EOF

# Test and reload Nginx
nginx -t
systemctl start nginx
systemctl enable nginx
systemctl reload nginx

echo "✓ Nginx configured"

# 5. Set permissions
echo ""
echo "Step 5: Setting permissions..."
chown -R nginx:nginx /var/www/maps
chmod -R 755 /var/www/maps
chmod +x /var/www/maps/scripts/auto_generate_map_linux.py

# 6. Configure firewall
echo ""
echo "Step 6: Configuring firewall..."
if command -v firewall-cmd &> /dev/null; then
    firewall-cmd --permanent --add-service=http
    firewall-cmd --reload
    echo "✓ Firewall configured"
fi

# 7. Setup cron job (only for Power Map)
echo ""
echo "Step 7: Setting up cron job for Power Map..."

# Backup existing crontab
crontab -l > /tmp/crontab_backup_$(date +%Y%m%d_%H%M%S).txt 2>/dev/null || true

# Remove any existing map generation cron jobs
crontab -l 2>/dev/null | grep -v "auto_generate_map" > /tmp/new_crontab || true

# Add power map cron job
cat >> /tmp/new_crontab << 'EOF'

# GB Power Map Auto-Generation (every 30 minutes)
*/30 * * * * /usr/bin/python3 /var/www/maps/scripts/auto_generate_map_linux.py >> /var/www/maps/logs/cron.log 2>&1

EOF

# Install new crontab
crontab /tmp/new_crontab
rm /tmp/new_crontab

echo "✓ Cron job installed"

echo ""
echo "========================================"
echo "Setup Complete!"
echo "========================================"
echo ""
echo "Running Projects:"
echo "  1. GB Power Map: http://94.237.55.234/gb_power_complete_map.html"
echo "     Auto-updates: Every 30 minutes"
echo ""
echo "  2. IRIS Pipeline: Already running (not touched)"
echo "     Updates: JSON data every 5 minutes"
echo ""
echo "Test map generation:"
echo "  python3 /var/www/maps/scripts/auto_generate_map_linux.py"
echo ""
echo "Monitor:"
echo "  tail -f /var/www/maps/logs/map_generation_\$(date +%Y%m%d).log"
echo ""
echo "View cron jobs:"
echo "  crontab -l"

#!/bin/bash
# Complete setup for AlmaLinux server
# Includes: GB Power Map + Property Companies Extraction

set -e

echo "========================================"
echo "AlmaLinux Complete Setup"
echo "Server: 94.237.55.234"
echo "========================================"
echo ""

# 1. Install system packages
echo "Step 1: Installing system packages..."
dnf update -y
dnf install -y python3 python3-pip nginx gcc python3-devel bc

# 2. Install Google Cloud SDK (for bq command)
echo ""
echo "Step 2: Installing Google Cloud SDK..."
if ! command -v bq &> /dev/null; then
    curl https://sdk.cloud.google.com | bash
    exec -l $SHELL
    source ~/.bashrc
else
    echo "✓ Google Cloud SDK already installed"
fi

# 3. Install Python packages
echo ""
echo "Step 3: Installing Python packages..."
pip3 install google-cloud-bigquery

# 4. Setup GB Power Map
echo ""
echo "Step 4: Setting up GB Power Map..."
mkdir -p /var/www/maps/{data,logs,scripts}

if [ -f "/tmp/gb_power_map_deployment/auto_generate_map_linux.py" ]; then
    cp /tmp/gb_power_map_deployment/auto_generate_map_linux.py /var/www/maps/scripts/
    chmod +x /var/www/maps/scripts/auto_generate_map_linux.py
    echo "✓ Map generator installed"
fi

if [ -f "/tmp/gb_power_map_deployment/dno_regions.geojson" ]; then
    cp /tmp/gb_power_map_deployment/dno_regions.geojson /var/www/maps/data/
    echo "✓ DNO regions installed"
fi

# 5. Setup Property Companies Extraction
echo ""
echo "Step 5: Setting up Property Companies Extraction..."
mkdir -p /var/www/property_companies/{data,logs,scripts}

if [ -f "extract_property_companies.sh" ]; then
    cp extract_property_companies.sh /var/www/property_companies/scripts/
    chmod +x /var/www/property_companies/scripts/extract_property_companies.sh
    echo "✓ Property extractor installed"
fi

# 6. Setup Nginx
echo ""
echo "Step 6: Setting up Nginx..."

# Configure Nginx for both projects
cat > /etc/nginx/conf.d/projects.conf << 'EOF'
server {
    listen 80;
    server_name _;
    
    root /var/www;
    
    # GB Power Map
    location /gb_power_complete_map.html {
        alias /var/www/maps/gb_power_complete_map.html;
        expires 5m;
        add_header Cache-Control "public, must-revalidate";
    }
    
    # Property Companies CSV
    location /property_companies.csv {
        alias /var/www/property_companies/data/property_owning_companies_clean.csv;
        add_header Content-Type text/csv;
        add_header Content-Disposition 'attachment; filename="property_companies.csv"';
    }
    
    # Default location
    location / {
        try_files $uri $uri/ =404;
    }
    
    # Enable gzip
    gzip on;
    gzip_types text/html text/css application/json text/csv;
    
    access_log /var/log/nginx/access.log;
    error_log /var/log/nginx/error.log;
}
EOF

# Test and reload Nginx
nginx -t
systemctl start nginx
systemctl enable nginx
systemctl reload nginx

echo "✓ Nginx configured"

# 7. Set permissions
echo ""
echo "Step 7: Setting permissions..."
chown -R nginx:nginx /var/www/maps
chown -R nginx:nginx /var/www/property_companies
chmod -R 755 /var/www/maps
chmod -R 755 /var/www/property_companies

# 8. Configure firewall
echo ""
echo "Step 8: Configuring firewall..."
if command -v firewall-cmd &> /dev/null; then
    firewall-cmd --permanent --add-service=http
    firewall-cmd --reload
    echo "✓ Firewall configured"
fi

# 9. Setup cron jobs
echo ""
echo "Step 9: Setting up cron jobs..."
./setup_dual_cron_jobs.sh

echo ""
echo "========================================"
echo "Setup Complete!"
echo "========================================"
echo ""
echo "URLs:"
echo "  Power Map: http://94.237.55.234/gb_power_complete_map.html"
echo "  Companies CSV: http://94.237.55.234/property_companies.csv"
echo ""
echo "Test manually:"
echo "  python3 /var/www/maps/scripts/auto_generate_map_linux.py"
echo "  bash /var/www/property_companies/scripts/extract_property_companies.sh"
echo ""
echo "Monitor:"
echo "  tail -f /var/www/maps/logs/map_generation_\$(date +%Y%m%d).log"
echo "  tail -f /var/www/property_companies/logs/extraction_\$(date +%Y%m%d).log"

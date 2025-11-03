#!/bin/bash
# Setup Script for Nginx Web Server on AlmaLinux UpCloud Server
# Hosts the GB Power Map with automated updates

set -e  # Exit on error

echo "=== Setting Up Nginx Web Server for GB Power Map ==="

# Server details
SERVER_IP="94.237.55.234"
SERVER_NAME="almalinux-1cpu-2gb-uk-lon1"

# Install Nginx if not already installed
echo ""
echo "Step 1: Installing Nginx..."
if ! command -v nginx &> /dev/null; then
    sudo dnf install -y nginx
    echo "✓ Nginx installed"
else
    echo "✓ Nginx already installed"
fi

# Start and enable Nginx
echo ""
echo "Step 2: Starting Nginx..."
sudo systemctl start nginx
sudo systemctl enable nginx
echo "✓ Nginx started and enabled"

# Create directory structure
echo ""
echo "Step 3: Creating directory structure..."
sudo mkdir -p /var/www/maps/data
sudo mkdir -p /var/www/maps/logs
sudo mkdir -p /var/www/maps/scripts

# Set permissions
sudo chown -R nginx:nginx /var/www/maps
sudo chmod -R 755 /var/www/maps

echo "✓ Directories created:"
echo "  - /var/www/maps/data     (for dno_regions.geojson)"
echo "  - /var/www/maps/logs     (for generation logs)"
echo "  - /var/www/maps/scripts  (for Python scripts)"

# Configure Nginx for the map
echo ""
echo "Step 4: Configuring Nginx..."

sudo tee /etc/nginx/conf.d/gb_power_map.conf > /dev/null << 'EOF'
server {
    listen 80;
    server_name _;
    
    root /var/www/maps;
    index gb_power_complete_map.html;
    
    # Enable gzip compression
    gzip on;
    gzip_types text/html text/css application/json application/javascript text/xml application/xml;
    gzip_min_length 1000;
    
    location / {
        try_files $uri $uri/ =404;
    }
    
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

echo "✓ Nginx configuration created"

# Test Nginx configuration
echo ""
echo "Step 5: Testing Nginx configuration..."
sudo nginx -t
echo "✓ Nginx configuration valid"

# Reload Nginx
sudo systemctl reload nginx
echo "✓ Nginx reloaded"

# Configure firewall
echo ""
echo "Step 6: Configuring firewall..."
if command -v firewall-cmd &> /dev/null; then
    sudo firewall-cmd --permanent --add-service=http
    sudo firewall-cmd --reload
    echo "✓ Firewall configured (HTTP port 80 open)"
else
    echo "⚠ firewalld not found - ensure port 80 is open in UpCloud firewall"
fi

# Create test page
echo ""
echo "Step 7: Creating test page..."
sudo tee /var/www/maps/index.html > /dev/null << 'EOF'
<!DOCTYPE html>
<html>
<head>
    <title>GB Power Map Server</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 800px;
            margin: 50px auto;
            padding: 20px;
        }
        h1 { color: #333; }
        .status { color: green; font-weight: bold; }
        .info { background: #f0f0f0; padding: 15px; border-radius: 5px; margin: 20px 0; }
    </style>
</head>
<body>
    <h1>GB Power Map Server</h1>
    <p class="status">✓ Server is running</p>
    <div class="info">
        <strong>Map URL:</strong><br>
        <a href="/gb_power_complete_map.html">/gb_power_complete_map.html</a>
    </div>
    <p><em>Map will be available once auto_generate_map.py runs</em></p>
</body>
</html>
EOF

sudo chown nginx:nginx /var/www/maps/index.html
echo "✓ Test page created"

# Display server information
echo ""
echo "=== Server Information ==="
echo "Web Root: /var/www/maps"
echo "Config: /etc/nginx/conf.d/gb_power_map.conf"
echo "Local URL: http://localhost/gb_power_complete_map.html"
echo "Public URL: http://$SERVER_IP/gb_power_complete_map.html"
echo ""
echo "Test URLs:"
echo "  http://$SERVER_IP/          (test page)"
echo "  http://$SERVER_IP/gb_power_complete_map.html  (map, once generated)"

# Test local access
echo ""
echo "Step 8: Testing web server..."
if curl -s http://localhost/ | grep -q "GB Power Map Server"; then
    echo "✓ Web server test successful!"
else
    echo "⚠ Warning: Could not verify web server"
fi

echo ""
echo "=== Nginx Setup Complete ==="
echo ""
echo "Next Steps:"
echo "1. Copy auto_generate_map.py to /var/www/maps/scripts/"
echo "2. Copy dno_regions.geojson to /var/www/maps/data/"
echo "3. Install Python packages: sudo pip3 install google-cloud-bigquery"
echo "4. Configure BigQuery credentials"
echo "5. Test: python3 /var/www/maps/scripts/auto_generate_map.py"
echo "6. Set up cron job (see setup_cron_job.sh)"
echo ""
echo "Current status:"
systemctl status nginx --no-pager -l

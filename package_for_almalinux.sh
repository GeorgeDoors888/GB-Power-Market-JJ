#!/bin/bash
# Package GB Power Map files for AlmaLinux deployment
# Creates a deployment package to upload to UpCloud server

set -e

echo "=== Creating AlmaLinux Deployment Package ==="

# Create deployment directory
DEPLOY_DIR="gb_power_map_deployment"
rm -rf "$DEPLOY_DIR"
mkdir -p "$DEPLOY_DIR"

echo ""
echo "Step 1: Copying files..."

# Copy main files
cp auto_generate_map_linux.py "$DEPLOY_DIR/"
cp dno_regions.geojson "$DEPLOY_DIR/"
cp setup_nginx_web_server.sh "$DEPLOY_DIR/"
cp setup_cron_job.sh "$DEPLOY_DIR/"
cp ALMALINUX_DEPLOYMENT_GUIDE.md "$DEPLOY_DIR/README.md"

# Make scripts executable
chmod +x "$DEPLOY_DIR/setup_nginx_web_server.sh"
chmod +x "$DEPLOY_DIR/setup_cron_job.sh"
chmod +x "$DEPLOY_DIR/auto_generate_map_linux.py"

echo "✓ Files copied"

# Create requirements.txt
echo ""
echo "Step 2: Creating requirements.txt..."
cat > "$DEPLOY_DIR/requirements.txt" << 'EOF'
google-cloud-bigquery>=3.11.0
EOF

echo "✓ requirements.txt created"

# Create deployment instructions
echo ""
echo "Step 3: Creating quick start guide..."
cat > "$DEPLOY_DIR/QUICK_START.txt" << 'EOF'
GB Power Map - AlmaLinux Quick Start
=====================================

Server: almalinux-1cpu-2gb-uk-lon1
IP: 94.237.55.234

Quick Deployment:
-----------------

1. Upload this package to server:
   scp -r gb_power_map_deployment root@94.237.55.234:/root/

2. SSH into server:
   ssh root@94.237.55.234

3. Run deployment:
   cd /root/gb_power_map_deployment
   sudo ./setup_nginx_web_server.sh
   sudo ./setup_cron_job.sh

4. Access map:
   http://94.237.55.234/gb_power_complete_map.html

See README.md for full documentation.
EOF

echo "✓ QUICK_START.txt created"

# Create a deployment script
echo ""
echo "Step 4: Creating deployment script..."
cat > "$DEPLOY_DIR/deploy.sh" << 'EOF'
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
EOF

chmod +x "$DEPLOY_DIR/deploy.sh"
echo "✓ deploy.sh created"

# Create ZIP archive
echo ""
echo "Step 5: Creating ZIP archive..."
zip -r gb_power_map_deployment.zip "$DEPLOY_DIR"
echo "✓ ZIP archive created"

# Display package contents
echo ""
echo "=== Package Contents ==="
find "$DEPLOY_DIR" -type f -exec ls -lh {} \; | awk '{print $9, "(" $5 ")"}'

# Get total size
TOTAL_SIZE=$(du -sh "$DEPLOY_DIR" | cut -f1)
ZIP_SIZE=$(ls -lh gb_power_map_deployment.zip | awk '{print $5}')

echo ""
echo "=== Package Created ==="
echo "Directory: $DEPLOY_DIR ($TOTAL_SIZE)"
echo "ZIP file: gb_power_map_deployment.zip ($ZIP_SIZE)"

echo ""
echo "=== Next Steps ==="
echo ""
echo "1. Upload package to server:"
echo "   scp gb_power_map_deployment.zip root@94.237.55.234:/root/"
echo ""
echo "2. SSH into server:"
echo "   ssh root@94.237.55.234"
echo ""
echo "3. Extract and deploy:"
echo "   unzip gb_power_map_deployment.zip"
echo "   cd gb_power_map_deployment"
echo "   sudo ./deploy.sh"
echo ""
echo "4. Configure BigQuery credentials:"
echo "   scp credentials.json root@94.237.55.234:/root/"
echo "   ssh root@94.237.55.234"
echo "   export GOOGLE_APPLICATION_CREDENTIALS=/root/credentials.json"
echo "   echo 'export GOOGLE_APPLICATION_CREDENTIALS=/root/credentials.json' >> ~/.bashrc"
echo ""
echo "5. Test the map:"
echo "   http://94.237.55.234/gb_power_complete_map.html"
echo ""
echo "See $DEPLOY_DIR/README.md for full documentation"

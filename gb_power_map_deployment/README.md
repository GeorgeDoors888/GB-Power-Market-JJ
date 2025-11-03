# 🚀 UpCloud AlmaLinux Server - GB Power Map Automation

## Server Details

**Server Name**: almalinux-1cpu-2gb-uk-lon1  
**IP Address**: 94.237.55.234  
**OS**: AlmaLinux 10  
**UUID**: 00f1dd6f-f773-493f-a89d-e287e52bfe61  
**Location**: London (UK)

---

## 🎯 Deployment Objective

Set up **automated live GB Power Map** that:
1. ✅ Hosts interactive map via Nginx web server
2. ✅ Auto-regenerates every 30 minutes with latest BigQuery data
3. ✅ Shows GSP flows, DNO boundaries, offshore wind, all generators
4. ✅ Runs 24/7 via cron job
5. ✅ Accessible via public URL

---

## 📦 Deployment Package

### Files Included

```
GB Power Map JJ/
├── auto_generate_map_linux.py       # Map generator for Linux
├── setup_nginx_web_server.sh        # Nginx installation & config
├── setup_cron_job.sh                # Automated cron scheduling
├── dno_regions.geojson              # DNO boundary data
└── ALMALINUX_DEPLOYMENT_GUIDE.md    # This file
```

---

## 🔧 Installation Steps

### Step 1: Connect to Server

```bash
# SSH connection
ssh root@94.237.55.234

# Or use UpCloud console
```

### Step 2: Install Prerequisites

```bash
# Update system
sudo dnf update -y

# Install Python 3 and pip
sudo dnf install -y python3 python3-pip

# Install Nginx
sudo dnf install -y nginx

# Install development tools
sudo dnf install -y gcc python3-devel

# Verify installations
python3 --version
pip3 --version
nginx -v
```

### Step 3: Install Python Dependencies

```bash
# Install BigQuery client
sudo pip3 install google-cloud-bigquery

# Verify installation
python3 -c "from google.cloud import bigquery; print('BigQuery OK')"
```

### Step 4: Configure Google Cloud Credentials

```bash
# Option A: Copy service account key
# Copy your credentials.json to server:
scp credentials.json root@94.237.55.234:/root/

# Set environment variable
export GOOGLE_APPLICATION_CREDENTIALS="/root/credentials.json"
echo 'export GOOGLE_APPLICATION_CREDENTIALS="/root/credentials.json"' >> ~/.bashrc

# Option B: Use gcloud auth
# Install gcloud SDK and authenticate
curl https://sdk.cloud.google.com | bash
exec -l $SHELL
gcloud init
gcloud auth application-default login
```

### Step 5: Upload Files to Server

```bash
# From your Mac, upload the deployment files
cd "/Users/georgemajor/GB Power Market JJ"

# Upload Python script
scp auto_generate_map_linux.py root@94.237.55.234:/tmp/

# Upload GeoJSON data
scp dno_regions.geojson root@94.237.55.234:/tmp/

# Upload setup scripts
scp setup_nginx_web_server.sh root@94.237.55.234:/tmp/
scp setup_cron_job.sh root@94.237.55.234:/tmp/
```

### Step 6: Run Setup Scripts on Server

```bash
# SSH into server
ssh root@94.237.55.234

# Make scripts executable
chmod +x /tmp/setup_nginx_web_server.sh
chmod +x /tmp/setup_cron_job.sh

# Run Nginx setup
cd /tmp
sudo ./setup_nginx_web_server.sh

# Move files to correct locations
sudo cp auto_generate_map_linux.py /var/www/maps/scripts/
sudo cp dno_regions.geojson /var/www/maps/data/

# Set permissions
sudo chown -R nginx:nginx /var/www/maps
sudo chmod +x /var/www/maps/scripts/auto_generate_map_linux.py

# Test manual generation
sudo python3 /var/www/maps/scripts/auto_generate_map_linux.py

# Setup automated cron job
sudo ./setup_cron_job.sh
```

### Step 7: Configure UpCloud Firewall

```bash
# Via UpCloud Web Console:
# 1. Go to Server > Firewall
# 2. Add rule: Allow TCP port 80 (HTTP)
# 3. Source: 0.0.0.0/0 (anywhere)

# Or via AlmaLinux firewall:
sudo firewall-cmd --permanent --add-service=http
sudo firewall-cmd --reload
sudo firewall-cmd --list-all
```

---

## 🌐 Access URLs

### After Deployment

**Test Page**: http://94.237.55.234/  
**Live Map**: http://94.237.55.234/gb_power_complete_map.html

---

## 📊 Data Sources

The map automatically queries these BigQuery tables:

1. **GSP Flows**
   - `bmrs_indgen` - Generation data
   - `bmrs_inddem` - Demand data
   - Latest settlement period automatically selected

2. **Offshore Wind Farms**
   - `offshore_wind_farms` - 35 operational sites

3. **All Generators**
   - `sva_generators_with_coords` - 7,072 small generators
   - `cva_plants` - 1,581 large power plants

4. **DNO Boundaries**
   - Local file: `dno_regions.geojson` - 14 DNO regions

---

## ⚙️ Automation Details

### Cron Schedule

```bash
# Map regenerates every 30 minutes
*/30 * * * * python3 /var/www/maps/scripts/auto_generate_map_linux.py >> /var/www/maps/logs/cron.log 2>&1
```

### Run Times
- **00, 30** minutes past each hour
- Example: 00:00, 00:30, 01:00, 01:30, etc.

---

## 🔍 Monitoring & Troubleshooting

### Check Map Status

```bash
# View map file
ls -lh /var/www/maps/gb_power_complete_map.html

# Check generation logs
tail -f /var/www/maps/logs/map_generation_$(date +%Y%m%d).log

# Check cron execution
tail -f /var/www/maps/logs/cron.log

# Check Nginx logs
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

### Manual Test

```bash
# Generate map manually
cd /var/www/maps/scripts
python3 auto_generate_map_linux.py

# Check if it worked
curl -I http://localhost/gb_power_complete_map.html
```

### Verify Cron Job

```bash
# List cron jobs
crontab -l

# Check cron service
systemctl status crond

# View cron execution history
sudo grep CRON /var/log/cron
```

### Nginx Commands

```bash
# Check Nginx status
systemctl status nginx

# Restart Nginx
sudo systemctl restart nginx

# Test Nginx configuration
sudo nginx -t

# View Nginx config
cat /etc/nginx/conf.d/gb_power_map.conf
```

---

## 📝 File Locations

```
/var/www/maps/
├── gb_power_complete_map.html       # Generated map (auto-updated)
├── index.html                       # Test page
├── data/
│   └── dno_regions.geojson          # DNO boundaries
├── scripts/
│   └── auto_generate_map_linux.py   # Generator script
└── logs/
    ├── map_generation_YYYYMMDD.log  # Daily generation logs
    ├── cron.log                     # Cron execution log
    ├── nginx_access.log             # HTTP access log
    └── nginx_error.log              # HTTP error log
```

---

## 🔐 Security Considerations

### BigQuery Credentials

```bash
# Service account key should have restricted permissions:
# - BigQuery Data Viewer
# - BigQuery Job User

# Secure the credentials file
chmod 600 /root/credentials.json
```

### Nginx Security

```bash
# Consider adding SSL/HTTPS
sudo dnf install certbot python3-certbot-nginx
sudo certbot --nginx -d yourdomain.com
```

### Firewall

```bash
# Only allow HTTP/HTTPS and SSH
sudo firewall-cmd --permanent --add-service=http
sudo firewall-cmd --permanent --add-service=https
sudo firewall-cmd --permanent --add-service=ssh
sudo firewall-cmd --reload
```

---

## 🔄 Integration with Google Sheets

### Option 1: Direct Hyperlink

Add this formula to your Google Sheets dashboard:

```
=HYPERLINK("http://94.237.55.234/gb_power_complete_map.html", "View Live Power Map")
```

### Option 2: Embedded iframe (Apps Script)

```javascript
function addMapToSheet() {
  var sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName('Dashboard');
  var html = '<iframe src="http://94.237.55.234/gb_power_complete_map.html" width="100%" height="600px"></iframe>';
  
  // Add as note or use custom function
  sheet.getRange('A1').setNote('Live Map: http://94.237.55.234/gb_power_complete_map.html');
}
```

### Option 3: Automatic Update Script

Create a script that updates the Google Sheet with the map URL:

```python
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# Authenticate
scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
creds = ServiceAccountCredentials.from_json_keyfile_name('credentials.json', scope)
client = gspread.authorize(creds)

# Open sheet and add link
sheet = client.open('GB Power Market Dashboard').sheet1
sheet.update_acell('A1', '=HYPERLINK("http://94.237.55.234/gb_power_complete_map.html", "Live Power Map")')
```

---

## ✅ Verification Checklist

After deployment, verify:

- [ ] Nginx is running: `systemctl status nginx`
- [ ] Map file exists: `ls -lh /var/www/maps/gb_power_complete_map.html`
- [ ] Map is accessible: `curl -I http://94.237.55.234/gb_power_complete_map.html`
- [ ] Public URL works: Open http://94.237.55.234/gb_power_complete_map.html in browser
- [ ] Cron job is scheduled: `crontab -l | grep map`
- [ ] Logs are being created: `ls -lh /var/www/maps/logs/`
- [ ] BigQuery credentials work: Test with `python3 -c "from google.cloud import bigquery; c=bigquery.Client(project='inner-cinema-476211-u9'); print('OK')"`

---

## 🆘 Common Issues

### Issue: Map shows "No data"

**Solution**: Check BigQuery credentials and project access

```bash
python3 -c "from google.cloud import bigquery; client = bigquery.Client(project='inner-cinema-476211-u9'); print(list(client.query('SELECT 1').result()))"
```

### Issue: HTTP 403 Forbidden

**Solution**: Fix file permissions

```bash
sudo chown -R nginx:nginx /var/www/maps
sudo chmod -R 755 /var/www/maps
sudo setenforce 0  # If SELinux is blocking
```

### Issue: Cron not running

**Solution**: Check cron service and logs

```bash
sudo systemctl status crond
sudo systemctl start crond
sudo grep CRON /var/log/cron | tail
```

### Issue: Can't access from browser

**Solution**: Check firewall and UpCloud settings

```bash
sudo firewall-cmd --list-all
# Ensure UpCloud firewall allows port 80
```

---

## 📞 Support

For issues:

1. Check logs: `/var/www/maps/logs/`
2. Test manual execution: `python3 /var/www/maps/scripts/auto_generate_map_linux.py`
3. Verify BigQuery access: Run test query
4. Check Nginx: `systemctl status nginx`
5. Review cron: `crontab -l` and `/var/log/cron`

---

## 🎉 Success!

Once deployed, your live GB Power Map will be:

✅ **Publicly accessible** at http://94.237.55.234/gb_power_complete_map.html  
✅ **Auto-updating** every 30 minutes with latest data  
✅ **Showing all 5 layers**: DNO, GSP, Offshore Wind, CVA, SVA  
✅ **Ready for Google Sheets integration**

**Next**: Add the URL to your Google Sheets dashboard!

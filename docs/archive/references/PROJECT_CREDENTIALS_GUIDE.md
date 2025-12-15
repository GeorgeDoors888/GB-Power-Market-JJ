# GB Power Market - Complete Credentials & Configuration Guide

**Last Updated:** 2 November 2025  
**Status:** ✅ All Systems Operational

---

## 🔐 Master Service Account

**One account to rule them all** - This service account provides access to BigQuery, Google Sheets, Google Docs, and Google Drive.

### Service Account Details
```json
{
  "account_name": "Smart Grid Service Account",
  "email": "all-jibber@inner-cinema-476211-u9.iam.gserviceaccount.com",
  "project_id": "inner-cinema-476211-u9",
  "client_id": "116148348392935598105"
}
```

### Credentials File Locations
- **Local Mac:** `/Users/georgemajor/GB Power Market JJ/smart_grid_credentials.json`
- **AlmaLinux Server:** `/root/bigquery_credentials.json`
- **Original Download:** `/Users/georgemajor/Downloads/inner-cinema-476211-u9-2547ee0ece35.json`

---

## 📊 BigQuery Connection

### Project Details
- **Project ID:** `inner-cinema-476211-u9`
- **Project Name:** Smart Grid
- **Region:** US
- **Primary Dataset:** `uk_energy_prod`
- **Analytics Dataset:** `uk_energy_analytics`

### Authentication Setup
```bash
# Set environment variable
export GOOGLE_APPLICATION_CREDENTIALS="/Users/georgemajor/GB Power Market JJ/smart_grid_credentials.json"
```

```python
# Python usage
from google.cloud import bigquery
import os

os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'smart_grid_credentials.json'
client = bigquery.Client(project='inner-cinema-476211-u9')

# Query example
query = """
SELECT boundary, SUM(generation) as total
FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_indgen`
WHERE settlementDate = CURRENT_DATE()
GROUP BY boundary
"""
results = client.query(query).result()
```

### Key Tables

| Table | Description | Records | Update Frequency |
|-------|-------------|---------|------------------|
| `bmrs_indgen` | GSP Generation Data | Live | 30 minutes |
| `bmrs_inddem` | GSP Demand Data | Live | 30 minutes |
| `sva_generators_with_coords` | Small Generators | 7,072 | Monthly |
| `cva_plants` | Large Power Plants | 1,581 | Monthly |
| `offshore_wind_farms` | Wind Farms | 35 | Quarterly |
| `bmrs_fuelinst` | Fuel Mix | Live | 15 minutes |
| `bmrs_freq` | Grid Frequency | Live | 15 minutes |

### Important Schema Notes
⚠️ **Common Column Name Issues:**
- GSP identifier: Use `boundary` (NOT `nationalGridBmUnit`)
- Longitude: Use `lng` (NOT `lon`)
- Demand table: Use `demand` column (NOT `generation`)
- Generator GSP: Use `gsp` (NOT `gsp_zone`)

---

## 📈 Google Sheets Connection

### Main Dashboard
- **Name:** GB Power Market Dashboard
- **Spreadsheet ID:** `1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA`
- **URL:** https://docs.google.com/spreadsheets/d/1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA/edit

### Authentication Setup
```python
import gspread
from google.oauth2.service_account import Credentials

# Define scopes
scopes = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]

# Authenticate
creds = Credentials.from_service_account_file(
    'smart_grid_credentials.json',
    scopes=scopes
)
client = gspread.authorize(creds)

# Open spreadsheet
spreadsheet = client.open_by_key('1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA')
sheet = spreadsheet.sheet1

# Read/write data
data = sheet.get_all_values()
sheet.update('A1', 'New Value')
```

### Sheets in Dashboard
1. **Dashboard** (Main) - KPIs and navigation links
2. **Analysis BI Enhanced** - Business intelligence analysis
3. **Fuel Mix** - Current generation by fuel type
4. **Grid Frequency** - Real-time frequency monitoring
5. **CVA Plants** - Large generator data export

### Permission Setup
⚠️ **Important:** To grant access to the service account:
1. Open your Google Sheet
2. Click "Share" button
3. Add: `all-jibber@inner-cinema-476211-u9.iam.gserviceaccount.com`
4. Set permission: **Editor**

---

## 📄 Google Docs Connection

### Authentication
```python
from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials

creds = Credentials.from_service_account_file('smart_grid_credentials.json')
service = build('docs', 'v1', credentials=creds)

# Read document
document = service.documents().get(documentId='YOUR_DOC_ID').execute()

# Update document
requests = [{
    'insertText': {
        'location': {'index': 1},
        'text': 'New content'
    }
}]
service.documents().batchUpdate(
    documentId='YOUR_DOC_ID',
    body={'requests': requests}
).execute()
```

---

## 💾 Google Drive Connection

### Authentication
```python
from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials

creds = Credentials.from_service_account_file('smart_grid_credentials.json')
service = build('drive', 'v3', credentials=creds)

# List files
results = service.files().list(
    pageSize=10,
    fields="files(id, name, mimeType)"
).execute()
files = results.get('files', [])

# Download file
file_id = 'YOUR_FILE_ID'
request = service.files().get_media(fileId=file_id)
with open('output.pdf', 'wb') as f:
    downloader = MediaIoBaseDownload(f, request)
    done = False
    while not done:
        status, done = downloader.next_chunk()
```

---

## 🖥️ Server Infrastructure (AlmaLinux)

### Server Details
- **Type:** AlmaLinux 10
- **Hostname:** almalinux-1cpu-2gb-uk-lon1
- **IP Address:** 94.237.55.234
- **Location:** London, UK
- **Web Server:** Nginx 1.26.3
- **Python:** 3.12.9

### Live Services

#### 1. IRIS Pipeline (Every 15 minutes)
```bash
# Location: /opt/iris-pipeline/
# Updates: BMRS fuel mix, frequency, demand data
# Output: JSON files
# Status: ✅ Active since deployment
```

#### 2. GB Power Map (Every 30 minutes)
```bash
# Script: /var/www/maps/scripts/auto_generate_map_linux.py
# Output: /var/www/maps/gb_power_complete_map.html
# URL: http://94.237.55.234/gb_power_complete_map.html
# Status: ✅ Active and generating
```

### Cron Jobs
```cron
# IRIS Pipeline
@reboot sleep 60 && /opt/iris-pipeline/start_iris_pipeline.sh
*/15 * * * * /opt/iris-pipeline/monitor_iris_pipeline.sh
0 * * * * /opt/iris-pipeline/collect_stats.sh

# GB Power Map
*/30 * * * * export GOOGLE_APPLICATION_CREDENTIALS=/root/bigquery_credentials.json && python3 /var/www/maps/scripts/auto_generate_map_linux.py
```

### Server Access
```bash
# SSH connection
ssh root@94.237.55.234

# Check map generation logs
tail -f /var/www/maps/logs/map_generation.log

# Check Nginx status
systemctl status nginx

# View cron jobs
crontab -l
```

---

## 🔧 Python Installation

### Required Libraries
```bash
# BigQuery
pip install google-cloud-bigquery

# Google Sheets
pip install gspread google-auth

# Google APIs (Docs, Drive)
pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib
```

### Complete Requirements
```txt
google-cloud-bigquery>=3.38.0
gspread>=5.0.0
google-auth>=2.0.0
google-api-python-client>=2.0.0
google-auth-httplib2>=0.1.0
google-auth-oauthlib>=0.5.0
```

---

## 🌐 Live URLs

### Production Services
- **Power Map:** http://94.237.55.234/gb_power_complete_map.html
- **Dashboard:** https://docs.google.com/spreadsheets/d/1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA/edit

### Google Cloud Console
- **BigQuery:** https://console.cloud.google.com/bigquery?project=inner-cinema-476211-u9
- **IAM & Admin:** https://console.cloud.google.com/iam-admin/serviceaccounts?project=inner-cinema-476211-u9
- **Dashboard:** https://console.cloud.google.com/home/dashboard?project=inner-cinema-476211-u9

---

## 🚨 Troubleshooting

### Permission Denied (BigQuery)
```bash
# Verify service account has roles:
# - BigQuery Data Viewer
# - BigQuery Job User
# Check in: https://console.cloud.google.com/iam-admin/iam?project=inner-cinema-476211-u9
```

### Permission Denied (Sheets)
```bash
# Share spreadsheet with service account email:
# all-jibber@inner-cinema-476211-u9.iam.gserviceaccount.com
# Grant "Editor" permission
```

### Credentials Not Found
```bash
# Set environment variable
export GOOGLE_APPLICATION_CREDENTIALS="/full/path/to/smart_grid_credentials.json"

# Verify file exists
ls -lh "$GOOGLE_APPLICATION_CREDENTIALS"

# Test connection
python3 -c "from google.cloud import bigquery; import os; client = bigquery.Client(project='inner-cinema-476211-u9'); print('✅ Connected:', client.project)"
```

### Schema Errors
Common issues when querying BigQuery:
- ❌ `nationalGridBmUnit` → ✅ `boundary`
- ❌ `lon` → ✅ `lng`
- ❌ `gsp_zone` → ✅ `gsp`

### Map Not Accessible
```bash
# Check Nginx
systemctl status nginx

# Check firewall
firewall-cmd --list-ports

# Check file exists
ls -lh /var/www/maps/gb_power_complete_map.html

# Test locally
curl -I http://94.237.55.234/gb_power_complete_map.html
```

---

## 📊 Data Flow Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Data Sources                              │
│  • BMRS API (Elexon)                                        │
│  • NESO API (National Energy System Operator)              │
│  • Manual Data Files (CVA, SVA, Wind Farms)                │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────┐
│              BigQuery (inner-cinema-476211-u9)              │
│  Dataset: uk_energy_prod                                    │
│  • bmrs_indgen (GSP Generation)                            │
│  • bmrs_inddem (GSP Demand)                                │
│  • sva_generators_with_coords (7,072 generators)           │
│  • cva_plants (1,581 plants)                               │
│  • offshore_wind_farms (35 farms)                          │
│  • bmrs_fuelinst (Fuel mix)                                │
│  • bmrs_freq (Grid frequency)                              │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────┐
│              Processing (Python Scripts)                     │
│  Authentication: all-jibber@inner-cinema-476211-u9         │
│  • auto_generate_map_linux.py (Maps)                       │
│  • update_analysis_bi_enhanced.py (BI)                     │
│  • update_analysis_with_calculations.py (Stats)            │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────┐
│                  Outputs                                     │
│  • Google Sheets Dashboard (Live)                           │
│  • GB Power Map HTML (http://94.237.55.234)                │
│  • Analysis Reports                                         │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔐 Security Best Practices

1. **Never commit credentials to version control**
   ```bash
   # Add to .gitignore
   echo "smart_grid_credentials.json" >> .gitignore
   echo "**/*credentials*.json" >> .gitignore
   echo "!*template.json" >> .gitignore
   ```

2. **Secure file permissions on server**
   ```bash
   chmod 600 /root/bigquery_credentials.json
   chown root:root /root/bigquery_credentials.json
   ```

3. **Rotate credentials annually**
   - Create new service account key
   - Update all deployment locations
   - Delete old key from GCP console

4. **Use HTTPS in production**
   ```bash
   # Install Let's Encrypt on server
   dnf install certbot python3-certbot-nginx
   certbot --nginx -d yourdomain.com
   ```

5. **Audit service account permissions**
   - Review IAM roles quarterly
   - Remove unused permissions
   - Monitor activity logs

---

## ✅ Connection Verification Tests

### Test BigQuery Connection
```bash
python3 -c "
from google.cloud import bigquery
import os
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'smart_grid_credentials.json'
client = bigquery.Client(project='inner-cinema-476211-u9')
query = 'SELECT COUNT(*) as count FROM \`inner-cinema-476211-u9.uk_energy_prod.sva_generators_with_coords\`'
result = list(client.query(query).result())[0]
print(f'✅ BigQuery Connected - Found {result.count} generators')
"
```

### Test Google Sheets Connection
```bash
python3 -c "
import gspread
from google.oauth2.service_account import Credentials
scopes = ['https://www.googleapis.com/auth/spreadsheets']
creds = Credentials.from_service_account_file('smart_grid_credentials.json', scopes=scopes)
client = gspread.authorize(creds)
sheet = client.open_by_key('1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA')
print(f'✅ Sheets Connected - Opened: {sheet.title}')
"
```

### Test Map Accessibility
```bash
curl -I http://94.237.55.234/gb_power_complete_map.html
# Should return: HTTP/1.1 200 OK
```

---

## 📞 Quick Reference

### One-Liner Connections

**BigQuery:**
```python
from google.cloud import bigquery; client = bigquery.Client(project='inner-cinema-476211-u9')
```

**Sheets:**
```python
import gspread; from google.oauth2.service_account import Credentials; client = gspread.authorize(Credentials.from_service_account_file('smart_grid_credentials.json', scopes=['https://www.googleapis.com/auth/spreadsheets']))
```

**Environment Variable:**
```bash
export GOOGLE_APPLICATION_CREDENTIALS="/Users/georgemajor/GB Power Market JJ/smart_grid_credentials.json"
```

---

## 📚 Additional Resources

- [BigQuery Python Client Docs](https://cloud.google.com/python/docs/reference/bigquery/latest)
- [gspread Documentation](https://docs.gspread.org/)
- [Google API Python Client](https://github.com/googleapis/google-api-python-client)
- [Service Account Best Practices](https://cloud.google.com/iam/docs/best-practices-service-accounts)

---

**Project Status:** ✅ **All Systems Operational**  
**Last Verified:** 2 November 2025 12:33 UTC  
**Next Review:** December 2025

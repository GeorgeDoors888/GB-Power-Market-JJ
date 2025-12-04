# VLP Dashboard - Automated Refresh Setup

## ✅ Quick Setup

### 1. Test Manual Refresh
```bash
cd ~/GB-Power-Market-JJ
./refresh_vlp_auto.sh
```

Expected output:
```
✅ Dashboard data refreshed
📈 Current Metrics:
   Profit: £242.81/MWh
   Signal: DISCHARGE_HIGH
✅ AUTO-REFRESH COMPLETE
```

---

## 🕐 Option 1: Cron Job (Recommended)

### Setup (5-minute refresh)
```bash
# Open crontab editor
crontab -e

# Add this line (refresh every 5 minutes)
*/5 * * * * cd ~/GB-Power-Market-JJ && ./refresh_vlp_auto.sh >> logs/cron_output.log 2>&1

# Save and exit (Ctrl+X, Y, Enter in nano)
```

### Verify Cron Job
```bash
# List active cron jobs
crontab -l

# Check logs after 5 minutes
tail -f ~/GB-Power-Market-JJ/logs/cron_output.log
```

### Alternative: 30-minute refresh (less frequent)
```bash
# Edit crontab
crontab -e

# Add this line
*/30 * * * * cd ~/GB-Power-Market-JJ && ./refresh_vlp_auto.sh >> logs/cron_output.log 2>&1
```

---

## 🚀 Option 2: LaunchAgent (macOS, survives restarts)

### Create LaunchAgent plist
```bash
cat > ~/Library/LaunchAgents/uk.upowerenergy.vlp-dashboard.plist << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>uk.upowerenergy.vlp-dashboard</string>
    
    <key>ProgramArguments</key>
    <array>
        <string>/bin/bash</string>
        <string>-c</string>
        <string>cd ~/GB-Power-Market-JJ && ./refresh_vlp_auto.sh</string>
    </array>
    
    <key>StartInterval</key>
    <integer>300</integer> <!-- 300 seconds = 5 minutes -->
    
    <key>StandardOutPath</key>
    <string>~/GB-Power-Market-JJ/logs/launchagent_stdout.log</string>
    
    <key>StandardErrorPath</key>
    <string>~/GB-Power-Market-JJ/logs/launchagent_stderr.log</string>
    
    <key>RunAtLoad</key>
    <true/>
    
    <key>KeepAlive</key>
    <false/>
</dict>
</plist>
EOF
```

### Load LaunchAgent
```bash
# Load and start
launchctl load ~/Library/LaunchAgents/uk.upowerenergy.vlp-dashboard.plist

# Verify it's running
launchctl list | grep vlp-dashboard

# Check logs
tail -f ~/GB-Power-Market-JJ/logs/launchagent_stdout.log
```

### Unload (if needed)
```bash
launchctl unload ~/Library/LaunchAgents/uk.upowerenergy.vlp-dashboard.plist
```

---

## ☁️ Option 3: Cloud Function (Advanced)

### Deploy to Google Cloud Functions
```bash
# Create function directory
mkdir -p cloud-functions/vlp-dashboard-refresh
cd cloud-functions/vlp-dashboard-refresh

# Create requirements.txt
cat > requirements.txt << EOF
google-cloud-bigquery==3.14.1
gspread==6.1.3
google-auth==2.25.2
pandas==2.1.4
db-dtypes==1.2.1
pyarrow==14.0.2
gspread-formatting==1.2.0
EOF

# Create main.py
cat > main.py << 'EOF'
from google.cloud import bigquery
import gspread
from google.oauth2.service_account import Credentials

def refresh_vlp_dashboard(request):
    """HTTP Cloud Function to refresh VLP dashboard"""
    # Copy logic from vlp_dashboard_python.py
    # ... (implementation)
    
    return {'status': 'success', 'message': 'Dashboard refreshed'}
EOF

# Deploy to GCP
gcloud functions deploy vlp-dashboard-refresh \
    --runtime python311 \
    --trigger-http \
    --allow-unauthenticated \
    --entry-point refresh_vlp_dashboard \
    --region us-central1
```

### Schedule with Cloud Scheduler
```bash
# Create Cloud Scheduler job (every 5 minutes)
gcloud scheduler jobs create http vlp-dashboard-schedule \
    --schedule="*/5 * * * *" \
    --uri="https://us-central1-inner-cinema-476211-u9.cloudfunctions.net/vlp-dashboard-refresh" \
    --http-method=POST \
    --time-zone="Europe/London"
```

---

## 🔔 Option 4: Webhook Integration

### Flask Webhook Server
```python
# webhook_server.py
from flask import Flask, request, jsonify
import subprocess
import os

app = Flask(__name__)

@app.route('/refresh-vlp', methods=['POST'])
def refresh_vlp():
    """Webhook endpoint to trigger dashboard refresh"""
    try:
        # Change to project directory
        os.chdir('/Users/georgemajor/GB-Power-Market-JJ')
        
        # Run refresh script
        result = subprocess.run(
            ['./refresh_vlp_auto.sh'],
            capture_output=True,
            text=True,
            timeout=60
        )
        
        return jsonify({
            'status': 'success',
            'output': result.stdout,
            'timestamp': datetime.now().isoformat()
        }), 200
    
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5002)
```

### Run Webhook Server
```bash
# Install Flask
pip3 install --user flask

# Run server (background)
nohup python3 webhook_server.py > logs/webhook_server.log 2>&1 &

# Expose with ngrok
ngrok http 5002

# Trigger from anywhere
curl -X POST https://YOUR-NGROK-URL.ngrok.io/refresh-vlp
```

### Apps Script Integration
```javascript
// Add to Code.gs
function triggerVlpRefresh() {
  var webhookUrl = 'https://YOUR-NGROK-URL.ngrok.io/refresh-vlp';
  
  var options = {
    'method': 'post',
    'contentType': 'application/json',
    'muteHttpExceptions': true
  };
  
  try {
    var response = UrlFetchApp.fetch(webhookUrl, options);
    var result = JSON.parse(response.getContentText());
    
    if (result.status === 'success') {
      SpreadsheetApp.getActive().toast('✅ Dashboard refreshed', 'VLP Dashboard', 3);
    } else {
      SpreadsheetApp.getActive().toast('❌ Refresh failed: ' + result.message, 'VLP Dashboard', 5);
    }
  } catch (e) {
    SpreadsheetApp.getActive().toast('❌ Error: ' + e.message, 'VLP Dashboard', 5);
  }
}

function onOpen() {
  SpreadsheetApp.getUi()
    .createMenu('⚡ Energy Tools')
    .addSubMenu(SpreadsheetApp.getUi().createMenu('💰 VLP Revenue')
      .addItem('🔄 Refresh Now', 'triggerVlpRefresh')
      .addItem('📊 View Dashboard', 'openVlpSheet'))
    .addToUi();
}
```

---

## 📊 Monitoring

### Check Refresh History
```bash
# Last 10 refreshes
tail -10 ~/GB-Power-Market-JJ/logs/vlp_refresh_history.log

# Today's detailed logs
tail -50 ~/GB-Power-Market-JJ/logs/vlp_refresh_$(date +%Y%m%d).log

# Live tail (watch real-time updates)
tail -f ~/GB-Power-Market-JJ/logs/cron_output.log
```

### Verify Latest Data
```bash
cd ~/GB-Power-Market-JJ

# Quick check
python3 -c "
from google.cloud import bigquery
from google.oauth2.service_account import Credentials
from datetime import datetime

creds = Credentials.from_service_account_file(
    'inner-cinema-credentials.json',
    scopes=['https://www.googleapis.com/auth/bigquery']
)
client = bigquery.Client(project='inner-cinema-476211-u9', location='US', credentials=creds)

query = '''
SELECT 
    MAX(settlementDate) as last_date,
    MAX(settlementPeriod) as last_period
FROM \`inner-cinema-476211-u9.uk_energy_prod.v_btm_bess_inputs\`
'''

result = client.query(query).result()
for row in result:
    print(f'Latest data: {row.last_date} Period {row.last_period}')
    now = datetime.now()
    print(f'Current time: {now.strftime(\"%Y-%m-%d %H:%M\")}')
"
```

---

## 🔧 Troubleshooting

### Issue: Cron job not running
```bash
# Check cron is active
pgrep cron || echo "Cron not running!"

# Check cron logs (macOS)
log show --predicate 'process == "cron"' --last 1h

# Check script permissions
ls -la ~/GB-Power-Market-JJ/refresh_vlp_auto.sh
# Should show: -rwxr-xr-x (executable)
```

### Issue: "Permission denied"
```bash
chmod +x ~/GB-Power-Market-JJ/refresh_vlp_auto.sh
chmod +x ~/GB-Power-Market-JJ/vlp_dashboard_python.py
```

### Issue: Python packages not found
```bash
# Verify packages installed
python3 -c "import google.cloud.bigquery; print('✅ BigQuery OK')"
python3 -c "import gspread; print('✅ gspread OK')"

# Reinstall if needed
pip3 install --user --upgrade google-cloud-bigquery gspread google-auth pandas db-dtypes pyarrow gspread-formatting
```

### Issue: Credentials not found
```bash
# Check file exists
ls -la ~/GB-Power-Market-JJ/inner-cinema-credentials.json

# Verify path in script
grep CREDENTIALS ~/GB-Power-Market-JJ/vlp_dashboard_python.py
```

---

## 📈 Performance

### Typical Execution Times
- **Dashboard Refresh**: 5-10 seconds
  - BigQuery queries: 2-3 seconds
  - Google Sheets API: 3-5 seconds
  - Formatting: 1-2 seconds

- **Charts Update**: 3-5 seconds
  - Chart creation: 1-2 seconds per chart
  - Advanced formatting: 1 second

### Resource Usage
- **CPU**: < 5% (during execution)
- **Memory**: ~100MB (Python process)
- **Network**: ~500KB per refresh (BigQuery + Sheets API)
- **BigQuery**: ~1MB scanned per query (well within free tier)

---

## 🎯 Recommended Schedule

### Production Setup
```bash
# Crontab entries for optimal refresh
crontab -e

# Main dashboard: Every 5 minutes (high priority)
*/5 * * * * cd ~/GB-Power-Market-JJ && ./refresh_vlp_auto.sh >> logs/cron_output.log 2>&1

# Charts: Every 30 minutes (less critical)
*/30 * * * * cd ~/GB-Power-Market-JJ && python3 vlp_charts_python.py >> logs/charts_cron.log 2>&1

# Cleanup old logs: Daily at 2 AM
0 2 * * * find ~/GB-Power-Market-JJ/logs -name "*.log" -mtime +30 -delete
```

### Development/Testing Setup
```bash
# More frequent updates for testing
*/1 * * * * cd ~/GB-Power-Market-JJ && ./refresh_vlp_auto.sh >> logs/cron_output.log 2>&1
```

---

## 🔐 Security Notes

### Credentials Protection
```bash
# Ensure credentials are not world-readable
chmod 600 ~/GB-Power-Market-JJ/inner-cinema-credentials.json

# Add to .gitignore (already done)
echo "inner-cinema-credentials.json" >> .gitignore
```

### Service Account Permissions
The service account needs:
- **BigQuery**: `roles/bigquery.dataViewer` (read data)
- **BigQuery**: `roles/bigquery.jobUser` (run queries)
- **Google Sheets**: Editor access (shared explicitly)

### Network Security
- Webhook server: Use HTTPS (ngrok provides this)
- Cloud Functions: Require authentication or use secret token
- IP whitelist: Restrict webhook access to known IPs

---

## ✅ Success Criteria

Your automated refresh is working if:
- [x] Cron job shows in `crontab -l`
- [x] Logs show successful refreshes every 5 minutes
- [x] Google Sheets shows "Last updated" timestamp advancing
- [x] Current profit metrics match BigQuery latest data
- [x] No error messages in logs

---

**Last Updated**: December 3, 2025  
**Status**: ✅ Production Ready  
**Maintainer**: George Major (george@upowerenergy.uk)

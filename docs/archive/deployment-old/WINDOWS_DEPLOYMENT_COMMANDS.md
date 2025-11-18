# Windows Server Deployment - Step-by-Step Commands

**Server Details:**
- Hostname: windows-1cpu-2gb-uk-lon1
- Location: London, UK
- Password: T8zh5AQS2H9jHdsK
- Package: iris_windows_deployment.zip (ready on your Mac)

---

## STEP 1: Connect to Windows Server

### Option A: Using Microsoft Remote Desktop (Recommended for Mac)
1. Download Microsoft Remote Desktop from Mac App Store
2. Create new connection:
   - PC Name: `windows-1cpu-2gb-uk-lon1` (or use IP address from UpCloud dashboard)
   - User Account: `Administrator`
   - Password: `T8zh5AQS2H9jHdsK`
3. Connect to server

### Option B: Using Windows RDP Client
```bash
# If you have a Windows machine or Windows in VM
mstsc /v:windows-1cpu-2gb-uk-lon1
```

---

## STEP 2: Upload Deployment Package

### Method 1: Drag & Drop (Easiest)
1. Once connected via RDP, simply **drag** `iris_windows_deployment.zip` from your Mac Finder
2. **Drop** it into the Windows Desktop or Downloads folder on the RDP window

### Method 2: Via UpCloud Console
1. Go to UpCloud dashboard → Your server → Console
2. Use file upload feature if available

### Method 3: Via Cloud Storage (if drag-drop fails)
```bash
# On your Mac - upload to Google Drive or similar
# Then download from Windows server browser
```

---

## STEP 3: Extract & Prepare Files

**On Windows Server (PowerShell as Administrator):**

```powershell
# Navigate to where you uploaded the ZIP
cd C:\Users\Administrator\Downloads

# Extract the package
Expand-Archive -Path iris_windows_deployment.zip -DestinationPath C:\

# Verify extraction
cd C:\iris_windows_deployment
Get-ChildItem -Recurse

# You should see:
# - iris_client/
# - scripts/
# - logs/
# - iris_data/
# - *.ps1 files
```

---

## STEP 4: Install Python 3.11+

```powershell
# Download Python 3.11 installer
Invoke-WebRequest -Uri "https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe" -OutFile "C:\python-installer.exe"

# Install Python (silent install with PATH)
Start-Process -Wait -FilePath "C:\python-installer.exe" -ArgumentList "/quiet", "InstallAllUsers=1", "PrependPath=1", "Include_test=0"

# Verify installation
python --version
# Should show: Python 3.11.9

# Verify pip
pip --version
```

---

## STEP 5: Install Google Cloud SDK

```powershell
# Download Google Cloud SDK installer
Invoke-WebRequest -Uri "https://dl.google.com/dl/cloudsdk/channels/rapid/GoogleCloudSDKInstaller.exe" -OutFile "C:\gcloud-installer.exe"

# Run installer (this will open a window - follow prompts)
Start-Process -FilePath "C:\gcloud-installer.exe"

# After installation, restart PowerShell and verify
gcloud --version

# Authenticate with Google Cloud
gcloud auth login
# This will open browser - login with your Google account

# Set project
gcloud config set project inner-cinema-476211-u9

# Create service account credentials (if not already done)
# Option 1: Copy credentials.json from your Mac to server
# Option 2: Create new credentials and download

# Authenticate for BigQuery
gcloud auth application-default login
```

---

## STEP 6: Copy Google Cloud Credentials

### Method A: From your Mac
```bash
# On your Mac, copy credentials to clipboard
cat "/Users/georgemajor/GB Power Market JJ/credentials.json"
# Copy the output
```

Then on Windows Server:
```powershell
# Create credentials file
notepad C:\iris_windows_deployment\credentials.json
# Paste the credentials JSON and save
```

### Method B: Via RDP drag-drop
Just drag `credentials.json` from your Mac to the Windows server.

---

## STEP 7: Install Python Dependencies

```powershell
cd C:\iris_windows_deployment

# Install required packages
pip install -r scripts\requirements.txt

# Should install:
# - azure-servicebus
# - google-cloud-bigquery
# - google-cloud-bigquery-storage
# - pandas
```

---

## STEP 8: Set Environment Variables

```powershell
# Set Google credentials path
[Environment]::SetEnvironmentVariable("GOOGLE_APPLICATION_CREDENTIALS", "C:\iris_windows_deployment\credentials.json", "Machine")

# Set project ID
[Environment]::SetEnvironmentVariable("GOOGLE_CLOUD_PROJECT", "inner-cinema-476211-u9", "Machine")

# Restart PowerShell to apply changes
exit
# Then reopen PowerShell as Administrator
```

---

## STEP 9: Test IRIS Client (Optional but Recommended)

```powershell
cd C:\iris_windows_deployment

# Test download (10 messages)
python iris_client\client.py --output-dir iris_data --max-messages 10

# Check if files were created
Get-ChildItem iris_data -Recurse | Measure-Object

# You should see JSON files in various subfolders
```

---

## STEP 10: Test BigQuery Upload (Optional but Recommended)

```powershell
# Test uploading the sample files
python scripts\iris_to_bigquery_unified.py --input-dir iris_data --delete-after-upload

# Check for success messages in output
# Check BigQuery tables updated:
# https://console.cloud.google.com/bigquery?project=inner-cinema-476211-u9
```

---

## STEP 11: Install as Windows Service

```powershell
cd C:\iris_windows_deployment

# Run installation script as Administrator
.\install_service.ps1

# You should see:
# ✅ Service installed successfully
# ✅ Task Name: IrisDataPipeline
# ✅ Will run at startup
```

---

## STEP 12: Start the Pipeline

```powershell
# Start the scheduled task (begins pipeline)
Start-ScheduledTask -TaskName "IrisDataPipeline"

# Verify it's running
Get-ScheduledTask -TaskName "IrisDataPipeline"

# Check if processes are running
Get-Process | Where-Object {$_.ProcessName -like "*python*"}
```

---

## STEP 13: Monitor the Pipeline

### View Real-time Logs
```powershell
# Watch the pipeline log (live)
Get-Content C:\iris_windows_deployment\logs\pipeline.log -Wait -Tail 50

# You should see:
# - "Starting IRIS client..."
# - "Files in iris_data: XX"
# - "Running BigQuery uploader..."
# - "Upload complete. Rows inserted: XXX"
```

### Run Health Check
```powershell
# Run health check script
cd C:\iris_windows_deployment
.\check_health.ps1

# Shows:
# - Service status
# - File count
# - Recent activity
# - Disk space
# - Recent log entries
```

### Check File Accumulation
```powershell
# Count files in iris_data folder
(Get-ChildItem C:\iris_windows_deployment\iris_data -Recurse -File).Count

# Should stay under 10,000 (auto-deleted after upload)
```

### View Upload Statistics
```powershell
# Check last 100 log lines for upload stats
Get-Content C:\iris_windows_deployment\logs\pipeline.log -Tail 100 | Select-String "Rows inserted"
```

---

## STEP 14: Verify Data in BigQuery

### On your Mac (or on Windows server via browser):
```bash
# Check latest data in IRIS tables
bq query --use_legacy_sql=false '
SELECT 
  MAX(timestamp) as latest_time,
  COUNT(*) as total_rows
FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_mid_iris`
'

# Should show recent data (within 2-5 minutes)
```

Or visit BigQuery Console:
https://console.cloud.google.com/bigquery?project=inner-cinema-476211-u9

Check these tables for fresh data:
- `bmrs_mid_iris` (prices)
- `bmrs_indo_iris` (demand) 
- `bmrs_fuelinst_iris` (wind generation)

---

## STEP 15: Schedule Regular Monitoring

### Set up daily health check email (optional):
```powershell
# Create monitoring task
$trigger = New-ScheduledTaskTrigger -Daily -At 9AM
$action = New-ScheduledTaskAction -Execute "PowerShell.exe" -Argument "-File C:\iris_windows_deployment\check_health.ps1"
Register-ScheduledTask -TaskName "IrisHealthCheck" -Trigger $trigger -Action $action -RunLevel Highest
```

---

## Troubleshooting Commands

### If service isn't running:
```powershell
# Check task status
Get-ScheduledTask -TaskName "IrisDataPipeline" | Select-Object State, LastRunTime, LastTaskResult

# View task history
Get-ScheduledTask -TaskName "IrisDataPipeline" | Get-ScheduledTaskInfo

# Restart service
Stop-ScheduledTask -TaskName "IrisDataPipeline"
Start-ScheduledTask -TaskName "IrisDataPipeline"
```

### If files accumulating (not uploading):
```powershell
# Check file count
(Get-ChildItem C:\iris_windows_deployment\iris_data -Recurse -File).Count

# Manual upload
cd C:\iris_windows_deployment
python scripts\iris_to_bigquery_unified.py --input-dir iris_data --delete-after-upload
```

### If client not downloading:
```powershell
# Test IRIS connection
cd C:\iris_windows_deployment
python iris_client\client.py --output-dir iris_data --max-messages 5

# Check error messages in output
```

### Check disk space:
```powershell
Get-PSDrive C | Select-Object Used,Free
```

---

## Success Indicators

✅ **Pipeline Running Successfully:**
- Python processes visible in Task Manager
- Files created in `iris_data/` folder every few seconds
- Log file growing (`logs/pipeline.log`)
- File count cycles: builds up → uploads → resets to low number
- BigQuery tables showing data within last 2-5 minutes

✅ **Expected Performance:**
- Download rate: 100-500 messages/minute
- File count: Usually 5,000-10,000 before upload
- Upload frequency: Every 5 minutes
- Data latency: 30 seconds to 2 minutes

---

## What to Watch For

⚠️ **Warning Signs:**
- File count exceeds 10,000 (upload may be failing)
- No new files in 5+ minutes (client may have crashed)
- Disk space below 1 GB (need to clear old logs)
- No log entries for 10+ minutes (service may be stopped)

---

## Quick Reference - Most Used Commands

```powershell
# Check service status
Get-ScheduledTask -TaskName "IrisDataPipeline"

# View live logs
Get-Content C:\iris_windows_deployment\logs\pipeline.log -Wait -Tail 50

# Run health check
cd C:\iris_windows_deployment
.\check_health.ps1

# Count files
(Get-ChildItem C:\iris_windows_deployment\iris_data -Recurse -File).Count

# Restart service
Stop-ScheduledTask -TaskName "IrisDataPipeline"
Start-ScheduledTask -TaskName "IrisDataPipeline"
```

---

## Support Files Location

- **Deployment Package**: `/Users/georgemajor/GB Power Market JJ/iris_windows_deployment.zip`
- **Full Guide**: `/Users/georgemajor/GB Power Market JJ/UPCLOUD_DEPLOYMENT_PLAN.md`
- **Credentials**: `/Users/georgemajor/GB Power Market JJ/credentials.json`
- **This Guide**: `/Users/georgemajor/GB Power Market JJ/WINDOWS_DEPLOYMENT_COMMANDS.md`

---

## Next: Once Pipeline is Running

After 24 hours of stable operation, you can update your chart script to use the real-time IRIS tables instead of the delayed historical tables. This will give you current data (30s-2min old) instead of 3-6 days old!

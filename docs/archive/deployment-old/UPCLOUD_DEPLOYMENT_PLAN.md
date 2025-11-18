# 🚀 UpCloud Windows Server Deployment Plan

## Server Details

**Server Name**: windows-1cpu-2gb-uk-lon1  
**Hostname**: windows-1cpu-2gb-uk-lon1  
**Location**: London (UK)  
**Password**: T8hz5AQS2H9jHdsK  
**OS**: Windows Server

---

## 🎯 Deployment Objective

Set up **automated live data ingestion** that:
1. ✅ Downloads IRIS messages from Azure Service Bus
2. ✅ Batch uploads to BigQuery every 5-15 minutes  
3. ✅ Automatically deletes local files after successful ingestion
4. ✅ Runs 24/7 as Windows service
5. ✅ Monitors health and restarts on failure

---

## 📋 Pre-Deployment Checklist

### Required Files to Upload

```
iris-clients/python/
├── client.py                    # IRIS message downloader
├── requirements.txt             # Python dependencies
└── config.json                  # Azure Service Bus credentials

iris_to_bigquery_unified.py      # Batch uploader & auto-delete
monitor_iris_pipeline.py         # Health checker & restart
```

### Credentials Needed

1. **Azure Service Bus** (IRIS)
   - Connection string
   - Topic subscriptions
   - Already configured in `client.py`

2. **Google Cloud (BigQuery)**
   - Project: inner-cinema-476211-u9
   - Dataset: uk_energy_prod
   - Service account JSON or gcloud auth

3. **UpCloud Server Access**
   - RDP credentials (provided)
   - Administrator access

---

## 🔧 Installation Steps

### Step 1: Connect to Server

```powershell
# RDP connection
Server: windows-1cpu-2gb-uk-lon1
Username: Administrator
Password: T8hz5AQS2H9jHdsK
```

### Step 2: Install Python 3.11+

```powershell
# Download Python installer
# https://www.python.org/downloads/windows/

# Install with:
# - Add to PATH
# - Include pip
# - py launcher

# Verify
python --version
pip --version
```

### Step 3: Install Google Cloud SDK

```powershell
# Download from:
# https://cloud.google.com/sdk/docs/install#windows

# Install and run:
gcloud init
gcloud auth login
gcloud config set project inner-cinema-476211-u9
```

### Step 4: Create Working Directory

```powershell
# Create directory
New-Item -Path "C:\IrisDataPipeline" -ItemType Directory

# Navigate
cd C:\IrisDataPipeline

# Create subdirectories
mkdir iris_data
mkdir logs
mkdir scripts
```

### Step 5: Upload Files

**Upload via RDP or SFTP:**
```
C:\IrisDataPipeline\
├── scripts\
│   ├── client.py
│   ├── iris_to_bigquery_unified.py
│   ├── monitor_iris_pipeline.py
│   └── requirements.txt
├── iris_data\          # Downloaded messages go here
└── logs\               # Log files
```

### Step 6: Install Python Dependencies

```powershell
cd C:\IrisDataPipeline\scripts

# Install requirements
pip install -r requirements.txt

# Key packages:
# - google-cloud-bigquery
# - azure-servicebus
# - azure-identity
# - pandas
# - dacite
```

### Step 7: Test Components

```powershell
# Test IRIS client (download messages)
cd C:\IrisDataPipeline
python scripts\client.py --output-dir iris_data --max-messages 10

# Test BigQuery uploader
python scripts\iris_to_bigquery_unified.py --input-dir iris_data --delete-after-upload

# Check if data appears in BigQuery
```

---

## 🤖 Windows Service Setup

### Create Service Script: `start_iris_pipeline.ps1`

```powershell
# C:\IrisDataPipeline\start_iris_pipeline.ps1

$LogFile = "C:\IrisDataPipeline\logs\pipeline.log"
$ScriptDir = "C:\IrisDataPipeline\scripts"
$DataDir = "C:\IrisDataPipeline\iris_data"

function Write-Log {
    param($Message)
    $Timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    "$Timestamp - $Message" | Tee-Object -FilePath $LogFile -Append
}

Write-Log "===== IRIS Pipeline Starting ====="

# Start IRIS client (download messages)
Write-Log "Starting IRIS client..."
$ClientProcess = Start-Process python -ArgumentList "$ScriptDir\client.py --output-dir $DataDir --continuous" -PassThru -NoNewWindow

# Wait for initial messages to download
Start-Sleep -Seconds 30

# Start BigQuery uploader (runs every 5 minutes)
Write-Log "Starting BigQuery uploader..."
while ($true) {
    try {
        Write-Log "Running batch upload..."
        python "$ScriptDir\iris_to_bigquery_unified.py" --input-dir "$DataDir" --delete-after-upload
        
        # Check file count
        $FileCount = (Get-ChildItem -Path $DataDir -File).Count
        Write-Log "Files remaining: $FileCount"
        
        # Check if client is still running
        if ($ClientProcess.HasExited) {
            Write-Log "ERROR: Client process died. Restarting..."
            $ClientProcess = Start-Process python -ArgumentList "$ScriptDir\client.py --output-dir $DataDir --continuous" -PassThru -NoNewWindow
        }
        
    } catch {
        Write-Log "ERROR: $($_.Exception.Message)"
    }
    
    # Wait 5 minutes before next upload
    Start-Sleep -Seconds 300
}
```

### Create Windows Scheduled Task

```powershell
# Create scheduled task to run on startup

$Action = New-ScheduledTaskAction -Execute "PowerShell.exe" -Argument "-ExecutionPolicy Bypass -File C:\IrisDataPipeline\start_iris_pipeline.ps1"

$Trigger = New-ScheduledTaskTrigger -AtStartup

$Principal = New-ScheduledTaskPrincipal -UserId "SYSTEM" -LogonType ServiceAccount -RunLevel Highest

$Settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -RestartInterval (New-TimeSpan -Minutes 1) -RestartCount 3

Register-ScheduledTask -TaskName "IrisDataPipeline" -Action $Action -Trigger $Trigger -Principal $Principal -Settings $Settings -Description "IRIS real-time data ingestion to BigQuery"
```

### Alternative: NSSM (Non-Sucking Service Manager)

```powershell
# Download NSSM from: https://nssm.cc/download
# Extract to C:\IrisDataPipeline\nssm\

# Install as service
.\nssm.exe install IrisDataPipeline "PowerShell.exe" "-ExecutionPolicy Bypass -File C:\IrisDataPipeline\start_iris_pipeline.ps1"

# Configure service
.\nssm.exe set IrisDataPipeline AppDirectory "C:\IrisDataPipeline"
.\nssm.exe set IrisDataPipeline AppStdout "C:\IrisDataPipeline\logs\service_stdout.log"
.\nssm.exe set IrisDataPipeline AppStderr "C:\IrisDataPipeline\logs\service_stderr.log"
.\nssm.exe set IrisDataPipeline AppRotateFiles 1
.\nssm.exe set IrisDataPipeline AppRotateBytes 10485760  # 10MB

# Start service
.\nssm.exe start IrisDataPipeline

# Check status
.\nssm.exe status IrisDataPipeline
```

---

## 📊 Monitoring & Maintenance

### Check Pipeline Status

```powershell
# View logs
Get-Content C:\IrisDataPipeline\logs\pipeline.log -Tail 50

# Check file count (should stay low)
(Get-ChildItem -Path C:\IrisDataPipeline\iris_data -File).Count

# Check BigQuery table
# Via web console: https://console.cloud.google.com/bigquery
# Project: inner-cinema-476211-u9
# Dataset: uk_energy_prod
# Tables: bmrs_*_iris
```

### Health Monitoring Script: `check_pipeline_health.ps1`

```powershell
# C:\IrisDataPipeline\check_pipeline_health.ps1

$DataDir = "C:\IrisDataPipeline\iris_data"
$LogFile = "C:\IrisDataPipeline\logs\health_check.log"

function Write-HealthLog {
    param($Message)
    $Timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    "$Timestamp - $Message" | Tee-Object -FilePath $LogFile -Append
}

# Check 1: File accumulation (should be < 10,000)
$FileCount = (Get-ChildItem -Path $DataDir -File).Count
if ($FileCount -gt 10000) {
    Write-HealthLog "⚠️ WARNING: $FileCount files accumulated (threshold: 10,000)"
} else {
    Write-HealthLog "✅ File count OK: $FileCount"
}

# Check 2: Disk space (should be > 1GB free)
$Drive = Get-PSDrive C
$FreeSpaceGB = [math]::Round($Drive.Free / 1GB, 2)
if ($FreeSpaceGB -lt 1) {
    Write-HealthLog "🔴 CRITICAL: Only ${FreeSpaceGB}GB free on C:"
} else {
    Write-HealthLog "✅ Disk space OK: ${FreeSpaceGB}GB free"
}

# Check 3: Service running
$Service = Get-ScheduledTask -TaskName "IrisDataPipeline" -ErrorAction SilentlyContinue
if ($Service -and $Service.State -eq "Running") {
    Write-HealthLog "✅ Service running"
} else {
    Write-HealthLog "🔴 CRITICAL: Service not running"
}

# Check 4: Recent file creation (should be < 5 minutes ago)
$LatestFile = Get-ChildItem -Path $DataDir -File | Sort-Object LastWriteTime -Descending | Select-Object -First 1
if ($LatestFile) {
    $Age = (Get-Date) - $LatestFile.LastWriteTime
    if ($Age.TotalMinutes -gt 5) {
        Write-HealthLog "⚠️ WARNING: No new files in $([math]::Round($Age.TotalMinutes, 1)) minutes"
    } else {
        Write-HealthLog "✅ Recent file activity (< 5 minutes ago)"
    }
}
```

**Schedule health check every 15 minutes:**
```powershell
$Action = New-ScheduledTaskAction -Execute "PowerShell.exe" -Argument "-ExecutionPolicy Bypass -File C:\IrisDataPipeline\check_pipeline_health.ps1"
$Trigger = New-ScheduledTaskTrigger -Once -At (Get-Date) -RepetitionInterval (New-TimeSpan -Minutes 15) -RepetitionDuration ([TimeSpan]::MaxValue)
Register-ScheduledTask -TaskName "IrisHealthCheck" -Action $Action -Trigger $Trigger
```

---

## 🔄 Pipeline Flow

```
┌─────────────────────────────────────────────────────────────┐
│                     Windows Server                          │
│                  windows-1cpu-2gb-uk-lon1                   │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  STEP 1: Download (client.py)                              │
│  ┌──────────────────────────────────────┐                  │
│  │ Azure Service Bus (IRIS)             │                  │
│  │ ↓                                    │                  │
│  │ C:\IrisDataPipeline\iris_data\       │                  │
│  │ - BOD_20251031_170000.json           │                  │
│  │ - FUELINST_20251031_170030.json      │                  │
│  │ - FREQ_20251031_170100.json          │                  │
│  │ ... (accumulates for 5-15 minutes)   │                  │
│  └──────────────────────────────────────┘                  │
│               │                                             │
│               ↓                                             │
│  STEP 2: Batch Upload (iris_to_bigquery_unified.py)        │
│  ┌──────────────────────────────────────┐                  │
│  │ Read all JSON files                  │                  │
│  │ Parse by message type (BOD/FREQ/etc) │                  │
│  │ Batch insert to BigQuery             │                  │
│  │ → bmrs_bod_iris                      │                  │
│  │ → bmrs_fuelinst_iris                 │                  │
│  │ → bmrs_freq_iris                     │                  │
│  │ → bmrs_mid_iris                      │                  │
│  └──────────────────────────────────────┘                  │
│               │                                             │
│               ↓                                             │
│  STEP 3: Auto-Delete (after successful upload)             │
│  ┌──────────────────────────────────────┐                  │
│  │ Delete uploaded JSON files           │                  │
│  │ Free disk space                      │                  │
│  │ iris_data/ folder stays clean        │                  │
│  └──────────────────────────────────────┘                  │
│                                                             │
│  STEP 4: Repeat every 5-15 minutes                         │
│                                                             │
└─────────────────────────────────────────────────────────────┘
                            │
                            ↓
              ┌─────────────────────────────┐
              │   Google Cloud BigQuery     │
              │   inner-cinema-476211-u9    │
              │   uk_energy_prod dataset    │
              │                             │
              │   bmrs_bod_iris        ✅   │
              │   bmrs_fuelinst_iris   ✅   │
              │   bmrs_freq_iris       ✅   │
              │   bmrs_mid_iris        ✅   │
              │   (real-time, 30s-2min lag) │
              └─────────────────────────────┘
```

---

## ⚡ Performance Targets

| Metric | Target | Notes |
|--------|--------|-------|
| **Message Download** | 100-500 msgs/minute | From Azure Service Bus |
| **File Accumulation** | < 10,000 files | Before batch upload |
| **Upload Frequency** | Every 5-15 minutes | Configurable |
| **Files Deleted** | 100% after upload | Automatic cleanup |
| **Disk Usage** | < 500 MB | iris_data folder |
| **Data Latency** | 30 seconds - 15 minutes | End-to-end |
| **Uptime** | 99.9% | Auto-restart on failure |

---

## 🚨 Troubleshooting

### Problem: Files accumulating, not uploading

**Check:**
```powershell
# Is BigQuery uploader running?
Get-Process | Where-Object {$_.CommandLine -like "*iris_to_bigquery*"}

# Check logs
Get-Content C:\IrisDataPipeline\logs\pipeline.log -Tail 100

# Manual upload
python C:\IrisDataPipeline\scripts\iris_to_bigquery_unified.py --input-dir C:\IrisDataPipeline\iris_data --delete-after-upload
```

### Problem: IRIS client not downloading

**Check:**
```powershell
# Is client running?
Get-Process | Where-Object {$_.CommandLine -like "*client.py*"}

# Test connection
python C:\IrisDataPipeline\scripts\client.py --output-dir C:\IrisDataPipeline\iris_data --max-messages 10

# Check Azure credentials in client.py config
```

### Problem: BigQuery authentication error

**Fix:**
```powershell
# Re-authenticate
gcloud auth login
gcloud config set project inner-cinema-476211-u9

# Or use service account
$env:GOOGLE_APPLICATION_CREDENTIALS = "C:\IrisDataPipeline\service_account.json"
```

### Problem: Disk full

**Emergency cleanup:**
```powershell
# Delete old files (ONLY IF SAFE)
Remove-Item C:\IrisDataPipeline\iris_data\* -Force

# Check disk space
Get-PSDrive C
```

---

## 📝 Next Steps

1. **Connect to UpCloud server** via RDP
2. **Install Python + Google Cloud SDK**
3. **Upload pipeline scripts** from Mac
4. **Test manual execution** of each component
5. **Set up Windows Scheduled Task** or NSSM service
6. **Monitor for 24 hours** to verify stability
7. **Set up health check script**
8. **Document any server-specific configuration**

---

## 📚 Related Documentation

- `UNIFIED_ARCHITECTURE_HISTORICAL_AND_REALTIME.md` - Full pipeline architecture
- `DATA_FRESHNESS_ISSUE.md` - Why we need real-time IRIS data
- `README.md` - Main project documentation

---

**Created**: 31 October 2025  
**Target Server**: windows-1cpu-2gb-uk-lon1 (London)  
**Status**: Ready for deployment

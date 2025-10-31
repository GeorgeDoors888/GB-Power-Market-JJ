#!/bin/bash
# Package IRIS pipeline for Windows UpCloud server deployment

echo "======================================================================"
echo "📦 IRIS Pipeline Windows Deployment Package Creator"
echo "======================================================================"
echo ""

# Create package directory
PACKAGE_DIR="iris_windows_deployment"
echo "Creating package directory: $PACKAGE_DIR"
rm -rf "$PACKAGE_DIR"
mkdir -p "$PACKAGE_DIR/scripts"
mkdir -p "$PACKAGE_DIR/iris_data"
mkdir -p "$PACKAGE_DIR/logs"

echo "✅ Package structure created"
echo ""

# Check if IRIS client exists
if [ -d "$HOME/iris-clients" ]; then
    echo "📥 Found IRIS client at ~/iris-clients"
    
    # Copy IRIS client
    cp -r "$HOME/iris-clients/python" "$PACKAGE_DIR/iris_client"
    echo "✅ Copied IRIS client"
else
    echo "⚠️  IRIS client not found at ~/iris-clients"
    echo "   Expected location: ~/iris-clients/python/client.py"
    echo "   You'll need to copy this manually"
fi

echo ""

# Check if IRIS processor exists
IRIS_PROCESSOR="$HOME/iris_to_bigquery_unified.py"
if [ -f "$IRIS_PROCESSOR" ]; then
    echo "📥 Found IRIS processor at ~/iris_to_bigquery_unified.py"
    cp "$IRIS_PROCESSOR" "$PACKAGE_DIR/scripts/"
    echo "✅ Copied IRIS processor"
elif [ -f "./iris_to_bigquery_unified.py" ]; then
    echo "📥 Found IRIS processor in current directory"
    cp "./iris_to_bigquery_unified.py" "$PACKAGE_DIR/scripts/"
    echo "✅ Copied IRIS processor"
else
    echo "⚠️  IRIS processor not found"
    echo "   Expected: ~/iris_to_bigquery_unified.py"
    echo "   You'll need to copy this manually"
fi

echo ""

# Create requirements.txt
echo "📝 Creating requirements.txt"
cat > "$PACKAGE_DIR/scripts/requirements.txt" << 'EOF'
# Google Cloud
google-cloud-bigquery==3.38.0
google-cloud-storage
db-dtypes==1.4.3

# Azure (IRIS)
azure-servicebus==7.13.0
azure-identity==1.19.0
dacite==1.8.1

# Data processing
pandas==2.3.2
numpy==2.0.2
pyarrow==21.0.0

# Utilities
python-dotenv==1.0.0
EOF

echo "✅ Created requirements.txt"
echo ""

# Create Windows startup script
echo "📝 Creating Windows PowerShell scripts"

cat > "$PACKAGE_DIR/start_iris_pipeline.ps1" << 'EOF'
# IRIS Pipeline Startup Script for Windows
# C:\IrisDataPipeline\start_iris_pipeline.ps1

$ErrorActionPreference = "Stop"
$LogFile = "C:\IrisDataPipeline\logs\pipeline.log"
$ScriptDir = "C:\IrisDataPipeline\scripts"
$DataDir = "C:\IrisDataPipeline\iris_data"

function Write-Log {
    param($Message)
    $Timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $LogMessage = "$Timestamp - $Message"
    Write-Host $LogMessage
    $LogMessage | Out-File -FilePath $LogFile -Append -Encoding UTF8
}

Write-Log "===== IRIS Pipeline Starting ====="
Write-Log "Script Dir: $ScriptDir"
Write-Log "Data Dir: $DataDir"

# Check Python
try {
    $PythonVersion = python --version 2>&1
    Write-Log "Python: $PythonVersion"
} catch {
    Write-Log "ERROR: Python not found. Install Python 3.11+"
    exit 1
}

# Start IRIS client (download messages continuously)
Write-Log "Starting IRIS client..."
$ClientArgs = "iris_client\client.py --output-dir $DataDir --continuous --log-file $LogFile"
$ClientProcess = Start-Process python -ArgumentList $ClientArgs -WorkingDirectory "$ScriptDir\.." -PassThru -WindowStyle Hidden

Write-Log "IRIS Client started (PID: $($ClientProcess.Id))"

# Wait for initial messages
Write-Log "Waiting 60 seconds for initial messages..."
Start-Sleep -Seconds 60

# Main upload loop (every 5 minutes)
Write-Log "Starting upload loop (5-minute intervals)..."
$LoopCount = 0

while ($true) {
    $LoopCount++
    Write-Log "===== Upload Loop #$LoopCount ====="
    
    try {
        # Count files before upload
        $FilesBefore = @(Get-ChildItem -Path $DataDir -File -ErrorAction SilentlyContinue).Count
        Write-Log "Files before upload: $FilesBefore"
        
        if ($FilesBefore -gt 0) {
            # Run BigQuery uploader
            Write-Log "Starting BigQuery upload..."
            python "$ScriptDir\iris_to_bigquery_unified.py" `
                --input-dir "$DataDir" `
                --delete-after-upload `
                --batch-size 1000 `
                --log-level INFO
            
            # Count files after upload
            $FilesAfter = @(Get-ChildItem -Path $DataDir -File -ErrorAction SilentlyContinue).Count
            $FilesProcessed = $FilesBefore - $FilesAfter
            Write-Log "Upload complete. Files processed: $FilesProcessed, Remaining: $FilesAfter"
        } else {
            Write-Log "No files to upload"
        }
        
        # Check if client is still running
        if ($ClientProcess.HasExited) {
            Write-Log "WARNING: Client process died (Exit code: $($ClientProcess.ExitCode)). Restarting..."
            $ClientProcess = Start-Process python -ArgumentList $ClientArgs -WorkingDirectory "$ScriptDir\.." -PassThru -WindowStyle Hidden
            Write-Log "Client restarted (PID: $($ClientProcess.Id))"
        } else {
            Write-Log "Client still running (PID: $($ClientProcess.Id))"
        }
        
    } catch {
        Write-Log "ERROR: $($_.Exception.Message)"
        Write-Log "Stack: $($_.ScriptStackTrace)"
    }
    
    # Wait 5 minutes (300 seconds)
    Write-Log "Waiting 5 minutes until next upload..."
    Start-Sleep -Seconds 300
}
EOF

cat > "$PACKAGE_DIR/install_service.ps1" << 'EOF'
# Install IRIS Pipeline as Windows Service using Task Scheduler
# Run this as Administrator

$TaskName = "IrisDataPipeline"
$ScriptPath = "C:\IrisDataPipeline\start_iris_pipeline.ps1"

Write-Host "Installing IRIS Pipeline as Windows Service..."

# Check if task exists
$ExistingTask = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
if ($ExistingTask) {
    Write-Host "Removing existing task..."
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
}

# Create action
$Action = New-ScheduledTaskAction `
    -Execute "PowerShell.exe" `
    -Argument "-ExecutionPolicy Bypass -NoProfile -WindowStyle Hidden -File $ScriptPath"

# Create trigger (at startup)
$Trigger = New-ScheduledTaskTrigger -AtStartup

# Create settings
$Settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -RestartInterval (New-TimeSpan -Minutes 1) `
    -RestartCount 3 `
    -ExecutionTimeLimit (New-TimeSpan -Days 365)

# Create principal (run as SYSTEM)
$Principal = New-ScheduledTaskPrincipal `
    -UserId "SYSTEM" `
    -LogonType ServiceAccount `
    -RunLevel Highest

# Register task
Register-ScheduledTask `
    -TaskName $TaskName `
    -Action $Action `
    -Trigger $Trigger `
    -Settings $Settings `
    -Principal $Principal `
    -Description "IRIS real-time data ingestion to BigQuery with auto-delete"

Write-Host "✅ Service installed successfully!"
Write-Host ""
Write-Host "To start the service:"
Write-Host "  Start-ScheduledTask -TaskName $TaskName"
Write-Host ""
Write-Host "To check status:"
Write-Host "  Get-ScheduledTask -TaskName $TaskName"
Write-Host ""
Write-Host "To view logs:"
Write-Host "  Get-Content C:\IrisDataPipeline\logs\pipeline.log -Tail 50 -Wait"
EOF

cat > "$PACKAGE_DIR/check_health.ps1" << 'EOF'
# Health check script for IRIS Pipeline
# Run this to check if everything is working

$DataDir = "C:\IrisDataPipeline\iris_data"
$LogFile = "C:\IrisDataPipeline\logs\pipeline.log"

Write-Host "======================================================================"
Write-Host "🏥 IRIS Pipeline Health Check"
Write-Host "======================================================================"
Write-Host ""

# Check 1: Service running
Write-Host "1. Checking service status..."
$Task = Get-ScheduledTask -TaskName "IrisDataPipeline" -ErrorAction SilentlyContinue
if ($Task) {
    Write-Host "   Status: $($Task.State)"
    if ($Task.State -eq "Running") {
        Write-Host "   ✅ Service is running"
    } else {
        Write-Host "   ❌ Service is NOT running"
        Write-Host "   Start with: Start-ScheduledTask -TaskName IrisDataPipeline"
    }
} else {
    Write-Host "   ❌ Service not installed"
}
Write-Host ""

# Check 2: File count
Write-Host "2. Checking file accumulation..."
$Files = @(Get-ChildItem -Path $DataDir -File -ErrorAction SilentlyContinue)
$FileCount = $Files.Count
Write-Host "   Files in iris_data: $FileCount"
if ($FileCount -lt 10000) {
    Write-Host "   ✅ File count is healthy"
} else {
    Write-Host "   ⚠️  WARNING: Too many files accumulated"
}
Write-Host ""

# Check 3: Recent file activity
Write-Host "3. Checking recent activity..."
if ($Files.Count -gt 0) {
    $LatestFile = $Files | Sort-Object LastWriteTime -Descending | Select-Object -First 1
    $Age = (Get-Date) - $LatestFile.LastWriteTime
    Write-Host "   Latest file: $($LatestFile.Name)"
    Write-Host "   Age: $([math]::Round($Age.TotalMinutes, 1)) minutes ago"
    if ($Age.TotalMinutes -lt 5) {
        Write-Host "   ✅ Recent file activity detected"
    } else {
        Write-Host "   ⚠️  WARNING: No new files in $([math]::Round($Age.TotalMinutes, 1)) minutes"
    }
} else {
    Write-Host "   No files found in iris_data folder"
}
Write-Host ""

# Check 4: Disk space
Write-Host "4. Checking disk space..."
$Drive = Get-PSDrive C
$FreeSpaceGB = [math]::Round($Drive.Free / 1GB, 2)
Write-Host "   Free space on C: ${FreeSpaceGB}GB"
if ($FreeSpaceGB -gt 1) {
    Write-Host "   ✅ Disk space OK"
} else {
    Write-Host "   ❌ CRITICAL: Low disk space!"
}
Write-Host ""

# Check 5: Recent log entries
Write-Host "5. Recent log entries (last 10 lines):"
if (Test-Path $LogFile) {
    Get-Content $LogFile -Tail 10 | ForEach-Object { Write-Host "   $_" }
} else {
    Write-Host "   Log file not found at: $LogFile"
}
Write-Host ""

Write-Host "======================================================================"
Write-Host "Health check complete"
Write-Host "======================================================================"
EOF

echo "✅ Created PowerShell scripts"
echo ""

# Create README
echo "📝 Creating deployment README"
cat > "$PACKAGE_DIR/README.txt" << 'EOF'
IRIS Pipeline - Windows Server Deployment Package
==================================================

This package contains everything needed to deploy the IRIS real-time
data pipeline on your Windows UpCloud server.

CONTENTS:
---------
scripts/                     - Python scripts
  ├── client.py             - IRIS message downloader
  ├── iris_to_bigquery_unified.py - BigQuery uploader
  └── requirements.txt      - Python dependencies

iris_data/                   - Downloaded messages (initially empty)
logs/                        - Log files (created automatically)
start_iris_pipeline.ps1      - Main startup script
install_service.ps1          - Install as Windows service
check_health.ps1             - Health check script

INSTALLATION:
-------------
1. Copy entire folder to: C:\IrisDataPipeline

2. Install Python 3.11+ from: https://www.python.org/downloads/

3. Install Google Cloud SDK from: 
   https://cloud.google.com/sdk/docs/install#windows

4. Open PowerShell as Administrator and run:
   cd C:\IrisDataPipeline
   pip install -r scripts\requirements.txt
   
5. Authenticate with Google Cloud:
   gcloud auth login
   gcloud config set project inner-cinema-476211-u9

6. Test manually:
   .\start_iris_pipeline.ps1
   (Press Ctrl+C after 5 minutes to stop)

7. Install as service:
   .\install_service.ps1

8. Start service:
   Start-ScheduledTask -TaskName IrisDataPipeline

9. Check health:
   .\check_health.ps1

MONITORING:
-----------
View logs in real-time:
  Get-Content logs\pipeline.log -Tail 50 -Wait

Check service status:
  Get-ScheduledTask -TaskName IrisDataPipeline

Check file count:
  (Get-ChildItem iris_data -File).Count

TROUBLESHOOTING:
----------------
If files accumulate (>10,000):
  - Check logs for upload errors
  - Verify BigQuery authentication
  - Manually run: python scripts\iris_to_bigquery_unified.py --input-dir iris_data

If no files downloading:
  - Check IRIS client configuration
  - Verify Azure Service Bus credentials
  - Test: python scripts\client.py --max-messages 10

SERVICE CONTROL:
----------------
Start:  Start-ScheduledTask -TaskName IrisDataPipeline
Stop:   Stop-ScheduledTask -TaskName IrisDataPipeline
Remove: Unregister-ScheduledTask -TaskName IrisDataPipeline

SUPPORT:
--------
See UPCLOUD_DEPLOYMENT_PLAN.md for detailed documentation
Server: windows-1cpu-2gb-uk-lon1
Password: T8hz5AQS2H9jHdsK
EOF

echo "✅ Created README.txt"
echo ""

# Create ZIP archive
echo "📦 Creating ZIP archive..."
if command -v zip &> /dev/null; then
    zip -r "${PACKAGE_DIR}.zip" "$PACKAGE_DIR"
    echo "✅ Created ${PACKAGE_DIR}.zip"
else
    echo "⚠️  'zip' command not found. You can zip manually or use macOS Finder"
fi

echo ""
echo "======================================================================"
echo "✅ Package created successfully!"
echo "======================================================================"
echo ""
echo "📁 Package location: ./$PACKAGE_DIR"
if [ -f "${PACKAGE_DIR}.zip" ]; then
    echo "📦 ZIP archive: ./${PACKAGE_DIR}.zip"
fi
echo ""
echo "📋 Next steps:"
echo "1. Upload ${PACKAGE_DIR}.zip to Windows server via RDP"
echo "2. Extract to C:\IrisDataPipeline"
echo "3. Follow instructions in README.txt"
echo ""
echo "🔗 Server details:"
echo "   Hostname: windows-1cpu-2gb-uk-lon1"
echo "   Password: T8hz5AQS2H9jHdsK"
echo ""

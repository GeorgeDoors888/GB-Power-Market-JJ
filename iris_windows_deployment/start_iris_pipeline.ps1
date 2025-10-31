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

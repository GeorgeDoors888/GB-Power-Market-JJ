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

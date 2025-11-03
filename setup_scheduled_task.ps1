# PowerShell Script to Set Up Windows Task Scheduler for Automated Map Generation
# Run as Administrator on Windows UpCloud server

Write-Host "=== Setting Up Scheduled Task for GB Power Map ===" -ForegroundColor Green

# Task configuration
$taskName = "Generate GB Power Map"
$taskDescription = "Automatically generates the GB power system map every 30 minutes using latest BigQuery data"
$scriptPath = "C:\maps\scripts\auto_generate_map.py"
$pythonPath = "python"  # Adjust if Python is in a specific location

# Check if Python is available
Write-Host "`nStep 1: Checking Python installation..." -ForegroundColor Yellow
try {
    $pythonVersion = & python --version 2>&1
    Write-Host "Found: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "ERROR: Python not found in PATH" -ForegroundColor Red
    Write-Host "Please install Python or update PATH" -ForegroundColor Yellow
    exit 1
}

# Check if script exists
Write-Host "`nStep 2: Checking script file..." -ForegroundColor Yellow
if (Test-Path $scriptPath) {
    Write-Host "Found: $scriptPath" -ForegroundColor Green
} else {
    Write-Host "ERROR: Script not found at $scriptPath" -ForegroundColor Red
    Write-Host "Please copy auto_generate_map.py to C:\maps\scripts\" -ForegroundColor Yellow
    exit 1
}

# Remove existing task if it exists
Write-Host "`nStep 3: Checking for existing task..." -ForegroundColor Yellow
$existingTask = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
if ($existingTask) {
    Write-Host "Removing existing task..." -ForegroundColor Yellow
    Unregister-ScheduledTask -TaskName $taskName -Confirm:$false
}

# Create scheduled task action
Write-Host "`nStep 4: Creating scheduled task..." -ForegroundColor Yellow
$action = New-ScheduledTaskAction `
    -Execute $pythonPath `
    -Argument $scriptPath `
    -WorkingDirectory "C:\maps\scripts"

# Create trigger - every 30 minutes
$trigger = New-ScheduledTaskTrigger `
    -Once `
    -At (Get-Date) `
    -RepetitionInterval (New-TimeSpan -Minutes 30) `
    -RepetitionDuration ([TimeSpan]::MaxValue)

# Create settings
$settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -RunOnlyIfNetworkAvailable `
    -MultipleInstances IgnoreNew

# Register the task
Register-ScheduledTask `
    -TaskName $taskName `
    -Description $taskDescription `
    -Action $action `
    -Trigger $trigger `
    -Settings $settings `
    -User "SYSTEM" `
    -RunLevel Highest

Write-Host "Scheduled task created successfully!" -ForegroundColor Green

# Display task information
Write-Host "`n=== Task Information ===" -ForegroundColor Cyan
$task = Get-ScheduledTask -TaskName $taskName
Write-Host "Task Name: $($task.TaskName)" -ForegroundColor White
Write-Host "State: $($task.State)" -ForegroundColor White
Write-Host "Schedule: Every 30 minutes" -ForegroundColor White
Write-Host "Script: $scriptPath" -ForegroundColor White

# Test run the task
Write-Host "`n=== Testing Task ===" -ForegroundColor Cyan
Write-Host "Running task manually to test..." -ForegroundColor Yellow
Start-ScheduledTask -TaskName $taskName

# Wait a few seconds
Start-Sleep -Seconds 5

# Check task status
$taskInfo = Get-ScheduledTaskInfo -TaskName $taskName
Write-Host "Last Run Time: $($taskInfo.LastRunTime)" -ForegroundColor White
Write-Host "Last Result: $($taskInfo.LastTaskResult)" -ForegroundColor White
Write-Host "Next Run Time: $($taskInfo.NextRunTime)" -ForegroundColor White

# Check if map was generated
Write-Host "`n=== Checking Output ===" -ForegroundColor Cyan
$mapFile = "C:\inetpub\wwwroot\gb_power_complete_map.html"
if (Test-Path $mapFile) {
    $fileInfo = Get-Item $mapFile
    Write-Host "Map file created: $mapFile" -ForegroundColor Green
    Write-Host "Size: $([math]::Round($fileInfo.Length / 1MB, 2)) MB" -ForegroundColor White
    Write-Host "Last Modified: $($fileInfo.LastWriteTime)" -ForegroundColor White
} else {
    Write-Host "WARNING: Map file not found at $mapFile" -ForegroundColor Yellow
    Write-Host "Check logs at C:\maps\logs\" -ForegroundColor Yellow
}

# Check log file
$logDir = "C:\maps\logs"
$todayLog = Join-Path $logDir "map_generation_$(Get-Date -Format 'yyyyMMdd').log"
if (Test-Path $todayLog) {
    Write-Host "`nLatest log entries:" -ForegroundColor Cyan
    Get-Content $todayLog -Tail 10 | ForEach-Object { Write-Host $_ -ForegroundColor Gray }
}

Write-Host "`n=== Setup Complete ===" -ForegroundColor Green
Write-Host "`nThe map will now be automatically generated every 30 minutes." -ForegroundColor White
Write-Host "View logs at: C:\maps\logs\" -ForegroundColor White
Write-Host "View map at: http://localhost/gb_power_complete_map.html" -ForegroundColor White

# Get public IP
try {
    $publicIP = (Invoke-WebRequest -Uri "http://ifconfig.me/ip" -UseBasicParsing).Content.Trim()
    Write-Host "Public URL: http://$publicIP/gb_power_complete_map.html" -ForegroundColor Yellow
} catch {
    Write-Host "Public IP: 94.237.72.132 (from UpCloud)" -ForegroundColor Yellow
    Write-Host "Public URL: http://94.237.72.132/gb_power_complete_map.html" -ForegroundColor Yellow
}

Write-Host "`nTo view task in Task Scheduler:" -ForegroundColor Cyan
Write-Host "1. Open Task Scheduler (taskschd.msc)" -ForegroundColor White
Write-Host "2. Look for '$taskName' in Task Scheduler Library" -ForegroundColor White
Write-Host "3. Right-click to Run, Edit, or Disable" -ForegroundColor White

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

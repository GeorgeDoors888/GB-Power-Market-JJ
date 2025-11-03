# PowerShell Script to Set Up IIS Web Server for GB Power Map
# Run as Administrator on Windows UpCloud server

Write-Host "=== Setting Up IIS Web Server for GB Power Map ===" -ForegroundColor Green

# Install IIS if not already installed
Write-Host "`nStep 1: Installing IIS..." -ForegroundColor Yellow
Install-WindowsFeature -Name Web-Server -IncludeManagementTools

# Verify IIS is running
$iisService = Get-Service -Name W3SVC
if ($iisService.Status -eq "Running") {
    Write-Host "IIS is running successfully" -ForegroundColor Green
} else {
    Start-Service W3SVC
    Write-Host "Started IIS service" -ForegroundColor Green
}

# Create maps directory structure
Write-Host "`nStep 2: Creating directory structure..." -ForegroundColor Yellow
$mapsDir = "C:\maps"
$dataDir = "C:\maps\data"
$logsDir = "C:\maps\logs"
$scriptsDir = "C:\maps\scripts"

@($mapsDir, $dataDir, $logsDir, $scriptsDir) | ForEach-Object {
    if (-not (Test-Path $_)) {
        New-Item -Path $_ -ItemType Directory -Force
        Write-Host "Created: $_" -ForegroundColor Green
    } else {
        Write-Host "Already exists: $_" -ForegroundColor Gray
    }
}

# Configure IIS to serve the map
Write-Host "`nStep 3: Configuring IIS..." -ForegroundColor Yellow

# Set default document
Set-WebConfigurationProperty -Filter "//defaultDocument/files" -PSPath "IIS:\Sites\Default Web Site" -Name "Collection" -Value @{value='gb_power_complete_map.html'}

# Enable directory browsing (optional)
Set-WebConfigurationProperty -Filter /system.webServer/directoryBrowse -PSPath "IIS:\Sites\Default Web Site" -Name enabled -Value $false

# Configure MIME types for JSON files (if needed)
Add-WebConfigurationProperty -PSPath "IIS:\Sites\Default Web Site" -Filter "system.webServer/staticContent" -Name "." -Value @{fileExtension='.json'; mimeType='application/json'} -ErrorAction SilentlyContinue

Write-Host "IIS configured successfully" -ForegroundColor Green

# Configure Windows Firewall
Write-Host "`nStep 4: Configuring firewall..." -ForegroundColor Yellow
$firewallRule = Get-NetFirewallRule -DisplayName "Allow HTTP" -ErrorAction SilentlyContinue
if (-not $firewallRule) {
    New-NetFirewallRule -DisplayName "Allow HTTP" -Direction Inbound -LocalPort 80 -Protocol TCP -Action Allow
    Write-Host "Firewall rule created for HTTP (port 80)" -ForegroundColor Green
} else {
    Write-Host "Firewall rule already exists" -ForegroundColor Gray
}

# Test web server
Write-Host "`nStep 5: Testing web server..." -ForegroundColor Yellow
$testFile = "C:\inetpub\wwwroot\test.html"
"<html><body><h1>IIS is working!</h1></body></html>" | Out-File -FilePath $testFile -Encoding utf8

try {
    $response = Invoke-WebRequest -Uri "http://localhost/test.html" -UseBasicParsing
    if ($response.StatusCode -eq 200) {
        Write-Host "Web server test successful!" -ForegroundColor Green
    }
} catch {
    Write-Host "Warning: Could not test web server - $($_.Exception.Message)" -ForegroundColor Yellow
}

# Display server information
Write-Host "`n=== Server Information ===" -ForegroundColor Cyan
Write-Host "Web Root: C:\inetpub\wwwroot" -ForegroundColor White
Write-Host "Maps Directory: C:\maps" -ForegroundColor White
Write-Host "Local URL: http://localhost/gb_power_complete_map.html" -ForegroundColor White

# Get public IP
try {
    $publicIP = (Invoke-WebRequest -Uri "http://ifconfig.me/ip" -UseBasicParsing).Content.Trim()
    Write-Host "Public URL: http://$publicIP/gb_power_complete_map.html" -ForegroundColor Yellow
} catch {
    Write-Host "Public IP: Unable to detect (check UpCloud dashboard)" -ForegroundColor Yellow
}

Write-Host "`n=== IIS Setup Complete ===" -ForegroundColor Green
Write-Host "`nNext Steps:" -ForegroundColor Cyan
Write-Host "1. Copy auto_generate_map.py to C:\maps\scripts\" -ForegroundColor White
Write-Host "2. Copy dno_regions.geojson to C:\maps\data\" -ForegroundColor White
Write-Host "3. Install Python packages: pip install google-cloud-bigquery" -ForegroundColor White
Write-Host "4. Configure BigQuery credentials" -ForegroundColor White
Write-Host "5. Run: python C:\maps\scripts\auto_generate_map.py" -ForegroundColor White
Write-Host "6. Set up Windows Task Scheduler (see setup_scheduled_task.ps1)" -ForegroundColor White

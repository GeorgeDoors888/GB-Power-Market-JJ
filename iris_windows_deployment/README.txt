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

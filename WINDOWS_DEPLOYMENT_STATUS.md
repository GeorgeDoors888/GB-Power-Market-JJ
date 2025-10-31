# ✅ Windows UpCloud Deployment Package - Ready

## Package Created Successfully

**Date**: 31 October 2025  
**Location**: `./iris_windows_deployment.zip`  
**Size**: ~5KB (scripts only, IRIS client code needs to be added manually)

---

## 📦 What's in the Package

```
iris_windows_deployment/
├── README.txt                      # Installation instructions
├── scripts/
│   └── requirements.txt            # Python dependencies
├── iris_data/                      # Empty (for downloaded messages)
├── logs/                           # Empty (for log files)
├── start_iris_pipeline.ps1         # Main startup script
├── install_service.ps1             # Service installer
└── check_health.ps1                # Health monitoring
```

---

## ⚠️ Missing Components (Need to Add Manually)

The script couldn't find these files on your Mac. You'll need to locate and add them:

### 1. IRIS Client (`client.py`)
**Expected location**: `~/iris-clients/python/client.py`  
**What it does**: Downloads messages from Azure Service Bus  
**Size**: ~2-5 MB (includes dependencies)

**How to find it:**
```bash
# Search your Mac
find ~ -name "client.py" -path "*/iris-clients/*" 2>/dev/null

# Or search for iris-clients directory
find ~ -type d -name "iris-clients" 2>/dev/null
```

### 2. IRIS Processor (`iris_to_bigquery_unified.py`)
**Expected location**: `~/iris_to_bigquery_unified.py`  
**What it does**: Uploads JSON files to BigQuery and deletes them  
**Size**: ~50-100 KB

**How to find it:**
```bash
# Search your Mac
find ~ -name "iris_to_bigquery_unified.py" 2>/dev/null

# Or search for any iris*bigquery* files
find ~ -name "*iris*bigquery*.py" 2>/dev/null
```

---

## 🔄 How to Complete the Package

### Option 1: Add Files Locally, Then Re-zip

```bash
cd "GB Power Market JJ"

# Copy IRIS client (once you find it)
cp -r ~/path/to/iris-clients/python iris_windows_deployment/iris_client

# Copy IRIS processor (once you find it)
cp ~/path/to/iris_to_bigquery_unified.py iris_windows_deployment/scripts/

# Re-create ZIP
rm iris_windows_deployment.zip
zip -r iris_windows_deployment.zip iris_windows_deployment

# Upload to Windows server
```

### Option 2: Add Files Directly on Windows Server

1. Upload current `iris_windows_deployment.zip` to Windows server
2. Extract to `C:\IrisDataPipeline`
3. Separately copy IRIS scripts via RDP:
   - `iris_client/` folder → `C:\IrisDataPipeline\iris_client\`
   - `iris_to_bigquery_unified.py` → `C:\IrisDataPipeline\scripts\`

---

## 🚀 Deployment Steps on Windows Server

### 1. Connect via RDP

```
Server: windows-1cpu-2gb-uk-lon1
Username: Administrator  
Password: T8hz5AQS2H9jHdsK
```

### 2. Upload Package

- Copy `iris_windows_deployment.zip` to server (via RDP drag-and-drop)
- Extract to `C:\IrisDataPipeline`

### 3. Install Prerequisites

**Python 3.11+:**
- Download from: https://www.python.org/downloads/
- ✅ Check "Add to PATH"
- ✅ Include pip

**Google Cloud SDK:**
- Download from: https://cloud.google.com/sdk/docs/install#windows
- Run: `gcloud init`
- Login: `gcloud auth login`
- Set project: `gcloud config set project inner-cinema-476211-u9`

### 4. Install Python Packages

```powershell
cd C:\IrisDataPipeline
pip install -r scripts\requirements.txt
```

### 5. Test Components

```powershell
# Test IRIS client (download 10 messages)
python iris_client\client.py --output-dir iris_data --max-messages 10

# Check if files downloaded
Get-ChildItem iris_data

# Test BigQuery uploader
python scripts\iris_to_bigquery_unified.py --input-dir iris_data --delete-after-upload

# Check if files deleted
Get-ChildItem iris_data  # Should be empty
```

### 6. Install as Service

```powershell
# Run as Administrator
.\install_service.ps1

# Start service
Start-ScheduledTask -TaskName IrisDataPipeline

# Check status
Get-ScheduledTask -TaskName IrisDataPipeline
```

### 7. Monitor

```powershell
# View logs in real-time
Get-Content logs\pipeline.log -Tail 50 -Wait

# Check health
.\check_health.ps1

# View file count
(Get-ChildItem iris_data -File).Count  # Should stay < 10,000
```

---

## 📊 How It Works

```
┌─────────────────────────────────────────────────────┐
│             Windows Server (Every 5 min)            │
├─────────────────────────────────────────────────────┤
│                                                     │
│  1. IRIS Client (Continuous)                       │
│     Azure Service Bus → iris_data/ (JSON files)    │
│                                                     │
│  2. BigQuery Uploader (Every 5 minutes)            │
│     iris_data/*.json → BigQuery → Delete files     │
│                                                     │
│  3. Auto-Restart on Failure                        │
│     Monitors client, restarts if crashed           │
│                                                     │
└─────────────────────────────────────────────────────┘
                        ↓
        ┌───────────────────────────────┐
        │   Google Cloud BigQuery       │
        │   inner-cinema-476211-u9      │
        │                               │
        │   bmrs_bod_iris        ✅    │
        │   bmrs_fuelinst_iris   ✅    │
        │   bmrs_freq_iris       ✅    │
        │   bmrs_mid_iris        ✅    │
        │   (Real-time, 5-15 min lag)   │
        └───────────────────────────────┘
```

---

## 🎯 Expected Behavior

| Metric | Expected Value | What It Means |
|--------|---------------|---------------|
| **Files in iris_data/** | 0 - 10,000 | Downloading then deleting |
| **Upload frequency** | Every 5 minutes | Configurable |
| **Files deleted** | 100% after upload | Disk space management |
| **Data latency** | 5-15 minutes | End-to-end |
| **Service uptime** | 99.9%+ | Auto-restart enabled |

---

## 🔍 Where to Find IRIS Scripts

Since the scripts weren't found automatically, here are likely locations:

### Check Your Mac

```bash
# Find IRIS client
ls -la ~/iris-clients/python/client.py
ls -la ~/Downloads/iris-clients/python/client.py
ls -la ~/Documents/iris-clients/python/client.py

# Find IRIS processor
ls -la ~/iris_to_bigquery_unified.py
ls -la ~/Downloads/iris_to_bigquery_unified.py
ls -la ~/GB\ Power\ Market\ JJ/iris_to_bigquery_unified.py

# Search everywhere
mdfind -name "iris_to_bigquery_unified.py"
mdfind -name "client.py" | grep iris
```

### Check Your Server (if already deployed)

You mentioned this was "implemented yesterday". The scripts might already be on the UpCloud server or another server:

```bash
# If scripts are on another server, copy from there
# Then upload to Windows server
```

---

## 📚 Documentation References

- **Full deployment guide**: `UPCLOUD_DEPLOYMENT_PLAN.md`
- **Architecture docs**: `UNIFIED_ARCHITECTURE_HISTORICAL_AND_REALTIME.md`
- **Data freshness issue**: `DATA_FRESHNESS_ISSUE.md`
- **Main README**: `README.md`

---

## ✅ Checklist

Before deploying to Windows server:

- [ ] Located `iris-clients/python/client.py`
- [ ] Located `iris_to_bigquery_unified.py`
- [ ] Added scripts to package
- [ ] Re-zipped package
- [ ] Uploaded to Windows server
- [ ] Installed Python 3.11+
- [ ] Installed Google Cloud SDK
- [ ] Authenticated with `gcloud auth login`
- [ ] Installed Python requirements
- [ ] Tested IRIS client download
- [ ] Tested BigQuery upload
- [ ] Installed as Windows service
- [ ] Started service
- [ ] Monitored for 1 hour
- [ ] Verified auto-delete working
- [ ] Set up health check schedule

---

## 🆘 Need Help?

**If IRIS scripts are missing:**
1. Check if pipeline is already running on another server
2. Contact whoever set up the IRIS pipeline yesterday
3. Scripts should be in the server where IRIS is currently running

**If you can't find the scripts:**
- Let me know and I can help recreate them based on the documentation
- The architecture is fully documented in `UNIFIED_ARCHITECTURE_HISTORICAL_AND_REALTIME.md`

---

**Status**: Package created, waiting for IRIS scripts to be added  
**Next**: Locate IRIS scripts, add to package, deploy to Windows server

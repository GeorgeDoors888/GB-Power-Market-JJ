# 🤖 ChatGPT Integration & UpCloud Deployment - Complete Guide

**Last Updated**: November 6, 2025  
**Status**: ✅ All Systems Operational

---

## 📋 Table of Contents

1. [ChatGPT Integrations Overview](#chatgpt-integrations-overview)
2. [UpCloud Server Infrastructure](#upcloud-server-infrastructure)
3. [Integration Details](#integration-details)
4. [Deployment Guides](#deployment-guides)
5. [Management & Operations](#management--operations)
6. [Troubleshooting](#troubleshooting)

---

## 🤖 ChatGPT Integrations Overview

You have **4 distinct ChatGPT integrations** configured in your GB Power Market JJ system:

### 1️⃣ **Google Drive OAuth Connection** ✅

**Purpose**: Access Google Drive/Sheets directly within ChatGPT conversations

**What It Does**:
- Read Google Drive files in ChatGPT
- Access Google Sheets data
- View Google Docs content
- List and browse your files
- Interactive file queries

**Status**: ✅ Configured and ready to use

**How to Use**:
```
In ChatGPT: "Can you list files from my Google Drive?"
In ChatGPT: "Read my power dashboard sheet 12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8"
In ChatGPT: "What's the current renewable percentage?"
```

**Setup Process**:
1. Go to ChatGPT Settings → Data Controls
2. Connect Google Drive
3. Authorize with `george@upowerenergy.uk`
4. Grant permissions (Drive, Sheets, Docs)

**Authentication**: OAuth 2.0 (personal account)

**Documentation**: `FIX_CHATGPT_OAUTH.md`

**Common Issue**: "There was a problem syncing GitHub" error
- **Misleading message** - actually about Google Drive OAuth, not GitHub
- **Fix**: Remove old connection at myaccount.google.com/permissions, reconnect
- **Alternative**: Use service account exports to Google Sheets

**What ChatGPT CAN Do**:
- ✅ Read files (read-only access)
- ✅ Access Sheets/Docs
- ✅ List Drive contents

**What ChatGPT CANNOT Do**:
- ❌ Modify or delete files
- ❌ Access files not owned by you
- ❌ Share files
- ❌ Change permissions

---

### 2️⃣ **GitHub Integration** ✅

**Purpose**: Secure code management workflow with ChatGPT guidance

**What It Does**:
- ChatGPT provides code/solutions
- You save files locally
- Push to GitHub with authenticated access
- Token stays on YOUR Mac only

**Status**: ✅ Fully configured (November 2, 2025)

**Workflow**:
```
1. Ask ChatGPT for code
   ↓
2. ChatGPT provides solution
   ↓
3. Save file locally (VS Code/Copilot)
   ↓
4. Push to GitHub: ./quick-push.sh "Description"
   ↓
5. Continue with ChatGPT: "I pushed it, can you add X?"
```

**Quick Commands**:
```bash
# Easy push
./quick-push.sh "Added feature from ChatGPT"

# Check auth status
gh auth status

# View repo on GitHub
gh repo view --web

# Manual git (if needed)
git add .
git commit -m "message"
git push
```

**Security Model**:
- ⚠️ ChatGPT **cannot** accept or store GitHub tokens (by design)
- ✅ Token stored securely in macOS keyring
- ✅ Full write access to repositories
- ✅ ChatGPT provides guidance only

**Files Created**:
- ✅ `quick-push.sh` - One-command commit and push
- ✅ GitHub CLI authenticated on your Mac

**Documentation**: `CHATGPT_SETUP_COMPLETE.md`, `CHATGPT_GITHUB_FIX.md`

**Common Issues**:

**Issue 1**: "Access Denied" or "403 Forbidden"
- **Cause**: ChatGPT GitHub App not installed
- **Fix**: Install at https://github.com/apps/chatgpt
- **Steps**: 
  1. Visit github.com/apps/chatgpt
  2. Click "Install"
  3. Grant access to repositories
  4. Re-authenticate in ChatGPT

**Issue 2**: "Repository Not Found" 
- **Cause**: Private repo not shared with ChatGPT
- **Fix**: github.com/settings/installations → ChatGPT → Configure
- Grant repository access

**Issue 3**: "Authentication Required"
- **Cause**: OAuth token expired
- **Fix**: ChatGPT Settings → Remove GitHub → Re-add connection

**Documentation**: `CHATGPT_ERRORS_GUIDE.md`

---

### 3️⃣ **Codex Server (Code Execution)** ✅

**Purpose**: Execute Python/JavaScript code remotely from ChatGPT

**What It Does**:
- Execute code snippets in sandboxed environment
- Real-time output streaming
- Safe execution with timeouts
- Support for Python and JavaScript

**Status**: ✅ Operational on GitHub Codespaces

**Server Details**:
- **Platform**: GitHub Codespaces
- **Framework**: FastAPI
- **Port**: 8000
- **Languages**: Python, JavaScript/Node.js

**API Endpoints**:
```
GET  /health           - Health check
POST /execute          - Execute code
GET  /languages        - List supported languages
```

**Example Usage**:

**Request**:
```json
POST /execute
{
  "code": "print('Hello from ChatGPT!')",
  "language": "python",
  "timeout": 10
}
```

**Response**:
```json
{
  "output": "Hello from ChatGPT!\n",
  "error": "",
  "exit_code": 0,
  "execution_time": 0.023,
  "timestamp": "2025-11-06T12:00:00Z"
}
```

**Security Options**:

**Current Setup** (Development):
- Open access (no authentication)
- Private port in Codespaces
- Auto-stops after 30 minutes

**Production Options**:
1. **Bearer Token Authentication**:
   ```python
   Authorization: Bearer codex_abc123xyz456
   ```

2. **Custom GPT Action**:
   - Use OpenAPI schema (provided in docs)
   - Native ChatGPT integration
   - Seamless in conversations

3. **Webhook/Zapier Integration**:
   - No-code option
   - Use Make.com or Zapier
   - Forward requests to Codex server

**To Enable ChatGPT Access**:
1. Make port 8000 public in Codespaces PORTS tab
2. Copy the public URL (e.g., `https://super-duper-xyz-8000.app.github.dev`)
3. Tell ChatGPT the URL or create Custom Action
4. Test: "Execute this Python: print(2+2)"

**Sample ChatGPT Interaction**:
```
You: "Execute this on my server: import requests; print(requests.get('https://api.github.com').status_code)"

ChatGPT: [Sends to your Codex server]
         "Output: 200
          Exit Code: 0
          Execution Time: 0.45s"
```

**Cost**: 
- Codespaces: FREE for 60 hours/month
- After that: $0.18/hour for 2-core machine

**Documentation**: `codex-server/CHATGPT_INTEGRATION.md`

**Files**:
- `codex-server/codex_server.py` - Main server
- `codex-server/codex_server_secure.py` - With authentication
- `codex-server/test_client.py` - Testing client

---

### 4️⃣ **Google Gemini AI Analysis** ✅

**Purpose**: AI-powered insights on your power market data

**What It Does**:
- Analyzes current power market data
- Provides key observations
- Assesses grid health
- Identifies opportunities
- Generates recommendations

**Status**: ✅ Ready to use

**Model**: Google Gemini 1.5 Flash
- Fast inference (10-20 seconds)
- Large context window
- Free tier available

**How It Works**:
1. Script reads data from Google Sheets
2. Formats summary (generation, frequency, prices, balancing)
3. Sends to Gemini API with analysis prompt
4. Gemini returns insights
5. Results written back to sheet

**Setup** (2 minutes):
```bash
# Get free API key
# Visit: https://makersuite.google.com/app/apikey

# Option A: Environment variable
export GEMINI_API_KEY='your-api-key-here'
echo 'export GEMINI_API_KEY="your-key"' >> ~/.zshrc

# Option B: File
echo "your-api-key-here" > gemini_api_key.txt

# Install library (if needed)
pip3 install --user google-generativeai
```

**Usage**:
```bash
# Run analysis
cd ~/GB\ Power\ Market\ JJ
python3 ask_gemini_analysis.py

# Combine with data refresh
python3 update_analysis_bi_enhanced.py && python3 ask_gemini_analysis.py

# Automate (hourly)
# Add to crontab:
# 0 * * * * cd ~/GB\ Power\ Market\ JJ && python3 update_analysis_bi_enhanced.py && python3 ask_gemini_analysis.py >> gemini_analysis.log 2>&1
```

**Sample Output**:
```
🤖 GEMINI ANALYSIS

📊 KEY OBSERVATIONS:
- Wind generation at 42.3% of total mix (strong performance)
- System frequency stable at 49.98 Hz (within normal bounds)
- Renewable penetration at 68.4% (above average)

⚡ GRID HEALTH:
- Status: HEALTHY
- Frequency deviation: -0.02 Hz (minimal)
- No frequency alerts in last hour

🌱 RENEWABLE PERFORMANCE:
- Wind: 15,240 MW (excellent conditions)
- Solar: 3,120 MW (midday peak)
- Combined renewables: 18,360 MW

💰 MARKET INSIGHTS:
- System prices: £45.20/MWh (moderate)
- Price spread: £2.80/MWh (normal range)
- Balancing costs: £1.2M (24h period)

🎯 RECOMMENDATIONS:
1. Monitor wind curtailment in Scotland
2. Battery storage opportunity during solar peak
3. Consider forward contracts at current price levels
```

**What Gemini Analyzes**:
- Summary metrics (generation, renewable %, frequency, prices)
- Generation mix (top 10 fuel types)
- Recent frequency (last 5 measurements)
- Recent prices (last 5 settlement periods)
- Recent balancing costs (last 5 records)

**Documentation**: `GEMINI_AI_SETUP.md`

**File**: `ask_gemini_analysis.py`

---

## 🖥️ UpCloud Server Infrastructure

You have **THREE UpCloud servers** deployed in London:

### Server 1: AlmaLinux (Document Indexer) 🔴

**Purpose**: Drive→BigQuery document extraction and semantic search

**Server Details**:
- **Name**: almalinux-1cpu-1gb-uk-lon1
- **IP**: 94.237.55.15
- **OS**: AlmaLinux 10
- **RAM**: 1 GB
- **CPU**: 1 core
- **UUID**: 00765090-b26c-4259-8efe-761e8be9ec87
- **Location**: London, UK

**Services Running**:

1. **Document Extraction Service** (Systemd)
   - Service: `extraction.service`
   - Script: `continuous_extract_fixed.py`
   - Workers: 2 (optimized for 1GB RAM)
   - Batch Size: 100 documents
   - Auto-restart: Enabled
   - Logs: `/var/log/extraction.log`

2. **FastAPI Search Service** (Docker)
   - Container: `driveindexer`
   - Port: 8080
   - Endpoints: `/health`, `/search`
   - Auto-restart: Always

**Current Status** (Nov 6, 2025):
- ✅ Extraction: Active, 450 docs/hour
- ✅ Memory: 580 MB stable (was 7.2 GB - fixed!)
- ✅ Speed: 7-9 sec/doc (was 193 sec/doc - 20x faster!)
- 📊 Progress: 8,529 / 140,434 docs (6.1%)
- ⏱️ ETA: ~12 days to completion

**Recent Optimizations**:
- Fixed memory explosion (queue limit + query optimization)
- Reduced from 6 → 2 workers for 1GB RAM
- Memory reduced 92% (7.2 GB → 580 MB)
- Speed improved 20x (193 → 7 sec/doc)

**APIs**:
```bash
# Health check
curl http://94.237.55.15:8080/health

# Search
curl "http://94.237.55.15:8080/search?q=renewable%20energy&k=10"
```

**Management**:
```bash
# Check extraction status
ssh root@94.237.55.15 'docker stats driveindexer --no-stream'
ssh root@94.237.55.15 'tail -10 /var/log/extraction.log'

# Monitor service
ssh root@94.237.55.15 'systemctl status extraction.service'

# Restart if needed
ssh root@94.237.55.15 'systemctl restart extraction.service'

# Docker restart (clears memory)
ssh root@94.237.55.15 'systemctl stop extraction.service && systemctl restart docker && systemctl start extraction.service'
```

**Documentation**: 
- `UPCLOUD_DEPLOYMENT.md`
- `EXTRACTION_SYSTEMD_SETUP.md`
- `MEMORY_ISSUE_ROOT_CAUSE.md`

**Cost**: ~$5-10/month (server) + ~$0.35/month (GCP services)

---

### Server 2: AlmaLinux (GB Power Map) 🟢

**Purpose**: Live interactive power map with auto-refresh

**Server Details**:
- **Name**: almalinux-1cpu-2gb-uk-lon1
- **IP**: 94.237.55.234
- **OS**: AlmaLinux 10
- **RAM**: 2 GB
- **CPU**: 1 core
- **UUID**: 00f1dd6f-f773-493f-a89d-e287e52bfe61
- **Location**: London, UK

**Services Running**:

1. **Nginx Web Server**
   - Port: 80 (HTTP)
   - Web root: `/var/www/maps/`
   - Main file: `gb_power_complete_map.html`

2. **Map Auto-Regeneration** (Cron)
   - Schedule: Every 30 minutes
   - Script: `/var/www/maps/scripts/auto_generate_map_linux.py`
   - Logs: `/var/www/maps/logs/cron.log`

**What It Displays**:
- 🗺️ Interactive Leaflet map of Great Britain
- 📍 8,653 total generators (CVA + SVA)
- 🌊 35 offshore wind farms
- ⚡ GSP flow indicators (blue=export, orange=import)
- 🏢 14 DNO boundary regions
- 📊 Latest generation/demand data from BigQuery

**5 Toggleable Layers**:
1. DNO Boundaries (14 regions)
2. GSP Flows (real-time grid supply points)
3. Offshore Wind Farms (35 sites)
4. CVA Plants (1,581 large generators)
5. SVA Generators (7,072 small sites)

**Public URL**: http://94.237.55.234/gb_power_complete_map.html

**Data Sources**:
- `bmrs_indgen` - Generation data
- `bmrs_inddem` - Demand data
- `offshore_wind_farms` - Wind farm locations
- `sva_generators_with_coords` - Small generators
- `cva_plants` - Large power plants
- Local: `dno_regions.geojson` - DNO boundaries

**Automation**:
```bash
# Cron job (every 30 minutes)
*/30 * * * * python3 /var/www/maps/scripts/auto_generate_map_linux.py >> /var/www/maps/logs/cron.log 2>&1
```

**Management**:
```bash
# Check map generation
ssh root@94.237.55.234 'tail -20 /var/www/maps/logs/cron.log'

# Check Nginx status
ssh root@94.237.55.234 'systemctl status nginx'

# Regenerate map manually
ssh root@94.237.55.234 'python3 /var/www/maps/scripts/auto_generate_map_linux.py'

# View last generation time
ssh root@94.237.55.234 'ls -lh /var/www/maps/gb_power_complete_map.html'
```

**Deployment Package**:
- ✅ `gb_power_map_deployment.zip` (ready to upload)
- Contains: scripts, data files, setup automation
- One-command deployment: `./deploy.sh`

**Documentation**:
- `ALMALINUX_DEPLOYMENT_GUIDE.md`
- `ALMALINUX_AUTOMATION_COMPLETE.md`
- `POWER_MAP_IRIS_DEPLOYMENT.md`

**Cost**: ~$10/month (2GB server)

---

### Server 3: Ubuntu (IRIS Pipeline) �

**Purpose**: Real-time IRIS data ingestion (Azure Service Bus → BigQuery)

**Server Details**:
- **Name**: dev-server
- **IP**: 83.136.250.239
- **OS**: Ubuntu 22.04.5 LTS
- **RAM**: 2 GB
- **CPU**: 1 core
- **UUID**: 00ffa2df-8e13-4de0-9097-cad7b1185831
- **Location**: London, UK

**Services Running**:

1. **IRIS Client** (Python)
   - Script: `client.py`
   - Downloads messages from Azure Service Bus
   - Saves to `/opt/iris-pipeline/data`
   - Runs continuously

2. **BigQuery Uploader** (Python)
   - Script: `iris_to_bigquery_unified.py`
   - Batch uploads every 5 minutes
   - Auto-deletes local files after upload
   - Prevents disk fill-up

3. **Pipeline Service** (Systemd)
   - Service: `iris-pipeline.service`
   - Auto-start on boot
   - Auto-restart on failure
   - Logs: `/opt/iris-pipeline/logs/`

**Status**: ✅ Deployed and operational (Nov 6, 2025)

**Why Ubuntu?**:
- Consistent with other UpCloud servers (AlmaLinux/Debian-based)
- Python automation with systemd
- Lower resource usage (no GUI)
- Better SSH management
- Lower cost than Windows Server

**Data Flow**:
```
Azure Service Bus (IRIS messages)
         ↓
Ubuntu Server (client.py downloads)
         ↓
Local Directory (/opt/iris-pipeline/data)
         ↓
Batch Upload every 5 min (iris_to_bigquery_unified.py)
         ↓
BigQuery Tables (bmrs_*_iris)
         ↓
Google Sheets Dashboard + Power Map
```

**Management Commands**:
```bash
# Check status
ssh root@83.136.250.239 'systemctl status iris-pipeline.service'

# View logs
ssh root@83.136.250.239 'tail -50 /opt/iris-pipeline/logs/pipeline.log'

# Restart service
ssh root@83.136.250.239 'systemctl restart iris-pipeline.service'

# Check file count
ssh root@83.136.250.239 'find /opt/iris-pipeline/data -type f | wc -l'

# Check disk space
ssh root@83.136.250.239 'df -h /opt/iris-pipeline/data'
```

**Documentation**: `IRIS_DEPLOYMENT_GUIDE_ALMALINUX.md`, `deploy-iris-ubuntu.sh`

**Cost**: ~$10/month (2GB server)

---

## 🔗 Integration Details

### How ChatGPT Connects to UpCloud Services

#### 1. **Drive OAuth → Document Search**
```
ChatGPT (Drive access) → Google Drive files
                              ↓
                    AlmaLinux Server 94.237.55.15
                              ↓
                    Document Indexer extracts text
                              ↓
                    BigQuery (searchable chunks)
                              ↓
                    FastAPI /search endpoint
```

**Flow**:
1. You ask ChatGPT: "What's in my power market documents?"
2. ChatGPT reads your Drive (OAuth)
3. Behind the scenes: UpCloud server has indexed those files
4. You can also search via API: `curl http://94.237.55.15:8080/search?q=query`

#### 2. **GitHub → Code Deployment**
```
ChatGPT (provides code) → You save locally
                              ↓
                    ./quick-push.sh pushes to GitHub
                              ↓
                    Pull on UpCloud server
                              ↓
                    Deploy new code
```

**Example Workflow**:
```
You: "ChatGPT, create a script to monitor frequency"
ChatGPT: [Provides Python code]
You: [Save as monitor_frequency.py]
You: ./quick-push.sh "Add frequency monitor"
You: ssh root@94.237.55.234 'cd /var/www/maps && git pull'
```

#### 3. **Gemini AI → Power Data Analysis**
```
UpCloud Server 94.237.55.234
         ↓
BigQuery (power market data)
         ↓
Python script reads latest data
         ↓
Gemini API analyzes patterns
         ↓
Insights written to Google Sheet
         ↓
ChatGPT can read via Drive OAuth
```

**Complete Loop**:
1. Power data streams to BigQuery (IRIS/historical)
2. Map server auto-generates visualization every 30 min
3. Python script sends data to Gemini for AI analysis
4. Gemini returns insights written to Sheet
5. You ask ChatGPT: "What does Gemini say about the power market?"
6. ChatGPT reads Sheet via Drive OAuth and summarizes

#### 4. **Codex Server → Remote Execution**
```
ChatGPT → Request to execute code
         ↓
Codespace (Codex server)
         ↓
Execute Python/JavaScript
         ↓
Return output to ChatGPT
```

**Use Case**: Testing queries before deploying to UpCloud
```
You: "ChatGPT, test this BigQuery query on my Codex server"
ChatGPT: [Executes via Codex server]
ChatGPT: "Query returned 1,234 rows. Results look good."
You: [Deploy to UpCloud]
```

---

## 📚 Deployment Guides

### Document Indexer (94.237.55.15)

**Quick Deploy**:
```bash
# Automated deployment
chmod +x deploy-to-upcloud.sh
./deploy-to-upcloud.sh
```

**Manual Steps**:
1. SSH: `ssh root@94.237.55.15`
2. Install Docker
3. Copy files: `scp -r drive-bq-indexer root@94.237.55.15:/opt/`
4. Build: `docker build -t driveindexer:latest .`
5. Run: `docker run -d --name driveindexer --restart=always -p 8080:8080 driveindexer:latest`

**Files**: `UPCLOUD_DEPLOYMENT.md`, `EXTRACTION_SYSTEMD_SETUP.md`

---

### GB Power Map (94.237.55.234)

**Quick Deploy**:
```bash
# Upload deployment package
cd "/Users/georgemajor/GB Power Market JJ"
scp gb_power_map_deployment.zip root@94.237.55.234:/root/

# SSH and extract
ssh root@94.237.55.234
unzip gb_power_map_deployment.zip
cd gb_power_map_deployment

# One-command deploy
sudo ./deploy.sh
```

**What It Does**:
1. ✅ Installs Nginx web server
2. ✅ Copies map generator script
3. ✅ Sets up cron job (every 30 min)
4. ✅ Configures firewall (port 80)
5. ✅ Generates initial map
6. ✅ Tests web access

**Files**: `ALMALINUX_DEPLOYMENT_GUIDE.md`, `ALMALINUX_AUTOMATION_COMPLETE.md`

---

### Windows IRIS Server (Pending)

**Deploy Steps**:
1. RDP to server
2. Install Python 3.11+
3. Install Google Cloud SDK
4. Upload scripts (`client.py`, `iris_to_bigquery_unified.py`)
5. Configure credentials
6. Set up Task Scheduler
7. Start services

**Files**: `UPCLOUD_DEPLOYMENT_PLAN.md`, `WINDOWS_DEPLOYMENT_STATUS.md`

---

## 🛠️ Management & Operations

### Daily Operations

**Check Document Extraction Status**:
```bash
ssh root@94.237.55.15 'tail -5 /var/log/extraction.log'
ssh root@94.237.55.15 'docker stats driveindexer --no-stream'
```

**Check Power Map Updates**:
```bash
ssh root@94.237.55.234 'tail -10 /var/www/maps/logs/cron.log'
# Open in browser: http://94.237.55.234/gb_power_complete_map.html
```

**Update ChatGPT Integrations**:
```bash
# GitHub push
./quick-push.sh "Update from ChatGPT suggestions"

# Refresh Gemini analysis
python3 ask_gemini_analysis.py
```

### Monitoring Commands

**Server Health**:
```bash
# Check all services
ssh root@94.237.55.15 'systemctl status extraction.service'
ssh root@94.237.55.234 'systemctl status nginx'

# Check resource usage
ssh root@94.237.55.15 'free -h && df -h'
ssh root@94.237.55.234 'free -h && df -h'
```

**API Health**:
```bash
# Document search API
curl http://94.237.55.15:8080/health

# Power map web server
curl -I http://94.237.55.234/gb_power_complete_map.html
```

### Backup Procedures

**Document Indexer**:
```bash
# Backup BigQuery data
ssh root@94.237.55.15 'docker exec driveindexer python -m src.cli export-data > /backups/data-$(date +%Y%m%d).json'

# Backup configs
ssh root@94.237.55.15 'tar -czf /backups/configs-$(date +%Y%m%d).tar.gz /opt/drive-bq-indexer/.env'
```

**Power Map**:
```bash
# Backup scripts
ssh root@94.237.55.234 'tar -czf /backups/maps-$(date +%Y%m%d).tar.gz /var/www/maps/'
```

---

## 🔧 Troubleshooting

### ChatGPT Issues

**Problem**: "There was a problem syncing GitHub"
- **Actually means**: Google Drive OAuth issue (misleading error)
- **Fix**: Remove connection at myaccount.google.com/permissions, reconnect
- **Doc**: `FIX_CHATGPT_OAUTH.md`

**Problem**: "Access Denied" from GitHub
- **Cause**: ChatGPT GitHub App not installed
- **Fix**: Install at github.com/apps/chatgpt
- **Doc**: `CHATGPT_ERRORS_GUIDE.md`, `CHATGPT_GITHUB_FIX.md`

**Problem**: Codex server unreachable
- **Cause**: Port not public or Codespace stopped
- **Fix**: Make port 8000 public in PORTS tab
- **Doc**: `codex-server/CHATGPT_INTEGRATION.md`

**Problem**: Gemini not returning analysis
- **Cause**: Missing API key
- **Fix**: `export GEMINI_API_KEY='your-key'`
- **Doc**: `GEMINI_AI_SETUP.md`

---

### UpCloud Server Issues

**Document Indexer (94.237.55.15)**

**Problem**: Memory usage high (>2GB)
- **Fixed**: Now optimized to 580MB
- **If returns**: Restart Docker: `systemctl restart docker`
- **Doc**: `MEMORY_ISSUE_ROOT_CAUSE.md`

**Problem**: Extraction slow
- **Check**: `tail -20 /var/log/extraction.log`
- **Expected**: 7-9 seconds/doc
- **If slower**: Check worker count in run_ce.py (should be 2)

**Problem**: Search API not responding
- **Check**: `docker ps | grep driveindexer`
- **Restart**: `docker restart driveindexer`
- **Logs**: `docker logs driveindexer`

**Power Map Server (94.237.55.234)**

**Problem**: Map not updating
- **Check**: `tail -20 /var/www/maps/logs/cron.log`
- **Manual run**: `python3 /var/www/maps/scripts/auto_generate_map_linux.py`
- **Verify cron**: `crontab -l`

**Problem**: Nginx not serving
- **Check**: `systemctl status nginx`
- **Restart**: `systemctl restart nginx`
- **Test**: `curl -I http://localhost/`

**Problem**: BigQuery connection failed
- **Check**: `echo $GOOGLE_APPLICATION_CREDENTIALS`
- **Verify**: Service account JSON exists
- **Test**: `gcloud auth application-default print-access-token`

---

## 📊 System Status Summary

| Component | Status | Location | Documentation |
|-----------|--------|----------|---------------|
| **ChatGPT Drive OAuth** | ✅ Ready | ChatGPT Settings | FIX_CHATGPT_OAUTH.md |
| **GitHub Integration** | ✅ Configured | Local Mac | CHATGPT_SETUP_COMPLETE.md |
| **Codex Server** | ✅ Operational | Codespaces | codex-server/CHATGPT_INTEGRATION.md |
| **Gemini AI** | ✅ Ready | API | GEMINI_AI_SETUP.md |
| **Document Indexer** | ✅ Active | 94.237.55.15 | UPCLOUD_DEPLOYMENT.md |
| **Power Map** | ✅ Live | 94.237.55.234 | ALMALINUX_DEPLOYMENT_GUIDE.md |
| **IRIS Pipeline** | ✅ Operational | 83.136.250.239 | deploy-iris-ubuntu.sh |

---

## 💰 Cost Summary

| Service | Monthly Cost | Notes |
|---------|--------------|-------|
| UpCloud Server 1 (1GB) | $5-10 | Document indexer |
| UpCloud Server 2 (2GB) | $10 | Power map |
| UpCloud Server 3 (2GB) | $10 | IRIS (when deployed) |
| BigQuery Storage | $0.10 | Data storage |
| Vertex AI Embeddings | $0.25-2.50 | Document search |
| GitHub Codespaces | Free | 60 hrs/month free tier |
| Gemini API | Free | Free tier sufficient |
| **Total** | **$25-33/month** | All systems running |

**Cost Optimization**:
- Use stub embeddings instead of Vertex AI (-$2.50)
- Stop Codespaces when not in use (manual)
- Run indexing on-demand instead of continuously (-$5)

---

## 🚀 Quick Reference

### Essential URLs

- **Document Search API**: http://94.237.55.15:8080/search
- **API Health**: http://94.237.55.15:8080/health
- **Power Map**: http://94.237.55.234/gb_power_complete_map.html
- **Google Sheets Dashboard**: https://docs.google.com/spreadsheets/d/12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8/
- **ChatGPT**: https://chat.openai.com
- **Gemini API**: https://makersuite.google.com/app/apikey

### Essential Commands

```bash
# ChatGPT GitHub Push
./quick-push.sh "Description"

# Gemini Analysis
python3 ask_gemini_analysis.py

# Check Extraction
ssh root@94.237.55.15 'tail -5 /var/log/extraction.log'

# Check Power Map
ssh root@94.237.55.234 'tail -10 /var/www/maps/logs/cron.log'

# Restart Services
ssh root@94.237.55.15 'systemctl restart extraction.service'
ssh root@94.237.55.234 'systemctl restart nginx'
```

---

## 📖 Complete Documentation Index

### ChatGPT Integration
1. `FIX_CHATGPT_OAUTH.md` - Google Drive OAuth setup
2. `CHATGPT_SETUP_COMPLETE.md` - GitHub integration guide
3. `CHATGPT_ERRORS_GUIDE.md` - Common problems & fixes
4. `CHATGPT_GITHUB_FIX.md` - GitHub App installation
5. `codex-server/CHATGPT_INTEGRATION.md` - Code execution server
6. `GEMINI_AI_SETUP.md` - AI analysis setup

### UpCloud Deployment
7. `UPCLOUD_DEPLOYMENT.md` - Document indexer deployment
8. `UPCLOUD_DEPLOYMENT_PLAN.md` - Windows IRIS server plan
9. `ALMALINUX_DEPLOYMENT_GUIDE.md` - Power map deployment
10. `ALMALINUX_AUTOMATION_COMPLETE.md` - Map automation details
11. `EXTRACTION_SYSTEMD_SETUP.md` - Extraction service setup
12. `MEMORY_ISSUE_ROOT_CAUSE.md` - Memory optimization

### General
13. `SYSTEM_CAPABILITIES_OVERVIEW.md` - Complete system capabilities
14. `README.md` - Main project documentation
15. `DOCUMENTATION_INDEX.md` - All 22+ documentation files

---

**Last Updated**: November 6, 2025  
**Status**: ✅ All ChatGPT Integrations & UpCloud Services Operational  
**All 3 Servers Deployed**: Document Indexer, Power Map, IRIS Pipeline

🤖 **ChatGPT + UpCloud = Powerful Automated Power Market Intelligence System!** 🚀

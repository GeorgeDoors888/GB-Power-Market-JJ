# Dashboard Deployment System

## Overview

Automated system to detect changes in Dashboard V2 and apply them to new spreadsheets.

## Components

### 1. Template Manager (`template_manager.py`)
**Python script using Google Sheets API**

**Features:**
- Captures current state of Dashboard V2
- Detects changes (new sheets, modified cells, formatting)
- Applies template to new spreadsheets
- Watches for changes in real-time

**Usage:**
```bash
# Capture current template
python3 template_manager.py capture

# Detect changes
python3 template_manager.py detect

# Apply to new sheet
python3 template_manager.py apply <spreadsheet_id>

# Watch for changes
python3 template_manager.py watch
```

### 2. Clasp Deployer (`clasp_deployer.py`)
**Python wrapper for clasp CLI**

**Features:**
- Automates Apps Script deployment
- Updates Config with spreadsheet ID
- Auto-deploys on code changes
- Manages multiple deployments

**Usage:**
```bash
# Check clasp installation
python3 clasp_deployer.py check

# Push current code
python3 clasp_deployer.py push

# Deploy to new sheet
python3 clasp_deployer.py deploy <spreadsheet_id> [webhook_url]

# Watch Code.gs and auto-deploy
python3 clasp_deployer.py watch
```

### 3. Complete Pipeline (`deployment_pipeline.py`)
**End-to-end deployment**

**Usage:**
```bash
# Deploy complete new dashboard
python3 deployment_pipeline.py deploy "Client Dashboard"

# With webhook URL
python3 deployment_pipeline.py deploy "Client Dashboard" "https://webhook.url"
```

## Workflow

### Initial Setup (One Time)
```bash
# 1. Capture Dashboard V2 as template
python3 template_manager.py capture

# 2. Verify clasp is configured
python3 clasp_deployer.py check
```

### Making Changes to Dashboard V2
```bash
# 1. Make your changes in Dashboard V2 spreadsheet
# 2. Detect what changed
python3 template_manager.py detect

# 3. Template is automatically updated
```

### Deploying to New Client
```bash
# Single command - creates sheet, applies template, deploys Apps Script
python3 deployment_pipeline.py deploy "Client Name Dashboard"

# Result:
# ✅ New spreadsheet created
# ✅ All sheets copied from Dashboard V2
# ✅ Formatting applied
# ✅ Apps Script deployed with correct config
# ✅ Menus working
```

### Continuous Monitoring
```bash
# Watch Dashboard V2 for changes (runs continuously)
python3 deployment_pipeline.py watch
```

## What Gets Captured

### Data
- All sheet contents (values)
- Sheet structure (rows, cols)
- Frozen rows/columns

### Formatting
- Header styles (Dashboard A1:K3)
- Section headers (A10, A30, A80, A116)
- Number formats
- Colors (Upower blue #0072ce, orange #ff7f0f)

### Apps Script
- All menus and functions
- Config updated per deployment
- Constraint map coordinates
- Webhook URLs

## Change Detection

The system detects:
- ✅ New sheets added
- ✅ Sheets removed
- ✅ Cell value changes
- ✅ Row/column count changes
- ✅ Formatting changes

Example output:
```
📊 Change Summary:
   Sheets added: 1
   Sheets removed: 0
   Sheets modified: 2

📝 Modified sheets:
   Dashboard: 15 cells changed
   Daily_Chart_Data: 42 cells changed
```

## Architecture

```
Dashboard V2 (Master Template)
         ↓
   [Capture State]
         ↓
   template_cache.json
         ↓
   [Detect Changes]
         ↓
   [Apply to New Sheet] ← Google Sheets API (Python)
         ↓
   New Spreadsheet
         ↓
   [Deploy Apps Script] ← clasp CLI (Python wrapper)
         ↓
   ✅ Complete Dashboard
```

## Files Created

- `template_cache.json` - Current template state
- `Code.gs` - Apps Script code (auto-updated)
- `.clasp.json` - Clasp configuration

## Benefits

✅ **Consistency** - All new dashboards match Dashboard V2 exactly  
✅ **Speed** - Deploy in ~30 seconds instead of manual copying  
✅ **Automation** - Detect changes automatically  
✅ **Python-First** - 90% Python, minimal Apps Script interaction  
✅ **Scalable** - Deploy to unlimited client dashboards  

## Example Session

```bash
# Monday: Make improvements to Dashboard V2
# (add new chart, improve formatting, etc.)

# Capture changes
$ python3 template_manager.py detect
📊 Change Summary:
   Sheets added: 1 (Chart_Wind)
   Sheets modified: 1 (Dashboard: 5 cells changed)

# Wednesday: New client needs dashboard
$ python3 deployment_pipeline.py deploy "ABC Energy Dashboard"
🚀 DEPLOYING NEW DASHBOARD: ABC Energy Dashboard
✅ Created: ABC Energy Dashboard
📋 Applying template...
   📄 Applying Dashboard... ✅ 193 rows copied
   📄 Applying Chart_Wind... ✅ 50 rows copied
🚀 Deploying Apps Script...
✅ DEPLOYMENT COMPLETE!
📊 https://docs.google.com/spreadsheets/d/[NEW_ID]

# Result: Client has exact copy of your improved Dashboard V2
```

## Maintenance

### Update Master Template
```bash
# After making changes to Dashboard V2
python3 template_manager.py capture
```

### Update Apps Script Template
```bash
# After changing Code.gs
python3 clasp_deployer.py push
```

### Verify System
```bash
# Check all components
python3 template_manager.py capture
python3 clasp_deployer.py check
python3 deployment_pipeline.py capture
```

## Troubleshooting

**Template not found:**
```bash
python3 template_manager.py capture
```

**Clasp auth error:**
```bash
clasp login
```

**Changes not detected:**
- Refresh Dashboard V2
- Clear cache: `rm template_cache.json`
- Recapture: `python3 template_manager.py capture`

---

**Status:** ✅ Ready to use  
**Dependencies:** Python 3.9+, gspread, clasp CLI  
**Master Template:** Dashboard V2 (1LmMq4OEE639Y-XXpOJ3xnvpAmHB6vUovh5g6gaU_vzc)

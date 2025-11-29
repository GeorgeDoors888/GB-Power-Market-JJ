# Dashboard Maintenance Guide

## 🔄 Automatic Sync System

When you make changes to any dashboard files, the sync system will automatically:
- Deploy Apps Script updates via clasp
- Validate Python scripts
- Backup changed files
- Update documentation
- Commit to git

---

## 📝 How to Make Changes

### 1. Edit Files Normally
Edit any file in your preferred editor:
```bash
code ~/GB-Power-Market-JJ/new-dashboard/UpdateDashboard.gs
code ~/GB-Power-Market-JJ/realtime_dashboard_updater.py
```

### 2. Run Sync
After saving changes:
```bash
cd ~/GB-Power-Market-JJ
python3 sync_dashboard_changes.py
```

**What it does:**
- ✅ Detects changed files
- ✅ Backs up to `backups/YYYYMMDD_HHMMSS/`
- ✅ Validates Python syntax
- ✅ Deploys Apps Script via `clasp push --force`
- ✅ Updates documentation timestamps

### 3. Watch Mode (Optional)
For continuous monitoring:
```bash
python3 sync_dashboard_changes.py --watch
```

This checks for changes every 30 seconds and auto-syncs.

---

## 🔧 What Gets Synced

### Apps Script Files (auto-deployed)
- `new-dashboard/Code.gs`
- `new-dashboard/UpdateDashboard.gs`
- `new-dashboard/DashboardFilters.gs`
- `new-dashboard/appsscript.json`

**After sync:** Changes are live in Google Sheets immediately

### Python Scripts (validated)
- `realtime_dashboard_updater.py`
- `update_summary_for_chart.py`
- `update_iris_dashboard.py`
- `clear_outages_section.py`
- `update_outages_for_v2.py`
- `apply_orange_redesign.py`
- `add_validation_and_formatting.py`
- `fix_dashboard_layout.py`

**After sync:** Syntax checked, no deployment (cron uses files directly)

### Documentation (tracked)
- `DASHBOARD_V2_STATUS.md`
- `CHART_SPECS.md`
- `FINAL_SETUP_INSTRUCTIONS.md`

**After sync:** Changes logged in backup

### Config Files (flagged)
- `inner-cinema-credentials.json` ⚠️ Manual review
- `new-dashboard/.clasp.json` ⚠️ Manual review

**After sync:** Warning displayed, no auto-deployment

---

## 🎯 Common Workflows

### Update Apps Script Function
```bash
# 1. Edit the file
nano ~/GB-Power-Market-JJ/new-dashboard/UpdateDashboard.gs

# 2. Sync (auto-deploys)
python3 sync_dashboard_changes.py
```

### Fix Python Script Bug
```bash
# 1. Edit the file
nano ~/GB-Power-Market-JJ/realtime_dashboard_updater.py

# 2. Sync (validates syntax)
python3 sync_dashboard_changes.py

# 3. Test manually
python3 realtime_dashboard_updater.py
```

### Update Documentation
```bash
# 1. Edit
nano ~/GB-Power-Market-JJ/DASHBOARD_V2_STATUS.md

# 2. Sync
python3 sync_dashboard_changes.py
```

### Add New Script
```bash
# 1. Create file
touch ~/GB-Power-Market-JJ/new_feature.py

# 2. Add to monitoring (edit sync script)
nano sync_dashboard_changes.py
# Add to MONITORED_FILES['python_scripts']

# 3. Sync will track it automatically
```

---

## 💾 Backups

Every sync creates a timestamped backup:
```
backups/
├── 20251129_143000/
│   ├── apps_script/
│   │   ├── Code.gs
│   │   └── UpdateDashboard.gs
│   ├── python_scripts/
│   │   └── realtime_dashboard_updater.py
│   └── documentation/
│       └── DASHBOARD_V2_STATUS.md
└── 20251129_150000/
    └── ...
```

**Restore from backup:**
```bash
cp backups/20251129_143000/apps_script/Code.gs new-dashboard/
python3 sync_dashboard_changes.py
```

---

## 📦 Git Integration

Commit and push changes to GitHub:
```bash
# Sync files first
python3 sync_dashboard_changes.py

# Git sync
./git_sync.sh
```

**Or manually:**
```bash
git add -A
git commit -m "Dashboard V2: Updated formatting logic"
git push origin main
```

---

## 🔍 Troubleshooting

### Sync Script Not Working
```bash
# Check Python
python3 --version  # Should be 3.14+

# Check clasp
which clasp  # Should be /opt/homebrew/bin/clasp

# Re-run with error output
python3 sync_dashboard_changes.py 2>&1
```

### Apps Script Deployment Fails
```bash
# Check clasp auth
cd ~/GB-Power-Market-JJ/new-dashboard
clasp login

# Manual deploy
clasp push --force

# Check script ID
cat .clasp.json
```

### Python Validation Fails
```bash
# Check syntax manually
python3 -m py_compile realtime_dashboard_updater.py

# See detailed error
python3 realtime_dashboard_updater.py
```

### Watch Mode Stuck
```bash
# Stop: Ctrl+C

# Check state file
cat .dashboard_sync_state.json

# Reset (deletes state)
rm .dashboard_sync_state.json
```

---

## ⚙️ Configuration

### Add File to Monitoring
Edit `sync_dashboard_changes.py`:
```python
MONITORED_FILES = {
    'python_scripts': [
        # ... existing files ...
        BASE_DIR / "your_new_script.py",  # Add here
    ],
}
```

### Change Sync Interval (Watch Mode)
```python
# In sync_dashboard_changes.py, line ~230
time.sleep(30)  # Change 30 to desired seconds
```

### Exclude Files from Backup
```python
# In backup_changes() function, add:
if file.name in ['credentials.json', 'secrets.py']:
    continue
```

---

## 🚀 Automation Setup

### Cron Job for Auto-Sync
Add to crontab:
```bash
crontab -e

# Add:
*/5 * * * * cd /Users/georgemajor/GB-Power-Market-JJ && /opt/homebrew/bin/python3 sync_dashboard_changes.py >> logs/sync.log 2>&1
```

### Git Auto-Push
```bash
# Add to crontab:
0 * * * * cd /Users/georgemajor/GB-Power-Market-JJ && ./git_sync.sh >> logs/git_sync.log 2>&1
```

---

## 📊 Status Check

View current state:
```bash
# Show monitored files
python3 -c "from sync_dashboard_changes import *; print(json.dumps(MONITORED_FILES, indent=2, default=str))"

# Show last sync state
cat .dashboard_sync_state.json | python3 -m json.tool

# Check backups
ls -lh backups/
```

---

## 🎯 Quick Reference

| Task | Command |
|------|---------|
| **Sync once** | `python3 sync_dashboard_changes.py` |
| **Watch mode** | `python3 sync_dashboard_changes.py --watch` |
| **Git sync** | `./git_sync.sh` |
| **Manual deploy** | `cd new-dashboard && clasp push --force` |
| **Validate Python** | `python3 -m py_compile script.py` |
| **View backups** | `ls -R backups/` |
| **Restore file** | `cp backups/*/category/file.py .` |

---

**🔄 Your changes are now automatically maintained!**

Just edit files and run `python3 sync_dashboard_changes.py` - everything else is handled automatically.

# 🔄 Dashboard Sync - Quick Reference

## When You Make Changes

**Just run:**
```bash
cd ~/GB-Power-Market-JJ
python3 sync_dashboard_changes.py
```

**What happens automatically:**
- ✅ Backs up your changes
- ✅ Validates Python scripts
- ✅ Deploys Apps Script to Google Sheets
- ✅ Updates documentation
- ✅ Logs everything

---

## Watch Mode (Auto-Sync)

Start monitoring (checks every 30 sec):
```bash
python3 sync_dashboard_changes.py --watch
```

Stop: Press `Ctrl+C`

---

## Git Sync

After syncing, push to GitHub:
```bash
./git_sync.sh
```

---

## Files That Auto-Deploy

| File Type | What Happens |
|-----------|--------------|
| `new-dashboard/*.gs` | Deploys to Google Sheets via clasp |
| `*.py` | Validates syntax only (no deploy) |
| `*.md` | Tracked in backups |
| `*.json` | Flagged for manual review |

---

## Backups Location

Every sync creates backup:
```
backups/YYYYMMDD_HHMMSS/
├── apps_script/
├── python_scripts/
└── documentation/
```

---

## Full Guide

See `MAINTENANCE_GUIDE.md` for detailed instructions.

---

**That's it! Edit → Sync → Done.**

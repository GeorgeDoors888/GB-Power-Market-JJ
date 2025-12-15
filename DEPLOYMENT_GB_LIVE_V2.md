# GB Live Dashboard v2 - Deployment Guide

## ⚠️ Critical Configuration
**Script ID**: `1b2dOZ4lw-zJvKdZ4MaJ48f1NR7ewCtUbZOGWGb3n8O7P-kgnUsThs980`
**Project Directory**: `clasp-gb-live-2`
**Google Sheet**: GB Live Dashboard v2 (ID: `1-u794iGngn5...`)

## How to Deploy
**DO NOT** run `clasp push` manually if you are unsure of the directory.
Use the safety script in the root folder:

```bash
./deploy_gb_live_v2.sh
```

This script will:
1.  Navigate to the correct folder (`clasp-gb-live-2`).
2.  **Verify** the Script ID matches the production ID above.
3.  Push the code.

## Troubleshooting
If changes are not appearing:
1.  Run `./deploy_gb_live_v2.sh` and check for "✅ Deployment Successful".
2.  Open the Google Sheet.
3.  Go to **Extensions > Apps Script**.
4.  Check `Code.gs` for the latest version log (e.g., `VERSION: ...`).
5.  Reload the Google Sheet browser tab.

## Directory Structure
The correct code is in:
`/home/george/GB-Power-Market-JJ/clasp-gb-live-2/`

Ignore these folders (legacy/backups):
- `clasp-project`
- `clasp-sheet-project`
- `energy_dashboard_clasp`

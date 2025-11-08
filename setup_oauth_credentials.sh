#!/bin/bash

cat << 'EOF'

🔐 QUICK OAUTH SETUP FOR APPS SCRIPT DEPLOYMENT
================================================

The simplest solution is to use YOUR Google account credentials
instead of the service account. This bypasses all project linking issues.

📋 STEPS TO GET OAUTH CREDENTIALS
================================================

1️⃣  Open Google Cloud Console:
    https://console.cloud.google.com/apis/credentials?project=inner-cinema-476211-u9

2️⃣  Click: "+ CREATE CREDENTIALS" (top of page)

3️⃣  Select: "OAuth client ID"

4️⃣  If prompted to configure consent screen:
    • Click "CONFIGURE CONSENT SCREEN"
    • Select: "Internal" (if available) or "External"
    • Click "CREATE"
    • Fill in:
      - App name: "GB Power Market Script Deployer"
      - User support email: (your email)
      - Developer contact: (your email)
    • Click "SAVE AND CONTINUE" (3 times)
    • Click "BACK TO DASHBOARD"
    • Return to: Credentials page

5️⃣  Click "+ CREATE CREDENTIALS" → "OAuth client ID" again

6️⃣  Application type: "Desktop app"

7️⃣  Name: "Apps Script Deployer"

8️⃣  Click "CREATE"

9️⃣  Click "DOWNLOAD JSON" (download icon)

🔟  Rename downloaded file to: oauth_credentials.json

1️⃣1️⃣  Move it to this folder:
    /Users/georgemajor/GB Power Market JJ/oauth_credentials.json

================================================
THEN RUN THIS COMMAND
================================================

python3 deploy_apps_script_oauth.py

• Browser will open
• Login with YOUR Google account (the one that owns the sheet)
• Click "Allow"
• Script updates automatically
• Done!

================================================
WHY THIS WORKS
================================================

✅ Uses YOUR account (not service account)
✅ YOU own the Apps Script → full access
✅ No project linking needed
✅ No permission errors
✅ Works immediately after OAuth setup

================================================
TIME ESTIMATE
================================================

⏱️  OAuth setup: 3-5 minutes (one time)
⏱️  First deployment: 10 seconds
⏱️  Future deployments: 5 seconds (token saved)

================================================
ALTERNATIVE: Manual Copy/Paste
================================================

If you prefer to avoid OAuth setup:
1. Open: google_sheets_dashboard.gs
2. Copy all content (Cmd+A, Cmd+C)
3. Open your Google Sheet
4. Extensions → Apps Script
5. Delete old code
6. Paste new code
7. Save (Cmd+S)
8. Refresh sheet
9. Run One-Click Setup

Time: 2 minutes

EOF

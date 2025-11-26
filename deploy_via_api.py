#!/usr/bin/env python3
"""
Deploy constraint map using Apps Script API directly
"""

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import json

# Configuration
CREDENTIALS_FILE = "inner-cinema-credentials.json"
SPREADSHEET_ID = "12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8"
SCRIPT_ID = "1c9BJqrtruVFh_LT_IWrHOpJIy8c29_zH6v1Co8-KHU9R1o9g2wZZERH5"

# Scopes needed
SCOPES = [
    'https://www.googleapis.com/auth/script.projects',
    'https://www.googleapis.com/auth/spreadsheets'
]

# Read the code
with open('constraint_map_simple.gs', 'r') as f:
    code_content = f.read()

# Prepare files for Apps Script
files = [
    {
        "name": "appsscript",
        "type": "JSON",
        "source": json.dumps({
            "timeZone": "Europe/London",
            "oauthScopes": [
                "https://www.googleapis.com/auth/spreadsheets.currentonly",
                "https://www.googleapis.com/auth/script.container.ui"
            ],
            "exceptionLogging": "STACKDRIVER"
        }, indent=2)
    },
    {
        "name": "Code",
        "type": "SERVER_JS",
        "source": code_content
    }
]

print("=" * 80)
print("DEPLOYING TO APPS SCRIPT VIA API")
print("=" * 80)

try:
    # Load credentials
    creds = service_account.Credentials.from_service_account_file(
        CREDENTIALS_FILE,
        scopes=SCOPES
    )
    print("✅ Credentials loaded")
    
    # Build service
    script_service = build('script', 'v1', credentials=creds)
    print("✅ Apps Script API initialized")
    
    # Update content
    print(f"\n📤 Uploading to script: {SCRIPT_ID}")
    request = {"files": files}
    
    response = script_service.projects().updateContent(
        scriptId=SCRIPT_ID,
        body=request
    ).execute()
    
    print("✅ Code uploaded successfully!")
    print(f"\n🔗 Open script: https://script.google.com/d/{SCRIPT_ID}/edit")
    print(f"🔗 Open spreadsheet: https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}")
    
    print("\n" + "=" * 80)
    print("NEXT STEPS")
    print("=" * 80)
    print("1. Open your Google Sheet")
    print("2. Close and reopen the sheet")
    print("3. Look for '🗺️ Constraint Map' menu")
    print("4. Click 'Show Live Map'")
    print("\nIf menu doesn't appear:")
    print("- Go to Extensions → Apps Script")
    print("- Run function: onOpen")
    print("- Authorize when prompted")
    
except HttpError as e:
    print(f"❌ Error: {e}")
    print("\n⚠️  Service accounts may have limited Apps Script API access")
    print("   Try using OAuth2 user credentials or manual upload")
except Exception as e:
    print(f"❌ Error: {e}")

#!/usr/bin/env python3
"""
Quick test to verify workspace-credentials.json works for Sheets access
"""

from google.oauth2 import service_account
import gspread

print("=" * 80)
print("🧪 Testing workspace-credentials.json with Sheets")
print("=" * 80)
print()

try:
    print("🔑 Loading credentials...")
    creds = service_account.Credentials.from_service_account_file(
        'workspace-credentials.json',
        scopes=['https://www.googleapis.com/auth/spreadsheets']
    ).with_subject('george@upowerenergy.uk')
    
    print(f"   Service Account: {creds.service_account_email}")
    print(f"   Impersonating: george@upowerenergy.uk")
    print()
    
    print("📊 Connecting to Sheets...")
    gc = gspread.authorize(creds)
    
    print("✅ gspread client created successfully!")
    print()
    
    print("🎯 Testing with GB Energy Dashboard...")
    spreadsheet = gc.open_by_key('12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8')
    
    print(f"✅ SUCCESS! Can access: {spreadsheet.title}")
    print(f"   Worksheets: {len(spreadsheet.worksheets())}")
    print()
    
    print("=" * 80)
    print("🎉 WORKSPACE CREDENTIALS WORKING!")
    print("=" * 80)
    print()
    print("✅ You can now use workspace-credentials.json in your scripts!")
    print()
    print("Example usage:")
    print("─" * 80)
    print("from google.oauth2 import service_account")
    print("import gspread")
    print()
    print("creds = service_account.Credentials.from_service_account_file(")
    print("    'workspace-credentials.json',")
    print("    scopes=['https://www.googleapis.com/auth/spreadsheets']")
    print(").with_subject('george@upowerenergy.uk')")
    print()
    print("gc = gspread.authorize(creds)")
    print("spreadsheet = gc.open_by_key('YOUR_SHEET_ID')")
    print("─" * 80)
    
except FileNotFoundError:
    print("❌ workspace-credentials.json not found")
    print("   Did you copy it? Run:")
    print("   cp ~/Overarch\\ Jibber\\ Jabber/gridsmart_service_account.json \\")
    print("      ~/GB\\ Power\\ Market\\ JJ/workspace-credentials.json")
    
except Exception as e:
    print(f"❌ Error: {e}")
    print()
    print("Possible causes:")
    print("1. Missing gspread library: pip3 install --user gspread")
    print("2. Sheets scope not authorized in Workspace Admin")
    print("3. File permissions issue")

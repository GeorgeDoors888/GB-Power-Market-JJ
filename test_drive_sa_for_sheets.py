#!/usr/bin/env python3
"""
Test if Drive Indexer service account can access Google Sheets with delegation.

This tests whether we can reuse the existing gridsmart_service_account.json
(which already has Drive delegation working) for Sheets access.

If this works, you don't need to create a new service account!
"""

import sys
from pathlib import Path

print("=" * 80)
print("🧪 TESTING: Can Drive Indexer Service Account Access Sheets?")
print("=" * 80)
print()

# Check if credentials file exists - try multiple locations
possible_paths = [
    Path.home() / "Overarch Jibber Jabber" / "gridsmart_service_account.json",
    Path(__file__).parent / "overarch-jibber-jabber" / "gridsmart_service_account.json",
    Path(__file__).parent / "drive-bq-indexer" / "gridsmart_service_account.json",
]

creds_path = None
for path in possible_paths:
    if path.exists():
        creds_path = path
        break

if not creds_path:
    print("❌ Credentials file not found in any expected location:")
    print()
    for p in possible_paths:
        print(f"   {p}")
    print()
    print("Please ensure gridsmart_service_account.json exists in one of these locations.")
    sys.exit(1)

print(f"✅ Found credentials: {creds_path}")
print()

# Try to import required libraries
try:
    from google.oauth2 import service_account
    import gspread
    print("✅ Required libraries installed")
    print()
except ImportError as e:
    print(f"❌ Missing library: {e}")
    print()
    print("Install with:")
    print("  pip3 install --user google-auth gspread")
    sys.exit(1)

# Load credentials with Sheets scope
print("🔑 Loading service account credentials...")
try:
    creds = service_account.Credentials.from_service_account_file(
        str(creds_path),
        scopes=['https://www.googleapis.com/auth/spreadsheets']
    )
    print(f"   Service Account: {creds.service_account_email}")
    print()
except Exception as e:
    print(f"❌ Failed to load credentials: {e}")
    sys.exit(1)

# Add delegation (impersonate admin user)
print("👤 Adding domain-wide delegation...")
ADMIN_EMAIL = 'george@upowerenergy.uk'
try:
    delegated_creds = creds.with_subject(ADMIN_EMAIL)
    print(f"   Impersonating: {ADMIN_EMAIL}")
    print()
except Exception as e:
    print(f"❌ Failed to add delegation: {e}")
    sys.exit(1)

# Try to access the GB Power Market dashboard
SPREADSHEET_ID = '12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8'
print("📊 Testing Sheets access...")
print(f"   Target: GB Power Market Dashboard")
print(f"   ID: {SPREADSHEET_ID}")
print()

try:
    gc = gspread.authorize(delegated_creds)
    spreadsheet = gc.open_by_key(SPREADSHEET_ID)
    
    print("✅ SUCCESS! Can access spreadsheet")
    print()
    print("   Spreadsheet Details:")
    print(f"   - Title: {spreadsheet.title}")
    print(f"   - URL: {spreadsheet.url}")
    
    # Try to list worksheets
    worksheets = spreadsheet.worksheets()
    print(f"   - Worksheets: {len(worksheets)}")
    for ws in worksheets[:5]:  # Show first 5
        print(f"      • {ws.title}")
    if len(worksheets) > 5:
        print(f"      ... and {len(worksheets) - 5} more")
    
    print()
    print("=" * 80)
    print("🎉 RESULT: Drive Indexer SA CAN access Sheets!")
    print("=" * 80)
    print()
    print("✅ What this means:")
    print("   1. You can reuse the same service account for both Drive AND Sheets")
    print("   2. No need to create a new service account")
    print("   3. Just need to add Sheets scope in Google Workspace Admin")
    print()
    print("📋 Next Steps:")
    print("   1. Go to: https://admin.google.com/ac/owl/domainwidedelegation")
    print("   2. Find Client ID: 108583076839984080568")
    print("   3. Add scope: https://www.googleapis.com/auth/spreadsheets")
    print("   4. Click 'Authorize'")
    print()
    print("   Then you can use gridsmart_service_account.json in your scripts!")
    print()
    
except gspread.exceptions.APIError as e:
    if 'PERMISSION_DENIED' in str(e) or 'insufficient authentication scopes' in str(e).lower():
        print("⚠️  PARTIAL SUCCESS - Delegation works, but scope not authorized")
        print()
        print("   Error:", str(e))
        print()
        print("=" * 80)
        print("🔧 RESULT: Need to add Sheets scope in Admin Console")
        print("=" * 80)
        print()
        print("✅ Good news: Domain-wide delegation is working!")
        print("⚠️  Issue: Sheets scope not authorized yet")
        print()
        print("📋 Fix (5 minutes):")
        print("   1. Go to: https://admin.google.com/ac/owl/domainwidedelegation")
        print("   2. Find entry with Client ID: 108583076839984080568")
        print("   3. Click 'Edit'")
        print("   4. Add this scope (comma-separated or new line):")
        print("      https://www.googleapis.com/auth/spreadsheets")
        print("   5. Click 'Authorize'")
        print("   6. Wait 5 minutes for changes to propagate")
        print("   7. Run this test again")
        print()
        sys.exit(2)
    else:
        raise

except Exception as e:
    print(f"❌ FAILED: Cannot access spreadsheet")
    print()
    print(f"   Error: {e}")
    print(f"   Type: {type(e).__name__}")
    print()
    print("=" * 80)
    print("🔧 RESULT: Need to set up domain-wide delegation for Sheets")
    print("=" * 80)
    print()
    print("❌ Delegation not working for this service account + Sheets")
    print()
    print("📋 Options:")
    print()
    print("   Option A: Add Sheets to existing delegation")
    print("   1. Go to: https://admin.google.com/ac/owl/domainwidedelegation")
    print("   2. Find: jibber-jabber-knowledge@appspot.gserviceaccount.com")
    print("   3. Add scope: https://www.googleapis.com/auth/spreadsheets")
    print()
    print("   Option B: Create new service account (recommended if Option A complex)")
    print("   1. Follow: WORKSPACE_SERVICE_ACCOUNT_SETUP.md")
    print("   2. Create fresh SA with Sheets access from the start")
    print()
    sys.exit(1)

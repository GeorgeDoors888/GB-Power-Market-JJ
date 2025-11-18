#!/usr/bin/env python3
"""
Comprehensive test of workspace-credentials.json for ALL Google services:
- Google Sheets ✓
- Google Drive ✓
- Google Docs
- Apps Script
"""

from google.oauth2 import service_account
import os
from pathlib import Path

# Try to import all libraries
try:
    import gspread
    GSPREAD_AVAILABLE = True
except ImportError:
    GSPREAD_AVAILABLE = False
    print("⚠️  gspread not installed: pip3 install --user gspread")

try:
    from googleapiclient.discovery import build
    GOOGLE_API_AVAILABLE = True
except ImportError:
    GOOGLE_API_AVAILABLE = False
    print("⚠️  google-api-python-client not installed: pip3 install --user google-api-python-client")

print("=" * 80)
print("🧪 TESTING ALL GOOGLE SERVICES WITH WORKSPACE DELEGATION")
print("=" * 80)
print()

# Find credentials
possible_paths = [
    Path.home() / 'Overarch Jibber Jabber' / 'gridsmart_service_account.json',
    Path(__file__).parent / 'workspace-credentials.json',
]

creds_file = None
for path in possible_paths:
    if path.exists():
        creds_file = path
        break

if not creds_file:
    print("❌ Credentials not found in any of these locations:")
    for p in possible_paths:
        print(f"   - {p}")
    exit(1)

print(f"✅ Found credentials: {creds_file}")
print()

# Load service account details
import json
with open(creds_file, 'r') as f:
    sa_data = json.load(f)
    
print(f"🔑 Service Account: {sa_data.get('client_email')}")
print(f"📋 Client ID: {sa_data.get('client_id')}")
print()

admin_email = 'george@upowerenergy.uk'
print(f"👤 Will impersonate: {admin_email}")
print()

print("=" * 80)
print("📊 TEST 1: Google Sheets")
print("=" * 80)

if GSPREAD_AVAILABLE:
    try:
        sheets_creds = service_account.Credentials.from_service_account_file(
            str(creds_file),
            scopes=['https://www.googleapis.com/auth/spreadsheets']
        ).with_subject(admin_email)
        
        gc = gspread.authorize(sheets_creds)
        spreadsheet = gc.open_by_key('12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8')
        
        print(f"✅ SUCCESS - Can access Sheets!")
        print(f"   Title: {spreadsheet.title}")
        print(f"   Worksheets: {len(spreadsheet.worksheets())}")
        print(f"   Scope: https://www.googleapis.com/auth/spreadsheets")
    except Exception as e:
        print(f"❌ FAILED - Sheets access denied")
        print(f"   Error: {e}")
        print(f"   Scope needed: https://www.googleapis.com/auth/spreadsheets")
else:
    print("⚠️  Skipped (gspread not installed)")

print()

print("=" * 80)
print("📁 TEST 2: Google Drive")
print("=" * 80)

if GOOGLE_API_AVAILABLE:
    try:
        drive_creds = service_account.Credentials.from_service_account_file(
            str(creds_file),
            scopes=['https://www.googleapis.com/auth/drive.readonly']
        ).with_subject(admin_email)
        
        drive_service = build('drive', 'v3', credentials=drive_creds)
        
        # List first 10 files
        results = drive_service.files().list(
            pageSize=10,
            fields="files(id, name, mimeType)"
        ).execute()
        
        files = results.get('files', [])
        
        print(f"✅ SUCCESS - Can access Drive!")
        print(f"   Files found: {len(files)}")
        if files:
            print(f"   First file: {files[0].get('name')}")
        print(f"   Scope: https://www.googleapis.com/auth/drive.readonly")
    except Exception as e:
        print(f"❌ FAILED - Drive access denied")
        print(f"   Error: {e}")
        print(f"   Scope needed: https://www.googleapis.com/auth/drive.readonly")
else:
    print("⚠️  Skipped (google-api-python-client not installed)")

print()

print("=" * 80)
print("📝 TEST 3: Google Docs")
print("=" * 80)

if GOOGLE_API_AVAILABLE:
    try:
        docs_creds = service_account.Credentials.from_service_account_file(
            str(creds_file),
            scopes=['https://www.googleapis.com/auth/documents']
        ).with_subject(admin_email)
        
        docs_service = build('docs', 'v1', credentials=docs_creds)
        
        # Try to access a test document (we'll use the spreadsheet ID as fallback test)
        # For real test, you'd need a Google Doc ID
        print(f"⚠️  PARTIAL TEST - Service created successfully")
        print(f"   Scope: https://www.googleapis.com/auth/documents")
        print(f"   Note: Need a Google Doc ID to fully test")
        print(f"   Service object: {type(docs_service).__name__}")
        
    except Exception as e:
        print(f"❌ FAILED - Docs access denied")
        print(f"   Error: {e}")
        print(f"   Scope needed: https://www.googleapis.com/auth/documents")
else:
    print("⚠️  Skipped (google-api-python-client not installed)")

print()

print("=" * 80)
print("🔧 TEST 4: Apps Script")
print("=" * 80)

if GOOGLE_API_AVAILABLE:
    try:
        script_creds = service_account.Credentials.from_service_account_file(
            str(creds_file),
            scopes=['https://www.googleapis.com/auth/script.projects']
        ).with_subject(admin_email)
        
        script_service = build('script', 'v1', credentials=script_creds)
        
        # Apps Script API doesn't have a simple list endpoint
        # Just verify the service was created successfully
        print(f"✅ SUCCESS - Apps Script service created!")
        print(f"   Scope: https://www.googleapis.com/auth/script.projects")
        print(f"   Service: {type(script_service).__name__}")
        print(f"   Note: Full test requires script project ID")
        
    except Exception as e:
        print(f"❌ FAILED - Apps Script access denied")
        print(f"   Error: {e}")
        print(f"   Scope needed: https://www.googleapis.com/auth/script.projects")
else:
    print("⚠️  Skipped (google-api-python-client not installed)")

print()
print("=" * 80)
print("📋 SUMMARY")
print("=" * 80)
print()
print("To enable ALL scopes, go to Workspace Admin:")
print("URL: https://admin.google.com/ac/owl/domainwidedelegation")
print(f"Client ID: {sa_data.get('client_id')}")
print()
print("Add these scopes (comma-separated):")
print("─" * 80)
print("https://www.googleapis.com/auth/spreadsheets,")
print("https://www.googleapis.com/auth/drive.readonly,")
print("https://www.googleapis.com/auth/drive,")
print("https://www.googleapis.com/auth/documents,")
print("https://www.googleapis.com/auth/script.projects")
print("─" * 80)
print()
print("⚠️  NOTE: Do NOT add bigquery scope!")
print("   BigQuery is separate company (Smart Grid)")
print("   Uses inner-cinema-credentials.json instead")
print()
print("Then click 'Authorize' and wait 5-10 minutes for propagation.")
print()

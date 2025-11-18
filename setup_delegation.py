#!/usr/bin/env python3
"""
Domain-Wide Delegation Setup for GB Power Market
=================================================
This script updates your service account to use domain-wide delegation
for accessing Google Sheets, Docs, and Apps Script.

BEFORE RUNNING:
1. Go to: https://console.cloud.google.com/iam-admin/serviceaccounts?project=inner-cinema-476211-u9
2. Click on: all-jibber@inner-cinema-476211-u9.iam.gserviceaccount.com
3. Enable "Google Workspace Domain-wide Delegation"
4. Note the Client ID (will be displayed)

THEN:
5. Go to: https://admin.google.com/ac/owl/domainwidedelegation
6. Click "Add new" (or edit existing)
7. Enter Client ID from step 4
8. OAuth Scopes: https://www.googleapis.com/auth/spreadsheets,https://www.googleapis.com/auth/documents,https://www.googleapis.com/auth/drive.readonly,https://www.googleapis.com/auth/script.projects
9. Click "Authorize"

FINALLY:
10. Update your .env file with GOOGLE_WORKSPACE_ADMIN_EMAIL
11. Run this script to verify setup
"""

import os
import json
from google.oauth2 import service_account
from google.cloud import bigquery
import gspread

# Configuration
PROJECT_ID = "inner-cinema-476211-u9"
CREDENTIALS_FILE = "inner-cinema-credentials.json"
ADMIN_EMAIL = os.environ.get("GOOGLE_WORKSPACE_ADMIN_EMAIL", "george@upowerenergy.uk")

# Scopes for domain-wide delegation
SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',      # Sheets access
    'https://www.googleapis.com/auth/documents',         # Docs access
    'https://www.googleapis.com/auth/drive.readonly',    # Read Drive files
    'https://www.googleapis.com/auth/script.projects',   # Apps Script access
    'https://www.googleapis.com/auth/bigquery'           # BigQuery (already working)
]

def print_header(title):
    print(f"\n{'='*70}")
    print(f"🔍 {title}")
    print(f"{'='*70}")

def check_credentials_file():
    """Check if credentials file exists and extract Client ID"""
    print_header("STEP 1: Check Credentials File")
    
    if not os.path.exists(CREDENTIALS_FILE):
        print(f"❌ Credentials file not found: {CREDENTIALS_FILE}")
        return None
    
    with open(CREDENTIALS_FILE, 'r') as f:
        creds_data = json.load(f)
    
    client_id = creds_data.get('client_id')
    client_email = creds_data.get('client_email')
    
    print(f"✅ Credentials file found")
    print(f"   Email: {client_email}")
    print(f"   Client ID: {client_id}")
    print(f"\n📋 Save this Client ID - you'll need it in Google Workspace Admin!")
    
    return client_id

def test_standard_auth():
    """Test standard authentication (current setup)"""
    print_header("STEP 2: Test Standard Authentication")
    
    try:
        creds = service_account.Credentials.from_service_account_file(
            CREDENTIALS_FILE,
            scopes=SCOPES
        )
        
        # Test BigQuery
        bq_client = bigquery.Client(project=PROJECT_ID, credentials=creds)
        datasets = list(bq_client.list_datasets())
        print(f"✅ Standard auth working")
        print(f"   BigQuery datasets: {len(datasets)}")
        
        # Test Sheets (will only see explicitly shared sheets)
        gc = gspread.authorize(creds)
        sheets = gc.openall()
        print(f"   Sheets accessible: {len(sheets)}")
        print(f"   (Only explicitly shared sheets visible)")
        
        return True
        
    except Exception as e:
        print(f"❌ Standard auth failed: {e}")
        return False

def test_delegated_auth():
    """Test domain-wide delegation (if configured)"""
    print_header("STEP 3: Test Domain-Wide Delegation")
    
    try:
        # Load credentials
        creds = service_account.Credentials.from_service_account_file(
            CREDENTIALS_FILE,
            scopes=SCOPES
        )
        
        # Create delegated credentials
        print(f"🔐 Attempting to impersonate: {ADMIN_EMAIL}")
        delegated_creds = creds.with_subject(ADMIN_EMAIL)
        
        # Test BigQuery with delegation
        bq_client = bigquery.Client(project=PROJECT_ID, credentials=delegated_creds)
        datasets = list(bq_client.list_datasets())
        print(f"✅ Delegated BigQuery working: {len(datasets)} datasets")
        
        # Test Sheets with delegation
        gc = gspread.authorize(delegated_creds)
        sheets = gc.openall()
        print(f"✅ Delegated Sheets working: {len(sheets)} sheets accessible")
        print(f"   (All sheets {ADMIN_EMAIL} can access)")
        
        # Show sample sheets
        if sheets:
            print(f"\n📊 Sample accessible sheets:")
            for sheet in sheets[:5]:
                print(f"   - {sheet.title}")
        
        return True
        
    except Exception as e:
        error_msg = str(e)
        
        if "unauthorized_client" in error_msg.lower():
            print(f"⚠️  Domain-wide delegation NOT YET configured")
            print(f"\n📋 TO ENABLE DELEGATION:")
            print(f"   1. Enable delegation in GCP Console")
            print(f"   2. Authorize in Google Workspace Admin")
            print(f"   3. Wait 5-10 minutes for propagation")
            print(f"   4. Run this script again")
            return False
        else:
            print(f"❌ Delegation test failed: {e}")
            return False

def print_setup_instructions(client_id):
    """Print detailed setup instructions"""
    print_header("SETUP INSTRUCTIONS")
    
    print(f"""
🔧 How to Enable Domain-Wide Delegation:

STEP 1: Enable in GCP Console (2 minutes)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
URL: https://console.cloud.google.com/iam-admin/serviceaccounts?project={PROJECT_ID}

1. Click on: all-jibber@inner-cinema-476211-u9.iam.gserviceaccount.com
2. Click "SHOW ADVANCED SETTINGS" or "DETAILS"
3. Find "Domain-wide delegation" section
4. Click "ENABLE G SUITE DOMAIN-WIDE DELEGATION" (or similar)
5. Note the Client ID: {client_id}

STEP 2: Authorize in Google Workspace Admin (3 minutes)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
URL: https://admin.google.com/ac/owl/domainwidedelegation

1. Click "Add new" (or "Edit" if already exists)
2. Client ID: {client_id}
3. OAuth Scopes (copy-paste all): 
   https://www.googleapis.com/auth/spreadsheets,https://www.googleapis.com/auth/documents,https://www.googleapis.com/auth/drive.readonly,https://www.googleapis.com/auth/script.projects,https://www.googleapis.com/auth/bigquery
4. Click "Authorize"

STEP 3: Configure Environment
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Add to your .env file or environment:

export GOOGLE_WORKSPACE_ADMIN_EMAIL="george@upowerenergy.uk"

Or in Python scripts:
os.environ['GOOGLE_WORKSPACE_ADMIN_EMAIL'] = 'george@upowerenergy.uk'

STEP 4: Wait and Verify
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. Wait 5-10 minutes for changes to propagate
2. Run this script again: python3 setup_delegation.py
3. Should see "✅ Delegated Sheets working"

⚠️  IMPORTANT NOTES:
- Domain-wide delegation requires Google Workspace (not personal Gmail)
- You must be a Workspace admin to authorize in Step 2
- Changes can take up to 20 minutes to propagate
- Keep credentials secure - delegation is powerful!
""")

def main():
    print(f"""
╔══════════════════════════════════════════════════════════════════════╗
║         Domain-Wide Delegation Setup for GB Power Market             ║
╚══════════════════════════════════════════════════════════════════════╝

This script will:
1. Check your credentials file
2. Test standard authentication (current setup)
3. Test domain-wide delegation (if configured)
4. Provide setup instructions if needed

Admin Email: {ADMIN_EMAIL}
""")
    
    # Check credentials
    client_id = check_credentials_file()
    if not client_id:
        return
    
    # Test standard auth
    standard_works = test_standard_auth()
    if not standard_works:
        print("\n❌ Standard authentication is not working. Fix this first!")
        return
    
    # Test delegated auth
    delegation_works = test_delegated_auth()
    
    # Print instructions if delegation not working
    if not delegation_works:
        print_setup_instructions(client_id)
    else:
        print(f"""
╔══════════════════════════════════════════════════════════════════════╗
║              🎉 DOMAIN-WIDE DELEGATION IS WORKING! 🎉                ║
╚══════════════════════════════════════════════════════════════════════╝

✅ Your service account can now access:
   • All Sheets {ADMIN_EMAIL} can access
   • All Docs {ADMIN_EMAIL} can access  
   • All Drive files (read-only)
   • Apps Script projects

🔄 Next Steps:
   1. Update your scripts to use delegated credentials
   2. Run: python3 update_all_scripts_for_delegation.py
   3. Test with: python3 test_delegation_access.py

📚 See: DOMAIN_DELEGATION_IMPLEMENTATION.md for details
""")

if __name__ == "__main__":
    main()

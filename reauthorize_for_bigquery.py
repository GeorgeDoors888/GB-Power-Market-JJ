#!/usr/bin/env python3
"""
Re-authorize OAuth with BigQuery scope
Make sure to use the Smart Grid account (not upowerenergy.uk)
"""

import os
import pickle
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

# All required scopes including BigQuery
SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive',
    'https://www.googleapis.com/auth/bigquery',
    'https://www.googleapis.com/auth/bigquery.readonly'
]

def main():
    print("=" * 60)
    print("🔐 OAuth Re-authorization for BigQuery Access")
    print("=" * 60)
    print()
    print("⚠️  IMPORTANT: When browser opens, use SMART GRID account")
    print("   (NOT upowerenergy.uk)")
    print()
    
    # Remove old token to force fresh authorization
    if os.path.exists('token.pickle'):
        backup = 'token.pickle.backup'
        os.rename('token.pickle', backup)
        print(f"✅ Backed up old token to {backup}")
    
    # Check for credentials.json
    if not os.path.exists('credentials.json'):
        print("❌ ERROR: credentials.json not found!")
        print("   Please ensure credentials.json is in the current directory")
        return
    
    print("\n🌐 Opening browser for authorization...")
    print("   Scopes being requested:")
    for scope in SCOPES:
        print(f"   - {scope}")
    print()
    
    # Start OAuth flow
    flow = InstalledAppFlow.from_client_secrets_file(
        'credentials.json', 
        SCOPES
    )
    
    # This will open the browser
    creds = flow.run_local_server(port=0)
    
    # Save the credentials
    with open('token.pickle', 'wb') as token:
        pickle.dump(creds, token)
    
    print()
    print("=" * 60)
    print("✅ Authorization complete!")
    print("=" * 60)
    print(f"📋 Token saved to: token.pickle")
    print(f"🔑 Account: {creds._id_token.get('email', 'Unknown') if hasattr(creds, '_id_token') else 'Authorized'}")
    print()
    print("You can now run automated_iris_dashboard.py")
    print()

if __name__ == "__main__":
    main()

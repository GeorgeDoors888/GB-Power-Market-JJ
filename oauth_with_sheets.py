#!/usr/bin/env python3
"""
Re-authorize OAuth with Google Sheets API scope included
This will allow creating Google Sheets in YOUR Drive (7TB available!)
"""

from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import pickle
import os

# Scopes needed for both Drive AND Sheets
SCOPES = [
    'https://www.googleapis.com/auth/drive',
    'https://www.googleapis.com/auth/drive.file',
    'https://www.googleapis.com/auth/spreadsheets'
]

def main():
    print("🔐 OAuth Re-Authorization with Sheets Scope")
    print("="*80)
    print("\nScopes being requested:")
    for scope in SCOPES:
        print(f"  ✓ {scope}")
    
    creds = None
    
    # Delete old token to force re-authorization
    if os.path.exists('token.pickle'):
        print("\n🗑️  Removing old token.pickle...")
        os.remove('token.pickle')
    
    # Check for credentials.json
    if not os.path.exists('credentials.json'):
        print("\n❌ ERROR: credentials.json not found!")
        print("\nPlease ensure credentials.json exists in the current directory.")
        print("This file contains your OAuth 2.0 Client ID credentials.")
        return
    
    print("\n🌐 Starting OAuth flow...")
    print("\nA browser window will open for you to:")
    print("  1. Select your Google account (@upowerenergy.co.uk)")
    print("  2. Grant access to:")
    print("     - Google Drive (read/write files)")
    print("     - Google Sheets (create/edit spreadsheets)")
    print("\n⏳ Waiting for authorization...")
    
    flow = InstalledAppFlow.from_client_secrets_file(
        'credentials.json', 
        SCOPES
    )
    
    # This will open a browser window
    creds = flow.run_local_server(port=0)
    
    # Save the credentials for future use
    print("\n💾 Saving credentials to token.pickle...")
    with open('token.pickle', 'wb') as token:
        pickle.dump(creds, token)
    
    print("\n" + "="*80)
    print("✅ AUTHORIZATION SUCCESSFUL!")
    print("="*80)
    print("\n📋 New scopes authorized:")
    for scope in SCOPES:
        print(f"  ✓ {scope}")
    
    print("\n🎯 You can now:")
    print("  • Access Google Drive files")
    print("  • Create Google Sheets")
    print("  • Edit existing spreadsheets")
    
    print("\n💡 The token is saved in token.pickle")
    print("   You won't need to re-authorize unless the token expires.")
    
    print("\n" + "="*80)

if __name__ == '__main__':
    main()

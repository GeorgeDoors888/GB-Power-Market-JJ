#!/usr/bin/env python3
"""
Manual OAuth Re-authorization for BigQuery
Uses manual code entry instead of callback server
"""

import os
import pickle
from google_auth_oauthlib.flow import InstalledAppFlow

# All required scopes including BigQuery
SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive',
    'https://www.googleapis.com/auth/bigquery',
    'https://www.googleapis.com/auth/bigquery.readonly'
]

def main():
    print("=" * 60)
    print("🔐 OAuth Re-authorization for BigQuery Access (Manual)")
    print("=" * 60)
    print()
    print("⚠️  IMPORTANT: Use SMART GRID account when authorizing")
    print()
    
    # Backup old token
    if os.path.exists('token.pickle'):
        backup = 'token.pickle.backup'
        if os.path.exists(backup):
            os.remove(backup)
        os.rename('token.pickle', backup)
        print(f"✅ Backed up old token to {backup}")
    
    # Check for credentials.json
    if not os.path.exists('credentials.json'):
        print("❌ ERROR: credentials.json not found!")
        return
    
    print("\n📋 Requesting authorization with scopes:")
    for scope in SCOPES:
        print(f"   - {scope.split('/')[-1]}")
    print()
    
    # Start OAuth flow with manual code entry
    flow = InstalledAppFlow.from_client_secrets_file(
        'credentials.json', 
        SCOPES,
        redirect_uri='urn:ietf:wg:oauth:2.0:oob'  # Manual code entry
    )
    
    # Get authorization URL
    auth_url, _ = flow.authorization_url(prompt='consent')
    
    print("🌐 STEP 1: Copy this URL and open it in your browser:")
    print()
    print(auth_url)
    print()
    print("🔑 STEP 2: After authorizing, copy the code and paste below")
    print()
    
    # Get code from user
    code = input("Enter authorization code: ").strip()
    
    # Exchange code for credentials
    print("\n🔄 Exchanging code for credentials...")
    flow.fetch_token(code=code)
    creds = flow.credentials
    
    # Save the credentials
    with open('token.pickle', 'wb') as token:
        pickle.dump(creds, token)
    
    print()
    print("=" * 60)
    print("✅ Authorization complete!")
    print("=" * 60)
    print(f"📋 Token saved to: token.pickle")
    print()
    print("You can now run automated_iris_dashboard.py")
    print()

if __name__ == "__main__":
    main()

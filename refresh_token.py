#!/usr/bin/env python3
"""
Refresh Google OAuth Token
Regenerates token.pickle for Google API access
"""

from google_auth_oauthlib.flow import InstalledAppFlow
import pickle

# Scopes needed for all operations
SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive',
    'https://www.googleapis.com/auth/documents'
]

print("=" * 80)
print("🔑 GOOGLE API TOKEN REFRESH")
print("=" * 80)
print()
print("This will open a browser window for authentication.")
print("Please log in with your Google account and grant permissions.")
print()
print("Required scopes:")
for scope in SCOPES:
    print(f"  ✓ {scope}")
print()
input("Press Enter to continue...")

try:
    # Run OAuth flow
    flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
    creds = flow.run_local_server(port=0)
    
    # Save token
    with open('token.pickle', 'wb') as f:
        pickle.dump(creds, f)
    
    print()
    print("=" * 80)
    print("✅ SUCCESS!")
    print("=" * 80)
    print()
    print("Token saved to token.pickle")
    print("You can now run your scripts.")
    
except FileNotFoundError:
    print()
    print("❌ ERROR: credentials.json not found")
    print()
    print("Please ensure credentials.json exists in the current directory.")
    print("This should be your OAuth 2.0 Client ID credentials from Google Cloud Console.")
    
except Exception as e:
    print()
    print(f"❌ ERROR: {e}")
    print()
    print("Make sure you have:")
    print("  1. credentials.json in current directory")
    print("  2. OAuth 2.0 credentials (not service account)")
    print("  3. Google Sheets, Drive, and Docs APIs enabled")

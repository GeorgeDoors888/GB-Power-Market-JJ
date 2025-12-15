#!/usr/bin/env python3
"""
Deploy fixed chart script to Apps Script
"""

import pickle
import os
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

SPREADSHEET_ID = '1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA'
SCRIPT_ID = '1wJuJJSlS-_XjwXBd92fax7THLVbpnjBlhL3HkflsLjUTYkfdsua1YMoS'

print("\n🔧 Updating Apps Script with fixed chart code...")
print("=" * 60)

# Load OAuth credentials
creds = None
if os.path.exists('token.pickle'):
    with open('token.pickle', 'rb') as token:
        creds = pickle.load(token)

if not creds or not creds.valid:
    if creds and creds.expired and creds.refresh_token:
        print("🔄 Refreshing token...")
        creds.refresh(Request())
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

# Read the fixed script
with open('dashboard/apps-script/dashboard_charts_v3_fixed.gs', 'r') as f:
    script_content = f.read()

print(f"✅ Read fixed script ({len(script_content)} characters)")

# Update the script
script_service = build('script', 'v1', credentials=creds)

try:
    # Get current project
    project = script_service.projects().get(scriptId=SCRIPT_ID).execute()
    
    # Update content
    request = {
        'files': [{
            'name': 'Code',
            'type': 'SERVER_JS',
            'source': script_content
        }]
    }
    
    response = script_service.projects().updateContent(
        scriptId=SCRIPT_ID,
        body=request
    ).execute()
    
    print("✅ Apps Script updated successfully!")
    print("\n" + "=" * 60)
    print("🎯 Next: Run createDashboardCharts() in Apps Script")
    print("   Link: https://script.google.com/d/" + SCRIPT_ID + "/edit")
    print("=" * 60)
    
except Exception as e:
    print(f"❌ Error: {e}")
    print("\n📋 Manual deployment required:")
    print("1. Open: https://script.google.com/d/" + SCRIPT_ID + "/edit")
    print("2. Delete all code")
    print("3. Copy from: dashboard/apps-script/dashboard_charts_v3_fixed.gs")
    print("4. Paste and Save")
    print("5. Run createDashboardCharts()")

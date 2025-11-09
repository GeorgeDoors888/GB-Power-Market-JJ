#!/usr/bin/env python3
"""
Deploy fixed Apps Script and execute createDashboardCharts
"""

import gspread
from oauth2client.service_account import ServiceAccountCredentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import pickle
import os
import logging

logging.basicConfig(level=logging.INFO, format='%(message)s')

SPREADSHEET_ID = '12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8'
SCRIPT_ID = '1wJuJJSlS-_XjwXBd92fax7THLVbpnjBlhL3HkflsLjUTYkfdsua1YMoS'

print("\n" + "=" * 70)
print("📊 DEPLOYING FIXED APPS SCRIPT & EXECUTING CHART CREATION")
print("=" * 70)

# Step 1: Load OAuth credentials
print("\n📋 Step 1: Loading OAuth credentials...")
if not os.path.exists('token.pickle'):
    print("❌ token.pickle not found! Run authenticate script first.")
    exit(1)

with open('token.pickle', 'rb') as token:
    creds = pickle.load(token)

print("✅ OAuth credentials loaded")

# Step 2: Read the fixed script
print("\n📋 Step 2: Reading fixed Apps Script code...")
script_file = 'dashboard/apps-script/dashboard_charts_v3_final.gs'
if not os.path.exists(script_file):
    print(f"❌ {script_file} not found!")
    exit(1)

with open(script_file, 'r') as f:
    script_content = f.read()

print(f"✅ Read {len(script_content)} characters from {script_file}")

# Step 3: Deploy to Apps Script
print("\n📋 Step 3: Deploying to Apps Script API...")

try:
    service = build('script', 'v1', credentials=creds)
    
    # Update the script content with manifest
    request_body = {
        'files': [
            {
                'name': 'appsscript',
                'type': 'JSON',
                'source': '''{
  "timeZone": "Europe/London",
  "dependencies": {},
  "exceptionLogging": "STACKDRIVER",
  "runtimeVersion": "V8",
  "oauthScopes": [
    "https://www.googleapis.com/auth/spreadsheets.currentonly",
    "https://www.googleapis.com/auth/spreadsheets"
  ]
}'''
            },
            {
                'name': 'Code',
                'type': 'SERVER_JS',
                'source': script_content
            }
        ]
    }
    
    response = service.projects().updateContent(
        scriptId=SCRIPT_ID,
        body=request_body
    ).execute()
    
    print(f"✅ Script updated successfully")
    print(f"   Script ID: {SCRIPT_ID}")
    
except HttpError as e:
    print(f"❌ Failed to update script: {e}")
    exit(1)

# Step 4: Execute createDashboardCharts
print("\n📋 Step 4: Executing createDashboardCharts()...")

try:
    request_body = {
        'function': 'createDashboardCharts',
        'devMode': False
    }
    
    response = service.scripts().run(
        scriptId=SCRIPT_ID,
        body=request_body
    ).execute()
    
    if 'error' in response:
        error = response['error']['details'][0]
        print(f"❌ Execution failed:")
        print(f"   {error.get('errorMessage', 'Unknown error')}")
        print(f"\n💡 Manual step required:")
        print(f"   1. Open: https://script.google.com/d/{SCRIPT_ID}/edit")
        print(f"   2. Run: createDashboardCharts")
    else:
        print("✅ createDashboardCharts() executed successfully!")
        print("\n🎉 Charts should now be visible in your dashboard!")
        
except HttpError as e:
    print(f"⚠️  Could not execute function: {e}")
    print(f"\n💡 Manual step required:")
    print(f"   1. Open: https://script.google.com/d/{SCRIPT_ID}/edit")
    print(f"   2. Run: createDashboardCharts")

print("\n" + "=" * 70)
print("📊 View Dashboard:")
print(f"   https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/")
print("=" * 70)
print()

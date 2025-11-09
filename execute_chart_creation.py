#!/usr/bin/env python3
"""
Execute Dashboard Charts Creation
Runs the chart creation function via Apps Script API
"""

import os
import pickle
import time
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

# Configuration
SCRIPT_ID = os.environ.get('APPS_SCRIPT_ID', "1NH75y8hbrHd0H7972ooEUdi2v8ICON3IVHrOdm1aLnDIaPvdL4DVj6GR")
TOKEN_FILE = "apps_script_token.pickle"

print("🚀 Executing Dashboard Charts Creation")
print("=" * 60)

def get_credentials():
    """Load OAuth credentials"""
    if not os.path.exists(TOKEN_FILE):
        print(f"❌ Token file not found: {TOKEN_FILE}")
        print("   Run: python3 deploy_dashboard_charts.py first")
        return None
    
    with open(TOKEN_FILE, 'rb') as token:
        creds = pickle.load(token)
    
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
        with open(TOKEN_FILE, 'wb') as token:
            pickle.dump(creds, token)
    
    return creds

def main():
    try:
        print("\n📋 Loading credentials...")
        creds = get_credentials()
        
        if not creds:
            return
        
        print("✅ Credentials loaded")
        
        print("\n📋 Building Apps Script API client...")
        script_service = build('script', 'v1', credentials=creds)
        print("✅ API client ready")
        
        print(f"\n📋 Executing createDashboardCharts()...")
        print(f"   Script ID: {SCRIPT_ID}")

        request = {
            'function': 'createDashboardCharts',
            'devMode': True
        }

        # Retry loop for propagation delays (Apps Script run endpoint sometimes
        # returns 404 for newly created projects). We'll retry a few times with
        # short backoff before failing.
        max_retries = 5
        delay = 10
        response = None
        for attempt in range(1, max_retries + 1):
            try:
                print(f"   → Attempt {attempt} of {max_retries}...")
                response = script_service.scripts().run(
                    scriptId=SCRIPT_ID,
                    body=request
                ).execute()
                break
            except Exception as e:
                err = str(e)
                print(f"   ⚠️  Attempt {attempt} failed: {err}")
                if '404' in err and attempt < max_retries:
                    print(f"   ⏳ Waiting {delay} seconds before retry...")
                    time.sleep(delay)
                    delay *= 2
                    continue
                raise
        
        if 'error' in response:
            error = response['error']
            details = error.get('details', [{}])[0]
            error_message = details.get('errorMessage', 'Unknown error')
            error_type = details.get('errorType', 'Unknown type')
            
            print(f"\n❌ Execution Error:")
            print(f"   Type: {error_type}")
            print(f"   Message: {error_message}")
            
            if "Exception" in error_type:
                print(f"\n💡 This might be a script error. Check:")
                print(f"   • Data range exists in Dashboard sheet")
                print(f"   • '24-HOUR GENERATION TREND' row is present")
                print(f"   • Sheet has sufficient data")
            
            return False
        
        result = response.get('response', {}).get('result', {})
        
        print("\n✅ CHARTS CREATED SUCCESSFULLY!")
        print(f"\n📊 View Dashboard:")
        print(f"   https://docs.google.com/spreadsheets/d/12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8/")
        print(f"\n✨ 4 Interactive Charts Added:")
        print("   1. ⚡ 24-Hour Generation Trend (Line Chart)")
        print("   2. 🥧 Current Generation Mix (Pie Chart)")
        print("   3. 📊 Stacked Generation by Source (Area Chart)")
        print("   4. 📊 Top Generation Sources (Column Chart)")
        
        return True
        
    except Exception as e:
        error_str = str(e)
        print(f"\n❌ Error: {e}")
        
        if "404" in error_str:
            print("\n💡 Script not found - Try this:")
            print("   1. Wait 30 seconds for script to propagate")
            print("   2. Run this command again")
        elif "403" in error_str:
            print("\n💡 Permission error - Try this:")
            print("   1. Open script manually:")
            print(f"      https://script.google.com/d/{SCRIPT_ID}/edit")
            print("   2. Run createDashboardCharts() once manually")
            print("   3. Grant permissions")
            print("   4. Then run this script again")
        
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)

#!/usr/bin/env python3
"""
Execute Apps Script functions using Google Apps Script API
"""
import os
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'inner-cinema-credentials.json'

from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

SCOPES = [
    'https://www.googleapis.com/auth/script.projects',
    'https://www.googleapis.com/auth/spreadsheets'
]

SCRIPT_ID = "1c9BJqrtruVFh_LT_IWrHOpJIy8c29_zH6v1Co8-KHU9R1o9g2wZZERH5"

def execute_function(function_name):
    creds = Credentials.from_service_account_file(
        'inner-cinema-credentials.json',
        scopes=SCOPES
    )
    
    service = build('script', 'v1', credentials=creds)
    
    request = {"function": function_name}
    
    try:
        response = service.scripts().run(scriptId=SCRIPT_ID, body=request).execute()
        
        if 'error' in response:
            print(f"❌ Error in {function_name}:")
            print(f"   {response['error']['message']}")
            return False
        else:
            print(f"✅ {function_name} executed successfully")
            if 'response' in response:
                print(f"   Result: {response['response'].get('result')}")
            return True
            
    except Exception as error:
        print(f"❌ Exception executing {function_name}: {error}")
        return False

if __name__ == "__main__":
    print("⚡ EXECUTING APPS SCRIPT FUNCTIONS")
    print("=" * 60)
    
    print("\n1️⃣ Running formatDashboard...")
    execute_function("formatDashboard")
    
    print("\n2️⃣ Running buildAllCharts...")
    execute_function("buildAllCharts")
    
    print("\n3️⃣ Installing daily chart rebuild trigger...")
    execute_function("installDailyChartRebuild")
    
    print("\n✅ All functions executed!")

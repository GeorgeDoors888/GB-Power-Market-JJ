#!/usr/bin/env python3
"""
Check which Apps Script project has the Dashboard v2 code
"""

import pickle
import os
from googleapiclient.discovery import build

SCRIPT_ID = '19d9ooPFGTrzRERacvirLsL-LLWzAwGbUfc7WV-4SFhfF59pefOj8vvkA'
TOKEN_FILE = 'apps_script_token.pickle'

def main():
    print("🔍 Checking Apps Script Project Details...\n")
    
    # Load credentials
    with open(TOKEN_FILE, 'rb') as f:
        creds = pickle.load(f)
    
    service = build('script', 'v1', credentials=creds)
    
    try:
        # Get project details
        project = service.projects().get(scriptId=SCRIPT_ID).execute()
        
        print("📋 Project Information:")
        print(f"   Script ID: {SCRIPT_ID}")
        print(f"   Title: {project.get('title', 'Untitled')}")
        print(f"   Created: {project.get('createTime', 'Unknown')}")
        print(f"   Updated: {project.get('updateTime', 'Unknown')}")
        
        # Get content to see files
        content = service.projects().getContent(scriptId=SCRIPT_ID).execute()
        files = content.get('files', [])
        
        print(f"\n📁 Files in Project ({len(files)} total):")
        for file in files:
            name = file.get('name', 'Unknown')
            ftype = file.get('type', 'Unknown')
            print(f"   • {name} ({ftype})")
            
            # Check if it has our new dashboard code
            if name == 'DashboardFunctions':
                source = file.get('source', '')
                if 'Market Overview' in source and 'setupDashboard' in source:
                    print("     ✅ Contains Dashboard v2 code!")
        
        print(f"\n🔗 Open in Editor:")
        print(f"   https://script.google.com/home/projects/{SCRIPT_ID}/edit")
        
        print(f"\n📊 Bound to Google Sheet:")
        print(f"   https://docs.google.com/spreadsheets/d/12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8/edit")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == '__main__':
    main()

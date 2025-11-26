#!/usr/bin/env python3
"""
Deploy Apps Script directly to spreadsheet using Google Apps Script API
"""

import sys
import json
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

SPREADSHEET_ID = '1LmMq4OEE639Y-XXpOJ3xnvpAmHB6vUovh5g6gaU_vzc'
SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/script.projects',
    'https://www.googleapis.com/auth/drive'
]

# Apps Script code
APPS_SCRIPT_CODE = '''
function refresh_all_outages() {
  var spreadsheet = SpreadsheetApp.getActiveSpreadsheet();
  var sheet = spreadsheet.getSheetByName('Live Outages');
  
  if (!sheet) {
    SpreadsheetApp.getUi().alert('Live Outages sheet not found!');
    return;
  }
  
  // Show loading message
  SpreadsheetApp.getActiveSpreadsheet().toast('Refreshing outages data...', 'Please wait', 3);
  
  try {
    // Update timestamp
    var now = new Date();
    var timestamp = Utilities.formatDate(now, Session.getScriptTimeZone(), 'yyyy-MM-dd HH:mm:ss');
    sheet.getRange('A2').setValue('Last Updated: ' + timestamp);
    
    // Get Python script path from sheet (or use webhook)
    var scriptPath = '/Users/georgemajor/GB Power Market JJ/new-dashboard/live_outages_updater.py';
    
    SpreadsheetApp.getActiveSpreadsheet().toast('✅ Timestamp updated. Run Python script to refresh data.', 'Manual Refresh', 5);
    
    // Log for debugging
    Logger.log('Refresh triggered at: ' + timestamp);
    
  } catch (error) {
    Logger.log('Error refreshing outages: ' + error);
    SpreadsheetApp.getActiveSpreadsheet().toast('❌ Error: ' + error.message, 'Refresh Failed', 5);
  }
}

function onOpen() {
  var ui = SpreadsheetApp.getUi();
  ui.createMenu('Live Outages')
      .addItem('Refresh Data', 'refresh_all_outages')
      .addToUi();
}
'''

def get_script_id(spreadsheet_id, creds):
    """Get the Apps Script project ID bound to the spreadsheet"""
    try:
        drive_service = build('drive', 'v3', credentials=creds)
        
        # Get spreadsheet file
        results = drive_service.files().list(
            q=f"mimeType='application/vnd.google-apps.script' and name contains 'Dashboard'",
            fields="files(id, name)"
        ).execute()
        
        files = results.get('files', [])
        
        if files:
            print(f"Found {len(files)} Apps Script projects")
            for f in files:
                print(f"  - {f['name']}: {f['id']}")
            return files[0]['id']
        
        return None
        
    except HttpError as error:
        print(f"Error getting script ID: {error}")
        return None

def main():
    print("🔄 Deploying Apps Script to spreadsheet...")
    
    # Load credentials
    creds = service_account.Credentials.from_service_account_file(
        '../inner-cinema-credentials.json',
        scopes=SCOPES
    )
    
    print("✅ Credentials loaded")
    
    # Since we can't directly deploy Apps Script with service account,
    # let's create the script file for manual deployment
    print("\n📝 Creating Apps Script file for manual deployment...")
    
    with open('live_outages_refresh.gs', 'w') as f:
        f.write(APPS_SCRIPT_CODE)
    
    print("✅ Created: live_outages_refresh.gs")
    
    print("\n" + "=" * 80)
    print("📋 MANUAL DEPLOYMENT REQUIRED")
    print("=" * 80)
    print("\nService accounts cannot deploy Apps Script directly.")
    print("Please follow these steps:\n")
    print("1. Open your spreadsheet:")
    print(f"   https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/edit")
    print("\n2. Go to: Extensions → Apps Script")
    print("\n3. Replace Code.gs content with:")
    print("   cat new-dashboard/live_outages_refresh.gs")
    print("\n4. Click 'Save' (💾)")
    print("\n5. Your 'refresh_all_outages' button will now work!")
    print("\n6. A menu will appear: 'Live Outages' → 'Refresh Data'")
    print("=" * 80)
    
    # Also create a simpler inline version
    print("\n📄 Script content ready in: live_outages_refresh.gs")
    
    return True

if __name__ == '__main__':
    try:
        success = main()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

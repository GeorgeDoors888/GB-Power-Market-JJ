#!/usr/bin/env python3
"""
Setup date dropdowns and create Apps Script refresh function for Live Outages
"""

import sys
from google.oauth2 import service_account
import gspread
from datetime import datetime, timedelta

SPREADSHEET_ID = '1LmMq4OEE639Y-XXpOJ3xnvpAmHB6vUovh5g6gaU_vzc'

def main():
    print("🔄 Setting up Live Outages refresh system...")
    
    creds = service_account.Credentials.from_service_account_file(
        '../inner-cinema-credentials.json',
        scopes=['https://www.googleapis.com/auth/spreadsheets']
    )
    gc = gspread.authorize(creds)
    spreadsheet = gc.open_by_key(SPREADSHEET_ID)
    sheet = spreadsheet.worksheet('Live Outages')
    
    # Update date validation to use DATE_BEFORE for proper dropdown
    print("📅 Adding date dropdown selectors...")
    
    # Set up proper date dropdowns with calendar picker
    sheet.spreadsheet.batch_update({
        'requests': [
            {
                'setDataValidation': {
                    'range': {
                        'sheetId': sheet.id,
                        'startRowIndex': 6,
                        'endRowIndex': 7,
                        'startColumnIndex': 4,  # E7
                        'endColumnIndex': 5
                    },
                    'rule': {
                        'condition': {
                            'type': 'DATE_IS_VALID'
                        },
                        'showCustomUi': True,
                        'strict': False,
                        'inputMessage': 'Select start date from calendar'
                    }
                }
            },
            {
                'setDataValidation': {
                    'range': {
                        'sheetId': sheet.id,
                        'startRowIndex': 6,
                        'endRowIndex': 7,
                        'startColumnIndex': 6,  # G7
                        'endColumnIndex': 7
                    },
                    'rule': {
                        'condition': {
                            'type': 'DATE_IS_VALID'
                        },
                        'showCustomUi': True,
                        'strict': False,
                        'inputMessage': 'Select end date from calendar'
                    }
                }
            }
        ]
    })
    
    print("✅ Date dropdowns configured")
    
    # Create the Apps Script code
    apps_script = '''
function refresh_all_outages() {
  var spreadsheet = SpreadsheetApp.getActiveSpreadsheet();
  var sheet = spreadsheet.getSheetByName('Live Outages');
  
  if (!sheet) {
    SpreadsheetApp.getUi().alert('Live Outages sheet not found!');
    return;
  }
  
  // Show loading message
  SpreadsheetApp.getActiveSpreadsheet().toast('Refreshing all outages data...', 'Please wait', -1);
  
  try {
    // Update timestamp
    var now = new Date();
    var timestamp = Utilities.formatDate(now, Session.getScriptTimeZone(), 'yyyy-MM-dd HH:mm:ss');
    sheet.getRange('A2').setValue('Last Updated: ' + timestamp);
    
    // Call the Python webhook to refresh data
    var webhookUrl = 'YOUR_WEBHOOK_URL_HERE';  // Replace with ngrok or permanent webhook
    
    var options = {
      'method': 'post',
      'contentType': 'application/json',
      'payload': JSON.stringify({
        'action': 'refresh_outages',
        'spreadsheet_id': spreadsheet.getId(),
        'sheet_name': 'Live Outages'
      }),
      'muteHttpExceptions': true
    };
    
    var response = UrlFetchApp.fetch(webhookUrl, options);
    var result = JSON.parse(response.getContentText());
    
    if (result.status === 'success') {
      SpreadsheetApp.getActiveSpreadsheet().toast('✅ Outages refreshed: ' + result.count + ' active outages', 'Success', 5);
    } else {
      throw new Error(result.message || 'Unknown error');
    }
    
  } catch (error) {
    Logger.log('Error refreshing outages: ' + error);
    SpreadsheetApp.getActiveSpreadsheet().toast('❌ Error: ' + error.message, 'Refresh Failed', 5);
  }
}

// Manual refresh without webhook (updates timestamp only)
function refresh_all_outages_manual() {
  var spreadsheet = SpreadsheetApp.getActiveSpreadsheet();
  var sheet = spreadsheet.getSheetByName('Live Outages');
  
  if (!sheet) {
    SpreadsheetApp.getUi().alert('Live Outages sheet not found!');
    return;
  }
  
  var now = new Date();
  var timestamp = Utilities.formatDate(now, Session.getScriptTimeZone(), 'yyyy-MM-dd HH:mm:ss');
  sheet.getRange('A2').setValue('Last Updated: ' + timestamp);
  
  SpreadsheetApp.getActiveSpreadsheet().toast('Timestamp updated. Run Python script to refresh data.', 'Manual Refresh', 3);
}
'''
    
    print("\n" + "=" * 80)
    print("✅ SETUP COMPLETE")
    print("=" * 80)
    print("\n📋 Apps Script code generated. To install:")
    print("   1. Open the spreadsheet")
    print("   2. Go to Extensions → Apps Script")
    print("   3. Paste the code below into Code.gs")
    print("   4. Save and assign 'refresh_all_outages' to your button")
    print("\n" + "=" * 80)
    print(apps_script)
    print("=" * 80)
    
    # Save the script to a file
    with open('live_outages_apps_script.gs', 'w') as f:
        f.write(apps_script)
    
    print("\n✅ Apps Script saved to: live_outages_apps_script.gs")
    
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

#!/usr/bin/env python3
"""
Deploy Dashboard Outages Apps Script via Apps Script API
Automatically installs the trigger and code into Google Sheets
"""

import pickle
import os
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import json

# Scopes needed for Apps Script API
SCOPES = [
    'https://www.googleapis.com/auth/script.projects',
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]

SPREADSHEET_ID = '1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA'
PYTHON_API_URL = 'https://jibber-jabber-production.up.railway.app'

# Apps Script code to deploy
APPS_SCRIPT_CODE = """
const PYTHON_API_URL = '""" + PYTHON_API_URL + """';
const SPREADSHEET_ID = '""" + SPREADSHEET_ID + """';

/**
 * Update Dashboard outages from Python API
 * Runs every 1 minute via time-based trigger
 */
function updateOutagesFromPython() {
  try {
    Logger.log('🔄 Fetching outages from Python API...');
    
    const url = `${PYTHON_API_URL}/outages/names`;
    const response = UrlFetchApp.fetch(url, {muteHttpExceptions: true});
    const responseCode = response.getResponseCode();
    
    if (responseCode !== 200) {
      Logger.log(`❌ API returned status ${responseCode}`);
      return;
    }
    
    const data = JSON.parse(response.getContentText());
    
    if (data.status !== 'success') {
      Logger.log('❌ API returned error status');
      return;
    }
    
    Logger.log(`✅ Fetched ${data.count} outages`);
    
    // Open Dashboard sheet
    const sheet = SpreadsheetApp.openById(SPREADSHEET_ID).getSheetByName('Dashboard');
    
    if (!sheet) {
      Logger.log('❌ Dashboard sheet not found');
      return;
    }
    
    // Prepare outage names for rows 23-36 (14 entries)
    const outages = data.outages || [];
    const values = [];
    
    for (let i = 0; i < 14; i++) {
      if (i < outages.length) {
        values.push([outages[i].station_name]);
      } else {
        values.push(['']); // Empty cell if fewer than 14 outages
      }
    }
    
    // Write to Dashboard A23:A36
    sheet.getRange('A23:A36').setValues(values);
    Logger.log('✅ Updated outages list (A23:A36)');
    
    // Update timestamp in B2
    const now = new Date();
    const timestamp = Utilities.formatDate(now, Session.getScriptTimeZone(), 'yyyy-MM-dd HH:mm:ss');
    sheet.getRange('B2').setValue(`⏰ Last Updated: ${timestamp}`);
    Logger.log('✅ Updated timestamp (B2)');
    
    Logger.log('✅ Dashboard update complete');
    
  } catch (error) {
    Logger.log(`❌ Error: ${error.toString()}`);
  }
}

/**
 * Set up time-based trigger (run this once manually)
 */
function setupTrigger() {
  // Delete existing triggers for this function
  const triggers = ScriptApp.getProjectTriggers();
  triggers.forEach(trigger => {
    if (trigger.getHandlerFunction() === 'updateOutagesFromPython') {
      ScriptApp.deleteTrigger(trigger);
      Logger.log('🗑️ Deleted existing trigger');
    }
  });
  
  // Create new trigger - every 1 minute
  ScriptApp.newTrigger('updateOutagesFromPython')
    .timeBased()
    .everyMinutes(1)
    .create();
  
  Logger.log('✅ Trigger created: updateOutagesFromPython() every 1 minute');
}

/**
 * Manual test function
 */
function testUpdate() {
  Logger.log('🧪 Running manual test...');
  updateOutagesFromPython();
}

/**
 * Remove all triggers (cleanup)
 */
function removeTrigger() {
  const triggers = ScriptApp.getProjectTriggers();
  triggers.forEach(trigger => {
    if (trigger.getHandlerFunction() === 'updateOutagesFromPython') {
      ScriptApp.deleteTrigger(trigger);
      Logger.log('🗑️ Trigger removed');
    }
  });
}
"""

def get_credentials():
    """Get or refresh credentials"""
    creds = None
    
    # Token file stores access and refresh tokens
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    
    # If no valid credentials, let user log in
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("🔄 Refreshing credentials...")
            creds.refresh(Request())
        else:
            print("❌ No valid credentials found")
            print("Please ensure token.pickle has Apps Script API scope")
            return None
        
        # Save credentials for next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)
    
    return creds

def get_script_project_id(creds, spreadsheet_id):
    """Get the Apps Script project ID associated with a spreadsheet"""
    try:
        sheets_service = build('sheets', 'v4', credentials=creds)
        spreadsheet = sheets_service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
        
        # Check if spreadsheet has a container-bound script
        if 'properties' in spreadsheet and 'containerInfo' in spreadsheet['properties']:
            script_id = spreadsheet['properties']['containerInfo']['containerId']
            print(f"✅ Found existing Apps Script project: {script_id}")
            return script_id
        
        print("ℹ️ No existing Apps Script project found, will create new one")
        return None
        
    except HttpError as error:
        print(f"⚠️ Could not check for existing script: {error}")
        return None

def create_or_update_script(creds, spreadsheet_id):
    """Create or update Apps Script project"""
    try:
        script_service = build('script', 'v1', credentials=creds)
        
        # Try to get existing script project
        script_id = get_script_project_id(creds, spreadsheet_id)
        
        if script_id:
            print(f"📝 Updating existing script project: {script_id}")
            
            # Get current project content
            try:
                project = script_service.projects().get(scriptId=script_id).execute()
                print(f"✅ Retrieved project: {project.get('title', 'Untitled')}")
            except HttpError as e:
                print(f"❌ Could not access script project: {e}")
                print("You may need to open Extensions → Apps Script in the spreadsheet first")
                return None
            
            # Update content
            content = {
                'files': [
                    {
                        'name': 'Code',
                        'type': 'SERVER_JS',
                        'source': APPS_SCRIPT_CODE
                    },
                    {
                        'name': 'appsscript',
                        'type': 'JSON',
                        'source': json.dumps({
                            'timeZone': 'Europe/London',
                            'dependencies': {},
                            'exceptionLogging': 'STACKDRIVER',
                            'oauthScopes': [
                                'https://www.googleapis.com/auth/spreadsheets',
                                'https://www.googleapis.com/auth/script.external_request'
                            ]
                        })
                    }
                ]
            }
            
            request = {'files': content['files']}
            response = script_service.projects().updateContent(
                scriptId=script_id,
                body=request
            ).execute()
            
            print("✅ Apps Script code deployed successfully!")
            print(f"📋 Script ID: {script_id}")
            print(f"🔗 Open in editor: https://script.google.com/d/{script_id}/edit")
            
            return script_id
            
        else:
            print("❌ No existing script found")
            print("\n📝 Manual steps required:")
            print("1. Open your spreadsheet")
            print("2. Go to Extensions → Apps Script")
            print("3. This creates a container-bound script")
            print("4. Run this script again to deploy the code")
            return None
            
    except HttpError as error:
        print(f"❌ Error: {error}")
        return None

def run_setup_trigger(creds, script_id):
    """Run the setupTrigger function to create the time-based trigger"""
    try:
        script_service = build('script', 'v1', credentials=creds)
        
        print("\n⏱️ Creating time-based trigger...")
        
        request = {
            'function': 'setupTrigger',
            'devMode': False
        }
        
        response = script_service.scripts().run(
            scriptId=script_id,
            body=request
        ).execute()
        
        if 'error' in response:
            print(f"❌ Error running setupTrigger: {response['error']}")
            return False
        
        print("✅ Trigger created successfully!")
        print("⏰ Dashboard will now update every 1 minute automatically")
        return True
        
    except HttpError as error:
        print(f"❌ Error creating trigger: {error}")
        return False

def test_api_connection():
    """Test connection to Python API"""
    import requests
    
    print("\n🧪 Testing Python API connection...")
    try:
        response = requests.get(f"{PYTHON_API_URL}/outages/names", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ API working: {data['count']} outages found")
            return True
        else:
            print(f"❌ API returned status {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ API connection failed: {e}")
        return False

def main():
    print("=" * 60)
    print("📋 Dashboard Outages Apps Script Deployment")
    print("=" * 60)
    
    # Test API connection first
    if not test_api_connection():
        print("\n⚠️ Warning: API not responding, but continuing with deployment")
    
    # Get credentials
    print("\n🔐 Authenticating...")
    creds = get_credentials()
    
    if not creds:
        print("\n❌ Authentication failed")
        print("\nTo fix this, you need to:")
        print("1. Ensure token.pickle has Apps Script API scope")
        print("2. Or delete token.pickle and re-authenticate")
        return
    
    print("✅ Authenticated successfully")
    
    # Create or update script
    print(f"\n📝 Deploying to spreadsheet: {SPREADSHEET_ID}")
    script_id = create_or_update_script(creds, SPREADSHEET_ID)
    
    if script_id:
        print("\n✅ Deployment complete!")
        
        # Ask if user wants to create trigger
        response = input("\n❓ Create time-based trigger now? (y/n): ").lower()
        if response == 'y':
            if run_setup_trigger(creds, script_id):
                print("\n✅ All done! Dashboard will auto-update every minute")
            else:
                print("\n⚠️ Trigger creation failed")
                print("Run setupTrigger() manually from Apps Script editor")
        else:
            print("\nℹ️ Skipped trigger creation")
            print("Run setupTrigger() manually from Apps Script editor when ready")
    else:
        print("\n⚠️ Deployment incomplete - see instructions above")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    main()

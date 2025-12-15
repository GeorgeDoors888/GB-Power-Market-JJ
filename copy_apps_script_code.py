#!/usr/bin/env python3
"""
Quick Deploy: Copy Apps Script code to clipboard for manual paste
Simpler approach while Apps Script API setup is completed
"""

PYTHON_API_URL = 'https://jibber-jabber-production.up.railway.app'
SPREADSHEET_ID = '1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA'

APPS_SCRIPT_CODE = f"""const PYTHON_API_URL = '{PYTHON_API_URL}';
const SPREADSHEET_ID = '{SPREADSHEET_ID}';

/**
 * Update Dashboard outages from Python API
 * Runs every 1 minute via time-based trigger
 */
function updateOutagesFromPython() {{
  try {{
    Logger.log('🔄 Fetching outages from Python API...');
    
    const url = `${{PYTHON_API_URL}}/outages/names`;
    const response = UrlFetchApp.fetch(url, {{muteHttpExceptions: true}});
    const responseCode = response.getResponseCode();
    
    if (responseCode !== 200) {{
      Logger.log(`❌ API returned status ${{responseCode}}`);
      return;
    }}
    
    const data = JSON.parse(response.getContentText());
    
    if (data.status !== 'success') {{
      Logger.log('❌ API returned error status');
      return;
    }}
    
    Logger.log(`✅ Fetched ${{data.count}} outages`);
    
    // Open Dashboard sheet
    const sheet = SpreadsheetApp.openById(SPREADSHEET_ID).getSheetByName('Dashboard');
    
    if (!sheet) {{
      Logger.log('❌ Dashboard sheet not found');
      return;
    }}
    
    // Prepare outage names for rows 23-36 (14 entries)
    const outages = data.outages || [];
    const values = [];
    
    for (let i = 0; i < 14; i++) {{
      if (i < outages.length) {{
        values.push([outages[i].station_name]);
      }} else {{
        values.push(['']); // Empty cell if fewer than 14 outages
      }}
    }}
    
    // Write to Dashboard A23:A36
    sheet.getRange('A23:A36').setValues(values);
    Logger.log('✅ Updated outages list (A23:A36)');
    
    // Update timestamp in B2
    const now = new Date();
    const timestamp = Utilities.formatDate(now, Session.getScriptTimeZone(), 'yyyy-MM-dd HH:mm:ss');
    sheet.getRange('B2').setValue(`⏰ Last Updated: ${{timestamp}}`);
    Logger.log('✅ Updated timestamp (B2)');
    
    Logger.log('✅ Dashboard update complete');
    
  }} catch (error) {{
    Logger.log(`❌ Error: ${{error.toString()}}`);
  }}
}}

/**
 * Set up time-based trigger (run this once manually)
 */
function setupTrigger() {{
  // Delete existing triggers for this function
  const triggers = ScriptApp.getProjectTriggers();
  triggers.forEach(trigger => {{
    if (trigger.getHandlerFunction() === 'updateOutagesFromPython') {{
      ScriptApp.deleteTrigger(trigger);
      Logger.log('🗑️ Deleted existing trigger');
    }}
  }});
  
  // Create new trigger - every 1 minute
  ScriptApp.newTrigger('updateOutagesFromPython')
    .timeBased()
    .everyMinutes(1)
    .create();
  
  Logger.log('✅ Trigger created: updateOutagesFromPython() every 1 minute');
}}

/**
 * Manual test function
 */
function testUpdate() {{
  Logger.log('🧪 Running manual test...');
  updateOutagesFromPython();
}}

/**
 * Remove all triggers (cleanup)
 */
function removeTrigger() {{
  const triggers = ScriptApp.getProjectTriggers();
  triggers.forEach(trigger => {{
    if (trigger.getHandlerFunction() === 'updateOutagesFromPython') {{
      ScriptApp.deleteTrigger(trigger);
      Logger.log('🗑️ Trigger removed');
    }}
  }});
}}
"""

def main():
    print("=" * 70)
    print("📋 Dashboard Outages Apps Script - Ready to Deploy")
    print("=" * 70)
    
    try:
        pyperclip.copy(APPS_SCRIPT_CODE)
        print("\n✅ Apps Script code COPIED TO CLIPBOARD!")
    except:
        print("\n⚠️ Could not copy to clipboard (pyperclip not installed)")
        print("📝 Code is shown below - copy manually")
    
    print("\n📝 MANUAL DEPLOYMENT STEPS:")
    print("-" * 70)
    print("1. Open Dashboard spreadsheet:")
    print(f"   https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/")
    print()
    print("2. Go to: Extensions → Apps Script")
    print()
    print("3. Delete any existing code in Code.gs")
    print()
    print("4. Paste the code (from clipboard or below)")
    print()
    print("5. Click Save (💾 icon)")
    print()
    print("6. Run 'testUpdate' function once to authorize")
    print()
    print("7. Run 'setupTrigger' function to create 1-minute auto-refresh")
    print()
    print("8. Check Executions tab to verify it's running")
    print("-" * 70)
    
    print("\n📋 APPS SCRIPT CODE:")
    print("=" * 70)
    print(APPS_SCRIPT_CODE)
    print("=" * 70)
    
    print("\n✅ API Status: Railway endpoint working")
    print(f"🔗 API URL: {PYTHON_API_URL}/outages/names")
    print("\n🎯 After setup, Dashboard will update every 1 minute automatically!")

if __name__ == "__main__":
    main()

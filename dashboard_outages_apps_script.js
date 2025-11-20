/**
 * Minimal Apps Script - Calls Python API for Outages Data
 * 
 * Setup:
 * 1. Copy this entire script
 * 2. Open Google Sheet → Extensions → Apps Script
 * 3. Paste and replace all existing code
 * 4. Update PYTHON_API_URL with your deployment URL
 * 5. Click Save
 * 6. Run installTrigger() once
 * 
 * The Python API does all the heavy lifting:
 * - Queries BigQuery
 * - Loads BMU registration data
 * - Converts codes to station names
 * - Returns ready-to-use data
 */

// Configuration - UPDATE THIS with your Python API URL
const PYTHON_API_URL = 'http://localhost:5001/outages/names'; // Local testing
// const PYTHON_API_URL = 'https://your-railway-app.railway.app/outages/names'; // Production

const SPREADSHEET_ID = '12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8';
const OUTAGES_START_ROW = 23; // Row A23 in Dashboard
const OUTAGES_MAX_ROWS = 14;  // A23:A36

/**
 * Main function - Fetch and update outages
 * Called by time trigger every 1 minute
 */
function updateDashboardOutages() {
  try {
    Logger.log('🔄 Fetching outages from Python API...');
    
    // Call Python API
    const response = UrlFetchApp.fetch(PYTHON_API_URL, {
      method: 'get',
      muteHttpExceptions: true
    });
    
    const data = JSON.parse(response.getContentText());
    
    if (data.status !== 'success') {
      Logger.log('❌ API returned error: ' + data.message);
      return;
    }
    
    Logger.log(`✅ Received ${data.count} outage names`);
    
    // Open spreadsheet
    const ss = SpreadsheetApp.openById(SPREADSHEET_ID);
    const sheet = ss.getSheetByName('Dashboard');
    
    if (!sheet) {
      Logger.log('❌ Dashboard sheet not found');
      return;
    }
    
    // Prepare data for sheet (pad to 14 rows)
    const updateData = [];
    for (let i = 0; i < OUTAGES_MAX_ROWS; i++) {
      if (i < data.names.length) {
        updateData.push([data.names[i]]);
      } else {
        updateData.push(['']); // Empty cell if fewer outages
      }
    }
    
    // Update outages column (A23:A36)
    const range = sheet.getRange(OUTAGES_START_ROW, 1, OUTAGES_MAX_ROWS, 1);
    range.setValues(updateData);
    
    // Update timestamp in B2
    const now = new Date();
    const timestamp = Utilities.formatDate(now, Session.getScriptTimeZone(), 'yyyy-MM-dd HH:mm:ss');
    sheet.getRange('B2').setValue(`⏰ Last Updated: ${timestamp} | ✅ FRESH`);
    
    Logger.log('✅ Dashboard updated successfully');
    
  } catch (error) {
    Logger.log('❌ Error: ' + error.toString());
  }
}

/**
 * Install time-based trigger (every 1 minute)
 * Run this once to set up automatic updates
 */
function installTrigger() {
  // Delete existing triggers first
  const triggers = ScriptApp.getProjectTriggers();
  triggers.forEach(trigger => {
    if (trigger.getHandlerFunction() === 'updateDashboardOutages') {
      ScriptApp.deleteTrigger(trigger);
    }
  });
  
  // Create new trigger - every 1 minute
  ScriptApp.newTrigger('updateDashboardOutages')
    .timeBased()
    .everyMinutes(1)
    .create();
  
  Logger.log('✅ Trigger installed: Updates every 1 minute');
}

/**
 * Remove all triggers (if you need to stop auto-updates)
 */
function removeTrigger() {
  const triggers = ScriptApp.getProjectTriggers();
  triggers.forEach(trigger => {
    if (trigger.getHandlerFunction() === 'updateDashboardOutages') {
      ScriptApp.deleteTrigger(trigger);
    }
  });
  Logger.log('✅ All triggers removed');
}

/**
 * Manual test function
 */
function testUpdate() {
  updateDashboardOutages();
}

/**
 * Test API connection
 */
function testAPI() {
  try {
    Logger.log('Testing Python API connection...');
    
    const response = UrlFetchApp.fetch(PYTHON_API_URL, {
      method: 'get',
      muteHttpExceptions: true
    });
    
    Logger.log('Response Code: ' + response.getResponseCode());
    Logger.log('Response Body: ' + response.getContentText());
    
  } catch (error) {
    Logger.log('❌ API Test Failed: ' + error.toString());
  }
}

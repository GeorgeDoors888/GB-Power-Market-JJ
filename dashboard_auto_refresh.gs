/**
 * GB Energy Dashboard - Auto-Refresh Apps Script
 * 
 * Automatically refreshes dashboard every 5 minutes with latest data
 * Includes manual refresh button and audit logging
 */

// Configuration
const SPREADSHEET_ID = '12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8';
const REFRESH_INTERVAL_MINUTES = 5;

/**
 * Creates custom menu on spreadsheet open
 */
function onOpen() {
  const ui = SpreadsheetApp.getUi();
  ui.createMenu('🔄 Dashboard')
    .addItem('🔄 Refresh Now', 'manualRefresh')
    .addItem('⚙️ Setup Auto-Refresh', 'setupAutoRefresh')
    .addItem('🛑 Stop Auto-Refresh', 'stopAutoRefresh')
    .addItem('📊 View Refresh Log', 'viewRefreshLog')
    .addToUi();
  
  Logger.log('Dashboard menu created');
}

/**
 * Manual refresh triggered by user
 */
function manualRefresh() {
  const ui = SpreadsheetApp.getUi();
  
  try {
    ui.alert('🔄 Refreshing Dashboard', 
             'Fetching latest data from BigQuery...\\nThis may take 10-15 seconds.', 
             ui.ButtonSet.OK);
    
    const result = refreshDashboard();
    
    if (result.success) {
      ui.alert('✅ Refresh Complete!', 
               `Dashboard updated successfully at ${new Date().toLocaleTimeString()}\\n\\n` +
               `📊 Settlement Periods: ${result.periods}\\n` +
               `🔥 Fuel Types: ${result.fuelTypes}\\n` +
               `📈 Charts Updated: 4`, 
               ui.ButtonSet.OK);
    } else {
      ui.alert('❌ Refresh Failed', 
               `Error: ${result.error}\\n\\nPlease check the logs.`, 
               ui.ButtonSet.OK);
    }
  } catch (error) {
    ui.alert('❌ Error', 
             `Failed to refresh: ${error.message}`, 
             ui.ButtonSet.OK);
    Logger.log('Manual refresh error: ' + error.message);
  }
}

/**
 * Core refresh function - calls Python script via Railway API
 */
function refreshDashboard() {
  try {
    const startTime = new Date();
    
    // Call Railway API endpoint to trigger Python refresh
    const apiUrl = 'https://jibber-jabber-production.up.railway.app/api/refresh-dashboard';
    
    const options = {
      'method': 'post',
      'contentType': 'application/json',
      'muteHttpExceptions': true,
      'headers': {
        'Authorization': 'Bearer ' + getApiToken()
      }
    };
    
    const response = UrlFetchApp.fetch(apiUrl, options);
    const responseCode = response.getResponseCode();
    
    if (responseCode === 200) {
      const result = JSON.parse(response.getContentText());
      
      // Log successful refresh
      logRefresh({
        timestamp: startTime,
        status: 'SUCCESS',
        periods: result.periods || 0,
        fuelTypes: result.fuelTypes || 0,
        duration: (new Date() - startTime) / 1000,
        trigger: 'MANUAL'
      });
      
      return {
        success: true,
        periods: result.periods,
        fuelTypes: result.fuelTypes
      };
    } else {
      throw new Error(`API returned ${responseCode}: ${response.getContentText()}`);
    }
    
  } catch (error) {
    // Log failed refresh
    logRefresh({
      timestamp: new Date(),
      status: 'FAILED',
      error: error.message,
      trigger: 'MANUAL'
    });
    
    return {
      success: false,
      error: error.message
    };
  }
}

/**
 * Automatic refresh (called by time-driven trigger)
 */
function autoRefresh() {
  try {
    Logger.log('Starting automatic refresh...');
    const result = refreshDashboard();
    
    if (result.success) {
      Logger.log(`Auto-refresh SUCCESS: ${result.periods} periods, ${result.fuelTypes} fuel types`);
    } else {
      Logger.log(`Auto-refresh FAILED: ${result.error}`);
    }
  } catch (error) {
    Logger.log('Auto-refresh error: ' + error.message);
  }
}

/**
 * Setup time-driven trigger for auto-refresh
 */
function setupAutoRefresh() {
  const ui = SpreadsheetApp.getUi();
  
  try {
    // Delete existing triggers first
    stopAutoRefresh();
    
    // Create new trigger every 5 minutes
    ScriptApp.newTrigger('autoRefresh')
      .timeBased()
      .everyMinutes(REFRESH_INTERVAL_MINUTES)
      .create();
    
    ui.alert('✅ Auto-Refresh Enabled', 
             `Dashboard will now refresh automatically every ${REFRESH_INTERVAL_MINUTES} minutes.\\n\\n` +
             'You can stop this by selecting "Stop Auto-Refresh" from the menu.', 
             ui.ButtonSet.OK);
    
    Logger.log(`Auto-refresh trigger created (every ${REFRESH_INTERVAL_MINUTES} minutes)`);
  } catch (error) {
    ui.alert('❌ Setup Failed', 
             `Could not enable auto-refresh: ${error.message}`, 
             ui.ButtonSet.OK);
    Logger.log('Setup error: ' + error.message);
  }
}

/**
 * Stop auto-refresh by deleting all triggers
 */
function stopAutoRefresh() {
  const triggers = ScriptApp.getProjectTriggers();
  let deletedCount = 0;
  
  for (let trigger of triggers) {
    if (trigger.getHandlerFunction() === 'autoRefresh') {
      ScriptApp.deleteTrigger(trigger);
      deletedCount++;
    }
  }
  
  if (deletedCount > 0) {
    SpreadsheetApp.getUi().alert('🛑 Auto-Refresh Stopped', 
                                  `Removed ${deletedCount} automatic refresh trigger(s).\\n\\n` +
                                  'Dashboard will no longer update automatically.', 
                                  SpreadsheetApp.getUi().ButtonSet.OK);
    Logger.log(`Deleted ${deletedCount} auto-refresh triggers`);
  } else {
    SpreadsheetApp.getUi().alert('ℹ️ No Active Triggers', 
                                  'Auto-refresh was not enabled.', 
                                  SpreadsheetApp.getUi().ButtonSet.OK);
  }
}

/**
 * Log refresh activity to hidden audit sheet
 */
function logRefresh(data) {
  try {
    const ss = SpreadsheetApp.getActiveSpreadsheet();
    let logSheet = ss.getSheetByName('RefreshLog');
    
    if (!logSheet) {
      logSheet = ss.insertSheet('RefreshLog');
      logSheet.appendRow(['Timestamp', 'Status', 'Periods', 'Fuel Types', 'Duration (s)', 'Trigger', 'Error']);
      logSheet.hideSheet();
    }
    
    logSheet.appendRow([
      data.timestamp,
      data.status,
      data.periods || '',
      data.fuelTypes || '',
      data.duration || '',
      data.trigger,
      data.error || ''
    ]);
    
    // Keep only last 1000 entries
    if (logSheet.getLastRow() > 1000) {
      logSheet.deleteRows(2, logSheet.getLastRow() - 1000);
    }
  } catch (error) {
    Logger.log('Logging error: ' + error.message);
  }
}

/**
 * View refresh log
 */
function viewRefreshLog() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  let logSheet = ss.getSheetByName('RefreshLog');
  
  if (logSheet) {
    logSheet.showSheet();
    logSheet.activate();
    SpreadsheetApp.getUi().alert('📊 Refresh Log', 
                                  'Showing refresh activity log.\\n\\n' +
                                  'This sheet is normally hidden to keep the dashboard clean.', 
                                  SpreadsheetApp.getUi().ButtonSet.OK);
  } else {
    SpreadsheetApp.getUi().alert('ℹ️ No Log Found', 
                                  'No refresh activity has been logged yet.', 
                                  SpreadsheetApp.getUi().ButtonSet.OK);
  }
}

/**
 * Get API token from script properties
 */
function getApiToken() {
  const properties = PropertiesService.getScriptProperties();
  let token = properties.getProperty('API_TOKEN');
  
  if (!token) {
    // Generate and save token on first use
    token = Utilities.getUuid();
    properties.setProperty('API_TOKEN', token);
  }
  
  return token;
}

/**
 * Test function to verify Railway API connectivity
 */
function testApiConnection() {
  const ui = SpreadsheetApp.getUi();
  
  try {
    const apiUrl = 'https://jibber-jabber-production.up.railway.app/workspace/health';
    const response = UrlFetchApp.fetch(apiUrl);
    
    if (response.getResponseCode() === 200) {
      ui.alert('✅ API Connected', 
               'Successfully connected to Railway API!\\n\\n' +
               'The dashboard is ready for auto-refresh.', 
               ui.ButtonSet.OK);
    } else {
      ui.alert('⚠️ API Issue', 
               `API responded with code ${response.getResponseCode()}`, 
               ui.ButtonSet.OK);
    }
  } catch (error) {
    ui.alert('❌ Connection Failed', 
             `Could not reach Railway API: ${error.message}`, 
             ui.ButtonSet.OK);
  }
}

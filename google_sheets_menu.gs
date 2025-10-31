/**
 * Google Apps Script for Enhanced BI Analysis Sheet
 * Adds custom menu with "Refresh Data" button that triggers Python recalculation
 * 
 * HOW TO INSTALL:
 * 1. Open your Google Sheet
 * 2. Go to Extensions > Apps Script
 * 3. Delete any existing code
 * 4. Paste this entire script
 * 5. Click Save (disk icon)
 * 6. DO NOT click "Run" - that will cause an error!
 * 7. Just close the Apps Script tab
 * 8. Refresh your Google Sheet
 * 9. You'll see "⚡ Power Market" menu at the top
 * 
 * IMPORTANT: Don't run onOpen() manually! It runs automatically when you open the sheet.
 */

/**
 * TEST FUNCTION - Run this to verify the script works
 * This can be executed manually from the Apps Script editor
 */
function testInstallation() {
  const sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName('Analysis BI Enhanced');
  
  if (!sheet) {
    Logger.log('❌ ERROR: Sheet "Analysis BI Enhanced" not found!');
    Logger.log('Available sheets: ' + SpreadsheetApp.getActiveSpreadsheet().getSheets().map(s => s.getName()).join(', '));
    return;
  }
  
  Logger.log('✅ Sheet "Analysis BI Enhanced" found!');
  Logger.log('✅ Script is installed correctly.');
  Logger.log('✅ Close this tab and refresh your Google Sheet.');
  Logger.log('✅ You should see "⚡ Power Market" menu at the top.');
}

/**
 * AUTHORIZATION FUNCTION - Run this to authorize the script
 * This will trigger Google's permission dialog
 */
function authorizeScript() {
  // This simple function requires basic permissions
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  Logger.log('Spreadsheet name: ' + ss.getName());
  Logger.log('✅ Authorization successful!');
  Logger.log('Now close this tab and refresh your Google Sheet.');
}

/**
 * SETUP TRIGGER - Run this ONCE to make menu appear automatically
 * This creates an installable trigger so menu persists
 */
function setupPermanentTrigger() {
  // Delete any existing onOpen triggers
  const triggers = ScriptApp.getProjectTriggers();
  triggers.forEach(function(trigger) {
    if (trigger.getHandlerFunction() === 'onOpen') {
      ScriptApp.deleteTrigger(trigger);
      Logger.log('Deleted old trigger');
    }
  });
  
  // Create new installable trigger
  ScriptApp.newTrigger('onOpen')
      .forSpreadsheet(SpreadsheetApp.getActiveSpreadsheet())
      .onOpen()
      .create();
  
  Logger.log('✅ Permanent trigger installed!');
  Logger.log('✅ Menu will now appear every time you open the sheet');
  Logger.log('🔄 Close Apps Script and refresh your sheet now');
  
  // Also create the menu immediately
  onOpen();
  Logger.log('✅ Menu created for this session');
}

/**
 * COMPREHENSIVE DIAGNOSTIC - Run this to debug menu issues
 */
function diagnoseMenu() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const sheets = ss.getSheets();
  
  Logger.log('=== DIAGNOSTIC INFO ===');
  Logger.log('Spreadsheet: ' + ss.getName());
  Logger.log('Spreadsheet ID: ' + ss.getId());
  Logger.log('Number of sheets: ' + sheets.length);
  Logger.log('Available sheets:');
  sheets.forEach(function(sheet) {
    Logger.log('  - "' + sheet.getName() + '"');
  });
  
  // Try to find the target sheet
  const targetSheet = ss.getSheetByName('Analysis BI Enhanced');
  if (targetSheet) {
    Logger.log('✅ Found sheet: "Analysis BI Enhanced"');
  } else {
    Logger.log('❌ Sheet "Analysis BI Enhanced" NOT FOUND');
    Logger.log('💡 Check the exact sheet name in your spreadsheet');
  }
  
  // Check triggers
  Logger.log('\n=== TRIGGERS ===');
  const triggers = ScriptApp.getProjectTriggers();
  Logger.log('Installed triggers: ' + triggers.length);
  if (triggers.length === 0) {
    Logger.log('⚠️ NO TRIGGERS INSTALLED - Run setupPermanentTrigger()');
  }
  triggers.forEach(function(trigger) {
    Logger.log('  - ' + trigger.getHandlerFunction() + ' (' + trigger.getEventType() + ')');
    Logger.log('    Trigger ID: ' + trigger.getUniqueId());
  });
  
  // Check UI availability
  Logger.log('\n=== UI CONTEXT ===');
  try {
    const ui = SpreadsheetApp.getUi();
    Logger.log('✅ UI context available');
    
    // Try creating menu
    Logger.log('\n=== MENU CREATION ===');
    const menu = ui.createMenu('⚡ Power Market')
        .addItem('🔄 Refresh Data Now', 'triggerRefresh')
        .addSeparator()
        .addItem('📊 Quick Refresh (1 Week)', 'quickRefresh1Week')
        .addItem('📊 Quick Refresh (1 Month)', 'quickRefresh1Month')
        .addSeparator()
        .addItem('ℹ️ Help', 'showHelp');
    
    menu.addToUi();
    Logger.log('✅ Menu creation command executed successfully');
    Logger.log('');
    Logger.log('🎯 THE MENU IS NOW ACTIVE IN YOUR SHEET!');
    Logger.log('⚠️  Menu appears in YOUR GOOGLE SHEET, not here in Apps Script');
    Logger.log('');
    Logger.log('WHERE TO LOOK:');
    Logger.log('1. Switch to your Google Sheet browser tab (not Apps Script)');
    Logger.log('2. Look at the very top menu bar');
    Logger.log('3. It should be at the far right, after "Help"');
    Logger.log('4. Look for: ⚡ Power Market');
    Logger.log('');
    Logger.log('If still not visible:');
    Logger.log('- Do a hard refresh: Cmd+Shift+R (Mac) or Ctrl+Shift+R (Windows)');
    Logger.log('- Close sheet tab completely and reopen');
    Logger.log('- Check browser console for JavaScript errors (F12 → Console)');
    
  } catch (e) {
    Logger.log('❌ ERROR with UI: ' + e.toString());
    Logger.log('This usually means the script is running outside sheet context');
  }
  
  // Check effective user
  Logger.log('\n=== USER INFO ===');
  try {
    const email = Session.getEffectiveUser().getEmail();
    Logger.log('Effective user: ' + email);
  } catch (e) {
    Logger.log('Could not get user email: ' + e.toString());
  }
}

/**
 * PROOF OF LIFE - Write to sheet to prove script works
 * This will write "SCRIPT WORKS!" to cell Z1
 */
function proofScriptWorks() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const sheet = ss.getActiveSheet();
  
  // Write to cell Z1
  sheet.getRange('Z1').setValue('SCRIPT WORKS! Time: ' + new Date().toISOString());
  sheet.getRange('Z1').setBackground('#00FF00');
  
  Logger.log('✅ Written to cell Z1');
  Logger.log('🔄 Go to your sheet and check cell Z1');
  Logger.log('You should see green cell with "SCRIPT WORKS!"');
  
  // Now try creating menu
  const ui = SpreadsheetApp.getUi();
  ui.createMenu('⚡ Power Market')
      .addItem('🔄 Refresh Data Now', 'triggerRefresh')
      .addSeparator()
      .addItem('📊 Quick Refresh (1 Week)', 'quickRefresh1Week')
      .addItem('📊 Quick Refresh (1 Month)', 'quickRefresh1Month')
      .addSeparator()
      .addItem('ℹ️ Help', 'showHelp')
      .addToUi();
  
  Logger.log('✅ Menu also created!');
  Logger.log('📍 Check your sheet NOW - look for menu at top!');
}

/**
 * MANUAL MENU CREATOR - Run this if onOpen() doesn't trigger automatically
 * This forces the menu to appear
 */
function createMenuManually() {
  const ui = SpreadsheetApp.getUi();
  ui.createMenu('⚡ Power Market')
      .addItem('🔄 Refresh Data Now', 'triggerRefresh')
      .addSeparator()
      .addItem('📊 Quick Refresh (1 Week)', 'quickRefresh1Week')
      .addItem('📊 Quick Refresh (1 Month)', 'quickRefresh1Month')
      .addSeparator()
      .addItem('ℹ️ Help', 'showHelp')
      .addToUi();
  
  Logger.log('✅ Menu created successfully!');
  Logger.log('⚠️ The menu appears in YOUR SHEET, not here in Apps Script!');
  Logger.log('🔄 Switch back to the sheet tab and look at the menu bar!');
  Logger.log('📍 It should be next to "Help" menu');
}

/**
 * Runs when the sheet is opened - adds custom menu
 * DO NOT run this manually! It runs automatically.
 */
function onOpen() {
  const ui = SpreadsheetApp.getUi();
  ui.createMenu('⚡ Power Market')
      .addItem('🔄 Refresh Data Now', 'triggerRefresh')
      .addSeparator()
      .addItem('📊 Quick Refresh (1 Week)', 'quickRefresh1Week')
      .addItem('📊 Quick Refresh (1 Month)', 'quickRefresh1Month')
      .addSeparator()
      .addItem('ℹ️ Help', 'showHelp')
      .addToUi();
}

/**
 * CREATE REFRESH BUTTON - Run this to add a button to your sheet
 * This creates a clickable button that triggers the refresh
 */
function createRefreshButton() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const sheet = ss.getSheetByName('Analysis BI Enhanced');
  
  if (!sheet) {
    Logger.log('❌ Sheet "Analysis BI Enhanced" not found!');
    return;
  }
  
  // Add button instructions in cell N5
  sheet.getRange('N5').setValue('👉 Click cell O5 to refresh →');
  sheet.getRange('N5').setFontWeight('bold');
  sheet.getRange('N5').setBackground('#E3F2FD');
  
  // Create the trigger cell with instructions
  sheet.getRange('O5').setValue('🔄 CLICK HERE TO REFRESH');
  sheet.getRange('O5').setFontWeight('bold');
  sheet.getRange('O5').setFontSize(12);
  sheet.getRange('O5').setBackground('#4CAF50');
  sheet.getRange('O5').setFontColor('#FFFFFF');
  sheet.getRange('O5').setHorizontalAlignment('center');
  
  Logger.log('✅ Refresh button created in cell O5!');
  Logger.log('📍 Go to your sheet and click cell O5 to trigger refresh');
  Logger.log('');
  Logger.log('NEXT STEP: Assign the script to the cell:');
  Logger.log('1. Right-click cell O5');
  Logger.log('2. Select "Insert drawing" or use Insert menu > Drawing');
  Logger.log('3. Create a simple shape/button');
  Logger.log('4. Assign script: triggerRefresh');
  Logger.log('');
  Logger.log('OR just use the simpler approach below...');
}

/**
 * Triggers Python script to refresh data
 * This updates a cell that your Python script monitors
 */
function triggerRefresh() {
  const sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName('Analysis BI Enhanced');
  
  if (!sheet) {
    SpreadsheetApp.getUi().alert('Error: "Analysis BI Enhanced" sheet not found!');
    return;
  }
  
  // Write trigger timestamp to a specific cell
  const triggerCell = 'M5';
  const timestamp = new Date().toISOString();
  sheet.getRange(triggerCell).setValue('REFRESH_REQUESTED:' + timestamp);
  
  // Update status
  sheet.getRange('L5').setValue('⏳ Refreshing...');
  sheet.getRange('L5').setBackground('#FFF9C4'); // Yellow background
  
  // Visual confirmation in the trigger cell
  sheet.getRange('O5').setValue('⏳ REFRESHING...');
  sheet.getRange('O5').setBackground('#FFF9C4');
  
  // Show message to user
  SpreadsheetApp.getUi().alert(
    '🔄 Refresh Requested',
    'Data refresh has been triggered.\n\n' +
    'The Python script will automatically detect this and refresh the data.\n' +
    'This usually takes 30-60 seconds.\n\n' +
    'Watch cell L5 for status updates.',
    SpreadsheetApp.getUi().ButtonSet.OK
  );
  
  // Reset button after 5 seconds
  Utilities.sleep(5000);
  sheet.getRange('O5').setValue('🔄 CLICK HERE TO REFRESH');
  sheet.getRange('O5').setBackground('#4CAF50');
}

/**
 * Quick refresh with 1 Week date range
 */
function quickRefresh1Week() {
  const sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName('Analysis BI Enhanced');
  
  if (!sheet) {
    SpreadsheetApp.getUi().alert('Error: "Analysis BI Enhanced" sheet not found!');
    return;
  }
  
  // Set date range to 1 Week
  sheet.getRange('B5').setValue('1 Week');
  
  // Trigger refresh
  triggerRefresh();
}

/**
 * Quick refresh with 1 Month date range
 */
function quickRefresh1Month() {
  const sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName('Analysis BI Enhanced');
  
  if (!sheet) {
    SpreadsheetApp.getUi().alert('Error: "Analysis BI Enhanced" sheet not found!');
    return;
  }
  
  // Set date range to 1 Month
  sheet.getRange('B5').setValue('1 Month');
  
  // Trigger refresh
  triggerRefresh();
}

/**
 * Shows help dialog
 */
function showHelp() {
  const help = 
    '⚡ POWER MARKET DASHBOARD HELP\n\n' +
    '🔄 Refresh Data Now:\n' +
    '   Triggers Python script to refresh all data from BigQuery.\n' +
    '   Wait 30-60 seconds, then refresh your browser.\n\n' +
    '📊 Quick Refresh:\n' +
    '   Sets date range and refreshes in one click.\n\n' +
    '💡 TIP:\n' +
    '   You can also manually change cell B5 (date range)\n' +
    '   and click "Refresh Data Now".\n\n' +
    'Python script must be running in background:\n' +
    '   python3 watch_sheet_for_refresh.py';
  
  SpreadsheetApp.getUi().alert('Help', help, SpreadsheetApp.getUi().ButtonSet.OK);
}

/**
 * Reset refresh status (called by Python after successful refresh)
 */
function resetRefreshStatus() {
  const sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName('Analysis BI Enhanced');
  
  if (!sheet) {
    return;
  }
  
  sheet.getRange('L5').setValue('✅ Up to date');
  sheet.getRange('L5').setBackground('#C8E6C9'); // Green background
  sheet.getRange('M5').clearContent();
}

/**
 * Set error status (called by Python if refresh fails)
 */
function setErrorStatus(errorMessage) {
  const sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName('Analysis BI Enhanced');
  
  if (!sheet) {
    return;
  }
  
  sheet.getRange('L5').setValue('❌ Error');
  sheet.getRange('L5').setBackground('#FFCDD2'); // Red background
  
  if (errorMessage) {
    SpreadsheetApp.getUi().alert('Refresh Error', errorMessage, SpreadsheetApp.getUi().ButtonSet.OK);
  }
}

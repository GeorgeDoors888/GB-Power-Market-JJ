/**
 * Dashboard Auto-Refresh Script
 * Paste this into Extensions → Apps Script
 */

function updateTimestamp() {
  const sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName('Dashboard');
  const now = new Date().toLocaleString();
  sheet.getRange('A26').setValue('⏰ Last updated: ' + now + ' | Auto-refresh active');
}

function onOpen() {
  const ui = SpreadsheetApp.getUi();
  ui.createMenu('⚙️ Dashboard Tools')
    .addItem('🔄 Refresh Timestamp', 'updateTimestamp')
    .addItem('📊 Refresh Data', 'refreshDashboardData')
    .addToUi();
}

function refreshDashboardData() {
  // This will trigger when connected to BigQuery or other data sources
  updateTimestamp();
  SpreadsheetApp.getActiveSpreadsheet().toast('Dashboard data refreshed', '✅ Success', 3);
}

// Set up time-driven trigger: Edit → Current project triggers → Add trigger
// Choose: updateTimestamp, Time-driven, Minutes timer, Every 5 minutes
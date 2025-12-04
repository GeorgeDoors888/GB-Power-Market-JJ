/**
 * @OnlyCurrentDoc
 *
 * The onOpen function runs automatically when the user opens the spreadsheet.
 */
function onOpen() {
  SpreadsheetApp.getUi()
      .createMenu('⚡ GB Energy')
      .addItem('📊 Rebuild Chart', 'buildDashboardChart')
      .addItem('🔄 Refresh Live Data', 'refreshAllData')
      .addSeparator()
      .addItem('⚙️ Set Date Range', 'showDateRangeSidebar')
      .addToUi();
}

/**
 * Triggers all Python data refresh scripts via a webhook or API call.
 * For now, this is a placeholder.
 */
function refreshAllData() {
  // In a real scenario, this would call a Railway/Vercel endpoint
  // that triggers the Python refresh scripts.
  SpreadsheetApp.getUi().alert('Live data refresh would be triggered now.');
  
  // Placeholder to log the action
  logAudit('Manual Data Refresh', 'Triggered by user menu.', 'Success');
}

/**
 * Shows a sidebar to select the date range.
 * This is an alternative to a dropdown if more complex logic is needed.
 */
function showDateRangeSidebar() {
  var html = HtmlService.createHtmlOutputFromFile('DateRangeSidebar')
      .setTitle('Select Date Range');
  SpreadsheetApp.getUi().showSidebar(html);
}

/**
 * Logs an action to the 'Audit' sheet.
 * @param {string} action The action performed (e.g., "Rebuild Chart").
 * @param {string} details Additional details about the action.
 * @param {string} status The status ("Success", "Error").
 * @param {string} [error_message] The error message, if any.
 */
function logAudit(action, details, status, error_message) {
  try {
    var auditSheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName('Audit');
    if (auditSheet) {
      var timestamp = new Date();
      var user = Session.getActiveUser().getEmail();
      auditSheet.appendRow([action, timestamp, user, status, details, error_message || '']);
    }
  } catch (e) {
    // Fails silently if Audit sheet doesn't exist or there's a permissions issue.
  }
}

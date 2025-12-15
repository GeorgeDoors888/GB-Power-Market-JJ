/**
 * Clear D45:E47 range
 */
function clearD45toE47() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const sheet = ss.getActiveSheet();
  
  // Clear D45:E47
  sheet.getRange('D45:E47').clearContent();
  sheet.getRange('D45:E47').clearDataValidations();
  sheet.getRange('D45:E47').setBackground(null);
  sheet.getRange('D45:E47').setBorder(false, false, false, false, false, false);
  
  Logger.log('✓ Cleared D45:E47');
  
  SpreadsheetApp.getUi().alert(
    '✅ Range D45:E47 Cleared!',
    SpreadsheetApp.getUi().ButtonSet.OK
  );
}

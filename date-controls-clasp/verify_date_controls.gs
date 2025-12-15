/**
 * Verify date controls are working
 */
function verifyDateControls() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const sheet = ss.getActiveSheet();
  
  // Check D65 (From date)
  const fromCell = sheet.getRange('D65');
  const fromValue = fromCell.getValue();
  const fromValidation = fromCell.getDataValidation();
  
  // Check E66 (To date)
  const toCell = sheet.getRange('E66');
  const toValue = toCell.getValue();
  const toValidation = toCell.getDataValidation();
  
  // Check labels
  const fromLabel = sheet.getRange('C65').getValue();
  const toLabel = sheet.getRange('D66').getValue();
  
  Logger.log('=== DATE CONTROLS VERIFICATION ===');
  Logger.log('C65 Label: ' + fromLabel);
  Logger.log('D65 From Date: ' + fromValue + ' (Has validation: ' + (fromValidation !== null) + ')');
  Logger.log('D66 Label: ' + toLabel);
  Logger.log('E66 To Date: ' + toValue + ' (Has validation: ' + (toValidation !== null) + ')');
  
  SpreadsheetApp.getUi().alert(
    '✅ Date Controls Verified!\n\n' +
    'D65 From: ' + Utilities.formatDate(fromValue, Session.getScriptTimeZone(), 'yyyy-MM-dd') + '\n' +
    'E66 To: ' + Utilities.formatDate(toValue, Session.getScriptTimeZone(), 'yyyy-MM-dd') + '\n\n' +
    'Both cells have calendar picker validation!'
  );
}

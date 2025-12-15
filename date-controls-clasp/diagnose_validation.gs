/**
 * Diagnose why date picker isn't showing
 */
function diagnoseValidation() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const sheet = ss.getActiveSheet();
  
  // Check D65
  const d65 = sheet.getRange('D65');
  const d65Validation = d65.getDataValidation();
  const d65Value = d65.getValue();
  
  // Check D66
  const d66 = sheet.getRange('D66');
  const d66Validation = d66.getDataValidation();
  const d66Value = d66.getValue();
  
  let msg = '🔍 Validation Diagnosis:\n\n';
  
  msg += 'D65 (From Date):\n';
  msg += '  Value: ' + d65Value + '\n';
  msg += '  Has validation: ' + (d65Validation !== null) + '\n';
  if (d65Validation) {
    msg += '  Criteria type: ' + d65Validation.getCriteriaType() + '\n';
  }
  
  msg += '\nD66 (To Date):\n';
  msg += '  Value: ' + d66Value + '\n';
  msg += '  Has validation: ' + (d66Validation !== null) + '\n';
  if (d66Validation) {
    msg += '  Criteria type: ' + d66Validation.getCriteriaType() + '\n';
  }
  
  Logger.log(msg);
  SpreadsheetApp.getUi().alert('Validation Diagnosis', msg, SpreadsheetApp.getUi().ButtonSet.OK);
}

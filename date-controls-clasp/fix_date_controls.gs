/**
 * Fix date controls - clear wrong locations and set up correctly
 */
function fixDateControls() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const sheet = ss.getActiveSheet();
  
  // Clear any data in row 55 (D55, E55, etc)
  sheet.getRange('C55:F55').clear();
  sheet.getRange('C55:F55').clearDataValidations();
  
  // Clear row 65 and 66 to start fresh
  sheet.getRange('C65:E66').clear();
  sheet.getRange('C65:E66').clearDataValidations();
  
  // NOW set up correctly:
  // C65 = "From Date:" label
  // D65 = From date picker
  // C66 = "To Date:" label  
  // D66 = To date picker
  
  // Label for "From" date (C65)
  const fromLabel = sheet.getRange('C65');
  fromLabel.setValue('📅 From Date:');
  fromLabel.setFontWeight('bold');
  fromLabel.setHorizontalAlignment('right');
  fromLabel.setBackground('#e8f4f8');
  
  // From date picker (D65)
  const fromCell = sheet.getRange('D65');
  const defaultFromDate = new Date();
  defaultFromDate.setDate(defaultFromDate.getDate() - 30);
  fromCell.setValue(defaultFromDate);
  fromCell.setNumberFormat('yyyy-mm-dd');
  fromCell.setBackground('#ffffff');
  fromCell.setBorder(true, true, true, true, false, false, '#4285f4', SpreadsheetApp.BorderStyle.SOLID_MEDIUM);
  fromCell.setHorizontalAlignment('center');
  fromCell.setFontSize(11);
  
  const fromRule = SpreadsheetApp.newDataValidation()
    .requireDate()
    .setAllowInvalid(false)
    .setHelpText('Select start date for analysis period')
    .build();
  fromCell.setDataValidation(fromRule);
  
  // Label for "To" date (C66)
  const toLabel = sheet.getRange('C66');
  toLabel.setValue('📅 To Date:');
  toLabel.setFontWeight('bold');
  toLabel.setHorizontalAlignment('right');
  toLabel.setBackground('#e8f4f8');
  
  // To date picker (D66)
  const toCell = sheet.getRange('D66');
  const defaultToDate = new Date();
  toCell.setValue(defaultToDate);
  toCell.setNumberFormat('yyyy-mm-dd');
  toCell.setBackground('#ffffff');
  toCell.setBorder(true, true, true, true, false, false, '#4285f4', SpreadsheetApp.BorderStyle.SOLID_MEDIUM);
  toCell.setHorizontalAlignment('center');
  toCell.setFontSize(11);
  
  const toRule = SpreadsheetApp.newDataValidation()
    .requireDate()
    .setAllowInvalid(false)
    .setHelpText('Select end date for analysis period')
    .build();
  toCell.setDataValidation(toRule);
  
  Logger.log('✓ Date controls fixed!');
  Logger.log('C65: From Date label');
  Logger.log('D65: From date picker');
  Logger.log('C66: To Date label');
  Logger.log('D66: To date picker');
  
  SpreadsheetApp.getUi().alert(
    '✅ Date Controls Fixed!\n\n' +
    'Layout:\n' +
    'Row 65: C65 = "From Date:" | D65 = date picker\n' +
    'Row 66: C66 = "To Date:" | D66 = date picker\n\n' +
    'Click D65 and D66 to open calendar!'
  );
}

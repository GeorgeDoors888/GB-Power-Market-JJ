/**
 * Move controls to new "Selector" sheet
 */
function moveToSelectorSheet() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  
  // Get or create "Selector" sheet
  let selectorSheet = ss.getSheetByName('Selector');
  if (!selectorSheet) {
    selectorSheet = ss.insertSheet('Selector');
    Logger.log('✓ Created new "Selector" sheet');
  }
  
  // Clear the current sheet's row 65-66 area (C65:G66)
  const currentSheet = ss.getActiveSheet();
  currentSheet.getRange('C65:G66').clearContent();
  currentSheet.getRange('C65:G66').clearDataValidations();
  currentSheet.getRange('C65:G66').setBackground(null);
  currentSheet.getRange('C65:G66').setBorder(false, false, false, false, false, false);
  Logger.log('✓ Cleared controls from current sheet');
  
  // Set up controls on Selector sheet
  // Row 2: From Date
  selectorSheet.getRange('A2').setValue('📅 From Date:').setFontWeight('bold').setHorizontalAlignment('right').setBackground('#e8f4f8');
  const fromDate = selectorSheet.getRange('B2');
  const defaultFrom = new Date();
  defaultFrom.setDate(defaultFrom.getDate() - 30);
  fromDate.setValue(defaultFrom);
  fromDate.setNumberFormat('yyyy-mm-dd');
  fromDate.setDataValidation(SpreadsheetApp.newDataValidation().requireDate().setAllowInvalid(false).build());
  fromDate.setBackground('#ffffff').setBorder(true, true, true, true, false, false, '#4285f4', SpreadsheetApp.BorderStyle.SOLID_MEDIUM);
  
  // Row 3: To Date
  selectorSheet.getRange('A3').setValue('📅 To Date:').setFontWeight('bold').setHorizontalAlignment('right').setBackground('#e8f4f8');
  const toDate = selectorSheet.getRange('B3');
  toDate.setValue(new Date());
  toDate.setNumberFormat('yyyy-mm-dd');
  toDate.setDataValidation(SpreadsheetApp.newDataValidation().requireDate().setAllowInvalid(false).build());
  toDate.setBackground('#ffffff').setBorder(true, true, true, true, false, false, '#4285f4', SpreadsheetApp.BorderStyle.SOLID_MEDIUM);
  
  // Row 4: BM Unit
  selectorSheet.getRange('A4').setValue('BM Unit:').setFontWeight('bold').setHorizontalAlignment('right').setBackground('#e8f4f8');
  const bmUnit = selectorSheet.getRange('B4');
  const bmUnits = ['All BM Units', 'FBPGM002', 'FFSEN005', 'T_DRAXX-1', 'T_DRAXX-2', 'T_DRAXX-3', 'T_DRAXX-4', 'E_WBURB-1', 'E_WBURB-2'];
  bmUnit.setDataValidation(SpreadsheetApp.newDataValidation().requireValueInList(bmUnits, true).setAllowInvalid(false).build());
  bmUnit.setValue('All BM Units');
  bmUnit.setBackground('#ffffff').setBorder(true, true, true, true, false, false, '#4285f4', SpreadsheetApp.BorderStyle.SOLID_MEDIUM);
  
  // Format columns
  selectorSheet.setColumnWidth(1, 150);
  selectorSheet.setColumnWidth(2, 200);
  
  Logger.log('✓ Controls moved to Selector sheet');
  
  SpreadsheetApp.getUi().alert(
    '✅ Controls Moved to "Selector" Sheet!\n\n' +
    'Old location (row 65-66) cleared.\n' +
    'New location: "Selector" sheet\n' +
    '  B2: From Date\n' +
    '  B3: To Date\n' +
    '  B4: BM Unit\n\n' +
    'Click on the "Selector" tab to see them!'
  );
}

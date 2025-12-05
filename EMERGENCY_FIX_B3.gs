/**
 * EMERGENCY FIX FOR B3 VALIDATION
 * 
 * Copy this entire function into your Apps Script editor and run it.
 * This will fix the validation issue without rebuilding the entire dashboard.
 */
function EMERGENCY_FIX_B3_VALIDATION() {
  const ss = SpreadsheetApp.openById("1LmMq4OEE639Y-XXpOJ3xnvpAmHB6vUovh5g6gaU_vzc");
  const sheet = ss.getSheetByName("Dashboard V3");
  
  if (!sheet) {
    Browser.msgBox('Error', 'Dashboard V3 sheet not found!', Browser.Buttons.OK);
    return;
  }
  
  Logger.log('Fixing B3 validation...');
  
  // Step 1: Clear B3 completely
  const b3 = sheet.getRange("B3");
  b3.clearContent();
  b3.clearDataValidations();
  Logger.log('Cleared B3');
  
  // Step 2: Set correct validation
  const timeRangeRule = SpreadsheetApp.newDataValidation()
    .requireValueInList([
      'Today – Auto Refresh', 
      'Today – Manual', 
      'Last 7 Days', 
      'Last 30 Days', 
      'Year to Date'
    ], true)
    .setAllowInvalid(false)
    .build();
  
  b3.setDataValidation(timeRangeRule);
  Logger.log('Set new validation');
  
  // Step 3: Set value
  b3.setValue("Last 7 Days");
  Logger.log('Set value to "Last 7 Days"');
  
  // Also fix F3 while we're at it
  const f3 = sheet.getRange("F3");
  f3.clearContent();
  f3.clearDataValidations();
  
  const dnoRule = SpreadsheetApp.newDataValidation()
    .requireValueInRange(ss.getRange('DNO_Map!A2:A20'), true)
    .setAllowInvalid(false)
    .build();
  
  f3.setDataValidation(dnoRule);
  f3.setValue("All GB");
  Logger.log('Fixed F3');
  
  // Show success message
  Browser.msgBox(
    'SUCCESS!', 
    '✅ Fixed B3 and F3 validation!\n\nB3 now accepts:\n• Today – Auto Refresh\n• Today – Manual\n• Last 7 Days\n• Last 30 Days\n• Year to Date\n\nCurrent value: Last 7 Days',
    Browser.Buttons.OK
  );
  
  Logger.log('COMPLETE! B3 validation fixed.');
}

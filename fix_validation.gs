/**
 * Quick fix to update B3 validation without rebuilding entire dashboard
 * Run this function once from Apps Script editor
 */
function fixTimeRangeValidation() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const sheet = ss.getSheetByName("Dashboard V3");
  
  if (!sheet) {
    SpreadsheetApp.getUi().alert('Dashboard V3 sheet not found');
    return;
  }
  
  // Clear existing value first
  sheet.getRange("B3").clearContent();
  
  // Set new validation rule
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
  
  sheet.getRange("B3").setDataValidation(timeRangeRule);
  
  // Set default value
  sheet.getRange("B3").setValue("Last 7 Days");
  
  SpreadsheetApp.getActiveSpreadsheet().toast(
    '✅ Time Range validation fixed! Cell B3 now accepts correct values.',
    'Fixed',
    5
  );
}

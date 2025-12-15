/**
 * Simple deployment script - adds redesignLiveDashboard function to existing sheet
 * Run this from Apps Script Editor: Extensions → Apps Script → paste this file → Run
 */

function redesignLiveDashboard() {
  const ss = SpreadsheetApp.openById("1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA");
  
  // Find source sheet
  const src = ss.getSheets().find(s => s.getName().toLowerCase().includes("live dashboardv2"));
  if (!src) {
    SpreadsheetApp.getUi().alert("Could not find 'live dashboardv2' sheet");
    return;
  }
  
  // Create clean destination sheet
  let dash = ss.getSheetByName("Dashboard - Redesigned");
  if (dash) {
    ss.deleteSheet(dash);
  }
  dash = ss.insertSheet("Dashboard - Redesigned");
  
  // Build header
  dash.getRange("A1:L1").merge()
    .setValue("⚡ GB Power Market - BM Revenue Dashboard")
    .setFontSize(18)
    .setFontWeight("bold")
    .setFontColor("#FFFFFF")
    .setBackground("#1a73e8")
    .setHorizontalAlignment("center")
    .setVerticalAlignment("middle");
  
  dash.setRowHeight(1, 50);
  
  // Copy the BM Revenue Analysis data
  const dataSheet = ss.getSheetByName("BM Revenue Analysis - Full History");
  if (dataSheet) {
    const data = dataSheet.getDataRange().getValues();
    dash.getRange(3, 1, data.length, data[0].length).setValues(data);
    
    // Format header row
    dash.getRange(3, 1, 1, data[0].length)
      .setFontWeight("bold")
      .setBackground("#f3f3f3")
      .setHorizontalAlignment("center");
    
    // Auto-resize columns
    for (let i = 1; i <= data[0].length; i++) {
      dash.autoResizeColumn(i);
    }
  }
  
  // Styling
  dash.setFrozenRows(3);
  dash.setHiddenGridlines(true);
  
  // Move to front
  ss.setActiveSheet(dash);
  ss.moveActiveSheet(1);
  
  SpreadsheetApp.getUi().alert("✅ Dashboard redesigned! Check 'Dashboard - Redesigned' tab");
}

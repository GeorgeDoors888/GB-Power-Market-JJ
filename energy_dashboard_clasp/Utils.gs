/**
 * Utility functions for logging and helpers
 */

function log(msg) {
  console.log(`[EnergyDashboard ${new Date().toISOString()}] ${msg}`);
}

/**
 * Test connection to BESS sheet
 */
function testConnection() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const bess = ss.getSheetByName("BESS");
  const dash = ss.getSheetByName("Dashboard");
  
  if (!bess) {
    SpreadsheetApp.getUi().alert('❌ BESS sheet not found');
    return;
  }
  
  if (!dash) {
    SpreadsheetApp.getUi().alert('❌ Dashboard sheet not found');
    return;
  }
  
  const lastRow = bess.getLastRow();
  SpreadsheetApp.getUi().alert(`✅ Connection OK\n\nBESS sheet has ${lastRow} rows\nDashboard sheet found`);
}

/**
 * Clear all data from BESS sheet (use with caution!)
 */
function clearBESSData() {
  const ui = SpreadsheetApp.getUi();
  const response = ui.alert(
    'Clear BESS Data',
    'Are you sure you want to clear all BESS data? This cannot be undone!',
    ui.ButtonSet.YES_NO
  );
  
  if (response === ui.Button.YES) {
    const ss = SpreadsheetApp.getActiveSpreadsheet();
    const bess = ss.getSheetByName("BESS");
    
    if (bess && bess.getLastRow() > 1) {
      bess.deleteRows(2, bess.getLastRow() - 1);
      log("BESS data cleared");
      ui.alert('✅ BESS data cleared');
    }
  }
}

/**
 * Export current KPIs to JSON (for debugging)
 */
function exportKPIsToJSON() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const bess = ss.getSheetByName("BESS");
  
  const kpis = {
    timestamp: new Date().toISOString(),
    charged: bess.getRange("B3").getValue(),
    discharged: bess.getRange("B4").getValue(),
    revenue: bess.getRange("B5").getValue(),
    cost: bess.getRange("B6").getValue(),
    ebitda: bess.getRange("B7").getValue()
  };
  
  const json = JSON.stringify(kpis, null, 2);
  log("KPIs exported: " + json);
  
  SpreadsheetApp.getUi().alert('KPIs:\n\n' + json);
  return json;
}

/**
 * Dashboard refresh and KPI update functions
 */

function refreshDashboard() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const bess = ss.getSheetByName("BESS");
  const dash = ss.getSheetByName("Dashboard");

  if (!bess || !dash) {
    log("ERROR: Missing BESS or Dashboard sheet");
    return;
  }

  try {
    // Extract KPIs from BESS sheet
    const KPIS = {
      charged: bess.getRange("B3").getValue(),
      discharged: bess.getRange("B4").getValue(),
      revenue: bess.getRange("B5").getValue(),
      cost: bess.getRange("B6").getValue(),
      ebitda: bess.getRange("B7").getValue(),
    };

    // Update Dashboard KPI strip (Row 2-5)
    dash.getRange("B2").setValue(KPIS.charged);
    dash.getRange("C2").setValue(KPIS.discharged);
    dash.getRange("D2").setValue(KPIS.revenue);
    dash.getRange("E2").setValue(KPIS.cost);
    dash.getRange("F2").setValue(KPIS.ebitda);
    
    // Update timestamp
    dash.getRange("A99").setValue("Last Updated: " + new Date().toLocaleString('en-GB'));
    
    log("Dashboard refreshed successfully");
    
  } catch (e) {
    log("ERROR refreshing dashboard: " + e.toString());
    SpreadsheetApp.getUi().alert('❌ Error refreshing dashboard: ' + e.toString());
  }
}

/**
 * Format Dashboard KPI strip
 */
function formatDashboard() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const dash = ss.getSheetByName("Dashboard");
  
  // Format header row (Row 1)
  const headerRange = dash.getRange("A1:F1");
  headerRange.setBackground("#006FBD")
           .setFontColor("#FFFFFF")
           .setFontWeight("bold")
           .setHorizontalAlignment("center");
  
  // Set column headers
  dash.getRange("A1").setValue("⚡ Battery Summary");
  dash.getRange("B1").setValue("Charged (MWh)");
  dash.getRange("C1").setValue("Discharged (MWh)");
  dash.getRange("D1").setValue("Revenue (£)");
  dash.getRange("E1").setValue("Cost (£)");
  dash.getRange("F1").setValue("EBITDA (£)");
  
  // Format KPI cells (Row 2)
  const kpiRange = dash.getRange("B2:F2");
  kpiRange.setNumberFormat("#,##0.00")
         .setFontWeight("bold")
         .setHorizontalAlignment("center");
  
  log("Dashboard formatting applied");
}

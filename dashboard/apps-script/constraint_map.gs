
// ============================================================================
// CONSTRAINT MAP - Embedded in Dashboard Sheet
// ============================================================================

/**
 * Add custom menu for map controls
 */
function onOpen() {
  SpreadsheetApp.getUi()
    .createMenu('🗺️ Constraint Map')
    .addItem('📍 Show Interactive Map', 'showConstraintMap')
    .addItem('🔄 Refresh Map Data', 'refreshMapData')
    .addItem('ℹ️ Map Help', 'showMapHelp')
    .addToUi();
}

/**
 * Show interactive constraint map in sidebar
 */
function showConstraintMap() {
  const html = HtmlService.createHtmlOutputFromFile('ConstraintMap')
    .setTitle('GB Transmission Constraints')
    .setWidth(600);
  SpreadsheetApp.getUi().showSidebar(html);
}

/**
 * Get constraint data from BigQuery via Dashboard sheet
 */
function getConstraintData() {
  const ss = SpreadsheetApp.getActive();
  const dashboard = ss.getSheetByName('Dashboard');
  
  // Read boundary data from rows 116-126
  const boundaryData = dashboard.getRange('A116:H126').getValues();
  
  const constraints = [];
  for (let i = 1; i < boundaryData.length; i++) {
    if (boundaryData[i][0]) {
      constraints.push({
        boundary_id: boundaryData[i][0],
        name: boundaryData[i][1],
        flow_mw: parseFloat(boundaryData[i][2]) || 0,
        limit_mw: parseFloat(boundaryData[i][3]) || 0,
        util_pct: parseFloat(boundaryData[i][4]) || 0,
        margin_mw: parseFloat(boundaryData[i][5]) || 0,
        status: boundaryData[i][6],
        direction: boundaryData[i][7]
      });
    }
  }
  
  return constraints;
}

/**
 * Refresh map data from BigQuery
 */
function refreshMapData() {
  // Trigger the constraint dashboard update script
  SpreadsheetApp.getUi().alert('Map data refresh initiated. Please wait 30 seconds for update.');
}

/**
 * Show map help dialog
 */
function showMapHelp() {
  const help = `
GB TRANSMISSION CONSTRAINT MAP

🎨 Color Coding:
  🟢 Green: <50% utilization (Normal)
  🟡 Yellow: 50-75% utilization (Moderate)
  🟠 Orange: 75-90% utilization (High)
  🔴 Red: >90% utilization (Critical)

📊 Layers:
  ✓ Transmission Boundaries (B6, B7, SC1, etc.)
  ✓ DNO License Areas
  ✓ TNUoS Generation Zones
  ✓ GSP Regions

🔄 Updates:
  Map data refreshes every 5 minutes from BigQuery

💡 Usage:
  Click boundaries to see:
  • Flow vs Limit (MW)
  • Utilization %
  • Available margin
  • Constraint status
`;
  
  SpreadsheetApp.getUi().alert('Constraint Map Help', help, SpreadsheetApp.getUi().ButtonSet.OK);
}

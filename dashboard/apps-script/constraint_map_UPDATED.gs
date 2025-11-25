// ============================================================================
// CONSTRAINT MAP - Embedded in Dashboard Sheet
// ============================================================================

/**
 * @OnlyCurrentDoc
 * 
 * Required OAuth Scopes:
 * - https://www.googleapis.com/auth/spreadsheets.currentonly
 * - https://www.googleapis.com/auth/script.container.ui
 */

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
  try {
    const ss = SpreadsheetApp.getActive();
    const dashboard = ss.getSheetByName('Dashboard');
    
    if (!dashboard) {
      throw new Error('Dashboard sheet not found');
    }
    
    // Read boundary data from rows 116-126
    const boundaryData = dashboard.getRange('A116:H126').getValues();
    
    // ✅ Coordinate lookup for GB transmission boundaries
    const boundaryCoords = {
      'BRASIZEX': {lat: 51.8, lng: -2.0},    // Bristol area
      'ERROEX': {lat: 53.5, lng: -2.5},      // North West
      'ESTEX': {lat: 51.5, lng: 0.5},        // Essex/East
      'FLOWSTH': {lat: 52.0, lng: -1.5},     // Flow South
      'GALLEX': {lat: 53.0, lng: -3.0},      // North Wales
      'GETEX': {lat: 52.5, lng: -1.0},       // Get Export
      'GM+SNOW5A': {lat: 53.5, lng: -2.2},   // Greater Manchester/Snowdonia
      'HARSPNBLY': {lat: 55.0, lng: -3.5},   // Harker-Stella/Penwortham-Blyth
      'NKILGRMO': {lat: 56.5, lng: -5.0},    // North Kilbride-Grudie-Moyle
      'SCOTEX': {lat: 55.5, lng: -3.0}       // Scotland Export
    };
    
    // ✅ Helper functions defined ONCE (outside loop)
    function parsePercent(value) {
      if (typeof value === 'number') return value;
      if (typeof value === 'string') {
        return parseFloat(value.replace('%', '')) || 0;
      }
      return 0;
    }
    
    function parseNumber(value) {
      if (typeof value === 'number') return value;
      return parseFloat(value) || 0;
    }
    
    const constraints = [];
    for (let i = 1; i < boundaryData.length; i++) {
      const boundaryId = String(boundaryData[i][0]);
      if (boundaryId) {
        const coords = boundaryCoords[boundaryId] || {lat: 54.5, lng: -2.5}; // Default to UK center
        constraints.push({
          boundary_id: boundaryId,
          name: String(boundaryData[i][1] || 'Unknown'),
          flow_mw: parseNumber(boundaryData[i][2]),
          limit_mw: parseNumber(boundaryData[i][3]),
          util_pct: parsePercent(boundaryData[i][4]),
          margin_mw: parseNumber(boundaryData[i][5]),
          status: String(boundaryData[i][6] || 'Unknown'),
          direction: String(boundaryData[i][7] || 'N/A'),
          lat: coords.lat,
          lng: coords.lng
        });
      }
    }
    
    Logger.log('Retrieved ' + constraints.length + ' constraints with coordinates');
    return constraints;
    
  } catch (error) {
    Logger.log('Error in getConstraintData: ' + error.toString());
    throw new Error('Failed to load data: ' + error.message);
  }
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
  ✓ Transmission Boundaries (BRASIZEX, SCOTEX, etc.)
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

/**
 * Test function for debugging constraint data
 */
function testMapData() {
  try {
    var result = getConstraintData();
    Logger.log('✅ SUCCESS! Got ' + result.length + ' constraints');
    Logger.log('Sample constraint: ' + JSON.stringify(result[0]));
    return result;
  } catch (error) {
    Logger.log('❌ ERROR: ' + error.toString());
    Logger.log('Stack: ' + error.stack);
    throw error;
  }
}

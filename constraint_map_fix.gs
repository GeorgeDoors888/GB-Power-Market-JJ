// ============================================================================
// UPDATED getConstraintData() with coordinate lookup
// ============================================================================

function getConstraintData() {
  try {
    const ss = SpreadsheetApp.getActive();
    const dashboard = ss.getSheetByName('Dashboard');
    if (!dashboard) {
      throw new Error('Dashboard sheet not found');
    }
    
    // Read boundary data from rows 116-126
    const boundaryData = dashboard.getRange('A116:H126').getValues();
    
    // Coordinate lookup for each boundary
    const boundaryCoords = {
      'B6': {lat: 55.5, lng: -3.0},
      'B7': {lat: 54.5, lng: -2.5},
      'SC1': {lat: 53.5, lng: -1.5},
      'B7a': {lat: 54.2, lng: -2.8},
      'B8': {lat: 54.8, lng: -3.2},
      'EC5': {lat: 52.5, lng: 1.0},
      'LE1': {lat: 51.5, lng: 0.0},
      'B4': {lat: 56.0, lng: -3.5},
      'B2': {lat: 57.0, lng: -3.0},
      'B1': {lat: 57.5, lng: -2.5},
    };
    
    // Helper functions
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
        const coords = boundaryCoords[boundaryId] || {lat: null, lng: null};
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
    
    Logger.log('Retrieved ' + constraints.length + ' constraints');
    return constraints;
    
  } catch (error) {
    Logger.log('Error in getConstraintData: ' + error.toString());
    throw new Error('Failed to load data: ' + error.message);
  }
}

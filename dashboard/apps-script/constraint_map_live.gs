// ========================================================================
// LIVE CONSTRAINT MAP - Fetches Data from Sheet on Every Load
// ========================================================================

/**
 * @OnlyCurrentDoc
 */

/**
 * Coordinate lookup for GB transmission boundaries
 */
const BOUNDARY_COORDS = {
  'BRASIZEX': {lat: 51.8, lng: -2.0},
  'ERROEX': {lat: 53.5, lng: -2.5},
  'ESTEX': {lat: 51.5, lng: 0.5},
  'FLOWSTH': {lat: 52.0, lng: -1.5},
  'GALLEX': {lat: 53.0, lng: -3.0},
  'GETEX': {lat: 52.5, lng: -1.0},
  'GM+SNOW5A': {lat: 53.5, lng: -2.2},
  'HARSPNBLY': {lat: 55.0, lng: -3.5},
  'NKILGRMO': {lat: 56.5, lng: -5.0},
  'SCOTEX': {lat: 55.5, lng: -3.0}
};

/**
 * Add custom menu
 */
function onOpen() {
  SpreadsheetApp.getUi()
    .createMenu('🗺️ Constraint Map')
    .addItem('📍 Show Live Map', 'showConstraintMapLive')
    .addToUi();
}

/**
 * Show map sidebar with live data
 */
function showConstraintMapLive() {
  const html = HtmlService.createHtmlOutput(getMapHtml())
    .setTitle('GB Transmission Constraints')
    .setWidth(600);
  SpreadsheetApp.getUi().showSidebar(html);
}

/**
 * Fetch constraint data from Dashboard sheet
 */
function getConstraintData() {
  const sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName('Dashboard');
  const data = sheet.getRange('A116:H126').getValues();
  
  const constraints = [];
  
  // Skip header row (row 0)
  for (let i = 1; i < data.length; i++) {
    const row = data[i];
    const boundary = row[0];
    
    if (!boundary) continue; // Skip empty rows
    
    const coords = BOUNDARY_COORDS[boundary];
    if (!coords) {
      Logger.log(`⚠️  No coordinates for boundary: ${boundary}`);
      continue;
    }
    
    const flow = parseFloat(row[3]) || 0;
    const limit = parseFloat(row[4]) || 0;
    const utilization = parseFloat(row[7]) || 0;
    const status = row[6] || 'Unknown';
    const direction = row[5] || '—';
    
    constraints.push({
      boundary: boundary,
      flow: flow,
      limit: limit,
      utilization: utilization,
      status: status,
      direction: direction,
      lat: coords.lat,
      lng: coords.lng
    });
  }
  
  Logger.log(`✅ Loaded ${constraints.length} constraints`);
  return constraints;
}

/**
 * Generate HTML for map with live data
 */
function getMapHtml() {
  const constraints = getConstraintData();
  const constraintsJson = JSON.stringify(constraints);
  
  return `
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>GB Transmission Constraints</title>
  <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
  <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
  <style>
    body {
      margin: 0;
      padding: 0;
      font-family: Arial, sans-serif;
    }
    #map {
      width: 100%;
      height: 100vh;
    }
    .legend {
      position: absolute;
      bottom: 30px;
      right: 10px;
      background: white;
      padding: 10px;
      border-radius: 5px;
      box-shadow: 0 2px 5px rgba(0,0,0,0.3);
      z-index: 1000;
      font-size: 12px;
    }
    .legend-item {
      margin: 5px 0;
      display: flex;
      align-items: center;
    }
    .legend-color {
      width: 20px;
      height: 20px;
      border-radius: 50%;
      margin-right: 8px;
      border: 2px solid #333;
    }
  </style>
</head>
<body>
  <div id="map"></div>
  <div class="legend">
    <strong>Utilization</strong>
    <div class="legend-item">
      <div class="legend-color" style="background: #4CAF50;"></div>
      <span>&lt; 50% (Normal)</span>
    </div>
    <div class="legend-item">
      <div class="legend-color" style="background: #FFC107;"></div>
      <span>50-75% (Moderate)</span>
    </div>
    <div class="legend-item">
      <div class="legend-color" style="background: #FF9800;"></div>
      <span>75-90% (High)</span>
    </div>
    <div class="legend-item">
      <div class="legend-color" style="background: #F44336;"></div>
      <span>&gt; 90% (Critical)</span>
    </div>
  </div>

  <script>
    // Constraint data from Google Sheet
    const constraints = ${constraintsJson};
    
    // Initialize map
    const map = L.map('map').setView([54.5, -3.5], 6);
    
    // Add OpenStreetMap tiles
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '© OpenStreetMap contributors',
      maxZoom: 19
    }).addTo(map);
    
    // Add markers
    constraints.forEach(constraint => {
      // Determine color based on utilization
      let color = '#4CAF50'; // Green (< 50%)
      if (constraint.utilization >= 90) {
        color = '#F44336'; // Red (>= 90%)
      } else if (constraint.utilization >= 75) {
        color = '#FF9800'; // Orange (75-90%)
      } else if (constraint.utilization >= 50) {
        color = '#FFC107'; // Yellow (50-75%)
      }
      
      // Create circle marker
      const marker = L.circleMarker([constraint.lat, constraint.lng], {
        radius: 12,
        fillColor: color,
        color: '#333',
        weight: 2,
        opacity: 1,
        fillOpacity: 0.8
      }).addTo(map);
      
      // Create popup content
      const popupContent = \`
        <div style="min-width: 200px;">
          <h3 style="margin: 0 0 10px 0; color: #333;">\${constraint.boundary}</h3>
          <table style="width: 100%; font-size: 12px;">
            <tr>
              <td><strong>Flow:</strong></td>
              <td>\${constraint.flow.toFixed(0)} MW</td>
            </tr>
            <tr>
              <td><strong>Limit:</strong></td>
              <td>\${constraint.limit.toFixed(0)} MW</td>
            </tr>
            <tr>
              <td><strong>Utilization:</strong></td>
              <td style="color: \${color}; font-weight: bold;">
                \${constraint.utilization.toFixed(1)}%
              </td>
            </tr>
            <tr>
              <td><strong>Status:</strong></td>
              <td>\${constraint.status}</td>
            </tr>
            <tr>
              <td><strong>Direction:</strong></td>
              <td>\${constraint.direction}</td>
            </tr>
          </table>
        </div>
      \`;
      
      marker.bindPopup(popupContent);
    });
    
    console.log('✅ Loaded', constraints.length, 'constraints');
  </script>
</body>
</html>
  `;
}

/**
 * Test function to verify data fetch
 */
function testMapData() {
  const constraints = getConstraintData();
  Logger.log('=' .repeat(80));
  Logger.log('CONSTRAINT MAP TEST');
  Logger.log('=' .repeat(80));
  Logger.log(\`Found \${constraints.length} constraints\`);
  
  if (constraints.length > 0) {
    Logger.log('Sample constraint:');
    Logger.log(JSON.stringify(constraints[0], null, 2));
    Logger.log('✅ SUCCESS! Data is loading correctly.');
  } else {
    Logger.log('❌ ERROR: No constraints loaded!');
  }
}

/**
 * RefreshDashboard - Main refresh function with filter support
 */
function RefreshDashboard() {
  try {
    const ss = SpreadsheetApp.getActiveSpreadsheet();
    const dash = ss.getSheetByName("Dashboard");
    
    if (!dash) {
      Logger.log('Error: Dashboard sheet not found');
      return;
    }
    
    // Read filter values
    const timeRange = dash.getRange("B3").getValue() || "24h";
    const region = dash.getRange("D3").getValue() || "All GB";
    const alertType = dash.getRange("F3").getValue() || "All";
    const fromDate = dash.getRange("I3").getValue() || new Date(Date.now() - 7*24*60*60*1000);
    const toDate = dash.getRange("K3").getValue() || new Date();
    
    // Update timestamp
    dash.getRange("A2").setValue("⚡ Live Data: " + new Date().toLocaleString());
    
    Logger.log('Dashboard refreshed with filters: ' + timeRange + ', ' + region + ', ' + alertType);
    
  } catch (error) {
    Logger.log('Error in RefreshDashboard: ' + error.toString());
  }
}

/**
 * FormatDashboard - Apply consistent styling to Dashboard sheet
 */
function formatDashboard() {
  try {
    const ss = SpreadsheetApp.getActiveSpreadsheet();
    const dash = ss.getSheetByName("Dashboard");
    
    if (!dash) {
      Logger.log('Error: Dashboard sheet not found');
      return;
    }
    
    // Header (A1)
    dash.getRange("A1")
      .setBackground("#4A90E2")
      .setFontColor("#FFFFFF")
      .setFontWeight("bold")
      .setFontSize(16)
      .setHorizontalAlignment("center");
    
    // Timestamp (A2)
    dash.getRange("A2")
      .setFontColor("#3366CC")
      .setFontStyle("italic");
    
    // Filter labels (A3, C3, E3, H3, J3)
    const filterRanges = ["A3", "C3", "E3", "H3", "J3"];
    filterRanges.forEach(cell => {
      dash.getRange(cell)
        .setFontWeight("bold")
        .setFontColor("#333333");
    });
    
    // KPI Strip (A5:H5)
    dash.getRange("A5:H5")
      .setBackground("#E3F2FD")
      .setFontWeight("bold")
      .setFontSize(12);
    
    // Fuel Mix header (A8:C8)
    dash.getRange("A8:C8")
      .setBackground("#FFF9C4")
      .setFontWeight("bold");
    
    // Interconnectors header (D8:E8)
    dash.getRange("D8:E8")
      .setBackground("#C8E6C9")
      .setFontWeight("bold");
    
    // Outages header (F8:H8)
    dash.getRange("F8:H8")
      .setBackground("#FFCCBC")
      .setFontWeight("bold");
    
    // Column widths
    dash.setColumnWidth(1, 120);  // A
    dash.setColumnWidth(2, 150);  // B
    dash.setColumnWidth(3, 20);   // C (spacer)
    dash.setColumnWidth(4, 150);  // D
    dash.setColumnWidth(5, 20);   // E (spacer)
    dash.setColumnWidth(6, 150);  // F
    
    // Row heights
    dash.setRowHeight(1, 40);     // Header
    dash.setRowHeight(2, 30);     // Timestamp
    dash.setRowHeight(3, 35);     // Filters
    dash.setRowHeight(5, 40);     // KPI strip
    
    Logger.log('✅ Dashboard formatting complete!');
    
  } catch (error) {
    Logger.log('Error in formatDashboard: ' + error.toString());
  }
}

/**
 * Get constraint data from Map_Data sheet
 */
function getConstraintData() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const mapSheet = ss.getSheetByName("Map_Data");
  
  if (!mapSheet) {
    return [];
  }
  
  const data = mapSheet.getDataRange().getValues();
  const constraints = [];
  
  for (let i = 1; i < data.length; i++) {
    if (data[i][0]) {
      constraints.push({
        gsp: data[i][0],
        region: data[i][1],
        lat: data[i][2],
        lng: data[i][3],
        mw: data[i][4],
        severity: data[i][5]
      });
    }
  }
  
  return constraints;
}

/**
 * Show live constraint map
 */
function showConstraintMapLive() {
  const html = HtmlService.createHtmlOutput(getMapHtml())
    .setWidth(1200)
    .setHeight(800);
  SpreadsheetApp.getUi().showModalDialog(html, 'GB Transmission Constraints - Live');
}

/**
 * Generate map HTML
 */
function getMapHtml() {
  const constraints = getConstraintData();
  
  return `
    <!DOCTYPE html>
    <html>
    <head>
      <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
      <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
      <style>
        body { margin: 0; padding: 0; }
        #map { height: 100vh; width: 100%; }
      </style>
    </head>
    <body>
      <div id="map"></div>
      <script>
        const map = L.map('map').setView([54.5, -3.5], 6);
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png').addTo(map);
        
        const constraints = ${JSON.stringify(constraints)};
        
        constraints.forEach(c => {
          const color = c.severity === 'High' ? 'red' : c.severity === 'Medium' ? 'orange' : 'yellow';
          L.circleMarker([c.lat, c.lng], {
            radius: Math.min(c.mw / 50, 20),
            fillColor: color,
            color: '#000',
            weight: 1,
            opacity: 1,
            fillOpacity: 0.7
          }).bindPopup(\`<b>\${c.gsp}</b><br>\${c.region}<br>\${c.mw} MW\`).addTo(map);
        });
      </script>
    </body>
    </html>
  `;
}

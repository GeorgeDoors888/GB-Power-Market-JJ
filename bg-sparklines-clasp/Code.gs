/**
 * GB Live Dashboard - Sparkline Formula Writer
 * 
 * Writes cross-sheet SPARKLINE formulas that reference Data_Hidden sheet.
 * Works because Apps Script runs in the Sheets context (unlike API v4).
 * 
 * Spreadsheet: GB Live Dashboard
 * ID: 1MSl8fJ0to6Y08enXA2oysd8wvNUVm3AtfJ1bVqRH8_I
 */

// Fuel type sparkline configurations (Column C, rows 11-20)
const FUEL_SPARKLINES = [
  { row: 11, dataRow: 1, color: '#4ECDC4', max: 20, label: '💨 Wind' },
  { row: 12, dataRow: 2, color: '#FF6B6B', max: 10, label: '🔥 CCGT' },
  { row: 13, dataRow: 3, color: '#FFA07A', max: 5, label: '⚛️ Nuclear' },
  { row: 14, dataRow: 4, color: '#98D8C8', max: 5, label: '🌱 Biomass' },
  { row: 15, dataRow: 5, color: '#F7DC6F', max: 2, label: '❓ Other' },
  { row: 16, dataRow: 6, color: '#85C1E9', max: 2, label: '💧 Pumped' },
  { row: 17, dataRow: 7, color: '#52B788', max: 1, label: '🌊 Hydro' },
  { row: 18, dataRow: 8, color: '#E76F51', max: 1, label: '🔥 OCGT' },
  { row: 19, dataRow: 9, color: '#666666', max: 1, label: '⚫ Coal' },
  { row: 20, dataRow: 10, color: '#8B4513', max: 1, label: '🛢️ Oil' }
];

// Interconnector sparkline configurations (Column F, rows 11-20)
const IC_SPARKLINES = [
  { row: 11, dataRow: 11, color: '#0055A4', max: 2, label: '🇫🇷 France' },
  { row: 12, dataRow: 12, color: '#169B62', max: 1, label: '🇮🇪 Ireland' },
  { row: 13, dataRow: 13, color: '#FF9B00', max: 1, label: '🇳🇱 Netherlands' },
  { row: 14, dataRow: 14, color: '#00843D', max: 1, label: '🏴 East-West' },
  { row: 15, dataRow: 15, color: '#FDDA24', max: 1, label: '🇧🇪 Belgium (Nemo)' },
  { row: 16, dataRow: 16, color: '#EF3340', max: 1, label: '🇧🇪 Belgium (Elec)' },
  { row: 17, dataRow: 17, color: '#0055A4', max: 2, label: '🇫🇷 IFA2' },
  { row: 18, dataRow: 18, color: '#BA0C2F', max: 2, label: '🇳🇴 Norway (NSL)' },
  { row: 19, dataRow: 19, color: '#C8102E', max: 2, label: '🇩🇰 Viking Link' },
  { row: 20, dataRow: 20, color: '#169B62', max: 1, label: '🇮🇪 Greenlink' }
];

/**
 * Main function: Write all sparkline formulas to GB Live dashboard
 */
function writeSparklines() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const gbLive = ss.getSheetByName('GB Live');
  const dataHidden = ss.getSheetByName('Data_Hidden');

  // Validate sheets exist
  if (!gbLive) {
    throw new Error("Sheet 'GB Live' not found!");
  }
  if (!dataHidden) {
    throw new Error("Sheet 'Data_Hidden' not found! Run Python script first to create it.");
  }

  Logger.log('✅ Found sheets: GB Live and Data_Hidden');
  
  // Write fuel type sparklines (Column C)
  writeFuelSparklines(gbLive);
  
  // Write interconnector sparklines (Column F)
  writeInterconnectorSparklines(gbLive);
  
  Logger.log('✅ All sparkline formulas written successfully!');
  Logger.log('📊 Next: Open sheet in browser to verify charts display');
}

/**
 * Write fuel type sparklines to Column C (rows 11-20)
 */
function writeFuelSparklines(sheet) {
  Logger.log('📝 Writing Column C fuel sparklines...');
  
  FUEL_SPARKLINES.forEach(config => {
    const formula = `=SPARKLINE(Data_Hidden!A${config.dataRow}:X${config.dataRow},` +
                   `{"charttype","line";"linewidth",2;"color","${config.color}";` +
                   `"max",${config.max};"ymin",0})`;
    
    sheet.getRange(`C${config.row}`).setFormula(formula);
    Logger.log(`   ✅ C${config.row} (${config.label}): Formula written`);
  });
  
  Logger.log(`✅ Wrote ${FUEL_SPARKLINES.length} fuel sparklines`);
}

/**
 * Write interconnector sparklines to Column F (rows 11-20)
 */
function writeInterconnectorSparklines(sheet) {
  Logger.log('📝 Writing Column F interconnector sparklines...');
  
  IC_SPARKLINES.forEach(config => {
    const formula = `=SPARKLINE(Data_Hidden!A${config.dataRow}:X${config.dataRow},` +
                   `{"charttype","line";"linewidth",2;"color","${config.color}";` +
                   `"max",${config.max};"ymin",0})`;
    
    sheet.getRange(`F${config.row}`).setFormula(formula);
    Logger.log(`   ✅ F${config.row} (${config.label}): Formula written`);
  });
  
  Logger.log(`✅ Wrote ${IC_SPARKLINES.length} interconnector sparklines`);
}

/**
 * Verify that Data_Hidden sheet has data
 */
function verifyDataHidden() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const dataHidden = ss.getSheetByName('Data_Hidden');
  
  if (!dataHidden) {
    Logger.log('❌ Data_Hidden sheet not found!');
    return false;
  }
  
  // Check if row 1 has data (Wind generation)
  const row1Values = dataHidden.getRange('A1:X1').getValues()[0];
  const nonEmpty = row1Values.filter(v => v !== '' && v !== null && v !== undefined);
  
  Logger.log(`✅ Data_Hidden found with ${nonEmpty.length}/24 data points in row 1`);
  
  if (nonEmpty.length < 10) {
    Logger.log('⚠️ Warning: Insufficient data in Data_Hidden. Run Python script first.');
    return false;
  }
  
  return true;
}

/**
 * Create custom menus in Google Sheets UI
 */
function onOpen() {
  const ui = SpreadsheetApp.getUi();
  
  // GB Live Dashboard menu for sparklines
  ui.createMenu('⚡ GB Live Dashboard')
    .addItem('✨ Write Sparkline Formulas', 'writeSparklines')
    .addItem('🔍 Verify Data_Hidden', 'verifyDataHidden')
    .addItem('🗑️ Clear Sparklines', 'clearSparklines')
    .addSeparator()
    .addItem('🏥 Health Check', 'quickHealthCheck')
    .addToUi();
  
  // DNO Map menu for geographic visualizations
  ui.createMenu('🗺️ DNO Map')
    .addItem('View Interactive Map', 'createDNOMap')
    .addItem('View Map with Site Markers', 'createDNOMapWithSites')
    .addItem('Embed Map in DNO Sheet', 'embedMapInSheet')
    .addToUi();
}

/**
 * Clear all sparklines (for testing/redeployment)
 */
function clearSparklines() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const gbLive = ss.getSheetByName('GB Live');
  
  if (!gbLive) {
    throw new Error("Sheet 'GB Live' not found!");
  }
  
  // Clear Column C (rows 11-20)
  gbLive.getRange('C11:C20').clearContent();
  
  // Clear Column F (rows 11-20)
  gbLive.getRange('F11:F20').clearContent();
  
  Logger.log('✅ Cleared all sparklines from columns C and F');
}

/**
 * Optional: Auto-refresh sparklines hourly
 * Note: Not needed if Python script updates Data_Hidden every 5 minutes
 */
function createHourlyTrigger() {
  // Delete existing triggers first
  const triggers = ScriptApp.getProjectTriggers();
  triggers.forEach(trigger => {
    if (trigger.getHandlerFunction() === 'writeSparklines') {
      ScriptApp.deleteTrigger(trigger);
    }
  });
  
  // Create new hourly trigger
  ScriptApp.newTrigger('writeSparklines')
           .timeBased()
           .everyHours(1)
           .create();
  
  Logger.log('✅ Hourly trigger created for writeSparklines()');
}

/**
 * Remove all triggers (for cleanup)
 */
function removeAllTriggers() {
  const triggers = ScriptApp.getProjectTriggers();
  triggers.forEach(trigger => {
    if (trigger.getHandlerFunction() === 'writeSparklines') {
      ScriptApp.deleteTrigger(trigger);
    }
  });
  
  Logger.log('✅ All writeSparklines triggers removed');
}

/**
 * Webhook endpoint - call from Python to trigger sparkline refresh
 * URL: https://script.google.com/macros/s/YOUR_DEPLOYMENT_ID/exec
 */
function doPost(e) {
  try {
    writeSparklines();
    return ContentService.createTextOutput(JSON.stringify({
      status: 'success',
      message: 'Sparklines written successfully',
      timestamp: new Date().toISOString()
    })).setMimeType(ContentService.MimeType.JSON);
  } catch (error) {
    return ContentService.createTextOutput(JSON.stringify({
      status: 'error',
      message: error.toString(),
      timestamp: new Date().toISOString()
    })).setMimeType(ContentService.MimeType.JSON);
  }
}

/**
 * Test function - validates everything is working
 */
function runTests() {
  Logger.log('🧪 Running tests...');
  
  // Test 1: Verify sheets exist
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const gbLive = ss.getSheetByName('GB Live');
  const dataHidden = ss.getSheetByName('Data_Hidden');
  
  Logger.log(`✅ Test 1: GB Live exists: ${gbLive !== null}`);
  Logger.log(`✅ Test 1: Data_Hidden exists: ${dataHidden !== null}`);
  
  // Test 2: Verify Data_Hidden has data
  if (dataHidden) {
    const hasData = verifyDataHidden();
    Logger.log(`✅ Test 2: Data_Hidden has data: ${hasData}`);
  }
  
  // Test 3: Write sparklines
  writeSparklines();
  
  // Test 4: Verify formulas were written
  if (gbLive) {
    const c11 = gbLive.getRange('C11').getFormula();
    const f11 = gbLive.getRange('F11').getFormula();
    
    Logger.log(`✅ Test 4: C11 has formula: ${c11.includes('SPARKLINE')}`);
    Logger.log(`✅ Test 4: F11 has formula: ${f11.includes('SPARKLINE')}`);
  }
  
  Logger.log('🎉 All tests complete!');
}

// ============================================================================
// DNO MAP FUNCTIONS
// ============================================================================

/**
 * Display interactive DNO map with real geographic boundaries
 */
function createDNOMap() {
  const html = HtmlService.createHtmlOutput(`
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>UK DNO License Areas - Real Boundaries</title>
  <script src="https://cdn.jsdelivr.net/npm/leaflet@1.9.4/dist/leaflet.js"></script>
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/leaflet@1.9.4/dist/leaflet.css"/>
  <style>
    body { margin: 0; padding: 0; font-family: Arial, sans-serif; }
    #map { height: 100vh; width: 100%; }
    #loading {
      position: fixed;
      top: 50%;
      left: 50%;
      transform: translate(-50%, -50%);
      background: white;
      padding: 30px;
      border-radius: 10px;
      box-shadow: 0 4px 20px rgba(0,0,0,0.3);
      z-index: 10000;
      text-align: center;
      font-size: 16px;
    }
    #loading .spinner {
      border: 4px solid #f3f3f3;
      border-top: 4px solid #FF6600;
      border-radius: 50%;
      width: 40px;
      height: 40px;
      animation: spin 1s linear infinite;
      margin: 20px auto;
    }
    @keyframes spin {
      0% { transform: rotate(0deg); }
      100% { transform: rotate(360deg); }
    }
    .info {
      padding: 10px;
      font: 14px/16px Arial, Helvetica, sans-serif;
      background: white;
      background: rgba(255,255,255,0.95);
      box-shadow: 0 0 15px rgba(0,0,0,0.3);
      border-radius: 8px;
      max-width: 300px;
    }
    .info h4 { 
      margin: 0 0 8px; 
      color: #333; 
      font-size: 16px;
      border-bottom: 2px solid #FF6600;
      padding-bottom: 5px;
    }
    .info b { color: #FF6600; }
    .info small { color: #666; display: block; margin-top: 5px; }
    .legend {
      line-height: 22px;
      color: #555;
      background: white;
      padding: 10px;
      border-radius: 8px;
      box-shadow: 0 0 15px rgba(0,0,0,0.3);
      max-height: 500px;
      overflow-y: auto;
    }
    .legend h4 {
      margin: 0 0 8px;
      color: #333;
      font-size: 14px;
      border-bottom: 2px solid #FF6600;
      padding-bottom: 5px;
    }
    .legend i {
      width: 18px;
      height: 18px;
      float: left;
      margin-right: 8px;
      opacity: 0.8;
      border: 1px solid #999;
    }
    .legend-item {
      clear: both;
      margin: 4px 0;
    }
  </style>
</head>
<body>
  <div id="loading">
    <div>⚡ Loading Real DNO Boundaries</div>
    <div class="spinner"></div>
    <small>Fetching detailed geographic data...</small>
  </div>
  <div id="map"></div>
  <script>
    // Initialize map centered on UK
    var map = L.map('map').setView([54.5, -3], 6);
    
    // Add OpenStreetMap tiles
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '© OpenStreetMap contributors',
      maxZoom: 18
    }).addTo(map);
    
    // Info panel control
    var info = L.control({position: 'topright'});
    info.onAdd = function (map) {
      this._div = L.DomUtil.create('div', 'info');
      this.update();
      return this._div;
    };
    info.update = function (props) {
      this._div.innerHTML = '<h4>🗺️ UK DNO Regions</h4>' +  
        (props ?
          '<b>' + props.dno_name + '</b><br/>' +
          'Area: ' + props.area + '<br/>' +
          'MPAN ID: <b>' + props.mpan_id + '</b><br/>' +
          'GSP Group: ' + props.gsp_group + '<br/>' +
          'Coverage: ' + props.coverage + '<br/>' +
          '<small>📍 ' + props.area_sqkm.toFixed(0) + ' km²</small>'
        : 'Hover over a region');
    };
    info.addTo(map);
    
    // Color palette for DNOs
    var colors = {
      10: '#FF6B6B', 11: '#4ECDC4', 12: '#45B7D1', 13: '#FFA07A',
      14: '#98D8C8', 15: '#F7DC6F', 16: '#BB8FCE', 17: '#85C1E9',
      18: '#F8B739', 19: '#52B788', 20: '#E76F51', 21: '#2A9D8F',
      22: '#264653', 23: '#E9C46A'
    };
    
    function getColor(mpanId) {
      return colors[mpanId] || '#95A5A6';
    }
    
    function style(feature) {
      return {
        fillColor: getColor(feature.properties.mpan_id),
        weight: 2,
        opacity: 1,
        color: '#666',
        fillOpacity: 0.6
      };
    }
    
    function highlightFeature(e) {
      var layer = e.target;
      layer.setStyle({
        weight: 3,
        color: '#333',
        fillOpacity: 0.8
      });
      layer.bringToFront();
      info.update(layer.feature.properties);
    }
    
    function resetHighlight(e) {
      geojson.resetStyle(e.target);
      info.update();
    }
    
    function zoomToFeature(e) {
      map.fitBounds(e.target.getBounds());
    }
    
    function onEachFeature(feature, layer) {
      layer.on({
        mouseover: highlightFeature,
        mouseout: resetHighlight,
        click: zoomToFeature
      });
    }
    
    var geojson; // Will hold the layer
    
    // Fetch real DNO boundaries from GitHub
    var geojsonUrl = 'https://raw.githubusercontent.com/GeorgeDoors888/GB-Power-Market-JJ/main/gb_power_map_deployment/dno_regions.geojson';
    
    fetch(geojsonUrl)
      .then(response => {
        if (!response.ok) throw new Error('Failed to load DNO boundaries');
        return response.json();
      })
      .then(dnoData => {
        // Hide loading indicator
        document.getElementById('loading').style.display = 'none';
        
        // Add GeoJSON layer with real boundaries
        geojson = L.geoJson(dnoData, {
          style: style,
          onEachFeature: onEachFeature
        }).addTo(map);
        
        // Fit map to actual data bounds
        map.fitBounds(geojson.getBounds());
        
        // Create legend
        var legend = L.control({position: 'bottomright'});
        legend.onAdd = function (map) {
          var div = L.DomUtil.create('div', 'info legend');
          div.innerHTML = '<h4>License Areas</h4>';
          
          // Sort features by MPAN ID for consistent display
          var sortedFeatures = dnoData.features.sort((a, b) => 
            a.properties.mpan_id - b.properties.mpan_id
          );
          
          sortedFeatures.forEach(function(feature) {
            var props = feature.properties;
            div.innerHTML += 
              '<div class="legend-item">' +
              '<i style="background:' + getColor(props.mpan_id) + '"></i> ' +
              '<b>' + props.mpan_id + '</b>: ' + props.area +
              '</div>';
          });
          
          return div;
        };
        legend.addTo(map);
        
        console.log('✅ Loaded ' + dnoData.features.length + ' DNO regions with real boundaries');
      })
      .catch(error => {
        document.getElementById('loading').innerHTML = 
          '<div style="color: red;">❌ Error Loading Map</div>' +
          '<div style="font-size: 12px; margin-top: 10px;">' + error.message + '</div>' +
          '<div style="font-size: 11px; color: #666; margin-top: 10px;">Check GitHub repository access</div>';
        console.error('Error loading GeoJSON:', error);
      });
  </script>
</body>
</html>
  `)
  .setWidth(1200)
  .setHeight(800);
  
  SpreadsheetApp.getUi().showModalDialog(html, '🗺️ UK DNO License Areas - Real Geographic Boundaries');
}

/**
 * Display DNO map with battery site marker from BtM sheet postcode
 */
function createDNOMapWithSites() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const btm = ss.getSheetByName('BtM');
  
  if (!btm) {
    SpreadsheetApp.getUi().alert('⚠️ BtM sheet not found!');
    return;
  }
  
  // Get postcode from A6
  const postcode = btm.getRange('A6').getValue();
  
  if (!postcode || postcode.toString().startsWith('←')) {
    SpreadsheetApp.getUi().alert('⚠️ No postcode found!\n\nPlease enter a postcode in cell A6 of the BtM sheet.');
    return;
  }
  
  // Geocode the postcode using postcodes.io
  let siteData = [];
  try {
    const cleanPostcode = postcode.toString().trim().replace(/\s+/g, '');
    const url = 'https://api.postcodes.io/postcodes/' + encodeURIComponent(cleanPostcode);
    const response = UrlFetchApp.fetch(url);
    const json = JSON.parse(response.getContentText());
    
    if (json.status == 200 && json.result) {
      const lat = json.result.latitude;
      const lon = json.result.longitude;
      const area = json.result.admin_district || 'Unknown';
      
      siteData.push({
        postcode: postcode,
        lat: lat,
        lon: lon,
        area: area,
        label: 'Battery Site'
      });
      
      Logger.log('Geocoded: ' + postcode + ' -> ' + lat + ', ' + lon);
    }
  } catch (e) {
    Logger.log('Geocoding error: ' + e);
    SpreadsheetApp.getUi().alert('⚠️ Could not geocode postcode: ' + postcode + '\n\nError: ' + e);
    return;
  }
  
  // Create map with site markers
  const siteDataJson = JSON.stringify(siteData);
  
  const html = HtmlService.createHtmlOutput(`
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>UK DNO License Areas with Sites</title>
  <script src="https://cdn.jsdelivr.net/npm/leaflet@1.9.4/dist/leaflet.js"></script>
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/leaflet@1.9.4/dist/leaflet.css"/>
  <style>
    body { margin: 0; padding: 0; font-family: Arial, sans-serif; }
    #map { height: 100vh; width: 100%; }
    #loading {
      position: fixed;
      top: 50%;
      left: 50%;
      transform: translate(-50%, -50%);
      background: white;
      padding: 30px;
      border-radius: 10px;
      box-shadow: 0 4px 20px rgba(0,0,0,0.3);
      z-index: 10000;
      text-align: center;
    }
    .site-marker {
      background-color: #FF0000;
      border: 3px solid white;
      border-radius: 50%;
      width: 20px;
      height: 20px;
      box-shadow: 0 2px 10px rgba(255,0,0,0.5);
    }
  </style>
</head>
<body>
  <div id="loading">🗺️ Loading DNO boundaries and site markers...</div>
  <div id="map"></div>
  <script>
    const map = L.map('map').setView([54.5, -3], 6);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '© OpenStreetMap'
    }).addTo(map);
    
    const siteData = ${siteDataJson};
    
    // Load DNO boundaries
    fetch('https://raw.githubusercontent.com/GeorgeDoors888/GB-Power-Market-JJ/main/gb_power_map_deployment/dno_regions.geojson')
      .then(r => r.json())
      .then(dnoData => {
        const colors = ['#FF6B6B','#4ECDC4','#45B7D1','#FFA07A','#98D8C8','#F7DC6F','#BB8FCE','#85C1E9','#F8B739','#52B788','#E76F51','#2A9D8F','#264653','#E9C46A'];
        
        // Add DNO boundaries
        L.geoJSON(dnoData, {
          style: f => ({
            fillColor: colors[f.properties.mpan_id % colors.length],
            weight: 2,
            opacity: 1,
            color: '#666',
            fillOpacity: 0.3
          }),
          onEachFeature: (f, layer) => {
            const p = f.properties;
            layer.bindPopup('<b>'+p.dno_name+'</b><br/>Area: '+p.area+'<br/>MPAN: '+p.mpan_id+'<br/>Coverage: '+p.coverage);
          }
        }).addTo(map);
        
        // Add site markers
        siteData.forEach(site => {
          const marker = L.circleMarker([site.lat, site.lon], {
            radius: 10,
            fillColor: '#FF0000',
            color: '#FFFFFF',
            weight: 3,
            opacity: 1,
            fillOpacity: 0.9
          }).addTo(map);
          
          marker.bindPopup(
            '<b>🔋 ' + site.label + '</b><br/>' +
            'Postcode: ' + site.postcode + '<br/>' +
            'Location: ' + site.area + '<br/>' +
            'Lat/Lon: ' + site.lat.toFixed(4) + ', ' + site.lon.toFixed(4)
          );
          
          // Zoom to site
          map.setView([site.lat, site.lon], 10);
        });
        
        document.getElementById('loading').style.display = 'none';
      })
      .catch(err => {
        document.getElementById('loading').innerHTML = '❌ Error loading map: ' + err;
      });
  </script>
</body>
</html>
  `)
  .setWidth(1200)
  .setHeight(800);
  
  SpreadsheetApp.getUi().showModalDialog(html, '🗺️ UK DNO Areas with Battery Site: ' + postcode);
}

/**
 * Embed DNO map in DNO sheet
 */
function embedMapInSheet() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const sheet = ss.getSheetByName('DNO');
  
  if (!sheet) {
    SpreadsheetApp.getUi().alert('⚠️ Sheet "DNO" not found!\n\nPlease create a sheet named "DNO" first.');
    return;
  }
  
  // Create HTML for embedded map (compact version)
  const mapHtml = `
<!DOCTYPE html>
<html>
<head>
  <script src="https://cdn.jsdelivr.net/npm/leaflet@1.9.4/dist/leaflet.js"></script>
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/leaflet@1.9.4/dist/leaflet.css"/>
  <style>
    body { margin: 0; padding: 0; }
    #map { height: 600px; width: 100%; }
  </style>
</head>
<body>
  <div id="map"></div>
  <script>
    const map = L.map('map').setView([54.5, -3], 6);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png').addTo(map);
    
    fetch('https://raw.githubusercontent.com/GeorgeDoors888/GB-Power-Market-JJ/main/gb_power_map_deployment/dno_regions.geojson')
      .then(r => r.json())
      .then(data => {
        const colors = ['#FF6B6B','#4ECDC4','#45B7D1','#FFA07A','#98D8C8','#F7DC6F','#BB8FCE','#85C1E9','#F8B739','#52B788','#E76F51','#2A9D8F','#264653','#E9C46A'];
        L.geoJSON(data, {
          style: f => ({
            fillColor: colors[f.properties.mpan_id % colors.length],
            weight: 2,
            opacity: 1,
            color: '#666',
            fillOpacity: 0.5
          }),
          onEachFeature: (f, layer) => {
            layer.bindPopup('<b>'+f.properties.dno_name+'</b><br/>Area: '+f.properties.area+'<br/>MPAN: '+f.properties.mpan_id);
          }
        }).addTo(map);
      });
  </script>
</body>
</html>`;
  
  // Upload to Google Drive and get URL
  const blob = Utilities.newBlob(mapHtml, 'text/html', 'dno_map_embedded.html');
  const file = DriveApp.createFile(blob);
  file.setSharing(DriveApp.Access.ANYONE_WITH_LINK, DriveApp.Permission.VIEW);
  const fileUrl = 'https://drive.google.com/uc?export=view&id=' + file.getId();
  
  // Add image/iframe reference in sheet
  const formula = '=IMAGE("' + fileUrl + '", 1)';
  sheet.getRange('H1').setFormula(formula);
  
  SpreadsheetApp.getUi().alert('✅ Map embedded in DNO sheet!\n\nLocation: Column H (starting at H1)\n\nNote: Google Sheets IMAGE() function has limitations with interactive HTML.\nFor best experience, use "View Interactive Map" from the menu.');
}

// ============================================================================
// DIAGNOSTIC FUNCTIONS
// ============================================================================

/**
 * Comprehensive environment diagnostics
 * Run from: Extensions → Apps Script → Select 'diagnostics' → Run
 */
function diagnostics() {
  Logger.log("=" .repeat(70));
  Logger.log("=== GB LIVE DASHBOARD - ENVIRONMENT DIAGNOSTICS ===");
  Logger.log("=" .repeat(70));
  
  // 1. Current user
  try {
    const user = Session.getActiveUser().getEmail();
    Logger.log("✅ User: " + (user || "Anonymous"));
  } catch (e) {
    Logger.log("❌ User: Error - " + e);
  }
  
  // 2. Script information
  try {
    Logger.log("✅ Script URL: " + ScriptApp.getScriptId());
    Logger.log("   Full URL: https://script.google.com/d/" + ScriptApp.getScriptId() + "/edit");
  } catch (e) {
    Logger.log("❌ Script info: Error - " + e);
  }
  
  // 3. Spreadsheet information
  try {
    const ss = SpreadsheetApp.getActiveSpreadsheet();
    Logger.log("✅ Spreadsheet: " + ss.getName());
    Logger.log("   ID: " + ss.getId());
    Logger.log("   URL: " + ss.getUrl());
    Logger.log("   Sheets: " + ss.getSheets().length);
    ss.getSheets().forEach(s => Logger.log("      - " + s.getName()));
  } catch (e) {
    Logger.log("❌ Spreadsheet info: Error - " + e);
  }
  
  // 4. Check required sheets
  Logger.log("\n📊 Checking Required Sheets:");
  checkSheet('GB Live');
  checkSheet('Data_Hidden');
  checkSheet('BtM');
  checkSheet('DNO');
  
  // 5. Active triggers
  try {
    const triggers = ScriptApp.getProjectTriggers();
    Logger.log("\n⏰ Active Triggers: " + triggers.length);
    if (triggers.length > 0) {
      triggers.forEach(t => {
        Logger.log("   - " + t.getHandlerFunction() + " | " + t.getEventType());
      });
    } else {
      Logger.log("   (No triggers configured)");
    }
  } catch (e) {
    Logger.log("❌ Triggers: Error - " + e);
  }
  
  // 6. Available services
  Logger.log("\n🔧 Service Availability:");
  Logger.log("   Drive API: " + (isServiceEnabled("Drive") ? "✅ Enabled" : "❌ Disabled"));
  Logger.log("   UrlFetch: " + (isServiceEnabled("UrlFetch") ? "✅ Enabled" : "❌ Disabled"));
  
  // 7. Test Data_Hidden content
  Logger.log("\n📈 Data_Hidden Content Check:");
  try {
    const ss = SpreadsheetApp.getActiveSpreadsheet();
    const dataHidden = ss.getSheetByName('Data_Hidden');
    if (dataHidden) {
      const row1 = dataHidden.getRange('A1:X1').getValues()[0];
      const nonEmpty = row1.filter(v => v !== '' && v !== null);
      Logger.log("   ✅ Row 1 (Wind): " + nonEmpty.length + " values");
      Logger.log("   Sample: [" + row1.slice(0, 5).join(", ") + "...]");
    } else {
      Logger.log("   ⚠️ Data_Hidden sheet not found");
    }
  } catch (e) {
    Logger.log("   ❌ Error reading Data_Hidden: " + e);
  }
  
  // 8. Test sparkline formulas
  Logger.log("\n✨ Sparkline Formula Check:");
  try {
    const ss = SpreadsheetApp.getActiveSpreadsheet();
    const gbLive = ss.getSheetByName('GB Live');
    if (gbLive) {
      const c11 = gbLive.getRange('C11').getFormula();
      const f11 = gbLive.getRange('F11').getFormula();
      Logger.log("   C11: " + (c11 ? (c11.includes('SPARKLINE') ? "✅ Has formula" : "⚠️ " + c11) : "❌ Empty"));
      Logger.log("   F11: " + (f11 ? (f11.includes('SPARKLINE') ? "✅ Has formula" : "⚠️ " + f11) : "❌ Empty"));
    }
  } catch (e) {
    Logger.log("   ❌ Error checking formulas: " + e);
  }
  
  // 9. Test GitHub access
  Logger.log("\n🌐 GitHub GeoJSON Access:");
  try {
    const url = 'https://raw.githubusercontent.com/GeorgeDoors888/GB-Power-Market-JJ/main/gb_power_map_deployment/dno_regions.geojson';
    const response = UrlFetchApp.fetch(url, {muteHttpExceptions: true});
    const code = response.getResponseCode();
    if (code === 200) {
      const json = JSON.parse(response.getContentText());
      Logger.log("   ✅ GitHub accessible - " + (json.features ? json.features.length + " features" : "JSON loaded"));
    } else {
      Logger.log("   ❌ HTTP " + code + ": " + response.getContentText().substring(0, 100));
    }
  } catch (e) {
    Logger.log("   ❌ Error: " + e);
  }
  
  Logger.log("\n" + "=" .repeat(70));
  Logger.log("✅ Diagnostics complete! Check View → Executions for full log.");
  Logger.log("=" .repeat(70));
}

/**
 * Check if a specific sheet exists
 */
function checkSheet(sheetName) {
  try {
    const ss = SpreadsheetApp.getActiveSpreadsheet();
    const sheet = ss.getSheetByName(sheetName);
    if (sheet) {
      Logger.log("   ✅ " + sheetName + " (ID: " + sheet.getSheetId() + ")");
      return true;
    } else {
      Logger.log("   ❌ " + sheetName + " - NOT FOUND");
      return false;
    }
  } catch (e) {
    Logger.log("   ❌ " + sheetName + " - Error: " + e);
    return false;
  }
}

/**
 * Check if a service is enabled
 */
function isServiceEnabled(service) {
  try {
    if (service === "Drive") {
      DriveApp.getRootFolder();
      return true;
    }
    if (service === "UrlFetch") {
      UrlFetchApp.fetch("https://www.google.com", {muteHttpExceptions: true});
      return true;
    }
    return false;
  } catch (e) {
    return false;
  }
}

/**
 * Quick health check - run this from menu
 */
function quickHealthCheck() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const ui = SpreadsheetApp.getUi();
  
  let report = "📊 GB Live Dashboard Health Check\n\n";
  
  // Check sheets
  const gbLive = ss.getSheetByName('GB Live');
  const dataHidden = ss.getSheetByName('Data_Hidden');
  report += "Sheets:\n";
  report += gbLive ? "  ✅ GB Live\n" : "  ❌ GB Live MISSING\n";
  report += dataHidden ? "  ✅ Data_Hidden\n" : "  ❌ Data_Hidden MISSING\n";
  
  // Check sparklines
  if (gbLive) {
    const c11 = gbLive.getRange('C11').getFormula();
    const f11 = gbLive.getRange('F11').getFormula();
    report += "\nSparklines:\n";
    report += c11 && c11.includes('SPARKLINE') ? "  ✅ Column C (Fuel)\n" : "  ❌ Column C missing formulas\n";
    report += f11 && f11.includes('SPARKLINE') ? "  ✅ Column F (IC)\n" : "  ❌ Column F missing formulas\n";
  }
  
  // Check data
  if (dataHidden) {
    const row1 = dataHidden.getRange('A1:X1').getValues()[0];
    const nonEmpty = row1.filter(v => v !== '' && v !== null);
    report += "\nData:\n";
    report += nonEmpty.length >= 10 ? "  ✅ Data_Hidden has data (" + nonEmpty.length + " values)\n" : "  ⚠️ Insufficient data (" + nonEmpty.length + " values)\n";
  }
  
  // Check triggers
  const triggers = ScriptApp.getProjectTriggers();
  report += "\nTriggers: " + triggers.length + " active\n";
  
  report += "\n" + "=".repeat(40);
  report += "\nFor detailed diagnostics, run 'diagnostics' function from Apps Script editor.";
  
  ui.alert("Health Check Results", report, ui.ButtonSet.OK);
  
  Logger.log(report);
}

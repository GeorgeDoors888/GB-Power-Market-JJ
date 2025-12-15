// GB Energy Market Dashboard - Apps Script
// Version 5 - Multi-Spreadsheet Support
// Works on BOTH: BtM (1MSl8fJ0...) and GB Energy Dashboard (12jY0d4j...)
// Combined: DNO Map + Sparklines + BESS Tools

function onOpen() {
  var ui = SpreadsheetApp.getUi();
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var ssId = ss.getId();
  
  // Detect which spreadsheet we're in
  var isBtMSpreadsheet = (ssId === '1MSl8fJ0to6Y08enXA2oysd8wvNUVm3AtfJ1bVqRH8_I');
  var isGBEnergySpreadsheet = (ssId === '12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8');
  
  // DNO Map menu (available in both)
  ui.createMenu('🗺️ DNO Map')
      .addItem('View Interactive Map', 'createDNOMap')
      .addItem('View Map with Site Markers', 'createDNOMapWithSites')
      .addItem('Embed Map in DNO Sheet', 'embedMapInSheet')
      .addToUi();
  
  // BESS Tools menu (available in both - both have BESS sheets)
  ui.createMenu('🔋 BESS Tools')
      .addItem('📊 Generate HH Data', 'generateHHDataDirect')
      .addSeparator()
      .addItem('🔄 Refresh DNO Data', 'manualRefreshDno')
      .addSeparator()
      .addItem('💰 Calculate PPA Analysis', 'calculatePPAAnalysis')
      .addSeparator()
      .addItem('📈 Show HH Data Status', 'showHHDataStatus')
      .addToUi();
  
  // Sparklines menu (only in BtM spreadsheet - has GB Live + Data_Hidden)
  if (isBtMSpreadsheet) {
    var gbLiveSheet = ss.getSheetByName('GB Live');
    var dataHiddenSheet = ss.getSheetByName('Data_Hidden');
    
    if (gbLiveSheet && dataHiddenSheet) {
      ui.createMenu('⚡ GB Live Dashboard')
          .addItem('✨ Write Sparkline Formulas', 'writeSparklines')
          .addItem('🔍 Verify Data_Hidden', 'verifyDataHidden')
          .addItem('🗑️ Clear Sparklines', 'clearSparklines')
          .addSeparator()
          .addItem('🏥 Health Check', 'quickHealthCheck')
          .addToUi();
    }
  }
  
  // Diagnostics menu (available everywhere)
  ui.createMenu('🔧 Diagnostics')
      .addItem('Run Full Diagnostics', 'diagnostics')
      .addItem('Show Spreadsheet Info', 'showSpreadsheetInfo')
      .addToUi();
}

function createDNOMap() {
  var html = HtmlService.createHtmlOutput(`
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

function embedMapInSheet() {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var sheet = ss.getSheetByName('DNO');
  
  if (!sheet) {
    SpreadsheetApp.getUi().alert('⚠️ Sheet "DNO" not found!\n\nPlease create a sheet named "DNO" first.');
    return;
  }
  
  // Create HTML for embedded map (compact version)
  var mapHtml = `
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
  var blob = Utilities.newBlob(mapHtml, 'text/html', 'dno_map_embedded.html');
  var file = DriveApp.createFile(blob);
  file.setSharing(DriveApp.Access.ANYONE_WITH_LINK, DriveApp.Permission.VIEW);
  var fileUrl = 'https://drive.google.com/uc?export=view&id=' + file.getId();
  
  // Add image/iframe reference in sheet
  var formula = '=IMAGE("' + fileUrl + '", 1)';
  sheet.getRange('H1').setFormula(formula);
  
  SpreadsheetApp.getUi().alert('✅ Map embedded in DNO sheet!\n\nLocation: Column H (starting at H1)\n\nNote: Google Sheets IMAGE() function has limitations with interactive HTML.\nFor best experience, use "View Interactive Map" from the menu.');
}

function createDNOMapWithSites() {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var btm = ss.getSheetByName('BtM');
  
  if (!btm) {
    SpreadsheetApp.getUi().alert('⚠️ BtM sheet not found!');
    return;
  }
  
  // Get postcode from A6
  var postcode = btm.getRange('A6').getValue();
  
  if (!postcode || postcode.toString().startsWith('←')) {
    SpreadsheetApp.getUi().alert('⚠️ No postcode found!\n\nPlease enter a postcode in cell A6 of the BtM sheet.');
    return;
  }
  
  // Geocode the postcode using postcodes.io
  var siteData = [];
  try {
    var cleanPostcode = postcode.toString().trim().replace(/\s+/g, '');
    var url = 'https://api.postcodes.io/postcodes/' + encodeURIComponent(cleanPostcode);
    var response = UrlFetchApp.fetch(url);
    var json = JSON.parse(response.getContentText());
    
    if (json.status == 200 && json.result) {
      var lat = json.result.latitude;
      var lon = json.result.longitude;
      var area = json.result.admin_district || 'Unknown';
      
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
  var siteDataJson = JSON.stringify(siteData);
  
  var html = HtmlService.createHtmlOutput(`
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

// NOTE: getGeoJSONData() function removed - now fetching directly from GitHub

// ============================================================================
// BESS TOOLS FUNCTIONS
// ============================================================================

/**
 * Generate HH Data directly - called from BESS sheet button/menu
 * Reads Min/Avg/Max kW from B17:B19 and generates synthetic half-hourly data
 */
function generateHHDataDirect() {
  const sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName('BESS');
  
  if (!sheet) {
    SpreadsheetApp.getUi().alert('Error', 'BESS sheet not found', SpreadsheetApp.getUi().ButtonSet.OK);
    return;
  }
  
  // Show progress
  SpreadsheetApp.getUi().showModelessDialog(
    HtmlService.createHtmlOutput('<h3>⏳ Generating HH Data...</h3><p>This will take 30-60 seconds</p><p>Parameters from B17:B19</p>'),
    'HH Data Generator'
  );
  
  try {
    // Read parameters
    const minKw = sheet.getRange('B17').getValue() || 500;
    const avgKw = sheet.getRange('B18').getValue() || 1000;
    const maxKw = sheet.getRange('B19').getValue() || 1500;
    
    Logger.log('Generating HH Data: Min=' + minKw + ', Avg=' + avgKw + ', Max=' + maxKw);
    
    // Trigger webhook to Python script
    const webhookUrl = 'http://localhost:5001/generate_hh'; // Local webhook
    
    const payload = {
      min_kw: minKw,
      avg_kw: avgKw,
      max_kw: maxKw,
      days: 365
    };
    
    const options = {
      method: 'post',
      contentType: 'application/json',
      payload: JSON.stringify(payload),
      muteHttpExceptions: true
    };
    
    try {
      const response = UrlFetchApp.fetch(webhookUrl, options);
      const result = JSON.parse(response.getContentText());
      
      if (result.status === 'success') {
        SpreadsheetApp.getUi().alert(
          'Success',
          '✅ HH Data generated!\n\n' + result.periods + ' periods created\nDate range: ' + result.date_range,
          SpreadsheetApp.getUi().ButtonSet.OK
        );
      } else {
        throw new Error(result.message || 'Unknown error');
      }
    } catch (webhookError) {
      // Webhook not available - show manual instructions
      Logger.log('Webhook error: ' + webhookError);
      SpreadsheetApp.getUi().alert(
        'Manual Generation Required',
        'Python webhook not running.\n\nTo generate HH Data, run this command in terminal:\n\n' +
        'cd ~/GB-Power-Market-JJ\n' +
        'python3 generate_hh_profile.py\n\n' +
        'Parameters: Min=' + minKw + 'kW, Avg=' + avgKw + 'kW, Max=' + maxKw + 'kW',
        SpreadsheetApp.getUi().ButtonSet.OK
      );
    }
    
  } catch (error) {
    Logger.log('Error: ' + error);
    SpreadsheetApp.getUi().alert(
      'Error',
      '❌ Failed to generate HH Data\n\n' + error.message,
      SpreadsheetApp.getUi().ButtonSet.OK
    );
  }
}

/**
 * Manual refresh of DNO data - triggers Python lookup
 */
function manualRefreshDno() {
  const sheet = SpreadsheetApp.getActive().getSheetByName('BESS');
  
  if (!sheet) {
    SpreadsheetApp.getUi().alert('Error', 'BESS sheet not found', SpreadsheetApp.getUi().ButtonSet.OK);
    return;
  }
  
  const postcode = sheet.getRange('A6').getValue();
  const mpanId = sheet.getRange('B6').getValue();
  const voltage = String(sheet.getRange('A9').getValue() || '');
  
  // Show loading indicator
  sheet.getRange('A4:H4').setValues([[
    '🔄 Looking up DNO...', 
    'Calling Python script...', 
    '', '', '', '', '', ''
  ]]);
  sheet.getRange('A4:H4').setBackground('#FFEB3B');  // Yellow
  sheet.getRange('A4:H4').setFontWeight('bold');
  SpreadsheetApp.flush();
  
  // Extract voltage level
  var voltageLevel = 'LV';
  const voltageStr = String(voltage || '');
  if (voltageStr && voltageStr.indexOf('(') > 0) {
    voltageLevel = voltageStr.substring(0, voltageStr.indexOf('(')).trim();
  }
  
  // Determine MPAN from postcode or use direct MPAN
  var finalMpan = mpanId;
  
  if (postcode && postcode.toString().trim()) {
    // Try to geocode postcode and map to MPAN
    try {
      const postcodeClean = postcode.toString().trim().toUpperCase().replace(/\s+/g, '');
      const postcodeResponse = UrlFetchApp.fetch(
        'https://api.postcodes.io/postcodes/' + encodeURIComponent(postcodeClean),
        { muteHttpExceptions: true }
      );
      
      if (postcodeResponse.getResponseCode() === 200) {
        const postcodeData = JSON.parse(postcodeResponse.getContentText());
        if (postcodeData.status === 200) {
          const lat = postcodeData.result.latitude;
          const lng = postcodeData.result.longitude;
          
          // Map coordinates to MPAN
          finalMpan = coordinatesToMpan(lat, lng);
          
          Logger.log('Geocoded ' + postcode + ' -> MPAN ' + finalMpan);
        }
      }
    } catch (e) {
      Logger.log('Geocoding error: ' + e);
    }
  }
  
  if (!finalMpan) {
    sheet.getRange('A4:H4').setValues([[
      '❌ No valid postcode or MPAN', '', '', '', '', '', '', ''
    ]]);
    sheet.getRange('A4:H4').setBackground('#FF5252');  // Red
    return;
  }
  
  // Call Python webhook
  const webhookUrl = 'http://localhost:5001/dno_lookup';
  
  const payload = {
    mpan_id: finalMpan,
    voltage: voltageLevel
  };
  
  const options = {
    method: 'post',
    contentType: 'application/json',
    payload: JSON.stringify(payload),
    muteHttpExceptions: true
  };
  
  try {
    const response = UrlFetchApp.fetch(webhookUrl, options);
    const result = JSON.parse(response.getContentText());
    
    if (result.status === 'success') {
      sheet.getRange('A4:H4').setValues([[
        '✅ DNO data refreshed!', result.dno_name || '', '', '', '', '', '', ''
      ]]);
      sheet.getRange('A4:H4').setBackground('#4CAF50');  // Green
    } else {
      throw new Error(result.message || 'Lookup failed');
    }
  } catch (webhookError) {
    // Webhook not available - show manual instructions
    Logger.log('Webhook error: ' + webhookError);
    sheet.getRange('A4:H4').setValues([[
      '⚡ Run: python3 dno_lookup_python.py ' + finalMpan + ' ' + voltageLevel,
      '', '', '', '', '', '', ''
    ]]);
    sheet.getRange('A4:H4').setBackground('#FFC107');  // Amber
  }
}

/**
 * Map coordinates to MPAN ID using regional boundaries
 */
function coordinatesToMpan(lat, lng) {
  // Regional boundary definitions
  const regions = [
    // Scotland
    { bounds: [56.0, 60.0, -7.0, -1.0], mpan: 17 },  // SSE-SHEPD
    { bounds: [55.0, 56.0, -5.0, -2.0], mpan: 18 },  // SP-Distribution
    
    // North England
    { bounds: [54.0, 55.5, -3.5, -1.0], mpan: 15 },  // NPg-NE
    { bounds: [53.0, 54.5, -2.5, -0.5], mpan: 23 },  // NPg-Y
    { bounds: [53.0, 54.0, -3.5, -2.0], mpan: 16 },  // ENWL
    { bounds: [53.0, 54.0, -4.0, -2.5], mpan: 13 },  // SP-Manweb
    
    // Midlands
    { bounds: [52.0, 53.5, -3.0, -0.5], mpan: 11 },  // NGED-EM
    { bounds: [52.0, 53.0, -3.0, -1.5], mpan: 14 },  // NGED-WM
    
    // East England
    { bounds: [51.5, 53.0, 0.0, 2.0], mpan: 10 },    // UKPN-EPN
    
    // London & South East
    { bounds: [51.3, 51.7, -0.5, 0.3], mpan: 12 },   // UKPN-LPN
    { bounds: [50.8, 51.8, -0.5, 1.5], mpan: 19 },   // UKPN-SPN
    { bounds: [50.5, 52.0, -2.5, 0.0], mpan: 20 },   // SSE-SEPD
    
    // South West & Wales
    { bounds: [51.0, 52.5, -5.5, -2.5], mpan: 21 },  // NGED-SWales
    { bounds: [50.0, 51.5, -6.0, -2.0], mpan: 22 },  // NGED-SW
  ];
  
  // Find matching region
  for (var i = 0; i < regions.length; i++) {
    const r = regions[i];
    const latMin = r.bounds[0];
    const latMax = r.bounds[1];
    const lngMin = r.bounds[2];
    const lngMax = r.bounds[3];
    
    if (lat >= latMin && lat <= latMax && lng >= lngMin && lng <= lngMax) {
      return r.mpan;
    }
  }
  
  // Default to London if no match
  return 12;
}

/**
 * Calculate PPA analysis (new function)
 */
function calculatePPAAnalysis() {
  const sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName('BESS');
  
  SpreadsheetApp.getUi().showModelessDialog(
    HtmlService.createHtmlOutput('<h3>⏳ Calculating PPA Analysis...</h3><p>This will take 1-2 minutes</p><p>Querying BigQuery for system prices</p>'),
    'PPA Analysis'
  );
  
  // For now, show manual instructions
  Utilities.sleep(1000);
  
  SpreadsheetApp.getUi().alert(
    'Manual Calculation',
    'To calculate PPA analysis, run:\n\n' +
    'cd ~/GB-Power-Market-JJ\n' +
    'python3 calculate_btm_ppa_analysis.py\n\n' +
    'This will:\n' +
    '- Read HH Data\n' +
    '- Query BigQuery for system prices\n' +
    '- Calculate profitable periods\n' +
    '- Update BESS sheet rows 26-42',
    SpreadsheetApp.getUi().ButtonSet.OK
  );
}

/**
 * Show HH Data status
 */
function showHHDataStatus() {
  try {
    const hhSheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName('HH Data');
    
    if (!hhSheet) {
      SpreadsheetApp.getUi().alert(
        'HH Data Status',
        '❌ HH Data sheet does not exist\n\nUse: 🔋 BESS Tools → Generate HH Data',
        SpreadsheetApp.getUi().ButtonSet.OK
      );
      return;
    }
    
    const lastRow = hhSheet.getLastRow();
    const header = hhSheet.getRange(1, 1, 1, 4).getValues()[0];
    
    var message = '✅ HH Data sheet exists\n\n';
    message += 'Rows: ' + (lastRow - 1) + ' data rows\n';
    message += 'Expected: 17,520 rows (365 days × 48 periods)\n\n';
    message += 'Columns: ' + header.join(', ');
    
    if (lastRow > 1) {
      const firstData = hhSheet.getRange(2, 1, 1, 2).getValues()[0];
      const lastData = hhSheet.getRange(lastRow, 1, 1, 2).getValues()[0];
      message += '\n\nFirst: ' + firstData[0] + ' - ' + firstData[1] + ' kW';
      message += '\nLast: ' + lastData[0] + ' - ' + lastData[1] + ' kW';
    }
    
    SpreadsheetApp.getUi().alert('HH Data Status', message, SpreadsheetApp.getUi().ButtonSet.OK);
    
  } catch (error) {
    SpreadsheetApp.getUi().alert('Error', 'Failed to check HH Data: ' + error.message, SpreadsheetApp.getUi().ButtonSet.OK);
  }
}

/**
 * Auto-trigger on edit (optional - requires trigger setup)
 */
function onEdit(e) {
  try {
    const sheet = e.source.getActiveSheet();
    
    // Only run on BESS sheet
    if (sheet.getName() !== 'BESS') {
      return;
    }
    
    const range = e.range;
    const row = range.getRow();
    const col = range.getColumn();
    
    // Check if edit was in A6 (postcode) or B6 (MPAN)
    if (row === 6 && (col === 1 || col === 2)) {
      // Get current values
      const postcode = sheet.getRange('A6').getValue();
      const mpanId = sheet.getRange('B6').getValue();
      
      // Only trigger if there's actually a value
      if (!postcode && !mpanId) {
        return;
      }
      
      // Show loading indicator
      sheet.getRange('A4:H4').setValues([[
        '🔄 Auto-looking up DNO...', '', '', '', '', '', '', ''
      ]]);
      sheet.getRange('A4:H4').setBackground('#FFEB3B');  // Yellow
      
      // Trigger the lookup (after a small delay to allow user to finish typing)
      Utilities.sleep(1500);
      manualRefreshDno();
    }
    
  } catch (err) {
    Logger.log('onEdit error: ' + err);
  }
}

// ============================================================================
// SPARKLINE FUNCTIONS (for BtM spreadsheet - GB Live sheet)
// ============================================================================

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
  
  SpreadsheetApp.getUi().alert(
    'Success',
    '✅ All sparkline formulas written!\n\n20 sparklines created:\n- 10 fuel types (Column C)\n- 10 interconnectors (Column F)',
    SpreadsheetApp.getUi().ButtonSet.OK
  );
  
  Logger.log('✅ All sparkline formulas written successfully!');
}

/**
 * Write fuel type sparklines to Column C (rows 11-20)
 */
function writeFuelSparklines(sheet) {
  Logger.log('📝 Writing Column C fuel sparklines...');
  
  FUEL_SPARKLINES.forEach(config => {
    const formula = '=SPARKLINE(Data_Hidden!A' + config.dataRow + ':X' + config.dataRow + ',' +
                   '{"charttype","line";"linewidth",2;"color","' + config.color + '";' +
                   '"max",' + config.max + ';"ymin",0})';
    
    sheet.getRange('C' + config.row).setFormula(formula);
    Logger.log('   ✅ C' + config.row + ' (' + config.label + '): Formula written');
  });
  
  Logger.log('✅ Wrote ' + FUEL_SPARKLINES.length + ' fuel sparklines');
}

/**
 * Write interconnector sparklines to Column F (rows 11-20)
 */
function writeInterconnectorSparklines(sheet) {
  Logger.log('📝 Writing Column F interconnector sparklines...');
  
  IC_SPARKLINES.forEach(config => {
    const formula = '=SPARKLINE(Data_Hidden!A' + config.dataRow + ':X' + config.dataRow + ',' +
                   '{"charttype","line";"linewidth",2;"color","' + config.color + '";' +
                   '"max",' + config.max + ';"ymin",0})';
    
    sheet.getRange('F' + config.row).setFormula(formula);
    Logger.log('   ✅ F' + config.row + ' (' + config.label + '): Formula written');
  });
  
  Logger.log('✅ Wrote ' + IC_SPARKLINES.length + ' interconnector sparklines');
}

/**
 * Verify that Data_Hidden sheet has data
 */
function verifyDataHidden() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const dataHidden = ss.getSheetByName('Data_Hidden');
  
  if (!dataHidden) {
    SpreadsheetApp.getUi().alert(
      'Data_Hidden Not Found',
      '❌ Data_Hidden sheet not found!\n\nRun Python script first:\ncd ~/GB-Power-Market-JJ\npython3 update_bg_live_dashboard.py',
      SpreadsheetApp.getUi().ButtonSet.OK
    );
    return false;
  }
  
  // Check if row 1 has data (Wind generation)
  const row1Values = dataHidden.getRange('A1:X1').getValues()[0];
  const nonEmpty = row1Values.filter(v => v !== '' && v !== null && v !== undefined);
  
  var message = '✅ Data_Hidden found!\n\n';
  message += 'Data points in row 1: ' + nonEmpty.length + ' / 24\n';
  message += 'Expected: 24 values (12 hours × 2 periods/hour)\n\n';
  
  if (nonEmpty.length >= 10) {
    message += 'Status: ✅ Ready for sparklines\n\n';
    message += 'Sample values: ' + row1Values.slice(0, 5).join(', ');
  } else {
    message += 'Status: ⚠️ Insufficient data\n\n';
    message += 'Run: python3 update_bg_live_dashboard.py';
  }
  
  SpreadsheetApp.getUi().alert('Data_Hidden Status', message, SpreadsheetApp.getUi().ButtonSet.OK);
  
  Logger.log('✅ Data_Hidden found with ' + nonEmpty.length + '/24 data points in row 1');
  return nonEmpty.length >= 10;
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
  
  SpreadsheetApp.getUi().alert(
    'Cleared',
    '✅ Cleared all sparklines\n\nColumns C and F (rows 11-20) are now empty.',
    SpreadsheetApp.getUi().ButtonSet.OK
  );
  
  Logger.log('✅ Cleared all sparklines from columns C and F');
}

/**
 * Quick health check - run this from menu
 */
function quickHealthCheck() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const ui = SpreadsheetApp.getUi();
  
  var report = '📊 Health Check: ' + ss.getName() + '\n\n';
  
  // Check sheets
  const gbLive = ss.getSheetByName('GB Live');
  const dataHidden = ss.getSheetByName('Data_Hidden');
  const bess = ss.getSheetByName('BESS');
  
  report += 'Sheets:\n';
  report += (gbLive ? '  ✅ GB Live\n' : '  ⚠️ GB Live (not found)\n');
  report += (dataHidden ? '  ✅ Data_Hidden\n' : '  ⚠️ Data_Hidden (not found)\n');
  report += (bess ? '  ✅ BESS\n' : '  ⚠️ BESS (not found)\n');
  
  // Check sparklines (if applicable)
  if (gbLive) {
    const c11 = gbLive.getRange('C11').getFormula();
    const f11 = gbLive.getRange('F11').getFormula();
    report += '\nSparklines:\n';
    report += (c11 && c11.indexOf('SPARKLINE') >= 0 ? '  ✅ Column C (Fuel)\n' : '  ❌ Column C missing\n');
    report += (f11 && f11.indexOf('SPARKLINE') >= 0 ? '  ✅ Column F (IC)\n' : '  ❌ Column F missing\n');
  }
  
  // Check data
  if (dataHidden) {
    const row1 = dataHidden.getRange('A1:X1').getValues()[0];
    const nonEmpty = row1.filter(v => v !== '' && v !== null);
    report += '\nData:\n';
    report += (nonEmpty.length >= 10 ? '  ✅ Data_Hidden has data (' + nonEmpty.length + ' values)\n' : '  ⚠️ Insufficient data (' + nonEmpty.length + ' values)\n');
  }
  
  // Check triggers
  const triggers = ScriptApp.getProjectTriggers();
  report += '\nTriggers: ' + triggers.length + ' active\n';
  
  report += '\nSpreadsheet ID: ' + ss.getId().substring(0, 20) + '...';
  
  ui.alert('Health Check Results', report, ui.ButtonSet.OK);
  
  Logger.log(report);
}

// ============================================================================
// DIAGNOSTIC FUNCTIONS
// ============================================================================

/**
 * Comprehensive environment diagnostics
 */
function diagnostics() {
  Logger.log('='.repeat(70));
  Logger.log('=== COMPREHENSIVE DIAGNOSTICS ===');
  Logger.log('='.repeat(70));
  
  // 1. Current user
  try {
    const user = Session.getActiveUser().getEmail();
    Logger.log('✅ User: ' + (user || 'Anonymous'));
  } catch (e) {
    Logger.log('❌ User: Error - ' + e);
  }
  
  // 2. Spreadsheet information
  try {
    const ss = SpreadsheetApp.getActiveSpreadsheet();
    Logger.log('\n📊 Spreadsheet Information:');
    Logger.log('   Name: ' + ss.getName());
    Logger.log('   ID: ' + ss.getId());
    Logger.log('   URL: ' + ss.getUrl());
    Logger.log('   Total Sheets: ' + ss.getSheets().length);
    
    // Detect which spreadsheet
    const ssId = ss.getId();
    if (ssId === '1MSl8fJ0to6Y08enXA2oysd8wvNUVm3AtfJ1bVqRH8_I') {
      Logger.log('   Type: 🎯 BtM Spreadsheet (Sparklines)');
    } else if (ssId === '12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8') {
      Logger.log('   Type: 🎯 GB Energy Dashboard (BESS)');
    } else {
      Logger.log('   Type: ⚠️ Unknown spreadsheet');
    }
    
    Logger.log('\n   Sheets list:');
    ss.getSheets().slice(0, 15).forEach(s => Logger.log('      - ' + s.getName()));
    if (ss.getSheets().length > 15) {
      Logger.log('      ... and ' + (ss.getSheets().length - 15) + ' more');
    }
  } catch (e) {
    Logger.log('❌ Spreadsheet info: Error - ' + e);
  }
  
  // 3. Check required sheets
  Logger.log('\n📋 Required Sheets Check:');
  checkSheetDiagnostic('GB Live');
  checkSheetDiagnostic('Data_Hidden');
  checkSheetDiagnostic('BESS');
  checkSheetDiagnostic('BtM');
  checkSheetDiagnostic('DNO');
  checkSheetDiagnostic('HH Data');
  
  // 4. Active triggers
  try {
    const triggers = ScriptApp.getProjectTriggers();
    Logger.log('\n⏰ Active Triggers: ' + triggers.length);
    if (triggers.length > 0) {
      triggers.forEach(t => {
        Logger.log('   - ' + t.getHandlerFunction() + ' | ' + t.getEventType());
      });
    } else {
      Logger.log('   (No triggers configured)');
    }
  } catch (e) {
    Logger.log('❌ Triggers: Error - ' + e);
  }
  
  // 5. Test sparkline formulas (if applicable)
  Logger.log('\n✨ Sparkline Formula Check:');
  try {
    const ss = SpreadsheetApp.getActiveSpreadsheet();
    const gbLive = ss.getSheetByName('GB Live');
    if (gbLive) {
      const c11 = gbLive.getRange('C11').getFormula();
      const f11 = gbLive.getRange('F11').getFormula();
      Logger.log('   C11: ' + (c11 ? (c11.indexOf('SPARKLINE') >= 0 ? '✅ Has formula' : '⚠️ ' + c11) : '❌ Empty'));
      Logger.log('   F11: ' + (f11 ? (f11.indexOf('SPARKLINE') >= 0 ? '✅ Has formula' : '⚠️ ' + f11) : '❌ Empty'));
    } else {
      Logger.log('   ⚠️ GB Live sheet not found (not applicable for this spreadsheet)');
    }
  } catch (e) {
    Logger.log('   ❌ Error checking formulas: ' + e);
  }
  
  // 6. Test Data_Hidden content (if applicable)
  Logger.log('\n📈 Data_Hidden Content Check:');
  try {
    const ss = SpreadsheetApp.getActiveSpreadsheet();
    const dataHidden = ss.getSheetByName('Data_Hidden');
    if (dataHidden) {
      const row1 = dataHidden.getRange('A1:X1').getValues()[0];
      const nonEmpty = row1.filter(v => v !== '' && v !== null);
      Logger.log('   ✅ Row 1 (Wind): ' + nonEmpty.length + ' values');
      Logger.log('   Sample: [' + row1.slice(0, 5).join(', ') + '...]');
    } else {
      Logger.log('   ⚠️ Data_Hidden sheet not found (not applicable for this spreadsheet)');
    }
  } catch (e) {
    Logger.log('   ❌ Error reading Data_Hidden: ' + e);
  }
  
  // 7. Test GitHub access
  Logger.log('\n🌐 GitHub GeoJSON Access:');
  try {
    const url = 'https://raw.githubusercontent.com/GeorgeDoors888/GB-Power-Market-JJ/main/gb_power_map_deployment/dno_regions.geojson';
    const response = UrlFetchApp.fetch(url, {muteHttpExceptions: true});
    const code = response.getResponseCode();
    if (code === 200) {
      const json = JSON.parse(response.getContentText());
      Logger.log('   ✅ GitHub accessible - ' + (json.features ? json.features.length + ' features' : 'JSON loaded'));
    } else {
      Logger.log('   ❌ HTTP ' + code);
    }
  } catch (e) {
    Logger.log('   ❌ Error: ' + e);
  }
  
  Logger.log('\n' + '='.repeat(70));
  Logger.log('✅ Diagnostics complete! Check View → Executions for full log.');
  Logger.log('='.repeat(70));
  
  SpreadsheetApp.getUi().alert(
    'Diagnostics Complete',
    'Full diagnostic report generated!\n\nView results:\nExtensions → Apps Script → View → Executions\n\nCheck the execution log for detailed information.',
    SpreadsheetApp.getUi().ButtonSet.OK
  );
}

/**
 * Check if a specific sheet exists (diagnostic helper)
 */
function checkSheetDiagnostic(sheetName) {
  try {
    const ss = SpreadsheetApp.getActiveSpreadsheet();
    const sheet = ss.getSheetByName(sheetName);
    if (sheet) {
      Logger.log('   ✅ ' + sheetName + ' (ID: ' + sheet.getSheetId() + ')');
      return true;
    } else {
      Logger.log('   ⚠️ ' + sheetName + ' - NOT FOUND');
      return false;
    }
  } catch (e) {
    Logger.log('   ❌ ' + sheetName + ' - Error: ' + e);
    return false;
  }
}

/**
 * Show spreadsheet info popup
 */
function showSpreadsheetInfo() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const ssId = ss.getId();
  
  var message = '📊 Spreadsheet Information\n\n';
  message += 'Name: ' + ss.getName() + '\n';
  message += 'ID: ' + ssId + '\n';
  message += 'URL: ' + ss.getUrl() + '\n\n';
  
  // Detect type
  if (ssId === '1MSl8fJ0to6Y08enXA2oysd8wvNUVm3AtfJ1bVqRH8_I') {
    message += 'Type: 🎯 BtM Spreadsheet\n';
    message += 'Features:\n';
    message += '  ✅ GB Live + Sparklines\n';
    message += '  ✅ BESS Tools\n';
    message += '  ✅ DNO Map\n';
  } else if (ssId === '12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8') {
    message += 'Type: 🎯 GB Energy Dashboard\n';
    message += 'Features:\n';
    message += '  ✅ BESS Tools (primary)\n';
    message += '  ✅ DNO Map\n';
    message += '  ⚠️ No sparklines (use BtM spreadsheet)\n';
  } else {
    message += 'Type: ⚠️ Unknown\n';
  }
  
  message += '\nTotal Sheets: ' + ss.getSheets().length;
  
  SpreadsheetApp.getUi().alert('Spreadsheet Info', message, SpreadsheetApp.getUi().ButtonSet.OK);
}

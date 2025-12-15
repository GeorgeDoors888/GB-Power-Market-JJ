// GB Energy Market Dashboard - Apps Script
// Version 3 - With Real DNO Boundaries from GitHub

function onOpen() {
  var ui = SpreadsheetApp.getUi();
  ui.createMenu('🗺️ DNO Map')
      .addItem('View Interactive Map', 'createDNOMap')
      .addItem('View Map with Site Markers', 'createDNOMapWithSites')
      .addItem('Embed Map in DNO Sheet', 'embedMapInSheet')
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

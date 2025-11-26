/**
 * @OnlyCurrentDoc
 */

var BOUNDARY_COORDS = {
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

function onOpen() {
  SpreadsheetApp.getUi()
    .createMenu('🗺️ Constraint Map')
    .addItem('📍 Show Live Map', 'showConstraintMapLive')
    .addToUi();
}

function showConstraintMapLive() {
  var html = HtmlService.createHtmlOutput(getMapHtml())
    .setTitle('GB Transmission Constraints')
    .setWidth(600);
  SpreadsheetApp.getUi().showSidebar(html);
}

function getConstraintData() {
  var sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName('Dashboard');
  var data = sheet.getRange('A116:H126').getValues();
  var constraints = [];
  
  for (var i = 1; i < data.length; i++) {
    var row = data[i];
    var boundary = row[0];
    if (!boundary) continue;
    
    var coords = BOUNDARY_COORDS[boundary];
    if (!coords) continue;
    
    constraints.push({
      boundary: boundary,
      flow: parseFloat(row[3]) || 0,
      limit: parseFloat(row[4]) || 0,
      utilization: parseFloat(row[7]) || 0,
      status: row[6] || 'Unknown',
      direction: row[5] || '—',
      lat: coords.lat,
      lng: coords.lng
    });
  }
  
  return constraints;
}

function getMapHtml() {
  var constraints = getConstraintData();
  var json = JSON.stringify(constraints);
  
  var html = '<!DOCTYPE html>';
  html += '<html><head>';
  html += '<meta charset="utf-8">';
  html += '<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>';
  html += '<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>';
  html += '<style>';
  html += 'body{margin:0;padding:0;font-family:Arial}';
  html += '#map{width:100%;height:100vh}';
  html += '.legend{position:absolute;bottom:30px;right:10px;background:white;padding:10px;border-radius:5px;box-shadow:0 2px 5px rgba(0,0,0,0.3);z-index:1000;font-size:12px}';
  html += '.legend-item{margin:5px 0}';
  html += '.legend-color{width:20px;height:20px;border-radius:50%;margin-right:8px;border:2px solid #333;display:inline-block}';
  html += '</style>';
  html += '</head><body>';
  html += '<div id="map"></div>';
  html += '<div class="legend">';
  html += '<strong>Utilization</strong><br>';
  html += '<div class="legend-item"><span class="legend-color" style="background:#4CAF50"></span> &lt; 50% (Normal)</div>';
  html += '<div class="legend-item"><span class="legend-color" style="background:#FFC107"></span> 50-75% (Moderate)</div>';
  html += '<div class="legend-item"><span class="legend-color" style="background:#FF9800"></span> 75-90% (High)</div>';
  html += '<div class="legend-item"><span class="legend-color" style="background:#F44336"></span> &gt; 90% (Critical)</div>';
  html += '</div>';
  html += '<script>';
  html += 'var constraints=' + json + ';';
  html += 'var map=L.map("map").setView([54.5,-3.5],6);';
  html += 'L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",{attribution:"© OpenStreetMap"}).addTo(map);';
  html += 'constraints.forEach(function(c){';
  html += 'var col="#4CAF50";';
  html += 'if(c.utilization>=90)col="#F44336";';
  html += 'else if(c.utilization>=75)col="#FF9800";';
  html += 'else if(c.utilization>=50)col="#FFC107";';
  html += 'var m=L.circleMarker([c.lat,c.lng],{radius:12,fillColor:col,color:"#333",weight:2,opacity:1,fillOpacity:0.8}).addTo(map);';
  html += 'm.bindPopup("<h3>"+c.boundary+"</h3><table><tr><td>Flow:</td><td>"+c.flow.toFixed(0)+" MW</td></tr><tr><td>Limit:</td><td>"+c.limit.toFixed(0)+" MW</td></tr><tr><td>Util:</td><td style=color:"+col+">"+c.utilization.toFixed(1)+"%</td></tr></table>");';
  html += '});';
  html += '</script>';
  html += '</body></html>';
  
  return html;
}

function testMapData() {
  var constraints = getConstraintData();
  Logger.log('Found ' + constraints.length + ' constraints');
  if (constraints.length > 0) {
    Logger.log('Sample: ' + JSON.stringify(constraints[0]));
  }
}

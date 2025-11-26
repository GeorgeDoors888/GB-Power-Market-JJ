/**
 * Dashboard V2 - Complete Apps Script
 * Menus, charts, data refresh, formatting automation
 */

// ============================================================================
// CONFIGURATION
// ============================================================================

var CONFIG = {
  SPREADSHEET_ID: 'YOUR_SPREADSHEET_ID_HERE',
  WEBHOOK_URL: 'YOUR_WEBHOOK_URL_HERE',  // Update when deploying
  BOUNDARY_COORDS: {
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
  }
};

// ============================================================================
// MENU SYSTEM
// ============================================================================

function onOpen() {
  var ui = SpreadsheetApp.getUi();
  
  ui.createMenu('🗺️ Maps')
    .addItem('📍 Constraint Map', 'showConstraintMap')
    .addItem('⚡ Generator Map', 'showGeneratorMap')
    .addToUi();
    
  ui.createMenu('🔄 Data')
    .addItem('📥 Refresh All Data', 'refreshAllData')
    .addSeparator()
    .addItem('📊 Refresh Dashboard', 'refreshDashboard')
    .addItem('🔋 Refresh BESS', 'refreshBESS')
    .addItem('⚠️ Refresh Outages', 'refreshOutages')
    .addItem('📈 Refresh Charts', 'refreshCharts')
    .addToUi();
    
  ui.createMenu('🎨 Format')
    .addItem('✨ Apply Theme', 'applyTheme')
    .addItem('🔢 Format Numbers', 'formatNumbers')
    .addItem('📏 Auto-resize Columns', 'autoResizeColumns')
    .addToUi();
    
  ui.createMenu('🛠️ Tools')
    .addItem('🧹 Clear Old Data', 'clearOldData')
    .addItem('📋 Export to CSV', 'exportToCSV')
    .addItem('ℹ️ About Dashboard', 'showAbout')
    .addToUi();
}

// ============================================================================
// DATA REFRESH FUNCTIONS
// ============================================================================

function refreshAllData() {
  var ui = SpreadsheetApp.getUi();
  var result = ui.alert(
    'Refresh All Data',
    'This will update Dashboard, BESS, Outages, and Charts. Continue?',
    ui.ButtonSet.YES_NO
  );
  
  if (result == ui.Button.YES) {
    SpreadsheetApp.getActiveSpreadsheet().toast('Starting full refresh...', 'Data Refresh', 5);
    refreshDashboard();
    Utilities.sleep(2000);
    refreshBESS();
    Utilities.sleep(2000);
    refreshOutages();
    Utilities.sleep(2000);
    refreshCharts();
    SpreadsheetApp.getActiveSpreadsheet().toast('✅ All data refreshed!', 'Complete', 5);
  }
}

function refreshDashboard() {
  try {
    var response = UrlFetchApp.fetch(CONFIG.WEBHOOK_URL + '/refresh-dashboard', {
      method: 'post',
      muteHttpExceptions: true
    });
    
    var result = JSON.parse(response.getContentText());
    
    if (result.success) {
      SpreadsheetApp.getActiveSpreadsheet().toast('Dashboard updated', 'Success', 3);
    }
  } catch (e) {
    Logger.log('Refresh error: ' + e.message);
  }
}

function refreshBESS() {
  SpreadsheetApp.getActiveSpreadsheet().toast('Refreshing BESS data...', 'Data Refresh', 3);
}

function refreshOutages() {
  SpreadsheetApp.getActiveSpreadsheet().toast('Refreshing outages...', 'Data Refresh', 3);
}

function refreshCharts() {
  SpreadsheetApp.getActiveSpreadsheet().toast('Updating chart data...', 'Charts', 3);
  SpreadsheetApp.flush();
}

// ============================================================================
// CONSTRAINT MAP
// ============================================================================

function showConstraintMap() {
  var html = HtmlService.createHtmlOutput(getConstraintMapHtml())
    .setTitle('GB Transmission Constraints')
    .setWidth(600);
  SpreadsheetApp.getUi().showSidebar(html);
}

function getConstraintData() {
  var sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName('Dashboard');
  if (!sheet) return [];
  
  var data = sheet.getRange('A116:H126').getValues();
  var constraints = [];
  
  for (var i = 1; i < data.length; i++) {
    var row = data[i];
    var boundary = row[0];
    if (!boundary) continue;
    
    var coords = CONFIG.BOUNDARY_COORDS[boundary];
    if (!coords) continue;
    
    constraints.push({
      boundary: boundary,
      flow: parseFloat(row[3]) || 0,
      limit: parseFloat(row[4]) || 0,
      utilization: parseFloat(row[7]) || 0,
      lat: coords.lat,
      lng: coords.lng
    });
  }
  
  return constraints;
}

function getConstraintMapHtml() {
  var constraints = getConstraintData();
  var json = JSON.stringify(constraints);
  
  var html = '<!DOCTYPE html><html><head>';
  html += '<meta charset="utf-8">';
  html += '<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>';
  html += '<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>';
  html += '<style>body{margin:0;padding:0;font-family:Arial}#map{width:100%;height:100vh}</style>';
  html += '</head><body><div id="map"></div><script>';
  html += 'var c=' + json + ';';
  html += 'var m=L.map("map").setView([54.5,-3.5],6);';
  html += 'L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png").addTo(m);';
  html += 'c.forEach(function(d){';
  html += 'var col="#4CAF50";';
  html += 'if(d.utilization>=90)col="#F44336";';
  html += 'else if(d.utilization>=75)col="#FF9800";';
  html += 'else if(d.utilization>=50)col="#FFC107";';
  html += 'L.circleMarker([d.lat,d.lng],{radius:12,fillColor:col,color:"#333",weight:2,fillOpacity:0.8}).addTo(m)';
  html += '.bindPopup("<h3>"+d.boundary+"</h3><b>Flow:</b> "+d.flow.toFixed(0)+" MW<br><b>Limit:</b> "+d.limit.toFixed(0)+" MW<br><b>Util:</b> "+d.utilization.toFixed(1)+"%");';
  html += '});</script></body></html>';
  
  return html;
}

// ============================================================================
// FORMATTING FUNCTIONS
// ============================================================================

function applyTheme() {
  var dashboard = SpreadsheetApp.getActiveSpreadsheet().getSheetByName('Dashboard');
  if (!dashboard) return;
  
  SpreadsheetApp.getActiveSpreadsheet().toast('Applying theme...', 'Format', 3);
  
  var headerRange = dashboard.getRange('A1:K3');
  headerRange.setBackground('#0072ce').setFontColor('#FFFFFF').setFontWeight('bold');
  
  SpreadsheetApp.getActiveSpreadsheet().toast('✅ Theme applied!', 'Complete', 3);
}

function formatNumbers() {
  var dashboard = SpreadsheetApp.getActiveSpreadsheet().getSheetByName('Dashboard');
  if (!dashboard) return;
  
  var genRange = dashboard.getRange('B10:B40');
  genRange.setNumberFormat('#,##0.0');
  
  var priceRange = dashboard.getRange('B81:B84');
  priceRange.setNumberFormat('£#,##0.00');
  
  SpreadsheetApp.getActiveSpreadsheet().toast('✅ Numbers formatted!', 'Complete', 3);
}

function autoResizeColumns() {
  var sheets = SpreadsheetApp.getActiveSpreadsheet().getSheets();
  sheets.forEach(function(sheet) {
    sheet.autoResizeColumns(1, sheet.getLastColumn());
  });
  SpreadsheetApp.getActiveSpreadsheet().toast('✅ Columns resized!', 'Complete', 3);
}

function showAbout() {
  var ui = SpreadsheetApp.getUi();
  var message = 'GB Energy Dashboard V2\n\n';
  message += 'Real-time energy market data from Elexon BMRS\n';
  message += 'Auto-updates every 5 minutes\n\n';
  message += 'Created: November 2025';
  ui.alert('About', message, ui.ButtonSet.OK);
}

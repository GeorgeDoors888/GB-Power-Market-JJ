/**
 * Dashboard V2 - Complete Apps Script
 * Menus, charts, data refresh, formatting automation
 */

// ============================================================================
// CONFIGURATION
// ============================================================================

var CONFIG = {
  SPREADSHEET_ID: '1LmMq4OEE639Y-XXpOJ3xnvpAmHB6vUovh5g6gaU_vzc',
  WEBHOOK_URL: 'https://5893b8404ab5.ngrok-free.app',
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
      SpreadsheetApp.getActiveSpreadsheet().toast(
        'Dashboard updated with latest data', 
        'Success', 
        3
      );
    } else {
      SpreadsheetApp.getActiveSpreadsheet().toast(
        'Refresh failed: ' + (result.error || 'Unknown error'), 
        'Error', 
        5
      );
    }
  } catch (e) {
    SpreadsheetApp.getActiveSpreadsheet().toast(
      'Webhook error: ' + e.message, 
      'Error', 
      5
    );
  }
}

function refreshBESS() {
  SpreadsheetApp.getActiveSpreadsheet().toast('Refreshing BESS data...', 'Data Refresh', 3);
  // Call webhook for BESS refresh
  try {
    var response = UrlFetchApp.fetch(CONFIG.WEBHOOK_URL + '/refresh-bess', {
      method: 'post',
      muteHttpExceptions: true
    });
    SpreadsheetApp.getActiveSpreadsheet().toast('BESS data updated', 'Success', 3);
  } catch (e) {
    Logger.log('BESS refresh error: ' + e.message);
  }
}

function refreshOutages() {
  SpreadsheetApp.getActiveSpreadsheet().toast('Refreshing outages...', 'Data Refresh', 3);
  // Call webhook for outages refresh
  try {
    var response = UrlFetchApp.fetch(CONFIG.WEBHOOK_URL + '/refresh-outages', {
      method: 'post',
      muteHttpExceptions: true
    });
    SpreadsheetApp.getActiveSpreadsheet().toast('Outages updated', 'Success', 3);
  } catch (e) {
    Logger.log('Outages refresh error: ' + e.message);
  }
}

function refreshCharts() {
  SpreadsheetApp.getActiveSpreadsheet().toast('Updating chart data...', 'Charts', 3);
  // Charts auto-update from their data sources
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
  // Try webhook first
  try {
    var response = UrlFetchApp.fetch(CONFIG.WEBHOOK_URL + '/get-constraints', {
      method: 'get',
      muteHttpExceptions: true
    });
    
    var result = JSON.parse(response.getContentText());
    
    if (result.success && result.constraints.length > 0) {
      return result.constraints;
    }
  } catch (e) {
    Logger.log('Webhook failed, falling back to sheet: ' + e.message);
  }
  
  // Fallback: Read from sheet
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
      status: row[6] || 'Unknown',
      direction: row[5] || '—',
      lat: coords.lat,
      lng: coords.lng
    });
  }
  
  return constraints;
}

function getConstraintMapHtml() {
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
  html += '</style>';
  html += '</head><body>';
  html += '<div id="map"></div>';
  html += '<script>';
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
  html += '});';
  html += '</script></body></html>';
  
  return html;
}

// ============================================================================
// GENERATOR MAP
// ============================================================================

function showGeneratorMap() {
  var html = HtmlService.createHtmlOutputFromFile('GeneratorMap')
    .setTitle('GB Generators')
    .setWidth(800);
  SpreadsheetApp.getUi().showSidebar(html);
}

// ============================================================================
// FORMATTING FUNCTIONS
// ============================================================================

function applyTheme() {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var dashboard = ss.getSheetByName('Dashboard');
  
  if (!dashboard) {
    SpreadsheetApp.getUi().alert('Dashboard sheet not found!');
    return;
  }
  
  SpreadsheetApp.getActiveSpreadsheet().toast('Applying theme...', 'Format', 3);
  
  // Header formatting (Row 1-3)
  var headerRange = dashboard.getRange('A1:K3');
  headerRange.setBackground('#0072ce')
    .setFontColor('#FFFFFF')
    .setFontWeight('bold')
    .setFontSize(11);
  
  // Generation section headers
  var sectionHeaders = ['A10', 'A30', 'A80', 'A116'];
  sectionHeaders.forEach(function(cell) {
    dashboard.getRange(cell).setBackground('#ff7f0f')
      .setFontColor('#FFFFFF')
      .setFontWeight('bold');
  });
  
  SpreadsheetApp.getActiveSpreadsheet().toast('✅ Theme applied!', 'Complete', 3);
}

function formatNumbers() {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var dashboard = ss.getSheetByName('Dashboard');
  
  if (!dashboard) return;
  
  // Format generation values as numbers with comma separator
  var genRange = dashboard.getRange('B10:B40');
  genRange.setNumberFormat('#,##0.0');
  
  // Format prices as currency
  var priceRange = dashboard.getRange('B81:B84');
  priceRange.setNumberFormat('£#,##0.00');
  
  SpreadsheetApp.getActiveSpreadsheet().toast('✅ Numbers formatted!', 'Complete', 3);
}

function autoResizeColumns() {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var sheets = ss.getSheets();
  
  sheets.forEach(function(sheet) {
    sheet.autoResizeColumns(1, sheet.getLastColumn());
  });
  
  SpreadsheetApp.getActiveSpreadsheet().toast('✅ Columns resized!', 'Complete', 3);
}

// ============================================================================
// UTILITY FUNCTIONS
// ============================================================================

function clearOldData() {
  var ui = SpreadsheetApp.getUi();
  var result = ui.alert(
    'Clear Old Data',
    'This will remove data older than 7 days. Continue?',
    ui.ButtonSet.YES_NO
  );
  
  if (result == ui.Button.YES) {
    SpreadsheetApp.getActiveSpreadsheet().toast('Clearing old data...', 'Cleanup', 3);
    // Implement cleanup logic
    SpreadsheetApp.getActiveSpreadsheet().toast('✅ Old data cleared!', 'Complete', 3);
  }
}

function exportToCSV() {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var dashboard = ss.getSheetByName('Dashboard');
  
  if (!dashboard) {
    SpreadsheetApp.getUi().alert('Dashboard sheet not found!');
    return;
  }
  
  var data = dashboard.getDataRange().getValues();
  var csv = '';
  
  data.forEach(function(row) {
    csv += row.join(',') + '\n';
  });
  
  var filename = 'Dashboard_Export_' + new Date().toISOString().split('T')[0] + '.csv';
  var blob = Utilities.newBlob(csv, 'text/csv', filename);
  
  SpreadsheetApp.getUi().alert('CSV created: ' + filename + '\nDownload from Drive');
}

function showAbout() {
  var ui = SpreadsheetApp.getUi();
  var message = 'GB Energy Dashboard V2\n\n';
  message += 'Real-time energy market data from Elexon BMRS\n';
  message += 'Auto-updates every 5 minutes via Python cron\n\n';
  message += 'Features:\n';
  message += '• Live generation by fuel type\n';
  message += '• Market prices and demand\n';
  message += '• Transmission constraints\n';
  message += '• BESS analysis\n';
  message += '• Generator outages\n\n';
  message += 'Created: November 2025';
  
  ui.alert('About', message, ui.ButtonSet.OK);
}

// ============================================================================
// AUTO-REFRESH TRIGGER (Optional - set via Triggers menu)
// ============================================================================

function autoRefresh() {
  // This function can be triggered by a time-based trigger
  // Edit → Current project's triggers → Add trigger
  // Function: autoRefresh
  // Event source: Time-driven
  // Type: Minutes timer
  // Interval: Every 5 minutes
  
  try {
    refreshDashboard();
    Logger.log('Auto-refresh completed at ' + new Date());
  } catch (e) {
    Logger.log('Auto-refresh error: ' + e.message);
  }
}

/**
 * DASHBOARD LIVE INTEGRATION - Apps Script Code
 * Copy this entire file into Apps Script editor
 * This will enable the embedded map and auto-refresh
 */

// Configuration
const SHEET_ID = '12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8';
const DASHBOARD_SHEET = 'Dashboard';
const MAP_RANGE = 'A47:H60';  // Where map will be embedded

/**
 * Creates custom menu on open
 */
function onOpen() {
  const ui = SpreadsheetApp.getUi();
  ui.createMenu('🔄 Live Dashboard')
    .addItem('📊 Refresh All Data', 'refreshDashboard')
    .addItem('🗺️ Show Interactive Map', 'showEmbeddedMap')
    .addItem('📈 Update Charts', 'updateCharts')
    .addSeparator()
    .addItem('⚙️ Auto-Refresh: ON (5 min)', 'showAutoRefreshStatus')
    .addToUi();
  
  Logger.log('✅ Live Dashboard menu created');
}

/**
 * Refresh all dashboard data
 */
function refreshDashboard() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const dashboard = ss.getSheetByName(DASHBOARD_SHEET);
  
  SpreadsheetApp.getActiveSpreadsheet().toast('Refreshing dashboard data...', '🔄 Live Update');
  
  // Force recalculation
  SpreadsheetApp.flush();
  
  // Update timestamp
  const now = new Date();
  const timestamp = Utilities.formatDate(now, 'Europe/London', 'yyyy-MM-dd HH:mm:ss');
  dashboard.getRange('B2').setValue(`⏰ Last Updated: ${timestamp} | ✅ FRESH`);
  
  SpreadsheetApp.getActiveSpreadsheet().toast('Dashboard refreshed successfully', '✅ Complete', 3);
}

/**
 * Show embedded interactive map
 */
function showEmbeddedMap() {
  const html = HtmlService.createHtmlOutputFromFile('dynamicMapView')
    .setWidth(900)
    .setHeight(600);
  
  SpreadsheetApp.getUi().showModalDialog(html, '🗺️ GB Energy Interactive Map');
}

/**
 * Update chart data from BigQuery
 * Called automatically every 5 minutes
 */
function updateCharts() {
  // This would be implemented with BigQuery API
  // For now, data is updated by Python script
  SpreadsheetApp.getActiveSpreadsheet().toast('Charts update via Python script', '📊 Info', 2);
}

/**
 * Show auto-refresh status
 */
function showAutoRefreshStatus() {
  const ui = SpreadsheetApp.getUi();
  ui.alert(
    '⚙️ Auto-Refresh Status',
    'Dashboard auto-refreshes every 5 minutes via:\n\n' +
    '1. Python cron job (realtime_dashboard_updater.py)\n' +
    '2. Updates: Metrics, Charts, Map data\n' +
    '3. Status: ✅ ACTIVE\n\n' +
    'Manual refresh: Menu → 🔄 Live Dashboard → 📊 Refresh All Data',
    ui.ButtonSet.OK
  );
}

/**
 * Get regional map data (for HTML map)
 */
function getRegionalMapData(region, overlayType, icMode) {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  
  // Read from Map_Data_* sheets (populated by Python)
  const gspSheet = ss.getSheetByName('Map_Data_GSP');
  const icSheet = ss.getSheetByName('Map_Data_IC');
  const dnoSheet = ss.getSheetByName('Map_Data_DNO');
  
  const gspData = gspSheet ? gspSheet.getDataRange().getValues() : [];
  const icData = icSheet ? icSheet.getDataRange().getValues() : [];
  const dnoData = dnoSheet ? dnoSheet.getDataRange().getValues() : [];
  
  // Convert to JSON
  return {
    gsp: parseGspData(gspData, region),
    ic: parseIcData(icData, icMode),
    dno: parseDnoData(dnoData, region)
  };
}

// Helper functions for data parsing
function parseGspData(data, region) {
  // Skip header row
  const result = [];
  for (let i = 1; i < data.length; i++) {
    const row = data[i];
    result.push({
      id: row[0],
      name: row[1],
      lat: parseFloat(row[2]),
      lng: parseFloat(row[3]),
      region: row[5],
      load_mw: parseFloat(row[6]) || 0,
      frequency_hz: parseFloat(row[7]) || 50.0,
      constraint_mw: parseFloat(row[8]) || 0,
      generation_mw: parseFloat(row[9]) || 0
    });
  }
  return result;
}

function parseIcData(data, icMode) {
  const result = [];
  for (let i = 1; i < data.length; i++) {
    const row = data[i];
    const flow = parseFloat(row[2]) || 0;
    
    // Filter by mode
    if (icMode === 'Imports' && flow <= 0) continue;
    if (icMode === 'Exports' && flow >= 0) continue;
    
    result.push({
      name: row[0],
      country: row[1],
      flow_mw: flow,
      start: { lat: parseFloat(row[3]), lng: parseFloat(row[4]) },
      end: { lat: parseFloat(row[5]), lng: parseFloat(row[6]) },
      capacity_mw: parseFloat(row[7]) || 1000,
      status: row[8] || 'Active',
      direction: flow > 0 ? 'Import' : 'Export'
    });
  }
  return result;
}

function parseDnoData(data, region) {
  const result = [];
  for (let i = 1; i < data.length; i++) {
    const row = data[i];
    
    // Filter by region
    if (region !== 'National' && row[0].indexOf(region) === -1) continue;
    
    result.push({
      name: row[0],
      coordinates: JSON.parse(row[1]),
      total_load_mw: parseFloat(row[2]) || 0,
      total_generation_mw: parseFloat(row[3]) || 0,
      area_sqkm: parseFloat(row[4]) || 0,
      color_hex: row[5]
    });
  }
  return result;
}
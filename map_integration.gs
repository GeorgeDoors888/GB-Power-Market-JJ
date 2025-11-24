/**
 * GB Energy Dashboard - Interactive Map with Regional Overlays
 * Created: 23 November 2025
 * Purpose: Dynamic map visualization with DNO filtering, heatmaps, and interconnector views
 */

/**
 * Create custom menu on spreadsheet open
 */
function onOpen() {
  const ui = SpreadsheetApp.getUi();
  ui.createMenu('🗺️ Map Tools')
    .addItem('🌍 Open Interactive Map', 'openDynamicMap')
    .addItem('📊 Refresh Map Data', 'refreshMapData')
    .addItem('🔧 Setup Map Sheets', 'setupMapSheets')
    .addToUi();
  
  Logger.log('Map Tools menu created');
}

/**
 * Open dynamic map in sidebar
 */
function openDynamicMap() {
  const html = HtmlService.createHtmlOutputFromFile('dynamicMapView')
    .setWidth(1300)
    .setHeight(900)
    .setTitle('GB Energy Interactive Map');
  
  SpreadsheetApp.getUi().showSidebar(html);
  Logger.log('Dynamic map opened');
}

/**
 * Setup required sheets for map data
 */
function setupMapSheets() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  
  // Create Map_Data_GSP sheet
  let gspSheet = ss.getSheetByName('Map_Data_GSP');
  if (!gspSheet) {
    gspSheet = ss.insertSheet('Map_Data_GSP');
    gspSheet.appendRow([
      'GSP_ID', 'Name', 'Latitude', 'Longitude', 'Postcode', 'DNO_Region',
      'Load_MW', 'Frequency_Hz', 'Constraint_MW', 'Generation_MW', 'Last_Updated'
    ]);
    gspSheet.getRange('A1:K1').setBackground('#1E1E1E').setFontColor('#FFFFFF').setFontWeight('bold');
  }
  
  // Create Map_Data_IC sheet
  let icSheet = ss.getSheetByName('Map_Data_IC');
  if (!icSheet) {
    icSheet = ss.insertSheet('Map_Data_IC');
    icSheet.appendRow([
      'IC_Name', 'Country', 'Flow_MW', 'Start_Lat', 'Start_Lng', 'End_Lat', 'End_Lng',
      'Status', 'Direction', 'Capacity_MW', 'Last_Updated'
    ]);
    icSheet.getRange('A1:K1').setBackground('#1E1E1E').setFontColor('#FFFFFF').setFontWeight('bold');
  }
  
  // Create Map_Data_DNO sheet
  let dnoSheet = ss.getSheetByName('Map_Data_DNO');
  if (!dnoSheet) {
    dnoSheet = ss.insertSheet('Map_Data_DNO');
    dnoSheet.appendRow([
      'DNO_Name', 'Boundary_Coordinates_JSON', 'Total_Load_MW', 'Total_Generation_MW',
      'Area_SqKm', 'Color_Hex', 'Last_Updated'
    ]);
    dnoSheet.getRange('A1:G1').setBackground('#1E1E1E').setFontColor('#FFFFFF').setFontWeight('bold');
  }
  
  SpreadsheetApp.getUi().alert('✅ Map Sheets Created', 
    'Map data sheets have been created:\n\n' +
    '• Map_Data_GSP (Grid Supply Points)\n' +
    '• Map_Data_IC (Interconnectors)\n' +
    '• Map_Data_DNO (Distribution Network Operators)\n\n' +
    'Ready to populate with data!',
    SpreadsheetApp.getUi().ButtonSet.OK);
}

/**
 * Get regional map data based on filters
 * Called from HTML frontend
 */
function getRegionalMapData(region, overlayType, icMode) {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  
  // Get GSP data
  const gspSheet = ss.getSheetByName('Map_Data_GSP');
  const gspData = gspSheet ? gspSheet.getDataRange().getValues().slice(1) : [];
  
  const gsp = gspData.map(r => ({
    id: r[0],
    name: r[1],
    lat: parseFloat(r[2]),
    lng: parseFloat(r[3]),
    postcode: r[4],
    region: r[5],
    load_mw: parseFloat(r[6]) || 0,
    frequency_hz: parseFloat(r[7]) || 50.0,
    constraint_mw: parseFloat(r[8]) || 0,
    generation_mw: parseFloat(r[9]) || 0,
    last_updated: r[10]
  })).filter(g => {
    // Filter by region if not National
    return region === 'National' || g.region === region;
  }).filter(g => {
    // Only include valid coordinates
    return g.lat && g.lng && !isNaN(g.lat) && !isNaN(g.lng);
  });
  
  // Get Interconnector data
  const icSheet = ss.getSheetByName('Map_Data_IC');
  const icData = icSheet ? icSheet.getDataRange().getValues().slice(1) : [];
  
  const ic = icData.map(r => ({
    name: r[0],
    country: r[1],
    flow_mw: parseFloat(r[2]) || 0,
    start: { lat: parseFloat(r[3]), lng: parseFloat(r[4]) },
    end: { lat: parseFloat(r[5]), lng: parseFloat(r[6]) },
    status: r[7],
    direction: r[8],
    capacity_mw: parseFloat(r[9]) || 0,
    last_updated: r[10]
  })).filter(i => {
    // Filter by interconnector mode
    if (icMode === 'Imports') return i.flow_mw > 0;
    if (icMode === 'Exports') return i.flow_mw < 0;
    if (icMode === 'Outages') return i.status === 'Outage';
    return true; // 'All'
  }).filter(i => {
    // Only include valid coordinates
    return i.start.lat && i.start.lng && i.end.lat && i.end.lng;
  });
  
  // Get DNO boundary data
  const dnoSheet = ss.getSheetByName('Map_Data_DNO');
  const dnoData = dnoSheet ? dnoSheet.getDataRange().getValues().slice(1) : [];
  
  const dno = dnoData.map(r => ({
    name: r[0],
    coordinates: tryParseJSON(r[1]),
    total_load_mw: parseFloat(r[2]) || 0,
    total_generation_mw: parseFloat(r[3]) || 0,
    area_sqkm: parseFloat(r[4]) || 0,
    color_hex: r[5] || '#29B6F6',
    last_updated: r[6]
  })).filter(d => {
    // Filter by region if not National
    return region === 'National' || d.name === region;
  }).filter(d => {
    // Only include valid coordinate arrays
    return d.coordinates && Array.isArray(d.coordinates) && d.coordinates.length > 0;
  });
  
  Logger.log(`Returning map data: ${gsp.length} GSPs, ${ic.length} ICs, ${dno.length} DNOs`);
  
  return {
    gsp: gsp,
    ic: ic,
    dno: dno,
    overlayType: overlayType,
    region: region
  };
}

/**
 * Helper function to safely parse JSON
 */
function tryParseJSON(str) {
  try {
    return JSON.parse(str);
  } catch (e) {
    Logger.log('JSON parse error: ' + e.message);
    return [];
  }
}

/**
 * Refresh map data from BigQuery
 */
function refreshMapData() {
  const ui = SpreadsheetApp.getUi();
  
  const result = ui.alert(
    '🔄 Refresh Map Data',
    'This will fetch the latest GSP, Interconnector, and DNO data from BigQuery.\n\n' +
    'This may take 30-60 seconds. Continue?',
    ui.ButtonSet.YES_NO
  );
  
  if (result === ui.Button.YES) {
    try {
      // Call Railway API to trigger refresh
      const apiUrl = 'https://jibber-jabber-production.up.railway.app/api/refresh-map-data';
      
      const options = {
        'method': 'post',
        'contentType': 'application/json',
        'muteHttpExceptions': true
      };
      
      const response = UrlFetchApp.fetch(apiUrl, options);
      const responseCode = response.getResponseCode();
      
      if (responseCode === 200) {
        ui.alert('✅ Success', 'Map data refreshed successfully!', ui.ButtonSet.OK);
      } else {
        ui.alert('⚠️ Warning', 
          'Refresh completed with status: ' + responseCode + '\n\n' +
          'You may need to run the Python refresh script manually.',
          ui.ButtonSet.OK);
      }
    } catch (error) {
      ui.alert('❌ Error', 
        'Could not refresh map data:\n' + error.message + '\n\n' +
        'Please run the Python script manually:\n' +
        'python3 refresh_map_data.py',
        ui.ButtonSet.OK);
    }
  }
}

/**
 * Get sample data for testing
 */
function populateSampleMapData() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  
  // Sample GSP data
  const gspSheet = ss.getSheetByName('Map_Data_GSP');
  if (gspSheet && gspSheet.getLastRow() <= 1) {
    const sampleGSP = [
      ['N', 'London Core', 51.5074, -0.1278, 'EC1A', 'UKPN', 20138, 50.0, 50, 15000, new Date()],
      ['B9', 'East Anglia', 52.6309, 1.2974, 'NR1', 'UKPN', 7742, 50.0, 30, 8500, new Date()],
      ['B8', 'North West', 53.4808, -2.2426, 'M1', 'ENWL', 5746, 50.0, 45, 4200, new Date()],
      ['B16', 'Humber', 53.7457, -0.3367, 'HU1', 'Northern Powergrid', 4270, 50.0, 20, 6800, new Date()],
      ['B11', 'South West', 51.4545, -2.5879, 'BS1', 'Western Power', 3592, 50.0, 15, 5500, new Date()]
    ];
    
    gspSheet.getRange(2, 1, sampleGSP.length, sampleGSP[0].length).setValues(sampleGSP);
  }
  
  // Sample IC data
  const icSheet = ss.getSheetByName('Map_Data_IC');
  if (icSheet && icSheet.getLastRow() <= 1) {
    const sampleIC = [
      ['IFA', 'France', 1509, 50.8503, -1.1, 49.8, 1.4, 'Active', 'Import', 2000, new Date()],
      ['BritNed', 'Netherlands', -833, 51.9, 1.3, 52.1, 4.3, 'Active', 'Export', 1000, new Date()],
      ['NSL', 'Norway', 1397, 58.4, -3.2, 59.9, 10.7, 'Active', 'Import', 1400, new Date()],
      ['Viking Link', 'Denmark', -1090, 53.1, 0.3, 55.5, 8.4, 'Active', 'Export', 1400, new Date()],
      ['ElecLink', 'France', 999, 51.1, 1.3, 50.9, 1.8, 'Partial', 'Import', 1000, new Date()]
    ];
    
    icSheet.getRange(2, 1, sampleIC.length, sampleIC[0].length).setValues(sampleIC);
  }
  
  SpreadsheetApp.getUi().alert('✅ Sample Data Added', 
    'Sample GSP and Interconnector data has been added for testing.',
    SpreadsheetApp.getUi().ButtonSet.OK);
}

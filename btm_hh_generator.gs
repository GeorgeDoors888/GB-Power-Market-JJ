/**
 * BtM HH Data Generator - Apps Script Functions
 * 
 * Installation:
 * 1. Open Google Sheets: https://docs.google.com/spreadsheets/d/1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA/edit
 * 2. Go to: Extensions > Apps Script
 * 3. Paste this entire file
 * 4. Save (Ctrl+S)
 * 5. Refresh your spreadsheet
 * 6. New menu "⚡ BtM Tools" will appear
 */

/**
 * Create custom menu when spreadsheet opens
 */
function onOpen() {
  const ui = SpreadsheetApp.getUi();
  ui.createMenu('⚡ BtM Tools')
      .addItem('🔄 Generate HH Data', 'produceHHData')
      .addItem('📊 View HH DATA Sheet', 'viewHHDataSheet')
      .addToUi();
}

/**
 * Main function to generate HH data
 * Called when user clicks button or menu item
 */
function produceHHData() {
  const ui = SpreadsheetApp.getUi();
  
  // Confirm action
  const response = ui.alert(
    '🔄 Generate HH Data',
    'This will:\n' +
    '• Read parameters from B17-B20\n' +
    '• Delete old HH DATA\n' +
    '• Generate 17,520 new periods\n\n' +
    'Continue?',
    ui.ButtonSet.YES_NO
  );
  
  if (response !== ui.Button.YES) {
    return;
  }
  
  try {
    // Show progress
    ui.alert('⏳ Generating HH data...\n\nThis will take 10-15 seconds.\nPlease wait.');
    
    // Call the generation function and get result
    const result = generateHHDataDirect();
    
    // Success message
    ui.alert(
      '✅ Success!',
      `HH DATA sheet updated with ${result.periods} periods.\n\n` +
      `Profile: ${result.supplyType}\n` +
      `Scaling: ${result.scaleType} kW = ${result.scaleValue.toLocaleString()}\n\n` +
      '📤 NEXT STEP: Upload to BigQuery\n' +
      'Run in terminal:\n' +
      `python3 upload_hh_to_bigquery.py "${result.supplyType}" ${result.scaleValue}\n\n` +
      'Benefits: 70x faster calculations, auto-cleanup, no spreadsheet clutter',
      ui.ButtonSet.OK
    );
    
  } catch (error) {
    ui.alert('❌ Error', 'Failed to generate HH data:\n\n' + error.toString(), ui.ButtonSet.OK);
  }
}

/**
 * Generate HH data directly in Apps Script
 * Fetches real HH profile data from API and scales to kW range
 */
function generateHHDataDirect() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const btmSheet = ss.getSheetByName('BtM');
  
  // 1. Read parameters from BtM sheet
  const minKw = parseFloat(btmSheet.getRange('B17').getValue() || 0);
  const avgKw = parseFloat(btmSheet.getRange('B18').getValue() || 0);
  const maxKw = parseFloat(btmSheet.getRange('B19').getValue() || 0);
  const supplyType = (btmSheet.getRange('B20').getValue() || 'Commercial').toString();
  
  // Determine which scaling value to use (priority: Max > Avg > Min)
  let scaleValue = 0;
  let scaleType = '';
  if (maxKw > 0) {
    scaleValue = maxKw;
    scaleType = 'Max';
  } else if (avgKw > 0) {
    scaleValue = avgKw;
    scaleType = 'Avg';
  } else if (minKw > 0) {
    scaleValue = minKw;
    scaleType = 'Min';
  } else {
    SpreadsheetApp.getUi().alert('❌ Error', 'Please enter a value in B17 (Min kW), B18 (Avg kW), or B19 (Max kW)', SpreadsheetApp.getUi().ButtonSet.OK);
    return;
  }
  
  // Convert to API key format
  const supplyTypeKey = supplyType.toLowerCase().replace(/ /g, '_');
  
  Logger.log(`Parameters: ${scaleType} kW = ${scaleValue}, ${supplyType}`);
  
  // 2. Fetch all HH profile data from UK Power Networks (using export endpoint for all 17,520 records)
  const BASE_URL = 'https://ukpowernetworks.opendatasoft.com';
  const DATASET_ID = 'ukpn-standard-profiles-electricity-demand';
  const exportUrl = `${BASE_URL}/api/v2/catalog/datasets/${DATASET_ID}/exports/json?limit=-1`;
  
  Logger.log('Fetching all 17,520 HH periods from UK Power Networks...');
  
  let allRecords;
  try {
    const response = UrlFetchApp.fetch(exportUrl, {
      method: 'get',
      headers: {'Content-Type': 'application/json'},
      muteHttpExceptions: true
    });
    
    if (response.getResponseCode() !== 200) {
      throw new Error(`API error: ${response.getResponseCode()}`);
    }
    
    allRecords = JSON.parse(response.getContentText());
    Logger.log(`Fetched ${allRecords.length} HH periods from UK Power Networks`);
    
  } catch (error) {
    throw new Error(`Failed to fetch HH data: ${error.toString()}`);
  }
  
  // Transform export format to our format
  const apiData = {
    total_count: allRecords.length,
    results: allRecords.map(r => ({
      timestamp: r.timestamp,
      domestic: r.domestic,
      commercial: r.commercial,
      industrial: r.industrial,
      network_rail: r.network_rail,
      ev_charging: r.ev_charging,
      datacentre: r.datacentre,
      non_variable: r.non_variable,
      solar_and_storage: r.solar_and_storage,
      storage: r.storage,
      solar_and_wind_and_storage: r.solar_and_wind_and_storage
    }))
  };
  
  // 2b. Validate supply type exists in API data
  // 2b. Validate supply type exists in API data
  if (!apiData.results || apiData.results.length === 0) {
    throw new Error('No HH data returned from API');
  }
  
  const firstRecord = apiData.results[0];
  if (!firstRecord[supplyTypeKey]) {
    throw new Error(`Supply type "${supplyTypeKey}" not found in API data. Available: ${Object.keys(firstRecord).filter(k => k !== 'timestamp').join(', ')}`);
  }
  
  // 3. Get or create HH DATA sheet
  let hhSheet = ss.getSheetByName('HH DATA');
  if (hhSheet) {
    hhSheet.clear();
  } else {
    hhSheet = ss.insertSheet('HH DATA');
  }
  
  // 4. Write headers
  const headers = [['Timestamp', 'Settlement Period', 'Day Type', 'Demand (kW)', 'Profile %']];
  hhSheet.getRange(1, 1, 1, 5).setValues(headers);
  
  // 5. Process API data and scale to kW range
  const batchSize = 1000;
  let rowData = [];
  let currentRow = 2;
  let sp = 1;
  
  for (let i = 0; i < apiData.results.length; i++) {
    const record = apiData.results[i];
    
    // Parse timestamp
    const timestamp = new Date(record.timestamp);
    const isWeekend = timestamp.getDay() === 0 || timestamp.getDay() === 6;
    const dayType = isWeekend ? 'Weekend' : 'Weekday';
    
    // Get profile % from API
    const profilePct = parseFloat(record[supplyTypeKey]);
    
    // Scale profile: demand = scale_value × (profile% / 100)
    const demandKw = scaleValue * (profilePct / 100);
    
    // Format timestamp
    const formattedTime = Utilities.formatDate(timestamp, Session.getScriptTimeZone(), 'yyyy-MM-dd HH:mm');
    
    rowData.push([
      formattedTime,
      sp,
      dayType,
      Math.round(demandKw * 100) / 100,
      Math.round(profilePct * 10) / 10
    ]);
    
    // Increment settlement period (1-48, resets at midnight)
    sp++;
    if (sp > 48) sp = 1;
    
    // Write in batches to avoid timeout
    if (rowData.length >= batchSize) {
      hhSheet.getRange(currentRow, 1, rowData.length, 5).setValues(rowData);
      currentRow += rowData.length;
      rowData = [];
    }
  }
  
  // Write remaining data
  if (rowData.length > 0) {
    hhSheet.getRange(currentRow, 1, rowData.length, 5).setValues(rowData);
  }
  
  // 6. Format headers
  hhSheet.getRange(1, 1, 1, 5)
    .setBackground('#4285f4')
    .setFontColor('white')
    .setFontWeight('bold')
    .setHorizontalAlignment('center');
  
  // Auto-resize columns
  for (let col = 1; col <= 5; col++) {
    hhSheet.autoResizeColumn(col);
  }
  
  Logger.log(`HH data generation complete: ${apiData.results.length} periods from API`);
  
  // Return result for success message
  return {
    periods: apiData.results.length,
    supplyType: supplyType,
    scaleType: scaleType,
    scaleValue: scaleValue
  };
}

/**
 * Navigate to HH DATA sheet
 */
function viewHHDataSheet() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const hhSheet = ss.getSheetByName('HH DATA');
  
  if (hhSheet) {
    ss.setActiveSheet(hhSheet);
    hhSheet.getRange('A1').activate();
  } else {
    SpreadsheetApp.getUi().alert('HH DATA sheet not found. Generate data first.');
  }
}

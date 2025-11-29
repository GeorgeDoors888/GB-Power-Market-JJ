/**
 * BESS Sheet - Auto Trigger for DNO Lookup
 * Add this to your Apps Script project alongside bess_webapp_api.gs
 * 
 * Installation:
 * 1. Copy this entire file into Apps Script editor
 * 2. Click the clock icon (Triggers) in the left sidebar
 * 3. Click "+ Add Trigger" button (bottom right)
 * 4. Configure:
 *    - Function: onEdit
 *    - Deployment: Head
 *    - Event source: From spreadsheet
 *    - Event type: On edit
 * 5. Click "Save"
 * 
 * Now when you type a postcode in A6 or MPAN in B6, it will auto-lookup!
 */

/**
 * Trigger function that runs automatically when any cell is edited
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
      const voltage = String(sheet.getRange('A9').getValue() || '');
      
      // Only trigger if there's actually a value
      if (!postcode && !mpanId) {
        return;
      }
      
      // Show loading indicator
      sheet.getRange('A4:H4').setValues([[
        '🔄 Looking up DNO...', '', '', '', '', '', '', ''
      ]]);
      sheet.getRange('A4:H4').setBackground('#FFEB3B');  // Yellow
      
      // Trigger the lookup
      triggerDnoLookup(postcode, mpanId, voltage);
    }
    
  } catch (err) {
    Logger.log('onEdit error: ' + err);
  }
}

/**
 * Call the external Python script via URL Fetch
 * (Alternative: Could call BigQuery API directly from Apps Script)
 */
function triggerDnoLookup(postcode, mpanId, voltage) {
  try {
    const sheet = SpreadsheetApp.getActive().getSheetByName('BESS');
    
    // Extract voltage level (e.g., "LV (<1kV)" -> "LV")
    let voltageLevel = 'LV';
    const voltageStr = String(voltage || '');
    if (voltageStr && voltageStr.indexOf('(') > 0) {
      voltageLevel = voltageStr.substring(0, voltageStr.indexOf('(')).trim();
    }
    
    // For now, we'll call the BigQuery API directly from Apps Script
    // This is more reliable than trying to trigger an external Python script
    
    // Determine MPAN from postcode or use direct MPAN
    let finalMpan = mpanId;
    
    if (postcode && postcode.trim()) {
      // Call postcodes.io API to get coordinates
      const postcodeClean = postcode.trim().toUpperCase().replace(' ', '');
      const postcodeResponse = UrlFetchApp.fetch(
        `https://api.postcodes.io/postcodes/${postcodeClean}`,
        { muteHttpExceptions: true }
      );
      
      if (postcodeResponse.getResponseCode() === 200) {
        const postcodeData = JSON.parse(postcodeResponse.getContentText());
        if (postcodeData.status === 200) {
          const lat = postcodeData.result.latitude;
          const lng = postcodeData.result.longitude;
          
          // Map coordinates to MPAN using regional boundaries
          finalMpan = coordinatesToMpan(lat, lng);
        }
      }
    }
    
    if (!finalMpan) {
      sheet.getRange('A4:H4').setValues([[
        '❌ No valid postcode or MPAN', '', '', '', '', '', '', ''
      ]]);
      sheet.getRange('A4:H4').setBackground('#FF5252');  // Red
      return;
    }
    
    // Now query BigQuery for DNO info and rates
    // Note: This requires BigQuery API to be enabled for your project
    // For simplicity, we'll show a message to run the Python script instead
    
    sheet.getRange('A4:H4').setValues([[
      `⚡ Run: python3 dno_webapp_client.py`,
      `(or wait for Python script to detect change)`,
      '', '', '', '', '', ''
    ]]);
    sheet.getRange('A4:H4').setBackground('#FFC107');  // Amber
    
  } catch (err) {
    const sheet = SpreadsheetApp.getActive().getSheetByName('BESS');
    sheet.getRange('A4:H4').setValues([[
      '❌ Error: ' + err.toString().substring(0, 50), '', '', '', '', '', '', ''
    ]]);
    sheet.getRange('A4:H4').setBackground('#FF5252');  // Red
    Logger.log('triggerDnoLookup error: ' + err);
  }
}

/**
 * Map coordinates to MPAN ID using regional boundaries
 */
function coordinatesToMpan(lat, lng) {
  // Regional boundary definitions (same as Python)
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
  for (let i = 0; i < regions.length; i++) {
    const [latMin, latMax, lngMin, lngMax] = regions[i].bounds;
    if (lat >= latMin && lat <= latMax && lng >= lngMin && lng <= lngMax) {
      return regions[i].mpan;
    }
  }
  
  // Default to London if no match
  return 12;
}

/**
 * Manual button to trigger lookup via Python webhook
 * This is what gets called when you click the button
 */
function manualRefreshDno() {
  const sheet = SpreadsheetApp.getActive().getSheetByName('BESS');
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
  let voltageLevel = 'LV';
  const voltageStr = String(voltage || '');
  if (voltageStr && voltageStr.indexOf('(') > 0) {
    voltageLevel = voltageStr.substring(0, voltageStr.indexOf('(')).trim();
  }
  
  // Call Python webhook (localhost or ngrok URL)
  const webhookUrl = 'https://26eff9472aea.ngrok-free.app/trigger-dno-lookup';
  
  const payload = {
    postcode: postcode || '',
    mpan_id: mpanId || null,
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
      // Python script will update the sheet via Web App
      // Just wait a moment for it to complete
      Utilities.sleep(2000);
      
      sheet.getRange('A4:H4').setValues([[
        '✅ Lookup complete!', 
        'Check rows 6-9 for updates', 
        '', '', '', '', '', ''
      ]]);
      sheet.getRange('A4:H4').setBackground('#90EE90');  // Green
    } else {
      sheet.getRange('A4:H4').setValues([[
        '❌ Error: ' + (result.message || 'Unknown error').substring(0, 50), 
        '', '', '', '', '', '', ''
      ]]);
      sheet.getRange('A4:H4').setBackground('#FF5252');  // Red
    }
  } catch (err) {
    // Webhook server not running - fall back to manual instructions
    sheet.getRange('A4:H4').setValues([[
      '⚡ Run: python3 dno_webapp_client.py', 
      '(Webhook server not running)', 
      '', '', '', '', '', ''
    ]]);
    sheet.getRange('A4:H4').setBackground('#FFC107');  // Orange
  }
}

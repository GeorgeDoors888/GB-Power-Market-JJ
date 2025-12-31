/**
 * BtM Calculate 2 Button - Apps Script Functions
 * 
 * Triggers comprehensive BtM calculations:
 * - DNO & DUoS rate lookup
 * - kWh calculation by time band (Red/Amber/Green)
 * - Transmission charges (TNUoS, BSUoS)
 * - Environmental levies (CCL, RO, FiT)
 * - Total unit rate (£/MWh)
 * 
 * Installation:
 * 1. Open: https://docs.google.com/spreadsheets/d/1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA/edit
 * 2. Extensions > Apps Script
 * 3. Paste this file
 * 4. Save (Ctrl+S)
 * 5. Assign button to Calculate2() function
 */

/**
 * Create custom menu when spreadsheet opens
 */
function onOpen() {
  const ui = SpreadsheetApp.getUi();
  ui.createMenu('⚡ BtM Tools')
      .addItem('🔄 Calculate All', 'Calculate2')
      .addItem('🔄 Generate HH Data', 'produceHHData')
      .addItem('📊 View Results', 'viewBtmSheet')
      .addSeparator()
      .addItem('ℹ️ About', 'showAbout')
      .addToUi();
}

/**
 * Main calculation function - called by "Calculate 2" button
 * Displays instructions for running Python script
 */
function Calculate2() {
  const ui = SpreadsheetApp.getUi();
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const btmSheet = ss.getSheetByName('BtM');
  
  if (!btmSheet) {
    ui.alert('❌ Error', 'BtM sheet not found', ui.ButtonSet.OK);
    return;
  }
  
  // Read input cells
  const postcode = btmSheet.getRange('H6').getValue() || '(empty)';
  const mpanSupplement = btmSheet.getRange('I6').getValue() || '(empty)';
  const mpanCore = btmSheet.getRange('J6').getValue() || '(empty)';
  const voltage = btmSheet.getRange('B9').getValue() || 'LV';
  
  // Show calculation dialog
  const message = `
📊 BtM Comprehensive Calculation

This will calculate:
✅ DNO & DUoS rates (Red/Amber/Green)
✅ kWh totals from HH DATA
✅ Transmission charges (TNUoS, BSUoS)
✅ Environmental levies (CCL, RO, FiT)
✅ Total unit rate (£/MWh)

📍 Input Data:
   Postcode (H6): ${postcode}
   MPAN Supplement (I6): ${mpanSupplement}
   MPAN Core (J6): ${mpanCore}
   Voltage (B9): ${voltage}

🖥️  Run this command in terminal:

cd /home/george/GB-Power-Market-JJ
python3 btm_dno_lookup.py

⏱️  Expected time: 10-15 seconds
📊 Results will appear in BtM sheet

Continue?
`;
  
  const response = ui.alert('⚡ Calculate All', message, ui.ButtonSet.YES_NO);
  
  if (response === ui.Button.YES) {
    ui.alert(
      '✅ Ready to Calculate',
      'Run the command in your terminal:\n\n' +
      'python3 btm_dno_lookup.py\n\n' +
      'Results will update automatically in the BtM sheet.',
      ui.ButtonSet.OK
    );
  }
}

/**
 * Generate HH Data - redirects to btm_hh_generator.gs function
 */
function produceHHData() {
  const ui = SpreadsheetApp.getUi();
  
  // Check if btm_hh_generator.gs is loaded
  if (typeof generateHHDataDirect === 'function') {
    // Call the function from btm_hh_generator.gs
    const ui = SpreadsheetApp.getUi();
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
      ui.alert('⏳ Generating HH data...\n\nThis will take 10-15 seconds.\nPlease wait.');
      const result = generateHHDataDirect();
      ui.alert(
        '✅ Success!',
        `HH DATA sheet updated with ${result.periods} periods.\n\n` +
        `Profile: ${result.supplyType}\n` +
        `Scaling: ${result.scaleType} kW = ${result.scaleValue.toLocaleString()}\n\n` +
        'Go to "HH DATA" sheet to view results.',
        ui.ButtonSet.OK
      );
    } catch (error) {
      ui.alert('❌ Error', 'Failed to generate HH data:\n\n' + error.toString(), ui.ButtonSet.OK);
    }
  } else {
    ui.alert(
      '⚠️ Function Not Found',
      'The produceHHData function requires btm_hh_generator.gs to be installed.\n\n' +
      'Please add btm_hh_generator.gs to Apps Script.',
      ui.ButtonSet.OK
    );
  }
}

/**
 * Navigate to BtM sheet and highlight results
 */
function viewBtmSheet() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const btmSheet = ss.getSheetByName('BtM');
  
  if (btmSheet) {
    ss.setActiveSheet(btmSheet);
    btmSheet.getRange('C6').activate();  // DNO results
  } else {
    SpreadsheetApp.getUi().alert('BtM sheet not found.');
  }
}

/**
 * Show about dialog
 */
function showAbout() {
  const ui = SpreadsheetApp.getUi();
  ui.alert(
    'ℹ️ BtM Tools',
    'Behind the Meter Calculator\n\n' +
    'Features:\n' +
    '• DNO & DUoS rate lookup\n' +
    '• kWh calculation by time band\n' +
    '• Transmission & levy calculations\n' +
    '• HH data generation\n\n' +
    'Version: 1.2\n' +
    'Updated: December 30, 2025',
    ui.ButtonSet.OK
  );
}

/**
 * Test function - verify BtM sheet access
 */
function testBtmAccess() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const btmSheet = ss.getSheetByName('BtM');
  
  if (btmSheet) {
    Logger.log('✅ BtM sheet found');
    Logger.log('Sheet ID: ' + ss.getId());
    Logger.log('Sheet name: ' + btmSheet.getName());
    Logger.log('Last row: ' + btmSheet.getLastRow());
    return true;
  } else {
    Logger.log('❌ BtM sheet not found');
    return false;
  }
}

/**
 * BESS HH Data Generator - Apps Script
 * Triggers Python script to generate synthetic HH data
 */

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
    
    Logger.log(`Generating HH Data: Min=${minKw}, Avg=${avgKw}, Max=${maxKw}`);
    
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
          `✅ HH Data generated!\n\n${result.periods} periods created\nDate range: ${result.date_range}`,
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
        `Parameters: Min=${minKw}kW, Avg=${avgKw}kW, Max=${maxKw}kW`,
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
 * Add menu item to BESS sheet
 */
function onOpen() {
  const ui = SpreadsheetApp.getUi();
  ui.createMenu('🔋 BESS Tools')
    .addItem('📊 Generate HH Data', 'generateHHDataDirect')
    .addSeparator()
    .addItem('🔄 Refresh DNO Data', 'refreshDnoData')
    .addSeparator()
    .addItem('💰 Calculate PPA Analysis', 'calculatePPAAnalysis')
    .addToUi();
}

/**
 * Refresh DNO data (existing function)
 */
function refreshDnoData() {
  SpreadsheetApp.getUi().alert(
    'DNO Refresh',
    'Run: python3 dno_lookup_python.py\n\nOr use webhook if running',
    SpreadsheetApp.getUi().ButtonSet.OK
  );
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
 * Validate HH parameters before generation
 */
function validateHHParameters() {
  const sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName('BESS');
  const minKw = sheet.getRange('B17').getValue();
  const avgKw = sheet.getRange('B18').getValue();
  const maxKw = sheet.getRange('B19').getValue();
  
  if (!minKw || !avgKw || !maxKw) {
    return { valid: false, message: 'Please enter Min, Avg, and Max kW values in B17:B19' };
  }
  
  if (minKw > avgKw || avgKw > maxKw) {
    return { valid: false, message: 'Values must be: Min ≤ Avg ≤ Max' };
  }
  
  if (minKw < 0 || maxKw > 100000) {
    return { valid: false, message: 'Values must be between 0 and 100,000 kW' };
  }
  
  return { valid: true };
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
    
    let message = `✅ HH Data sheet exists\n\n`;
    message += `Rows: ${lastRow - 1} data rows\n`;
    message += `Expected: 17,520 rows (365 days × 48 periods)\n\n`;
    message += `Columns: ${header.join(', ')}`;
    
    if (lastRow > 1) {
      const firstData = hhSheet.getRange(2, 1, 1, 2).getValues()[0];
      const lastData = hhSheet.getRange(lastRow, 1, 1, 2).getValues()[0];
      message += `\n\nFirst: ${firstData[0]} - ${firstData[1]} kW`;
      message += `\nLast: ${lastData[0]} - ${lastData[1]} kW`;
    }
    
    SpreadsheetApp.getUi().alert('HH Data Status', message, SpreadsheetApp.getUi().ButtonSet.OK);
    
  } catch (error) {
    SpreadsheetApp.getUi().alert('Error', 'Failed to check HH Data: ' + error.message, SpreadsheetApp.getUi().ButtonSet.OK);
  }
}

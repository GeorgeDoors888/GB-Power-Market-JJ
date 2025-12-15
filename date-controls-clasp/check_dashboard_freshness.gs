/**
 * check_dashboard_freshness.gs
 * Reads key cells from GB Live/BTM Dashboard to verify data freshness
 * UPDATED: Correct cell locations based on actual sheet structure
 */

function checkDashboardFreshness() {
  const ss = SpreadsheetApp.openById('1MSl8fJ0to6Y08enXA2oysd8wvNUVm3AtfJ1bVqRH8_I');
  
  // Find the correct sheet - try common names
  let sheet = ss.getSheetByName('GB Live');
  if (!sheet) sheet = ss.getSheetByName('Dashboard');
  if (!sheet) sheet = ss.getSheetByName('GB LIVE');
  if (!sheet) sheet = ss.getSheets()[0]; // Fallback to first sheet
  
  const sheetName = sheet.getName();
  Logger.log('Reading from sheet: ' + sheetName);
  
  // Read key cells - scanning for actual data
  const data = {
    sheetName: sheetName,
    
    // Try multiple locations for title/header
    a1: sheet.getRange('A1').getValue(),
    a2: sheet.getRange('A2').getValue(),
    b1: sheet.getRange('B1').getValue(),
    b2: sheet.getRange('B2').getValue(),
    
    // Scan rows 5-10 for KPI data
    row5: sheet.getRange('A5:H5').getValues()[0],
    row6: sheet.getRange('A6:H6').getValues()[0],
    row7: sheet.getRange('A7:H7').getValues()[0],
    row8: sheet.getRange('A8:H8').getValues()[0],
    
    // Scan for generation mix (rows 10-15)
    row10: sheet.getRange('A10:F10').getValues()[0],
    row11: sheet.getRange('A11:F11').getValues()[0],
    row12: sheet.getRange('A12:F12').getValues()[0]
  };
  
  // Get current timestamp
  const now = new Date();
  const checkTime = Utilities.formatDate(now, 'Europe/London', 'yyyy-MM-dd HH:mm:ss');
  
  // Log all data
  Logger.log('=== DASHBOARD FRESHNESS CHECK ===');
  Logger.log('Check Time: ' + checkTime);
  Logger.log('Sheet: ' + sheetName);
  Logger.log('');
  Logger.log('HEADER CELLS:');
  Logger.log('  A1: ' + data.a1);
  Logger.log('  A2: ' + data.a2);
  Logger.log('  B1: ' + data.b1);
  Logger.log('  B2: ' + data.b2);
  Logger.log('');
  Logger.log('ROW 5: ' + data.row5.join(' | '));
  Logger.log('ROW 6: ' + data.row6.join(' | '));
  Logger.log('ROW 7: ' + data.row7.join(' | '));
  Logger.log('ROW 8: ' + data.row8.join(' | '));
  Logger.log('');
  Logger.log('GENERATION DATA:');
  Logger.log('ROW 10: ' + data.row10.join(' | '));
  Logger.log('ROW 11: ' + data.row11.join(' | '));
  Logger.log('ROW 12: ' + data.row12.join(' | '));
  
  // Search for "Updated:" timestamp
  let lastUpdateTime = 'Unknown';
  let freshnessMinutes = 'N/A';
  
  // Check A2 first
  if (data.a2 && data.a2.toString().includes('Updated:')) {
    const timestampMatch = data.a2.toString().match(/\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}/);
    if (timestampMatch) {
      lastUpdateTime = timestampMatch[0];
      const lastUpdate = new Date(lastUpdateTime);
      freshnessMinutes = Math.round((now - lastUpdate) / (1000 * 60));
    }
  }
  
  // Extract metrics from row data
  let price = 'N/A', demand = 'N/A', frequency = 'N/A', wind = 'N/A';
  
  // Try to find numeric values in rows 6-8
  for (let val of data.row6.concat(data.row7).concat(data.row8)) {
    const str = String(val);
    // Price pattern: £XX.XX/MWh or £XX.XX
    if (str.includes('£') && str.includes('/MWh')) {
      price = str;
    }
    // GW pattern: XX.XX GW
    if (str.includes('GW') && !str.includes('Wind')) {
      if (demand === 'N/A') demand = str;
    }
    // Hz pattern: XX.X Hz
    if (str.includes('Hz')) {
      frequency = str;
    }
  }
  
  // Wind from generation mix (row 10 or 11)
  if (data.row10[0] && data.row10[0].toString().includes('Wind')) {
    wind = data.row10[1] + ' GW (' + data.row10[2] + ')';
  } else if (data.row11[0] && data.row11[0].toString().includes('Wind')) {
    wind = data.row11[1] + ' GW (' + data.row11[2] + ')';
  }
  
  Logger.log('');
  Logger.log('FRESHNESS ANALYSIS:');
  Logger.log('  Last Update: ' + lastUpdateTime);
  Logger.log('  Age: ' + freshnessMinutes + ' minutes');
  Logger.log('  Status: ' + (freshnessMinutes < 10 ? '✅ FRESH' : freshnessMinutes < 30 ? '⚠️ AGING' : '❌ STALE'));
  Logger.log('');
  
  // Create user-friendly alert
  const alertMsg = 
    '📊 DASHBOARD FRESHNESS CHECK\n' +
    '━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n' +
    '📄 Sheet: ' + sheetName + '\n' +
    '🕐 Check Time: ' + checkTime + '\n' +
    '📅 Last Updated: ' + lastUpdateTime + '\n' +
    '⏱️ Age: ' + freshnessMinutes + ' minutes\n\n' +
    '⚡ KEY METRICS:\n' +
    '  • Price: ' + price + '\n' +
    '  • Demand: ' + demand + '\n' +
    '  • Frequency: ' + frequency + '\n' +
    '  • Wind: ' + wind + '\n\n' +
    '📊 STATUS: ' + (freshnessMinutes < 10 ? '✅ FRESH' : freshnessMinutes < 30 ? '⚠️ AGING' : '❌ STALE');
  
  SpreadsheetApp.getUi().alert(alertMsg);
  
  return data;
}

/**
 * Simpler version - just show what's in each cell
 */
function debugCellLocations() {
  const ss = SpreadsheetApp.openById('1MSl8fJ0to6Y08enXA2oysd8wvNUVm3AtfJ1bVqRH8_I');
  let sheet = ss.getSheetByName('GB Live');
  if (!sheet) sheet = ss.getSheets()[0];
  
  let output = '🔍 CELL LOCATION DEBUG\n';
  output += '━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n';
  
  // Check common cells
  const cells = ['A1', 'A2', 'A6', 'B6', 'C6', 'D6', 'E6', 'F6', 'B7', 'B10', 'C10', 'B11', 'C11'];
  cells.forEach(cell => {
    const value = sheet.getRange(cell).getValue();
    output += cell + ': ' + (value || '(empty)') + '\n';
  });
  
  Logger.log(output);
  SpreadsheetApp.getUi().alert(output);
}

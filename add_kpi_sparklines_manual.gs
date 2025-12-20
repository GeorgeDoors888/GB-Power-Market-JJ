/**
 * KPI Sparkline Installer for Live Dashboard v2
 *
 * THIS SCRIPT ADDS SPARKLINES TO ROW 4 THAT REFERENCE Data_Hidden SHEET
 *
 * INSTALLATION:
 * 1. Open Live Dashboard v2 spreadsheet
 * 2. Extensions → Apps Script
 * 3. Paste this entire file
 * 4. Save
 * 5. Run addKPISparklines() function
 * 6. Refresh to see sparklines
 *
 * Spreadsheet: 1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA
 */

function addKPISparklines() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const sheet = ss.getSheetByName('Live Dashboard v2');
  const dataHidden = ss.getSheetByName('Data_Hidden');

  if (!sheet) {
    throw new Error("'Live Dashboard v2' sheet not found!");
  }
  if (!dataHidden) {
    throw new Error("'Data_Hidden' sheet not found! Run Python script first.");
  }

  Logger.log('✅ Found sheets');

  // KPI Sparkline configurations
  // Row 4, columns B, D, F, G
  const kpiConfigs = [
    { cell: 'B4', dataRow: 22, label: '📉 Wholesale Price', color: '#e74c3c', chartType: 'column' },
    { cell: 'D4', dataRow: 23, label: '💓 Grid Frequency', color: '#2ecc71', chartType: 'line' },
    { cell: 'F4', dataRow: 24, label: '🏭 Total Generation', color: '#f39c12', chartType: 'column' },
    { cell: 'G4', dataRow: 25, label: '🌬️ Wind Output', color: '#4ECDC4', chartType: 'column' }
  ];

  // Add each sparkline
  kpiConfigs.forEach(config => {
    const formula = `=SPARKLINE(Data_Hidden!$B$${config.dataRow}:$AW$${config.dataRow}, ` +
                   `{"charttype","${config.chartType}";"color","${config.color}"})`;

    sheet.getRange(config.cell).setFormula(formula);
    Logger.log(`✅ ${config.cell}: ${config.label} sparkline added`);
  });

  Logger.log('✅ ALL 4 KPI SPARKLINES ADDED!');
  SpreadsheetApp.getUi().alert('✅ Success!\\n\\n4 KPI sparklines added to row 4.\\n\\nColumns: B, D, F, G');
}

/**
 * Optional: Add to custom menu for easy access
 */
function onOpen() {
  SpreadsheetApp.getUi()
    .createMenu('🔧 Dashboard Tools')
    .addItem('Add KPI Sparklines', 'addKPISparklines')
    .addToUi();
}

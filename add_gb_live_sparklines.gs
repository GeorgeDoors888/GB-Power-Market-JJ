/**
 * GB Live Dashboard - Sparkline Formula Writer
 * Adds SPARKLINE formulas to rows 7-8 that display 48-period generation trends
 */

function addSparklinesToGBLive() {
  const ss = SpreadsheetApp.openById('1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA');  // Live Dashboard v2 - CORRECT!
  const gbLive = ss.getSheetByName('Live Dashboard v2');
  
  if (!gbLive) {
    Logger.log('ERROR: GB Live sheet not found');
    return;
  }
  
  Logger.log('Adding sparklines to GB Live rows 7-8...');
  
  // Row 7: Price and Generation sparklines
  // Assuming KPIs are in row 6, sparklines in row 7 should show trends
  
  // Column A: VLP Revenue trend (48 periods)
  // We'll create formulas that reference Data_Hidden sheet rows for each metric
  
  // Sparkline configurations for different metrics
  const sparklines = [
    // Row 7 sparklines (showing intraday trends)
    { cell: 'A8', dataRange: 'Data_Hidden!A1:AV1', color: '#3498db', label: 'Wind 24h' },
    { cell: 'B8', dataRange: 'Data_Hidden!A2:AV2', color: '#e74c3c', label: 'CCGT 24h' },
    { cell: 'C8', dataRange: 'Data_Hidden!A3:AV3', color: '#f39c12', label: 'Nuclear 24h' },
    { cell: 'D8', dataRange: 'Data_Hidden!A4:AV4', color: '#2ecc71', label: 'Biomass 24h' },
    { cell: 'E8', dataRange: 'Data_Hidden!A5:AV5', color: '#9b59b6', label: 'Hydro 24h' },
    { cell: 'F8', dataRange: 'Data_Hidden!A6:AV6', color: '#1abc9c', label: 'Other 24h' },
  ];
  
  // Write sparkline formulas
  sparklines.forEach(config => {
    const formula = `=SPARKLINE(${config.dataRange}, {"charttype","line";"linewidth",2;"color","${config.color}";"ymin",0})`;
    gbLive.getRange(config.cell).setFormula(formula);
    Logger.log(`✅ Added ${config.label} sparkline to ${config.cell}`);
  });
  
  // Format row 8 to make sparklines visible
  gbLive.setRowHeight(8, 50); // Taller row for sparklines
  
  Logger.log('✅ All sparklines added successfully!');
  Logger.log('Open dashboard: https://docs.google.com/spreadsheets/d/1MSl8fJ0to6Y08enXA2oysd8wvNUVm3AtfJ1bVqRH8_I/');
}

/**
 * Alternative: Add sparklines as mini charts in generation mix section
 */
function addGenerationSparklines() {
  const ss = SpreadsheetApp.openById('1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA');  // Live Dashboard v2 - CORRECT!
  const gbLive = ss.getSheetByName('Live Dashboard v2');
  
  if (!gbLive) {
    Logger.log('ERROR: GB Live sheet not found');
    return;
  }
  
  Logger.log('Adding generation mix sparklines (rows 13-22, column D)...');
  
  // Sparklines for each fuel type showing 48-period trend
  const fuelSparklines = [
    { row: 13, dataRow: 1, color: '#4ECDC4', fuel: 'Wind' },      // Wind = Data_Hidden row 1
    { row: 14, dataRow: 3, color: '#FFA07A', fuel: 'Nuclear' },   // Nuclear = Data_Hidden row 3
    { row: 15, dataRow: 2, color: '#FF6B6B', fuel: 'CCGT' },      // CCGT = Data_Hidden row 2
    { row: 16, dataRow: 4, color: '#52B788', fuel: 'Biomass' },   // Biomass = Data_Hidden row 4
    { row: 17, dataRow: 5, color: '#F7DC6F', fuel: 'Hydro' },     // NPSHYD = Data_Hidden row 5
    { row: 18, dataRow: 6, color: '#45B7D1', fuel: 'Other' },     // Other = Data_Hidden row 6
    { row: 19, dataRow: 7, color: '#E76F51', fuel: 'OCGT' },      // OCGT = Data_Hidden row 7
    { row: 20, dataRow: 8, color: '#264653', fuel: 'Coal' },      // Coal = Data_Hidden row 8
    { row: 21, dataRow: 9, color: '#85C1E9', fuel: 'Oil' },       // Oil = Data_Hidden row 9
    { row: 22, dataRow: 10, color: '#BB8FCE', fuel: 'PS' },       // PS = Data_Hidden row 10
  ];
  
  fuelSparklines.forEach(config => {
    const formula = `=SPARKLINE(Data_Hidden!A${config.dataRow}:AV${config.dataRow}, {"charttype","line";"linewidth",2;"color","${config.color}";"ymin",0})`;
    gbLive.getRange(`D${config.row}`).setFormula(formula);
    Logger.log(`✅ Added ${config.fuel} sparkline to row ${config.row}`);
  });
  
  // Merge D-E for each row to give sparklines more space
  for (let i = 0; i < fuelSparklines.length; i++) {
    const row = fuelSparklines[i].row;
    gbLive.getRange(`D${row}:E${row}`).merge();
  }
  
  Logger.log('✅ All generation sparklines added!');
}

/**
 * Menu function to run from Google Sheets
 */
function onOpen() {
  const ui = SpreadsheetApp.getUi();
  ui.createMenu('GB Live Update')
    .addItem('Add Row 7-8 Sparklines', 'addSparklinesToGBLive')
    .addItem('Add Generation Sparklines (Column D)', 'addGenerationSparklines')
    .addToUi();
}

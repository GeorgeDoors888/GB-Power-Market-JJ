/**
 * KPI Sparklines - Auto-installer for Live Dashboard v2
 *
 * Adds 4 sparklines to row 4 that visualize KPI timeseries from Data_Hidden sheet
 * This runs as part of the main dashboard update to ensure sparklines persist
 */

/**
 * Create custom menu when spreadsheet opens
 */
function onOpen() {
  const ui = SpreadsheetApp.getUi();

  ui.createMenu('GB Live Dashboard')
    .addItem('Add KPI Sparklines', 'addKPISparklinesManual')
    .addSeparator()
    .addItem('Enable Auto-Maintenance', 'installSparklineMaintenance')
    .addToUi();
}

/**
 * Main function to add/update KPI sparklines
 * Called from main dashboard update or manually via menu
 */
function updateKPISparklines() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const sheet = ss.getSheetByName('Live Dashboard v2');
  const dataHidden = ss.getSheetByName('Data_Hidden');

  if (!sheet) {
    Logger.log('⚠️  Live Dashboard v2 sheet not found');
    return false;
  }

  if (!dataHidden) {
    Logger.log('⚠️  Data_Hidden sheet not found (Python creates this)');
    return false;
  }

  // Check if Python is managing the data
  const isPythonManaged = sheet.getRange('AA1').getValue();
  if (isPythonManaged !== 'PYTHON_MANAGED') {
    Logger.log('⚠️  Sheet not marked as PYTHON_MANAGED, skipping sparklines');
    return false;
  }

  Logger.log('📊 Adding KPI sparklines to row 7 (merged 7-8)...');

  // KPI Sparkline configurations - Row 7 (merged 7-8) for visual sparklines
  // Data_Hidden rows: 22=Wholesale, 23=Frequency, 24=Total Gen, 25=Wind, 26=Demand
  const kpiConfigs = [
    { cell: 'C7', dataRow: 22, label: 'Wholesale Price', color: '#e74c3c', chartType: 'column', ymin: null, ymax: null },
    { cell: 'E7', dataRow: 23, label: 'Grid Frequency', color: '#2ecc71', chartType: 'line', ymin: 49.8, ymax: 50.2 },
    { cell: 'G7', dataRow: 24, label: 'Total Generation', color: '#f39c12', chartType: 'column', ymin: 20, ymax: 45 },
    { cell: 'I7', dataRow: 25, label: 'Wind Output', color: '#4ECDC4', chartType: 'column', ymin: 5, ymax: 20 }
  ];

  // Add each sparkline (48 periods from Data_Hidden columns B-AW)
  kpiConfigs.forEach(config => {
    let options = `{"charttype","${config.chartType}";"color","${config.color}"`;
    
    // Add ymin/ymax if specified (fixes flat appearance for generation/wind)
    if (config.ymin !== null && config.ymax !== null) {
      options += `;"ymin",${config.ymin};"ymax",${config.ymax}`;
    }
    
    options += `}`;
    
    const formula = `=SPARKLINE(Data_Hidden!$B$${config.dataRow}:$AW$${config.dataRow}, ${options})`;

    sheet.getRange(config.cell).setFormula(formula);
    Logger.log(`   ✅ ${config.cell}: ${config.label}`);
  });

  Logger.log('✅ KPI sparklines updated successfully');
  return true;
}

/**
 * Manual trigger function - can be called from menu
 */
function addKPISparklinesManual() {
  const success = updateKPISparklines();

  if (success) {
    SpreadsheetApp.getUi().alert(
      '✅ Success!\n\n' +
      '4 KPI sparklines added to row 7 (merged 7-8):\n' +
      '• C7: Wholesale Price (column chart)\n' +
      '• E7: Grid Frequency (line chart)\n' +
      '• G7: Total Generation (column chart)\n' +
      '• I7: Wind Output (column chart)\n\n' +
      'These will update automatically when Python refreshes the dashboard.'
    );
  } else {
    SpreadsheetApp.getUi().alert(
      '⚠️ Could not add sparklines\n\n' +
      'Make sure:\n' +
      '1. Live Dashboard v2 sheet exists\n' +
      '2. Data_Hidden sheet exists (created by Python)\n' +
      '3. Python has run at least once to populate data'
    );
  }
}

/**
 * Time-driven trigger to re-add sparklines every 5 minutes
 * This ensures they persist even if accidentally cleared
 */
function maintainKPISparklines() {
  // Only run if on Live Dashboard v2 sheet
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const sheet = ss.getSheetByName('Live Dashboard v2');

  if (!sheet) return;

  // Check if sparklines exist in row 7
  const c7 = sheet.getRange('C7').getFormula();

  // If sparklines missing, re-add them
  if (!c7 || !c7.includes('SPARKLINE')) {
    Logger.log('🔧 Sparklines missing, re-adding...');
    updateKPISparklines();
  }
}

/**
 * Install time-driven trigger (run this once to set up auto-maintenance)
 */
function installSparklineMaintenance() {
  // Delete existing triggers first
  const triggers = ScriptApp.getProjectTriggers();
  triggers.forEach(trigger => {
    if (trigger.getHandlerFunction() === 'maintainKPISparklines') {
      ScriptApp.deleteTrigger(trigger);
    }
  });

  // Install new 5-minute trigger
  ScriptApp.newTrigger('maintainKPISparklines')
    .timeBased()
    .everyMinutes(5)
    .create();

  Logger.log('✅ Installed 5-minute maintenance trigger for KPI sparklines');
  SpreadsheetApp.getUi().alert('✅ Auto-maintenance enabled!\n\nKPI sparklines will be checked and restored every 5 minutes if needed.');
}

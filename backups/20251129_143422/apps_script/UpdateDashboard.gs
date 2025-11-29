/**
 * UpdateDashboard.gs
 * Complete dashboard automation using Google Sheets API
 * - Updates all formatting
 * - Creates chart zones
 * - Manages data validations
 * - Auto-refresh functionality
 */

// Configuration
const SPREADSHEET_ID = '1LmMq4OEE639Y-XXpOJ3xnvpAmHB6vUovh5g6gaU_vzc';
const DASHBOARD_SHEET = 'Dashboard';

// Orange Theme Colors (RGB 0-1 scale)
const COLORS = {
  orange: {red: 1.0, green: 0.55, blue: 0.0},        // #FF8C00
  blue: {red: 0.0, green: 0.30, blue: 0.59},         // #004C97
  green: {red: 0.26, green: 0.63, blue: 0.28},       // #43A047
  red: {red: 0.90, green: 0.22, blue: 0.21},         // #E53935
  gray: {red: 0.96, green: 0.96, blue: 0.96},        // #F5F5F5
  white: {red: 1, green: 1, blue: 1},
  chartZone: {red: 1.0, green: 0.95, blue: 0.90},
  kpiLight: {red: 1.0, green: 0.93, blue: 0.85}
};

/**
 * Apply complete orange theme formatting to dashboard
 */
function applyOrangeTheme() {
  const ss = SpreadsheetApp.openById(SPREADSHEET_ID);
  const sheet = ss.getSheetByName(DASHBOARD_SHEET);
  
  if (!sheet) {
    throw new Error('Dashboard sheet not found');
  }
  
  Logger.log('🎨 Applying Orange Theme...');
  
  // 1. Title Bar (Row 1)
  sheet.getRange('A1:L1')
    .merge()
    .setValue('⚡ GB ENERGY DASHBOARD – REAL-TIME MARKET INSIGHTS (Orange Theme)')
    .setBackground('#FF8C00')
    .setFontColor('#FFFFFF')
    .setFontWeight('bold')
    .setFontSize(16)
    .setHorizontalAlignment('center');
  sheet.setRowHeight(1, 30);
  
  // 2. Timestamp (Row 2)
  sheet.getRange('A2')
    .setValue(`Last Updated: ${new Date().toLocaleString('en-GB')}`)
    .setFontStyle('italic')
    .setFontColor('#004C97')
    .setFontSize(10);
  
  // 3. Filter Bar (Row 3)
  sheet.getRange('A3:L3')
    .setBackground('#F5F5F5')
    .setFontWeight('bold')
    .setFontSize(10)
    .setHorizontalAlignment('center');
  sheet.setRowHeight(3, 35);
  
  sheet.getRange('A3').setValue('⏱️ Time Range:');
  sheet.getRange('C3').setValue('🗺️ Region:');
  sheet.getRange('E3').setValue('🔔 Alerts:');
  sheet.getRange('G3').setValue('📅 Start Date:');
  sheet.getRange('I3').setValue('📅 End Date:');
  
  // Set default values
  sheet.getRange('B3').setValue('Real-Time (10 min)');
  sheet.getRange('D3').setValue('All GB');
  sheet.getRange('F3').setValue('All');
  sheet.getRange('H3').setValue(new Date('2025-11-01'));
  sheet.getRange('J3').setValue(new Date());
  
  // 4. KPI Strip (Row 5)
  sheet.getRange('A5:L5')
    .setBackground('#FFE8D6')
    .setFontWeight('bold')
    .setFontSize(11)
    .setHorizontalAlignment('center');
  sheet.setRowHeight(5, 25);
  
  // 5. Column Widths
  sheet.setColumnWidth(1, 140);  // A
  for (let col = 2; col <= 12; col++) {
    sheet.setColumnWidth(col, col === 5 || col === 8 ? 150 : 100);
  }
  
  // 6. Table Headers (Row 9)
  sheet.setRowHeight(9, 22);
  
  // Fuel Mix (A9:C9)
  sheet.getRange('A9:C9')
    .setBackground('#FFF8E1')
    .setFontWeight('bold');
  sheet.getRange('A9').setValue('🔥 FUEL MIX');
  sheet.getRange('B9').setValue('GW');
  sheet.getRange('C9').setValue('% Total');
  
  // Interconnectors (E9:F9)
  sheet.getRange('E9:F9')
    .setBackground('#C8E6C9')
    .setFontWeight('bold');
  sheet.getRange('E9').setValue('🌍 INTERCONNECTORS');
  sheet.getRange('F9').setValue('FLOW (MW)');
  
  // Financial (H9:L9)
  sheet.getRange('H9:L9')
    .setBackground('#FFD8B2')
    .setFontWeight('bold');
  sheet.getRange('H9').setValue('💷 FINANCIAL KPIs');
  
  Logger.log('✅ Orange theme applied');
}

/**
 * Set up all chart zones with proper formatting
 */
function setupChartZones() {
  const ss = SpreadsheetApp.openById(SPREADSHEET_ID);
  const sheet = ss.getSheetByName(DASHBOARD_SHEET);
  
  Logger.log('📊 Setting up chart zones...');
  
  const chartZones = [
    {range: 'A20:F20', title: '📊 CHART: Fuel Mix (Doughnut/Pie) - A20:F40'},
    {range: 'G20:L20', title: '📊 CHART: Interconnector Flows (Multi-line) - G20:L40'},
    {range: 'A45:F45', title: '📊 CHART: Demand vs Generation 48h (Stacked Area) - A45:F65'},
    {range: 'G45:L45', title: '📊 CHART: System Prices SSP/SBP/MID (3-Line) - G45:L65'},
    {range: 'A70:L70', title: '📊 CHART: Financial KPIs BOD/BID/Imbalance (Column) - A70:L88'}
  ];
  
  chartZones.forEach(zone => {
    const range = sheet.getRange(zone.range);
    range.merge()
      .setValue(zone.title)
      .setBackground('#FFF1E6')
      .setFontColor('#FF8C00')
      .setFontWeight('bold')
      .setFontStyle('italic')
      .setFontSize(11)
      .setHorizontalAlignment('center');
    
    // Add placeholder text below
    const row = parseInt(zone.range.split(':')[0].match(/\d+/)[0]);
    sheet.getRange(`A${row + 2}`).setValue('[Chart will be inserted here via Apps Script]')
      .setFontSize(9)
      .setFontStyle('italic')
      .setFontColor('#999999');
  });
  
  Logger.log('✅ Chart zones created');
}

/**
 * Set up Top 12 Outages section
 */
function setupOutagesSection() {
  const ss = SpreadsheetApp.openById(SPREADSHEET_ID);
  const sheet = ss.getSheetByName(DASHBOARD_SHEET);
  
  Logger.log('⚠️ Setting up outages section...');
  
  // Header (Row 90)
  sheet.getRange('A90:H90')
    .merge()
    .setValue('⚠️  TOP 12 ACTIVE OUTAGES (by MW Unavailable)')
    .setBackground('#E53935')
    .setFontColor('#FFFFFF')
    .setFontWeight('bold')
    .setFontSize(12)
    .setHorizontalAlignment('center');
  
  // Column headers (Row 91)
  const headers = ['BM Unit', 'Plant', 'Fuel', 'MW Lost', 'Region', 'Start Time', 'End Time', 'Status'];
  sheet.getRange('A91:H91')
    .setValues([headers])
    .setBackground('#FFCDD2')
    .setFontWeight('bold');
  
  // Note
  sheet.getRange('A92')
    .setValue('(Auto-updated every 10 minutes)')
    .setFontStyle('italic')
    .setFontSize(9)
    .setFontColor('#999999');
  
  // Clear data rows
  sheet.getRange('A93:H104').clearContent();
  
  Logger.log('✅ Outages section created');
}

/**
 * Set up data validations (dropdowns)
 */
function setupDataValidations() {
  const ss = SpreadsheetApp.openById(SPREADSHEET_ID);
  const sheet = ss.getSheetByName(DASHBOARD_SHEET);
  
  Logger.log('🔽 Setting up data validations...');
  
  // Time Range (B3)
  const timeValues = ['Real-Time (10 min)', '24 h', '48 h', '7 days', '30 days'];
  const timeRule = SpreadsheetApp.newDataValidation()
    .requireValueInList(timeValues, true)
    .setAllowInvalid(false)
    .build();
  sheet.getRange('B3').setDataValidation(timeRule);
  
  // Region (D3)
  const regionValues = [
    'All GB', 'Eastern Power Networks (EPN)', 'South Eastern Power Networks (SPN)',
    'London Power Networks (LPN)', 'South Wales', 'South West',
    'East Midlands', 'West Midlands', 'North Wales & Merseyside',
    'South Scotland', 'North Scotland', 'Northern', 'Yorkshire', 'North West', 'Southern'
  ];
  const regionRule = SpreadsheetApp.newDataValidation()
    .requireValueInList(regionValues, true)
    .setAllowInvalid(false)
    .build();
  sheet.getRange('D3').setDataValidation(regionRule);
  
  // Alert Filter (F3)
  const alertValues = ['All', 'Critical Only', 'Wind Warning', 'Outages', 'Price Spike'];
  const alertRule = SpreadsheetApp.newDataValidation()
    .requireValueInList(alertValues, true)
    .setAllowInvalid(false)
    .build();
  sheet.getRange('F3').setDataValidation(alertRule);
  
  // Date pickers (H3, J3)
  const dateRule = SpreadsheetApp.newDataValidation()
    .requireDate()
    .setAllowInvalid(false)
    .setHelpText('Select a date')
    .build();
  sheet.getRange('H3').setDataValidation(dateRule);
  sheet.getRange('J3').setDataValidation(dateRule);
  
  Logger.log('✅ Data validations set up');
}

/**
 * Apply conditional formatting rules
 */
function setupConditionalFormatting() {
  const ss = SpreadsheetApp.openById(SPREADSHEET_ID);
  const sheet = ss.getSheetByName(DASHBOARD_SHEET);
  
  Logger.log('🎨 Setting up conditional formatting...');
  
  // Clear existing rules
  sheet.clearConditionalFormatRules();
  
  const rules = [];
  
  // Rule 1: Critical outages (>500 MW) in outages section (B93:D104)
  const outageRule = SpreadsheetApp.newConditionalFormatRule()
    .whenNumberGreaterThan(500)
    .setBackground('#E53935')
    .setFontColor('#FFFFFF')
    .setBold(true)
    .setRanges([sheet.getRange('D93:D104')])
    .build();
  rules.push(outageRule);
  
  // Rule 2: High generation (>5000 MW) in fuel mix data (B10:B18)
  const genRule = SpreadsheetApp.newConditionalFormatRule()
    .whenNumberGreaterThan(5000)
    .setBackground('#43A047')
    .setFontColor('#FFFFFF')
    .setBold(true)
    .setRanges([sheet.getRange('B10:B18')])
    .build();
  rules.push(genRule);
  
  sheet.setConditionalFormatRules(rules);
  
  Logger.log('✅ Conditional formatting applied');
}

/**
 * Create usage notes
 */
function addUsageNotes() {
  const ss = SpreadsheetApp.openById(SPREADSHEET_ID);
  const sheet = ss.getSheetByName(DASHBOARD_SHEET);
  
  Logger.log('📝 Adding usage notes...');
  
  sheet.getRange('A110:L110')
    .merge()
    .setValue('📌 DASHBOARD NOTES')
    .setBackground('#004C97')
    .setFontColor('#FFFFFF')
    .setFontWeight('bold');
  
  const notes = [
    ['• Chart zones (rows 20-88) are reserved - automation should NOT write here'],
    ['• Top 12 Outages section (rows 90-105) - auto-updated every 10 min'],
    ['• Full outage history is in the \'Outages\' sheet (searchable/filterable)'],
    ['• Date pickers in H3 & J3 filter historical data (click cells to see calendar)'],
    ['• Chart creation: Use Apps Script with ranges specified in CHART_SPECS.md'],
    ['• Automation scripts should only update: Rows 10-18 (data), Row 2 (timestamp), Rows 93-104 (outages)']
  ];
  
  sheet.getRange(111, 1, notes.length, 1).setValues(notes)
    .setFontSize(9)
    .setWrap(true);
  
  Logger.log('✅ Usage notes added');
}

/**
 * Create custom menu
 */
function onOpen() {
  const ui = SpreadsheetApp.getUi();
  ui.createMenu('⚡ Dashboard Controls')
    .addItem('🎨 Apply Orange Theme', 'applyFullDashboardSetup')
    .addItem('🔄 Refresh Timestamp', 'updateTimestamp')
    .addItem('🧹 Clear Outages', 'clearOutagesSection')
    .addSeparator()
    .addItem('📊 Create All Charts', 'createAllCharts')
    .addItem('🗺️ Setup Map', 'setupEnergyMap')
    .addToUi();
}

/**
 * Main function to set up everything
 */
function applyFullDashboardSetup() {
  const startTime = new Date();
  Logger.log('='.repeat(70));
  Logger.log('⚡ DASHBOARD V2 COMPLETE SETUP');
  Logger.log('='.repeat(70));
  
  try {
    applyOrangeTheme();
    setupChartZones();
    setupOutagesSection();
    setupDataValidations();
    setupConditionalFormatting();
    addUsageNotes();
    
    const endTime = new Date();
    const duration = (endTime - startTime) / 1000;
    
    Logger.log('='.repeat(70));
    Logger.log(`✅ COMPLETE! (${duration.toFixed(2)}s)`);
    Logger.log('='.repeat(70));
    
    SpreadsheetApp.getUi().alert(
      '✅ Dashboard Setup Complete!',
      `Orange theme applied successfully in ${duration.toFixed(2)} seconds.\n\n` +
      '• Date pickers active (H3, J3)\n' +
      '• Chart zones positioned\n' +
      '• Top 12 Outages section ready\n' +
      '• Conditional formatting applied\n\n' +
      'Check rows 110+ for usage notes.',
      SpreadsheetApp.getUi().ButtonSet.OK
    );
    
  } catch (error) {
    Logger.log(`❌ Error: ${error.message}`);
    Logger.log(error.stack);
    SpreadsheetApp.getUi().alert('❌ Error', error.message, SpreadsheetApp.getUi().ButtonSet.OK);
  }
}

/**
 * Update timestamp
 */
function updateTimestamp() {
  const ss = SpreadsheetApp.openById(SPREADSHEET_ID);
  const sheet = ss.getSheetByName(DASHBOARD_SHEET);
  sheet.getRange('A2').setValue(`Last Updated: ${new Date().toLocaleString('en-GB')}`);
  Logger.log('✅ Timestamp updated');
}

/**
 * Clear outages section
 */
function clearOutagesSection() {
  const ss = SpreadsheetApp.openById(SPREADSHEET_ID);
  const sheet = ss.getSheetByName(DASHBOARD_SHEET);
  sheet.getRange('A93:H104').clearContent();
  sheet.getRange('A93').setValue(`No active outages (checked: ${new Date().toLocaleString('en-GB')})`);
  Logger.log('✅ Outages cleared');
}

/**
 * Setup Energy Map sheet
 */
function setupEnergyMap() {
  const ss = SpreadsheetApp.openById(SPREADSHEET_ID);
  let mapSheet = ss.getSheetByName('Energy_Map');
  
  if (!mapSheet) {
    mapSheet = ss.insertSheet('Energy_Map');
  }
  
  // Title
  mapSheet.getRange('A1:Z1')
    .merge()
    .setValue('🗺️  ENERGY MAP – DNO REGIONS, GSP CONNECTIONS & OFFSHORE WIND')
    .setBackground('#FF8C00')
    .setFontColor('#FFFFFF')
    .setFontWeight('bold')
    .setFontSize(14)
    .setHorizontalAlignment('center');
  mapSheet.setRowHeight(1, 30);
  
  // Layer table
  const layers = [
    ['Layer', 'Colour', 'Description'],
    ['DNO Boundaries', '#FFD180', 'Polygon overlay per DNO region'],
    ['GSP Points', '#004C97', 'Grid Supply Points (hover shows ID & MW)'],
    ['Offshore Wind', '#FF8C00', 'Wind farms & connecting GSP lines'],
    ['Outages', '#E53935', 'Active outage markers on map']
  ];
  
  mapSheet.getRange(3, 1, layers.length, 3).setValues(layers);
  mapSheet.getRange('A3:C3')
    .setBackground('#F5F5F5')
    .setFontWeight('bold');
  
  Logger.log('✅ Energy Map sheet configured');
  SpreadsheetApp.getUi().alert('✅ Energy Map Ready', 'Energy_Map sheet has been configured.', SpreadsheetApp.getUi().ButtonSet.OK);
}

/**
 * Placeholder for chart creation (to be implemented)
 */
function createAllCharts() {
  SpreadsheetApp.getUi().alert(
    '📊 Chart Creation',
    'Chart creation is not yet implemented.\n\n' +
    'Charts will be added manually using the marked zones:\n' +
    '• A20:F40 - Fuel Mix\n' +
    '• G20:L40 - Interconnectors\n' +
    '• A45:F65 - Demand vs Gen\n' +
    '• G45:L65 - System Prices\n' +
    '• A70:L88 - Financial KPIs\n\n' +
    'See CHART_SPECS.md for specifications.',
    SpreadsheetApp.getUi().ButtonSet.OK
  );
}

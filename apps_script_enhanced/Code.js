// Enhanced Apps Script for GB Energy Dashboard
// Includes unified color scheme, BESS/TCR formatting, and automation

// ==================== COLOR SCHEME ====================
const COLORS = {
  ORANGE: '#FF6600',        // Titles
  WHITE: '#FFFFFF',          // Text on orange, backgrounds
  GREY: '#F5F5F5',          // Table bodies
  LIGHT_BLUE: '#D9E9F7',    // Column headers
  DARK_GREY: '#333333',     // Text
  BORDER: '#CCCCCC'         // Cell borders
};

function onOpen() {
  const ui = SpreadsheetApp.getUi();
  ui.createMenu('⚡ GB Energy Dashboard')
    .addItem('🎨 Format All Sheets', 'formatAllSheets')
    .addItem('📊 Format Dashboard', 'formatDashboard')
    .addItem('🔋 Format BESS Sheet', 'formatBESS')
    .addItem('💷 Format TCR Sheet', 'formatTCR')
    .addSeparator()
    .addItem('⚙️ Setup Dropdowns', 'setupDropdowns')
    .addItem('🗺️ Refresh Maps', 'updateMaps')
    .addSeparator()
    .addItem('🔄 Run Python Pipeline', 'triggerPythonPipeline')
    .addToUi();
}

// ==================== UNIFIED FORMATTING ====================

function formatAllSheets() {
  formatDashboard();
  formatBESS();
  formatTCR();
  
  SpreadsheetApp.getActiveSpreadsheet().toast(
    '✅ All sheets formatted with unified design',
    'Success',
    5
  );
}

function formatDashboard() {
  const ss = SpreadsheetApp.getActive();
  const sh = ss.getSheetByName('Dashboard');
  if (!sh) return;

  // Main header (A1)
  sh.getRange('A1:L1')
    .setBackground(COLORS.ORANGE)
    .setFontColor(COLORS.WHITE)
    .setFontWeight('bold')
    .setFontSize(14)
    .setValue('⚡ GB ENERGY DASHBOARD - LIVE DATA');

  // Last updated row (A2)
  sh.getRange('A2:G2')
    .setBackground(COLORS.GREY)
    .setFontWeight('bold')
    .setFontSize(9);

  // Filters row (A3)
  sh.getRange('A3:H3')
    .setBackground(COLORS.LIGHT_BLUE)
    .setFontWeight('bold')
    .setFontSize(9);

  // KPI strip headers (A4)
  sh.getRange('A4:F4')
    .setBackground(COLORS.LIGHT_BLUE)
    .setFontWeight('bold')
    .setHorizontalAlignment('center');

  // KPI values (A5:F5)
  sh.getRange('A5:F5')
    .setBackground(COLORS.WHITE)
    .setFontSize(11)
    .setHorizontalAlignment('center')
    .setBorder(true, true, true, true, true, true, COLORS.BORDER, SpreadsheetApp.BorderStyle.SOLID);

  // Fuel mix section
  sh.getRange('A9:C9')
    .setBackground(COLORS.LIGHT_BLUE)
    .setFontWeight('bold')
    .setValue(['Fuel Type', 'MW', '%']);

  sh.getRange('A10:C25')
    .setBackground(COLORS.GREY);

  // Interconnectors section
  sh.getRange('D9:E9')
    .setBackground(COLORS.LIGHT_BLUE)
    .setFontWeight('bold')
    .setValue(['Interconnector', 'MW']);

  sh.getRange('D10:E25')
    .setBackground(COLORS.GREY);

  // Outages header
  sh.getRange('A28:F28')
    .setBackground(COLORS.ORANGE)
    .setFontColor(COLORS.WHITE)
    .setFontWeight('bold')
    .setValue(['🚨 CURRENT OUTAGES', '', '', '', '', '']);

  sh.getRange('A29:F29')
    .setBackground(COLORS.LIGHT_BLUE)
    .setFontWeight('bold');

  // Column widths
  sh.setColumnWidth(1, 200);  // A
  sh.setColumnWidth(2, 150);  // B
  sh.setColumnWidth(3, 100);  // C
  sh.setColumnWidth(4, 200);  // D
  sh.setColumnWidth(5, 120);  // E
  sh.setColumnWidth(6, 120);  // F

  Logger.log('✅ Dashboard formatted');
}

function formatBESS() {
  const ss = SpreadsheetApp.getActive();
  let sh = ss.getSheetByName('BESS');
  
  if (!sh) {
    sh = ss.insertSheet('BESS');
  }

  // Header (A1)
  sh.getRange('A1:Q1')
    .setBackground(COLORS.ORANGE)
    .setFontColor(COLORS.WHITE)
    .setFontWeight('bold')
    .setFontSize(14)
    .setValues([['Timestamp', '', '', '', '', '', '', '', '', '', 
                 'Charge (MWh)', 'Discharge (MWh)', 'SoC (MWh)', 
                 'Cost (£)', 'Revenue (£)', 'Profit (£)', 'Cumulative (£)']]);

  // Inputs section (A1:B5)
  const inputs = [
    ['Asset ID:', ''],
    ['Site ID:', ''],
    ['Year:', ''],
    ['Scenario:', ''],
    ['Strategy:', '']
  ];
  sh.getRange('A1:B5')
    .setBackground(COLORS.LIGHT_BLUE)
    .setFontWeight('bold')
    .setValues(inputs);

  // KPI Labels (A3:A10)
  const kpiLabels = [
    ['Total Charged (MWh):'],
    ['Total Discharged (MWh):'],
    ['Total Revenue (£):'],
    ['Total Cost (£):'],
    ['Net Profit (£):'],
    ['Profit (£/kW/yr):'],
    ['Cycles/year:'],
    ['IRR (10-yr):']
  ];
  sh.getRange('A3:A10')
    .setBackground(COLORS.LIGHT_BLUE)
    .setFontWeight('bold')
    .setValues(kpiLabels);

  sh.getRange('B3:B10')
    .setBackground(COLORS.WHITE)
    .setNumberFormat('#,##0.00');

  // Revenue stack (F3:H3)
  sh.getRange('F3:H3')
    .setBackground(COLORS.ORANGE)
    .setFontColor(COLORS.WHITE)
    .setFontWeight('bold')
    .setValues([['Revenue Stream', 'Annual (£)', 'Share (%)']]);

  sh.getRange('F4:H10')
    .setBackground(COLORS.GREY);

  // VLP costs section (AA1:AB7)
  const vlpLabels = [
    ['VLP / BM ASSUMPTIONS', ''],
    ['SCRP (£/MWh):', '150'],
    ['Elexon monthly (£):', '250'],
    ['Other VLP costs (£/mo):', '150'],
    ['Total fixed (£/yr):', '=12*(AB3+AB4)'],
    ['Portfolio MW:', '2.5'],
    ['Fixed cost (£/MW/yr):', '=IF(AB6>0,AB5/AB6,0)']
  ];
  sh.getRange('AA1:AB7')
    .setValues(vlpLabels);
  
  sh.getRange('AA1:AB1')
    .setBackground(COLORS.ORANGE)
    .setFontColor(COLORS.WHITE)
    .setFontWeight('bold');

  sh.getRange('AA2:AA7')
    .setBackground(COLORS.LIGHT_BLUE)
    .setFontWeight('bold');

  // Column widths
  sh.setColumnWidth(1, 180);  // A: Timestamp
  sh.setColumnWidths(11, 7, 110);  // K-Q: Data columns

  Logger.log('✅ BESS sheet formatted');
}

function formatTCR() {
  const ss = SpreadsheetApp.getActive();
  let sh = ss.getSheetByName('TCR_Model');
  
  if (!sh) {
    sh = ss.insertSheet('TCR_Model');
  }

  // Header
  sh.getRange('A1:F1')
    .setBackground(COLORS.ORANGE)
    .setFontColor(COLORS.WHITE)
    .setFontWeight('bold')
    .setFontSize(14)
    .setValue('💷 TCR MODEL - NON-ENERGY CHARGE FORECASTS');

  // Inputs (A1:C10)
  const inputs = [
    ['Site ID:', ''],
    ['Year:', '2025'],
    ['Scenario:', 'central'],
    ['Import (MWh/yr):', ''],
    ['', ''],
    ['PV Size (MW):', '0'],
    ['PV MWh/year:', '0'],
    ['BESS Power (MW):', '0'],
    ['BESS Energy (MWh):', '0'],
    ['Strategy:', 'None']
  ];
  sh.getRange('A1:B10')
    .setValues(inputs);

  sh.getRange('A1:A10')
    .setBackground(COLORS.LIGHT_BLUE)
    .setFontWeight('bold');

  // Cost breakdown header (A15:D15)
  sh.getRange('A15:D15')
    .setBackground(COLORS.ORANGE)
    .setFontColor(COLORS.WHITE)
    .setFontWeight('bold')
    .setValues([['Component', 'Base (£/yr)', 'With PV+BESS (£/yr)', 'Savings (£/yr)']]);

  // Cost rows
  const costRows = [
    ['TNUoS (fixed)', '', '', ''],
    ['DUoS residual', '', '', ''],
    ['DUoS RAG', '', '', ''],
    ['BSUoS', '', '', ''],
    ['RO', '', '', ''],
    ['FiT Levy', '', '', ''],
    ['CfD', '', '', ''],
    ['CCL', '', '', ''],
    ['ECO + WHD', '', '', ''],
    ['', '', '', ''],
    ['TOTAL', '', '', ''],
    ['£/MWh', '', '', '']
  ];
  sh.getRange('A16:D27')
    .setValues(costRows);

  sh.getRange('A16:A27')
    .setBackground(COLORS.GREY);

  sh.getRange('B16:D27')
    .setBackground(COLORS.WHITE)
    .setNumberFormat('#,##0.00');

  // Bold totals row
  sh.getRange('A26:D26')
    .setFontWeight('bold')
    .setBackground(COLORS.LIGHT_BLUE);

  Logger.log('✅ TCR sheet formatted');
}

// ==================== DROPDOWNS ====================

function setupDropdowns() {
  const ss = SpreadsheetApp.getActive();
  const cfg = ss.getSheetByName('Config');
  const dash = ss.getSheetByName('Dashboard');
  const bess = ss.getSheetByName('BESS');
  const tcr = ss.getSheetByName('TCR_Model');

  if (!cfg) {
    Logger.log('⚠️  Config sheet not found');
    return;
  }

  // Dashboard dropdowns
  if (dash) {
    // Time range
    const dvTime = SpreadsheetApp.newDataValidation()
      .requireValueInList(['Real-Time (10 min)', '24h', '48h', '7 days', '14 days', '30 days'], true)
      .setAllowInvalid(false)
      .build();
    dash.getRange('B3').setDataValidation(dvTime);
  }

  // BESS dropdowns
  if (bess) {
    const dvYear = SpreadsheetApp.newDataValidation()
      .requireValueInList(['2023', '2024', '2025', '2026', '2027', '2028', '2029', '2030'], true)
      .build();
    bess.getRange('B3').setDataValidation(dvYear);

    const dvScenario = SpreadsheetApp.newDataValidation()
      .requireValueInList(['central', 'high', 'low'], true)
      .build();
    bess.getRange('B4').setDataValidation(dvScenario);
  }

  // TCR dropdowns
  if (tcr) {
    const dvYear = SpreadsheetApp.newDataValidation()
      .requireValueInList(['2025', '2026', '2027', '2028', '2029', '2030'], true)
      .build();
    tcr.getRange('B2').setDataValidation(dvYear);

    const dvScenario = SpreadsheetApp.newDataValidation()
      .requireValueInList(['central', 'high', 'low'], true)
      .build();
    tcr.getRange('B3').setDataValidation(dvScenario);

    const dvStrategy = SpreadsheetApp.newDataValidation()
      .requireValueInList(['None', 'Peak Shaving', 'RAG Shifting', 'CCL Avoidance', 'Full Flex'], true)
      .build();
    tcr.getRange('B10').setDataValidation(dvStrategy);
  }

  Logger.log('✅ Dropdowns configured');
}

// ==================== MAPS ====================

function updateMaps() {
  const ss = SpreadsheetApp.getActive();
  const dash = ss.getSheetByName('Dashboard');
  const mapSheet = ss.getSheetByName('Map_Data');
  
  if (!dash || !mapSheet) return;

  // Create static map
  const values = mapSheet.getRange('A2:G200').getValues();
  const map = Maps.newStaticMap()
    .setCenter('United Kingdom')
    .setZoom(5)
    .setSize(640, 400);

  values.forEach(row => {
    const lat = row[2];
    const lng = row[3];
    const lf = row[5];
    if (!lat || !lng) return;
    
    let color = 'red';
    if (lf > 0.6) color = 'green';
    else if (lf > 0.3) color = 'orange';
    
    map.addMarker(lat, lng, { color: color });
  });

  const blob = map.getBlob();
  dash.insertImage(blob, 8, 7);
  
  Logger.log('✅ Maps updated');
}

// ==================== PYTHON PIPELINE TRIGGER ====================

function triggerPythonPipeline() {
  // This would call your webhook/Cloud Function
  // For now, just display message
  SpreadsheetApp.getActiveSpreadsheet().toast(
    '🐍 Trigger Python pipeline via webhook or Cloud Scheduler',
    'Info',
    5
  );
}

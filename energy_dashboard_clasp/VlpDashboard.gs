/**
 * VLP Revenue Dashboard - Sheet Layout and Formatting
 */

// Color scheme
const COLORS = {
  primary: '#1e88e5',      // Blue
  success: '#43a047',      // Green
  warning: '#fb8c00',      // Orange
  danger: '#e53935',       // Red
  background: '#f5f5f5',   // Light gray
  text: '#212121'          // Dark gray
};

/**
 * Create or refresh VLP Revenue sheet
 */
function createVlpRevenueSheet() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  let sheet = ss.getSheetByName('VLP Revenue');
  
  if (!sheet) {
    sheet = ss.insertSheet('VLP Revenue');
  } else {
    sheet.clear();
  }
  
  // Build all sections
  buildLiveTicker(sheet);
  buildCurrentPeriodSection(sheet);
  buildServiceBreakdownSection(sheet);
  buildCostBreakdownSection(sheet);
  buildStackingScenarios(sheet);
  buildCompatibilityMatrix(sheet);
  buildProfitAnalysis(sheet);
  
  // Apply overall formatting
  sheet.setFrozenRows(3);
  sheet.setColumnWidths(1, 26, 100);
  
  return sheet;
}

/**
 * Build live ticker at top
 */
function buildLiveTicker(sheet) {
  // Merge cells for ticker banner
  sheet.getRange('A1:M3').merge();
  sheet.getRange('A1').setValue('⚡ LIVE VLP REVENUE TICKER - Loading...');
  sheet.getRange('A1')
    .setFontSize(16)
    .setFontWeight('bold')
    .setHorizontalAlignment('center')
    .setVerticalAlignment('middle')
    .setBackground(COLORS.primary)
    .setFontColor('#FFFFFF');
}

/**
 * Build current period summary section
 */
function buildCurrentPeriodSection(sheet) {
  const startRow = 5;
  
  // Header
  sheet.getRange(`A${startRow}`).setValue('📊 CURRENT PERIOD SUMMARY');
  sheet.getRange(`A${startRow}`).setFontSize(14).setFontWeight('bold').setFontColor(COLORS.primary);
  
  // Labels
  const labels = [
    ['Settlement Date:', ''],
    ['Settlement Period:', ''],
    ['Time:', ''],
    ['DUoS Band:', ''],
    ['Market Price:', ''],
    ['Total Revenue:', ''],
    ['Total Cost:', ''],
    ['Net Profit:', ''],
    ['Trading Signal:', '']
  ];
  
  sheet.getRange(`A${startRow + 1}:B${startRow + 9}`).setValues(labels);
  sheet.getRange(`A${startRow + 1}:A${startRow + 9}`).setFontWeight('bold');
  
  // Format value cells
  sheet.getRange(`B${startRow + 5}:B${startRow + 7}`).setNumberFormat('"£"#,##0.00');
  sheet.getRange(`B${startRow + 8}`).setNumberFormat('"£"#,##0.00');
}

/**
 * Build service breakdown section
 */
function buildServiceBreakdownSection(sheet) {
  const startRow = 17;
  
  // Header
  sheet.getRange(`A${startRow}`).setValue('💰 VLP SERVICE BREAKDOWN (£/MWh)');
  sheet.getRange(`A${startRow}`).setFontSize(14).setFontWeight('bold').setFontColor(COLORS.primary);
  
  // Column headers
  sheet.getRange(`A${startRow + 1}:E${startRow + 1}`).setValues([
    ['Service', 'Revenue/MWh', '% of Total', 'Annual (£)', 'Status']
  ]);
  sheet.getRange(`A${startRow + 1}:E${startRow + 1}`)
    .setFontWeight('bold')
    .setBackground(COLORS.background);
  
  // Service rows
  const services = [
    ['PPA Discharge', '', '', '', ''],
    ['DC (Dynamic Containment)', '', '', '', ''],
    ['DM (Dynamic Moderation)', '', '', '', ''],
    ['DR (Dynamic Regulation)', '', '', '', ''],
    ['CM (Capacity Market)', '', '', '', ''],
    ['BM (Balancing Mechanism)', '', '', '', ''],
    ['Triad Avoidance', '', '', '', ''],
    ['Negative Pricing', '', '', '', '']
  ];
  
  sheet.getRange(`A${startRow + 2}:E${startRow + 9}`).setValues(services);
  
  // Format currency columns
  sheet.getRange(`B${startRow + 2}:B${startRow + 9}`).setNumberFormat('"£"#,##0.00');
  sheet.getRange(`D${startRow + 2}:D${startRow + 9}`).setNumberFormat('"£"#,##0');
  sheet.getRange(`C${startRow + 2}:C${startRow + 9}`).setNumberFormat('0.0"%"');
  
  // Total row
  sheet.getRange(`A${startRow + 10}:E${startRow + 10}`).setValues([
    ['TOTAL STACKED REVENUE', '', '100.0%', '', '✅']
  ]);
  sheet.getRange(`A${startRow + 10}:E${startRow + 10}`)
    .setFontWeight('bold')
    .setBackground(COLORS.success)
    .setFontColor('#FFFFFF');
}

/**
 * Build cost breakdown section
 */
function buildCostBreakdownSection(sheet) {
  const startRow = 5;
  const startCol = 'G';
  
  // Header
  sheet.getRange(`${startCol}${startRow}`).setValue('💸 COST BREAKDOWN (£/MWh)');
  sheet.getRange(`${startCol}${startRow}`).setFontSize(14).setFontWeight('bold').setFontColor(COLORS.primary);
  
  // Cost items
  const costs = [
    ['Market Price (System Buy)', ''],
    ['DUoS Charge', ''],
    ['TNUoS (Transmission)', '£12.50'],
    ['BSUoS (Balancing)', '£4.50'],
    ['CCL (Climate Change Levy)', '£7.75'],
    ['RO (Renewables Obligation)', '£61.90'],
    ['FiT (Feed-in Tariff)', '£11.50'],
    ['', ''],
    ['TOTAL COST', '']
  ];
  
  sheet.getRange(`${startCol}${startRow + 1}:H${startRow + 9}`).setValues(costs);
  sheet.getRange(`${startCol}${startRow + 1}:${startCol}${startRow + 9}`).setFontWeight('bold');
  
  // Format currency
  sheet.getRange(`H${startRow + 1}:H${startRow + 9}`).setNumberFormat('"£"#,##0.00');
  
  // Total row formatting
  sheet.getRange(`${startCol}${startRow + 9}:H${startRow + 9}`)
    .setFontWeight('bold')
    .setBackground(COLORS.danger)
    .setFontColor('#FFFFFF');
}

/**
 * Build stacking scenarios comparison
 */
function buildStackingScenarios(sheet) {
  const startRow = 30;
  
  // Header
  sheet.getRange(`A${startRow}`).setValue('🎯 REVENUE STACKING SCENARIOS');
  sheet.getRange(`A${startRow}`).setFontSize(14).setFontWeight('bold').setFontColor(COLORS.primary);
  
  // Column headers
  sheet.getRange(`A${startRow + 1}:H${startRow + 1}`).setValues([
    ['Scenario', 'Services', 'Annual Revenue', 'Revenue/MWh', 'Profit Margin', 'Risk Level', 'Status', 'Description']
  ]);
  sheet.getRange(`A${startRow + 1}:H${startRow + 1}`)
    .setFontWeight('bold')
    .setBackground(COLORS.background)
    .setWrap(true);
  
  // Scenario rows (will be populated by refresh function)
  const scenarios = [
    ['Conservative', '', '', '', '', 'Low', '', ''],
    ['Balanced', '', '', '', '', 'Medium', '', ''],
    ['Aggressive', '', '', '', '', 'High', '', ''],
    ['Opportunistic', '', '', '', '', 'Low-Medium', '', '']
  ];
  
  sheet.getRange(`A${startRow + 2}:H${startRow + 5}`).setValues(scenarios);
  
  // Format currency columns
  sheet.getRange(`C${startRow + 2}:C${startRow + 5}`).setNumberFormat('"£"#,##0');
  sheet.getRange(`D${startRow + 2}:D${startRow + 5}`).setNumberFormat('"£"#,##0.00');
  sheet.getRange(`E${startRow + 2}:E${startRow + 5}`).setNumberFormat('"£"#,##0.00');
  
  // Set column widths
  sheet.setColumnWidth(sheet.getRange(`B${startRow}`).getColumn(), 200);
  sheet.setColumnWidth(sheet.getRange(`H${startRow}`).getColumn(), 250);
}

/**
 * Build service compatibility matrix
 */
function buildCompatibilityMatrix(sheet) {
  const startRow = 38;
  
  // Header
  sheet.getRange(`A${startRow}`).setValue('🧩 SERVICE COMPATIBILITY MATRIX');
  sheet.getRange(`A${startRow}`).setFontSize(14).setFontWeight('bold').setFontColor(COLORS.primary);
  
  // Matrix headers (services along top and left)
  const services = ['DC', 'DM', 'DR', 'BM', 'CM', 'PPA', 'TRIAD', 'NEG'];
  
  // Top row
  sheet.getRange(`B${startRow + 1}:I${startRow + 1}`).setValues([services]);
  sheet.getRange(`B${startRow + 1}:I${startRow + 1}`)
    .setFontWeight('bold')
    .setBackground(COLORS.background)
    .setHorizontalAlignment('center');
  
  // Left column
  for (let i = 0; i < services.length; i++) {
    sheet.getRange(`A${startRow + 2 + i}`).setValue(services[i]);
  }
  sheet.getRange(`A${startRow + 2}:A${startRow + 9}`)
    .setFontWeight('bold')
    .setBackground(COLORS.background)
    .setHorizontalAlignment('center');
  
  // Matrix will be populated with ✓, ✗, ⚠ by refresh function
}

/**
 * Build profit analysis section
 */
function buildProfitAnalysis(sheet) {
  const startRow = 17;
  const startCol = 'K';
  
  // Header
  sheet.getRange(`${startCol}${startRow}`).setValue('📈 PROFIT ANALYSIS BY DUOS BAND');
  sheet.getRange(`${startCol}${startRow}`).setFontSize(14).setFontWeight('bold').setFontColor(COLORS.primary);
  
  // Column headers
  sheet.getRange(`${startCol}${startRow + 1}:N${startRow + 1}`).setValues([
    ['Band', 'Avg Profit', 'Min Profit', 'Max Profit']
  ]);
  sheet.getRange(`${startCol}${startRow + 1}:N${startRow + 1}`)
    .setFontWeight('bold')
    .setBackground(COLORS.background);
  
  // Band rows
  const bands = [
    ['GREEN', '', '', ''],
    ['AMBER', '', '', ''],
    ['RED', '', '', '']
  ];
  
  sheet.getRange(`${startCol}${startRow + 2}:N${startRow + 4}`).setValues(bands);
  
  // Format currency
  sheet.getRange(`L${startRow + 2}:N${startRow + 4}`).setNumberFormat('"£"#,##0.00');
  
  // Color code bands
  sheet.getRange(`${startCol}${startRow + 2}`).setBackground('#c8e6c9'); // GREEN
  sheet.getRange(`${startCol}${startRow + 3}`).setBackground('#ffe0b2'); // AMBER
  sheet.getRange(`${startCol}${startRow + 4}`).setBackground('#ffcdd2'); // RED
}

/**
 * Update live ticker with latest data
 */
function updateLiveTicker() {
  const sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName('VLP Revenue');
  if (!sheet) return;
  
  const latest = getLatestVlpRevenue();
  if (!latest) {
    sheet.getRange('A1').setValue('⚠️ DATA UNAVAILABLE - Check IRIS feed');
    sheet.getRange('A1').setBackground(COLORS.warning);
    return;
  }
  
  // Build ticker text
  const profit = latest.net_margin_per_mwh;
  const profitIcon = profit > 150 ? '🟢' : profit > 100 ? '🟡' : '🔴';
  
  const tickerText = `${profitIcon} LIVE: ${latest.duos_band} | Market £${latest.market_price.toFixed(2)} | Revenue £${latest.total_stacked_revenue_per_mwh.toFixed(2)} | Profit £${profit.toFixed(2)}/MWh | Signal: ${latest.trading_signal} | ${new Date().toLocaleTimeString()}`;
  
  sheet.getRange('A1').setValue(tickerText);
  
  // Color based on profit
  if (profit > 150) {
    sheet.getRange('A1').setBackground(COLORS.success);
  } else if (profit > 100) {
    sheet.getRange('A1').setBackground(COLORS.warning);
  } else {
    sheet.getRange('A1').setBackground(COLORS.danger);
  }
}

/**
 * Refresh all VLP dashboard data
 */
function refreshVlpDashboard() {
  const sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName('VLP Revenue');
  if (!sheet) {
    createVlpRevenueSheet();
    return;
  }
  
  // Update ticker
  updateLiveTicker();
  
  // Update current period
  updateCurrentPeriod(sheet);
  
  // Update service breakdown
  updateServiceBreakdown(sheet);
  
  // Update cost breakdown
  updateCostBreakdown(sheet);
  
  // Update stacking scenarios
  updateStackingScenarios(sheet);
  
  // Update compatibility matrix
  updateCompatibilityMatrix(sheet);
  
  // Update profit analysis
  updateProfitAnalysis(sheet);
  
  SpreadsheetApp.getUi().alert('✅ VLP Dashboard refreshed successfully!');
}

/**
 * Update current period section with latest data
 */
function updateCurrentPeriod(sheet) {
  const latest = getLatestVlpRevenue();
  if (!latest) return;
  
  const values = [
    [latest.settlementDate],
    [latest.settlementPeriod],
    [latest.ts_halfhour],
    [latest.duos_band],
    [latest.market_price],
    [latest.total_stacked_revenue_per_mwh],
    [latest.total_cost_per_mwh],
    [latest.net_margin_per_mwh],
    [latest.trading_signal]
  ];
  
  sheet.getRange('B6:B14').setValues(values);
  
  // Color code trading signal
  const signalCell = sheet.getRange('B14');
  if (latest.trading_signal === 'DISCHARGE_HIGH') {
    signalCell.setBackground(COLORS.success).setFontColor('#FFFFFF');
  } else if (latest.trading_signal === 'DISCHARGE_MODERATE') {
    signalCell.setBackground(COLORS.warning).setFontColor('#FFFFFF');
  } else if (latest.trading_signal === 'HOLD') {
    signalCell.setBackground(COLORS.danger).setFontColor('#FFFFFF');
  }
}

/**
 * Update service breakdown
 */
function updateServiceBreakdown(sheet) {
  const breakdown = getServiceBreakdown();
  if (!breakdown) return;
  
  const services = Object.keys(breakdown);
  const total = Object.values(breakdown).reduce((sum, val) => sum + val, 0);
  
  let row = 19;
  services.forEach(service => {
    const value = breakdown[service];
    const pct = (value / total) * 100;
    const annual = value * 2482; // Annual MWh discharged
    const status = value > 0 ? '✅' : '⏸️';
    
    sheet.getRange(`B${row}`).setValue(value);
    sheet.getRange(`C${row}`).setValue(pct);
    sheet.getRange(`D${row}`).setValue(annual);
    sheet.getRange(`E${row}`).setValue(status);
    row++;
  });
  
  // Update total
  sheet.getRange('B27').setValue(total);
  sheet.getRange('D27').setValue(total * 2482);
}

/**
 * Update cost breakdown
 */
function updateCostBreakdown(sheet) {
  const costs = getCostBreakdown();
  if (!costs) return;
  
  sheet.getRange('H6').setValue(costs.market_price);
  sheet.getRange('H7').setValue(costs.duos);
  sheet.getRange('H14').setValue(costs.total_cost);
}

/**
 * Update stacking scenarios
 */
function updateStackingScenarios(sheet) {
  const scenarios = getStackingScenarios();
  
  let row = 32;
  scenarios.forEach(s => {
    sheet.getRange(`B${row}`).setValue(s.services);
    sheet.getRange(`C${row}`).setValue(s.annual_revenue);
    sheet.getRange(`D${row}`).setValue(s.revenue_per_mwh);
    sheet.getRange(`E${row}`).setValue(s.revenue_per_mwh - 120); // Approx profit
    sheet.getRange(`G${row}`).setValue(s.risk === 'Low' ? '✅' : s.risk === 'High' ? '⚠️' : '🟡');
    sheet.getRange(`H${row}`).setValue(s.description);
    row++;
  });
}

/**
 * Update compatibility matrix
 */
function updateCompatibilityMatrix(sheet) {
  const compat = getServiceCompatibility();
  const services = ['DC', 'DM', 'DR', 'BM', 'CM', 'PPA', 'TRIAD', 'NEG'];
  
  // Initialize matrix with diagonal (service with itself = N/A)
  for (let i = 0; i < services.length; i++) {
    sheet.getRange(40 + i, 2 + i).setValue('-');
  }
  
  // Fill compatibility data
  compat.forEach(c => {
    const idx1 = services.indexOf(c.service1);
    const idx2 = services.indexOf(c.service2);
    
    if (idx1 >= 0 && idx2 >= 0) {
      const symbol = c.compatible ? '✓' : '✗';
      sheet.getRange(40 + idx1, 2 + idx2).setValue(symbol);
      sheet.getRange(40 + idx2, 2 + idx1).setValue(symbol); // Symmetric
    }
  });
}

/**
 * Update profit analysis by band
 */
function updateProfitAnalysis(sheet) {
  const profitData = getProfitByBand();
  
  let row = 20;
  profitData.forEach(band => {
    sheet.getRange(`L${row}`).setValue(band.avg_profit);
    sheet.getRange(`M${row}`).setValue(band.min_profit);
    sheet.getRange(`N${row}`).setValue(band.max_profit);
    row++;
  });
}

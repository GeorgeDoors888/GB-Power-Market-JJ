/**
 * Sets up the dashboard layout.
 */
function setupDashboardLayout(sheet) {
  sheet.clear();
  sheet.setFrozenRows(2);
  sheet.getRange('1:1000').setBackground('#f3f3f3').setFontColor('#000000');
  sheet.setColumnWidths(1, 12, 150);

  // Header
  sheet.getRange('A1:L1').merge()
    .setValue('GB Power Market - Live Executive Dashboard v2.1')
    .setBackground('#212121')
    .setFontColor('#ffffff')
    .setFontSize(20)
    .setFontWeight('bold')
    .setHorizontalAlignment('center')
    .setVerticalAlignment('middle');
  sheet.setRowHeight(1, 50);

  sheet.getRange('A2:L2').merge()
    .setValue('Last Updated: ' + new Date().toLocaleString('en-GB', { timeZone: 'Europe/London' }))
    .setBackground('#424242')
    .setFontColor('#ffffff')
    .setFontSize(10)
    .setHorizontalAlignment('center');

  // KPI Section - Row 4 left unmerged for sparklines
  sheet.getRange('A4')
    .setValue('Key Performance Indicators')
    .setFontSize(14)
    .setFontWeight('bold');

  const kpiHeaders = ['VLP Revenue (£k)', 'Wholesale Avg (£/MWh)', 'Grid Frequency (Hz)',
                      'Total Gen (GW)', 'Wind Gen (GW)', 'Demand (GW)'];

  for (let i = 0; i < kpiHeaders.length; i++) {
    const col = i * 2 + 1;
    sheet.getRange(5, col, 1, 2).merge()
      .setValue(kpiHeaders[i])
      .setFontWeight('bold')
      .setHorizontalAlignment('center')
      .setBackground('#eeeeee')
      .setBorder(true, true, true, true, null, null);

    sheet.getRange(6, col)
      .setFontSize(18)
      .setFontWeight('bold')
      .setHorizontalAlignment('center')
      .setVerticalAlignment('middle')
      .setBorder(null, true, null, true, null, null);

    sheet.getRange(7, col, 2, 1).merge()
      .setBorder(true, true, true, true, null, null);

    sheet.getRange(6, col + 1, 3, 1).merge()
      .setBorder(null, true, true, null, null, null);
  }

  sheet.setRowHeight(6, 40);
  sheet.setRowHeights(7, 2, 20);

  // Live Snapshot Section
  sheet.getRange('A10:L10').merge()
    .setValue('Live Market Snapshot')
    .setFontSize(14)
    .setFontWeight('bold');

  // Generation Mix headers
  sheet.getRange('A11:B11').merge()
    .setValue('Generation Mix')
    .setFontWeight('bold')
    .setHorizontalAlignment('center')
    .setBackground('#eeeeee');

  sheet.getRange('A12').setValue('Fuel Type').setFontWeight('bold');
  sheet.getRange('B12').setValue('MW').setFontWeight('bold');

  sheet.getRange('D12').setValue('Connection').setFontWeight('bold');
  sheet.getRange('E12').setValue('Flow (MW)').setFontWeight('bold');
}

function setupDashboardLayoutV2(sheet) {
  // Check if Python updater is managing the layout
  const skipAutoLayout = sheet.getRange('AA1').getValue();
  if (skipAutoLayout === 'PYTHON_MANAGED') {
    Logger.log('Skipping layout setup - managed by Python script');
    return;
  }

  sheet.clear();
  sheet.setFrozenRows(2);
  sheet.getRange('1:1000').setBackground('#ffffff').setFontColor('#333333');
  sheet.setColumnWidths(1, 12, 100);

  // Modern Header with Emojis ⚡🇬🇧
  sheet.getRange('A1:L1').merge()
    .setValue('⚡ GB Power Market v2 🇬🇧')
    .setBackground('#2c3e50') // Dark Blue/Grey
    .setFontColor('#ffffff')
    .setFontSize(24)
    .setFontWeight('bold')
    .setHorizontalAlignment('left')
    .setVerticalAlignment('middle');
  sheet.setRowHeight(1, 60);

  // Sub-header
  sheet.getRange('A2:L2').merge()
    .setValue('📊 Live Executive Dashboard | Last Updated: ' + new Date().toLocaleString('en-GB', { timeZone: 'Europe/London' }))
    .setBackground('#ecf0f1')
    .setFontColor('#7f8c8d')
    .setFontSize(11)
    .setHorizontalAlignment('left')
    .setVerticalAlignment('middle');
  sheet.setRowHeight(2, 30);

  // KPI Section - Row 4 left unmerged for sparklines (C4, E4, G4, I4, K4)
  // Only set text in A4, leave other cells for sparklines
  sheet.getRange('A4')
    .setValue('🚀 Market Overview')
    .setFontSize(16)
    .setFontWeight('bold')
    .setFontColor('#2c3e50');

  const kpiHeaders = ['💰 VLP Revenue', '📉 Wholesale Price', '💓 Grid Frequency',
                      '🏭 Total Generation', '🌬️ Wind Output', '🔌 System Demand'];

  // Create card-like look for KPIs
  for (let i = 0; i < kpiHeaders.length; i++) {
    const col = i * 2 + 1;

    // 1. Card Container (Border around the whole card)
    // We will border the individual sections to look like a card

    // Header (Row 5)
    sheet.getRange(5, col, 1, 2).merge()
      .setValue(kpiHeaders[i])
      .setFontWeight('bold')
      .setHorizontalAlignment('center')
      .setBackground('#f1f2f6') // Light grey
      .setFontColor('#57606f')
      .setBorder(true, true, false, true, null, null, '#dfe4ea', SpreadsheetApp.BorderStyle.SOLID_MEDIUM);

    // Value (Row 6)
    sheet.getRange(6, col, 1, 2).merge()
      .setFontSize(24) // Larger font
      .setFontWeight('bold')
      .setHorizontalAlignment('center')
      .setVerticalAlignment('middle')
      .setBackground('#ffffff')
      .setFontColor('#2f3542')
      .setBorder(false, true, false, true, null, null, '#dfe4ea', SpreadsheetApp.BorderStyle.SOLID_MEDIUM);

    // Sparkline area (Row 7-8 merged)
    sheet.getRange(7, col, 2, 2).merge()
      .setBackground('#ffffff')
      .setHorizontalAlignment('center')
      .setVerticalAlignment('middle')
      .setBorder(false, true, true, true, null, null, '#dfe4ea', SpreadsheetApp.BorderStyle.SOLID_MEDIUM);
  }

  sheet.setRowHeight(6, 60); // Taller for value
  sheet.setRowHeights(7, 2, 60); // Much taller for sparklines (was 30)

  // Main Content Area
  sheet.getRange('A10:F10').merge()
    .setValue('🔋 Generation Mix')
    .setFontSize(14)
    .setFontWeight('bold')
    .setBorder(null, null, true, null, null, null, '#2980b9', SpreadsheetApp.BorderStyle.SOLID_MEDIUM);

  sheet.getRange('G10:L10').merge()
    .setValue('🌍 Interconnectors & Map')
    .setFontSize(14)
    .setFontWeight('bold')
    .setBorder(null, null, true, null, null, null, '#2980b9', SpreadsheetApp.BorderStyle.SOLID_MEDIUM);

  // Wind Analysis Section (New)
  sheet.getRange('A30:L30').merge()
    .setValue('🌬️ Wind Analysis & Outages')
    .setFontSize(14)
    .setFontWeight('bold')
    .setBorder(null, null, true, null, null, null, '#2980b9', SpreadsheetApp.BorderStyle.SOLID_MEDIUM);

  // Headers for Gen Mix
  sheet.getRange('A12').setValue('🛢️ Fuel Type')
    .setFontWeight('bold')
    .setBackground('#ecf0f1');

  sheet.getRange('B12').setValue('⚡ GW')
    .setFontWeight('bold')
    .setBackground('#ecf0f1');

  sheet.getRange('C12').setValue('📊 Share')
    .setFontWeight('bold')
    .setBackground('#ecf0f1');

  sheet.getRange('D12').setValue('📊 Bar')
    .setFontWeight('bold')
    .setBackground('#ecf0f1');

  sheet.getRange('E12').setValue('📈 Trend (00:00→)')
    .setFontWeight('bold')
    .setBackground('#ecf0f1');

  // Headers for Interconnectors
  sheet.getRange('G12').setValue('🔗 Connection')
    .setFontWeight('bold')
    .setBackground('#ecf0f1');

  sheet.getRange('H12:I12').merge()
    .setValue('🌊 Flow Trend')
    .setFontWeight('bold')
    .setBackground('#ecf0f1')
    .setHorizontalAlignment('center');

  sheet.getRange('J12').setValue('MW')
    .setFontWeight('bold')
    .setBackground('#ecf0f1');

  // Constraint Analysis Section
  sheet.getRange('A53:L53').merge()
    .setValue('🚧 Live Constraint Actions (Current Day)')
    .setFontSize(14)
    .setFontWeight('bold')
    .setBorder(null, null, true, null, null, null, '#2980b9', SpreadsheetApp.BorderStyle.SOLID_MEDIUM);

  // Add Conditional Formatting
  var rules = sheet.getConditionalFormatRules();

  // Frequency Rule (Green if stable)
  var freqRange = sheet.getRange("E6");
  var ruleFreq = SpreadsheetApp.newConditionalFormatRule()
    .whenNumberBetween(49.8, 50.2)
    .setBackground("#e6f4ea") // Light Green
    .setFontColor("#137333")
    .setRanges([freqRange])
    .build();
  rules.push(ruleFreq);

  // Price Rule (Red if high > 100)
  var priceRange = sheet.getRange("C6");
  var rulePrice = SpreadsheetApp.newConditionalFormatRule()
    .whenNumberGreaterThan(100)
    .setBackground("#fce8e6") // Light Red
    .setFontColor("#c5221f")
    .setRanges([priceRange])
    .build();
  rules.push(rulePrice);

  sheet.setConditionalFormatRules(rules);
}

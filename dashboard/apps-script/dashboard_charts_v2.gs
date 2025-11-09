/**
 * GB Power Market Dashboard Charts - V2 (ChartData Sheet)
 * Creates interactive charts from hidden ChartData sheet
 * 
 * Data Source: ChartData sheet (hidden)
 * Display Location: Dashboard sheet
 */

/**
 * Helper function to show messages - works in both UI and API contexts
 */
function showMessage(message) {
  Logger.log(message);
  try {
    SpreadsheetApp.getUi().alert(message);
  } catch (e) {
    // API context - UI not available, Logger.log already called above
  }
}

function createDashboardCharts() {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var dashboard = ss.getSheetByName('Dashboard');  // Updated to Dashboard
  var chartData = ss.getSheetByName('ChartData') || ss.getSheetByName('Chart Data');  // Support both names
  
  if (!dashboard) {
    showMessage('❌ Dashboard sheet not found!');
    return;
  }
  
  if (!chartData) {
    showMessage('❌ ChartData sheet not found! Run enhance_dashboard_layout.py first.');
    return;
  }
  
  // Get data range from ChartData sheet
  var lastRow = chartData.getLastRow();
  if (lastRow < 2) {
    showMessage('❌ No chart data found in ChartData sheet!');
    return;
  }
  
  var dataRange = chartData.getRange('A1:F' + lastRow);
  
  // Remove existing charts
  var charts = dashboard.getCharts();
  charts.forEach(function(chart) {
    dashboard.removeChart(chart);
  });
  
  Logger.log('✅ Removed ' + charts.length + ' existing charts');
  Logger.log('📊 Creating charts from ChartData (rows: ' + lastRow + ')...');
  
  // Chart positions - Right side of Dashboard (Column J+)
  var chartWidth = 550;
  var chartHeight = 350;
  var startRow = 7;   // Start below header, aligned with Generation section
  var startCol = 10;  // Column J (right side)
  
  // 1. LINE CHART - 24h Generation Trend (Top Left)
  var lineChart = dashboard.newChart()
    .setChartType(Charts.ChartType.LINE)
    .addRange(dataRange)
    .setPosition(startRow, startCol, 0, 0)
    .setOption('title', '📈 24-Hour Generation Trend')
    .setOption('width', chartWidth)
    .setOption('height', chartHeight)
    .setOption('hAxis', {
      title: 'Settlement Period',
      slantedText: true,
      slantedTextAngle: 45
    })
    .setOption('vAxis', {
      title: 'Generation (MW)',
      format: '#,###'
    })
    .setOption('legend', {position: 'bottom'})
    .setOption('curveType', 'function')
    .setOption('lineWidth', 2)
    .setOption('colors', ['#1E88E5', '#FDD835', '#43A047', '#E53935', '#9E9E9E'])
    .setOption('series', {
      0: {labelInLegend: 'Wind'},
      1: {labelInLegend: 'Solar'},
      2: {labelInLegend: 'Nuclear'},
      3: {labelInLegend: 'Gas'},
      4: {labelInLegend: 'Total'}
    })
    .build();
  
  dashboard.insertChart(lineChart);
  Logger.log('✅ Line chart created');
  
  // 2. PIE CHART - Current Generation Mix (Top Right - next to line chart)
  // Get generation data from Dashboard sheet (Row 7-17)
  var genMixStartRow = 7;  // Where "GENERATION BY FUEL TYPE" starts
  var genMixData = dashboard.getRange('A8:B17');  // Fuel types and generation
  
  var pieChart = dashboard.newChart()
    .setChartType(Charts.ChartType.PIE)
    .addRange(genMixData)
    .setPosition(startRow, startCol + 7, 0, 0)  // Column Q (next to line chart)
    .setOption('title', '🥧 Current Generation Mix')
    .setOption('width', chartWidth)
    .setOption('height', chartHeight)
    .setOption('is3D', true)
    .setOption('pieSliceText', 'percentage')
    .setOption('legend', {position: 'right'})
    .setOption('sliceVisibilityThreshold', 0.01)  // Hide slices < 1%
    .build();
  
  dashboard.insertChart(pieChart);
  Logger.log('✅ Pie chart created');
  
  // 3. AREA CHART - Stacked Generation (Bottom Left)
  var areaChart = dashboard.newChart()
    .setChartType(Charts.ChartType.AREA)
    .addRange(dataRange)
    .setPosition(startRow + 22, startCol, 0, 0)  // Below line chart
    .setOption('title', '📊 Stacked Generation (24h)')
    .setOption('width', chartWidth)
    .setOption('height', chartHeight)
    .setOption('isStacked', true)
    .setOption('hAxis', {
      title: 'Settlement Period',
      slantedText: true,
      slantedTextAngle: 45
    })
    .setOption('vAxis', {
      title: 'Generation (MW)',
      format: '#,###'
    })
    .setOption('legend', {position: 'bottom'})
    .setOption('colors', ['#1E88E5', '#FDD835', '#43A047', '#E53935'])
    .setOption('series', {
      0: {labelInLegend: 'Wind'},
      1: {labelInLegend: 'Solar'},
      2: {labelInLegend: 'Nuclear'},
      3: {labelInLegend: 'Gas'}
    })
    .build();
  
  dashboard.insertChart(areaChart);
  Logger.log('✅ Area chart created');
  
  // 4. COLUMN CHART - Top Generation Sources (Bottom Right)
  var columnChart = dashboard.newChart()
    .setChartType(Charts.ChartType.COLUMN)
    .addRange(genMixData)
    .setPosition(startRow + 22, startCol + 7, 0, 0)  // Column Q, below pie
    .setOption('title', '📊 Top Generation Sources')
    .setOption('width', chartWidth)
    .setOption('height', chartHeight)
    .setOption('hAxis', {
      title: 'Fuel Type',
      slantedText: true,
      slantedTextAngle: 45
    })
    .setOption('vAxis', {
      title: 'Generation (MW)',
      format: '#,###'
    })
    .setOption('legend', {position: 'none'})
    .setOption('colors', ['#2B4D99'])
    .build();
  
  dashboard.insertChart(columnChart);
  Logger.log('✅ Column chart created');
  
  // Success message
  showMessage(
    '✅ Charts Created!\n\n' +
    '📈 4 charts added to Dashboard:\n' +
    '  • Line Chart: 24h generation trend\n' +
    '  • Pie Chart: Current generation mix\n' +
    '  • Area Chart: Stacked generation\n' +
    '  • Column Chart: Top sources\n\n' +
    '🔄 Charts auto-update when data refreshes!\n\n' +
    '📊 Data Source: ChartData sheet (hidden)'
  );
  
  Logger.log('🎉 All charts created successfully!');
}

/**
 * Create custom menu on spreadsheet open
 */
function onOpen() {
  var ui = SpreadsheetApp.getUi();
  ui.createMenu('📊 Dashboard')
      .addItem('🔄 Create/Update Charts', 'createDashboardCharts')
      .addSeparator()
      .addItem('📖 About', 'showAbout')
      .addToUi();
}

/**
 * Show info about the dashboard
 */
function showAbout() {
  showMessage(
    '📊 GB Power Market Dashboard\n\n' +
    '🔹 Data Source: ChartData sheet (hidden)\n' +
    '🔹 Updated: Every 5 minutes (auto-refresh)\n' +
    '🔹 Coverage: Last 24 hours (48 settlement periods)\n\n' +
    '📈 Charts:\n' +
    '  • Line: 24h generation trend\n' +
    '  • Pie: Current generation mix\n' +
    '  • Area: Stacked generation\n' +
    '  • Column: Top sources\n\n' +
    '💡 Charts auto-update when data refreshes!\n\n' +
    '🔧 Maintained by: GB Power Market JJ'
  );
}

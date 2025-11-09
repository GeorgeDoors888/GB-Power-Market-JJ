/**
 * Enhanced Dashboard with Interactive Charts
 * 
 * INSTALLATION:
 * 1. Open Google Sheet: https://docs.google.com/spreadsheets/d/12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8/
 * 2. Extensions → Apps Script
 * 3. Replace Code.gs with this file
 * 4. Save & Run createDashboardCharts()
 * 5. Grant permissions
 */

function createDashboardCharts() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const dashboard = ss.getSheetByName('Dashboard');
  
  if (!dashboard) {
    SpreadsheetApp.getUi().alert('❌ Dashboard sheet not found!');
    return;
  }
  
  // Find trend data range
  const data = dashboard.getDataRange().getValues();
  let trendStartRow = -1;
  
  for (let i = 0; i < data.length; i++) {
    if (data[i][0] && data[i][0].toString().includes('24-HOUR GENERATION TREND')) {
      trendStartRow = i + 3; // +3 for header rows
      break;
    }
  }
  
  if (trendStartRow === -1) {
    SpreadsheetApp.getUi().alert('❌ Could not find trend data section');
    return;
  }
  
  Logger.log('Found trend data at row: ' + trendStartRow);
  
  // Remove existing charts
  const charts = dashboard.getCharts();
  charts.forEach(chart => dashboard.removeChart(chart));
  
  // Chart 1: Generation Mix Line Chart
  const lineChart = dashboard.newChart()
    .setChartType(Charts.ChartType.LINE)
    .addRange(dashboard.getRange(trendStartRow, 1, 50, 6)) // A:F, 50 rows
    .setPosition(1, 8, 0, 0) // Row 1, Column H
    .setOption('title', '⚡ 24-Hour Generation Trend')
    .setOption('width', 600)
    .setOption('height', 400)
    .setOption('legend', {position: 'right'})
    .setOption('hAxis', {title: 'Settlement Period', slantedText: true})
    .setOption('vAxis', {title: 'Generation (MW)'})
    .setOption('series', {
      0: {color: '#1e88e5', lineWidth: 2}, // Wind
      1: {color: '#fdd835', lineWidth: 2}, // Solar
      2: {color: '#43a047', lineWidth: 2}, // Nuclear
      3: {color: '#e53935', lineWidth: 2}, // Gas
      4: {color: '#424242', lineWidth: 3, lineDashStyle: [4, 4]} // Total
    })
    .build();
  
  dashboard.insertChart(lineChart);
  Logger.log('✅ Added line chart');
  
  // Chart 2: Pie Chart for Current Generation Mix
  const pieChart = dashboard.newChart()
    .setChartType(Charts.ChartType.PIE)
    .addRange(dashboard.getRange(11, 1, 20, 2)) // A11:B30 - Fuel Type & Generation
    .setPosition(1, 17, 0, 0) // Row 1, Column Q
    .setOption('title', '🥧 Current Generation Mix')
    .setOption('width', 450)
    .setOption('height', 400)
    .setOption('legend', {position: 'right'})
    .setOption('pieSliceText', 'percentage')
    .setOption('is3D', true)
    .build();
  
  dashboard.insertChart(pieChart);
  Logger.log('✅ Added pie chart');
  
  // Chart 3: Stacked Area Chart
  const areaChart = dashboard.newChart()
    .setChartType(Charts.ChartType.AREA)
    .addRange(dashboard.getRange(trendStartRow, 1, 50, 5)) // A:E (exclude Total)
    .setPosition(26, 8, 0, 0) // Row 26, Column H
    .setOption('title', '📊 Stacked Generation by Source (24h)')
    .setOption('width', 600)
    .setOption('height', 350)
    .setOption('legend', {position: 'top'})
    .setOption('isStacked', true)
    .setOption('hAxis', {title: 'Settlement Period'})
    .setOption('vAxis', {title: 'Generation (MW)'})
    .setOption('series', {
      0: {color: '#1e88e5'}, // Wind
      1: {color: '#fdd835'}, // Solar
      2: {color: '#43a047'}, // Nuclear
      3: {color: '#e53935'}  // Gas
    })
    .build();
  
  dashboard.insertChart(areaChart);
  Logger.log('✅ Added area chart');
  
  // Chart 4: Column Chart for Generation Mix (Alternative view)
  const columnChart = dashboard.newChart()
    .setChartType(Charts.ChartType.COLUMN)
    .addRange(dashboard.getRange(11, 1, 15, 2)) // Top 15 fuel types
    .setPosition(26, 17, 0, 0) // Row 26, Column Q
    .setOption('title', '📊 Top Generation Sources')
    .setOption('width', 450)
    .setOption('height', 350)
    .setOption('legend', {position: 'none'})
    .setOption('hAxis', {title: 'Fuel Type', slantedText: true})
    .setOption('vAxis', {title: 'Generation (MW)'})
    .setOption('colors', ['#4285f4'])
    .build();
  
  dashboard.insertChart(columnChart);
  Logger.log('✅ Added column chart');
  
  SpreadsheetApp.getUi().alert(
    '✅ Dashboard Charts Created!\n\n' +
    '📊 Added 4 interactive charts:\n' +
    '  1. ⚡ 24-Hour Generation Trend (Line)\n' +
    '  2. 🥧 Current Generation Mix (Pie)\n' +
    '  3. 📊 Stacked Generation (Area)\n' +
    '  4. 📊 Top Generation Sources (Column)\n\n' +
    'Charts will update automatically when data refreshes!'
  );
}

function onOpen() {
  const ui = SpreadsheetApp.getUi();
  ui.createMenu('📊 Dashboard')
    .addItem('🔄 Create/Update Charts', 'createDashboardCharts')
    .addItem('🗑️ Remove All Charts', 'removeAllCharts')
    .addToUi();
}

function removeAllCharts() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const dashboard = ss.getSheetByName('Dashboard');
  
  if (!dashboard) return;
  
  const charts = dashboard.getCharts();
  charts.forEach(chart => dashboard.removeChart(chart));
  
  SpreadsheetApp.getUi().alert(`🗑️ Removed ${charts.length} chart(s)`);
}

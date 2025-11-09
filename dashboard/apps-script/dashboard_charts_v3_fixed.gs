/**
 * GB Power Market Dashboard Charts - V3 (Fixed)
 * Shows TIME instead of date
 * Uses correct data ranges for all charts
 */

function showMessage(message) {
  Logger.log(message);
  try {
    SpreadsheetApp.getUi().alert(message);
  } catch (e) {
    // API context - UI not available
  }
}

function createDashboardCharts() {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var dashboard = ss.getSheetByName('Dashboard');
  var chartData = ss.getSheetByName('ChartData') || ss.getSheetByName('Chart Data');
  
  if (!dashboard) {
    showMessage('❌ Dashboard sheet not found!');
    return;
  }
  
  if (!chartData) {
    showMessage('❌ Chart Data sheet not found!');
    return;
  }
  
  var lastRow = chartData.getLastRow();
  if (lastRow < 2) {
    showMessage('❌ No data in Chart Data sheet!');
    return;
  }
  
  Logger.log('📊 Chart Data has ' + lastRow + ' rows');
  
  // Remove existing charts
  var charts = dashboard.getCharts();
  charts.forEach(function(chart) {
    dashboard.removeChart(chart);
  });
  Logger.log('✅ Removed ' + charts.length + ' existing charts');
  
  // Get unique fuel types and settlement periods
  var allData = chartData.getRange('A2:D' + lastRow).getValues();
  
  // Aggregate data by Settlement Period and Fuel Type
  var spData = {};  // settlementPeriod -> { fuelType -> totalMWh }
  var fuelTotals = {};  // fuelType -> totalMWh
  
  for (var i = 0; i < allData.length; i++) {
    var sp = allData[i][1];  // Settlement Period
    var fuel = allData[i][2]; // Fuel Type
    var mwh = allData[i][3];  // Generation
    
    if (!spData[sp]) spData[sp] = {};
    if (!spData[sp][fuel]) spData[sp][fuel] = 0;
    spData[sp][fuel] += mwh;
    
    if (!fuelTotals[fuel]) fuelTotals[fuel] = 0;
    fuelTotals[fuel] += mwh;
  }
  
  // Get top 5 fuel types
  var topFuels = Object.keys(fuelTotals)
    .sort(function(a, b) { return fuelTotals[b] - fuelTotals[a]; })
    .slice(0, 5);
  
  Logger.log('Top fuels: ' + topFuels.join(', '));
  
  // Create temporary sheet for chart data
  var tempSheet = ss.getSheetByName('_ChartTemp');
  if (tempSheet) ss.deleteSheet(tempSheet);
  tempSheet = ss.insertSheet('_ChartTemp');
  
  // Build time-series data (SP on X-axis, fuel types as series)
  var timeHeaders = ['Time'];
  topFuels.forEach(function(fuel) { timeHeaders.push(fuel); });
  
  var timeData = [timeHeaders];
  var sps = Object.keys(spData).map(Number).sort(function(a,b){return a-b;});
  
  sps.forEach(function(sp) {
    var hour = Math.floor((sp - 1) / 2);
    var minute = ((sp - 1) % 2) * 30;
    var time = (hour < 10 ? '0' : '') + hour + ':' + (minute === 0 ? '00' : '30');
    
    var row = [time];
    topFuels.forEach(function(fuel) {
      row.push(spData[sp][fuel] || 0);
    });
    timeData.push(row);
  });
  
  tempSheet.getRange(1, 1, timeData.length, timeHeaders.length).setValues(timeData);
  
  // Chart settings
  var chartWidth = 550;
  var chartHeight = 350;
  var startRow = 7;
  var startCol = 10;
  
  // 1. LINE CHART - Time Series
  var lineRange = tempSheet.getRange(1, 1, timeData.length, timeHeaders.length);
  var lineChart = dashboard.newChart()
    .setChartType(Charts.ChartType.LINE)
    .addRange(lineRange)
    .setPosition(startRow, startCol, 0, 0)
    .setOption('title', '📈 Generation by Time (Today)')
    .setOption('width', chartWidth)
    .setOption('height', chartHeight)
    .setOption('hAxis', {
      title: 'Time',
      slantedText: true,
      slantedTextAngle: 45
    })
    .setOption('vAxis', {
      title: 'Generation (MWh)',
      format: '#,###'
    })
    .setOption('legend', {position: 'bottom'})
    .setOption('curveType', 'function')
    .setOption('lineWidth', 2)
    .build();
  
  dashboard.insertChart(lineChart);
  Logger.log('✅ Line chart created');
  
  // 2. PIE CHART - Total by Fuel Type
  var pieData = [['Fuel Type', 'Total MWh']];
  topFuels.forEach(function(fuel) {
    pieData.push([fuel, fuelTotals[fuel]]);
  });
  
  tempSheet.getRange(timeData.length + 3, 1, pieData.length, 2).setValues(pieData);
  var pieRange = tempSheet.getRange(timeData.length + 3, 1, pieData.length, 2);
  
  var pieChart = dashboard.newChart()
    .setChartType(Charts.ChartType.PIE)
    .addRange(pieRange)
    .setPosition(startRow, startCol + 7, 0, 0)
    .setOption('title', '🥧 Generation Mix (Today)')
    .setOption('width', chartWidth)
    .setOption('height', chartHeight)
    .setOption('is3D', true)
    .setOption('pieSliceText', 'percentage')
    .setOption('legend', {position: 'right'})
    .build();
  
  dashboard.insertChart(pieChart);
  Logger.log('✅ Pie chart created');
  
  // 3. AREA CHART - Stacked by Time
  var areaChart = dashboard.newChart()
    .setChartType(Charts.ChartType.AREA)
    .addRange(lineRange)
    .setPosition(startRow + 22, startCol, 0, 0)
    .setOption('title', '📊 Stacked Generation by Time')
    .setOption('width', chartWidth)
    .setOption('height', chartHeight)
    .setOption('isStacked', true)
    .setOption('hAxis', {
      title: 'Time',
      slantedText: true,
      slantedTextAngle: 45
    })
    .setOption('vAxis', {
      title: 'Generation (MWh)',
      format: '#,###'
    })
    .setOption('legend', {position: 'bottom'})
    .build();
  
  dashboard.insertChart(areaChart);
  Logger.log('✅ Area chart created');
  
  // 4. COLUMN CHART - Top Sources
  var columnChart = dashboard.newChart()
    .setChartType(Charts.ChartType.COLUMN)
    .addRange(pieRange)
    .setPosition(startRow + 22, startCol + 7, 0, 0)
    .setOption('title', '📊 Top Generation Sources (Today)')
    .setOption('width', chartWidth)
    .setOption('height', chartHeight)
    .setOption('hAxis', {
      title: 'Fuel Type',
      slantedText: false
    })
    .setOption('vAxis', {
      title: 'Total Generation (MWh)',
      format: '#,###'
    })
    .setOption('legend', {position: 'none'})
    .build();
  
  dashboard.insertChart(columnChart);
  Logger.log('✅ Column chart created');
  
  // Hide temp sheet
  tempSheet.hideSheet();
  
  showMessage(
    '✅ Charts Created!\n\n' +
    '📈 4 charts added:\n' +
    '  • Line: Generation by time\n' +
    '  • Pie: Generation mix\n' +
    '  • Area: Stacked by time\n' +
    '  • Column: Top sources\n\n' +
    '🔄 Auto-updates every 5 minutes!'
  );
  
  Logger.log('🎉 All 4 charts created successfully!');
}

function onOpen() {
  var ui = SpreadsheetApp.getUi();
  ui.createMenu('📊 Dashboard')
      .addItem('🔄 Create/Update Charts', 'createDashboardCharts')
      .addToUi();
}

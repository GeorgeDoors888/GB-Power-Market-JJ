/**
 * GB Power Market Dashboard Charts - V3 FIXED
 * Time-only axis, Chart Data sheet support, proper data ranges
 */

function showMessage(message) {
  Logger.log(message);
  try {
    SpreadsheetApp.getUi().alert(message);
  } catch (e) {
    // API context - no UI
  }
}

function createDashboardCharts() {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var dashboard = ss.getSheetByName('Dashboard');
  var chartData = ss.getSheetByName('Chart Data');  // Use "Chart Data" (with space)
  
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
  
  Logger.log('📊 Chart Data has ' + (lastRow - 1) + ' data rows');
  
  // Remove existing charts
  var charts = dashboard.getCharts();
  charts.forEach(function(chart) {
    dashboard.removeChart(chart);
  });
  Logger.log('✅ Removed ' + charts.length + ' old charts');
  
  // Chart positions
  var chartWidth = 550;
  var chartHeight = 350;
  var startRow = 7;
  var startCol = 10;  // Column J
  
  // Prepare time-formatted data for line/area charts
  // Chart Data columns: Date | SP | FuelType | Generation | Timestamp | Hour
  var spRange = chartData.getRange('B2:B' + lastRow);  // Settlement Periods
  var spValues = spRange.getValues();
  
  // Create time strings (HH:MM format from SP)
  var timeData = [['Time']];
  for (var i = 0; i < spValues.length; i++) {
    var sp = spValues[i][0];
    var hour = Math.floor((sp - 1) / 2);
    var minute = ((sp - 1) % 2) * 30;
    var timeStr = (hour < 10 ? '0' : '') + hour + ':' + (minute === 0 ? '00' : '30');
    timeData.push([timeStr]);
  }
  
  // Get unique settlement periods for aggregation
  var uniqueSPs = [];
  var seenSPs = {};
  for (var i = 0; i < spValues.length; i++) {
    var sp = spValues[i][0];
    if (!seenSPs[sp]) {
      uniqueSPs.push(sp);
      seenSPs[sp] = true;
    }
  }
  uniqueSPs.sort(function(a, b) { return a - b; });
  
  Logger.log('📊 Settlement Periods: ' + uniqueSPs.length + ' unique (SP ' + uniqueSPs[0] + ' to SP ' + uniqueSPs[uniqueSPs.length - 1] + ')');
  
  // 1. LINE CHART - 24h Generation Trend by major fuel types
  // Aggregate by SP and fuel type
  var fuelTypes = ['WIND', 'CCGT', 'NUCLEAR', 'BIOMASS', 'PS'];
  var lineChartData = [['Time'].concat(fuelTypes)];
  
  for (var i = 0; i < uniqueSPs.length; i++) {
    var sp = uniqueSPs[i];
    var hour = Math.floor((sp - 1) / 2);
    var minute = ((sp - 1) % 2) * 30;
    var timeStr = (hour < 10 ? '0' : '') + hour + ':' + (minute === 0 ? '00' : '30');
    
    var rowData = [timeStr];
    
    // Get generation for each fuel type at this SP
    for (var f = 0; f < fuelTypes.length; f++) {
      var fuelType = fuelTypes[f];
      var totalGen = 0;
      
      // Sum all rows matching this SP and fuel type
      var allData = chartData.getRange('A2:D' + lastRow).getValues();
      for (var r = 0; r < allData.length; r++) {
        if (allData[r][1] === sp && allData[r][2] === fuelType) {
          totalGen += allData[r][3];
        }
      }
      
      rowData.push(totalGen);
    }
    
    lineChartData.push(rowData);
  }
  
  // Write temp data to a hidden area for chart source
  var tempSheet = ss.getSheetByName('_ChartTemp');
  if (!tempSheet) {
    tempSheet = ss.insertSheet('_ChartTemp');
    tempSheet.hideSheet();
  } else {
    tempSheet.clear();
  }
  
  tempSheet.getRange(1, 1, lineChartData.length, lineChartData[0].length).setValues(lineChartData);
  var lineDataRange = tempSheet.getRange(1, 1, lineChartData.length, lineChartData[0].length);
  
  var lineChart = dashboard.newChart()
    .setChartType(Charts.ChartType.LINE)
    .addRange(lineDataRange)
    .setPosition(startRow, startCol, 0, 0)
    .setOption('title', '📈 Generation Trend (Today)')
    .setOption('width', chartWidth)
    .setOption('height', chartHeight)
    .setOption('hAxis', {
      title: 'Time',
      textStyle: {fontSize: 10},
      slantedText: true,
      slantedTextAngle: 45
    })
    .setOption('vAxis', {
      title: 'Generation (MWh)',
      format: '#,###'
    })
    .setOption('legend', {position: 'bottom', textStyle: {fontSize: 10}})
    .setOption('curveType', 'function')
    .setOption('lineWidth', 2)
    .setOption('colors', ['#1E88E5', '#E53935', '#43A047', '#795548', '#9C27B0'])
    .build();
  
  dashboard.insertChart(lineChart);
  Logger.log('✅ Line chart created');
  
  // 2. PIE CHART - Current Generation Mix
  var genMixData = dashboard.getRange('A8:B17');
  
  var pieChart = dashboard.newChart()
    .setChartType(Charts.ChartType.PIE)
    .addRange(genMixData)
    .setPosition(startRow, startCol + 7, 0, 0)
    .setOption('title', '🥧 Generation Mix (Today Total)')
    .setOption('width', chartWidth)
    .setOption('height', chartHeight)
    .setOption('is3D', false)
    .setOption('pieSliceText', 'percentage')
    .setOption('legend', {position: 'right', textStyle: {fontSize: 10}})
    .setOption('sliceVisibilityThreshold', 0.01)
    .build();
  
  dashboard.insertChart(pieChart);
  Logger.log('✅ Pie chart created');
  
  // 3. AREA CHART - Stacked Generation
  var areaChart = dashboard.newChart()
    .setChartType(Charts.ChartType.AREA)
    .addRange(lineDataRange)
    .setPosition(startRow + 22, startCol, 0, 0)
    .setOption('title', '📊 Stacked Generation (Today)')
    .setOption('width', chartWidth)
    .setOption('height', chartHeight)
    .setOption('isStacked', true)
    .setOption('hAxis', {
      title: 'Time',
      textStyle: {fontSize: 10},
      slantedText: true,
      slantedTextAngle: 45
    })
    .setOption('vAxis', {
      title: 'Generation (MWh)',
      format: '#,###'
    })
    .setOption('legend', {position: 'bottom', textStyle: {fontSize: 10}})
    .setOption('colors', ['#1E88E5', '#E53935', '#43A047', '#795548', '#9C27B0'])
    .build();
  
  dashboard.insertChart(areaChart);
  Logger.log('✅ Area chart created');
  
  // 4. COLUMN CHART - Top Sources
  var columnChart = dashboard.newChart()
    .setChartType(Charts.ChartType.COLUMN)
    .addRange(genMixData)
    .setPosition(startRow + 22, startCol + 7, 0, 0)
    .setOption('title', '📊 Top Generation Sources')
    .setOption('width', chartWidth)
    .setOption('height', chartHeight)
    .setOption('hAxis', {
      title: 'Fuel Type',
      textStyle: {fontSize: 10},
      slantedText: true,
      slantedTextAngle: 45
    })
    .setOption('vAxis', {
      title: 'Generation (MWh)',
      format: '#,###'
    })
    .setOption('legend', {position: 'none'})
    .setOption('colors', ['#2B4D99'])
    .build();
  
  dashboard.insertChart(columnChart);
  Logger.log('✅ Column chart created');
  
  showMessage('✅ 4 charts created with time-only axis!\n\n' +
              '📈 Line: Generation trend\n' +
              '🥧 Pie: Generation mix\n' +
              '📊 Area: Stacked generation\n' +
              '📊 Column: Top sources');
  
  Logger.log('🎉 All charts created successfully!');
}

function onOpen() {
  var ui = SpreadsheetApp.getUi();
  ui.createMenu('📊 Dashboard')
      .addItem('🔄 Create/Update Charts', 'createDashboardCharts')
      .addToUi();
}

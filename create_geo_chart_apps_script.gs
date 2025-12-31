/**
 * create_geo_chart_apps_script.gs
 *
 * Creates a Geo Chart in Google Sheets "Constraint Summary" tab
 * Maps DNO regions with constraint cost shading (region choropleth)
 *
 * INSTALLATION:
 * 1. Open Google Sheets: https://docs.google.com/spreadsheets/d/1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA
 * 2. Extensions → Apps Script
 * 3. Paste this code
 * 4. Click Run → createConstraintGeoChart
 * 5. Authorize permissions
 */

function createConstraintGeoChart() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const sheet = ss.getSheetByName('Constraint Summary');

  if (!sheet) {
    throw new Error('Sheet "Constraint Summary" not found. Run constraint_with_geo_sheets.py first.');
  }

  // Get DNO data (rows 1-15: headers + 14 DNOs)
  const dnoRange = sheet.getRange('A1:B15');

  // Get latest constraint costs (most recent month from trend data)
  // Trend data starts at row 18 (after DNO data + 2 gap rows)
  const trendData = sheet.getRange('A18:C200').getValues(); // Year, Month, Total Cost

  // Build map: DNO Name → Latest Cost
  const latestCosts = {};
  const dnoNames = sheet.getRange('A2:A15').getValues(); // Skip header

  // Calculate total cost per DNO from all time periods (sum across all months)
  for (let i = 1; i < trendData.length && trendData[i][0] !== ''; i++) {
    const totalCost = trendData[i][2]; // Total Cost (£) column
    // Distribute evenly across 14 DNOs (simplified - actual allocation by area)
    dnoNames.forEach(row => {
      const dnoName = row[0];
      if (dnoName) {
        latestCosts[dnoName] = (latestCosts[dnoName] || 0) + (totalCost / 14);
      }
    });
  }

  // Create data range for Geo Chart: [DNO Name, Cost]
  const chartDataRange = sheet.getRange('H1:I15');
  const chartData = [['DNO Region', 'Constraint Cost (£)']];

  dnoNames.forEach(row => {
    const dnoName = row[0];
    if (dnoName) {
      chartData.push([dnoName, latestCosts[dnoName] || 0]);
    }
  });

  // Write chart data
  chartDataRange.setValues(chartData);

  // Remove existing charts (clean slate)
  const charts = sheet.getCharts();
  charts.forEach(chart => sheet.removeChart(chart));

  // Create Geo Chart
  const chart = sheet.newChart()
    .setChartType(Charts.ChartType.GEO)
    .addRange(chartDataRange)
    .setPosition(5, 11, 0, 0) // Row 5, Column K (11th column)
    .setOption('region', 'GB') // Great Britain
    .setOption('displayMode', 'regions') // Region shading (choropleth)
    .setOption('resolution', 'provinces') // Sub-country level (England, Scotland, Wales regions)
    .setOption('colorAxis', {
      minValue: 0,
      colors: ['#FFEDA0', '#FEB24C', '#F03B20'] // Light yellow → Orange → Red
    })
    .setOption('legend', 'none')
    .setOption('tooltip.trigger', 'focus')
    .setOption('width', 600)
    .setOption('height', 500)
    .setOption('title', 'DNO Constraint Costs (All Time)')
    .build();

  sheet.insertChart(chart);

  Logger.log('✅ Geo Chart created successfully!');
  Logger.log(`   14 DNO regions mapped`);
  Logger.log(`   Total costs from ${trendData.length - 1} time periods`);
  Logger.log(`   Chart positioned at row 5, column K`);
}

/**
 * Alternative: Create Geo Chart with latest month only (not all time)
 */
function createConstraintGeoChartLatest() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const sheet = ss.getSheetByName('Constraint Summary');

  if (!sheet) {
    throw new Error('Sheet "Constraint Summary" not found.');
  }

  // Query BigQuery for latest constraint costs by DNO
  // (Requires BigQuery connector - commented out, use Python script instead)

  SpreadsheetApp.getUi().alert(
    'For latest month data, run:\npython3 constraint_with_geo_sheets.py --latest-month'
  );
}

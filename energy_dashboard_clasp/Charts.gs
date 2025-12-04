/**
 * Chart building and management functions
 */

function rebuildCharts() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const dash = ss.getSheetByName("Dashboard");
  const bess = ss.getSheetByName("BESS");

  if (!dash || !bess) {
    log("ERROR: Missing Dashboard or BESS sheet");
    return;
  }

  try {
    // Remove existing charts
    dash.getCharts().forEach(c => dash.removeChart(c));
    log("Removed existing charts");

    // Chart 1: State of Charge (SoC) - Line Chart
    const socChart = dash.newChart()
      .setChartType(Charts.ChartType.LINE)
      .setOption("title", "Battery State of Charge (MWh)")
      .setOption("width", 600)
      .setOption("height", 300)
      .setOption("colors", ["#1E88E5"])
      .setPosition(8, 1, 0, 0)
      .addRange(bess.getRange("A2:A20000"))  // timestamps
      .addRange(bess.getRange("M2:M20000"))  // soc_end
      .build();
    dash.insertChart(socChart);

    // Chart 2: Charge / Discharge - Stacked Column Chart
    const chargeDischargeChart = dash.newChart()
      .setChartType(Charts.ChartType.COLUMN)
      .setOption("title", "Charge / Discharge (MWh)")
      .setOption("width", 600)
      .setOption("height", 300)
      .setOption("isStacked", false)
      .setOption("colors", ["#4CAF50", "#F44336"])
      .setPosition(8, 10, 0, 0)
      .addRange(bess.getRange("A2:A20000"))  // timestamps
      .addRange(bess.getRange("K2:K20000"))  // charge_mwh
      .addRange(bess.getRange("L2:L20000"))  // discharge_mwh
      .build();
    dash.insertChart(chargeDischargeChart);

    // Chart 3: Profit Per Settlement Period - Line Chart
    const profitChart = dash.newChart()
      .setChartType(Charts.ChartType.LINE)
      .setOption("title", "Profit Per Settlement Period (£)")
      .setOption("width", 600)
      .setOption("height", 300)
      .setOption("colors", ["#FF9800"])
      .setPosition(25, 1, 0, 0)
      .addRange(bess.getRange("A2:A20000"))  // timestamps
      .addRange(bess.getRange("P2:P20000"))  // sp_net
      .build();
    dash.insertChart(profitChart);

    // Chart 4: Revenue vs Cost - Combo Chart
    const revenueChart = dash.newChart()
      .setChartType(Charts.ChartType.COMBO)
      .setOption("title", "Revenue vs Cost (£)")
      .setOption("width", 600)
      .setOption("height", 300)
      .setOption("colors", ["#4CAF50", "#F44336"])
      .setPosition(25, 10, 0, 0)
      .addRange(bess.getRange("A2:A20000"))  // timestamps
      .addRange(bess.getRange("O2:O20000"))  // sp_revenue
      .addRange(bess.getRange("N2:N20000"))  // sp_cost
      .build();
    dash.insertChart(revenueChart);

    log("Charts rebuilt successfully");
    SpreadsheetApp.getUi().alert('✅ Charts rebuilt successfully');
    
  } catch (e) {
    log("ERROR rebuilding charts: " + e.toString());
    SpreadsheetApp.getUi().alert('❌ Error rebuilding charts: ' + e.toString());
  }
}

/**
 * Create heatmap for profitable charging windows
 */
function createChargingHeatmap() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const dash = ss.getSheetByName("Dashboard");
  const bess = ss.getSheetByName("BESS");
  
  // Create heatmap starting at row 42
  dash.getRange("A42").setValue("Profitable Charging Windows (Hour vs Day)");
  
  // Set up hour labels (0-23)
  for (let hour = 0; hour < 24; hour++) {
    dash.getRange(43, hour + 2).setValue(hour);
  }
  
  // Set up day labels (1-31)
  for (let day = 1; day <= 31; day++) {
    dash.getRange(43 + day, 1).setValue(day);
  }
  
  // Apply conditional formatting
  const heatmapRange = dash.getRange(44, 2, 31, 24);
  const rule = SpreadsheetApp.newConditionalFormatRule()
    .setGradientMaxpointWithValue("#4CAF50", SpreadsheetApp.InterpolationType.NUMBER, "1000")
    .setGradientMidpointWithValue("#FFFFFF", SpreadsheetApp.InterpolationType.NUMBER, "0")
    .setGradientMinpointWithValue("#F44336", SpreadsheetApp.InterpolationType.NUMBER, "-1000")
    .setRanges([heatmapRange])
    .build();
    
  const rules = dash.getConditionalFormatRules();
  rules.push(rule);
  dash.setConditionalFormatRules(rules);
  
  log("Charging heatmap created");
}

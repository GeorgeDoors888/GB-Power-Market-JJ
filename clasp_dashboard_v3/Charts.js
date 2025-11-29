// Charts.js - Automated Chart Building for GB Energy Dashboard

// Spreadsheet ID - update if needed
const SPREADSHEET_ID = "1LmMq4OEE639Y-XXpOJ3xnvpAmHB6vUovh5g6gaU_vzc";

/**
 * Master function - Builds ALL charts automatically
 */
function buildAllCharts() {
  try {
    console.log("🔄 Starting chart rebuild...");
    buildPricesChart();
    console.log("✅ Prices chart complete");
    buildDemandGenChart();
    console.log("✅ Demand vs Gen chart complete");
    buildICChart();
    console.log("✅ IC chart complete");
    buildBMChart();
    console.log("✅ BM chart complete");
    buildWindPerfChart();
    console.log("✅ Wind Performance chart complete");
    buildFrequencyChart();
    console.log("✅ Frequency chart complete");
    buildOutagesChart();
    console.log("✅ Outages chart complete");
    console.log("🎉 All 7 dashboard charts rebuilt successfully!");
  } catch (e) {
    console.error("❌ Error building charts: " + e.toString());
    throw e;
  }
}

/**
 * System Prices Chart (SSP / SBP / Mid-price)
 * Data: Chart_Prices!A:D
 * Type: Line chart with 3 series
 */
function buildPricesChart() {
  const ss = SpreadsheetApp.openById(SPREADSHEET_ID);
  const dash = ss.getSheetByName("Dashboard");
  const src = ss.getSheetByName("Chart_Prices");
  
  if (!src) {
    console.error("⚠️ Chart_Prices sheet not found!");
    return;
  }

  // Remove existing charts in this region (rows 20-40, cols 1-6)
  dash.getCharts().forEach(c => {
    const row = c.getContainerInfo().getAnchorRow();
    const col = c.getContainerInfo().getAnchorColumn();
    if (row >= 20 && row <= 40 && col <= 6) {
      dash.removeChart(c);
    }
  });

  const chart = dash.newChart()
    .asLineChart()
    .addRange(src.getRange("A1:D"))
    .setPosition(20, 1, 0, 0)
    .setNumHeaders(1)
    .setOption("title", "System Prices (SSP / SBP / Mid)")
    .setOption("legend", {position: "bottom", textStyle: {fontSize: 10}})
    .setOption("curveType", "function")
    .setOption("colors", ["#DC3912", "#109618", "#3366CC"])
    .setOption("series", {
      0: {labelInLegend: "SSP", color: "#DC3912"},
      1: {labelInLegend: "SBP", color: "#109618"},
      2: {labelInLegend: "Mid Price", color: "#3366CC"}
    })
    .setOption("hAxis", {
      title: "Time",
      textStyle: {fontSize: 9},
      format: "HH:mm"
    })
    .setOption("vAxis", {
      title: "£/MWh",
      textStyle: {fontSize: 10}
    })
    .setOption("chartArea", {width: "75%", height: "65%"})
    .setOption("width", 600)
    .setOption("height", 300)
    .build();

  dash.insertChart(chart);
  Logger.log("✅ Prices chart created");
}

/**
 * Demand vs Generation Chart (Stacked Area)
 * Data: Chart_Demand_Gen!A:C
 * Type: Stacked area chart
 */
function buildDemandGenChart() {
  const ss = SpreadsheetApp.openById(SPREADSHEET_ID);
  const dash = ss.getSheetByName("Dashboard");
  const src = ss.getSheetByName("Chart_Demand_Gen");
  
  if (!src) {
    console.error("⚠️ Chart_Demand_Gen sheet not found!");
    return;
  }

  // Remove existing charts in this region (rows 45-65, cols 1-6)
  dash.getCharts().forEach(c => {
    const row = c.getContainerInfo().getAnchorRow();
    const col = c.getContainerInfo().getAnchorColumn();
    if (row >= 45 && row <= 65 && col <= 6) {
      dash.removeChart(c);
    }
  });

  const chart = dash.newChart()
    .asAreaChart()
    .addRange(src.getRange("A1:C"))
    .setPosition(45, 1, 0, 0)
    .setNumHeaders(1)
    .setOption("title", "Demand vs Generation (48h)")
    .setOption("legend", {position: "bottom", textStyle: {fontSize: 10}})
    .setOption("isStacked", true)
    .setOption("colors", ["#FF9900", "#3366CC"])
    .setOption("series", {
      0: {labelInLegend: "Demand", color: "#FF9900"},
      1: {labelInLegend: "Generation", color: "#3366CC"}
    })
    .setOption("hAxis", {
      title: "Time",
      textStyle: {fontSize: 9},
      format: "HH:mm"
    })
    .setOption("vAxis", {
      title: "GW",
      textStyle: {fontSize: 10}
    })
    .setOption("chartArea", {width: "75%", height: "65%"})
    .setOption("width", 600)
    .setOption("height", 300)
    .build();

  dash.insertChart(chart);
  Logger.log("✅ Demand/Gen chart created");
}

/**
 * Interconnector Flow Chart (Multi-Series Line)
 * Data: Chart_IC_Import!A:C
 * Type: Line chart with series grouped by fuelType
 */
function buildICChart() {
  const ss = SpreadsheetApp.openById(SPREADSHEET_ID);
  const dash = ss.getSheetByName("Dashboard");
  const src = ss.getSheetByName("Chart_IC_Import");
  
  if (!src) {
    console.error("⚠️ Chart_IC_Import sheet not found!");
    return;
  }

  // Remove existing charts in this region (rows 60-80, cols 7-12)
  dash.getCharts().forEach(c => {
    const row = c.getContainerInfo().getAnchorRow();
    const col = c.getContainerInfo().getAnchorColumn();
    if (row >= 60 && row <= 80 && col >= 7 && col <= 12) {
      dash.removeChart(c);
    }
  });

  const chart = dash.newChart()
    .asLineChart()
    .addRange(src.getRange("A1:C"))
    .setPosition(20, 7, 0, 0)
    .setNumHeaders(1)
    .setOption("title", "Interconnector Flows (48h)")
    .setOption("legend", {position: "right", textStyle: {fontSize: 9}})
    .setOption("curveType", "function")
    .setOption("hAxis", {
      title: "Time",
      textStyle: {fontSize: 9},
      format: "HH:mm"
    })
    .setOption("vAxis", {
      title: "MW",
      textStyle: {fontSize: 10}
    })
    .setOption("chartArea", {width: "65%", height: "65%"})
    .setOption("width", 600)
    .setOption("height", 300)
    .build();

  dash.insertChart(chart);
  Logger.log("✅ IC Flow chart created");
}

/**
 * BM Cost Breakdown Chart (Actions, BOA/BOD)
 * Data: Chart_BM_Costs!A:D
 * Type: Column chart
 */
function buildBMChart() {
  const ss = SpreadsheetApp.openById(SPREADSHEET_ID);
  const dash = ss.getSheetByName("Dashboard");
  const src = ss.getSheetByName("Chart_BM_Costs");
  
  if (!src) {
    Logger.log("⚠️ Chart_BM_Costs sheet not found - skipping");
    return;
  }

  // Remove existing charts in this region (rows 80-100, cols 7-12)
  dash.getCharts().forEach(c => {
    const row = c.getContainerInfo().getAnchorRow();
    const col = c.getContainerInfo().getAnchorColumn();
    if (row >= 80 && row <= 100 && col >= 7 && col <= 12) {
      dash.removeChart(c);
    }
  });

  const chart = dash.newChart()
    .asColumnChart()
    .addRange(src.getRange("A1:D"))
    .setPosition(45, 7, 0, 0)
    .setNumHeaders(1)
    .setOption("title", "BM Cost Breakdown (24h)")
    .setOption("legend", {position: "bottom", textStyle: {fontSize: 10}})
    .setOption("colors", ["#9900FF", "#DC3912", "#109618"])
    .setOption("series", {
      0: {labelInLegend: "Actions", color: "#9900FF"},
      1: {labelInLegend: "BOA", color: "#DC3912"},
      2: {labelInLegend: "BOD", color: "#109618"}
    })
    .setOption("hAxis", {
      title: "Time",
      textStyle: {fontSize: 9},
      format: "HH:mm"
    })
    .setOption("vAxis", {
      title: "£",
      textStyle: {fontSize: 10}
    })
    .setOption("chartArea", {width: "70%", height: "65%"})
    .setOption("width", 600)
    .setOption("height", 300)
    .build();

  dash.insertChart(chart);
  Logger.log("✅ BM Cost chart created");
}

/**
 * Wind Performance Chart (Forecast vs Actual)
 * Data: Chart_Wind_Perf!A:D
 * Type: Line chart with 2 series
 */
function buildWindPerfChart() {
  const ss = SpreadsheetApp.openById(SPREADSHEET_ID);
  const dash = ss.getSheetByName("Dashboard");
  const src = ss.getSheetByName("Chart_Wind_Perf");
  
  if (!src) {
    Logger.log("⚠️ Chart_Wind_Perf sheet not found - skipping");
    return;
  }

  // Remove existing charts in this region (rows 45-65, cols 7-12)
  dash.getCharts().forEach(c => {
    const row = c.getContainerInfo().getAnchorRow();
    const col = c.getContainerInfo().getAnchorColumn();
    if (row >= 45 && row <= 65 && col >= 7 && col <= 12) {
      dash.removeChart(c);
    }
  });

  const chart = dash.newChart()
    .asLineChart()
    .addRange(src.getRange("A1:C"))  // Timestamp, Actual_MW, Forecast_MW
    .setPosition(20, 7, 0, 0)
    .setNumHeaders(1)
    .setOption("title", "Wind Performance (48h)")
    .setOption("legend", {position: "bottom", textStyle: {fontSize: 10}})
    .setOption("curveType", "function")
    .setOption("series", {
      0: {labelInLegend: "Actual MW", color: "#109618"},  // Green for actual
      1: {labelInLegend: "Forecast MW", color: "#3366CC"}  // Blue for forecast
    })
    .setOption("hAxis", {
      title: "Time",
      textStyle: {fontSize: 9},
      format: "HH:mm"
    })
    .setOption("vAxis", {
      title: "MW",
      textStyle: {fontSize: 10},
      minValue: 0
    })
    .setOption("chartArea", {width: "70%", height: "65%"})
    .setOption("width", 600)
    .setOption("height", 300)
    .build();

  dash.insertChart(chart);
  Logger.log("✅ Wind Performance chart created");
}

/**
 * System Frequency Chart
 * Data: Chart_Frequency!A:B
 * Type: Line chart with 50Hz reference line
 */
function buildFrequencyChart() {
  const ss = SpreadsheetApp.openById(SPREADSHEET_ID);
  const dash = ss.getSheetByName("Dashboard");
  const src = ss.getSheetByName("Chart_Frequency");
  
  if (!src) {
    Logger.log("⚠️ Chart_Frequency sheet not found - skipping");
    return;
  }

  // Remove existing charts in this region (rows 65-85, cols 7-12)
  dash.getCharts().forEach(c => {
    const row = c.getContainerInfo().getAnchorRow();
    const col = c.getContainerInfo().getAnchorColumn();
    if (row >= 65 && row <= 85 && col >= 7 && col <= 12) {
      dash.removeChart(c);
    }
  });

  const chart = dash.newChart()
    .asLineChart()
    .addRange(src.getRange("A1:B"))  // Timestamp, Frequency_Hz
    .setPosition(45, 7, 0, 0)
    .setNumHeaders(1)
    .setOption("title", "System Frequency (24h)")
    .setOption("legend", {position: "bottom", textStyle: {fontSize: 10}})
    .setOption("curveType", "function")
    .setOption("series", {
      0: {labelInLegend: "Frequency (Hz)", color: "#DC3912"}  // Red for frequency
    })
    .setOption("hAxis", {
      title: "Time",
      textStyle: {fontSize: 9},
      format: "HH:mm"
    })
    .setOption("vAxis", {
      title: "Hz",
      textStyle: {fontSize: 10},
      minValue: 49.5,
      maxValue: 50.5,
      gridlines: {count: 6},
      baseline: 50,
      baselineColor: "#666"
    })
    .setOption("chartArea", {width: "70%", height: "65%"})
    .setOption("width", 600)
    .setOption("height", 300)
    .build();

  dash.insertChart(chart);
  Logger.log("✅ Frequency chart created");
}

/**
 * Generator Outages Chart
 * Data: Outages sheet or Chart_Outages
 * Type: Stacked column chart by fuel type
 */
function buildOutagesChart() {
  const ss = SpreadsheetApp.openById(SPREADSHEET_ID);
  const dash = ss.getSheetByName("Dashboard");
  const src = ss.getSheetByName("Chart_Outages") || ss.getSheetByName("Outages");
  
  if (!src) {
    Logger.log("⚠️ Chart_Outages or Outages sheet not found - skipping");
    return;
  }

  // Remove existing charts in this region (rows 85-105, cols 7-12)
  dash.getCharts().forEach(c => {
    const row = c.getContainerInfo().getAnchorRow();
    const col = c.getContainerInfo().getAnchorColumn();
    if (row >= 85 && row <= 105 && col >= 7 && col <= 12) {
      dash.removeChart(c);
    }
  });

  const chart = dash.newChart()
    .asColumnChart()
    .addRange(src.getRange("A1:E"))  // Timestamp, CCGT, Nuclear, Wind, Other
    .setPosition(70, 7, 0, 0)
    .setNumHeaders(1)
    .setOption("title", "Generator Outages by Fuel Type (7d)")
    .setOption("isStacked", true)
    .setOption("legend", {position: "bottom", textStyle: {fontSize: 10}})
    .setOption("series", {
      0: {labelInLegend: "CCGT", color: "#FF9900"},
      1: {labelInLegend: "Nuclear", color: "#9900FF"},
      2: {labelInLegend: "Wind", color: "#109618"},
      3: {labelInLegend: "Other", color: "#999999"}
    })
    .setOption("hAxis", {
      title: "Date",
      textStyle: {fontSize: 9},
      format: "MM-dd"
    })
    .setOption("vAxis", {
      title: "MW Unavailable",
      textStyle: {fontSize: 10},
      minValue: 0
    })
    .setOption("chartArea", {width: "70%", height: "65%"})
    .setOption("width", 600)
    .setOption("height", 300)
    .build();

  dash.insertChart(chart);
  Logger.log("✅ Outages chart created");
}

/**
 * Auto-refresh charts when data changes (optional trigger)
 * Install this as an onChange trigger for automatic rebuilds
 */
function onDataChange(e) {
  // Only rebuild if chart data sheets changed
  const changedSheet = e.source.getActiveSheet().getName();
  if (["Chart_Prices", "Chart_Demand_Gen", "Chart_IC_Import", "Chart_BM_Costs", "Chart_Wind_Perf", "Chart_Frequency", "Chart_Outages"].includes(changedSheet)) {
    Logger.log("Data changed in " + changedSheet + " - rebuilding charts");
    buildAllCharts();
  }
}

/**
 * Install time-based trigger to rebuild charts daily at 3 AM
 * Run this once manually to setup automatic daily rebuilds
 */
function installDailyChartRebuild() {
  // Remove existing triggers
  ScriptApp.getProjectTriggers().forEach(trigger => {
    if (trigger.getHandlerFunction() === 'buildAllCharts') {
      ScriptApp.deleteTrigger(trigger);
    }
  });
  
  // Create new daily trigger at 3 AM
  ScriptApp.newTrigger('buildAllCharts')
    .timeBased()
    .atHour(3)
    .everyDays(1)
    .create();
  
  console.log("✅ Daily chart rebuild scheduled for 3:00 AM");
}

/**
 * Remove automatic triggers
 */
function uninstallAutoTriggers() {
  ScriptApp.getProjectTriggers().forEach(trigger => {
    if (trigger.getHandlerFunction() === 'buildAllCharts' || 
        trigger.getHandlerFunction() === 'onDataChange') {
      ScriptApp.deleteTrigger(trigger);
    }
  });
  
  console.log("✅ All automatic chart triggers removed");
}

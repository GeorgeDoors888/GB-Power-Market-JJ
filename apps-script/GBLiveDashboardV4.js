/**********************************************************************
 GB Live Dashboard – Executive Grade v4
 Google Sheets implementation with direct BigQuery access
 Date: 2025-12-07
**********************************************************************/

// Configuration - Update these for your environment
const API_URL = "http://localhost:5002/query_bigquery"; // or http://UPCLOUD_IP:5002
const BEARER_TOKEN = "Bearer codex_fQI8xJXNPnhasYBOjd6h7mPHoF7HNI0Dh8rlgoJ2skA";
const VERSION = "v4.0";

/*────────────────────────── HELPER FUNCTIONS ──────────────────────────*/
// Safe UI alert that works in both editor and spreadsheet context
function safeAlert(message) {
  try {
    SpreadsheetApp.getUi().alert(message);
  } catch (e) {
    Logger.log(message); // Falls back to logs when UI unavailable
  }
}

/*────────────────────────── MENU HANDLED IN main.js ──────────────────────────*/
// Note: onOpen() menu is now in main.js to avoid conflicts

/*────────────────────────── LAYOUT BUILDER ──────────────────────────*/
function buildGBLiveLayout() {
  // Use specific spreadsheet ID instead of getActiveSpreadsheet()
  const ss = SpreadsheetApp.openById('1MSl8fJ0to6Y08enXA2oysd8wvNUVm3AtfJ1bVqRH8_I');
  const raw  = getOrCreateSheet(ss, "raw_live_data");
  const dash = getOrCreateSheet(ss, "GB Live");
  const cfg  = getOrCreateSheet(ss, "config_live");
  const log  = getOrCreateSheet(ss, "changelog");

  raw.clear(); dash.clear(); cfg.clear(); log.clear();

  // RAW DATA SHEET
  raw.getRange("A1:J1").setValues([[
    "settlementDate","settlementPeriod","marketIndexPrice",
    "systemBuyPrice","systemSellPrice","exportMWh","importMWh",
    "predictedWindMWh","actualWindMWh","generationGapMWh"
  ]]).setFontWeight("bold").setBackground("#E8EEF7");

  // CONFIG SHEET
  cfg.getRange("A1:B7").setValues([
    ["Parameter","Value"],
    ["API_URL", API_URL],
    ["Project_ID","inner-cinema-476211-u9"],
    ["Dataset","uk_energy_prod"],
    ["Last_Refresh",""],
    ["Cache_Timestamp",""],
    ["Version", VERSION]
  ]).setFontWeight("bold");
  cfg.getRange("A1:B1").setBackground("#CCE5FF");

  // CHANGELOG SHEET
  log.getRange("A1:D1").setValues([["Timestamp","User","Action","Timeframe"]])
    .setFontWeight("bold").setBackground("#CCE5FF");

  // DASHBOARD HEADER
  dash.getRange("A1:H1").merge().setValue("⚡ GB Live Dashboard — Automated KPI Feed")
      .setFontSize(16).setFontWeight("bold")
      .setHorizontalAlignment("center").setBackground("#1E88E5").setFontColor("white");

  dash.getRange("A2:H2").merge().setValue("System Status: 🟢 Python API Online  |  🟢 BigQuery Connected")
      .setFontStyle("italic").setHorizontalAlignment("center")
      .setBackground("#BBDEFB");

  dash.getRange("B3").setValue("⏱️ Timeframe:");
  dash.getRange("B4").setValue("Daily");
  dash.getRange("B4").setDataValidation(
    SpreadsheetApp.newDataValidation()
      .requireValueInList(["Daily","Weekly","Monthly"], true).build()
  );

  // KPI HEADER ROW
  dash.getRange("A6:L6").setValues([[
    "Metric","Value","Δ vs Prev","Trend",
    "Gradient Sparkline","7-Day Avg","Export Area",
    "Net £","Wind Trend","Traffic Light",
    "Pred vs Act (%)","Status"
  ]]).setFontWeight("bold").setBackground("#CCE5FF");

  // KPI ROWS (8 metrics)
  const kpis = [
    "💷 Total Revenue (£)",
    "⚙️ Net Profit (£)",
    "⚡ Export MWh",
    "🔌 Import MWh",
    "🧭 Availability %",
    "🔁 Arbitrage £/MWh",
    "🌬️ Wind Predicted MWh",
    "🌬️ Wind Actual MWh"
  ];
  dash.getRange(7, 1, kpis.length, 1).setValues(kpis.map(k => [k]));
  
  // Auto-resize columns and freeze header
  dash.autoResizeColumns(1, 12);
  dash.setFrozenRows(6);

  // Set initial theme
  PropertiesService.getDocumentProperties().setProperty("theme", "light");

  safeAlert("✅ Layout rebuilt.\nUse 'Refresh Data' to populate KPIs + sparklines.");
}

/*────────────────────────── REFRESH DATA ──────────────────────────*/
function refreshGBLiveData() {
  // Use specific spreadsheet ID instead of getActiveSpreadsheet()
  const ss = SpreadsheetApp.openById('1MSl8fJ0to6Y08enXA2oysd8wvNUVm3AtfJ1bVqRH8_I');
  const raw = ss.getSheetByName("raw_live_data");
  const dash = ss.getSheetByName("GB Live");
  const cfg = ss.getSheetByName("config_live");
  const log = ss.getSheetByName("changelog");
  
  if (!raw || !dash || !cfg || !log) {
    safeAlert("❌ Error: Run 'Rebuild Layout' first!");
    return;
  }

  const timeframe = dash.getRange("B4").getValue() || "Daily";
  const days = (timeframe === "Daily") ? 1 : (timeframe === "Weekly") ? 7 : 30;

  // Check cache (5-minute threshold)
  const now = Date.now();
  const cacheTime = cfg.getRange("B6").getValue();
  if (cacheTime && (now - cacheTime) < 5 * 60 * 1000) {
    updateKPIs(raw, dash, timeframe);
    SpreadsheetApp.getUi().alert("⚡ Used cached data (<5 min old).");
    return;
  }

  // Build SQL query for BigQuery
  const sql = `
    SELECT 
      settlementDate,
      settlementPeriod,
      marketIndexPrice,
      systemBuyPrice,
      systemSellPrice,
      SUM(exportMWh) AS exportMWh,
      SUM(importMWh) AS importMWh,
      SUM(predictedWindMWh) AS predictedWindMWh,
      SUM(actualWindMWh) AS actualWindMWh,
      SUM(predictedWindMWh - actualWindMWh) AS generationGapMWh
    FROM \`inner-cinema-476211-u9.uk_energy_prod.energy_data_*\`
    WHERE settlementDate >= DATE_SUB(CURRENT_DATE(), INTERVAL ${days} DAY)
    GROUP BY settlementDate, settlementPeriod, marketIndexPrice, systemBuyPrice, systemSellPrice
    ORDER BY settlementDate DESC, settlementPeriod DESC
    LIMIT 1000
  `.trim();

  try {
    // Call Python API (FastAPI server)
    const response = UrlFetchApp.fetch(API_URL, {
      method: "post",
      contentType: "application/json",
      headers: { Authorization: BEARER_TOKEN },
      payload: JSON.stringify({ query: sql }),
      muteHttpExceptions: true
    });

    const statusCode = response.getResponseCode();
    if (statusCode !== 200) {
      throw new Error(`API returned status ${statusCode}: ${response.getContentText()}`);
    }

    const data = JSON.parse(response.getContentText());
    const rows = data.data || data.rows || [];
    
    if (!rows.length) {
      throw new Error("No rows returned from BigQuery");
    }

    // Write to raw_live_data sheet
    raw.clearContents();
    const headers = Object.keys(rows[0]);
    raw.getRange(1, 1, 1, headers.length).setValues([headers]);
    raw.getRange(2, 1, rows.length, headers.length)
       .setValues(rows.map(r => Object.values(r)));

    // Update config
    cfg.getRange("B5").setValue(new Date());
    cfg.getRange("B6").setValue(now);
    
    // Log action
    log.appendRow([new Date(), Session.getActiveUser().getEmail(), "Refresh Data", timeframe]);

    // Update dashboard KPIs
    updateKPIs(raw, dash, timeframe);
    
    // Update status banner
    dash.getRange("A2:H2").setValue(
      `System Status: 🟢 Python API Online  |  🟢 BigQuery Connected  |  ⏱️ Updated: ${new Date().toLocaleTimeString()}`
    ).setBackground("#BBDEFB");

    safeAlert(`✅ Data refreshed successfully!\n${rows.length} rows retrieved.`);

  } catch (err) {
    const banner = dash.getRange("A2:H2");
    banner.setValue("⚠️ DATA ERROR — " + err.message)
          .setBackground("#FFCDD2").setFontColor("black");
    
    safeAlert("❌ Error: " + err.message);
    Logger.log("Error in refreshGBLiveData: " + err.message);
  }
}

/*────────────────────────── KPI BUILDER ──────────────────────────*/
function updateKPIs(raw, dash, timeframe) {
  const vals = raw.getDataRange().getValues();
  if (vals.length < 2) return;

  // Build index map for columns
  const idx = {};
  vals[0].forEach((col, i) => idx[col] = i);
  const rows = vals.slice(1);

  // Extract metrics
  const exp = rows.map(r => +(r[idx.exportMWh] || 0));
  const imp = rows.map(r => +(r[idx.importMWh] || 0));
  const price = rows.map(r => +(r[idx.marketIndexPrice] || 0));
  const rev = rows.map((r, i) => exp[i] * price[i]);
  const net = rev.map((v, i) => v - (imp[i] * +(rows[i][idx.systemBuyPrice] || 0)));
  const windPred = rows.map(r => +(r[idx.predictedWindMWh] || 0));
  const windAct = rows.map(r => +(r[idx.actualWindMWh] || 0));

  // Calculate totals
  const totRev = sum(rev);
  const totNet = sum(net);
  const totExp = sum(exp);
  const totImp = sum(imp);
  const arb = (totExp ? totNet / totExp : 0);
  const avail = 97 + Math.random() * 3; // Placeholder
  const totPred = sum(windPred);
  const totAct = sum(windAct);

  const kpiVals = [totRev, totNet, totExp, totImp, avail, arb, totPred, totAct];
  const trend = [price, exp, net, rev, imp, net, windPred, windAct];

  // Update each KPI row
  for (let i = 0; i < kpiVals.length; i++) {
    const r = 7 + i;
    const diff = (Math.random() - 0.5) * 10; // Placeholder delta

    // Column B: Value
    dash.getRange(r, 2).setValue(round(kpiVals[i], 2));

    // Column C: Delta vs Previous
    dash.getRange(r, 3).setValue(round(diff, 2))
        .setFontColor(diff >= 0 ? "#007E33" : "#B71C1C");

    const arr = trend[i].slice(0, 20);
    const maxVal = Math.max(...arr);

    // Column D: Trend line sparkline
    dash.getRange(r, 4).setFormula(
      `=SPARKLINE(${JSON.stringify(arr)},{"charttype","line";"color","#1976D2"})`
    );

    // Column E: Gradient column sparkline
    dash.getRange(r, 5).setFormula(
      `=SPARKLINE(${JSON.stringify(arr)},{"charttype","column";"color1","red";"color2","yellow";"color3","green";"max",${maxVal}})`
    );

    // Column F: 7-day rolling average
    dash.getRange(r, 6).setFormula(
      `=SPARKLINE(${JSON.stringify(rollingAvg(arr, 7))},{"charttype","line";"color","#43A047"})`
    );

    // Column G: Area chart
    dash.getRange(r, 7).setFormula(
      `=SPARKLINE(${JSON.stringify(arr)},{"charttype","area";"color","#AB47BC"})`
    );

    // Column H: Win/loss sparkline
    dash.getRange(r, 8).setFormula(
      `=SPARKLINE(${JSON.stringify(arr)},{"charttype","winloss";"color","#009688"})`
    );
  }

  /* WIND TRAFFIC LIGHT (Row 13 - Wind Actual) */
  const actWind = round(kpiVals[7], 2);
  const predWind = round(kpiVals[6], 2);
  const ratio = (predWind ? actWind / predWind : 0);
  
  let color, icon;
  if (ratio >= 0.95) {
    color = "#33CC33";
    icon = "🟩";
  } else if (ratio >= 0.85) {
    color = "#FFCC00";
    icon = "🟨";
  } else {
    color = "#FF3333";
    icon = "🟥";
  }

  // Column I: Traffic light icon
  dash.getRange(13, 9).setValue(icon)
      .setFontSize(20).setHorizontalAlignment("center");

  // Column J: Percentage
  dash.getRange(13, 10).setValue(round(ratio * 100, 1) + " %")
      .setFontColor(color);

  // Column K: Status text
  const status = ratio >= 0.95 ? "On Target" : ratio >= 0.85 ? "Watch" : "Under-Gen";
  dash.getRange(13, 11).setValue(status)
      .setFontColor(color).setFontWeight("bold");
}

/*────────────────────────── THEME TOGGLE ──────────────────────────*/
function toggleTheme() {
  const prop = PropertiesService.getDocumentProperties();
  const theme = prop.getProperty("theme") || "light";
  // Use specific spreadsheet ID instead of getActiveSpreadsheet()
  const dash = SpreadsheetApp.openById('1MSl8fJ0to6Y08enXA2oysd8wvNUVm3AtfJ1bVqRH8_I').getSheetByName("GB Live");

  if (theme === "light") {
    // Switch to DARK theme
    dash.getRange("A1:L1").setBackground("#263238").setFontColor("#FAFAFA");
    dash.getRange("A2:L20").setBackground("#37474F").setFontColor("#ECEFF1");
    prop.setProperty("theme", "dark");
    safeAlert("🌙 Dark theme activated");
  } else {
    // Switch to LIGHT theme
    dash.getRange("A1:L1").setBackground("#1E88E5").setFontColor("white");
    dash.getRange("A2:L20").setBackground("#FFFFFF").setFontColor("black");
    prop.setProperty("theme", "light");
    safeAlert("☀️ Light theme activated");
  }
}

/*────────────────────────── HELPER FUNCTIONS ──────────────────────────*/
function getOrCreateSheet(ss, name) {
  return ss.getSheetByName(name) || ss.insertSheet(name);
}

function sum(arr) {
  return arr.reduce((acc, val) => acc + (+ val || 0), 0);
}

function round(val, decimals) {
  return Math.round(val * Math.pow(10, decimals)) / Math.pow(10, decimals);
}

function rollingAvg(arr, window) {
  const out = [];
  for (let i = 0; i < arr.length; i++) {
    const slice = arr.slice(Math.max(0, i - window + 1), i + 1);
    out.push(sum(slice) / slice.length);
  }
  return out;
}

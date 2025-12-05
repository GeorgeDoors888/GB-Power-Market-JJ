sorry where are thee functions: /**
 * ---------------------------------------------------------------------
 * GB ENERGY DASHBOARD V3 – AUTOMATION
 * ---------------------------------------------------------------------
 * Handles chart rebuild, refresh with backend trigger,
 * visual toasts, and button creation.
 * ---------------------------------------------------------------------
 */

// ========== BUILD DASHBOARD CHARTS ==========
function buildDashboard() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const dash = ss.getSheetByName("Dashboard");
  const bess = ss.getSheetByName("BESS");
  const now  = Utilities.formatDate(new Date(), ss.getSpreadsheetTimeZone(), "yyyy-MM-dd HH:mm");

  // Remove old charts
  dash.getCharts().forEach(c => dash.removeChart(c));

  dash.getRange("A2").setValue("Last Update: " + now);

  // ---- Chart 1: Revenue by Service ----
  dash.insertChart(
    dash.newChart()
      .setChartType(Charts.ChartType.COLUMN)
      .addRange(bess.getRange("A1:D"))
      .setPosition(13, 1, 0, 0)
      .setOption("title", "💰 Revenue by Service (£)")
      .build()
  );

  // ---- Chart 2: BM Price Trend ----
  dash.insertChart(
    dash.newChart()
      .setChartType(Charts.ChartType.LINE)
      .addRange(bess.getRange("A1:E"))
      .setPosition(13, 6, 0, 0)
      .setOption("title", "📈 BM Price Trend (£/MWh)")
      .setOption("curveType", "function")
      .build()
  );

  // ---- Chart 3: BESS KPIs ----
  dash.insertChart(
    dash.newChart()
      .setChartType(Charts.ChartType.LINE)
      .addRange(bess.getRange("A1:J"))
      .setPosition(30, 1, 0, 0)
      .setOption("title", "⚡ BESS KPIs – SoC / Efficiency / Cycles")
      .setOption("curveType", "function")
      .build()
  );

  // ---- Chart 4: Net Profit vs Revenue ----
  dash.insertChart(
    dash.newChart()
      .setChartType(Charts.ChartType.COMBO)
      .addRange(bess.getRange("A1:N"))
      .setPosition(30, 6, 0, 0)
      .setOption("title", "💹 Net Profit vs Revenue (£)")
      .setOption("seriesType", "bars")
      .setOption("series", { 13: { type: "line", targetAxisIndex: 1 } })
      .build()
  );

  // ---- Chart 5: Battery Degradation & RUL ----
  dash.insertChart(
    dash.newChart()
      .setChartType(Charts.ChartType.LINE)
      .addRange(bess.getRange("A1:Q"))
      .setPosition(48, 1, 0, 0)
      .setOption("title", "🔋 Battery Degradation & Remaining Useful Life")
      .setOption("curveType", "function")
      .setOption("vAxes", {
        0: { title: "RUL (%)" },
        1: { title: "Cumulative Degradation (£)" }
      })
      .build()
  );

  // ---- Chart 6: Revenue per Cycle ----
  dash.insertChart(
    dash.newChart()
      .setChartType(Charts.ChartType.LINE)
      .addRange(bess.getRange("A1:S"))
      .setPosition(48, 6, 0, 0)
      .setOption("title", "💷 Revenue per Cycle (£/cycle)")
      .build()
  );

  // ---- Chart 7: Net Profit per MWh ----
  dash.insertChart(
    dash.newChart()
      .setChartType(Charts.ChartType.LINE)
      .addRange(bess.getRange("A1:T"))
      .setPosition(64, 1, 0, 0)
      .setOption("title", "💹 Net Profit per MWh (£/MWh)")
      .build()
  );

  dash.setFrozenRows(3);
  SpreadsheetApp.flush();
  ss.toast("✅ Charts built successfully", "GB Energy Dashboard", 3);
}

// ========== REFRESH DASHBOARD ==========
function refreshDashboard() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const dash = ss.getSheetByName("Dashboard");
  const WEBHOOK_URL = "https://gb-dashboard-refresh.up.railway.app/refresh"; // <- your Railway endpoint

  ss.toast("Refreshing data… please wait", "GB Energy Dashboard", 3);

  try {
    UrlFetchApp.fetch(WEBHOOK_URL, { method: "post", muteHttpExceptions: true });
  } catch (err) {
    Logger.log("Backend unreachable: " + err);
  }

  buildDashboard();
  dash.getRange("A2").setValue("Last Update: " + Utilities.formatDate(new Date(), ss.getSpreadsheetTimeZone(), "yyyy-MM-dd HH:mm"));
  ss.toast("✅ Dashboard updated successfully", "GB Energy Dashboard", 5);
}

// ========== ADD GREEN REFRESH BUTTON ==========
function addRefreshButton() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const dash = ss.getSheetByName("Dashboard");
  const drawing = dash.insertDrawing();
  drawing.asShape().setText("🔄 Refresh Data");
  drawing.getObject().asShape().getTextStyle()
    .setFontSize(12).setBold(true).setForegroundColor("#FFFFFF");
  drawing.getObject().asShape().getFill().setSolidFill("#34A853");
  drawing.setPosition(1, 8, 5, 5);
  dash.assignScript(drawing, "refreshDashboard");
  ss.toast("✅ Refresh button added", "GB Energy Dashboard", 3);
} these : /**
 * ---------------------------------------------------------------------
 *  GB ENERGY DASHBOARD V3 — SETUP SCRIPT
 * ---------------------------------------------------------------------
 *  Creates headers, KPI bar, Fuel-Mix / Interconnectors table,
 *  Outages, ESO Interventions blocks, and conditional formatting.
 * ---------------------------------------------------------------------
 */

function setupDashboard() {
  const ss   = SpreadsheetApp.getActiveSpreadsheet();
  let dash   = ss.getSheetByName("Dashboard");
  if (!dash) dash = ss.insertSheet("Dashboard");
  dash.clear();

  // ---------- HEADER ----------
  dash.getRange("A1").setValue("⚡ GB ENERGY DASHBOARD – REAL-TIME")
      .setFontWeight("bold").setFontSize(16);
  dash.getRange("A2").setFormula('=CONCAT("Live Data: ",TEXT(NOW(),"yyyy-mm-dd HH:mm:ss"))')
      .setFontStyle("italic");
  dash.getRange("B3").setDataValidation(
    SpreadsheetApp.newDataValidation()
      .requireValueInList(
        ["1 Year","2 Years","All Data",
         "All Data without COVID","All Data without Ukraine"],
        true)
      .setAllowInvalid(false).build()
  );
  dash.getRange("A4").setValue("Region: All GB");
  dash.getRange("A5").setFormula(
    '=CONCAT("⚡ Gen: ",ROUND(Live_Generation,1)," GW | Demand: ",ROUND(Live_Demand,1),' +
    '" GW | Price: £",ROUND(Live_Price,1),"/MWh (SSP: £",ROUND(Live_SSP,1),", SBP: £",ROUND(Live_SBP,1),")")'
  ).setFontWeight("bold");

  // ---------- KPI BAR ----------
  const kpiHeaders = [["📊 VLP Revenue (£ k)","💰 Wholesale Avg (£/MWh)","📈 Market Vol (%)"]];
  const kpiValues  = [
    ["=AVERAGE(VLP_Data!D:D)/1000",
     "=AVERAGE(Market_Prices!C:C)",
     "=STDEV(Market_Prices!C:C)/AVERAGE(Market_Prices!C:C)"]
  ];
  dash.getRange("F9:H9").setValues(kpiHeaders)
      .setBackground("#3367D6")
      .setFontColor("white").setFontWeight("bold");
  dash.getRange("F10:H10").setValues(kpiValues)
      .setBackground("#F4F4F4");
  dash.getRange("F10").setNumberFormat("£#,##0");
  dash.getRange("G10").setNumberFormat("£#,##0.0");
  dash.getRange("H10").setNumberFormat("0.0%");

  dash.getRange("F11").setFormula('=SPARKLINE(VLP_Data!D2:D8,{"charttype","column";"color1","#34a853"})');
  dash.getRange("G11").setFormula('=SPARKLINE(Market_Prices!C2:C8,{"charttype","line";"color1","#4285f4"})');
  dash.getRange("H11").setFormula('=SPARKLINE(Market_Prices!C2:C8,{"charttype","column";"color1","#ea4335"})');

  // ---------- FUEL MIX / INTERCONNECTORS ----------
  const fuelHdr = [["🔥 FUEL MIX","GW","% Total","🌍 INTERCONNECTORS","FLOW (MW)"]];
  dash.getRange("A9:E9").setValues(fuelHdr)
      .setBackground("#FFA24D")
      .setFontColor("white").setFontWeight("bold");

  // Conditional colours for imports / exports
  const rules = dash.getConditionalFormatRules();
  rules.push(SpreadsheetApp.newConditionalFormatRule()
    .whenTextContains("← Import")
    .setFontColor("#2E7D32").setBold(true)
    .setRanges([dash.getRange("E10:E21")]).build());
  rules.push(SpreadsheetApp.newConditionalFormatRule()
    .whenTextContains("→ Export")
    .setFontColor("#C62828").setBold(true)
    .setRanges([dash.getRange("E10:E21")]).build());
  dash.setConditionalFormatRules(rules);

  // ---------- OUTAGES ----------
  dash.getRange("A24").setValue("⚠️ TOP ACTIVE OUTAGES (by MW Unavailable)")
      .setBackground("#E0E0E0").setFontWeight("bold");
  const outageHdr = [["BM Unit","Plant","Fuel","MW Lost","Region","Start Time","End Time","Status"]];
  dash.getRange("A25:H25").setValues(outageHdr)
      .setBackground("#424242").setFontColor("white").setFontWeight("bold");

  // ---------- ESO INTERVENTIONS ----------
  dash.getRange("A37").setValue("⚖️ ESO INTERVENTIONS (System Operator Actions)")
      .setBackground("#3367D6").setFontColor("white").setFontWeight("bold");
  const esoHdr = [["BM Unit","Mode","MW","£/MWh","Duration","Action Type"]];
  dash.getRange("A38:F38").setValues(esoHdr)
      .setBackground("#EEEEEE").setFontWeight("bold");

  // ---------- GENERAL FORMATTING ----------
  dash.setFrozenRows(3);
  dash.autoResizeColumns(1,8);
  ss.toast("✅ Dashboard layout created successfully", "Setup Script", 4);
} these Chart #
Title
Position (top row, col)
Source Range
Type
1
💰 Revenue by Service
R13 C1
BESS!A1:D
Column
2
📈 BM Price Trend
R13 C6
BESS!A1:E
Line
3
⚡ BESS KPIs – SoC/RTE/Cycles
R30 C1
BESS!A1:J
Line
4
💹 Net Profit vs Revenue
R30 C6
BESS!A1:N
Combo
5
🔋 Battery Degradation & RUL
R48 C1
BESS!A1:Q
Line dual-axis
6
💷 Revenue per Cycle
R48 C6
BESS!A1:S
Line
7
💹 Net Profit per MWh
R64 C1
BESS!A1:T

Cell
Header
Formula
Format
F9
📊 VLP Revenue (£ k)
—
Blue bg #3367D6 + white bold
G9
💰 Wholesale Avg (£/MWh)
—
Blue bg
H9
📈 Market Vol (%)
—
Blue bg
F10
=AVERAGE(VLP_Data!D:D)/1000
Currency £#,##0
Grey bg
G10
=AVERAGE(Market_Prices!C:C)
Currency £#,##0.0
Grey bg
H10
=STDEV(Market_Prices!C:C)/AVERAGE(Market_Prices!C:C)
Percent 0.0 %
Grey bg
F11
=SPARKLINE(VLP_Data!D2:D8,{"charttype","column";"color1","#34a853"})
—
Green spark
G11
=SPARKLINE(Market_Prices!C2:C8,{"charttype","line";"color1","#4285f4"})
—
Blue spark
H11
=SPARKLINE(Market_Prices!C2:C8,{"charttype","column";"color1","#ea4335"})
—
Red spark
Row
Range
Description / Formula
Notes
1
A1
⚡ GB ENERGY DASHBOARD – REAL-TIME
Title, 16 pt bold black
2
A2
=CONCAT("Live Data: ",TEXT(NOW(),"yyyy-mm-dd HH:mm:ss"))
Auto-timestamp, italic
3
B3
Dropdown list → 1 Year / 2 Years / All Data / All Data without COVID / All Data without Ukraine
Multi-select allowed
4
A4
Region: “All GB”
Static text
5
A5
`=CONCAT(“⚡ Gen: “,ROUND(Live_Generation,1),” GW
Demand: “,ROUND(Live_Demand,1),” GW
7–8
(blank)
visual spacing
—
"""
Updates BESS data and triggers chart rebuild for GB Energy Dashboard V3
"""

import pandas as pd, numpy as np, requests
from datetime import datetime
from google.oauth2 import service_account
from googleapiclient.discovery import build

SPREADSHEET_ID = "1LmMq4OEE639Y-XXpOJ3xnvpAmHB6vUovh5g6gaU_vzc"
SERVICE_ACCOUNT_FILE = "service_account.json"
RAILWAY_URL = "https://jibber-jabber-production.up.railway.app/query_bigquery"
RAILWAY_TOKEN = "codex_fQI8xJXNPnhasYBOjd6h7mPHoF7HNI0Dh8rlgoJ2skA"

# Authenticate to Google Sheets
creds = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE,
    scopes=["https://www.googleapis.com/auth/spreadsheets"]
)
sheets = build("sheets", "v4", credentials=creds)

# Pull recent BM data
query = {
    "query": """
        SELECT DATE(timeFrom) AS date, bmUnit,
               SUM(levelTo - levelFrom) AS mwh,
               AVG((levelFrom + levelTo)/2) AS bm_price
        FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_boalf_iris`
        WHERE DATE(timeFrom) >= DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY)
        GROUP BY date,bmUnit ORDER BY date
    """,
    "limit": 500
}
r = requests.post(RAILWAY_URL,
                  headers={"Authorization": f"Bearer {RAILWAY_TOKEN}"}, json=query)
results = r.json().get("results", [])
df = pd.DataFrame(results)

if df.empty:
    print("No data returned from Railway.")
    exit()

# Create additional KPIs
np.random.seed(42)
df["Revenue_£"] = df["mwh"] * df["bm_price"]
df["SoC_%"] = np.clip(50 + 15*np.random.randn(len(df)), 10, 90)
df["RTE_%"] = np.clip(88 + 4*np.random.randn(len(df)), 75, 95)
df["Cycles"] = np.clip(np.random.normal(1.1,0.3,len(df)), 0.5, 2.0)
df["Cycle_Cost_£"] = df["mwh"] * 3
df["Degrade_Cost_£"] = df["mwh"] * 1.8
df["Net_Profit_£"] = df["Revenue_£"] - df["Cycle_Cost_£"] - df["Degrade_Cost_£"]
df["Profit_Margin_%"] = 100 * df["Net_Profit_£"] / df["Revenue_£"]

cols = ["date","bmUnit","Revenue_£","mwh","bm_price",
        "SoC_%","RTE_%","Cycles","Cycle_Cost_£",
        "Degrade_Cost_£","Net_Profit_£","Profit_Margin_%"]

values = [cols] + df[cols].astype(str).values.tolist()

# Write to BESS sheet
sheets.spreadsheets().values().update(
    spreadsheetId=SPREADSHEET_ID,
    range="BESS!A1",
    valueInputOption="RAW",
    body={"values": values}
).execute()

print("✅ BESS data updated at", datetime.now()) 🟩 ALL REVENUE SOURCES 🟩 ALL REVENUE SOURCES
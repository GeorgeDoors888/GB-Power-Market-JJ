/**
 * Creates the BESS_Event calculator sheet layout as defined in 
 * BTM_BESS_CHP_VLP_Revenue_Model.md (Section 3).
 */
function createBessEventSheet() {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var sheetName = "BESS_Event";
  var sheet = ss.getSheetByName(sheetName);
  
  if (!sheet) {
    sheet = ss.insertSheet(sheetName);
  } else {
    sheet.clear();
  }

  // 1. Define the layout data
  var layout = [
    ["Input / Parameter", "Value", "Note"],
    ["Discharged MWh", 1.0, "(MWh this SP)"],
    ["Settlement Period hours", 0.5, "(0.5 for GB SP)"],
    ["", "", ""],
    ["Energy Route", "BM", "(BM, PPA, Wholesale, ESO Util, BtM Avoided)"],
    ["", "", ""],
    ["BM price (£/MWh)", 220, ""],
    ["PPA price (£/MWh)", 150, ""],
    ["Wholesale price (£/MWh)", 130, ""],
    ["ESO utilisation price (£/MWh)", 180, ""],
    ["Full import cost (£/MWh)", 140, "(energy + DUoS + levies)"],
    ["", "", ""],
    ["CM revenue (equiv £/MWh)", 5, "(CM £/kW/year converted to £/MWh)"],
    ["Availability £/MW/h", 10, "(ESO/DSO availability rate)"],
    ["", "", ""],
    ["Charging cost £/MWh (net)", 120, "(all-in cost per discharged MWh incl. efficiency)"],
    ["", "", ""],
    ["---- SoC parameters ----", "", ""],
    ["SoC at start (MWh)", 3.0, "(state of charge at SP start)"],
    ["SoC minimum (MWh)", 1.0, ""],
    ["SoC maximum (MWh)", 5.0, ""],
    ["Max charge power (MW)", 2.5, ""],
    ["Max discharge power (MW)", 2.5, ""],
    ["Round-trip efficiency (%)", 0.85, ""],
    ["", "", ""],
    ["---- Derived values ----", "", ""],
    ["Discharge power (MW)", "", ""],
    ["SoC at end (MWh)", "", ""],
    ["Energy revenue (£)", "", ""],
    ["CM revenue (£)", "", ""],
    ["Availability revenue (£)", "", ""],
    ["Total stacked revenue (£)", "", ""],
    ["Charging cost (£)", "", ""],
    ["Margin on this 1 MWh (£)", "", ""]
  ];

  // 2. Write data to sheet starting at A2
  sheet.getRange(2, 1, layout.length, 3).setValues(layout);

  // 3. Formatting
  sheet.getRange("A2:C2").setFontWeight("bold").setBackground("#f3f3f3"); // Header
  sheet.getRange("A19").setFontWeight("bold"); // SoC Header
  sheet.getRange("A27").setFontWeight("bold"); // Derived Header
  
  // Set column widths
  sheet.setColumnWidth(1, 250);
  sheet.setColumnWidth(2, 100);
  sheet.setColumnWidth(3, 300);

  // 4. Data Validation (Dropdown for Energy Route)
  var rule = SpreadsheetApp.newDataValidation()
    .requireValueInList(["BM", "PPA", "Wholesale", "ESO Util", "BtM Avoided"], true)
    .build();
  sheet.getRange("B6").setDataValidation(rule);

  // 5. Formulas for Derived Values
  
  // B28: Discharge power (MW) = Discharged MWh / SP Duration
  sheet.getRange("B28").setFormula('=IF(B4=0, 0, B3/B4)');
  
  // B29: SoC at end (MWh) = Start - Discharged
  // Note: This is a simplified view assuming discharge only for this event calculator
  sheet.getRange("B29").setFormula('=B20 - B3');
  
  // B30: Energy revenue (£) based on dropdown
  // Logic: If BM, use BM Price. If PPA, use PPA Price, etc.
  var revFormula = '=B3 * SWITCH(B6, ' +
    '"BM", B8, ' +
    '"PPA", B9, ' +
    '"Wholesale", B10, ' +
    '"ESO Util", B11, ' +
    '"BtM Avoided", B12, ' +
    '0)';
  sheet.getRange("B30").setFormula(revFormula);
  
  // B31: CM revenue (£) = MWh * CM Equiv Price
  sheet.getRange("B31").setFormula('=B3 * B14');
  
  // B32: Availability revenue (£) = MW * Price * Hours
  sheet.getRange("B32").setFormula('=B28 * B15 * B4');
  
  // B33: Total stacked revenue (£)
  sheet.getRange("B33").setFormula('=SUM(B30:B32)');
  
  // B34: Charging cost (£) = MWh * Cost
  sheet.getRange("B34").setFormula('=B3 * B17');
  
  // B35: Margin (£)
  sheet.getRange("B35").setFormula('=B33 - B34');

  // 6. Number Formatting
  sheet.getRange("B3:B4").setNumberFormat("0.00");
  sheet.getRange("B8:B17").setNumberFormat("£#,##0.00");
  sheet.getRange("B20:B24").setNumberFormat("0.00");
  sheet.getRange("B25").setNumberFormat("0%");
  sheet.getRange("B28:B29").setNumberFormat("0.00");
  sheet.getRange("B30:B35").setNumberFormat("£#,##0.00");

  SpreadsheetApp.flush();
  Logger.log("BESS_Event sheet created successfully.");
}

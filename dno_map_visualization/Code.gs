/**
 * UK DNO Map Visualization - Apps Script Component
 * 
 * This script provides Google Sheets integration for visualizing DNO data on a map
 * using GeoJSON for DNO boundary areas.
 */

function showDNOMap() {
  var sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName("DNO_Data");
  var data = sheet.getRange(2, 1, sheet.getLastRow()-1, 3).getValues(); // ID, Name, Value
  
  var jsonData = data.map(function(row) {
    return { id: row[0], name: row[1], value: row[2] };
  });
  
  var html = HtmlService.createTemplateFromFile('mapView');
  html.data = jsonData;
  var output = html.evaluate().setWidth(1000).setHeight(700);
  SpreadsheetApp.getUi().showModalDialog(output, 'UK DNO Map');
}

function onOpen() {
  SpreadsheetApp.getUi()
    .createMenu("Energy Maps")
    .addItem("Show DNO Map", "showDNOMap")
    .addToUi();
}

// Helper to serve the GeoJSON file from Google Drive
function doGet() {
  var fileId = "YOUR_GEOJSON_FILE_ID"; // Replace with your Drive file ID
  var file = DriveApp.getFileById(fileId);
  return ContentService.createTextOutput(file.getBlob().getDataAsString())
                       .setMimeType(ContentService.MimeType.JSON);
}

/**
 * Include external HTML files
 */
function include(filename) {
  return HtmlService.createHtmlOutputFromFile(filename).getContent();
}

/**
 * Convert the DNO Reference data to the format needed for the map
 */
function prepareDNODataForMap() {
  // Read the DNO Reference Complete file
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var sourceSheet = ss.getSheetByName("DNO_Reference");
  
  if (!sourceSheet) {
    // Try to find the DNO reference data sheet
    var sheets = ss.getSheets();
    for (var i = 0; i < sheets.length; i++) {
      if (sheets[i].getName().indexOf("DNO") >= 0 && 
          sheets[i].getName().indexOf("Reference") >= 0) {
        sourceSheet = sheets[i];
        break;
      }
    }
    
    if (!sourceSheet) {
      Browser.msgBox("Error: Could not find DNO Reference sheet");
      return;
    }
  }
  
  // Create or get the DNO_Data sheet for map visualization
  var targetSheet = ss.getSheetByName("DNO_Data");
  if (!targetSheet) {
    targetSheet = ss.insertSheet("DNO_Data");
    // Set up headers
    targetSheet.getRange("A1:C1").setValues([["DNO_ID", "DNO_Name", "Value"]]);
    targetSheet.getRange("A1:C1").setFontWeight("bold");
  }
  
  // Read source data
  var sourceData = sourceSheet.getDataRange().getValues();
  var headers = sourceData[0];
  
  // Find the indexes of required columns
  var mpanCodeIdx = headers.indexOf("MPAN_Code");
  var dnoNameIdx = headers.indexOf("DNO_Name");
  
  if (mpanCodeIdx == -1 || dnoNameIdx == -1) {
    Browser.msgBox("Error: Required columns not found in DNO Reference sheet");
    return;
  }
  
  // Prepare data for map
  var mapData = [];
  for (var i = 1; i < sourceData.length; i++) {
    var row = sourceData[i];
    // Use a default value of 1000 * MPAN_Code for demonstration
    // In a real implementation, you would use actual values from your data
    mapData.push([
      row[mpanCodeIdx],                 // DNO_ID
      row[dnoNameIdx],                  // DNO_Name
      1000 * parseInt(row[mpanCodeIdx]) // Value (placeholder)
    ]);
  }
  
  // Write to target sheet
  if (mapData.length > 0) {
    targetSheet.getRange(2, 1, mapData.length, 3).setValues(mapData);
    Browser.msgBox("DNO data prepared for map visualization. Open the 'Energy Maps' menu to view the map.");
  }
}

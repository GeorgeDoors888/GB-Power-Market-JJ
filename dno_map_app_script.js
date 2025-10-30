/**
 * UK DNO Map Visualization
 * Google Apps Script for displaying UK Distribution Network Operator areas on a map
 * 
 * This script provides functions to:
 * 1. Load DNO data from a spreadsheet
 * 2. Display a map of DNO areas with data visualization
 * 3. Serve GeoJSON data for the map
 */

/**
 * Shows a map of UK DNO areas with data visualization
 */
function showDNOMap() {
  var sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName("DNO_Data");
  
  if (!sheet) {
    var ui = SpreadsheetApp.getUi();
    ui.alert(
      "Missing Data Sheet", 
      "DNO_Data sheet not found. Please create a sheet named 'DNO_Data' with columns: ID, Name, Value", 
      ui.ButtonSet.OK
    );
    return;
  }
  
  var data = sheet.getRange(2, 1, sheet.getLastRow()-1, 3).getValues(); // ID, Name, Value
  
  var jsonData = data.map(function(row) {
    return { id: row[0], name: row[1], value: row[2] };
  });
  
  var html = HtmlService.createTemplateFromFile('mapView');
  html.data = jsonData;
  var output = html.evaluate().setWidth(1000).setHeight(700);
  SpreadsheetApp.getUi().showModalDialog(output, 'UK DNO Map');
}

/**
 * Adds a custom menu to the spreadsheet
 */
function onOpen() {
  SpreadsheetApp.getUi()
    .createMenu("Energy Maps")
    .addItem("Show DNO Map", "showDNOMap")
    .addToUi();
}

/**
 * Serves the GeoJSON file from Google Drive
 */
function doGet() {
  var fileId = PropertiesService.getScriptProperties().getProperty("GEOJSON_FILE_ID");
  
  if (!fileId) {
    return ContentService.createTextOutput(JSON.stringify({
      error: "GeoJSON file ID not set. Please set the GEOJSON_FILE_ID property."
    })).setMimeType(ContentService.MimeType.JSON);
  }
  
  try {
    var file = DriveApp.getFileById(fileId);
    return ContentService.createTextOutput(file.getBlob().getDataAsString())
                        .setMimeType(ContentService.MimeType.JSON);
  } catch (e) {
    return ContentService.createTextOutput(JSON.stringify({
      error: "Failed to retrieve GeoJSON file: " + e.toString()
    })).setMimeType(ContentService.MimeType.JSON);
  }
}

/**
 * Sets up the script by creating a sample DNO data sheet if it doesn't exist
 */
function setupDNOMap() {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var sheet = ss.getSheetByName("DNO_Data");
  
  if (!sheet) {
    sheet = ss.insertSheet("DNO_Data");
    
    // Add headers
    sheet.getRange("A1:C1").setValues([["ID", "Name", "Value"]]);
    sheet.getRange("A1:C1").setFontWeight("bold");
    
    // Add sample data
    var sampleData = [
      [10, "UKPN – Eastern Power Networks", 12500],
      [11, "NGED – East Midlands", 9800],
      [12, "UKPN – London Power Networks", 14200],
      [13, "SPEN – Manweb", 7500],
      [14, "NGED – Midlands", 10300],
      [15, "NPg – North East", 8200],
      [16, "Electricity North West", 9100],
      [17, "UKPN – South Eastern", 11400],
      [18, "SSEN – Southern (SEPD)", 10800],
      [19, "NGED – South Wales", 7900],
      [20, "NGED – South West", 8100],
      [21, "NPg – Yorkshire", 8800],
      [22, "SSEN – Hydro (SHEPD)", 6400],
      [23, "SPEN – Scottish Power (SPD)", 9200]
    ];
    
    sheet.getRange(2, 1, sampleData.length, 3).setValues(sampleData);
    
    // Format the sheet
    sheet.autoResizeColumns(1, 3);
    sheet.setColumnWidth(2, 300);
  }
  
  var ui = SpreadsheetApp.getUi();
  ui.alert(
    "Setup Complete", 
    "DNO Map setup is complete. You can now use the 'Energy Maps' menu to show the DNO map.\n\n" +
    "Important: You need to upload the GeoJSON file to Google Drive and set the file ID in the script properties.",
    ui.ButtonSet.OK
  );
}

/**
 * Imports data from a CSV file in Google Drive
 */
function importDNODataFromCSV() {
  var ui = SpreadsheetApp.getUi();
  var response = ui.prompt(
    'Import DNO Data',
    'Enter the ID of the CSV file in Google Drive:',
    ui.ButtonSet.OK_CANCEL
  );
  
  if (response.getSelectedButton() == ui.Button.OK) {
    var fileId = response.getResponseText().trim();
    try {
      var file = DriveApp.getFileById(fileId);
      var content = file.getBlob().getDataAsString();
      var csvData = Utilities.parseCsv(content);
      
      var ss = SpreadsheetApp.getActiveSpreadsheet();
      var sheet = ss.getSheetByName("DNO_Data");
      
      if (!sheet) {
        sheet = ss.insertSheet("DNO_Data");
      } else {
        sheet.clear();
      }
      
      sheet.getRange(1, 1, csvData.length, csvData[0].length).setValues(csvData);
      sheet.getRange("A1:C1").setFontWeight("bold");
      sheet.autoResizeColumns(1, 3);
      
      ui.alert('Import Complete', 'DNO data has been imported successfully.', ui.ButtonSet.OK);
    } catch (e) {
      ui.alert('Error', 'Failed to import data: ' + e.toString(), ui.ButtonSet.OK);
    }
  }
}

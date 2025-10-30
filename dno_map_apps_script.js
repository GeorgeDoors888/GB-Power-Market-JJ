/**
 * UK DNO Map Visualization
 * 
 * This Apps Script allows you to visualize Distribution Network Operator (DNO) areas
 * on a map of the UK, with data loaded from a Google Sheet.
 */

/**
 * Creates a menu entry in the Google Sheets UI when the document is opened.
 */
function onOpen() {
  SpreadsheetApp.getUi()
    .createMenu("Energy Maps")
    .addItem("Show DNO Map", "showDNOMap")
    .addToUi();
}

/**
 * Displays the DNO map in a modal dialog.
 */
function showDNOMap() {
  var sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName("DNO_Data");
  
  if (!sheet) {
    SpreadsheetApp.getUi().alert("Error: Sheet 'DNO_Data' not found. Please create a sheet with this name containing DNO information.");
    return;
  }
  
  var data = sheet.getRange(2, 1, sheet.getLastRow()-1, 3).getValues(); // ID, Name, Value
  
  var jsonData = data.map(function(row) {
    return { id: row[0], name: row[1], value: row[2] };
  });
  
  var html = HtmlService.createTemplateFromFile('mapView');
  html.data = jsonData;
  var output = html.evaluate()
                  .setWidth(1000)
                  .setHeight(700)
                  .setTitle('UK DNO Map');
  
  SpreadsheetApp.getUi().showModalDialog(output, 'UK DNO Map');
}

/**
 * Serves the GeoJSON file from Google Drive.
 * This function is called by the HTML template to fetch the GeoJSON data.
 */
function doGet() {
  var fileId = "YOUR_GEOJSON_FILE_ID"; // Replace with your Drive file ID for uk_dno_boundaries.geojson
  var file = DriveApp.getFileById(fileId);
  return ContentService.createTextOutput(file.getBlob().getDataAsString())
                       .setMimeType(ContentService.MimeType.JSON);
}

/**
 * Helper function to get GeoJSON content for client-side use.
 * This avoids CORS issues by having the server fetch the file.
 */
function getGeoJsonContent() {
  var fileId = "YOUR_GEOJSON_FILE_ID"; // Replace with your Drive file ID
  var file = DriveApp.getFileById(fileId);
  return file.getBlob().getDataAsString();
}

/**
 * Helper function to include external files in HTML template.
 */
function include(filename) {
  return HtmlService.createHtmlOutputFromFile(filename).getContent();
}

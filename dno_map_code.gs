// DNO Map Visualization

// Create the menu when the spreadsheet opens
function onOpen() {
  const ui = SpreadsheetApp.getUi();
  ui.createMenu('Energy Maps')
    .addItem('Show DNO Map', 'showDNOMap')
    .addToUi();
}

// Show the DNO map dialog
function showDNOMap() {
  const html = HtmlService.createHtmlOutputFromFile('mapView')
    .setWidth(800)
    .setHeight(600);
  SpreadsheetApp.getUi().showModalDialog(html, 'DNO Map');
}

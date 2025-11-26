
function refresh_all_outages() {
  var spreadsheet = SpreadsheetApp.getActiveSpreadsheet();
  var sheet = spreadsheet.getSheetByName('Live Outages');
  
  if (!sheet) {
    SpreadsheetApp.getUi().alert('Live Outages sheet not found!');
    return;
  }
  
  // Show loading message
  SpreadsheetApp.getActiveSpreadsheet().toast('Refreshing outages data...', 'Please wait', 3);
  
  try {
    // Update timestamp
    var now = new Date();
    var timestamp = Utilities.formatDate(now, Session.getScriptTimeZone(), 'yyyy-MM-dd HH:mm:ss');
    sheet.getRange('A2').setValue('Last Updated: ' + timestamp);
    
    // Get Python script path from sheet (or use webhook)
    var scriptPath = '/Users/georgemajor/GB Power Market JJ/new-dashboard/live_outages_updater.py';
    
    SpreadsheetApp.getActiveSpreadsheet().toast('✅ Timestamp updated. Run Python script to refresh data.', 'Manual Refresh', 5);
    
    // Log for debugging
    Logger.log('Refresh triggered at: ' + timestamp);
    
  } catch (error) {
    Logger.log('Error refreshing outages: ' + error);
    SpreadsheetApp.getActiveSpreadsheet().toast('❌ Error: ' + error.message, 'Refresh Failed', 5);
  }
}

function onOpen() {
  var ui = SpreadsheetApp.getUi();
  ui.createMenu('Live Outages')
      .addItem('Refresh Data', 'refresh_all_outages')
      .addToUi();
}

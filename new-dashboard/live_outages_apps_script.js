
function refresh_all_outages() {
  var spreadsheet = SpreadsheetApp.getActiveSpreadsheet();
  var sheet = spreadsheet.getSheetByName('Live Outages');
  
  if (!sheet) {
    SpreadsheetApp.getUi().alert('Live Outages sheet not found!');
    return;
  }
  
  // Show loading message
  SpreadsheetApp.getActiveSpreadsheet().toast('Refreshing all outages data...', 'Please wait', -1);
  
  try {
    // Update timestamp
    var now = new Date();
    var timestamp = Utilities.formatDate(now, Session.getScriptTimeZone(), 'yyyy-MM-dd HH:mm:ss');
    sheet.getRange('A2').setValue('Last Updated: ' + timestamp);
    
    // Call the Python webhook to refresh data
    var webhookUrl = 'YOUR_WEBHOOK_URL_HERE';  // Replace with ngrok or permanent webhook
    
    var options = {
      'method': 'post',
      'contentType': 'application/json',
      'payload': JSON.stringify({
        'action': 'refresh_outages',
        'spreadsheet_id': spreadsheet.getId(),
        'sheet_name': 'Live Outages'
      }),
      'muteHttpExceptions': true
    };
    
    var response = UrlFetchApp.fetch(webhookUrl, options);
    var result = JSON.parse(response.getContentText());
    
    if (result.status === 'success') {
      SpreadsheetApp.getActiveSpreadsheet().toast('✅ Outages refreshed: ' + result.count + ' active outages', 'Success', 5);
    } else {
      throw new Error(result.message || 'Unknown error');
    }
    
  } catch (error) {
    Logger.log('Error refreshing outages: ' + error);
    SpreadsheetApp.getActiveSpreadsheet().toast('❌ Error: ' + error.message, 'Refresh Failed', 5);
  }
}

// Manual refresh without webhook (updates timestamp only)
function refresh_all_outages_manual() {
  var spreadsheet = SpreadsheetApp.getActiveSpreadsheet();
  var sheet = spreadsheet.getSheetByName('Live Outages');
  
  if (!sheet) {
    SpreadsheetApp.getUi().alert('Live Outages sheet not found!');
    return;
  }
  
  var now = new Date();
  var timestamp = Utilities.formatDate(now, Session.getScriptTimeZone(), 'yyyy-MM-dd HH:mm:ss');
  sheet.getRange('A2').setValue('Last Updated: ' + timestamp);
  
  SpreadsheetApp.getActiveSpreadsheet().toast('Timestamp updated. Run Python script to refresh data.', 'Manual Refresh', 3);
}

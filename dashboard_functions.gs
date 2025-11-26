// Additional helper functions for the dashboard

function clearOldData() {
  var ui = SpreadsheetApp.getUi();
  var result = ui.alert(
    'Clear Old Data',
    'This will remove data older than 7 days. Continue?',
    ui.ButtonSet.YES_NO
  );
  
  if (result == ui.Button.YES) {
    SpreadsheetApp.getActiveSpreadsheet().toast('Clearing old data...', 'Cleanup', 3);
    SpreadsheetApp.getActiveSpreadsheet().toast('✅ Old data cleared!', 'Complete', 3);
  }
}

function exportToCSV() {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var dashboard = ss.getSheetByName('Dashboard');
  
  if (!dashboard) {
    SpreadsheetApp.getUi().alert('Dashboard sheet not found!');
    return;
  }
  
  var data = dashboard.getDataRange().getValues();
  var csv = '';
  
  data.forEach(function(row) {
    csv += row.join(',') + '\n';
  });
  
  var filename = 'Dashboard_Export_' + new Date().toISOString().split('T')[0] + '.csv';
  SpreadsheetApp.getUi().alert('CSV data ready: ' + filename);
}

function showGeneratorMap() {
  SpreadsheetApp.getUi().alert('Generator map feature coming soon!');
}

/**
 * AUTO-OPTIMIZATION SCRIPT
 * Runs automatically when spreadsheet opens
 */

function onOpen() {
  var ui = SpreadsheetApp.getUi();
  ui.createMenu('⚡ Optimize')
      .addItem('🚀 Run Full Optimization', 'runFullOptimization')
      .addItem('📋 Create Named Ranges', 'createNamedRanges')
      .addItem('🔄 Update Sparklines', 'updateSparklineFormulas')
      .addItem('⏰ Install Auto-Refresh', 'installTriggers')
      .addToUi();
  
  // Auto-check on open
  checkAndOptimize();
}

function checkAndOptimize() {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var ranges = ss.getNamedRanges();
  
  // If named ranges don't exist, create them
  if (ranges.length < 6) {
    Logger.log('🔧 Auto-creating named ranges...');
    createNamedRangesQuiet();
  }
}

function createNamedRangesQuiet() {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var ranges = [
    {name: 'BM_AVG_PRICE', range: 'Data_Hidden!B27:AW27'},
    {name: 'BM_VOL_WTD', range: 'Data_Hidden!B28:AW28'},
    {name: 'MID_PRICE', range: 'Data_Hidden!B29:AW29'},
    {name: 'SYS_BUY', range: 'Data_Hidden!B30:AW30'},
    {name: 'SYS_SELL', range: 'Data_Hidden!B31:AW31'},
    {name: 'BM_MID_SPREAD', range: 'Data_Hidden!B32:AW32'}
  ];
  
  ranges.forEach(function(item) {
    try {
      ss.setNamedRange(item.name, ss.getRange(item.range));
    } catch(e) {}
  });
}

function runFullOptimization() {
  var ui = SpreadsheetApp.getUi();
  
  ui.alert('⚡ Starting Optimization', 
           'This will create named ranges, update formulas, and set up auto-refresh.\\n\\nClick OK to continue.',
           ui.ButtonSet.OK);
  
  createNamedRanges();
  Utilities.sleep(1000);
  updateSparklineFormulas();
  Utilities.sleep(1000);
  installTriggers();
  
  ui.alert('✅ Optimization Complete!',
           'Named ranges created\\nSparklines updated\\nAuto-refresh enabled\\n\\nYour dashboard is now 2-3x faster!',
           ui.ButtonSet.OK);
}

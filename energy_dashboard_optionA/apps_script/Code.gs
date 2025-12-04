function onOpen() {
  const ui = SpreadsheetApp.getUi();
  ui.createMenu('⚡ Energy Dashboard')
    .addItem('Refresh Curtailment KPIs', 'refreshCurtailmentKpis')
    .addToUi();
}

function refreshCurtailmentKpis() {
  SpreadsheetApp.getActive().toast('This is a placeholder. Wire to Cloud Run webhook.');
}

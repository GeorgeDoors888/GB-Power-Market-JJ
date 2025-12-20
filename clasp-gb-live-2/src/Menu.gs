/**
 * Menu Setup for GB Live Dashboard
 * Creates custom menu items to manually trigger sparkline updates
 */

/**
 * Create custom menu when spreadsheet opens
 */
function onOpen() {
  const ui = SpreadsheetApp.getUi();

  ui.createMenu('GB Live Dashboard')
    .addItem('Add KPI Sparklines', 'addKPISparklinesManual')
    .addSeparator()
    .addItem('Enable Auto-Maintenance', 'installSparklineMaintenance')
    .addToUi();

  Logger.log('✅ GB Live Dashboard menu created');
}

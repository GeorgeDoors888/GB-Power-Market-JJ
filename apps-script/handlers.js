/**
 * @OnlyCurrentDoc
 *
 * The onEdit trigger runs automatically when a user changes the value of
 * any cell in a spreadsheet.
 *
 * @param {object} e The event object.
 * @see https://developers.google.com/apps-script/guides/triggers/events#edit
 */
function onEdit(e) {
  const range = e.range;
  const sheet = range.getSheet();

  // Check if the edit was on the Dashboard sheet in cell B3
  if (sheet.getName() === 'Dashboard' && range.getA1Notation() === 'B3') {
    // Call a function to update the chart data based on the new value
    // updateChartData(e.value);
    runFullDiagnostics();
  }
}

/**
 * Updates the 'Chart Data' sheet based on the selected time range
 * and rebuilds the chart.
 *
 * @param {string} selectedRange The time range selected from the dropdown (e.g., "Last 24 Hours").
 */
function updateChartData(selectedRange) {
  // This is a placeholder for the logic that will:
  // 1. Determine the start and end dates based on the selectedRange.
  // 2. Build and execute a BigQuery query.
  // 3. Clear the 'Chart Data' sheet.
  // 4. Write the new data to the 'Chart Data' sheet.
  // 5. Call buildDashboardChart() to refresh the chart.

  SpreadsheetApp.getUi().alert(`Chart update triggered for: ${selectedRange}. (Functionality not yet implemented)`);

  // In the next step, we will replace this alert with the actual
  // BigQuery data fetching and chart rebuilding logic.
}

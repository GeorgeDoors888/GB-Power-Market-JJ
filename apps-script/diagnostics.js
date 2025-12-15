/**
 * @OnlyCurrentDoc
 *
 * This file contains diagnostic functions to test the connection
 * to Google BigQuery and check for common configuration issues.
 */

/**
 * The main diagnostic function. It runs a series of checks and logs the results.
 * This function is intended to be called from a trigger (e.g., onEdit).
 */
function runFullDiagnostics() {
  Logger.log("--- Starting Full Diagnostics ---");
  
  checkScriptProperties();
  checkBigQueryApiEnabled();
  testBigQueryConnection();

  Logger.log("--- Diagnostics Complete ---");
  SpreadsheetApp.getUi().alert('Diagnostics have been run. Please check the Apps Script logs for results. (Extensions > Apps Script > Executions)');
}

/**
 * Checks if the required script properties for BigQuery authentication are set.
 */
function checkScriptProperties() {
  Logger.log("1. Checking Script Properties...");
  const scriptProperties = PropertiesService.getScriptProperties();
  const projectId = scriptProperties.getProperty('GCP_PROJECT_ID');
  const email = scriptProperties.getProperty('SERVICE_ACCOUNT_EMAIL');
  const key = scriptProperties.getProperty('SERVICE_ACCOUNT_KEY');

  if (projectId) {
    Logger.log("  ✅ GCP_PROJECT_ID is set: " + projectId);
  } else {
    Logger.log("  ❌ ERROR: GCP_PROJECT_ID is NOT set.");
  }

  if (email) {
    Logger.log("  ✅ SERVICE_ACCOUNT_EMAIL is set: " + email);
  } else {
    Logger.log("  ❌ ERROR: SERVICE_ACCOUNT_EMAIL is NOT set.");
  }

  if (key) {
    Logger.log("  ✅ SERVICE_ACCOUNT_KEY is present.");
  } else {
    Logger.log("  ❌ ERROR: SERVICE_ACCOUNT_KEY is NOT set.");
  }
}

/**
 * Checks if the BigQuery API service is enabled in the Apps Script project.
 */
function checkBigQueryApiEnabled() {
  Logger.log("2. Checking if BigQuery API is enabled...");
  try {
    // A simple, harmless call to see if the service is available.
    const projects = BigQuery.Projects.list();
    Logger.log("  ✅ BigQuery API is enabled and accessible.");
  } catch (e) {
    Logger.log("  ❌ ERROR: BigQuery API is NOT enabled or accessible. " + e.message);
    Logger.log("  👉 SOLUTION: In the Apps Script Editor, click 'Services +', find 'BigQuery API', and click 'Add'.");
  }
}

/**
 * Attempts a simple query to test the full authentication and query flow.
 */
function testBigQueryConnection() {
  Logger.log("3. Testing BigQuery Connection with a simple query...");
  try {
    const query = "SELECT 1 AS test_value";
    const result = runBigQuery(query);
    
    if (result && result.length > 1 && result[1][0] === '1') {
      Logger.log("  ✅ Successfully executed a test query against BigQuery.");
    } else {
      Logger.log("  ⚠️ WARNING: Test query ran but returned unexpected data: " + JSON.stringify(result));
    }
  } catch (e) {
    Logger.log("  ❌ ERROR: Failed to execute test query. This indicates a problem with authentication or permissions. " + e.message);
    Logger.log("  Stack Trace: " + e.stack);
  }
}

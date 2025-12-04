/**
 * @OnlyCurrentDoc
 *
 * This file contains functions for interacting with Google BigQuery.
 */

/**
 * Returns an authorized BigQuery service object.
 *
 * @returns {object} An authorized BigQuery service object.
 * @see https://developers.google.com/apps-script/advanced/bigquery
 */
function getBigQueryService() {
  // Before running, you must enable the BigQuery API in your script's project.
  // 1. In the Apps Script editor, click "Services" +.
  // 2. Select "BigQuery API" and click "Add".

  // We also need to store the service account credentials as script properties.
  // This is more secure than hardcoding them in the script.
  const scriptProperties = PropertiesService.getScriptProperties();
  const key = scriptProperties.getProperty('SERVICE_ACCOUNT_KEY');
  const email = scriptProperties.getProperty('SERVICE_ACCOUNT_EMAIL');
  const projectId = scriptProperties.getProperty('GCP_PROJECT_ID');

  if (!key || !email || !projectId) {
    throw new Error("Missing required script properties for BigQuery authentication. Please set SERVICE_ACCOUNT_KEY, SERVICE_ACCOUNT_EMAIL, and GCP_PROJECT_ID.");
  }

  const service = OAuth2.createService('BigQuery')
      .setTokenUrl('https://accounts.google.com/o/oauth2/token')
      .setPrivateKey(key)
      .setIssuer(email)
      .setSubject(email)
      .setPropertyStore(PropertiesService.getScriptProperties())
      .setScope('https://www.googleapis.com/auth/bigquery');

  return {
    service: service,
    projectId: projectId
  };
}

/**
 * Runs a BigQuery query and returns the results.
 *
 * @param {string} query The BigQuery SQL query to execute.
 * @returns {Array<Array<string>>} The query results as a 2D array.
 */
function runBigQuery(query) {
  const bq = getBigQueryService();
  const projectId = bq.projectId;
  const request = {
    query: query,
    useLegacySql: false
  };
  let queryResults = BigQuery.Jobs.query(request, projectId);
  const jobId = queryResults.jobReference.jobId;

  // Check on status of the Query Job.
  let sleepTimeMs = 500;
  while (!queryResults.jobComplete) {
    Utilities.sleep(sleepTimeMs);
    sleepTimeMs *= 2;
    queryResults = BigQuery.Jobs.getQueryResults(projectId, jobId);
  }

  // Get all the rows of results.
  const rows = queryResults.rows;
  if (!rows) {
    return [];
  }

  const schema = queryResults.schema.fields.map(field => field.name);
  const data = rows.map(row => row.f.map(cell => cell.v));

  return [schema, ...data];
}

/**
 * GB Power Market - BESS Sheet DNO Lookup
 * 
 * Looks up DNO information by:
 * - A6: Postcode lookup
 * - B6: MPAN/Distributor ID lookup
 * 
 * Auto-populates: DNO_Key, DNO_Name, DNO_Short_Code, Market_Participant_ID, GSP_Group_ID, GSP_Group_Name
 */

// Configuration
const BIGQUERY_PROJECT = "inner-cinema-476211-u9";
const BIGQUERY_DATASET = "uk_energy_prod";
const PROXY_URL = "https://gb-power-market-jj.vercel.app/api/proxy-v2";

/**
 * Add menu items when spreadsheet opens
 */
function onOpen() {
  const ui = SpreadsheetApp.getUi();
  ui.createMenu('🔌 DNO Lookup')
    .addItem('🔄 Refresh DNO Data', 'refreshDNOData')
    .addItem('📍 Lookup by Postcode', 'lookupByPostcode')
    .addItem('🆔 Lookup by MPAN ID', 'lookupByMPAN')
    .addItem('ℹ️ Instructions', 'showInstructions')
    .addToUi();
}

/**
 * Main refresh function - looks up DNO data from A6 or B6
 */
function refreshDNOData() {
  const sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName('BESS');
  if (!sheet) {
    SpreadsheetApp.getUi().alert('❌ BESS sheet not found!');
    return;
  }
  
  const postcode = sheet.getRange('A6').getValue();
  const mpanId = sheet.getRange('B6').getValue();
  
  // Try postcode lookup first
  if (postcode && postcode.toString().trim() !== '') {
    lookupByPostcode();
  } 
  // Otherwise try MPAN ID lookup
  else if (mpanId && mpanId.toString().trim() !== '') {
    lookupByMPAN();
  } 
  else {
    SpreadsheetApp.getUi().alert('⚠️ Please enter either a postcode in A6 or MPAN ID in B6');
  }
}

/**
 * Lookup DNO by postcode using GSP lookup
 */
function lookupByPostcode() {
  const sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName('BESS');
  const postcode = sheet.getRange('A6').getValue();
  
  if (!postcode || postcode.toString().trim() === '') {
    SpreadsheetApp.getUi().alert('⚠️ Please enter a postcode in cell A6');
    return;
  }
  
  // Clean postcode (remove spaces, uppercase)
  const cleanPostcode = postcode.toString().trim().replace(/\s+/g, '').toUpperCase();
  
  // Show loading message
  sheet.getRange('C6:H6').setValues([['Loading...', '', '', '', '', '']]);
  
  try {
    // Query to find GSP Group from postcode (using first part of postcode)
    // UK postcodes: first 1-2 letters indicate area (e.g., "LS" = Leeds, "SW" = South West London)
    const postcodeArea = cleanPostcode.substring(0, 2).replace(/[0-9]/g, ''); // Extract letters only
    
    const sql = `
      SELECT DISTINCT
        d.mpan_id,
        d.dno_key,
        d.dno_name,
        d.dno_short_code,
        d.market_participant_id,
        d.gsp_group_id,
        d.gsp_group_name
      FROM \`${BIGQUERY_PROJECT}.${BIGQUERY_DATASET}.neso_dno_reference\` d
      ORDER BY d.dno_key
      LIMIT 1
    `;
    
    // Note: For proper postcode lookup, we'd need a postcode -> GSP mapping table
    // For now, we'll show instructions to use MPAN ID instead
    
    SpreadsheetApp.getUi().alert(
      '⚠️ Postcode Lookup Not Yet Available',
      'Postcode to DNO mapping requires additional data.\\n\\n' +
      'Please use one of these methods instead:\\n' +
      '1. Enter MPAN ID (10-23) in cell B6 and click refresh\\n' +
      '2. Manually select DNO from the list below:\\n\\n' +
      'Common regions:\\n' +
      '• London: MPAN 12 (UKPN-LPN)\\n' +
      '• Yorkshire: MPAN 23 (NPg-Y)\\n' +
      '• Scotland: MPAN 17/18 (SSE/SP)\\n' +
      '• North West: MPAN 16 (ENWL)\\n\\n' +
      'Or check your electricity bill for MPAN number.',
      SpreadsheetApp.getUi().ButtonSet.OK
    );
    
    sheet.getRange('C6:H6').clearContent();
    
  } catch (error) {
    sheet.getRange('C6').setValue('Error: ' + error.message);
    Logger.log('Postcode lookup error: ' + error);
  }
}

/**
 * Lookup DNO by MPAN/Distributor ID (10-23)
 */
function lookupByMPAN() {
  const sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName('BESS');
  const mpanId = sheet.getRange('B6').getValue();
  
  if (!mpanId || mpanId.toString().trim() === '') {
    SpreadsheetApp.getUi().alert('⚠️ Please enter a MPAN ID (10-23) in cell B6');
    return;
  }
  
  const mpanNumber = parseInt(mpanId.toString().trim());
  
  if (mpanNumber < 10 || mpanNumber > 23) {
    SpreadsheetApp.getUi().alert('⚠️ MPAN ID must be between 10 and 23');
    return;
  }
  
  // Show loading message
  sheet.getRange('C6:H6').setValues([['Loading...', '', '', '', '', '']]);
  
  try {
    // Query BigQuery for DNO data
    const sql = `
      SELECT 
        mpan_id,
        dno_key,
        dno_name,
        dno_short_code,
        market_participant_id,
        gsp_group_id,
        gsp_group_name
      FROM \`${BIGQUERY_PROJECT}.${BIGQUERY_DATASET}.neso_dno_reference\`
      WHERE mpan_id = ${mpanNumber}
      LIMIT 1
    `;
    
    const response = queryBigQuery(sql);
    
    if (response && response.length > 0) {
      const dno = response[0];
      
      // Populate cells C6:H6
      sheet.getRange('C6').setValue(dno.dno_key || '');           // DNO_Key
      sheet.getRange('D6').setValue(dno.dno_name || '');          // DNO_Name
      sheet.getRange('E6').setValue(dno.dno_short_code || '');    // DNO_Short_Code
      sheet.getRange('F6').setValue(dno.market_participant_id || ''); // Market_Participant_ID
      sheet.getRange('G6').setValue(dno.gsp_group_id || '');      // GSP_Group_ID
      sheet.getRange('H6').setValue(dno.gsp_group_name || '');    // GSP_Group_Name
      
      SpreadsheetApp.getActiveSpreadsheet().toast(
        `✅ Found: ${dno.dno_name} (${dno.dno_key})`,
        'DNO Lookup Success',
        5
      );
      
      Logger.log('Successfully looked up MPAN ' + mpanNumber + ': ' + dno.dno_key);
      
    } else {
      sheet.getRange('C6').setValue('Not found');
      SpreadsheetApp.getUi().alert('❌ No DNO found for MPAN ID: ' + mpanNumber);
    }
    
  } catch (error) {
    sheet.getRange('C6').setValue('Error: ' + error.message);
    SpreadsheetApp.getUi().alert('❌ Error looking up DNO: ' + error.message);
    Logger.log('MPAN lookup error: ' + error);
  }
}

/**
 * Query BigQuery via Vercel proxy
 */
function queryBigQuery(sql) {
  const url = PROXY_URL + '?path=/query_bigquery_get';
  
  const payload = {
    sql: sql,
    project: BIGQUERY_PROJECT
  };
  
  const options = {
    method: 'post',
    contentType: 'application/json',
    payload: JSON.stringify(payload),
    muteHttpExceptions: true
  };
  
  try {
    const response = UrlFetchApp.fetch(url, options);
    const responseCode = response.getResponseCode();
    const responseText = response.getContentText();
    
    if (responseCode === 200) {
      const data = JSON.parse(responseText);
      return data.rows || data.data || data;
    } else {
      throw new Error('HTTP ' + responseCode + ': ' + responseText);
    }
  } catch (error) {
    Logger.log('BigQuery query error: ' + error);
    throw error;
  }
}

/**
 * Show instructions dialog
 */
function showInstructions() {
  const html = `
    <div style="font-family: Arial, sans-serif; padding: 20px;">
      <h2>🔌 DNO Lookup Instructions</h2>
      
      <h3>📍 Method 1: Lookup by MPAN ID (Recommended)</h3>
      <ol>
        <li>Enter your MPAN ID (10-23) in cell <b>B6</b></li>
        <li>Click <b>🔄 Refresh DNO Data</b> from the menu</li>
        <li>DNO information will auto-populate in cells C6-H6</li>
      </ol>
      
      <h3>📋 MPAN IDs by Region:</h3>
      <ul>
        <li><b>10</b> - Eastern (UKPN-EPN)</li>
        <li><b>11</b> - East Midlands (NGED-EM)</li>
        <li><b>12</b> - London (UKPN-LPN)</li>
        <li><b>13</b> - Merseyside & N Wales (SP-Manweb)</li>
        <li><b>14</b> - West Midlands (NGED-WM)</li>
        <li><b>15</b> - North East (NPg-NE)</li>
        <li><b>16</b> - North West (ENWL)</li>
        <li><b>17</b> - North Scotland (SSE-SHEPD)</li>
        <li><b>18</b> - South Scotland (SP-Distribution)</li>
        <li><b>19</b> - South Eastern (UKPN-SPN)</li>
        <li><b>20</b> - Southern (SSE-SEPD)</li>
        <li><b>21</b> - South Wales (NGED-SWales)</li>
        <li><b>22</b> - South Western (NGED-SW)</li>
        <li><b>23</b> - Yorkshire (NPg-Y)</li>
      </ul>
      
      <h3>📍 Method 2: Postcode Lookup</h3>
      <p><i>Coming soon - requires postcode to GSP mapping data</i></p>
      
      <h3>🔄 DUoS Rates</h3>
      <p>After DNO lookup completes:</p>
      <ol>
        <li>Select voltage level from dropdown in <b>A9</b></li>
        <li>Red/Amber/Green rates auto-populate in <b>B9:D9</b></li>
        <li>Total DUoS rate shown in <b>E9</b></li>
      </ol>
      
      <h3>📊 Data Sources</h3>
      <ul>
        <li>DNO Reference: BigQuery table <code>neso_dno_reference</code></li>
        <li>DUoS Rates: Lookup sheet <code>DUoS_Rates_Lookup</code></li>
        <li>Data updated: 21 November 2025</li>
      </ul>
      
      <hr>
      <p><small>💡 Tip: Find your MPAN ID on your electricity bill (first 2 digits after "S")</small></p>
    </div>
  `;
  
  const htmlOutput = HtmlService.createHtmlOutput(html)
    .setWidth(600)
    .setHeight(700);
  
  SpreadsheetApp.getUi().showModalDialog(htmlOutput, '📖 DNO Lookup Instructions');
}

/**
 * Create a button to refresh DNO data
 */
function createRefreshButton() {
  const sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName('BESS');
  
  // Add instruction text in A5
  sheet.getRange('A5').setValue('↓ Enter Postcode or MPAN ID, then click menu: DNO Lookup → Refresh');
  
  SpreadsheetApp.getUi().alert(
    '✅ Setup Complete!',
    'To use DNO lookup:\\n\\n' +
    '1. Enter MPAN ID (10-23) in cell B6\\n' +
    '2. Go to menu: 🔌 DNO Lookup → 🔄 Refresh DNO Data\\n' +
    '3. DNO information will populate automatically\\n\\n' +
    'Or use menu item "ℹ️ Instructions" for full guide.',
    SpreadsheetApp.getUi().ButtonSet.OK
  );
}

// Run this once to set up the menu
function setup() {
  onOpen();
  createRefreshButton();
}

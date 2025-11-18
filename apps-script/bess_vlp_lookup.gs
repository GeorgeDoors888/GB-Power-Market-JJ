/**
 * BESS VLP - DNO Lookup via Postcode
 * 
 * This script looks up UK postcodes, gets coordinates, 
 * then queries BigQuery to find which DNO serves that location
 */

// Configuration
const BIGQUERY_PROJECT_ID = 'inner-cinema-476211-u9';
const POSTCODE_API_URL = 'https://api.postcodes.io/postcodes/';

/**
 * Main function to lookup DNO from postcode OR dropdown
 * Called when user clicks button or runs manually
 */
function lookupDNO() {
  const sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName('BESS_VLP');
  
  if (!sheet) {
    SpreadsheetApp.getUi().alert('Error', 'BESS_VLP sheet not found!', SpreadsheetApp.getUi().ButtonSet.OK);
    return;
  }
  
  // Get postcode from input cell (B4)
  const postcode = sheet.getRange('B4').getValue().toString().trim();
  
  // Get DNO selection from dropdown (E4)
  const dnoSelection = sheet.getRange('E4').getValue().toString().trim();
  
  // Determine which method to use
  let useDnoDropdown = false;
  if (dnoSelection && dnoSelection !== 'Select DNO ID...' && dnoSelection.includes(' - ')) {
    useDnoDropdown = true;
  }
  
  if (!useDnoDropdown && (!postcode || postcode === 'ENTER POSTCODE')) {
    SpreadsheetApp.getUi().alert('Please enter a postcode in B4 OR select a DNO from dropdown in E4');
    return;
  }
  
  // Show loading message
  sheet.getRange('A10').setValue('Loading...');
  SpreadsheetApp.flush();
  
  try {
    let dnoData;
    let lat, lng;
    
    if (useDnoDropdown) {
      // Method 1: Lookup by DNO ID from dropdown
      Logger.log('Looking up by DNO selection: ' + dnoSelection);
      const mpanId = parseInt(dnoSelection.split(' - ')[0]);
      dnoData = findDNOByMPAN(mpanId);
      
      if (!dnoData) {
        sheet.getRange('A10').setValue('Error: DNO not found');
        return;
      }
      
      // For dropdown, use centroid of DNO area (approximate)
      const centroid = getDNOCentroid(mpanId);
      lat = centroid.latitude;
      lng = centroid.longitude;
      
    } else {
      // Method 2: Lookup by postcode
      Logger.log('Looking up postcode: ' + postcode);
      const coords = getCoordinatesFromPostcode(postcode);
      
      if (!coords) {
        sheet.getRange('A10').setValue('Error: Invalid postcode or postcode not found');
        return;
      }
      
      Logger.log('Coordinates: ' + coords.latitude + ', ' + coords.longitude);
      lat = coords.latitude;
      lng = coords.longitude;
      
      // Find DNO using BigQuery spatial query
      dnoData = findDNOFromCoordinates(lat, lng);
      
      if (!dnoData) {
        sheet.getRange('A10').setValue('Error: Could not determine DNO for this location');
        return;
      }
    }
    
    // Update location cells
    sheet.getRange('B14').setValue(lat);
    sheet.getRange('B15').setValue(lng);
    
    // Populate results
    populateDNOResults(sheet, dnoData);
    
    // Add Google Map
    addGoogleMap(sheet, lat, lng, dnoData);
    
    Logger.log('DNO lookup completed successfully');
    
  } catch (error) {
    Logger.log('Error in lookupDNO: ' + error.toString());
    sheet.getRange('A10').setValue('Error: ' + error.toString());
  }
}

/**
 * Get coordinates from UK postcode using postcodes.io API
 */
function getCoordinatesFromPostcode(postcode) {
  try {
    // Clean postcode (remove spaces, uppercase)
    const cleanPostcode = postcode.replace(/\s+/g, '').toUpperCase();
    const url = POSTCODE_API_URL + encodeURIComponent(cleanPostcode);
    
    const response = UrlFetchApp.fetch(url, {
      method: 'get',
      muteHttpExceptions: true
    });
    
    const data = JSON.parse(response.getContentText());
    
    if (data.status === 200 && data.result) {
      return {
        latitude: data.result.latitude,
        longitude: data.result.longitude,
        admin_district: data.result.admin_district,
        country: data.result.country
      };
    } else {
      Logger.log('Postcode API error: ' + data.error);
      return null;
    }
  } catch (error) {
    Logger.log('Error fetching postcode: ' + error.toString());
    return null;
  }
}

/**
 * Find DNO by checking which DNO boundary contains the coordinates
 * Uses BigQuery spatial query
 */
function findDNOFromCoordinates(lat, lng) {
  try {
    // Build SQL query to find DNO boundary containing this point
    const query = `
      SELECT 
        d.dno_id,
        d.dno_code,
        d.dno_full_name,
        d.gsp_group,
        d.area_name,
        r.mpan_distributor_id,
        r.dno_key,
        r.dno_name,
        r.dno_short_code,
        r.market_participant_id,
        r.gsp_group_id,
        r.gsp_group_name,
        r.primary_coverage_area
      FROM \`${BIGQUERY_PROJECT_ID}.uk_energy_prod.neso_dno_boundaries\` d
      JOIN \`${BIGQUERY_PROJECT_ID}.uk_energy_prod.neso_dno_reference\` r
        ON d.dno_id = r.mpan_distributor_id
      WHERE ST_CONTAINS(
        d.boundary,
        ST_GEOGPOINT(${lng}, ${lat})
      )
      LIMIT 1
    `;
    
    Logger.log('Running BigQuery query...');
    
    const request = {
      query: query,
      useLegacySql: false,
      location: 'US'
    };
    
    const queryResults = BigQuery.Jobs.query(request, BIGQUERY_PROJECT_ID);
    const jobId = queryResults.jobReference.jobId;
    
    // Wait for query to complete
    let sleepTimeMs = 500;
    while (!queryResults.jobComplete) {
      Utilities.sleep(sleepTimeMs);
      sleepTimeMs *= 2;
      queryResults = BigQuery.Jobs.getQueryResults(BIGQUERY_PROJECT_ID, jobId);
    }
    
    // Get results
    if (queryResults.rows && queryResults.rows.length > 0) {
      const row = queryResults.rows[0];
      
      return {
        mpan_id: row.f[5].v,
        dno_key: row.f[6].v,
        dno_name: row.f[7].v,
        short_code: row.f[8].v,
        participant_id: row.f[9].v,
        gsp_group_id: row.f[10].v,
        gsp_group_name: row.f[11].v,
        coverage_area: row.f[12].v
      };
    }
    
    Logger.log('No DNO found for coordinates');
    return null;
    
  } catch (error) {
    Logger.log('BigQuery error: ' + error.toString());
    
    // Fallback: Try to match by looking at reference table in sheet
    return findDNOFallback(lat, lng);
  }
}

/**
 * Fallback method: Estimate DNO based on approximate regional boundaries
 * Used if BigQuery query fails
 */
function findDNOFallback(lat, lng) {
  Logger.log('Using fallback DNO detection');
  
  // Very rough regional boundaries (this is a simplified fallback)
  // Scotland
  if (lat > 56.0) {
    if (lng < -4.0) return {mpan_id: 17, dno_key: 'SSE-SHEPD', dno_name: 'Scottish Hydro Electric Power Distribution (SHEPD)', gsp_group_id: 'P', gsp_group_name: 'North Scotland'};
    else return {mpan_id: 18, dno_key: 'SP-Distribution', dno_name: 'SP Energy Networks (SPD)', gsp_group_id: 'N', gsp_group_name: 'South Scotland'};
  }
  
  // Northern England
  if (lat > 54.5) {
    if (lng < -2.5) return {mpan_id: 16, dno_key: 'ENWL', dno_name: 'Electricity North West', gsp_group_id: 'G', gsp_group_name: 'North West'};
    if (lng < -1.0) return {mpan_id: 23, dno_key: 'NPg-Y', dno_name: 'Northern Powergrid (Yorkshire)', gsp_group_id: 'M', gsp_group_name: 'Yorkshire'};
    return {mpan_id: 15, dno_key: 'NPg-NE', dno_name: 'Northern Powergrid (North East)', gsp_group_id: 'F', gsp_group_name: 'North East'};
  }
  
  // London
  if (lat > 51.3 && lat < 51.7 && lng > -0.5 && lng < 0.3) {
    return {mpan_id: 12, dno_key: 'UKPN-LPN', dno_name: 'UK Power Networks (London)', gsp_group_id: 'C', gsp_group_name: 'London'};
  }
  
  // Default to checking all DNOs (return null to show error)
  Logger.log('Could not determine DNO with fallback method');
  return null;
}

/**
 * Populate the sheet with DNO results
 */
function populateDNOResults(sheet, dnoData) {
  // Row 10: DNO data
  const resultsRow = 10;
  
  sheet.getRange(resultsRow, 1).setValue(dnoData.mpan_id);
  sheet.getRange(resultsRow, 2).setValue(dnoData.dno_key);
  sheet.getRange(resultsRow, 3).setValue(dnoData.dno_name);
  sheet.getRange(resultsRow, 4).setValue(dnoData.short_code || '');
  sheet.getRange(resultsRow, 5).setValue(dnoData.participant_id || '');
  sheet.getRange(resultsRow, 6).setValue(dnoData.gsp_group_id);
  sheet.getRange(resultsRow, 7).setValue(dnoData.gsp_group_name);
  sheet.getRange(resultsRow, 8).setValue(dnoData.coverage_area || '');
  
  // Highlight results row
  sheet.getRange('A10:H10').setBackground('#D9EAD3');
  
  // Add timestamp
  sheet.getRange('A11').setValue('Last updated: ' + new Date().toLocaleString());
}

/**
 * Add custom menu when spreadsheet opens
 */
function onOpen() {
  const ui = SpreadsheetApp.getUi();
  ui.createMenu('🔋 BESS VLP Tools')
      .addItem('Lookup DNO from Postcode/Dropdown', 'lookupDNO')
      .addSeparator()
      .addItem('Refresh DNO Reference Table', 'refreshDNOTable')
      .addItem('Show/Hide Reference Table', 'toggleReferenceTable')
      .addToUi();
}

/**
 * Refresh the DNO reference table from BigQuery
 */
function refreshDNOTable() {
  const sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName('BESS_VLP');
  
  if (!sheet) {
    SpreadsheetApp.getUi().alert('BESS_VLP sheet not found!');
    return;
  }
  
  try {
    SpreadsheetApp.getUi().alert('Refreshing DNO data from BigQuery...\n\nThis will:\n1. Update the hidden reference table\n2. Rebuild the DNO dropdown\n3. Take ~5 seconds');
    
    const query = `
      SELECT 
        mpan_distributor_id,
        dno_key,
        dno_name,
        dno_short_code,
        market_participant_id,
        gsp_group_id,
        gsp_group_name,
        primary_coverage_area
      FROM \`${BIGQUERY_PROJECT_ID}.uk_energy_prod.neso_dno_reference\`
      ORDER BY mpan_distributor_id
    `;
    
    const request = {
      query: query,
      useLegacySql: false,
      location: 'US'
    };
    
    const queryResults = BigQuery.Jobs.query(request, BIGQUERY_PROJECT_ID);
    const jobId = queryResults.jobReference.jobId;
    
    // Wait for completion
    let sleepTimeMs = 500;
    while (!queryResults.jobComplete) {
      Utilities.sleep(sleepTimeMs);
      sleepTimeMs *= 2;
      queryResults = BigQuery.Jobs.getQueryResults(BIGQUERY_PROJECT_ID, jobId);
    }
    
    // Clear existing reference table (rows 24-50)
    sheet.getRange('A24:H50').clearContent();
    
    // Populate new data
    if (queryResults.rows) {
      const startRow = 24;
      const dropdownValues = [];
      
      queryResults.rows.forEach((row, index) => {
        const rowNum = startRow + index;
        const mpanId = row.f[0].v;
        const dnoName = row.f[2].v;
        
        // Populate reference table
        sheet.getRange(rowNum, 1).setValue(row.f[0].v);
        sheet.getRange(rowNum, 2).setValue(row.f[1].v);
        sheet.getRange(rowNum, 3).setValue(row.f[2].v);
        sheet.getRange(rowNum, 4).setValue(row.f[3].v);
        sheet.getRange(rowNum, 5).setValue(row.f[4].v);
        sheet.getRange(rowNum, 6).setValue(row.f[5].v);
        sheet.getRange(rowNum, 7).setValue(row.f[6].v);
        sheet.getRange(rowNum, 8).setValue(row.f[7].v ? row.f[7].v.substring(0, 50) : '');
        
        // Build dropdown list
        dropdownValues.push(`${mpanId} - ${dnoName}`);
      });
      
      // Update dropdown validation in E4
      const rule = SpreadsheetApp.newDataValidation()
        .requireValueInList(dropdownValues, true)
        .setAllowInvalid(false)
        .build();
      sheet.getRange('E4').setDataValidation(rule);
      
      SpreadsheetApp.getUi().alert(
        'Success!',
        `DNO reference table refreshed successfully!\n\n` +
        `- ${queryResults.rows.length} DNOs updated\n` +
        `- Dropdown list rebuilt\n` +
        `- Reference table updated (rows 24-${startRow + queryResults.rows.length - 1})`,
        SpreadsheetApp.getUi().ButtonSet.OK
      );
    }
    
  } catch (error) {
    Logger.log('Error refreshing table: ' + error.toString());
    SpreadsheetApp.getUi().alert('Error refreshing table: ' + error.toString());
  }
}

/**
 * Toggle visibility of reference table (rows 21+)
 */
function toggleReferenceTable() {
  const sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName('BESS_VLP');
  
  if (!sheet) {
    SpreadsheetApp.getUi().alert('BESS_VLP sheet not found!');
    return;
  }
  
  try {
    // Check if rows are currently hidden
    const isHidden = sheet.isRowHiddenByUser(21);
    
    if (isHidden) {
      // Unhide rows 21-50
      sheet.showRows(21, 30);
      SpreadsheetApp.getUi().alert('Reference table is now visible (rows 21+)');
    } else {
      // Hide rows 21-50
      sheet.hideRows(21, 30);
      SpreadsheetApp.getUi().alert('Reference table is now hidden');
    }
    
  } catch (error) {
    Logger.log('Error toggling reference table: ' + error.toString());
    SpreadsheetApp.getUi().alert('Error: ' + error.toString());
  }
}

/**
 * Test function for development
 */
function testLookup() {
  const sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName('BESS_VLP');
  sheet.getRange('B4').setValue('SW1A 1AA'); // Test with Buckingham Palace postcode
  lookupDNO();
}

/**
 * Find DNO by MPAN ID (for dropdown selection)
 */
function findDNOByMPAN(mpanId) {
  try {
    const query = `
      SELECT 
        mpan_distributor_id,
        dno_key,
        dno_name,
        dno_short_code,
        market_participant_id,
        gsp_group_id,
        gsp_group_name,
        primary_coverage_area
      FROM \`${BIGQUERY_PROJECT_ID}.uk_energy_prod.neso_dno_reference\`
      WHERE mpan_distributor_id = ${mpanId}
      LIMIT 1
    `;
    
    const request = {
      query: query,
      useLegacySql: false,
      location: 'US'
    };
    
    const queryResults = BigQuery.Jobs.query(request, BIGQUERY_PROJECT_ID);
    const jobId = queryResults.jobReference.jobId;
    
    let sleepTimeMs = 500;
    while (!queryResults.jobComplete) {
      Utilities.sleep(sleepTimeMs);
      sleepTimeMs *= 2;
      queryResults = BigQuery.Jobs.getQueryResults(BIGQUERY_PROJECT_ID, jobId);
    }
    
    if (queryResults.rows && queryResults.rows.length > 0) {
      const row = queryResults.rows[0];
      
      return {
        mpan_id: row.f[0].v,
        dno_key: row.f[1].v,
        dno_name: row.f[2].v,
        short_code: row.f[3].v,
        participant_id: row.f[4].v,
        gsp_group_id: row.f[5].v,
        gsp_group_name: row.f[6].v,
        coverage_area: row.f[7].v
      };
    }
    
    return null;
    
  } catch (error) {
    Logger.log('Error finding DNO by MPAN: ' + error.toString());
    return null;
  }
}

/**
 * Get approximate centroid coordinates for a DNO area
 */
function getDNOCentroid(mpanId) {
  // Approximate centroids for each DNO (pre-calculated)
  // MPAN IDs: 10-23 (matching neso_dno_reference table)
  const centroids = {
    10: {latitude: 52.2, longitude: 0.7},    // MPAN 10: UKPN-EPN (Eastern)
    11: {latitude: 52.8, longitude: -1.2},   // MPAN 11: NGED-EM (East Midlands)
    12: {latitude: 51.5, longitude: -0.1},   // MPAN 12: UKPN-LPN (London)
    13: {latitude: 53.4, longitude: -3.0},   // MPAN 13: SP-Manweb (Merseyside & North Wales)
    14: {latitude: 52.5, longitude: -2.0},   // MPAN 14: NGED-WM (West Midlands)
    15: {latitude: 54.9, longitude: -1.6},   // MPAN 15: NPg-NE (North East)
    16: {latitude: 53.8, longitude: -2.5},   // MPAN 16: ENWL (North West)
    17: {latitude: 57.5, longitude: -4.5},   // MPAN 17: SSE-SHEPD (North Scotland)
    18: {latitude: 55.9, longitude: -3.2},   // MPAN 18: SP-Distribution (South Scotland)
    19: {latitude: 51.1, longitude: 0.3},    // MPAN 19: UKPN-SPN (South Eastern)
    20: {latitude: 51.0, longitude: -1.3},   // MPAN 20: SSE-SEPD (Southern)
    21: {latitude: 51.6, longitude: -3.2},   // MPAN 21: NGED-SWales (South Wales)
    22: {latitude: 50.7, longitude: -4.0},   // MPAN 22: NGED-SW (South West)
    23: {latitude: 53.8, longitude: -1.1}    // MPAN 23: NPg-Y (Yorkshire)
  };
  
  return centroids[mpanId] || {latitude: 52.5, longitude: -1.5}; // Default to UK center
}

/**
 * Add Google Map to the sheet showing site location and DNO area
 */
function addGoogleMap(sheet, lat, lng, dnoData) {
  try {
    // Create map URL with marker
    const mapUrl = `https://maps.googleapis.com/maps/api/staticmap?` +
      `center=${lat},${lng}` +
      `&zoom=10` +
      `&size=600x400` +
      `&markers=color:red%7Clabel:S%7C${lat},${lng}` +
      `&key=YOUR_GOOGLE_MAPS_API_KEY`;
    
    // For now, create a text link (Google Sheets doesn't support embedded images easily in Apps Script)
    const mapLink = `https://www.google.com/maps?q=${lat},${lng}&z=10`;
    
    // Add clickable link
    const richText = SpreadsheetApp.newRichTextValue()
      .setText('🗺️ View on Google Maps')
      .setLinkUrl(mapLink)
      .build();
    
    sheet.getRange('A19').setRichTextValue(richText);
    
    // Add map info
    sheet.getRange('A20').setValue(`Location: ${lat.toFixed(6)}, ${lng.toFixed(6)}`);
    sheet.getRange('A21').setValue(`DNO: ${dnoData.dno_name} (${dnoData.dno_key})`);
    sheet.getRange('A22').setValue(`GSP: ${dnoData.gsp_group_id} - ${dnoData.gsp_group_name}`);
    
    Logger.log('Map link added successfully');
    
  } catch (error) {
    Logger.log('Error adding map: ' + error.toString());
    sheet.getRange('A19').setValue('Map unavailable');
  }
}

# Google Sheets Integration for Postcode Lookup
# This file provides the script to use in Google Sheets
# to send postcodes to our local API and process the results

"""
INSTRUCTIONS FOR GOOGLE SHEETS INTEGRATION:

1. Start the Flask API server by running:
   python postcode_lookup.py --api 5000

2. If running on a local machine, use ngrok or similar to expose your local server:
   ngrok http 5000

3. Copy the following script into Google Apps Script editor in your Google Sheet:

```javascript
// Custom function to look up DNO and GSP for a postcode
function LOOKUP_DNO_GSP(postcode) {
  if (!postcode) return [["No postcode provided"]];

  // Replace with your actual API endpoint (e.g. ngrok URL)
  const API_ENDPOINT = "https://your-ngrok-url.ngrok.io/lookup/postcode";

  try {
    const response = UrlFetchApp.fetch(`${API_ENDPOINT}?postcode=${encodeURIComponent(postcode)}`, {
      muteHttpExceptions: true
    });

    const result = JSON.parse(response.getContentText());

    if (result.error) {
      return [[result.error]];
    }

    // Return as a 2D array for proper display in spreadsheet cells
    return [[
      result.postcode,
      result.dno || "Not found",
      result.gsp || "Not found",
      result.is_boundary ? "Boundary" : "Non-boundary",
      result.method
    ]];
  } catch (error) {
    return [["Error: " + error.toString()]];
  }
}

// Function to batch process multiple postcodes
function BATCH_LOOKUP_DNO_GSP(postcodeRange) {
  const postcodes = postcodeRange.getValues().flat().filter(Boolean);

  if (postcodes.length === 0) {
    return [["No postcodes provided"]];
  }

  // Replace with your actual API endpoint (e.g. ngrok URL)
  const API_ENDPOINT = "https://your-ngrok-url.ngrok.io/lookup/batch";

  try {
    const response = UrlFetchApp.fetch(API_ENDPOINT, {
      method: "post",
      contentType: "application/json",
      payload: JSON.stringify({ postcodes: postcodes }),
      muteHttpExceptions: true
    });

    const resultData = JSON.parse(response.getContentText());

    if (resultData.error) {
      return [[resultData.error]];
    }

    // Convert results to a 2D array for display
    const results = resultData.results.map(result => [
      result.postcode,
      result.dno || "Not found",
      result.gsp || "Not found",
      result.is_boundary ? "Boundary" : "Non-boundary",
      result.method
    ]);

    return results;
  } catch (error) {
    return [["Error: " + error.toString()]];
  }
}

// Creates a menu item for bulk processing
function onOpen() {
  const ui = SpreadsheetApp.getUi();
  ui.createMenu('DNO/GSP Tools')
    .addItem('Batch Process Selected Postcodes', 'processBatch')
    .addToUi();
}

// Processes the selected range of postcodes and outputs results
function processBatch() {
  const sheet = SpreadsheetApp.getActiveSheet();
  const range = sheet.getActiveRange();

  if (!range) {
    SpreadsheetApp.getUi().alert('Please select a range of postcodes first.');
    return;
  }

  const postcodes = range.getValues().flat().filter(Boolean);

  if (postcodes.length === 0) {
    SpreadsheetApp.getUi().alert('No postcodes found in the selected range.');
    return;
  }

  // Create a new sheet for results if it doesn't exist
  let resultSheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName('DNO GSP Results');
  if (!resultSheet) {
    resultSheet = SpreadsheetApp.getActiveSpreadsheet().insertSheet('DNO GSP Results');
    resultSheet.appendRow(['Postcode', 'DNO', 'GSP Group', 'Boundary Status', 'Lookup Method']);
  }

  // Clear previous results (keep the header)
  if (resultSheet.getLastRow() > 1) {
    resultSheet.getRange(2, 1, resultSheet.getLastRow() - 1, 5).clear();
  }

  // Display a loading message
  SpreadsheetApp.getUi().alert(`Processing ${postcodes.length} postcodes. This may take a moment...`);

  // Get the results using the batch function
  const results = BATCH_LOOKUP_DNO_GSP(range);

  // Write the results to the sheet
  if (results.length > 0) {
    resultSheet.getRange(2, 1, results.length, results[0].length).setValues(results);
  }

  // Activate the results sheet
  resultSheet.activate();
  SpreadsheetApp.getUi().alert(`Completed processing ${postcodes.length} postcodes.`);
}
```

4. Save the script and reload your Google Sheet.

5. You'll now have a "DNO/GSP Tools" menu item in Google Sheets.

6. You can also use the formula in a cell:
   =LOOKUP_DNO_GSP(A1)
   Where A1 contains a postcode.

7. For batch processing, select a range of cells containing postcodes and use the
   "DNO/GSP Tools > Batch Process Selected Postcodes" menu item.
"""

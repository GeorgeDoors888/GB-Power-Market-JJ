// ========================================
// Google Sheets Service Account Verification
// ========================================
// Instructions: 
// 1. Open your Google Sheet: https://docs.google.com/spreadsheets/d/12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8/
// 2. Go to Extensions → Apps Script
// 3. Copy/paste these functions
// 4. Run each function and check the logs (View → Logs)
// ========================================

/**
 * Test A: List all sheet tabs
 * Verifies basic read access to spreadsheet structure
 */
function debugListTabs() {
  const ss = SpreadsheetApp.getActive();
  const names = ss.getSheets().map(s => s.getName());
  Logger.log("✅ Found " + names.length + " tabs:");
  Logger.log(names.join(", "));
  return names;
}

/**
 * Test B: Read cell A1 from Live Dashboard
 * Verifies read access to specific sheet data
 */
function debugReadA1() {
  const ss = SpreadsheetApp.getActive();
  const sh = ss.getSheetByName('Live Dashboard');
  
  if (!sh) {
    Logger.log("❌ 'Live Dashboard' sheet not found!");
    return null;
  }
  
  const value = sh.getRange('A1').getDisplayValue();
  Logger.log("✅ Live Dashboard A1 value: " + value);
  return value;
}

/**
 * Test C: Write timestamp to Audit_Log
 * Verifies write access to spreadsheet
 */
function debugWriteStamp() {
  const ss = SpreadsheetApp.getActive();
  let sh = ss.getSheetByName('Audit_Log');
  
  // Create Audit_Log sheet if it doesn't exist
  if (!sh) {
    Logger.log("⚠️ Audit_Log not found, creating new sheet...");
    sh = ss.insertSheet('Audit_Log');
    sh.appendRow(['Timestamp', 'Action', 'User', 'Status']); // Header row
  }
  
  const timestamp = new Date();
  const user = Session.getActiveUser().getEmail();
  
  sh.appendRow([timestamp, 'debugWriteStamp', user, 'ok']);
  Logger.log("✅ Successfully wrote to Audit_Log:");
  Logger.log("  Timestamp: " + timestamp);
  Logger.log("  User: " + user);
  Logger.log("  Status: ok");
  
  return true;
}

/**
 * Test D: Combined verification (runs all tests)
 * Run this to execute all checks at once
 */
function runAllVerificationTests() {
  Logger.log("========================================");
  Logger.log("Starting Service Account Verification Tests");
  Logger.log("========================================\n");
  
  // Test 1: List tabs
  Logger.log("TEST 1: List Tabs");
  try {
    const tabs = debugListTabs();
    Logger.log("✅ PASS: Found " + tabs.length + " tabs\n");
  } catch (e) {
    Logger.log("❌ FAIL: " + e.toString() + "\n");
  }
  
  // Test 2: Read A1
  Logger.log("TEST 2: Read Live Dashboard A1");
  try {
    const value = debugReadA1();
    Logger.log("✅ PASS: Read value '" + value + "'\n");
  } catch (e) {
    Logger.log("❌ FAIL: " + e.toString() + "\n");
  }
  
  // Test 3: Write to Audit_Log
  Logger.log("TEST 3: Write to Audit_Log");
  try {
    debugWriteStamp();
    Logger.log("✅ PASS: Write successful\n");
  } catch (e) {
    Logger.log("❌ FAIL: " + e.toString() + "\n");
  }
  
  Logger.log("========================================");
  Logger.log("Verification Tests Complete");
  Logger.log("========================================");
}

/**
 * Test E: Check service account permissions
 * Lists who has access to the spreadsheet
 */
function checkPermissions() {
  const ss = SpreadsheetApp.getActive();
  const file = DriveApp.getFileById(ss.getId());
  
  Logger.log("========================================");
  Logger.log("Spreadsheet Permissions:");
  Logger.log("========================================");
  Logger.log("Name: " + file.getName());
  Logger.log("ID: " + ss.getId());
  Logger.log("Owner: " + file.getOwner().getEmail());
  Logger.log("Sharing Access: " + file.getSharingAccess());
  Logger.log("Sharing Permission: " + file.getSharingPermission());
  
  Logger.log("\nEditors:");
  const editors = file.getEditors();
  editors.forEach(function(editor) {
    Logger.log("  - " + editor.getEmail());
  });
  
  Logger.log("\nViewers:");
  const viewers = file.getViewers();
  viewers.forEach(function(viewer) {
    Logger.log("  - " + viewer.getEmail());
  });
  
  // Check for service account
  const serviceAccountEmail = "jibber-jabber-knowledge@appspot.gserviceaccount.com";
  const hasServiceAccount = editors.some(e => e.getEmail() === serviceAccountEmail);
  
  if (hasServiceAccount) {
    Logger.log("\n✅ Service account found: " + serviceAccountEmail);
  } else {
    Logger.log("\n⚠️ Service account NOT found: " + serviceAccountEmail);
    Logger.log("   Add it as Editor for automation to work!");
  }
}

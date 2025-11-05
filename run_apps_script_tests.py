"""
Remote Apps Script Execution via Apps Script API
Runs the verification tests in Google Sheets without manual intervention
"""

from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
import json
import time

# Configuration
SHEET_ID = "12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8"
SA_PATH = "smart_grid_credentials.json"  # Service account credentials
SCOPES = [
    "https://www.googleapis.com/auth/script.projects",
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

def get_credentials():
    """Load service account credentials"""
    return Credentials.from_service_account_file(SA_PATH, scopes=SCOPES)

def get_script_id_from_sheet(sheets_service, sheet_id):
    """
    Get the bound Apps Script project ID from a Google Sheet
    
    Note: This requires the sheet to have a bound script.
    If no script exists, you'll need to create one first via the UI.
    """
    try:
        # Get spreadsheet metadata
        spreadsheet = sheets_service.spreadsheets().get(
            spreadsheetId=sheet_id,
            fields="spreadsheetId"
        ).execute()
        
        # Unfortunately, the Sheets API doesn't directly expose the script ID
        # You need to either:
        # 1. Manually find it: Extensions → Apps Script → Project Settings → Script ID
        # 2. Use the Drive API to find it
        
        print("⚠️  Script ID must be obtained manually:")
        print("   1. Open Sheet → Extensions → Apps Script")
        print("   2. Click Project Settings (gear icon)")
        print("   3. Copy the Script ID")
        print("   4. Set SCRIPT_ID variable below")
        
        return None
        
    except Exception as e:
        print(f"Error getting script ID: {e}")
        return None

def run_apps_script_function(script_service, script_id, function_name):
    """
    Execute a specific Apps Script function remotely
    
    Args:
        script_service: Apps Script API service
        script_id: Apps Script project ID
        function_name: Name of function to run
        
    Returns:
        dict: Execution result
    """
    try:
        # Create execution request
        request = {
            "function": function_name,
            "devMode": True  # Use draft version
        }
        
        # Execute the function
        response = script_service.scripts().run(
            scriptId=script_id,
            body=request
        ).execute()
        
        # Check for errors
        if "error" in response:
            error = response["error"]
            print(f"❌ Execution failed: {error.get('message')}")
            return {"status": "error", "error": error}
        
        # Get response
        result = response.get("response", {}).get("result")
        
        return {"status": "success", "result": result}
        
    except Exception as e:
        print(f"❌ Exception running {function_name}: {e}")
        return {"status": "exception", "error": str(e)}

def deploy_verification_script(script_service, script_id):
    """
    Upload/update the verification script code to Apps Script project
    
    This requires the Apps Script API and appropriate permissions
    """
    
    # Read the verification script
    with open("verify_sheets_access.gs", "r") as f:
        script_content = f.read()
    
    # Create script manifest
    manifest = {
        "timeZone": "Europe/London",
        "dependencies": {},
        "exceptionLogging": "STACKDRIVER"
    }
    
    # Prepare the content
    files = [
        {
            "name": "verify_sheets_access",
            "type": "SERVER_JS",
            "source": script_content
        },
        {
            "name": "appsscript",
            "type": "JSON",
            "source": json.dumps(manifest)
        }
    ]
    
    try:
        # Update the project
        response = script_service.projects().updateContent(
            scriptId=script_id,
            body={"files": files}
        ).execute()
        
        print("✅ Verification script deployed successfully")
        return True
        
    except Exception as e:
        print(f"❌ Failed to deploy script: {e}")
        return False

def run_all_verification_tests(script_id=None):
    """
    Run all verification tests via Apps Script API
    
    Args:
        script_id: Apps Script project ID (get from Project Settings)
    """
    
    if not script_id:
        print("❌ Script ID required!")
        print("\nTo find your Script ID:")
        print("1. Open: https://docs.google.com/spreadsheets/d/12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8/")
        print("2. Extensions → Apps Script")
        print("3. Project Settings (gear icon)")
        print("4. Copy the Script ID")
        print("\nThen run: python run_apps_script_tests.py <SCRIPT_ID>")
        return
    
    print("=" * 60)
    print("🔍 Remote Apps Script Verification Tests")
    print("=" * 60)
    print(f"Sheet ID: {SHEET_ID}")
    print(f"Script ID: {script_id}")
    print()
    
    # Get credentials
    try:
        creds = get_credentials()
        script_service = build("script", "v1", credentials=creds)
        print("✅ Connected to Apps Script API\n")
    except Exception as e:
        print(f"❌ Failed to connect: {e}")
        return
    
    # Run tests
    tests = [
        ("debugListTabs", "List all sheet tabs"),
        ("debugReadA1", "Read Live Dashboard A1"),
        ("debugWriteStamp", "Write to Audit_Log"),
        ("checkPermissions", "Check service account permissions")
    ]
    
    results = {}
    
    for function_name, description in tests:
        print(f"Running: {description}...")
        result = run_apps_script_function(script_service, script_id, function_name)
        results[function_name] = result
        
        if result["status"] == "success":
            print(f"  ✅ PASS")
            if result.get("result"):
                print(f"  Result: {result['result']}")
        else:
            print(f"  ❌ FAIL")
            if result.get("error"):
                print(f"  Error: {result['error']}")
        
        print()
        time.sleep(1)  # Rate limiting
    
    # Summary
    print("=" * 60)
    print("📊 Test Summary")
    print("=" * 60)
    
    passed = sum(1 for r in results.values() if r["status"] == "success")
    total = len(results)
    
    print(f"Passed: {passed}/{total}")
    
    if passed == total:
        print("\n🎉 All tests passed! Service account access is working!")
    else:
        print("\n⚠️  Some tests failed. Check errors above.")
    
    return results

def check_apps_script_api_enabled():
    """
    Helper to check if Apps Script API is enabled
    """
    try:
        creds = get_credentials()
        script_service = build("script", "v1", credentials=creds)
        
        # Try a simple API call
        script_service.projects().get(scriptId="test").execute()
        
    except Exception as e:
        error_str = str(e)
        
        if "API has not been used" in error_str or "not enabled" in error_str:
            print("⚠️  Apps Script API is not enabled!")
            print("\nTo enable:")
            print("1. Go to: https://console.cloud.google.com/apis/library/script.googleapis.com")
            print("2. Select project: jibber-jabber-knowledge")
            print("3. Click 'ENABLE'")
            print("4. Wait 1-2 minutes, then try again")
            return False
        
        # Other errors (like invalid script ID) are expected
        return True

if __name__ == "__main__":
    import sys
    
    print("🔧 Apps Script API Remote Execution Tool\n")
    
    # Check if API is enabled
    if not check_apps_script_api_enabled():
        sys.exit(1)
    
    # Get script ID from command line or prompt
    if len(sys.argv) > 1:
        script_id = sys.argv[1]
    else:
        print("Usage: python run_apps_script_tests.py <SCRIPT_ID>")
        print("\nTo find your Script ID:")
        print("1. Open: https://docs.google.com/spreadsheets/d/12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8/")
        print("2. Extensions → Apps Script")
        print("3. Project Settings (gear icon)")
        print("4. Copy the Script ID")
        print("\nExample:")
        print("  python run_apps_script_tests.py AKfycby...")
        sys.exit(1)
    
    # Run tests
    results = run_all_verification_tests(script_id)
    
    # Exit with appropriate code
    if results:
        all_passed = all(r["status"] == "success" for r in results.values())
        sys.exit(0 if all_passed else 1)
    else:
        sys.exit(1)

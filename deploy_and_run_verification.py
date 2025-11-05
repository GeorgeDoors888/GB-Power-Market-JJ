"""
Deploy Apps Script verification code and run tests remotely
This script uploads the verification functions to Apps Script and executes them
"""

from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
import json
import sys

# Configuration
SHEET_ID = "12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8"
SA_PATH = "smart_grid_credentials.json"
SCOPES = [
    "https://www.googleapis.com/auth/script.projects",
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

# Read the Apps Script code
with open("verify_sheets_access.gs", "r") as f:
    VERIFICATION_CODE = f.read()

# Apps Script manifest
MANIFEST = {
    "timeZone": "Europe/London",
    "dependencies": {},
    "exceptionLogging": "STACKDRIVER",
    "runtimeVersion": "V8",
    "oauthScopes": [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/script.external_request"
    ]
}

def get_credentials():
    """Load service account credentials"""
    return Credentials.from_service_account_file(SA_PATH, scopes=SCOPES)

def deploy_script(script_service, script_id):
    """
    Deploy the verification code to Apps Script project
    
    Args:
        script_service: Apps Script API service
        script_id: Apps Script project ID
    """
    try:
        print("📤 Deploying verification script...")
        
        # Prepare project files with manifest
        files = [
            {
                "name": "appsscript",
                "type": "JSON",
                "source": json.dumps(MANIFEST, indent=2)
            },
            {
                "name": "verify_sheets_access",
                "type": "SERVER_JS",
                "source": VERIFICATION_CODE
            }
        ]
        
        # Update the project
        response = script_service.projects().updateContent(
            scriptId=script_id,
            body={"files": files}
        ).execute()
        
        print("✅ Script deployed successfully")
        return True
        
    except Exception as e:
        print(f"❌ Deployment failed: {e}")
        return False

def run_function(script_service, script_id, function_name):
    """Execute a function and return result"""
    try:
        request = {"function": function_name, "devMode": True}
        response = script_service.scripts().run(
            scriptId=script_id,
            body=request
        ).execute()
        
        if "error" in response:
            error = response["error"]
            return {"status": "error", "error": error.get("message")}
        
        result = response.get("response", {}).get("result")
        return {"status": "success", "result": result}
        
    except Exception as e:
        return {"status": "exception", "error": str(e)}

def main():
    if len(sys.argv) < 2:
        print("Usage: python deploy_and_run_verification.py <SCRIPT_ID>")
        print("\nTo find your Script ID:")
        print("1. Open your sheet: https://docs.google.com/spreadsheets/d/12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8/")
        print("2. Go to Extensions → Apps Script")
        print("3. Click Project Settings (gear icon)")
        print("4. Copy the Script ID")
        sys.exit(1)
    
    script_id = sys.argv[1]
    
    print("=" * 60)
    print("Apps Script Verification - Deploy & Run")
    print("=" * 60)
    print(f"Script ID: {script_id}")
    print(f"Sheet ID: {SHEET_ID}")
    print(f"Service Account: {SA_PATH}")
    print()
    
    # Authenticate
    creds = get_credentials()
    script_service = build('script', 'v1', credentials=creds)
    
    # Deploy the code
    if not deploy_script(script_service, script_id):
        print("\n⚠️  Deployment failed. Trying to run existing functions...")
    
    print("\n" + "=" * 60)
    print("Running Verification Tests")
    print("=" * 60)
    
    # Test functions
    tests = [
        ("debugListTabs", "List all sheet tabs"),
        ("debugReadA1", "Read Live Dashboard A1"),
        ("debugWriteStamp", "Write to Audit_Log"),
        ("checkPermissions", "Check service account permissions")
    ]
    
    passed = 0
    failed = 0
    
    for func_name, description in tests:
        print(f"\nRunning: {description}...")
        result = run_function(script_service, script_id, func_name)
        
        if result["status"] == "success":
            print(f"✅ PASSED: {description}")
            if result.get("result"):
                print(f"   Result: {result['result']}")
            passed += 1
        else:
            print(f"❌ FAILED: {description}")
            print(f"   Error: {result.get('error', 'Unknown error')}")
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 60)
    
    if passed == len(tests):
        print("🎉 All tests passed! Service account has full access.")
        return 0
    else:
        print("⚠️  Some tests failed. Check permissions and sheet structure.")
        return 1

if __name__ == "__main__":
    sys.exit(main())

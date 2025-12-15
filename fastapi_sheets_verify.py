"""
FastAPI Google Sheets Read Endpoint
Test service account access from UpCloud server
"""

from fastapi import FastAPI, HTTPException
from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials
import os

app = FastAPI()

# Service account file path
SA_PATH = "/secrets/sa.json"
SHEETS_SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]

def get_sheets_service():
    """Create authenticated Google Sheets service"""
    if not os.path.exists(SA_PATH):
        raise FileNotFoundError(f"Service account file not found: {SA_PATH}")
    
    creds = Credentials.from_service_account_file(SA_PATH, scopes=SHEETS_SCOPES)
    service = build("sheets", "v4", credentials=creds)
    return service

@app.get("/sheets/readA1")
def read_a1(sheet_id: str):
    """
    Read cell A1 from 'Live Dashboard' sheet
    
    Example:
        curl "http://94.237.55.15:8080/sheets/readA1?sheet_id=1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA"
    
    Args:
        sheet_id: Google Sheets ID (from URL)
    
    Returns:
        {"value": "cell content", "status": "ok"}
    """
    try:
        service = get_sheets_service()
        
        # Read A1 from Live Dashboard
        result = service.spreadsheets().values().get(
            spreadsheetId=sheet_id,
            range="Live Dashboard!A1"
        ).execute()
        
        values = result.get("values", [])
        cell_value = values[0][0] if values and values[0] else ""
        
        return {
            "value": cell_value,
            "status": "ok",
            "sheet_id": sheet_id,
            "range": "Live Dashboard!A1"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/sheets/listTabs")
def list_tabs(sheet_id: str):
    """
    List all sheet tabs
    
    Example:
        curl "http://94.237.55.15:8080/sheets/listTabs?sheet_id=1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA"
    
    Args:
        sheet_id: Google Sheets ID (from URL)
    
    Returns:
        {"tabs": ["Sheet1", "Sheet2"], "count": 2}
    """
    try:
        service = get_sheets_service()
        
        # Get spreadsheet metadata
        spreadsheet = service.spreadsheets().get(spreadsheetId=sheet_id).execute()
        
        # Extract sheet names
        sheets = spreadsheet.get("sheets", [])
        tab_names = [sheet.get("properties", {}).get("title") for sheet in sheets]
        
        return {
            "tabs": tab_names,
            "count": len(tab_names),
            "status": "ok",
            "sheet_id": sheet_id
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/sheets/readRange")
def read_range(sheet_id: str, range: str):
    """
    Read any range from spreadsheet
    
    Example:
        curl "http://94.237.55.15:8080/sheets/readRange?sheet_id=1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA&range=Live%20Dashboard!A1:B10"
    
    Args:
        sheet_id: Google Sheets ID (from URL)
        range: A1 notation range (e.g., "Sheet1!A1:B10")
    
    Returns:
        {"values": [[row1], [row2]], "rows": 2}
    """
    try:
        service = get_sheets_service()
        
        # Read range
        result = service.spreadsheets().values().get(
            spreadsheetId=sheet_id,
            range=range
        ).execute()
        
        values = result.get("values", [])
        
        return {
            "values": values,
            "rows": len(values),
            "cols": len(values[0]) if values else 0,
            "status": "ok",
            "sheet_id": sheet_id,
            "range": range
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/sheets/verifyAccess")
def verify_access(sheet_id: str = "1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA"):
    """
    Comprehensive verification of service account access
    
    Example:
        curl "http://94.237.55.15:8080/sheets/verifyAccess"
    
    Returns:
        Full diagnostic info about access status
    """
    results = {
        "sheet_id": sheet_id,
        "tests": {}
    }
    
    try:
        service = get_sheets_service()
        
        # Test 1: List tabs
        try:
            spreadsheet = service.spreadsheets().get(spreadsheetId=sheet_id).execute()
            sheets = spreadsheet.get("sheets", [])
            tab_names = [sheet.get("properties", {}).get("title") for sheet in sheets]
            
            results["tests"]["list_tabs"] = {
                "status": "✅ PASS",
                "tabs": tab_names,
                "count": len(tab_names)
            }
        except Exception as e:
            results["tests"]["list_tabs"] = {
                "status": "❌ FAIL",
                "error": str(e)
            }
        
        # Test 2: Read A1
        try:
            result = service.spreadsheets().values().get(
                spreadsheetId=sheet_id,
                range="Live Dashboard!A1"
            ).execute()
            
            values = result.get("values", [])
            cell_value = values[0][0] if values and values[0] else ""
            
            results["tests"]["read_a1"] = {
                "status": "✅ PASS",
                "value": cell_value
            }
        except Exception as e:
            results["tests"]["read_a1"] = {
                "status": "❌ FAIL",
                "error": str(e)
            }
        
        # Overall status
        all_pass = all(
            test.get("status", "").startswith("✅")
            for test in results["tests"].values()
        )
        
        results["overall_status"] = "✅ ALL TESTS PASSED" if all_pass else "❌ SOME TESTS FAILED"
        
    except Exception as e:
        results["overall_status"] = "❌ CRITICAL FAILURE"
        results["error"] = str(e)
    
    return results

# Health check (already exists, but include for completeness)
@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {"ok": True}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)

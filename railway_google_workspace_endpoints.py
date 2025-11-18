"""
Railway API Endpoints for Google Workspace Access
Add these to your Railway API to enable ChatGPT to read/write Sheets, Drive, Docs

Deploy workspace-credentials.json to Railway first!
"""

from fastapi import FastAPI, HTTPException, Depends, Header
from google.oauth2 import service_account
from googleapiclient.discovery import build
import gspread
from typing import Optional, List, Dict
import os

app = FastAPI()

# Security
API_TOKEN = os.getenv("CODEX_API_TOKEN", "codex_fQI8xJXNPnhasYBOjd6h7mPHoF7HNI0Dh8rlgoJ2skA")

def verify_token(authorization: str = Header(None)):
    """Verify bearer token"""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid authorization header")
    token = authorization.replace("Bearer ", "")
    if token != API_TOKEN:
        raise HTTPException(status_code=401, detail="Invalid token")
    return token

# Workspace credentials path (deploy this file to Railway!)
WORKSPACE_CREDS = os.getenv("WORKSPACE_CREDENTIALS_PATH", "workspace-credentials.json")
ADMIN_EMAIL = "george@upowerenergy.uk"

# ============================================================================
# GOOGLE SHEETS ENDPOINTS
# ============================================================================

@app.post("/read_sheet")
def read_sheet(
    sheet_id: str,
    worksheet: str = "Sheet1",
    range_name: Optional[str] = None,
    token: str = Depends(verify_token)
):
    """
    Read data from Google Sheets
    
    Example:
    POST /read_sheet
    {
        "sheet_id": "12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8",
        "worksheet": "Dashboard",
        "range_name": "A1:E10"  // optional
    }
    """
    try:
        creds = service_account.Credentials.from_service_account_file(
            WORKSPACE_CREDS,
            scopes=['https://www.googleapis.com/auth/spreadsheets']
        ).with_subject(ADMIN_EMAIL)
        
        gc = gspread.authorize(creds)
        spreadsheet = gc.open_by_key(sheet_id)
        ws = spreadsheet.worksheet(worksheet)
        
        if range_name:
            data = ws.get(range_name)
        else:
            data = ws.get_all_records()
        
        return {
            "status": "success",
            "spreadsheet": spreadsheet.title,
            "worksheet": worksheet,
            "rows": len(data) if isinstance(data, list) else len(data[0]) if data else 0,
            "data": data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading sheet: {str(e)}")


@app.post("/write_sheet")
def write_sheet(
    sheet_id: str,
    worksheet: str,
    data: List[List],
    range_name: str = "A1",
    token: str = Depends(verify_token)
):
    """
    Write data to Google Sheets
    
    Example:
    POST /write_sheet
    {
        "sheet_id": "12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8",
        "worksheet": "Dashboard",
        "data": [["Header1", "Header2"], ["Value1", "Value2"]],
        "range_name": "A1"
    }
    """
    try:
        creds = service_account.Credentials.from_service_account_file(
            WORKSPACE_CREDS,
            scopes=['https://www.googleapis.com/auth/spreadsheets']
        ).with_subject(ADMIN_EMAIL)
        
        gc = gspread.authorize(creds)
        spreadsheet = gc.open_by_key(sheet_id)
        ws = spreadsheet.worksheet(worksheet)
        
        ws.update(range_name, data)
        
        return {
            "status": "success",
            "spreadsheet": spreadsheet.title,
            "worksheet": worksheet,
            "rows_written": len(data)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error writing sheet: {str(e)}")


@app.get("/list_worksheets")
def list_worksheets(
    sheet_id: str,
    token: str = Depends(verify_token)
):
    """
    List all worksheets in a spreadsheet
    
    Example:
    GET /list_worksheets?sheet_id=12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8
    """
    try:
        creds = service_account.Credentials.from_service_account_file(
            WORKSPACE_CREDS,
            scopes=['https://www.googleapis.com/auth/spreadsheets']
        ).with_subject(ADMIN_EMAIL)
        
        gc = gspread.authorize(creds)
        spreadsheet = gc.open_by_key(sheet_id)
        
        worksheets = []
        for ws in spreadsheet.worksheets():
            worksheets.append({
                "title": ws.title,
                "id": ws.id,
                "rows": ws.row_count,
                "cols": ws.col_count
            })
        
        return {
            "status": "success",
            "spreadsheet": spreadsheet.title,
            "worksheets": worksheets,
            "count": len(worksheets)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing worksheets: {str(e)}")


# ============================================================================
# GOOGLE DRIVE ENDPOINTS
# ============================================================================

@app.get("/list_drive_files")
def list_drive_files(
    query: Optional[str] = None,
    page_size: int = 20,
    token: str = Depends(verify_token)
):
    """
    List files from Google Drive
    
    Examples:
    GET /list_drive_files?query=name contains 'battery'
    GET /list_drive_files?query=mimeType='application/vnd.google-apps.spreadsheet'
    """
    try:
        creds = service_account.Credentials.from_service_account_file(
            WORKSPACE_CREDS,
            scopes=['https://www.googleapis.com/auth/drive.readonly']
        ).with_subject(ADMIN_EMAIL)
        
        drive = build('drive', 'v3', credentials=creds)
        
        params = {
            'pageSize': page_size,
            'fields': 'files(id, name, mimeType, modifiedTime, size, webViewLink)'
        }
        
        if query:
            params['q'] = query
        
        results = drive.files().list(**params).execute()
        files = results.get('files', [])
        
        return {
            "status": "success",
            "count": len(files),
            "files": files
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing drive files: {str(e)}")


@app.get("/search_drive")
def search_drive(
    name: Optional[str] = None,
    mime_type: Optional[str] = None,
    modified_after: Optional[str] = None,
    token: str = Depends(verify_token)
):
    """
    Search Google Drive with common filters
    
    Example:
    GET /search_drive?name=battery&mime_type=spreadsheet
    """
    try:
        creds = service_account.Credentials.from_service_account_file(
            WORKSPACE_CREDS,
            scopes=['https://www.googleapis.com/auth/drive.readonly']
        ).with_subject(ADMIN_EMAIL)
        
        drive = build('drive', 'v3', credentials=creds)
        
        # Build query
        query_parts = []
        if name:
            query_parts.append(f"name contains '{name}'")
        if mime_type:
            if mime_type == 'spreadsheet':
                query_parts.append("mimeType='application/vnd.google-apps.spreadsheet'")
            elif mime_type == 'document':
                query_parts.append("mimeType='application/vnd.google-apps.document'")
            elif mime_type == 'csv':
                query_parts.append("mimeType='text/csv'")
            else:
                query_parts.append(f"mimeType='{mime_type}'")
        if modified_after:
            query_parts.append(f"modifiedTime > '{modified_after}'")
        
        query = " and ".join(query_parts) if query_parts else None
        
        params = {
            'pageSize': 50,
            'fields': 'files(id, name, mimeType, modifiedTime, webViewLink)'
        }
        if query:
            params['q'] = query
        
        results = drive.files().list(**params).execute()
        files = results.get('files', [])
        
        return {
            "status": "success",
            "query": query,
            "count": len(files),
            "files": files
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error searching drive: {str(e)}")


# ============================================================================
# GOOGLE DOCS ENDPOINTS
# ============================================================================

@app.get("/read_doc")
def read_doc(
    doc_id: str,
    token: str = Depends(verify_token)
):
    """
    Read content from Google Doc
    
    Example:
    GET /read_doc?doc_id=YOUR_DOC_ID
    """
    try:
        creds = service_account.Credentials.from_service_account_file(
            WORKSPACE_CREDS,
            scopes=['https://www.googleapis.com/auth/documents.readonly']
        ).with_subject(ADMIN_EMAIL)
        
        docs = build('docs', 'v1', credentials=creds)
        document = docs.documents().get(documentId=doc_id).execute()
        
        # Extract text content
        content = []
        for element in document.get('body', {}).get('content', []):
            if 'paragraph' in element:
                for text_run in element['paragraph'].get('elements', []):
                    if 'textRun' in text_run:
                        content.append(text_run['textRun']['content'])
        
        return {
            "status": "success",
            "title": document.get('title'),
            "doc_id": doc_id,
            "content": ''.join(content)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading doc: {str(e)}")


@app.post("/create_doc")
def create_doc(
    title: str,
    content: Optional[str] = None,
    token: str = Depends(verify_token)
):
    """
    Create new Google Doc
    
    Example:
    POST /create_doc
    {
        "title": "Weekly Battery Report",
        "content": "Battery revenue analysis..."
    }
    """
    try:
        creds = service_account.Credentials.from_service_account_file(
            WORKSPACE_CREDS,
            scopes=['https://www.googleapis.com/auth/documents']
        ).with_subject(ADMIN_EMAIL)
        
        docs = build('docs', 'v1', credentials=creds)
        
        # Create document
        doc = docs.documents().create(body={'title': title}).execute()
        doc_id = doc['documentId']
        
        # Add content if provided
        if content:
            requests = [
                {
                    'insertText': {
                        'location': {'index': 1},
                        'text': content
                    }
                }
            ]
            docs.documents().batchUpdate(
                documentId=doc_id,
                body={'requests': requests}
            ).execute()
        
        return {
            "status": "success",
            "title": title,
            "doc_id": doc_id,
            "url": f"https://docs.google.com/document/d/{doc_id}"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating doc: {str(e)}")


# ============================================================================
# CONVENIENCE ENDPOINTS
# ============================================================================

@app.get("/gb_energy_dashboard")
def gb_energy_dashboard(token: str = Depends(verify_token)):
    """Quick access to GB Energy Dashboard"""
    return list_worksheets(
        sheet_id="12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8",
        token=token
    )


@app.get("/workspace_health")
def workspace_health(token: str = Depends(verify_token)):
    """Check Google Workspace access health"""
    try:
        # Test Sheets
        sheets_creds = service_account.Credentials.from_service_account_file(
            WORKSPACE_CREDS,
            scopes=['https://www.googleapis.com/auth/spreadsheets']
        ).with_subject(ADMIN_EMAIL)
        gc = gspread.authorize(sheets_creds)
        sheets_ok = True
        
        # Test Drive
        drive_creds = service_account.Credentials.from_service_account_file(
            WORKSPACE_CREDS,
            scopes=['https://www.googleapis.com/auth/drive.readonly']
        ).with_subject(ADMIN_EMAIL)
        drive = build('drive', 'v3', credentials=drive_creds)
        drive.files().list(pageSize=1).execute()
        drive_ok = True
        
        # Test Docs
        docs_creds = service_account.Credentials.from_service_account_file(
            WORKSPACE_CREDS,
            scopes=['https://www.googleapis.com/auth/documents.readonly']
        ).with_subject(ADMIN_EMAIL)
        docs = build('docs', 'v1', credentials=docs_creds)
        docs_ok = True
        
        return {
            "status": "healthy",
            "services": {
                "sheets": "ok" if sheets_ok else "error",
                "drive": "ok" if drive_ok else "error",
                "docs": "ok" if docs_ok else "error"
            }
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

from fastapi import FastAPI, HTTPException, Header, Request
from pydantic import BaseModel
import subprocess
import tempfile
import os
import time
import logging
from typing import Optional
import secrets

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Generate a secure API token
# IMPORTANT: Save this token! You'll need it to authenticate requests
API_TOKEN = os.getenv("CODEX_API_TOKEN") or f"codex_{secrets.token_urlsafe(32)}"

app = FastAPI(
    title="Codex Server",
    description="Secure code execution server for Python and JavaScript",
    version="1.0.0"
)

class CodeRequest(BaseModel):
    code: str
    language: str = "python"
    timeout: int = 10

class CodeResponse(BaseModel):
    output: str
    error: Optional[str] = None
    exit_code: int
    execution_time: float
    timestamp: str

# Security: List of forbidden patterns
FORBIDDEN_PATTERNS = [
    'import os',
    'import sys',
    'import subprocess',
    'import shutil',
    '__import__',
    'eval(',
    'exec(',
    'compile(',
    'open(',
]

def verify_token(authorization: Optional[str] = Header(None)) -> bool:
    """Verify the API token from Authorization header"""
    if not authorization:
        raise HTTPException(
            status_code=401,
            detail="Missing Authorization header. Include: 'Authorization: Bearer YOUR_TOKEN'"
        )
    
    # Extract token from "Bearer TOKEN" format
    try:
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            raise HTTPException(
                status_code=401,
                detail="Invalid authentication scheme. Use: 'Authorization: Bearer YOUR_TOKEN'"
            )
        
        if token != API_TOKEN:
            raise HTTPException(
                status_code=401,
                detail="Invalid API token"
            )
        
        return True
    except ValueError:
        raise HTTPException(
            status_code=401,
            detail="Invalid Authorization header format. Use: 'Authorization: Bearer YOUR_TOKEN'"
        )

def validate_code(code: str, language: str):
    """Validate code for security issues"""
    code_lower = code.lower()
    
    for pattern in FORBIDDEN_PATTERNS:
        if pattern.lower() in code_lower:
            raise HTTPException(
                status_code=400,
                detail=f"Forbidden pattern detected: {pattern}"
            )

def execute_python(code: str, timeout: int) -> CodeResponse:
    """Execute Python code safely"""
    start_time = time.time()
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(code)
        temp_file = f.name
    
    try:
        result = subprocess.run(
            ['python', temp_file],
            capture_output=True,
            text=True,
            timeout=timeout
        )
        
        execution_time = time.time() - start_time
        
        return CodeResponse(
            output=result.stdout,
            error=result.stderr if result.stderr else None,
            exit_code=result.returncode,
            execution_time=round(execution_time, 6),
            timestamp=time.strftime("%Y-%m-%d %H:%M:%S")
        )
    except subprocess.TimeoutExpired:
        execution_time = time.time() - start_time
        return CodeResponse(
            output="",
            error=f"Execution timed out after {timeout} seconds",
            exit_code=-1,
            execution_time=round(execution_time, 6),
            timestamp=time.strftime("%Y-%m-%d %H:%M:%S")
        )
    finally:
        os.unlink(temp_file)

def execute_javascript(code: str, timeout: int) -> CodeResponse:
    """Execute JavaScript code safely"""
    start_time = time.time()
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.js', delete=False) as f:
        f.write(code)
        temp_file = f.name
    
    try:
        result = subprocess.run(
            ['node', temp_file],
            capture_output=True,
            text=True,
            timeout=timeout
        )
        
        execution_time = time.time() - start_time
        
        return CodeResponse(
            output=result.stdout,
            error=result.stderr if result.stderr else None,
            exit_code=result.returncode,
            execution_time=round(execution_time, 6),
            timestamp=time.strftime("%Y-%m-%d %H:%M:%S")
        )
    except subprocess.TimeoutExpired:
        execution_time = time.time() - start_time
        return CodeResponse(
            output="",
            error=f"Execution timed out after {timeout} seconds",
            exit_code=-1,
            execution_time=round(execution_time, 6),
            timestamp=time.strftime("%Y-%m-%d %H:%M:%S")
        )
    finally:
        os.unlink(temp_file)

@app.get("/")
async def root():
    """Root endpoint with server information"""
    return {
        "name": "Codex Server",
        "version": "1.0.0",
        "status": "running",
        "authentication": "required",
        "endpoints": {
            "health": "/health",
            "execute": "/execute (POST)",
            "languages": "/languages",
            "docs": "/docs"
        },
        "note": "Authentication required. Include 'Authorization: Bearer YOUR_TOKEN' header"
    }

@app.get("/health")
async def health_check():
    """Public health check endpoint (no auth required)"""
    return {
        "status": "healthy",
        "version": "1.0.0",
        "languages": ["python", "javascript"],
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    }

@app.post("/execute", response_model=CodeResponse)
async def execute_code(
    request: CodeRequest,
    authorization: Optional[str] = Header(None)
):
    """
    Execute code with authentication.
    
    Requires Authorization header: Bearer YOUR_TOKEN
    """
    # Verify authentication
    verify_token(authorization)
    
    # Log request
    logger.info(f"Received execution request for {request.language}")
    
    # Validate code
    validate_code(request.code, request.language)
    
    # Execute based on language
    if request.language == "python":
        logger.info(f"Executing Python code: {request.code[:100]}...")
        result = execute_python(request.code, request.timeout)
    elif request.language == "javascript":
        logger.info(f"Executing JavaScript code: {request.code[:100]}...")
        result = execute_javascript(request.code, request.timeout)
    else:
        raise HTTPException(400, f"Unsupported language: {request.language}")
    
    logger.info(f"Execution completed: exit_code={result.exit_code}, time={result.execution_time}s")
    return result

@app.get("/languages")
async def list_languages():
    """List supported programming languages (no auth required)"""
    return {
        "languages": [
            {
                "name": "python",
                "version": subprocess.run(['python', '--version'], capture_output=True, text=True).stdout.strip(),
                "available": True
            },
            {
                "name": "javascript",
                "version": "node",
                "available": True
            }
        ]
    }

# ============================================
# GOOGLE WORKSPACE ENDPOINTS
# ============================================

@app.get("/workspace/health")
async def workspace_health(authorization: Optional[str] = Header(None)):
    """Check if Workspace delegation is working"""
    verify_token(authorization)
    
    try:
        import base64
        import json
        from google.oauth2 import service_account
        import gspread
        
        # Get workspace credentials from environment
        workspace_creds_base64 = os.getenv("GOOGLE_WORKSPACE_CREDENTIALS")
        if not workspace_creds_base64:
            return {
                "status": "error",
                "message": "GOOGLE_WORKSPACE_CREDENTIALS not found in environment"
            }
        
        # Decode credentials
        creds_json = base64.b64decode(workspace_creds_base64).decode('utf-8')
        creds_dict = json.loads(creds_json)
        
        # Create credentials with delegation
        credentials = service_account.Credentials.from_service_account_info(
            creds_dict,
            scopes=['https://www.googleapis.com/auth/spreadsheets',
                   'https://www.googleapis.com/auth/drive']
        ).with_subject('george@upowerenergy.uk')
        
        # Test access
        gc = gspread.authorize(credentials)
        
        # List accessible spreadsheets
        spreadsheets = gc.openall()
        
        return {
            "status": "healthy",
            "message": "Workspace access working!",
            "services": {
                "sheets": "ok",
                "drive": "ok"
            },
            "accessible_spreadsheets": len(spreadsheets),
            "sample_spreadsheets": [
                {"title": s.title, "id": s.id, "url": s.url} 
                for s in spreadsheets[:5]
            ]
        }
    except Exception as e:
        logger.error(f"Workspace health check failed: {e}")
        return {
            "status": "error",
            "message": str(e)
        }


@app.get("/workspace/list_spreadsheets")
async def list_spreadsheets(authorization: Optional[str] = Header(None)):
    """List all accessible Google Sheets spreadsheets"""
    verify_token(authorization)
    
    try:
        import base64
        import json
        from google.oauth2 import service_account
        import gspread
        
        # Get workspace credentials
        workspace_creds_base64 = os.getenv("GOOGLE_WORKSPACE_CREDENTIALS")
        if not workspace_creds_base64:
            raise HTTPException(status_code=503, detail="Workspace credentials not configured")
        
        creds_json = base64.b64decode(workspace_creds_base64).decode('utf-8')
        creds_dict = json.loads(creds_json)
        
        credentials = service_account.Credentials.from_service_account_info(
            creds_dict,
            scopes=['https://www.googleapis.com/auth/spreadsheets',
                   'https://www.googleapis.com/auth/drive']
        ).with_subject('george@upowerenergy.uk')
        
        gc = gspread.authorize(credentials)
        spreadsheets = gc.openall()
        
        results = []
        for sheet in spreadsheets:
            results.append({
                "title": sheet.title,
                "id": sheet.id,
                "url": sheet.url,
                "worksheets": len(sheet.worksheets())
            })
        
        return {
            "success": True,
            "total_spreadsheets": len(results),
            "spreadsheets": results
        }
    except Exception as e:
        logger.error(f"List spreadsheets error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/workspace/get_spreadsheet")
async def get_spreadsheet_info(request: Request, authorization: Optional[str] = Header(None)):
    """Get information about a specific spreadsheet by ID or title"""
    verify_token(authorization)
    
    try:
        import base64
        import json
        from google.oauth2 import service_account
        import gspread
        
        body = await request.json()
        spreadsheet_id = body.get('spreadsheet_id')
        spreadsheet_title = body.get('spreadsheet_title')
        
        if not spreadsheet_id and not spreadsheet_title:
            raise HTTPException(status_code=400, detail="Must provide spreadsheet_id or spreadsheet_title")
        
        # Get workspace credentials
        workspace_creds_base64 = os.getenv("GOOGLE_WORKSPACE_CREDENTIALS")
        if not workspace_creds_base64:
            raise HTTPException(status_code=503, detail="Workspace credentials not configured")
        
        creds_json = base64.b64decode(workspace_creds_base64).decode('utf-8')
        creds_dict = json.loads(creds_json)
        
        credentials = service_account.Credentials.from_service_account_info(
            creds_dict,
            scopes=['https://www.googleapis.com/auth/spreadsheets',
                   'https://www.googleapis.com/auth/drive']
        ).with_subject('george@upowerenergy.uk')
        
        gc = gspread.authorize(credentials)
        
        # Open by ID or title
        if spreadsheet_id:
            sheet = gc.open_by_key(spreadsheet_id)
        else:
            sheet = gc.open(spreadsheet_title)
        
        worksheets = []
        for ws in sheet.worksheets():
            worksheets.append({
                "id": ws.id,
                "title": ws.title,
                "rows": ws.row_count,
                "cols": ws.col_count
            })
        
        return {
            "success": True,
            "title": sheet.title,
            "spreadsheet_id": sheet.id,
            "url": sheet.url,
            "worksheets": worksheets,
            "total_worksheets": len(worksheets)
        }
    except Exception as e:
        logger.error(f"Get spreadsheet error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/workspace/read_sheet")
async def read_sheet_data(request: Request, authorization: Optional[str] = Header(None)):
    """Read data from any worksheet in any accessible spreadsheet"""
    verify_token(authorization)
    
    try:
        import base64
        import json
        from google.oauth2 import service_account
        import gspread
        
        # Get request body
        body = await request.json()
        spreadsheet_id = body.get('spreadsheet_id', '12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8')  # Default to GB Energy Dashboard
        spreadsheet_title = body.get('spreadsheet_title')
        worksheet_name = body.get('worksheet_name', 'Dashboard')
        cell_range = body.get('cell_range', '')
        
        # Get workspace credentials
        workspace_creds_base64 = os.getenv("GOOGLE_WORKSPACE_CREDENTIALS")
        if not workspace_creds_base64:
            raise HTTPException(status_code=503, detail="Workspace credentials not configured")
        
        creds_json = base64.b64decode(workspace_creds_base64).decode('utf-8')
        creds_dict = json.loads(creds_json)
        
        credentials = service_account.Credentials.from_service_account_info(
            creds_dict,
            scopes=['https://www.googleapis.com/auth/spreadsheets',
                   'https://www.googleapis.com/auth/drive']
        ).with_subject('george@upowerenergy.uk')
        
        gc = gspread.authorize(credentials)
        
        # Open spreadsheet by ID or title
        if spreadsheet_title:
            sheet = gc.open(spreadsheet_title)
        else:
            sheet = gc.open_by_key(spreadsheet_id)
        
        worksheet = sheet.worksheet(worksheet_name)
        
        if cell_range:
            data = worksheet.get(cell_range)
        else:
            data = worksheet.get_all_values()
        
        return {
            "success": True,
            "spreadsheet_title": sheet.title,
            "spreadsheet_id": sheet.id,
            "worksheet_name": worksheet_name,
            "rows": len(data),
            "cols": len(data[0]) if data else 0,
            "data": data[:100]  # Limit to first 100 rows
        }
    except Exception as e:
        logger.error(f"Read sheet error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/workspace/write_sheet")
async def write_sheet_data(request: Request, authorization: Optional[str] = Header(None)):
    """Write/update data in a Google Sheet"""
    verify_token(authorization)
    
    try:
        import base64
        import json
        from google.oauth2 import service_account
        import gspread
        
        body = await request.json()
        spreadsheet_id = body.get('spreadsheet_id', '12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8')
        spreadsheet_title = body.get('spreadsheet_title')
        worksheet_name = body.get('worksheet_name', 'Dashboard')
        cell_range = body.get('cell_range')  # Required for writing
        values = body.get('values')  # 2D array of values to write
        
        if not cell_range or not values:
            raise HTTPException(status_code=400, detail="Must provide cell_range and values")
        
        # Get workspace credentials
        workspace_creds_base64 = os.getenv("GOOGLE_WORKSPACE_CREDENTIALS")
        if not workspace_creds_base64:
            raise HTTPException(status_code=503, detail="Workspace credentials not configured")
        
        creds_json = base64.b64decode(workspace_creds_base64).decode('utf-8')
        creds_dict = json.loads(creds_json)
        
        credentials = service_account.Credentials.from_service_account_info(
            creds_dict,
            scopes=['https://www.googleapis.com/auth/spreadsheets',
                   'https://www.googleapis.com/auth/drive']
        ).with_subject('george@upowerenergy.uk')
        
        gc = gspread.authorize(credentials)
        
        # Open spreadsheet
        if spreadsheet_title:
            sheet = gc.open(spreadsheet_title)
        else:
            sheet = gc.open_by_key(spreadsheet_id)
        
        worksheet = sheet.worksheet(worksheet_name)
        
        # Write data
        worksheet.update(cell_range, values)
        
        return {
            "success": True,
            "spreadsheet_title": sheet.title,
            "worksheet_name": worksheet_name,
            "cell_range": cell_range,
            "rows_written": len(values)
        }
    except Exception as e:
        logger.error(f"Write sheet error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/workspace/list_drive_files")
async def list_drive_files(authorization: Optional[str] = Header(None), file_type: Optional[str] = None):
    """List all files in Google Drive (Docs, Sheets, PDFs, etc.)"""
    verify_token(authorization)
    
    try:
        import base64
        import json
        from google.oauth2 import service_account
        from googleapiclient.discovery import build
        
        # Get workspace credentials
        workspace_creds_base64 = os.getenv("GOOGLE_WORKSPACE_CREDENTIALS")
        if not workspace_creds_base64:
            raise HTTPException(status_code=503, detail="Workspace credentials not configured")
        
        creds_json = base64.b64decode(workspace_creds_base64).decode('utf-8')
        creds_dict = json.loads(creds_json)
        
        credentials = service_account.Credentials.from_service_account_info(
            creds_dict,
            scopes=['https://www.googleapis.com/auth/drive']
        ).with_subject('george@upowerenergy.uk')
        
        drive_service = build('drive', 'v3', credentials=credentials)
        
        # Build query
        query_parts = []
        if file_type:
            mime_types = {
                'doc': 'application/vnd.google-apps.document',
                'sheet': 'application/vnd.google-apps.spreadsheet',
                'slide': 'application/vnd.google-apps.presentation',
                'pdf': 'application/pdf',
                'folder': 'application/vnd.google-apps.folder'
            }
            mime = mime_types.get(file_type.lower())
            if mime:
                query_parts.append(f"mimeType='{mime}'")
        
        query = " and ".join(query_parts) if query_parts else None
        
        # List files
        results = drive_service.files().list(
            q=query,
            pageSize=100,
            fields="files(id, name, mimeType, modifiedTime, size, webViewLink)"
        ).execute()
        
        files = results.get('files', [])
        
        return {
            "success": True,
            "total_files": len(files),
            "files": files
        }
    except Exception as e:
        logger.error(f"List drive files error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/workspace/search_drive")
async def search_drive(request: Request, authorization: Optional[str] = Header(None)):
    """Search Google Drive by filename or content"""
    verify_token(authorization)
    
    try:
        import base64
        import json
        from google.oauth2 import service_account
        from googleapiclient.discovery import build
        
        body = await request.json()
        search_query = body.get('query', '')
        file_type = body.get('file_type')  # 'doc', 'sheet', 'slide', 'pdf', 'folder'
        
        if not search_query:
            raise HTTPException(status_code=400, detail="Must provide search query")
        
        # Get workspace credentials
        workspace_creds_base64 = os.getenv("GOOGLE_WORKSPACE_CREDENTIALS")
        if not workspace_creds_base64:
            raise HTTPException(status_code=503, detail="Workspace credentials not configured")
        
        creds_json = base64.b64decode(workspace_creds_base64).decode('utf-8')
        creds_dict = json.loads(creds_json)
        
        credentials = service_account.Credentials.from_service_account_info(
            creds_dict,
            scopes=['https://www.googleapis.com/auth/drive']
        ).with_subject('george@upowerenergy.uk')
        
        drive_service = build('drive', 'v3', credentials=credentials)
        
        # Build query
        query_parts = [f"name contains '{search_query}' or fullText contains '{search_query}'"]
        
        if file_type:
            mime_types = {
                'doc': 'application/vnd.google-apps.document',
                'sheet': 'application/vnd.google-apps.spreadsheet',
                'slide': 'application/vnd.google-apps.presentation',
                'pdf': 'application/pdf',
                'folder': 'application/vnd.google-apps.folder'
            }
            mime = mime_types.get(file_type.lower())
            if mime:
                query_parts.append(f"mimeType='{mime}'")
        
        query = " and ".join(query_parts)
        
        # Search files
        results = drive_service.files().list(
            q=query,
            pageSize=50,
            fields="files(id, name, mimeType, modifiedTime, webViewLink)"
        ).execute()
        
        files = results.get('files', [])
        
        return {
            "success": True,
            "query": search_query,
            "results_count": len(files),
            "files": files
        }
    except Exception as e:
        logger.error(f"Search drive error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/workspace/read_doc")
async def read_google_doc(request: Request, authorization: Optional[str] = Header(None)):
    """Read content from a Google Doc"""
    verify_token(authorization)
    
    try:
        import base64
        import json
        from google.oauth2 import service_account
        from googleapiclient.discovery import build
        
        body = await request.json()
        document_id = body.get('document_id')
        document_title = body.get('document_title')
        
        if not document_id and not document_title:
            raise HTTPException(status_code=400, detail="Must provide document_id or document_title")
        
        # Get workspace credentials
        workspace_creds_base64 = os.getenv("GOOGLE_WORKSPACE_CREDENTIALS")
        if not workspace_creds_base64:
            raise HTTPException(status_code=503, detail="Workspace credentials not configured")
        
        creds_json = base64.b64decode(workspace_creds_base64).decode('utf-8')
        creds_dict = json.loads(creds_json)
        
        credentials = service_account.Credentials.from_service_account_info(
            creds_dict,
            scopes=['https://www.googleapis.com/auth/documents.readonly',
                   'https://www.googleapis.com/auth/drive.readonly']
        ).with_subject('george@upowerenergy.uk')
        
        # Find document by title if needed
        if document_title and not document_id:
            drive_service = build('drive', 'v3', credentials=credentials)
            results = drive_service.files().list(
                q=f"name='{document_title}' and mimeType='application/vnd.google-apps.document'",
                fields="files(id)"
            ).execute()
            files = results.get('files', [])
            if not files:
                raise HTTPException(status_code=404, detail=f"Document '{document_title}' not found")
            document_id = files[0]['id']
        
        # Read document
        docs_service = build('docs', 'v1', credentials=credentials)
        document = docs_service.documents().get(documentId=document_id).execute()
        
        # Extract text content
        content = []
        for element in document.get('body', {}).get('content', []):
            if 'paragraph' in element:
                for text_run in element['paragraph'].get('elements', []):
                    if 'textRun' in text_run:
                        content.append(text_run['textRun']['content'])
        
        full_text = ''.join(content)
        
        return {
            "success": True,
            "document_id": document['documentId'],
            "title": document.get('title'),
            "content": full_text,
            "character_count": len(full_text)
        }
    except Exception as e:
        logger.error(f"Read doc error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/workspace/write_doc")
async def write_google_doc(request: Request, authorization: Optional[str] = Header(None)):
    """Write/update content in a Google Doc"""
    verify_token(authorization)
    
    try:
        import base64
        import json
        from google.oauth2 import service_account
        from googleapiclient.discovery import build
        
        body = await request.json()
        document_id = body.get('document_id')
        content = body.get('content')
        append = body.get('append', False)  # Append or replace
        
        if not document_id or not content:
            raise HTTPException(status_code=400, detail="Must provide document_id and content")
        
        # Get workspace credentials
        workspace_creds_base64 = os.getenv("GOOGLE_WORKSPACE_CREDENTIALS")
        if not workspace_creds_base64:
            raise HTTPException(status_code=503, detail="Workspace credentials not configured")
        
        creds_json = base64.b64decode(workspace_creds_base64).decode('utf-8')
        creds_dict = json.loads(creds_json)
        
        credentials = service_account.Credentials.from_service_account_info(
            creds_dict,
            scopes=['https://www.googleapis.com/auth/documents',
                   'https://www.googleapis.com/auth/drive']
        ).with_subject('george@upowerenergy.uk')
        
        docs_service = build('docs', 'v1', credentials=credentials)
        
        # Get document
        document = docs_service.documents().get(documentId=document_id).execute()
        
        requests = []
        
        if not append:
            # Delete all content first
            requests.append({
                'deleteContentRange': {
                    'range': {
                        'startIndex': 1,
                        'endIndex': len(document.get('body', {}).get('content', [])) + 1
                    }
                }
            })
        
        # Insert new content
        requests.append({
            'insertText': {
                'location': {
                    'index': 1
                },
                'text': content
            }
        })
        
        # Execute updates
        docs_service.documents().batchUpdate(
            documentId=document_id,
            body={'requests': requests}
        ).execute()
        
        return {
            "success": True,
            "document_id": document_id,
            "title": document.get('title'),
            "action": "appended" if append else "replaced",
            "characters_written": len(content)
        }
    except Exception as e:
        logger.error(f"Write doc error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    
    # Print the API token on startup
    print("\n" + "="*60)
    print("🚀 Codex Server Starting...")
    print("="*60)
    print(f"\n🔑 Your API Token (SAVE THIS!):")
    print(f"   {API_TOKEN}")
    print(f"\n📋 How to use:")
    print(f"   Include this header in all requests:")
    print(f"   Authorization: Bearer {API_TOKEN}")
    print(f"\n🧪 Test with curl:")
    print(f'   curl -X POST http://localhost:8000/execute \\')
    print(f'     -H "Authorization: Bearer {API_TOKEN}" \\')
    print(f'     -H "Content-Type: application/json" \\')
    print(f'     -d \'{{"code": "print(\\"Hello!\\")", "language": "python"}}\'')
    print(f"\n📖 API Documentation: http://localhost:8000/docs")
    print("="*60 + "\n")
    
    # Use PORT environment variable for Railway, default to 8000 for local
    port = int(os.getenv("PORT", 8000))
    logger.info(f"Starting Codex Server on port {port}...")
    uvicorn.run(app, host="0.0.0.0", port=port)

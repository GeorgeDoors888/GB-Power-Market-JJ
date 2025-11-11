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
                   'https://www.googleapis.com/auth/drive.readonly']
        ).with_subject('george@upowerenergy.uk')
        
        # Test access
        gc = gspread.authorize(credentials)
        sheet = gc.open_by_key('12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8')
        
        return {
            "status": "healthy",
            "message": "Workspace access working!",
            "services": {
                "sheets": "ok",
                "drive": "ok"
            },
            "dashboard": {
                "title": sheet.title,
                "worksheets": len(sheet.worksheets())
            }
        }
    except Exception as e:
        logger.error(f"Workspace health check failed: {e}")
        return {
            "status": "error",
            "message": str(e)
        }


@app.get("/workspace/dashboard")
async def get_dashboard_info(authorization: Optional[str] = Header(None)):
    """Get GB Energy Dashboard information"""
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
                   'https://www.googleapis.com/auth/drive.readonly']
        ).with_subject('george@upowerenergy.uk')
        
        gc = gspread.authorize(credentials)
        sheet = gc.open_by_key('12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8')
        
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
        logger.error(f"Dashboard access error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/workspace/read_sheet")
async def read_sheet_data(authorization: Optional[str] = Header(None)):
    """Read data from any worksheet in the dashboard"""
    verify_token(authorization)
    
    try:
        import base64
        import json
        from google.oauth2 import service_account
        import gspread
        from fastapi import Body
        
        # Get request body
        body = await Request.json()
        worksheet_name = body.get('worksheet_name', 'Dashboard')
        cell_range = body.get('range', '')
        
        # Get workspace credentials
        workspace_creds_base64 = os.getenv("GOOGLE_WORKSPACE_CREDENTIALS")
        if not workspace_creds_base64:
            raise HTTPException(status_code=503, detail="Workspace credentials not configured")
        
        creds_json = base64.b64decode(workspace_creds_base64).decode('utf-8')
        creds_dict = json.loads(creds_json)
        
        credentials = service_account.Credentials.from_service_account_info(
            creds_dict,
            scopes=['https://www.googleapis.com/auth/spreadsheets',
                   'https://www.googleapis.com/auth/drive.readonly']
        ).with_subject('george@upowerenergy.uk')
        
        gc = gspread.authorize(credentials)
        sheet = gc.open_by_key('12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8')
        worksheet = sheet.worksheet(worksheet_name)
        
        if cell_range:
            data = worksheet.get(cell_range)
        else:
            data = worksheet.get_all_values()
        
        return {
            "success": True,
            "worksheet_name": worksheet_name,
            "rows": len(data),
            "cols": len(data[0]) if data else 0,
            "data": data[:100]  # Limit to first 100 rows
        }
    except Exception as e:
        logger.error(f"Read sheet error: {e}")
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
    
    logger.info("Starting Codex Server...")
    uvicorn.run(app, host="0.0.0.0", port=8000)

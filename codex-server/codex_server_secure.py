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

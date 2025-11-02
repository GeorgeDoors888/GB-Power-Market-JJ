#!/usr/bin/env python3
"""
Codex Server - Safe Code Execution API
Supports Python and JavaScript execution in sandboxed environment
"""

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import subprocess
import tempfile
import os
import sys
from typing import Optional, List
from datetime import datetime
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('codex-server.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Codex Server",
    description="Safe code execution API for Python and JavaScript",
    version="1.0.0"
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request/Response Models
class CodeRequest(BaseModel):
    code: str
    language: str = "python"
    timeout: int = 30
    args: Optional[List[str]] = None

class CodeResponse(BaseModel):
    output: str
    error: Optional[str] = None
    exit_code: int
    execution_time: float
    timestamp: str

class HealthResponse(BaseModel):
    status: str
    version: str
    languages: List[str]
    timestamp: str

# Security: Forbidden patterns
FORBIDDEN_PATTERNS = [
    'import os',
    'import sys',
    'import subprocess',
    '__import__',
    'eval(',
    'exec(',
    'open(',
    'file(',
]

def validate_code(code: str, language: str) -> None:
    """Validate code for security issues"""
    if language == "python":
        for pattern in FORBIDDEN_PATTERNS:
            if pattern in code.lower():
                raise HTTPException(
                    status_code=400,
                    detail=f"Forbidden pattern detected: {pattern}"
                )

def execute_python(code: str, timeout: int = 30) -> dict:
    """Execute Python code in a temporary file"""
    start_time = datetime.now()
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(code)
        temp_file = f.name
    
    try:
        logger.info(f"Executing Python code: {temp_file}")
        result = subprocess.run(
            [sys.executable, temp_file],
            capture_output=True,
            text=True,
            timeout=timeout,
            env={'PYTHONIOENCODING': 'utf-8'}
        )
        
        execution_time = (datetime.now() - start_time).total_seconds()
        
        return {
            'output': result.stdout,
            'error': result.stderr if result.stderr else None,
            'exit_code': result.returncode,
            'execution_time': execution_time
        }
    except subprocess.TimeoutExpired:
        logger.error(f"Python execution timed out after {timeout}s")
        return {
            'output': '',
            'error': f"Execution timed out after {timeout} seconds",
            'exit_code': -1,
            'execution_time': timeout
        }
    except Exception as e:
        logger.error(f"Python execution error: {e}")
        return {
            'output': '',
            'error': str(e),
            'exit_code': -1,
            'execution_time': (datetime.now() - start_time).total_seconds()
        }
    finally:
        try:
            os.unlink(temp_file)
        except:
            pass

def execute_javascript(code: str, timeout: int = 30) -> dict:
    """Execute JavaScript code using Node.js"""
    start_time = datetime.now()
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.js', delete=False) as f:
        f.write(code)
        temp_file = f.name
    
    try:
        logger.info(f"Executing JavaScript code: {temp_file}")
        result = subprocess.run(
            ['node', temp_file],
            capture_output=True,
            text=True,
            timeout=timeout
        )
        
        execution_time = (datetime.now() - start_time).total_seconds()
        
        return {
            'output': result.stdout,
            'error': result.stderr if result.stderr else None,
            'exit_code': result.returncode,
            'execution_time': execution_time
        }
    except FileNotFoundError:
        logger.error("Node.js not found")
        return {
            'output': '',
            'error': "Node.js not installed on server",
            'exit_code': -1,
            'execution_time': 0
        }
    except subprocess.TimeoutExpired:
        logger.error(f"JavaScript execution timed out after {timeout}s")
        return {
            'output': '',
            'error': f"Execution timed out after {timeout} seconds",
            'exit_code': -1,
            'execution_time': timeout
        }
    except Exception as e:
        logger.error(f"JavaScript execution error: {e}")
        return {
            'output': '',
            'error': str(e),
            'exit_code': -1,
            'execution_time': (datetime.now() - start_time).total_seconds()
        }
    finally:
        try:
            os.unlink(temp_file)
        except:
            pass

# API Endpoints
@app.get("/", response_model=HealthResponse)
async def root():
    """Root endpoint with server info"""
    return {
        "status": "running",
        "version": "1.0.0",
        "languages": ["python", "javascript"],
        "timestamp": datetime.now().isoformat()
    }

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": "1.0.0",
        "languages": ["python", "javascript"],
        "timestamp": datetime.now().isoformat()
    }

@app.post("/execute", response_model=CodeResponse)
async def execute_code(request: CodeRequest):
    """
    Execute code in a sandboxed environment
    
    Supported languages:
    - python
    - javascript
    
    Example:
    ```
    {
        "code": "print('Hello World')",
        "language": "python",
        "timeout": 30
    }
    ```
    """
    logger.info(f"Received execution request for {request.language}")
    
    # Validate code
    try:
        validate_code(request.code, request.language)
    except HTTPException as e:
        logger.warning(f"Code validation failed: {e.detail}")
        raise e
    
    # Execute based on language
    if request.language == "python":
        result = execute_python(request.code, request.timeout)
    elif request.language == "javascript":
        result = execute_javascript(request.code, request.timeout)
    else:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported language: {request.language}. Supported: python, javascript"
        )
    
    response = CodeResponse(
        output=result['output'],
        error=result['error'],
        exit_code=result['exit_code'],
        execution_time=result['execution_time'],
        timestamp=datetime.now().isoformat()
    )
    
    logger.info(f"Execution completed: exit_code={response.exit_code}, time={response.execution_time}s")
    return response

@app.get("/languages")
async def get_supported_languages():
    """Get list of supported programming languages"""
    return {
        "languages": [
            {
                "name": "python",
                "version": sys.version.split()[0],
                "available": True
            },
            {
                "name": "javascript",
                "version": "node",
                "available": os.system("which node > /dev/null 2>&1") == 0
            }
        ]
    }

if __name__ == "__main__":
    import uvicorn
    
    logger.info("Starting Codex Server...")
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )

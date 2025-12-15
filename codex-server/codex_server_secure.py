from fastapi import FastAPI, HTTPException, Header, Request
from pydantic import BaseModel
import subprocess
import tempfile
import os
import time
import logging
from typing import Optional, List, Dict, Any
import secrets
import pandas as pd
from pathlib import Path
from datetime import datetime, timezone
from google.cloud import bigquery
from google.oauth2 import service_account
import json
import base64
from googleapiclient.discovery import build
from google.auth.transport.requests import Request as GoogleAuthRequest

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

# Initialize BigQuery client
try:
    creds_base64 = os.environ.get("GOOGLE_CREDENTIALS_BASE64")
    if creds_base64:
        logger.info("Loading BigQuery credentials from environment")
        creds_json = base64.b64decode(creds_base64).decode('utf-8')
        creds_dict = json.loads(creds_json)
        credentials = service_account.Credentials.from_service_account_info(creds_dict)
        bq_client = bigquery.Client(project="inner-cinema-476211-u9", credentials=credentials)
        logger.info("✅ BigQuery client initialized")
    else:
        bq_client = bigquery.Client(project="inner-cinema-476211-u9")
        logger.info("✅ BigQuery client initialized with default credentials")
except Exception as e:
    logger.error(f"❌ Failed to initialize BigQuery: {e}")
    bq_client = None

# Initialize Google Sheets API client
SPREADSHEET_ID = '1LmMq4OEE639Y-XXpOJ3xnvpAmHB6vUovh5g6gaU_vzc'
sheets_service = None
try:
    if creds_base64:
        # Use the same credentials for Sheets API
        scoped_credentials = credentials.with_scopes([
            'https://www.googleapis.com/auth/spreadsheets',
            'https://www.googleapis.com/auth/drive.readonly'
        ])
        sheets_service = build('sheets', 'v4', credentials=scoped_credentials)
        logger.info("✅ Google Sheets API initialized")
    else:
        logger.warning("⚠️ No credentials for Sheets API")
except Exception as e:
    logger.error(f"❌ Failed to initialize Sheets API: {e}")
    sheets_service = None

# BMU Data Loading for Outages
BMU_REGISTRATION_FILE = 'bmu_registration_data.csv'
bmu_data_cache = None

def load_bmu_data():
    """Load BMU registration data for station name lookups"""
    global bmu_data_cache
    if bmu_data_cache is None:
        try:
            # Try multiple paths (Railway vs local)
            possible_paths = [
                Path(__file__).parent.parent / BMU_REGISTRATION_FILE,  # One level up
                Path(__file__).parent / BMU_REGISTRATION_FILE,  # Same directory
                Path('/app') / BMU_REGISTRATION_FILE,  # Railway root
            ]
            
            for bmu_file in possible_paths:
                if bmu_file.exists():
                    bmu_data_cache = pd.read_csv(bmu_file)
                    logger.info(f"✅ Loaded {len(bmu_data_cache)} BMU registrations from {bmu_file}")
                    break
            
            if bmu_data_cache is None:
                logger.warning("⚠️ BMU data file not found")
                bmu_data_cache = pd.DataFrame()
        except Exception as e:
            logger.error(f"❌ Failed to load BMU data: {e}")
            bmu_data_cache = pd.DataFrame()
    return bmu_data_cache

def get_station_name(bmu_code: str, bmu_df: pd.DataFrame) -> str:
    """Convert BMU code to friendly station name with emoji"""
    
    # Hardcoded mapping for common outages (fallback when CSV not available)
    STATION_MAP = {
        # Interconnectors
        'I_IED-IFA2': ('🔌', 'IFA2 France (Import)'),
        'I_IEG-IFA2': ('🔌', 'IFA2 France (Export)'),
        'I_IED-FRAN1': ('🔌', 'IFA1 France (Import)'),
        'I_IEG-FRAN1': ('🔌', 'IFA1 France (Export)'),
        'I_NEMO-1': ('🔌', 'NEMO Belgium'),
        'I_NSLK-1': ('🔌', 'NSL Norway'),
        'I_EIRE-1': ('🔌', 'East-West Ireland'),
        'I_MOYL-1': ('🔌', 'Moyle Ireland'),
        
        # Nuclear Plants
        'T_HEYM27': ('⚛️', 'Heysham 2 Unit 7'),
        'T_HEYM28': ('⚛️', 'Heysham 2 Unit 8'),
        'T_HEYM12': ('⚛️', 'Heysham 1 Unit 2'),
        'T_HEYM11': ('⚛️', 'Heysham 1 Unit 1'),
        'T_HRTL-1': ('⚛️', 'Hartlepool Unit 1'),
        'T_HRTL-2': ('⚛️', 'Hartlepool Unit 2'),
        'T_TORN-1': ('⚛️', 'Torness Unit 1'),
        'T_TORN-2': ('⚛️', 'Torness Unit 2'),
        'T_SIZEWELL-B': ('⚛️', 'Sizewell B'),
        'T_HINKE-3': ('⚛️', 'Hinkley Point B Unit 3'),
        'T_HINKE-4': ('⚛️', 'Hinkley Point B Unit 4'),
        
        # Gas Plants (CCGT)
        'DAMC-1': ('🔥', 'Damhead Creek'),
        'DIDCB6': ('🔥', 'Didcot B Unit 6'),
        'GRAI-6': ('🔥', 'Grain Unit 6'),
        'PEMB-1': ('🔥', 'Pembroke'),
        'DRAXX-1': ('🔥', 'Drax Unit 1'),
        'WBURB-2': ('🔥', 'West Burton B Unit 2'),
        'T_SUTB-1': ('🔥', 'Sutton Bridge Unit 1'),
        'KILN-1': ('🔥', 'Killingholme'),
        'STAY-1': ('🔥', 'Staythorpe'),
        
        # Coal (legacy)
        'RATS-1': ('🪨', 'Ratcliffe'),
        
        # Wind
        'WFOFF-1': ('💨', 'Offshore Wind'),
        'WNON-1': ('💨', 'Onshore Wind'),
        
        # Storage/Batteries
        'BESS-1': ('🔋', 'Battery Storage'),
    }
    
    # Check hardcoded map first
    if bmu_code in STATION_MAP:
        emoji, name = STATION_MAP[bmu_code]
        return f"{emoji} {name}"
    
    # Try CSV data if available
    if not bmu_df.empty:
        # Try exact match
        match = bmu_df[bmu_df['nationalGridBmUnit'] == bmu_code]
        if match.empty:
            match = bmu_df[bmu_df['elexonBmUnit'] == bmu_code]
        
        if not match.empty:
            fuel_type = match.iloc[0]['fuelType']
            station_name = match.iloc[0]['bmUnitName']
            
            emoji_map = {
                'NUCLEAR': '⚛️',
                'CCGT': '🔥',
                'OCGT': '🔥',
                'WIND': '💨',
                'PS': '🔋',
            }
            emoji = emoji_map.get(fuel_type, '⚡')
            return f"{emoji} {station_name}"
    
    # Fallback: just show the code
    return f"⚡ {bmu_code}"

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

@app.get("/outages/names")
async def get_outages_with_names():
    """
    Get current REMIT outages with station names (no auth required for dashboard)
    Returns: List of station names for Dashboard display
    """
    try:
        bmu_df = load_bmu_data()
        
        if not bq_client:
            raise HTTPException(status_code=503, detail="BigQuery client not available")
        
        query = """
        WITH latest_revisions AS (
            SELECT 
                affectedUnit,
                MAX(revisionNumber) as max_rev
            FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_remit_unavailability`
            WHERE DATE(eventStartTime) <= CURRENT_DATE()
                AND (DATE(eventEndTime) >= CURRENT_DATE() OR eventEndTime IS NULL)
            GROUP BY affectedUnit
        )
        SELECT 
            u.affectedUnit as bmu_id,
            u.unavailableCapacity as unavailable_mw,
            u.fuelType,
            u.eventStartTime
        FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_remit_unavailability` u
        INNER JOIN latest_revisions lr
            ON u.affectedUnit = lr.affectedUnit
            AND u.revisionNumber = lr.max_rev
        WHERE DATE(u.eventStartTime) <= CURRENT_DATE()
            AND (DATE(u.eventEndTime) >= CURRENT_DATE() OR u.eventEndTime IS NULL)
        ORDER BY u.unavailableCapacity DESC
        LIMIT 15
        """
        
        df = bq_client.query(query).to_dataframe()
        
        # Enrich with station names
        outages = []
        for _, row in df.iterrows():
            station_name = get_station_name(row['bmu_id'], bmu_df)
            outages.append({
                'station_name': station_name,
                'bmu_id': row['bmu_id'],
                'unavailable_mw': float(row['unavailable_mw']),
                'fuel_type': row['fuelType']
            })
        
        logger.info(f"✅ Fetched {len(outages)} outages with station names")
        
        return {
            'status': 'success',
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'count': len(outages),
            'names': [o['station_name'] for o in outages],
            'outages': outages
        }
    
    except Exception as e:
        logger.error(f"❌ Error fetching outages: {e}")
        raise HTTPException(status_code=500, detail=str(e))

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
# BIGQUERY ENDPOINTS
# ============================================

@app.post("/query_bigquery")
async def query_bigquery(request: Request, authorization: Optional[str] = Header(None)):
    """Execute BigQuery SQL query"""
    verify_token(authorization)
    
    try:
        from google.cloud import bigquery
        import base64
        import json
        
        body = await request.json()
        sql = body.get('sql') or body.get('query')
        
        if not sql:
            raise HTTPException(status_code=400, detail="Must provide 'sql' or 'query' parameter")
        
        # Get BigQuery credentials
        bq_creds_base64 = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
        if not bq_creds_base64:
            raise HTTPException(status_code=503, detail="BigQuery credentials not configured")
        
        # Decode and create client
        creds_json = base64.b64decode(bq_creds_base64).decode('utf-8')
        creds_dict = json.loads(creds_json)
        
        project_id = os.getenv("BQ_PROJECT_ID", "inner-cinema-476211-u9")
        
        # Create BigQuery client
        client = bigquery.Client.from_service_account_info(creds_dict, project=project_id)
        
        # Execute query
        query_job = client.query(sql)
        results = query_job.result()
        
        # Convert to list of dicts
        rows = [dict(row) for row in results]
        
        return {
            "success": True,
            "rows": len(rows),
            "results": rows
        }
        
    except Exception as e:
        logger.error(f"BigQuery query error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/query_bigquery_get")
async def query_bigquery_get(sql: str, authorization: Optional[str] = Header(None)):
    """Execute BigQuery SQL query via GET (for simple queries)"""
    verify_token(authorization)
    
    try:
        from google.cloud import bigquery
        import base64
        import json
        
        if not sql:
            raise HTTPException(status_code=400, detail="Must provide 'sql' parameter")
        
        # Get BigQuery credentials
        bq_creds_base64 = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
        if not bq_creds_base64:
            raise HTTPException(status_code=503, detail="BigQuery credentials not configured")
        
        # Decode and create client
        creds_json = base64.b64decode(bq_creds_base64).decode('utf-8')
        creds_dict = json.loads(creds_json)
        
        project_id = os.getenv("BQ_PROJECT_ID", "inner-cinema-476211-u9")
        
        # Create BigQuery client
        client = bigquery.Client.from_service_account_info(creds_dict, project=project_id)
        
        # Execute query
        query_job = client.query(sql)
        results = query_job.result()
        
        # Convert to list of dicts
        rows = [dict(row) for row in results]
        
        return {
            "success": True,
            "rows": len(rows),
            "results": rows
        }
        
    except Exception as e:
        logger.error(f"BigQuery query error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/debug/env")
async def debug_env(authorization: Optional[str] = Header(None)):
    """Debug environment variables (auth required)"""
    verify_token(authorization)
    
    return {
        "has_bigquery_creds": bool(os.getenv("GOOGLE_APPLICATION_CREDENTIALS")),
        "has_workspace_creds": bool(os.getenv("GOOGLE_WORKSPACE_CREDENTIALS")),
        "bq_project_id": os.getenv("BQ_PROJECT_ID"),
        "bq_dataset": os.getenv("BQ_DATASET"),
        "api_token_set": bool(os.getenv("CODEX_API_TOKEN"))
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
        spreadsheet_id = body.get('spreadsheet_id', '1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA')  # Default to GB Energy Dashboard
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
        spreadsheet_id = body.get('spreadsheet_id', '1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA')
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


# ============================================================================
# GOOGLE SHEETS API ENDPOINTS
# ============================================================================

class SheetsReadRequest(BaseModel):
    sheet: str
    range: str
    spreadsheet_id: Optional[str] = None

class SheetsWriteRequest(BaseModel):
    sheet: str
    range: str
    values: List[List[Any]]

@app.get("/sheets_health")
async def sheets_health():
    """Health check for Google Sheets API"""
    return {
        "ok": True,
        "message": "Google Sheets API is healthy",
        "spreadsheet_id": SPREADSHEET_ID,
        "sheets_api_available": sheets_service is not None
    }

@app.get("/sheets_list")
async def sheets_list(authorization: str = Header(None)):
    """List all sheets in the spreadsheet"""
    if authorization != f"Bearer {API_TOKEN}":
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    if not sheets_service:
        raise HTTPException(status_code=503, detail="Sheets API not initialized")
    
    try:
        spreadsheet = sheets_service.spreadsheets().get(
            spreadsheetId=SPREADSHEET_ID
        ).execute()
        
        sheets = [sheet['properties']['title'] for sheet in spreadsheet.get('sheets', [])]
        
        return {
            "ok": True,
            "spreadsheet_id": SPREADSHEET_ID,
            "sheets": sheets,
            "count": len(sheets)
        }
    except Exception as e:
        logger.error(f"Sheets list error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/sheets_read")
async def sheets_read(request: SheetsReadRequest, authorization: str = Header(None)):
    """Read data from a Google Sheet"""
    if authorization != f"Bearer {API_TOKEN}":
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    if not sheets_service:
        raise HTTPException(status_code=503, detail="Sheets API not initialized")
    
    try:
        range_name = f"{request.sheet}!{request.range}"
        result = sheets_service.spreadsheets().values().get(
            spreadsheetId=request.spreadsheet_id or SPREADSHEET_ID,
            range=range_name
        ).execute()
        
        values = result.get('values', [])
        
        return {
            "ok": True,
            "range": result.get('range'),
            "values": values,
            "rows": len(values),
            "columns": len(values[0]) if values else 0
        }
    except Exception as e:
        logger.error(f"Sheets read error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/sheets_write")
async def sheets_write(request: SheetsWriteRequest, authorization: str = Header(None)):
    """Write data to a Google Sheet"""
    if authorization != f"Bearer {API_TOKEN}":
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    if not sheets_service:
        raise HTTPException(status_code=503, detail="Sheets API not initialized")
    
    try:
        range_name = f"{request.sheet}!{request.range}"
        body = {
            'values': request.values
        }
        
        result = sheets_service.spreadsheets().values().update(
            spreadsheetId=SPREADSHEET_ID,
            range=range_name,
            valueInputOption='USER_ENTERED',
            body=body
        ).execute()
        
        return {
            "ok": True,
            "updated_range": result.get('updatedRange'),
            "updated_rows": result.get('updatedRows'),
            "updated_columns": result.get('updatedColumns'),
            "updated_cells": result.get('updatedCells')
        }
    except Exception as e:
        logger.error(f"Sheets write error: {e}")
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

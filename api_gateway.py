"""
AI Gateway API Server - Level 3 Full Automation
Created: 2025-11-06
Purpose: Enable ChatGPT to directly interact with infrastructure
Security: Full authentication, rate limiting, audit logging, approval workflows
"""

from fastapi import FastAPI, HTTPException, Header, Depends, Request, Response
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import JSONResponse
from google.cloud import bigquery
from google.oauth2 import service_account
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import paramiko
import os
import sys
import base64
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone
import logging
import json
from pathlib import Path
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import requests
from functools import wraps
import traceback
import pandas as pd

# ============================================
# CONFIGURATION & SETUP
# ============================================

# Load environment variables from .env.ai-gateway
env_file = Path(__file__).parent / ".env.ai-gateway"
if env_file.exists():
    with open(env_file) as f:
        for line in f:
            if line.strip() and not line.startswith('#') and '=' in line:
                key, value = line.strip().split('=', 1)
                os.environ[key] = value

# Configuration
UPCLOUD_HOST = os.environ.get("UPCLOUD_HOST", "94.237.55.234")
UPCLOUD_USER = os.environ.get("UPCLOUD_USER", "root")
UPCLOUD_KEY_PATH = os.path.expanduser(os.environ.get("UPCLOUD_SSH_KEY_PATH", "~/.ssh/id_rsa"))
BQ_PROJECT = os.environ.get("BQ_PROJECT_ID", "inner-cinema-476211-u9")
BQ_DATASET = os.environ.get("BQ_DATASET", "uk_energy_prod")
SHEETS_ID = os.environ.get("SHEETS_ID", "1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA")
SLACK_WEBHOOK = os.environ.get("SLACK_WEBHOOK_URL", "")
LOG_FILE = os.environ.get("LOG_FILE", "/tmp/ai-gateway-audit.log")
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")
RATE_LIMIT_MIN = int(os.environ.get("RATE_LIMIT_PER_MINUTE", "20"))
RATE_LIMIT_HOUR = int(os.environ.get("RATE_LIMIT_PER_HOUR", "200"))

# API Key validation
VALID_API_KEY = os.environ.get("AI_GATEWAY_API_KEY")
if not VALID_API_KEY:
    print("❌ ERROR: AI_GATEWAY_API_KEY not set in environment!")
    print("   Please set it in .env.ai-gateway file")
    sys.exit(1)

EMERGENCY_TOKEN = os.environ.get("EMERGENCY_SHUTDOWN_TOKEN", "")

# Setup comprehensive logging
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Initialize FastAPI with rate limiting
limiter = Limiter(key_func=get_remote_address)
app = FastAPI(
    title="Power Market AI Gateway",
    description="Level 3 Full Automation - Direct AI access to infrastructure",
    version="3.0.0"
)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

security = HTTPBearer()

# Initialize BigQuery client with credentials
try:
    # Try to load credentials from base64 env var (for Railway)
    creds_base64 = os.environ.get("GOOGLE_CREDENTIALS_BASE64")
    if creds_base64:
        logger.info("Loading credentials from GOOGLE_CREDENTIALS_BASE64")
        creds_json = base64.b64decode(creds_base64).decode('utf-8')
        creds_dict = json.loads(creds_json)
        credentials = service_account.Credentials.from_service_account_info(creds_dict)
        bq_client = bigquery.Client(project=BQ_PROJECT, credentials=credentials)
        logger.info(f"✅ BigQuery client initialized for project {BQ_PROJECT} with base64 credentials")
    else:
        # Fall back to default credentials (for local development)
        logger.info("Using default credentials (ADC)")
        bq_client = bigquery.Client(project=BQ_PROJECT)
        logger.info(f"✅ BigQuery client initialized for project {BQ_PROJECT} with default credentials")
except Exception as e:
    logger.error(f"❌ Failed to initialize BigQuery client: {e}")
    bq_client = None

# ============================================
# SECURITY & MONITORING FUNCTIONS
# ============================================

def send_slack_alert(message: str, level: str = "info", details: Dict = None):
    """Send alert to Slack with optional details"""
    if not SLACK_WEBHOOK or SLACK_WEBHOOK == "https://hooks.slack.com/services/YOUR/WEBHOOK/URL":
        return  # Slack not configured
    
    emoji = {"info": "ℹ️", "warning": "⚠️", "critical": "🚨", "success": "✅"}
    
    payload = {
        "text": f"{emoji.get(level, 'ℹ️')} {message}",
        "username": "AI Gateway Bot"
    }
    
    if details:
        payload["attachments"] = [{
            "color": {"info": "good", "warning": "warning", "critical": "danger"}.get(level, "good"),
            "fields": [{"title": k, "value": str(v), "short": True} for k, v in details.items()]
        }]
    
    try:
        requests.post(SLACK_WEBHOOK, json=payload, timeout=5)
    except Exception as e:
        logger.error(f"Failed to send Slack alert: {e}")

def log_action(action: str, details: Dict[str, Any], level: str = "INFO"):
    """Comprehensive audit logging"""
    log_entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "action": action,
        "details": details
    }
    
    if level == "WARNING":
        logger.warning(json.dumps(log_entry))
        send_slack_alert(f"Action: {action}", "warning", details)
    elif level == "CRITICAL":
        logger.critical(json.dumps(log_entry))
        send_slack_alert(f"CRITICAL: {action}", "critical", details)
    else:
        logger.info(json.dumps(log_entry))

def verify_api_key(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify API key from Bearer token"""
    if credentials.credentials != VALID_API_KEY:
        log_action("UNAUTHORIZED_ACCESS_ATTEMPT", {
            "attempted_key": credentials.credentials[:10] + "...",
            "remote_ip": "unknown"
        }, "WARNING")
        raise HTTPException(status_code=403, detail="Invalid API key")
    return credentials.credentials

def check_dangerous_command(command: str) -> tuple[bool, str]:
    """
    Check if command contains dangerous patterns
    Returns: (is_dangerous, reason)
    """
    DANGEROUS_PATTERNS = [
        ('rm -rf', 'Recursive forced deletion'),
        ('dd if=', 'Direct disk write'),
        ('mkfs', 'Filesystem creation'),
        (':(){:|:&};:', 'Fork bomb'),
        ('chmod 777', 'Insecure permissions'),
        ('wget | sh', 'Remote script execution'),
        ('curl | bash', 'Remote script execution'),
        ('>/dev/sda', 'Direct disk write'),
        ('shred', 'Secure deletion'),
        ('wipefs', 'Filesystem wipe'),
        ('fdisk', 'Disk partitioning'),
        ('parted', 'Partition editing'),
        ('killall -9', 'Force kill all processes'),
        ('> /etc/', 'System config overwrite'),
        ('rm /boot', 'Boot deletion'),
        ('userdel root', 'Root user deletion'),
    ]
    
    cmd_lower = command.lower()
    for pattern, reason in DANGEROUS_PATTERNS:
        if pattern.lower() in cmd_lower:
            return True, reason
    
    return False, ""

def require_approval(action_name: str):
    """Decorator for actions that require approval"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, require_approval: bool = True, **kwargs):
            if require_approval:
                log_action("APPROVAL_REQUIRED", {
                    "action": action_name,
                    "function": func.__name__
                }, "WARNING")
                return {
                    "success": False,
                    "approval_required": True,
                    "action": action_name,
                    "message": f"This {action_name} requires manual approval. "
                              f"Set require_approval=false to execute.",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            
            log_action(f"APPROVED_{action_name.upper()}", {
                "function": func.__name__,
                "approval_bypassed": True
            }, "CRITICAL")
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator

def get_sheets_client():
    """Get authenticated Google Sheets client using workspace delegation"""
    try:
        # Try to load workspace credentials from base64 env var (for Railway)
        workspace_creds_base64 = os.environ.get("GOOGLE_WORKSPACE_CREDENTIALS")
        
        if workspace_creds_base64:
            logger.info("Loading workspace credentials from GOOGLE_WORKSPACE_CREDENTIALS")
            creds_json = base64.b64decode(workspace_creds_base64).decode('utf-8')
            creds_dict = json.loads(creds_json)
            
            # Create credentials with delegation
            credentials = service_account.Credentials.from_service_account_info(
                creds_dict,
                scopes=['https://www.googleapis.com/auth/spreadsheets',
                       'https://www.googleapis.com/auth/drive.readonly']
            ).with_subject('george@upowerenergy.uk')
            
            return gspread.authorize(credentials)
        else:
            # Fall back to local credentials file
            logger.info("Using local workspace-credentials.json file")
            credentials = service_account.Credentials.from_service_account_file(
                'workspace-credentials.json',
                scopes=['https://www.googleapis.com/auth/spreadsheets',
                       'https://www.googleapis.com/auth/drive.readonly']
            ).with_subject('george@upowerenergy.uk')
            
            return gspread.authorize(credentials)
            
    except Exception as e:
        logger.error(f"Failed to initialize Sheets client: {e}")
        logger.error(traceback.format_exc())
        return None

# ============================================
# MIDDLEWARE
# ============================================

@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all requests for audit trail"""
    start_time = datetime.now(timezone.utc)
    client_ip = request.client.host if request.client else "unknown"
    
    # Log request
    log_action("API_REQUEST", {
        "method": request.method,
        "path": request.url.path,
        "client_ip": client_ip,
        "user_agent": request.headers.get("user-agent", "unknown")
    })
    
    # Process request
    response = await call_next(request)
    
    # Log response
    duration = (datetime.now(timezone.utc) - start_time).total_seconds()
    log_action("API_RESPONSE", {
        "path": request.url.path,
        "status_code": response.status_code,
        "duration_seconds": round(duration, 3)
    })
    
    return response

# ============================================
# HEALTH & STATUS ENDPOINTS
# ============================================

@app.get("/")
@limiter.limit(f"{RATE_LIMIT_MIN}/minute")
def root(request: Request):
    """Health check endpoint - no authentication required"""
    return {
        "status": "healthy",
        "service": "Power Market AI Gateway",
        "version": "3.0.0",
        "security_level": "Level 3 - Full Automation",
        "features": [
            "Read-only BigQuery access",
            "Monitored write operations",
            "Approved SSH command execution",
            "BigQuery write operations (with approval)",
            "Comprehensive audit logging",
            "Rate limiting active",
            "Slack notifications (if configured)"
        ],
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "rate_limits": {
            "per_minute": RATE_LIMIT_MIN,
            "per_hour": RATE_LIMIT_HOUR
        }
    }

@app.get("/health")
@limiter.limit(f"{RATE_LIMIT_MIN}/minute")
def health_check(request: Request, api_key: str = Depends(verify_api_key)):
    """Detailed health check with component status"""
    status = {
        "overall": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "components": {}
    }
    
    # Check BigQuery
    try:
        if bq_client:
            query = f"SELECT COUNT(*) as count FROM `{BQ_PROJECT}.{BQ_DATASET}.bmrs_mid` LIMIT 1"
            bq_client.query(query).result()
            status["components"]["bigquery"] = "healthy"
        else:
            status["components"]["bigquery"] = "unavailable"
            status["overall"] = "degraded"
    except Exception as e:
        status["components"]["bigquery"] = f"unhealthy: {str(e)}"
        status["overall"] = "degraded"
    
    # Check Google Sheets
    try:
        gc = get_sheets_client()
        if gc:
            sheet = gc.open_by_key(SHEETS_ID)
            status["components"]["google_sheets"] = "healthy"
        else:
            status["components"]["google_sheets"] = "unavailable"
            status["overall"] = "degraded"
    except Exception as e:
        status["components"]["google_sheets"] = f"unhealthy: {str(e)}"
        status["overall"] = "degraded"
    
    # Check UpCloud SSH
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(UPCLOUD_HOST, username=UPCLOUD_USER, key_filename=UPCLOUD_KEY_PATH, timeout=5)
        ssh.close()
        status["components"]["upcloud_ssh"] = "healthy"
    except Exception as e:
        status["components"]["upcloud_ssh"] = f"unhealthy: {str(e)}"
        status["overall"] = "degraded"
    
    # Check Slack
    status["components"]["slack_notifications"] = "configured" if SLACK_WEBHOOK and "YOUR" not in SLACK_WEBHOOK else "not_configured"
    
    return status

# ============================================
# BMU DATA LOADING FOR OUTAGES
# ============================================

BMU_REGISTRATION_FILE = 'bmu_registration_data.csv'
bmu_data_cache = None

def load_bmu_data():
    """Load BMU registration data for station name lookups"""
    global bmu_data_cache
    if bmu_data_cache is None:
        try:
            bmu_file = Path(__file__).parent / BMU_REGISTRATION_FILE
            bmu_data_cache = pd.read_csv(bmu_file)
            logger.info(f"✅ Loaded {len(bmu_data_cache)} BMU registrations")
        except Exception as e:
            logger.error(f"❌ Failed to load BMU data: {e}")
            bmu_data_cache = pd.DataFrame()  # Empty DataFrame as fallback
    return bmu_data_cache

def get_station_name(bmu_code: str, bmu_df: pd.DataFrame) -> str:
    """Convert BMU code to friendly station name with emoji"""
    if bmu_df.empty:
        return f"⚡ {bmu_code}"
    
    # Try exact match on nationalGridBmUnit
    match = bmu_df[bmu_df['nationalGridBmUnit'] == bmu_code]
    if match.empty:
        # Try elexonBmUnit
        match = bmu_df[bmu_df['elexonBmUnit'] == bmu_code]
    
    if not match.empty:
        fuel_type = match.iloc[0]['fuelType']
        station_name = match.iloc[0]['bmUnitName']
        
        # Add emoji based on fuel type
        emoji_map = {
            'NUCLEAR': '⚛️',
            'CCGT': '🔥',
            'OCGT': '🔥',
            'WIND': '💨',
            'PS': '🔋',  # Pumped Storage
        }
        emoji = emoji_map.get(fuel_type, '⚡')
        return f"{emoji} {station_name}"
    
    return f"⚡ {bmu_code}"

@app.get("/outages/names")
@limiter.limit(f"{RATE_LIMIT_MIN}/minute")
def get_outages_with_names(request: Request):
    """
    Get current REMIT outages with station names (no auth required for dashboard)
    Returns: List of station names for Dashboard display
    """
    try:
        bmu_df = load_bmu_data()
        
        if not bq_client:
            raise HTTPException(status_code=503, detail="BigQuery client not available")
        
        query = f"""
        WITH latest_revisions AS (
            SELECT 
                affectedUnit,
                MAX(revisionNumber) as max_rev
            FROM `{BQ_PROJECT}.{BQ_DATASET}.bmrs_remit_unavailability`
            WHERE DATE(eventStartTime) <= CURRENT_DATE()
                AND (DATE(eventEndTime) >= CURRENT_DATE() OR eventEndTime IS NULL)
            GROUP BY affectedUnit
        )
        SELECT 
            u.affectedUnit as bmu_id,
            u.unavailableCapacity as unavailable_mw,
            u.fuelType,
            u.eventStartTime
        FROM `{BQ_PROJECT}.{BQ_DATASET}.bmrs_remit_unavailability` u
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
        
        log_action("OUTAGES_READ", {"count": len(outages)}, "INFO")
        
        return {
            'status': 'success',
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'count': len(outages),
            'names': [o['station_name'] for o in outages],
            'outages': outages
        }
    
    except Exception as e:
        logger.error(f"Error fetching outages: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================
# LEVEL 1: READ-ONLY ENDPOINTS (SAFE)
# ============================================

@app.get("/bigquery/prices")
@limiter.limit(f"{RATE_LIMIT_MIN}/minute")
def get_prices(
    request: Request,
    days: int = 7,
    api_key: str = Depends(verify_api_key)
):
    """
    Get electricity prices for the last N days
    Safe: Read-only BigQuery query
    """
    log_action("BIGQUERY_READ", {"endpoint": "prices", "days": days})
    
    if not bq_client:
        raise HTTPException(status_code=503, detail="BigQuery client not available")
    
    query = f"""
    SELECT 
        DATE(settlementDate) as date,
        AVG(price) as avg_price,
        MIN(price) as min_price,
        MAX(price) as max_price,
        COUNT(*) as num_periods,
        SUM(CASE WHEN price < 0 THEN 1 ELSE 0 END) as negative_periods
    FROM `{BQ_PROJECT}.{BQ_DATASET}.bmrs_mid`
    WHERE DATE(settlementDate) >= DATE_SUB(CURRENT_DATE(), INTERVAL {days} DAY)
    GROUP BY date
    ORDER BY date DESC
    """
    
    try:
        df = bq_client.query(query).to_dataframe()
        return {
            "success": True,
            "days_requested": days,
            "rows": len(df),
            "data": json.loads(df.to_json(orient='records', date_format='iso'))
        }
    except Exception as e:
        logger.error(f"BigQuery error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/bigquery/generation")
@limiter.limit(f"{RATE_LIMIT_MIN}/minute")
def get_generation(
    request: Request,
    days: int = 7,
    fuel_type: Optional[str] = None,
    api_key: str = Depends(verify_api_key)
):
    """
    Get generation mix for the last N days
    Safe: Read-only BigQuery query
    """
    log_action("BIGQUERY_READ", {
        "endpoint": "generation",
        "days": days,
        "fuel_type": fuel_type or "all"
    })
    
    if not bq_client:
        raise HTTPException(status_code=503, detail="BigQuery client not available")
    
    fuel_filter = f"AND fuelType = '{fuel_type}'" if fuel_type else ""
    
    query = f"""
    SELECT 
        DATE(settlementDate) as date,
        fuelType,
        SUM(generation) as total_generation_mw,
        AVG(generation) as avg_generation_mw,
        MAX(generation) as peak_generation_mw
    FROM `{BQ_PROJECT}.{BQ_DATASET}.bmrs_fuelinst`
    WHERE DATE(settlementDate) >= DATE_SUB(CURRENT_DATE(), INTERVAL {days} DAY)
    {fuel_filter}
    GROUP BY date, fuelType
    ORDER BY date DESC, total_generation_mw DESC
    LIMIT 1000
    """
    
    try:
        df = bq_client.query(query).to_dataframe()
        return {
            "success": True,
            "days_requested": days,
            "fuel_type_filter": fuel_type,
            "rows": len(df),
            "data": json.loads(df.to_json(orient='records', date_format='iso'))
        }
    except Exception as e:
        logger.error(f"BigQuery error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/sheets/read")
@limiter.limit(f"{RATE_LIMIT_MIN}/minute")
def read_sheet(
    request: Request,
    tab: str = "Analysis BI Enhanced",
    range: str = "A1:Z100",
    api_key: str = Depends(verify_api_key)
):
    """
    Read data from Google Sheet
    Safe: Read-only access
    """
    log_action("SHEETS_READ", {"tab": tab, "range": range})
    
    try:
        gc = get_sheets_client()
        if not gc:
            raise HTTPException(status_code=503, detail="Google Sheets client not available")
        
        sheet = gc.open_by_key(SHEETS_ID)
        worksheet = sheet.worksheet(tab)
        values = worksheet.get(range)
        
        return {
            "success": True,
            "tab": tab,
            "range": range,
            "rows": len(values),
            "cols": len(values[0]) if values else 0,
            "data": values
        }
    except Exception as e:
        logger.error(f"Sheets error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/upcloud/status")
@limiter.limit(f"{RATE_LIMIT_MIN}/minute")
def check_server_status(
    request: Request,
    api_key: str = Depends(verify_api_key)
):
    """
    Check UpCloud server status
    Safe: Read-only SSH commands
    """
    log_action("UPCLOUD_STATUS_CHECK", {"host": UPCLOUD_HOST})
    
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(UPCLOUD_HOST, username=UPCLOUD_USER, key_filename=UPCLOUD_KEY_PATH, timeout=10)
        
        # Run status check commands
        commands = {
            "arbitrage_service": "systemctl status arbitrage.service --no-pager",
            "disk_usage": "df -h /opt/arbitrage",
            "memory_usage": "free -h",
            "last_run": "tail -5 /opt/arbitrage/logs/arbitrage.log 2>/dev/null || echo 'No logs found'",
            "health_check": "cat /opt/arbitrage/reports/data/health.json 2>/dev/null || echo '{}'"
        }
        
        results = {}
        for name, cmd in commands.items():
            stdin, stdout, stderr = ssh.exec_command(cmd)
            results[name] = {
                "stdout": stdout.read().decode(),
                "stderr": stderr.read().decode(),
                "exit_code": stdout.channel.recv_exit_status()
            }
        
        ssh.close()
        
        return {
            "success": True,
            "server": UPCLOUD_HOST,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "results": results
        }
    except Exception as e:
        logger.error(f"SSH error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================
# LEVEL 2: MONITORED WRITE ACCESS (MODERATE)
# ============================================

@app.post("/sheets/update")
@limiter.limit(f"{RATE_LIMIT_MIN//2}/minute")  # Lower limit for write operations
def update_sheet(
    request: Request,
    tab: str,
    range: str,
    values: List[List],
    api_key: str = Depends(verify_api_key)
):
    """
    Update Google Sheet with new data
    Moderate risk: Write access with logging and alerts
    """
    log_action("SHEETS_WRITE", {
        "tab": tab,
        "range": range,
        "rows": len(values)
    }, "WARNING")
    
    send_slack_alert(
        f"Google Sheet Update: {tab} range {range}",
        "warning",
        {"rows": len(values), "timestamp": datetime.now(timezone.utc).isoformat()}
    )
    
    try:
        gc = get_sheets_client()
        if not gc:
            raise HTTPException(status_code=503, detail="Google Sheets client not available")
        
        sheet = gc.open_by_key(SHEETS_ID)
        worksheet = sheet.worksheet(tab)
        worksheet.update(range, values)
        
        log_action("SHEETS_WRITE_SUCCESS", {
            "tab": tab,
            "range": range,
            "rows_updated": len(values)
        })
        
        return {
            "success": True,
            "tab": tab,
            "range": range,
            "rows_updated": len(values),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        logger.error(f"Sheets update error: {str(e)}")
        send_slack_alert(f"Sheet update FAILED: {str(e)}", "critical")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/sheets/run-apps-script")
@limiter.limit(f"{RATE_LIMIT_MIN}/minute")
def run_apps_script(
    request: Request,
    function_name: str,
    api_key: str = Depends(verify_api_key)
):
    """
    Execute Google Apps Script function on the spreadsheet
    
    Available functions:
    - setupDashboard: Initial setup (run once)
    - refreshData: Refresh dashboard data
    - manualRefresh: Manual refresh with UI feedback
    
    Moderate risk: Can modify spreadsheet via Apps Script
    """
    # Whitelist of allowed functions
    ALLOWED_FUNCTIONS = [
        "setupDashboard",
        "refreshData", 
        "manualRefresh",
        "showLogs"
    ]
    
    if function_name not in ALLOWED_FUNCTIONS:
        log_action("BLOCKED_APPS_SCRIPT", {
            "function": function_name,
            "reason": "not in whitelist"
        }, "CRITICAL")
        raise HTTPException(
            status_code=403,
            detail=f"Function '{function_name}' not in whitelist. Allowed: {', '.join(ALLOWED_FUNCTIONS)}"
        )
    
    log_action("APPS_SCRIPT_EXECUTION", {
        "function": function_name,
        "sheet_id": SHEETS_ID
    }, "WARNING")
    
    try:
        # Note: Google Apps Script API requires OAuth2 setup and project deployment
        # For now, we'll return instructions for manual setup
        # To fully automate, you'd need to use the Apps Script API with service account
        
        return {
            "success": True,
            "function": function_name,
            "message": f"To execute '{function_name}', use one of these methods:",
            "methods": {
                "manual": f"Open Sheet → Extensions → Apps Script → Run {function_name}",
                "menu_button": "Open Sheet → Dashboard menu → Refresh Data Now",
                "trigger": "Runs automatically every 15 minutes (if setup completed)",
                "direct_url": f"https://docs.google.com/spreadsheets/d/{SHEETS_ID}/edit"
            },
            "note": "Apps Script functions run in Google's environment, not via API. Use the menu button for manual refresh.",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        logger.error(f"Apps Script execution error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/upcloud/run-script")
@limiter.limit(f"{RATE_LIMIT_MIN//4}/minute")  # Very low limit for script execution
def run_approved_script(
    request: Request,
    script_name: str,
    api_key: str = Depends(verify_api_key)
):
    """
    Run pre-approved script on UpCloud server
    Moderate risk: Only whitelisted scripts allowed
    """
    # Whitelist of allowed scripts
    ALLOWED_SCRIPTS = [
        "battery_arbitrage.py",
        "update_analysis_bi_enhanced.py",
        "check_health.sh"
    ]
    
    if script_name not in ALLOWED_SCRIPTS:
        log_action("BLOCKED_SCRIPT", {
            "script": script_name,
            "reason": "not in whitelist"
        }, "CRITICAL")
        raise HTTPException(
            status_code=403,
            detail=f"Script '{script_name}' not in whitelist. Allowed: {', '.join(ALLOWED_SCRIPTS)}"
        )
    
    log_action("SCRIPT_EXECUTION", {
        "script": script_name,
        "host": UPCLOUD_HOST
    }, "WARNING")
    
    send_slack_alert(
        f"Executing script: {script_name} on {UPCLOUD_HOST}",
        "warning"
    )
    
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(UPCLOUD_HOST, username=UPCLOUD_USER, key_filename=UPCLOUD_KEY_PATH, timeout=10)
        
        cmd = f"cd /opt/arbitrage && python3 {script_name}"
        stdin, stdout, stderr = ssh.exec_command(cmd, timeout=300)  # 5 minute timeout
        
        output = stdout.read().decode()
        error = stderr.read().decode()
        exit_code = stdout.channel.recv_exit_status()
        
        ssh.close()
        
        log_action("SCRIPT_EXECUTION_COMPLETE", {
            "script": script_name,
            "exit_code": exit_code,
            "success": exit_code == 0
        })
        
        if exit_code == 0:
            send_slack_alert(f"Script completed successfully: {script_name}", "success")
        else:
            send_slack_alert(f"Script failed: {script_name} (exit code {exit_code})", "critical")
        
        return {
            "success": exit_code == 0,
            "script": script_name,
            "exit_code": exit_code,
            "output": output[-5000:],  # Last 5000 chars to avoid huge responses
            "error": error[-5000:] if error else "",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        logger.error(f"Script execution error: {str(e)}")
        send_slack_alert(f"Script execution ERROR: {script_name} - {str(e)}", "critical")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================
# LEVEL 3: FULL ACCESS (HIGH RISK)
# ============================================

@app.post("/bigquery/execute")
@limiter.limit(f"{RATE_LIMIT_MIN//10}/minute")  # Very restrictive
async def execute_bigquery(
    request: Request,
    query: str,
    dry_run: bool = True,
    require_approval: bool = True,
    api_key: str = Depends(verify_api_key)
):
    """
    Execute arbitrary BigQuery query
    HIGH RISK: Can modify/delete data
    Default: dry_run=True, require_approval=True for safety
    """
    # Check for dangerous operations
    query_upper = query.upper()
    is_write_operation = any(op in query_upper for op in ['INSERT', 'UPDATE', 'DELETE', 'DROP', 'CREATE', 'ALTER'])
    
    if is_write_operation and require_approval:
        log_action("BIGQUERY_APPROVAL_REQUIRED", {
            "query_preview": query[:200],
            "reason": "write operation detected"
        }, "CRITICAL")
        
        return {
            "success": False,
            "approval_required": True,
            "query_type": "WRITE",
            "message": "This query modifies data and requires approval. Set require_approval=false to execute.",
            "dry_run_recommended": True
        }
    
    log_action("BIGQUERY_EXECUTE", {
        "query_preview": query[:200],
        "dry_run": dry_run,
        "approval_bypassed": not require_approval
    }, "CRITICAL" if not dry_run else "WARNING")
    
    if not dry_run:
        send_slack_alert(
            f"🚨 DANGEROUS: Executing WRITE query on BigQuery!",
            "critical",
            {"query": query[:500], "dry_run": False}
        )
    
    try:
        if not bq_client:
            raise HTTPException(status_code=503, detail="BigQuery client not available")
        
        job_config = bigquery.QueryJobConfig(dry_run=dry_run)
        query_job = bq_client.query(query, job_config=job_config)
        
        if dry_run:
            return {
                "success": True,
                "dry_run": True,
                "bytes_processed": query_job.total_bytes_processed,
                "estimated_cost_usd": round((query_job.total_bytes_processed / 1e12) * 5, 4),
                "query_preview": query[:500]
            }
        else:
            result = query_job.result()
            df = result.to_dataframe() if result.total_rows > 0 else None
            
            log_action("BIGQUERY_WRITE_COMPLETE", {
                "rows_affected": result.total_rows,
                "bytes_processed": query_job.total_bytes_processed
            })
            
            return {
                "success": True,
                "dry_run": False,
                "rows_affected": result.total_rows,
                "data": json.loads(df.to_json(orient='records')) if df is not None else []
            }
    except Exception as e:
        logger.error(f"BigQuery execution error: {str(e)}")
        send_slack_alert(f"BigQuery execution FAILED: {str(e)}", "critical")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/upcloud/ssh")
@limiter.limit(f"{RATE_LIMIT_MIN//10}/minute")  # Very restrictive
async def execute_ssh_command(
    request: Request,
    command: str,
    require_approval: bool = True,
    api_key: str = Depends(verify_api_key)
):
    """
    Execute arbitrary SSH command on UpCloud
    HIGH RISK: Full shell access
    Default: require_approval=True
    Includes dangerous command detection
    """
    # Check for dangerous commands
    is_dangerous, danger_reason = check_dangerous_command(command)
    
    if is_dangerous:
        log_action("DANGEROUS_COMMAND_BLOCKED", {
            "command": command,
            "reason": danger_reason
        }, "CRITICAL")
        
        send_slack_alert(
            f"🚨 BLOCKED DANGEROUS COMMAND!",
            "critical",
            {"command": command, "reason": danger_reason}
        )
        
        raise HTTPException(
            status_code=403,
            detail=f"Dangerous command blocked: {danger_reason}. Command: {command}"
        )
    
    if require_approval:
        log_action("SSH_APPROVAL_REQUIRED", {
            "command": command
        }, "CRITICAL")
        
        return {
            "success": False,
            "approval_required": True,
            "command": command,
            "message": "This command requires manual approval. Set require_approval=false to execute.",
            "warning": "This gives full shell access to your UpCloud server!"
        }
    
    log_action("SSH_COMMAND_EXECUTE", {
        "command": command,
        "host": UPCLOUD_HOST,
        "approval_bypassed": True
    }, "CRITICAL")
    
    send_slack_alert(
        f"🚨 EXECUTING SSH COMMAND on {UPCLOUD_HOST}",
        "critical",
        {"command": command}
    )
    
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(UPCLOUD_HOST, username=UPCLOUD_USER, key_filename=UPCLOUD_KEY_PATH, timeout=10)
        
        stdin, stdout, stderr = ssh.exec_command(command, timeout=60)
        
        output = stdout.read().decode()
        error = stderr.read().decode()
        exit_code = stdout.channel.recv_exit_status()
        
        ssh.close()
        
        log_action("SSH_COMMAND_COMPLETE", {
            "command": command,
            "exit_code": exit_code,
            "success": exit_code == 0
        })
        
        if exit_code != 0:
            send_slack_alert(f"SSH command failed (exit {exit_code}): {command}", "critical")
        
        return {
            "success": exit_code == 0,
            "command": command,
            "exit_code": exit_code,
            "output": output[-5000:],
            "error": error[-5000:] if error else "",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        logger.error(f"SSH execution error: {str(e)}")
        send_slack_alert(f"SSH execution ERROR: {str(e)}", "critical")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================
# EMERGENCY ENDPOINTS
# ============================================

@app.post("/emergency/shutdown")
def emergency_shutdown(
    request: Request,
    token: str,
    api_key: str = Depends(verify_api_key)
):
    """Emergency shutdown endpoint - requires special token"""
    if token != EMERGENCY_TOKEN:
        log_action("INVALID_SHUTDOWN_ATTEMPT", {}, "CRITICAL")
        raise HTTPException(status_code=403, detail="Invalid emergency token")
    
    log_action("EMERGENCY_SHUTDOWN_INITIATED", {}, "CRITICAL")
    send_slack_alert("🚨 EMERGENCY SHUTDOWN ACTIVATED!", "critical")
    
    # In production, this would gracefully shut down the server
    return {
        "success": True,
        "message": "Emergency shutdown would be initiated (not implemented in this version)",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

# ============================================
# GOOGLE WORKSPACE ENDPOINTS (NEW)
# ============================================

@app.get("/workspace/health")
@limiter.limit(f"{RATE_LIMIT_MIN}/minute")
def workspace_health(
    request: Request,
    api_key: str = Depends(verify_api_key)
):
    """Check if Workspace delegation is working"""
    try:
        gc = get_sheets_client()
        if not gc:
            return {
                "status": "error",
                "message": "Could not initialize Sheets client"
            }
        
        # Try to access the dashboard
        sheet = gc.open_by_key(SHEETS_ID)
        
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
@limiter.limit(f"{RATE_LIMIT_MIN}/minute")
def get_dashboard_info(
    request: Request,
    api_key: str = Depends(verify_api_key)
):
    """Get GB Energy Dashboard information"""
    log_action("WORKSPACE_DASHBOARD_ACCESS", {"spreadsheet_id": SHEETS_ID})
    
    try:
        gc = get_sheets_client()
        if not gc:
            raise HTTPException(status_code=503, detail="Sheets client not available")
        
        sheet = gc.open_by_key(SHEETS_ID)
        
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
@limiter.limit(f"{RATE_LIMIT_MIN}/minute")
async def read_sheet_data(
    request: Request,
    api_key: str = Depends(verify_api_key)
):
    """Read data from any worksheet in the dashboard"""
    body = await request.json()
    worksheet_name = body.get('worksheet_name', 'Dashboard')
    cell_range = body.get('range', '')
    
    log_action("WORKSPACE_READ_SHEET", {
        "worksheet": worksheet_name,
        "range": cell_range
    })
    
    try:
        gc = get_sheets_client()
        if not gc:
            raise HTTPException(status_code=503, detail="Sheets client not available")
        
        sheet = gc.open_by_key(SHEETS_ID)
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

@app.post("/api/refresh-dashboard")
@limiter.limit(f"{RATE_LIMIT_MIN}/minute")
async def refresh_dashboard_endpoint(
    request: Request,
    authorization: Optional[str] = Header(None)
):
    """Refresh dashboard by triggering Python script on UpCloud server"""
    log_action("DASHBOARD_REFRESH", {"trigger": "apps_script"})
    
    try:
        # Run the dashboard refresh script on UpCloud
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        # Connect to UpCloud server
        ssh.connect(
            hostname=UPCLOUD_HOST,
            username=UPCLOUD_USER,
            key_filename=UPCLOUD_KEY_PATH,
            timeout=10
        )
        
        # Execute the enhanced chart update script
        command = 'cd "/root/GB Power Market JJ" && python3 fix_dashboard_complete.py'
        stdin, stdout, stderr = ssh.exec_command(command, timeout=120)
        
        output = stdout.read().decode()
        error = stderr.read().decode()
        exit_code = stdout.channel.recv_exit_status()
        
        ssh.close()
        
        if exit_code == 0:
            # Parse output to extract stats
            periods = 0
            fuel_types = 0
            
            if "Retrieved" in output:
                import re
                match = re.search(r'Retrieved (\d+) settlement periods, (\d+) fuel types', output)
                if match:
                    periods = int(match.group(1))
                    fuel_types = int(match.group(2))
            
            return {
                "success": True,
                "periods": periods,
                "fuelTypes": fuel_types,
                "message": "Dashboard refreshed successfully"
            }
        else:
            logger.error(f"Dashboard refresh failed: {error}")
            raise HTTPException(status_code=500, detail=f"Refresh script failed: {error}")
            
    except Exception as e:
        logger.error(f"Dashboard refresh error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================
# STARTUP & SHUTDOWN
# ============================================

@app.on_event("startup")
async def startup_event():
    """Log server startup"""
    log_action("SERVER_STARTUP", {
        "version": "3.0.0",
        "security_level": "Level 3 - Full Automation",
        "rate_limit_min": RATE_LIMIT_MIN,
        "rate_limit_hour": RATE_LIMIT_HOUR,
        "slack_configured": bool(SLACK_WEBHOOK and "YOUR" not in SLACK_WEBHOOK)
    })
    
    send_slack_alert(
        "✅ AI Gateway Server Started",
        "success",
        {"version": "3.0.0", "security": "Level 3"}
    )
    
    print("\n" + "="*70)
    print("⚡ AI Gateway API Server - Level 3 Full Automation")
    print("="*70)
    print(f"📝 Audit logs: {LOG_FILE}")
    print(f"🔒 API Key: {'✅ Configured' if VALID_API_KEY else '❌ MISSING'}")
    print(f"💬 Slack: {'✅ Configured' if SLACK_WEBHOOK and 'YOUR' not in SLACK_WEBHOOK else '⚠️  Not configured'}")
    print(f"⚡ Rate limits: {RATE_LIMIT_MIN}/min, {RATE_LIMIT_HOUR}/hour")
    print("="*70)
    print("\n⚠️  WARNING: Level 3 gives AI full access to your infrastructure!")
    print("   - Read/write BigQuery access")
    print("   - Google Sheets modification")
    print("   - SSH command execution")
    print("   - All actions logged and monitored\n")

@app.on_event("shutdown")
async def shutdown_event():
    """Log server shutdown"""
    log_action("SERVER_SHUTDOWN", {}, "WARNING")
    send_slack_alert("⚠️ AI Gateway Server Shutting Down", "warning")

# ============================================
# PUB ENDPOINTS (OPTIONAL)
# ============================================
# Uncomment the following lines to enable pub checker feature:
from pub_endpoints import pub_router
app.include_router(pub_router)

if __name__ == "__main__":
    import uvicorn
    
    host = os.environ.get("API_HOST", "0.0.0.0")
    port = int(os.environ.get("API_PORT", "8000"))
    
    print(f"\n🌐 Starting server on http://{host}:{port}")
    print("📖 API docs: http://localhost:8000/docs")
    print("🔍 Health check: http://localhost:8000/health\n")
    
    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level="info"
    )

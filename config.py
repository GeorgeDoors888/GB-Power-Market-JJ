"""
Centralized Configuration for GB Power Market JJ
SINGLE SOURCE OF TRUTH for all IDs and credentials
"""

# ==========================================
# GOOGLE SHEETS CONFIGURATION
# ==========================================
# ⚠️ CRITICAL: This is the ONLY place to define spreadsheet IDs
# Last updated: 2025-12-12 16:45 GMT
# Verified by: User correction

GOOGLE_SHEETS_CONFIG = {
    # Main Dashboard - Primary analytics and live data
    'MAIN_DASHBOARD_ID': '1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA',
    'MAIN_DASHBOARD_URL': 'https://docs.google.com/spreadsheets/d/1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA/edit',
    'MAIN_DASHBOARD_NAME': 'GB Power Market Dashboard',
}

# ==========================================
# BIGQUERY CONFIGURATION
# ==========================================
BIGQUERY_CONFIG = {
    'PROJECT_ID': 'inner-cinema-476211-u9',  # NOT jibber-jabber-knowledge!
    'DATASET': 'uk_energy_prod',
    'LOCATION': 'US',  # NOT europe-west2!
}

# ==========================================
# CREDENTIALS
# ==========================================
CREDENTIALS_CONFIG = {
    'GCP_CREDENTIALS_FILE': 'inner-cinema-credentials.json',
}

# ==========================================
# HELPER FUNCTIONS
# ==========================================
def get_main_dashboard_id():
    """Get the main dashboard spreadsheet ID."""
    return GOOGLE_SHEETS_CONFIG['MAIN_DASHBOARD_ID']

def get_main_dashboard_url():
    """Get the main dashboard URL."""
    return GOOGLE_SHEETS_CONFIG['MAIN_DASHBOARD_URL']

def validate_spreadsheet_connection(gc, sheet_id=None):
    """
    Validate that we're connecting to the correct spreadsheet.
    
    Args:
        gc: Authorized gspread client
        sheet_id: Optional sheet ID to validate (defaults to MAIN_DASHBOARD_ID)
    
    Returns:
        Spreadsheet object if valid
    
    Raises:
        Exception if wrong spreadsheet or user rejects
    """
    if sheet_id is None:
        sheet_id = get_main_dashboard_id()
    
    sh = gc.open_by_key(sheet_id)
    
    print("="*80)
    print("SPREADSHEET VALIDATION")
    print("="*80)
    print(f"Title: {sh.title}")
    print(f"ID: {sheet_id}")
    print(f"URL: {sh.url}")
    print(f"Expected: {GOOGLE_SHEETS_CONFIG['MAIN_DASHBOARD_NAME']}")
    print("="*80)
    
    if sheet_id != get_main_dashboard_id():
        print(f"⚠️  WARNING: Using non-standard sheet ID!")
        print(f"   Expected: {get_main_dashboard_id()}")
        print(f"   Actual: {sheet_id}")
    
    return sh

# ==========================================
# DEPLOYMENT ENDPOINTS
# ==========================================
DEPLOYMENT_CONFIG = {
    'CHATGPT_PROXY': 'https://gb-power-market-jj.vercel.app/api/proxy-v2',
    'IRIS_SERVER': '94.237.55.234',
    'GENERATOR_MAP': 'http://94.237.55.15/gb_power_comprehensive_map.html',
}

# ==========================================
# USAGE EXAMPLE
# ==========================================
"""
# In any Python script:

from config import GOOGLE_SHEETS_CONFIG, validate_spreadsheet_connection
import gspread
from google.oauth2.service_account import Credentials

# Get credentials
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
CREDS = Credentials.from_service_account_file('inner-cinema-credentials.json', scopes=SCOPES)
gc = gspread.authorize(CREDS)

# Use centralized ID
SHEET_ID = GOOGLE_SHEETS_CONFIG['MAIN_DASHBOARD_ID']

# Validate before updating (RECOMMENDED)
sh = validate_spreadsheet_connection(gc, SHEET_ID)

# Now safe to update
ws = sh.worksheet('Dashboard')
ws.update('A1', [['Updated!']])
"""

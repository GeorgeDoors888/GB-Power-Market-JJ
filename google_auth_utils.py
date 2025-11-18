"""
Google Authentication Utilities with Domain-Wide Delegation Support
====================================================================
Drop-in replacement for your existing authentication code.

USAGE:
------
Replace this:
    from google.oauth2 import service_account
    creds = service_account.Credentials.from_service_account_file(
        'inner-cinema-credentials.json',
        scopes=[...]
    )

With this:
    from google_auth_utils import get_credentials
    creds = get_credentials()  # Automatically uses delegation if configured

"""

import os
from google.oauth2 import service_account
from google.cloud import bigquery
import gspread

# Configuration
PROJECT_ID = "inner-cinema-476211-u9"
LOCATION = "US"
CREDENTIALS_FILE = os.environ.get(
    'GOOGLE_APPLICATION_CREDENTIALS',
    'inner-cinema-credentials.json'
)

# Check if domain-wide delegation is enabled
ADMIN_EMAIL = os.environ.get('GOOGLE_WORKSPACE_ADMIN_EMAIL')
USE_DELEGATION = ADMIN_EMAIL is not None

# Default scopes
DEFAULT_SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/documents',
    'https://www.googleapis.com/auth/drive.readonly',
    'https://www.googleapis.com/auth/script.projects',
    'https://www.googleapis.com/auth/bigquery'
]

def get_credentials(scopes=None, force_delegation=None, subject=None):
    """
    Get Google API credentials with optional domain-wide delegation.
    
    Args:
        scopes (list): OAuth scopes. Defaults to DEFAULT_SCOPES
        force_delegation (bool): Force delegation on/off. None = auto-detect
        subject (str): Email to impersonate. Defaults to GOOGLE_WORKSPACE_ADMIN_EMAIL
    
    Returns:
        google.auth.credentials.Credentials: Credentials object
    
    Examples:
        # Auto-detect delegation (uses env var GOOGLE_WORKSPACE_ADMIN_EMAIL)
        creds = get_credentials()
        
        # Force standard auth (no delegation)
        creds = get_credentials(force_delegation=False)
        
        # Force delegation with specific user
        creds = get_credentials(force_delegation=True, subject='user@domain.com')
        
        # Custom scopes
        creds = get_credentials(scopes=['https://www.googleapis.com/auth/spreadsheets'])
    """
    if scopes is None:
        scopes = DEFAULT_SCOPES
    
    # Load base credentials
    creds = service_account.Credentials.from_service_account_file(
        CREDENTIALS_FILE,
        scopes=scopes
    )
    
    # Determine if we should use delegation
    use_delegation = force_delegation if force_delegation is not None else USE_DELEGATION
    impersonate_user = subject if subject is not None else ADMIN_EMAIL
    
    if use_delegation and impersonate_user:
        # Create delegated credentials
        print(f"🔐 Using domain-wide delegation (impersonating: {impersonate_user})")
        creds = creds.with_subject(impersonate_user)
    
    return creds

def get_bigquery_client(use_delegation=None):
    """
    Get BigQuery client with optional delegation.
    
    Args:
        use_delegation (bool): Use delegation. None = auto-detect
    
    Returns:
        google.cloud.bigquery.Client: BigQuery client
    
    Example:
        client = get_bigquery_client()
        df = client.query("SELECT * FROM table").to_dataframe()
    """
    creds = get_credentials(force_delegation=use_delegation)
    return bigquery.Client(
        project=PROJECT_ID,
        location=LOCATION,
        credentials=creds
    )

def get_sheets_client(use_delegation=None):
    """
    Get gspread (Sheets) client with optional delegation.
    
    Args:
        use_delegation (bool): Use delegation. None = auto-detect
    
    Returns:
        gspread.Client: Sheets client
    
    Example:
        gc = get_sheets_client()
        sheet = gc.open_by_key('SHEET_ID')
        worksheet = sheet.worksheet('Sheet1')
    """
    creds = get_credentials(force_delegation=use_delegation)
    return gspread.authorize(creds)

def print_auth_status():
    """Print current authentication configuration"""
    print(f"""
╔══════════════════════════════════════════════════════════════════════╗
║                    Authentication Status                             ║
╚══════════════════════════════════════════════════════════════════════╝

Credentials File: {CREDENTIALS_FILE}
Project ID: {PROJECT_ID}
Location: {LOCATION}

Domain-Wide Delegation:
  Enabled: {'✅ YES' if USE_DELEGATION else '❌ NO'}
  Admin Email: {ADMIN_EMAIL if ADMIN_EMAIL else 'Not configured'}
  
Authentication Mode:
  {'🔓 DELEGATED ACCESS' if USE_DELEGATION else '🔒 STANDARD ACCESS'}
  {'(Can access all files admin can access)' if USE_DELEGATION else '(Only explicitly shared files)'}

To enable delegation:
  export GOOGLE_WORKSPACE_ADMIN_EMAIL="george@upowerenergy.uk"
  
To disable delegation:
  unset GOOGLE_WORKSPACE_ADMIN_EMAIL

╚══════════════════════════════════════════════════════════════════════╝
""")

# Backward compatibility aliases
def get_bq_client(**kwargs):
    """Alias for get_bigquery_client()"""
    return get_bigquery_client(**kwargs)

def get_gc_client(**kwargs):
    """Alias for get_sheets_client()"""
    return get_sheets_client(**kwargs)

if __name__ == "__main__":
    # Test script
    print_auth_status()
    
    # Test credentials
    try:
        creds = get_credentials()
        print("✅ Credentials loaded successfully")
        
        # Test BigQuery
        bq = get_bigquery_client()
        datasets = list(bq.list_datasets())
        print(f"✅ BigQuery working: {len(datasets)} datasets accessible")
        
        # Test Sheets
        gc = get_sheets_client()
        sheets = gc.openall()
        print(f"✅ Sheets working: {len(sheets)} sheets accessible")
        
        if USE_DELEGATION:
            print(f"\n🎉 Domain-wide delegation is ACTIVE!")
            print(f"   Accessing files as: {ADMIN_EMAIL}")
        else:
            print(f"\n📋 Using standard authentication")
            print(f"   Only seeing explicitly shared files")
            print(f"\n   To enable delegation:")
            print(f"   export GOOGLE_WORKSPACE_ADMIN_EMAIL='george@upowerenergy.uk'")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        if USE_DELEGATION and "unauthorized_client" in str(e).lower():
            print(f"\n⚠️  Domain-wide delegation not yet authorized!")
            print(f"   Run: python3 setup_delegation.py")

"""
Copy this code to REPLACE the get_sheets_client() function in api_gateway.py
Find the function around line 234 and replace it entirely with this version
"""

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
            from google.oauth2 import service_account as sa
            credentials = sa.Credentials.from_service_account_info(
                creds_dict,
                scopes=['https://www.googleapis.com/auth/spreadsheets',
                       'https://www.googleapis.com/auth/drive.readonly']
            ).with_subject('george@upowerenergy.uk')
            
            return gspread.authorize(credentials)
        else:
            # Fall back to local credentials file
            logger.info("Using local workspace-credentials.json file")
            from google.oauth2 import service_account as sa
            credentials = sa.Credentials.from_service_account_file(
                'workspace-credentials.json',
                scopes=['https://www.googleapis.com/auth/spreadsheets',
                       'https://www.googleapis.com/auth/drive.readonly']
            ).with_subject('george@upowerenergy.uk')
            
            return gspread.authorize(credentials)
            
    except Exception as e:
        logger.error(f"Failed to initialize Sheets client: {e}")
        logger.error(traceback.format_exc())
        return None

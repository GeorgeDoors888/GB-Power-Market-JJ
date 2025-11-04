from google.oauth2 import service_account
from googleapiclient.discovery import build
from google.cloud import bigquery
import os

# ⚠️ WARNING: Full Drive access enabled - use carefully!
DRIVE_SCOPES = [
    "https://www.googleapis.com/auth/drive",  # Full read/write access
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/documents",
    "https://www.googleapis.com/auth/presentations"
]
BQ_SCOPES = ["https://www.googleapis.com/auth/bigquery"]

def drive_client():
    # Use Drive-specific service account (jibber-jabber-knowledge)
    drive_sa = os.environ.get("DRIVE_SERVICE_ACCOUNT", os.environ["GOOGLE_APPLICATION_CREDENTIALS"])
    
    # Check if domain-wide delegation is enabled
    admin_email = os.environ.get("GOOGLE_WORKSPACE_ADMIN_EMAIL")
    
    if admin_email:
        # Use domain-wide delegation to impersonate admin user
        print(f"🔐 Using domain-wide delegation (impersonating: {admin_email})")
        creds = service_account.Credentials.from_service_account_file(
            drive_sa, 
            scopes=DRIVE_SCOPES,
            subject=admin_email  # Impersonate this user
        )
    else:
        # Regular service account access (requires manual sharing)
        creds = service_account.Credentials.from_service_account_file(
            drive_sa, scopes=DRIVE_SCOPES
        )
    
    return build("drive", "v3", credentials=creds, cache_discovery=False)

def bq_client():
    # Use BigQuery-specific service account (inner-cinema-476211-u9)
    bq_sa = os.environ["GOOGLE_APPLICATION_CREDENTIALS"]
    creds = service_account.Credentials.from_service_account_file(
        bq_sa, scopes=BQ_SCOPES
    )
    return bigquery.Client(project=os.environ["GCP_PROJECT"], credentials=creds)

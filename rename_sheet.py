
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

SERVICE_ACCOUNT_FILE = "workspace-credentials.json"
SCOPES = ["https://www.googleapis.com/auth/drive"]

SPREADSHEET_ID = "1LmMq4OEE639Y-XXpOJ3xnvpAmHB6vUovh5g6gaU_vzc"

def rename_spreadsheet():
    creds = Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES
    )
    service = build("drive", "v3", credentials=creds)
    
    print(f"Renaming spreadsheet: {SPREADSHEET_ID}")
    
    body = {'name': 'GB Energy Dashboard V3'}
    
    try:
        service.files().update(
            fileId=SPREADSHEET_ID,
            body=body
        ).execute()
        print("✅ Successfully renamed spreadsheet to 'GB Energy Dashboard V3'")
    except Exception as e:
        print(f"❌ Error renaming spreadsheet: {e}")

if __name__ == "__main__":
    rename_spreadsheet()

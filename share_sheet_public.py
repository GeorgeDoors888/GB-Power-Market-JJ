
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

SERVICE_ACCOUNT_FILE = "workspace-credentials.json"
SCOPES = ["https://www.googleapis.com/auth/drive"]

SPREADSHEET_ID = "1LmMq4OEE639Y-XXpOJ3xnvpAmHB6vUovh5g6gaU_vzc"

def share_spreadsheet():
    creds = Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES
    )
    service = build("drive", "v3", credentials=creds)
    
    print(f"Sharing spreadsheet: {SPREADSHEET_ID}")
    
    # Create permission for anyone with the link to be a reader
    user_permission = {
        'type': 'anyone',
        'role': 'reader',
    }
    
    try:
        service.permissions().create(
            fileId=SPREADSHEET_ID,
            body=user_permission,
            fields='id',
        ).execute()
        print("✅ Successfully shared spreadsheet with 'anyone with link' as reader.")
    except Exception as e:
        print(f"❌ Error sharing spreadsheet: {e}")

if __name__ == "__main__":
    share_spreadsheet()

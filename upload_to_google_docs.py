import os

from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# Path to the service account credentials
SERVICE_ACCOUNT_FILE = "jibber_jaber_key.json"
SCOPES = ["https://www.googleapis.com/auth/documents"]

# Authenticate using the service account
credentials = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
service = build("docs", "v1", credentials=credentials)

# Path to the file to upload
file_path = "Updated_Report.md"

# Read the content of the file
with open(file_path, "r") as file:
    content = file.read()

# Create a new Google Docs document
document = service.documents().create(body={"title": "Updated Report"}).execute()
document_id = document.get("documentId")

# Update the document with the content
requests = [{"insertText": {"location": {"index": 1}, "text": content}}]
service.documents().batchUpdate(
    documentId=document_id, body={"requests": requests}
).execute()

print(
    f"Document uploaded successfully. View it at: https://docs.google.com/document/d/{document_id}"
)

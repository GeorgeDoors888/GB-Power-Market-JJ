"""
google_docs_progress.py
Creates a Google Doc and provides functions to update it with download progress.
"""
import os
from google.oauth2 import service_account
from googleapiclient.discovery import build

# --- CONFIG ---
SCOPES = ['https://www.googleapis.com/auth/documents']
SERVICE_ACCOUNT_FILE = 'google_service_account.json'  # Place your credentials here

def create_google_doc(title="Data Download Progress"):
    creds = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    service = build('docs', 'v1', credentials=creds)
    doc = service.documents().create(body={"title": title}).execute()
    doc_id = doc.get('documentId')
    print(f"Created Google Doc: https://docs.google.com/document/d/{doc_id}/edit")
    return doc_id

def write_progress(doc_id, text):
    creds = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    service = build('docs', 'v1', credentials=creds)
    requests = [
        {
            'insertText': {
                'location': {
                    'index': 1
                },
                'text': text + '\n'
            }
        }
    ]
    service.documents().batchUpdate(documentId=doc_id, body={'requests': requests}).execute()

if __name__ == "__main__":
    # Example usage: create doc and write a test message
    doc_id = create_google_doc()
    write_progress(doc_id, "Download started...")

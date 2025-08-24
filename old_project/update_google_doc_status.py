"""
update_google_doc_status.py

This script will prompt you to authenticate in your browser and append a status message to your Google Doc.
"""
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ['https://www.googleapis.com/auth/documents']
DOCUMENT_ID = '1b1xUT2Q-9y1SXaUM-3sEsPYtpYKKpInIBNHHvgHAIYQ'


def get_creds():
    flow = InstalledAppFlow.from_client_secrets_file(
        'client_secret.json', SCOPES)
    creds = flow.run_local_server(port=0)
    return creds


def append_status_to_doc(doc_id, status_message):
    creds = get_creds()
    service = build('docs', 'v1', credentials=creds)
    requests = [{
        'insertText': {
            'location': {'index': 1},
            'text': status_message + '\n'
        }
    }]
    service.documents().batchUpdate(documentId=doc_id, body={'requests': requests}).execute()
    print('Status message appended to the Google Doc.')


def main():
    status_message = input('Enter the status message to append to the Google Doc: ')
    append_status_to_doc(DOCUMENT_ID, status_message)
    print(f'View your doc at: https://docs.google.com/document/d/{DOCUMENT_ID}/edit')


if __name__ == "__main__":
    main()

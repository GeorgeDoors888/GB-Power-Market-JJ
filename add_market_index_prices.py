from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import os.path
import pickle

# Define the scope
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

# Spreadsheet ID and range
SPREADSHEET_ID = '1FoA72QMekY6JSqyU7DJdFnw0SeHFdgAdoX9jhJh8D2M'  # Replace with your spreadsheet ID
RANGE_NAME = 'Sheet1!A1'  # Replace with the desired range

# Data to be added
data = [
    ["Market Index Prices"],
    ["Market Index Price data is received from each of the appointed Market Index Data Providers (MIDPs) and reflects the price of wholesale electricity in Great Britain for the relevant period in the short-term markets."],
    ["Market Index Prices are a key component in the calculation of System Buy Price and System Sell Price for each Settlement Period."],
    ["What You Need to Know While Using This Data"],
    ["* The graph's default view is the last 24 hours"],
]

# Authenticate and build the service
creds = None
# The file token.pickle stores the user's access and refresh tokens, and is
# created automatically when the authorization flow completes for the first
# time.
if os.path.exists('token.pickle'):
    with open('token.pickle', 'rb') as token:
        creds = pickle.load(token)
# If there are no (valid) credentials available, let the user log in.
if not creds or not creds.valid:
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
    else:
        flow = InstalledAppFlow.from_client_secrets_file(  
            'credentials.json', SCOPES)  # Path to your credentials.json file
        creds = flow.run_local_server(port=0)
    # Save the credentials for the next run
    with open('token.pickle', 'wb') as token:
        pickle.dump(creds, token)

service = build('sheets', 'v4', credentials=creds)

# Prepare the request body
body = {
    'values': data
}

# Call the Sheets API to update the spreadsheet
sheet = service.spreadsheets()
result = sheet.values().update(
    spreadsheetId=SPREADSHEET_ID,
    range=RANGE_NAME,
    valueInputOption='RAW',
    body=body
).execute()

print(f"{result.get('updatedCells')} cells updated.")

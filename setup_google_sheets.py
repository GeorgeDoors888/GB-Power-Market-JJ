import json
import os

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# Load service account credentials
SERVICE_ACCOUNT_FILE = "jibber_jabber_key.json"
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

credentials = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES
)

# Initialize Google Sheets and Drive API clients
sheets_service = build("sheets", "v4", credentials=credentials)
drive_service = build("drive", "v3", credentials=credentials)

# Google Sheet ID and GeoJSON file path
SPREADSHEET_ID = "12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8"  # Updated with the provided Google Sheet ID
GEOJSON_FILE_PATH = "system_regulatory/gis/merged_geojson.geojson"
script_id = "AKfycbx1a2b3c4d5e6f7g8h9i0j"  # Replace with your Apps Script project ID

# Step 1: Upload GeoJSON file to Google Drive
file_metadata = {"name": "DNO_Map_GeoJSON.json", "mimeType": "application/json"}
media = MediaFileUpload(GEOJSON_FILE_PATH, mimetype="application/json")
file = (
    drive_service.files()
    .create(body=file_metadata, media_body=media, fields="id")
    .execute()
)
geojson_file_id = file.get("id")
print(f"Uploaded GeoJSON file. File ID: {geojson_file_id}")

# Step 2: Update Google Sheet with DNO data
DNO_DATA = [
    ["ID", "Name", "Value"],
    ["1", "DNO Area 1", "10000"],
    ["2", "DNO Area 2", "12000"],
    ["3", "DNO Area 3", "14000"],
]

sheets_service.spreadsheets().values().update(
    spreadsheetId=SPREADSHEET_ID,
    range="DNO_Data!A1",
    valueInputOption="RAW",
    body={"values": DNO_DATA},
).execute()
print("Updated Google Sheet with DNO data.")

# Step 3: Configure Apps Script project with GeoJSON file ID
apps_script_service = build("script", "v1", credentials=credentials)

# Update script properties
apps_script_service.projects().updateContent(
    scriptId=script_id,
    body={
        "files": [
            {
                "name": "Code",
                "type": "SERVER_JS",
                "source": f"var GEOJSON_FILE_ID = '{geojson_file_id}';",
            }
        ]
    },
).execute()
print("Configured Apps Script project with GeoJSON file ID.")

# Add logging to verify the active account and storage status
about = drive_service.about().get(fields="user, storageQuota").execute()
print("Active Account:", about["user"]["emailAddress"])
print("Storage Quota:", about["storageQuota"])

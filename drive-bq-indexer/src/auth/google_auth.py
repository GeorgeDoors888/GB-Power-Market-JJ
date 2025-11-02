from google.oauth2 import service_account
from googleapiclient.discovery import build
from google.cloud import bigquery
import os

SCOPES = [
    "https://www.googleapis.com/auth/drive.readonly",
    "https://www.googleapis.com/auth/bigquery",
]

def drive_client():
    creds = service_account.Credentials.from_service_account_file(
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"], scopes=SCOPES
    )
    return build("drive", "v3", credentials=creds, cache_discovery=False)

def bq_client():
    return bigquery.Client(project=os.environ["GCP_PROJECT"])

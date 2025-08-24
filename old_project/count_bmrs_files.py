"""
count_bmrs_files.py
Summarizes all CSVs in bmrs_historical_data by type and year, estimates download rate, and files remaining.
"""
import os
import glob
import time
from collections import defaultdict

# Google Docs API imports
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# --- CONFIG ---
BASE_DIR = 'bmrs_historical_data'
END_DATE = time.strftime('%Y-%m-%d')

summary = defaultdict(lambda: defaultdict(int))
first_file_time = None
last_file_time = None
file_times = []
total_files = 0

for root, dirs, files in os.walk(BASE_DIR):
    for file in files:
        if file.endswith('.csv'):
            total_files += 1
            # Type is the first subfolder after BASE_DIR
            rel = os.path.relpath(root, BASE_DIR)
            parts = rel.split(os.sep)
            if len(parts) >= 2:
                ftype, year = parts[0], parts[1]
            elif len(parts) == 1:
                ftype, year = parts[0], 'unknown'
            else:
                ftype, year = 'unknown', 'unknown'
            summary[ftype][year] += 1
            # Get file creation/modification time
            fpath = os.path.join(root, file)
            mtime = os.path.getmtime(fpath)
            file_times.append(mtime)
            if first_file_time is None or mtime < first_file_time:
                first_file_time = mtime
            if last_file_time is None or mtime > last_file_time:
                last_file_time = mtime

# --- Google Docs update ---
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

# --- Calculate rate ---
rate_per_hour = None
if first_file_time and last_file_time and last_file_time > first_file_time:
    elapsed_hours = (last_file_time - first_file_time) / 3600
    rate_per_hour = total_files / elapsed_hours if elapsed_hours > 0 else None

# --- Estimate files to go ---
# For a full set, estimate from endpoints.csv (one file per endpoint per day)
import pandas as pd
endpoints = pd.read_csv('endpoints.csv')
num_types = endpoints['name'].nunique()
from datetime import datetime
start_date = datetime(2016, 1, 1)
end_date = datetime.now()
days = (end_date - start_date).days + 1
expected_total = num_types * days
files_remaining = expected_total - total_files


output = []
output.append("BMRS Download Summary:")
output.append(f"Total files downloaded: {total_files}")
output.append(f"Download rate: {rate_per_hour:.2f} files/hour" if rate_per_hour else "Download rate: N/A")
output.append(f"Expected total files: {expected_total}")
output.append(f"Files remaining: {files_remaining}")
output.append("\nBreakdown by type and year:")
for ftype in sorted(summary):
    for year in sorted(summary[ftype]):
        output.append(f"  {ftype} {year}: {summary[ftype][year]}")
output.append("\nFile types detected: " + ', '.join(sorted(summary.keys())))

print('\n'.join(output))

# Also send to Google Doc
try:
    append_status_to_doc(DOCUMENT_ID, '\n'.join(output))
    print(f"\nStatus also appended to Google Doc: https://docs.google.com/document/d/{DOCUMENT_ID}/edit")
except Exception as e:
    print(f"\nFailed to update Google Doc: {e}")

#!/usr/bin/env python3
from googleapiclient.discovery import build
import pickle

with open('token.pickle', 'rb') as f:
    creds = pickle.load(f)

service = build('sheets', 'v4', credentials=creds)

# Read wider range to find data
result = service.spreadsheets().values().get(
    spreadsheetId='1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA',
    range='Sheet1!A1:H50'
).execute()

values = result.get('values', [])
print(f'Found {len(values)} rows')
print()

for i, row in enumerate(values[:30], 1):
    if row:  # Only print non-empty rows
        print(f'Row {i}: {row[:8]}')

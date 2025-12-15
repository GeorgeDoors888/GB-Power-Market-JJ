#!/usr/bin/env python3
"""Quick read of Sheet1 data structure"""
from googleapiclient.discovery import build
import pickle

with open('token.pickle', 'rb') as f:
    creds = pickle.load(f)

service = build('sheets', 'v4', credentials=creds)
result = service.spreadsheets().values().get(
    spreadsheetId='1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA',
    range='Sheet1!A18:H31'
).execute()

values = result.get('values', [])
print('📊 Data from Sheet1 A18:H31')
print('=' * 80)
print()

if values and len(values) > 0:
    print(f"Headers (Row 18): {values[0]}")
    print()
    print("Column mapping:")
    for i, header in enumerate(values[0]):
        col_letter = chr(65 + i)
        print(f"   {col_letter}: {header}")
    print()
    print("Sample data (Rows 19-23):")
    for i, row in enumerate(values[1:6]):
        print(f"   Row {19+i}: {row}")
else:
    print("No data found")

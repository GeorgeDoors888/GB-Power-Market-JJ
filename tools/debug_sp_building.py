#!/usr/bin/env python3
import os
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

SHEET_ID = '1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA'
SA_PATH = '../inner-cinema-credentials.json'

SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
CREDS = Credentials.from_service_account_file(SA_PATH, scopes=SCOPES)
sheets = build('sheets', 'v4', credentials=CREDS).spreadsheets()

# Read Live Dashboard
live_vals = sheets.values().get(spreadsheetId=SHEET_ID, range='Live Dashboard!A1:Z60').execute().get('values', [])

headers = live_vals[0]
sp_idx = headers.index('SP') if 'SP' in headers else 0
gen_idx = headers.index('Generation_MW') if 'Generation_MW' in headers else None
ssp_idx = headers.index('SSP') if 'SSP' in headers else None
sbp_idx = headers.index('SBP') if 'SBP' in headers else None

print(f'Column indices: sp={sp_idx}, gen={gen_idx}, ssp={ssp_idx}, sbp={sbp_idx}')
print()

# Test SP building for first 5 rows
for i, row in enumerate(live_vals[1:6], start=1):
    sp_num = row[sp_idx] if len(row) > sp_idx else ''
    sp_label = f'SP{int(sp_num):02d}' if sp_num else ''
    
    gen_gw = ''
    if gen_idx and len(row) > gen_idx and row[gen_idx]:
        try:
            gen_val = float(row[gen_idx])
            gen_gw = f'{gen_val / 1000:.1f}'
            print(f'SP{i}: row[{gen_idx}]={row[gen_idx]} → gen_val={gen_val} → gen_gw={gen_gw}')
        except Exception as e:
            print(f'SP{i}: FAILED to convert row[{gen_idx}]={row[gen_idx]} - {e}')
    else:
        print(f'SP{i}: NO GEN DATA - gen_idx={gen_idx}, len(row)={len(row)}, row[gen_idx]={row[gen_idx] if len(row) > gen_idx else "OUT_OF_RANGE"}')
    
    print(f'  Final: [{sp_label}, {gen_gw}, ...]')
    print()

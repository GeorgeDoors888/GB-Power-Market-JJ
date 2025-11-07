#!/usr/bin/env python3
"""Check what data was actually pulled for today's dashboard"""

from google.oauth2 import service_account
from googleapiclient.discovery import build
import os

SHEET_ID = '12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8'
CREDS_FILE = '/Users/georgemajor/GB Power Market JJ/inner-cinema-credentials.json'

creds = service_account.Credentials.from_service_account_file(
    CREDS_FILE,
    scopes=['https://www.googleapis.com/auth/spreadsheets']
)
sheets = build('sheets', 'v4', credentials=creds).spreadsheets()

print("\n" + "="*100)
print("🔍 DETAILED DATA CHECK - IRIS Tables")
print("="*100)

# Check Live_Raw_Gen (from indgen_iris)
print("\n📊 Live_Raw_Gen Tab (bmrs_indgen_iris data):")
print("-"*100)
result = sheets.values().get(
    spreadsheetId=SHEET_ID,
    range='Live_Raw_Gen!A1:D10'
).execute()

values = result.get('values', [])
if values:
    for i, row in enumerate(values):
        if i == 0:
            print("Headers:", " | ".join(row))
            print("-"*100)
        else:
            print(f"Row {i}:", " | ".join(str(v) for v in row))
else:
    print("❌ NO DATA in Live_Raw_Gen tab")

# Check Live_Raw_Interconnectors (from fuelinst_iris)
print("\n🌐 Live_Raw_Interconnectors Tab (bmrs_fuelinst_iris data):")
print("-"*100)
result = sheets.values().get(
    spreadsheetId=SHEET_ID,
    range='Live_Raw_Interconnectors!A1:D10'
).execute()

values = result.get('values', [])
if values:
    for i, row in enumerate(values):
        if i == 0:
            print("Headers:", " | ".join(row))
            print("-"*100)
        else:
            print(f"Row {i}:", " | ".join(str(v) for v in row))
else:
    print("❌ NO DATA in Live_Raw_Interconnectors tab")

# Check main Live Dashboard to see if gen_mw and ic_net_mw columns have data
print("\n📈 Live Dashboard Tab - Check Generation & Interconnector Columns:")
print("-"*100)
result = sheets.values().get(
    spreadsheetId=SHEET_ID,
    range='Live Dashboard!A1:J10'
).execute()

values = result.get('values', [])
if values and len(values) > 0:
    headers = values[0]
    print("Headers:", " | ".join(headers))
    print("-"*100)
    
    # Find the indices for Demand_MW, Generation_MW, and IC_NET_MW
    try:
        demand_idx = headers.index('Demand_MW')
        gen_idx = headers.index('Generation_MW')
        ic_idx = headers.index('IC_NET_MW')
        
        print(f"\nColumn positions: Demand={demand_idx}, Generation={gen_idx}, Interconnectors={ic_idx}")
        print("\nFirst 5 settlement periods:")
        print("-"*100)
        
        for i in range(1, min(6, len(values))):
            row = values[i]
            sp = row[0] if len(row) > 0 else "?"
            demand = row[demand_idx] if len(row) > demand_idx else "EMPTY"
            gen = row[gen_idx] if len(row) > gen_idx else "EMPTY"
            ic = row[ic_idx] if len(row) > ic_idx else "EMPTY"
            
            print(f"SP {sp}: Demand={demand} MW, Generation={gen} MW, Interconnectors={ic} MW")
            
            # Check if values are actually empty or zero
            if demand == "" or demand == "EMPTY":
                print(f"  ⚠️  Demand_MW is EMPTY for SP {sp}")
            if gen == "" or gen == "EMPTY":
                print(f"  ⚠️  Generation_MW is EMPTY for SP {sp}")
            if ic == "" or ic == "EMPTY":
                print(f"  ⚠️  IC_NET_MW is EMPTY for SP {sp}")
                
    except ValueError as e:
        print(f"❌ Error finding columns: {e}")
        print(f"Available headers: {headers}")
else:
    print("❌ NO DATA in Live Dashboard tab")

print("\n" + "="*100 + "\n")

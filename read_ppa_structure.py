#!/usr/bin/env python3
"""
Read BESS sheet rows 26-49 to understand PPA calculations and Final Demand Customer structure
"""
import gspread
from google.oauth2.service_account import Credentials

SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
creds = Credentials.from_service_account_file('inner-cinema-credentials.json', scopes=SCOPES)
gc = gspread.authorize(creds)

ss = gc.open_by_key('1LmMq4OEE639Y-XXpOJ3xnvpAmHB6vUovh5g6gaU_vzc')
bess = ss.worksheet('BESS')

print('='*140)
print('BESS SHEET - ROWS 26-49 (All Columns A-M)')
print('='*140)
print()

# Read full range
data = bess.get('A26:M49')

# Print with column headers
print(f'{"Row":4} | {"A":25} | {"B":15} | {"C":15} | {"D":15} | {"E":15} | {"F":15} | {"G":15} | {"H":15} | {"I":15} | {"J":15} | {"K":15} | {"L":15} | {"M":15}')
print('-'*140)

for idx, row in enumerate(data, start=26):
    # Pad row to ensure 13 columns
    while len(row) < 13:
        row.append('')
    
    print(f'{idx:4} | {row[0][:25]:25} | {row[1][:15]:15} | {row[2][:15]:15} | {row[3][:15]:15} | {row[4][:15]:15} | {row[5][:15]:15} | {row[6][:15]:15} | {row[7][:15]:15} | {row[8][:15]:15} | {row[9][:15]:15} | {row[10][:15]:15} | {row[11][:15]:15} | {row[12][:15]:15}')

print()
print('='*140)
print('KEY OBSERVATIONS:')
print('='*140)
print()

# Look for PPA-related information
ppa_info = []
for idx, row in enumerate(data, start=26):
    row_text = ' '.join([str(cell) for cell in row if cell])
    if any(keyword in row_text.upper() for keyword in ['PPA', 'FINAL DEMAND', 'REVENUE', 'PRICE', 'CONTRACT']):
        ppa_info.append((idx, row_text[:150]))

if ppa_info:
    print('PPA/Revenue Related Rows:')
    for row_num, text in ppa_info:
        print(f'  Row {row_num}: {text}')
    print()

# Check for formulas in column C (E26:C49 seems like typo, probably means A26:C49)
print('Column C (Costs) - Key Values:')
for idx, row in enumerate(data, start=26):
    if len(row) > 2 and row[2]:
        print(f'  C{idx}: {row[2]}')

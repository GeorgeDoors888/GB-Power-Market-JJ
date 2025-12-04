#!/usr/bin/env python3
"""Show BESS sheet structure rows 26-50"""
import gspread
from google.oauth2.service_account import Credentials

SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
creds = Credentials.from_service_account_file('inner-cinema-credentials.json', scopes=SCOPES)
gc = gspread.authorize(creds)

ss = gc.open_by_key('1LmMq4OEE639Y-XXpOJ3xnvpAmHB6vUovh5g6gaU_vzc')
bess = ss.worksheet('BESS')

print('='*130)
print('BESS SHEET STRUCTURE - ROWS 26-50')
print('='*130)
print()
print('Row |     Column A           |    Column B    |    Column C    |    Column D    |    Column E    |    Column F    |    Column G    |    Column H    |')
print('-'*130)

for row_num in range(26, 51):
    row_data = bess.get(f'A{row_num}:H{row_num}')
    if row_data and row_data[0]:
        cells = row_data[0]
        while len(cells) < 8:
            cells.append('')
        
        print(f' {row_num:2d} | {cells[0][:22]:22} | {cells[1][:14]:14} | {cells[2][:14]:14} | {cells[3][:14]:14} | {cells[4][:14]:14} | {cells[5][:14]:14} | {cells[6][:14]:14} | {cells[7][:14]:14} |')

print()
print('='*130)
print('EXPLANATION OF LAYOUT')
print('='*130)
print()
print('LEFT SIDE (Columns A-C): "BtM PPA Non BESS Element Costs"')
print('  - Site consuming directly from grid WITHOUT battery optimization')
print('  - Column A: Cost category (DUoS, TNUoS, etc.)')
print('  - Column B: kWh consumed')
print('  - Column C: Cost (£)')
print()
print('RIGHT SIDE (Columns F-H): "BtM PPA BESS Costs"')
print('  - Battery charging costs (when BESS imports from grid)')
print('  - Column F: Rate (p/kWh or £/MWh)')
print('  - Column G: kWh charged')
print('  - Column H: Cost (£)')
print()
print('Columns D & E: Likely labels/spacers between the two sections')

#!/usr/bin/env python3
"""Show specific cell ranges E28:E38, F28:F38, G28:G37"""
import gspread
from google.oauth2.service_account import Credentials

SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
creds = Credentials.from_service_account_file('inner-cinema-credentials.json', scopes=SCOPES)
gc = gspread.authorize(creds)

ss = gc.open_by_key('1LmMq4OEE639Y-XXpOJ3xnvpAmHB6vUovh5g6gaU_vzc')
bess = ss.worksheet('BESS')

print('='*100)
print('CELL CONTENTS: E28:E38, F28:F38, G28:G37')
print('='*100)
print()
print('Row | Column E (Spacer?)      | Column F (Rate/Label)   | Column G (kWh/Volume)   |')
print('-'*100)

for row_num in range(28, 39):
    e_val = bess.acell(f'E{row_num}').value or ''
    f_val = bess.acell(f'F{row_num}').value or ''
    g_val = bess.acell(f'G{row_num}').value or ''
    
    print(f' {row_num:2d} | {e_val[:23]:23} | {f_val[:23]:23} | {g_val[:23]:23} |')

print()
print('='*100)
print('EXPLANATION:')
print('='*100)
print()
print('Column E (E28:E38):')
print('  - Appears to be empty/spacer column between Non-BESS and BESS sections')
print()
print('Column F (F28:F38):')
print('  - F28-F30: DUoS RATES (p/kWh) for Red/Amber/Green')
print('  - F31-F32: Network charge RATES (£/MWh) for TNUoS/BNUoS')
print('  - F34: "Total" label for Environmental Levies')
print('  - F35-F37: Environmental levy RATES (£/MWh) for CCL/RO/FiT')
print()
print('Column G (G28:G37):')
print('  - kWh volumes charged by BESS in each cost category')
print('  - G28: Red band kWh (should be 0 - avoiding expensive periods)')
print('  - G29: Amber band kWh')
print('  - G30: Green band kWh (largest - charging during cheap periods)')
print('  - G31-G37: Total kWh for network charges and levies')

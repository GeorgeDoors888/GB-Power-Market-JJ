#!/usr/bin/env python3
"""
Create Party_Wide Tab Only
Simplified version without heavy formatting
"""

import gspread
from google.oauth2.service_account import Credentials

SHEET_ID = "1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA"
CREDENTIALS_FILE = "inner-cinema-credentials.json"

# Category names (from Categories tab)
CATEGORIES = [
    "Generator", "Supplier", "Network Operator", "Interconnector",
    "Virtual Lead Party", "Storage Operator", "Distribution System Operator",
    "Transmission System Operator", "Non-Physical Trader", "Party Agent",
    "Data Aggregator", "Meter Operator", "Data Collector", "Licensed Distributor",
    "Supplier Agent", "Half Hourly Data Collector", "Non Half Hourly Data Collector",
    "Meter Administrator", "Balancing Mechanism Unit"
]

print("🔐 Authenticating...")
scopes = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
creds = Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=scopes)
gc = gspread.authorize(creds)

print("📊 Opening spreadsheet...")
wb = gc.open_by_key(SHEET_ID)

# Check if exists
try:
    sheet = wb.worksheet('Party_Wide')
    print("   ⚠️  Party_Wide exists, deleting...")
    wb.del_worksheet(sheet)
except:
    pass

print("➕ Creating Party_Wide tab...")
sheet = wb.add_worksheet(title='Party_Wide', rows=1000, cols=25)

# Build headers
headers = [['Party ID', 'Party Name'] + CATEGORIES + ['Total Categories']]

print("   Writing headers...")
sheet.update(values=headers, range_name='A1')

# Format headers (simple)
print("   Formatting headers...")
sheet.format('A1:Z1', {
    'backgroundColor': {'red': 0.26, 'green': 0.52, 'blue': 0.96},
    'textFormat': {'foregroundColor': {'red': 1, 'green': 1, 'blue': 1}, 'bold': True},
    'horizontalAlignment': 'CENTER'
})

# Write formula template in row 2
print("   Adding formula template...")
formulas_row2 = [
    'P001',  # Party ID
    '=IFERROR(VLOOKUP(A2,Parties!A:B,2,FALSE),"")'  # Party Name lookup
]

# Add formula for each category
for i, cat in enumerate(CATEGORIES):
    col_letter = chr(67 + i)  # C, D, E, ...
    formula = f'=IF(COUNTIFS(Party_Category!$A:$A,$A2,Party_Category!$B:$B,{col_letter}$1)>0,"TRUE","FALSE")'
    formulas_row2.append(formula)

# Total categories formula
end_col = chr(67 + len(CATEGORIES) - 1)
total_formula = f'=COUNTIF(C2:{end_col}2,"TRUE")'
formulas_row2.append(total_formula)

sheet.update(values=[formulas_row2], range_name='A2')

# Freeze header and first 2 columns
print("   Freezing rows/columns...")
sheet.freeze(rows=1, cols=2)

print("\n✅ Party_Wide tab created successfully!")
print("\n📋 Formula template in row 2:")
print("   • Copy row 2 down to add more parties")
print("   • Party ID should match Parties tab")
print("   • TRUE/FALSE flags auto-populate from Party_Category links")

#!/usr/bin/env python3
"""Detailed sheet structure analysis"""
import gspread
from google.oauth2.service_account import Credentials
import json

SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]
creds = Credentials.from_service_account_file('jibber_jabber_key.json', scopes=SCOPES)
gc = gspread.authorize(creds)

sheet = gc.open_by_key('12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8')
worksheet = sheet.worksheet('Sheet1')

# Get all values
all_values = worksheet.get_all_values()

print('=' * 120)
print('COMPLETE SHEET STRUCTURE ANALYSIS')
print('=' * 120)
print(f'Total rows: {len(all_values)}')
print(f'Total columns: {len(all_values[0]) if all_values else 0}')
print()

print('ROW-BY-ROW BREAKDOWN:')
print('=' * 120)

for i, row in enumerate(all_values, 1):
    print(f'\n--- ROW {i} ---')
    for j, cell in enumerate(row, 1):
        col_letter = chr(64 + j)  # A=65, B=66, etc.
        if cell:  # Only show non-empty cells
            print(f'  {col_letter}{i}: "{cell}"')

print('\n' + '=' * 120)
print('SPECIFIC DATA CELLS TO UPDATE:')
print('=' * 120)

# Analyze what data should be updated
fuel_types = ['Gas', 'Nuclear', 'Wind', 'Solar', 'Biomass', 'Hydro', 'Coal']
print('\nFuel generation cells (looking for these types):')
for fuel in fuel_types:
    for i, row in enumerate(all_values, 1):
        for j, cell in enumerate(row, 1):
            if fuel in cell:
                col_letter = chr(64 + j)
                print(f'  {fuel}: Found in {col_letter}{i} = "{cell}"')
                break

print('\nInterconnector cells (looking for country codes):')
countries = ['France', 'Netherlands', 'Belgium', 'Norway', 'Ireland']
for country in countries:
    for i, row in enumerate(all_values, 1):
        for j, cell in enumerate(row, 1):
            if country in cell:
                col_letter = chr(64 + j)
                print(f'  {country}: Found in {col_letter}{i} = "{cell}"')
                break

print('\n' + '=' * 120)
print('STRUCTURE SUMMARY:')
print('=' * 120)
print(f'Row 1: {all_values[0][0] if len(all_values) > 0 else "N/A"}')
print(f'Row 2: {all_values[1][0][:50] if len(all_values) > 1 else "N/A"}...')
print(f'Row 4: Headers - {all_values[3] if len(all_values) > 3 else "N/A"}')
print(f'Rows 5-11: Data rows with emojis and values')

#!/usr/bin/env python3
import gspread
from oauth2client.service_account import ServiceAccountCredentials

scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
creds = ServiceAccountCredentials.from_json_keyfile_name('/Users/georgemajor/GB Power Market JJ/inner-cinema-credentials.json', scope)
gc = gspread.authorize(creds)

sh = gc.open_by_key('1LmMq4OEE639Y-XXpOJ3xnvpAmHB6vUovh5g6gaU_vzc')
sheet = sh.worksheet('Battery Revenue Analysis')

print("🧹 VERIFYING CLEAN LAYOUT\n")
print("=" * 70)

print("\nRow 3 (Today's section header):")
print(f"  {sheet.row_values(3)[:3]}")

print("\nRow 25 (Historical section header):")
print(f"  {sheet.row_values(25)[:3]}")

print("\nRow 26 (Historical column headers):")
headers = sheet.row_values(26)
print(f"  {headers[:8]}")

print("\nRow 27 (First historical data - should be 2025-11-26):")
data = sheet.row_values(27)
print(f"  Date: {data[0]} | Acc: {data[1]} | Price: {data[5] if len(data) > 5 else 'N/A'}")

print("\nRow 80 (Unit Performance section header):")
print(f"  {sheet.row_values(80)[:3]}")

print("\nRow 81 (Unit Performance column headers):")
headers = sheet.row_values(81)
print(f"  {headers[:6]}")

print("\nRow 82 (First unit - should be battery name):")
data = sheet.row_values(82)
print(f"  Unit: {data[0]} | Acc: {data[1]} | Vol: {data[4] if len(data) > 4 else 'N/A'}")

print("\n" + "=" * 70)
print("✅ Layout check complete!")

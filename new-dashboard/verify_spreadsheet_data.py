#!/usr/bin/env python3
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
creds = ServiceAccountCredentials.from_json_keyfile_name('/Users/georgemajor/GB Power Market JJ/inner-cinema-credentials.json', scope)
gc = gspread.authorize(creds)

sh = gc.open_by_key('1LmMq4OEE639Y-XXpOJ3xnvpAmHB6vUovh5g6gaU_vzc')
sheet = sh.worksheet('Battery Revenue Analysis')

print("📊 SPREADSHEET DATA ANALYSIS\n")
print("=" * 60)

# Check header
print("\nRow 25 (Section Header):")
row25 = sheet.row_values(25)
print(f"  {row25[:5] if row25 else 'EMPTY'}")

print("\nRow 26 (Column Headers):")
row26 = sheet.row_values(26)
print(f"  {row26[:8] if row26 else 'EMPTY'}")

# Get all historical data
print("\n" + "=" * 60)
print("HISTORICAL DATA (rows 27+):")
print("=" * 60)

historical = sheet.get('A27:H100')
dates = []
for i, row in enumerate(historical, 27):
    if row and len(row) > 0 and row[0]:
        # Check if it looks like a date (starts with "20")
        if str(row[0]).startswith('20'):
            try:
                date_str = row[0]
                dates.append(date_str)
                # Only show first 5 and last 5
                if len(dates) <= 5 or i >= 65:  # Show first 5 and rows 65+
                    acc = row[1] if len(row) > 1 else 'N/A'
                    vol = row[4] if len(row) > 4 else 'N/A'
                    print(f"Row {i}: {date_str} | Acc: {acc} | Vol: {vol} MW")
            except:
                pass

if dates:
    print("\n" + "=" * 60)
    print("SUMMARY:")
    print("=" * 60)
    print(f"First date: {dates[0]}")
    print(f"Last date: {dates[-1]}")
    print(f"Total days: {len(dates)}")
    print(f"\n⚠️  Expected: 44-49 days covering Oct 8 - Nov 26, 2025")
    
    # Parse dates to check range
    try:
        first = datetime.strptime(dates[0], '%Y-%m-%d')
        last = datetime.strptime(dates[-1], '%Y-%m-%d')
        span = (last - first).days + 1
        print(f"📅 Date span: {span} days ({first.strftime('%b %d')} - {last.strftime('%b %d, %Y')})")
    except Exception as e:
        print(f"(Could not parse dates: {e})")
else:
    print("\n❌ NO HISTORICAL DATA FOUND!")

import pickle
import gspread
import json

with open('token.pickle', 'rb') as f:
    creds = pickle.load(f)

gc = gspread.authorize(creds)
sheet = gc.open_by_key('12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8').worksheet('Sheet1')

# Basic info
info = {
    'total_rows': sheet.row_count,
    'total_cols': sheet.col_count,
}

# Get first 40 rows to see structure
data = sheet.get('A1:L40')

structure = []
for i, row in enumerate(data, 1):
    if row and any(cell for cell in row):
        structure.append({
            'row': i,
            'first_cell': row[0][:60] if row[0] else '',
            'num_filled': len([c for c in row if c])
        })

info['structure'] = structure

# Save to file
with open('sheet_structure.json', 'w') as f:
    json.dump(info, f, indent=2)

print("✅ Structure saved to sheet_structure.json")
print(f"Total rows: {info['total_rows']}")
print(f"Total cols: {info['total_cols']}")
print(f"Rows with data: {len(structure)}")

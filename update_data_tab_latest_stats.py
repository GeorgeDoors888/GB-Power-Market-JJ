#!/usr/bin/env python3
"""
Update DATA sheet with latest BigQuery statistics
After P114 backfill + automated downloads, dataset has grown significantly
"""

import gspread
from google.oauth2.service_account import Credentials
from google.cloud import bigquery

SPREADSHEET_ID = "1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA"
PROJECT_ID = "inner-cinema-476211-u9"
DATASET = "uk_energy_prod"

# Initialize clients
scopes = ['https://www.googleapis.com/auth/spreadsheets']
creds = Credentials.from_service_account_file('inner-cinema-credentials.json', scopes=scopes)
gc = gspread.authorize(creds)
bq_client = bigquery.Client(project=PROJECT_ID, location="US")

spreadsheet = gc.open_by_key(SPREADSHEET_ID)

print("📊 Getting latest BigQuery statistics...")

# Get comprehensive dataset stats
dataset_ref = bq_client.dataset(DATASET)
tables = list(bq_client.list_tables(dataset_ref))

total_rows = 0
total_bytes = 0
table_stats = {}

for table in tables:
    full_table = bq_client.get_table(f'{PROJECT_ID}.{DATASET}.{table.table_id}')
    rows = full_table.num_rows if full_table.num_rows else 0
    bytes_val = full_table.num_bytes if full_table.num_bytes else 0
    total_rows += rows
    total_bytes += bytes_val

    # Store for individual table lookup
    table_stats[table.table_id] = {
        'rows': rows,
        'gb': bytes_val / (1024**3)
    }

table_count = len(tables)
total_gb = total_bytes / (1024**3)

print(f"\n✅ Dataset Statistics:")
print(f"   Tables: {table_count}")
print(f"   Total Rows: {total_rows:,}")
print(f"   Total Size: {total_gb:.2f} GB")

# Update DATA sheet
try:
    worksheet = spreadsheet.worksheet('DATA')
    print(f"\n📝 Found DATA sheet, updating statistics...")
except gspread.WorksheetNotFound:
    print(f"\n❌ DATA sheet not found!")
    exit(1)

# Get current data
all_values = worksheet.get_all_values()

# Update specific cells (preserving structure)
updates = []

# Find and update key metrics
for row_idx, row in enumerate(all_values, start=1):
    if not row:
        continue

    first_cell = row[0] if row else ''

    # Update total dataset size
    if 'Total Dataset Size' in first_cell:
        updates.append({
            'range': f'B{row_idx}',
            'values': [[f'{total_gb:.1f} GB']]
        })
        updates.append({
            'range': f'C{row_idx}',
            'values': [[f'Complete uk_energy_prod dataset ({table_count} tables)']]
        })
        updates.append({
            'range': f'D{row_idx}',
            'values': [[f'BigQuery storage, {total_rows:,} total rows']]
        })
        print(f"   Row {row_idx}: Updated 'Total Dataset Size' → {total_gb:.1f} GB")

    # Update Total BMRS Tables count
    elif 'Total BMRS Tables' in first_cell:
        updates.append({
            'range': f'B{row_idx}',
            'values': [[f'{table_count}']]
        })
        print(f"   Row {row_idx}: Updated 'Total BMRS Tables' → {table_count}")

    # Update bmrs_bod statistics (largest table)
    elif 'Largest Table' in first_cell or 'bmrs_bod' in first_cell.lower():
        if 'bmrs_bod' in table_stats:
            bod_rows = table_stats['bmrs_bod']['rows']
            updates.append({
                'range': f'B{row_idx}',
                'values': [[f'{bod_rows:,} rows']]
            })
            print(f"   Row {row_idx}: Updated bmrs_bod rows → {bod_rows:,}")

    # Update TOTAL DATASET row (in tables section)
    elif 'TOTAL DATASET' in first_cell:
        updates.append({
            'range': f'B{row_idx}',
            'values': [[f'{total_rows:,} rows']]
        })
        updates.append({
            'range': f'C{row_idx}',
            'values': [[f'{total_gb:.1f} GB']]
        })
        print(f"   Row {row_idx}: Updated TOTAL DATASET → {total_rows:,} rows, {total_gb:.1f} GB")

    # Update individual table stats if they exist in the sheet
    elif first_cell.startswith('bmrs_') or first_cell.startswith('elexon_') or first_cell.startswith('neso_'):
        table_name = first_cell.split()[0]  # Get just the table name
        if table_name in table_stats:
            stats = table_stats[table_name]
            if stats['rows'] > 0:
                # Update row count (column B)
                updates.append({
                    'range': f'B{row_idx}',
                    'values': [[f"{stats['rows']:,}"]]
                })
                # Update size (column C)
                updates.append({
                    'range': f'C{row_idx}',
                    'values': [[f"{stats['gb']:.2f} GB"]]
                })
                print(f"   Row {row_idx}: Updated {table_name} → {stats['rows']:,} rows, {stats['gb']:.2f} GB")

# Apply all updates in batch
if updates:
    print(f"\n📤 Applying {len(updates)} updates to Google Sheets...")
    worksheet.batch_update(updates)
    print(f"✅ Successfully updated DATA tab!")
else:
    print(f"\n⚠️  No updates needed (or couldn't find update locations)")

# Add timestamp
import datetime
timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M')

# Find "Last Updated" row and update it
for row_idx, row in enumerate(all_values, start=1):
    if 'Last Updated' in (row[0] if row else ''):
        worksheet.update(f'A{row_idx}', f'Last Updated: {timestamp} | Project: {PROJECT_ID}.{DATASET}')
        print(f"\n🕐 Updated timestamp to {timestamp}")
        break

print(f"\n{'='*80}")
print(f"📊 SUMMARY")
print(f"{'='*80}")
print(f"Dataset: {PROJECT_ID}.{DATASET}")
print(f"Tables: {table_count}")
print(f"Total Rows: {total_rows:,}")
print(f"Total Size: {total_gb:.2f} GB")
print(f"Avg per table: {total_rows // table_count:,} rows, {total_gb / table_count:.1f} GB")
print(f"\n✅ DATA tab updated successfully!")

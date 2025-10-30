#!/usr/bin/env python3
"""
Upload NGED Charging Data to Google Sheets
Handles splitting data if file size > 10MB
Authenticates with Google Sheets API using service account
"""

import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from pathlib import Path
import time
from datetime import datetime

# Configuration
CSV_PATH = Path("/Users/georgemajor/GB Power Market JJ/nged_charging_data_parsed.csv")
SERVICE_ACCOUNT_FILE = Path("/Users/georgemajor/GB Power Market JJ/jibber_jabber_key.json")
SPREADSHEET_NAME_PREFIX = "NGED Charging Data"
MAX_ROWS_PER_SHEET = 50000  # Google Sheets limit per sheet
CHUNK_SIZE = 10000  # Upload in chunks for safety

# Google Sheets API scope
SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]

def authenticate():
    """Authenticate with Google Sheets API"""
    print("🔐 Authenticating with Google Sheets...")
    
    if not SERVICE_ACCOUNT_FILE.exists():
        raise FileNotFoundError(f"Service account key not found: {SERVICE_ACCOUNT_FILE}")
    
    creds = Credentials.from_service_account_file(
        str(SERVICE_ACCOUNT_FILE),
        scopes=SCOPES
    )
    
    client = gspread.authorize(creds)
    print("   ✅ Authentication successful")
    return client

def load_data():
    """Load parsed CSV data"""
    print(f"📂 Loading data from CSV...")
    df = pd.read_csv(CSV_PATH)
    
    # Clean up the data
    # Convert lists stored as strings back to actual lists
    if 'rates_found' in df.columns:
        df['rates_found'] = df['rates_found'].apply(lambda x: str(x) if pd.notna(x) else '')
    if 'values_found' in df.columns:
        df['values_found'] = df['values_found'].apply(lambda x: str(x) if pd.notna(x) else '')
    
    print(f"   ✅ Loaded {len(df):,} records")
    print(f"   📊 Columns: {list(df.columns)}")
    print(f"   💾 Memory: {df.memory_usage(deep=True).sum() / 1024 / 1024:.1f} MB")
    return df

def calculate_splits(df):
    """Calculate how many spreadsheets we need based on row limits"""
    total_rows = len(df)
    
    if total_rows <= MAX_ROWS_PER_SHEET:
        return [{'start': 0, 'end': total_rows, 'name': SPREADSHEET_NAME_PREFIX}]
    
    splits = []
    num_sheets = (total_rows + MAX_ROWS_PER_SHEET - 1) // MAX_ROWS_PER_SHEET
    
    for i in range(num_sheets):
        start = i * MAX_ROWS_PER_SHEET
        end = min((i + 1) * MAX_ROWS_PER_SHEET, total_rows)
        splits.append({
            'start': start,
            'end': end,
            'name': f"{SPREADSHEET_NAME_PREFIX} - Part {i+1} of {num_sheets}"
        })
    
    return splits

def create_spreadsheet(client, name, share_email=None):
    """Create a new Google Spreadsheet and optionally share it"""
    print(f"📄 Creating spreadsheet: {name}")
    
    try:
        spreadsheet = client.create(name)
        print(f"   ✅ Created: {spreadsheet.url}")
        
        # Share with user's email if provided
        if share_email:
            try:
                spreadsheet.share(share_email, perm_type='user', role='writer')
                print(f"   ✅ Shared with: {share_email}")
            except Exception as e:
                print(f"   ⚠️  Could not share: {e}")
        
        return spreadsheet
    except Exception as e:
        if "quota" in str(e).lower() or "storage" in str(e).lower():
            print(f"   ❌ Service account storage quota exceeded")
            print(f"   💡 The service account has limited storage")
            print(f"   💡 Alternative: Save to Excel and upload manually to your Drive")
            raise
        else:
            raise

def upload_data_to_sheet(worksheet, df, chunk_size=CHUNK_SIZE):
    """Upload DataFrame to worksheet in chunks"""
    print(f"   📤 Uploading {len(df):,} rows...")
    
    # Clear existing data
    worksheet.clear()
    
    # Prepare data (header + rows)
    data = [df.columns.tolist()] + df.values.tolist()
    
    # Upload in chunks
    total_rows = len(data)
    for i in range(0, total_rows, chunk_size):
        end = min(i + chunk_size, total_rows)
        chunk = data[i:end]
        
        # Calculate cell range
        start_row = i + 1
        end_row = end
        end_col = chr(65 + len(df.columns) - 1)  # A, B, C, ...
        
        cell_range = f'A{start_row}:{end_col}{end_row}'
        
        print(f"      Uploading rows {start_row:,} - {end_row:,}...")
        worksheet.update(cell_range, chunk, value_input_option='RAW')
        
        # Rate limiting
        if end < total_rows:
            time.sleep(1)
    
    print(f"   ✅ Upload complete: {len(df):,} rows")

def format_worksheet(worksheet, df):
    """Apply formatting to the worksheet"""
    print(f"   🎨 Applying formatting...")
    
    # Freeze header row
    worksheet.freeze(rows=1)
    
    # Format header row
    header_format = {
        'backgroundColor': {'red': 0.2, 'green': 0.6, 'blue': 0.8},
        'textFormat': {'bold': True, 'foregroundColor': {'red': 1, 'green': 1, 'blue': 1}},
        'horizontalAlignment': 'CENTER'
    }
    
    end_col = chr(65 + len(df.columns) - 1)
    worksheet.format(f'A1:{end_col}1', header_format)
    
    # Auto-resize columns
    worksheet.columns_auto_resize(0, len(df.columns))
    
    print(f"   ✅ Formatting applied")

def create_summary_sheet(spreadsheet, df):
    """Create a summary sheet with statistics"""
    print(f"   📊 Creating summary sheet...")
    
    # Add new sheet
    summary = spreadsheet.add_worksheet('Summary', rows=100, cols=10)
    
    # Prepare summary data
    summary_data = [
        ['NGED Charging Data Summary', ''],
        ['Generated', datetime.now().strftime('%Y-%m-%d %H:%M:%S')],
        ['', ''],
        ['Statistics', ''],
        ['Total Records', len(df)],
        ['Years Covered', f"{df['year'].min()} - {df['year'].max()}"],
        ['DNO Areas', ', '.join(df['dno_code'].unique())],
        ['Files Parsed', df['filename'].nunique()],
        ['Sheets Parsed', df['sheet'].nunique()],
        ['', ''],
        ['Records by Year', ''],
    ]
    
    # Add year breakdown
    year_counts = df['year'].value_counts().sort_index()
    for year, count in year_counts.items():
        summary_data.append([f'  {year}', count])
    
    summary_data.append(['', ''])
    summary_data.append(['Records by DNO', ''])
    
    # Add DNO breakdown
    dno_counts = df.groupby('dno_code').size().sort_values(ascending=False)
    for dno, count in dno_counts.items():
        dno_name = df[df['dno_code'] == dno]['dno_name'].iloc[0]
        summary_data.append([f'  {dno} ({dno_name})', count])
    
    # Upload summary
    summary.update('A1', summary_data, value_input_option='RAW')
    
    # Format summary
    summary.format('A1:B1', {
        'backgroundColor': {'red': 0.1, 'green': 0.4, 'blue': 0.7},
        'textFormat': {'bold': True, 'foregroundColor': {'red': 1, 'green': 1, 'blue': 1}, 'fontSize': 14},
    })
    
    summary.format('A4:A4', {
        'textFormat': {'bold': True},
    })
    
    summary.format('A11:A11', {
        'textFormat': {'bold': True},
    })
    
    # Move to first position
    summary_sheets = spreadsheet.worksheets()
    spreadsheet.reorder_worksheets([summary] + [s for s in summary_sheets if s.title != 'Summary'])
    
    print(f"   ✅ Summary sheet created")

def main():
    """Main execution"""
    print("=" * 80)
    print("NGED CHARGING DATA - GOOGLE SHEETS UPLOADER")
    print("=" * 80)
    print()
    
    # User email to share with
    USER_EMAIL = "george@upowerenergy.uk"
    print(f"📧 Will share with: {USER_EMAIL}")
    print()
    
    # Authenticate
    client = authenticate()
    print()
    
    # Load data
    df = load_data()
    print()
    
    # Calculate splits
    splits = calculate_splits(df)
    print(f"📑 Data will be split into {len(splits)} spreadsheet(s)")
    for i, split in enumerate(splits, 1):
        rows = split['end'] - split['start']
        print(f"   {i}. {split['name']}: {rows:,} rows")
    print()
    
    # Upload each split
    spreadsheet_urls = []
    
    for i, split in enumerate(splits, 1):
        print(f"[{i}/{len(splits)}] Processing: {split['name']}")
        print("-" * 80)
        
        # Extract data chunk
        df_chunk = df.iloc[split['start']:split['end']].copy()
        
        # Create spreadsheet and share with user
        spreadsheet = create_spreadsheet(client, split['name'], share_email=USER_EMAIL)
        spreadsheet_urls.append({
            'name': split['name'],
            'url': spreadsheet.url,
            'rows': len(df_chunk)
        })
        
        # Get first worksheet (Sheet1)
        worksheet = spreadsheet.sheet1
        worksheet.update_title('Charging Data')
        
        # Upload data
        upload_data_to_sheet(worksheet, df_chunk)
        
        # Format worksheet
        format_worksheet(worksheet, df_chunk)
        
        # Create summary sheet
        create_summary_sheet(spreadsheet, df_chunk)
        
        print()
    
    # Final summary
    print("=" * 80)
    print("✅ UPLOAD COMPLETE!")
    print("=" * 80)
    print()
    print(f"📊 Total records uploaded: {len(df):,}")
    print(f"📄 Spreadsheets created: {len(spreadsheet_urls)}")
    print()
    print("🔗 Spreadsheet Links:")
    for info in spreadsheet_urls:
        print(f"   • {info['name']} ({info['rows']:,} rows)")
        print(f"     {info['url']}")
        print()
    
    print("💡 Next steps:")
    print("   1. Open the spreadsheet(s) in your browser")
    print("   2. Share with your Google account if needed")
    print("   3. Review the Summary sheet for statistics")
    print("   4. Use filters and pivots to analyze the data")
    print()

if __name__ == "__main__":
    main()

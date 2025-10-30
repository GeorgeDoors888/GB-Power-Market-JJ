#!/usr/bin/env python3
"""
Parse NGED Charging Files and Extract Tariff Data
Handles all 4 NGED areas: EMEB (ID 11), MIDE (ID 14), SWAE (ID 21), SWEB (ID 22)
Extracts: tariff codes, unit rates, time bands, capacity charges, fixed charges, dates
"""

import json
import pandas as pd
import openpyxl
from pathlib import Path
from datetime import datetime
from collections import defaultdict
import re

# Configuration
JSON_PATH = Path("/Users/georgemajor/GB Power Market JJ/dno_files_by_distribution_id_and_year.json")
OUTPUT_CSV = Path("/Users/georgemajor/GB Power Market JJ/nged_charging_data_parsed.csv")
OUTPUT_JSON = Path("/Users/georgemajor/GB Power Market JJ/nged_charging_data_parsed.json")

# NGED Distribution IDs
NGED_IDS = {
    '11': {'dno_key': 'NGED-EM', 'name': 'East Midlands', 'code': 'EMEB'},
    '14': {'dno_key': 'NGED-WM', 'name': 'West Midlands', 'code': 'MIDE'},
    '21': {'dno_key': 'NGED-SWales', 'name': 'South Wales', 'code': 'SWAE'},
    '22': {'dno_key': 'NGED-SW', 'name': 'South West', 'code': 'SWEB'},
}

def load_file_list():
    """Load NGED files from JSON"""
    with open(JSON_PATH, 'r') as f:
        data = json.load(f)
    
    files = []
    for dist_id, info in NGED_IDS.items():
        if dist_id in data['files_by_distribution_id']:
            years = data['files_by_distribution_id'][dist_id].get('years', {})
            for year, year_data in years.items():
                if year.isdigit():
                    year_files = year_data.get('files', [])
                    for file_info in year_files:
                        if file_info['extension'] in ['.xlsx', '.xls']:
                            files.append({
                                'path': file_info['path'],
                                'filename': file_info['filename'],
                                'year': int(year),
                                'dist_id': dist_id,
                                'dno_key': info['dno_key'],
                                'dno_name': info['name'],
                                'dno_code': info['code']
                            })
    
    return sorted(files, key=lambda x: (x['year'], x['dist_id']))

def extract_sheet_names(workbook_path):
    """Get all sheet names from Excel file"""
    try:
        wb = openpyxl.load_workbook(workbook_path, read_only=True, data_only=True)
        sheets = wb.sheetnames
        wb.close()
        return sheets
    except Exception as e:
        print(f"  ⚠️  Error reading sheets: {e}")
        return []

def find_tariff_sheets(sheets):
    """Identify sheets likely to contain tariff data"""
    tariff_keywords = [
        'annex', 'lv', 'hv', 'ehv', 'charge', 'tariff', 'rate', 
        'domestic', 'non-domestic', 'unmetered', 'ums',
        'capacity', 'unit', 'schedule', 'table'
    ]
    
    relevant_sheets = []
    for sheet in sheets:
        sheet_lower = sheet.lower()
        if any(keyword in sheet_lower for keyword in tariff_keywords):
            relevant_sheets.append(sheet)
    
    return relevant_sheets

def parse_excel_sheet(file_path, sheet_name, file_info):
    """Parse a single sheet and extract tariff data"""
    try:
        # Read with pandas
        df = pd.read_excel(file_path, sheet_name=sheet_name, header=None)
        
        extracted_data = []
        
        # Look for patterns in the data
        for idx, row in df.iterrows():
            row_str = ' '.join([str(cell) for cell in row if pd.notna(cell)])
            row_lower = row_str.lower()
            
            # Skip empty or header-only rows
            if len(row_str.strip()) < 5:
                continue
            
            # Look for tariff codes (common patterns)
            tariff_match = re.search(r'(LV|HV|EHV|NHH|HH|DOM|UMS)[-\s]?(\w+)', row_str, re.IGNORECASE)
            
            # Look for rates (pence patterns)
            rate_match = re.findall(r'(\d+\.?\d*)\s*p', row_str)
            
            # Look for monetary values
            money_match = re.findall(r'£?\s*(\d+\.?\d*)', row_str)
            
            # If we find potential tariff data
            if tariff_match or (rate_match and len(rate_match) > 0):
                record = {
                    'year': file_info['year'],
                    'dist_id': file_info['dist_id'],
                    'dno_key': file_info['dno_key'],
                    'dno_name': file_info['dno_name'],
                    'dno_code': file_info['dno_code'],
                    'filename': file_info['filename'],
                    'sheet': sheet_name,
                    'row_index': idx,
                    'tariff_code': tariff_match.group(0) if tariff_match else None,
                    'rates_found': rate_match if rate_match else [],
                    'values_found': money_match if money_match else [],
                    'raw_text': row_str[:200],  # First 200 chars
                }
                
                # Try to identify voltage level
                voltage = None
                if 'lv' in row_lower:
                    voltage = 'LV'
                elif 'hv' in row_lower or 'high voltage' in row_lower:
                    voltage = 'HV'
                elif 'ehv' in row_lower or 'extra high' in row_lower:
                    voltage = 'EHV'
                record['voltage'] = voltage
                
                # Try to identify customer type
                customer_type = None
                if 'domestic' in row_lower:
                    customer_type = 'Domestic'
                elif 'non-domestic' in row_lower or 'commercial' in row_lower:
                    customer_type = 'Non-Domestic'
                elif 'unmetered' in row_lower or 'ums' in row_lower:
                    customer_type = 'Unmetered'
                record['customer_type'] = customer_type
                
                # Try to identify time band
                time_band = None
                if 'day' in row_lower and 'night' not in row_lower:
                    time_band = 'Day'
                elif 'night' in row_lower:
                    time_band = 'Night'
                elif 'peak' in row_lower and 'off' not in row_lower:
                    time_band = 'Peak'
                elif 'off-peak' in row_lower or 'offpeak' in row_lower:
                    time_band = 'Off-Peak'
                elif 'weekend' in row_lower:
                    time_band = 'Weekend'
                record['time_band'] = time_band
                
                extracted_data.append(record)
        
        return extracted_data
    
    except Exception as e:
        print(f"  ⚠️  Error parsing sheet '{sheet_name}': {e}")
        return []

def parse_all_files():
    """Parse all NGED charging files"""
    print("=" * 80)
    print("NGED CHARGING FILE PARSER")
    print("=" * 80)
    print()
    
    # Load files
    print("📂 Loading NGED file list...")
    files = load_file_list()
    print(f"   ✅ Found {len(files)} NGED Excel files")
    print()
    
    all_data = []
    stats = defaultdict(int)
    
    for i, file_info in enumerate(files, 1):
        print(f"[{i}/{len(files)}] Processing: {file_info['filename']}")
        print(f"   Year: {file_info['year']} | DNO: {file_info['dno_code']} ({file_info['dno_name']})")
        
        file_path = Path(file_info['path'])
        if not file_path.exists():
            print(f"   ⚠️  File not found: {file_path}")
            stats['files_missing'] += 1
            continue
        
        # Get sheet names
        sheets = extract_sheet_names(file_path)
        print(f"   📄 Sheets: {len(sheets)}")
        
        # Find relevant sheets
        relevant_sheets = find_tariff_sheets(sheets)
        print(f"   🎯 Relevant sheets: {len(relevant_sheets)}")
        
        if relevant_sheets:
            print(f"      {', '.join(relevant_sheets[:5])}{'...' if len(relevant_sheets) > 5 else ''}")
        
        # Parse relevant sheets
        for sheet in relevant_sheets[:10]:  # Limit to first 10 relevant sheets
            data = parse_excel_sheet(file_path, sheet, file_info)
            all_data.extend(data)
            if data:
                print(f"      ✓ {sheet}: {len(data)} records")
                stats['sheets_parsed'] += 1
                stats['records_extracted'] += len(data)
        
        stats['files_processed'] += 1
        print()
    
    print("=" * 80)
    print("PARSING COMPLETE")
    print("=" * 80)
    print()
    print(f"📊 Statistics:")
    print(f"   Files processed: {stats['files_processed']}")
    print(f"   Sheets parsed: {stats['sheets_parsed']}")
    print(f"   Records extracted: {stats['records_extracted']}")
    print()
    
    return all_data, stats

def save_results(data):
    """Save parsed data to CSV and JSON"""
    print("💾 Saving results...")
    
    # Convert to DataFrame
    df = pd.DataFrame(data)
    
    # Save to CSV
    df.to_csv(OUTPUT_CSV, index=False)
    print(f"   ✅ CSV saved: {OUTPUT_CSV}")
    print(f"   📄 Size: {OUTPUT_CSV.stat().st_size / 1024:.1f} KB")
    print(f"   📊 Records: {len(df):,}")
    
    # Save to JSON
    with open(OUTPUT_JSON, 'w') as f:
        json.dump(data, f, indent=2, default=str)
    print(f"   ✅ JSON saved: {OUTPUT_JSON}")
    print(f"   📄 Size: {OUTPUT_JSON.stat().st_size / 1024:.1f} KB")
    print()
    
    # Show summary
    print("📈 Data Summary:")
    print(f"   Years: {df['year'].min()} - {df['year'].max()}")
    print(f"   DNOs: {df['dno_code'].nunique()} ({', '.join(df['dno_code'].unique())})")
    print(f"   Files: {df['filename'].nunique()}")
    print(f"   Sheets: {df['sheet'].nunique()}")
    
    if 'voltage' in df.columns:
        voltage_counts = df['voltage'].value_counts()
        print(f"   Voltage levels: {dict(voltage_counts)}")
    
    if 'customer_type' in df.columns:
        customer_counts = df['customer_type'].value_counts()
        print(f"   Customer types: {dict(customer_counts)}")
    
    print()
    
    return df

def main():
    """Main execution"""
    # Parse files
    data, stats = parse_all_files()
    
    if not data:
        print("⚠️  No data extracted!")
        return
    
    # Save results
    df = save_results(data)
    
    print("=" * 80)
    print("✅ PARSING COMPLETE!")
    print("=" * 80)
    print()
    print(f"Next steps:")
    print(f"1. Review CSV: {OUTPUT_CSV}")
    print(f"2. Upload to Google Sheets with: python3 upload_to_google_sheets.py")
    print()

if __name__ == "__main__":
    main()

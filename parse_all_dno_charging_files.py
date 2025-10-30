#!/usr/bin/env python3
"""
Parse ALL DNO Charging Files (All 14 DNOs)
Comprehensive extraction of tariff data from all 323 charging files
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
OUTPUT_CSV = Path("/Users/georgemajor/GB Power Market JJ/all_dno_charging_data_parsed.csv")
OUTPUT_JSON = Path("/Users/georgemajor/GB Power Market JJ/all_dno_charging_data_parsed.json")

# All 14 DNO Distribution IDs
ALL_DNOS = ['10', '11', '12', '13', '14', '15', '16', '17', '18', '19', '20', '21', '22', '23']

def load_file_list():
    """Load ALL DNO files from JSON"""
    with open(JSON_PATH, 'r') as f:
        data = json.load(f)
    
    files = []
    for dist_id in ALL_DNOS:
        if dist_id in data['files_by_distribution_id']:
            dno_info = data['files_by_distribution_id'][dist_id]['dno_info']
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
                                'dno_key': dno_info['dno_key'],
                                'dno_name': dno_info['name'],
                                'dno_code': dno_info['short_code']
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
        return []

def find_tariff_sheets(sheets):
    """Identify sheets likely to contain tariff data"""
    tariff_keywords = [
        'annex', 'lv', 'hv', 'ehv', 'charge', 'tariff', 'rate', 
        'domestic', 'non-domestic', 'unmetered', 'ums',
        'capacity', 'unit', 'schedule', 'table', 'pricing'
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
        df = pd.read_excel(file_path, sheet_name=sheet_name, header=None)
        extracted_data = []
        
        for idx, row in df.iterrows():
            row_str = ' '.join([str(cell) for cell in row if pd.notna(cell)])
            row_lower = row_str.lower()
            
            if len(row_str.strip()) < 5:
                continue
            
            # Look for tariff codes
            tariff_match = re.search(r'(LV|HV|EHV|NHH|HH|DOM|UMS)[-\s]?(\w+)', row_str, re.IGNORECASE)
            
            # Look for rates
            rate_match = re.findall(r'(\d+\.?\d*)\s*p', row_str)
            money_match = re.findall(r'£?\s*(\d+\.?\d*)', row_str)
            
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
                    'raw_text': row_str[:200],
                }
                
                # Voltage level
                voltage = None
                if 'lv' in row_lower or 'low voltage' in row_lower:
                    voltage = 'LV'
                elif 'hv' in row_lower or 'high voltage' in row_lower:
                    voltage = 'HV'
                elif 'ehv' in row_lower or 'extra high' in row_lower:
                    voltage = 'EHV'
                elif '132' in row_str or '132kv' in row_lower:
                    voltage = '132kV'
                record['voltage'] = voltage
                
                # Customer type
                customer_type = None
                if 'domestic' in row_lower:
                    customer_type = 'Domestic'
                elif 'non-domestic' in row_lower or 'commercial' in row_lower:
                    customer_type = 'Non-Domestic'
                elif 'unmetered' in row_lower or 'ums' in row_lower:
                    customer_type = 'Unmetered'
                elif 'industrial' in row_lower:
                    customer_type = 'Industrial'
                record['customer_type'] = customer_type
                
                # Time band
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
        return []

def parse_all_files():
    """Parse all DNO charging files"""
    print("=" * 80)
    print("ALL DNO CHARGING FILE PARSER (14 DNOs)")
    print("=" * 80)
    print()
    
    print("📂 Loading file list for all 14 DNOs...")
    files = load_file_list()
    print(f"   ✅ Found {len(files)} Excel files across all DNOs")
    print()
    
    # Show DNO breakdown
    dno_counts = defaultdict(int)
    for f in files:
        dno_counts[f['dno_code']] += 1
    
    print("📊 Files by DNO:")
    for dno, count in sorted(dno_counts.items()):
        print(f"   {dno}: {count} files")
    print()
    
    all_data = []
    stats = defaultdict(int)
    
    for i, file_info in enumerate(files, 1):
        print(f"[{i}/{len(files)}] {file_info['dno_code']} {file_info['year']}: {file_info['filename'][:50]}...")
        
        file_path = Path(file_info['path'])
        if not file_path.exists():
            stats['files_missing'] += 1
            continue
        
        sheets = extract_sheet_names(file_path)
        relevant_sheets = find_tariff_sheets(sheets)
        
        if not relevant_sheets:
            stats['files_no_relevant_sheets'] += 1
            continue
        
        # Parse relevant sheets (limit to 10 per file)
        sheet_records = 0
        for sheet in relevant_sheets[:10]:
            data = parse_excel_sheet(file_path, sheet, file_info)
            all_data.extend(data)
            sheet_records += len(data)
        
        if sheet_records > 0:
            print(f"   ✅ {sheet_records} records from {len(relevant_sheets[:10])} sheets")
            stats['files_with_data'] += 1
        
        stats['files_processed'] += 1
        
        # Progress indicator
        if (i % 20) == 0:
            print(f"   📊 Progress: {i}/{len(files)} files, {len(all_data):,} records so far")
            print()
    
    print()
    print("=" * 80)
    print("PARSING COMPLETE")
    print("=" * 80)
    print()
    print(f"📊 Statistics:")
    print(f"   Files processed: {stats['files_processed']}")
    print(f"   Files with data: {stats['files_with_data']}")
    print(f"   Files missing: {stats['files_missing']}")
    print(f"   Files without relevant sheets: {stats['files_no_relevant_sheets']}")
    print(f"   Total records extracted: {len(all_data):,}")
    print()
    
    return all_data, stats

def save_results(data):
    """Save parsed data to CSV and JSON"""
    print("💾 Saving results...")
    
    df = pd.DataFrame(data)
    
    # Save to CSV
    df.to_csv(OUTPUT_CSV, index=False)
    print(f"   ✅ CSV saved: {OUTPUT_CSV}")
    print(f"   📄 Size: {OUTPUT_CSV.stat().st_size / 1024 / 1024:.1f} MB")
    print(f"   📊 Records: {len(df):,}")
    
    # Save to JSON
    with open(OUTPUT_JSON, 'w') as f:
        json.dump(data, f, indent=2, default=str)
    print(f"   ✅ JSON saved: {OUTPUT_JSON}")
    print(f"   📄 Size: {OUTPUT_JSON.stat().st_size / 1024 / 1024:.1f} MB")
    print()
    
    # Summary
    print("📈 Data Summary:")
    print(f"   Years: {df['year'].min()} - {df['year'].max()}")
    print(f"   DNOs: {df['dno_code'].nunique()} - {', '.join(sorted(df['dno_code'].unique()))}")
    print(f"   Files: {df['filename'].nunique()}")
    
    print()
    print("📊 Records by DNO:")
    dno_counts = df['dno_code'].value_counts().sort_index()
    for dno, count in dno_counts.items():
        print(f"   {dno}: {count:,} records")
    
    print()
    print("📊 Records by Year:")
    year_counts = df['year'].value_counts().sort_index()
    for year, count in year_counts.items():
        print(f"   {year}: {count:,} records")
    
    print()
    
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
    data, stats = parse_all_files()
    
    if not data:
        print("⚠️  No data extracted!")
        return
    
    df = save_results(data)
    
    print("=" * 80)
    print("✅ ALL DNO PARSING COMPLETE!")
    print("=" * 80)
    print()
    print(f"Next steps:")
    print(f"1. Review CSV: {OUTPUT_CSV}")
    print(f"2. Export to Excel: python3 export_all_dno_to_excel.py")
    print(f"3. Upload to your Google Drive (7TB available)")
    print()

if __name__ == "__main__":
    main()

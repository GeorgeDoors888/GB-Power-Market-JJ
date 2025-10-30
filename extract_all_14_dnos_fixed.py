#!/usr/bin/env python3
"""
Extract comprehensive tariff data from ALL 14 UK DNOs
Uses position-based extraction (reliable across different file formats)
"""

import pandas as pd
import re
from pathlib import Path
import glob
from typing import List, Dict

# DNO Mappings
DNO_MAP = {
    'EMEB': {'code': 'EMID', 'name': 'East Midlands'},
    'MIDE': {'code': 'WMID', 'name': 'West Midlands'},
    'SWAE': {'code': 'SWAE', 'name': 'South Wales'},
    'SWEB': {'code': 'SWEB', 'name': 'South West'},
    'london': {'code': 'LPN', 'name': 'London'},
    'eastern': {'code': 'EPN', 'name': 'Eastern'},
    'south-eastern': {'code': 'SPN', 'name': 'South Eastern'},
    'Northeast': {'code': 'NEPN', 'name': 'Northern Powergrid Northeast'},
    'Yorkshire': {'code': 'YPED', 'name': 'Northern Powergrid Yorkshire'},
    'enwl': {'code': 'ENWL', 'name': 'Electricity North West'},
    'SPD': {'code': 'SPD', 'name': 'SP Distribution'},
    'SPM': {'code': 'SPM', 'name': 'SP Manweb'},
    'shepd': {'code': 'SHEPD', 'name': 'Scottish Hydro'},
    'sepd': {'code': 'SEPD', 'name': 'Southern Electric'},
}


def extract_doc_reference(filename: str) -> str:
    """Extract version and year from filename"""
    version_match = re.search(r'[Vv]\.?(\d+\.?\d*)', filename)
    version = f"v{version_match.group(1)}" if version_match else ""
    
    year_match = re.search(r'20(2[0-6])', filename)
    year = f"20{year_match.group(1)}" if year_match else ""
    
    return f"{year} {version}".strip()


def identify_dno(filename: str) -> tuple:
    """Identify DNO from filename"""
    filename_lower = filename.lower()
    
    for key, info in DNO_MAP.items():
        if key.lower() in filename_lower:
            return info['code'], info['name']
    
    return 'UNKNOWN', 'Unknown DNO'


def extract_tariffs(file_path: str) -> List[Dict]:
    """Extract tariffs from any DNO file using position-based approach"""
    file_name = Path(file_path).name
    dno_code, dno_name = identify_dno(file_name)
    doc_ref = extract_doc_reference(file_name)
    results = []
    
    try:
        # Try to find the correct sheet
        excel_file = pd.ExcelFile(file_path)
        
        # Priority sheet names
        target_sheets = [
            "Annex 1 LV, HV and UMS charges",
            "Annex 1",
            "LV charges",
            "Schedule of charges",
            "Tariff table",
        ]
        
        sheet_name = None
        for target in target_sheets:
            if target in excel_file.sheet_names:
                sheet_name = target
                break
        
        # Fall back to first sheet with "annex" or "charges"
        if not sheet_name:
            for sn in excel_file.sheet_names:
                if any(word in sn.lower() for word in ['annex', 'charges', 'tariff', 'schedule']):
                    sheet_name = sn
                    break
        
        if not sheet_name:
            return []
        
        df = pd.read_excel(file_path, sheet_name=sheet_name)
        
        # Find header row
        header_row = None
        for idx, row in df.iterrows():
            row_str = ' '.join([str(x) for x in row if pd.notna(x)])
            if any(term in row_str for term in ['Tariff name', 'LLFCs', 'Tariff description']):
                header_row = idx
                break
        
        if header_row is None:
            return []
        
        # Set proper column names
        headers = df.iloc[header_row].tolist()
        data_df = df.iloc[header_row+1:].copy()
        data_df.columns = headers
        
        # Extract tariff rows
        for idx, row in data_df.iterrows():
            tariff_name = str(row.iloc[0]) if pd.notna(row.iloc[0]) else ""
            
            if not tariff_name or tariff_name in ['nan', '', 'NaN']:
                continue
            
            # Skip header-like rows
            if any(x in tariff_name.lower() for x in ['tariff name', 'unit rate', 'closed']):
                continue
            
            # Get LLFCs and PCs (columns 1 and 2)
            llfcs = str(row.iloc[1]) if len(row) > 1 and pd.notna(row.iloc[1]) else ""
            pcs = str(row.iloc[2]) if len(row) > 2 and pd.notna(row.iloc[2]) else ""
            
            # Get rates (usually columns 3, 4, 5)
            red_rate = float(row.iloc[3]) if len(row) > 3 and pd.notna(row.iloc[3]) and isinstance(row.iloc[3], (int, float)) else None
            amber_rate = float(row.iloc[4]) if len(row) > 4 and pd.notna(row.iloc[4]) and isinstance(row.iloc[4], (int, float)) else None
            green_rate = float(row.iloc[5]) if len(row) > 5 and pd.notna(row.iloc[5]) and isinstance(row.iloc[5], (int, float)) else None
            
            # Get fixed charge and capacity charge (columns 6, 7)
            fixed_charge = float(row.iloc[6]) if len(row) > 6 and pd.notna(row.iloc[6]) and isinstance(row.iloc[6], (int, float)) else None
            capacity_charge = float(row.iloc[7]) if len(row) > 7 and pd.notna(row.iloc[7]) and isinstance(row.iloc[7], (int, float)) else None
            
            # Only include rows with at least one rate
            if red_rate is not None or amber_rate is not None or green_rate is not None:
                # Extract year from doc_ref
                year_match = re.search(r'(20\d{2})', doc_ref)
                year = year_match.group(1) if year_match else ""
                
                results.append({
                    'Year': year,
                    'DNO_Code': dno_code,
                    'DNO_Name': dno_name,
                    'Tariff_Name': tariff_name,
                    'LLFCs': llfcs,
                    'PCs': pcs,
                    'Red_Rate_p_kWh': red_rate,
                    'Amber_Rate_p_kWh': amber_rate,
                    'Green_Rate_p_kWh': green_rate,
                    'Fixed_Charge_p_day': fixed_charge,
                    'Capacity_Charge_p_kVA_day': capacity_charge,
                    'Document': file_name,
                    'Document_Reference': doc_ref,
                })
    
    except Exception as e:
        print(f"      ⚠️  Error: {e}")
    
    return results


def main():
    """Main extraction function"""
    print("\n" + "="*100)
    print("📊 COMPREHENSIVE DNO TARIFF EXTRACTION - ALL 14 DNOs")
    print("="*100 + "\n")
    
    all_results = []
    
    # 1. NGED (4 DNOs)
    print("🔍 NGED (National Grid Electricity Distribution)")
    nged_files = sorted(glob.glob("duos_nged_data/*.xlsx"))
    for file_path in nged_files:
        if not Path(file_path).name.startswith('~'):
            print(f"   📂 {Path(file_path).name}")
            results = extract_tariffs(file_path)
            all_results.extend(results)
            print(f"      ✅ Extracted {len(results)} tariffs")
    
    # 2. UKPN (3 DNOs)
    print("\n🔍 UK Power Networks (London, Eastern, South Eastern)")
    for pattern in ['london-power-networks-*.xlsx', 'eastern-power-networks-*.xlsx', 'south-eastern-power-networks-*.xlsx']:
        ukpn_files = sorted(glob.glob(pattern))
        for file_path in ukpn_files:
            if not Path(file_path).name.startswith('~'):
                print(f"   📂 {Path(file_path).name}")
                results = extract_tariffs(file_path)
                all_results.extend(results)
                print(f"      ✅ Extracted {len(results)} tariffs")
    
    # 3. Northern Powergrid (2 DNOs)
    print("\n🔍 Northern Powergrid (Northeast, Yorkshire)")
    npg_files = sorted(glob.glob('Northern Powergrid*.xlsx'))
    for file_path in npg_files:
        if not Path(file_path).name.startswith('~') and 'Schedule of charges' in Path(file_path).name:
            print(f"   📂 {Path(file_path).name}")
            results = extract_tariffs(file_path)
            all_results.extend(results)
            print(f"      ✅ Extracted {len(results)} tariffs")
    
    # 4. ENWL (1 DNO)
    print("\n🔍 Electricity North West")
    enwl_files = sorted(glob.glob('enwl*.xlsx'))
    for file_path in enwl_files:
        if not Path(file_path).name.startswith('~') and 'schedule' in Path(file_path).name.lower():
            print(f"   📂 {Path(file_path).name}")
            results = extract_tariffs(file_path)
            all_results.extend(results)
            print(f"      ✅ Extracted {len(results)} tariffs")
    
    # 5. SP Energy Networks (2 DNOs)
    print("\n🔍 SP Energy Networks (SPD, SPM)")
    for pattern in ['SPD-Schedule*.xlsx', 'SPM-Schedule*.xlsx', 'SP_Distribution*.xlsx', 'SP_Manweb*.xlsx']:
        spen_files = sorted(glob.glob(pattern))
        for file_path in spen_files:
            if not Path(file_path).name.startswith('~'):
                print(f"   📂 {Path(file_path).name}")
                results = extract_tariffs(file_path)
                all_results.extend(results)
                print(f"      ✅ Extracted {len(results)} tariffs")
    
    # 6. SSE (2 DNOs)
    print("\n🔍 SSE (Scottish Hydro, Southern Electric)")
    for subdir in ['shepd', 'sepd']:
        sse_files = sorted(glob.glob(f'duos_ssen_data/{subdir}/*.xlsx'))
        for file_path in sse_files:
            if not Path(file_path).name.startswith('~') and 'schedule' in Path(file_path).name.lower():
                print(f"   📂 {Path(file_path).name}")
                results = extract_tariffs(file_path)
                all_results.extend(results)
                print(f"      ✅ Extracted {len(results)} tariffs")
    
    # Create DataFrame
    df = pd.DataFrame(all_results)
    
    # Summary
    print("\n" + "="*100)
    print("📊 EXTRACTION SUMMARY")
    print("="*100)
    print(f"\nTotal tariffs extracted: {len(df)}")
    
    if len(df) > 0:
        print(f"\nDNOs covered: {df['DNO_Name'].nunique()}")
        print(f"Years covered: {sorted(df['Year'].dropna().unique())}")
        
        print("\n📊 Tariff counts by DNO:")
        dno_counts = df.groupby('DNO_Name').size().reset_index(name='Count')
        print(dno_counts.to_string(index=False))
        
        # Save to CSV
        output_csv = 'all_14_dnos_comprehensive_tariffs.csv'
        df.to_csv(output_csv, index=False)
        print(f"\n✅ Saved to: {output_csv}")
        
        # Save to Excel with sheets
        output_xlsx = 'all_14_dnos_comprehensive_tariffs.xlsx'
        with pd.ExcelWriter(output_xlsx, engine='openpyxl') as writer:
            # All tariffs
            df.to_excel(writer, sheet_name='All Tariffs', index=False)
            
            # By year
            for year in sorted(df['Year'].dropna().unique()):
                if year:
                    year_df = df[df['Year'] == year]
                    sheet_name = f'Year {year}'
                    year_df.to_excel(writer, sheet_name=sheet_name, index=False)
            
            # By DNO
            for dno in sorted(df['DNO_Name'].unique()):
                dno_df = df[df['DNO_Name'] == dno]
                sheet_name = dno[:31]  # Excel sheet name limit
                dno_df.to_excel(writer, sheet_name=sheet_name, index=False)
        
        print(f"✅ Saved to: {output_xlsx}")
        
        # Show sample
        print("\n📋 SAMPLE: Non-Domestic Tariffs")
        sample = df[df['Tariff_Name'].str.contains('Non-Domestic', case=False, na=False)]
        if len(sample) > 0:
            print(f"\nFound {len(sample)} Non-Domestic tariffs")
            for idx, row in sample.head(5).iterrows():
                print(f"\n{row['DNO_Name']} ({row['Year']}): {row['Tariff_Name']}")
                print(f"  LLFCs: {row['LLFCs']} | PCs: {row['PCs']}")
                print(f"  Red: {row['Red_Rate_p_kWh']} | Amber: {row['Amber_Rate_p_kWh']} | Green: {row['Green_Rate_p_kWh']}")
    
    print("\n" + "="*100)
    print("✅ EXTRACTION COMPLETE!")
    print("="*100 + "\n")


if __name__ == "__main__":
    main()

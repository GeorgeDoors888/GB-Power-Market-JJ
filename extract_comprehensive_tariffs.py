#!/usr/bin/env python3
"""
Comprehensive DNO Tariff Extraction with Full Documentation
Extracts all tariffs with source references, LLFCs, PCs, and rates
"""

import pandas as pd
import glob
from pathlib import Path
import re

def extract_document_reference(filename):
    """Extract document reference/version from filename"""
    # Extract version number if present
    version_match = re.search(r'[Vv]\.?(\d+\.?\d*)', filename)
    version = f"v{version_match.group(1)}" if version_match else ""
    
    # Extract year
    year_match = re.search(r'20\d{2}', filename)
    year = year_match.group(0) if year_match else ""
    
    return f"{year} {version}".strip()

def extract_nged_tariffs(file_path):
    """Extract tariffs from NGED files"""
    file_name = Path(file_path).name
    doc_ref = extract_document_reference(file_name)
    
    # Determine DNO from filename
    if 'EMEB' in file_name or 'East' in file_name:
        dno_name = "East Midlands"
        dno_code = "EMID"
    elif 'MIDE' in file_name or 'Midlands' in file_name:
        dno_name = "West Midlands"
        dno_code = "WMID"
    elif 'SWEB' in file_name:
        dno_name = "South West"
        dno_code = "SWEST"
    elif 'SWAE' in file_name:
        dno_name = "South Wales"
        dno_code = "SWALES"
    else:
        return []
    
    results = []
    
    try:
        df = pd.read_excel(file_path, sheet_name="Annex 1 LV, HV and UMS charges")
        
        # Find header row (contains "Tariff name" or similar)
        header_row = None
        for idx, row in df.iterrows():
            row_str = ' '.join([str(x) for x in row if pd.notna(x)])
            if 'Tariff name' in row_str or 'LLFCs' in row_str:
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
            if any(x in tariff_name.lower() for x in ['tariff name', 'llfcs', 'unit rate', 'closed']):
                continue
            
            # Get LLFCs and PCs
            llfcs = str(row.iloc[1]) if len(row) > 1 and pd.notna(row.iloc[1]) else ""
            pcs = str(row.iloc[2]) if len(row) > 2 and pd.notna(row.iloc[2]) else ""
            
            # Get rates (usually columns 3, 4, 5)
            red_rate = float(row.iloc[3]) if len(row) > 3 and pd.notna(row.iloc[3]) and isinstance(row.iloc[3], (int, float)) else None
            amber_rate = float(row.iloc[4]) if len(row) > 4 and pd.notna(row.iloc[4]) and isinstance(row.iloc[4], (int, float)) else None
            green_rate = float(row.iloc[5]) if len(row) > 5 and pd.notna(row.iloc[5]) and isinstance(row.iloc[5], (int, float)) else None
            
            # Get fixed charge and capacity charge
            fixed_charge = float(row.iloc[6]) if len(row) > 6 and pd.notna(row.iloc[6]) and isinstance(row.iloc[6], (int, float)) else None
            capacity_charge = float(row.iloc[7]) if len(row) > 7 and pd.notna(row.iloc[7]) and isinstance(row.iloc[7], (int, float)) else None
            
            # Only include rows with at least one rate
            if red_rate is not None or amber_rate is not None or green_rate is not None:
                results.append({
                    'DNO_Name': dno_name,
                    'DNO_Code': dno_code,
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
                    'Source_Sheet': "Annex 1 LV, HV and UMS charges"
                })
    
    except Exception as e:
        print(f"   ⚠️  Error processing {file_name}: {e}")
    
    return results

def main():
    print("=" * 100)
    print("📊 COMPREHENSIVE DNO TARIFF EXTRACTION")
    print("=" * 100)
    print()
    
    all_results = []
    
    # Process NGED files
    print("🔍 Processing NGED files...")
    nged_files = sorted(glob.glob("duos_nged_data/*.xlsx"))
    
    for file_path in nged_files:
        file_name = Path(file_path).name
        print(f"   📂 {file_name}")
        
        results = extract_nged_tariffs(file_path)
        all_results.extend(results)
        print(f"      ✅ Extracted {len(results)} tariffs")
    
    print(f"\n✅ Total extracted: {len(all_results)} tariffs\n")
    
    # Convert to DataFrame
    df = pd.DataFrame(all_results)
    
    # Save to CSV
    output_csv = "comprehensive_dno_tariffs_with_references.csv"
    df.to_csv(output_csv, index=False)
    print(f"💾 Saved to: {output_csv}")
    
    # Save to Excel with formatting
    output_excel = "comprehensive_dno_tariffs_with_references.xlsx"
    with pd.ExcelWriter(output_excel, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='All Tariffs', index=False)
        
        # Also create separate sheets by year
        df['Year'] = df['Document_Reference'].str.extract(r'(20\d{2})')
        for year in sorted(df['Year'].dropna().unique()):
            year_df = df[df['Year'] == year]
            year_df.to_excel(writer, sheet_name=f'Year_{year}', index=False)
    
    print(f"💾 Saved to: {output_excel}")
    
    # Display sample
    print("\n" + "=" * 100)
    print("📋 SAMPLE TARIFFS")
    print("=" * 100)
    print()
    
    # Show Non-Domestic Aggregated tariffs
    agg_tariffs = df[df['Tariff_Name'].str.contains('Non-Domestic Aggregated', case=False, na=False)]
    
    if len(agg_tariffs) > 0:
        print(f"Found {len(agg_tariffs)} 'Non-Domestic Aggregated' tariffs:\n")
        for idx, row in agg_tariffs.head(10).iterrows():
            print(f"DNO: {row['DNO_Name']} ({row['DNO_Code']})")
            print(f"Tariff: {row['Tariff_Name']}")
            print(f"LLFCs: {row['LLFCs']}")
            print(f"PCs: {row['PCs']}")
            print(f"Red: {row['Red_Rate_p_kWh']} p/kWh | Amber: {row['Amber_Rate_p_kWh']} p/kWh | Green: {row['Green_Rate_p_kWh']} p/kWh")
            print(f"Fixed: {row['Fixed_Charge_p_day']} p/day | Capacity: {row['Capacity_Charge_p_kVA_day']} p/kVA/day")
            print(f"Document: {row['Document']}")
            print(f"Reference: {row['Document_Reference']}")
            print()
    
    print("✅ EXTRACTION COMPLETE!")

if __name__ == "__main__":
    main()

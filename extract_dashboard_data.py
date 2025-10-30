#!/usr/bin/env python3
"""
Extract Red/Amber/Green Traffic Light Tariffs and TNUoS/BSUoS Charges
Creates comprehensive dashboard data for Google Sheets
"""

import pandas as pd
import json
from pathlib import Path
from datetime import datetime

# Configuration
CSV_PATH = Path("/Users/georgemajor/GB Power Market JJ/all_dno_charging_data_parsed.csv")
OUTPUT_DIR = Path("/Users/georgemajor/GB Power Market JJ/dashboard_data")

def load_data():
    """Load the parsed CSV data"""
    print("📂 Loading ALL DNO charging data...")
    df = pd.read_csv(CSV_PATH)
    print(f"   ✅ Loaded {len(df):,} records")
    return df

def extract_traffic_light_tariffs(df):
    """Extract red/amber/green tariff information"""
    print("\n🚦 Extracting Red/Amber/Green Traffic Light Tariffs...")
    
    # Search for traffic light indicators
    red_mask = df['raw_text'].astype(str).str.lower().str.contains(r'red|black', na=False, regex=True)
    amber_mask = df['raw_text'].astype(str).str.lower().str.contains(r'amber|yellow', na=False, regex=True)
    green_mask = df['raw_text'].astype(str).str.lower().str.contains(r'green', na=False, regex=True)
    
    # Combine and extract
    traffic_light_mask = red_mask | amber_mask | green_mask
    traffic_light_df = df[traffic_light_mask].copy()
    
    # Determine color
    traffic_light_df['tariff_color'] = 'Unknown'
    traffic_light_df.loc[red_mask[traffic_light_mask], 'tariff_color'] = 'Red'
    traffic_light_df.loc[amber_mask[traffic_light_mask], 'tariff_color'] = 'Amber'
    traffic_light_df.loc[green_mask[traffic_light_mask], 'tariff_color'] = 'Green'
    
    print(f"   ✅ Found {len(traffic_light_df):,} traffic light tariff records")
    print(f"      Red: {(traffic_light_df['tariff_color'] == 'Red').sum():,}")
    print(f"      Amber: {(traffic_light_df['tariff_color'] == 'Amber').sum():,}")
    print(f"      Green: {(traffic_light_df['tariff_color'] == 'Green').sum():,}")
    
    return traffic_light_df

def extract_tnuos_bsuos(df):
    """Extract TNUoS and BSUoS related charges"""
    print("\n⚡ Extracting TNUoS and BSUoS Charges...")
    
    # Search terms
    tnuos_terms = ['tnuos', 'transmission', 'triad', 'national grid']
    bsuos_terms = ['bsuos', 'balancing', 'system charge']
    
    # Build search masks
    tnuos_mask = pd.Series([False] * len(df))
    bsuos_mask = pd.Series([False] * len(df))
    
    for term in tnuos_terms:
        tnuos_mask |= df['raw_text'].astype(str).str.lower().str.contains(term, na=False)
        tnuos_mask |= df['sheet'].astype(str).str.lower().str.contains(term, na=False)
    
    for term in bsuos_terms:
        bsuos_mask |= df['raw_text'].astype(str).str.lower().str.contains(term, na=False)
        bsuos_mask |= df['sheet'].astype(str).str.lower().str.contains(term, na=False)
    
    tnuos_df = df[tnuos_mask].copy()
    bsuos_df = df[bsuos_mask].copy()
    
    print(f"   ✅ Found {len(tnuos_df):,} TNUoS-related records")
    print(f"   ✅ Found {len(bsuos_df):,} BSUoS-related records")
    
    return tnuos_df, bsuos_df

def create_time_band_summary(df):
    """Create summary of time bands by DNO and year"""
    print("\n⏰ Creating Time Band Summary...")
    
    # Filter records with time band info
    time_band_df = df[df['time_band'].notna() & (df['time_band'] != '')].copy()
    
    # Create summary
    summary = time_band_df.groupby(['dno_code', 'dno_name', 'year', 'time_band']).agg({
        'tariff_code': 'count',
        'voltage': lambda x: ', '.join(x.dropna().unique()),
        'customer_type': lambda x: ', '.join(x.dropna().unique())
    }).reset_index()
    
    summary.columns = ['dno_code', 'dno_name', 'year', 'time_band', 'record_count', 'voltages', 'customer_types']
    
    print(f"   ✅ Created summary with {len(summary):,} entries")
    print(f"      Time bands found: {', '.join(summary['time_band'].unique())}")
    
    return summary

def create_dashboard_summary(df, traffic_light_df, tnuos_df, bsuos_df, time_band_summary):
    """Create comprehensive dashboard summary"""
    print("\n📊 Creating Dashboard Summary...")
    
    dashboard = {
        'metadata': {
            'generated': datetime.now().isoformat(),
            'total_records': len(df),
            'years_covered': f"{df['year'].min()}-{df['year'].max()}",
            'dnos_covered': df['dno_code'].nunique()
        },
        'traffic_light': {
            'total_records': len(traffic_light_df),
            'red_count': (traffic_light_df['tariff_color'] == 'Red').sum() if len(traffic_light_df) > 0 else 0,
            'amber_count': (traffic_light_df['tariff_color'] == 'Amber').sum() if len(traffic_light_df) > 0 else 0,
            'green_count': (traffic_light_df['tariff_color'] == 'Green').sum() if len(traffic_light_df) > 0 else 0,
        },
        'transmission_charges': {
            'tnuos_records': len(tnuos_df),
            'bsuos_records': len(bsuos_df)
        },
        'time_bands': {
            'unique_bands': time_band_summary['time_band'].nunique(),
            'bands_list': sorted(time_band_summary['time_band'].unique().tolist())
        },
        'by_dno': []
    }
    
    # Create per-DNO summary
    for dno in sorted(df['dno_code'].unique()):
        dno_data = df[df['dno_code'] == dno]
        dno_name = dno_data['dno_name'].iloc[0]
        
        dno_summary = {
            'dno_code': dno,
            'dno_name': dno_name,
            'total_records': len(dno_data),
            'years': sorted(dno_data['year'].unique().tolist()),
            'traffic_light_records': len(traffic_light_df[traffic_light_df['dno_code'] == dno]),
            'tnuos_records': len(tnuos_df[tnuos_df['dno_code'] == dno]),
            'bsuos_records': len(bsuos_df[bsuos_df['dno_code'] == dno]),
            'time_bands': sorted(time_band_summary[time_band_summary['dno_code'] == dno]['time_band'].unique().tolist())
        }
        
        dashboard['by_dno'].append(dno_summary)
    
    print(f"   ✅ Dashboard summary created")
    
    return dashboard

def main():
    """Main execution"""
    print("=" * 80)
    print("TRAFFIC LIGHT TARIFF & TRANSMISSION CHARGE EXTRACTOR")
    print("=" * 80)
    print()
    
    # Create output directory
    OUTPUT_DIR.mkdir(exist_ok=True)
    
    # Load data
    df = load_data()
    
    # Extract traffic light tariffs
    traffic_light_df = extract_traffic_light_tariffs(df)
    
    # Extract TNUoS/BSUoS
    tnuos_df, bsuos_df = extract_tnuos_bsuos(df)
    
    # Create time band summary
    time_band_summary = create_time_band_summary(df)
    
    # Create dashboard summary
    dashboard = create_dashboard_summary(df, traffic_light_df, tnuos_df, bsuos_df, time_band_summary)
    
    # Save outputs
    print("\n💾 Saving outputs...")
    
    # Save traffic light tariffs
    traffic_light_path = OUTPUT_DIR / "traffic_light_tariffs.csv"
    traffic_light_df.to_csv(traffic_light_path, index=False)
    print(f"   ✅ Saved: {traffic_light_path.name} ({len(traffic_light_df):,} records)")
    
    # Save TNUoS
    tnuos_path = OUTPUT_DIR / "tnuos_charges.csv"
    tnuos_df.to_csv(tnuos_path, index=False)
    print(f"   ✅ Saved: {tnuos_path.name} ({len(tnuos_df):,} records)")
    
    # Save BSUoS
    bsuos_path = OUTPUT_DIR / "bsuos_charges.csv"
    bsuos_df.to_csv(bsuos_path, index=False)
    print(f"   ✅ Saved: {bsuos_path.name} ({len(bsuos_df):,} records)")
    
    # Save time band summary
    time_band_path = OUTPUT_DIR / "time_band_summary.csv"
    time_band_summary.to_csv(time_band_path, index=False)
    print(f"   ✅ Saved: {time_band_path.name} ({len(time_band_summary):,} records)")
    
    # Save dashboard JSON (convert numpy types to Python types)
    dashboard_path = OUTPUT_DIR / "dashboard_summary.json"
    # Convert numpy int64 to int
    def convert_types(obj):
        if isinstance(obj, dict):
            return {k: convert_types(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [convert_types(item) for item in obj]
        elif hasattr(obj, 'item'):  # numpy types
            return obj.item()
        return obj
    
    dashboard_clean = convert_types(dashboard)
    with open(dashboard_path, 'w') as f:
        json.dump(dashboard_clean, f, indent=2)
    print(f"   ✅ Saved: {dashboard_path.name}")
    
    # Create Excel workbook with all sheets
    print("\n📊 Creating comprehensive Excel workbook...")
    excel_path = OUTPUT_DIR / "Dashboard_Data_All_Sheets.xlsx"
    
    with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
        # Dashboard summary sheet
        dashboard_df = pd.DataFrame([
            ['Dashboard Summary', ''],
            ['Generated', dashboard['metadata']['generated']],
            ['Total Records', dashboard['metadata']['total_records']],
            ['Years Covered', dashboard['metadata']['years_covered']],
            ['DNOs Covered', dashboard['metadata']['dnos_covered']],
            ['', ''],
            ['Traffic Light Tariffs', ''],
            ['Total Traffic Light Records', dashboard['traffic_light']['total_records']],
            ['Red Tariffs', dashboard['traffic_light']['red_count']],
            ['Amber Tariffs', dashboard['traffic_light']['amber_count']],
            ['Green Tariffs', dashboard['traffic_light']['green_count']],
            ['', ''],
            ['Transmission Charges', ''],
            ['TNUoS Records', dashboard['transmission_charges']['tnuos_records']],
            ['BSUoS Records', dashboard['transmission_charges']['bsuos_records']],
            ['', ''],
            ['Time Bands', ''],
            ['Unique Time Bands', dashboard['time_bands']['unique_bands']],
            ['Time Bands List', ', '.join(dashboard['time_bands']['bands_list'])],
        ])
        dashboard_df.to_excel(writer, sheet_name='Summary', index=False, header=False)
        
        # Traffic light tariffs
        traffic_light_df.to_excel(writer, sheet_name='Traffic Light Tariffs', index=False)
        
        # TNUoS charges
        tnuos_df.to_excel(writer, sheet_name='TNUoS Charges', index=False)
        
        # BSUoS charges
        bsuos_df.to_excel(writer, sheet_name='BSUoS Charges', index=False)
        
        # Time band summary
        time_band_summary.to_excel(writer, sheet_name='Time Band Summary', index=False)
        
        # Per-DNO summaries
        dno_summary_df = pd.DataFrame(dashboard['by_dno'])
        dno_summary_df.to_excel(writer, sheet_name='DNO Summary', index=False)
    
    print(f"   ✅ Saved: {excel_path.name}")
    
    print()
    print("=" * 80)
    print("✅ EXTRACTION COMPLETE!")
    print("=" * 80)
    print()
    print(f"📁 Output directory: {OUTPUT_DIR}")
    print()
    print("📊 Files created:")
    print(f"   1. traffic_light_tariffs.csv ({len(traffic_light_df):,} records)")
    print(f"   2. tnuos_charges.csv ({len(tnuos_df):,} records)")
    print(f"   3. bsuos_charges.csv ({len(bsuos_df):,} records)")
    print(f"   4. time_band_summary.csv ({len(time_band_summary):,} records)")
    print(f"   5. dashboard_summary.json")
    print(f"   6. Dashboard_Data_All_Sheets.xlsx (6 sheets)")
    print()
    print("🚀 Next: Upload Dashboard_Data_All_Sheets.xlsx to Google Sheets")
    print()

if __name__ == "__main__":
    main()

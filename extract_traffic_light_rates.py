#!/usr/bin/env python3
"""
Extract Red/Amber/Green Traffic Light Tariff Rates from DNO Data
Creates a clean summary showing actual rates and time bands for each DNO
"""

import pandas as pd
import re
from pathlib import Path

def extract_rates_from_text(text):
    """Extract numeric rates from text"""
    if pd.isna(text):
        return []
    
    # Find all decimal numbers
    numbers = re.findall(r'\d+\.\d+', str(text))
    return [float(n) for n in numbers]

def extract_time_bands(text):
    """Extract time band descriptions"""
    if pd.isna(text):
        return ""
    
    text = str(text).lower()
    
    # Common patterns
    if '16:00' in text and '19:00' in text:
        return "16:00-19:00 Weekdays"
    elif '07:30' in text or '07:00' in text:
        return "07:00-16:00 & 19:00-23:00 Weekdays"
    elif '00:00' in text and '24:00' in text:
        return "00:00-07:00 & 23:00-24:00 Weekdays; All Weekend"
    
    return ""

def main():
    print("🚦 EXTRACTING TRAFFIC LIGHT TARIFF RATES\n")
    print("=" * 80)
    
    # Load parsed data
    csv_file = "all_dno_charging_data_parsed.csv"
    print(f"📂 Loading: {csv_file}")
    
    df = pd.read_csv(csv_file)
    print(f"✅ Loaded {len(df):,} records")
    
    # Filter for recent years with traffic light data
    print("\n🔍 Filtering for traffic light tariffs...")
    
    # Search for red/amber/green in raw_text
    traffic_light = df[
        df['raw_text'].str.contains(
            r'red|amber|green|16:00.*19:00', 
            case=False, 
            na=False, 
            regex=True
        )
    ].copy()
    
    # Also look for specific rate patterns (3 rates = red/amber/green)
    rate_pattern = df[
        (df['rates_found'].notna()) & 
        (df['rates_found'].str.contains(r"'1'.*'2'.*'3'", na=False))
    ].copy()
    
    combined = pd.concat([traffic_light, rate_pattern]).drop_duplicates()
    
    print(f"✅ Found {len(combined):,} potential traffic light records")
    
    # Focus on most recent years
    recent = combined[combined['year'] >= 2024].copy()
    print(f"✅ Filtered to {len(recent):,} records from 2024+")
    
    # Extract rates for each DNO
    print("\n📊 Extracting rates by DNO...\n")
    
    results = []
    
    for (year, dno_code, dno_name), group in recent.groupby(['year', 'dno_code', 'dno_name']):
        if pd.isna(dno_code) or dno_code == '':
            continue
        
        # Look for rows with 3 rates (red, amber, green)
        for idx, row in group.iterrows():
            raw_text = str(row['raw_text'])
            
            # Try to find explicit red/amber/green rates
            red_match = re.search(r'red[^\d]*([\d.]+)', raw_text, re.IGNORECASE)
            amber_match = re.search(r'amber[^\d]*([\d.]+)', raw_text, re.IGNORECASE)
            green_match = re.search(r'green[^\d]*([\d.]+)', raw_text, re.IGNORECASE)
            
            # Or look for unit rate 1, 2, 3 pattern
            rates = extract_rates_from_text(row['values_found'])
            
            if (red_match and amber_match and green_match):
                red_rate = float(red_match.group(1))
                amber_rate = float(amber_match.group(1))
                green_rate = float(green_match.group(1))
                
                results.append({
                    'Year': year,
                    'DNO_Code': dno_code,
                    'DNO_Name': dno_name,
                    'Red_Rate_p_per_kWh': red_rate,
                    'Amber_Rate_p_per_kWh': amber_rate,
                    'Green_Rate_p_per_kWh': green_rate,
                    'Red_Time': "16:00-19:00 Weekdays",
                    'Amber_Time': "07:00-16:00 & 19:00-23:00 Weekdays",
                    'Green_Time': "00:00-07:00 & 23:00-24:00 Weekdays; All Weekend",
                    'Source_Sheet': row['sheet'],
                    'Tariff_Code': row['tariff_code']
                })
                break  # Found rates for this DNO
            
            elif len(rates) >= 3:
                # Assume first 3 rates are red, amber, green
                results.append({
                    'Year': year,
                    'DNO_Code': dno_code,
                    'DNO_Name': dno_name,
                    'Red_Rate_p_per_kWh': rates[0],
                    'Amber_Rate_p_per_kWh': rates[1],
                    'Green_Rate_p_per_kWh': rates[2],
                    'Red_Time': "16:00-19:00 Weekdays",
                    'Amber_Time': "07:00-16:00 & 19:00-23:00 Weekdays",
                    'Green_Time': "00:00-07:00 & 23:00-24:00 Weekdays; All Weekend",
                    'Source_Sheet': row['sheet'],
                    'Tariff_Code': row['tariff_code']
                })
                break
    
    # Convert to DataFrame
    results_df = pd.DataFrame(results)
    
    if len(results_df) == 0:
        print("❌ No traffic light rates found!")
        print("\n💡 Trying alternative approach with DUoS outputs...")
        
        # Check if we have DUoS outputs
        duos_dir = Path("duos_outputs2/gsheets_csv/by_year")
        if duos_dir.exists():
            print(f"\n📂 Found DUoS outputs directory: {duos_dir}")
            
            # Load 2025 and 2026 data
            for year_file in duos_dir.glob("Year_*.csv"):
                print(f"   Reading: {year_file.name}")
                duos_df = pd.read_csv(year_file)
                
                if 'color' in duos_df.columns:
                    print(f"   ✅ Found color column with {len(duos_df)} records")
                    print(f"   Colors: {duos_df['color'].unique()}")
        
        return
    
    # Sort by year and DNO
    results_df = results_df.sort_values(['Year', 'DNO_Name'])
    
    print(f"✅ Extracted rates for {len(results_df)} DNO/year combinations\n")
    
    # Display summary
    print("=" * 80)
    print("📊 TRAFFIC LIGHT TARIFF RATES SUMMARY")
    print("=" * 80)
    print()
    
    for idx, row in results_df.iterrows():
        print(f"Region: {row['DNO_Name']}")
        print(f"DNO ID: {row['DNO_Code']}")
        print(f"Year: {row['Year']}")
        print(f"  Red Band:   {row['Red_Rate_p_per_kWh']:.2f} p/kWh  ({row['Red_Time']})")
        print(f"  Amber Band: {row['Amber_Rate_p_per_kWh']:.2f} p/kWh  ({row['Amber_Time']})")
        print(f"  Green Band: {row['Green_Rate_p_per_kWh']:.2f} p/kWh  ({row['Green_Time']})")
        print()
    
    # Save to CSV
    output_file = "traffic_light_rates_clean.csv"
    results_df.to_csv(output_file, index=False)
    print(f"💾 Saved to: {output_file}")
    
    # Save to Excel with nice formatting
    output_excel = "traffic_light_rates_clean.xlsx"
    with pd.ExcelWriter(output_excel, engine='openpyxl') as writer:
        results_df.to_excel(writer, sheet_name='Traffic Light Rates', index=False)
    print(f"💾 Saved to: {output_excel}")
    
    print("\n✅ EXTRACTION COMPLETE!")

if __name__ == "__main__":
    main()

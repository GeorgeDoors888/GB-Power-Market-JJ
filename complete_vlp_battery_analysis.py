#!/usr/bin/env python3
"""
Complete VLP-Battery Market Analysis

This script:
1. Downloads BMU registration data from NESO API (BMU-to-Generator mapping)
2. Cross-references with generator register to identify battery BMUs
3. Analyzes which batteries are operated by VLPs (aggregators)
4. Calculates market share and revenue for VLP-operated batteries using BOD data
"""

import pandas as pd
import requests
import json
from google.cloud import bigquery
from datetime import datetime, timedelta
import os
import re

# Configuration
PROJECT_ID = "inner-cinema-476211-u9"
DATASET_ID = "uk_energy_prod"
BOD_TABLE = "bmrs_bod"
GENERATORS_CSV = "generators_list.csv"
CREDENTIALS_PATH = "inner-cinema-credentials.json"
NESO_API_BASE = "https://data.elexon.co.uk/bmrs/api/v1"

# Set credentials
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = CREDENTIALS_PATH

def download_bmu_registration_data():
    """Download complete BMU registration data from NESO"""
    print("\n" + "="*80)
    print("📥 STEP 1: Download BMU Registration Data")
    print("="*80)
    
    url = f"{NESO_API_BASE}/reference/bmunits/all"
    print(f"\n🌐 Fetching BMU data from: {url}")
    
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        bmu_data = response.json()
        
        df = pd.DataFrame(bmu_data)
        print(f"✅ Downloaded {len(df):,} BMU registrations")
        
        # Save to file
        df.to_csv('bmu_registration_data.csv', index=False)
        print(f"💾 Saved to: bmu_registration_data.csv")
        
        # Show summary
        print(f"\n📊 BMU Data Summary:")
        print(f"   Total BMUs: {len(df):,}")
        print(f"   Unique Lead Parties: {df['leadPartyName'].nunique():,}")
        print(f"   Fuel Types: {df['fuelType'].nunique():,}")
        
        # Show fuel type breakdown
        print(f"\n🔋 Fuel Type Distribution:")
        fuel_counts = df['fuelType'].value_counts().head(15)
        for fuel, count in fuel_counts.items():
            print(f"   {fuel}: {count}")
        
        return df
    
    except Exception as e:
        print(f"❌ Error downloading BMU data: {e}")
        return None

def load_battery_generators():
    """Load battery generators from previous analysis"""
    print("\n" + "="*80)
    print("📊 STEP 2: Load Battery Generator Data")
    print("="*80)
    
    # Try to load the most recent battery generators file
    import glob
    battery_files = sorted(glob.glob('battery_generators_*.csv'), reverse=True)
    
    if battery_files:
        print(f"📂 Loading: {battery_files[0]}")
        df = pd.read_csv(battery_files[0])
        print(f"✅ Loaded {len(df):,} battery storage sites")
        return df
    else:
        print("⚠️ No battery generators file found. Loading from generators_list.csv...")
        # Reload from original
        df = pd.read_csv(GENERATORS_CSV, skiprows=1, low_memory=False)
        
        # Identify batteries
        battery_keywords = ['battery', 'bess', 'storage', 'electro-chemical', 'stored energy']
        battery_mask = pd.Series(False, index=df.index)
        
        for col in df.columns:
            if pd.api.types.is_string_dtype(df[col]):
                for keyword in battery_keywords:
                    battery_mask |= df[col].astype(str).str.lower().str.contains(keyword, na=False)
        
        battery_df = df[battery_mask].copy()
        print(f"✅ Identified {len(battery_df):,} battery storage sites")
        return battery_df

def cross_reference_batteries_with_bmus(battery_gen_df, bmu_df):
    """Cross-reference battery generators with BMU registration data"""
    print("\n" + "="*80)
    print("🔗 STEP 3: Cross-Reference Batteries with BMUs")
    print("="*80)
    
    # Strategy 1: Look for batteries in BMU data by fuel type
    print("\n🔍 Strategy 1: Identify batteries by BMU fuel type...")
    
    battery_fuel_keywords = ['BESS', 'BATTERY', 'STORAGE', 'STORED', 'ELECTRIC']
    
    battery_bmu_mask = pd.Series(False, index=bmu_df.index)
    for keyword in battery_fuel_keywords:
        if 'fuelType' in bmu_df.columns:
            battery_bmu_mask |= bmu_df['fuelType'].astype(str).str.upper().str.contains(keyword, na=False)
        if 'bmUnitName' in bmu_df.columns:
            battery_bmu_mask |= bmu_df['bmUnitName'].astype(str).str.upper().str.contains(keyword, na=False)
    
    battery_bmus = bmu_df[battery_bmu_mask].copy()
    print(f"✅ Found {len(battery_bmus)} battery BMUs by fuel type/name")
    
    # Strategy 2: Match by site name (fuzzy matching)
    print(f"\n🔍 Strategy 2: Matching by site name...")
    
    # Get site names from generator data
    if 'Customer Site ' in battery_gen_df.columns:
        gen_sites = battery_gen_df['Customer Site '].dropna().str.upper().str.strip()
        
        matched_bmus = []
        for idx, row in bmu_df.iterrows():
            bmu_name = str(row.get('bmUnitName', '')).upper().strip()
            if bmu_name:
                # Check if any generator site name is in BMU name
                for site in gen_sites:
                    if site and len(site) > 5:  # Avoid short matches
                        # Extract key words from site name
                        site_words = set(re.findall(r'\w+', site))
                        bmu_words = set(re.findall(r'\w+', bmu_name))
                        
                        # If significant overlap, it's likely a match
                        common_words = site_words & bmu_words
                        if len(common_words) >= 2:  # At least 2 words match
                            matched_bmus.append(row)
                            break
        
        if matched_bmus:
            matched_df = pd.DataFrame(matched_bmus)
            print(f"✅ Found {len(matched_df)} additional matches by site name")
            battery_bmus = pd.concat([battery_bmus, matched_df]).drop_duplicates(subset=['nationalGridBmUnit'])
        else:
            print(f"⚠️ No additional matches found by site name")
    
    print(f"\n📊 Total Battery BMUs Identified: {len(battery_bmus)}")
    
    if len(battery_bmus) > 0:
        print(f"\n📋 Sample Battery BMUs:")
        for idx, row in battery_bmus.head(10).iterrows():
            print(f"   {row['nationalGridBmUnit']} | {row['bmUnitName']} | {row['leadPartyName']} | {row['generationCapacity']}MW")
    
    return battery_bmus

def identify_vlp_operators(battery_bmus):
    """Identify which batteries are operated by VLPs (aggregators)"""
    print("\n" + "="*80)
    print("🏢 STEP 4: Identify VLP Operators")
    print("="*80)
    
    # VLP indicators:
    # 1. Lead party name contains aggregator keywords
    # 2. BMU code patterns (2__, C__, M__ prefixes often indicate aggregators)
    # 3. Multiple BMUs under same lead party (portfolio management)
    
    vlp_keywords = [
        'virtual', 'vlp', 'aggregat', 'portfolio', 'flex', 'energy trading',
        'limejump', 'gridserve', 'flexitricity', 'kiwi power', 'voltalis',
        'smartest', 'octopus', 'edf trading', 'centrica', 'drax', 'engie'
    ]
    
    # Identify VLPs by lead party name
    battery_bmus['is_vlp_by_name'] = False
    for keyword in vlp_keywords:
        battery_bmus['is_vlp_by_name'] |= battery_bmus['leadPartyName'].astype(str).str.lower().str.contains(keyword, na=False)
    
    # Identify by BMU code pattern
    battery_bmus['is_aggregator_code'] = battery_bmus['nationalGridBmUnit'].astype(str).str.match(r'^[2CM]__')
    
    # Count BMUs per lead party (VLPs typically manage multiple assets)
    lead_party_counts = battery_bmus.groupby('leadPartyName').size()
    multiple_asset_operators = lead_party_counts[lead_party_counts > 1].index
    battery_bmus['multiple_assets'] = battery_bmus['leadPartyName'].isin(multiple_asset_operators)
    
    # Combined VLP flag
    battery_bmus['is_vlp'] = (
        battery_bmus['is_vlp_by_name'] | 
        battery_bmus['is_aggregator_code'] | 
        battery_bmus['multiple_assets']
    )
    
    vlp_batteries = battery_bmus[battery_bmus['is_vlp']].copy()
    direct_batteries = battery_bmus[~battery_bmus['is_vlp']].copy()
    
    print(f"\n📊 Battery Ownership Analysis:")
    print(f"   Total Battery BMUs: {len(battery_bmus)}")
    print(f"   VLP-Operated: {len(vlp_batteries)} ({len(vlp_batteries)/len(battery_bmus)*100:.1f}%)")
    print(f"   Direct-Operated: {len(direct_batteries)} ({len(direct_batteries)/len(battery_bmus)*100:.1f}%)")
    
    print(f"\n🏆 Top VLP Operators:")
    if len(vlp_batteries) > 0:
        vlp_lead_parties = vlp_batteries.groupby('leadPartyName').agg({
            'nationalGridBmUnit': 'count',
            'generationCapacity': lambda x: pd.to_numeric(x, errors='coerce').sum()
        }).sort_values('nationalGridBmUnit', ascending=False)
        
        for idx, row in vlp_lead_parties.head(10).iterrows():
            print(f"   {idx}: {int(row['nationalGridBmUnit'])} BMUs, {row['generationCapacity']:.1f}MW capacity")
    
    return battery_bmus, vlp_batteries, direct_batteries

def analyze_bod_revenue(battery_bmus, vlp_batteries):
    """Calculate market participation and revenue for VLP vs direct batteries"""
    print("\n" + "="*80)
    print("💰 STEP 5: Analyze Market Participation & Revenue")
    print("="*80)
    
    client = bigquery.Client(project=PROJECT_ID)
    
    # Get all battery BMU IDs - use elexonBmUnit which matches BOD table
    all_battery_ids = battery_bmus['elexonBmUnit'].tolist()
    vlp_battery_ids = vlp_batteries['elexonBmUnit'].tolist()
    
    print(f"\n⏳ Analyzing BOD data for {len(all_battery_ids)} battery BMUs...")
    print(f"   (This may take a minute...)")
    
    # Create SQL query
    battery_ids_str = "', '".join(all_battery_ids)
    vlp_ids_str = "', '".join(vlp_battery_ids)
    
    query = f"""
    WITH battery_activity AS (
      SELECT 
        bmUnit,
        COUNT(*) as total_actions,
        COUNT(DISTINCT settlementDate) as active_days,
        MIN(settlementDate) as first_action,
        MAX(settlementDate) as last_action,
        
        -- Bid activity (selling reduction/buying power)
        COUNT(CASE WHEN bid > 0 AND bid < 9000 THEN 1 END) as bid_actions,
        AVG(CASE WHEN bid > 0 AND bid < 9000 THEN bid END) as avg_bid_price,
        SUM(CASE WHEN bid > 0 AND bid < 9000 THEN ABS(levelTo - levelFrom) END) as total_bid_mw,
        
        -- Offer activity (selling increase/selling power)
        COUNT(CASE WHEN offer > 0 AND offer < 9000 THEN 1 END) as offer_actions,
        AVG(CASE WHEN offer > 0 AND offer < 9000 THEN offer END) as avg_offer_price,
        SUM(CASE WHEN offer > 0 AND offer < 9000 THEN ABS(levelTo - levelFrom) END) as total_offer_mw,
        
        -- Capacity
        MAX(GREATEST(ABS(levelFrom), ABS(levelTo))) as max_capacity_mw,
        AVG(ABS(levelTo - levelFrom)) as avg_action_size_mw
        
      FROM `{PROJECT_ID}.{DATASET_ID}.{BOD_TABLE}`
      WHERE bmUnit IN ('{battery_ids_str}')
        AND settlementDate >= DATE_SUB(CURRENT_DATE(), INTERVAL 365 DAY)
      GROUP BY bmUnit
    ),
    revenue_estimate AS (
      SELECT 
        *,
        -- Estimate revenue (simplified: MW * price * 0.5 hours per settlement period)
        (COALESCE(total_bid_mw, 0) * COALESCE(avg_bid_price, 0) * 0.5 + 
         COALESCE(total_offer_mw, 0) * COALESCE(avg_offer_price, 0) * 0.5) as estimated_revenue_gbp,
        
        CASE WHEN bmUnit IN ('{vlp_ids_str}') THEN TRUE ELSE FALSE END as is_vlp
      FROM battery_activity
    )
    SELECT * FROM revenue_estimate
    ORDER BY estimated_revenue_gbp DESC
    """
    
    df = client.query(query).to_dataframe()
    
    if len(df) == 0:
        print(f"⚠️ No BOD data found for battery BMUs")
        return None
    
    print(f"✅ Analyzed {len(df)} battery BMUs with BOD activity")
    
    # Calculate summary statistics
    vlp_df = df[df['is_vlp'] == True]
    direct_df = df[df['is_vlp'] == False]
    
    print(f"\n" + "="*80)
    print(f"📊 MARKET SHARE ANALYSIS")
    print(f"="*80)
    
    print(f"\n🔋 VLP-Operated Batteries:")
    print(f"   Count: {len(vlp_df)}")
    print(f"   Total Capacity: {vlp_df['max_capacity_mw'].sum():.1f} MW")
    print(f"   Total Actions: {vlp_df['total_actions'].sum():,}")
    print(f"   Avg Actions per BMU: {vlp_df['total_actions'].mean():.0f}")
    print(f"   Total Estimated Revenue: £{vlp_df['estimated_revenue_gbp'].sum():,.0f}")
    print(f"   Avg Revenue per BMU: £{vlp_df['estimated_revenue_gbp'].mean():,.0f}")
    
    print(f"\n🏭 Direct-Operated Batteries:")
    print(f"   Count: {len(direct_df)}")
    print(f"   Total Capacity: {direct_df['max_capacity_mw'].sum():.1f} MW")
    print(f"   Total Actions: {direct_df['total_actions'].sum():,}")
    print(f"   Avg Actions per BMU: {direct_df['total_actions'].mean():.0f}")
    print(f"   Total Estimated Revenue: £{direct_df['estimated_revenue_gbp'].sum():,.0f}")
    print(f"   Avg Revenue per BMU: £{direct_df['estimated_revenue_gbp'].mean():,.0f}")
    
    # Market share
    total_revenue = df['estimated_revenue_gbp'].sum()
    vlp_revenue = vlp_df['estimated_revenue_gbp'].sum()
    vlp_market_share = (vlp_revenue / total_revenue * 100) if total_revenue > 0 else 0
    
    print(f"\n💰 Revenue Market Share:")
    print(f"   VLP-Operated: {vlp_market_share:.1f}% (£{vlp_revenue:,.0f})")
    print(f"   Direct-Operated: {100-vlp_market_share:.1f}% (£{total_revenue - vlp_revenue:,.0f})")
    print(f"   Total Market: £{total_revenue:,.0f}")
    
    print(f"\n🏆 Top 10 Revenue Generators:")
    for idx, row in df.head(10).iterrows():
        vlp_flag = " [VLP]" if row['is_vlp'] else ""
        print(f"   {row['bmUnit']}{vlp_flag}")
        print(f"      Revenue: £{row['estimated_revenue_gbp']:,.0f} | Actions: {row['total_actions']:,} | Capacity: {row['max_capacity_mw']:.1f}MW")
    
    return df

def export_final_results(battery_bmus, vlp_batteries, direct_batteries, revenue_df):
    """Export comprehensive results"""
    print("\n" + "="*80)
    print("💾 STEP 6: Export Results")
    print("="*80)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Export battery BMUs with VLP flag
    export_df = battery_bmus.copy()
    battery_bmus.to_csv(f'battery_bmus_complete_{timestamp}.csv', index=False)
    print(f"✅ Exported: battery_bmus_complete_{timestamp}.csv")
    
    # Export VLP batteries only
    vlp_batteries.to_csv(f'vlp_operated_batteries_{timestamp}.csv', index=False)
    print(f"✅ Exported: vlp_operated_batteries_{timestamp}.csv")
    
    # Export direct batteries only
    direct_batteries.to_csv(f'direct_operated_batteries_{timestamp}.csv', index=False)
    print(f"✅ Exported: direct_operated_batteries_{timestamp}.csv")
    
    # Export revenue analysis
    if revenue_df is not None and len(revenue_df) > 0:
        revenue_df.to_csv(f'battery_revenue_analysis_{timestamp}.csv', index=False)
        print(f"✅ Exported: battery_revenue_analysis_{timestamp}.csv")

def generate_final_report(battery_bmus, vlp_batteries, revenue_df):
    """Generate comprehensive final report"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    vlp_count = len(vlp_batteries)
    direct_count = len(battery_bmus) - vlp_count
    
    report = f"""
{"="*80}
🔋 COMPLETE VLP-BATTERY MARKET ANALYSIS REPORT
{"="*80}

📅 Report Date: {timestamp}
📂 Data Sources:
   - NESO BMU Registration API
   - BigQuery BOD Table: {PROJECT_ID}.{DATASET_ID}.{BOD_TABLE}
   - Generator Register: {GENERATORS_CSV}

{"="*80}
📊 EXECUTIVE SUMMARY
{"="*80}

Total Battery BMUs Identified: {len(battery_bmus)}
├─ VLP-Operated: {vlp_count} ({vlp_count/len(battery_bmus)*100:.1f}%)
└─ Direct-Operated: {direct_count} ({direct_count/len(battery_bmus)*100:.1f}%)

"""
    
    if revenue_df is not None and len(revenue_df) > 0:
        vlp_rev_df = revenue_df[revenue_df['is_vlp'] == True]
        direct_rev_df = revenue_df[revenue_df['is_vlp'] == False]
        
        total_revenue = revenue_df['estimated_revenue_gbp'].sum()
        vlp_revenue = vlp_rev_df['estimated_revenue_gbp'].sum()
        vlp_share = (vlp_revenue / total_revenue * 100) if total_revenue > 0 else 0
        
        report += f"""
💰 REVENUE ANALYSIS (Last 365 Days)
{"="*80}

Total Market Revenue: £{total_revenue:,.0f}

VLP-Operated Batteries:
├─ Revenue: £{vlp_revenue:,.0f} ({vlp_share:.1f}% market share)
├─ Capacity: {vlp_rev_df['max_capacity_mw'].sum():.1f} MW
├─ Total Actions: {vlp_rev_df['total_actions'].sum():,}
└─ Avg Revenue/BMU: £{vlp_rev_df['estimated_revenue_gbp'].mean():,.0f}

Direct-Operated Batteries:
├─ Revenue: £{total_revenue - vlp_revenue:,.0f} ({100-vlp_share:.1f}% market share)
├─ Capacity: {direct_rev_df['max_capacity_mw'].sum():.1f} MW
├─ Total Actions: {direct_rev_df['total_actions'].sum():,}
└─ Avg Revenue/BMU: £{direct_rev_df['estimated_revenue_gbp'].mean():,.0f}

"""
        
        report += f"""
🏆 TOP 10 REVENUE GENERATORS
{"="*80}
"""
        for idx, row in revenue_df.head(10).iterrows():
            vlp_flag = "[VLP]" if row['is_vlp'] else "[DIRECT]"
            report += f"""
{row['bmUnit']} {vlp_flag}
├─ Revenue: £{row['estimated_revenue_gbp']:,.0f}
├─ Capacity: {row['max_capacity_mw']:.1f} MW
├─ Actions: {row['total_actions']:,}
├─ Active Days: {row['active_days']}
├─ Avg Bid Price: £{row['avg_bid_price']:.2f}/MWh
└─ Avg Offer Price: £{row['avg_offer_price']:.2f}/MWh
"""
    
    report += f"""
{"="*80}
🏢 TOP VLP OPERATORS
{"="*80}
"""
    
    if len(vlp_batteries) > 0:
        vlp_summary = vlp_batteries.groupby('leadPartyName').agg({
            'nationalGridBmUnit': 'count',
            'generationCapacity': lambda x: pd.to_numeric(x, errors='coerce').sum()
        }).sort_values('nationalGridBmUnit', ascending=False)
        
        for idx, row in vlp_summary.head(15).iterrows():
            report += f"\n{idx}"
            report += f"\n├─ BMUs: {int(row['nationalGridBmUnit'])}"
            report += f"\n└─ Total Capacity: {row['generationCapacity']:.1f} MW\n"
    
    report += f"""
{"="*80}
💡 KEY INSIGHTS
{"="*80}

1. VLP MARKET POSITION:
   • VLPs operate {vlp_count} battery BMUs ({vlp_count/len(battery_bmus)*100:.1f}% of total)
"""
    
    if revenue_df is not None and len(revenue_df) > 0:
        report += f"   • VLPs capture {vlp_share:.1f}% of battery balancing revenue\n"
        report += f"   • Average VLP revenue: £{vlp_rev_df['estimated_revenue_gbp'].mean():,.0f} per BMU\n"
        report += f"   • Average direct revenue: £{direct_rev_df['estimated_revenue_gbp'].mean():,.0f} per BMU\n"
    
    report += f"""
2. VLP ADVANTAGES:
   • Professional optimization and trading
   • Portfolio diversification across multiple assets
   • Better market access and liquidity management
   • Reduced operational burden for asset owners

3. MARKET STRUCTURE:
   • Battery storage is increasingly important for grid flexibility
   • VLPs provide aggregation services to smaller storage operators
   • Direct operation more common for larger, utility-scale batteries
   • Mixed ownership model emerging (some assets both VLP and direct)

{"="*80}
📋 METHODOLOGY
{"="*80}

VLP Identification Criteria:
1. Lead party name contains aggregator keywords (virtual, aggregat, flex, etc.)
2. BMU code patterns indicating aggregation (2__, C__, M__ prefixes)
3. Multiple BMUs under single lead party (portfolio management)

Revenue Calculation:
• Based on Bid-Offer Data (BOD) from last 365 days
• Formula: (MWh traded * Average price * 0.5 hours per period)
• Note: Simplified estimate, actual revenue includes:
  - System balancing payments
  - Availability payments
  - Response services
  - Ancillary services revenue

{"="*80}
"""
    
    report_file = f"complete_vlp_battery_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    with open(report_file, 'w') as f:
        f.write(report)
    
    print(report)
    print(f"\n💾 Report saved: {report_file}")

def main():
    print("\n" + "="*80)
    print("🔋 COMPLETE VLP-BATTERY MARKET ANALYSIS")
    print("="*80)
    print("\nThis analysis will:")
    print("1. Download BMU registration data from NESO")
    print("2. Cross-reference with battery generators")
    print("3. Identify VLP operators")
    print("4. Calculate market share and revenue")
    print("="*80)
    
    try:
        # Step 1: Download BMU data
        bmu_df = download_bmu_registration_data()
        if bmu_df is None:
            return
        
        # Step 2: Load battery generators
        battery_gen_df = load_battery_generators()
        
        # Step 3: Cross-reference
        battery_bmus = cross_reference_batteries_with_bmus(battery_gen_df, bmu_df)
        
        if len(battery_bmus) == 0:
            print("\n⚠️ No battery BMUs found. Cannot continue analysis.")
            return
        
        # Step 4: Identify VLPs
        battery_bmus, vlp_batteries, direct_batteries = identify_vlp_operators(battery_bmus)
        
        # Step 5: Analyze revenue
        revenue_df = analyze_bod_revenue(battery_bmus, vlp_batteries)
        
        # Step 6: Export results
        export_final_results(battery_bmus, vlp_batteries, direct_batteries, revenue_df)
        
        # Step 7: Generate report
        generate_final_report(battery_bmus, vlp_batteries, revenue_df)
        
        print("\n" + "="*80)
        print("✅ ANALYSIS COMPLETE!")
        print("="*80)
        print("\nGenerated files:")
        print("  • battery_bmus_complete_YYYYMMDD_HHMMSS.csv")
        print("  • vlp_operated_batteries_YYYYMMDD_HHMMSS.csv")
        print("  • direct_operated_batteries_YYYYMMDD_HHMMSS.csv")
        print("  • battery_revenue_analysis_YYYYMMDD_HHMMSS.csv")
        print("  • complete_vlp_battery_report_YYYYMMDD_HHMMSS.txt")
        print("="*80 + "\n")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()

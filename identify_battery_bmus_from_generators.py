#!/usr/bin/env python3
"""
Identify Battery BMUs by Cross-Referencing Generator Register with BOD Data

This script:
1. Loads generator register CSV to find battery storage sites
2. Maps generators to BMU IDs from BOD table
3. Analyzes battery participation in balancing mechanism
4. Identifies potential VLPs
"""

import pandas as pd
import json
from google.cloud import bigquery
from datetime import datetime
import os

# Configuration
PROJECT_ID = "inner-cinema-476211-u9"
DATASET_ID = "uk_energy_prod"
BOD_TABLE = "bmrs_bod"
GENERATORS_CSV = "generators_list.csv"
CREDENTIALS_PATH = "inner-cinema-credentials.json"

# Set credentials
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = CREDENTIALS_PATH

def load_generators_data():
    """Load and parse generator register CSV"""
    print("\n📊 Loading generator register...")
    
    # The CSV has multiple header rows, skip the first one
    df = pd.read_csv(GENERATORS_CSV, skiprows=1, low_memory=False)
    
    print(f"✅ Loaded {len(df):,} generator records")
    
    # Show columns to understand structure
    print(f"\n📋 Available columns ({len(df.columns)}):")
    for i, col in enumerate(df.columns[:20]):  # Show first 20
        print(f"   {i}: {col}")
    
    return df

def identify_battery_generators(df):
    """Find generators with battery storage technology"""
    print("\n🔋 Identifying battery storage generators...")
    
    # Look for battery keywords in energy source and technology columns
    battery_keywords = ['battery', 'bess', 'storage', 'electro-chemical']
    
    # Get energy source and technology columns
    energy_cols = [col for col in df.columns if 'Energy Source' in col or 'Technology' in col or 'Storage' in col]
    print(f"\n🔍 Searching in {len(energy_cols)} energy-related columns:")
    for col in energy_cols[:10]:
        print(f"   - {col}")
    
    # Create battery mask
    battery_mask = pd.Series(False, index=df.index)
    
    for col in df.columns:
        if pd.api.types.is_string_dtype(df[col]):
            for keyword in battery_keywords:
                battery_mask |= df[col].astype(str).str.lower().str.contains(keyword, na=False)
    
    battery_df = df[battery_mask].copy()
    
    print(f"\n✅ Found {len(battery_df)} battery storage sites")
    
    if len(battery_df) > 0:
        # Show sample
        print(f"\n📋 Sample battery generators:")
        for idx, row in battery_df.head(10).iterrows():
            site_name = row.get('Customer Site ', 'Unknown')
            capacity = row.get('Energy Source & Energy Conversion Technology 1 - Registered Capacity (MW)', 'N/A')
            energy_source = row.get('Energy Source 1', 'N/A')
            print(f"   {site_name}: {capacity}MW ({energy_source})")
    
    return battery_df

def get_all_bmu_ids():
    """Get all unique BMU IDs from BOD table"""
    print("\n📊 Fetching all BMU IDs from BOD table...")
    
    client = bigquery.Client(project=PROJECT_ID)
    
    query = f"""
    SELECT DISTINCT bmUnit
    FROM `{PROJECT_ID}.{DATASET_ID}.{BOD_TABLE}`
    WHERE bmUnit IS NOT NULL 
      AND bmUnit != 'None'
    ORDER BY bmUnit
    """
    
    df = client.query(query).to_dataframe()
    print(f"✅ Found {len(df)} unique BMU IDs")
    
    return df['bmUnit'].tolist()

def match_generators_to_bmus(battery_df, bmu_list):
    """Try to match generator sites to BMU IDs"""
    print("\n🔗 Attempting to match battery generators to BMUs...")
    
    # Common matching strategies:
    # 1. Direct site name to BMU code matching
    # 2. Postcode/location matching
    # 3. Capacity correlation
    
    # For now, let's show what we have and note that we need a mapping table
    print(f"\n⚠️ Direct matching requires a generator-to-BMU mapping table")
    print(f"   Battery generators: {len(battery_df)}")
    print(f"   BMU IDs in BOD: {len(bmu_list)}")
    
    # Show some BMU examples
    print(f"\n📋 Sample BMU IDs:")
    for bmu in bmu_list[:20]:
        print(f"   {bmu}")
    
    return None

def analyze_all_bmus_for_battery_patterns():
    """
    Analyze all BMUs to find battery-like behavior patterns
    (frequent bidirectional flow, quick response times)
    """
    print("\n🔍 Analyzing BMU behavior patterns to identify potential batteries...")
    
    client = bigquery.Client(project=PROJECT_ID)
    
    # Look for BMUs with characteristics of battery storage:
    # - Frequent bid/offer pairs (buying and selling)
    # - Variable output levels (charge/discharge)
    # - Participation across many settlement periods
    
    query = f"""
    WITH bmu_stats AS (
      SELECT 
        bmUnit,
        COUNT(*) as total_records,
        COUNT(DISTINCT settlementDate) as active_days,
        COUNT(DISTINCT CASE WHEN bid > 0 THEN pairId END) as bid_pairs,
        COUNT(DISTINCT CASE WHEN offer > 0 THEN pairId END) as offer_pairs,
        AVG(ABS(levelTo - levelFrom)) as avg_level_change_mw,
        STDDEV(ABS(levelTo - levelFrom)) as stddev_level_change,
        MIN(settlementDate) as first_seen,
        MAX(settlementDate) as last_seen,
        AVG(CASE WHEN bid > 0 THEN bid END) as avg_bid_price,
        AVG(CASE WHEN offer > 0 THEN offer END) as avg_offer_price
      FROM `{PROJECT_ID}.{DATASET_ID}.{BOD_TABLE}`
      WHERE bmUnit IS NOT NULL 
        AND bmUnit != 'None'
        AND settlementDate >= DATE_SUB(CURRENT_DATE(), INTERVAL 365 DAY)
      GROUP BY bmUnit
    )
    SELECT *,
      -- Battery-like indicators
      CASE WHEN bid_pairs > 100 AND offer_pairs > 100 THEN TRUE ELSE FALSE END as bidirectional,
      CASE WHEN avg_level_change_mw > 10 AND stddev_level_change > 5 THEN TRUE ELSE FALSE END as variable_output,
      CASE WHEN active_days > 300 THEN TRUE ELSE FALSE END as highly_active
    FROM bmu_stats
    WHERE total_records > 1000  -- Filter for active BMUs
    ORDER BY total_records DESC
    LIMIT 100
    """
    
    print(f"\n⏳ Running analysis query...")
    df = client.query(query).to_dataframe()
    
    print(f"\n✅ Analyzed {len(df)} active BMUs")
    
    # Identify potential batteries by behavior
    potential_batteries = df[
        (df['bidirectional'] == True) & 
        (df['variable_output'] == True) &
        (df['highly_active'] == True)
    ]
    
    print(f"\n🔋 Found {len(potential_batteries)} BMUs with battery-like behavior:")
    print(f"   - Bidirectional (bid + offer)")
    print(f"   - Variable output (flexible MW levels)")
    print(f"   - Highly active (>300 days)")
    
    if len(potential_batteries) > 0:
        print(f"\n🏆 Top 20 Potential Battery BMUs:")
        for idx, row in potential_batteries.head(20).iterrows():
            print(f"\n   {row['bmUnit']}")
            print(f"      Records: {row['total_records']:,} | Days: {row['active_days']}")
            print(f"      Avg change: {row['avg_level_change_mw']:.1f}MW (±{row['stddev_level_change']:.1f})")
            print(f"      Bid pairs: {row['bid_pairs']:,} | Offer pairs: {row['offer_pairs']:,}")
    
    return df, potential_batteries

def identify_vlp_patterns(df):
    """Look for VLP indicators in BMU behavior"""
    print("\n🔍 Identifying potential VLP patterns...")
    
    # VLP indicators:
    # - BMU codes starting with "2__" (often aggregated units)
    # - High variability in output (aggregating multiple sites)
    # - Very frequent trading (professional optimization)
    
    vlp_candidates = df[
        df['bmUnit'].str.startswith('2__', na=False) |
        (df['total_records'] > df['total_records'].quantile(0.95))
    ].copy()
    
    print(f"\n✅ Found {len(vlp_candidates)} potential VLP BMUs")
    
    if len(vlp_candidates) > 0:
        print(f"\n📋 VLP Candidates:")
        for idx, row in vlp_candidates.head(10).iterrows():
            print(f"   {row['bmUnit']}: {row['total_records']:,} records, {row['active_days']} days")
    
    return vlp_candidates

def export_results(all_bmus_df, battery_like_df, vlp_df, battery_generators_df):
    """Export results to CSV files"""
    print("\n💾 Exporting results...")
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Export all analyzed BMUs
    all_file = f"bmu_behavior_analysis_{timestamp}.csv"
    all_bmus_df.to_csv(all_file, index=False)
    print(f"✅ Exported all BMUs: {all_file}")
    
    # Export battery-like BMUs
    if len(battery_like_df) > 0:
        battery_file = f"battery_like_bmus_{timestamp}.csv"
        battery_like_df.to_csv(battery_file, index=False)
        print(f"✅ Exported battery-like BMUs: {battery_file}")
    
    # Export VLP candidates
    if len(vlp_df) > 0:
        vlp_file = f"vlp_candidate_bmus_{timestamp}.csv"
        vlp_df.to_csv(vlp_file, index=False)
        print(f"✅ Exported VLP candidates: {vlp_file}")
    
    # Export battery generators
    gen_file = f"battery_generators_{timestamp}.csv"
    battery_generators_df.to_csv(gen_file, index=False)
    print(f"✅ Exported battery generators: {gen_file}")

def generate_report(all_bmus_df, battery_like_df, vlp_df, battery_generators_df):
    """Generate comprehensive report"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    report = f"""
================================================================================
🔋 GB BATTERY & VLP IDENTIFICATION REPORT
================================================================================

📅 Report Date: {timestamp}
📂 Data Sources: 
   - BOD Table: {PROJECT_ID}.{DATASET_ID}.{BOD_TABLE}
   - Generator Register: {GENERATORS_CSV}

--------------------------------------------------------------------------------
📊 GENERATOR REGISTER ANALYSIS
--------------------------------------------------------------------------------
Total generators in register: {len(battery_generators_df.index) if hasattr(battery_generators_df, 'index') else 0:,}
Battery storage sites identified: {len(battery_generators_df):,}

Battery Technology Breakdown:
"""
    
    if len(battery_generators_df) > 0 and 'Energy Source 1' in battery_generators_df.columns:
        tech_counts = battery_generators_df['Energy Source 1'].value_counts()
        for tech, count in tech_counts.head(10).items():
            report += f"   {tech}: {count}\n"
    
    report += f"""
--------------------------------------------------------------------------------
📊 BMU BEHAVIOR ANALYSIS
--------------------------------------------------------------------------------
Total active BMUs analyzed: {len(all_bmus_df):,}
BMUs with battery-like behavior: {len(battery_like_df):,}
  - Bidirectional trading (bid + offer)
  - Variable output (flexible MW levels)
  - Highly active (>300 days/year)

Potential VLP BMUs identified: {len(vlp_df):,}
  - Aggregator codes (2__ prefix)
  - High frequency trading
  - Large record volumes

"""
    
    if len(battery_like_df) > 0:
        report += f"""
🏆 TOP 10 BATTERY-LIKE BMUs:
"""
        for idx, row in battery_like_df.head(10).iterrows():
            report += f"""
   {row['bmUnit']}
      Records: {row['total_records']:,} | Active days: {row['active_days']}
      Avg level change: {row['avg_level_change_mw']:.1f} MW (±{row['stddev_level_change']:.1f})
      Bid pairs: {row['bid_pairs']:,} | Offer pairs: {row['offer_pairs']:,}
      Date range: {row['first_seen']} to {row['last_seen']}
"""
    
    if len(vlp_df) > 0:
        report += f"""
--------------------------------------------------------------------------------
🔍 VLP CANDIDATES
--------------------------------------------------------------------------------
"""
        for idx, row in vlp_df.head(10).iterrows():
            report += f"""   {row['bmUnit']}
      Total records: {row['total_records']:,}
      Active days: {row['active_days']}
      Avg level change: {row['avg_level_change_mw']:.1f} MW
"""
    
    report += f"""
================================================================================
💡 KEY INSIGHTS
================================================================================

BATTERY IDENTIFICATION:
• Generator register shows {len(battery_generators_df)} battery storage sites
• Behavioral analysis found {len(battery_like_df)} BMUs with battery-like patterns
• Direct generator-to-BMU mapping requires additional reference data

VLP IDENTIFICATION:
• {len(vlp_df)} BMUs show VLP characteristics
• BMUs starting with "2__" are often aggregators/VLPs
• High trading frequency indicates professional optimization

NEXT STEPS:
1. Obtain NESO's BMU-to-Generator mapping table
2. Cross-reference generator register with BMU behavioral data
3. Verify VLP status with REMIT participant data
4. Analyze revenue and market impact of identified batteries/VLPs

================================================================================
"""
    
    report_file = f"battery_vlp_identification_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    with open(report_file, 'w') as f:
        f.write(report)
    
    print(report)
    print(f"\n💾 Report saved: {report_file}")

def main():
    print("="*80)
    print("🔋 GB Battery & VLP Identification Analysis")
    print("="*80)
    print("\nCross-referencing generator register with BOD behavioral data")
    print("="*80)
    
    try:
        # Step 1: Load generator register
        generators_df = load_generators_data()
        
        # Step 2: Identify battery generators
        battery_generators = identify_battery_generators(generators_df)
        
        # Step 3: Analyze BMU behavior patterns
        all_bmus_df, battery_like_df = analyze_all_bmus_for_battery_patterns()
        
        # Step 4: Identify VLP patterns
        vlp_df = identify_vlp_patterns(all_bmus_df)
        
        # Step 5: Export results
        export_results(all_bmus_df, battery_like_df, vlp_df, battery_generators)
        
        # Step 6: Generate report
        generate_report(all_bmus_df, battery_like_df, vlp_df, battery_generators)
        
        print("\n✅ Analysis Complete!")
        print("="*80)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()

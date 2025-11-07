#!/usr/bin/env python3
"""
Analyze Battery and VLP Participation in GB Balancing Market

Since REMIT reference endpoints only return IDs, this script:
1. Downloads recent REMIT messages with full asset details
2. Analyzes BOD data for battery/VLP BMU IDs directly
3. Cross-references to identify Virtual Lead Parties
"""

import requests
import pandas as pd
from datetime import datetime, timedelta
import os

BMRS_API = 'https://data.elexon.co.uk/bmrs/api/v1'
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = '/Users/georgemajor/GB Power Market JJ/inner-cinema-credentials.json'

from google.cloud import bigquery

PROJECT = 'inner-cinema-476211-u9'
DATASET = 'uk_energy_prod'

VLP_KEYWORDS = ['virtual', 'aggregat', 'portfolio', 'vlp', 'multi', 'flex', 'pool']
BATTERY_KEYWORDS = ['bess', 'battery', 'stor', 'energy storage', 'btry', 'ess']

def download_remit_search(asset_id=None, days_back=30):
    """
    Search REMIT messages by mRID or date range
    """
    print(f"📥 Downloading REMIT messages (last {days_back} days)...")
    
    url = f"{BMRS_API}/remit/list/by-publish"
    
    to_date = datetime.now()
    from_date = to_date - timedelta(days=days_back)
    
    params = {
        'publishDateTimeFrom': from_date.strftime('%Y-%m-%dT00:00:00Z'),
        'publishDateTimeTo': to_date.strftime('%Y-%m-%dT23:59:59Z')
    }
    
    try:
        response = requests.get(url, params=params, timeout=120)
        
        # Check if 404 - endpoint may not exist in this form
        if response.status_code == 404:
            print("⚠️ Endpoint not found, trying search endpoint...")
            url = f"{BMRS_API}/remit/search"
            response = requests.get(url, timeout=60)
        
        response.raise_for_status()
        data = response.json()
        
        messages = data if isinstance(data, list) else data.get('data', [])
        print(f"✅ Downloaded {len(messages)} REMIT messages")
        return messages
        
    except Exception as e:
        print(f"❌ REMIT download failed: {e}")
        print("   Continuing with BOD-only analysis...")
        return []

def analyze_bod_for_batteries():
    """
    Query BOD data to find all battery BMU IDs based on naming patterns
    """
    print("\n🔋 Analyzing BOD data for battery BMUs...")
    
    client = bigquery.Client(project=PROJECT)
    
    # Note: Using bmUnit. BOD schema has: bid/offer (prices), levelFrom/levelTo (MW levels)
    query = f"""
    WITH battery_candidates AS (
      SELECT 
        bmUnit,
        COUNT(*) as total_periods,
        COUNT(DISTINCT settlementDate) as active_days,
        MIN(settlementDate) as first_seen,
        MAX(settlementDate) as last_seen,
        AVG(ABS(levelTo - levelFrom)) as avg_level_change_mw,
        AVG(CASE WHEN bid IS NOT NULL AND bid > 0 THEN bid END) as avg_bid_price,
        AVG(CASE WHEN offer IS NOT NULL AND offer > 0 THEN offer END) as avg_offer_price,
        AVG(levelFrom) as avg_level_from,
        AVG(levelTo) as avg_level_to
      FROM `{PROJECT}.{DATASET}.bmrs_bod`
      WHERE (
        LOWER(bmUnit) LIKE '%bess%' 
        OR LOWER(bmUnit) LIKE '%stor%'
        OR LOWER(bmUnit) LIKE '%btry%'
        OR LOWER(bmUnit) LIKE '%battery%'
        OR LOWER(bmUnit) LIKE '%ess%'
      )
      AND settlementDate >= DATE_SUB(CURRENT_DATE(), INTERVAL 365 DAY)
      GROUP BY bmUnit
    )
    SELECT 
      *,
      -- Check for VLP indicators in name
      CASE 
        WHEN LOWER(bmUnit) LIKE '%virtual%' THEN TRUE
        WHEN LOWER(bmUnit) LIKE '%aggr%' THEN TRUE
        WHEN LOWER(bmUnit) LIKE '%port%' THEN TRUE
        WHEN LOWER(bmUnit) LIKE '%flex%' THEN TRUE
        WHEN LOWER(bmUnit) LIKE '%pool%' THEN TRUE
        WHEN LOWER(bmUnit) LIKE '%multi%' THEN TRUE
        ELSE FALSE
      END as potential_vlp,
      -- Categorize by keywords matched
      CASE
        WHEN LOWER(bmUnit) LIKE '%bess%' THEN 'BESS'
        WHEN LOWER(bmUnit) LIKE '%stor%' THEN 'STOR'
        WHEN LOWER(bmUnit) LIKE '%btry%' THEN 'BATTERY'
        WHEN LOWER(bmUnit) LIKE '%ess%' THEN 'ESS'
        ELSE 'OTHER'
      END as battery_type
    FROM battery_candidates
    ORDER BY total_periods DESC
    """
    
    try:
        df = client.query(query).to_dataframe()
        print(f"✅ Found {len(df)} battery BMUs")
        print(f"   {df['potential_vlp'].sum()} identified as potential VLPs by name")
        
        # Show breakdown by type
        print(f"\n📊 Battery types:")
        print(df['battery_type'].value_counts())
        
        return df
        
    except Exception as e:
        print(f"❌ Error querying BOD: {e}")
        return pd.DataFrame()

def analyze_bod_all_units():
    """
    Get summary of ALL BMUs in BOD data to understand market structure
    """
    print("\n📊 Analyzing all BMUs in BOD data...")
    
    client = bigquery.Client(project=PROJECT)
    
    query = f"""
    SELECT 
      COUNT(DISTINCT bmUnit) as total_unique_bmus,
      COUNT(*) as total_records,
      COUNT(DISTINCT settlementDate) as days_with_data,
      MIN(settlementDate) as earliest_date,
      MAX(settlementDate) as latest_date
    FROM `{PROJECT}.{DATASET}.bmrs_bod`
    WHERE settlementDate >= DATE_SUB(CURRENT_DATE(), INTERVAL 365 DAY)
    """
    
    try:
        summary = client.query(query).to_dataframe()
        print(f"\n📈 BOD Summary (last 365 days):")
        print(f"   Total unique BMUs: {summary['total_unique_bmus'].iloc[0]:,}")
        print(f"   Total records: {summary['total_records'].iloc[0]:,}")
        print(f"   Days with data: {summary['days_with_data'].iloc[0]}")
        print(f"   Date range: {summary['earliest_date'].iloc[0]} to {summary['latest_date'].iloc[0]}")
        
        return summary
        
    except Exception as e:
        print(f"❌ Error querying BOD summary: {e}")
        return pd.DataFrame()

def export_results(battery_df, timestamp):
    """Export results to CSV"""
    print("\n💾 Exporting results...")
    
    if len(battery_df) > 0:
        # All batteries
        file = f'battery_bmus_bod_{timestamp}.csv'
        battery_df.to_csv(file, index=False)
        print(f"   ✅ Exported all batteries: {file}")
        
        # VLP batteries only
        vlp_batteries = battery_df[battery_df['potential_vlp'] == True]
        if len(vlp_batteries) > 0:
            file = f'vlp_battery_bmus_{timestamp}.csv'
            vlp_batteries.to_csv(file, index=False)
            print(f"   ✅ Exported VLP batteries: {file}")
        
        # Top 100 by activity
        top_batteries = battery_df.nlargest(100, 'total_periods')
        file = f'top_100_battery_bmus_{timestamp}.csv'
        top_batteries.to_csv(file, index=False)
        print(f"   ✅ Exported top 100: {file}")

def generate_report(battery_df, summary_df):
    """Generate comprehensive report"""
    print("\n" + "="*80)
    print("📊 GB BATTERY & VLP MARKET ANALYSIS REPORT")
    print("="*80)
    
    print(f"\n📅 Report Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📂 Data Source: {PROJECT}.{DATASET}.bmrs_bod")
    
    if len(summary_df) > 0:
        print("\n" + "-"*80)
        print("📈 BALANCING MARKET OVERVIEW")
        print("-"*80)
        print(f"Total unique BMUs: {summary_df['total_unique_bmus'].iloc[0]:,}")
        print(f"Total BOD records: {summary_df['total_records'].iloc[0]:,}")
        print(f"Days analyzed: {summary_df['days_with_data'].iloc[0]}")
    
    if len(battery_df) > 0:
        print("\n" + "-"*80)
        print("🔋 BATTERY STORAGE ANALYSIS")
        print("-"*80)
        print(f"Total battery BMUs identified: {len(battery_df)}")
        print(f"Potential VLPs: {battery_df['potential_vlp'].sum()}")
        
        print(f"\n📊 Battery Types:")
        type_counts = battery_df['battery_type'].value_counts()
        for btype, count in type_counts.items():
            print(f"   {btype}: {count}")
        
        print(f"\n🏆 Top 10 Most Active Battery BMUs:")
        top10 = battery_df.nlargest(10, 'total_periods')
        for idx, row in top10.iterrows():
            vlp_marker = " [VLP]" if row['potential_vlp'] else ""
            print(f"   {row['bmUnit']}{vlp_marker}")
            print(f"      Periods: {row['total_periods']:,} | Days: {row['active_days']} | Avg Change: {row['avg_level_change_mw']:.1f}MW | Avg Bid: £{row['avg_bid_price']:.1f} | Avg Offer: £{row['avg_offer_price']:.1f}")
        
        print(f"\n🏢 Virtual Lead Party (VLP) Batteries:")
        vlp_batteries = battery_df[battery_df['potential_vlp'] == True].sort_values('total_periods', ascending=False)
        if len(vlp_batteries) > 0:
            print(f"   Found {len(vlp_batteries)} potential VLP battery units")
            print(f"\n   Top VLP Batteries:")
            for idx, row in vlp_batteries.head(15).iterrows():
                print(f"   {row['bmUnit']}")
                print(f"      Periods: {row['total_periods']:,} | Days: {row['active_days']} | Type: {row['battery_type']}")
        else:
            print("   No BMUs with VLP name patterns found")
            print("   (This doesn't mean VLPs don't exist - they may use standard BMU names)")
        
        # Stats
        print(f"\n📊 Market Statistics:")
        print(f"   Total settlement periods (all batteries): {battery_df['total_periods'].sum():,}")
        print(f"   Average periods per battery: {battery_df['total_periods'].mean():.0f}")
        print(f"   Average level change: {battery_df['avg_level_change_mw'].mean():.1f} MW")
        print(f"   Average bid price: £{battery_df['avg_bid_price'].mean():.2f}/MWh")
        print(f"   Average offer price: £{battery_df['avg_offer_price'].mean():.2f}/MWh")
    else:
        print("\n⚠️ No battery BMUs found in BOD data")
    
    print("\n" + "="*80)
    print("\n💡 KEY INSIGHTS:")
    print("-"*80)
    print("• Battery BMUs are identified by keywords in their ID (BESS, STOR, BTRY, ESS)")
    print("• VLPs may use standard BMU names without 'virtual' or 'aggregate' keywords")
    print("• To definitively identify VLPs, cross-reference with:")
    print("  - NESO generator register (All_Generators.xlsx)")
    print("  - REMIT messages for specific assets")
    print("  - Lead party information from settlement data")
    print("• Many VLPs operate under single BMU IDs that aggregate multiple sites")
    
    print("\n" + "="*80)

def main():
    """Main execution"""
    print("🚀 GB Battery & VLP Market Analysis")
    print("="*80)
    print("Analyzing Balancing Mechanism (BOD) data for battery storage")
    print("and Virtual Lead Party (VLP) participation")
    print("="*80)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # Step 1: Get market overview
    print("\n📊 STEP 1: Market Overview")
    print("-"*80)
    summary_df = analyze_bod_all_units()
    
    # Step 2: Identify batteries
    print("\n🔋 STEP 2: Identify Battery BMUs")
    print("-"*80)
    battery_df = analyze_bod_for_batteries()
    
    # Step 3: Try to get REMIT data (if available)
    print("\n📥 STEP 3: Download REMIT Data (Optional)")
    print("-"*80)
    remit_messages = download_remit_search(days_back=30)
    
    # Step 4: Export
    print("\n💾 STEP 4: Export Results")
    print("-"*80)
    export_results(battery_df, timestamp)
    
    # Step 5: Report
    print("\n📊 STEP 5: Generate Report")
    print("-"*80)
    generate_report(battery_df, summary_df)
    
    print("\n✅ Analysis Complete!")
    print("="*80)
    
    return battery_df, summary_df

if __name__ == '__main__':
    battery_results, summary = main()

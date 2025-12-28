#!/usr/bin/env python3
"""
Download REMIT Dataset and Analyze Virtual Lead Parties (VLPs)

This script:
1. Downloads REMIT asset registry from ELEXON API
2. Identifies Virtual Lead Parties (VLPs) by keywords
3. Cross-references with BOD data to analyze market participation
4. Exports results to CSV and loads to BigQuery
"""

import requests
import json
from datetime import datetime, timedelta
from google.cloud import bigquery
import pandas as pd
import logging
import sys

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)

# Configuration
BMRS_API = 'https://data.elexon.co.uk/bmrs/api/v1'
PROJECT = 'inner-cinema-476211-u9'
DATASET = 'uk_energy_prod'

# VLP keywords to search for
VLP_KEYWORDS = [
    'virtual',
    'aggregat',  # catches aggregate, aggregation, aggregated
    'portfolio',
    'vlp',
    'multi-site',
    'multi site',
    'aggregator',
    'flex',
    'flexibility'
]

def download_remit_messages(days_back=90):
    """
    Download REMIT messages from ELEXON API
    
    Args:
        days_back: Number of days of historical data to retrieve
    
    Returns:
        List of REMIT message dictionaries
    """
    logging.info(f"📥 Downloading REMIT messages (last {days_back} days)...")
    
    endpoint = f"{BMRS_API}/remit/list/by-publish"
    
    # Calculate date range
    to_date = datetime.now()
    from_date = to_date - timedelta(days=days_back)
    
    params = {
        'publishDateTimeFrom': from_date.strftime('%Y-%m-%dT%H:%M:%SZ'),
        'publishDateTimeTo': to_date.strftime('%Y-%m-%dT%H:%M:%SZ'),
        'format': 'json'
    }
    
    all_messages = []
    
    try:
        response = requests.get(endpoint, params=params, timeout=120)
        response.raise_for_status()
        data = response.json()
        
        if 'data' in data:
            all_messages = data['data']
            logging.info(f"✅ Downloaded {len(all_messages)} REMIT messages")
        else:
            logging.warning(f"⚠️ No 'data' key in response: {list(data.keys())}")
            
    except Exception as e:
        logging.error(f"❌ Error downloading REMIT messages: {e}")
        
        # Try alternative endpoint
        logging.info("🔄 Trying alternative endpoint: /datasets/REMIT...")
        try:
            alt_endpoint = f"{BMRS_API}/datasets/REMIT"
            alt_params = {
                'publishDateTimeFrom': from_date.strftime('%Y-%m-%d'),
                'publishDateTimeTo': to_date.strftime('%Y-%m-%d'),
                'format': 'json'
            }
            response = requests.get(alt_endpoint, params=alt_params, timeout=120)
            response.raise_for_status()
            data = response.json()
            
            if 'data' in data:
                all_messages = data['data']
                logging.info(f"✅ Downloaded {len(all_messages)} REMIT messages (alt endpoint)")
        except Exception as e2:
            logging.error(f"❌ Alternative endpoint also failed: {e2}")
    
    return all_messages

def download_remit_assets():
    """
    Download REMIT asset registry
    
    Returns:
        List of asset dictionaries
    """
    logging.info("📥 Downloading REMIT asset registry...")
    
    endpoint = f"{BMRS_API}/reference/remit/assets/all"
    
    try:
        response = requests.get(endpoint, timeout=60)
        response.raise_for_status()
        data = response.json()
        
        # Handle direct list response or data wrapper
        if isinstance(data, list):
            assets = data
            logging.info(f"✅ Downloaded {len(assets)} REMIT assets")
            return assets
        elif 'data' in data:
            assets = data['data']
            logging.info(f"✅ Downloaded {len(assets)} REMIT assets")
            return assets
        else:
            logging.warning(f"⚠️ Unexpected response format: {type(data)}")
            return []
            
    except Exception as e:
        logging.error(f"❌ Error downloading REMIT assets: {e}")
        return []

def download_remit_participants():
    """
    Download REMIT participant registry
    
    Returns:
        List of participant dictionaries
    """
    logging.info("📥 Downloading REMIT participants...")
    
    endpoint = f"{BMRS_API}/reference/remit/participants/all"
    
    try:
        response = requests.get(endpoint, timeout=60)
        response.raise_for_status()
        data = response.json()
        
        # Handle direct list response or data wrapper
        if isinstance(data, list):
            participants = data
            logging.info(f"✅ Downloaded {len(participants)} REMIT participants")
            return participants
        elif 'data' in data:
            participants = data['data']
            logging.info(f"✅ Downloaded {len(participants)} REMIT participants")
            return participants
        else:
            logging.warning(f"⚠️ Unexpected response format: {type(data)}")
            return []
            
    except Exception as e:
        logging.error(f"❌ Error downloading REMIT participants: {e}")
        return []

def identify_vlps(messages):
    """
    Identify potential VLPs from REMIT messages
    
    Args:
        messages: List of REMIT message dictionaries
    
    Returns:
        DataFrame of potential VLPs
    """
    logging.info("🔍 Identifying Virtual Lead Parties (VLPs)...")
    
    vlp_records = []
    
    for msg in messages:
        # Extract key fields
        asset_name = str(msg.get('affectedAssetName', '')).lower()
        asset_id = msg.get('affectedAsset', '')
        participant = msg.get('participant', '')
        fuel_type = msg.get('fuelType', '')
        installed_capacity = msg.get('installedCapacity', 0)
        unavailable_capacity = msg.get('unavailableCapacity', 0)
        
        # Check if any VLP keyword appears in asset name
        is_vlp = any(keyword in asset_name for keyword in VLP_KEYWORDS)
        
        if is_vlp:
            vlp_records.append({
                'asset_id': asset_id,
                'asset_name': msg.get('affectedAssetName', ''),
                'participant': participant,
                'fuel_type': fuel_type,
                'installed_capacity_mw': installed_capacity,
                'unavailable_capacity_mw': unavailable_capacity,
                'message_type': msg.get('messageType', ''),
                'event_start': msg.get('eventStart', ''),
                'event_end': msg.get('eventEnd', ''),
                'publish_time': msg.get('publishTime', ''),
                'matched_keywords': ', '.join([kw for kw in VLP_KEYWORDS if kw in asset_name])
            })
    
    df = pd.DataFrame(vlp_records)
    
    if len(df) > 0:
        # Remove duplicates based on asset_id
        df = df.drop_duplicates(subset=['asset_id'], keep='first')
        logging.info(f"✅ Identified {len(df)} potential VLPs")
    else:
        logging.warning("⚠️ No VLPs found in REMIT data")
    
    return df

def load_to_bigquery(df, table_name):
    """
    Load DataFrame to BigQuery
    
    Args:
        df: pandas DataFrame
        table_name: Target table name (without project/dataset prefix)
    """
    if len(df) == 0:
        logging.warning(f"⚠️ No data to load to {table_name}")
        return
    
    logging.info(f"📤 Loading {len(df)} rows to BigQuery table: {table_name}...")
    
    client = bigquery.Client(project=PROJECT)
    table_id = f"{PROJECT}.{DATASET}.{table_name}"
    
    # Configure load job
    job_config = bigquery.LoadJobConfig(
        write_disposition='WRITE_TRUNCATE',  # Replace existing data
        autodetect=True
    )
    
    try:
        job = client.load_table_from_dataframe(df, table_id, job_config=job_config)
        job.result()  # Wait for completion
        
        logging.info(f"✅ Loaded {len(df)} rows to {table_id}")
        
        # Show table info
        table = client.get_table(table_id)
        logging.info(f"   Table now has {table.num_rows} rows")
        
    except Exception as e:
        logging.error(f"❌ Error loading to BigQuery: {e}")

def cross_reference_with_bod(vlp_df):
    """
    Cross-reference VLP asset IDs with BOD (Bid-Offer Data) to see market participation
    
    Args:
        vlp_df: DataFrame of VLPs
    
    Returns:
        DataFrame with BOD statistics for each VLP
    """
    if len(vlp_df) == 0:
        logging.warning("⚠️ No VLPs to cross-reference")
        return pd.DataFrame()
    
    logging.info("🔗 Cross-referencing VLPs with BOD data...")
    
    try:
        client = bigquery.Client(project=PROJECT)
    except Exception as e:
        logging.warning(f"⚠️ Cannot connect to BigQuery: {e}")
        logging.info("   Skipping BOD cross-reference...")
        vlp_df['active_in_balancing_market'] = False
        return vlp_df
    
    # Get list of VLP asset IDs
    vlp_ids = vlp_df['asset_id'].dropna().unique().tolist()
    
    if len(vlp_ids) == 0:
        logging.warning("⚠️ No valid asset IDs to query")
        return pd.DataFrame()
    
    # Create comma-separated list for SQL IN clause
    vlp_ids_str = "', '".join(vlp_ids)
    
    query = f"""
    WITH vlp_bods AS (
      SELECT 
        bmUnitId,
        COUNT(*) as num_periods,
        COUNT(DISTINCT settlementDate) as num_days,
        MIN(settlementDate) as first_active_date,
        MAX(settlementDate) as last_active_date,
        AVG(CASE WHEN bidPrice > 0 THEN bidPrice END) as avg_bid_price,
        AVG(CASE WHEN offerPrice > 0 THEN offerPrice END) as avg_offer_price,
        AVG(CASE WHEN bidVolume > 0 THEN bidVolume END) as avg_bid_volume_mw,
        AVG(CASE WHEN offerVolume > 0 THEN offerVolume END) as avg_offer_volume_mw,
        SUM(bidVolume) as total_bid_volume_mw,
        SUM(offerVolume) as total_offer_volume_mw
      FROM `{PROJECT}.{DATASET}.bmrs_bod`
      WHERE bmUnitId IN ('{vlp_ids_str}')
        AND settlementDate >= DATE_SUB(CURRENT_DATE(), INTERVAL 365 DAY)
      GROUP BY bmUnitId
    )
    
    SELECT * FROM vlp_bods
    ORDER BY num_periods DESC
    """
    
    try:
        logging.info(f"   Querying BOD data for {len(vlp_ids)} VLP asset IDs...")
        bod_df = client.query(query).to_dataframe()
        
        if len(bod_df) > 0:
            logging.info(f"✅ Found BOD data for {len(bod_df)} VLPs")
            
            # Merge with VLP info
            result = vlp_df.merge(
                bod_df, 
                left_on='asset_id', 
                right_on='bmUnitId', 
                how='left'
            )
            
            # Calculate participation rate
            result['active_in_balancing_market'] = result['num_periods'].notna()
            
            return result
        else:
            logging.warning("⚠️ No matching BOD data found for VLP asset IDs")
            vlp_df['active_in_balancing_market'] = False
            return vlp_df
            
    except Exception as e:
        logging.error(f"❌ Error querying BOD data: {e}")
        vlp_df['active_in_balancing_market'] = False
        return vlp_df

def analyze_battery_bmus():
    """
    Analyze battery BMUs from BOD data to identify potential VLPs
    
    Returns:
        DataFrame of battery BMUs
    """
    logging.info("🔋 Analyzing battery BMUs from BOD data...")
    
    try:
        client = bigquery.Client(project=PROJECT)
    except Exception as e:
        logging.warning(f"⚠️ Cannot connect to BigQuery: {e}")
        logging.info("   Continuing without BigQuery analysis...")
        return pd.DataFrame()
    
    query = f"""
    SELECT 
      bmUnitId,
      COUNT(*) as total_periods,
      COUNT(DISTINCT settlementDate) as active_days,
      MIN(settlementDate) as first_seen,
      MAX(settlementDate) as last_seen,
      AVG(CASE WHEN bidVolume > 0 THEN bidVolume END) as avg_bid_mw,
      AVG(CASE WHEN offerVolume > 0 THEN offerVolume END) as avg_offer_mw,
      AVG(bidPrice) as avg_bid_price,
      AVG(offerPrice) as avg_offer_price,
      -- Check if BMU name suggests it might be a VLP
      CASE 
        WHEN LOWER(bmUnitId) LIKE '%virtual%' THEN TRUE
        WHEN LOWER(bmUnitId) LIKE '%aggr%' THEN TRUE
        WHEN LOWER(bmUnitId) LIKE '%port%' THEN TRUE
        WHEN LOWER(bmUnitId) LIKE '%flex%' THEN TRUE
        ELSE FALSE
      END as potential_vlp
    FROM `{PROJECT}.{DATASET}.bmrs_bod`
    WHERE (
      bmUnitId LIKE '%BESS%' 
      OR bmUnitId LIKE '%STOR%'
      OR bmUnitId LIKE '%BTRY%'
      OR bmUnitId LIKE '%ENSO%'
    )
    AND settlementDate >= DATE_SUB(CURRENT_DATE(), INTERVAL 365 DAY)
    GROUP BY bmUnitId
    ORDER BY total_periods DESC
    LIMIT 500
    """
    
    try:
        df = client.query(query).to_dataframe()
        logging.info(f"✅ Found {len(df)} battery BMUs in BOD data")
        logging.info(f"   {df['potential_vlp'].sum()} identified as potential VLPs by name")
        return df
    except Exception as e:
        logging.error(f"❌ Error querying battery BMUs: {e}")
        return pd.DataFrame()

def generate_summary_report(vlp_df, battery_df):
    """
    Generate summary report of findings
    
    Args:
        vlp_df: DataFrame of VLPs from REMIT
        battery_df: DataFrame of battery BMUs from BOD
    """
    print("\n" + "="*80)
    print("📊 VIRTUAL LEAD PARTY (VLP) ANALYSIS REPORT")
    print("="*80)
    
    print(f"\n📅 Report Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    print("\n" + "-"*80)
    print("📋 REMIT DATA SUMMARY")
    print("-"*80)
    
    if len(vlp_df) > 0:
        print(f"Total VLPs identified from REMIT: {len(vlp_df)}")
        print(f"VLPs active in balancing market: {vlp_df['active_in_balancing_market'].sum()}")
        
        if 'installed_capacity_mw' in vlp_df.columns:
            total_capacity = vlp_df['installed_capacity_mw'].sum()
            print(f"Total installed capacity: {total_capacity:,.0f} MW")
        
        print("\n🔝 Top 10 VLPs by Installed Capacity:")
        top_vlps = vlp_df.nlargest(10, 'installed_capacity_mw')[
            ['asset_name', 'participant', 'installed_capacity_mw', 'fuel_type']
        ]
        print(top_vlps.to_string(index=False))
        
        if 'num_periods' in vlp_df.columns:
            active_vlps = vlp_df[vlp_df['num_periods'].notna()].nlargest(10, 'num_periods')
            if len(active_vlps) > 0:
                print("\n📈 Top 10 Most Active VLPs in Balancing Market:")
                print(active_vlps[[
                    'asset_name', 'num_periods', 'num_days', 
                    'avg_bid_price', 'avg_offer_price'
                ]].to_string(index=False))
    else:
        print("⚠️ No VLPs found in REMIT data")
    
    print("\n" + "-"*80)
    print("🔋 BATTERY BMU ANALYSIS")
    print("-"*80)
    
    if len(battery_df) > 0:
        print(f"Total battery BMUs found: {len(battery_df)}")
        print(f"Potential VLPs by name: {battery_df['potential_vlp'].sum()}")
        
        print("\n🔝 Top 10 Most Active Battery BMUs:")
        top_batteries = battery_df.head(10)[
            ['bmUnitId', 'total_periods', 'active_days', 'avg_bid_mw', 'avg_offer_mw', 'potential_vlp']
        ]
        print(top_batteries.to_string(index=False))
        
        print("\n🏢 Battery BMUs Likely to be VLPs:")
        vlp_batteries = battery_df[battery_df['potential_vlp'] == True].head(20)
        if len(vlp_batteries) > 0:
            print(vlp_batteries[
                ['bmUnitId', 'total_periods', 'avg_bid_mw', 'avg_offer_mw']
            ].to_string(index=False))
        else:
            print("   None identified by name pattern")
    else:
        print("⚠️ No battery BMUs found in BOD data")
    
    print("\n" + "="*80)

def main():
    """Main execution function"""
    print("⚡ Starting VLP Analysis Pipeline")
    print("="*80)
    
    # Step 1: Download REMIT data
    print("\n📥 STEP 1: Download REMIT Data")
    print("-"*80)
    
    remit_messages = download_remit_messages(days_back=90)
    remit_assets = download_remit_assets()
    remit_participants = download_remit_participants()
    
    # Step 2: Identify VLPs from REMIT
    print("\n🔍 STEP 2: Identify VLPs")
    print("-"*80)
    
    vlp_df = identify_vlps(remit_messages)
    
    # Step 3: Cross-reference with BOD
    print("\n🔗 STEP 3: Cross-reference with BOD Data")
    print("-"*80)
    
    vlp_with_bod = cross_reference_with_bod(vlp_df)
    
    # Step 4: Analyze battery BMUs
    print("\n🔋 STEP 4: Analyze Battery BMUs")
    print("-"*80)
    
    battery_df = analyze_battery_bmus()
    
    # Step 5: Export results
    print("\n💾 STEP 5: Export Results")
    print("-"*80)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # Export VLPs
    if len(vlp_with_bod) > 0:
        vlp_file = f'vlp_analysis_{timestamp}.csv'
        vlp_with_bod.to_csv(vlp_file, index=False)
        logging.info(f"✅ Exported VLP analysis to: {vlp_file}")
        
        # Load to BigQuery
        load_to_bigquery(vlp_with_bod, 'vlp_analysis')
    
    # Export battery BMUs
    if len(battery_df) > 0:
        battery_file = f'battery_bmus_{timestamp}.csv'
        battery_df.to_csv(battery_file, index=False)
        logging.info(f"✅ Exported battery BMU analysis to: {battery_file}")
        
        # Load to BigQuery
        load_to_bigquery(battery_df, 'battery_bmu_analysis')
    
    # Export raw REMIT data if available
    if len(remit_messages) > 0:
        remit_df = pd.DataFrame(remit_messages)
        remit_file = f'remit_messages_{timestamp}.csv'
        remit_df.to_csv(remit_file, index=False)
        logging.info(f"✅ Exported REMIT messages to: {remit_file}")
        
        # Load to BigQuery
        load_to_bigquery(remit_df, 'remit_messages')
    
    # Step 6: Generate summary report
    print("\n📊 STEP 6: Generate Summary Report")
    print("-"*80)
    
    generate_summary_report(vlp_with_bod, battery_df)
    
    print("\n✅ VLP Analysis Complete!")
    print("="*80)
    
    return vlp_with_bod, battery_df

if __name__ == '__main__':
    vlp_results, battery_results = main()

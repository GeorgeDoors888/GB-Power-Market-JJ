#!/usr/bin/env python3
"""
BMU Metadata Ingestion
Fetches BMU reference data from Elexon API and stores in BigQuery.

Purpose: Enable technology-based analysis (BESS, wind, solar, gas, etc.)
API: https://data.elexon.co.uk/bmrs/api/v1/reference/bmunits/all
Table: inner-cinema-476211-u9.uk_energy_prod.bmu_metadata

Author: George Major
Date: December 14, 2025
"""

import requests
import pandas as pd
from google.cloud import bigquery
from datetime import datetime
import logging

# Configuration
PROJECT_ID = "inner-cinema-476211-u9"
DATASET = "uk_energy_prod"
TABLE = "bmu_metadata"
API_URL = "https://data.elexon.co.uk/bmrs/api/v1/reference/bmunits/all"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(message)s'
)

def fetch_bmu_metadata():
    """Fetch all BMU units from Elexon API."""
    logging.info(f"Fetching BMU metadata from {API_URL}...")
    
    try:
        response = requests.get(API_URL, timeout=60)
        response.raise_for_status()
        data = response.json()
        
        # Handle both direct list and {'data': [...]} formats
        if isinstance(data, list):
            bmus = data
        elif isinstance(data, dict) and 'data' in data:
            bmus = data['data']
        else:
            logging.error(f"Unexpected API response format")
            return None
        
        logging.info(f"✅ Fetched {len(bmus)} BMU records")
        return bmus
        
    except Exception as e:
        logging.error(f"❌ Failed to fetch BMU metadata: {e}")
        return None

def transform_bmu_data(bmus):
    """Transform BMU data and add technology classification."""
    
    records = []
    for bmu in bmus:
        # Extract key fields
        record = {
            'nationalGridBmUnit': bmu.get('nationalGridBmUnit'),
            'bmUnitId': bmu.get('bmUnitId'),
            'bmUnitType': bmu.get('bmUnitType'),
            'leadPartyName': bmu.get('leadPartyName'),
            'fuelType': bmu.get('fuelType'),
            'powerStationType': bmu.get('powerStationType'),
            'registeredCapacity': bmu.get('registeredCapacity'),
            'gspGroup': bmu.get('gspGroup'),
            'effectiveFrom': bmu.get('effectiveFrom'),
            'effectiveTo': bmu.get('effectiveTo'),
        }
        
        # Add technology classification
        fuel = (record['fuelType'] or '').lower()
        pst = (record['powerStationType'] or '').lower()
        bmu_type = (record['bmUnitType'] or '').lower()
        
        if any(x in fuel for x in ['battery', 'bess', 'storage']) or 'battery' in pst:
            tech = 'BESS'
        elif any(x in fuel for x in ['wind', 'offshore', 'onshore']):
            tech = 'Wind'
        elif 'solar' in fuel or 'pv' in fuel or 'photovoltaic' in pst:
            tech = 'Solar'
        elif any(x in fuel for x in ['demand', 'dsr']) or 'demand' in bmu_type:
            tech = 'Demand'
        elif any(x in fuel for x in ['gas', 'ccgt', 'ocgt']):
            tech = 'Gas'
        elif 'coal' in fuel:
            tech = 'Coal'
        elif 'biomass' in fuel:
            tech = 'Biomass'
        elif 'nuclear' in fuel:
            tech = 'Nuclear'
        elif 'hydro' in fuel:
            tech = 'Hydro'
        elif 'interconnector' in fuel or 'interconnector' in pst:
            tech = 'Interconnector'
        else:
            tech = 'Other'
        
        record['technology'] = tech
        record['_ingested_utc'] = datetime.utcnow().isoformat()
        
        records.append(record)
    
    df = pd.DataFrame(records)
    logging.info(f"📊 Transformed {len(df)} records")
    
    # Technology breakdown
    tech_counts = df['technology'].value_counts()
    logging.info(f"\n📋 Technology Breakdown:")
    for tech, count in tech_counts.items():
        logging.info(f"   {tech}: {count}")
    
    return df

def upload_to_bigquery(df):
    """Upload BMU metadata to BigQuery."""
    
    client = bigquery.Client(project=PROJECT_ID, location="US")
    table_id = f"{PROJECT_ID}.{DATASET}.{TABLE}"
    
    # Define schema
    schema = [
        bigquery.SchemaField("nationalGridBmUnit", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("bmUnitId", "INTEGER", mode="NULLABLE"),
        bigquery.SchemaField("bmUnitType", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("leadPartyName", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("fuelType", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("powerStationType", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("registeredCapacity", "FLOAT64", mode="NULLABLE"),
        bigquery.SchemaField("gspGroup", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("effectiveFrom", "DATETIME", mode="NULLABLE"),
        bigquery.SchemaField("effectiveTo", "DATETIME", mode="NULLABLE"),
        bigquery.SchemaField("technology", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("_ingested_utc", "STRING", mode="NULLABLE"),
    ]
    
    # Create or replace table
    job_config = bigquery.LoadJobConfig(
        schema=schema,
        write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,  # Replace existing
    )
    
    logging.info(f"Uploading to {table_id}...")
    job = client.load_table_from_dataframe(df, table_id, job_config=job_config)
    job.result()  # Wait for completion
    
    # Verify
    table = client.get_table(table_id)
    logging.info(f"✅ Uploaded {table.num_rows:,} rows to {table_id}")
    
    return table_id

def create_summary_stats(table_id):
    """Generate summary statistics."""
    
    client = bigquery.Client(project=PROJECT_ID, location="US")
    
    query = f"""
    SELECT 
        technology,
        COUNT(*) as bmu_count,
        COUNT(CASE WHEN effectiveTo IS NULL THEN 1 END) as active_count,
        SUM(registeredCapacity) as total_capacity_mw,
        AVG(registeredCapacity) as avg_capacity_mw
    FROM `{table_id}`
    GROUP BY technology
    ORDER BY bmu_count DESC
    """
    
    print("\n" + "=" * 80)
    print("BMU METADATA SUMMARY")
    print("=" * 80)
    print(f"{'Technology':<20} {'Total':<10} {'Active':<10} {'Capacity MW':<15} {'Avg MW':<10}")
    print("=" * 80)
    
    for row in client.query(query).result():
        print(f"{row.technology:<20} {row.bmu_count:<10} {row.active_count:<10} "
              f"{row.total_capacity_mw or 0:<15,.0f} {row.avg_capacity_mw or 0:<10,.1f}")
    
    print("=" * 80)

def main():
    """Main execution."""
    
    print("=" * 80)
    print("🔧 BMU METADATA INGESTION")
    print("=" * 80)
    
    # Step 1: Fetch data
    bmus = fetch_bmu_metadata()
    if not bmus:
        logging.error("❌ Failed to fetch BMU data - exiting")
        return 1
    
    # Step 2: Transform
    df = transform_bmu_data(bmus)
    
    # Step 3: Upload
    table_id = upload_to_bigquery(df)
    
    # Step 4: Summary
    create_summary_stats(table_id)
    
    print("\n" + "=" * 80)
    print("✅ BMU METADATA INGESTION COMPLETE")
    print("=" * 80)
    print(f"Table: {table_id}")
    print(f"Records: {len(df):,}")
    print(f"Usage: JOIN on nationalGridBmUnit for technology classification")
    print("=" * 80)
    
    return 0

if __name__ == "__main__":
    exit(main())

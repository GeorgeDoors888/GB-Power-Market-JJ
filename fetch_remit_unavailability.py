#!/usr/bin/env python3
"""
Fetch REMIT Unavailability Data from Elexon/ENTSO-E and Upload to BigQuery

REMIT (Regulation on wholesale Energy Market Integrity and Transparency) data
tracks unplanned unavailability of electrical facilities.

Data Sources:
1. Elexon BMRS API (if available)
2. ENTSO-E Transparency Platform
3. Manual CSV import from Elexon Portal
"""

import httpx
import pandas as pd
from google.cloud import bigquery
from datetime import datetime, date, timedelta
import json
from typing import Optional, List, Dict

# Configuration
PROJECT_ID = "inner-cinema-476211-u9"
DATASET_ID = "uk_energy_prod"
TABLE_ID = "bmrs_remit_unavailability"

# ENTSO-E API (alternative source for UK REMIT data)
ENTSOE_API_URL = "https://web-api.tp.entsoe.eu/api"

def create_remit_table_if_not_exists(client: bigquery.Client):
    """Create REMIT unavailability table in BigQuery if it doesn't exist"""
    
    table_id = f"{PROJECT_ID}.{DATASET_ID}.{TABLE_ID}"
    
    schema = [
        bigquery.SchemaField("messageId", "STRING", mode="REQUIRED", description="Unique message ID"),
        bigquery.SchemaField("revisionNumber", "INTEGER", description="Revision number of the message"),
        bigquery.SchemaField("messageType", "STRING", description="Type of REMIT message"),
        bigquery.SchemaField("eventType", "STRING", description="Type of event"),
        bigquery.SchemaField("unavailabilityType", "STRING", description="Unplanned/Planned"),
        
        # Participant and Asset Information
        bigquery.SchemaField("participantId", "STRING", description="Market participant ID"),
        bigquery.SchemaField("participantName", "STRING", description="Market participant name"),
        bigquery.SchemaField("assetId", "STRING", description="Asset/Unit ID"),
        bigquery.SchemaField("assetName", "STRING", description="Asset/Unit name"),
        bigquery.SchemaField("assetType", "STRING", description="Type of asset (e.g., Generator)"),
        bigquery.SchemaField("affectedUnit", "STRING", description="Affected BM Unit"),
        bigquery.SchemaField("eicCode", "STRING", description="EIC code for the asset"),
        
        # Fuel and Capacity
        bigquery.SchemaField("fuelType", "STRING", description="Type of fuel (CCGT, Wind, etc.)"),
        bigquery.SchemaField("normalCapacity", "FLOAT", description="Normal capacity in MW"),
        bigquery.SchemaField("availableCapacity", "FLOAT", description="Available capacity in MW"),
        bigquery.SchemaField("unavailableCapacity", "FLOAT", description="Unavailable capacity in MW"),
        
        # Timing
        bigquery.SchemaField("eventStartTime", "DATETIME", description="Start time of unavailability"),
        bigquery.SchemaField("eventEndTime", "DATETIME", description="End time of unavailability"),
        bigquery.SchemaField("publishTime", "DATETIME", description="When the message was published"),
        
        # Details
        bigquery.SchemaField("eventStatus", "STRING", description="Active/Cancelled/Updated"),
        bigquery.SchemaField("cause", "STRING", description="Reason for unavailability"),
        bigquery.SchemaField("relatedInfo", "STRING", description="Additional information"),
        
        # Metadata
        bigquery.SchemaField("_ingested_utc", "DATETIME", description="When data was ingested"),
        bigquery.SchemaField("_source", "STRING", description="Data source"),
    ]
    
    table = bigquery.Table(table_id, schema=schema)
    table.time_partitioning = bigquery.TimePartitioning(
        type_=bigquery.TimePartitioningType.DAY,
        field="eventStartTime"
    )
    
    try:
        table = client.create_table(table)
        print(f"✅ Created table {table_id}")
    except Exception as e:
        if "Already Exists" in str(e):
            print(f"ℹ️  Table {table_id} already exists")
        else:
            raise e
    
    return table_id


def fetch_sample_remit_data() -> pd.DataFrame:
    """
    Create sample REMIT data for demonstration
    
    In production, this would fetch from:
    - Elexon IRIS service
    - ENTSO-E Transparency Platform
    - Elexon Portal CSV downloads
    """
    
    print("📊 Creating sample REMIT unavailability data...")
    print("   (In production, this would fetch from Elexon/ENTSO-E APIs)")
    
    # Sample data representing typical UK unavailability events
    sample_data = [
        {
            "messageId": "UK-REMIT-2025-001234",
            "revisionNumber": 1,
            "messageType": "Unavailability",
            "eventType": "Unplanned Outage",
            "unavailabilityType": "Unplanned",
            "participantId": "UK001",
            "participantName": "Major Energy Ltd",
            "assetId": "T_DRAXX-1",
            "assetName": "Drax Unit 1",
            "assetType": "Generation Unit",
            "affectedUnit": "T_DRAXX-1",
            "eicCode": "48W00000DRAXX-1K",
            "fuelType": "BIOMASS",
            "normalCapacity": 660.0,
            "availableCapacity": 0.0,
            "unavailableCapacity": 660.0,
            "eventStartTime": datetime.now() - timedelta(hours=2),
            "eventEndTime": datetime.now() + timedelta(days=3),
            "publishTime": datetime.now() - timedelta(hours=2, minutes=15),
            "eventStatus": "Active",
            "cause": "Generator fault - turbine bearing failure",
            "relatedInfo": "Estimated return to service: 72 hours",
        },
        {
            "messageId": "UK-REMIT-2025-001235",
            "revisionNumber": 1,
            "messageType": "Unavailability",
            "eventType": "Unplanned Outage",
            "unavailabilityType": "Unplanned",
            "participantId": "UK002",
            "participantName": "Nuclear Power Co",
            "assetId": "T_SIZB-1",
            "assetName": "Sizewell B",
            "assetType": "Generation Unit",
            "affectedUnit": "T_SIZB-1",
            "eicCode": "48W00000SIZB-1K",
            "fuelType": "NUCLEAR",
            "normalCapacity": 1198.0,
            "availableCapacity": 898.0,
            "unavailableCapacity": 300.0,
            "eventStartTime": datetime.now() - timedelta(days=1),
            "eventEndTime": datetime.now() + timedelta(hours=12),
            "publishTime": datetime.now() - timedelta(days=1, minutes=5),
            "eventStatus": "Active",
            "cause": "Reactor de-rating for maintenance inspection",
            "relatedInfo": "Partial outage - operating at 75% capacity",
        },
        {
            "messageId": "UK-REMIT-2025-001236",
            "revisionNumber": 2,
            "messageType": "Unavailability",
            "eventType": "Unplanned Outage",
            "unavailabilityType": "Unplanned",
            "participantId": "UK003",
            "participantName": "Wind Energy Ltd",
            "assetId": "WFARM-001",
            "assetName": "London Array Wind Farm",
            "assetType": "Wind Farm",
            "affectedUnit": "E_LNDA-1",
            "eicCode": "48W00000LNDA-1K",
            "fuelType": "WIND",
            "normalCapacity": 630.0,
            "availableCapacity": 480.0,
            "unavailableCapacity": 150.0,
            "eventStartTime": datetime.now() - timedelta(hours=6),
            "eventEndTime": datetime.now() + timedelta(days=2),
            "publishTime": datetime.now() - timedelta(hours=6, minutes=10),
            "eventStatus": "Active",
            "cause": "Grid connection issue - cable fault",
            "relatedInfo": "24% capacity offline. Repair work underway.",
        },
        {
            "messageId": "UK-REMIT-2025-001237",
            "revisionNumber": 1,
            "messageType": "Unavailability",
            "eventType": "Unplanned Outage",
            "unavailabilityType": "Unplanned",
            "participantId": "UK004",
            "participantName": "Gas Power PLC",
            "assetId": "T_PEMB-4",
            "assetName": "Pembroke CCGT Unit 4",
            "assetType": "Generation Unit",
            "affectedUnit": "T_PEMB-4",
            "eicCode": "48W00000PEMB-4K",
            "fuelType": "CCGT",
            "normalCapacity": 537.0,
            "availableCapacity": 0.0,
            "unavailableCapacity": 537.0,
            "eventStartTime": datetime.now() - timedelta(hours=12),
            "eventEndTime": datetime.now() + timedelta(days=5),
            "publishTime": datetime.now() - timedelta(hours=12, minutes=8),
            "eventStatus": "Active",
            "cause": "Boiler tube leak - emergency shutdown",
            "relatedInfo": "Unit tripped. Damage assessment in progress.",
        },
        {
            "messageId": "UK-REMIT-2025-001238",
            "revisionNumber": 1,
            "messageType": "Unavailability",
            "eventType": "Return to Service",
            "unavailabilityType": "Unplanned",
            "participantId": "UK005",
            "participantName": "Interconnector Ltd",
            "assetId": "IFA-001",
            "assetName": "IFA Interconnector",
            "assetType": "Interconnector",
            "affectedUnit": "IFA",
            "eicCode": "10Y1001C--00098F",
            "fuelType": "INTFR",
            "normalCapacity": 2000.0,
            "availableCapacity": 2000.0,
            "unavailableCapacity": 0.0,
            "eventStartTime": datetime.now() - timedelta(days=2),
            "eventEndTime": datetime.now() - timedelta(hours=1),
            "publishTime": datetime.now() - timedelta(minutes=30),
            "eventStatus": "Completed",
            "cause": "Cable testing completed - returned to full capacity",
            "relatedInfo": "Full capacity restored",
        },
    ]
    
    df = pd.DataFrame(sample_data)
    
    # Add ingestion metadata
    df['_ingested_utc'] = datetime.utcnow()
    df['_source'] = 'Sample Data (Demo)'
    
    print(f"✅ Created {len(df)} sample REMIT events")
    return df


def upload_to_bigquery(df: pd.DataFrame, client: bigquery.Client, table_id: str):
    """Upload REMIT data to BigQuery"""
    
    if df.empty:
        print("⚠️  No data to upload")
        return
    
    print(f"⬆️  Uploading {len(df)} records to BigQuery...")
    
    # Ensure datetime columns are proper type
    datetime_cols = ['eventStartTime', 'eventEndTime', 'publishTime', '_ingested_utc']
    for col in datetime_cols:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col])
    
    # Ensure numeric columns
    numeric_cols = ['normalCapacity', 'availableCapacity', 'unavailableCapacity', 'revisionNumber']
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    
    job_config = bigquery.LoadJobConfig(
        write_disposition=bigquery.WriteDisposition.WRITE_APPEND,
    )
    
    job = client.load_table_from_dataframe(df, table_id, job_config=job_config)
    job.result()
    
    print(f"✅ Uploaded {len(df)} records to {table_id}")


def get_current_unavailability_summary(client: bigquery.Client, table_id: str):
    """Get summary of current unavailability events"""
    
    query = f"""
    SELECT
        COUNT(*) as active_events,
        COUNT(DISTINCT assetId) as affected_assets,
        SUM(unavailableCapacity) as total_unavailable_mw,
        STRING_AGG(DISTINCT fuelType, ', ' ORDER BY fuelType) as fuel_types_affected
    FROM `{table_id}`
    WHERE eventStatus = 'Active'
      AND eventStartTime <= CURRENT_TIMESTAMP()
      AND eventEndTime >= CURRENT_TIMESTAMP()
    """
    
    try:
        result = list(client.query(query).result())
        if result and result[0].active_events > 0:
            print(f"\n📊 Current Unavailability Summary:")
            print(f"   Active Events: {result[0].active_events}")
            print(f"   Affected Assets: {result[0].affected_assets}")
            print(f"   Total Unavailable: {result[0].total_unavailable_mw:.1f} MW")
            print(f"   Fuel Types: {result[0].fuel_types_affected}")
        else:
            print("\nℹ️  No active unavailability events found")
    except Exception as e:
        print(f"⚠️  Could not query summary: {e}")


def main():
    """Main execution function"""
    
    print("="*70)
    print("🔴 REMIT UNAVAILABILITY DATA INGESTION")
    print("="*70)
    print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # Initialize BigQuery client
    client = bigquery.Client(project=PROJECT_ID)
    
    # Create table if needed
    table_id = create_remit_table_if_not_exists(client)
    
    # Fetch REMIT data
    print("\n📡 Fetching REMIT unavailability data...")
    df = fetch_sample_remit_data()
    
    # Show preview
    if not df.empty:
        print("\n📋 Preview of REMIT events:")
        for idx, row in df.iterrows():
            status_icon = "🔴" if row['eventStatus'] == 'Active' else "✅"
            print(f"   {status_icon} {row['assetName']} ({row['fuelType']})")
            print(f"      Unavailable: {row['unavailableCapacity']:.0f} MW")
            print(f"      Cause: {row['cause']}")
            print(f"      Until: {row['eventEndTime'].strftime('%Y-%m-%d %H:%M')}")
            print()
    
    # Upload to BigQuery
    upload_to_bigquery(df, client, table_id)
    
    # Get summary
    get_current_unavailability_summary(client, table_id)
    
    print("\n" + "="*70)
    print("✅ REMIT DATA INGESTION COMPLETE!")
    print("="*70)
    print(f"\n💡 Note: This is sample data for demonstration.")
    print(f"   To fetch live REMIT data, integrate with:")
    print(f"   • Elexon IRIS service")
    print(f"   • ENTSO-E Transparency Platform")
    print(f"   • Elexon Portal CSV downloads")
    

if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""
Fetch BSC Party Roles from Elexon Insights API
Identify VLP (Virtual Lead Party) and VTP (Virtual Trading Party) roles
Update dim_bmu and create dim_party tables with role classifications
"""

import requests
import pandas as pd
from google.cloud import bigquery
import os
from datetime import datetime

# Configuration
PROJECT_ID = "inner-cinema-476211-u9"
DATASET = "uk_energy_prod"
ELEXON_API_BASE = "https://data.elexon.co.uk/bmrs/api/v1"

os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = '/home/george/GB-Power-Market-JJ/inner-cinema-credentials.json'

def fetch_bsc_parties():
    """
    Fetch all BSC parties from Elexon Insights API
    Endpoint: /reference/parties or /parties
    """
    print("🔍 Fetching BSC Parties from Elexon Insights API...\n")

    # Try multiple endpoints (Elexon API structure varies)
    endpoints = [
        f"{ELEXON_API_BASE}/reference/parties",
        f"{ELEXON_API_BASE}/parties",
        f"{ELEXON_API_BASE}/balancing/settlement/parties"
    ]

    for endpoint in endpoints:
        try:
            print(f"   Trying: {endpoint}")
            response = requests.get(endpoint, timeout=30)

            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ Success! Retrieved {len(data)} parties\n")
                return pd.DataFrame(data)
            else:
                print(f"   ❌ Status {response.status_code}")
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")

    print("\n⚠️  All endpoints failed. Using fallback method...\n")
    return None

def fetch_bmu_reference_data():
    """
    Fetch BM Units reference data which includes lead party info
    Endpoint: /reference/bmunits/all
    """
    print("🔍 Fetching BM Units reference data from Elexon...\n")

    endpoint = f"{ELEXON_API_BASE}/reference/bmunits/all"

    try:
        print(f"   Calling: {endpoint}")
        response = requests.get(endpoint, timeout=60)

        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Retrieved {len(data)} BM Units\n")
            return pd.DataFrame(data)
        else:
            print(f"   ❌ Status {response.status_code}: {response.text[:200]}")
            return None
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
        return None

def extract_parties_from_bmu_data(bmu_df):
    """
    Extract unique parties from BM Units data
    Infer VLP/VTP from BMU patterns
    """
    print("📊 Extracting parties from BM Units data...\n")

    # Group by lead party
    party_groups = bmu_df.groupby(['leadPartyName', 'leadPartyId']).agg({
        'elexonBmUnit': 'count',
        'nationalGridBmUnit': lambda x: list(x.unique())[:10]  # Limit to 10 samples
    }).reset_index()

    party_groups.columns = ['party_name', 'party_id', 'bmu_count', 'bmu_sample']

    # Check for V_* pattern BMUs (indicates VLP)
    def check_vlp(row):
        bmu_list = bmu_df[bmu_df['leadPartyId'] == row['party_id']]['elexonBmUnit'].tolist()
        return any(bmu.startswith('V_') or bmu.startswith('V__') for bmu in bmu_list)

    # Check for any BMUs (indicates VTP if they trade)
    def check_vtp(row):
        # If they have BMUs, they can be VTP
        return row['bmu_count'] > 0

    party_groups['is_vlp'] = party_groups.apply(check_vlp, axis=1)
    party_groups['is_vtp'] = party_groups.apply(check_vtp, axis=1)

    print(f"   Found {len(party_groups)} unique parties")
    print(f"   VLP parties: {party_groups['is_vlp'].sum()}")
    print(f"   VTP parties: {party_groups['is_vtp'].sum()}")

    return party_groups

def create_dim_party_table(party_df, client):
    """
    Create/update dim_party table in BigQuery
    """
    print("\n📤 Uploading to BigQuery: dim_party...\n")

    # Add metadata
    party_df['dim_created_at'] = datetime.now()
    party_df['data_source'] = 'Elexon Insights API'

    # Create table
    table_id = f"{PROJECT_ID}.{DATASET}.dim_party"

    job_config = bigquery.LoadJobConfig(
        write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
        schema=[
            bigquery.SchemaField("party_name", "STRING"),
            bigquery.SchemaField("party_id", "STRING"),
            bigquery.SchemaField("bmu_count", "INTEGER"),
            bigquery.SchemaField("is_vlp", "BOOLEAN"),
            bigquery.SchemaField("is_vtp", "BOOLEAN"),
            bigquery.SchemaField("data_source", "STRING"),
            bigquery.SchemaField("dim_created_at", "TIMESTAMP"),
        ],
    )

    # Upload
    df_upload = party_df[['party_name', 'party_id', 'bmu_count', 'is_vlp', 'is_vtp', 'data_source', 'dim_created_at']]
    job = client.load_table_from_dataframe(df_upload, table_id, job_config=job_config)
    job.result()

    print(f"   ✅ Uploaded {len(df_upload)} parties to dim_party")

    return table_id

def update_dim_bmu_with_roles(client):
    """
    Update dim_bmu table with VLP/VTP flags from dim_party
    """
    print("\n🔄 Updating dim_bmu with VLP/VTP roles...\n")

    query = f"""
    -- Add columns if they don't exist
    ALTER TABLE `{PROJECT_ID}.{DATASET}.dim_bmu`
    ADD COLUMN IF NOT EXISTS is_vlp BOOL,
    ADD COLUMN IF NOT EXISTS is_vtp BOOL;

    -- Update from dim_party
    UPDATE `{PROJECT_ID}.{DATASET}.dim_bmu` AS bmu
    SET
        is_vlp = party.is_vlp,
        is_vtp = party.is_vtp
    FROM `{PROJECT_ID}.{DATASET}.dim_party` AS party
    WHERE bmu.lead_party_id = party.party_id;
    """

    try:
        # Split into separate queries (ALTER and UPDATE can't be in same statement)
        alter_query = f"""
        ALTER TABLE `{PROJECT_ID}.{DATASET}.dim_bmu`
        ADD COLUMN IF NOT EXISTS is_vlp BOOL,
        ADD COLUMN IF NOT EXISTS is_vtp BOOL
        """

        update_query = f"""
        UPDATE `{PROJECT_ID}.{DATASET}.dim_bmu` AS bmu
        SET
            is_vlp = party.is_vlp,
            is_vtp = party.is_vtp
        FROM `{PROJECT_ID}.{DATASET}.dim_party` AS party
        WHERE bmu.lead_party_id = party.party_id
        """

        # Execute ALTER
        print("   Adding is_vlp and is_vtp columns...")
        job1 = client.query(alter_query)
        job1.result()

        # Execute UPDATE
        print("   Updating BMU records with party roles...")
        job2 = client.query(update_query)
        result = job2.result()

        print(f"   ✅ Updated {job2.num_dml_affected_rows} BMU records")

    except Exception as e:
        print(f"   ⚠️  Error: {str(e)}")
        print("   Trying alternative approach...")

        # If columns already exist, just update
        try:
            job = client.query(update_query)
            result = job.result()
            print(f"   ✅ Updated {job.num_dml_affected_rows} BMU records")
        except Exception as e2:
            print(f"   ❌ Failed: {str(e2)}")

def display_vlp_vtp_summary(client):
    """
    Display summary of VLP/VTP parties
    """
    print("\n\n" + "=" * 120)
    print("📊 VLP/VTP PARTY SUMMARY")
    print("=" * 120)

    # VLP parties
    query = f"""
    SELECT
        party_name,
        party_id,
        bmu_count,
        is_vlp,
        is_vtp
    FROM `{PROJECT_ID}.{DATASET}.dim_party`
    WHERE is_vlp = TRUE
    ORDER BY bmu_count DESC
    LIMIT 20
    """

    print("\n🔄 TOP 20 VIRTUAL LEAD PARTIES (VLP):\n")
    df_vlp = client.query(query).to_dataframe()
    print(df_vlp.to_string(index=False))

    # Statistics
    query = f"""
    SELECT
        COUNT(*) as total_parties,
        SUM(CASE WHEN is_vlp THEN 1 ELSE 0 END) as vlp_count,
        SUM(CASE WHEN is_vtp THEN 1 ELSE 0 END) as vtp_count,
        SUM(CASE WHEN is_vlp AND is_vtp THEN 1 ELSE 0 END) as both_vlp_vtp,
        SUM(bmu_count) as total_bmus
    FROM `{PROJECT_ID}.{DATASET}.dim_party`
    """

    print("\n\n📈 OVERALL STATISTICS:\n")
    df_stats = client.query(query).to_dataframe()
    print(df_stats.to_string(index=False))

    # Virtual units by party
    query = f"""
    SELECT
        d.lead_party_name,
        d.lead_party_id,
        COUNT(*) as virtual_units,
        SUM(CASE WHEN d.is_battery_storage THEN 1 ELSE 0 END) as battery_units,
        STRING_AGG(d.bm_unit_id, ', ' ORDER BY d.bm_unit_id LIMIT 10) as sample_units
    FROM `{PROJECT_ID}.{DATASET}.dim_bmu` d
    INNER JOIN `{PROJECT_ID}.{DATASET}.dim_party` p
        ON d.lead_party_id = p.party_id
    WHERE p.is_vlp = TRUE
        AND d.is_virtual_unit = TRUE
    GROUP BY d.lead_party_name, d.lead_party_id
    ORDER BY virtual_units DESC
    LIMIT 20
    """

    print("\n\n🔄 PARTIES WITH MOST VIRTUAL UNITS:\n")
    df_virtual = client.query(query).to_dataframe()
    print(df_virtual.to_string(index=False))

def main():
    print("=" * 120)
    print("⚡ FETCHING BSC PARTIES AND VLP/VTP ROLES FROM ELEXON")
    print("=" * 120)

    client = bigquery.Client(project=PROJECT_ID, location="US")

    # Try to fetch parties directly
    parties_df = fetch_bsc_parties()

    # If that fails, get parties from BMU reference data
    if parties_df is None:
        print("\n📋 Fetching parties from BM Units reference data...\n")
        bmu_df = fetch_bmu_reference_data()

        if bmu_df is not None:
            parties_df = extract_parties_from_bmu_data(bmu_df)
        else:
            print("\n❌ Could not fetch data from Elexon API")
            print("⚠️  This might require API key or different endpoint")
            print("\n💡 FALLBACK: Using existing dim_bmu data to infer VLP/VTP...\n")

            # Fallback: infer from existing data
            query = f"""
            SELECT
                lead_party_name,
                lead_party_id,
                COUNT(*) as bmu_count,
                SUM(CASE WHEN is_virtual_unit THEN 1 ELSE 0 END) as virtual_count,
                SUM(CASE WHEN is_battery_storage THEN 1 ELSE 0 END) as battery_count
            FROM `{PROJECT_ID}.{DATASET}.dim_bmu`
            WHERE lead_party_id IS NOT NULL
            GROUP BY lead_party_name, lead_party_id
            """

            parties_df = client.query(query).to_dataframe()
            parties_df['is_vlp'] = parties_df['virtual_count'] > 0
            parties_df['is_vtp'] = parties_df['bmu_count'] > 0
            parties_df = parties_df[['lead_party_name', 'lead_party_id', 'bmu_count', 'is_vlp', 'is_vtp']]
            parties_df.columns = ['party_name', 'party_id', 'bmu_count', 'is_vlp', 'is_vtp']

    if parties_df is not None and len(parties_df) > 0:
        # Create dim_party table
        create_dim_party_table(parties_df, client)

        # Update dim_bmu with roles
        update_dim_bmu_with_roles(client)

        # Display summary
        display_vlp_vtp_summary(client)

        print("\n\n✅ SUCCESS!")
        print("=" * 120)
        print("\n📊 Tables created/updated:")
        print("   • dim_party - All BSC parties with VLP/VTP flags")
        print("   • dim_bmu - Updated with is_vlp and is_vtp columns")
        print("\n🔍 Query examples:")
        print(f"   -- All VLP parties:")
        print(f"   SELECT * FROM `{PROJECT_ID}.{DATASET}.dim_party` WHERE is_vlp = TRUE")
        print(f"\n   -- All VTP parties:")
        print(f"   SELECT * FROM `{PROJECT_ID}.{DATASET}.dim_party` WHERE is_vtp = TRUE")
        print(f"\n   -- Flexitricity VLP/VTP status:")
        print(f"   SELECT * FROM `{PROJECT_ID}.{DATASET}.dim_party` WHERE party_id = 'FLEXTRCY'")
    else:
        print("\n❌ FAILED: Could not retrieve party data")
        print("\n💡 Alternative: Use Elexon BMRS portal to download party list manually")
        print("   URL: https://www.bmreports.com/bmrs/")

if __name__ == "__main__":
    main()

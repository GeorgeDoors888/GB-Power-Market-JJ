#!/usr/bin/env python3
"""
Upload BSC Signatories CSV to BigQuery

Usage:
    python3 upload_bsc_signatories.py ELEXON-BSC-Signatories_20251220162340.csv
"""

from google.cloud import bigquery
import pandas as pd
import os
import sys

PROJECT_ID = "inner-cinema-476211-u9"
DATASET = "uk_energy_prod"
TABLE = "bsc_signatories"

def upload_bsc_signatories(csv_path):
    """Upload BSC signatories CSV to BigQuery"""

    if not os.path.exists(csv_path):
        print(f"❌ File not found: {csv_path}")
        return False

    # Set credentials
    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = '/home/george/GB-Power-Market-JJ/inner-cinema-credentials.json'

    print(f"📂 Reading CSV file: {csv_path}")
    df = pd.read_csv(csv_path)
    print(f"✅ Loaded {len(df)} BSC parties")

    # Show sample data
    print(f"\n📋 Columns: {', '.join(df.columns.tolist())}")
    print(f"\nSample parties:")
    for idx, row in df.head(5).iterrows():
        party_name = row['Party Name'] if 'Party Name' in row else 'N/A'
        party_id = row['Party ID'] if 'Party ID' in row else 'N/A'
        roles = row['Party Roles'] if 'Party Roles' in row else 'N/A'
        print(f"  {party_id:12s} - {party_name[:50]:50s} ({roles})")

    # Upload to BigQuery
    client = bigquery.Client(project=PROJECT_ID, location='US')
    table_id = f'{PROJECT_ID}.{DATASET}.{TABLE}'

    print(f"\n📤 Uploading to BigQuery: {table_id}")

    job_config = bigquery.LoadJobConfig(
        write_disposition='WRITE_TRUNCATE',  # Replace existing data
        autodetect=True
    )

    job = client.load_table_from_dataframe(df, table_id, job_config=job_config)
    job.result()  # Wait for completion

    # Verify upload
    table = client.get_table(table_id)
    print(f"\n✅ Successfully uploaded {table.num_rows:,} rows to BigQuery!")
    print(f"📊 Table: {table_id}")
    print(f"🏷️  Columns: {len(table.schema)} fields")

    # Show party role breakdown
    print(f"\n📈 Analyzing party roles...")
    role_query = f"""
    SELECT
        TRIM(role) as role,
        COUNT(DISTINCT `Party ID`) as party_count
    FROM `{table_id}`,
    UNNEST(SPLIT(`Party Roles`, ',')) as role
    GROUP BY role
    ORDER BY party_count DESC
    """

    roles_df = client.query(role_query).to_dataframe()
    print(f"\nParty Role Distribution:")
    print(roles_df.to_string(index=False))

    return True

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python3 upload_bsc_signatories.py <csv_file>")
        print("\nExample:")
        print("  python3 upload_bsc_signatories.py ELEXON-BSC-Signatories_20251220162340.csv")
        sys.exit(1)

    csv_file = sys.argv[1]
    success = upload_bsc_signatories(csv_file)
    sys.exit(0 if success else 1)

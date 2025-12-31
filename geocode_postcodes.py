#!/usr/bin/env python3
"""
Postcodes.io Geocoding for Constraint Analysis
Geocodes unique postcodes from BMU/constraint data for regional analysis
"""

from google.cloud import bigquery
import requests
import time
import json
from typing import Dict, List, Tuple

PROJECT_ID = "inner-cinema-476211-u9"
DATASET = "uk_energy_prod"
POSTCODES_API = "https://api.postcodes.io/postcodes"

def get_unique_postcodes(client) -> List[str]:
    """Extract unique postcodes from BMU and constraint-related tables"""

    print("\n📍 Extracting unique postcodes from BMU data...")

    # Query to get postcodes from various sources
    query = f"""
    WITH all_postcodes AS (
      -- From dim_bmu (if postcode field exists)
      SELECT DISTINCT
        UPPER(TRIM(REGEXP_REPLACE(postcode, r'[^A-Z0-9 ]', ''))) as postcode
      FROM `{PROJECT_ID}.{DATASET}.dim_bmu`
      WHERE postcode IS NOT NULL AND postcode != ''

      UNION DISTINCT

      -- From bmu_registration_data
      SELECT DISTINCT
        UPPER(TRIM(REGEXP_REPLACE(postcode, r'[^A-Z0-9 ]', ''))) as postcode
      FROM `{PROJECT_ID}.{DATASET}.bmu_registration_data`
      WHERE postcode IS NOT NULL AND postcode != ''
    )
    SELECT postcode
    FROM all_postcodes
    WHERE LENGTH(postcode) BETWEEN 5 AND 8  -- Valid UK postcode length
    AND postcode LIKE '%[0-9]%'  -- Must contain number
    ORDER BY postcode
    """

    try:
        result = client.query(query).result()
        postcodes = [row.postcode for row in result]
        print(f"✅ Found {len(postcodes)} unique postcodes")
        return postcodes
    except Exception as e:
        print(f"⚠️  No postcode fields found in tables: {e}")
        # Return sample postcodes for testing
        print("Using sample postcodes for demonstration...")
        return [
            'SW1A 1AA',  # Parliament
            'EC2N 2DB',  # City of London
            'M1 1AD',    # Manchester
            'B1 1AA',    # Birmingham
            'EH1 1YZ',   # Edinburgh
            'G1 1AA',    # Glasgow
            'CF10 1DD',  # Cardiff
            'BT1 1AA',   # Belfast
        ]

def geocode_postcode(postcode: str) -> Dict:
    """Geocode a single postcode using postcodes.io API"""

    try:
        response = requests.get(f"{POSTCODES_API}/{postcode}")

        if response.status_code == 200:
            data = response.json()
            if data['status'] == 200 and data['result']:
                result = data['result']
                return {
                    'postcode': postcode,
                    'latitude': result.get('latitude'),
                    'longitude': result.get('longitude'),
                    'region': result.get('region'),
                    'country': result.get('country'),
                    'parliamentary_constituency': result.get('parliamentary_constituency'),
                    'admin_district': result.get('admin_district'),
                    'admin_county': result.get('admin_county'),
                    'parish': result.get('parish'),
                    'outcode': result.get('outcode'),
                    'incode': result.get('incode'),
                    'eastings': result.get('eastings'),
                    'northings': result.get('northings'),
                    'success': True,
                    'error': None
                }

        return {
            'postcode': postcode,
            'success': False,
            'error': f"HTTP {response.status_code}"
        }

    except Exception as e:
        return {
            'postcode': postcode,
            'success': False,
            'error': str(e)
        }

def batch_geocode_postcodes(postcodes: List[str], batch_size: int = 100) -> List[Dict]:
    """Batch geocode postcodes using postcodes.io bulk API"""

    print(f"\n🌍 Geocoding {len(postcodes)} postcodes...")

    results = []
    failed = []

    # Process in batches
    for i in range(0, len(postcodes), batch_size):
        batch = postcodes[i:i+batch_size]

        print(f"  Batch {i//batch_size + 1}/{(len(postcodes)-1)//batch_size + 1} ({len(batch)} postcodes)...", end='', flush=True)

        try:
            # Bulk API endpoint
            response = requests.post(
                f"{POSTCODES_API}",
                json={"postcodes": batch}
            )

            if response.status_code == 200:
                data = response.json()
                if data['status'] == 200:
                    for item in data['result']:
                        if item['result']:
                            result = item['result']
                            results.append({
                                'postcode': item['query'],
                                'latitude': result.get('latitude'),
                                'longitude': result.get('longitude'),
                                'region': result.get('region'),
                                'country': result.get('country'),
                                'parliamentary_constituency': result.get('parliamentary_constituency'),
                                'admin_district': result.get('admin_district'),
                                'admin_county': result.get('admin_county'),
                                'outcode': result.get('outcode'),
                                'eastings': result.get('eastings'),
                                'northings': result.get('northings'),
                                'success': True
                            })
                        else:
                            failed.append(item['query'])

                    print(f" ✅ {len([r for r in data['result'] if r['result']])} succeeded")
                else:
                    print(f" ❌ API error")
                    failed.extend(batch)
            else:
                print(f" ❌ HTTP {response.status_code}")
                failed.extend(batch)

        except Exception as e:
            print(f" ❌ {e}")
            failed.extend(batch)

        # Rate limiting - be nice to free API
        time.sleep(0.5)

    print(f"\n✅ Successfully geocoded: {len(results)}")
    print(f"❌ Failed: {len(failed)}")

    if failed:
        print(f"   Failed postcodes: {', '.join(failed[:10])}" + ("..." if len(failed) > 10 else ""))

    return results

def upload_to_bigquery(client, results: List[Dict]):
    """Upload geocoded results to BigQuery"""

    print(f"\n📤 Uploading {len(results)} geocoded postcodes to BigQuery...")

    table_id = f"{PROJECT_ID}.{DATASET}.postcode_geocoded"

    # Define schema
    schema = [
        bigquery.SchemaField("postcode", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("latitude", "FLOAT64"),
        bigquery.SchemaField("longitude", "FLOAT64"),
        bigquery.SchemaField("region", "STRING"),
        bigquery.SchemaField("country", "STRING"),
        bigquery.SchemaField("parliamentary_constituency", "STRING"),
        bigquery.SchemaField("admin_district", "STRING"),
        bigquery.SchemaField("admin_county", "STRING"),
        bigquery.SchemaField("outcode", "STRING"),
        bigquery.SchemaField("eastings", "INTEGER"),
        bigquery.SchemaField("northings", "INTEGER"),
        bigquery.SchemaField("geocoded_at", "TIMESTAMP"),
    ]

    # Add timestamp and clean fields
    from datetime import datetime
    clean_results = []
    for result in results:
        clean_results.append({
            'postcode': result['postcode'],
            'latitude': result.get('latitude'),
            'longitude': result.get('longitude'),
            'region': result.get('region'),
            'country': result.get('country'),
            'parliamentary_constituency': result.get('parliamentary_constituency'),
            'admin_district': result.get('admin_district'),
            'admin_county': result.get('admin_county'),
            'outcode': result.get('outcode'),
            'eastings': result.get('eastings'),
            'northings': result.get('northings'),
            'geocoded_at': datetime.utcnow().isoformat()
        })

    # Create or replace table
    job_config = bigquery.LoadJobConfig(
        schema=schema,
        write_disposition="WRITE_TRUNCATE",
    )

    job = client.load_table_from_json(
        clean_results,
        table_id,
        job_config=job_config
    )

    job.result()  # Wait for completion

    table = client.get_table(table_id)
    print(f"✅ Loaded {table.num_rows} rows to {table_id}")

    return table_id

def create_joined_view(client):
    """Create view joining BMU data with geocoded postcodes"""

    print("\n🔗 Creating BMU+Geocode joined view...")

    sql = f"""
    CREATE OR REPLACE VIEW `{PROJECT_ID}.{DATASET}.v_bmu_with_geocode` AS
    SELECT
      b.*,
      g.latitude,
      g.longitude,
      g.region,
      g.country,
      g.admin_district,
      g.admin_county,
      g.eastings,
      g.northings
    FROM `{PROJECT_ID}.{DATASET}.ref_bmu_canonical` b
    LEFT JOIN `{PROJECT_ID}.{DATASET}.postcode_geocoded` g
      ON UPPER(TRIM(REGEXP_REPLACE(b.postcode, r'[^A-Z0-9 ]', ''))) = g.postcode
    """

    try:
        client.query(sql).result()
        print(f"✅ Created view: v_bmu_with_geocode")
    except Exception as e:
        print(f"⚠️  Could not create view (postcode field may not exist in BMU tables): {e}")

def main():
    print("="*80)
    print("POSTCODES.IO GEOCODING FOR CONSTRAINT ANALYSIS")
    print("="*80)

    # Initialize BigQuery client
    client = bigquery.Client(project=PROJECT_ID, location="US")

    # Step 1: Get unique postcodes
    postcodes = get_unique_postcodes(client)

    if not postcodes:
        print("\n⚠️  No postcodes found to geocode")
        return

    # Step 2: Geocode via postcodes.io
    results = batch_geocode_postcodes(postcodes)

    if not results:
        print("\n❌ No successful geocoding results")
        return

    # Step 3: Upload to BigQuery
    table_id = upload_to_bigquery(client, results)

    # Step 4: Create joined view (if possible)
    create_joined_view(client)

    # Summary
    print("\n" + "="*80)
    print("✅ GEOCODING COMPLETE")
    print("="*80)
    print(f"Postcodes processed: {len(postcodes)}")
    print(f"Successfully geocoded: {len(results)}")
    print(f"BigQuery table: {table_id}")
    print(f"\nQuery example:")
    print(f"  SELECT postcode, latitude, longitude, region")
    print(f"  FROM `{table_id}`")
    print(f"  ORDER BY postcode;")

if __name__ == "__main__":
    main()

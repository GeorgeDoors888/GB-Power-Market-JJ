#!/usr/bin/env python3
"""
Create missing BigQuery tables for IRIS message types
"""
from google.cloud import bigquery
from pathlib import Path
import json

PROJECT_ID = "inner-cinema-476211-u9"
DATASET = "uk_energy_prod"

# Table definitions based on actual IRIS data structures
TABLE_SCHEMAS = {
    'bmrs_fuelhh_iris': [
        bigquery.SchemaField('publishTime', 'TIMESTAMP'),
        bigquery.SchemaField('fuelType', 'STRING'),
        bigquery.SchemaField('settlementDate', 'DATE'),
        bigquery.SchemaField('settlementPeriod', 'INTEGER'),
        bigquery.SchemaField('generation', 'FLOAT64'),
        bigquery.SchemaField('_ingested_utc', 'TIMESTAMP'),
    ],
    'bmrs_fou2t14d_iris': [
        bigquery.SchemaField('publishTime', 'TIMESTAMP'),
        bigquery.SchemaField('bmUnit', 'STRING'),
        bigquery.SchemaField('nationalGridBmUnit', 'STRING'),
        bigquery.SchemaField('fuelType', 'STRING'),
        bigquery.SchemaField('settlementDate', 'DATE'),
        bigquery.SchemaField('settlementPeriod', 'INTEGER'),
        bigquery.SchemaField('output', 'INTEGER'),
        bigquery.SchemaField('_ingested_utc', 'TIMESTAMP'),
    ],
    'bmrs_fou2t3yw_iris': [
        bigquery.SchemaField('publishTime', 'TIMESTAMP'),
        bigquery.SchemaField('bmUnit', 'STRING'),
        bigquery.SchemaField('nationalGridBmUnit', 'STRING'),
        bigquery.SchemaField('fuelType', 'STRING'),
        bigquery.SchemaField('week', 'INTEGER'),
        bigquery.SchemaField('year', 'INTEGER'),
        bigquery.SchemaField('output', 'INTEGER'),
        bigquery.SchemaField('_ingested_utc', 'TIMESTAMP'),
    ],
    'bmrs_uou2t3yw_iris': [
        bigquery.SchemaField('publishTime', 'TIMESTAMP'),
        bigquery.SchemaField('bmUnit', 'STRING'),
        bigquery.SchemaField('nationalGridBmUnit', 'STRING'),
        bigquery.SchemaField('fuelType', 'STRING'),
        bigquery.SchemaField('week', 'INTEGER'),
        bigquery.SchemaField('year', 'INTEGER'),
        bigquery.SchemaField('outputUsable', 'INTEGER'),
        bigquery.SchemaField('_ingested_utc', 'TIMESTAMP'),
    ],
    'bmrs_uou2t14d_iris': [
        bigquery.SchemaField('publishTime', 'TIMESTAMP'),
        bigquery.SchemaField('bmUnit', 'STRING'),
        bigquery.SchemaField('nationalGridBmUnit', 'STRING'),
        bigquery.SchemaField('fuelType', 'STRING'),
        bigquery.SchemaField('settlementDate', 'DATE'),
        bigquery.SchemaField('settlementPeriod', 'INTEGER'),
        bigquery.SchemaField('outputUsable', 'INTEGER'),
        bigquery.SchemaField('_ingested_utc', 'TIMESTAMP'),
    ],
    'bmrs_nou2t3yw_iris': [
        bigquery.SchemaField('publishTime', 'TIMESTAMP'),
        bigquery.SchemaField('fuelType', 'STRING'),
        bigquery.SchemaField('week', 'INTEGER'),
        bigquery.SchemaField('year', 'INTEGER'),
        bigquery.SchemaField('outputUsable', 'INTEGER'),
        bigquery.SchemaField('_ingested_utc', 'TIMESTAMP'),
    ],
    'bmrs_nou2t14d_iris': [
        bigquery.SchemaField('publishTime', 'TIMESTAMP'),
        bigquery.SchemaField('fuelType', 'STRING'),
        bigquery.SchemaField('settlementDate', 'DATE'),
        bigquery.SchemaField('settlementPeriod', 'INTEGER'),
        bigquery.SchemaField('outputUsable', 'INTEGER'),
        bigquery.SchemaField('_ingested_utc', 'TIMESTAMP'),
    ],
    'bmrs_ocnmfw_iris': [
        bigquery.SchemaField('publishTime', 'TIMESTAMP'),
        bigquery.SchemaField('week', 'INTEGER'),
        bigquery.SchemaField('year', 'INTEGER'),
        bigquery.SchemaField('margin', 'INTEGER'),
        bigquery.SchemaField('_ingested_utc', 'TIMESTAMP'),
    ],
    'bmrs_ocnmfw2_iris': [
        bigquery.SchemaField('publishTime', 'TIMESTAMP'),
        bigquery.SchemaField('week', 'INTEGER'),
        bigquery.SchemaField('year', 'INTEGER'),
        bigquery.SchemaField('margin', 'INTEGER'),
        bigquery.SchemaField('_ingested_utc', 'TIMESTAMP'),
    ],
    'bmrs_ocnmfd2_iris': [
        bigquery.SchemaField('publishTime', 'TIMESTAMP'),
        bigquery.SchemaField('settlementDate', 'DATE'),
        bigquery.SchemaField('settlementPeriod', 'INTEGER'),
        bigquery.SchemaField('margin', 'INTEGER'),
        bigquery.SchemaField('_ingested_utc', 'TIMESTAMP'),
    ],
    'bmrs_ocnmf3y2_iris': [
        bigquery.SchemaField('publishTime', 'TIMESTAMP'),
        bigquery.SchemaField('week', 'INTEGER'),
        bigquery.SchemaField('year', 'INTEGER'),
        bigquery.SchemaField('margin', 'INTEGER'),
        bigquery.SchemaField('_ingested_utc', 'TIMESTAMP'),
    ],
    'bmrs_qpn_iris': [
        bigquery.SchemaField('publishTime', 'TIMESTAMP'),
        bigquery.SchemaField('bmUnit', 'STRING'),
        bigquery.SchemaField('nationalGridBmUnit', 'STRING'),
        bigquery.SchemaField('timeFrom', 'TIMESTAMP'),
        bigquery.SchemaField('timeTo', 'TIMESTAMP'),
        bigquery.SchemaField('mw', 'FLOAT64'),
        bigquery.SchemaField('_ingested_utc', 'TIMESTAMP'),
    ],
    'bmrs_netbsad_iris': [
        bigquery.SchemaField('publishTime', 'TIMESTAMP'),
        bigquery.SchemaField('settlementDate', 'DATE'),
        bigquery.SchemaField('settlementPeriod', 'INTEGER'),
        bigquery.SchemaField('costSoFlag', 'STRING'),
        bigquery.SchemaField('costSoFlagDescription', 'STRING'),
        bigquery.SchemaField('bsadCost', 'FLOAT64'),
        bigquery.SchemaField('_ingested_utc', 'TIMESTAMP'),
    ],
    'bmrs_itsdo_iris': [
        bigquery.SchemaField('publishTime', 'TIMESTAMP'),
        bigquery.SchemaField('settlementDate', 'DATE'),
        bigquery.SchemaField('settlementPeriod', 'INTEGER'),
        bigquery.SchemaField('demand', 'INTEGER'),
        bigquery.SchemaField('_ingested_utc', 'TIMESTAMP'),
    ],
    'bmrs_beb_iris': [
        bigquery.SchemaField('publishTime', 'TIMESTAMP'),
        bigquery.SchemaField('settlementDate', 'DATE'),
        bigquery.SchemaField('settlementPeriod', 'INTEGER'),
        bigquery.SchemaField('bmUnit', 'STRING'),
        bigquery.SchemaField('nationalGridBmUnit', 'STRING'),
        bigquery.SchemaField('fuelType', 'STRING'),
        bigquery.SchemaField('energyBalanced', 'FLOAT64'),
        bigquery.SchemaField('_ingested_utc', 'TIMESTAMP'),
    ],
    'bmrs_inddem_iris': [
        bigquery.SchemaField('publishTime', 'TIMESTAMP'),
        bigquery.SchemaField('settlementDate', 'DATE'),
        bigquery.SchemaField('settlementPeriod', 'INTEGER'),
        bigquery.SchemaField('bmUnit', 'STRING'),
        bigquery.SchemaField('nationalGridBmUnit', 'STRING'),
        bigquery.SchemaField('demand', 'FLOAT64'),
        bigquery.SchemaField('_ingested_utc', 'TIMESTAMP'),
    ],
    'bmrs_mels_iris': [
        bigquery.SchemaField('publishTime', 'TIMESTAMP'),
        bigquery.SchemaField('bmUnit', 'STRING'),
        bigquery.SchemaField('nationalGridBmUnit', 'STRING'),
        bigquery.SchemaField('settlementDate', 'DATE'),
        bigquery.SchemaField('settlementPeriod', 'INTEGER'),
        bigquery.SchemaField('mels', 'FLOAT64'),
        bigquery.SchemaField('_ingested_utc', 'TIMESTAMP'),
    ],
    'bmrs_mils_iris': [
        bigquery.SchemaField('publishTime', 'TIMESTAMP'),
        bigquery.SchemaField('bmUnit', 'STRING'),
        bigquery.SchemaField('nationalGridBmUnit', 'STRING'),
        bigquery.SchemaField('settlementDate', 'DATE'),
        bigquery.SchemaField('settlementPeriod', 'INTEGER'),
        bigquery.SchemaField('mils', 'FLOAT64'),
        bigquery.SchemaField('_ingested_utc', 'TIMESTAMP'),
    ],
}

def main():
    """Create all missing IRIS tables"""
    client = bigquery.Client(project=PROJECT_ID, location="US")

    print(f"Creating missing IRIS tables in {PROJECT_ID}.{DATASET}...\n")

    created = 0
    existing = 0

    for table_name, schema in TABLE_SCHEMAS.items():
        table_id = f"{PROJECT_ID}.{DATASET}.{table_name}"
        try:
            client.get_table(table_id)
            existing += 1
            print(f"✓ {table_name} (exists)")
        except Exception:
            table = bigquery.Table(table_id, schema=schema)
            client.create_table(table)
            created += 1
            print(f"✅ {table_name} (created)")

    print(f"\n{'='*60}")
    print(f"Summary: {created} created, {existing} already existed")
    print(f"Total tables: {created + existing}")
    print(f"{'='*60}\n")

if __name__ == '__main__':
    main()

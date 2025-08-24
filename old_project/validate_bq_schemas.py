#!/usr/bin/env python3
"""
BigQuery Schema Validator

This script validates the BigQuery tables and their schemas, ensuring they are
properly set up for the energy data system. It can help identify schema issues
before attempting to load data.
"""

import argparse
import json
import sys
from google.cloud import bigquery

# Expected schemas for each table
EXPECTED_SCHEMAS = {
    "elexon_demand_outturn": [
        {"name": "publishTime", "type": "TIMESTAMP"},
        {"name": "startTime", "type": "TIMESTAMP"},
        {"name": "settlementDate", "type": "DATE"},
        {"name": "settlementPeriod", "type": "INTEGER"},
        {"name": "initialDemandOutturn", "type": "FLOAT"},
        {"name": "initialTransmissionSystemDemandOutturn", "type": "FLOAT"}
    ],
    "elexon_frequency": [
        {"name": "timestamp", "type": "DATETIME"},
        {"name": "settlement_date", "type": "DATE"},
        {"name": "settlement_period", "type": "INTEGER"},
        {"name": "frequency", "type": "FLOAT"}
    ],
    "elexon_generation_outturn": [
        {"name": "recordType", "type": "STRING"},
        {"name": "startTime", "type": "TIMESTAMP"},
        {"name": "settlementDate", "type": "DATE"},
        {"name": "settlementPeriod", "type": "INTEGER"},
        {"name": "demand", "type": "FLOAT"}
    ],
    "neso_balancing_services": [
        {"name": "timestamp", "type": "DATETIME"},
        {"name": "settlement_date", "type": "DATE"},
        {"name": "settlement_period", "type": "INTEGER"},
        {"name": "service_type", "type": "STRING"},
        {"name": "volume", "type": "FLOAT"},
        {"name": "cost", "type": "FLOAT"}
    ],
    "elexon_system_warnings": [
        {"name": "published_time", "type": "DATETIME"},
        {"name": "warning_type", "type": "STRING"},
        {"name": "message", "type": "STRING"},
        {"name": "severity", "type": "STRING"}
    ],
    "neso_interconnector_flows": [
        {"name": "timestamp", "type": "DATETIME"},
        {"name": "settlement_date", "type": "DATE"},
        {"name": "settlement_period", "type": "INTEGER"},
        {"name": "interconnector_id", "type": "STRING"},
        {"name": "flow_volume", "type": "FLOAT"},
        {"name": "flow_direction", "type": "STRING"}
    ],
    "neso_carbon_intensity": [
        {"name": "timestamp", "type": "DATETIME"},
        {"name": "settlement_date", "type": "DATE"},
        {"name": "settlement_period", "type": "INTEGER"},
        {"name": "carbon_intensity", "type": "FLOAT"},
        {"name": "generation_mix", "type": "STRING"}
    ]
}

def validate_table_schema(client, project, dataset, table_name):
    """Validate that a table's schema matches the expected schema."""
    full_table_id = f"{project}.{dataset}.{table_name}"
    
    try:
        # Get the actual table schema
        table = client.get_table(full_table_id)
        actual_schema = table.schema
        
        # Convert to simple format for comparison
        actual_fields = [{"name": field.name, "type": field.field_type} for field in actual_schema]
        
        # Get expected schema
        expected_fields = EXPECTED_SCHEMAS.get(table_name, [])
        
        if not expected_fields:
            print(f"⚠️ No expected schema defined for {table_name}")
            return True
        
        # Compare schemas
        missing_fields = []
        mismatched_types = []
        
        for expected in expected_fields:
            matching = [f for f in actual_fields if f["name"] == expected["name"]]
            if not matching:
                missing_fields.append(expected["name"])
            elif matching[0]["type"] != expected["type"]:
                mismatched_types.append({
                    "field": expected["name"],
                    "expected": expected["type"],
                    "actual": matching[0]["type"]
                })
        
        if missing_fields or mismatched_types:
            print(f"❌ Schema validation failed for {full_table_id}")
            if missing_fields:
                print(f"   Missing fields: {', '.join(missing_fields)}")
            if mismatched_types:
                for mismatch in mismatched_types:
                    print(f"   Field {mismatch['field']} has type {mismatch['actual']}, expected {mismatch['expected']}")
            return False
        
        print(f"✅ Schema validation passed for {full_table_id}")
        
        # Check row count
        query = f"SELECT COUNT(*) as count FROM `{full_table_id}`"
        query_job = client.query(query)
        results = query_job.result()
        rows = list(results)[0].count
        
        print(f"   Table has {rows} rows")
        
        # If rows exist, check date range
        if rows > 0 and table_name != "elexon_system_warnings":
            date_col = "settlement_date"
            date_query = f"SELECT MIN({date_col}) as min_date, MAX({date_col}) as max_date FROM `{full_table_id}`"
            date_job = client.query(date_query)
            date_results = date_job.result()
            date_row = list(date_results)[0]
            
            print(f"   Date range: {date_row.min_date} to {date_row.max_date}")
        
        return True
        
    except Exception as e:
        if "Not found" in str(e):
            print(f"❌ Table {full_table_id} does not exist")
        else:
            print(f"❌ Error validating {full_table_id}: {str(e)}")
        return False

def create_table_with_schema(client, project, dataset, table_name):
    """Create a table with the expected schema if it doesn't exist."""
    full_table_id = f"{project}.{dataset}.{table_name}"
    
    # Get expected schema
    expected_fields = EXPECTED_SCHEMAS.get(table_name, [])
    
    if not expected_fields:
        print(f"⚠️ No expected schema defined for {table_name}")
        return False
    
    # Convert to BigQuery schema format
    schema = []
    for field in expected_fields:
        schema.append(bigquery.SchemaField(
            field["name"], 
            field["type"],
            mode="NULLABLE"
        ))
    
    # Create table
    table = bigquery.Table(full_table_id, schema=schema)
    
    try:
        table = client.create_table(table)
        print(f"✅ Created table {full_table_id}")
        return True
    except Exception as e:
        print(f"❌ Error creating {full_table_id}: {str(e)}")
        return False

def main():
    parser = argparse.ArgumentParser(description='Validate BigQuery tables for energy data system')
    parser.add_argument('--project', type=str, default='jibber-jabber-knowledge',
                        help='BigQuery project ID')
    parser.add_argument('--dataset', type=str, default='uk_energy_prod',
                        help='BigQuery dataset name')
    parser.add_argument('--table', type=str, choices=list(EXPECTED_SCHEMAS.keys()) + ['all'],
                        default='all', help='Table to validate (default: all)')
    parser.add_argument('--create-missing', action='store_true',
                        help='Create tables that are missing')
    
    args = parser.parse_args()
    
    print(f"Validating BigQuery tables in {args.project}.{args.dataset}")
    
    client = bigquery.Client(project=args.project)
    
    tables_to_validate = list(EXPECTED_SCHEMAS.keys()) if args.table == 'all' else [args.table]
    all_valid = True
    
    for table_name in tables_to_validate:
        valid = validate_table_schema(client, args.project, args.dataset, table_name)
        if not valid and args.create_missing:
            print(f"Attempting to create table {table_name}...")
            create_table_with_schema(client, args.project, args.dataset, table_name)
        all_valid = all_valid and valid
    
    if all_valid:
        print("\n✅ All tables validated successfully")
        return 0
    else:
        print("\n⚠️ Some tables have validation issues")
        return 1

if __name__ == "__main__":
    sys.exit(main())

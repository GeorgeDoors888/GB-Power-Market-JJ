#!/usr/bin/env python3
"""
Import GridSmart cost data into BigQuery
"""
import sys
sys.path.insert(0, "drive-bq-indexer")

import os
from google.cloud import bigquery
from google.oauth2 import service_account

# Setup credentials
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "gridsmart_service_account.json"

PROJECT_ID = "inner-cinema-476211-u9"
DATASET = "uk_energy_insights"

def create_costs_table(client):
    """Create the gridsmart_costs table if it doesn't exist"""
    table_id = f"{PROJECT_ID}.{DATASET}.gridsmart_costs"
    
    schema = [
        bigquery.SchemaField("cost_id", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("timestamp", "TIMESTAMP", mode="REQUIRED"),
        bigquery.SchemaField("meter_id", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("location", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("cost_type", "STRING", mode="NULLABLE"),  # e.g., "electricity", "gas", "maintenance"
        bigquery.SchemaField("amount", "FLOAT64", mode="REQUIRED"),
        bigquery.SchemaField("currency", "STRING", mode="NULLABLE", default_value_expression="'GBP'"),
        bigquery.SchemaField("units", "STRING", mode="NULLABLE"),  # e.g., "kWh", "m3"
        bigquery.SchemaField("unit_cost", "FLOAT64", mode="NULLABLE"),
        bigquery.SchemaField("usage", "FLOAT64", mode="NULLABLE"),
        bigquery.SchemaField("description", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("period_start", "TIMESTAMP", mode="NULLABLE"),
        bigquery.SchemaField("period_end", "TIMESTAMP", mode="NULLABLE"),
        bigquery.SchemaField("imported_at", "TIMESTAMP", mode="REQUIRED"),
    ]
    
    table = bigquery.Table(table_id, schema=schema)
    table = client.create_table(table, exists_ok=True)
    print(f"✅ Table {table_id} ready")
    return table

def import_from_csv(client, csv_path):
    """Import costs from a CSV file"""
    table_id = f"{PROJECT_ID}.{DATASET}.gridsmart_costs"
    
    job_config = bigquery.LoadJobConfig(
        source_format=bigquery.SourceFormat.CSV,
        skip_leading_rows=1,
        autodetect=True,
        write_disposition=bigquery.WriteDisposition.WRITE_APPEND,
    )
    
    with open(csv_path, "rb") as source_file:
        job = client.load_table_from_file(source_file, table_id, job_config=job_config)
    
    job.result()  # Wait for the job to complete
    
    table = client.get_table(table_id)
    print(f"✅ Loaded {table.num_rows} rows into {table_id}")

def import_from_sheets(client, sheet_id, range_name="Sheet1!A:M"):
    """Import costs from Google Sheets"""
    from googleapiclient.discovery import build
    
    # Build the Sheets API client
    creds = service_account.Credentials.from_service_account_file(
        "gridsmart_service_account.json",
        scopes=['https://www.googleapis.com/auth/spreadsheets.readonly']
    )
    
    service = build('sheets', 'v4', credentials=creds)
    sheet = service.spreadsheets()
    
    # Fetch data
    result = sheet.values().get(spreadsheetId=sheet_id, range=range_name).execute()
    values = result.get('values', [])
    
    if not values:
        print("❌ No data found in sheet")
        return
    
    # Assume first row is headers
    headers = values[0]
    rows = values[1:]
    
    # Convert to dict format for BigQuery
    table_id = f"{PROJECT_ID}.{DATASET}.gridsmart_costs"
    
    # Map your sheet columns to BigQuery schema
    # Adjust this mapping based on your actual sheet structure
    data = []
    for row in rows:
        if len(row) < len(headers):
            row.extend([''] * (len(headers) - len(row)))  # Pad short rows
        
        record = dict(zip(headers, row))
        data.append(record)
    
    # Load into BigQuery
    errors = client.insert_rows_json(table_id, data)
    
    if errors:
        print(f"❌ Errors: {errors}")
    else:
        print(f"✅ Loaded {len(data)} rows from Google Sheets")

def main():
    """Main import function"""
    client = bigquery.Client(project=PROJECT_ID)
    
    print("📊 GridSmart Cost Data Importer")
    print("=" * 60)
    
    # Create table
    create_costs_table(client)
    
    print("\nChoose import source:")
    print("1. CSV file")
    print("2. Google Sheets")
    print("3. Manual data entry (for testing)")
    
    choice = input("\nEnter choice (1-3): ").strip()
    
    if choice == "1":
        csv_path = input("Enter CSV file path: ").strip()
        if os.path.exists(csv_path):
            import_from_csv(client, csv_path)
        else:
            print(f"❌ File not found: {csv_path}")
    
    elif choice == "2":
        sheet_id = input("Enter Google Sheet ID: ").strip()
        range_name = input("Enter range (default: Sheet1!A:M): ").strip() or "Sheet1!A:M"
        import_from_sheets(client, sheet_id, range_name)
    
    elif choice == "3":
        # Insert sample data for testing
        table_id = f"{PROJECT_ID}.{DATASET}.gridsmart_costs"
        from datetime import datetime
        
        sample_data = [
            {
                "cost_id": "TEST001",
                "timestamp": datetime.now().isoformat(),
                "meter_id": "METER_123",
                "location": "Building A",
                "cost_type": "electricity",
                "amount": 125.50,
                "currency": "GBP",
                "units": "kWh",
                "unit_cost": 0.25,
                "usage": 502.0,
                "description": "Monthly electricity cost",
                "imported_at": datetime.now().isoformat(),
            }
        ]
        
        errors = client.insert_rows_json(table_id, sample_data)
        if errors:
            print(f"❌ Errors: {errors}")
        else:
            print(f"✅ Inserted test record")
    
    print("\n✅ Import complete!")
    print(f"\nQuery your data:")
    print(f"  SELECT * FROM `{PROJECT_ID}.{DATASET}.gridsmart_costs` LIMIT 10")

if __name__ == "__main__":
    main()

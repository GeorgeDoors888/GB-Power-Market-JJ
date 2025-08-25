import os
from google.cloud import bigquery

# Settings
dataset_id = "uk_energy_prod"
project_id = os.environ.get("GOOGLE_CLOUD_PROJECT", "jibber-jabber-knowledge")

client = bigquery.Client(project=project_id)
print(f"[INFO] Using project: {client.project}")
print(f"[INFO] Using dataset: {dataset_id}")

# List all tables in the dataset
tables = list(client.list_tables(dataset_id))
print(f"[INFO] Tables in dataset {dataset_id}:")
for t in tables:
    print(f"  - {t.table_id}")

# Try to create and insert a dummy row for a failing table
# Example: system_warnings
failing_tables = ["system_warnings", "indo", "system_frequency"]
for table_name in failing_tables:
    table_id = f"{project_id}.{dataset_id}.{table_name}"
    print(f"\n[DEBUG] Checking table: {table_id}")
    # Try to get the table
    try:
        table = client.get_table(table_id)
        print(f"[OK] Table exists: {table_id}")
    except Exception as e:
        print(f"[WARN] Table does not exist: {table_id} ({e})")
        # Try to create with a simple schema
        schema = [
            bigquery.SchemaField("test_field", "STRING")
        ]
        table = bigquery.Table(table_id, schema=schema)
        try:
            client.create_table(table)
            print(f"[OK] Created table: {table_id}")
        except Exception as ce:
            print(f"[ERROR] Could not create table {table_id}: {ce}")
            continue
    # Try to insert a dummy row
    rows_to_insert = [
        {"test_field": "debug_test"}
    ]
    try:
        errors = client.insert_rows_json(table_id, rows_to_insert)
        if not errors:
            print(f"[OK] Inserted dummy row into {table_id}")
        else:
            print(f"[ERROR] Insert failed for {table_id}: {errors}")
    except Exception as ie:
        print(f"[ERROR] Exception on insert for {table_id}: {ie}")

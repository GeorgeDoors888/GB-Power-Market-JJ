import os
from google.cloud import bigquery

# Settings
project_id = os.environ.get("GOOGLE_CLOUD_PROJECT", "jibber-jabber-knowledge")
new_dataset_id = "uk_energy_prod_test"

client = bigquery.Client(project=project_id)
print(f"[INFO] Using project: {client.project}")

# Create a new dataset
full_dataset_id = f"{client.project}.{new_dataset_id}"
try:
    dataset = bigquery.Dataset(full_dataset_id)
    dataset.location = "EU"
    client.create_dataset(dataset, exists_ok=True)
    print(f"[OK] Created dataset: {full_dataset_id}")
except Exception as e:
    print(f"[ERROR] Could not create dataset: {e}")

# Create and insert into test tables
for table_name in ["system_warnings_test", "indo_test", "system_frequency_test"]:
    table_id = f"{client.project}.{new_dataset_id}.{table_name}"
    print(f"\n[DEBUG] Creating table: {table_id}")
    schema = [
        bigquery.SchemaField("test_field", "STRING")
    ]
    table = bigquery.Table(table_id, schema=schema)
    try:
        client.create_table(table, exists_ok=True)
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

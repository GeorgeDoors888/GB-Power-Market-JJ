import os
import json
import time
import logging
from google.cloud import bigquery
from google.api_core.exceptions import NotFound, BadRequest

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')

# Configuration
IRIS_DATA_DIR = os.path.join(os.path.dirname(__file__), 'iris-clients', 'python', 'iris_data')
BQ_PROJECT = os.environ.get('BQ_PROJECT') or 'inner-cinema-476211-u9'
BQ_DATASET = os.environ.get('BQ_DATASET') or 'uk_energy_prod'

# Initialize BigQuery client
bq_client = bigquery.Client(project=BQ_PROJECT)

def get_table_ref(dataset, table):
    return f"{BQ_PROJECT}.{dataset}.{table}"

def get_existing_schema(table_ref):
    try:
        table = bq_client.get_table(table_ref)
        return {field.name: field for field in table.schema}
    except NotFound:
        return {}

def add_new_columns(table_ref, new_fields):
    table = bq_client.get_table(table_ref)
    schema = list(table.schema)
    for field_name, field_type in new_fields.items():
        schema.append(bigquery.SchemaField(field_name, field_type, mode="NULLABLE"))
        logging.info(f"Adding new column: {field_name} ({field_type}) to {table_ref}")
    table.schema = schema
    bq_client.update_table(table, ["schema"])

def infer_bq_type(value):
    if isinstance(value, bool):
        return "BOOLEAN"
    if isinstance(value, int):
        return "INT64"
    if isinstance(value, float):
        return "FLOAT64"
    if isinstance(value, dict):
        return "RECORD"
    return "STRING"

def upsert_to_bigquery(table_ref, rows):
    errors = bq_client.insert_rows_json(table_ref, rows)
    if errors:
        logging.error(f"BigQuery insert errors: {errors}")
    else:
        logging.info(f"Inserted {len(rows)} rows into {table_ref}")

def process_file(filepath):
    with open(filepath, 'r') as f:
        data = json.load(f)
    # Determine table name
    dataset = os.path.basename(os.path.dirname(filepath)).lower()
    table_ref = get_table_ref(BQ_DATASET, f"bmrs_{dataset}")
    # Get schema
    existing_schema = get_existing_schema(table_ref)
    # Detect new fields
    new_fields = {}
    for key, value in data.items():
        if key not in existing_schema:
            new_fields[key] = infer_bq_type(value)
    if new_fields:
        add_new_columns(table_ref, new_fields)
    # Insert row
    upsert_to_bigquery(table_ref, [data])
    # Optionally, move or delete file after processing
    os.remove(filepath)
    logging.info(f"Processed and removed {filepath}")

def main():
    logging.info(f"Watching IRIS data directory: {IRIS_DATA_DIR}")
    while True:
        for dataset_dir in os.listdir(IRIS_DATA_DIR):
            dataset_path = os.path.join(IRIS_DATA_DIR, dataset_dir)
            if not os.path.isdir(dataset_path):
                continue
            for filename in os.listdir(dataset_path):
                if not filename.endswith('.json'):
                    continue
                filepath = os.path.join(dataset_path, filename)
                try:
                    process_file(filepath)
                except (json.JSONDecodeError, BadRequest) as e:
                    logging.error(f"Failed to process {filepath}: {e}")
                    os.remove(filepath)  # Remove bad file
        time.sleep(10)

if __name__ == "__main__":
    main()

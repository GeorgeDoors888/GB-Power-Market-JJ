import os
import json
import asyncio
import aiohttp
import hashlib
from datetime import datetime, timedelta
from google.cloud import bigquery
from google.cloud.exceptions import NotFound
from dotenv import load_dotenv

# ---------------------------
# CONFIGURATION
# ---------------------------
load_dotenv("api.env")
BQ_PROJECT = "jibber-jabber-knowledge"
BQ_DATASET = "uk_energy_prod"
CONFIG_FILE = "insights_datasets.json"
API_KEYS = [os.getenv(f"BMRS_API_KEY_{i}") for i in range(1, 21)]
if not all(API_KEYS):
    raise ValueError("One or more BMRS_API_KEY environment variables are not set.")

# ---------------------------
# BIGQUERY SETUP
# ---------------------------
try:
    bq_client = bigquery.Client(project=BQ_PROJECT)
    print("BigQuery client created successfully.")
except Exception as e:
    raise RuntimeError(f"Failed to create BigQuery client: {e}")

def hash_row(row):
    """Creates a SHA-256 hash of a dictionary to use as a unique row ID."""
    # Sort the dictionary by key to ensure consistent hash results
    sorted_row_str = json.dumps(row, sort_keys=True)
    return hashlib.sha256(sorted_row_str.encode("utf-8")).hexdigest()

def infer_and_convert_schema(row):
    """Infers BigQuery schema from a sample row and converts data types."""
    schema = []
    converted_row = {}
    for key, value in row.items():
        # Copy original value
        converted_row[key] = value

        # Infer schema type
        if isinstance(value, bool):
            field_type = "BOOLEAN"
        elif isinstance(value, int):
            field_type = "INTEGER"
        elif isinstance(value, float):
            field_type = "FLOAT"
        elif isinstance(value, str):
            try:
                # Check for ISO 8601 format datetime with Z or timezone
                datetime.fromisoformat(value.replace('Z', '+00:00'))
                field_type = "TIMESTAMP"
            except (ValueError, TypeError):
                field_type = "STRING"
        else:
            field_type = "STRING"
            # Convert non-standard types to string for BQ compatibility
            converted_row[key] = str(value)

        schema.append(bigquery.SchemaField(key, field_type, mode="NULLABLE"))
    return schema, converted_row

async def ensure_bq_table(table_id, sample_row):
    """Ensures a BigQuery table exists, creating or updating its schema as needed."""
    try:
        table = bq_client.get_table(table_id)

        # Check for schema differences
        existing_schema_map = {field.name: field.field_type for field in table.schema}
        inferred_schema, _ = infer_and_convert_schema(sample_row)

        new_fields = [field for field in inferred_schema if field.name not in existing_schema_map]

        if new_fields:
            print(f"Schema evolution for {table_id}: Adding new fields: {[f.name for f in new_fields]}")
            new_schema = table.schema + new_fields
            table.schema = new_schema
            bq_client.update_table(table, ["schema"])
            print(f"Table {table_id} schema updated.")

    except NotFound:
        print(f"Table {table_id} not found. Creating new table.")
        schema, _ = infer_and_convert_schema(sample_row)
        table = bigquery.Table(table_id, schema=schema)
        bq_client.create_table(table)
        print(f"Table {table_id} created.")
    except Exception as e:
        print(f"[ERROR] Failed to ensure table {table_id}: {e}")
        raise

# ---------------------------
# API FETCHING
# ---------------------------
async def fetch_and_ingest(session, dataset, key_cycler):
    """Fetches data for a given dataset config and ingests it into BigQuery."""
    table_id = f"{BQ_PROJECT}.{BQ_DATASET}.{dataset['dataset_code'].lower()}"

    # TEST OVERRIDE: Force date range to July 2025
    start_date = datetime.strptime("2025-07-01", "%Y-%m-%d").date()
    end_date = datetime.strptime("2025-07-31", "%Y-%m-%d").date()
    print(f"--- TEST MODE: Processing {dataset['dataset_code']} for July 2025 only. ---")

    current_date = start_date
    while current_date <= end_date:
        chunk_end_date = min(current_date + timedelta(days=6), end_date)

        api_key = next(key_cycler)
        params = {
            "startTime": current_date.strftime("%Y-%m-%d"),
            "endTime": chunk_end_date.strftime("%Y-%m-%d"),
            "format": "json"
        }

        try:
            async with session.get(dataset["endpoint"], params=params, headers={"key": api_key}, timeout=180) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    if data and "data" in data and data["data"]:
                        rows_to_insert = data["data"]

                        # Infer schema from first row and ensure table exists/is updated
                        await ensure_bq_table(table_id, rows_to_insert[0])

                        # Prepare rows for insertion
                        processed_rows = []
                        for row in rows_to_insert:
                            _, converted_row = infer_and_convert_schema(row)
                            row_id = hash_row(converted_row)
                            processed_rows.append(bigquery.InsertRowsTuple(row_id, converted_row))

                        # Stream insert
                        errors = bq_client.insert_rows(table_id, processed_rows)
                        if not errors:
                            print(f"[OK] Ingested {len(processed_rows)} rows for {dataset['dataset_code']} from {current_date} to {chunk_end_date}.")
                        else:
                            print(f"[FAIL] BigQuery insert errors for {dataset['dataset_code']}: {errors}")
                    else:
                        print(f"[SKIP] No data for {dataset['dataset_code']} from {current_date} to {chunk_end_date}.")

                elif resp.status == 404:
                    print(f"[WARN] HTTP 404 - Not Found for {dataset['dataset_code']} for period starting {current_date}. Might be no data for this period.")
                else:
                    error_text = await resp.text()
                    print(f"[ERROR] HTTP {resp.status} for {dataset['dataset_code']} for period starting {current_date}. Response: {error_text[:200]}")

        except asyncio.TimeoutError:
            print(f"[ERROR] Timeout fetching {dataset['dataset_code']} for period starting {current_date}.")
        except Exception as e:
            print(f"[ERROR] Exception fetching/ingesting {dataset['dataset_code']} for period {current_date}: {e}")

        # Move to the next 7-day chunk
        current_date += timedelta(days=7)
        await asyncio.sleep(0.1) # Small delay to be polite

# ---------------------------
# MAIN ORCHESTRATOR
# ---------------------------
async def main():
    """Main function to orchestrate the data fetching and ingestion process."""
    try:
        with open(CONFIG_FILE, 'r') as f:
            datasets = json.load(f)
        print(f"Loaded {len(datasets)} dataset configurations from {CONFIG_FILE}.")
    except FileNotFoundError:
        print(f"[FATAL] Configuration file {CONFIG_FILE} not found.")
        return
    except json.JSONDecodeError:
        print(f"[FATAL] Could not decode JSON from {CONFIG_FILE}.")
        return

    # Create a cycle iterator for API keys
    from itertools import cycle
    key_cycler = cycle(API_KEYS)

    # Use a semaphore to limit concurrent requests to the number of API keys
    sem = asyncio.Semaphore(len(API_KEYS))

    async def task_wrapper(session, dataset, key_cycler):
        async with sem:
            await fetch_and_ingest(session, dataset, key_cycler)

    # Use a single aiohttp session for all requests
    async with aiohttp.ClientSession() as session:
        tasks = [task_wrapper(session, dataset, key_cycler) for dataset in datasets]
        await asyncio.gather(*tasks)

if __name__ == "__main__":
    print("Starting Elexon Insights data ingestion pipeline...")
    start_time = datetime.now()

    # Set the GOOGLE_APPLICATION_CREDENTIALS environment variable
    # IMPORTANT: Replace with the actual path to your service account key file
    credential_path = os.path.join(os.path.dirname(__file__), "jibber-jabber-knowledge-e6fc00c9002c.json")
    if os.path.exists(credential_path):
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = credential_path
        print(f"Set GOOGLE_APPLICATION_CREDENTIALS to: {credential_path}")
    else:
        print(f"[WARN] Service account key file not found at {credential_path}. Using default credentials if available.")

    asyncio.run(main())

    end_time = datetime.now()
    print(f"Pipeline finished. Total execution time: {end_time - start_time}")

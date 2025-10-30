import os
import logging
from datetime import datetime
import pandas as pd
import requests
from google.cloud import bigquery
from google.api_core.exceptions import NotFound

# --- Configuration ---
BQ_PROJECT = "jibber-jabber-knowledge"
BQ_DATASET = "elexon_data_landing_zone"
TEMP_TABLE_NAME = "debug_bmrs_wind_solar_gen_temp"
TABLE_ID = f"{BQ_PROJECT}.{BQ_DATASET}.{TEMP_TABLE_NAME}"

START_DATE = "2025-09-22"
END_DATE = "2025-09-23"

LOG_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"
logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)

# --- Explicit Schema Definition ---
# This schema matches the expected structure, with 'publishtime' as a STRING.
SCHEMA = [
    bigquery.SchemaField("dataset", "STRING"),
    bigquery.SchemaField("publishTime", "STRING"),
    bigquery.SchemaField("startTime", "TIMESTAMP"),
    bigquery.SchemaField("settlementDate", "DATE"),
    bigquery.SchemaField("settlementPeriod", "INTEGER"),
    bigquery.SchemaField("powerSystemResourceType", "STRING"),
    bigquery.SchemaField("quantity", "FLOAT"),
]

def fetch_wind_solar_data(start_str: str, end_str: str) -> pd.DataFrame:
    """Fetches WIND_SOLAR_GEN data from the BMRS API."""
    logging.info(f"Fetching data from {start_str} to {end_str}")
    
    # This endpoint seems to be the one returning data for this set
    url = "https://data.elexon.co.uk/bmrs/api/v1/generation/actual/per-type/wind-and-solar"
    
    params = {
        "from": start_str,
        "to": end_str,
        "format": "json"
    }
    
    try:
        response = requests.get(url, params=params, timeout=60)
        response.raise_for_status()
        
        # Log the raw response to inspect its structure
        import json
        logging.info("--- Raw JSON Response ---")
        raw_data = response.json()
        logging.info(json.dumps(raw_data, indent=2))

        # The actual data is nested under the 'data' key
        if 'data' in raw_data:
            df = pd.DataFrame(raw_data['data'])
            logging.info(f"Successfully parsed {len(df)} records from 'data' key.")
        else:
            df = pd.DataFrame(raw_data)
            logging.info(f"Parsed {len(df)} records from root of JSON.")
            
        return df
    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to fetch data: {e}")
        return pd.DataFrame()
    except (ValueError, json.JSONDecodeError) as e:
        logging.error(f"Failed to parse JSON response: {e}")
        logging.error(f"--- Raw Response Text --- \n{response.text}")
        return pd.DataFrame()

def main():
    """Main function to run the debug process."""
    client = bigquery.Client(project=BQ_PROJECT)

    # 1. Delete the temporary table if it exists
    try:
        client.delete_table(TABLE_ID, not_found_ok=True)
        logging.info(f"Deleted old temporary table: {TABLE_ID}")
    except Exception as e:
        logging.warning(f"Could not delete old table, may not have existed: {e}")

    # 2. Create the temporary table with the correct schema
    try:
        table = bigquery.Table(TABLE_ID, schema=SCHEMA)
        client.create_table(table)
        logging.info(f"Successfully created temporary table: {TABLE_ID}")
    except Exception as e:
        logging.error(f"Failed to create temporary table: {e}")
        return

    # 3. Fetch the data
    df = fetch_wind_solar_data(START_DATE, END_DATE)
    if df.empty:
        logging.warning("No data fetched, exiting.")
        return

    logging.info("--- Data Types After Fetch ---")
    logging.info(df.dtypes)

    # 4. Explicitly ensure 'publishTime' is a string
    if 'publishTime' in df.columns:
        df['publishTime'] = df['publishTime'].astype(str)
        logging.info("Explicitly converted 'publishTime' to string.")

    logging.info("--- Data Types Before Load ---")
    logging.info(df.dtypes)
    
    # Rename columns to match BigQuery schema
    df = df.rename(columns={
        'powerSystemResourceType': 'powerSystemResourceType',
        'publishTime': 'publishTime'
    })

    # 5. Load data into BigQuery
    job_config = bigquery.LoadJobConfig(
        schema=SCHEMA,
        write_disposition="WRITE_TRUNCATE",
    )

    try:
        logging.info(f"Attempting to load {len(df)} rows into {TABLE_ID}...")
        load_job = client.load_table_from_dataframe(
            df, TABLE_ID, job_config=job_config
        )
        load_job.result()  # Wait for the job to complete
        
        if load_job.errors:
            logging.error("--- BigQuery Load Errors ---")
            for error in load_job.errors:
                logging.error(error['message'])
        else:
            logging.info("✅✅✅ SUCCESS: Data loaded successfully into temporary table! ✅✅✅")

    except Exception as e:
        logging.error(f"--- BigQuery Load Failed ---")
        logging.error(e)

if __name__ == "__main__":
    main()

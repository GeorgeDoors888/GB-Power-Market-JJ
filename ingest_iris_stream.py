import asyncio
import json
import logging
import os
import time
from datetime import datetime, timezone

import aiohttp  # <-- Newly added import
import pandas as pd
from azure.identity.aio import ClientSecretCredential
from azure.servicebus.aio import ServiceBusClient
from google.cloud import bigquery

# --- Configuration ---
TENANT_ID = os.getenv("IRIS_TENANT_ID")
CLIENT_ID = os.getenv("IRIS_CLIENT_ID")
CLIENT_SECRET = os.getenv("IRIS_CLIENT_SECRET")
SERVICEBUS_NAMESPACE = os.getenv("IRIS_SERVICEBUS_NAMESPACE")
QUEUE_NAME = os.getenv("IRIS_QUEUE_NAME")
BQ_PROJECT = os.getenv("BQ_PROJECT", "jibber-jabber-knowledge")
BQ_DATASET = "uk_energy_insights"
BQ_TABLE = "iris_stream_data"

# Define the explicit schema for the BigQuery table
# This ensures data types are correct and removes reliance on autodetect
BQ_SCHEMA = [
    bigquery.SchemaField("created_utc", "TIMESTAMP"),
    bigquery.SchemaField("correlation_id", "STRING"),
    bigquery.SchemaField("message", "STRING"),
    bigquery.SchemaField("subject", "STRING"),
    bigquery.SchemaField("message_id", "STRING"),
    bigquery.SchemaField("event_type", "STRING"),
    bigquery.SchemaField("event_time", "TIMESTAMP"),
    bigquery.SchemaField("data_version", "STRING"),
    bigquery.SchemaField("topic", "STRING"),
    bigquery.SchemaField("_ingested_utc", "TIMESTAMP"),
    bigquery.SchemaField("_message_id", "STRING"),
]

MAX_BATCH_SIZE = 500
MAX_WAIT_TIME = 10
MAX_DF_ROWS = 10000

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
)


def check_env_vars():
    required_vars = [
        "IRIS_TENANT_ID",
        "IRIS_CLIENT_ID",
        "IRIS_CLIENT_SECRET",
        "IRIS_SERVICEBUS_NAMESPACE",
        "IRIS_QUEUE_NAME",
        "BQ_PROJECT",
    ]
    missing = [v for v in required_vars if not os.getenv(v)]
    if missing:
        logging.error(f"Missing required environment variables: {', '.join(missing)}")
        exit(1)
    logging.info("✅ All required environment variables are set.")


def transform_for_bigquery(df: pd.DataFrame) -> pd.DataFrame:
    """
    Transforms the DataFrame to match the BigQuery schema.
    - Converts timestamp columns to datetime objects
    - Ensures all columns from the schema are present
    """
    # Convert timestamp columns
    for col in ["created_utc", "event_time", "_ingested_utc"]:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce", utc=True)

    # Ensure all schema columns exist, fill missing with NaT/None
    for field in BQ_SCHEMA:
        if field.name not in df.columns:
            if field.field_type in ("TIMESTAMP", "DATETIME"):
                df[field.name] = pd.NaT
            else:
                df[field.name] = None

    # Reorder columns to match schema for consistency
    schema_columns = [field.name for field in BQ_SCHEMA]
    return df[schema_columns]


def load_to_bigquery(df: pd.DataFrame):
    if df.empty:
        return
    try:
        client = bigquery.Client(project=BQ_PROJECT)
        table_id = f"{BQ_PROJECT}.{BQ_DATASET}.{BQ_TABLE}"

        # Transform the dataframe before loading
        df = transform_for_bigquery(df)

        logging.info(f"⬆️ Loading {len(df)} rows to BigQuery table {table_id}...")
        job_config = bigquery.LoadJobConfig(
            schema=BQ_SCHEMA,  # Use the explicit schema
            write_disposition="WRITE_APPEND",
        )
        job = client.load_table_from_dataframe(df, table_id, job_config=job_config)
        job.result()
        logging.info(
            f"✅ Successfully loaded {job.output_rows} rows to {table_id} at {datetime.now(timezone.utc).isoformat()}"
        )
    except Exception as e:
        logging.error(f"❌ Failed to load data to BigQuery: {e}")


def decode_servicebus_message(msg) -> tuple[dict | None, str | None]:
    """Decode a ServiceBus message body to JSON.

    Returns (json_dict, raw_text). If decoding fails, returns (None, None).
    """
    try:
        # msg.body is an iterable of body sections; join bytes-like parts
        parts: list[bytes] = []
        for p in msg.body:  # type: ignore[attr-defined]
            if isinstance(p, (bytes, bytearray, memoryview)):
                parts.append(bytes(p))
            else:
                parts.append(str(p).encode("utf-8"))
        raw = b"".join(parts).decode("utf-8", errors="replace")
        data = json.loads(raw)
        return data, raw
    except Exception:
        return None, None


async def main():
    check_env_vars()

    # Assert that all required env vars are strings for type safety
    assert isinstance(TENANT_ID, str)
    assert isinstance(CLIENT_ID, str)
    assert isinstance(CLIENT_SECRET, str)
    assert isinstance(SERVICEBUS_NAMESPACE, str)
    assert isinstance(QUEUE_NAME, str)

    fully_qualified_namespace = f"{SERVICEBUS_NAMESPACE}.servicebus.windows.net"
    credential = ClientSecretCredential(
        tenant_id=TENANT_ID, client_id=CLIENT_ID, client_secret=CLIENT_SECRET
    )

    buffered_rows = []
    last_heartbeat_time = time.time()
    last_flush_time = time.time()

    # Set flush intervals and row counts
    FLUSH_INTERVAL_SECONDS = 30  # Flush every 30 seconds regardless of row count
    FLUSH_MIN_ROWS = 500  # Or flush when 500 rows are buffered

    async with ServiceBusClient(
        fully_qualified_namespace=fully_qualified_namespace, credential=credential
    ) as servicebus_client:
        receiver = servicebus_client.get_queue_receiver(queue_name=QUEUE_NAME)
        logging.info(
            f"Connection successful. Listening for messages on queue '{QUEUE_NAME}'..."
        )
        async with receiver:
            while True:
                try:
                    received_msgs = await receiver.receive_messages(
                        max_message_count=MAX_BATCH_SIZE, max_wait_time=MAX_WAIT_TIME
                    )

                    if received_msgs:
                        logging.info(
                            f"Received a batch of {len(received_msgs)} messages."
                        )
                        last_heartbeat_time = time.time()
                        for msg in received_msgs:
                            try:
                                data, raw_body = decode_servicebus_message(msg)

                                if data and isinstance(data, dict):
                                    data["_ingested_utc"] = datetime.now(
                                        timezone.utc
                                    ).isoformat()
                                    data["_message_id"] = str(msg.message_id)
                                    buffered_rows.append(data)
                                else:
                                    logging.warning(
                                        f"[SKIP] Decoded message is not a dict (got {type(data)}); raw={raw_body[:200] if raw_body else 'N/A'}"
                                    )

                            except Exception as e:
                                logging.error(
                                    f"Error processing message {getattr(msg, 'message_id', '?')}: {e}"
                                )
                            finally:
                                await receiver.complete_message(msg)
                    else:
                        # No messages received, print heartbeat if it's been a while
                        if time.time() - last_heartbeat_time > 60:
                            logging.info(
                                "...still listening (no new messages in the last 60s)..."
                            )
                            last_heartbeat_time = time.time()

                    # Flush buffer if conditions are met
                    time_since_last_flush = time.time() - last_flush_time
                    should_flush = (len(buffered_rows) >= FLUSH_MIN_ROWS) or (
                        time_since_last_flush >= FLUSH_INTERVAL_SECONDS
                        and buffered_rows
                    )

                    if should_flush:
                        logging.info(
                            f"Flushing {len(buffered_rows)} rows. Reason: "
                            f"{'row count limit' if len(buffered_rows) >= FLUSH_MIN_ROWS else 'time limit'}."
                        )
                        df = pd.json_normalize(buffered_rows)
                        load_to_bigquery(df)
                        buffered_rows.clear()
                        last_flush_time = time.time()

                except asyncio.CancelledError:
                    logging.info("Shutdown signal received. Exiting.")
                    break
                except Exception as e:
                    logging.error(f"An unexpected error occurred in the main loop: {e}")
                    logging.info("Restarting connection in 30 seconds...")
                    await asyncio.sleep(30)

    # Final flush on graceful exit
    if buffered_rows:
        logging.info(
            f"Performing final flush of {len(buffered_rows)} rows before shutdown."
        )
        df = pd.json_normalize(buffered_rows)
        load_to_bigquery(df)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("Process interrupted by user. Shutting down.")

"""BigQuery utilities for handling quotas, retries, and optimizations."""

import logging
import time
from typing import Dict, Optional, Tuple

import pandas as pd
from google.api_core import retry
from google.api_core.exceptions import Forbidden, GoogleAPIError
from google.api_core.exceptions import ResourceExhausted as QuotaExceeded
from google.cloud import bigquery


class BigQueryQuotaManager:
    def __init__(self, client: bigquery.Client):
        self.client = client
        self.last_check = 0
        self.check_interval = 60  # Check quotas every 60 seconds
        self.quota_thresholds = {
            "LoadDataIngestBytes": 0.8,  # 80% threshold
            "StorageBytes": 0.8,
            "concurrent_queries": 0.8,
        }

    def check_quotas(self) -> Dict[str, float]:
        """Check current quota usage levels."""
        now = time.time()
        if now - self.last_check < self.check_interval:
            return {}

        query = """
        SELECT
            quota_name,
            quota_limit,
            quota_current,
            SAFE_DIVIDE(quota_current, quota_limit) as usage_ratio
        FROM region-eu.INFORMATION_SCHEMA.QUOTA_USAGE
        WHERE quota_name IN ('LoadDataIngestBytes', 'StorageBytes', 'concurrent_queries')
        """

        try:
            df = self.client.query(query).to_dataframe()
            quotas = df.set_index("quota_name")["usage_ratio"].to_dict()
            self.last_check = now
            return quotas
        except Exception as e:
            logging.warning(f"Failed to check quotas: {e}")
            return {}

    def should_throttle(self) -> Tuple[bool, Optional[float]]:
        """Check if we should throttle operations based on quota usage."""
        quotas = self.check_quotas()

        for quota_name, usage in quotas.items():
            threshold = self.quota_thresholds.get(quota_name, 0.8)
            if usage > threshold:
                wait_time = min(60, (usage - threshold) * 120)  # Dynamic wait time
                return True, wait_time

        return False, None


def create_retry_policy():
    """Create a custom retry policy for BigQuery operations."""
    return retry.Retry(
        initial=1.0,  # Start with 1 second delay
        maximum=60.0,  # Maximum 60 seconds delay
        multiplier=2.0,  # Exponential backoff
        predicate=retry.if_exception_type(QuotaExceeded, GoogleAPIError, Forbidden),
        deadline=600.0,  # 10 minutes total deadline
    )


def load_dataframe_with_retry(
    client: bigquery.Client,
    df: pd.DataFrame,
    table_id: str,
    job_config: Optional[bigquery.LoadJobConfig] = None,
    max_retries: int = 5,
    quota_manager: Optional[BigQueryQuotaManager] = None,
) -> bigquery.LoadJob:
    """Load a DataFrame to BigQuery with smart retries and quota management."""
    if quota_manager is None:
        quota_manager = BigQueryQuotaManager(client)

    retry_policy = create_retry_policy()
    attempt = 0

    while attempt < max_retries:
        try:
            # Check quotas before attempting load
            should_throttle, wait_time = quota_manager.should_throttle()
            if should_throttle and wait_time is not None:
                logging.warning(
                    f"Throttling due to high quota usage, waiting {wait_time:.1f}s"
                )
                time.sleep(wait_time)

            # Attempt the load with retry policy
            load_job = retry_policy(client.load_table_from_dataframe)(
                df, table_id, job_config=job_config
            )

            # Wait for completion
            load_job.result()

            logging.info(f"✅ Successfully loaded {len(df)} rows to {table_id}")
            return load_job

        except Exception as e:
            attempt += 1
            if attempt >= max_retries:
                logging.error(f"Failed to load data after {max_retries} attempts: {e}")
                raise

            wait_time = min(60, 2**attempt)
            logging.warning(f"Load attempt {attempt} failed, waiting {wait_time}s: {e}")
            time.sleep(wait_time)

    raise RuntimeError("Failed to load data after maximum retries")


def load_dataframe_with_schema_adaptation(
    client: bigquery.Client,
    df,
    project: str,
    dataset: str,
    table_name: str,
    write_disposition: str = "WRITE_APPEND",
    load_timeout_sec: int = 600,
    auto_add_schema_fields: bool = True,
) -> bool:
    """
    Load a DataFrame to BigQuery with improved schema adaptation.

    This function:
    1. Checks the existing schema of the table
    2. Filters DataFrame columns to match the schema
    3. Adds missing schema fields if needed
    4. Handles the bytestring length issue with hash fields

    Args:
        client: BigQuery client
        df: Pandas DataFrame to load
        project: BigQuery project ID
        dataset: BigQuery dataset ID
        table_name: BigQuery table name
        write_disposition: BigQuery write disposition
        load_timeout_sec: Timeout for load job in seconds
        auto_add_schema_fields: Whether to add missing schema fields automatically

    Returns:
        bool: True if load was successful, False otherwise
    """
    import logging
    import time

    import pandas as pd
    from google.api_core.exceptions import (
        BadRequest,
        Conflict,
        DeadlineExceeded,
        NotFound,
    )
    from google.cloud import bigquery

    if df is None or df.empty:
        logging.info(f"🟡 No data to load for {table_name}")
        return True

    table_id = f"{project}.{dataset}.{table_name}"
    df_columns = set(
        df.columns
    )  # Check if table exists and get its schema    try:        table = client.get_table(table_id)        existing_columns = {field.name for field in table.schema}        logging.info(f"Found existing table {table_id} with {len(existing_columns)} columns")    except NotFound:        # Table doesnt exist yet        existing_columns = df_columns        logging.info(f"Table {table_id} not found, will create with all columns")        # Create filtered DataFrame with only columns that exist in both    common_columns = list(df_columns & existing_columns)    if len(common_columns) < len(df_columns):        filtered_df = df[common_columns]        logging.info(f"Filtered DataFrame from {len(df_columns)} to {len(common_columns)} columns")                # Check if we have hash fields that might be causing the bytestring issue        hash_fields = {"_hash_source_cols", "_hash_key", "_source_columns", "_source_api"}        missing_hash_fields = hash_fields & (df_columns - existing_columns)                if missing_hash_fields and auto_add_schema_fields:            # We need to update the table schema to add these fields            logging.info(f"Adding missing hash fields to {table_id}: {missing_hash_fields}")                        new_fields = []            for field_name in missing_hash_fields:                new_fields.append(                    bigquery.SchemaField(                        name=field_name,                        field_type="STRING",                        mode="NULLABLE"                    )                )                        # Update schema            try:                new_schema = table.schema + new_fields                table.schema = new_schema                client.update_table(table, ["schema"])                                # Now we can include these fields                for field in missing_hash_fields:                    common_columns.append(field)                                filtered_df = df[common_columns]                logging.info(f"Updated schema and included additional columns, now using {len(common_columns)} columns")            except Exception as e:                logging.error(f"Failed to update schema: {e}")    else:        filtered_df = df        # Load the filtered DataFrame    try:        job_config = bigquery.LoadJobConfig(            write_disposition=write_disposition,        )        # Attempt the load with limited retries on quota errors        MAX_LOAD_RETRIES = 5        for attempt in range(1, MAX_LOAD_RETRIES + 1):            try:                load_job = client.load_table_from_dataframe(                    filtered_df, table_id, job_config=job_config                )                try:                    load_job.result(timeout=load_timeout_sec)                except DeadlineExceeded as te:                    # Try to cancel and fall back to splitting the batch to reduce risk                    try:                        load_job.cancel()                    except Exception:                        pass                    if len(filtered_df.index) > 1:                        logging.warning(                            "⏳ Load timed out for %s (rows=%d). Splitting batch and retrying...",                            table_id,                            len(filtered_df.index),                        )                        mid = len(filtered_df.index) // 2                        part_a = filtered_df.iloc[:mid]                        part_b = filtered_df.iloc[mid:]                                                # Recursively load smaller parts with same timeout                        ok_a = load_dataframe_with_schema_adaptation(                            client,                            part_a,                            project,                            dataset,                            table_name,                            write_disposition=write_disposition,                            load_timeout_sec=load_timeout_sec,                            auto_add_schema_fields=auto_add_schema_fields,                        )                        ok_b = load_dataframe_with_schema_adaptation(                            client,                            part_b,                            project,                            dataset,                            table_name,                            write_disposition=write_disposition,                            load_timeout_sec=load_timeout_sec,                            auto_add_schema_fields=auto_add_schema_fields,                        )                        if ok_a and ok_b:                            logging.info(                                "✅ Successfully loaded split batches to %s (rows=%d)",                                table_id,                                len(filtered_df.index),                            )                            return True                        # If split didnt help, raise to outer handler                    raise te                logging.info(                    f"✅ Successfully loaded {len(filtered_df)} rows to {table_id}"                )                # Add a small delay between batch loads to avoid hitting quota limits                time.sleep(2.0)                return True            except Exception as e:                msg = str(e)                # Backoff specifically for BigQuery quotaExceeded                if "quotaExceeded" in msg or "Quota exceeded" in msg:                    # More aggressive exponential backoff with jitter for quota issues                    import random                    base_wait = 30 * (2 ** (attempt - 1))  # 30s, 60s, 120s, 240s, 480s                    jitter = random.uniform(0.5, 1.5)  # Add 50% randomness                    wait_s = min(900, base_wait * jitter)  # Cap at 15 minutes                    logging.warning(                        f"⏳ Quota exceeded while loading {table_id} (attempt {attempt}/{MAX_LOAD_RETRIES}). Sleeping {wait_s:.1f}s before retry"                    )                    time.sleep(wait_s)                    continue                else:                    raise        # If we reach here, all retries exhausted        raise Exception(            f"Load retries exhausted for {table_id} after {MAX_LOAD_RETRIES} attempts due to quotaExceeded"        )    except Exception as e:        logging.error(f"❌ Failed to load data to {table_id}: {e}")        # Try one more time with just the basic metadata columns if they exist        try:            # Only include metadata columns that are present in the existing table            metadata_columns = {                "_dataset",                "_window_from_utc",                "_window_to_utc",                "_ingested_utc",            }            minimal_columns = list((metadata_columns & df_columns) & existing_columns)            if minimal_columns:                minimal_df = df[minimal_columns]                job_config = bigquery.LoadJobConfig(                    write_disposition=write_disposition,                )                load_job = client.load_table_from_dataframe(                    minimal_df, table_id, job_config=job_config                )                load_job.result()                logging.info(                    f"✅ Loaded minimal data ({len(minimal_columns)} columns) to {table_id}"                )                return True        except Exception as min_e:            logging.error(f"❌ Final attempt failed: {min_e}")        return False

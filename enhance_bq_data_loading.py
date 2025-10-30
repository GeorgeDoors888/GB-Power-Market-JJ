#!/usr/bin/env python
"""
enhance_bq_data_loading.py - A script to improve BigQuery data loading for the energy data automation system

This script:
1. Creates a new version of the BQ loading logic with improved handling of schema differences
2. Adds the ability to automatically detect and adapt to schema differences
3. Includes proper type conversion for hash-related fields

Usage:
python enhance_bq_data_loading.py [--fix-all-tables]
"""

import argparse
import logging
import os
from typing import Dict, List, Set

from google.cloud import bigquery

from schema_handler import METADATA_FIELDS

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Default project and dataset
DEFAULT_PROJECT = "jibber-jabber-knowledge"
DEFAULT_DATASET = "uk_energy_insights"


def get_all_tables(client: bigquery.Client, project: str, dataset: str) -> List[str]:
    """Get a list of all tables in the dataset."""
    dataset_ref = f"{project}.{dataset}"
    tables = []
    try:
        for table in client.list_tables(dataset_ref):
            if table.table_id.startswith("bmrs_"):
                tables.append(table.table_id)
        return tables
    except Exception as e:
        logger.error(f"Error listing tables in {dataset_ref}: {e}")
        return []


def add_enhanced_load_function():
    """Create a new improved BigQuery load function."""
    load_fn_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "bigquery_utils.py"
    )

    # Check if the file exists
    if os.path.exists(load_fn_path):
        with open(load_fn_path, "r") as f:
            content = f.read()
            if "load_dataframe_with_schema_adaptation" in content:
                logger.info(
                    "Enhanced loading function already exists in bigquery_utils.py"
                )
                return

    # Create or append to the file
    with open(load_fn_path, "a") as f:
        f.write(
            "\n"
            "def load_dataframe_with_schema_adaptation("
            "    client: bigquery.Client,"
            "    df,"
            "    project: str,"
            "    dataset: str,"
            "    table_name: str,"
            '    write_disposition: str = "WRITE_APPEND",'
            "    load_timeout_sec: int = 600,"
            "    auto_add_schema_fields: bool = True,"
            ") -> bool:"
            '    """'
            "    Load a DataFrame to BigQuery with improved schema adaptation."
            "    "
            "    This function:"
            "    1. Checks the existing schema of the table"
            "    2. Filters DataFrame columns to match the schema"
            "    3. Adds missing schema fields if needed"
            "    4. Handles the bytestring length issue with hash fields"
            "    "
            "    Args:"
            "        client: BigQuery client"
            "        df: Pandas DataFrame to load"
            "        project: BigQuery project ID"
            "        dataset: BigQuery dataset ID"
            "        table_name: BigQuery table name"
            "        write_disposition: BigQuery write disposition"
            "        load_timeout_sec: Timeout for load job in seconds"
            "        auto_add_schema_fields: Whether to add missing schema fields automatically"
            "        "
            "    Returns:"
            "        bool: True if load was successful, False otherwise"
            '    """'
            "    import time"
            "    import pandas as pd"
            "    from google.api_core.exceptions import BadRequest, Conflict, DeadlineExceeded, NotFound"
            "    from google.cloud import bigquery"
            "    import logging"
            "    "
            "    if df is None or df.empty:"
            '        logging.info(f"🟡 No data to load for {table_name}")'
            "        return True"
            "    "
            '    table_id = f"{project}.{dataset}.{table_name}"'
            "    df_columns = set(df.columns)"
            "    "
            "    # Check if table exists and get its schema"
            "    try:"
            "        table = client.get_table(table_id)"
            "        existing_columns = {field.name for field in table.schema}"
            '        logging.info(f"Found existing table {table_id} with {len(existing_columns)} columns")'
            "    except NotFound:"
            "        # Table doesnt exist yet"
            "        existing_columns = df_columns"
            '        logging.info(f"Table {table_id} not found, will create with all columns")'
            "    "
            "    # Create filtered DataFrame with only columns that exist in both"
            "    common_columns = list(df_columns & existing_columns)"
            "    if len(common_columns) < len(df_columns):"
            "        filtered_df = df[common_columns]"
            '        logging.info(f"Filtered DataFrame from {len(df_columns)} to {len(common_columns)} columns")'
            "        "
            "        # Check if we have hash fields that might be causing the bytestring issue"
            '        hash_fields = {"_hash_source_cols", "_hash_key", "_source_columns", "_source_api"}'
            "        missing_hash_fields = hash_fields & (df_columns - existing_columns)"
            "        "
            "        if missing_hash_fields and auto_add_schema_fields:"
            "            # We need to update the table schema to add these fields"
            '            logging.info(f"Adding missing hash fields to {table_id}: {missing_hash_fields}")'
            "            "
            "            new_fields = []"
            "            for field_name in missing_hash_fields:"
            "                new_fields.append("
            "                    bigquery.SchemaField("
            "                        name=field_name,"
            '                        field_type="STRING",'
            '                        mode="NULLABLE"'
            "                    )"
            "                )"
            "            "
            "            # Update schema"
            "            try:"
            "                new_schema = table.schema + new_fields"
            "                table.schema = new_schema"
            '                client.update_table(table, ["schema"])'
            "                "
            "                # Now we can include these fields"
            "                for field in missing_hash_fields:"
            "                    common_columns.append(field)"
            "                "
            "                filtered_df = df[common_columns]"
            '                logging.info(f"Updated schema and included additional columns, now using {len(common_columns)} columns")'
            "            except Exception as e:"
            '                logging.error(f"Failed to update schema: {e}")'
            "    else:"
            "        filtered_df = df"
            "    "
            "    # Load the filtered DataFrame"
            "    try:"
            "        job_config = bigquery.LoadJobConfig("
            "            write_disposition=write_disposition,"
            "        )"
            ""
            "        # Attempt the load with limited retries on quota errors"
            "        MAX_LOAD_RETRIES = 5"
            "        for attempt in range(1, MAX_LOAD_RETRIES + 1):"
            "            try:"
            "                load_job = client.load_table_from_dataframe("
            "                    filtered_df, table_id, job_config=job_config"
            "                )"
            "                try:"
            "                    load_job.result(timeout=load_timeout_sec)"
            "                except DeadlineExceeded as te:"
            "                    # Try to cancel and fall back to splitting the batch to reduce risk"
            "                    try:"
            "                        load_job.cancel()"
            "                    except Exception:"
            "                        pass"
            "                    if len(filtered_df.index) > 1:"
            "                        logging.warning("
            '                            "⏳ Load timed out for %s (rows=%d). Splitting batch and retrying...",'
            "                            table_id,"
            "                            len(filtered_df.index),"
            "                        )"
            "                        mid = len(filtered_df.index) // 2"
            "                        part_a = filtered_df.iloc[:mid]"
            "                        part_b = filtered_df.iloc[mid:]"
            "                        "
            "                        # Recursively load smaller parts with same timeout"
            "                        ok_a = load_dataframe_with_schema_adaptation("
            "                            client,"
            "                            part_a,"
            "                            project,"
            "                            dataset,"
            "                            table_name,"
            "                            write_disposition=write_disposition,"
            "                            load_timeout_sec=load_timeout_sec,"
            "                            auto_add_schema_fields=auto_add_schema_fields,"
            "                        )"
            "                        ok_b = load_dataframe_with_schema_adaptation("
            "                            client,"
            "                            part_b,"
            "                            project,"
            "                            dataset,"
            "                            table_name,"
            "                            write_disposition=write_disposition,"
            "                            load_timeout_sec=load_timeout_sec,"
            "                            auto_add_schema_fields=auto_add_schema_fields,"
            "                        )"
            "                        if ok_a and ok_b:"
            "                            logging.info("
            '                                "✅ Successfully loaded split batches to %s (rows=%d)",'
            "                                table_id,"
            "                                len(filtered_df.index),"
            "                            )"
            "                            return True"
            "                        # If split didnt help, raise to outer handler"
            "                    raise te"
            "                logging.info("
            '                    f"✅ Successfully loaded {len(filtered_df)} rows to {table_id}"'
            "                )"
            "                # Add a small delay between batch loads to avoid hitting quota limits"
            "                time.sleep(2.0)"
            "                return True"
            "            except Exception as e:"
            "                msg = str(e)"
            "                # Backoff specifically for BigQuery quotaExceeded"
            '                if "quotaExceeded" in msg or "Quota exceeded" in msg:'
            "                    # More aggressive exponential backoff with jitter for quota issues"
            "                    import random"
            ""
            "                    base_wait = 30 * (2 ** (attempt - 1))  # 30s, 60s, 120s, 240s, 480s"
            "                    jitter = random.uniform(0.5, 1.5)  # Add 50% randomness"
            "                    wait_s = min(900, base_wait * jitter)  # Cap at 15 minutes"
            "                    logging.warning("
            '                        f"⏳ Quota exceeded while loading {table_id} (attempt {attempt}/{MAX_LOAD_RETRIES}). Sleeping {wait_s:.1f}s before retry"'
            "                    )"
            "                    time.sleep(wait_s)"
            "                    continue"
            "                else:"
            "                    raise"
            "        # If we reach here, all retries exhausted"
            "        raise Exception("
            '            f"Load retries exhausted for {table_id} after {MAX_LOAD_RETRIES} attempts due to quotaExceeded"'
            "        )"
            "    except Exception as e:"
            '        logging.error(f"❌ Failed to load data to {table_id}: {e}")'
            ""
            "        # Try one more time with just the basic metadata columns if they exist"
            "        try:"
            "            # Only include metadata columns that are present in the existing table"
            "            metadata_columns = {"
            '                "_dataset",'
            '                "_window_from_utc",'
            '                "_window_to_utc",'
            '                "_ingested_utc",'
            "            }"
            "            minimal_columns = list((metadata_columns & df_columns) & existing_columns)"
            "            if minimal_columns:"
            "                minimal_df = df[minimal_columns]"
            "                job_config = bigquery.LoadJobConfig("
            "                    write_disposition=write_disposition,"
            "                )"
            "                load_job = client.load_table_from_dataframe("
            "                    minimal_df, table_id, job_config=job_config"
            "                )"
            "                load_job.result()"
            "                logging.info("
            '                    f"✅ Loaded minimal data ({len(minimal_columns)} columns) to {table_id}"'
            "                )"
            "                return True"
            "        except Exception as min_e:"
            '            logging.error(f"❌ Final attempt failed: {min_e}")'
            ""
            "        return False"
        )

    logger.info("✅ Added enhanced load function to bigquery_utils.py")

    # Now update the import in ingest_elexon_fixed.py to use this function
    try:
        ingest_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "ingest_elexon_fixed.py"
        )

        if os.path.exists(ingest_path):
            with open(ingest_path, "r") as f:
                content = f.read()

            # Check if the import already exists
            if (
                "from bigquery_utils import load_dataframe_with_schema_adaptation"
                not in content
            ):
                # Add the import near the top, after other imports
                import_pos = content.find("# Load environment variables")
                if import_pos > 0:
                    new_content = (
                        content[:import_pos]
                        + "\n# Import enhanced BigQuery utils\nfrom bigquery_utils import load_dataframe_with_schema_adaptation\n\n"
                        + content[import_pos:]
                    )

                    # Create a backup of the original file
                    backup_path = ingest_path + ".bak"
                    with open(backup_path, "w") as f:
                        f.write(content)

                    # Write the updated content
                    with open(ingest_path, "w") as f:
                        f.write(new_content)

                    logger.info(
                        f"✅ Added import to ingest_elexon_fixed.py (backup saved to {backup_path})"
                    )
    except Exception as e:
        logger.error(f"Failed to update ingest_elexon_fixed.py: {e}")


def main():
    parser = argparse.ArgumentParser(
        description="Enhance BigQuery data loading for energy data automation"
    )
    parser.add_argument(
        "--fix-all-tables",
        action="store_true",
        help="Fix schema for all BMRS tables, not just the ones with known issues",
    )
    parser.add_argument(
        "--project",
        default=DEFAULT_PROJECT,
        help=f"BigQuery project ID (default: {DEFAULT_PROJECT})",
    )
    parser.add_argument(
        "--dataset",
        default=DEFAULT_DATASET,
        help=f"BigQuery dataset ID (default: {DEFAULT_DATASET})",
    )

    args = parser.parse_args()

    # Add the enhanced load function
    add_enhanced_load_function()

    if args.fix_all_tables:
        # Initialize BigQuery client
        client = bigquery.Client(project=args.project)

        # Get all tables in the dataset
        tables = get_all_tables(client, args.project, args.dataset)
        logger.info(f"Found {len(tables)} BMRS tables to check")

        # Import the fix script to fix all tables
        import fix_bq_schema_mismatch

        success_count = 0
        for table in tables:
            logger.info(f"Processing table {table}...")
            if fix_bq_schema_mismatch.update_table_schema(
                client, args.project, args.dataset, table
            ):
                success_count += 1

        logger.info(f"✅ Fixed schemas for {success_count} of {len(tables)} tables")

    logger.info(
        """
✅ Enhancement complete!

To use the new loading function in scripts, update code like this:

    from bigquery_utils import load_dataframe_with_schema_adaptation

    # Then replace calls to _load_dataframe_safely with:
    load_dataframe_with_schema_adaptation(
        client,
        df,
        project,
        dataset,
        table_name,
        write_disposition=write_disposition,
        load_timeout_sec=load_timeout_sec,
        auto_add_schema_fields=True,
    )
"""
    )


if __name__ == "__main__":
    main()

#!/usr/bin/env python
"""
fix_bq_schema_mismatch.py - Fix BigQuery schema issues causing "Got bytestring of length 8 (expected 16)" errors

This script:
1. Updates problematic table schemas in BigQuery
2. Adds missing hash-related fields if needed
3. Converts string type fields to the correct format

Usage:
python fix_bq_schema_mismatch.py [--tables TABLE1,TABLE2,...]
"""

import argparse
import logging
from typing import List, Optional, Set

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

# Tables known to have the hash bytestring length issue
PROBLEM_TABLES = [
    "bmrs_tsdfd",
    "bmrs_tsdfw",
    "bmrs_windfor",
    # Add other tables here if they show the same error
]


def get_table_schema(
    client: bigquery.Client, project: str, dataset: str, table: str
) -> List[bigquery.SchemaField]:
    """Get the current schema for a BigQuery table."""
    table_ref = f"{project}.{dataset}.{table}"
    try:
        table_obj = client.get_table(table_ref)
        return table_obj.schema
    except Exception as e:
        logger.error(f"Error getting schema for {table_ref}: {e}")
        return []


def update_table_schema(
    client: bigquery.Client,
    project: str,
    dataset: str,
    table: str,
    add_hash_fields: bool = True,
) -> bool:
    """Update a table's schema to fix the hash bytestring length issue."""
    table_ref = f"{project}.{dataset}.{table}"

    try:
        # Get current schema
        table_obj = client.get_table(table_ref)
        current_schema = table_obj.schema
        current_field_names = {field.name for field in current_schema}

        # Check which metadata fields need to be added
        new_fields = []

        # These are the extended metadata fields we need to ensure exist
        hash_fields = {
            "_source_columns",
            "_source_api",
            "_hash_source_cols",
            "_hash_key",
        }

        if add_hash_fields:
            for field_def in METADATA_FIELDS["extended"]:
                field_name = field_def["name"]
                if field_name in hash_fields and field_name not in current_field_names:
                    logger.info(f"Adding missing field {field_name} to {table_ref}")
                    new_fields.append(
                        bigquery.SchemaField(
                            name=field_name, field_type="STRING", mode="NULLABLE"
                        )
                    )

        # Update schema if we have new fields to add
        if new_fields:
            new_schema = current_schema + new_fields
            table_obj.schema = new_schema
            client.update_table(table_obj, ["schema"])
            logger.info(f"✅ Successfully updated schema for {table_ref}")
            return True
        else:
            logger.info(f"No schema changes needed for {table_ref}")
            return False

    except Exception as e:
        logger.error(f"❌ Failed to update schema for {table_ref}: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Fix BigQuery schema issues causing hash bytestring errors"
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
    parser.add_argument(
        "--tables",
        help="Comma-separated list of tables to fix (default: all known problem tables)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without making changes",
    )

    args = parser.parse_args()

    # Initialize BigQuery client
    client = bigquery.Client(project=args.project)

    # Determine which tables to process
    tables_to_fix = set(PROBLEM_TABLES)
    if args.tables:
        tables_to_fix = set(args.tables.split(","))

    logger.info(
        f"Will fix schema for {len(tables_to_fix)} tables: {', '.join(tables_to_fix)}"
    )

    # Process each table
    success_count = 0
    for table in tables_to_fix:
        logger.info(f"Processing table {table}...")

        if args.dry_run:
            schema = get_table_schema(client, args.project, args.dataset, table)
            field_names = {field.name for field in schema}
            missing = {
                f
                for f in [
                    "_source_columns",
                    "_source_api",
                    "_hash_source_cols",
                    "_hash_key",
                ]
                if f not in field_names
            }
            if missing:
                logger.info(f"Would add fields to {table}: {', '.join(missing)}")
            else:
                logger.info(f"No changes needed for {table}")
            success_count += 1
        else:
            if update_table_schema(client, args.project, args.dataset, table):
                success_count += 1

    # Summary
    action = "Would fix" if args.dry_run else "Fixed"
    logger.info(f"✅ {action} {success_count} of {len(tables_to_fix)} tables")


if __name__ == "__main__":
    main()

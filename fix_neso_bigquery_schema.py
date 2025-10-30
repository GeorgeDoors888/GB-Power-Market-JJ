#!/usr/bin/env python3
"""
NESO Data BigQuery Schema Fixer
===============================

Fixes schema issues with NESO data for BigQuery compliance:
- Field names with invalid characters
- Field names too long (>300 chars)
- Nested field issues
- Data type compatibility
"""

import json
import logging
import os
import re
import sqlite3

import pandas as pd
from google.cloud import bigquery
from google.cloud.exceptions import NotFound

# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)


class NESOBigQuerySchemaFixer:
    def __init__(self, sqlite_path="neso_data_comprehensive/neso_comprehensive.sqlite"):
        self.sqlite_path = sqlite_path
        self.client = bigquery.Client(project="jibber-jabber-knowledge")
        self.dataset_id = "uk_energy_insights"

    def clean_field_name(self, field_name):
        """Clean field names to be BigQuery compliant"""
        # Replace invalid characters with underscores
        cleaned = re.sub(r"[^a-zA-Z0-9_]", "_", str(field_name))

        # Ensure it starts with letter or underscore
        if cleaned and cleaned[0].isdigit():
            cleaned = f"field_{cleaned}"

        # Truncate to 300 characters max
        if len(cleaned) > 300:
            cleaned = cleaned[:300]

        # Remove trailing underscores
        cleaned = cleaned.rstrip("_")

        # Ensure it's not empty
        if not cleaned:
            cleaned = "unknown_field"

        return cleaned.lower()

    def get_bigquery_schema_from_dataframe(self, df):
        """Generate BigQuery schema from pandas DataFrame"""
        schema = []

        for column in df.columns:
            clean_name = self.clean_field_name(column)

            # Determine BigQuery type from pandas dtype
            dtype = df[column].dtype

            if pd.api.types.is_integer_dtype(dtype):
                bq_type = "INTEGER"
            elif pd.api.types.is_float_dtype(dtype):
                bq_type = "FLOAT"
            elif pd.api.types.is_bool_dtype(dtype):
                bq_type = "BOOLEAN"
            elif pd.api.types.is_datetime64_any_dtype(dtype):
                bq_type = "TIMESTAMP"
            else:
                bq_type = "STRING"

            schema.append(bigquery.SchemaField(clean_name, bq_type))

        return schema

    def fix_dataframe_columns(self, df):
        """Fix DataFrame column names for BigQuery compliance"""
        df_fixed = df.copy()

        # Create column mapping
        column_mapping = {}
        for col in df.columns:
            clean_col = self.clean_field_name(col)
            column_mapping[col] = clean_col

        # Rename columns
        df_fixed = df_fixed.rename(columns=column_mapping)

        # Handle nested data in intensity.forecast field specifically
        for col in df_fixed.columns:
            if "intensity" in col.lower() and "forecast" in col.lower():
                # If this contains nested JSON, flatten it
                if df_fixed[col].dtype == "object":
                    try:
                        # Try to parse as JSON and flatten
                        for idx, value in df_fixed[col].items():
                            if isinstance(value, str) and value.startswith("{"):
                                try:
                                    parsed = json.loads(value)
                                    if isinstance(parsed, dict):
                                        # Convert to string representation
                                        df_fixed.at[idx, col] = str(parsed)
                                except:
                                    pass
                    except:
                        pass

        return df_fixed, column_mapping

    def upload_table_to_bigquery(self, table_name, df, replace=True):
        """Upload a single table to BigQuery with schema fixing"""
        try:
            logger.info(f"📤 Processing table: {table_name}")

            if df.empty:
                logger.warning(f"⚠️ Table {table_name} is empty, skipping")
                return False

            # Fix column names and data
            df_fixed, column_mapping = self.fix_dataframe_columns(df)

            # Generate schema
            schema = self.get_bigquery_schema_from_dataframe(df_fixed)

            # Clean table name for BigQuery
            clean_table_name = self.clean_field_name(table_name)
            table_id = (
                f"{self.client.project}.{self.dataset_id}.neso_{clean_table_name}"
            )

            # Configure job
            job_config = bigquery.LoadJobConfig(
                schema=schema,
                write_disposition="WRITE_TRUNCATE" if replace else "WRITE_APPEND",
            )

            # Upload
            job = self.client.load_table_from_dataframe(
                df_fixed, table_id, job_config=job_config
            )
            job.result()  # Wait for completion

            logger.info(f"✅ Uploaded {clean_table_name}: {len(df_fixed)} rows")

            # Log column mappings if any were changed
            changed_columns = {k: v for k, v in column_mapping.items() if k != v}
            if changed_columns:
                logger.info(f"📝 Column mappings for {table_name}:")
                for old, new in list(changed_columns.items())[:5]:  # Show first 5
                    logger.info(f"   {old} → {new}")

            return True

        except Exception as e:
            logger.error(f"❌ Failed to upload {table_name}: {e}")
            return False

    def process_all_neso_tables(self):
        """Process all tables from NESO SQLite database"""
        if not os.path.exists(self.sqlite_path):
            logger.error(f"❌ SQLite database not found: {self.sqlite_path}")
            return

        logger.info(f"🚀 Starting NESO BigQuery Schema Fix")
        logger.info(f"📊 Source: {self.sqlite_path}")
        logger.info(f"☁️ Target: {self.client.project}.{self.dataset_id}")

        # Connect to SQLite
        conn = sqlite3.connect(self.sqlite_path)

        # Get all table names
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]

        logger.info(f"📋 Found {len(tables)} tables to process")

        successful_uploads = 0
        failed_uploads = 0

        for table_name in tables:
            try:
                # Read table
                df = pd.read_sql_query(f'SELECT * FROM "{table_name}"', conn)

                # Upload to BigQuery
                if self.upload_table_to_bigquery(table_name, df):
                    successful_uploads += 1
                else:
                    failed_uploads += 1

            except Exception as e:
                logger.error(f"❌ Error processing {table_name}: {e}")
                failed_uploads += 1

        conn.close()

        logger.info(f"🎯 NESO BigQuery Upload Complete!")
        logger.info(f"✅ Successful: {successful_uploads}")
        logger.info(f"❌ Failed: {failed_uploads}")
        logger.info(
            f"📊 Success rate: {successful_uploads/(successful_uploads+failed_uploads)*100:.1f}%"
        )

        return successful_uploads, failed_uploads


def main():
    """Main execution function"""
    fixer = NESOBigQuerySchemaFixer()

    # Check if BigQuery dataset exists
    try:
        fixer.client.get_dataset(fixer.dataset_id)
        logger.info(f"✅ Dataset {fixer.dataset_id} exists")
    except NotFound:
        logger.error(f"❌ Dataset {fixer.dataset_id} not found")
        return

    # Process all tables
    successful, failed = fixer.process_all_neso_tables()

    if successful > 0:
        logger.info(
            f"🎉 Schema fixing complete! {successful} tables uploaded successfully"
        )
    else:
        logger.error(f"😞 No tables uploaded successfully")


if __name__ == "__main__":
    main()

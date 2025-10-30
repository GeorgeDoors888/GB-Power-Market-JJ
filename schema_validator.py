"""Schema validation utilities"""

import logging
from typing import Dict, List, Optional

import pandas as pd
from google.cloud import bigquery

logger = logging.getLogger(__name__)


def validate_schema_compatibility(
    df: pd.DataFrame, target_schema: List[bigquery.SchemaField], source_year: int
) -> tuple[bool, Optional[str]]:
    """Validate if DataFrame schema is compatible with target BigQuery schema"""

    # Check required columns
    required_cols = {field.name for field in target_schema if field.mode == "REQUIRED"}
    missing_cols = required_cols - set(df.columns)
    if missing_cols:
        return False, f"Missing required columns: {missing_cols}"

    # Check data types
    type_map = {
        "STRING": (str, object),
        "INTEGER": (int, "int64"),
        "FLOAT": (float, "float64"),
        "TIMESTAMP": (pd.Timestamp, "datetime64[ns]"),
    }

    for field in target_schema:
        if field.name not in df.columns:
            continue

        col_dtype = df[field.name].dtype
        col_type = df[field.name].dtype.type
        expected_types = type_map.get(field.field_type, (object,))

        if not any(
            issubclass(col_type, t) if isinstance(t, type) else str(col_dtype) == t
            for t in expected_types
        ):
            return (
                False,
                f"Column {field.name} has type {col_dtype}, expected {field.field_type}",
            )

    # Year-specific validations
    if source_year < 2025:
        required_meta = {
            "_source_columns",
            "_source_api",
            "_hash_source_cols",
            "_hash_key",
        }
        missing_meta = required_meta - set(df.columns)
        if missing_meta:
            return (
                False,
                f"Missing required metadata columns for year {source_year}: {missing_meta}",
            )

    return True, None


def get_schema_for_year(dataset: str, year: int) -> List[bigquery.SchemaField]:
    """Get the appropriate schema for a dataset and year"""

    # Base metadata fields
    base_fields = [
        bigquery.SchemaField("_dataset", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("_window_from_utc", "TIMESTAMP", mode="REQUIRED"),
        bigquery.SchemaField("_window_to_utc", "TIMESTAMP", mode="REQUIRED"),
        bigquery.SchemaField("_ingested_utc", "TIMESTAMP", mode="REQUIRED"),
    ]

    # Additional fields for pre-2025
    if year < 2025:
        base_fields.extend(
            [
                bigquery.SchemaField("_source_columns", "STRING", mode="NULLABLE"),
                bigquery.SchemaField("_source_api", "STRING", mode="NULLABLE"),
                bigquery.SchemaField("_hash_source_cols", "STRING", mode="NULLABLE"),
                bigquery.SchemaField("_hash_key", "STRING", mode="NULLABLE"),
            ]
        )

    # Dataset-specific fields
    dataset_fields = {
        "FREQ": [
            bigquery.SchemaField("dataset", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("measurementTime", "TIMESTAMP", mode="REQUIRED"),
            bigquery.SchemaField("frequency", "FLOAT", mode="REQUIRED"),
        ],
        # Add other datasets as needed
    }

    return base_fields + dataset_fields.get(dataset, [])

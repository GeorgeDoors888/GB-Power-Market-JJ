import json
import logging
import os
from datetime import datetime

import pandas as pd

from ingest_elexon_fixed import CHUNK_RULES, _fetch_bmrs

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

# --- Configuration ---
YEARS_TO_GENERATE = [2022, 2023, 2024, 2025]
DATASETS_TO_GENERATE = sorted(list(CHUNK_RULES.keys()))
SCHEMA_DIR = "schemas"
# Use a consistent sample date in the middle of the year to avoid edge cases
SAMPLE_DATE_STR = "-06-01"


def infer_bq_schema_from_df(df: pd.DataFrame) -> list[dict]:
    """
    Infers a BigQuery schema from a pandas DataFrame.
    Excludes any columns that start with an underscore.
    Attempts to identify date/time columns and set their type to TIMESTAMP.
    """
    schema = []
    # List of column name fragments that indicate a date or timestamp
    datetime_patterns = ["date", "time", "period"]

    for col, dtype in df.dtypes.items():
        col_str = str(col)
        if col_str.startswith("_"):
            continue

        bq_type = "STRING"  # Default

        # Check if the column name suggests it's a date/time
        is_datetime_col = any(
            pattern in col_str.lower() for pattern in datetime_patterns
        )

        if is_datetime_col:
            try:
                # Attempt to convert to datetime to confirm
                pd.to_datetime(df[col], errors="raise")
                bq_type = "TIMESTAMP"
            except (ValueError, TypeError):
                # If conversion fails, fall back to original dtype inference
                pass

        if bq_type == "STRING":  # If not already identified as TIMESTAMP
            if pd.api.types.is_integer_dtype(dtype):
                bq_type = "INTEGER"
            elif pd.api.types.is_float_dtype(dtype):
                bq_type = "FLOAT"
            elif pd.api.types.is_bool_dtype(dtype):
                bq_type = "BOOLEAN"
            # This case is now handled by the pre-check, but left as a fallback
            elif pd.api.types.is_datetime64_any_dtype(dtype):
                bq_type = "TIMESTAMP"

        schema.append({"name": col_str, "type": bq_type, "mode": "NULLABLE"})

    return schema


def generate_schema_for_dataset(year: int, dataset: str):
    """
    Fetches data for a given year and dataset and generates a BQ schema file.
    """
    logging.info(f"--- Generating schema for: Dataset={dataset}, Year={year} ---")

    # 1. Fetch actual data from the API for a sample date in that year
    try:
        start_dt = datetime.fromisoformat(f"{year}{SAMPLE_DATE_STR}T00:00:00+00:00")
        end_dt = datetime.fromisoformat(f"{year}{SAMPLE_DATE_STR}T01:00:00+00:00")

        df = _fetch_bmrs(dataset, start_dt, end_dt)

        if df is None or df.empty:
            logging.warning(
                f"[{dataset}/{year}] No data returned from API. Cannot generate schema."
            )
            return

        api_columns = set(df.columns)
        logging.info(
            f"[{dataset}/{year}] Fetched {len(df)} rows with {len(api_columns)} columns."
        )

    except Exception as e:
        logging.error(f"[{dataset}/{year}] Failed to fetch data from API: {e}")
        return

    # 2. Infer the schema from the DataFrame
    try:
        bq_schema = infer_bq_schema_from_df(df)
        if not bq_schema:
            logging.warning(
                f"[{dataset}/{year}] Inferred schema is empty. Skipping file generation."
            )
            return

        logging.info(
            f"[{dataset}/{year}] Inferred schema with {len(bq_schema)} fields."
        )

    except Exception as e:
        logging.error(f"[{dataset}/{year}] Failed to infer schema: {e}")
        return

    # 3. Write the schema to a JSON file
    try:
        year_dir = os.path.join(SCHEMA_DIR, str(year))
        os.makedirs(year_dir, exist_ok=True)

        # Use the safe table name convention from the main script for the filename
        safe_dataset_name = f"bmrs_{dataset.lower()}"
        schema_path = os.path.join(year_dir, f"{safe_dataset_name}.json")

        with open(schema_path, "w") as f:
            json.dump(bq_schema, f, indent=2)

        logging.info(
            f"✅ [{dataset}/{year}] Successfully wrote schema to {schema_path}"
        )

    except Exception as e:
        logging.error(f"[{dataset}/{year}] Failed to write schema file: {e}")


def main():
    """
    Main function to iterate through all specified years and datasets.
    """
    for year in YEARS_TO_GENERATE:
        for dataset in DATASETS_TO_GENERATE:
            generate_schema_for_dataset(year, dataset)
            print("-" * 80)


if __name__ == "__main__":
    main()

import logging
from datetime import datetime

import pandas as pd

from ingest_elexon_fixed import CHUNK_RULES, _fetch_bmrs
from schema_handler import get_schema_for_dataset_and_year

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

# --- Configuration ---
YEARS_TO_TEST = [2022, 2023, 2024, 2025]
DATASETS_TO_TEST = sorted(list(CHUNK_RULES.keys()))
# Use a consistent sample date in the middle of the year to avoid edge cases
SAMPLE_DATE_STR = "-06-01"


def investigate_schema_for_year(year: int, dataset: str):
    """
    Fetches data for a given year and dataset, compares it to the local schema,
    and reports any discrepancies.
    """
    logging.info(f"--- Investigating: Dataset={dataset}, Year={year} ---")

    # 1. Get the expected schema from local files
    try:
        schema_fields = get_schema_for_dataset_and_year(dataset, year)
        if not schema_fields:
            logging.warning(
                f"[{dataset}/{year}] No local schema found. Skipping comparison."
            )
            # Still fetch data to see what the API returns
            schema_columns = set()
        else:
            # Extract column names from the schema definition
            schema_columns = {
                field.get("name") for field in schema_fields if field.get("name")
            }
            logging.info(
                f"[{dataset}/{year}] Loaded local schema with {len(schema_columns)} columns."
            )
            logging.debug(f"Expected columns: {sorted(list(schema_columns))}")

    except Exception as e:
        logging.error(f"[{dataset}/{year}] Failed to load local schema: {e}")
        return

    # 2. Fetch actual data from the API for a sample date in that year
    try:
        start_dt = datetime.fromisoformat(f"{year}{SAMPLE_DATE_STR}T00:00:00+00:00")
        end_dt = datetime.fromisoformat(f"{year}{SAMPLE_DATE_STR}T01:00:00+00:00")

        # Use the same fetch function as the main script
        df = _fetch_bmrs(dataset, start_dt, end_dt)

        if df is None or df.empty:
            logging.warning(
                f"[{dataset}/{year}] No data returned from API for sample date."
            )
            return

        api_columns = set(df.columns)
        logging.info(
            f"[{dataset}/{year}] Fetched {len(df)} rows from API with {len(api_columns)} columns."
        )
        logging.debug(f"API columns: {sorted(list(api_columns))}")

    except Exception as e:
        logging.error(f"[{dataset}/{year}] Failed to fetch data from API: {e}")
        return

    # 3. Compare the schemas and report differences
    if not schema_columns:
        logging.info(
            f"[{dataset}/{year}] API returned columns: {sorted(list(api_columns))}"
        )
        return

    missing_in_api = schema_columns - api_columns
    extra_in_api = api_columns - schema_columns

    if not missing_in_api and not extra_in_api:
        logging.info(f"✅ [{dataset}/{year}] Schema is a perfect match!")
    else:
        if missing_in_api:
            logging.error(
                f"❌ [{dataset}/{year}] Mismatch! Columns in local schema but MISSING from API data:"
            )
            for col in sorted(list(missing_in_api)):
                logging.error(f"  - {col}")
        if extra_in_api:
            logging.warning(
                f"⚠️ [{dataset}/{year}] Mismatch! Columns in API data but NOT in local schema:"
            )
            for col in sorted(list(extra_in_api)):
                logging.warning(f"  - {col}")


def main():
    """
    Main function to iterate through all specified years and datasets.
    """
    for year in YEARS_TO_TEST:
        for dataset in DATASETS_TO_TEST:
            investigate_schema_for_year(year, dataset)
            print("-" * 80)


if __name__ == "__main__":
    main()

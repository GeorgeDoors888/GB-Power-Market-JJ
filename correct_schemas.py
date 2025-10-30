import json
import logging
import os

import pandas as pd

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

# --- Configuration ---
INPUT_CSV = "schema_comparison_report.csv"
OUTPUT_DIR = "schemas/corrected"
BASE_YEAR = "2025"  # Use 2025 as the source of truth for schemas

# --- BMRS Dataset to Filename Mapping ---
# This mapping helps convert the 'dataset' column from the CSV to the expected JSON filename.
# It's not exhaustive and may need additions if new datasets are processed.
DATASET_TO_FILENAME_MAP = {
    "BOALF": "bmrs_boalf",
    "BOD": "bmrs_bod",
    "COSTS": "bmrs_costs",
    "DISBSAD": "bmrs_disbsad",
    "FOU2T14D": "bmrs_fou2t14d",
    "FOU2T3YW": "bmrs_fou2t3yw",
    "FREQ": "bmrs_freq",
    "FUELHH": "bmrs_fuelhh",
    "FUELINST": "bmrs_fuelinst",
    "IMBALNGC": "bmrs_imbalngc",
    "INDDEM": "bmrs_inddem",
    "INDGEN": "bmrs_indgen",
    "INDO": "bmrs_indo",
    "ITSDO": "bmrs_itsdo",
    "MELNGC": "bmrs_melngc",
    "MELS": "bmrs_mels",
    "MID": "bmrs_mid",
    "MILS": "bmrs_mils",
    "MNZT": "bmrs_mnzt",
    "MZT": "bmrs_mzt",
    "NDF": "bmrs_ndf",
    "NDFD": "bmrs_ndfd",
    "NDFW": "bmrs_ndfw",
    "NDZ": "bmrs_ndz",
    "NETBSAD": "bmrs_netbsad",
    "NONBM": "bmrs_nonbm",
    "NOU2T14D": "bmrs_nou2t14d",
    "NOU2T3YW": "bmrs_nou2t3yw",
    "OCNMF3Y": "bmrs_ocnmf3y",
    "OCNMF3Y2": "bmrs_ocnmf3y2",
    "OCNMFD": "bmrs_ocnmfd",
    "OCNMFD2": "bmrs_ocnmfd2",
    "PN": "bmrs_pn",
    "QAS": "bmrs_qas",
    "QPN": "bmrs_qpn",
    "RURE": "bmrs_rure",
    "SEL": "bmrs_sel",
    "TEMP": "bmrs_temp",
    "TSDF": "bmrs_tsdf",
    "TSDFD": "bmrs_tsdfd",
    "TSDFW": "bmrs_tsdfw",
    "UOU2T14D": "bmrs_uou2t14d",
    "UOU2T3YW": "bmrs_uou2t3yw",
    "WINDFOR": "bmrs_windfor",
    # Entries that were unavailable in the sample but might have schemas
    "RDRI": "bmrs_rdri_new_schema",
}


def pandas_to_bq_type(dtype: str, column_name: str) -> str:
    """Converts a pandas dtype to a BigQuery data type."""
    dtype = str(dtype).lower()
    column_name = column_name.lower()

    if "date" in column_name or "time" in column_name:
        return "TIMESTAMP"
    if dtype == "int64":
        return "INTEGER"
    if dtype == "float64":
        return "FLOAT"
    if dtype == "bool":
        return "BOOLEAN"
    return "STRING"


def generate_corrected_schemas():
    """
    Reads the schema comparison report and generates a new set of BigQuery
    schema files based on the most recent year's data types.
    """
    logging.info(
        f"Starting schema correction process. Using '{BASE_YEAR}' as the source of truth."
    )

    try:
        df = pd.read_csv(INPUT_CSV)
    except FileNotFoundError:
        logging.error(f"Critical error: Input file '{INPUT_CSV}' not found. Aborting.")
        return

    if not os.path.exists(OUTPUT_DIR):
        logging.info(f"Creating output directory: '{OUTPUT_DIR}'")
        os.makedirs(OUTPUT_DIR)

    datasets = df["dataset"].unique()
    logging.info(f"Found {len(datasets)} unique datasets in the report.")

    generated_files = 0
    for dataset_name in datasets:
        # Filter for the current dataset and drop columns that don't exist in the base year
        dataset_df = df[df["dataset"] == dataset_name].copy()
        dataset_df = dataset_df[dataset_df[BASE_YEAR] != "NOT_PRESENT"]

        if dataset_df.empty:
            logging.warning(
                f"Skipping dataset '{dataset_name}': No columns found for the base year '{BASE_YEAR}'."
            )
            continue

        schema_fields = []
        for _, row in dataset_df.iterrows():
            col_name = row["column_name"]
            pd_type = row[BASE_YEAR]
            bq_type = pandas_to_bq_type(pd_type, col_name)

            schema_fields.append(
                {"name": col_name, "type": bq_type, "mode": "NULLABLE"}
            )

        # Get the correct filename for the JSON
        filename_base = DATASET_TO_FILENAME_MAP.get(dataset_name)
        if not filename_base:
            logging.warning(f"Skipping '{dataset_name}': No filename mapping found.")
            continue

        output_path = os.path.join(OUTPUT_DIR, f"{filename_base}.json")

        try:
            with open(output_path, "w") as f:
                json.dump(schema_fields, f, indent=4)
            logging.info(
                f"Successfully generated schema for '{dataset_name}' at '{output_path}'"
            )
            generated_files += 1
        except Exception as e:
            logging.error(f"Failed to write schema for '{dataset_name}': {e}")

    logging.info(
        f"\nSchema correction process complete. Generated {generated_files} schema files in '{OUTPUT_DIR}'."
    )


if __name__ == "__main__":
    generate_corrected_schemas()

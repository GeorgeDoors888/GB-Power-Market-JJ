import os

from dotenv import load_dotenv
from google.api_core.exceptions import NotFound
from google.cloud import bigquery

# Load environment variables from .env file
load_dotenv()

# This list is derived from the CHUNK_RULES dictionary in ingest_elexon_fixed.py
DATASET_NAMES = [
    "BOD",
    "B1770",
    "BOALF",
    "NETBSAD",
    "DISBSAD",
    "IMBALNGC",
    "PN",
    "QPN",
    "QAS",
    "RDRE",
    "RDRI",
    "RURE",
    "RURI",
    "FREQ",
    "FUELINST",
    "FUELHH",
    "TEMP",
    "B1610",
    "NDF",
    "NDFD",
    "NDFW",
    "TSDF",
    "TSDFD",
    "TSDFW",
    "INDDEM",
    "INDGEN",
    "ITSDO",
    "INDO",
    "MELNGC",
    "WINDFOR",
    "WIND",
    "FOU2T14D",
    "FOU2T3YW",
    "NOU2T14D",
    "NOU2T3YW",
    "UOU2T14D",
    "UOU2T3YW",
    "SEL",
    "SIL",
    "OCNMF3Y",
    "OCNMF3Y2",
    "OCNMFD",
    "OCNMFD2",
    "INTBPT",
    "MIP",
    "MID",
    "MILS",
    "MELS",
    "MDP",
    "MDV",
    "MNZT",
    "MZT",
    "NTB",
    "NTO",
    "NDZ",
    "NONBM",
]


def list_all_table_schemas(project_id, dataset_id):
    """
    Connects to BigQuery and lists the schema for all potential tables.
    """
    try:
        if not os.getenv("GOOGLE_APPLICATION_CREDENTIALS"):
            print("Error: GOOGLE_APPLICATION_CREDENTIALS environment variable not set.")
            return

        client = bigquery.Client(project=project_id)

        print(
            f"--- Querying Schemas for Project: {project_id}, Dataset: {dataset_id} ---"
        )

        for name in DATASET_NAMES:
            # The script creates table names like 'bmrs_bod'
            table_name = f"bmrs_{name.lower()}"
            table_id = f"{project_id}.{dataset_id}.{table_name}"

            try:
                table = client.get_table(table_id)
                print(f"\n--- Headers for table: {table_name} ---")
                for schema_field in table.schema:
                    print(f"- {schema_field.name} ({schema_field.field_type})")
            except NotFound:
                print(f"\n--- Table '{table_name}' does not exist yet. ---")
            except Exception as e:
                print(f"\n--- Could not retrieve schema for '{table_name}': {e} ---")

    except Exception as e:
        print(f"An error occurred: {e}")


if __name__ == "__main__":
    PROJECT = "jibber-jabber-knowledge"
    DATASET = "uk_energy_insights"
    list_all_table_schemas(PROJECT, DATASET)

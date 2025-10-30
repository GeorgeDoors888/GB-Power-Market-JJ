import os
from datetime import datetime
from typing import Dict, List, Optional, Tuple

from google.api_core.exceptions import NotFound
from google.cloud import bigquery

# Datasets to check, derived from the ingest_elexon_fixed.py script
CHUNK_RULES = {
    "BOD": "1h",
    "B1770": "1d",
    "BOALF": "1d",
    "COSTS": "1d",
    "NETBSAD": "1d",
    "DISBSAD": "1d",
    "IMBALNGC": "7d",
    "PN": "1d",
    "QPN": "1d",
    "QAS": "1d",
    "RDRE": "1d",
    "RDRI": "1d",
    "RURE": "1d",
    "RURI": "1d",
    "FREQ": "1d",
    "FUELINST": "1d",
    "FUELHH": "1d",
    "TEMP": "7d",
    "B1610": "7d",
    "B1630": "1d",
    "NDF": "7d",
    "NDFD": "7d",
    "NDFW": "7d",
    "TSDF": "7d",
    "TSDFD": "7d",
    "TSDFW": "7d",
    "INDDEM": "7d",
    "INDGEN": "7d",
    "ITSDO": "7d",
    "INDO": "7d",
    "MELNGC": "7d",
    "WINDFOR": "7d",
    "WIND": "7d",
    "FOU2T14D": "7d",
    "FOU2T3YW": "7d",
    "NOU2T14D": "7d",
    "NOU2T3YW": "7d",
    "UOU2T14D": "1d",
    "UOU2T3YW": "1d",
    "SEL": "7d",
    "SIL": "7d",
    "OCNMF3Y": "7d",
    "OCNMF3Y2": "7d",
    "OCNMFD": "7d",
    "OCNMFD2": "7d",
    "INTBPT": "7d",
    "MIP": "7d",
    "MID": "7d",
    "MILS": "1d",
    "MELS": "1d",
    "MDP": "7d",
    "MDV": "7d",
    "MNZT": "7d",
    "MZT": "7d",
    "NTB": "7d",
    "NTO": "7d",
    "NDZ": "7d",
    "NONBM": "7d",
    # "WIND_SOLAR_GEN", "INTERCONNECTOR_FLOWS", "DEMAND_FORECAST",
    # "SURPLUS_MARGIN", "STOR", "MARKET_INDEX_PRICES" are handled differently or are not standard BMRS datasets
}

# Known date/time columns for each table
# Using a dictionary to handle variations in timestamp column names
DATE_COLUMNS = {
    "bmrs_freq": "measurementTime",
    "bmrs_pn": "timeFrom",
    "bmrs_qpn": "timeFrom",
    "bmrs_temp": "measurementDate",
    # Default for most tables
    "default": "settlementDate",
}

# User-provided details
DATASET_DETAILS = {
    "TSDF": """Publication Schedule: Day-and-day-ahead TSDF forecast (TSDF)
  - This is the forecast for the current day and next day, usually in half-hourly (settlement) periods.
  - Updated every 30 minutes, and within 15 minutes after the end of each relevant settlement (half-hour) period.
  - Also the forecast is available from 9:00AM for the next day’s TSDF.""",
    "TSDFD": """Publication Schedule: 2-14 days ahead TSDF forecast (TSDFD)
  - Forecast for demand over the 2 to 14 days ahead period.
  - Published daily. (Exact time not always explicitly given in public sources, but frequently available and updated via the API.)""",
    "TSDFW": """Publication Schedule: 2-52 weeks ahead TSDF forecast
  - Longer-term weekly average demand forecast out to about a year ahead.
  - Available from 4pm each Thursday.""",
}

# A prioritized list of possible date/time column names to search for in table schemas
TIMESTAMP_COLUMN_CANDIDATES = [
    "settlementDate",
    "startTime",
    "timeFrom",
    "measurementTime",
    "applicableAt",
    "publishTime",
    "measurementDate",
    "createdDate",
]


def get_latest_update_status(
    client: bigquery.Client, table_name: str
) -> Tuple[Optional[datetime], str]:
    """
    Queries a BigQuery table for the most recent date by dynamically finding a timestamp column.
    """
    table_id = f"jibber-jabber-knowledge.uk_energy_insights.{table_name}"
    status = ""
    latest_date = None
    date_column = None

    try:
        table = client.get_table(table_id)

        # Dynamically find the timestamp column from the schema
        schema_columns = {field.name.lower() for field in table.schema}
        for candidate in TIMESTAMP_COLUMN_CANDIDATES:
            if candidate.lower() in schema_columns:
                # Find the original case-sensitive name
                for field in table.schema:
                    if field.name.lower() == candidate.lower():
                        date_column = field.name
                        break
                break

        if not date_column:
            return None, "Table exists, but no suitable timestamp column found."

        query = f"SELECT MAX({date_column}) as last_updated FROM `{table_id}`"

        query_job = client.query(query)
        results = list(query_job.result())

        if results and results[0].last_updated:
            latest_date = results[0].last_updated
            status = f"Last Updated: {latest_date.strftime('%Y-%m-%d %H:%M:%S')} (using column '{date_column}')"
        else:
            status = "Table exists but is empty."

    except NotFound:
        status = "Table does not exist."
    except Exception as e:
        status = f"Error querying table: {e}"

    return latest_date, status


def main():
    """Checks all datasets and generates a status report."""
    report_lines = [
        "UK Energy Data - Dataset Status Report",
        f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "=======================================================",
    ]

    bq_client = bigquery.Client(project="jibber-jabber-knowledge")

    sorted_datasets = sorted(CHUNK_RULES.keys())

    for dataset_code in sorted_datasets:
        table_name = f"bmrs_{dataset_code.lower()}"
        report_lines.append(f"\nDataset: {dataset_code} (Table: {table_name})")

        _, status = get_latest_update_status(bq_client, table_name)
        report_lines.append(f"  - Status: {status}")

        if dataset_code in DATASET_DETAILS:
            report_lines.append(f"  - Details: {DATASET_DETAILS[dataset_code]}")

    report_content = "\n".join(report_lines)

    with open("dataset_status_report.txt", "w") as f:
        f.write(report_content)

    print("✅ Successfully generated 'dataset_status_report.txt'")
    print("\nReport Summary:")
    print(report_content)


if __name__ == "__main__":
    main()

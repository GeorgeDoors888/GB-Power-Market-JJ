#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Check the status of all datasets in BigQuery for the last 24 hours.
Provides a report on whether data is up to date.
"""

import logging
import os
import sys
from datetime import datetime, timedelta, timezone

import pandas as pd
from google.cloud import bigquery
from tabulate import tabulate

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

# BigQuery settings
BQ_PROJECT = "jibber-jabber-knowledge"
BQ_DATASET = "uk_energy_insights"

# All BMRS datasets
ALL_DATASETS = [
    "METADATA",
    "BOAL",
    "BOD",
    "COSTS",
    "DISBSAD",
    "FOU2T14D",
    "FOU2T3YW",
    "FOUT2T14D",
    "FREQ",
    "FUELHH",
    "FUELINST",
    "IMBALNGC",
    "INDDEM",
    "INDGEN",
    "INDO",
    "ITSDO",
    "MELNGC",
    "MID",
    "MILS",
    "MELS",
    "MDP",
    "MDV",
    "MNZT",
    "MZT",
    "NETBSAD",
    "NDF",
    "NDFD",
    "NDFW",
    "NONBM",
    "NOU2T14D",
    "NOU2T3YW",
    "NTB",
    "NTO",
    "NDZ",
    "OCNMF3Y",
    "OCNMF3Y2",
    "OCNMFD",
    "OCNMFD2",
    "PN",
    "QAS",
    "QPN",
    "RDRE",
    "RDRI",
    "RURE",
    "RURI",
    "SEL",
    "SIL",
    "STOR",
    "TEMP",
    "TSDF",
    "TSDFD",
    "TSDFW",
    "UOU2T14D",
    "UOU2T3YW",
    "WINDFOR",
]


def get_table_name(dataset):
    """Convert dataset code to BigQuery table name."""
    if dataset == "RDRI":
        return "bmrs_rdri_new"
    return f"bmrs_{dataset.lower()}"


def check_dataset_status(client, dataset_id, table_name, hours=24):
    """
    Check if the dataset has data for the specified time period.
    Returns a tuple of (exists, has_recent_data, last_update, total_rows, period_rows)
    """
    table_id = f"{client.project}.{dataset_id}.{table_name}"

    # Check if table exists
    try:
        table = client.get_table(table_id)
        exists = True
    except Exception:
        return (False, False, None, 0, 0)

    # Determine timestamp field
    timestamp_fields = [
        "_window_from_utc",
        "timeFrom",
        "settlementDate",
        "publishTime",
        "startTime",
        "startDate",
    ]

    ts_field = None
    for field in timestamp_fields:
        # Check if field exists in schema
        if any(f.name == field for f in table.schema):
            ts_field = field
            break

    if not ts_field:
        return (True, False, None, table.num_rows, 0)

    # Calculate time range
    now = datetime.now(timezone.utc)
    start_time = now - timedelta(hours=hours)

    # Query for the most recent record
    try:
        query = f"""
        SELECT
            MAX(`{ts_field}`) as last_update,
            COUNT(*) as total_rows
        FROM `{table_id}`
        """

        job = client.query(query)
        results = job.result()

        row = list(results)[0]
        last_update = row.last_update
        total_rows = row.total_rows

        # Query for records in the specified time period
        period_query = f"""
        SELECT COUNT(*) as period_rows
        FROM `{table_id}`
        WHERE `{ts_field}` >= TIMESTAMP('{start_time.isoformat()}')
        """

        period_job = client.query(period_query)
        period_results = period_job.result()

        period_rows = list(period_results)[0].period_rows

        # Check if data is recent
        has_recent_data = False
        if last_update:
            time_diff = now - last_update
            has_recent_data = time_diff.total_seconds() < (hours * 3600)

        return (True, has_recent_data, last_update, total_rows, period_rows)

    except Exception as e:
        logging.error(f"Error checking {table_name}: {e}")
        return (True, False, None, table.num_rows, 0)


def main():
    """Main function to check data status."""
    client = bigquery.Client(project=BQ_PROJECT)
    logging.info(
        f"Checking data status for the last 24 hours in {BQ_PROJECT}.{BQ_DATASET}"
    )

    results = []
    for dataset in ALL_DATASETS:
        table_name = get_table_name(dataset)
        logging.info(f"Checking {dataset} ({table_name})...")

        exists, has_recent_data, last_update, total_rows, period_rows = (
            check_dataset_status(client, BQ_DATASET, table_name)
        )

        status = "MISSING"
        if exists:
            status = "UP-TO-DATE" if has_recent_data else "OUTDATED"

        last_update_str = last_update.isoformat() if last_update else "N/A"

        results.append(
            [dataset, table_name, status, last_update_str, total_rows, period_rows]
        )

    # Sort results by status (MISSING, OUTDATED, UP-TO-DATE)
    status_order = {"MISSING": 0, "OUTDATED": 1, "UP-TO-DATE": 2}
    results.sort(key=lambda x: status_order.get(x[2], 3))

    # Print table
    headers = [
        "Dataset",
        "Table Name",
        "Status",
        "Last Update",
        "Total Rows",
        "24h Rows",
    ]
    print("\n" + tabulate(results, headers=headers, tablefmt="grid"))

    # Summary
    up_to_date = sum(1 for r in results if r[2] == "UP-TO-DATE")
    outdated = sum(1 for r in results if r[2] == "OUTDATED")
    missing = sum(1 for r in results if r[2] == "MISSING")

    print(f"\nSummary:")
    print(
        f"Up-to-date: {up_to_date}/{len(ALL_DATASETS)} ({up_to_date/len(ALL_DATASETS)*100:.1f}%)"
    )
    print(
        f"Outdated: {outdated}/{len(ALL_DATASETS)} ({outdated/len(ALL_DATASETS)*100:.1f}%)"
    )
    print(
        f"Missing: {missing}/{len(ALL_DATASETS)} ({missing/len(ALL_DATASETS)*100:.1f}%)"
    )

    # Export to CSV
    df = pd.DataFrame(results, columns=headers)
    csv_file = "dataset_status_report.csv"
    df.to_csv(csv_file, index=False)
    logging.info(f"Report saved to {csv_file}")


if __name__ == "__main__":
    main()

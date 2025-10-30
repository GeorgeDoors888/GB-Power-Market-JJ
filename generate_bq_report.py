#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Generates a summary report for the BMRS data ingested into BigQuery.

What this does
--------------
• Connects to the specified BigQuery project and dataset.
• Finds all tables created by the ingestion script (prefixed with `bmrs_`).
• For each table, it retrieves:
    - Total number of rows.
    - Total table size in Gigabytes (GB).
    - The minimum and maximum date range based on the `_window_from_utc` metadata column.
• Calculates overall totals for rows and size.
• Writes a clean, formatted report to `ingestion_report.txt`.

Usage
-----
# Make sure your virtual environment is active first:
# source .venv/bin/activate

python generate_bq_report.py
"""

import logging
from datetime import datetime, timedelta, timezone

from google.cloud import bigquery
from tqdm import tqdm

# --- Config ---
# These should match the values in your ingest script.
BQ_PROJECT = "jibber-jabber-knowledge"
BQ_DATASET = "uk_energy_prod"
TABLE_PREFIX = "bmrs_"
REPORT_FILENAME = "ingestion_report.txt"
# Define the global date range used for the ingestion run.
# This is used to check for completeness.
RUN_START_DATE = datetime(2016, 1, 1, tzinfo=timezone.utc)
RUN_END_DATE = datetime(2025, 8, 26, tzinfo=timezone.utc)


def generate_report():
    """Queries BigQuery and generates a text file report."""
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    try:
        client = bigquery.Client(project=BQ_PROJECT)
        dataset_ref = client.dataset(BQ_DATASET)
        logging.info(f"Connecting to project '{BQ_PROJECT}', dataset '{BQ_DATASET}'...")
    except Exception as e:
        logging.error(f"Failed to initialize BigQuery client: {e}")
        logging.error(
            "Please ensure you are authenticated (gcloud auth application-default login) and in the correct virtual environment."
        )
        return

    all_tables = list(client.list_tables(dataset_ref))
    bmrs_tables = sorted(
        [t for t in all_tables if t.table_id.startswith(TABLE_PREFIX)],
        key=lambda t: t.table_id,
    )

    if not bmrs_tables:
        logging.warning(
            f"No tables found with prefix '{TABLE_PREFIX}' in dataset '{BQ_DATASET}'."
        )
        return

    report_lines = []
    total_rows = 0
    total_bytes = 0

    # --- Report Header ---
    report_lines.append("=" * 50)
    report_lines.append("Elexon BMRS BigQuery Ingestion Report")
    report_lines.append("=" * 50)
    report_lines.append(f"Project: {BQ_PROJECT}")
    report_lines.append(f"Dataset: {BQ_DATASET}")
    report_lines.append(f"Generated On (UTC): {datetime.now(timezone.utc).isoformat()}")
    report_lines.append(
        f"Reporting Period: {RUN_START_DATE.date()} to {RUN_END_DATE.date()}"
    )
    report_lines.append("-" * 50)
    report_lines.append("\n")

    logging.info(f"Found {len(bmrs_tables)} tables to analyze. Generating stats...")

    # --- Per-Table Stats ---
    for table in tqdm(bmrs_tables, desc="Analyzing tables", unit="table"):
        try:
            table_obj = client.get_table(table)
            row_count = table_obj.num_rows
            size_gb = (table_obj.num_bytes / (1024**3)) if table_obj.num_bytes else 0
            total_rows += row_count if row_count else 0
            total_bytes += table_obj.num_bytes if table_obj.num_bytes else 0

            min_date, max_date = None, None
            completeness_notes = []
            if row_count and row_count > 0:
                # Query for actual date range present in the data
                query = f"SELECT MIN(_window_from_utc), MAX(_window_from_utc) FROM `{table_obj.project}.{table_obj.dataset_id}.{table_obj.table_id}`"
                query_job = client.query(query)
                results = list(query_job.result())
                if results and results[0][0] is not None:
                    min_date = results[0][0]
                    max_date = results[0][1]

                    # Analyze completeness
                    if min_date > RUN_START_DATE:
                        completeness_notes.append(
                            f"  - MISSING START: Data begins after {RUN_START_DATE.date()}."
                        )
                    # Check if data ends significantly before the run end date (e.g., more than a week)
                    if max_date < (RUN_END_DATE - timedelta(days=7)):
                        completeness_notes.append(
                            f"  - MISSING END: Data stops long before {RUN_END_DATE.date()}."
                        )
                    if not completeness_notes:
                        completeness_notes.append(
                            "  - Appears complete for the period."
                        )
                else:
                    completeness_notes.append("  - No valid date information found.")

            else:
                completeness_notes.append("  - Table is empty.")

            report_lines.append(f"Table: {table.table_id}")
            report_lines.append(f"  - Rows: {row_count:,}")
            report_lines.append(f"  - Size: {size_gb:.4f} GB")
            report_lines.append(f"  - Earliest Data Point: {min_date or 'N/A'}")
            report_lines.append(f"  - Latest Data Point:   {max_date or 'N/A'}")
            report_lines.append("  - Data Completeness:")
            report_lines.extend(completeness_notes)
            report_lines.append("")  # Blank line for spacing

        except Exception as e:
            logging.error(f"Could not process table {table.table_id}: {e}")
            report_lines.append(f"Table: {table.table_id}")
            report_lines.append(f"  - FAILED to retrieve stats: {e}")
            report_lines.append("")

    # --- Overall Summary ---
    total_gb = total_bytes / (1024**3)
    report_lines.append("-" * 50)
    report_lines.append("Overall Summary")
    report_lines.append("-" * 50)
    report_lines.append(f"Total Tables Analyzed: {len(bmrs_tables)}")
    report_lines.append(f"Total Rows Ingested: {total_rows:,}")
    report_lines.append(f"Total Size on BigQuery: {total_gb:.4f} GB")
    report_lines.append("=" * 50)

    # --- Write to File ---
    try:
        with open(REPORT_FILENAME, "w") as f:
            f.write("\n".join(report_lines))
        logging.info(f"✅ Report successfully generated: {REPORT_FILENAME}")
    except IOError as e:
        logging.error(f"Failed to write report file: {e}")


if __name__ == "__main__":
    generate_report()

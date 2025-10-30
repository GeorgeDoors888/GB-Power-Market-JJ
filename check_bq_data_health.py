"""
Checks the data health of tables in a BigQuery dataset for a given month.

Verifies that each table has data for every day of the specified month by
checking the `_window_from_utc` metadata column added during ingestion.
"""

import argparse
import calendar
from datetime import datetime

import pandas as pd
import requests
from google.api_core.exceptions import NotFound
from google.cloud import bigquery
from rich.console import Console
from rich.progress import Progress
from rich.table import Table


def check_data_completeness(project: str, dataset: str, year: int, month: int):
    """
    Lists tables in a dataset and checks the completeness of their data for a specific month.

    Args:
        project (str): The Google Cloud project ID.
        dataset (str): The BigQuery dataset ID.
        year (int): The year to check.
        month (int): The month to check.
    """
    console = Console()
    client = bigquery.Client(project=project)
    dataset_id = f"{project}.{dataset}"

    try:
        tables = list(client.list_tables(dataset_id))
    except NotFound:
        console.print(f"[bold red]Error: Dataset '{dataset_id}' not found.[/bold red]")
        return

    tables = [t for t in tables if t.table_id.startswith("bmrs_")]

    if not tables:
        console.print(
            f"[yellow]No tables with 'bmrs_' prefix found in dataset '{dataset_id}'.[/yellow]"
        )
        return

    _, num_days_in_month = calendar.monthrange(year, month)
    start_date = datetime(year, month, 1)
    end_date = datetime(year, month + 1, 1) if month < 12 else datetime(year + 1, 1, 1)

    console.print(
        f"Checking [bold cyan]{len(tables)}[/bold cyan] tables in [bold cyan]{dataset_id}[/bold cyan] "
        f"for [bold cyan]{num_days_in_month}[/bold cyan] days in [bold cyan]{year}-{month:02d}[/bold cyan]..."
    )

    results_table = Table(show_header=True, header_style="bold magenta")
    results_table.add_column("Table Name", style="cyan")
    results_table.add_column("Distinct Days", justify="right")
    results_table.add_column("Expected Days", justify="right")
    results_table.add_column("Completeness", justify="right")
    results_table.add_column("Min Date In Range", justify="center")
    results_table.add_column("Max Date In Range", justify="center")
    results_table.add_column("Status", justify="center")

    with Progress(console=console) as progress:
        task = progress.add_task("[cyan]Processing tables...", total=len(tables))

        for table in sorted(tables, key=lambda x: x.table_id):
            progress.update(task, advance=1, description=f"Checking {table.table_id}")
            table_ref = f"{dataset_id}.{table.table_id}"

            # Check if the essential metadata column exists to avoid query errors on other tables
            try:
                table_info = client.get_table(table_ref)
                if "_window_from_utc" not in [
                    schema.name for schema in table_info.schema
                ]:
                    results_table.add_row(
                        table.table_id,
                        "-",
                        "-",
                        "-",
                        "-",
                        "-",
                        "[yellow]SKIPPED (no _window_from_utc)[/yellow]",
                    )
                    continue
            except Exception as e:
                results_table.add_row(
                    table.table_id, "-", "-", "-", "-", "-", f"[red]ERROR: {e}[/red]"
                )
                continue

            query = f"""
            WITH
            data_with_timestamp AS (
                SELECT SAFE_CAST(_window_from_utc AS TIMESTAMP) AS ts
                FROM `{table_ref}`
            )
            SELECT
                COUNT(DISTINCT DATE(ts)) AS distinct_days,
                MIN(ts) AS min_date,
                MAX(ts) AS max_date
            FROM data_with_timestamp
            WHERE ts >= @start_date AND ts < @end_date
            """
            job_config = bigquery.QueryJobConfig(
                query_parameters=[
                    bigquery.ScalarQueryParameter(
                        "start_date", "TIMESTAMP", start_date
                    ),
                    bigquery.ScalarQueryParameter("end_date", "TIMESTAMP", end_date),
                ]
            )

            try:
                query_job = client.query(query, job_config=job_config)
                results = list(query_job.result())

                if not results:
                    results_table.add_row(
                        table.table_id,
                        "0",
                        str(num_days_in_month),
                        "0.0%",
                        "-",
                        "-",
                        "[red]NO DATA[/red]",
                    )
                    continue

                row = results[0]
                distinct_days = row.distinct_days or 0
                completeness = (distinct_days / num_days_in_month) * 100
                min_date_str = (
                    row.min_date.strftime("%Y-%m-%d") if row.min_date else "N/A"
                )
                max_date_str = (
                    row.max_date.strftime("%Y-%m-%d") if row.max_date else "N/A"
                )

                status = (
                    "[bold green]COMPLETE[/bold green]"
                    if distinct_days >= num_days_in_month
                    else "[bold yellow]INCOMPLETE[/bold yellow]"
                )
                if distinct_days == 0:
                    status = "[bold red]NO DATA[/bold red]"

                results_table.add_row(
                    table.table_id,
                    str(distinct_days),
                    str(num_days_in_month),
                    f"{completeness:.1f}%",
                    min_date_str,
                    max_date_str,
                    status,
                )

            except Exception as e:
                results_table.add_row(
                    table.table_id,
                    "-",
                    "-",
                    "-",
                    "-",
                    "-",
                    f"[red]QUERY FAILED: {e}[/red]",
                )

    console.print(results_table)


def main():
    ap = argparse.ArgumentParser(
        description="Check BigQuery for data completeness for a given month."
    )
    ap.add_argument(
        "--project", default="jibber-jabber-knowledge", help="BigQuery Project ID."
    )
    ap.add_argument("--dataset", default="uk_energy_insights", help="BigQuery Dataset.")
    ap.add_argument("--year", type=int, default=2025, help="Year to check.")
    ap.add_argument("--month", type=int, default=6, help="Month to check.")
    args = ap.parse_args()

    check_data_completeness(args.project, args.dataset, args.year, args.month)


if __name__ == "__main__":
    main()

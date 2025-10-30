"""
Ingests data from Elexon BMRS API into BigQuery with live updates.
Handles incremental loads and displays progress in real-time.
"""

import argparse
import os
import time
from datetime import datetime, timedelta

import pandas as pd
import requests
from dotenv import load_dotenv
from google.cloud import bigquery
from rich.console import Console
from rich.progress import (
    BarColumn,
    Progress,
    TextColumn,
    TimeElapsedColumn,
    TimeRemainingColumn,
)

# Load environment variables from .env file
load_dotenv()

# Constants
API_BASE_URL = "https://data.elexon.co.uk/bmrs/api/v1"
DATASETS_API_URL = "https://data.elexon.co.uk/bmrs/api/v1/datasets"
TABLE_PREFIX = "bmrs_"

console = Console()


def get_api_key():
    """Get API key from environment"""
    api_key = os.environ.get("ELEXON_API_KEY")
    if not api_key:
        console.print(
            "[bold red]Error: ELEXON_API_KEY not found in environment variables or .env file.[/bold red]"
        )
        exit(1)
    return api_key


def fetch_data_from_api(dataset_name, start_date, end_date, api_key):
    """Fetch data from Elexon API for the specified dataset and date range"""
    console.print(
        f"[bold blue]Fetching[/bold blue] {dataset_name} data from {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}"
    )

    url = f"{DATASETS_API_URL}/{dataset_name}"
    params = {
        "from": start_date.strftime("%Y-%m-%d"),
        "to": end_date.strftime("%Y-%m-%d"),
        "format": "json",
    }
    headers = {"Ocp-Apim-Subscription-Key": api_key}

    try:
        response = requests.get(url, params=params, headers=headers)
        response.raise_for_status()
        data = response.json()

        if not data or not isinstance(data, list) or not data:
            # Handle cases where API returns a dict with a 'data' key
            if isinstance(data, dict) and "data" in data:
                if not data["data"]:
                    console.print(
                        f"[yellow]Warning:[/yellow] No data returned for {dataset_name}"
                    )
                    return None
                return pd.DataFrame(data["data"])
            console.print(
                f"[yellow]Warning:[/yellow] No data returned for {dataset_name}"
            )
            return None

        return pd.DataFrame(data)

    except requests.exceptions.RequestException as e:
        console.print(f"[bold red]Error fetching {dataset_name}:[/bold red] {str(e)}")
        return None
    except ValueError:
        console.print(
            f"[bold red]Error decoding JSON for {dataset_name}. Response was: {response.text}[/bold red]"
        )
        return None


def transform_data(df, dataset_name):
    """Transform the data for BigQuery, add metadata columns"""
    if df is None or df.empty:
        return None

    # Add metadata columns
    df["_ingested_utc"] = pd.to_datetime(datetime.utcnow())
    if "settlementDate" in df.columns:
        df["_window_from_utc"] = pd.to_datetime(df["settlementDate"], errors="coerce")
    else:
        df["_window_from_utc"] = pd.to_datetime(datetime.utcnow().date())

    # Convert all columns to string to avoid schema issues with mixed types
    for col in df.columns:
        df[col] = df[col].astype(str)

    return df


def load_to_bigquery(df, project_id, dataset_id, dataset_name):
    """Load the data to BigQuery using streaming inserts"""
    if df is None or df.empty:
        return 0

    table_id = f"{TABLE_PREFIX}{dataset_name.lower()}"
    table_ref = f"{project_id}.{dataset_id}.{table_id}"

    client = bigquery.Client(project=project_id)

    job_config = bigquery.LoadJobConfig(
        write_disposition="WRITE_APPEND",
        autodetect=True,  # Autodetect schema
    )

    job = client.load_table_from_dataframe(df, table_ref, job_config=job_config)
    try:
        job.result()  # Wait for the job to complete
        console.print(f"Loaded {job.output_rows} rows into {table_id}")
        return job.output_rows
    except Exception as e:
        console.print(
            f"[bold red]Error loading data to {table_id}:[/bold red] {str(e)}"
        )
        # Log errors from BigQuery
        if job.errors:
            for error in job.errors:
                console.print(f"  - {error['message']}")
        return 0


def ingest_dataset(dataset_name, start_date, end_date, project_id, dataset_id, api_key):
    """Ingest a single dataset with progress updates"""
    df = fetch_data_from_api(dataset_name, start_date, end_date, api_key)

    if df is not None:
        df = transform_data(df, dataset_name)
        rows_loaded = load_to_bigquery(df, project_id, dataset_id, dataset_name)
        return rows_loaded

    return 0


def main():
    ap = argparse.ArgumentParser(
        description="Ingest Elexon BMRS data into BigQuery with live updates"
    )
    ap.add_argument(
        "--project", default="jibber-jabber-knowledge", help="BigQuery Project ID"
    )
    ap.add_argument("--dataset", default="uk_energy_insights", help="BigQuery Dataset")
    ap.add_argument("--start", help="Start date (YYYY-MM-DD)")
    ap.add_argument("--end", help="End date (YYYY-MM-DD)")
    ap.add_argument(
        "--datasets",
        help="Comma-separated list of datasets to ingest (e.g., FUELINST,FREQ,FUELHH)",
    )

    args = ap.parse_args()

    # Set default dates if not specified
    if not args.start:
        args.start = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    if not args.end:
        args.end = datetime.now().strftime("%Y-%m-%d")

    start_date = datetime.strptime(args.start, "%Y-%m-%d")
    end_date = datetime.strptime(args.end, "%Y-%m-%d")

    # Get API key
    api_key = get_api_key()
    if not api_key:
        console.print("[bold red]API Key is required.[/bold red]")
        return

    # Get datasets to ingest
    if args.datasets:
        datasets = [d.strip().upper() for d in args.datasets.split(",")]
    else:
        # Default datasets that are commonly used
        datasets = ["FUELINST", "FUELHH", "FREQ", "BOD", "BOALF", "NETBSAD", "QAS"]

    console.print(
        f"[bold green]Starting ingestion of {len(datasets)} datasets from {args.start} to {args.end}[/bold green]"
    )
    console.print(f"[bold]Project:[/bold] {args.project}")
    console.print(f"[bold]Dataset:[/bold] {args.dataset}")

    total_rows_loaded = 0

    with Progress(
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TimeElapsedColumn(),
        TimeRemainingColumn(),
        console=console,
    ) as progress:
        overall_task = progress.add_task(
            "[bold green]Overall Progress", total=len(datasets)
        )

        for idx, dataset_name in enumerate(datasets):
            dataset_task = progress.add_task(
                f"[cyan]Processing {dataset_name}", total=1
            )

            try:
                rows_loaded = ingest_dataset(
                    dataset_name,
                    start_date,
                    end_date,
                    args.project,
                    args.dataset,
                    api_key,
                )

                if rows_loaded is not None and rows_loaded > 0:
                    total_rows_loaded += rows_loaded
                    console.print(
                        f"[green]✓[/green] {dataset_name}: {rows_loaded} rows loaded"
                    )
                else:
                    console.print(
                        f"[yellow]i[/yellow] {dataset_name}: No new rows loaded."
                    )

            except Exception as e:
                console.print(
                    f"[bold red]Error processing {dataset_name}:[/bold red] {str(e)}"
                )

            progress.update(dataset_task, completed=1)
            progress.update(overall_task, advance=1)

            # Small delay to avoid hitting API rate limits
            time.sleep(1)

    console.print(
        f"[bold green]Ingestion complete![/bold green] Total rows loaded: {total_rows_loaded}"
    )


if __name__ == "__main__":
    main()

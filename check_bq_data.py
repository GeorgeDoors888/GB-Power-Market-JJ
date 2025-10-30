import os
from datetime import datetime

from google.api_core.exceptions import NotFound
from google.cloud import bigquery


def check_bigquery_data():
    """
    Connects to BigQuery, lists tables in the specified dataset,
    and prints a summary of row counts and last modified times.
    """
    try:
        # --- Configuration ---
        project_id = "jibber-jabber-knowledge"
        dataset_id = "elexon_data_landing_zone"

        # --- Initialize BigQuery Client ---
        # This will use the default credentials configured in your environment
        client = bigquery.Client(project=project_id)
        dataset_ref = client.dataset(dataset_id)

        print(f"--- Checking BigQuery Project: {project_id}, Dataset: {dataset_id} ---")

        # --- List Tables ---
        try:
            tables = list(client.list_tables(dataset_ref))
        except NotFound:
            print(f"❌ Dataset '{dataset_id}' not found.")
            return

        if not tables:
            print("No tables found in the dataset.")
            return

        print(f"Found {len(tables)} tables. Fetching details...\n")

        # --- Prepare and Execute Query for all tables ---
        table_summaries = []
        for table in tables:
            table_id = table.table_id

            # More efficient query to get metadata without scanning the whole table
            query = f"""
                SELECT
                    table_id,
                    row_count,
                    last_modified_time
                FROM `{project_id}.{dataset_id}.__TABLES__`
                WHERE table_id = '{table_id}'
            """

            try:
                query_job = client.query(query)
                results = query_job.result()  # Waits for the query to complete

                for row in results:
                    last_modified_datetime = datetime.fromtimestamp(
                        row.last_modified_time / 1000
                    )
                    last_modified_dt = last_modified_datetime.strftime(
                        "%Y-%m-%d %H:%M:%S UTC"
                    )
                    table_summaries.append(
                        {
                            "table": row.table_id,
                            "rows": f"{row.row_count:,}",
                            "last_modified": last_modified_dt,
                        }
                    )
            except Exception as e:
                table_summaries.append(
                    {
                        "table": table_id,
                        "rows": "Error fetching details",
                        "last_modified": f"Error: {e}",
                    }
                )

        # --- Print Results ---
        if table_summaries:
            # Sort by table name for consistent ordering
            table_summaries.sort(key=lambda x: x["table"])

            # Find max lengths for formatting
            max_len_table = max(len(s["table"]) for s in table_summaries)
            max_len_rows = max(len(s["rows"]) for s in table_summaries)

            # Header
            print(
                f"{'TABLE':<{max_len_table}} | {'TOTAL ROWS':>{max_len_rows}} | LAST MODIFIED"
            )
            print(
                f"{'-' * max_len_table}-+-{'-' * max_len_rows}-+----------------------"
            )

            # Rows
            for summary in table_summaries:
                print(
                    f"{summary['table']:<{max_len_table}} | {summary['rows']:>{max_len_rows}} | {summary['last_modified']}"
                )
        else:
            print("Could not retrieve summary information for the tables.")

    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        print(
            "Please ensure you have authenticated with Google Cloud CLI ('gcloud auth application-default login')."
        )


if __name__ == "__main__":
    check_bigquery_data()

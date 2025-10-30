import os
from datetime import datetime, timezone

import yaml
from google.cloud import bigquery

# --- Configuration ---
PROJECT_ID = "jibber-jabber-knowledge"
DATASET_ID = "uk_energy_insights"
CONFIG_FILE = "insights_endpoints.with_units.yml"
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_FILE = os.path.join(SCRIPT_DIR, "INGESTED_DATASETS_SUMMARY.md")
# --- End Configuration ---


def get_bq_table_metadata(client, table_id):
    """Fetches metadata (row count, date range) for a given BigQuery table."""
    try:
        # This will raise an exception if the table doesn't exist.
        client.get_table(table_id)

        query = f"""
            SELECT
                COUNT(*) AS total_rows,
                MIN(_window_from_utc) AS earliest_record,
                MAX(_window_to_utc) AS latest_record
            FROM `{table_id}`
        """
        query_job = client.query(query)
        results = query_job.result()
        for row in results:
            return {
                "total_rows": row.total_rows,
                "earliest_record": (
                    row.earliest_record.strftime("%Y-%m-%d %H:%M:%S")
                    if row.earliest_record
                    else "N/A"
                ),
                "latest_record": (
                    row.latest_record.strftime("%Y-%m-%d %H:%M:%S")
                    if row.latest_record
                    else "N/A"
                ),
            }
    except Exception as e:
        print(f"Could not fetch metadata for table {table_id}: {e}")

    # Return a default dictionary if metadata can't be fetched
    return {
        "total_rows": "Not Ingested",
        "earliest_record": "N/A",
        "latest_record": "N/A",
    }


def get_bq_schema_for_table(client, table_id):
    """Fetches the schema for a given BigQuery table and formats it for markdown."""
    try:
        table = client.get_table(table_id)
        schema_html = "<table><thead><tr><th>Column Name</th><th>Data Type</th></tr></thead><tbody>"
        for field in table.schema:
            schema_html += f"<tr><td>{field.name}</td><td>{field.field_type}</td></tr>"
        schema_html += "</tbody></table>"
        return schema_html
    except Exception as e:
        print(f"Could not fetch schema for table {table_id}: {e}")
        return "Schema not available."


def generate_markdown_for_group(client, group_name, datasets, api_type):
    """Generates a markdown table for a group of datasets."""
    if not datasets:
        return ""

    is_insights_api = api_type == "insights"

    header = (
        "| Dataset Name | BigQuery Table | Description |\n| :--- | :--- | :--- |\n"
        if is_insights_api
        else "| Dataset Code | BigQuery Table | Description |\n| :--- | :--- | :--- |\n"
    )

    rows = []
    for ds_key, ds_details in datasets.items():
        if not ds_details:
            continue

        table_name = ds_details.get("table_name", "")
        description = ds_details.get("description", "No description available.")

        table_id = f"{PROJECT_ID}.{DATASET_ID}.{table_name}"

        schema_details = get_bq_schema_for_table(client, table_id)
        metadata = get_bq_table_metadata(client, table_id)

        metadata_html = (
            f"<b>Total Rows:</b> {metadata['total_rows']}<br>"
            f"<b>Earliest Record (UTC):</b> {metadata['earliest_record']}<br>"
            f"<b>Latest Record (UTC):</b> {metadata['latest_record']}<br>"
            f"{description}"
        )

        description_with_schema = f"{metadata_html} <details><summary>Schema</summary>{schema_details}</details>"

        identifier = ds_key if is_insights_api else ds_details.get("code", ds_key)

        rows.append(f"| `{identifier}` | `{table_name}` | {description_with_schema} |")

    if not rows:
        return ""

    return (
        f"### {group_name.replace('_', ' ').title()}\n\n{header}"
        + "\n".join(rows)
        + "\n\n"
    )


def main():
    """Main function to generate the dataset summary."""
    if "GOOGLE_APPLICATION_CREDENTIALS" not in os.environ:
        print("Error: GOOGLE_APPLICATION_CREDENTIALS environment variable not set.")
        print("Please set it to the path of your service account key file.")
        return

    try:
        client = bigquery.Client(project=PROJECT_ID)
    except Exception as e:
        print(f"Failed to create BigQuery client: {e}")
        return

    print("Starting report generation...")

    with open(CONFIG_FILE, "r") as f:
        config = yaml.safe_load(f)
        print(f"YAML config loaded. Keys: {list(config.keys())}")

    markdown_content = f"""# Elexon Insights & BMRS Datasets Summary

This document provides a summary of all datasets configured for ingestion in `{CONFIG_FILE}`. The datasets are grouped by their respective APIs (Insights and BMRS) and categories.

*Last updated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}*

---

"""

    # Process Insights API datasets
    markdown_content += "## Insights API Datasets\n\nThese datasets are sourced from the newer Elexon Insights API.\n\n"
    if "insights_api" in config and config["insights_api"]:
        print("Processing Insights API datasets...")
        for group_name, datasets in config["insights_api"].items():
            print(f"  - Group: {group_name}")
            markdown_content += generate_markdown_for_group(
                client, group_name, datasets, "insights"
            )
    else:
        print("No 'insights_api' data found in config or it is empty.")

    markdown_content += "\n---\n\n"

    # Process BMRS Datasets API
    markdown_content += "## BMRS Datasets API\n\nThese datasets are sourced from the legacy BMRS Datasets API.\n\n"
    if "bmrs_datasets_api" in config and config["bmrs_datasets_api"]:
        print("Processing BMRS Datasets API datasets...")
        for group_name, datasets in config["bmrs_datasets_api"].items():
            print(f"  - Group: {group_name}")
            markdown_content += generate_markdown_for_group(
                client, group_name, datasets, "bmrs"
            )
    else:
        print("No 'bmrs_datasets_api' data found in config or it is empty.")

    markdown_content += f"\n---\n*This summary was generated based on the configuration in `{CONFIG_FILE}`.*"

    with open(OUTPUT_FILE, "w") as f:
        f.write(markdown_content)

    print(f"Successfully generated dataset summary at: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()

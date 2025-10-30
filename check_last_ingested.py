import os
from typing import Optional

from google.api_core.exceptions import NotFound
from google.cloud import bigquery


def get_latest_date_for_table(
    table_name: str, date_column: str, condition: Optional[str] = None
):
    """Queries a BigQuery table for the most recent date."""
    client = bigquery.Client(project="jibber-jabber-knowledge")
    table_id = f"jibber-jabber-knowledge.uk_energy_insights.{table_name}"

    try:
        client.get_table(table_id)
    except NotFound:
        print(f"  - ❌ ERROR: The table `{table_name}` does not exist.")
        return

    where_clause = f"WHERE {condition}" if condition else ""

    query = f"""
        SELECT MAX({date_column}) as last_ingested_date
        FROM `{table_id}`
        {where_clause}
    """
    try:
        query_job = client.query(query)
        results = query_job.result()

        for row in results:
            if row.last_ingested_date:
                print(
                    f"  - ✅ The latest data in `{table_name}` is from: {row.last_ingested_date.strftime('%Y-%m-%d')}"
                )
            else:
                print(
                    f"  - 🟡 No data found in `{table_name}` that matches the criteria."
                )
            return

    except Exception as e:
        print(f"  - ❌ An error occurred while querying `{table_name}`: {e}")


if __name__ == "__main__":
    print("🔍 Checking the last ingestion dates for key datasets...\n")

    print("1. Demand Data:")
    get_latest_date_for_table(table_name="bmrs_tsdf", date_column="settlementDate")

    print("\n2. Overall Generation Data:")
    get_latest_date_for_table(table_name="bmrs_fuelinst", date_column="settlementDate")

    print("\n3. Wind Generation Data:")
    get_latest_date_for_table(
        table_name="bmrs_fuelinst",
        date_column="settlementDate",
        condition="fuelType = 'WIND'",
    )
    print("")

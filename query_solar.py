import os

from google.api_core.exceptions import NotFound
from google.cloud import bigquery


def query_latest_b1630_solar():
    """Queries BigQuery for the latest solar generation figure from the B1630 dataset."""
    client = bigquery.Client(project="jibber-jabber-knowledge")
    table_id = "jibber-jabber-knowledge.uk_energy_insights.bmrs_b1630"

    try:
        # First, check if the table exists
        client.get_table(table_id)
        print(f"✅ Table `{table_id}` exists.")
    except NotFound:
        print(f"❌ Table `{table_id}` does not exist.")
        print("This is the reason solar data is missing from your reports.")
        print("I need to add 'B1630' to the ingestion script to fix this.")
        return

    query = f"""
        SELECT
          quantity,
          settlementDate,
          settlementPeriod,
          createdDateTime
        FROM
          `{table_id}`
        WHERE
          powerSystemResourceType = 'Solar'
        ORDER BY
          settlementDate DESC, settlementPeriod DESC, createdDateTime DESC
        LIMIT 1
    """
    try:
        print("🔍 Searching for the latest available Solar PV data in `bmrs_b1630`...")
        query_job = client.query(query)
        results = query_job.result()

        if results.total_rows == 0:
            print(
                "❌ No Solar PV data could be found in the `bmrs_b1630` table, but the table exists."
            )
            return

        for row in results:
            generation_gw = row.quantity / 1000 if row.quantity else 0
            print(f"✅ Latest Solar PV data found:")
            print(f"  - Generation: {generation_gw:.2f} GW")
            print(f"  - Settlement Date: {row.settlementDate.strftime('%Y-%m-%d')}")
            print(f"  - Settlement Period: {row.settlementPeriod}")
            print(
                f"  - Created DateTime: {row.createdDateTime.strftime('%Y-%m-%d %H:%M:%S')} UTC"
            )
            return

    except Exception as e:
        print(f"An error occurred while querying for data: {e}")


if __name__ == "__main__":
    query_latest_b1630_solar()

import pandas as pd
from google.cloud import bigquery


def get_latest_settlement_period():
    """
    Connects to BigQuery and retrieves the latest settlement period from the bmrs_bod table.
    """
    try:
        client = bigquery.Client(project="jibber-jabber-knowledge")

        # Find the most recent settlement date and period
        query = """
            SELECT
                MAX(settlementDate) as latest_date,
                MAX(settlementPeriod) as latest_period
            FROM
                `jibber-jabber-knowledge.uk_energy_insights.bmrs_bod`
            WHERE
                settlementDate = (
                    SELECT MAX(settlementDate)
                    FROM `jibber-jabber-knowledge.uk_energy_insights.bmrs_bod`
                )
        """

        query_job = client.query(query)
        results = query_job.to_dataframe()

        if not results.empty:
            latest_date = results["latest_date"].iloc[0]
            latest_period = results["latest_period"].iloc[0]
            print(
                f"✅ The latest ingested settlement period is for date: {latest_date}, period: {latest_period}."
            )
        else:
            print("Could not determine the latest settlement period.")

    except Exception as e:
        print(f"An error occurred: {e}")


if __name__ == "__main__":
    get_latest_settlement_period()

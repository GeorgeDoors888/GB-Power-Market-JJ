#!/usr/bin/env python3

from google.cloud import bigquery
from google.oauth2 import service_account


def check_date_distribution():
    # Create credentials from service account
    credentials = service_account.Credentials.from_service_account_file(
        "jibber_jabber_key.json", scopes=["https://www.googleapis.com/auth/bigquery"]
    )

    # Create BigQuery client
    client = bigquery.Client(credentials=credentials, project="jibber-jabber-knowledge")

    # Query to get data distribution by date
    query = """
    SELECT
        settlementDate,
        COUNT(*) as records_per_day,
        COUNT(DISTINCT settlementPeriod) as unique_periods,
        COUNT(DISTINCT fuelType) as unique_fuel_types,
        MIN(settlementPeriod) as min_period,
        MAX(settlementPeriod) as max_period
    FROM `jibber-jabber-knowledge.uk_energy_insights.bmrs_fuelinst`
    GROUP BY settlementDate
    ORDER BY settlementDate ASC
    """

    try:
        print("Analyzing data distribution by date...")
        query_job = client.query(query)
        results = query_job.result()

        for row in results:
            print(f"\nDate: {row.settlementDate}")
            print(f"Total records: {row.records_per_day}")
            print(
                f"Unique settlement periods: {row.unique_periods} (from {row.min_period} to {row.max_period})"
            )
            print(f"Unique fuel types: {row.unique_fuel_types}")
            print("-" * 50)

    except Exception as e:
        print(f"Error querying BigQuery: {str(e)}")


if __name__ == "__main__":
    check_date_distribution()

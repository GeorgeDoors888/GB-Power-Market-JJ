import os

import pandas as pd
from google.cloud import bigquery

# Set the environment variable for the service account key
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "jibber_jaber_key.json"

# Construct the BigQuery client
client = bigquery.Client()

# Define the SQL query
sql_query = """
WITH Bids AS (
    SELECT
        TIMESTAMP_TRUNC(timeFrom, HOUR) AS bid_hour,
        AVG(bidPrice) AS avg_bid_price,
        SUM(bidVolume) AS total_bid_volume
    FROM
        `jibber-jabber-knowledge.uk_energy_insights.bmrs_bod`
    WHERE
        bmUnitID = "T_HUMR-1"
        AND timeFrom >= "2025-09-01T00:00:00Z"
        AND timeFrom < "2025-09-08T00:00:00Z"
        AND bidPrice < 0 -- Only include bids to be paid to turn off
    GROUP BY
        bid_hour
),
Generation AS (
    SELECT
        TIMESTAMP_TRUNC(startTime, HOUR) AS generation_hour,
        fuelType,
        SUM(quantity) AS total_mw
    FROM
        `jibber-jabber-knowledge.uk_energy_insights.neso_generation_historic`
    WHERE
        startTime >= "2025-09-01T00:00:00Z"
        AND startTime < "2025-09-08T00:00:00Z"
        AND fuelType IN ("WIND", "SOLAR")
    GROUP BY
        generation_hour,
        fuelType
),
PivotedGeneration AS (
    SELECT
        generation_hour,
        SUM(CASE WHEN fuelType = "WIND" THEN total_mw ELSE 0 END) AS wind_mw,
        SUM(CASE WHEN fuelType = "SOLAR" THEN total_mw ELSE 0 END) AS solar_mw
    FROM
        Generation
    GROUP BY
        generation_hour
)
SELECT
    b.bid_hour,
    b.avg_bid_price,
    b.total_bid_volume,
    p.wind_mw,
    p.solar_mw
FROM
    Bids b
JOIN
    PivotedGeneration p ON b.bid_hour = p.generation_hour
ORDER BY
    b.bid_hour
"""

try:
    # Execute the query and get the results as a pandas DataFrame
    print("Executing query...")
    df = client.query(sql_query).to_dataframe()

    # Define the output CSV file name
    output_filename = "T_HUMR-1_bids_vs_renewables.csv"

    # Save the DataFrame to a CSV file
    df.to_csv(output_filename, index=False)

    print(f"Query successful. Results saved to {output_filename}")
    print("\nFirst 5 rows of the data:")
    print(df.head())

except Exception as e:
    print(f"An error occurred: {e}")

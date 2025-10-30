import os
from datetime import datetime, timedelta, timezone

import numpy as np
import pandas as pd
from google.cloud import bigquery


def analyze_price_relationships():
    """
    Calculates implied System Buy and Sell prices from DISBSAD data, compares them
    to the wholesale price (MID), and analyzes the most extreme events from the last 7 days.
    """
    try:
        # --- 1. Setup BigQuery Client ---
        print("Connecting to BigQuery...")
        credentials_path = os.path.expanduser(
            "~/.config/gcloud/application_default_credentials.json"
        )
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = credentials_path
        client = bigquery.Client(project="jibber-jabber-knowledge")
        dataset_id = "uk_energy_insights"

        # --- 2. Define Time Window ---
        now = datetime.now(timezone.utc)
        start_time = now - timedelta(days=7)
        start_time_str = start_time.strftime("%Y-%m-%d")
        print(f"Analyzing data from: {start_time_str} UTC onwards.")

        # --- 3. Construct and Run the Main Query ---
        # This query calculates the implied System Buy Price (SBP) and System Sell Price (SSP)
        # by aggregating costs and volumes from balancing actions in the DISBSAD table.
        # SBP is derived from positive costs (money paid out by the system).
        # SSP is derived from negative costs (money paid to the system).
        print("Fetching and calculating balancing prices from BigQuery...")
        query = f"""
            WITH disbsad_prices AS (
                SELECT
                    settlementDate,
                    settlementPeriod,
                    -- Calculate total cost and volume for actions that cost the system (Buy Price)
                    SUM(CASE WHEN cost > 0 THEN cost ELSE 0 END) AS total_buy_cost,
                    SUM(CASE WHEN cost > 0 THEN volume ELSE 0 END) AS total_buy_volume,
                    -- Calculate total cost and volume for actions that pay the system (Sell Price)
                    SUM(CASE WHEN cost < 0 THEN cost ELSE 0 END) AS total_sell_cost,
                    SUM(CASE WHEN cost < 0 THEN volume ELSE 0 END) AS total_sell_volume
                FROM
                    `{client.project}.{dataset_id}.bmrs_disbsad`
                WHERE
                    settlementDate >= '{start_time_str}'
                GROUP BY
                    settlementDate, settlementPeriod
            )
            SELECT
                p.settlementDate,
                p.settlementPeriod,
                mid.price AS wholesale_price,
                -- Avoid division by zero and calculate the implied buy price
                SAFE_DIVIDE(p.total_buy_cost, p.total_buy_volume) AS system_buy_price,
                -- Avoid division by zero and calculate the implied sell price
                SAFE_DIVIDE(p.total_sell_cost, p.total_sell_volume) AS system_sell_price
            FROM
                disbsad_prices AS p
            JOIN
                `{client.project}.{dataset_id}.bmrs_mid` AS mid
            ON
                p.settlementDate = mid.settlementDate
                AND p.settlementPeriod = mid.settlementPeriod
            ORDER BY
                p.settlementDate, p.settlementPeriod
        """
        df = client.query(query).to_dataframe()

        if df.empty:
            print("No price data found for the last 7 days. Exiting.")
            return

        # --- 4. Perform Analysis ---
        print("Analyzing price data...")
        # Fill NaN values for periods where there was no buy or sell action
        df.fillna(0, inplace=True)

        # Find the most expensive and cheapest settlement periods
        highest_buy_price_period = df.loc[df["system_buy_price"].idxmax()]
        lowest_sell_price_period = df.loc[df["system_sell_price"].idxmin()]

        # --- 5. Print Summary Report ---
        print("\n--- Price Relationship Analysis (Last 7 Days) ---\n")
        print(f"Average Wholesale Price: £{df['wholesale_price'].mean():.2f}/MWh")
        print(
            f"Average System Buy Price:  £{df[df['system_buy_price'] > 0]['system_buy_price'].mean():.2f}/MWh"
        )
        print(
            f"Average System Sell Price: £{df[df['system_sell_price'] < 0]['system_sell_price'].mean():.2f}/MWh\n"
        )
        print("-" * 50)

        # --- 6. Deep Dive into the Highest Buy Price Event ---
        print("\n🔍 Deep Dive: Highest System Buy Price Event\n")
        hb = highest_buy_price_period
        print(
            f"On {hb['settlementDate']}, Period {hb['settlementPeriod']}, "
            f"the System Buy Price spiked to £{hb['system_buy_price']:.2f}/MWh."
        )
        print(
            f"This was significantly higher than the wholesale price of £{hb['wholesale_price']:.2f}/MWh."
        )
        print(
            "This indicates the grid was 'short' on supply and had to pay a premium for last-minute power."
        )

        # --- 7. Deep Dive into the Lowest Sell Price Event ---
        print("\n" + "-" * 50)
        print("\n🔍 Deep Dive: Lowest System Sell Price Event\n")
        ls = lowest_sell_price_period
        print(
            f"On {ls['settlementDate']}, Period {ls['settlementPeriod']}, "
            f"the System Sell Price dropped to £{ls['system_sell_price']:.2f}/MWh."
        )
        print(
            f"This was significantly lower than the wholesale price of £{ls['wholesale_price']:.2f}/MWh."
        )
        print(
            "This indicates the grid was 'long' (in surplus) and had to pay some generators to reduce their output."
        )

    except Exception as e:
        print(f"An error occurred: {e}")


if __name__ == "__main__":
    analyze_price_relationships()

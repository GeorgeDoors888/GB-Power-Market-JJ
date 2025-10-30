import os

import pandas as pd
from google.cloud import bigquery


def analyze_bmu_data():
    """
    Analyzes BMU data by fetching accepted actions and corresponding bid/offer prices,
    calculating revenue, and generating a monthly summary.
    """
    project_id = "jibber-jabber-knowledge"
    dataset_id = "uk_energy_insights"
    bmu_id = "T_HUMR-1"
    actions_file = "T_HUMR-1_accepted_actions.csv"
    output_file = "T_HUMR-1_monthly_analysis.csv"

    # Check if the actions file exists
    if not os.path.exists(actions_file):
        print(f"Error: The file {actions_file} was not found.")
        print(
            "Please ensure the BigQuery query to create this file has run successfully."
        )
        return

    print("Reading accepted actions data...")
    try:
        actions_df = pd.read_csv(actions_file)
        if actions_df.empty:
            print("The accepted actions file is empty. No data to process.")
            return

        actions_df["acceptanceTime"] = pd.to_datetime(actions_df["acceptanceTime"])
        actions_df["settlementDate"] = pd.to_datetime(actions_df["settlementDate"])
    except Exception as e:
        print(f"Error reading or parsing {actions_file}: {e}")
        return

    print(f"Found {len(actions_df)} accepted actions for {bmu_id}.")

    # Fetch all bid/offer data from BMRS_BOD for the relevant period
    print("Fetching bid/offer price data from BigQuery...")
    client = bigquery.Client(project=project_id)

    min_date = actions_df["settlementDate"].min().strftime("%Y-%m-%d")
    max_date = actions_df["settlementDate"].max().strftime("%Y-%m-%d")

    bod_query = f"""
    SELECT
        settlementDate,
        settlementPeriod,
        bid,
        offer,
        levelFrom,
        levelTo
    FROM
        `{project_id}.{dataset_id}.bmrs_bod`
    WHERE
        bmUnit = "{bmu_id}"
        AND settlementDate BETWEEN '{min_date}' AND '{max_date}'
    """
    try:
        bod_df = client.query(bod_query).to_dataframe()
        bod_df["settlementDate"] = pd.to_datetime(bod_df["settlementDate"])
        print(f"Successfully fetched {len(bod_df)} price records.")
    except Exception as e:
        print(f"Failed to fetch data from BigQuery: {e}")
        return

    # Merge the two dataframes
    print("Merging acceptance data with price data...")
    # We need to cast settlementPeriod to a common type, as it can be string/int
    actions_df["settlementPeriod"] = actions_df["settlementPeriod"].astype(int)
    bod_df["settlementPeriod"] = bod_df["settlementPeriod"].astype(int)

    merged_df = pd.merge(
        actions_df, bod_df, on=["settlementDate", "settlementPeriod"], how="left"
    )

    # Filter for the correct price for each action
    # For offers (accepted_volume_mw > 0), find the offer price where the volume is within the level range
    # For bids (accepted_volume_mw < 0), find the bid price where the volume is within the level range
    def find_price(row):
        volume = row["accepted_volume_mw"]
        if volume > 0:  # It's an offer
            if volume > row["levelFrom"] and volume <= row["levelTo"]:
                return row["offer"]
        elif volume < 0:  # It's a bid
            if volume < row["levelFrom"] and volume >= row["levelTo"]:
                return row["bid"]
        return None

    merged_df["price"] = merged_df.apply(find_price, axis=1)

    # Clean up dataframe to keep only the definitive price for each acceptance
    final_df = merged_df.dropna(subset=["price"]).drop_duplicates(
        subset=["acceptanceTime", "settlementDate", "settlementPeriod"]
    )

    print(f"Successfully matched prices for {len(final_df)} actions.")

    # Calculate revenue (Price is in £/MWh, settlement periods are 30 mins, so divide by 2)
    final_df["revenue_gbp"] = (final_df["accepted_volume_mw"] * final_df["price"]) / 2
    final_df["year_month"] = final_df["acceptanceTime"].dt.to_period("M")

    # Create separate columns for offer and bid volumes/revenues
    final_df["accepted_offer_volume_mw"] = final_df.apply(
        lambda row: row["accepted_volume_mw"] if row["accepted_volume_mw"] > 0 else 0,
        axis=1,
    )
    final_df["revenue_from_offers_gbp"] = final_df.apply(
        lambda row: row["revenue_gbp"] if row["revenue_gbp"] > 0 else 0, axis=1
    )
    final_df["accepted_bid_volume_mw"] = final_df.apply(
        lambda row: -row["accepted_volume_mw"] if row["accepted_volume_mw"] < 0 else 0,
        axis=1,
    )
    final_df["revenue_from_bids_gbp"] = final_df.apply(
        lambda row: row["revenue_gbp"] if row["revenue_gbp"] < 0 else 0, axis=1
    )

    # Aggregate by month
    print("Aggregating data by month...")
    monthly_summary = (
        final_df.groupby("year_month")
        .agg(
            accepted_offer_volume_mw=("accepted_offer_volume_mw", "sum"),
            revenue_from_offers_gbp=("revenue_from_offers_gbp", "sum"),
            accepted_bid_volume_mw=("accepted_bid_volume_mw", "sum"),
            revenue_from_bids_gbp=("revenue_from_bids_gbp", "sum"),
        )
        .reset_index()
    )

    monthly_summary["year_month"] = monthly_summary["year_month"].astype(str)

    # Save to CSV
    monthly_summary.to_csv(output_file, index=False)
    print(f"Monthly analysis complete. Data saved to {output_file}")


if __name__ == "__main__":
    analyze_bmu_data()

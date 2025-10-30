#!/usr/bin/env python3
"""
V2: Final Enhanced Data Exporter for Generation and Prices
===========================================================

This script queries Google BigQuery for T_HUMR-1 generation, total gas
generation, and system buy prices, merges the data, and exports it to
both a CSV file and a Google Sheet. This version uses the corrected
query logic identified from the successful `analyze_balancing_prices.py` script.
"""

import datetime
import os

import pandas as pd
from google.cloud import bigquery
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# --- Configuration ---
CLIENT_SECRET_FILE = (
    "/Users/georgemajor/jibber-jabber 24 august 2025 big bop/client_secrets.json"
)
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/cloud-platform",  # For BigQuery
]
OUTPUT_DIR = "/Users/georgemajor/jibber-jabber 24 august 2025 big bop"
PROJECT_ID = "jibber-jabber-knowledge"

# --- Google API Functions ---


def authenticate_google_apis():
    """Authenticate with Google and return credentials."""
    print("Authenticating with Google...")
    flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRET_FILE, SCOPES)
    creds = flow.run_local_server(port=0)
    return creds


def create_and_populate_sheet(service, sheet_title, df):
    """Creates a new Google Sheet and populates it with data from a DataFrame."""
    print(f"Creating Google Sheet: '{sheet_title}'...")
    spreadsheet = (
        service.spreadsheets()
        .create(body={"properties": {"title": sheet_title}}, fields="spreadsheetId")
        .execute()
    )
    spreadsheet_id = spreadsheet.get("spreadsheetId")
    sheet_url = f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}"

    # Prepare data for upload, converting Timestamps to strings
    df_copy = df.copy()
    if "datetime_utc" in df_copy.columns:
        # Ensure datetime_utc is actually a datetime object before trying to format it
        df_copy["datetime_utc"] = pd.to_datetime(
            df_copy["datetime_utc"], errors="coerce"
        )
        df_copy["datetime_utc"] = df_copy["datetime_utc"].dt.strftime(
            "%Y-%m-%d %H:%M:%S"
        )

    # Replace NaN with empty strings for JSON serialization
    df_copy = df_copy.fillna("")

    print(f"  > Uploading {len(df_copy)} rows...")
    body = {"values": [df_copy.columns.values.tolist()] + df_copy.values.tolist()}
    service.spreadsheets().values().update(
        spreadsheetId=spreadsheet_id,
        range="Sheet1",
        valueInputOption="USER_ENTERED",
        body=body,
    ).execute()
    return sheet_url


# --- BigQuery Functions ---


def query_bigquery(client, query, name):
    """Runs a query on BigQuery and returns a DataFrame."""
    print(f"Running query for: {name}")
    try:
        df = client.query(query).to_dataframe()
        print(f"  > Success, {len(df)} rows returned.")
        return df
    except Exception as e:
        print(f"  > An error occurred during BigQuery query for {name}: {e}")
        return pd.DataFrame()


def get_combined_data(client):
    """Queries and merges all required datasets from BigQuery."""
    end_date = datetime.date.today()
    start_date = end_date - datetime.timedelta(days=24 * 30)  # Approx 24 months

    # Query 1: T_HUMR-1 Generation (from bmrs_pn)
    humr1_query = f"""
    SELECT
        TIMESTAMP_TRUNC(timeTo, HOUR) as datetime_utc,
        AVG(levelTo) as humr1_generation_mw
    FROM `jibber-jabber-knowledge.uk_energy_insights.bmrs_pn`
    WHERE bmUnit = 'T_HUMR-1'
    AND DATE(timeTo) BETWEEN '{start_date}' AND '{end_date}'
    GROUP BY 1
    """
    humr1_df = query_bigquery(client, humr1_query, "T_HUMR-1 Generation")

    # Query for System Buy Price (Bid Price from BOD)
    system_price_query = f"""
    SELECT
        TIMESTAMP(settlementDate) + INTERVAL (30 * (settlementPeriod - 1)) MINUTE as datetime_utc,
        AVG(CAST(bid AS FLOAT64)) as system_buy_price_gbp_per_mwh
    FROM `jibber-jabber-knowledge.uk_energy_insights.bmrs_bod`
    WHERE settlementDate BETWEEN '{start_date}' AND '{end_date}'
    GROUP BY 1
    """
    system_price_df = query_bigquery(client, system_price_query, "System Buy Price")

    # Query for Total Gas Generation
    gas_generation_query = f"""
    SELECT
        TIMESTAMP_TRUNC(TIMESTAMP(publishTime), MINUTE) as datetime_utc,
        SUM(generation) as total_gas_generation_mw
    FROM `jibber-jabber-knowledge.uk_energy_insights.bmrs_fuelinst`
    WHERE fuelType = 'GAS'
    AND publishTime BETWEEN '{start_date}' AND '{end_date}'
    GROUP BY 1
    """
    gas_df = query_bigquery(client, gas_generation_query, "Total Gas Generation")

    # Merge the dataframes
    print("\nMerging datasets...")
    if humr1_df.empty and system_price_df.empty and gas_df.empty:
        print("All dataframes are empty. Aborting.")
        return pd.DataFrame()

    # Set index for merging and handle potential duplicates by averaging
    if not humr1_df.empty:
        humr1_df = humr1_df.groupby("datetime_utc").mean()
    if not system_price_df.empty:
        system_price_df = system_price_df.groupby("datetime_utc").mean()
    if not gas_df.empty:
        gas_df = gas_df.groupby("datetime_utc").mean()

    # Join the data
    merged_df = pd.DataFrame()
    if not humr1_df.empty:
        merged_df = humr1_df
    if not system_price_df.empty:
        if not merged_df.empty:
            merged_df = merged_df.join(system_price_df, how="outer")
        else:
            merged_df = system_price_df
    if not gas_df.empty:
        if not merged_df.empty:
            merged_df = merged_df.join(gas_df, how="outer")
        else:
            merged_df = gas_df

    if merged_df.empty:
        print("Merge resulted in an empty dataframe. Exiting.")
        return pd.DataFrame()

    merged_df.sort_index(inplace=True)

    print(f"  > Merged data has {len(merged_df)} rows.")
    return merged_df.reset_index()


# --- Main Execution ---


def main():
    """Main function to run the data export process."""
    print("Starting V2 Final Enhanced Data Export Process...")

    creds = authenticate_google_apis()
    sheets_service = build("sheets", "v4", credentials=creds)
    bq_client = bigquery.Client(project=PROJECT_ID, credentials=creds)

    combined_df = get_combined_data(bq_client)

    if combined_df.empty:
        print("\nNo data was fetched from BigQuery. Exiting.")
        return

    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_filename = f"Final_Combined_Data_V2_{timestamp}.csv"
    csv_filepath = os.path.join(OUTPUT_DIR, csv_filename)
    combined_df.to_csv(csv_filepath, index=False)
    print(f"\nData saved to CSV: {csv_filename}")

    sheet_title = f"V2 Final Combined Report - {datetime.date.today()}"
    sheet_url = create_and_populate_sheet(sheets_service, sheet_title, combined_df)

    print("\n--- Export Summary ---")
    print(f"CSV Export:      {csv_filename}")
    print(f"Google Sheet:    {sheet_url}")
    print("\nProcess complete.")


if __name__ == "__main__":
    main()

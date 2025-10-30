#!/usr/bin/env python3
"""
Final Enhanced Data Exporter for Generation and Prices
======================================================

This script queries Google BigQuery for T_HUMR-1 generation, total gas
generation, and system buy prices, merges the data, and exports it to
both a CSV file and a Google Sheet. It uses insights from previous
successful queries to ensure correct table and column names.
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


def create_and_populate_sheet(service, title, df):
    """Creates a new Google Sheet and populates it with data from a DataFrame."""
    print(f"Creating Google Sheet: '{title}'...")
    spreadsheet_body = {"properties": {"title": title}}
    sheet = service.spreadsheets().create(body=spreadsheet_body).execute()
    spreadsheet_id = sheet["spreadsheetId"]
    spreadsheet_url = sheet["spreadsheetUrl"]

    print(f"  > Uploading {len(df)} rows...")
    df_list = df.astype(object).where(pd.notnull(df), None).values.tolist()

    body = {"values": [df.columns.values.tolist()] + df_list}
    service.spreadsheets().values().update(
        spreadsheetId=spreadsheet_id,
        range="A1",
        valueInputOption="USER_ENTERED",
        body=body,
    ).execute()

    print(f"  > Successfully created: {spreadsheet_url}")
    return spreadsheet_url


# --- BigQuery Functions ---


def query_bigquery(client, query):
    """Runs a query on BigQuery and returns a DataFrame."""
    print(f"Running query for: {query.split('FROM')[1].split('WHERE')[0].strip()}")
    try:
        df = client.query(query).to_dataframe()
        print(f"  > Success, {len(df)} rows returned.")
        return df
    except Exception as e:
        print(f"  > An error occurred during BigQuery query: {e}")
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

    # Query 2: System Buy Price (from bmrs_bod)
    system_price_query = f"""
    SELECT
        TIMESTAMP(settlementDate) + INTERVAL (30 * (settlementPeriod - 1)) MINUTE as datetime_utc,
        AVG(price) as system_buy_price_gbp_per_mwh
    FROM `jibber-jabber-knowledge.uk_energy_insights.bmrs_bod`
    WHERE settlementDate BETWEEN '{start_date}' AND '{end_date}'
    GROUP BY 1
    """

    # Query 3: Total Gas Generation (from bmrs_fuelinst)
    gas_gen_query = f"""
    SELECT
        TIMESTAMP_TRUNC(publishTime, HOUR) as datetime_utc,
        SUM(generation) as total_gas_generation_mw
    FROM `jibber-jabber-knowledge.uk_energy_insights.bmrs_fuelinst`
    WHERE fuelType = 'GAS'
    AND DATE(publishTime) BETWEEN '{start_date}' AND '{end_date}'
    GROUP BY 1
    """

    humr1_df = query_bigquery(client, humr1_query)
    price_df = query_bigquery(client, system_price_query)
    gas_df = query_bigquery(client, gas_gen_query)

    # Merge the dataframes
    print("\nMerging datasets...")
    if humr1_df.empty or price_df.empty or gas_df.empty:
        print("One or more dataframes are empty. Aborting merge.")
        return pd.DataFrame()

    # Set index for merging and handle potential duplicates by averaging
    humr1_df = humr1_df.groupby("datetime_utc").mean()
    price_df = price_df.groupby("datetime_utc").mean()
    gas_df = gas_df.groupby("datetime_utc").mean()

    # Join the data
    merged_df = humr1_df.join(price_df, how="outer").join(gas_df, how="outer")
    merged_df.sort_index(inplace=True)

    print(f"  > Merged data has {len(merged_df)} rows.")
    return merged_df.reset_index()


# --- Main Execution ---


def main():
    """Main function to run the data export process."""
    print("Starting Final Enhanced Data Export Process...")

    creds = authenticate_google_apis()
    sheets_service = build("sheets", "v4", credentials=creds)
    bq_client = bigquery.Client(project=PROJECT_ID, credentials=creds)

    combined_df = get_combined_data(bq_client)

    if combined_df.empty:
        print("\nNo data was fetched from BigQuery. Exiting.")
        return

    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_filename = f"Final_Combined_Data_{timestamp}.csv"
    csv_filepath = os.path.join(OUTPUT_DIR, csv_filename)
    combined_df.to_csv(csv_filepath, index=False)
    print(f"\nData saved to CSV: {csv_filename}")

    sheet_title = f"Final Combined Report - {datetime.date.today()}"
    sheet_url = create_and_populate_sheet(sheets_service, sheet_title, combined_df)

    print("\n--- Export Summary ---")
    print(f"CSV Export:      {csv_filename}")
    print(f"Google Sheet:    {sheet_url}")
    print("\nProcess complete.")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Data Exporter for T_HUMR-1 Generation and BSUoS Costs
=====================================================

This script exports generation and BSUoS cost data to both CSV files and Google Sheets.
"""

import datetime
import json
import os

import pandas as pd
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# --- Configuration ---
CLIENT_SECRET_FILE = (
    "/Users/georgemajor/jibber-jabber 24 august 2025 big bop/client_secrets.json"
)
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",  # To set file permissions
]
GENERATION_CSV_PATH = "/Users/georgemajor/jibber-jabber 24 august 2025 big bop/T_HUMR-1_Generation_Data_20250916_005502.csv"
BSUOS_JSON_PATH = "/Users/georgemajor/jibber-jabber 24 august 2025 big bop/VPI_BSUoS_Analysis_Report.json"
OUTPUT_DIR = "/Users/georgemajor/jibber-jabber 24 august 2025 big bop"

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
    body = {"values": [df.columns.values.tolist()] + df.values.tolist()}
    service.spreadsheets().values().update(
        spreadsheetId=spreadsheet_id,
        range="A1",
        valueInputOption="USER_ENTERED",
        body=body,
    ).execute()

    print(f"  > Successfully created: {spreadsheet_url}")
    return spreadsheet_url


# --- Data Processing Functions ---


def process_bsuos_data():
    """Loads BSUoS data from JSON, processes it, and saves it to a CSV."""
    print("\nProcessing BSUoS data...")
    with open(BSUOS_JSON_PATH, "r") as f:
        data = json.load(f)

    costs_data = data["bsuos_analysis"]["costs_and_trends"][
        "historic_average_costs_gbp_per_mwh"
    ]
    volatility_data = data["bsuos_analysis"]["costs_and_trends"][
        "volatility_std_dev_per_year"
    ]

    df = pd.DataFrame(
        {
            "Year": costs_data.keys(),
            "Average Cost (£/MWh)": costs_data.values(),
            "Volatility (Std Dev)": volatility_data.values(),
        }
    ).set_index("Year")

    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_filename = f"BSUoS_Costs_Report_{timestamp}.csv"
    csv_filepath = os.path.join(OUTPUT_DIR, csv_filename)

    df.to_csv(csv_filepath)
    print(f"  > BSUoS data saved to: {csv_filename}")

    return df, csv_filename


def get_generation_data():
    """Loads the existing generation data CSV."""
    print("\nLoading generation data...")
    df = pd.read_csv(GENERATION_CSV_PATH)
    print(f"  > Loaded {len(df)} records from {os.path.basename(GENERATION_CSV_PATH)}")
    return df


# --- Main Execution ---


def main():
    """Main function to run the data export process."""
    print("Starting Data Export Process...")

    # Authenticate and build service
    creds = authenticate_google_apis()
    sheets_service = build("sheets", "v4", credentials=creds)

    # --- Process and Upload BSUoS Data ---
    bsuos_df, bsuos_csv_name = process_bsuos_data()
    bsuos_sheet_title = f"BSUoS Costs and Volatility Report - {datetime.date.today()}"
    bsuos_sheet_url = create_and_populate_sheet(
        sheets_service, bsuos_sheet_title, bsuos_df.reset_index()
    )

    # --- Process and Upload Generation Data ---
    generation_df = get_generation_data()
    generation_sheet_title = (
        f"T_HUMR-1 Generation Data (24 Months) - {datetime.date.today()}"
    )
    generation_sheet_url = create_and_populate_sheet(
        sheets_service, generation_sheet_title, generation_df
    )

    print("\n--- Export Summary ---")
    print(f"BSUoS Costs CSV:      {bsuos_csv_name}")
    print(f"BSUoS Costs GSheet:     {bsuos_sheet_url}")
    print(
        f"Generation Data CSV:    {os.path.basename(GENERATION_CSV_PATH)} (existing file)"
    )
    print(f"Generation Data GSheet: {generation_sheet_url}")
    print("\nProcess complete.")


if __name__ == "__main__":
    main()

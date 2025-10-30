import os
from datetime import datetime, timedelta

import pandas as pd
import pytz
from google.cloud import bigquery
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# --- CONFIGURATION ---
# Google Cloud & BigQuery
PROJECT_ID = "jibber-jabber-knowledge"
DATASET_ID = "uk_energy_insights"
SERVICE_ACCOUNT_FILE = "jibber_jaber_key.json"
# Google Sheets
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/bigquery",
    "https://www.googleapis.com/auth/drive.file",
]
# Report Parameters
END_DATE = datetime.now(pytz.utc)
START_DATE = END_DATE - timedelta(days=730)  # Approx 24 months
SPREADSHEET_TITLE = (
    f"Comprehensive UK Energy Report - 24 Months to {END_DATE.strftime('%Y-%m-%d')}"
)
# --- END CONFIGURATION ---


def authenticate_google():
    """Handles Google authentication using a service account."""
    if not os.path.exists(SERVICE_ACCOUNT_FILE):
        print(f"FATAL: Service account key file not found at '{SERVICE_ACCOUNT_FILE}'")
        exit()
    creds = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES
    )
    return creds


def create_spreadsheet(sheets_service, title):
    """Creates a new Google Sheet and returns its ID and URL."""
    spreadsheet = {"properties": {"title": title}}
    sheet = (
        sheets_service.spreadsheets()
        .create(body=spreadsheet, fields="spreadsheetId,spreadsheetUrl")
        .execute()
    )
    print(f"Created new spreadsheet: {sheet['spreadsheetUrl']}")
    return sheet["spreadsheetId"], sheet["spreadsheetUrl"]


def get_data_from_bigquery(client, query, is_pn_query=False):
    """Executes a query on BigQuery and returns a pandas DataFrame."""
    print(f"Executing query: {query[:200]}...")
    try:
        df = client.query(query).to_dataframe()

        # Handle different timestamp columns
        if is_pn_query:
            # For bmrs_pn, the timestamp is timeFrom
            df.rename(columns={"timeFrom": "datetime_utc"}, inplace=True)
        elif "settlementDate" in df.columns and "settlementPeriod" in df.columns:
            # For other tables, construct datetime_utc from settlementDate and settlementPeriod
            # This logic assumes settlement periods are 30 mins, starting from 1
            df["datetime_utc"] = pd.to_datetime(df["settlementDate"]) + pd.to_timedelta(
                (df["settlementPeriod"] - 1) * 30, unit="m"
            )
            df.drop(columns=["settlementDate", "settlementPeriod"], inplace=True)

        # Ensure datetime column is timezone-aware UTC
        if "datetime_utc" in df.columns:
            # If the column is already timezone-aware, we don't need to localize it.
            # The BigQuery client often returns timezone-aware columns for TIMESTAMP types.
            if df["datetime_utc"].dt.tz is None:
                df["datetime_utc"] = df["datetime_utc"].dt.tz_localize("UTC")
            # If it's already aware, we can ensure it's in UTC, though it should be by default from BQ.
            else:
                df["datetime_utc"] = df["datetime_utc"].dt.tz_convert("UTC")
        return df
    except Exception as e:
        print(f"An error occurred during BigQuery query: {e}")
        return pd.DataFrame()


def write_df_to_sheet(sheets_service, spreadsheet_id, df, sheet_name="Data"):
    """Writes a pandas DataFrame to a specific sheet in a Google Sheet."""
    print(f"Writing {len(df)} rows to sheet '{sheet_name}'...")
    # Convert datetime columns to string format suitable for Google Sheets
    for col in df.select_dtypes(include=["datetime64[ns, UTC]"]).columns:
        df[col] = df[col].dt.strftime("%Y-%m-%d %H:%M:%S")

    body = {
        "valueInputOption": "USER_ENTERED",
        "data": [
            {
                "range": f"{sheet_name}!A1",
                "values": [df.columns.tolist()] + df.values.tolist(),
            }
        ],
    }
    try:
        sheets_service.spreadsheets().values().batchUpdate(
            spreadsheetId=spreadsheet_id, body=body
        ).execute()
        print("Successfully wrote data to Google Sheet.")
    except HttpError as e:
        print(f"An error occurred writing to Google Sheets: {e}")


def main():
    """Main function to generate the comprehensive energy report."""
    print("Starting comprehensive energy report generation...")
    creds = authenticate_google()
    bq_client = bigquery.Client(project=PROJECT_ID, credentials=creds)
    sheets_service = build("sheets", "v4", credentials=creds)

    # 1. Create master timeline
    print("1. Creating master 30-minute interval timeline...")
    master_timeline = pd.DataFrame(
        pd.date_range(start=START_DATE, end=END_DATE, freq="30min", tz="UTC"),
        columns=["datetime_utc"],
    )

    # 2. Fetch Generation Data (bmrs_fuelinst) for fuel types
    print(
        "\n2. Fetching and processing generation data (bmrs_fuelinst) by fuel type..."
    )
    fuel_query = f"""
    SELECT
        settlementDate,
        settlementPeriod,
        fuelType,
        generation
    FROM
        `{PROJECT_ID}.{DATASET_ID}.bmrs_fuelinst`
    WHERE
        settlementDate BETWEEN '{START_DATE.strftime('%Y-%m-%d')}' AND '{END_DATE.strftime('%Y-%m-%d')}'
    """
    fuel_df = get_data_from_bigquery(bq_client, fuel_query)
    if fuel_df.empty:
        print(
            "Error: No generation data (bmrs_fuelinst) could be fetched for the entire period. Aborting."
        )
        return
    # The datetime_utc column is already constructed by get_data_from_bigquery
    # Pivot so each fuelType is a column
    fuel_pivot = fuel_df.pivot_table(
        index="datetime_utc", columns="fuelType", values="generation", aggfunc="sum"
    ).reset_index()
    generation_df = fuel_pivot

    # 3. Fetch other datasets for the full period
    print("\n3. Fetching other datasets for the full period...")
    start_str = START_DATE.strftime("%Y-%m-%d %H:%M:%S")
    end_str = END_DATE.strftime("%Y-%m-%d %H:%M:%S")

    mid_query = f"SELECT settlementDate, settlementPeriod, price FROM `{PROJECT_ID}.{DATASET_ID}.bmrs_mid` WHERE settlementDate BETWEEN '{start_str.split(' ')[0]}' AND '{end_str.split(' ')[0]}'"
    bod_query = f"SELECT settlementDate, settlementPeriod, bid, offer FROM `{PROJECT_ID}.{DATASET_ID}.bmrs_bod` WHERE settlementDate BETWEEN '{start_str.split(' ')[0]}' AND '{end_str.split(' ')[0]}'"
    imbalngc_query = f"SELECT settlementDate, settlementPeriod, imbalance FROM `{PROJECT_ID}.{DATASET_ID}.bmrs_imbalngc` WHERE settlementDate BETWEEN '{start_str.split(' ')[0]}' AND '{end_str.split(' ')[0]}'"

    mid_df = get_data_from_bigquery(bq_client, mid_query)
    if not mid_df.empty:
        mid_df.rename(columns={"price": "market_index_price"}, inplace=True)

    bod_df = get_data_from_bigquery(bq_client, bod_query)
    if not bod_df.empty:
        bod_df.rename(
            columns={"bid": "system_buy_price", "offer": "system_sell_price"},
            inplace=True,
        )

    imbalngc_df = get_data_from_bigquery(bq_client, imbalngc_query)
    if not imbalngc_df.empty:
        imbalngc_df.rename(columns={"imbalance": "net_imbalance_volume"}, inplace=True)

    # 4. Merge all dataframes
    print("\n4. Merging all datasets...")
    final_df = master_timeline
    datasets = {
        "Generation": generation_df,
        "Market Index Price": mid_df,
        "System Prices": bod_df,
        "Net Imbalance Volume": imbalngc_df,
    }

    for name, df in datasets.items():
        if not df.empty:
            print(f"   - Merging {name}...")
            final_df = pd.merge(final_df, df, on="datetime_utc", how="left")
        else:
            print(f"   - Warning: {name} data is empty.")

    # 5. Save to CSV file instead of Google Sheets (due to permission issues)
    print("\n5. Saving to CSV file...")
    output_filename = f"UK_Energy_Report_{START_DATE.strftime('%Y%m%d')}_{END_DATE.strftime('%Y%m%d')}.csv"

    # Convert datetime columns to string format
    datetime_cols = final_df.select_dtypes(include=["datetime"]).columns
    for col in datetime_cols:
        final_df[col] = final_df[col].dt.strftime("%Y-%m-%d %H:%M:%S")

    final_df.to_csv(output_filename, index=False)
    print(f"Report saved to: {output_filename}")
    print(f"Total rows: {len(final_df)}")
    print(f"Columns: {list(final_df.columns)}")

    # Display sample of data
    print("\nSample data (first 5 rows):")
    print(final_df.head())

    print("\n--- REPORT GENERATION COMPLETE ---")
    print(f"CSV file saved as: {output_filename}")
    print("You can now manually upload this CSV to Google Sheets if needed.")
    print("------------------------------------")


if __name__ == "__main__":
    main()

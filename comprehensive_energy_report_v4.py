#!/usr/bin/env python3
"""
Comprehensive UK Energy Generation and Market Report V4
========================================================

This script creates a single, comprehensive 24-month report of UK energy data.
- Fetches all fuel types, prices, and imbalance data.
- Creates a complete, unbroken 30-minute timeline for the last 24 months.
- Pivots fuel data to ensure each fuel type has its own column.
- All generation data is in MW.
- Writes the final, clean data to a NEW Google Sheet.
"""

import datetime
import os
from decimal import Decimal

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
    "https://www.googleapis.com/auth/bigquery",
]
PROJECT_ID = "jibber-jabber-knowledge"

# --- Google API Functions ---


def authenticate_google_apis():
    """Authenticate with Google and return credentials."""
    print("🔐 Authenticating with Google APIs...")
    flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRET_FILE, SCOPES)
    creds = flow.run_local_server(port=0)
    return creds


def create_new_google_sheet(sheets_service, sheet_name):
    """Creates a brand new Google Sheet and returns its ID and URL."""
    print(f"📄 Creating a new spreadsheet: '{sheet_name}'...")
    spreadsheet = {"properties": {"title": sheet_name}}
    sheet = (
        sheets_service.spreadsheets()
        .create(body=spreadsheet, fields="spreadsheetId,spreadsheetUrl")
        .execute()
    )
    sheet_id = sheet.get("spreadsheetId")
    sheet_url = sheet.get("spreadsheetUrl")
    print(f"✅ New spreadsheet created. ID: {sheet_id}")
    return sheet_id, sheet_url


def write_to_google_sheet(sheets_service, sheet_id, dataframe):
    """Clears and writes a DataFrame to a specified Google Sheet."""
    print(f"📊 Writing {len(dataframe):,} rows to Google Sheet...")

    # Clear existing data
    try:
        print("🧹 Clearing existing data...")
        sheets_service.spreadsheets().values().clear(
            spreadsheetId=sheet_id, range="Sheet1"
        ).execute()
    except Exception as e:
        print(f"⚠️ Could not clear sheet, proceeding anyway. Error: {e}")

    # Prepare data for writing
    df_copy = dataframe.copy()

    # Convert Decimal types to float for JSON serialization
    for col in df_copy.columns:
        if df_copy[col].dtype == "object":
            # Apply conversion only if there are Decimals present
            if any(isinstance(x, Decimal) for x in df_copy[col].dropna()):
                df_copy[col] = df_copy[col].apply(
                    lambda x: float(x) if isinstance(x, Decimal) else x
                )

    # Convert all datetimes to string format for JSON serialization
    df_copy["datetime_utc"] = df_copy["datetime_utc"].dt.strftime("%Y-%m-%d %H:%M:%S")
    # Replace any remaining NaNs with an empty string
    df_copy = df_copy.fillna("")

    values = [df_copy.columns.tolist()] + df_copy.values.tolist()

    body = {"values": values}
    try:
        sheets_service.spreadsheets().values().update(
            spreadsheetId=sheet_id,
            range="Sheet1",
            valueInputOption="USER_ENTERED",
            body=body,
        ).execute()
        print("✅ Data written successfully to Google Sheet.")
    except Exception as e:
        print(f"❌❌❌ CRITICAL ERROR: Failed to write data to Google Sheet. ❌❌❌")
        print(f"Error: {e}")


# --- BigQuery Data Functions ---


def query_bigquery(client, query, name):
    """Runs a query on BigQuery and returns a DataFrame."""
    print(f"🔍 Running query for: {name}")
    try:
        df = client.query(query).to_dataframe()
        print(f"  -> Success, {len(df):,} rows returned.")
        return df
    except Exception as e:
        print(f"  -> ❌ Error during BigQuery query for {name}: {e}")
        return pd.DataFrame()


def get_all_fuel_generation(client, start_date, end_date):
    """
    Queries and pivots all fuel generation data from bmrs_fuelinst.
    This is the definitive method for getting all fuel types in separate columns.
    """
    query = f"""
    SELECT
        DATETIME_ADD(DATETIME(settlementDate), INTERVAL (settlementPeriod - 1) * 30 MINUTE) as datetime_utc,
        fuelType,
        SUM(generation) as generation_mw
    FROM `jibber-jabber-knowledge.uk_energy_insights.bmrs_fuelinst`
    WHERE settlementDate BETWEEN '{start_date}' AND '{end_date}'
    GROUP BY 1, 2
    """
    df = query_bigquery(client, query, "All Fuel Types")
    if df.empty:
        return pd.DataFrame()

    # Pivot the data
    print("🔄 Pivoting fuel data to create columns for each fuel type...")
    pivot_df = df.pivot_table(
        index="datetime_utc", columns="fuelType", values="generation_mw"
    ).reset_index()

    # Clean up column names
    pivot_df.columns = [
        f"{col.lower()}_generation_mw" if col != "datetime_utc" else col
        for col in pivot_df.columns
    ]
    print("✅ Fuel data pivoted successfully.")
    return pivot_df


def get_humr1_generation(client, start_date, end_date):
    """Gets generation data specifically for the T_HUMR-1 BMU."""
    query = f"""
    SELECT
        DATETIME_TRUNC(timeTo, MINUTE) as datetime_utc,
        levelTo as humr1_generation_mw
    FROM `jibber-jabber-knowledge.uk_energy_insights.bmrs_pn`
    WHERE bmUnit = 'T_HUMR-1' AND DATE(timeTo) BETWEEN '{start_date}' AND '{end_date}'
    """
    return query_bigquery(client, query, "HUMR-1 Generation")


def get_market_data(client, start_date, end_date):
    """Gets market prices and net imbalance volume."""
    queries = {
        "market_prices": f"""
        SELECT DATETIME_ADD(DATETIME(settlementDate), INTERVAL (settlementPeriod - 1) * 30 MINUTE) as datetime_utc,
               AVG(price) as market_index_price_gbp_per_mwh
        FROM `jibber-jabber-knowledge.uk_energy_insights.bmrs_mid`
        WHERE settlementDate BETWEEN '{start_date}' AND '{end_date}' GROUP BY 1
        """,
        "system_prices": f"""
        SELECT DATETIME_ADD(DATETIME(settlementDate), INTERVAL (settlementPeriod - 1) * 30 MINUTE) as datetime_utc,
               AVG(CAST(bid AS FLOAT64)) as system_buy_price_gbp_per_mwh,
               AVG(CAST(offer AS FLOAT64)) as system_sell_price_gbp_per_mwh
        FROM `jibber-jabber-knowledge.uk_energy_insights.bmrs_bod`
        WHERE settlementDate BETWEEN '{start_date}' AND '{end_date}' GROUP BY 1
        """,
        "niv": f"""
        SELECT DATETIME_ADD(DATETIME(settlementDate), INTERVAL (settlementPeriod - 1) * 30 MINUTE) as datetime_utc,
               AVG(imbalance) as net_imbalance_volume_mwh
        FROM `jibber-jabber-knowledge.uk_energy_insights.bmrs_imbalngc`
        WHERE settlementDate BETWEEN '{start_date}' AND '{end_date}' GROUP BY 1
        """,
    }

    dfs = [query_bigquery(client, query, name) for name, query in queries.items()]
    return dfs


# --- Main Execution ---


def main():
    """Main function to run the comprehensive energy report."""
    print("🚀 Starting Comprehensive UK Energy Generation & Market Report V4...")
    print("=" * 70)

    # 1. Authenticate and initialize clients
    creds = authenticate_google_apis()
    sheets_service = build("sheets", "v4", credentials=creds)
    bq_client = bigquery.Client(project=PROJECT_ID, credentials=creds)

    # 2. Define the 24-month period
    end_date = datetime.date.today()
    start_date = end_date - datetime.timedelta(days=730)
    print(f"📅 Reporting Period: {start_date} to {end_date}")

    # 3. Create the master timeline
    print("뼈 Creating master 30-minute timeline...")
    full_date_range = pd.date_range(
        start=start_date, end=end_date, freq="30min", tz="UTC"
    )
    master_df = pd.DataFrame(full_date_range, columns=["datetime_utc"])
    print(f"✅ Master timeline created with {len(master_df):,} settlement periods.")

    # 4. Fetch and merge all data
    data_frames_to_merge = []
    data_frames_to_merge.append(
        get_all_fuel_generation(bq_client, start_date, end_date)
    )
    data_frames_to_merge.append(get_humr1_generation(bq_client, start_date, end_date))
    data_frames_to_merge.extend(get_market_data(bq_client, start_date, end_date))

    for df in data_frames_to_merge:
        if not df.empty:
            print(f"🔗 Merging data...")
            # Standardize datetime column before merging to prevent timezone/precision errors
            if pd.api.types.is_datetime64_any_dtype(df["datetime_utc"]):
                if df["datetime_utc"].dt.tz is None:
                    # If the column is timezone-naive, localize it to UTC
                    df["datetime_utc"] = df["datetime_utc"].dt.tz_localize("UTC")
                else:
                    # If it's already timezone-aware, convert it to UTC
                    df["datetime_utc"] = df["datetime_utc"].dt.tz_convert("UTC")

            master_df = pd.merge(master_df, df, on="datetime_utc", how="left")

    # 5. Final cleanup
    print("🧹 Cleaning final dataset...")
    # Forward-fill HUMR-1 data as it's reported less frequently
    if "humr1_generation_mw" in master_df.columns:
        master_df["humr1_generation_mw"] = master_df["humr1_generation_mw"].ffill()
    # Fill all other numeric NaNs with 0
    numeric_cols = master_df.select_dtypes(include="number").columns
    master_df[numeric_cols] = master_df[numeric_cols].fillna(0)

    print(
        f"✅ Final dataset ready with {len(master_df):,} rows and {len(master_df.columns)} columns."
    )

    # 6. Create a new Google Sheet and write the data
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    sheet_name = f"UK Energy Report V4 - {timestamp}"
    sheet_id, sheet_url = create_new_google_sheet(sheets_service, sheet_name)

    if sheet_id:
        write_to_google_sheet(sheets_service, sheet_id, master_df)

    # 7. Final summary
    print("\n" + "=" * 70)
    print("🎉 COMPREHENSIVE ENERGY REPORT COMPLETE 🎉")
    print("=" * 70)
    print(f"📊 New Google Sheet URL: {sheet_url}")
    print(f"📈 Total Records:        {len(master_df):,}")
    print(f"📅 Data Period:          {start_date} to {end_date}")
    print("\n✅ Process complete!")


if __name__ == "__main__":
    main()

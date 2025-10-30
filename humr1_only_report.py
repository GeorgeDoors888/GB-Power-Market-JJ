#!/usr/bin/env python3
"""
HUMR-1 Generation Report
========================

This script creates a 24-month report for the T_HUMR-1 BMU.
- Creates a complete, unbroken 30-minute timeline for the last 24 months.
- Fetches generation data for T_HUMR-1.
- Resamples the data to 30-minute intervals to match the timeline.
- Writes the final data to a new Google Sheet.
"""

import datetime
import logging
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


def write_to_google_sheet(sheets_service, sheet_id, df):
    """Writes a DataFrame to a Google Sheet."""
    try:
        # Convert datetime columns to strings to avoid JSON serialization issues
        df_copy = df.copy()
        for col in df_copy.columns:
            if df_copy[
                col
            ].dtype == "datetime64[ns, UTC]" or pd.api.types.is_datetime64_any_dtype(
                df_copy[col]
            ):
                df_copy[col] = df_copy[col].astype(str)

        # Prepare the data
        values = [df_copy.columns.tolist()] + df_copy.values.tolist()

        body = {"values": values}

        result = (
            sheets_service.spreadsheets()
            .values()
            .update(
                spreadsheetId=sheet_id, range="A1", valueInputOption="RAW", body=body
            )
            .execute()
        )

        print(f"✅ Data written to Google Sheet: {result.get('updatedRows', 0)} rows")

    except Exception as e:
        print(f"❌ Error writing to Google Sheet: {e}")


# --- BigQuery Data Functions ---


def query_bigquery(client, query, name, job_config=None):
    """Runs a query on BigQuery and returns a DataFrame."""
    print(f"🔍 Running query for: {name}")
    try:
        df = client.query(query, job_config=job_config).to_dataframe()
        print(f"  -> Success, {len(df):,} rows returned.")
        return df
    except Exception as e:
        print(f"  -> ❌ Error during BigQuery query for {name}: {e}")
        return pd.DataFrame()


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


def get_humr1_costs(client, start_date, end_date):
    """Get HUMR-1 cost data from BMRS costs table."""
    query = f"""
    SELECT
        settlementDate,
        settlementPeriod,
        systemSellPrice,
        systemBuyPrice,
        priceDerivationCode as priceCategory
    FROM `jibber-jabber-knowledge.uk_energy_insights.bmrs_costs`
    WHERE settlementDate >= '{start_date}'
      AND settlementDate <= '{end_date}'
    ORDER BY settlementDate, settlementPeriod
    """
    try:
        return client.query(query).to_dataframe()
    except Exception as e:
        logging.warning(f"Could not fetch BMRS costs data: {e}")
        # Return empty DataFrame with expected columns
        return pd.DataFrame(
            columns=[
                "settlementDate",
                "settlementPeriod",
                "systemSellPrice",
                "systemBuyPrice",
                "priceCategory",
            ]
        )


def get_market_index_data(client, start_date, end_date):
    """Get Market Index Data from BMRS MID tables."""
    # Try both bmrs_mid and bmrs_mid_v2 tables
    for table_name in ["bmrs_mid_v2", "bmrs_mid"]:
        query = f"""
        SELECT
            settlementDate,
            settlementPeriod,
            price,
            volume,
            flowDirection
        FROM `jibber-jabber-knowledge.uk_energy_insights.{table_name}`
        WHERE settlementDate >= '{start_date}'
          AND settlementDate <= '{end_date}'
        ORDER BY settlementDate, settlementPeriod
        """
        try:
            result = client.query(query).to_dataframe()
            if not result.empty:
                return result
        except Exception as e:
            logging.debug(f"Could not fetch from {table_name}: {e}")
            continue

    # If no MID tables found, return empty DataFrame
    logging.warning("No Market Index Data tables found. Returning empty data.")
    return pd.DataFrame(
        columns=[
            "settlementDate",
            "settlementPeriod",
            "price",
            "volume",
            "flowDirection",
        ]
    )


# --- Main Execution ---


def main():
    """Main function to run the HUMR-1 report."""
    print("🚀 Starting HUMR-1 Generation Report...")
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

    # 4. Fetch HUMR-1 data
    humr1_df = get_humr1_generation(bq_client, start_date, end_date)
    humr1_costs_df = get_humr1_costs(bq_client, start_date, end_date)
    market_index_data = get_market_index_data(bq_client, start_date, end_date)

    if not humr1_df.empty:
        # 5. Resample and merge
        print("🔄 Resampling HUMR-1 data to 30-minute intervals...")

        # Ensure the datetime column is timezone-aware (UTC) before setting as index
        if humr1_df["datetime_utc"].dt.tz is None:
            humr1_df["datetime_utc"] = humr1_df["datetime_utc"].dt.tz_localize("UTC")
        else:
            humr1_df["datetime_utc"] = humr1_df["datetime_utc"].dt.tz_convert("UTC")

        humr1_df.set_index("datetime_utc", inplace=True)

        # Handle costs data if available
        if not humr1_costs_df.empty:
            # Create datetime_utc column for costs data
            humr1_costs_df["datetime_utc"] = pd.to_datetime(
                humr1_costs_df["settlementDate"]
            ) + pd.to_timedelta(
                (humr1_costs_df["settlementPeriod"] - 1) * 30, unit="minutes"
            )

            if humr1_costs_df["datetime_utc"].dt.tz is None:
                humr1_costs_df["datetime_utc"] = humr1_costs_df[
                    "datetime_utc"
                ].dt.tz_localize("UTC")
            else:
                humr1_costs_df["datetime_utc"] = humr1_costs_df[
                    "datetime_utc"
                ].dt.tz_convert("UTC")

            humr1_costs_df.set_index("datetime_utc", inplace=True)

        # Resample to 30-minute frequency, taking the mean value in each interval
        humr1_resampled = humr1_df.resample("30min").mean()

        # Only resample costs if we have costs data
        if not humr1_costs_df.empty:
            # Use specific aggregations for different column types
            humr1_costs_resampled = humr1_costs_df.resample("30min").agg(
                {
                    "systemSellPrice": "mean",
                    "systemBuyPrice": "mean",
                    "priceCategory": "first",  # Take first value for categorical data
                }
            )
        else:
            # Create empty costs dataframe with proper structure for merging
            humr1_costs_resampled = pd.DataFrame(
                index=humr1_resampled.index,
                columns=["systemSellPrice", "systemBuyPrice", "priceCategory"],
            )

        print("🔗 Merging data...")
        master_df = pd.merge(master_df, humr1_resampled, on="datetime_utc", how="left")
        master_df = pd.merge(
            master_df, humr1_costs_resampled, on="datetime_utc", how="left"
        )

        # 6. Final cleanup
        print("🧹 Cleaning final dataset...")
        # Forward-fill data to handle any gaps
        master_df["humr1_generation_mw"] = (
            master_df["humr1_generation_mw"].ffill().fillna(0)
        )

        # Handle cost columns if they exist
        if "systemSellPrice" in master_df.columns:
            master_df["systemSellPrice"] = master_df["systemSellPrice"].fillna(0)
        if "systemBuyPrice" in master_df.columns:
            master_df["systemBuyPrice"] = master_df["systemBuyPrice"].fillna(0)
        if "priceCategory" in master_df.columns:
            master_df["priceCategory"] = master_df["priceCategory"].fillna("N/A")

        print(f"✅ Final dataset ready with {len(master_df):,} rows.")
        print(f"📊 Columns: {list(master_df.columns)}")
    else:
        print("⚠️ No HUMR-1 data or cost data returned. The final sheet will be empty.")
        master_df["humr1_generation_mw"] = 0
        master_df["systemSellPrice"] = 0
        master_df["systemBuyPrice"] = 0
        master_df["priceCategory"] = "N/A"

    # 7. Create a new Google Sheet and write the data
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    sheet_name = f"HUMR-1 Only Report - {timestamp}"
    sheet_id, sheet_url = create_new_google_sheet(sheets_service, sheet_name)

    if sheet_id:
        write_to_google_sheet(sheets_service, sheet_id, master_df)

    # 8. Final summary
    print("\n" + "=" * 70)
    print("🎉 HUMR-1 REPORT COMPLETE 🎉")
    print("=" * 70)
    print(f"📊 New Google Sheet URL: {sheet_url}")
    print(f"📈 Total Records:        {len(master_df):,}")
    print(f"📅 Data Period:          {start_date} to {end_date}")
    print("\n✅ Process complete!")


if __name__ == "__main__":
    main()

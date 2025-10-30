#!/usr/bin/env python3
"""
Comprehensive UK Energy Generation Report V5
============================================

This script creates a single, comprehensive 24-month report of UK energy generation.
This version uses a more robust method of querying each major fuel type individually
to ensure data completeness.

- Fetches generation for each major fuel type in separate queries.
- Creates a complete, unbroken 30-minute timeline for the last 24 months.
- All generation data is in MW.
- Writes the final, clean data to a NEW Google Sheet.
"""

import datetime

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
    try:
        sheets_service.spreadsheets().values().clear(
            spreadsheetId=sheet_id, range="Sheet1"
        ).execute()
    except Exception as e:
        print(f"⚠️ Could not clear sheet, proceeding anyway. Error: {e}")

    df_copy = dataframe.copy()

    # Convert Decimal types to float for JSON serialization
    for col in df_copy.columns:
        # Check if the column is of object type which might contain Decimals
        if df_copy[col].dtype == "object":
            # Check for actual Decimal instances before applying conversion
            if any(
                isinstance(x, __import__("decimal").Decimal)
                for x in df_copy[col].dropna()
            ):
                df_copy[col] = df_copy[col].apply(
                    lambda x: (
                        float(x) if isinstance(x, __import__("decimal").Decimal) else x
                    )
                )

    df_copy["datetime_utc"] = df_copy["datetime_utc"].dt.strftime("%Y-%m-%d %H:%M:%S")
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
        print(f"❌ CRITICAL ERROR: Failed to write data to Google Sheet. Error: {e}")


# --- BigQuery Data Functions ---


def get_generation_by_fuel(client, start_date, end_date, fuel_type):
    """Queries generation data for a specific fuel type from bmrs_fuelinst."""
    column_name = f"{fuel_type.lower()}_generation_mw"
    print(f"🔍 Querying generation for: {fuel_type}")
    query = f"""
    SELECT
        DATETIME_ADD(DATETIME(settlementDate), INTERVAL (settlementPeriod - 1) * 30 MINUTE) as datetime_utc,
        SUM(generation) as `{column_name}`
    FROM `jibber-jabber-knowledge.uk_energy_insights.bmrs_fuelinst`
    WHERE settlementDate BETWEEN '{start_date}' AND '{end_date}'
      AND fuelType = '{fuel_type}'
    GROUP BY 1
    """
    try:
        df = client.query(query).to_dataframe()
        if df.empty:
            print(f"  -> ⚠️ No data returned for {fuel_type}.")
        else:
            print(f"  -> Success, {len(df):,} rows returned for {fuel_type}.")
        return df
    except Exception as e:
        print(f"  -> ❌ Error during BigQuery query for {fuel_type}: {e}")
        return pd.DataFrame(columns=["datetime_utc", column_name])


# --- Main Execution ---


def main():
    """Main function to run the comprehensive generation report."""
    print("🚀 Starting Comprehensive UK Generation Report V5...")
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

    # 4. Define fuel types and fetch data for each
    fuel_types = [
        "CCGT",
        "WIND",
        "NUCLEAR",
        "COAL",
        "PS",
        "NPSHYD",
        "OIL",
        "OCGT",
        "OTHER",
        "INTFR",
        "INTIRL",
        "INTNED",
        "INTEW",
        "INTIFA2",
        "INTNEM",
        "INTNSL",
        "INTVKL",
        "INTGRNL",
        "INTELEC",
        "BIOMASS",
    ]

    for fuel in fuel_types:
        fuel_df = get_generation_by_fuel(bq_client, start_date, end_date, fuel)
        if not fuel_df.empty:
            # Standardize datetime column before merging
            if fuel_df["datetime_utc"].dt.tz is None:
                fuel_df["datetime_utc"] = fuel_df["datetime_utc"].dt.tz_localize("UTC")
            else:
                fuel_df["datetime_utc"] = fuel_df["datetime_utc"].dt.tz_convert("UTC")

            print(f"🔗 Merging {fuel} data...")
            master_df = pd.merge(master_df, fuel_df, on="datetime_utc", how="left")

    # 5. Final cleanup
    print("🧹 Cleaning final dataset...")
    numeric_cols = master_df.select_dtypes(include="number").columns
    master_df[numeric_cols] = master_df[numeric_cols].fillna(0)

    print(
        f"✅ Final dataset ready with {len(master_df):,} rows and {len(master_df.columns)} columns."
    )

    # 6. Create a new Google Sheet and write the data
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    sheet_name = f"UK Generation Report V5 - {timestamp}"
    sheet_id, sheet_url = create_new_google_sheet(sheets_service, sheet_name)

    if sheet_id:
        write_to_google_sheet(sheets_service, sheet_id, master_df)

    # 7. Final summary
    print("\n" + "=" * 70)
    print("🎉 COMPREHENSIVE GENERATION REPORT COMPLETE 🎉")
    print("=" * 70)
    print(f"📊 New Google Sheet URL: {sheet_url}")
    print(f"📈 Total Records:        {len(master_df):,}")
    print(f"📅 Data Period:          {start_date} to {end_date}")
    print("\n✅ Process complete!")


if __name__ == "__main__":
    main()

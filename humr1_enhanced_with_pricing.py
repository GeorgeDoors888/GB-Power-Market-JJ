#!/usr/bin/env python3
"""
Enhanced HUMR-1 Generation Report with Historical Pricing

This script generates a comprehensive 24-month report for HUMR-1 power station,
combining generation data with system prices where available and historical
market index prices to fill gaps.

Key Features:
- HUMR-1 generation data from Physical Notifications (PN) table
- System prices from recent periods (bmrs_costs)
- Market index prices for historical periods (bmrs_mid)
- 30-minute settlement period resolution
- Automated Google Sheets export

Created: 2025-09-19
"""

import datetime
import json
import logging
import os
import pickle
from datetime import datetime, timedelta
from decimal import Decimal

import numpy as np
import pandas as pd
from google.auth.transport.requests import Request
from google.cloud import bigquery
from google.oauth2.credentials import Credentials
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

logging.basicConfig(level=logging.INFO)


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
        .create(body=spreadsheet, fields="spreadsheetId")
        .execute()
    )
    sheet_id = sheet.get("spreadsheetId")
    sheet_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/edit"
    print(f"✅ New spreadsheet created. ID: {sheet_id}")
    return sheet_id, sheet_url


def write_to_google_sheet(sheets_service, spreadsheet_id, dataframe):
    """Write dataframe to Google Sheet."""
    print("✅ Writing data to sheet: Sheet1")

    # Clean the dataframe for Google Sheets
    df_clean = dataframe.copy()

    # Convert datetime to string
    df_clean["datetime_utc"] = df_clean["datetime_utc"].dt.strftime("%Y-%m-%d %H:%M:%S")

    # Replace NaN with empty strings and ensure numeric columns are properly formatted
    df_clean = df_clean.fillna("")

    # Ensure all numeric columns are properly formatted
    numeric_columns = df_clean.select_dtypes(include=[np.number]).columns
    for col in numeric_columns:
        df_clean[col] = df_clean[col].astype(str).replace("nan", "").replace("NaN", "")

    # Prepare data for sheets API
    headers = df_clean.columns.tolist()
    data = [headers] + df_clean.values.tolist()

    body = {"values": data}

    result = (
        sheets_service.spreadsheets()
        .values()
        .update(
            spreadsheetId=spreadsheet_id,
            range="Sheet1!A1",
            valueInputOption="RAW",
            body=body,
        )
        .execute()
    )

    print(f"✅ Data written successfully. {result.get('updatedRows')} rows updated.")
    return result


def get_humr1_generation(client, start_date, end_date):
    """Get HUMR-1 generation data from PN table."""
    print("🔍 Running query for: HUMR-1 Generation")

    query = f"""
    SELECT
        settlementDate,
        settlementPeriod,
        bmUnit,
        AVG(CAST(levelTo AS FLOAT64)) AS generation_mw
    FROM `{PROJECT_ID}.uk_energy_insights.bmrs_pn`
    WHERE bmUnit LIKE '%HUMR%'
      AND settlementDate >= '{start_date}'
      AND settlementDate <= '{end_date}'
    GROUP BY settlementDate, settlementPeriod, bmUnit
    ORDER BY settlementDate, settlementPeriod, bmUnit
    """

    result = client.query(query).to_dataframe()

    if result.empty:
        print("  -> No HUMR-1 generation data found")
        return pd.DataFrame()

    # Sum all HUMR units (HUMR-1, HUMR-2, etc.)
    result_grouped = (
        result.groupby(["settlementDate", "settlementPeriod"])["generation_mw"]
        .sum()
        .reset_index()
    )

    # Create proper datetime column with UTC timezone
    result_grouped["datetime_utc"] = pd.to_datetime(
        result_grouped["settlementDate"]
    ) + pd.to_timedelta((result_grouped["settlementPeriod"] - 1) * 30, unit="minutes")

    # Ensure timezone-aware (handle both cases)
    if result_grouped["datetime_utc"].dt.tz is None:
        result_grouped["datetime_utc"] = result_grouped["datetime_utc"].dt.tz_localize(
            "UTC"
        )
    else:
        result_grouped["datetime_utc"] = result_grouped["datetime_utc"].dt.tz_convert(
            "UTC"
        )

    print(f"  -> Success, {len(result_grouped):,} rows returned.")
    return result_grouped[["datetime_utc", "generation_mw"]]


def get_system_prices(client, start_date, end_date):
    """Get system prices from system costs table."""
    print("🔍 Running query for: System Prices")

    query = f"""
    SELECT
        settlementDate,
        settlementPeriod,
        AVG(CAST(systemSellPrice AS FLOAT64)) AS system_sell_price,
        AVG(CAST(systemBuyPrice AS FLOAT64)) AS system_buy_price
    FROM `{PROJECT_ID}.uk_energy_insights.bmrs_costs`
    WHERE settlementDate >= '{start_date}'
      AND settlementDate <= '{end_date}'
    GROUP BY settlementDate, settlementPeriod
    ORDER BY settlementDate, settlementPeriod
    """

    result = client.query(query).to_dataframe()

    if result.empty:
        print("  -> No system prices data found")
        return pd.DataFrame()

    # Create proper datetime column with UTC timezone
    result["datetime_utc"] = pd.to_datetime(result["settlementDate"]) + pd.to_timedelta(
        (result["settlementPeriod"] - 1) * 30, unit="minutes"
    )

    # Ensure timezone-aware (handle both cases)
    if result["datetime_utc"].dt.tz is None:
        result["datetime_utc"] = result["datetime_utc"].dt.tz_localize("UTC")
    else:
        result["datetime_utc"] = result["datetime_utc"].dt.tz_convert("UTC")

    print(f"  -> Success, {len(result):,} rows returned.")
    return result[["datetime_utc", "system_sell_price", "system_buy_price"]]


def get_market_index_prices(client, start_date, end_date):
    """Get market index prices for historical data."""
    print("🔍 Running query for: Market Index Prices")

    query = f"""
    SELECT
        settlementDate,
        settlementPeriod,
        AVG(CAST(price AS FLOAT64)) AS market_index_price
    FROM `{PROJECT_ID}.uk_energy_insights.bmrs_mid`
    WHERE settlementDate >= '{start_date}'
      AND settlementDate <= '{end_date}'
    GROUP BY settlementDate, settlementPeriod
    ORDER BY settlementDate, settlementPeriod
    """

    result = client.query(query).to_dataframe()

    if result.empty:
        print("  -> No market index prices data found")
        return pd.DataFrame()

    # Create proper datetime column with UTC timezone
    result["datetime_utc"] = pd.to_datetime(result["settlementDate"]) + pd.to_timedelta(
        (result["settlementPeriod"] - 1) * 30, unit="minutes"
    )

    # Ensure timezone-aware (handle both cases)
    if result["datetime_utc"].dt.tz is None:
        result["datetime_utc"] = result["datetime_utc"].dt.tz_localize("UTC")
    else:
        result["datetime_utc"] = result["datetime_utc"].dt.tz_convert("UTC")

    print(f"  -> Success, {len(result):,} rows returned.")
    return result[["datetime_utc", "market_index_price"]]


def combine_price_data(system_prices, market_prices, full_timeline):
    """Combine system prices and market index prices to create complete price timeline."""
    print("🔗 Combining price data sources...")

    # Start with the full timeline
    combined = full_timeline.copy()

    # Add system prices where available (recent data)
    if not system_prices.empty:
        combined = pd.merge(combined, system_prices, on="datetime_utc", how="left")
        print(f"  -> Added system prices for {len(system_prices)} periods")
    else:
        combined["system_sell_price"] = None
        combined["system_buy_price"] = None

    # Add market index prices where available (historical data)
    if not market_prices.empty:
        combined = pd.merge(combined, market_prices, on="datetime_utc", how="left")
        print(f"  -> Added market index prices for {len(market_prices)} periods")
    else:
        combined["market_index_price"] = None

    # Create unified price columns
    # Use system prices when available, fall back to market prices
    combined["effectivePrice"] = combined["system_sell_price"].fillna(
        combined["market_index_price"]
    )
    combined["buyPrice"] = combined["system_buy_price"].fillna(
        combined["market_index_price"]
    )  # Assume sell=buy for market prices

    # Create price source indicator
    combined["priceSource"] = "None"
    combined.loc[combined["system_sell_price"].notna(), "priceSource"] = "System"
    combined.loc[
        (combined["system_sell_price"].isna())
        & (combined["market_index_price"].notna()),
        "priceSource",
    ] = "Market"

    # Fill remaining nulls with 0
    combined["effectivePrice"] = combined["effectivePrice"].fillna(0)
    combined["buyPrice"] = combined["buyPrice"].fillna(0)

    price_coverage = {
        "System": len(combined[combined["priceSource"] == "System"]),
        "Market": len(combined[combined["priceSource"] == "Market"]),
        "None": len(combined[combined["priceSource"] == "None"]),
    }

    print(
        f"  -> Price data coverage: System={price_coverage['System']:,}, Market={price_coverage['Market']:,}, None={price_coverage['None']:,}"
    )

    return combined


def main():
    """Main function to run the enhanced HUMR-1 report."""
    print("🚀 Starting Enhanced HUMR-1 Generation Report with Historical Pricing...")
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
    print("🗓️ Creating master 30-minute timeline...")
    full_date_range = pd.date_range(
        start=start_date, end=end_date, freq="30min", tz="UTC"
    )
    master_df = pd.DataFrame(full_date_range, columns=["datetime_utc"])
    print(f"✅ Master timeline created with {len(master_df):,} settlement periods.")

    # 4. Fetch all data sources
    humr1_df = get_humr1_generation(bq_client, start_date, end_date)
    system_prices_df = get_system_prices(bq_client, start_date, end_date)
    market_prices_df = get_market_index_prices(bq_client, start_date, end_date)

    # 5. Combine price data from multiple sources
    combined_prices = combine_price_data(system_prices_df, market_prices_df, master_df)

    # 6. Merge all data
    print("🔗 Merging all data...")

    # Merge HUMR-1 generation data
    if not humr1_df.empty:
        master_df = pd.merge(master_df, humr1_df, on="datetime_utc", how="left")
        master_df["humr1_generation_mw"] = master_df["generation_mw"].ffill().fillna(0)
        master_df.drop("generation_mw", axis=1, inplace=True)
    else:
        master_df["humr1_generation_mw"] = 0

    # Merge price data
    master_df = pd.merge(master_df, combined_prices, on="datetime_utc", how="left")

    # 7. Final cleanup
    print("🧹 Cleaning final dataset...")
    master_df["effectivePrice"] = master_df["effectivePrice"].fillna(0)
    master_df["buyPrice"] = master_df["buyPrice"].fillna(0)
    master_df["priceSource"] = master_df["priceSource"].fillna("None")

    # Rename columns for clarity
    master_df.rename(
        columns={
            "effectivePrice": "systemSellPrice",
            "buyPrice": "systemBuyPrice",
            "priceSource": "priceCategory",
        },
        inplace=True,
    )

    print(f"✅ Final dataset ready with {len(master_df):,} rows.")
    print(f"📊 Columns: {list(master_df.columns)}")

    # Show price data summary
    price_summary = master_df[master_df["systemSellPrice"] > 0]
    if not price_summary.empty:
        print(
            f"💰 Price Range: £{price_summary['systemSellPrice'].min():.2f} - £{price_summary['systemSellPrice'].max():.2f} per MWh"
        )
        print(
            f"💰 Average Price: £{price_summary['systemSellPrice'].mean():.2f} per MWh"
        )

        # Show breakdown by price source
        source_counts = master_df["priceCategory"].value_counts()
        print(f"📊 Price Sources: {dict(source_counts)}")

    # 8. Create a new Google Sheet and write the data
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    sheet_name = f"HUMR-1 Enhanced Report with Historical Pricing - {timestamp}"
    sheet_id, sheet_url = create_new_google_sheet(sheets_service, sheet_name)

    if sheet_id:
        write_to_google_sheet(sheets_service, sheet_id, master_df)

    # 9. Final summary
    print("\n" + "=" * 70)
    print("🎉 ENHANCED HUMR-1 REPORT COMPLETE 🎉")
    print("=" * 70)
    print(f"📊 New Google Sheet URL: {sheet_url}")
    print(f"📈 Total Records:        {len(master_df):,}")
    print(f"📅 Data Period:          {start_date} to {end_date}")

    if not price_summary.empty:
        print(
            f"💰 Price Range:          £{price_summary['systemSellPrice'].min():.2f} - £{price_summary['systemSellPrice'].max():.2f} per MWh"
        )
        print(
            f"💰 Average Price:        £{price_summary['systemSellPrice'].mean():.2f} per MWh"
        )

    print("\n✅ Process complete!")


if __name__ == "__main__":
    main()

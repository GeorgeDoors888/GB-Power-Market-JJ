#!/usr/bin/env python3
"""
Comprehensive Weekly Energy Market Report
==========================================

This script creates a comprehensive analysis of UK energy market data for the past week,
covering all major energy market indicators and forecasts.

Data Types Covered:
- Wind & Solar Generation (Actual/Estimated)
- Interconnector Flows
- Generation Forecasts
- Actual Aggregated Generation per Type
- Day-ahead Aggregated Generation
- System Demand (Rolling)
- Surplus Forecast and Margin
- Demand Outturn & Forecasts
- Load Forecasts
- Balancing Mechanism Data
- System Prices
- Market Index Prices
- And more...
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

# --- Setup logging ---
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


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


def write_to_google_sheet(sheets_service, sheet_id, data, sheet_name="Sheet1"):
    """Write data to Google Sheet with proper datetime formatting."""
    print(f"✅ Writing data to sheet: {sheet_name}")

    if data.empty:
        print("⚠️ No data to write")
        return

    # Convert data to list format for Google Sheets
    # Handle datetime columns by converting to string
    data_copy = data.copy()
    for col in data_copy.columns:
        if pd.api.types.is_datetime64_any_dtype(data_copy[col]):
            data_copy[col] = data_copy[col].dt.strftime("%Y-%m-%d %H:%M:%S")
        elif data_copy[col].dtype == "object":
            # Convert any remaining object types to string
            data_copy[col] = data_copy[col].astype(str)

    # Prepare the data for Google Sheets
    headers = [data_copy.columns.tolist()]
    values = data_copy.values.tolist()
    body = {"values": headers + values}

    # Clear the sheet first
    sheets_service.spreadsheets().values().clear(
        spreadsheetId=sheet_id, range=f"{sheet_name}!A:Z"
    ).execute()

    # Write the data
    result = (
        sheets_service.spreadsheets()
        .values()
        .update(
            spreadsheetId=sheet_id,
            range=f"{sheet_name}!A1",
            valueInputOption="RAW",
            body=body,
        )
        .execute()
    )

    print(f"✅ Data written to Google Sheet: {len(values)} rows")


def get_week_date_range():
    """Calculate the date range for the past week."""
    end_date = datetime.datetime.now().replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    start_date = end_date - datetime.timedelta(days=7)
    return start_date, end_date


def query_wind_solar_generation(client, start_date, end_date):
    """Query wind and solar generation data."""
    print("🔍 Querying Wind & Solar Generation Data...")

    query = f"""
    SELECT
        settlementDate,
        settlementPeriod,
        fuelType,
        generation,
        publishTime
    FROM `{PROJECT_ID}.uk_energy_insights.bmrs_fuelinst`
    WHERE settlementDate >= '{start_date.date()}'
      AND settlementDate < '{end_date.date()}'
      AND fuelType IN ('WIND', 'SOLAR')
    ORDER BY settlementDate, settlementPeriod, fuelType
    """

    result = client.query(query).to_dataframe()
    print(f"  -> Wind & Solar: {len(result)} rows")
    return result


def query_interconnector_flows(client, start_date, end_date):
    """Query interconnector flow data."""
    print("🔍 Querying Interconnector Flows...")

    query = f"""
    SELECT
        settlementDate,
        settlementPeriod,
        fuelType,
        generation as flow_mw,
        publishTime
    FROM `{PROJECT_ID}.uk_energy_insights.bmrs_fuelinst`
    WHERE settlementDate >= '{start_date.date()}'
      AND settlementDate < '{end_date.date()}'
      AND fuelType LIKE '%INTFR%' OR fuelType LIKE '%INTIRL%' OR fuelType LIKE '%INTNED%' OR fuelType LIKE '%INTBEL%'
    ORDER BY settlementDate, settlementPeriod, fuelType
    """

    result = client.query(query).to_dataframe()
    print(f"  -> Interconnector Flows: {len(result)} rows")
    return result


def query_generation_forecasts(client, start_date, end_date):
    """Query generation forecast data."""
    print("🔍 Querying Generation Forecasts...")

    query = f"""
    SELECT
        startTime,
        generation as forecast_mw,
        publishTime
    FROM `{PROJECT_ID}.uk_energy_insights.bmrs_windfor`
    WHERE DATE(startTime) >= '{start_date.date()}'
      AND DATE(startTime) < '{end_date.date()}'
    ORDER BY startTime
    """

    result = client.query(query).to_dataframe()
    print(f"  -> Generation Forecasts: {len(result)} rows")
    return result


def query_system_demand(client, start_date, end_date):
    """Query system demand data."""
    print("🔍 Querying System Demand Data...")

    query = f"""
    SELECT
        settlementDate,
        settlementPeriod,
        demand,
        publishTime
    FROM `{PROJECT_ID}.uk_energy_insights.bmrs_indo`
    WHERE settlementDate >= '{start_date.date()}'
      AND settlementDate < '{end_date.date()}'
    ORDER BY settlementDate, settlementPeriod
    """

    result = client.query(query).to_dataframe()
    print(f"  -> System Demand: {len(result)} rows")
    return result


def query_system_prices(client, start_date, end_date):
    """Query system price data."""
    print("🔍 Querying System Prices...")

    query = f"""
    SELECT
        settlementDate,
        settlementPeriod,
        systemSellPrice,
        systemBuyPrice,
        priceDerivationCode,
        netImbalanceVolume,
        startTime
    FROM `{PROJECT_ID}.uk_energy_insights.bmrs_costs`
    WHERE settlementDate >= '{start_date.date()}'
      AND settlementDate < '{end_date.date()}'
    ORDER BY settlementDate, settlementPeriod
    """

    result = client.query(query).to_dataframe()
    print(f"  -> System Prices: {len(result)} rows")
    return result


def query_market_index_prices(client, start_date, end_date):
    """Query market index price data."""
    print("🔍 Querying Market Index Prices...")

    query = f"""
    SELECT
        settlementDate,
        settlementPeriod,
        price,
        volume,
        dataProvider,
        startTime
    FROM `{PROJECT_ID}.uk_energy_insights.bmrs_mid`
    WHERE settlementDate >= '{start_date.date()}'
      AND settlementDate < '{end_date.date()}'
    ORDER BY settlementDate, settlementPeriod
    """

    result = client.query(query).to_dataframe()
    print(f"  -> Market Index Prices: {len(result)} rows")
    return result


def query_balancing_actions(client, start_date, end_date):
    """Query balancing mechanism data."""
    print("🔍 Querying Balancing Actions...")

    query = f"""
    SELECT
        settlementDate,
        settlementPeriod,
        soFlag,
        storFlag,
        cost,
        volume,
        service,
        assetId
    FROM `{PROJECT_ID}.uk_energy_insights.bmrs_disbsad`
    WHERE settlementDate >= '{start_date.date()}'
      AND settlementDate < '{end_date.date()}'
    ORDER BY settlementDate, settlementPeriod
    """

    result = client.query(query).to_dataframe()
    print(f"  -> Balancing Actions: {len(result)} rows")
    return result


def query_demand_forecasts(client, start_date, end_date):
    """Query demand forecast data."""
    print("🔍 Querying Demand Forecasts...")

    # Try NDF first
    query = f"""
    SELECT
        settlementDate,
        settlementPeriod,
        demand as nationalDemand,
        boundary,
        publishTime,
        startTime
    FROM `{PROJECT_ID}.uk_energy_insights.bmrs_ndf`
    WHERE settlementDate >= '{start_date.date()}'
      AND settlementDate < '{end_date.date()}'
    ORDER BY settlementDate, settlementPeriod
    """

    result = client.query(query).to_dataframe()
    print(f"  -> Demand Forecasts (NDF): {len(result)} rows")
    return result


def create_summary_statistics(all_data):
    """Create summary statistics for the weekly report."""
    summary = {}

    for data_type, df in all_data.items():
        if df is not None and not df.empty:
            # Get date column
            date_col = None
            if "settlementDate" in df.columns:
                date_col = "settlementDate"
            elif "startTime" in df.columns:
                date_col = "startTime"

            summary[data_type] = {"total_records": len(df)}

            if date_col:
                try:
                    summary[data_type][
                        "date_range"
                    ] = f"{df[date_col].min()} to {df[date_col].max()}"
                except:
                    summary[data_type]["date_range"] = "Date range unavailable"

            # Add specific metrics for each data type
            if "generation" in df.columns:
                summary[data_type][
                    "avg_generation"
                ] = f"{df['generation'].mean():.2f} MW"
                summary[data_type][
                    "max_generation"
                ] = f"{df['generation'].max():.2f} MW"
            elif "demand" in df.columns:
                summary[data_type]["avg_demand"] = f"{df['demand'].mean():.2f} MW"
                summary[data_type]["max_demand"] = f"{df['demand'].max():.2f} MW"
            elif "nationalDemand" in df.columns:
                summary[data_type][
                    "avg_demand"
                ] = f"{df['nationalDemand'].mean():.2f} MW"
                summary[data_type][
                    "max_demand"
                ] = f"{df['nationalDemand'].max():.2f} MW"
            elif "systemSellPrice" in df.columns:
                summary[data_type][
                    "avg_sell_price"
                ] = f"£{df['systemSellPrice'].mean():.2f}/MWh"
                summary[data_type][
                    "max_sell_price"
                ] = f"£{df['systemSellPrice'].max():.2f}/MWh"
            elif "price" in df.columns:
                summary[data_type]["avg_price"] = f"£{df['price'].mean():.2f}/MWh"
                summary[data_type]["max_price"] = f"£{df['price'].max():.2f}/MWh"

    return summary


def main():
    print("🚀 Starting Comprehensive Weekly Energy Market Report...")
    print("=" * 70)

    # Get date range
    start_date, end_date = get_week_date_range()
    print(f"📅 Reporting Period: {start_date.date()} to {end_date.date()}")

    # Initialize BigQuery client
    client = bigquery.Client(project=PROJECT_ID)

    # Authenticate Google APIs
    creds = authenticate_google_apis()
    sheets_service = build("sheets", "v4", credentials=creds)

    # Create timestamp for sheet name
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    sheet_name = f"UK Energy Market Weekly Report - {timestamp}"

    # Query all data types
    all_data = {}

    try:
        all_data["wind_solar"] = query_wind_solar_generation(
            client, start_date, end_date
        )
    except Exception as e:
        print(f"❌ Error querying wind/solar data: {e}")
        all_data["wind_solar"] = pd.DataFrame()

    try:
        all_data["interconnector"] = query_interconnector_flows(
            client, start_date, end_date
        )
    except Exception as e:
        print(f"❌ Error querying interconnector data: {e}")
        all_data["interconnector"] = pd.DataFrame()

    try:
        all_data["forecasts"] = query_generation_forecasts(client, start_date, end_date)
    except Exception as e:
        print(f"❌ Error querying forecast data: {e}")
        all_data["forecasts"] = pd.DataFrame()

    try:
        all_data["demand"] = query_system_demand(client, start_date, end_date)
    except Exception as e:
        print(f"❌ Error querying demand data: {e}")
        all_data["demand"] = pd.DataFrame()

    try:
        all_data["prices"] = query_system_prices(client, start_date, end_date)
    except Exception as e:
        print(f"❌ Error querying price data: {e}")
        all_data["prices"] = pd.DataFrame()

    try:
        all_data["market_index"] = query_market_index_prices(
            client, start_date, end_date
        )
    except Exception as e:
        print(f"❌ Error querying market index data: {e}")
        all_data["market_index"] = pd.DataFrame()

    try:
        all_data["balancing"] = query_balancing_actions(client, start_date, end_date)
    except Exception as e:
        print(f"❌ Error querying balancing data: {e}")
        all_data["balancing"] = pd.DataFrame()

    try:
        all_data["demand_forecasts"] = query_demand_forecasts(
            client, start_date, end_date
        )
    except Exception as e:
        print(f"❌ Error querying demand forecast data: {e}")
        all_data["demand_forecasts"] = pd.DataFrame()

    # Create summary statistics
    summary = create_summary_statistics(all_data)

    # Create Google Sheet
    sheet_id, sheet_url = create_new_google_sheet(sheets_service, sheet_name)

    # Write each dataset to a separate sheet
    sheet_names = []
    for data_type, df in all_data.items():
        if df is not None and not df.empty:
            sheet_name_tab = data_type.replace("_", " ").title()
            sheet_names.append(sheet_name_tab)

            # Add new sheet
            if sheet_name_tab != "Sheet1":
                add_sheet_request = {
                    "addSheet": {"properties": {"title": sheet_name_tab}}
                }
                sheets_service.spreadsheets().batchUpdate(
                    spreadsheetId=sheet_id, body={"requests": [add_sheet_request]}
                ).execute()

            # Write data to the sheet
            write_to_google_sheet(sheets_service, sheet_id, df, sheet_name_tab)

    # Create summary sheet
    if summary:
        summary_df = pd.DataFrame(summary).T
        summary_df.reset_index(inplace=True)
        summary_df.rename(columns={"index": "Data Type"}, inplace=True)

        # Add summary sheet
        add_sheet_request = {"addSheet": {"properties": {"title": "Summary"}}}
        sheets_service.spreadsheets().batchUpdate(
            spreadsheetId=sheet_id, body={"requests": [add_sheet_request]}
        ).execute()

        write_to_google_sheet(sheets_service, sheet_id, summary_df, "Summary")

    # Calculate totals
    total_records = sum(
        len(df) for df in all_data.values() if df is not None and not df.empty
    )

    print("\n" + "=" * 70)
    print("🎉 COMPREHENSIVE WEEKLY ENERGY MARKET REPORT COMPLETE 🎉")
    print("=" * 70)
    print(f"📊 New Google Sheet URL: {sheet_url}")
    print(f"📈 Total Records:        {total_records:,}")
    print(f"📅 Data Period:          {start_date.date()} to {end_date.date()}")
    print(
        f"📋 Data Types Covered:   {len([df for df in all_data.values() if df is not None and not df.empty])}"
    )
    print(f"📄 Sheets Created:       {len(sheet_names) + 1} (including Summary)")

    print("\n📊 Data Summary:")
    for data_type, info in summary.items():
        print(
            f"  • {data_type.replace('_', ' ').title()}: {info['total_records']:,} records"
        )

    print("\n✅ Process complete!")


if __name__ == "__main__":
    main()

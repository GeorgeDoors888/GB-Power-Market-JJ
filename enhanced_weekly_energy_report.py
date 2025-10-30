#!/usr/bin/env python3
"""
Enhanced UK Energy Market Weekly Report
=======================================

This script creates an enhanced comprehensive analysis of UK energy market data
for the past week, covering the maximum available energy market indicators.
"""

import datetime
import logging
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
    "https://www.googleapis.com/auth/bigquery",
]
PROJECT_ID = "jibber-jabber-knowledge"

logging.basicConfig(level=logging.INFO)


def authenticate_google_apis():
    flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRET_FILE, SCOPES)
    creds = flow.run_local_server(port=0)
    return creds


def create_new_google_sheet(sheets_service, sheet_name):
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
    if data.empty:
        print(f"⚠️ No data to write for {sheet_name}")
        return

    # Convert datetime columns to strings
    data_copy = data.copy()
    for col in data_copy.columns:
        if pd.api.types.is_datetime64_any_dtype(data_copy[col]):
            data_copy[col] = data_copy[col].dt.strftime("%Y-%m-%d %H:%M:%S")
        elif data_copy[col].dtype == "object":
            data_copy[col] = data_copy[col].astype(str)

    # Add new sheet if needed
    if sheet_name != "Sheet1":
        try:
            add_sheet_request = {"addSheet": {"properties": {"title": sheet_name}}}
            sheets_service.spreadsheets().batchUpdate(
                spreadsheetId=sheet_id, body={"requests": [add_sheet_request]}
            ).execute()
        except Exception as e:
            if "already exists" not in str(e):
                print(f"Warning: Could not create sheet {sheet_name}: {e}")

    # Prepare and write data
    headers = [data_copy.columns.tolist()]
    values = data_copy.values.tolist()
    body = {"values": headers + values}

    sheets_service.spreadsheets().values().clear(
        spreadsheetId=sheet_id, range=f"{sheet_name}!A:Z"
    ).execute()

    sheets_service.spreadsheets().values().update(
        spreadsheetId=sheet_id,
        range=f"{sheet_name}!A1",
        valueInputOption="RAW",
        body=body,
    ).execute()

    print(f"✅ {sheet_name}: {len(values)} rows written")


def get_week_date_range():
    end_date = datetime.datetime.now().replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    start_date = end_date - datetime.timedelta(days=7)
    return start_date, end_date


def safe_query(client, query_name, query):
    """Execute query with error handling."""
    try:
        result = client.query(query).to_dataframe()
        print(f"  -> {query_name}: {len(result)} rows")
        return result
    except Exception as e:
        print(f"❌ Error in {query_name}: {e}")
        return pd.DataFrame()


def main():
    print("🚀 Starting Enhanced UK Energy Market Weekly Report...")
    print("=" * 70)

    start_date, end_date = get_week_date_range()
    print(f"📅 Reporting Period: {start_date.date()} to {end_date.date()}")

    client = bigquery.Client(project=PROJECT_ID)
    creds = authenticate_google_apis()
    sheets_service = build("sheets", "v4", credentials=creds)

    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    sheet_name = f"Enhanced UK Energy Market Report - {timestamp}"
    sheet_id, sheet_url = create_new_google_sheet(sheets_service, sheet_name)

    all_data = {}

    # 1. Wind & Solar Generation
    print("🔍 Querying Wind & Solar Generation...")
    all_data["wind_solar"] = safe_query(
        client,
        "Wind & Solar",
        f"""
        SELECT settlementDate, settlementPeriod, fuelType, generation, publishTime
        FROM `{PROJECT_ID}.uk_energy_insights.bmrs_fuelinst`
        WHERE settlementDate >= '{start_date.date()}'
          AND settlementDate < '{end_date.date()}'
          AND fuelType IN ('WIND', 'SOLAR')
        ORDER BY settlementDate, settlementPeriod, fuelType
    """,
    )

    # 2. All Fuel Types Generation
    print("🔍 Querying All Generation by Fuel Type...")
    all_data["all_generation"] = safe_query(
        client,
        "All Generation",
        f"""
        SELECT settlementDate, settlementPeriod, fuelType, generation, publishTime
        FROM `{PROJECT_ID}.uk_energy_insights.bmrs_fuelinst`
        WHERE settlementDate >= '{start_date.date()}'
          AND settlementDate < '{end_date.date()}'
        ORDER BY settlementDate, settlementPeriod, fuelType
        LIMIT 50000
    """,
    )

    # 3. System Prices & Costs
    print("🔍 Querying System Prices & Costs...")
    all_data["system_prices"] = safe_query(
        client,
        "System Prices",
        f"""
        SELECT settlementDate, settlementPeriod, systemSellPrice, systemBuyPrice,
               priceDerivationCode, netImbalanceVolume, startTime
        FROM `{PROJECT_ID}.uk_energy_insights.bmrs_costs`
        WHERE settlementDate >= '{start_date.date()}'
          AND settlementDate < '{end_date.date()}'
        ORDER BY settlementDate, settlementPeriod
    """,
    )

    # 4. Market Index Prices
    print("🔍 Querying Market Index Prices...")
    all_data["market_index"] = safe_query(
        client,
        "Market Index",
        f"""
        SELECT settlementDate, settlementPeriod, price, volume, dataProvider, startTime
        FROM `{PROJECT_ID}.uk_energy_insights.bmrs_mid`
        WHERE settlementDate >= '{start_date.date()}'
          AND settlementDate < '{end_date.date()}'
        ORDER BY settlementDate, settlementPeriod
    """,
    )

    # 5. Balancing Actions
    print("🔍 Querying Balancing Actions...")
    all_data["balancing"] = safe_query(
        client,
        "Balancing",
        f"""
        SELECT settlementDate, settlementPeriod, soFlag, storFlag, cost, volume, service, assetId
        FROM `{PROJECT_ID}.uk_energy_insights.bmrs_disbsad`
        WHERE settlementDate >= '{start_date.date()}'
          AND settlementDate < '{end_date.date()}'
        ORDER BY settlementDate, settlementPeriod
    """,
    )

    # 6. Demand Forecasts
    print("🔍 Querying Demand Forecasts...")
    all_data["demand_forecasts"] = safe_query(
        client,
        "Demand Forecasts",
        f"""
        SELECT settlementDate, settlementPeriod, demand, boundary, publishTime, startTime
        FROM `{PROJECT_ID}.uk_energy_insights.bmrs_ndf`
        WHERE settlementDate >= '{start_date.date()}'
          AND settlementDate < '{end_date.date()}'
        ORDER BY settlementDate, settlementPeriod
    """,
    )

    # 7. Wind Forecasts
    print("🔍 Querying Wind Forecasts...")
    all_data["wind_forecasts"] = safe_query(
        client,
        "Wind Forecasts",
        f"""
        SELECT startTime, generation as forecast_mw, publishTime
        FROM `{PROJECT_ID}.uk_energy_insights.bmrs_windfor`
        WHERE DATE(startTime) >= '{start_date.date()}'
          AND DATE(startTime) < '{end_date.date()}'
        ORDER BY startTime
    """,
    )

    # 8. Physical Notifications
    print("🔍 Querying Physical Notifications...")
    all_data["physical_notifications"] = safe_query(
        client,
        "Physical Notifications",
        f"""
        SELECT settlementDate, settlementPeriod, bmUnit, levelFrom, levelTo, publishTime
        FROM `{PROJECT_ID}.uk_energy_insights.bmrs_pn`
        WHERE settlementDate >= '{start_date.date()}'
          AND settlementDate < '{end_date.date()}'
        ORDER BY settlementDate, settlementPeriod
        LIMIT 30000
    """,
    )

    # 9. Frequency Data
    print("🔍 Querying Frequency Data...")
    all_data["frequency"] = safe_query(
        client,
        "Frequency",
        f"""
        SELECT settlementDate, settlementPeriod, frequency, publishTime
        FROM `{PROJECT_ID}.uk_energy_insights.bmrs_freq`
        WHERE settlementDate >= '{start_date.date()}'
          AND settlementDate < '{end_date.date()}'
        ORDER BY settlementDate, settlementPeriod
    """,
    )

    # 10. BOD Data (Settlement)
    print("🔍 Querying BOD Settlement Data...")
    all_data["bod_settlement"] = safe_query(
        client,
        "BOD Settlement",
        f"""
        SELECT settlementDate, settlementPeriod, bmUnit, accountType, balancingMechanismPositionVolume, publishTime
        FROM `{PROJECT_ID}.uk_energy_insights.bmrs_bod`
        WHERE settlementDate >= '{start_date.date()}'
          AND settlementDate < '{end_date.date()}'
        ORDER BY settlementDate, settlementPeriod
        LIMIT 50000
    """,
    )

    # Write all data to sheets
    print("\n📊 Writing data to Google Sheets...")
    for data_type, df in all_data.items():
        if df is not None and not df.empty:
            sheet_name_tab = data_type.replace("_", " ").title()
            write_to_google_sheet(sheets_service, sheet_id, df, sheet_name_tab)

    # Create summary
    summary_data = []
    total_records = 0
    for data_type, df in all_data.items():
        if df is not None and not df.empty:
            records = len(df)
            total_records += records

            # Calculate basic stats
            stats = {
                "Data Type": data_type.replace("_", " ").title(),
                "Records": records,
            }

            # Add specific metrics
            if "generation" in df.columns:
                stats["Avg Generation (MW)"] = f"{df['generation'].mean():.1f}"
                stats["Max Generation (MW)"] = f"{df['generation'].max():.1f}"
            elif "demand" in df.columns:
                stats["Avg Demand (MW)"] = f"{df['demand'].mean():.1f}"
                stats["Max Demand (MW)"] = f"{df['demand'].max():.1f}"
            elif "systemSellPrice" in df.columns:
                stats["Avg Sell Price (£/MWh)"] = f"{df['systemSellPrice'].mean():.2f}"
                stats["Max Sell Price (£/MWh)"] = f"{df['systemSellPrice'].max():.2f}"
            elif "price" in df.columns:
                stats["Avg Price (£/MWh)"] = f"{df['price'].mean():.2f}"
                stats["Max Price (£/MWh)"] = f"{df['price'].max():.2f}"
            elif "frequency" in df.columns:
                stats["Avg Frequency (Hz)"] = f"{df['frequency'].mean():.3f}"
                stats["Min Frequency (Hz)"] = f"{df['frequency'].min():.3f}"

            summary_data.append(stats)

    if summary_data:
        summary_df = pd.DataFrame(summary_data)
        write_to_google_sheet(sheets_service, sheet_id, summary_df, "Summary")

    # Print final results
    print("\n" + "=" * 70)
    print("🎉 ENHANCED UK ENERGY MARKET REPORT COMPLETE 🎉")
    print("=" * 70)
    print(f"📊 Google Sheet URL: {sheet_url}")
    print(f"📈 Total Records: {total_records:,}")
    print(f"📅 Period: {start_date.date()} to {end_date.date()}")
    print(
        f"📋 Data Types: {len([df for df in all_data.values() if df is not None and not df.empty])}"
    )

    print("\n📊 Dataset Summary:")
    for data_type, df in all_data.items():
        if df is not None and not df.empty:
            print(f"  • {data_type.replace('_', ' ').title()}: {len(df):,} records")

    print("\n✅ Enhanced comprehensive report complete!")


if __name__ == "__main__":
    main()

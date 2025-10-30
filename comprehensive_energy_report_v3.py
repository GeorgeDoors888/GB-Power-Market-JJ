#!/usr/bin/env python3
"""
Comprehensive UK Energy Generation and Market Report V3
========================================================

This script creates a comprehensive report including:
- Complete fuel mix breakdown (all generation types in GW)
- Market Index Prices (APX, N2EX)
- System Buy/Sell PFrices with Net Imbalance Volume
- T_HUMR-1 generation data
- Exports to CSV, Google Sheets, and creates a summary document

Based on ELEXON/BMRS data analysis and NESO documentation.
"""

import datetime
import json
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
    "https://www.googleapis.com/auth/documents",
    "https://www.googleapis.com/auth/cloud-platform",
]
OUTPUT_DIR = "/Users/georgemajor/jibber-jabber 24 august 2025 big bop"
PROJECT_ID = "jibber-jabber-knowledge"


# --- Authentication ---
def authenticate_google_apis():
    """Authenticate with Google and return credentials."""
    print("🔐 Authenticating with Google APIs...")
    flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRET_FILE, SCOPES)
    creds = flow.run_local_server(port=0)
    return creds


# --- BigQuery Data Functions ---
def query_bigquery(client, query, name):
    """Runs a query on BigQuery and returns a DataFrame."""
    print(f"📊 Running query for: {name}")
    try:
        df = client.query(query).to_dataframe()
        print(f"  ✅ Success, {len(df):,} rows returned.")
        return df
    except Exception as e:
        print(f"  ❌ Error during BigQuery query for {name}: {e}")
        return pd.DataFrame()


def get_fuel_mix_data(client, start_date, end_date):
    """Get complete fuel mix breakdown from bmrs_fuelinst with correct fuel type codes"""

    # Dynamically adjust time range based on available data
    query_data_coverage = """
    SELECT MIN(settlementDate) as min_date, MAX(settlementDate) as max_date
    FROM `jibber-jabber-knowledge.uk_energy_insights.bmrs_fuelinst`
    WHERE settlementDate BETWEEN DATE_SUB(CURRENT_DATE(), INTERVAL 2 YEAR) AND CURRENT_DATE()
    """
    data_coverage = query_bigquery(
        client, query_data_coverage, "Data Coverage in bmrs_fuelinst"
    )
    if not data_coverage.empty:
        available_start_date = data_coverage["min_date"].iloc[0]
        available_end_date = data_coverage["max_date"].iloc[0]
        print(
            f"📊 Adjusting time range to available data: {available_start_date} to {available_end_date}"
        )
        start_date = max(start_date, available_start_date)
        end_date = min(end_date, available_end_date)
    else:
        print("❌ No data available in bmrs_fuelinst for the past 2 years.")
        return pd.DataFrame()

    # Query for fuel mix data
    fuel_mix_query = f"""
    WITH fuel_aggregated AS (
        SELECT
            TIMESTAMP(settlementDate) + INTERVAL (30 * (settlementPeriod - 1)) MINUTE as datetime_utc,
            fuelType,
            AVG(generation) as avg_generation_mw
        FROM `jibber-jabber-knowledge.uk_energy_insights.bmrs_fuelinst`
        WHERE settlementDate BETWEEN '{start_date}' AND '{end_date}'
        AND fuelType IS NOT NULL
        AND generation IS NOT NULL
        AND generation > 0  -- Only positive generation values
        GROUP BY 1, 2
    )
    SELECT
        datetime_utc,
        ROUND(SUM(CASE WHEN fuelType = 'CCGT' THEN avg_generation_mw ELSE 0 END) / 1000, 3) as gas_generation_gw,
        ROUND(SUM(CASE WHEN fuelType = 'WIND' THEN avg_generation_mw ELSE 0 END) / 1000, 3) as wind_generation_gw,
        ROUND(SUM(CASE WHEN fuelType = 'NUCLEAR' THEN avg_generation_mw ELSE 0 END) / 1000, 3) as nuclear_generation_gw,
        ROUND(SUM(CASE WHEN fuelType = 'COAL' THEN avg_generation_mw ELSE 0 END) / 1000, 3) as coal_generation_gw,
        ROUND(SUM(CASE WHEN fuelType = 'NPSHYD' THEN avg_generation_mw ELSE 0 END) / 1000, 3) as hydro_generation_gw,
        ROUND(SUM(CASE WHEN fuelType = 'BIOMASS' THEN avg_generation_mw ELSE 0 END) / 1000, 3) as biomass_generation_gw,
        ROUND(SUM(CASE WHEN fuelType = 'OIL' THEN avg_generation_mw ELSE 0 END) / 1000, 3) as oil_generation_gw,
        ROUND(SUM(CASE WHEN fuelType = 'OCGT' THEN avg_generation_mw ELSE 0 END) / 1000, 3) as ocgt_generation_gw,
        ROUND(SUM(CASE WHEN fuelType = 'OTHER' THEN avg_generation_mw ELSE 0 END) / 1000, 3) as other_generation_gw,
        ROUND(SUM(CASE WHEN fuelType = 'PS' THEN avg_generation_mw ELSE 0 END) / 1000, 3) as pumped_storage_gw,
        ROUND(SUM(CASE WHEN fuelType NOT IN ('INTNSL', 'INTFR', 'INTELEC', 'INTIFA2', 'INTEW', 'INTIRL', 'INTGRNL', 'INTNEM', 'INTVKL', 'INTNED') THEN avg_generation_mw ELSE 0 END) / 1000, 3) as total_domestic_generation_gw
    FROM fuel_aggregated
    GROUP BY 1
    ORDER BY 1
    """
    df = query_bigquery(client, fuel_mix_query, "Complete Fuel Mix (GW)")

    # Handle missing data: Fill gaps with 0 for numeric columns
    if not df.empty:
        print("✅ Fuel mix data retrieved successfully.")
        df = df.sort_values("datetime_utc")
        numeric_cols = df.select_dtypes(include=["float64", "int64"]).columns
        df[numeric_cols] = df[numeric_cols].fillna(0)
    else:
        print("❌ No fuel mix data available for the specified range.")

    return df


def get_market_index_prices(client, start_date, end_date):
    """Get Market Index Prices from MIDPs (APX and N2EX)"""
    # Check if we have market index data in bmrs_mid table
    market_prices_query = f"""
    SELECT
        TIMESTAMP(settlementDate) + INTERVAL (30 * (settlementPeriod - 1)) MINUTE as datetime_utc,
        AVG(CAST(price AS FLOAT64)) as market_index_price_gbp_per_mwh
    FROM `jibber-jabber-knowledge.uk_energy_insights.bmrs_mid`
    WHERE settlementDate BETWEEN '{start_date}' AND '{end_date}'
    AND price IS NOT NULL
    AND SAFE_CAST(price AS FLOAT64) IS NOT NULL
    GROUP BY 1
    ORDER BY 1
    """
    return query_bigquery(client, market_prices_query, "Market Index Prices (£/MWh)")


def get_system_prices_and_imbalance(client, start_date, end_date):
    """Get System Buy/Sell Prices and Net Imbalance Volume"""
    system_prices_query = f"""
    SELECT
        TIMESTAMP(settlementDate) + INTERVAL (30 * (settlementPeriod - 1)) MINUTE as datetime_utc,
        AVG(CAST(bid AS FLOAT64)) as system_buy_price_gbp_per_mwh,
        AVG(CAST(offer AS FLOAT64)) as system_sell_price_gbp_per_mwh
    FROM `jibber-jabber-knowledge.uk_energy_insights.bmrs_bod`
    WHERE settlementDate BETWEEN '{start_date}' AND '{end_date}'
    AND bid IS NOT NULL AND offer IS NOT NULL
    AND SAFE_CAST(bid AS FLOAT64) IS NOT NULL
    AND SAFE_CAST(offer AS FLOAT64) IS NOT NULL
    GROUP BY 1
    ORDER BY 1
    """
    return query_bigquery(client, system_prices_query, "System Buy/Sell Prices (£/MWh)")


def get_humr1_generation(client, start_date, end_date):
    """Get T_HUMR-1 generation data"""
    humr1_query = f"""
    SELECT
        TIMESTAMP_TRUNC(timeTo, HOUR) as datetime_utc,
        AVG(levelTo) as humr1_generation_mw
    FROM `jibber-jabber-knowledge.uk_energy_insights.bmrs_pn`
    WHERE bmUnit = 'T_HUMR-1'
    AND DATE(timeTo) BETWEEN '{start_date}' AND '{end_date}'
    GROUP BY 1
    ORDER BY 1
    """
    return query_bigquery(client, humr1_query, "T_HUMR-1 Generation")


def get_net_imbalance_volume(client, start_date, end_date):
    """Get Net Imbalance Volume from system balancing data"""
    # Use the correct column name 'imbalance' from bmrs_imbalngc
    niv_query = f"""
    SELECT
        TIMESTAMP(settlementDate) + INTERVAL (30 * (settlementPeriod - 1)) MINUTE as datetime_utc,
        AVG(CAST(imbalance AS FLOAT64)) as net_imbalance_volume_mwh
    FROM `jibber-jabber-knowledge.uk_energy_insights.bmrs_imbalngc`
    WHERE settlementDate BETWEEN '{start_date}' AND '{end_date}'
    AND imbalance IS NOT NULL
    AND SAFE_CAST(imbalance AS FLOAT64) IS NOT NULL
    GROUP BY 1
    ORDER BY 1
    """
    return query_bigquery(client, niv_query, "Net Imbalance Volume (MWh)")


def get_elexon_bmrs_data(client, start_date, end_date):
    """
    Queries and merges all required ELEXON/BMRS data for a fixed 24-month period.
    """
    print(f"� Starting data retrieval from {start_date} to {end_date}...")

    # 1. Create a complete date range for the last 24 months
    full_date_range = pd.date_range(
        start=start_date, end=end_date, freq="30min", tz="UTC"
    )
    merged_df = pd.DataFrame(full_date_range, columns=["datetime_utc"])

    # 2. Get all fuel generation data in a pivoted format
    fuel_df = get_all_fuel_generation(client, start_date, end_date)
    if not fuel_df.empty:
        merged_df = pd.merge(merged_df, fuel_df, on="datetime_utc", how="left")

    # 3. Define and run queries for other datasets
    other_queries = {
        "market_prices": f"""
        SELECT
            TIMESTAMP(settlementDate) + INTERVAL (30 * (settlementPeriod - 1)) MINUTE as datetime_utc,
            AVG(CAST(price AS FLOAT64)) as market_index_price_gbp_per_mwh
        FROM `jibber-jabber-knowledge.uk_energy_insights.bmrs_mid`
        WHERE settlementDate BETWEEN '{start_date}' AND '{end_date}' AND price IS NOT NULL
        GROUP BY 1
        """,
        "system_prices": f"""
        SELECT
            TIMESTAMP(settlementDate) + INTERVAL (30 * (settlementPeriod - 1)) MINUTE as datetime_utc,
            AVG(CAST(bid AS FLOAT64)) as system_buy_price_gbp_per_mwh,
            AVG(CAST(offer AS FLOAT64)) as system_sell_price_gbp_per_mwh
        FROM `jibber-jabber-knowledge.uk_energy_insights.bmrs_bod`
        WHERE settlementDate BETWEEN '{start_date}' AND '{end_date}' AND bid IS NOT NULL AND offer IS NOT NULL
        GROUP BY 1
        """,
        "niv": f"""
        SELECT
            TIMESTAMP(settlementDate) + INTERVAL (30 * (settlementPeriod - 1)) MINUTE as datetime_utc,
            AVG(CAST(imbalance AS FLOAT64)) as net_imbalance_volume_mwh
        FROM `jibber-jabber-knowledge.uk_energy_insights.bmrs_imbalngc`
        WHERE settlementDate BETWEEN '{start_date}' AND '{end_date}' AND imbalance IS NOT NULL
        GROUP BY 1
        """,
    }

    for name, query in other_queries.items():
        df = query_bigquery(client, query, name)
        if not df.empty:
            merged_df = pd.merge(merged_df, df, on="datetime_utc", how="left")

    # Final cleanup
    merged_df = merged_df.fillna(0)
    print(
        f"✅ Final merged dataset has {len(merged_df):,} rows and {len(merged_df.columns)} columns."
    )
    return merged_df


# --- Data Processing ---
def get_comprehensive_data(client):
    """Queries and merges all required datasets from BigQuery."""
    end_date = datetime.date.today()
    start_date = datetime.date(2025, 9, 1)  # Use recent data that we know exists

    print(f"📅 Querying data from {start_date} to {end_date}")

    # --- Adjust Data Range ---
    # Dynamically determine the available data range
    query_available_dates = """
    SELECT MIN(settlementDate) as min_date, MAX(settlementDate) as max_date
    FROM `jibber-jabber-knowledge.uk_energy_insights.bmrs_bod`
    """
    available_dates = query_bigquery(
        client, query_available_dates, "Available Data Range"
    )
    if not available_dates.empty:
        start_date = available_dates["min_date"].iloc[0]
        end_date = available_dates["max_date"].iloc[0]
        print(f"📅 Adjusted data range: {start_date} to {end_date}")
    else:
        print("❌ No data available in bmrs_bod table. Using default range.")
        start_date = datetime.date(2025, 9, 1)
        end_date = datetime.date.today()

    # --- Validate Settlement Periods ---
    # Ensure 48 settlement periods per day
    validate_settlement_periods_query = f"""
    SELECT COUNT(DISTINCT settlementPeriod) as periods_per_day, settlementDate
    FROM `jibber-jabber-knowledge.uk_energy_insights.bmrs_bod`
    WHERE settlementDate BETWEEN '{start_date}' AND '{end_date}'
    GROUP BY settlementDate
    HAVING periods_per_day != 48
    """
    invalid_periods = query_bigquery(
        client, validate_settlement_periods_query, "Validate Settlement Periods"
    )
    if not invalid_periods.empty:
        print("❌ Warning: Some days do not have 48 settlement periods.")
    else:
        print("✅ All days have 48 settlement periods.")

    # --- Get All Datasets ---
    datasets = {}
    datasets["fuel_mix"] = get_fuel_mix_data(client, start_date, end_date)
    datasets["market_prices"] = get_market_index_prices(client, start_date, end_date)

    # --- Update System Prices Query ---
    # Ensure accurate buy/sell prices
    system_prices_query = f"""
    SELECT
        TIMESTAMP(settlementDate) + INTERVAL (30 * (settlementPeriod - 1)) MINUTE as datetime_utc,
        AVG(CAST(bid AS FLOAT64)) as system_buy_price_gbp_per_mwh,
        AVG(CAST(offer AS FLOAT64)) as system_sell_price_gbp_per_mwh
    FROM `jibber-jabber-knowledge.uk_energy_insights.bmrs_bod`
    WHERE settlementDate BETWEEN '{start_date}' AND '{end_date}'
    AND bid IS NOT NULL AND offer IS NOT NULL
    AND SAFE_CAST(bid AS FLOAT64) IS NOT NULL
    AND SAFE_CAST(offer AS FLOAT64) IS NOT NULL
    GROUP BY 1
    ORDER BY 1
    """
    datasets["system_prices"] = query_bigquery(
        client, system_prices_query, "Updated System Buy/Sell Prices"
    )
    datasets["humr1"] = get_humr1_generation(client, start_date, end_date)
    datasets["niv"] = get_net_imbalance_volume(client, start_date, end_date)

    # Start with fuel mix as the base
    if datasets["fuel_mix"].empty:
        print("❌ No fuel mix data available. Cannot continue.")
        return pd.DataFrame()

    merged_df = datasets["fuel_mix"].copy()

    # Merge other datasets
    for name, df in datasets.items():
        if name == "fuel_mix" or df.empty:
            continue

        print(f"🔗 Merging {name} data...")
        # Set datetime as index for merging
        df_indexed = df.set_index("datetime_utc")
        merged_indexed = merged_df.set_index("datetime_utc")

        # Outer join to preserve all timestamps
        merged_indexed = merged_indexed.join(df_indexed, how="outer")
        merged_df = merged_indexed.reset_index()

    # Sort by datetime and fill NaN values with 0 for numeric columns
    merged_df = merged_df.sort_values("datetime_utc")
    numeric_cols = merged_df.select_dtypes(include=["float64", "int64"]).columns
    merged_df[numeric_cols] = merged_df[numeric_cols].fillna(0)

    print(f"✅ Final merged dataset has {len(merged_df):,} rows")
    return merged_df


# --- Export Functions ---
def create_google_sheet(sheets_service, drive_service, sheet_name, dataframe):
    """Create or update a Google Sheet with the given dataframe."""
    print(f"📊 Creating or updating Google Sheet: '{sheet_name}'...")

    # Check if the sheet already exists
    sheet_id = None
    try:
        print("🔍 Searching for existing spreadsheet...")
        results = (
            drive_service.files()
            .list(
                q=f"name='{sheet_name}' and mimeType='application/vnd.google-apps.spreadsheet'",
                spaces="drive",
            )
            .execute()
        )
        files = results.get("files", [])
        if files:
            sheet_id = files[0]["id"]
            print(f"✅ Found existing spreadsheet: {sheet_name} (ID: {sheet_id})")
    except Exception as e:
        print(f"❌ Error while searching for spreadsheet: {e}")

    # Create a new sheet if it doesn't exist
    if not sheet_id:
        print("📄 Creating a new spreadsheet...")
        spreadsheet = {"properties": {"title": sheet_name}}
        sheet = (
            sheets_service.spreadsheets()
            .create(body=spreadsheet, fields="spreadsheetId")
            .execute()
        )
        sheet_id = sheet.get("spreadsheetId")
        print(f"✅ New spreadsheet created: {sheet_name} (ID: {sheet_id})")

    # Clear existing data in the sheet
    try:
        print("🧹 Clearing existing data in the spreadsheet...")
        sheets_service.spreadsheets().values().clear(
            spreadsheetId=sheet_id, range="Sheet1"
        ).execute()
        print("✅ Existing data cleared.")
    except Exception as e:
        print(f"❌ Error while clearing data: {e}")

    # Write new data to the sheet
    try:
        print("📤 Writing new data to the spreadsheet...")
        dataframe = dataframe.copy()

        # Convert datetime to string
        if "datetime_utc" in dataframe.columns:
            dataframe["datetime_utc"] = dataframe["datetime_utc"].astype(str)

        # Convert Decimal objects to float
        for col in dataframe.columns:
            dataframe[col] = dataframe[col].apply(
                lambda x: (
                    float(x)
                    if isinstance(x, Decimal)
                    else (str(x) if pd.isna(x) is False else "")
                )
            )

        values = [dataframe.columns.tolist()] + dataframe.values.tolist()
        body = {"values": values}
        sheets_service.spreadsheets().values().update(
            spreadsheetId=sheet_id, range="Sheet1", valueInputOption="RAW", body=body
        ).execute()
        print("✅ Data written successfully.")
    except Exception as e:
        print(f"❌ Error while writing data: {e}")

    return sheet_id


def create_summary_document(docs_service, title, summary_stats, sheet_url):
    """Creates a Google Doc with summary analysis"""
    print(f"📝 Creating summary document: '{title}'...")

    # Create document
    doc = docs_service.documents().create(body={"title": title}).execute()

    doc_id = doc.get("documentId")
    doc_url = f"https://docs.google.com/document/d/{doc_id}"

    # Prepare content
    today = datetime.date.today().strftime("%Y-%m-%d")

    content = f"""
Comprehensive UK Energy Generation & Market Report
Generated: {today}

EXECUTIVE SUMMARY
=================

Data Period: {summary_stats.get('period', 'Last 30 days')}
Total Records: {summary_stats.get('total_records', 'N/A'):,}

GENERATION OVERVIEW (Average GW)
================================
• Gas Generation: {summary_stats.get('avg_gas_gw', 0):.2f} GW
• Wind Generation: {summary_stats.get('avg_wind_gw', 0):.2f} GW
• Solar Generation: {summary_stats.get('avg_solar_gw', 0):.2f} GW
• Nuclear Generation: {summary_stats.get('avg_nuclear_gw', 0):.2f} GW
• Total Generation: {summary_stats.get('avg_total_gw', 0):.2f} GW

RENEWABLE ENERGY SHARE
======================
• Wind & Solar Combined: {summary_stats.get('renewable_percentage', 0):.1f}% of total generation
• Low Carbon (Nuclear + Renewables): {summary_stats.get('low_carbon_percentage', 0):.1f}% of total generation

MARKET PRICES (£/MWh)
====================
• Average Market Index Price: £{summary_stats.get('avg_market_price', 0):.2f}/MWh
• Average System Buy Price: £{summary_stats.get('avg_system_buy_price', 0):.2f}/MWh
• Average System Sell Price: £{summary_stats.get('avg_system_sell_price', 0):.2f}/MWh

T_HUMR-1 PERFORMANCE
===================
• Average Generation: {summary_stats.get('avg_humr1_mw', 0):.2f} MW
• Peak Generation: {summary_stats.get('max_humr1_mw', 0):.2f} MW

SYSTEM BALANCING
===============
• Average Net Imbalance: {summary_stats.get('avg_niv_mwh', 0):.2f} MWh

DATA SOURCES
============
This report is based on ELEXON/BMRS data including:
- bmrs_fuelinst: Real-time generation by fuel type
- bmrs_mid: Market Index Prices from MIDPs
- bmrs_bod: System Buy/Sell Prices
- bmrs_pn: Physical Notifications (T_HUMR-1)
- bmrs_imbalngc: Net Imbalance Volume

Detailed data available in spreadsheet: {sheet_url}

Report generated using comprehensive ELEXON/BMRS data analysis.
"""

    # Insert content
    requests = [{"insertText": {"location": {"index": 1}, "text": content}}]

    docs_service.documents().batchUpdate(
        documentId=doc_id, body={"requests": requests}
    ).execute()

    return doc_url


def calculate_summary_stats(df):
    """Calculate summary statistics for the report"""
    if df.empty:
        return {}

    # Calculate renewable percentage (wind only since no solar in this dataset)
    wind_gen = df.get("wind_generation_gw", pd.Series([0])).mean()
    total_gen = df.get("total_domestic_generation_gw", pd.Series([0])).mean()
    renewable_pct = (wind_gen / total_gen * 100) if total_gen > 0 else 0

    # Calculate low carbon percentage (nuclear + renewables + hydro + biomass)
    nuclear_gen = df.get("nuclear_generation_gw", pd.Series([0])).mean()
    hydro_gen = df.get("hydro_generation_gw", pd.Series([0])).mean()
    biomass_gen = df.get("biomass_generation_gw", pd.Series([0])).mean()
    low_carbon_total = wind_gen + nuclear_gen + hydro_gen + biomass_gen
    low_carbon_pct = (low_carbon_total / total_gen * 100) if total_gen > 0 else 0

    return {
        "total_records": len(df),
        "period": "Last 30 days",
        "avg_gas_gw": df.get("gas_generation_gw", pd.Series([0])).mean(),
        "avg_wind_gw": wind_gen,
        "avg_solar_gw": 0,  # No solar data in BMRS fuel types
        "avg_nuclear_gw": nuclear_gen,
        "avg_total_gw": total_gen,
        "renewable_percentage": renewable_pct,
        "low_carbon_percentage": low_carbon_pct,
        "avg_market_price": df.get(
            "market_index_price_gbp_per_mwh", pd.Series([0])
        ).mean(),
        "avg_system_buy_price": df.get(
            "system_buy_price_gbp_per_mwh", pd.Series([0])
        ).mean(),
        "avg_system_sell_price": df.get(
            "system_sell_price_gbp_per_mwh", pd.Series([0])
        ).mean(),
        "avg_humr1_mw": df.get("humr1_generation_mw", pd.Series([0])).mean(),
        "max_humr1_mw": df.get("humr1_generation_mw", pd.Series([0])).max(),
        "avg_niv_mwh": df.get("net_imbalance_volume_mwh", pd.Series([0])).mean(),
    }


# --- Main Execution ---
def initialize_bigquery_client():
    """Initialize and return a BigQuery client."""
    print("🔗 Initializing BigQuery client...")
    try:
        client = bigquery.Client()
        print("✅ BigQuery client initialized.")
        return client
    except Exception as e:
        print(f"❌ Error initializing BigQuery client: {e}")
        return None


def main():
    """Main function to run the comprehensive energy report."""
    print("🚀 Starting Comprehensive UK Energy Generation & Market Report V3...")
    print("=" * 70)

    # Authenticate
    creds = authenticate_google_apis()
    sheets_service = build("sheets", "v4", credentials=creds)
    drive_service = build("drive", "v3", credentials=creds)
    docs_service = build("docs", "v1", credentials=creds)
    bq_client = bigquery.Client(project=PROJECT_ID, credentials=creds)

    # Initialize the client
    client = initialize_bigquery_client()
    if not client:
        print("❌ Cannot proceed without a BigQuery client.")
        exit(1)

    # --- Verify Data Availability ---
    # Check the actual data coverage in bmrs_fuelinst for the past 2 years
    query_data_coverage = """
    SELECT MIN(settlementDate) as min_date, MAX(settlementDate) as max_date, COUNT(*) as total_records
    FROM `jibber-jabber-knowledge.uk_energy_insights.bmrs_fuelinst`
    WHERE settlementDate BETWEEN DATE_SUB(CURRENT_DATE(), INTERVAL 2 YEAR) AND CURRENT_DATE()
    """
    data_coverage = query_bigquery(
        client, query_data_coverage, "Data Coverage in bmrs_fuelinst"
    )
    if not data_coverage.empty:
        print(
            f"📊 Data coverage: {data_coverage.iloc[0]['min_date']} to {data_coverage.iloc[0]['max_date']}, Total Records: {data_coverage.iloc[0]['total_records']}"
        )
    else:
        print("❌ No data available in bmrs_fuelinst for the past 2 years.")

    # Get comprehensive data
    combined_df = get_comprehensive_data(bq_client)

    if combined_df.empty:
        print("\n❌ No data was fetched from BigQuery. Exiting.")
        return

    # Generate timestamp
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

    # Export to CSV
    csv_filename = f"Comprehensive_Energy_Report_V3_{timestamp}.csv"
    csv_filepath = os.path.join(OUTPUT_DIR, csv_filename)
    combined_df.to_csv(csv_filepath, index=False)
    print(f"\n💾 Data saved to CSV: {csv_filename}")

    # Create Google Sheet
    sheet_title = f"UK Energy Report V3 - {datetime.date.today()}"
    sheet_url = create_google_sheet(
        sheets_service, drive_service, sheet_title, combined_df
    )

    # Calculate summary statistics
    summary_stats = calculate_summary_stats(combined_df)

    # Create summary document
    doc_title = f"UK Energy Analysis Summary - {datetime.date.today()}"
    doc_url = create_summary_document(docs_service, doc_title, summary_stats, sheet_url)

    # Final summary
    print("\n" + "=" * 70)
    print("📊 COMPREHENSIVE ENERGY REPORT COMPLETE")
    print("=" * 70)
    print(f"📁 CSV Export:           {csv_filename}")
    print(f"📊 Google Sheet:         {sheet_url}")
    print(f"📝 Summary Document:     {doc_url}")
    print(f"📈 Total Records:        {len(combined_df):,}")
    print(f"📅 Data Period:          Last 30 days")
    print("\n🎯 Report includes:")
    print("   • Complete fuel mix breakdown (all generation types in GW)")
    print("   • Market Index Prices from MIDPs (£/MWh)")
    print("   • System Buy/Sell Prices with Net Imbalance Volume")
    print("   • T_HUMR-1 generation performance")
    print("   • Renewable energy analysis and statistics")
    print("\n✅ Process complete!")


if __name__ == "__main__":
    main()


def write_to_google_sheet(sheets_service, sheet_id, dataframe):
    """Write data to a specific Google Sheet by ID."""
    print(f"📊 Writing data to Google Sheet ID: {sheet_id}...")

    # Clear existing data in the sheet
    try:
        print("🧹 Clearing existing data in the spreadsheet...")
        sheets_service.spreadsheets().values().clear(
            spreadsheetId=sheet_id, range="Sheet1"
        ).execute()
        print("✅ Existing data cleared.")
    except Exception as e:
        print(f"❌ Error while clearing data: {e}")

    # Write new data to the sheet
    try:
        print("📤 Writing new data to the spreadsheet...")
        dataframe = dataframe.copy()

        # Convert datetime to string
        if "datetime_utc" in dataframe.columns:
            dataframe["datetime_utc"] = dataframe["datetime_utc"].astype(str)

        # Convert Decimal objects to float
        for col in dataframe.columns:
            dataframe[col] = dataframe[col].apply(
                lambda x: (
                    float(x)
                    if isinstance(x, Decimal)
                    else (str(x) if pd.isna(x) is False else "")
                )
            )

        values = [dataframe.columns.tolist()] + dataframe.values.tolist()
        body = {"values": values}
        sheets_service.spreadsheets().values().update(
            spreadsheetId=sheet_id, range="Sheet1", valueInputOption="RAW", body=body
        ).execute()
        print("✅ Data written successfully.")
    except Exception as e:
        print(f"❌ Error while writing data: {e}")


# --- Main Execution ---
if __name__ == "__main__":
    client = initialize_bigquery_client()
    if client:
        start_date = datetime.date(2023, 9, 1)  # 24 months ago
        end_date = datetime.date.today()
        merged_data = get_elexon_bmrs_data(client, start_date, end_date)
        if not merged_data.empty:
            creds = authenticate_google_apis()
            sheets_service = build("sheets", "v4", credentials=creds)
            sheet_id = "1XSgf7oAkiv8wQoThDNfVM6b5X_UtFwzPaTVmx1DGncU"  # Provided Google Sheet ID
            write_to_google_sheet(sheets_service, sheet_id, merged_data)
            print(
                f"📊 Google Sheet updated: https://docs.google.com/spreadsheets/d/{sheet_id}"
            )

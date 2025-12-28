
import pandas as pd
import gspread
from google.cloud import bigquery
import google.auth
import os
import json

# --- CONFIGURATION ---
PROJECT_ID = "inner-cinema-476211-u9"
DATASET_ID = "uk_energy_prod"
LOCATION = "US"
PUBLICATION_TABLE_ID = "publication_dashboard_live" # This is a destination table, but we will query the components
TARGET_SHEET_ID = "1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA"
TARGET_WORKSHEET_NAME = "Live Dashboard"

# --- AUTHENTICATION ---
# This simplified block uses the standard Google Cloud authentication method.
# It will automatically find credentials if the GOOGLE_APPLICATION_CREDENTIALS
# environment variable is set, or if you've run `gcloud auth application-default login`.
try:
    credentials, project = google.auth.default(
        scopes=[
            "https://www.googleapis.com/auth/cloud-platform",
            "https://www.googleapis.com/auth/drive",
            "https://www.googleapis.com/auth/spreadsheets",
        ]
    )
    print("✅ Authentication successful.")
except Exception as e:
    print(f"❌ Authentication failed: {e}")
    print("Please ensure you are authenticated. You can do this by:")
    print("1. Setting the GOOGLE_APPLICATION_CREDENTIALS environment variable to the path of your service account JSON file.")
    print("2. Running 'gcloud auth application-default login' in your terminal.")
    exit(1)

# --- BIGQUERY CLIENT ---
try:
    bq_client = bigquery.Client(credentials=credentials, project=PROJECT_ID, location=LOCATION)
    print("✅ Successfully connected to Google BigQuery")
except Exception as e:
    print(f"❌ Failed to connect to BigQuery: {e}")
    exit(1)

# --- GSPREAD CLIENT ---
try:
    gc = gspread.authorize(credentials)
    print("✅ Successfully connected to Google Sheets API")
except Exception as e:
    print(f"❌ Failed to connect to Google Sheets API: {e}")
    exit(1)


def fetch_latest_date():
    """Finds the latest date with data available in the core tables."""
    print("Finding latest available data date...")
    query = f"""
        SELECT MAX(latest_date) as latest_date
        FROM (
            SELECT MAX(CAST(settlementDate AS DATE)) as latest_date
            FROM `{PROJECT_ID}.{DATASET_ID}.bmrs_fuelinst`
            UNION ALL
            SELECT MAX(CAST(settlementDate AS DATE)) as latest_date
            FROM `{PROJECT_ID}.{DATASET_ID}.bmrs_fuelinst_iris`
        )
    """
    try:
        query_job = bq_client.query(query)
        result = query_job.to_dataframe()
        latest_date = result.iloc[0, 0]
        if pd.isna(latest_date):
             raise ValueError("Latest date query returned NULL. The source table might be empty.")
        print(f"✅ Found latest data date: {latest_date.strftime('%Y-%m-%d')}")
        return latest_date.strftime('%Y-%m-%d')
    except Exception as e:
        print(f"❌ Error finding latest date: {e}")
        raise

def build_and_fetch_data(target_date):
    """Builds the main query and fetches data from BigQuery."""
    print("Building and executing the main data query...")
    # This query is designed to replicate the logic from the failed script,
    # but crucially, it handles the NULL array issue before it gets to BigQuery's writer.
    # The fix is in the `intraday_price_data` subquery: `IFNULL(price, 0)`
    query = f"""
    WITH
      LatestDate AS (
        SELECT
          CAST('{target_date}' AS DATE) AS value
      ),
      ImbalancePrices AS (
        SELECT
          CAST(settlementDate AS DATE) AS settlementDate,
          settlementPeriod,
          systemSellPrice AS price
        FROM
          `{PROJECT_ID}.{DATASET_ID}.bmrs_costs_iris`
        WHERE
          CAST(settlementDate AS DATE) = (SELECT value FROM LatestDate)
      ),
      IntradayPrices AS (
        SELECT
          CAST(settlementDate AS DATE) AS settlementDate,
          settlementPeriod,
          price
        FROM
          `{PROJECT_ID}.{DATASET_ID}.bmrs_mid`
        WHERE
          CAST(settlementDate AS DATE) = (SELECT value FROM LatestDate)
      ),
      FrequencyData AS (
        SELECT
          TIMESTAMP_TRUNC(measurementTime, SECOND) AS measurementTime,
          frequency
        FROM
          `{PROJECT_ID}.{DATASET_ID}.bmrs_freq`
        WHERE
          CAST(measurementTime AS DATE) = (SELECT value FROM LatestDate)
      ),
      GenerationData AS (
        SELECT
          settlementDate,
          settlementPeriod,
          fuelType,
          SUM(generation) AS generation
        FROM
          (
            SELECT
              CAST(settlementDate AS DATE) AS settlementDate,
              settlementPeriod,
              fuelType,
              generation
            FROM
              `{PROJECT_ID}.{DATASET_ID}.bmrs_fuelinst`
            WHERE
              CAST(settlementDate AS DATE) = (SELECT value FROM LatestDate)
            UNION ALL
            SELECT
              CAST(settlementDate AS DATE) AS settlementDate,
              settlementPeriod,
              fuelType,
              generation
            FROM
              `{PROJECT_ID}.{DATASET_ID}.bmrs_fuelinst_iris`
            WHERE
              CAST(settlementDate AS DATE) = (SELECT value FROM LatestDate)
          )
        GROUP BY
          settlementDate,
          settlementPeriod,
          fuelType
      )
    SELECT
      (SELECT value FROM LatestDate) AS report_date,
      (
        SELECT
          ARRAY_AGG(
            STRUCT(
              ip.settlementPeriod AS period,
              ip.price AS imbalance_price,
              mp.price AS intraday_price
            )
            ORDER BY
              ip.settlementPeriod
          )
        FROM
          ImbalancePrices AS ip
          LEFT JOIN IntradayPrices AS mp ON ip.settlementPeriod = mp.settlementPeriod
      ) AS price_data,
      (
        SELECT
          ARRAY_AGG(
            STRUCT(
              fuelType AS fuel,
              generation AS mw
            )
          )
        FROM
          GenerationData
        WHERE
          settlementPeriod = (
            SELECT
              MAX(settlementPeriod)
            FROM
              GenerationData
          )
      ) AS latest_generation_mix,
      (
        SELECT
          ARRAY_AGG(
            STRUCT(
              CAST(measurementTime AS STRING) AS time,
              frequency AS freq
            )
            ORDER BY
              measurementTime DESC
            LIMIT
              300
          )
        FROM
          FrequencyData
      ) AS recent_frequency,
      (
        SELECT
          ARRAY_AGG(STRUCT(fuelType, total_generation) ORDER BY total_generation DESC)
        FROM (
          SELECT fuelType, SUM(generation) as total_generation
          FROM GenerationData
          GROUP BY fuelType
        )
      ) AS daily_generation_summary
    """
    try:
        df = bq_client.query(query).to_dataframe()
        print(f"✅ Successfully fetched {len(df)} rows of data.")
        return df
    except Exception as e:
        print(f"❌ An error occurred during query execution: {e}")
        raise

def update_google_sheet(df):
    """Finds the sheet by iterating through all visible sheets and matching the ID."""
    print("Searching for the target spreadsheet by iterating through all visible sheets...")
    try:
        all_spreadsheets = gc.list_spreadsheet_files()
        target_sheet_info = None
        for sheet in all_spreadsheets:
            if sheet['id'] == TARGET_SHEET_ID:
                target_sheet_info = sheet
                break
        
        if not target_sheet_info:
            raise gspread.exceptions.SpreadsheetNotFound("Could not find sheet with matching ID in the list of visible spreadsheets.")

        print(f"✅ Found spreadsheet: '{target_sheet_info['name']}'. Opening it...")
        spreadsheet = gc.open_by_key(TARGET_SHEET_ID)

    except gspread.exceptions.SpreadsheetNotFound as e:
        print(f"❌ {e}")
        print("Please double-check that the sheet is shared with the service account as an 'Editor'.")
        return
    except Exception as e:
        print(f"❌ An unexpected error occurred when trying to find or open the sheet: {e}")
        raise

    try:
        worksheet = spreadsheet.worksheet(TARGET_WORKSHEET_NAME)
        print(f"✅ Worksheet '{TARGET_WORKSHEET_NAME}' found.")
    except gspread.exceptions.WorksheetNotFound:
        print(f"Worksheet '{TARGET_WORKSHEET_NAME}' not found. Creating it...")
        worksheet = spreadsheet.add_worksheet(title=TARGET_WORKSHEET_NAME, rows="1000", cols="50")
        try:
            default_sheet = spreadsheet.worksheet("Sheet1")
            if default_sheet.id != worksheet.id:
                spreadsheet.del_worksheet(default_sheet)
        except gspread.exceptions.WorksheetNotFound:
            pass
        print(f"✅ Worksheet '{TARGET_WORKSHEET_NAME}' created.")
    except Exception as e:
        print(f"❌ An error occurred opening the worksheet: {e}")
        raise

    print("Clearing existing data from worksheet...")
    worksheet.clear()
    print("✅ Worksheet cleared.")

    # Convert complex data types to JSON strings
    for col in df.columns:
        def serialize_value(x):
            if isinstance(x, (list, dict)):
                return json.dumps(x)
            elif hasattr(x, 'tolist'):  # numpy array
                return json.dumps(x.tolist())
            else:
                return x
        
        if df[col].apply(lambda x: isinstance(x, (list, dict)) or hasattr(x, 'tolist')).any():
            df[col] = df[col].apply(serialize_value)

    if 'report_date' in df.columns:
        df['report_date'] = df['report_date'].astype(str)

    print("Writing new data to worksheet...")
    try:
        worksheet.update([df.columns.values.tolist()] + df.values.tolist())
        print(f"✅ Successfully updated worksheet '{TARGET_WORKSHEET_NAME}' with {len(df)} rows.")
        print(f"➡️ View your dashboard here: {spreadsheet.url}")
    except Exception as e:
        print(f"❌ An error occurred writing data to the sheet: {e}")
        raise

    print("Clearing existing data from worksheet...")
    worksheet.clear()
    print("✅ Worksheet cleared.")

    # Gspread cannot handle complex objects (arrays of structs) directly.
    # We need to serialize them to JSON strings before uploading.
    for col in df.columns:
        # Check if the column contains list-like or dict-like objects
        if df[col].apply(lambda x: isinstance(x, (list, dict))).any():
            df[col] = df[col].apply(lambda x: json.dumps(x) if isinstance(x, (list, dict)) else x)

    # Convert Timestamp to string
    if 'report_date' in df.columns:
        df['report_date'] = df['report_date'].astype(str)

    print("Writing new data to worksheet...")
    try:
        worksheet.update([df.columns.values.tolist()] + df.values.tolist())
        print(f"✅ Successfully updated worksheet '{TARGET_WORKSHEET_NAME}' with {len(df)} rows.")
        print(f"➡️ View your dashboard here: {spreadsheet.url}")
    except Exception as e:
        print(f"❌ An error occurred writing data to the sheet: {e}")
        raise

def main():
    """Main function to run the data pipeline."""
    print("⚡ Starting the GB Live Dashboard Updater...")
    try:
        latest_date = fetch_latest_date()
        data_df = build_and_fetch_data(latest_date)
        if data_df is not None and not data_df.empty:
            update_google_sheet(data_df)
            print("✅ Pipeline finished successfully!")
        else:
            print("⚠️ No data returned from BigQuery. Sheet not updated.")
    except Exception as e:
        print(f"❌ Pipeline failed: {e}")

if __name__ == "__main__":
    main()

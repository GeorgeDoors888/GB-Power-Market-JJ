#!/usr/bin/env python3
"""
Google Sheets DUoS Data Direct Uploader
Uses Sheets API directly to upload data without going through Drive API
"""

import os
from datetime import datetime

import pandas as pd
from google.oauth2 import service_account
from googleapiclient.discovery import build

# Constants
SERVICE_ACCOUNT_FILE = "jibber_jaber_key.json"
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.file",  # Only for files created by the app
]
INPUT_FILE = "duos_outputs2/DNO_DUoS_All_Data_Consolidated_Complete.xlsx"
TIMESTAMP = datetime.now().strftime("%Y%m%d_%H%M%S")


def get_sheets_service():
    """Get authenticated Sheets service"""
    try:
        credentials = service_account.Credentials.from_service_account_file(
            SERVICE_ACCOUNT_FILE, scopes=SCOPES
        )
        service = build("sheets", "v4", credentials=credentials)
        print("✅ Successfully authenticated with Google Sheets API")
        return service
    except Exception as e:
        print(f"❌ Authentication failed: {e}")
        return None


def sanitize_data(df):
    """Clean DataFrame to ensure it can be safely uploaded to Sheets"""
    # Replace NaN with empty string
    df = df.fillna("")

    # Convert all values to strings and clean problematic characters
    for col in df.columns:
        df[col] = (
            df[col].astype(str).apply(lambda x: x.replace("\n", " ").replace("\t", " "))
        )

    return df


def get_safe_sheet_name(service, base_name, spreadsheet_id):
    """Get a sheet name that doesn't exist yet by appending a number if needed"""
    try:
        sheets = (
            service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()["sheets"]
        )
        existing_names = {sheet["properties"]["title"] for sheet in sheets}

        if base_name not in existing_names:
            return base_name

        counter = 1
        while f"{base_name} ({counter})" in existing_names:
            counter += 1
        return f"{base_name} ({counter})"
    except Exception:
        return base_name


def clear_existing_sheet(service, spreadsheet_id, sheet_name):
    """Clear all content from an existing sheet"""
    try:
        service.spreadsheets().values().clear(
            spreadsheetId=spreadsheet_id,
            range=f"{sheet_name}!A1:ZZ",
        ).execute()
    except Exception:
        pass  # Ignore errors if sheet doesn't exist or is already empty


def update_sheet_with_data(service, data_df, sheet_name):
    """Update existing sheet with data"""
    try:
        # Use the existing spreadsheet ID
        spreadsheet_id = "1BuIYAOjMqoyhQE_f6p8zRwH5poQsuTaHDAYIjskZsTo"

        # Sanitize data before upload
        data_df = sanitize_data(data_df)

        # Convert DataFrame to list of lists for the API
        values = [data_df.columns.tolist()] + data_df.values.tolist()

        # Get spreadsheet metadata
        spreadsheet = service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
        existing_sheets = {
            sheet["properties"]["title"]: sheet["properties"]["sheetId"]
            for sheet in spreadsheet["sheets"]
        }

        print(f"Found {len(existing_sheets)} existing sheets")

        # If sheet exists, clear it first
        if sheet_name in existing_sheets:
            print(f"Clearing existing sheet: {sheet_name}")
            service.spreadsheets().values().clear(
                spreadsheetId=spreadsheet_id,
                range=f"{sheet_name}!A1:ZZ",
            ).execute()
        else:
            print(f"Creating new sheet: {sheet_name}")
            body = {"requests": [{"addSheet": {"properties": {"title": sheet_name}}}]}
            service.spreadsheets().batchUpdate(
                spreadsheetId=spreadsheet_id, body=body
            ).execute()

        # Split data into chunks of 900 rows (leaving room for headers)
        MAX_ROWS_PER_SHEET = 900
        chunks = [
            values[i : i + MAX_ROWS_PER_SHEET]
            for i in range(0, len(values), MAX_ROWS_PER_SHEET)
        ]

        # If we need more than one sheet
        if len(chunks) > 1:
            print(f"Data requires {len(chunks)} sheets")

        for chunk_index, chunk in enumerate(chunks):
            # For additional chunks, create new sheets with numbered suffixes
            current_sheet_name = (
                sheet_name if chunk_index == 0 else f"{sheet_name} ({chunk_index + 1})"
            )

            if chunk_index > 0:
                if current_sheet_name in existing_sheets:
                    print(f"Clearing existing sheet: {current_sheet_name}")
                    service.spreadsheets().values().clear(
                        spreadsheetId=spreadsheet_id,
                        range=f"{current_sheet_name}!A1:ZZ",
                    ).execute()
                else:
                    print(f"Creating additional sheet: {current_sheet_name}")
                    body = {
                        "requests": [
                            {"addSheet": {"properties": {"title": current_sheet_name}}}
                        ]
                    }
                    service.spreadsheets().batchUpdate(
                        spreadsheetId=spreadsheet_id, body=body
                    ).execute()

            # Split into smaller batches and add delays to avoid quota limits
            BATCH_SIZE = 100  # Even smaller batch size
            DELAY_BETWEEN_BATCHES = 1  # 1 second delay between batches

        from time import sleep

        # Write data in smaller batches with delays
        for i in range(0, len(values), BATCH_SIZE):
            batch = values[i : i + BATCH_SIZE]
            range_name = f"{sheet_name}!A{i+1}"

            # Retry logic for quota exceeded errors
            max_retries = 3
            retry_delay = 5  # seconds

            for attempt in range(max_retries):
                try:
                    service.spreadsheets().values().update(
                        spreadsheetId=spreadsheet_id,
                        range=range_name,
                        valueInputOption="RAW",
                        body={"values": batch},
                    ).execute()
                    print(f"📝 Uploaded rows {i+1} to {i+len(batch)}")
                    sleep(DELAY_BETWEEN_BATCHES)  # Add delay between batches
                    break
                except Exception as batch_error:
                    if attempt < max_retries - 1:
                        if "429" in str(batch_error):  # Quota exceeded
                            print(
                                f"⏳ Rate limit hit, waiting {retry_delay}s before retry..."
                            )
                            sleep(retry_delay)
                            retry_delay *= 2  # Exponential backoff
                            continue
                    raise batch_error

        print(f"✨ Sheet URL: https://docs.google.com/spreadsheets/d/{spreadsheet_id}")
        return spreadsheet_id

    except Exception as e:
        print(f"❌ Error creating sheet: {e}")
        return None


def main():
    """Main execution"""
    print("🚀 Starting DUoS data upload")

    if not os.path.exists(INPUT_FILE):
        print(f"❌ Input file not found: {INPUT_FILE}")
        return

    service = get_sheets_service()
    if not service:
        return

    # Read Excel sheets
    xl = pd.ExcelFile(INPUT_FILE)
    sheet_names = xl.sheet_names

    print(f"📑 Found {len(sheet_names)} sheets to process")

    for idx, sheet_name in enumerate(sheet_names, 1):
        print(f"\n⏳ Processing sheet {idx}/{len(sheet_names)}: {sheet_name}")

        # Read sheet data
        df = pd.read_excel(INPUT_FILE, sheet_name=sheet_name)

        # Create sheet name - use original sheet name to avoid confusion
        update_sheet_with_data(service, df, sheet_name)

    print("\n✅ Upload Complete!")
    print(
        f"\nData uploaded to: https://docs.google.com/spreadsheets/d/1BuIYAOjMqoyhQE_f6p8zRwH5poQsuTaHDAYIjskZsTo"
    )


if __name__ == "__main__":
    main()

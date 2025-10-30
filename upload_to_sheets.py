import gspread
import pandas as pd
from gspread.exceptions import SpreadsheetNotFound
from gspread_dataframe import set_with_dataframe

# --- SETUP INSTRUCTIONS ---
# 1. Enable APIs:
#    - Go to the Google Cloud Console: https://console.cloud.google.com/
#    - Create a new project or select an existing one.
#    - In the navigation menu, go to "APIs & Services" > "Library".
#    - Search for and enable the "Google Drive API".
#    - Search for and enable the "Google Sheets API".

# 2. Create a Service Account:
#    - In "APIs & Services", go to "Credentials".
#    - Click "Create Credentials" > "Service account".
#    - Give it a name (e.g., "sheets-uploader") and click "Create and Continue".
#    - Grant it the "Editor" role and click "Continue", then "Done".
#    - On the Credentials page, find your new service account and click on it.
#    - Go to the "Keys" tab, click "Add Key" > "Create new key".
#    - Choose "JSON" and click "Create". A JSON file will be downloaded.

# 3. Prepare Files:
#    - Rename the downloaded JSON file to "service_account.json".
#    - Place "service_account.json" in the same directory as this script.
#    - Make sure the "T_HUMR-1_bidding_strategy.csv" file is also in this directory.

# 4. Share Your Google Sheet:
#    - Open the "service_account.json" file and find the "client_email" address.
#    - Create a new Google Sheet.
#    - Click the "Share" button in the top right.
#    - Paste the service account's email address and give it "Editor" permissions.
# ---


def upload_and_chart():
    """
    Uploads BMU bidding data to a Google Sheet and creates charts.
    """
    try:
        # --- CONFIGURATION ---
        # The ID of the Google Sheet you provided.
        GOOGLE_SHEET_ID = "1IuhKLHA8poRsP2M7WMYFlCKQT5TDB2lp4vfcumClGu8"
        # The name of the CSV file containing the data.
        CSV_FILE_PATH = "T_HUMR-1_bidding_strategy.csv"
        # The path to your service account credentials file.
        SERVICE_ACCOUNT_FILE = "jibber_jaber_key.json"
        # ---

        print("Connecting to Google Sheets...")
        gc = gspread.service_account(filename=SERVICE_ACCOUNT_FILE)

        print(f"Opening Google Sheet by ID...")
        try:
            spreadsheet = gc.open_by_key(GOOGLE_SHEET_ID)
        except gspread.exceptions.APIError as e:
            if e.response.status_code == 403:
                print(
                    "Error: Permission denied. Please make sure you have shared the Google Sheet with the service account email:"
                )
                print("jibber-jabber-knowledge@appspot.gserviceaccount.com")
                print("and given it 'Editor' permissions.")
            else:
                print(f"An API error occurred: {e}")
            return
        except SpreadsheetNotFound:
            print(f"Error: Spreadsheet with ID '{GOOGLE_SHEET_ID}' not found.")
            return
        except Exception as e:
            print(f"An unexpected error occurred while opening the sheet: {e}")
            return

        print("Reading data from CSV file...")
        df = pd.read_csv(CSV_FILE_PATH)

        # Get or create the worksheet
        worksheet_title = "BMU_Bidding_Data"
        try:
            worksheet = spreadsheet.worksheet(worksheet_title)
            worksheet.clear()
            print(f"Cleared existing worksheet: '{worksheet_title}'")
        except gspread.WorksheetNotFound:
            worksheet = spreadsheet.add_worksheet(
                title=worksheet_title, rows="100", cols="20"
            )
            print(f"Created new worksheet: '{worksheet_title}'")

        print("Uploading data to the worksheet...")
        set_with_dataframe(worksheet, df)
        print("Data upload complete.")

        # --- Chart Creation ---
        print("Creating charts...")

        # Chart 1: Average Prices Over Time
        price_chart = worksheet.new_chart()
        price_chart.title = "Average Bid vs. Offer Prices (£/MWh)"
        price_chart.set_x_axis(label="Month")
        price_chart.set_y_axis(label="Price (£/MWh)")
        price_chart.add_range(
            "A1:A" + str(len(df) + 1),
            "B1:B" + str(len(df) + 1),
            "D1:D" + str(len(df) + 1),
        )
        price_chart.chart_type = "LINE"
        price_chart.position = ("G2", None, None, None)

        # Chart 2: Total Volumes Over Time (even if zero, for future use)
        volume_chart = worksheet.new_chart()
        volume_chart.title = "Total Bid vs. Offer Volume (MW)"
        volume_chart.set_x_axis(label="Month")
        volume_chart.set_y_axis(label="Volume (MW)")
        volume_chart.add_range(
            "A1:A" + str(len(df) + 1),
            "C1:C" + str(len(df) + 1),
            "E1:E" + str(len(df) + 1),
        )
        volume_chart.chart_type = "COLUMN"
        volume_chart.position = ("G20", None, None, None)

        worksheet.insert_chart(price_chart)
        worksheet.insert_chart(volume_chart)
        print("Charts created successfully.")
        print("\n--- Process Complete ---")
        print(f"Check your Google Sheet: '{GOOGLE_SHEET_NAME}'")

    except FileNotFoundError as e:
        print(f"\n--- ERROR ---")
        if "service_account.json" in str(e):
            print(
                "Could not find 'service_account.json'. Please follow the setup instructions."
            )
        else:
            print(f"File not found: {e}")
    except Exception as e:
        print(f"\n--- An unexpected error occurred ---")
        print(e)
        print(
            "Please ensure your setup is correct (API enabled, sheet shared, file names match)."
        )


if __name__ == "__main__":
    # Before running, you need to install the required libraries:
    # pip install gspread pandas gspread-dataframe oauth2client
    upload_and_chart()

# BtM BESS + CHP Revenue Model - Setup Instructions

This guide explains how to set up and run the Python script `sync_btm_bess_to_sheets.py` on your local Dell machine to sync BigQuery data to your Google Sheet.

## 1. Prerequisites

Ensure you have Python 3.10+ installed on your machine.

### Install Required Libraries
Open your terminal (PowerShell or Command Prompt) and run:

```bash
pip install pandas google-cloud-bigquery google-auth google-auth-oauthlib google-auth-httplib2 gspread db-dtypes
```

## 2. Service Account Setup

1.  Locate your Google Cloud Service Account JSON key file (e.g., `inner-cinema-credentials.json`).
2.  Place it in a secure folder on your machine, for example: `C:\keys\`.
3.  **Important:** Update the `SERVICE_ACCOUNT_FILE` path in `sync_btm_bess_to_sheets.py` to match the actual location of your key file.

```python
# In sync_btm_bess_to_sheets.py
SERVICE_ACCOUNT_FILE = r"C:\keys\inner-cinema-credentials.json" 
```

## 3. Spreadsheet Configuration

The script is configured to update the following spreadsheet:
*   **Spreadsheet ID:** `1MSl8fJ0to6Y08enXA2oysd8wvNUVm3AtfJ1bVqRH8_I`
*   **Target Sheets:**
    *   `GB Live`: Updates KPIs (Total Discharge, Avg SoC, Margins).
    *   `BESS`: Updates detailed settlement period data.

**Note:** If the `BESS` sheet does not exist, the script will automatically create it for you.

## 4. Running the Script

Run the script from your terminal:

```bash
python sync_btm_bess_to_sheets.py
```

## 5. What the Script Does

1.  **Connects to BigQuery:** Authenticates using your service account and queries the `v_btm_bess_inputs` view.
2.  **Fetches Data:** Retrieves data for the configured date range (default: Today).
3.  **Updates "BESS" Sheet:**
    *   Clears existing content.
    *   Writes headers and new data rows.
    *   This effectively "designs" the sheet by populating it with the correct structure.
4.  **Updates "GB Live" Sheet:**
    *   Calculates KPIs (Total Discharge, Avg SoC, PPA Margin, CM+Avail).
    *   Updates specific cells (`B4`, `B5`, `B6`, `B7`, `A2`).

## 6. Troubleshooting

*   **"Service account file not found":** Double-check the path in `SERVICE_ACCOUNT_FILE`.
*   **"WorksheetNotFound":** The script tries to create the `BESS` sheet if missing. Ensure the service account has "Editor" access to the Google Sheet.
*   **"403 Forbidden":** Ensure the service account email (inside the JSON file) is shared with the Google Sheet as an Editor.

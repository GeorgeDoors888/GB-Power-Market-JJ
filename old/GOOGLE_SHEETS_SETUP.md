# Google Sheets API Authentication Setup

This document explains how to set up Google Sheets API authentication for the 15-minute update system.

## Accessing the Google Sheet

The system uses the following Google Sheet for tracking updates:
- **Spreadsheet ID**: `1K4mIoPBuqNTbQmrxkYsp0UJF1e2r1jAAdtSYxBEkZsw`
- **People with access**:
  - George Major (george@upowerenergy.uk)
  - Service account: jibber-jabber-knowledge@appspot.gserviceaccount.com
  - Anyone on the Internet with the link can edit

## Authentication Setup Options

There are three ways to set up authentication:

### Option 1: Environment Variables

1. Copy the `google_sheets.env` file to `.env` or update its values
2. Set the following environment variables:
   ```
   GOOGLE_PRIVATE_KEY_ID="your-private-key-id"
   GOOGLE_PRIVATE_KEY="your-private-key"
   GOOGLE_CLIENT_ID="your-client-id"
   ```

### Option 2: Service Account JSON File

1. Copy the `service_account_template.json` to `service_account.json`
2. Fill in the required fields:
   ```json
   {
     "private_key_id": "YOUR_PRIVATE_KEY_ID",
     "private_key": "YOUR_PRIVATE_KEY",
     "client_id": "YOUR_CLIENT_ID"
   }
   ```

### Option 3: Google Application Default Credentials

If you have Google Cloud SDK installed and are authenticated, the system will try to use your Application Default Credentials as a fallback.

## Testing Authentication

To test your authentication setup, run:

```bash
python test_google_sheets_auth.py
```

This will attempt to connect to the Google Sheet and verify read/write access.

## Running the 15-Minute Update System

Once authentication is set up, you can run the update system:

```bash
# Normal run
python update_all_data_15min.py

# Dry run (no actual updates)
python update_all_data_15min.py --dry-run
```

For development and testing, you can use the modified dry-run version that handles Google Sheets authentication errors gracefully:

```bash
python update_all_data_15min_dryrun.py --dry-run
```

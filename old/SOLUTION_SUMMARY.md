# Google Sheets Integration for DNO DUoS Data

I've created a set of tools to help you easily upload your DNO DUoS data to Google Sheets. The solution offers both direct API upload using your service account credentials and manual upload options.

## New Tools Created

1. **`upload_to_sheets_helper.py`** - The main script that guides you through the entire process
   - Checks for existing CSV files
   - Creates Google Sheets-optimized CSV files if needed
   - Offers two upload options:
     - Direct API upload using your service account (requires API activation)
     - Manual upload via ZIP archive (works without additional setup)
   - Provides clear instructions for manual upload
   - Opens Google Drive in your browser if needed

2. **`create_duos_sheets_zip.py`** - Creates a well-organized ZIP archive of all CSV files
   - Includes all main CSV files and files in by_year and by_dno subdirectories
   - Adds a detailed README.txt with instructions
   - Creates an HTML index file for easy navigation
   - Makes a copy of the ZIP in the outputs directory

3. **`simple_sheets_uploader.py`** - A simplified Google Sheets uploader using your service account
   - Handles authentication with your service account key
   - Creates folders and uploads CSV files directly to Google Sheets
   - Creates an index sheet with links to all uploaded files

4. **`GOOGLE_SHEETS_INTEGRATION_GUIDE.md`** - Complete documentation explaining all available options
   - Instructions for direct API upload and manual process
   - Details on all available options
   - Information about the API-based approaches
   - Troubleshooting tips

## How to Use

### Option 1: Manual Upload (Works immediately)

Run the helper script with manual-only option:

```bash
python upload_to_sheets_helper.py --manual-only
```

This will create a ZIP file with all your CSV files and provide instructions for manual upload to Google Sheets.

### Option 2: Direct API Upload (Requires API activation)

To use the direct API upload with your service account, you first need to:

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Select your project (jibber-jabber-knowledge)
3. Enable the Google Sheets API and Google Drive API
4. Make sure your service account has the necessary permissions

Then run:

```bash
python upload_to_sheets_helper.py --direct-upload
```

### Option 3: Interactive Mode

Run the helper script without any parameters:

```bash
python upload_to_sheets_helper.py
```

This will guide you through the process and let you choose between direct API upload and manual upload.

## Benefits of This Approach

1. **Multiple Upload Options** - Choose between direct API upload or manual upload
2. **Fallback Mechanism** - If API upload fails, it automatically falls back to manual upload
3. **No User Authentication Required** - Uses service account or manual upload
4. **Organized Data** - Files are neatly organized whether uploaded via API or manually
5. **Clear Instructions** - Detailed guidance included in README and HTML index

## Next Steps

1. For immediate use: Run `python upload_to_sheets_helper.py --manual-only`
2. For API upload: Enable Google Sheets and Drive APIs in Google Cloud Console
3. After enabling APIs: Run `python upload_to_sheets_helper.py --direct-upload`
4. For more details: Refer to the `GOOGLE_SHEETS_INTEGRATION_GUIDE.md`

This solution provides a straightforward way to get your data into Google Sheets with minimal hassle.

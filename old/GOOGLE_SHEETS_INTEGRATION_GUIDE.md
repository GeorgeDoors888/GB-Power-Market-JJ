# DNO DUoS Data Google Sheets Integration

This guide explains how to upload DNO Distribution Use of System (DUoS) charging data to Google Sheets. With your service account key (`jibber_jaber_key.json`), we can now offer both direct API upload and manual upload options.

## Available Tools

This project includes several tools for working with Google Sheets:

### Main Tools (Recommended)

1. **upload_to_sheets_helper.py** - Main script that guides you through the entire process
2. **create_duos_sheets_zip.py** - Creates a ZIP archive of CSV files ready for upload
3. **create_gsheets_csv.py** - Creates Google Sheets-optimized CSV files

### API-based Tools

1. **sheets_direct_uploader.py** - Uses service account authentication (with jibber_jaber_key.json)
2. **google_sheets_uploader.py** - Uses OAuth authentication (requires user login)

## Quick Start Guide

### Direct API Upload (Recommended)

```bash
python upload_to_sheets_helper.py --direct-upload
```

This will:
1. Create Google Sheets-optimized CSV files (if needed)
2. Use your service account (jibber_jaber_key.json) to upload directly to Google Sheets
3. No manual steps required

### Interactive Mode

```bash
python upload_to_sheets_helper.py
```

This will:
1. Create Google Sheets-optimized CSV files (if needed)
2. Ask you to choose between direct API upload or manual upload
3. Guide you through the selected process

### Manual Upload Only

```bash
python upload_to_sheets_helper.py --manual-only
```

This will:
1. Create Google Sheets-optimized CSV files (if needed)
2. Package them into a ZIP archive
3. Provide instructions for manual upload

## Detailed Options

### For Direct API Upload

```bash
python upload_to_sheets_helper.py --direct-upload [--key-file PATH_TO_KEY_FILE] [--csv-dir CSV_DIRECTORY] [--skip-csv-creation]
```

Options:
- `--key-file`: Path to the service account key file (default: jibber_jaber_key.json)
- `--csv-dir`: Directory containing the CSV files (default: duos_outputs2/gsheets_csv)
- `--skip-csv-creation`: Skip creating CSV files and use existing ones

### For Manual Process

If you prefer to run the steps individually:

#### Step 1: Create Google Sheets-optimized CSV files

```bash
python create_gsheets_csv.py [input_csv_path] [output_directory]
```

This creates several CSV files:
- Main data file
- Reference data
- Summary statistics
- Files organized by year and DNO

#### Step 2: Create a ZIP archive

```bash
python create_duos_sheets_zip.py --csv-dir [csv_directory] --output [output_directory]
```

This creates a ZIP file containing:
- All CSV files
- README with instructions
- HTML index for easy navigation

#### Step 3: Manual Upload to Google Sheets

You have two main options:

**Option A: Upload to Google Drive**
1. Go to [Google Drive](https://drive.google.com)
2. Create a new folder
3. Upload the ZIP file
4. Right-click and select "Open with" > "Google Workspace"
5. Google will extract the files which you can open with Sheets

**Option B: Direct Import to Google Sheets**
1. Extract the ZIP file locally
2. Go to [Google Sheets](https://sheets.new)
3. Use File > Import to upload each CSV file

## Using the Direct Uploader Standalone

You can also use the direct uploader directly:

```bash
python sheets_direct_uploader.py [csv_directory]
```

This requires:
1. The service account key file (jibber_jaber_key.json) in the current directory
2. The CSV files to upload

## Troubleshooting

**Service account authentication issues**
- Verify the key file exists and is correctly named (jibber_jaber_key.json)
- Check that the service account has appropriate permissions
- Ensure the service account is enabled in Google Cloud Console

**CSV files not found**
- Check that you've run create_gsheets_csv.py first
- Verify the path to the CSV directory

**ZIP creation fails**
- Ensure you have write permissions in the current directory
- Check disk space

**"Unable to access the service" error**
- Make sure Google Sheets and Drive APIs are enabled for your service account
- Check if the service account has been disabled

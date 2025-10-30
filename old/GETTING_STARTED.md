# Getting Started with Google Sheets Integration

I've created a set of tools to help you upload your DNO DUoS data to Google Sheets. This document provides a quick guide to get you started.

## What I've Built For You

1. **Manual Upload Tool** - Works immediately without any setup
2. **Direct API Upload Tool** - Uses your service account but requires API activation
3. **Helper Script** - Guides you through the process and offers both options
4. **Comprehensive Documentation** - Explains all available options and troubleshooting

## Quick Start Guide

### Option 1: Manual Upload (Works Immediately)

This option requires no additional setup and works right away:

```bash
python upload_to_sheets_helper.py --manual-only
```

This will:
1. Create a ZIP file with all your CSV files
2. Provide instructions for manual upload to Google Sheets
3. Open Google Drive in your browser if you choose

### Option 2: Direct API Upload (Requires Setup)

I found that your service account needs the Google Sheets and Drive APIs enabled before it can upload directly. To set this up:

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Select your project (jibber-jabber-knowledge)
3. Navigate to "APIs & Services" > "Library"
4. Search for and enable both:
   - Google Sheets API
   - Google Drive API

After enabling these APIs, you can use:

```bash
python upload_to_sheets_helper.py --direct-upload
```

## Service Account Details

I found your service account in the credentials file:
- Email: `jibber-jabber-knowledge@appspot.gserviceaccount.com`
- Project: `jibber-jabber-knowledge`

This service account can be used for automated uploads once the APIs are enabled.

## Need More Help?

Check these resources:
- `GOOGLE_SHEETS_INTEGRATION_GUIDE.md` - Comprehensive documentation
- `SOLUTION_SUMMARY.md` - Overview of all the tools created

## Troubleshooting Common Issues

**Permission Denied Errors**
- Make sure Google Sheets API and Google Drive API are enabled in Google Cloud Console
- Verify the service account has not been disabled
- Check if the service account has appropriate permissions

**Manual Upload Issues**
- Make sure you extract the ZIP file before trying to import individual files
- When uploading the ZIP to Google Drive, right-click and select "Open with" > "Google Workspace"

**CSV File Issues**
- If you encounter CSV format issues, try using the `--skip-csv-creation` flag with existing files
- Make sure the source CSV files exist in the expected location

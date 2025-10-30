# Google Sheets & Drive API Setup Guide

This guide walks through setting up the Google Cloud project and obtaining credentials needed for the Google Sheets Uploader script.

## 1. Create a Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Click on the project dropdown at the top of the page
3. Click "New Project"
4. Enter the project name: "jibber-jabber-knowledge"
5. Click "Create"

## 2. Enable the Required APIs

1. In the Google Cloud Console, select your new project
2. In the left sidebar, navigate to "APIs & Services" > "Library"
3. Search for and enable the following APIs:
   - Google Drive API
   - Google Sheets API

## 3. Create OAuth Credentials

1. In the left sidebar, navigate to "APIs & Services" > "Credentials"
2. Click "Create Credentials" > "OAuth client ID"
3. If prompted, configure the OAuth consent screen:
   - User Type: External
   - App name: "jibber-jabber-knowledge"
   - User support email: Your email address
   - Developer contact information: Your email address
   - Save and continue through the wizard, you don't need to add scopes or test users for this personal use case

4. Return to the Credentials page
5. Click "Create Credentials" > "OAuth client ID" again
6. Application type: Desktop app
7. Name: "jibber-jabber-knowledge-client"
8. Click "Create"
9. Click "Download JSON" and save the file as `credentials.json` in the same directory as the script

## 4. Run the Uploader Script

1. Install the required packages:
   ```
   pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib
   ```

2. Place the `credentials.json` file in the same directory as the script

3. Run the script:
   ```
   python google_sheets_uploader.py duos_outputs2/gsheets_csv
   ```

4. The first time you run the script, it will open a browser window asking you to log in with your Google account and grant permissions to the app. After authenticating, the script will store a token for future use.

## 5. Understanding the Outputs

The script will:
1. Create a main folder in your Google Drive
2. Upload all CSV files as Google Sheets
3. Organize files in subfolders (By Year, By DNO)
4. Create an index sheet with links to all uploaded files
5. Apply basic formatting to all sheets

## Troubleshooting

- **Error: "The caller does not have permission"**: Make sure you've enabled the necessary APIs in your Google Cloud project
- **Error: "invalid_grant"**: The token may have expired. Delete the `token.pickle` file and run the script again to re-authenticate
- **Browser doesn't open for authentication**: Try accessing the URL that the script outputs manually

## Security Notes

- The `credentials.json` file allows applications to request authorization from your Google account
- The `token.pickle` file contains access tokens and should be kept secure
- The script only requests access to Google Drive and Google Sheets, not your email or other Google services

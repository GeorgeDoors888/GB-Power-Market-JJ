# DNO Map OAuth 2.0 Setup Guide

This guide explains how to set up the DNO Map visualization with OAuth 2.0 authentication, which allows users to authenticate with their Google account and then use refresh tokens for subsequent accesses.

## Prerequisites

1. Python 3.6+ installed
2. Required Python packages (install with `pip install -r requirements.txt`):
   - google-auth
   - google-auth-oauthlib
   - google-auth-httplib2
   - google-api-python-client

## Setup Instructions

### 1. Create OAuth 2.0 Client ID in Google Cloud Console

1. Go to the [Google Cloud Console](https://console.cloud.google.com/)
2. Select your project (jibber-jabber-knowledge)
3. Go to "APIs & Services" > "Credentials"
4. Click "Create Credentials" > "OAuth client ID"
5. Application type: Desktop app
6. Name: "DNO Map Client"
7. Click "Create"
8. Download the JSON file and save it as `client_secrets.json` in the same directory as the script

### 2. Enable Required APIs

Make sure the following APIs are enabled in your Google Cloud project:

- Google Sheets API
- Google Drive API
- Google Apps Script API

To enable them:
1. Go to "APIs & Services" > "Library"
2. Search for each API and enable it if it's not already enabled

### 3. Run the OAuth Setup Script

```bash
# Activate your virtual environment if you have one
source gsheets_env/bin/activate

# Run the script
python dno_map_oauth_setup.py
```

### 4. First-time Authentication

When you run the script for the first time:

1. A browser window will open asking you to log in with your Google account
2. You'll see a warning that the app isn't verified - click "Advanced" and then "Go to DNO Map Client (unsafe)"
3. Grant the requested permissions
4. The browser will show "The authentication flow has completed. You may close this window."
5. The script will continue running and will:
   - Create or update the DNO_Data sheet
   - Create a new Apps Script project
   - Upload the map code

### 5. Subsequent Runs

After the first authentication:

1. The script will use the stored refresh token in `token.pickle`
2. No browser authentication will be needed unless the token expires or is revoked

## Troubleshooting

### "Error creating Apps Script project"

If you see this error, the script will fall back to generating local files for manual setup. Follow the instructions provided by the script to manually set up the Apps Script project.

### "Invalid client" error during OAuth flow

This might happen if:
1. The client_secrets.json file is incorrect
2. The OAuth client ID is not properly configured
3. The APIs are not enabled in your Google Cloud project

Double-check your Google Cloud Console settings and ensure all required APIs are enabled.

### "Access denied" when accessing the spreadsheet

Make sure:
1. You're authenticating with a Google account that has access to the spreadsheet
2. The spreadsheet ID in the script is correct

## Security Considerations

- The `token.pickle` file contains your OAuth refresh token. Keep it secure.
- Anyone with access to this token can access your Google resources with the permissions you granted.
- Consider storing the token in a more secure location for production use.

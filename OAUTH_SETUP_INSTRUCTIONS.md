# OAuth Setup Instructions for Google Drive/Sheets Access

## Why We Need OAuth

The **service account** (jibber-jabber-knowledge@appspot.gserviceaccount.com) has its own limited storage (~15GB quota exceeded).

To upload directly to **your Google Drive** (george@upowerenergy.uk with 7TB), we need OAuth credentials that authenticate as YOU.

---

## Step-by-Step OAuth Setup

### Step 1: Go to Google Cloud Console
1. Open: https://console.cloud.google.com
2. Log in as: **george@upowerenergy.uk**
3. Select your project (or the one with the service account)

### Step 2: Enable APIs (if not already enabled)
1. Go to **APIs & Services** → **Library**
2. Search and enable:
   - **Google Drive API**
   - **Google Sheets API**

### Step 3: Create OAuth Credentials
1. Go to **APIs & Services** → **Credentials**
2. Click **+ CREATE CREDENTIALS** → **OAuth client ID**
3. If prompted, configure **OAuth consent screen**:
   - User Type: **Internal** (if using Workspace) or **External**
   - App name: "DNO Charging Data Uploader"
   - User support email: george@upowerenergy.uk
   - Scopes: Add `/auth/drive.file` and `/auth/spreadsheets`
   - Test users: Add george@upowerenergy.uk
   - Save and continue

4. Back to **Create OAuth client ID**:
   - Application type: **Desktop app**
   - Name: "DNO Charging Uploader"
   - Click **CREATE**

5. Download the credentials:
   - Click **DOWNLOAD JSON**
   - Save as: `oauth_credentials.json`
   - Move to: `/Users/georgemajor/GB Power Market JJ/`

### Step 4: Update the Script
The script will use OAuth instead of service account and create files in YOUR Drive.

---

## What Happens Next

1. First time you run the script, it will:
   - Open a browser window
   - Ask you to log in as george@upowerenergy.uk
   - Request permission to access Drive/Sheets
   - Save a `token.json` file for future use

2. Subsequent runs will use the saved token (no login needed)

---

## Files You Need

```
/Users/georgemajor/GB Power Market JJ/
├── oauth_credentials.json  ← Download from Google Cloud Console
└── token.json              ← Will be created automatically on first run
```

---

**Once you have `oauth_credentials.json`, I'll update the upload script to use OAuth instead of the service account!**

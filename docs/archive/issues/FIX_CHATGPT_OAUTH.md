# Fix ChatGPT Google Drive OAuth Connection

## Problem
```
ChatGPT Error: "There was a problem syncing GitHub"
```

**This error message is misleading!** It's actually about Google Drive/Google Workspace OAuth, not GitHub.

---

## Understanding the Issue

ChatGPT web interface can connect to Google Drive to:
- Access your Google Drive files
- Read Google Sheets
- Use Google Docs

This connection is **separate** from the service account used by the extraction scripts. ChatGPT uses **OAuth** to connect as you directly.

---

## Solution Steps

### Option 1: Fix Existing Connection (Recommended)

#### Step 1: Check Current Connections

1. **Go to:** [https://myaccount.google.com/permissions](https://myaccount.google.com/permissions)

2. **Sign in as:** `george@upowerenergy.uk`

3. **Look for these apps:**
   - **ChatGPT** or **OpenAI**
   - Check if they appear in the list

#### Step 2: Remove Old Connection

1. If you see **ChatGPT** or **OpenAI** in the list:
   - Click on it
   - Click **REMOVE ACCESS**
   - Confirm removal

#### Step 3: Reconnect in ChatGPT

1. **Go to:** [https://chat.openai.com](https://chat.openai.com)

2. **Click your profile picture** (bottom left)

3. **Settings → Data controls**

4. **Look for "Google Drive" or "Connect apps"**

5. **Click "Connect" or "Reconnect"**

6. **Choose the account:** `george@upowerenergy.uk`

7. **Review permissions and click "Allow"**

---

### Option 2: Fresh Connection

If you don't see the option in ChatGPT settings:

#### In ChatGPT Conversation

1. **Type in ChatGPT:**
   ```
   Can you help me access my Google Drive files?
   ```

2. ChatGPT will prompt you to connect Google Drive

3. **Click the authorization link**

4. **Sign in with:** `george@upowerenergy.uk`

5. **Grant permissions:**
   - ✅ See and download all your Google Drive files
   - ✅ See, edit, create Google Sheets
   - ✅ View Google Docs

6. **Click "Allow"**

---

### Option 3: Use ChatGPT Desktop App (Alternative)

If the web version isn't working:

1. **Download ChatGPT Desktop App:**
   - macOS: Available in App Store or [openai.com/chatgpt/download](https://openai.com/chatgpt/download)

2. **Connect Google Drive:**
   - Desktop app may have better OAuth handling
   - Follow same steps as Option 1

---

## Verifying the Connection

After connecting, test it:

1. **In ChatGPT, type:**
   ```
   Can you list some files from my Google Drive?
   ```

2. **Or try to access a specific file:**
   ```
   Can you read this Google Sheet: [paste sheet URL]
   ```

3. **Should see:**
   - ✅ ChatGPT can access your files
   - ✅ No "syncing GitHub" error
   - ✅ Can read Sheets/Docs content

---

## Troubleshooting

### Still getting "syncing GitHub" error?

1. **Clear browser cache:**
   - Chrome: Settings → Privacy → Clear browsing data
   - Select "Cached images and files"
   - Clear data

2. **Try incognito/private mode:**
   - Open ChatGPT in incognito window
   - Sign in again
   - Try connecting Google Drive

3. **Check Google Workspace admin settings:**
   - Your admin might have restricted OAuth apps
   - Go to: [admin.google.com](https://admin.google.com) (as admin)
   - Security → API Controls → App access control
   - Make sure ChatGPT/OpenAI is not blocked

4. **Try a different browser:**
   - Sometimes browser extensions interfere
   - Try Safari, Firefox, or Chrome (different from your main browser)

### Google says "Access blocked"?

If you get "This app is blocked" when trying to authorize:

1. **Contact your Google Workspace admin**
   - They need to allowlist ChatGPT/OpenAI

2. **Admin needs to:**
   - Go to: [admin.google.com](https://admin.google.com)
   - Security → API Controls → App access control
   - Configure → Add app → OAuth App Name or Client ID
   - Search for "ChatGPT" or "OpenAI"
   - Select and click "Trust"

### Still not working?

**Alternative: Use service account instead**

You can use the existing extraction scripts to:
- Export data to Google Sheets (already have this: `export_to_sheets.py`)
- ChatGPT can then read those Sheets directly
- No OAuth needed if files are publicly shared or shared with your account

---

## What This Connection Does

Once connected, ChatGPT can:
- ✅ Read your Google Drive files
- ✅ Access Google Sheets data
- ✅ View Google Docs content
- ✅ List files in your Drive
- ✅ Help you analyze documents

ChatGPT **cannot**:
- ❌ Modify or delete files (read-only access)
- ❌ Access files not owned by george@upowerenergy.uk
- ❌ Share files with others
- ❌ Change permissions

---

## Difference: OAuth vs Service Account

**ChatGPT OAuth (this fix):**
- You authorize ChatGPT to access YOUR files
- Works through ChatGPT web interface
- You can revoke anytime at myaccount.google.com/permissions

**Service Account (extraction scripts):**
- Python scripts use `gridsmart_service_account.json`
- Automated access via domain-wide delegation
- Works on UpCloud server for extraction
- Different authentication method

Both can coexist! The service account is for automated extraction, OAuth is for interactive ChatGPT access.

---

## Next Steps

After fixing:

1. **Test the connection** with a simple request in ChatGPT
2. **Try accessing** a Google Sheet or Doc
3. **Verify** no more "syncing GitHub" errors

If you need help accessing specific files, you can share them with ChatGPT by:
- Making them accessible via link
- Ensuring george@upowerenergy.uk has access
- Using the export scripts to create Sheets

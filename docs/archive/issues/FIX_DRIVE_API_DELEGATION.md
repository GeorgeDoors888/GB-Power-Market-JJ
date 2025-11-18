# Fix Google Drive API - Domain-Wide Delegation Setup

## Problem
```
❌ unauthorized_client: Client is unauthorized to retrieve access tokens
```

The service account `jibber-jabber-knowledge@appspot.gserviceaccount.com` needs domain-wide delegation to access Google Drive files on behalf of users in the @upowerenergy.uk domain.

---

## Solution Steps

### Step 1: Access Google Workspace Admin Console

1. **Go to:** [https://admin.google.com](https://admin.google.com)
2. **Sign in as:** `admin@upowerenergy.uk` (or another super admin account)

---

### Step 2: Navigate to Domain-Wide Delegation

1. In the Admin Console, click **Security** (left sidebar)
   - If you don't see it, click **More controls** at the bottom
2. Click **Access and data control**
3. Click **API controls**
4. Scroll down to **Domain-wide delegation**
5. Click **MANAGE DOMAIN WIDE DELEGATION**

---

### Step 3: Add Service Account

1. Click **Add new** (blue button)
2. Fill in the form:

   **Client ID:**
   ```
   108583076839984080568
   ```

   **OAuth Scopes (copy/paste exactly):**
   ```
   https://www.googleapis.com/auth/drive.readonly,https://www.googleapis.com/auth/drive.metadata.readonly,https://www.googleapis.com/auth/drive,https://www.googleapis.com/auth/spreadsheets,https://www.googleapis.com/auth/documents.readonly
   ```

3. Click **AUTHORIZE**

---

### Step 4: Verify the Entry

You should now see an entry in the Domain-wide delegation list:

- **Client Name:** jibber-jabber-knowledge
- **Client ID:** 108583076839984080568
- **Scopes:** Multiple Google Drive, Sheets, Docs scopes
- **Status:** Active

---

### Step 5: Wait for Propagation (Important!)

⏰ **Wait 5-10 minutes** for Google's systems to propagate the change globally.

---

### Step 6: Test the Fix

Run the diagnostic script:

```bash
cd /Users/georgemajor/Overarch\ Jibber\ Jabber
source .venv/bin/activate
python3 diagnostic_dual_project.py
```

Look for:
```
✅ Drive API working: X files retrieved
```

---

## Troubleshooting

### If still getting unauthorized_client:

1. **Double-check the Client ID:**
   - Make sure it's exactly: `108583076839984080568`
   - No extra spaces or characters

2. **Verify the scopes include:**
   - `https://www.googleapis.com/auth/drive.readonly`
   - `https://www.googleapis.com/auth/drive.metadata.readonly`

3. **Wait longer:**
   - Can take up to 15 minutes to propagate
   - Try clearing your browser cache

4. **Check admin permissions:**
   - You must be a Google Workspace super admin
   - Regular admins may not have access to this section

### If you don't have admin access:

Contact your Google Workspace administrator and send them:
- This document
- The Client ID: `108583076839984080568`
- The scopes list above

---

## What This Does

Domain-wide delegation allows the service account to:
- ✅ Access Google Drive files as any user in @upowerenergy.uk
- ✅ Read file metadata and content
- ✅ List files in user drives
- ✅ Download PDF documents for extraction

This is necessary for the extraction process to read documents from Google Drive.

---

## Security Note

The service account will only be able to:
- Read files (not modify or delete)
- Act as `george@upowerenergy.uk` (specified in the code)
- Access only files that george@upowerenergy.uk has permission to see

The private key (`gridsmart_service_account.json`) must be kept secure.

# 🔐 Authentication & Credentials Guide

**Last Updated:** October 30, 2025  
**Repository Location:** `~/repo/GB Power Market JJ`

---

## 📁 Repository Location Change

**Previous Location:** `~/GB Power Market JJ`  
**Current Location:** `~/repo/GB Power Market JJ`

✅ Git repository fully functional at new location  
✅ GitHub connection maintained: `git@github.com:GeorgeDoors888/jibber-jabber-24-august-2025-big-bop.git`

### Scripts Updated for New Location:
- `fix-gb-power-market.sh` - Updated to use `~/repo/GB Power Market JJ`

---

## 🔑 Authentication Overview

This project uses **multiple authentication methods** for different Google Cloud services:

### 1️⃣ **BigQuery Access** (IRIS Data Queries)
- **Method:** Application Default Credentials (ADC)
- **How it works:** BigQuery Client automatically detects credentials
- **No explicit credentials needed** in code
- **Project:** `inner-cinema-476211-u9` (Smart Grid Data Project)
- **Datasets:** `uk_energy_prod` (contains IRIS tables)

```python
# How BigQuery is authenticated in our code:
client = bigquery.Client(project='inner-cinema-476211-u9')
# No credentials parameter - uses ADC automatically!
```

**Why this works:**
- Python Google Cloud libraries automatically check for credentials in this order:
  1. `GOOGLE_APPLICATION_CREDENTIALS` environment variable (not set)
  2. gcloud CLI credentials (if installed)
  3. OAuth token in `~/.config/gcloud/` (exists from previous setup)
  4. Service account credentials (if running on GCP)

### 2️⃣ **Google Sheets/Drive Access** (Dashboard Updates)
- **Method:** OAuth 2.0 (User Credentials)
- **Token File:** `token.pickle`
- **Credentials File:** `credentials.json`
- **User Account:** `george@upowerenergy.uk` (authorized account)
- **Scopes:**
  - `https://www.googleapis.com/auth/spreadsheets`
  - `https://www.googleapis.com/auth/drive`
  - `https://www.googleapis.com/auth/bigquery`

```python
# How Sheets is authenticated:
with open('token.pickle', 'rb') as f:
    creds = pickle.load(f)
gc = gspread.authorize(creds)
```

---

## 📋 Credential Files Inventory

### **token.pickle**
- **Type:** OAuth 2.0 Access Token (pickled Python object)
- **Location:** `~/repo/GB Power Market JJ/token.pickle`
- **Account:** george@upowerenergy.uk
- **Scopes:** Sheets, Drive, BigQuery
- **Status:** ✅ Active and valid
- **Expires:** Auto-refreshes using refresh token
- **Backup:** `token.pickle.backup` (created during re-auth attempts)

### **credentials.json**
- **Type:** OAuth 2.0 Client ID Configuration
- **Location:** `~/repo/GB Power Market JJ/credentials.json`
- **Project:** jibber-jabber-knowledge
- **Client ID:** `1090450657636-rup6nqmm66uq2okv3skqf720hdgi5b1f.apps.googleusercontent.com`
- **Client Secret:** `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`
- **Use:** OAuth flow to generate `token.pickle`

### **jibber_jabber_key.json**
- **Type:** Service Account Key
- **Location:** `~/repo/GB Power Market JJ/jibber_jabber_key.json`
- **Project:** jibber-jabber-knowledge
- **Email:** `jibber-jabber-knowledge@appspot.gserviceaccount.com`
- **Use:** ~~BigQuery operations~~ (NOT used for IRIS - no permissions on inner-cinema-476211-u9)
- **Permissions:** Full access to `jibber-jabber-knowledge` project only

### **service-account-key.json**
- **Status:** ❌ MISSING
- **Expected Location:** `~/repo/GB Power Market JJ/service-account-key.json`
- **Would Contain:** Smart Grid service account for `inner-cinema-476211-u9`
- **Workaround:** Using Application Default Credentials instead

---

## 🗂️ Google Cloud Projects

### **jibber-jabber-knowledge** (Service Account Project)
- **APIs Enabled:**
  - ✅ BigQuery API
  - ✅ Cloud Storage API
- **Service Account Access:** Full (via `jibber_jabber_key.json`)
- **Dataset:** `uk_energy_insights`
- **Use:** Non-IRIS data storage

### **inner-cinema-476211-u9** (Smart Grid - IRIS Data Project)
- **APIs Enabled:**
  - ✅ BigQuery API
  - ✅ BigQuery Data Transfer API
  - ✅ Cloud Storage API
- **Access Method:** Application Default Credentials (ADC)
- **Dataset:** `uk_energy_prod`
- **Tables:** IRIS tables (`bmrs_*_iris`)
  - `bmrs_mid_iris` - Market Index Data
  - `bmrs_freq_iris` - Grid Frequency
  - `bmrs_fuelinst_iris` - Fuel Generation
  - `bmrs_boalf_iris` - BOA Lift Forecast
  - `bmrs_bod_iris` - Bid-Offer Data
  - `bmrs_beb_iris` - Balancing Energy Bids
  - `bmrs_mels_iris` - MEL Data
  - `bmrs_mils_iris` - MIL Data

---

## 🌐 Google Account Access

### **george@upowerenergy.uk**
- **Services:**
  - ✅ Google Sheets API
  - ✅ Google Drive API
  - ✅ Apps Script API (via Sheets UI)
- **OAuth Token:** `token.pickle`
- **Dashboard:** "GB Energy Dashboard" (ID: `12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8`)
- **Sheets:** Owner of all 10 sheets

### **Smart Grid Account** (Exact email unknown)
- **Services:**
  - ✅ BigQuery access to `inner-cinema-476211-u9`
- **Access Method:** Application Default Credentials
- **Note:** Service account key file not available, but ADC works

---

## 🔄 How Authentication Works in Our Scripts

### **automated_iris_dashboard.py** (IRIS Dashboard)
```python
# BigQuery - Application Default Credentials
self.bq_client = bigquery.Client(project='inner-cinema-476211-u9')
# No credentials parameter - automatically uses ADC

# Google Sheets - OAuth
with open('token.pickle', 'rb') as f:
    oauth_creds = pickle.load(f)
self.gc = gspread.authorize(oauth_creds)
```

### **update_graph_data.py** (Settlement Data)
```python
# BigQuery - Application Default Credentials
client = bigquery.Client(project='inner-cinema-476211-u9')

# Google Sheets - Fallback pattern
try:
    creds = Credentials.from_service_account_file(
        'service-account-key.json',  # Tries this first (missing)
        scopes=SCOPES
    )
except:
    with open('token.pickle', 'rb') as token:
        creds = pickle.load(token)  # Falls back to this
return gspread.authorize(creds)
```

### **iris_to_bigquery_unified.py** (IRIS Processor)
```python
# Uses environment variable or service account
# Location: ~/repo/GB Power Market JJ (different repo location!)
```

---

## 🔧 Re-authenticating Services

### **Re-authenticate Google Sheets/Drive:**
```bash
cd ~/repo/GB\ Power\ Market\ JJ
./.venv/bin/python reauthorize_manual.py
```
This creates a new `token.pickle` with OAuth credentials.

### **Re-authenticate BigQuery:**
Not needed! Application Default Credentials work automatically.

If you need to explicitly set up BigQuery auth:
```bash
# Install gcloud CLI first, then:
gcloud auth application-default login
```

---

## 🚨 Common Authentication Issues

### **Issue 1: "Access Denied: User does not have bigquery.jobs.create permission"**
**Cause:** Using wrong service account (jibber_jabber_key.json)  
**Solution:** Use Application Default Credentials (no explicit credentials in code)

### **Issue 2: "The user's Drive storage quota has been exceeded"**
**Cause:** Trying to create new spreadsheets when Drive is full  
**Solution:** Use existing spreadsheet ID (`12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8`)

### **Issue 3: "Google hasn't verified this app"**
**Cause:** OAuth app not verified by Google (normal for dev apps)  
**Solution:** Click "Advanced" → "Go to [App Name] (unsafe)"

### **Issue 4: "Token expired" or "Token invalid"**
**Cause:** OAuth token needs refresh  
**Solution:** Run `reauthorize_manual.py` to get new token

---

## 📊 Active Dashboard

**Name:** GB Energy Dashboard  
**ID:** `12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8`  
**URL:** https://docs.google.com/spreadsheets/d/12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8  
**Owner:** george@upowerenergy.uk

**Sheets:**
1. Sheet1 - Settlement data (A18:H28)
2. Calculations BHM
3. HH Profile
4. Sheet7
5. DNO_ID
6. DNUoS 2
7. DNUoS
8. Map
9. DNO_Data
10. Chart Data

**IRIS Sheets** (auto-created by automated_iris_dashboard.py):
- Grid Frequency - 36 data points (refreshed automatically)
- Recent Activity - 4 datasets status
- System Prices - (empty - no recent MID data)
- Fuel Generation - (empty - no recent fuelinst data)

---

## 🎯 Working Authentication Flow

```
┌─────────────────────────────────────────────────────────────┐
│                    IRIS Dashboard Update                     │
└─────────────────────────────────────────────────────────────┘
                            │
                ┌───────────┴───────────┐
                │                       │
                ▼                       ▼
    ┌──────────────────┐    ┌─────────────────────┐
    │   BigQuery       │    │  Google Sheets      │
    │   (inner-cinema) │    │  (GB Energy Dash)   │
    └──────────────────┘    └─────────────────────┘
                │                       │
                │                       │
                ▼                       ▼
    ┌──────────────────┐    ┌─────────────────────┐
    │  Application     │    │   token.pickle      │
    │  Default Creds   │    │   (OAuth)           │
    │  (Auto-detect)   │    │   george@upoweruk   │
    └──────────────────┘    └─────────────────────┘
                │                       │
                └───────────┬───────────┘
                            │
                            ▼
                  ┌──────────────────┐
                  │  IRIS Data in    │
                  │  Dashboard ✅    │
                  └──────────────────┘
```

---

## 📝 Quick Reference Commands

```bash
# Navigate to repository
cd ~/repo/GB\ Power\ Market\ JJ

# Test BigQuery access
./.venv/bin/python -c "
from google.cloud import bigquery
client = bigquery.Client(project='inner-cinema-476211-u9')
print('✅ BigQuery connected')
"

# Test Sheets access
./.venv/bin/python -c "
import pickle, gspread
with open('token.pickle', 'rb') as f:
    creds = pickle.load(f)
gc = gspread.authorize(creds)
sheet = gc.open_by_key('12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8')
print('✅ Sheets connected:', sheet.title)
"

# Run automated dashboard
./.venv/bin/python automated_iris_dashboard.py

# Run in loop mode (every 5 minutes)
./.venv/bin/python automated_iris_dashboard.py --loop --interval 300
```

---

## ✅ Verification Checklist

- [x] Repository moved to `~/repo/GB Power Market JJ`
- [x] BigQuery access working via Application Default Credentials
- [x] Google Sheets access working via OAuth token
- [x] IRIS data flowing to dashboard
- [x] Grid Frequency data updating (36 rows)
- [x] Recent Activity tracking (4 datasets)
- [x] Automated dashboard script functional
- [ ] Chart creation (needs gspread API fix)
- [ ] MID data investigation (0 rows returned)
- [ ] FUELINST data investigation (0 rows returned)

---

## 🎉 Success Summary

**What's Working:**
1. ✅ BigQuery queries IRIS data from `inner-cinema-476211-u9`
2. ✅ Dashboard updates existing "GB Energy Dashboard"
3. ✅ Auto-creates new sheets (Grid Frequency, Recent Activity)
4. ✅ No manual authentication needed (ADC + token.pickle)
5. ✅ All scripts use correct repo location

**Authentication is now fully automated!**

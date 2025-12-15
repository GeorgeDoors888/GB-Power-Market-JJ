# ⚠️ CRITICAL: Google Cloud Project IDs Reference

## 🚨 Two Different Projects - DO NOT MIX!

Energy Jibber Jabber uses **TWO SEPARATE** Google Cloud projects for different purposes:

---

## 1️⃣ BigQuery Data Project

**Project ID:** `inner-cinema-476211-u9`  
**Project Name:** Inner Cinema  
**Purpose:** Data storage and analytics

### Used For:
- ✅ BigQuery datasets (`uk_energy_insights`, `uk_energy_prod`)
- ✅ Vertex AI embeddings
- ✅ Data pipeline operations
- ✅ Search API backend
- ✅ Service account: `all-jibber@inner-cinema-476211-u9.iam.gserviceaccount.com`

### Console Links:
- BigQuery: https://console.cloud.google.com/bigquery?project=inner-cinema-476211-u9
- APIs: https://console.cloud.google.com/apis?project=inner-cinema-476211-u9
- IAM: https://console.cloud.google.com/iam-admin?project=inner-cinema-476211-u9

### Example Usage:
```python
# ✅ CORRECT
client = bigquery.Client(project="inner-cinema-476211-u9")
query = "SELECT * FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_fuelinst`"
```

---

## 2️⃣ Apps Script / Sheets Project

**Project ID:** `jibber-jabber-knowledge`  
**Project Name:** Jibber Jabber Knowledge  
**Purpose:** Google Sheets automation and service account

### Used For:
- ✅ Google Sheets access (1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA)
- ✅ Apps Script API
- ✅ Service account: `jibber-jabber-knowledge@appspot.gserviceaccount.com`
- ✅ ChatGPT Drive connector authentication
- ✅ Sheets verification scripts

### Console Links:
- Apps Script API: https://console.cloud.google.com/apis/library/script.googleapis.com?project=jibber-jabber-knowledge
- APIs: https://console.cloud.google.com/apis?project=jibber-jabber-knowledge
- IAM: https://console.cloud.google.com/iam-admin?project=jibber-jabber-knowledge

### Example Usage:
```python
# ✅ CORRECT - For Sheets/Apps Script operations
SA_PATH = "smart_grid_credentials.json"  # jibber-jabber-knowledge@appspot
creds = Credentials.from_service_account_file(SA_PATH)
```

---

## 🔍 Quick Decision Guide

**When should I use `inner-cinema-476211-u9`?**
- Running BigQuery queries
- Accessing `uk_energy_insights` or `uk_energy_prod` datasets
- Vertex AI operations
- Data pipeline scripts
- Search API configuration

**When should I use `jibber-jabber-knowledge`?**
- Enabling Apps Script API
- Google Sheets automation
- Service account permissions for sheets
- Apps Script project settings
- Drive API operations for sheets

---

## ❌ Common Mistakes to Avoid

### Mistake 1: Using wrong project for Apps Script API
```bash
# ❌ WRONG
https://console.cloud.google.com/apis/library/script.googleapis.com?project=inner-cinema-476211-u9

# ✅ CORRECT
https://console.cloud.google.com/apis/library/script.googleapis.com?project=jibber-jabber-knowledge
```

### Mistake 2: Using wrong project for BigQuery
```python
# ❌ WRONG
client = bigquery.Client(project="jibber-jabber-knowledge")

# ✅ CORRECT
client = bigquery.Client(project="inner-cinema-476211-u9")
```

### Mistake 3: Linking Apps Script to wrong project
```
# ❌ WRONG (in Apps Script settings)
GCP Project: inner-cinema-476211-u9

# ✅ CORRECT
GCP Project: jibber-jabber-knowledge
```

---

## 📋 Service Accounts Summary

| Service Account | Project | Purpose |
|----------------|---------|---------|
| `all-jibber@inner-cinema-476211-u9.iam.gserviceaccount.com` | inner-cinema-476211-u9 | BigQuery data access |
| `jibber-jabber-knowledge@appspot.gserviceaccount.com` | jibber-jabber-knowledge | Sheets/Drive access |

**File:** `smart_grid_credentials.json`
- **Type:** service_account
- **Email:** jibber-jabber-knowledge@appspot.gserviceaccount.com
- **Project:** jibber-jabber-knowledge
- **Uses:** Google Sheets, Drive, Apps Script

---

## 🔧 Configuration Files

### Environment Variables (.env)
```bash
# BigQuery operations
BQ_PROJECT=inner-cinema-476211-u9
BQ_DATASET=uk_energy_insights

# Service account (for Sheets/Drive)
GOOGLE_APPLICATION_CREDENTIALS=smart_grid_credentials.json
```

### Python Code
```python
# BigQuery
BQ_PROJECT = "inner-cinema-476211-u9"
client = bigquery.Client(project=BQ_PROJECT)

# Sheets/Apps Script
SA_PATH = "smart_grid_credentials.json"  # jibber-jabber-knowledge project
creds = Credentials.from_service_account_file(SA_PATH)
```

---

## 📚 Updated Documentation

The following files have been corrected to use the right project IDs:

✅ **Fixed:**
- `ENABLE_APPS_SCRIPT_API.md` - Now uses `jibber-jabber-knowledge`
- `APPS_SCRIPT_API_GUIDE.md` - Updated all Apps Script references
- `run_apps_script_tests.py` - Correct project in error messages
- `deploy_and_run_verification.py` - Uses correct service account

✅ **Already Correct:**
- `drive-bq-indexer/API.md` - Uses `inner-cinema-476211-u9` for BigQuery
- `README.md` - Clear distinction between projects
- `PROJECT_CONFIGURATION.md` - Documented both projects

---

## 🎯 Action Items

### For Developers:
1. **Always check** which operation you're doing before choosing project
2. **Search codebase** for hardcoded project IDs before making changes
3. **Use environment variables** instead of hardcoding when possible
4. **Read this file** when confused about which project to use

### For New Contributors:
1. Read this file first
2. Understand there are TWO projects
3. Never mix them up
4. Ask if unsure

---

## 🔗 Quick Links

| Resource | inner-cinema-476211-u9 | jibber-jabber-knowledge |
|----------|------------------------|-------------------------|
| Console | [Link](https://console.cloud.google.com/home/dashboard?project=inner-cinema-476211-u9) | [Link](https://console.cloud.google.com/home/dashboard?project=jibber-jabber-knowledge) |
| BigQuery | [Link](https://console.cloud.google.com/bigquery?project=inner-cinema-476211-u9) | N/A |
| APIs | [Link](https://console.cloud.google.com/apis?project=inner-cinema-476211-u9) | [Link](https://console.cloud.google.com/apis?project=jibber-jabber-knowledge) |
| IAM | [Link](https://console.cloud.google.com/iam-admin?project=inner-cinema-476211-u9) | [Link](https://console.cloud.google.com/iam-admin?project=jibber-jabber-knowledge) |

---

**Last Updated:** November 5, 2025  
**Maintainer:** Energy Jibber Jabber Team  
**Status:** ✅ Canonical Reference

---

## 💡 Remember:

> **BigQuery = `inner-cinema-476211-u9`**  
> **Sheets/Apps Script = `jibber-jabber-knowledge`**

**Never mix these up again!** 🎯

# 🔑 PROJECT IDENTITY & OWNERSHIP - MASTER REFERENCE

**CRITICAL:** Read this FIRST before making ANY infrastructure changes!

---

## TWO SEPARATE GOOGLE CLOUD ORGANIZATIONS

### 🔵 SMART GRID (inner-cinema-476211-u9)

**GCP Project:** `inner-cinema-476211-u9`  
**GCP Project Number:** `922809339325`  
**Organization:** Smart Grid organization  
**Purpose:** BigQuery data warehouse, Railway backend, analytics

**Services:**
- ✅ **BigQuery datasets:**
  - `uk_energy_prod` - BMRS tables (bmrs_mid, bmrs_bod, bmrs_boalf, bmrs_indgen_iris, etc.)
  - `uk_energy_insights` - Document indexing, chunks, embeddings
- ✅ **Railway Backend:** jibber-jabber-production.up.railway.app
- ✅ **Service Account:** all-jibber@inner-cinema-476211-u9.iam.gserviceaccount.com
- ✅ **Vertex AI:** Embeddings generation
- ✅ **Vercel Proxy:** gb-power-market-jj.vercel.app

**Railway Configuration:**
```python
BQ_PROJECT = os.environ.get("BQ_PROJECT_ID", "inner-cinema-476211-u9")
BQ_DATASET = "uk_energy_prod"
```

---

### 🟢 UPOWER ENERGY (jibber-jabber-knowledge)

**GCP Project:** `jibber-jabber-knowledge`  
**GCP Project Number:** `1090450657636`  
**Organization:** upowerenergy.uk (Google Workspace)  
**Purpose:** Google Drive, Sheets, Docs, Apps Script

**Services:**
- ✅ **Google Drive:** 153,201+ files
- ✅ **Google Sheets:** Dashboards, analysis spreadsheets
- ✅ **Apps Script:** Container-bound scripts
- ✅ **Service Account:** jibber-jabber-knowledge@appspot.gserviceaccount.com
- ✅ **Domain:** upowerenergy.uk
- ✅ **User Account:** george@upowerenergy.uk

**Apps Script Configuration:**
```javascript
// Apps Script MUST query Smart Grid's BigQuery:
const PROJECT = 'inner-cinema-476211-u9';  // ← Smart Grid BigQuery
const DATASET = 'uk_energy_prod';
```

---

## DATA FLOW ARCHITECTURE

```
┌─────────────────────────────────────────────────────────────┐
│  UPOWER ENERGY (jibber-jabber-knowledge)                    │
│  Organization: upowerenergy.uk                              │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Google Sheets                                              │
│  ↓                                                          │
│  Apps Script (container-bound)                              │
│  const PROJECT = 'inner-cinema-476211-u9'  ← queries here  │
│                                                             │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ↓ (API call)
┌────────────────────────────────────────────────────────────┐
│  VERCEL PROXY                                              │
│  gb-power-market-jj.vercel.app/api/proxy-v2               │
└────────────────────┬───────────────────────────────────────┘
                     │
                     ↓ (forwards to)
┌────────────────────────────────────────────────────────────┐
│  RAILWAY BACKEND                                           │
│  jibber-jabber-production.up.railway.app                  │
│  ENV: BQ_PROJECT_ID = "inner-cinema-476211-u9"            │
└────────────────────┬───────────────────────────────────────┘
                     │
                     ↓ (queries)
┌─────────────────────────────────────────────────────────────┐
│  SMART GRID (inner-cinema-476211-u9)                       │
│  Organization: Smart Grid                                  │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  BigQuery:                                                  │
│  • inner-cinema-476211-u9.uk_energy_prod                   │
│    - bmrs_mid (System Prices)                              │
│    - bmrs_bod (BOD Prices)                                 │
│    - bmrs_boalf (Balancing Actions)                        │
│    - bmrs_indgen_iris (Generation)                         │
│    - bmrs_inddem_iris (Demand)                             │
│    - 170+ other BMRS tables                                │
│                                                             │
│  • inner-cinema-476211-u9.uk_energy_insights               │
│    - documents_clean (153k files metadata)                 │
│    - chunks (extracted text)                               │
│    - chunk_embeddings (Vertex AI vectors)                  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## CROSS-PROJECT CONFUSION - COMMON MISTAKES

### ❌ WRONG: Trying to use jibber-jabber-knowledge for BigQuery
```javascript
// DON'T DO THIS!
const PROJECT = 'jibber-jabber-knowledge';  // ← No BMRS data here!
const DATASET = 'bmrs_data';
```

**Why it fails:** The BMRS tables are in `inner-cinema-476211-u9.uk_energy_prod`, NOT in jibber-jabber-knowledge.

---

### ❌ WRONG: Linking Apps Script to inner-cinema-476211-u9
```
Apps Script Settings → Change GCP Project → 922809339325
```

**Why it fails:** upowerenergy.uk account doesn't have permissions in the Smart Grid GCP project.

---

### ❌ WRONG: Using inner-cinema service account for Apps Script
```python
SERVICE_ACCOUNT = "all-jibber@inner-cinema-476211-u9.iam.gserviceaccount.com"
# Trying to deploy Apps Script with this ← Fails!
```

**Why it fails:** Container-bound Apps Scripts must be created/updated by the owner (upowerenergy.uk), not service accounts.

---

## ✅ CORRECT PATTERNS

### Pattern 1: Apps Script Deployment (OAuth)
```python
# Use upowerenergy.uk OAuth credentials
# Apps Script stays in jibber-jabber-knowledge project
# But queries Smart Grid's BigQuery

SCRIPT_PROJECT = "jibber-jabber-knowledge"  # Apps Script lives here
DATA_PROJECT = "inner-cinema-476211-u9"     # Data lives here
```

### Pattern 2: Railway Backend Configuration
```bash
# Railway environment variables:
BQ_PROJECT_ID=inner-cinema-476211-u9
BQ_DATASET=uk_energy_prod
```

### Pattern 3: Apps Script Code
```javascript
// Apps Script queries cross-project:
const VERCEL_PROXY = 'https://gb-power-market-jj.vercel.app/api/proxy-v2';
const PROJECT = 'inner-cinema-476211-u9';  // ← Smart Grid BigQuery
const DATASET = 'uk_energy_prod';
```

---

## PROJECT PERMISSIONS MATRIX

| Service | jibber-jabber-knowledge | inner-cinema-476211-u9 |
|---------|------------------------|------------------------|
| **Owner** | upowerenergy.uk | Smart Grid |
| **Apps Script** | ✅ Lives here | ❌ No access |
| **Google Sheets** | ✅ Lives here | ❌ No access |
| **BigQuery BMRS Data** | ❌ Not here | ✅ Lives here |
| **Railway Backend** | ❌ Not here | ✅ Queries here |
| **Service Account (all-jibber@)** | ❌ No access | ✅ Full access |
| **Service Account (jibber-jabber-knowledge@)** | ✅ Full access | ❌ No access |

---

## WHY TWO PROJECTS?

### Organizational Separation
- **jibber-jabber-knowledge:** UPower Energy's Google Workspace - documents, sheets, collaboration
- **inner-cinema-476211-u9:** Smart Grid's data infrastructure - analytics, ML, data warehouse

### Security Boundary
- UPower Energy users can access Google Drive/Sheets
- Smart Grid controls BigQuery data access via service accounts
- Apps Script acts as authorized client to query Smart Grid data

### Billing Separation
- Google Workspace charges: upowerenergy.uk
- BigQuery/Vertex AI charges: Smart Grid

---

## GOLDEN RULES

1. **Apps Script ALWAYS stays in jibber-jabber-knowledge**
   - Owned by upowerenergy.uk
   - Deployed using upowerenergy.uk OAuth
   - GCP Project: 1090450657636

2. **BigQuery BMRS data ALWAYS in inner-cinema-476211-u9**
   - All bmrs_* tables
   - All uk_energy_prod dataset
   - GCP Project: 922809339325

3. **Railway ALWAYS queries inner-cinema-476211-u9**
   - ENV: BQ_PROJECT_ID=inner-cinema-476211-u9
   - Uses Smart Grid service account
   - Never changes to jibber-jabber-knowledge

4. **Apps Script queries cross-project via API**
   - Apps Script → Vercel → Railway → BigQuery
   - OAuth user: upowerenergy.uk
   - Data source: inner-cinema-476211-u9

---

## TROUBLESHOOTING DECISION TREE

**Q: Apps Script deployment failing?**
→ Use upowerenergy.uk OAuth (not service account)
→ Keep Apps Script in project 1090450657636

**Q: BigQuery queries failing?**
→ Check Railway ENV: BQ_PROJECT_ID=inner-cinema-476211-u9
→ Verify using correct table: inner-cinema-476211-u9.uk_energy_prod.TABLE_NAME

**Q: Permission denied errors?**
→ Apps Script must use upowerenergy.uk credentials
→ BigQuery must use inner-cinema service account
→ Never mix the two!

---

## CONTACT & ACCESS

### jibber-jabber-knowledge (UPower)
- **Admin:** george@upowerenergy.uk
- **Console:** https://console.cloud.google.com/?project=jibber-jabber-knowledge
- **Apps Script:** https://script.google.com (login as george@upowerenergy.uk)

### inner-cinema-476211-u9 (Smart Grid)
- **Admin:** Smart Grid team
- **Console:** https://console.cloud.google.com/?project=inner-cinema-476211-u9
- **Railway:** https://railway.app (Smart Grid account)

---

**Last Updated:** November 7, 2025  
**Status:** ✅ DOCUMENTED AND VERIFIED

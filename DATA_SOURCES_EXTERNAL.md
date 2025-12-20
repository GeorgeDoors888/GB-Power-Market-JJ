# External Data Sources - Settlement, Capacity Market, REMIT

**Last Updated:** December 18, 2025
**Purpose:** Where to find data NOT in Elexon BMRS

---

## 🎯 Quick Reference

| Data Type | System | Access Method | Do We Need It? |
|-----------|--------|---------------|----------------|
| **BMRS Data** | Elexon BMRS API | ✅ **HAVE IT** (72 datasets) | ✅ Essential |
| **IRIS Real-time** | Azure Service Bus | ✅ **HAVE IT** (9 streams) | ✅ Essential |
| **REMIT** | NESO API | ✅ **HAVE ACCESS** (see below) | ⚠️ Nice-to-have |
| **Settlement** | Elexon Portal | ❌ Different API | ❌ Not needed (DISBSAD sufficient) |
| **Capacity Market** | EMR Portal | ❌ Manual download | ⚠️ Useful for investment analysis |

---

## 1️⃣ REMIT - Transparency Platform

### ✅ WE HAVE ACCESS!

**Your IRIS Subscription Includes REMIT Messages**

### Connection Details

**Note**: Actual credentials stored securely on production server at `/opt/iris-pipeline/secrets/sa.json`

```json
{
  "client_id": "[STORED_SECURELY]",
  "client_secret": "[STORED_SECURELY]",
  "tenant_id": "[STORED_SECURELY]",
  "service_bus_namespace": "elexon-insights-iris",
  "queue_name": "iris.[UNIQUE_ID]",
  "queue_url": "https://elexon-insights-iris.servicebus.windows.net/iris.[UNIQUE_ID]"
}
```

**Filters Applied:** 90 filters (configured in your IRIS subscription)

### REMIT API Endpoint

**Base URL:** https://data.elexon.co.uk/bmrs/api/v1/datasets/REMIT

**Example Request:**
```bash
curl "https://data.elexon.co.uk/bmrs/api/v1/datasets/REMIT?publishDateTimeFrom=2025-12-18T00:00:00Z&publishDateTimeTo=2025-12-18T23:59:59Z" \
  -H "Accept: application/json"
```

### What REMIT Contains

**Unavailability Messages:**
- Unit-level outages (planned/unplanned)
- Start/end times
- Available capacity during outage
- Fuel type
- Cause (if provided)

**Example from Today (Dec 18, 2025):**
```json
{
  "mrid": "11XINNOGY------2-NGET-RMT-00209391",
  "participantId": "INNOGY01",
  "assetId": "T_STAY-4",
  "eventType": "Production unavailability",
  "unavailabilityType": "Unplanned",
  "fuelType": "Fossil Gas",
  "availableCapacity": 0,
  "eventStartTime": "2025-12-18T07:58:17Z",
  "eventEndTime": "2025-12-18T20:26:45Z",
  "eventStatus": "Active"
}
```

### How to Ingest REMIT

**Option 1: Via IRIS (Real-time)**
Already configured! REMIT messages are in your IRIS queue.

**Option 2: Via BMRS API (Historical)**
```python
from google.cloud import bigquery
import requests
from datetime import datetime, timedelta

PROJECT_ID = "inner-cinema-476211-u9"
DATASET = "uk_energy_prod"

def ingest_remit(from_date, to_date):
    """Ingest REMIT messages from Elexon API"""

    url = "https://data.elexon.co.uk/bmrs/api/v1/datasets/REMIT/stream"
    params = {
        "publishDateTimeFrom": from_date.isoformat() + "Z",
        "publishDateTimeTo": to_date.isoformat() + "Z"
    }

    response = requests.get(url, params=params)
    data = response.json()

    # Upload to BigQuery table: bmrs_remit
    client = bigquery.Client(project=PROJECT_ID)
    table_id = f"{PROJECT_ID}.{DATASET}.bmrs_remit"

    job = client.load_table_from_json(
        data['data'],
        table_id,
        job_config=bigquery.LoadJobConfig(
            write_disposition="WRITE_APPEND",
            schema_update_options=["ALLOW_FIELD_ADDITION"]
        )
    )
    job.result()
    print(f"✅ Loaded {len(data['data'])} REMIT messages")

# Example: Ingest last 7 days
to_date = datetime.utcnow()
from_date = to_date - timedelta(days=7)
ingest_remit(from_date, to_date)
```

### Useful REMIT Queries

**Find current outages affecting batteries:**
```sql
SELECT
  assetId,
  participantId,
  eventType,
  unavailabilityType,
  availableCapacity,
  normalCapacity,
  eventStartTime,
  eventEndTime,
  fuelType
FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_remit`
WHERE fuelType LIKE '%Battery%'
  OR assetId LIKE '%BESS%'
  OR assetId LIKE '%BATT%'
  AND eventStatus = 'Active'
ORDER BY eventStartTime DESC
```

**Today's unplanned gas outages:**
```sql
SELECT
  assetId,
  participantId,
  availableCapacity,
  normalCapacity,
  (normalCapacity - availableCapacity) as unavailable_mw,
  eventStartTime,
  eventEndTime
FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_remit`
WHERE fuelType = 'Fossil Gas'
  AND unavailabilityType = 'Unplanned'
  AND DATE(eventStartTime) = CURRENT_DATE()
ORDER BY unavailable_mw DESC
```

---

## 2️⃣ Settlement Final Cashflows

### ❌ Different System - Not Currently Ingested

**Why We Don't Have It:**
- Different API (Elexon Settlement Portal, not BMRS)
- Massive delays (final settlement up to 28 months!)
- We have DISBSAD which is sufficient for BM revenue analysis

**Where to Access:**

**Elexon Settlement Portal:**
- URL: https://www.elexon.co.uk/settlement/
- Requires: Elexon Portal account
- Login: https://www.elexonportal.co.uk/

**Available Reports:**
- SAA-I014: Settlement Report Service (SRS)
- SAA-I028: Trading Dispute Reports
- SAA-I105: Initial Settlement Run
- SAA-R1: First Reconciliation Run (~14 days after)
- SAA-R2: Second Reconciliation (~28 days)
- SAA-R3: Third Reconciliation (~3 months)
- SAA-RF: Final Settlement (up to 28 months!)

**Settlement Runs Timeline:**
```
Settlement Period: 2025-12-18 SP36 (17:30-18:00)
  ↓
II (Initial): 2025-12-19 (next day)
  ↓
R1: 2026-01-01 (~14 days)
  ↓
R2: 2026-01-15 (~28 days)
  ↓
R3: 2026-03-18 (~3 months)
  ↓
RF (Final): 2027-04-18 (28 months!)
```

**Do We Need It?**
❌ **NO** - For battery/VLP BM revenue analysis:
- DISBSAD provides indicative settlement prices (~30 min lag)
- BOALF provides actual NESO payments (our enhanced table)
- Final settlement adjustments are tiny vs BM revenue
- Example: £56,829 BM payment vs £2 final settlement adjustment

**If You Really Want It:**
```bash
# Manual download from Elexon Portal
# 1. Login: https://www.elexonportal.co.uk/
# 2. Navigate: Reports → Settlement → SAA-I014
# 3. Select date range
# 4. Download CSV
# 5. Upload to BigQuery manually
```

---

## 3️⃣ Capacity Market Auctions

### ❌ Manual Download Only - Not Currently Ingested

**What Is Capacity Market:**
- Government scheme for supply security
- Pays generators/batteries to be **available** 4 years ahead
- Annual auctions (T-4, T-1) for future delivery years
- Revenue: £/kW/year (availability payment, not energy)

**Where to Access:**

**EMR Delivery Body (Official Source):**
- URL: https://www.emrdeliverybody.com/Capacity-Markets/Capacity-Market.aspx
- Auction Results: https://www.emrdeliverybody.com/CM/Auctions---Results.aspx

**Recent Auctions:**
```
T-4 Auction 2024 → Delivery Year 2028/29
  Clearing Price: £6.95/kW/year
  Total Capacity: 39.6 GW
  Download: T-4_CM_Auction_Results_2024.xlsx

T-1 Auction 2025 → Delivery Year 2026/27
  Clearing Price: £63/kW/year
  Total Capacity: 2.1 GW
  Download: T-1_CM_Auction_Results_2025.xlsx
```

**Available Data:**
- ✅ Auction clearing prices (aggregated)
- ✅ De-rated capacity by technology
- ✅ New build vs existing
- ❌ Individual unit agreements (confidential)
- ❌ Unit-level capacity payments (confidential)

**If You Want to Ingest:**
```bash
# Manual process:
# 1. Download Excel from EMR website
# 2. Convert to CSV
# 3. Upload to BigQuery

# Example table structure:
CREATE TABLE `inner-cinema-476211-u9.uk_energy_prod.capacity_market_auctions` (
  auction_type STRING,        -- T-4, T-1
  auction_date DATE,
  delivery_year STRING,       -- 2028/29
  clearing_price FLOAT64,     -- £/kW/year
  total_capacity_mw FLOAT64,
  technology STRING,          -- Battery, CCGT, OCGT, etc.
  new_build BOOL
);
```

**Do We Need It?**
⚠️ **MAYBE** - Useful for:
- Full battery business case analysis
- Investment modeling (revenue = BM + CM + other services)
- Comparing battery economics across delivery years

❌ **NOT** needed for:
- BM dispatch optimization (our current focus)
- Daily trading decisions
- Revenue tracking (CM is annual, not real-time)

---

## 4️⃣ Comparison: What We Have vs Don't Have

### ✅ Data We HAVE (Complete Coverage)

| Source | Coverage | Latency | Use Case |
|--------|----------|---------|----------|
| **BMRS Historical** | 72 datasets, 2020-present | 15-45 min | Historical analysis |
| **IRIS Real-time** | 9 critical streams | 2-3 min | Real-time dispatch |
| **REMIT** | ✅ Available in IRIS | 2-3 min | Outage tracking |
| **BOALF Enhanced** | BM acceptances + prices | ~30 min | Revenue calculation |
| **DISBSAD** | Settlement proxy | ~30 min | Price analysis |

### ❌ Data We DON'T Have

| Source | Why Not | Alternative |
|--------|---------|-------------|
| **Settlement Runs** | Different API, 28-month delay | Use DISBSAD (sufficient) |
| **Capacity Market** | Manual download, annual | Manual if needed |
| **REMIT (full)** | 10+ scattered platforms | BMRS PN data overlaps |

---

## 5️⃣ How to Add REMIT to Ingestion Pipeline

### Update iris_to_bigquery_unified.py

Add REMIT to TABLE_MAPPING:

```python
TABLE_MAPPING = {
    'FUELINST': 'bmrs_fuelinst_iris',
    'WINDFOR': 'bmrs_windfor_iris',
    'FREQ': 'bmrs_freq_iris',
    'MID': 'bmrs_mid_iris',
    'BOALF': 'bmrs_boalf_iris',
    'BOD': 'bmrs_bod_iris',
    'COSTS': 'bmrs_costs_iris',
    'INDGEN': 'bmrs_indgen_iris',
    'INDO': 'bmrs_indo_iris',
    'REMIT': 'bmrs_remit_iris',  # ← ADD THIS
}
```

REMIT messages will automatically flow through your existing IRIS pipeline:
1. Azure Service Bus → JSON files
2. iris_to_bigquery_unified.py processes them
3. Uploaded to `bmrs_remit_iris` table

### Create Historical REMIT Table

```bash
cd /home/george/GB-Power-Market-JJ
python3 << 'EOF'
from google.cloud import bigquery
import requests
from datetime import datetime, timedelta

PROJECT_ID = "inner-cinema-476211-u9"
DATASET = "uk_energy_prod"

client = bigquery.Client(project=PROJECT_ID, location="US")

# Ingest last 30 days of REMIT
end_date = datetime.utcnow()
start_date = end_date - timedelta(days=30)

url = "https://data.elexon.co.uk/bmrs/api/v1/datasets/REMIT/stream"
params = {
    "publishDateTimeFrom": start_date.isoformat() + "Z",
    "publishDateTimeTo": end_date.isoformat() + "Z"
}

print(f"Fetching REMIT data from {start_date.date()} to {end_date.date()}...")
response = requests.get(url, params=params)
data = response.json()

table_id = f"{PROJECT_ID}.{DATASET}.bmrs_remit"
job = client.load_table_from_json(
    data['data'],
    table_id,
    job_config=bigquery.LoadJobConfig(
        write_disposition="WRITE_APPEND",
        schema_update_options=["ALLOW_FIELD_ADDITION"],
        autodetect=True
    )
)
job.result()

print(f"✅ Loaded {len(data['data'])} REMIT messages to {table_id}")
EOF
```

---

## 6️⃣ GitHub Reference

**Elexon IRIS Clients:**
- Repository: https://github.com/elexon-data/iris-clients
- Python example: https://github.com/elexon-data/iris-clients/tree/main/python
- Documentation: https://bmrs.elexon.co.uk/api-documentation

**Your Implementation:**
- IRIS client: `/home/george/GB-Power-Market-JJ/iris-clients/python/client.py`
- Uploader: `/home/george/GB-Power-Market-JJ/iris_to_bigquery_unified.py`
- Config: `config.json` (contains your credentials)

---

## 📋 Action Items

### To Add REMIT:
- [ ] Update `TABLE_MAPPING` in `iris_to_bigquery_unified.py`
- [ ] Restart IRIS pipeline on AlmaLinux server
- [ ] Run historical backfill script (above)
- [ ] Verify data in `bmrs_remit_iris` table

### To Add Capacity Market (if needed):
- [ ] Download Excel from EMR website
- [ ] Create `capacity_market_auctions` table
- [ ] Upload CSV data
- [ ] Set reminder for next auction (annual)

### To Add Settlement (if really needed):
- [ ] Create Elexon Portal account
- [ ] Automate SAA-I014 report download
- [ ] Parse CSV and upload to BigQuery
- [ ] Set daily cron job

---

## 🎯 Recommendation

**Current Setup is Excellent:**
- ✅ All BMRS data (72 datasets)
- ✅ Critical real-time streams (9 IRIS topics)
- ✅ BM revenue data (BOALF + BOD + DISBSAD)

**Should Add:**
- ✅ REMIT (easy, just update TABLE_MAPPING)

**Can Skip:**
- ❌ Settlement Runs (DISBSAD sufficient, 28-month delays not useful)
- ⚠️ Capacity Market (manual download once/year if doing investment analysis)

---

**Last Updated:** December 18, 2025
**Next Review:** When adding REMIT ingestion or if Capacity Market data becomes critical

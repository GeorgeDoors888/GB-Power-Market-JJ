# Elexon API Endpoint Patterns Reference

**Last Updated:** December 18, 2025
**Discovery Context:** NETBSAD backfill resolution (see `NETBSAD_BACKFILL_INCIDENT_REPORT.md`)

---

## Summary

Not all Elexon BMRS API datasets use the same endpoint structure or parameter naming. This document catalogs the discovered patterns to prevent future "dataset deprecated" misdiagnoses.

---

## Endpoint Structures

### Pattern 1: Standard Dataset Endpoint
**Format:** `/datasets/{NAME}`
**Parameters:** `from`, `to` (RFC3339 timestamps with `Z` suffix)
**Response:** `{"data": [...], "metadata": {...}}`

**Datasets Using This Pattern:**
- `MID` (Market Index Data)
- `INDGEN` (Individual Generator Outturn)
- `INDDEM` (Individual Demand Outturn)
- `DISBSAD` (Disaggregated Balancing Services Adjustment Data)
- `FUELINST` (Fuel Type Instantaneous)
- `FREQ` (System Frequency)
- `TEMP` (Temperature)
- Most other BMRS datasets

**Example:**
```bash
GET /datasets/MID?from=2025-12-17T00:00:00Z&to=2025-12-17T23:59:59Z
```

---

### Pattern 2: Stream Endpoint
**Format:** `/datasets/{NAME}/stream`
**Parameters:** `from`, `to` (RFC3339 timestamps with `Z` suffix)
**Response:** `[{...}, {...}, ...]` (JSON array directly, **NOT** wrapped in `data` key)

**Datasets Requiring This Pattern:**
- `NETBSAD` (Net Balancing Services Adjustment Data) ⭐ **Critical**
- `PN` (Physical Notifications)
- `QPN` (Quiescent Physical Notifications)
- `MILS` (Market Index Level Snapshot)
- `MELS` (Market Energy Level Snapshot)
- `BOD` (Bid-Offer Data) - Uses `/stream` with additional `settlementPeriodFrom`/`settlementPeriodTo`

**Example:**
```bash
GET /datasets/NETBSAD/stream?from=2025-12-17T00:00:00Z&to=2025-12-17T23:59:59Z
```

**Response Structure Difference:**
```json
// Standard endpoint wraps data:
{"data": [{"dataset": "MID", ...}], "metadata": {...}}

// Stream endpoint returns array directly:
[{"dataset": "NETBSAD", ...}, {"dataset": "NETBSAD", ...}]
```

---

### Pattern 3: Legacy publishDateTime Parameters
**Format:** `/datasets/{NAME}`
**Parameters:** `publishDateTimeFrom`, `publishDateTimeTo` (ISO 8601 timestamps)
**Response:** `{"data": [...]}`

**Note:** This pattern is **deprecated** for most datasets. Use `from`/`to` instead.

**Historical Usage:**
- Some older BMRS endpoints (pre-2024 API redesign)
- May still work for backward compatibility on select datasets

**Example (legacy, avoid):**
```bash
GET /datasets/NETBSAD?publishDateTimeFrom=2025-12-17T00:00:00Z&publishDateTimeTo=2025-12-17T23:59:59Z
# Returns: 404 (endpoint not found)
```

---

## Parameter Naming Conventions

| Parameter | Used By | Format | Notes |
|-----------|---------|--------|-------|
| `from` | Standard, Stream | `YYYY-MM-DDTHH:MM:SSZ` | RFC3339 with trailing `Z` |
| `to` | Standard, Stream | `YYYY-MM-DDTHH:MM:SSZ` | RFC3339 with trailing `Z` |
| `publishDateTimeFrom` | Legacy | `YYYY-MM-DDTHH:MM:SSZ` | **Deprecated** - Use `from` |
| `publishDateTimeTo` | Legacy | `YYYY-MM-DDTHH:MM:SSZ` | **Deprecated** - Use `to` |
| `settlementDateFrom` | Some datasets | `YYYY-MM-DD` | Date-only filter |
| `settlementDateTo` | Some datasets | `YYYY-MM-DD` | Date-only filter |
| `settlementPeriodFrom` | BOD, others | `1` to `50` | SP filter (BOD requires this) |
| `settlementPeriodTo` | BOD, others | `1` to `50` | SP filter (BOD requires this) |
| `format` | All | `json` | Optional, defaults to JSON |
| `apiKey` | All (optional) | `string` | Optional API key for rate limits |

---

## BigQuery Ingestion Patterns

### Streaming Insert (insert_rows_json)
**Max Payload:** 10 MB per request
**Use For:** Small datasets (<10k records/day)

**Datasets Suitable for Streaming:**
- `NETBSAD` (48-50 records/day → ~5-10 KB/day) ✅
- `DISBSAD` (50-200 records/day) ✅
- `COSTS` (48 records/day) ✅
- `MID` (48 records/day) ✅
- `FREQ` (2,880 records/day → ~500 KB/day) ✅

**Example:**
```python
client.insert_rows_json(table_ref, records)
```

---

### Batch Load (load_table_from_json)
**Max Payload:** Unlimited (GB+ supported)
**Use For:** Large datasets (>10k records/day or >10 MB/request)

**Datasets Requiring Batch Load:**
- `PN` (9,644 records/hour × 24 = **231k records/day**) ⚠️ Too large for streaming
- `QPN` (similar volume to PN) ⚠️ Too large for streaming
- `INDGEN` (millions of records/day) ⚠️
- `INDDEM` (millions of records/day) ⚠️
- `BOD` (millions of records/day) ⚠️

**Example:**
```python
job = client.load_table_from_json(records, table_ref)
job.result()  # Wait for load to complete
```

**PN/QPN Payload Size Calculation:**
- 9,644 records/hour (tested Dec 17, 2025)
- × 24 hours = 231,456 records/day
- × 7 days/chunk = **1.6M records/week**
- Estimated size: **200-300 MB/week** (well over 10 MB streaming limit)

---

## Verification: METADATA Endpoint

**Always check METADATA first** before assuming a dataset is deprecated:

```bash
GET /datasets/METADATA/latest
```

**Note:** Endpoint name is case-sensitive - use **capital letters** `METADATA` (not `metadata`).

**Response:**
```json
[
  {"dataset": "NETBSAD", "lastUpdated": "2025-12-18T19:08:00Z"},
  {"dataset": "PN", "lastUpdated": "2025-12-18T19:12:00Z"},
  ...
]
```

If dataset appears in METADATA with recent `lastUpdated`, it's **actively publishing**. Check if it requires `/stream` suffix before marking as unavailable.

---

## Discovery Timeline (User-Driven Resolution)

### Initial Failure (Dec 18, 2025 19:18 UTC)
- **Symptom:** `/datasets/NETBSAD` returned HTTP 404 for all date ranges
- **Incorrect Diagnosis:** Agent assumed dataset deprecated or unavailable
- **Impact:** 51-day gap (Oct 29 - Dec 18) in NETBSAD data

### User Intervention (Dec 18, 2025 19:30 UTC)
User challenged deprecation claim with three diagnostic steps:

1. **Check METADATA endpoint** (capital letters):
   - Found: `{"dataset":"NETBSAD","lastUpdated":"2025-12-18T19:08:00Z"}`
   - **Conclusion:** NETBSAD actively publishing (not deprecated)

2. **Try explicit format parameter**:
   - Tested: `?format=json`
   - **Result:** Still 404, but prompted testing other endpoint variants

3. **Verify base URL matches current API definition**:
   - Base URL correct: `https://data.elexon.co.uk/bmrs/api/v1`
   - **Discovery:** Endpoint structure wrong, not base URL

### Resolution (Dec 18, 2025 19:50 UTC)
- **Correct Endpoint:** `/datasets/NETBSAD/stream` (not `/datasets/NETBSAD`)
- **Correct Parameters:** `from`/`to` (not `publishDateTimeFrom`/`publishDateTimeTo`)
- **Response Structure:** JSON array directly (not `{"data": [...]}`)
- **Result:** ✅ **2,072 records backfilled** across 51 days (100% coverage)

### Pattern Extension (Dec 18, 2025 20:15 UTC)
Tested other "unavailable" datasets with `/stream` suffix:

- **PN:** `/datasets/PN/stream` → ✅ HTTP 200 (231k records/day)
- **QPN:** `/datasets/QPN/stream` → ✅ HTTP 200 (similar volume)
- **DISBSAD:** `/datasets/DISBSAD` → ✅ HTTP 200 (standard endpoint works)

**Key Learning:** Some datasets require `/stream` suffix - **not clearly documented** in Elexon API specs.

---

## Auto-Ingestion Implementation

### ingest_elexon_fixed.py (Line 735)
**Updated:** December 18, 2025

```python
# Add datasets requiring /stream endpoint to this set:
if ds in {"MILS", "MELS", "PN", "QPN", "NETBSAD"}:
    # Script will try multiple endpoint variants:
    # 1. /datasets/{ds}
    # 2. /datasets/{ds}/stream  ✅ Correct for these datasets
    # 3. /datasets/{ds}/data
    # 4. Variants with settlementPeriod constraints
```

**Behavior:**
- Tries standard endpoint first (backwards compatibility)
- Falls back to `/stream` if standard returns 404/422
- Uses `from`/`to` parameters (RFC3339 with `Z` suffix)
- Handles both wrapped (`{"data": [...]}`) and unwrapped (`[...]`) responses

---

## Testing Commands

### Quick Dataset Test (1-hour window)
```bash
# Standard endpoint
curl "https://data.elexon.co.uk/bmrs/api/v1/datasets/MID?from=2025-12-17T00:00:00Z&to=2025-12-17T01:00:00Z"

# Stream endpoint
curl "https://data.elexon.co.uk/bmrs/api/v1/datasets/NETBSAD/stream?from=2025-12-17T00:00:00Z&to=2025-12-17T01:00:00Z"
```

### Check if Dataset Active
```bash
curl "https://data.elexon.co.uk/bmrs/api/v1/datasets/METADATA/latest" | grep -i "NETBSAD"
```

### Count Records (validate payload size)
```bash
curl "..." | python3 -c "import sys, json; data = json.load(sys.stdin); print(f'Records: {len(data if isinstance(data, list) else data.get(\"data\", [])):,}')"
```

---

## Troubleshooting Decision Tree

```
Dataset returns 404 or "not found"
│
├─ Step 1: Check METADATA endpoint (capital letters)
│  ├─ Dataset NOT listed → Genuinely deprecated/unavailable
│  └─ Dataset listed with recent lastUpdated → Continue to Step 2
│
├─ Step 2: Try /stream suffix
│  ├─ /datasets/{NAME}/stream returns 200 → ✅ Use /stream
│  └─ Still 404 → Continue to Step 3
│
├─ Step 3: Try standard endpoint with from/to
│  ├─ /datasets/{NAME}?from=...&to=... returns 200 → ✅ Use standard
│  └─ Still 404 → Continue to Step 4
│
└─ Step 4: Check parameter naming
   ├─ Try settlementDateFrom/To (date-only)
   ├─ Try publishDateTimeFrom/To (legacy)
   └─ If all fail → Contact Elexon support
```

---

## Common Mistakes to Avoid

### ❌ Wrong: Assume 404 = Deprecated
```python
# Bad assumption:
if response.status_code == 404:
    log("Dataset deprecated, skip backfill")
    return
```

### ✅ Correct: Check METADATA First
```python
# Good practice:
metadata = requests.get("/datasets/METADATA/latest").json()
if dataset not in [d["dataset"] for d in metadata]:
    log("Dataset genuinely unavailable")
else:
    log("Dataset active, try /stream variant")
```

### ❌ Wrong: Use publishDateTime for New Datasets
```python
# Deprecated parameter naming:
params = {
    "publishDateTimeFrom": "2025-12-17T00:00:00Z",
    "publishDateTimeTo": "2025-12-17T23:59:59Z"
}
```

### ✅ Correct: Use from/to for Modern API
```python
# Modern parameter naming:
params = {
    "from": "2025-12-17T00:00:00Z",
    "to": "2025-12-17T23:59:59Z"
}
```

### ❌ Wrong: Expect Consistent Response Structure
```python
# Assumes all endpoints wrap in "data":
records = response.json()["data"]  # Fails for /stream endpoints!
```

### ✅ Correct: Handle Both Wrapped and Unwrapped
```python
# Safe for both standard and /stream:
json_data = response.json()
records = json_data if isinstance(json_data, list) else json_data.get("data", [])
```

---

## Contact & Support

**Elexon API Support:**
- Email: support@elexon.co.uk
- Portal: https://www.elexonportal.co.uk/
- Developer Docs: https://www.elexon.co.uk/data/data-insights/

**Questions for Elexon:**
1. Why do some datasets require `/stream` suffix? (NETBSAD, PN, QPN)
2. Is there a schema/metadata endpoint listing which datasets use which pattern?
3. Will `/stream` pattern be documented in official API specs?

---

## Related Documentation

- `NETBSAD_BACKFILL_INCIDENT_REPORT.md` - Full incident report with resolution timeline
- `STOP_DATA_ARCHITECTURE_REFERENCE.md` - Overall data architecture reference
- `ingest_elexon_fixed.py` - Auto-ingestion script (line 735 for /stream handling)
- `backfill_bmrs_netbsad.py` - NETBSAD backfill script (reference implementation)

---

**Credit:** Resolution driven by user's evidence-based diagnostic approach. Checking METADATA endpoint first prevented wasted time assuming deprecation.

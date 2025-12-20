# BOALF API Reference - Bid-Offer Acceptances

**Last Updated:** December 18, 2025

---

## Overview

**BOALF** = **B**id-**O**ffer **A**cceptance **L**evel **F**lagged

- **Elexon Data Stream**: B1610
- **Purpose**: Records which bid-offer submissions NESO accepted in the Balancing Mechanism
- **Endpoint**: `/balancing/acceptances`

---

## Elexon API Endpoint

### GET /balancing/acceptances

**Description**: Provides bid-offer acceptance data (BOALF) for a requested BMU.

### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `bmUnit` | string | ✅ Yes | The BM Unit to query (e.g., `T_MILWW-1`) |
| `from` | datetime | ✅ Yes | Start time or settlement date (RFC 3339 format) |
| `to` | datetime | ✅ Yes | End time or settlement date (RFC 3339 format) |
| `settlementPeriodFrom` | int | ❌ No | Settlement period filter (1-50) |
| `settlementPeriodTo` | int | ❌ No | Settlement period filter (1-50) |
| `format` | string | ❌ No | Response format: `json`, `xml`, or `csv` |

### Example Requests

**1. Filter by start time:**
```
GET /balancing/acceptances?bmUnit=T_DAMC-1&from=2022-06-01T00:00Z&to=2022-07-01T00:00Z
```

**2. Filter by settlement date and period:**
```
GET /balancing/acceptances?from=2022-06-01T00:00Z&to=2022-07-01T00:00Z&settlementPeriodFrom=1&settlementPeriodTo=50
```

---

## Response Schema

### Fields Provided by Elexon API

```json
{
  "data": [
    {
      "settlementDate": "2022-06-25",
      "settlementPeriodFrom": 29,
      "settlementPeriodTo": 32,
      "timeFrom": "2022-06-25T13:34:00Z",
      "timeTo": "2022-06-25T13:37:00Z",
      "levelFrom": 5,
      "levelTo": 46,
      "nationalGridBmUnit": "ABRBO-1",
      "bmUnit": "T_ABRBO-1",
      "acceptanceNumber": 1234567,
      "acceptanceTime": "2022-06-25T13:30:00Z",
      "deemedBoFlag": true,
      "soFlag": false,
      "storFlag": true,
      "rrFlag": false
    }
  ]
}
```

### Field Descriptions

| Field | Type | Description |
|-------|------|-------------|
| `settlementDate` | Date | Settlement date (YYYY-MM-DD) |
| `settlementPeriodFrom` | Integer | Starting settlement period (1-50) |
| `settlementPeriodTo` | Integer | Ending settlement period (1-50) |
| `timeFrom` | DateTime | Start time of acceptance (UTC) |
| `timeTo` | DateTime | End time of acceptance (UTC) |
| `levelFrom` | Integer | BOD pair ID start level |
| `levelTo` | Integer | BOD pair ID end level |
| `nationalGridBmUnit` | String | NESO BM Unit ID |
| `bmUnit` | String | Elexon BM Unit ID (with `T_` prefix) |
| `acceptanceNumber` | Integer | Unique acceptance identifier |
| `acceptanceTime` | DateTime | When NESO accepted the action (UTC) |
| `deemedBoFlag` | Boolean | Deemed bid-offer flag |
| `soFlag` | Boolean | System Operator flag |
| `storFlag` | Boolean | Short-term operating reserve flag |
| `rrFlag` | Boolean | Replacement reserve flag |

---

## ⚠️ CRITICAL: Missing Fields

**Elexon BOALF API does NOT provide:**

❌ **acceptancePrice** (£/MWh) - The price NESO paid
❌ **acceptanceVolume** (MWh) - The volume accepted
❌ **acceptanceType** (BID/OFFER) - Direction of action

### Why This Matters

Without price and volume, you **cannot calculate revenue** from BOALF alone!

**Example:**
- BOALF tells you: "Acceptance #1234567 at 13:30 for T_DAMC-1"
- BOALF does NOT tell you: "£997/MWh × 57 MWh = £56,829 revenue"

---

## Our Enhanced Data: boalf_with_prices

To get actual revenue data, we created `boalf_with_prices` table by:

### Data Enrichment Process

1. **Fetch BOALF from Elexon API** → Get acceptance records
2. **Fetch BOD (Bid-Offer Data)** → Get submitted prices
3. **Match BOALF ↔ BOD** → Join on bmUnit, time, level
4. **Derive missing fields:**
   - `acceptancePrice` = matched BOD offer/bid price
   - `acceptanceVolume` = matched BOD volume
   - `acceptanceType` = OFFER (reduce) or BID (increase)
5. **Calculate revenue** = price × volume
6. **Apply validation** = Elexon B1610 filters

### Match Rate

- **85-95%** of BOALF records successfully match to BOD
- Varies by month and market conditions
- Invalid matches filtered via `validation_flag='Valid'`

### Enhanced Schema

```sql
CREATE TABLE boalf_with_prices AS
SELECT
    -- Original BOALF fields
    b.bmUnit,
    b.acceptanceNumber,
    b.acceptanceTime,
    b.settlementDate,
    b.settlementPeriod,

    -- Derived from BOD matching
    bod.offer AS acceptancePrice,        -- ✅ NOT in Elexon API
    bod.volume AS acceptanceVolume,       -- ✅ NOT in Elexon API
    CASE
        WHEN bod.offer IS NOT NULL THEN 'OFFER'
        WHEN bod.bid IS NOT NULL THEN 'BID'
    END AS acceptanceType,                -- ✅ NOT in Elexon API

    -- Calculated fields
    bod.offer * bod.volume AS revenue_estimate_gbp,  -- ✅ Our calculation

    -- Validation
    CASE
        WHEN passes_b1610_filters THEN 'Valid'
        ELSE 'Invalid'
    END AS validation_flag                -- ✅ Our quality filter
FROM bmrs_boalf b
LEFT JOIN bmrs_bod bod
    ON b.bmUnit = bod.bmUnit
    AND b.acceptanceTime = bod.timeFrom
    AND b.levelFrom = bod.pairId
```

---

## Usage Examples

### Query BOALF (Elexon API - Raw Data)

```python
import requests

url = "https://api.bmreports.com/BMRS/balancing/acceptances"
params = {
    "bmUnit": "T_DAMC-1",
    "from": "2025-10-22T00:00Z",
    "to": "2025-10-22T23:59Z",
    "format": "json"
}

response = requests.get(url, params=params)
data = response.json()

# You get: acceptance numbers, times, flags
# You DON'T get: prices, volumes, revenue
```

### Query boalf_with_prices (Our Enhanced Data)

```python
from google.cloud import bigquery

client = bigquery.Client(project="inner-cinema-476211-u9")

query = """
SELECT
    bmUnit,
    acceptanceTime,
    acceptanceType,
    acceptancePrice,
    acceptanceVolume,
    revenue_estimate_gbp
FROM `inner-cinema-476211-u9.uk_energy_prod.boalf_with_prices`
WHERE bmUnit = 'T_DAMC-1'
  AND DATE(acceptanceTime) = '2025-10-22'
  AND validation_flag = 'Valid'
ORDER BY acceptancePrice DESC
"""

df = client.query(query).to_dataframe()

# You get: prices, volumes, revenue, types
# PLUS original BOALF fields
```

---

## Real-World Example

### BOALF API Response (What You Get)

```json
{
  "bmUnit": "T_DAMC-1",
  "acceptanceNumber": 7891234,
  "acceptanceTime": "2025-10-22T17:31:00Z",
  "levelFrom": 5,
  "levelTo": 5,
  "soFlag": true
}
```

**Analysis**: You know NESO accepted SOMETHING from T_DAMC-1 at 17:31, but you don't know:
- Was it a BID or OFFER?
- What price?
- How many MWh?
- What's the revenue?

### boalf_with_prices Response (What You Need)

```json
{
  "bmUnit": "T_DAMC-1",
  "acceptanceNumber": 7891234,
  "acceptanceTime": "2025-10-22T17:31:00Z",
  "acceptanceType": "OFFER",
  "acceptancePrice": 997.0,
  "acceptanceVolume": 57.0,
  "revenue_estimate_gbp": 56829.0,
  "validation_flag": "Valid"
}
```

**Analysis**: T_DAMC-1 got paid **£997/MWh** to reduce output by **57 MWh** = **£56,829 revenue** ✅

---

## Data Coverage

### Our Database Stats

- **Total BOALF Records**: 11.3M (2022-2025)
- **Records with Prices**: ~4.7M (42.8% - Valid matches only)
- **Total Revenue Tracked**: £6.85 billion
- **Top Earner**: T_DINO-5 (£363M all-time)

### Date Ranges

- **Historical**: 2022-01-01 to 2025-12-17
- **Real-time**: Last 24-48h via IRIS stream
- **Update Frequency**: 15-minute batches

---

## VLP/Battery Revenue Calculation

### Correct Formula

```
Total VLP Revenue = NESO Payment ± SCRP Compensation

Where:
  NESO Payment = acceptancePrice × acceptanceVolume (from boalf_with_prices)
  SCRP = £98/MWh (Supplier Compensation Reference Price)

For OFFER (reduce output):
  Revenue = (acceptancePrice × acceptanceVolume) - (volume × SCRP)
  Example: (£997 × 57 MWh) - (57 × £98) = £56,829 - £5,586 = £51,243

For BID (increase output):
  Revenue = (acceptancePrice × acceptanceVolume) + (volume × SCRP)
  Example: (£50 × 57 MWh) + (57 × £98) = £2,850 + £5,586 = £8,436
```

### Why SCRP Matters

From Elexon BSC Section T1.16:
- VLPs must compensate suppliers for disrupting their hedges
- SCRP is based on Ofgem Price Cap (includes DUoS, TNUoS, levies)
- Payment flows DIRECTLY between VLP and affected supplier

---

## Common Mistakes

### ❌ WRONG: Using BOALF API Alone

```python
# This gives you acceptances but NO revenue calculation
boalf = get_elexon_boalf("T_DAMC-1", "2025-10-22")
# Missing: prices, volumes, revenue ❌
```

### ❌ WRONG: Using bmrs_boalf Table Alone

```sql
-- This table also lacks price/volume!
SELECT * FROM bmrs_boalf WHERE bmUnit = 'T_DAMC-1'
-- Has: acceptanceNumber, acceptanceTime
-- Missing: acceptancePrice, acceptanceVolume ❌
```

### ✅ CORRECT: Using boalf_with_prices

```sql
-- This has everything you need
SELECT
    bmUnit,
    acceptanceTime,
    acceptanceType,
    acceptancePrice,
    acceptanceVolume,
    revenue_estimate_gbp
FROM boalf_with_prices
WHERE bmUnit = 'T_DAMC-1'
  AND validation_flag = 'Valid'  -- Only use matched records
```

---

## Related Documentation

- `bmrs_bod` - Submitted bid-offer prices (391M rows)
- `bmrs_boalf` - Raw acceptance records (11.3M rows, NO PRICES)
- `boalf_with_prices` - Enhanced with prices (4.7M valid, WITH PRICES)
- `bmrs_disbsad` - Settlement cashflows (volume-weighted avg)
- `bmrs_costs` - System imbalance prices (SBP/SSP)

---

## API Reference Links

- **Elexon Portal**: https://www.elexonportal.co.uk/
- **API Documentation**: https://developer.data.elexon.co.uk/
- **BOALF Endpoint**: `/balancing/acceptances`
- **BOD Endpoint**: `/balancing/bod`

---

**Last Updated:** December 18, 2025
**Maintained By:** George Major (george@upowerenergy.uk)

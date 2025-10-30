# Market Index Data (MID) Prices Integration

**Created:** 29 October 2025  
**Status:** ✅ Operational  
**Dashboard Cells:** A10 (N2EX), A11 (EPEX SPOT)

---

## Overview

Successfully integrated **Market Index Data (MID)** prices into the UK Power Generation Dashboard. This data shows real-time wholesale electricity prices from two appointed Market Index Data Providers (MIDPs) and is used by National Grid ESO to calculate System Buy Price (SBP) and System Sell Price (SSP).

### What is MID?

Market Index Price data reflects the price of wholesale electricity in Great Britain for each Settlement Period (30 minutes) in the short-term markets. It's a key component in determining balancing settlement prices.

---

## Data Providers

### 1. **N2EX (N2EXMIDP)** - Cell A10
- **Provider:** NASDAQ OMX Stockholm AB
- **Market:** UK Day-Ahead and Intra-Day
- **Current Status:** Often shows £0.00/MWh (below ILT threshold)
- **Normal Behavior:** Low liquidity periods result in zero prices per MIDS

### 2. **APX/EPEX SPOT (APXMIDP)** - Cell A11
- **Provider:** EPEX SPOT SE (formerly APX)
- **Market:** European Power Exchange - UK hub
- **Current Status:** Active pricing (e.g., £21.71/MWh with 2,216 MWh volume)
- **Typical Range:** £15-120/MWh depending on demand

---

## Current Implementation

### Dashboard Display

**A10 - N2EX:**
```
💷 N2EX: Below ILT threshold
```
*or when active:*
```
💷 N2EX: £45.23/MWh (1,234 MWh)
```

**A11 - EPEX SPOT:**
```
💶 EPEX SPOT: £21.71/MWh (2,216 MWh)
```

### Data Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                     MID PRICES DATA FLOW                         │
└─────────────────────────────────────────────────────────────────┘

1. BMRS API Endpoint:
   └─ GET /balancing/pricing/market-index
      ├─ N2EXMIDP (NASDAQ OMX)
      └─ APXMIDP (EPEX SPOT)

2. Real-time Ingestion (every 5 minutes):
   └─ realtime_updater.py
      └─ ingest_elexon_fixed.py --only FUELINST,WIND_SOLAR_GEN,MID
         └─ Writes to: uk_energy_prod.bmrs_mid

3. BigQuery Table: bmrs_mid
   ├─ settlementDate (DATETIME)
   ├─ settlementPeriod (INT64) - 1 to 50
   ├─ dataProvider (STRING) - N2EXMIDP or APXMIDP
   ├─ price (FLOAT64) - £/MWh
   ├─ volume (FLOAT64) - MWh traded
   └─ startTime (DATETIME) - Period start time

4. Dashboard Update:
   └─ dashboard_updater_complete.py
      └─ get_latest_mid_prices()
         ├─ Query latest MID data
         ├─ Update A10 (N2EX)
         └─ Update A11 (EPEX SPOT)
```

---

## API Details

### Endpoint
```
GET https://data.elexon.co.uk/bmrs/api/v1/balancing/pricing/market-index
```

### Parameters
- **from** (required): Start time or settlement date (RFC 3339)
- **to** (required): End time or settlement date
- **settlementPeriodFrom** (optional): 1-50
- **settlementPeriodTo** (optional): 1-50
- **dataProviders** (optional): ["N2EXMIDP", "APXMIDP"]
- **format** (optional): json, xml, csv

### Example Response
```json
{
  "data": [
    {
      "startTime": "2025-10-29T12:00:00Z",
      "dataProvider": "APXMIDP",
      "settlementDate": "2025-10-29",
      "settlementPeriod": 25,
      "price": 21.71,
      "volume": 2216.0
    }
  ]
}
```

---

## Understanding the Data

### Insufficient Liquidity Threshold (ILT)

When traded volume falls below the ILT, the MID defaults to £0.00 per the **Market Index Definition Statement (MIDS)**. This is **normal behavior**, not a data error.

**Why N2EX often shows £0.00:**
- Lower market share in UK compared to EPEX SPOT
- Fewer qualifying products traded
- ILT threshold breached frequently
- Market consolidation toward EPEX SPOT

### Price Ranges (EPEX SPOT)

| Time Period | Typical Price | Notes |
|-------------|---------------|-------|
| Night (00:00-06:00) | £15-30/MWh | Low demand |
| Morning ramp (06:00-09:00) | £40-70/MWh | Demand increasing |
| Peak (09:00-18:00) | £50-100/MWh | Business hours |
| Evening peak (17:00-20:00) | £70-120/MWh | Highest prices |
| Night valley (20:00-24:00) | £20-50/MWh | Demand falling |

---

## Verification

### Check Current Prices
```bash
.venv/bin/python realtime_updater.py --check-only
```

**Expected Output:**
```
💷 MID (Market Index Data) status:
   APXMIDP: £21.71/MWh (2216 MWh)
   N2EXMIDP: £0.00/MWh (0 MWh)
```

### View Dashboard
https://docs.google.com/spreadsheets/d/12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8

---

## Performance Metrics

| Metric | Value | Status |
|--------|-------|--------|
| **Latest APXMIDP** | £21.71/MWh | ✅ Active |
| **Latest N2EXMIDP** | £0.00/MWh | ⚠️ Below ILT (normal) |
| **Update Frequency** | Every 5 minutes | ✅ Operational |
| **Dashboard Cells** | 31 total | ✅ Working |

---

**Last Updated:** 29 October 2025, 15:10 GMT  
**Status:** ✅ Fully Operational

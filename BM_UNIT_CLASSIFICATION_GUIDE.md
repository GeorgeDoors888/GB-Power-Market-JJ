# BM Unit Classification Guide

**Date:** 16 December 2025  
**Dataset:** `inner-cinema-476211-u9.uk_energy_prod`

---

## ⚙️ Understanding BM Units

A **BM Unit** (bmUnitID) is the unique identifier Elexon gives each controllable asset in the Balancing Mechanism.

They're defined in the **Balancing Mechanism Unit Register (BMU Register)** — which lists:

| Field | Description |
|-------|-------------|
| **BM Unit ID** | Unique ID (e.g., T_MRWD-1, 2__FBPGM001) |
| **Fuel Type** | Gas, Wind, Battery, Hydro, etc. |
| **Lead Party** | Company owning the asset (e.g., Drax Power Ltd, Flexitricity) |
| **Grid Supply Point** | Connection node |
| **BMU Type** | Genset, Storage, Demand, etc. |

### Data Sources

**Official Register:**  
https://www.elexon.co.uk/operations-settlement/balancing-mechanism-units/bmu-register/

**BigQuery Lookup:**
```sql
SELECT DISTINCT bmUnitID, fuelType, leadPartyName
FROM `inner-cinema-476211-u9.uk_energy_prod.bm_unit_register`;
```

---

## 🔍 BM Unit ID Classification

You can classify BM Units directly from the ID pattern or via your lookup table:

| Prefix / Pattern | Likely Technology | Example | Behaviour |
|------------------|-------------------|---------|-----------|
| **T_** | Transmission-connected conventional generator | T_MRWD-1 | Gas, Coal, Nuclear |
| **2__** | Virtual Lead Party (VLP) / DER / Battery | 2__FBPGM001 | Battery or DSR asset |
| **B_** | Embedded BM Unit | B_NATPW1 | Wind or solar farm |
| **C_** | Interconnector | C_EWIC | Import/export |
| **D_** | Demand BM Unit | D_GB123 | Large consumer load |
| **E_** | Embedded generator | E_SKELB-1 | Wind, solar (embedded) |
| **I_** | Interconnector (alternate) | I_IFD-PEAK1 | Cross-border links |
| **V__** | Virtual unit | V__GHABI001 | Aggregated DER/DSR |

### Example Classification

**2__FBPGM001**:
- Prefix `2__` → Virtual Lead Party (Flexitricity, Zenobe, GridBeyond, etc.)
- → Battery / Demand Response asset, **NOT a gas generator**

---

## ⚡ Economic Interpretation of Bid/Offer Prices

| Case | What It Means | Who Pays Whom | Typical Tech |
|------|---------------|---------------|--------------|
| **Offer (> 0)** | Generator offers to increase generation (sells power to ESO) | ESO pays the generator | Gas, Coal, Battery Discharge |
| **Bid (< 0)** | Generator bids to reduce generation (pays ESO to be turned down) | Generator pays ESO | Gas CCGT, Wind, Battery Charge |
| **Bid = 0** | Free balancing energy (constraint or non-commercial) | No cash flow | Wind curtailment, batteries at zero |
| **Bid negative, large magnitude (e.g., -1000)** | Very strong incentive to be curtailed (keep other revenue streams) | Generator pays ESO heavily | Wind under CfD, nuclear constraint |

---

## 📊 Real-World Examples

### Example 1 – Gas Generator

**Unit Details:**
- `bmUnitID`: T_DIDC-1
- `bid`: -70 £/MWh
- `offer`: 100 £/MWh

**Interpretation:**
- Generator **pays ESO £70/MWh to reduce generation**
- **Why?** They keep their gas purchase contract (take-or-pay) and electricity receipts (hedged or forward-sold)
- ESO compensates system by reducing generation elsewhere

✅ **Typical for gas CCGT plants with fixed fuel supply**

---

### Example 2 – Battery Unit

**Unit Details:**
- `bmUnitID`: 2__FBPGM001
- `bid`: -10 £/MWh
- `offer`: 75 £/MWh

**Interpretation:**
- **Bid (charging)**: Battery pays ESO £10/MWh to absorb excess energy (charging)
- **Offer (discharging)**: Battery paid £75/MWh to supply power during shortage

✅ **Typical arbitrage behaviour**

---

### Example 3 – Wind Farm Under CfD

**Unit Details:**
- `bmUnitID`: T_MRWD-1
- `bid`: -999 £/MWh
- `offer`: N/A

**Interpretation:**
- Wind farm **pays ESO nearly £1000/MWh to be turned off**
- **Why?** Still gets CfD "strike price" payments, so prefers curtailment

✅ **"Negative bid" represents lost revenue protection**

---

## 🧮 Automatic Classification in SQL

If you already have the BMU register table (or a fuelType lookup), you can create a simple classifier:

```sql
SELECT
  bmUnit,
  CASE
    WHEN bmUnit LIKE '2__%' THEN 'Battery/DER'
    WHEN bmUnit LIKE 'T_%' THEN 'Conventional Generator'
    WHEN bmUnit LIKE 'B_%' THEN 'Embedded Renewable'
    WHEN bmUnit LIKE 'E_%' THEN 'Embedded Generator'
    WHEN bmUnit LIKE 'C_%' OR bmUnit LIKE 'I_%' THEN 'Interconnector'
    WHEN bmUnit LIKE 'V__%' THEN 'Virtual Unit'
    WHEN bmUnit LIKE 'D_%' THEN 'Demand'
    ELSE 'Other'
  END AS tech_category,
  AVG(offer) AS avg_offer,
  AVG(bid) AS avg_bid,
  COUNT(*) as total_records
FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_bod`
WHERE DATE(settlementDate) >= '2025-01-01'
GROUP BY bmUnit, tech_category
ORDER BY tech_category, total_records DESC;
```

---

## 🔋 Financial Flow Summary

| Tech | Action | Bid/Offer Sign | Who Pays | Why |
|------|--------|----------------|----------|-----|
| **Gas** | Reduce gen | Negative bid | Generator → ESO | Avoid over-generation, keep fuel receipts |
| **Gas** | Increase gen | Positive offer | ESO → Generator | Provide extra generation |
| **Battery** | Charge | Negative bid | Battery → ESO | Arbitrage, absorb excess power |
| **Battery** | Discharge | Positive offer | ESO → Battery | Supply during shortage |
| **Wind** | Curtail | Very negative bid | Wind → ESO | Still receives CfD payment |

---

## ✅ Summary Table for 2__FBPGM001

| Field | Value | Interpretation |
|-------|-------|----------------|
| **bmUnitID** | 2__FBPGM001 | VLP asset, almost certainly a battery |
| **bid** | Negative | Pays ESO to charge (absorbing energy) |
| **offer** | Positive | Paid by ESO to discharge (supply energy) |
| **fuelType** | Storage / DER | From BMU register |
| **Behaviour** | Arbitrage between grid imbalance prices | Battery pattern |

---

## 📊 Elexon B1610 - Actual Generation Output

**API Endpoint:** `/datasets/B1610`

Provides the actual metered volume output (MWh) per Settlement Period for all BM units (Positive, Negative or zero MWh values).

**Key Points:**
- Returns **metered volume** (MWh), not instantaneous power (MW)
- Published 5 days after operational period (Interim Information Settlement Run)
- Updated by subsequent Settlement Runs

**Example Query:**
```bash
GET /datasets/B1610?settlementDate=2022-08-12&settlementPeriod=10&bmUnit=T_CNQPS-1
```

**Response:**
```json
{
  "data": [
    {
      "dataset": "B1610",
      "psrType": "Generation",
      "bmUnit": "T_CNQPS-1",
      "nationalGridBmUnitId": "CNQPS-1",
      "settlementDate": "2022-08-12",
      "settlementPeriod": 10,
      "halfHourEndTime": "2022-08-12T04:00:00Z",
      "quantity": 116.109
    }
  ]
}
```

---

## 📚 References

- **Elexon BM Unit Register**: https://www.elexon.co.uk/operations-settlement/balancing-mechanism-units/bmu-register/
- **B1610 Validation Rules**: Elexon Data Validation Ruleset
- **CfD Explained**: LCCC CfD Generator Handbook
- **BMRS API Documentation**: https://developer.data.elexon.co.uk/

---

## 🔧 BigQuery Enrichment Query

To automatically join `bmrs_bod` or `bmrs_boalf_complete` with BM Unit → fuelType lookup:

```sql
WITH bmu_classified AS (
  SELECT
    bmUnit,
    CASE
      WHEN bmUnit LIKE '2__%' THEN 'Battery/DER'
      WHEN bmUnit LIKE 'T_%' THEN 'Conventional Generator'
      WHEN bmUnit LIKE 'B_%' OR bmUnit LIKE 'E_%' THEN 'Embedded Renewable'
      WHEN bmUnit LIKE 'C_%' OR bmUnit LIKE 'I_%' THEN 'Interconnector'
      WHEN bmUnit LIKE 'V__%' THEN 'Virtual Unit'
      ELSE 'Other'
    END AS tech_category
  FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_boalf_complete`
  GROUP BY bmUnit
)

SELECT 
  boalf.*,
  bmu.tech_category,
  CASE 
    WHEN boalf.acceptanceType = 'OFFER' AND boalf.acceptancePrice > 0 
      THEN 'Revenue (ESO → Generator)'
    WHEN boalf.acceptanceType = 'BID' AND boalf.acceptancePrice < 0 
      THEN 'Cost (Generator → ESO)'
    WHEN boalf.acceptanceType = 'BID' AND boalf.acceptancePrice > 0 
      THEN 'Revenue (ESO → Generator for reducing)'
    ELSE 'Other'
  END AS payment_direction

FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_boalf_complete` boalf
LEFT JOIN bmu_classified bmu
  ON boalf.bmUnit = bmu.bmUnit

WHERE boalf.validation_flag = 'Valid'
  AND DATE(boalf.settlementDate) >= '2025-10-01'

ORDER BY boalf.settlementDate, boalf.bmUnit
LIMIT 1000;
```

---

**Last Updated:** 16 December 2025  
**Maintainer:** George Major (george@upowerenergy.uk)

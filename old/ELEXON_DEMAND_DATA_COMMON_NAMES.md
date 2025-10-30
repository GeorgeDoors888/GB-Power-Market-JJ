# ELEXON Demand Data - Common Names

## 🎯 **Quick Answer**

The most common name for demand data in ELEXON is **"System Demand"** which refers to the **ITSDO** dataset.

## 📊 **Primary ELEXON Demand Datasets**

| Common Name                | ELEXON Code | Full Name                                  | Table Name   |
| -------------------------- | ----------- | ------------------------------------------ | ------------ |
| **System Demand**          | **ITSDO**   | Indicative Total System Demand Outturn     | `bmrs_itsdo` |
| **Demand Forecast**        | **TSDF**    | Transmission System Demand Forecast        | `bmrs_tsdf`  |
| **Weekly Demand Forecast** | **TSDFW**   | Transmission System Demand Forecast Weekly | `bmrs_tsdfw` |
| **Daily Demand Forecast**  | **TSDFD**   | Transmission System Demand Forecast Daily  | `bmrs_tsdfd` |

## 🔍 **Most Used: ITSDO (System Demand)**

**ITSDO** is the **most common demand dataset** in ELEXON:
- **Purpose:** Actual electricity demand on GB transmission system
- **Common Names:** "System Demand", "Demand Outturn", "Actual Demand"
- **Data:** Historical actual demand values
- **Frequency:** 30-minute settlement periods
- **Units:** Megawatts (MW)
- **Table:** `bmrs_itsdo`

## 💡 **Common Industry Terms**

People in the industry typically refer to ELEXON demand data as:

1. **"System Demand"** (most common)
2. **"Demand Outturn"**
3. **"Transmission Demand"**
4. **"ITSDO data"**
5. **"Settlement demand"**

## 🔗 **How to Access**

### BigQuery Table Names:
```sql
-- Actual demand (most common)
SELECT * FROM `jibber-jabber-knowledge.uk_energy_insights.bmrs_itsdo`;

-- Demand forecasts
SELECT * FROM `jibber-jabber-knowledge.uk_energy_insights.bmrs_tsdf`;
```

### Key Fields:
- **`demand`** - Demand value in MW
- **`settlementDate`** - Date of settlement period
- **`settlementPeriod`** - 30-minute period (1-48 per day)

## 📈 **Sample Data Structure**

| settlementDate | settlementPeriod | demand (MW) | Description         |
| -------------- | ---------------- | ----------- | ------------------- |
| 2025-09-09     | 20               | 26,054      | Evening peak demand |
| 2025-09-09     | 16               | 29,032      | Afternoon demand    |
| 2025-09-08     | 25               | 22,735      | Late evening demand |

## ✅ **Summary**

**Answer:** The common name for demand data in ELEXON is **"System Demand"** (ITSDO dataset), which contains actual electricity demand on the GB transmission system in 30-minute intervals.

# 📊 BigQuery Schema - UK Energy Data for VLP Analysis

**Project**: `inner-cinema-476211-u9`  
**Dataset**: `uk_energy_prod`  
**Last Updated**: 2025-11-09

---

## 🎯 Tables Overview

Your BigQuery dataset contains **50+ tables** from BMRS (Balancing Mechanism Reporting Service).

### Key Tables for VLP (Virtual Lead Participant):

| Priority | Table | Description | VLP Use Case |
|----------|-------|-------------|--------------|
| ⭐⭐⭐ | `bmrs_mid` | Market Index Data (System prices) | **Price signals** for arbitrage decisions |
| ⭐⭐⭐ | `bmrs_bod` | Bid-Offer Data | **Bid/offer prices** - core arbitrage opportunity detection |
| ⭐⭐⭐ | `bmrs_b1610` | Actual Generation by Fuel Type | **System mix** - predict price movements |
| ⭐⭐ | `bmrs_detsysprices` | Detailed System Prices (SSP/SBP) | **Spread analysis** - imbalance profitability |
| ⭐⭐ | `bmrs_netbsad` | Net Imbalance Volume | **Imbalance volume** - market direction signals |
| ⭐⭐ | `bmrs_indgen_iris` | Individual Generator Data | **Asset performance** - your units' output |
| ⭐⭐ | `bmrs_fuelinst_iris` | Fuel Mix Instant | **Real-time mix** - immediate price drivers |
| ⭐ | `bmrs_remit_unavailability` | Unit Unavailability | **Capacity constraints** - supply tightness signals |
| ⭐ | `bmrs_freq` | System Frequency | **Balancing stress** - emergency dispatch indicators |
| ⭐ | `bmrs_surplus_margin` | Surplus Forecast | **Capacity margins** - scarcity pricing risk |

---

## 📋 Detailed Schema by Table

### 1. **bmrs_mid** - Market Index Data (System Prices)
**Rows**: 155,405  
**Use**: Primary price signals for arbitrage and dispatch decisions

| Column | Type | Description | VLP Usage |
|--------|------|-------------|-----------|
| `settlementDate` | DATETIME | Settlement date | Time dimension |
| `settlementPeriod` | INT64 | Period 1-48 (half-hour) | Intraday patterns |
| `price` | FLOAT64 | Market Index Price (£/MWh) | ⭐ **Core arbitrage signal** |
| `volume` | FLOAT64 | Volume traded (MWh) | Liquidity indicator |
| `startTime` | DATETIME | Period start | Precise timing |
| `dataProvider` | STRING | Data source | Quality check |

**VLP Queries:**
```sql
-- Identify high-price periods for discharge
SELECT settlementDate, settlementPeriod, price
FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_mid`
WHERE price > 100  -- £100/MWh threshold
ORDER BY price DESC LIMIT 100;

-- Daily price volatility (arbitrage opportunity indicator)
SELECT 
  DATE(settlementDate) as date,
  AVG(price) as avg_price,
  STDDEV(price) as volatility,
  MAX(price) - MIN(price) as daily_spread
FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_mid`
GROUP BY DATE(settlementDate)
ORDER BY volatility DESC;
```

---

### 2. **bmrs_bod** - Bid-Offer Data
**Use**: Actual accepted bids/offers - direct arbitrage opportunities

| Column | Type | Description | VLP Usage |
|--------|------|-------------|-----------|
| `settlementDate` | DATETIME | Settlement date | Time key |
| `settlementPeriod` | INT64 | Period 1-48 | Timing |
| `timeFrom` | DATETIME | Bid validity start | Window start |
| `timeTo` | DATETIME | Bid validity end | Window end |
| `levelFrom` | INT64 | MW level from | Quantity |
| `levelTo` | INT64 | MW level to | Quantity |
| `bidOfferPairNumber` | INT64 | Pair ID | Matching |
| `offerPrice` | FLOAT64 | Offer price (£/MWh) | ⭐ **Sell price** |
| `bidPrice` | FLOAT64 | Bid price (£/MWh) | ⭐ **Buy price** |
| `bmUnit` | STRING | Balancing Unit ID | Asset identifier |

**VLP Queries:**
```sql
-- Find profitable bid-offer spreads
SELECT 
  settlementDate,
  settlementPeriod,
  bmUnit,
  offerPrice,
  bidPrice,
  (offerPrice - bidPrice) as spread,
  (levelTo - levelFrom) as volume_mw
FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_bod`
WHERE (offerPrice - bidPrice) > 20  -- £20/MWh minimum spread
ORDER BY spread DESC
LIMIT 100;
```

---

### 3. **bmrs_detsysprices** - Detailed System Prices (SSP/SBP)
**Use**: Imbalance pricing - System Sell Price vs System Buy Price

| Column | Type | Description | VLP Usage |
|--------|------|-------------|-----------|
| `settlementDate` | DATETIME | Settlement date | Time |
| `settlementPeriod` | INT64 | Period 1-48 | Period |
| `systemSellPrice` | FLOAT64 | SSP (£/MWh) | ⭐ **Long imbalance cost** |
| `systemBuyPrice` | FLOAT64 | SBP (£/MWh) | ⭐ **Short imbalance revenue** |
| `priceDerivationCode` | STRING | How price calculated | Transparency |
| `reserveScarcityPrice` | FLOAT64 | Scarcity premium | Stress signal |

**VLP Queries:**
```sql
-- Calculate imbalance spread (profitability of being short/long)
SELECT 
  settlementDate,
  settlementPeriod,
  systemSellPrice as SSP,
  systemBuyPrice as SBP,
  (systemSellPrice - systemBuyPrice) as imbalance_spread,
  reserveScarcityPrice
FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_detsysprices`
WHERE (systemSellPrice - systemBuyPrice) > 50  -- High spread = opportunity
ORDER BY imbalance_spread DESC;
```

---

### 4. **bmrs_netbsad** - Net Imbalance Volume
**Use**: Market direction - system short or long?

| Column | Type | Description | VLP Usage |
|--------|------|-------------|-----------|
| `settlementDate` | DATETIME | Date | Time |
| `settlementPeriod` | INT64 | Period | Period |
| `volume` | FLOAT64 | Net imbalance (MWh) | ⭐ **Direction signal** |

**VLP Logic:**
- `volume > 0`: System LONG → Prices falling → Charge batteries
- `volume < 0`: System SHORT → Prices rising → Discharge batteries

```sql
-- Identify periods with extreme imbalance (price volatility)
SELECT 
  settlementDate,
  settlementPeriod,
  volume,
  CASE 
    WHEN volume > 500 THEN 'LONG - Charge opportunity'
    WHEN volume < -500 THEN 'SHORT - Discharge opportunity'
    ELSE 'Balanced'
  END as signal
FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_netbsad`
WHERE ABS(volume) > 500
ORDER BY ABS(volume) DESC;
```

---

### 5. **bmrs_b1610** - Actual Generation by Fuel Type
**Use**: Predict price movements based on generation mix

| Column | Type | Description | VLP Usage |
|--------|------|-------------|-----------|
| `startTime` | DATETIME | Period start | Timing |
| `settlementDate` | DATETIME | Date | Date |
| `settlementPeriod` | INT64 | Period | Period |
| `ccgt` | FLOAT64 | Gas generation (MW) | Marginal price driver |
| `coal` | FLOAT64 | Coal generation (MW) | Expensive = high prices |
| `nuclear` | FLOAT64 | Nuclear (MW) | Baseload |
| `wind` | FLOAT64 | Wind (MW) | ⭐ **Renewables = low prices** |
| `solar` | FLOAT64 | Solar (MW) | Daytime signal |
| `biomass` | FLOAT64 | Biomass (MW) | Stable |
| `hydro` | FLOAT64 | Hydro (MW) | Flexible |
| `other` | FLOAT64 | Other (MW) | Mixed |

**VLP Queries:**
```sql
-- Identify periods with high renewables (low prices expected)
SELECT 
  settlementDate,
  settlementPeriod,
  wind,
  solar,
  (wind + solar) as total_renewables,
  ccgt as gas_generation
FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_b1610`
WHERE (wind + solar) > 10000  -- High renewables = charge opportunity
ORDER BY total_renewables DESC;

-- Gas generation (high gas = high prices)
SELECT 
  settlementDate,
  settlementPeriod,
  ccgt,
  coal
FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_b1610`
WHERE ccgt > 15000  -- High gas = discharge opportunity
ORDER BY ccgt DESC;
```

---

### 6. **bmrs_indgen_iris** - Individual Generator Data
**Use**: Track your own assets' performance

| Column | Type | Description | VLP Usage |
|--------|------|-------------|-----------|
| `settlementDate` | DATETIME | Date | Time |
| `settlementPeriod` | INT64 | Period | Period |
| `bmUnitId` | STRING | Unit ID | Your asset ID |
| `bmUnitType` | STRING | Unit type | Asset type |
| `leadPartyName` | STRING | Operator | Your company |
| `ngcBmUnitName` | STRING | NGC name | Official name |
| `quantity` | FLOAT64 | Output (MW) | ⭐ **Actual generation** |
| `fuelType` | STRING | Fuel type | Categorization |

**VLP Queries:**
```sql
-- Your battery performance tracking
SELECT 
  settlementDate,
  settlementPeriod,
  bmUnitId,
  quantity as output_mw,
  fuelType
FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_indgen_iris`
WHERE leadPartyName LIKE '%YOUR_COMPANY%'  -- Replace with your company name
ORDER BY settlementDate DESC, settlementPeriod DESC;
```

---

### 7. **bmrs_fuelinst_iris** - Fuel Mix Instant (Real-time)
**Use**: Current generation mix - immediate price drivers

| Column | Type | Description | VLP Usage |
|--------|------|-------------|-----------|
| `publishTime` | DATETIME | Publish timestamp | Real-time |
| `startTime` | DATETIME | Period start | Window |
| `ccgt` | INT64 | Gas (MW) | Price driver |
| `wind` | INT64 | Wind (MW) | Low price signal |
| `solar` | INT64 | Solar (MW) | Daytime signal |
| `nuclear` | INT64 | Nuclear (MW) | Baseload |
| `biomass` | INT64 | Biomass (MW) | Stable |

**VLP Queries:**
```sql
-- Real-time generation mix monitoring
SELECT 
  publishTime,
  ccgt,
  wind,
  solar,
  (wind + solar) as renewables,
  (ccgt + coal) as fossil
FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_fuelinst_iris`
WHERE publishTime > TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 1 HOUR)
ORDER BY publishTime DESC
LIMIT 50;
```

---

### 8. **bmrs_remit_unavailability** - Unit Unavailability
**Use**: Capacity constraints - supply tightness = higher prices

| Column | Type | Description | VLP Usage |
|--------|------|-------------|-----------|
| `assetName` | STRING | Unit name | Asset |
| `fuelType` | STRING | Fuel type | Category |
| `normalCapacity` | FLOAT64 | Normal MW | Baseline |
| `unavailableCapacity` | FLOAT64 | Unavailable MW | ⭐ **Lost capacity** |
| `eventStartTime` | DATETIME | Outage start | Window start |
| `eventEndTime` | DATETIME | Outage end | Window end |
| `cause` | STRING | Reason | Context |

**VLP Queries:**
```sql
-- Identify large outages (price spike opportunities)
SELECT 
  assetName,
  fuelType,
  unavailableCapacity,
  eventStartTime,
  eventEndTime,
  cause
FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_remit_unavailability`
WHERE unavailableCapacity > 500  -- Large outages
  AND eventEndTime > CURRENT_TIMESTAMP()  -- Ongoing
ORDER BY unavailableCapacity DESC;
```

---

### 9. **bmrs_freq** - System Frequency
**Use**: Grid stress indicator - emergency balancing events

| Column | Type | Description | VLP Usage |
|--------|------|-------------|-----------|
| `time` | DATETIME | Timestamp | When |
| `frequency` | FLOAT64 | Hz | ⭐ **Grid stability** |

**VLP Logic:**
- `freq < 49.8 Hz`: Low frequency → Scarcity → High prices
- `freq > 50.2 Hz`: High frequency → Surplus → Low prices

```sql
-- Identify low-frequency events (potential price spikes)
SELECT 
  time,
  frequency,
  CASE 
    WHEN frequency < 49.8 THEN 'CRITICAL LOW - Discharge opportunity'
    WHEN frequency > 50.2 THEN 'HIGH - Charge opportunity'
    ELSE 'Normal'
  END as signal
FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_freq`
WHERE frequency < 49.9 OR frequency > 50.1
ORDER BY time DESC
LIMIT 100;
```

---

### 10. **bmrs_surplus_margin** - Surplus Forecast
**Use**: Capacity margins - scarcity pricing risk

| Column | Type | Description | VLP Usage |
|--------|------|-------------|-----------|
| `forecastDate` | DATETIME | Forecast for date | Future |
| `publishTime` | DATETIME | When published | Freshness |
| `surplus` | INT64 | Surplus MW | ⭐ **Capacity cushion** |

**VLP Logic:**
- `surplus < 1000 MW`: Tight margins → High price risk
- `surplus > 5000 MW`: Comfortable → Lower prices

```sql
-- Identify tight capacity periods (price spike risk)
SELECT 
  forecastDate,
  surplus,
  CASE 
    WHEN surplus < 1000 THEN 'TIGHT - Price spike risk'
    WHEN surplus < 2000 THEN 'MEDIUM - Watch closely'
    ELSE 'COMFORTABLE'
  END as capacity_status
FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_surplus_margin`
WHERE forecastDate >= CURRENT_DATE()
ORDER BY forecastDate;
```

---

## 🎯 VLP Strategy Mapping

### Arbitrage Opportunities

**Buy Low (Charge):**
```sql
-- Combine signals for charge decision
SELECT 
  m.settlementDate,
  m.settlementPeriod,
  m.price as mid_price,
  d.systemBuyPrice as sbp,
  n.volume as net_imbalance,
  g.wind + g.solar as renewables
FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_mid` m
LEFT JOIN `inner-cinema-476211-u9.uk_energy_prod.bmrs_detsysprices` d 
  ON m.settlementDate = d.settlementDate 
  AND m.settlementPeriod = d.settlementPeriod
LEFT JOIN `inner-cinema-476211-u9.uk_energy_prod.bmrs_netbsad` n
  ON m.settlementDate = n.settlementDate 
  AND m.settlementPeriod = n.settlementPeriod
LEFT JOIN `inner-cinema-476211-u9.uk_energy_prod.bmrs_b1610` g
  ON m.settlementDate = g.settlementDate 
  AND m.settlementPeriod = g.settlementPeriod
WHERE m.price < 50  -- Low prices
  AND n.volume > 200  -- System long
  AND (g.wind + g.solar) > 8000  -- High renewables
ORDER BY m.settlementDate DESC, m.settlementPeriod DESC
LIMIT 100;
```

**Sell High (Discharge):**
```sql
-- High-price discharge opportunities
SELECT 
  m.settlementDate,
  m.settlementPeriod,
  m.price as mid_price,
  d.systemSellPrice as ssp,
  n.volume as net_imbalance,
  g.ccgt as gas_generation,
  s.surplus as capacity_margin
FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_mid` m
LEFT JOIN `inner-cinema-476211-u9.uk_energy_prod.bmrs_detsysprices` d 
  ON m.settlementDate = d.settlementDate 
  AND m.settlementPeriod = d.settlementPeriod
LEFT JOIN `inner-cinema-476211-u9.uk_energy_prod.bmrs_netbsad` n
  ON m.settlementDate = n.settlementDate 
  AND m.settlementPeriod = n.settlementPeriod
LEFT JOIN `inner-cinema-476211-u9.uk_energy_prod.bmrs_b1610` g
  ON m.settlementDate = g.settlementDate 
  AND m.settlementPeriod = g.settlementPeriod
LEFT JOIN `inner-cinema-476211-u9.uk_energy_prod.bmrs_surplus_margin` s
  ON DATE(m.settlementDate) = DATE(s.forecastDate)
WHERE m.price > 100  -- High prices
  AND n.volume < -200  -- System short
  AND s.surplus < 2000  -- Tight capacity
ORDER BY m.price DESC
LIMIT 100;
```

---

## 📊 Data Quality Checks

```sql
-- Check data coverage by table
SELECT 
  table_name,
  COUNT(*) as row_count,
  MIN(settlementDate) as earliest_date,
  MAX(settlementDate) as latest_date,
  DATE_DIFF(MAX(settlementDate), MIN(settlementDate), DAY) as days_coverage
FROM (
  SELECT 'bmrs_mid' as table_name, settlementDate FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_mid`
  UNION ALL
  SELECT 'bmrs_bod', settlementDate FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_bod`
  UNION ALL
  SELECT 'bmrs_detsysprices', settlementDate FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_detsysprices`
  UNION ALL
  SELECT 'bmrs_netbsad', settlementDate FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_netbsad`
  UNION ALL
  SELECT 'bmrs_b1610', settlementDate FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_b1610`
)
GROUP BY table_name
ORDER BY row_count DESC;
```

---

## 🔗 Quick Reference

**Project**: `inner-cinema-476211-u9`  
**Dataset**: `uk_energy_prod`  
**Total Tables**: 50+  
**Key Tables**: 10 (listed above)  
**Date Range**: Check with data quality query above  

**Access via Custom GPT**: https://chatgpt.com/g/g-690fd99ad3dc8191b47126eb06e2c593-gb-power-market-code-execution-true

---

**Next Steps**: Use these queries in your Custom GPT or run them directly via Railway API!

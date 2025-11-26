# APXMIDP vs N2EXMIDP Data Sources Explained

## 📊 What Are These Data Providers?

### **APXMIDP** (APX Power UK - Market Index Data Provider)
- **Active**: ✅ YES - 1,252 records in last 22 days
- **Price Range**: £5.16 - £216.25/MWh
- **Average**: £80.19/MWh
- **Coverage**: 100% of settlement periods
- **Zero Prices**: 0 (all valid market prices)
- **Source**: APX Power UK (part of EPEX SPOT - European Power Exchange)
- **What it represents**: UK day-ahead wholesale electricity market prices

### **N2EXMIDP** (Nord Pool - N2EX Market Index Data Provider)
- **Active**: ❌ NO - Essentially inactive
- **Price Range**: £0.00 - £101.39/MWh (only 3 non-zero records!)
- **Average**: £0.18/MWh (misleading - 99.8% are zeros)
- **Coverage**: Present in data but reporting £0.00
- **Zero Prices**: 1,251 out of 1,254 records
- **Source**: Nord Pool (European electricity exchange, Norway-based)
- **Status**: **Deprecated or inactive for UK market**

## 🔍 Key Findings

### Historical Data (Oct 1-30, 2025)
- **APXMIDP**: 1,334 records, ALL valid prices (£-15.55 to £287.57/MWh)
  - Yes, negative prices occur! (renewable oversupply)
- **N2EXMIDP**: 1,319 records, ALL £0.00 (completely inactive)

### Today's Data (Nov 26, 2025)
```
Period 34 (16:30-17:00): APXMIDP = £105.68/MWh | N2EXMIDP = £0.00
Period 33 (16:00-16:30): APXMIDP = £101.10/MWh | N2EXMIDP = £0.00
Period 32 (15:30-16:00): APXMIDP = £92.93/MWh  | N2EXMIDP = £0.00
Period 31 (15:00-15:30): APXMIDP = £85.34/MWh  | N2EXMIDP = £0.00
Period 30 (14:30-15:00): APXMIDP = £78.95/MWh  | N2EXMIDP = £0.00
```

## ✅ Recommendation: USE APXMIDP ONLY

**Why?**
1. **Active data source** - Real market prices every settlement period
2. **Reflects UK market** - APX Power UK is the primary UK wholesale market
3. **Complete coverage** - No zero-price gaps
4. **Historical consistency** - Works for both `bmrs_mid` (historical) and `bmrs_mid_iris` (real-time)

**N2EXMIDP should be filtered out** - it's either:
- Legacy data feed no longer active
- Backup feed that's not being populated
- Placeholder in BMRS data structure

## 🔧 Query Fix Required

### Current Problem
```sql
LEFT JOIN `bmrs_mid_iris` m
  ON a.settlementDate = m.settlementDate
  AND a.settlementPeriod = m.settlementPeriod
```
Returns **2 rows per period** (APXMIDP + N2EXMIDP), causing NULL in joins.

### Solution 1: Filter to APXMIDP (RECOMMENDED)
```sql
LEFT JOIN `bmrs_mid_iris` m
  ON a.settlementDate = m.settlementDate
  AND a.settlementPeriod = m.settlementPeriod
  AND m.dataProvider = 'APXMIDP'  -- ✅ Only use APX prices
```

### Solution 2: Use Subquery (if both providers become active)
```sql
LEFT JOIN (
  SELECT 
    settlementDate,
    settlementPeriod,
    AVG(CASE WHEN price > 0 THEN price ELSE NULL END) as price,
    SUM(volume) as volume
  FROM `bmrs_mid_iris`
  GROUP BY settlementDate, settlementPeriod
) m
  ON a.settlementDate = m.settlementDate
  AND a.settlementPeriod = m.settlementPeriod
```

## 📈 What APXMIDP Price Represents

**Market Index Data (MID)** = Day-ahead wholesale electricity price

- **Not**: Balancing mechanism acceptance prices (those aren't in BOALF data)
- **Is**: The reference price for the UK wholesale market
- **Use case**: Reasonable proxy for battery revenue opportunity
- **Calculation**: 
  - **Discharge** (positive volume): `volume_mw × apx_price / 2` = revenue earned
  - **Charge** (negative volume): `volume_mw × apx_price / 2` = cost paid
  - Division by 2 = converts MWh to half-hourly settlement period

## 💡 Business Interpretation

**Today's APXMIDP prices (£78-106/MWh) indicate:**
- Moderate to high wholesale prices
- Peak demand period (16:00-17:00 = £105.68/MWh)
- Good discharge opportunity for batteries
- Expensive charging period (avoid if possible)

**Battery Strategy:**
- **Discharge at**: £100+ (high revenue)
- **Hold at**: £70-100 (moderate revenue)
- **Charge at**: £30-50 (good charging opportunity)
- **Current period (£105/MWh)**: DISCHARGE mode optimal

---

**Last Updated**: November 26, 2025  
**Data Source**: `inner-cinema-476211-u9.uk_energy_prod.bmrs_mid_iris`

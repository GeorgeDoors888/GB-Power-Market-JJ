# Dimensional Model Complete - VLP/VTP Query Guide

**Created**: December 20, 2025
**Status**: ✅ Production Ready

---

## 🎯 Your Original Query - NOW WORKING!

```sql
SELECT
  f.*,
  b.lead_party_name,
  p.party_id,
  p.party_roles,
  p.is_vlp,
  p.is_vtp
FROM fact_ops f
LEFT JOIN dim_bmu b
  ON f.bmu_id = b.bm_unit_id
LEFT JOIN dim_party p
  ON LOWER(TRIM(COALESCE(b.lead_party_name, ''))) = LOWER(TRIM(COALESCE(p.party_name, '')))
WHERE (p.is_vlp = TRUE OR p.is_vtp = TRUE)
  AND f.acceptance_date >= '2025-01-01'
ORDER BY f.revenue_gbp DESC
LIMIT 100;
```

---

## 📊 Dimensional Model Summary

### 1. dim_party (Party Dimension)
- **Rows**: 700 BSC signatories
- **VLP Parties**: 22 (Virtual Lead Party)
- **VTP Parties**: 12 (Virtual Trader)
- **Key Columns**:
  - `party_key` (surrogate PK)
  - `party_id`, `party_name` (natural keys)
  - `is_vlp`, `is_vtp`, `is_generator`, `is_trader_supplier` (role flags)
  - `role_count`, `primary_role_category` (classification)

### 2. dim_bmu (BM Unit Dimension)
- **Rows**: 2,717 BM units
- **Battery/Storage**: 67 units
- **Traditional Generators**: 455 units (T_ prefix)
- **Embedded Generation**: 155 units (E_ prefix)
- **Virtual Units**: 91 units (V_ prefix)
- **Key Columns**:
  - `bmu_key` (surrogate PK)
  - `bm_unit_id`, `lead_party_name` (natural keys)
  - `generation_type` (Wind, Solar, Gas, Battery Storage, etc.)
  - `is_battery_storage`, `is_traditional_generator` (flags)
  - `generation_capacity_mw`, `demand_capacity_mw` (measures)

### 3. fact_ops (Operational Facts)
- **Rows**: 1,348,838 valid balancing acceptances
- **Date Range**: 2022-01-01 to 2025-12-20
- **Total Volume**: 100,156,078 MWh
- **Total Revenue**: £6,880,014,847
- **Average Price**: £62.93/MWh
- **Unique BM Units**: 616
- **Key Columns**:
  - `fact_key` (surrogate PK)
  - `bmu_id` (FK to dim_bmu)
  - `acceptance_date`, `acceptance_year`, `acceptance_month` (time dimensions)
  - `volume_mwh`, `price_gbp_mwh`, `revenue_gbp` (measures)
  - `acceptanceType`, `is_offer`, `is_bid` (flags)
  - `validation_flag`, `data_quality` (quality indicators)

---

## 💰 VLP/VTP Revenue Analysis (2025)

### Top 5 Virtual Lead Parties by Revenue

| Party Name | Roles | Acceptances | Units | Total MWh | Revenue (£) | Avg Price |
|-----------|-------|------------|-------|-----------|-------------|-----------|
| **BP Gas Marketing** | BP,TI,TN,TG,EN,MV,TS,VP | 16,006 | 4 | 198,355 | £13,861,646 | £67.95/MWh |
| **Octopus Energy Trading** | BP,TS,VP,VT,EN,MV | 11,076 | 5 | 85,820 | £4,946,512 | £57.04/MWh |
| **Habitat Energy** | BP,TN,VP,EN,MV,TS | 1,499 | 4 | 21,774 | £2,341,214 | £107.92/MWh |
| **Flexitricity** | BP,TS,VP,AV,VT | 3,816 | 30 | 31,839 | £1,291,258 | £39.28/MWh |
| **Danske Commodities** | BP,TI,TN,EN,MV,VP | 681 | 1 | 2,947 | £197,336 | £78.40/MWh |

### Key Findings

1. **BP Gas Marketing** dominates VLP revenue (60% market share)
   - Operating 4 BM units including 2__FBPGM002 (battery)
   - High-value acceptances: £67.95/MWh average

2. **Octopus Energy Trading** is both VLP + VTP (dual role)
   - 5 units, diversified portfolio
   - Lower avg price (£57/MWh) but high volume (85,820 MWh)

3. **Habitat Energy** has highest price premium
   - £107.92/MWh average (strategy: hold for high prices)
   - Specializes in V__HHABI008 unit (49 MW typical acceptance)

4. **Negative Revenue Parties**:
   - BESS Holdco 2: -£294k (potential bid strategy issues)
   - EDF Energy: -£1.1M (likely grid support at negative prices)

---

## 🔋 Battery Storage Units with VLP Parties

### Active Battery BMUs (Dec 2025)

| BMU ID | Party | Acceptances | Revenue | Storage Type |
|--------|-------|------------|---------|--------------|
| 2__FBPGM002 | BP Gas Marketing | 4,503 | £13.2M | Battery |
| E_PILLB-2 | BP Gas Marketing | Multiple | £96k | Battery Storage |
| V__HHABI008 | Habitat Energy | 1,499 | £2.3M | Virtual Battery |

**Note**: `is_battery_storage` flag identifies 67 battery/storage units total, but only 22 VLP parties have balancing acceptances tracked.

---

## 📈 Query Patterns & Use Cases

### 1. Monthly VLP Revenue Trend
```sql
SELECT
    DATE_TRUNC(f.acceptance_date, MONTH) as month,
    p.party_name,
    COUNT(*) as acceptances,
    ROUND(SUM(f.revenue_gbp), 0) as total_revenue
FROM fact_ops f
JOIN dim_bmu b ON f.bmu_id = b.bm_unit_id
JOIN dim_party p ON LOWER(TRIM(b.lead_party_name)) = LOWER(TRIM(p.party_name))
WHERE p.is_vlp = TRUE
  AND f.acceptance_date >= '2025-01-01'
GROUP BY month, p.party_name
ORDER BY month DESC, total_revenue DESC;
```

### 2. Battery Storage Performance
```sql
SELECT
    f.bmu_id,
    b.lead_party_name,
    b.generation_capacity_mw,
    COUNT(*) as total_cycles,
    SUM(CASE WHEN f.is_offer THEN f.volume_mwh ELSE 0 END) as discharge_mwh,
    SUM(CASE WHEN f.is_bid THEN f.volume_mwh ELSE 0 END) as charge_mwh,
    ROUND(AVG(f.price_gbp_mwh), 2) as avg_price,
    ROUND(SUM(f.revenue_gbp), 0) as net_revenue
FROM fact_ops f
JOIN dim_bmu b ON f.bmu_id = b.bm_unit_id
WHERE b.is_battery_storage = TRUE
  AND f.acceptance_date >= '2025-01-01'
GROUP BY f.bmu_id, b.lead_party_name, b.generation_capacity_mw
ORDER BY net_revenue DESC;
```

### 3. VLP vs VTP Comparison
```sql
SELECT
    CASE WHEN p.is_vtp THEN 'VTP' ELSE 'VLP' END as party_type,
    COUNT(DISTINCT p.party_name) as unique_parties,
    COUNT(*) as total_acceptances,
    ROUND(SUM(f.volume_mwh), 0) as total_volume_mwh,
    ROUND(SUM(f.revenue_gbp), 0) as total_revenue_gbp,
    ROUND(AVG(f.price_gbp_mwh), 2) as avg_price
FROM fact_ops f
JOIN dim_bmu b ON f.bmu_id = b.bm_unit_id
JOIN dim_party p ON LOWER(TRIM(b.lead_party_name)) = LOWER(TRIM(p.party_name))
WHERE (p.is_vlp = TRUE OR p.is_vtp = TRUE)
  AND f.acceptance_date >= '2025-01-01'
GROUP BY party_type;
```

### 4. Multi-Role Party Analysis
```sql
SELECT
    p.party_name,
    p.party_roles,
    p.role_count,
    p.is_vlp,
    p.is_generator,
    p.is_trader_supplier,
    COUNT(DISTINCT f.bmu_id) as bm_units_operated,
    ROUND(SUM(f.revenue_gbp), 0) as total_revenue
FROM dim_party p
LEFT JOIN dim_bmu b ON LOWER(TRIM(b.lead_party_name)) = LOWER(TRIM(p.party_name))
LEFT JOIN fact_ops f ON f.bmu_id = b.bm_unit_id
WHERE p.role_count >= 5  -- Parties with 5+ roles
  AND f.acceptance_date >= '2025-01-01'
GROUP BY p.party_name, p.party_roles, p.role_count, p.is_vlp, p.is_generator, p.is_trader_supplier
ORDER BY total_revenue DESC;
```

---

## 🚨 Join Considerations & Gotchas

### Party Name Matching
The join uses **case-insensitive, trimmed** party name matching:
```sql
ON LOWER(TRIM(COALESCE(b.lead_party_name, ''))) =
   LOWER(TRIM(COALESCE(p.party_name, '')))
```

**Why**: Party names may have inconsistent casing or trailing spaces between `bmu_registration_data` and `bsc_signatories_full`.

### Unmatched Records
- Some BM units have `lead_party_name` values NOT in BSC signatories (e.g., legacy names)
- Use `LEFT JOIN` to preserve all fact records
- Filter on `p.party_key IS NOT NULL` to exclude unmatched records if needed

### Multiple BM Units per Party
- VLP parties typically operate 1-30 BM units (Flexitricity has 30!)
- Group by `party_name` when aggregating revenue across all units
- Use `COUNT(DISTINCT f.bmu_id)` to count unique units per party

---

## 🗂️ Table Locations

```
BigQuery Project: inner-cinema-476211-u9
Dataset: uk_energy_prod

Tables:
├── dim_party (700 rows, 0.10 MB)
├── dim_bmu (2,717 rows, 0.50 MB)
├── fact_ops (1,348,838 rows, ~250 MB)
│
Source Tables:
├── bsc_signatories_full (700 rows)
├── bmu_registration_data (2,783 rows)
└── bmrs_boalf_complete (3.1M rows, Valid only)
```

---

## 🛠️ Maintenance & Updates

### Refresh Dimensional Model
```bash
# Re-run dimensional model creation
python3 /home/george/GB-Power-Market-JJ/create_dimensional_model.py
```

**When to refresh**:
- New BSC signatories added (quarterly)
- BM unit registrations change (monthly)
- After large BOALF data backfill (daily_data_pipeline.py)

### Add New Party Roles
To add new role flags to `dim_party`, edit the CREATE TABLE query in `create_dimensional_model.py`:
```sql
REGEXP_CONTAINS(Party_Roles, r'(^|, )NEW_ROLE(,|$)') AS is_new_role,
```

---

## 📚 Related Documentation

- `BSC_PARTY_DATA_MAPPING.md` - Party role definitions and data sources
- `PROJECT_CONFIGURATION.md` - BigQuery credentials and setup
- `STOP_DATA_ARCHITECTURE_REFERENCE.md` - Schema reference and gotchas

---

## ✅ Success Criteria Met

- ✅ `dim_party` created with 22 VLP parties identified
- ✅ `dim_bmu` created with 2,717 BM units (67 batteries)
- ✅ `fact_ops` created with 1.35M acceptances (2022-2025)
- ✅ Your original query **WORKS** and returns VLP/VTP revenue data
- ✅ Top 5 VLP parties identified: BP Gas (£13.8M), Octopus (£4.9M), Habitat (£2.3M)
- ✅ Battery storage units linked to VLP parties (2__FBPGM002, E_PILLB-2)

---

**Next Steps**:
1. Deploy queries to Google Sheets for VLP dashboard
2. Create time-series analysis of VLP revenue trends
3. Add alerts for negative revenue patterns
4. Map remaining 584 BM units to parties (improve join coverage)

---

**Last Updated**: December 20, 2025
**Maintainer**: George Major (george@upowerenergy.uk)

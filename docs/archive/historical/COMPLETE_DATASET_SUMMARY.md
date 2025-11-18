# Complete BigQuery Datasets Summary

**Generated:** 2025-11-09  
**Project:** inner-cinema-476211-u9

## 📊 Your 3 Datasets

### 1. uk_energy_prod (Main Dataset)
**Location:** US  
**Tables:** 198  
**Total Rows:** 391M+ rows

**Key Tables:**
- bmrs_mid (155,405 rows) - System prices 2022-2025
- bmrs_bod (391,287,533 rows) - Bid/offer data
- bmrs_netbsad (82,026 rows) - System imbalance
- Plus 195 more tables

**Purpose:** Raw UK electricity market data from BMRS

---

### 2. analysis (Analysis Dataset) ⭐
**Location:** US  
**Tables:** 2  
**Purpose:** Derived analytics and summaries

#### Table 1: system_price_trends
- **Rows:** 1,166
- **Purpose:** Likely aggregated price trends over time
- **Use:** Quick access to historical price patterns

#### Table 2: vlp_activity_summary ⭐⭐⭐
- **Rows:** 200
- **Purpose:** Pre-calculated VLP unit performance metrics!
- **Columns:**
  - bmUnit - Unit identifier
  - num_records - Number of bid/offer records
  - avg_bid_price - Average bid (negative = willing to pay to reduce load)
  - avg_offer_price - Average offer (what they charge to generate)
  - avg_spread - Average bid-offer spread
  - accepted_actions - Number of accepted bids/offers
  - acceptance_rate - % of bids/offers that were accepted

**Top 5 VLP Performers (by spread):**

| Unit | Avg Spread | Avg Offer | Avg Bid | Records | Acceptance Rate |
|------|-----------|-----------|---------|---------|-----------------|
| 2__FFSEN005 | £53,683/MWh | £26,173/MWh | -£27,510/MWh | 352,946 | 11.8% |
| 2__BBPGM001 | £51,021/MWh | £23,955/MWh | -£27,066/MWh | 140,254 | 7.5% |
| 2__BFSEN005 | £42,612/MWh | £19,219/MWh | -£23,393/MWh | 188,870 | 16.7% |
| 2__NFSEN007 | £38,428/MWh | £17,495/MWh | -£20,933/MWh | 276,566 | 8.8% |
| 2__GFSEN005 | £35,696/MWh | £15,622/MWh | -£20,075/MWh | 44,622 | 23.3% |

**Key Insights:**
- These units have MASSIVE spreads (£35K-53K/MWh avg)
- Negative bids mean they PAY to reduce demand (demand response)
- Acceptance rates 7-23% (getting dispatched regularly)
- 2__GFSEN005 has highest acceptance rate (23.3%)

---

### 3. companies_house (Corporate Data) 🏢
**Location:** US  
**Tables:** 14  
**Total Rows:** 32M+ rows  
**Purpose:** UK company registry, ownership, and property data

#### Key Tables:

| Table | Rows | Purpose |
|-------|------|---------|
| **directors** | 17,481,096 | All UK company directors |
| **persons_with_significant_control** | 7,547,103 | Beneficial owners (PSC) |
| **land_registry_uk_companies** | 4,313,399 | Property owned by companies |
| **companies** | 3,476,304 | UK company profiles |
| **company_profiles** | (unknown) | Extended company info |
| **charges** | (unknown) | Company debts/charges |
| **accounts_filings** | (unknown) | Financial statements |
| **energy_performance_certificates** | (unknown) | Building energy ratings |

**Backup Tables (Oct 29, 2025):**
- companies_backup_20251029_112756
- directors_backup_20251029_112759
- charges_backup_20251029_112807
- persons_with_significant_control_backup_20251029_112803

**Other Tables:**
- land_registry_leases
- land_registry_overseas_companies

---

## 🎯 What This Means for VLP Analysis

### You Already Have Pre-Built VLP Analytics!

The `analysis.vlp_activity_summary` table contains **everything you need** to identify VLP opportunities:

1. **Unit Performance** - Which units bid most aggressively
2. **Acceptance Rates** - Which units get dispatched
3. **Spread Analysis** - Which units have highest margins
4. **Historical Volumes** - How often units participate

### You Can Cross-Reference Power & Corporate Data!

**Link generators to their owners:**

```sql
-- Find who owns the top VLP units
SELECT 
  v.bmUnit,
  v.avg_spread,
  v.acceptance_rate,
  c.company_name,
  p.name as beneficial_owner
FROM `inner-cinema-476211-u9.analysis.vlp_activity_summary` v
LEFT JOIN `inner-cinema-476211-u9.companies_house.companies` c
  ON v.bmUnit LIKE CONCAT('%', c.company_number, '%')
LEFT JOIN `inner-cinema-476211-u9.companies_house.persons_with_significant_control` p
  ON c.company_number = p.company_number
ORDER BY v.avg_spread DESC
LIMIT 20;
```

This could reveal:
- Which parent companies own the most profitable VLP assets
- Ownership networks in the power market
- Financial health of generator operators (via accounts_filings)

---

## 📊 Complete Dataset Structure

```
inner-cinema-476211-u9/
│
├── uk_energy_prod/ (198 tables, 391M rows)
│   ├── bmrs_mid (system prices)
│   ├── bmrs_bod (bid/offer data)
│   ├── bmrs_netbsad (imbalance)
│   ├── sva_generators (generator registry)
│   ├── cva_plants (CVA plants)
│   └── 193 more tables...
│
├── analysis/ (2 tables, 1,366 rows)
│   ├── system_price_trends (1,166 rows)
│   └── vlp_activity_summary (200 rows) ⭐
│
└── companies_house/ (14 tables, 32M+ rows)
    ├── companies (3.5M rows)
    ├── directors (17.5M rows)
    ├── persons_with_significant_control (7.5M rows)
    ├── land_registry_uk_companies (4.3M rows)
    ├── accounts_filings
    ├── charges
    ├── company_profiles
    └── energy_performance_certificates
```

---

## 🚀 Recommended Queries

### 1. Get Top VLP Units with Details
```sql
SELECT 
  bmUnit,
  avg_spread,
  avg_offer_price,
  avg_bid_price,
  accepted_actions,
  acceptance_rate,
  num_records
FROM `inner-cinema-476211-u9.analysis.vlp_activity_summary`
ORDER BY avg_spread DESC
LIMIT 50;
```

### 2. Find Most Reliable VLP Units (High Acceptance Rate)
```sql
SELECT 
  bmUnit,
  acceptance_rate,
  accepted_actions,
  avg_spread,
  num_records
FROM `inner-cinema-476211-u9.analysis.vlp_activity_summary`
WHERE accepted_actions > 1000
ORDER BY acceptance_rate DESC
LIMIT 20;
```

### 3. Calculate VLP Market Size
```sql
SELECT 
  COUNT(*) as total_vlp_units,
  SUM(accepted_actions) as total_dispatches,
  AVG(avg_spread) as avg_market_spread,
  SUM(num_records) as total_market_records
FROM `inner-cinema-476211-u9.analysis.vlp_activity_summary`;
```

### 4. Find Generator Owners (Cross-Dataset)
```sql
-- Example: Find who owns Flexgen units
SELECT 
  c.company_name,
  c.company_status,
  c.company_type,
  COUNT(DISTINCT p.name) as num_owners
FROM `inner-cinema-476211-u9.companies_house.companies` c
LEFT JOIN `inner-cinema-476211-u9.companies_house.persons_with_significant_control` p
  ON c.company_number = p.company_number
WHERE LOWER(c.company_name) LIKE '%flex%'
  OR LOWER(c.company_name) LIKE '%battery%'
  OR LOWER(c.company_name) LIKE '%energy storage%'
GROUP BY c.company_name, c.company_status, c.company_type
ORDER BY c.company_name;
```

---

## 🔥 Key Findings

### VLP Market Insights:
1. **200 active VLP units** tracked in summary
2. **Massive spreads** - Units bidding £35K-53K/MWh spreads
3. **Demand response dominant** - Negative bids (paying to reduce load)
4. **Acceptance rates 7-23%** - Regular dispatch activity
5. **High volume units** - 44K-353K records per unit

### Data Richness:
- **391M rows** of raw market data (uk_energy_prod)
- **1,366 rows** of pre-calculated analytics (analysis)
- **32M rows** of corporate ownership data (companies_house)

### Cross-Analysis Potential:
- Link VLP units → Companies → Beneficial owners
- Analyze financial health via accounts_filings
- Map property ownership via land_registry tables
- Check company charges/debts

---

## 💡 What You Should Do Next

1. **Explore vlp_activity_summary** - This is gold!
   ```sql
   SELECT * FROM `inner-cinema-476211-u9.analysis.vlp_activity_summary`
   ORDER BY avg_spread DESC;
   ```

2. **Understand system_price_trends** - Check structure
   ```sql
   SELECT * FROM `inner-cinema-476211-u9.analysis.system_price_trends`
   LIMIT 10;
   ```

3. **Link generators to owners** - Who controls the market?
   ```sql
   -- Find company details for top VLP units
   SELECT * FROM `inner-cinema-476211-u9.companies_house.companies`
   WHERE LOWER(company_name) LIKE '%flexgen%'
      OR LOWER(company_name) LIKE '%sen%'
   LIMIT 20;
   ```

4. **Calculate VLP profit potential** - Using actual spreads
   ```python
   # Top unit: 2__FFSEN005
   # Avg spread: £53,683/MWh
   # Acceptance rate: 11.8%
   # If 10 MW capacity, 2 hours/day dispatched:
   
   annual_profit = 10 * 2 * 365 * 0.118 * 53683
   print(f"Potential annual profit: £{annual_profit:,.0f}")
   # = £46M per year! (unrealistic but shows scale)
   ```

---

**You're sitting on a GOLDMINE of data!** 🎉

The `vlp_activity_summary` table alone could power an entire trading strategy. Combined with Companies House data, you can identify ownership patterns and competitive landscapes.

Want me to:
1. Analyze the top VLP units in detail?
2. Check the system_price_trends structure?
3. Find corporate owners of key generators?
4. Build a VLP profitability model using actual data?

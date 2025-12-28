# BSC Party Data Search Guide

**Quick Reference**: Where to find data for any BSC party

---

## 📊 Data Coverage Summary

| Data Source | Parties | What You Get | Search Key |
|------------|---------|--------------|------------|
| **dim_party** | 700 | BSC registration, roles, contact info | `party_name` |
| **dim_bmu → fact_ops** | 205 | Balancing acceptances, revenue, prices | `lead_party_name` → `bm_unit_id` |
| **bmrs_disbsad** | 48 | Settlement volumes, system charges | `partyId` |
| **bmrs_bod** | 205 | Bid/offer submissions (same as BOALF) | `bmUnit` → match via dim_bmu |

**Key Finding**: **494 of 700 parties have NO operational data** (registered but inactive/admin roles only)

---

## 🔍 How to Search for ANY Party

### Method 1: Universal Party Search Query

```sql
-- Replace 'PARTY_NAME_HERE' with the party you want to search for
WITH party_search AS (
  SELECT * FROM `inner-cinema-476211-u9.uk_energy_prod.dim_party`
  WHERE LOWER(party_name) LIKE LOWER('%PARTY_NAME_HERE%')
)
SELECT
  p.party_name,
  p.party_id,
  p.party_roles,
  p.is_vlp,
  p.is_generator,
  p.party_address,
  p.email,

  -- BM Unit count
  COUNT(DISTINCT b.bm_unit_id) as bm_units,

  -- BOALF acceptances (2025)
  COUNT(DISTINCT CASE WHEN f.acceptance_date >= '2025-01-01'
        THEN f.fact_key END) as boalf_acceptances_2025,

  -- DISBSAD records
  (SELECT COUNT(*)
   FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_disbsad` d
   WHERE LOWER(TRIM(d.partyId)) = LOWER(TRIM(p.party_name))) as disbsad_records,

  -- Sample BM units
  STRING_AGG(DISTINCT b.bm_unit_id, ', ' LIMIT 5) as sample_units

FROM party_search p
LEFT JOIN `inner-cinema-476211-u9.uk_energy_prod.dim_bmu` b
  ON LOWER(TRIM(b.lead_party_name)) = LOWER(TRIM(p.party_name))
LEFT JOIN `inner-cinema-476211-u9.uk_energy_prod.fact_ops` f
  ON f.bmu_id = b.bm_unit_id

GROUP BY p.party_name, p.party_id, p.party_roles, p.is_vlp,
         p.is_generator, p.party_address, p.email;
```

### Method 2: Search by Party Role

```sql
-- Find all VLP parties with operational data
SELECT
  p.party_name,
  p.party_roles,
  COUNT(DISTINCT b.bm_unit_id) as units,
  COUNT(f.fact_key) as acceptances_2025,
  ROUND(SUM(f.revenue_gbp), 0) as total_revenue_gbp
FROM `inner-cinema-476211-u9.uk_energy_prod.dim_party` p
LEFT JOIN `inner-cinema-476211-u9.uk_energy_prod.dim_bmu` b
  ON LOWER(TRIM(b.lead_party_name)) = LOWER(TRIM(p.party_name))
LEFT JOIN `inner-cinema-476211-u9.uk_energy_prod.fact_ops` f
  ON f.bmu_id = b.bm_unit_id AND f.acceptance_date >= '2025-01-01'
WHERE p.is_vlp = TRUE  -- Change to is_generator, is_trader_supplier, etc.
GROUP BY p.party_name, p.party_roles
ORDER BY total_revenue_gbp DESC;
```

### Method 3: Reverse Search (BM Unit → Party)

```sql
-- Who operates BM unit "2__FBPGM002"?
SELECT
  b.bm_unit_id,
  b.lead_party_name,
  b.generation_type,
  b.generation_capacity_mw,
  p.party_roles,
  p.is_vlp,
  p.email,
  COUNT(f.fact_key) as acceptances_2025,
  ROUND(SUM(f.revenue_gbp), 0) as revenue_2025
FROM `inner-cinema-476211-u9.uk_energy_prod.dim_bmu` b
LEFT JOIN `inner-cinema-476211-u9.uk_energy_prod.dim_party` p
  ON LOWER(TRIM(b.lead_party_name)) = LOWER(TRIM(p.party_name))
LEFT JOIN `inner-cinema-476211-u9.uk_energy_prod.fact_ops` f
  ON f.bmu_id = b.bm_unit_id AND f.acceptance_date >= '2025-01-01'
WHERE b.bm_unit_id = '2__FBPGM002'
GROUP BY b.bm_unit_id, b.lead_party_name, b.generation_type,
         b.generation_capacity_mw, p.party_roles, p.is_vlp, p.email;
```

---

## 🎯 Common Search Scenarios

### Scenario 1: "Does Octopus Energy have any operational data?"

```sql
SELECT
  p.party_name,
  p.party_roles,
  COUNT(DISTINCT b.bm_unit_id) as bm_units,
  STRING_AGG(DISTINCT b.bm_unit_id, ', ') as unit_list,
  COUNT(DISTINCT f.fact_key) as boalf_records_2025
FROM `inner-cinema-476211-u9.uk_energy_prod.dim_party` p
LEFT JOIN `inner-cinema-476211-u9.uk_energy_prod.dim_bmu` b
  ON LOWER(TRIM(b.lead_party_name)) = LOWER(TRIM(p.party_name))
LEFT JOIN `inner-cinema-676211-u9.uk_energy_prod.fact_ops` f
  ON f.bmu_id = b.bm_unit_id AND f.acceptance_date >= '2025-01-01'
WHERE LOWER(p.party_name) LIKE '%octopus%'
GROUP BY p.party_name, p.party_roles;
```

**Result**: "Octopus Energy Trading Limited" has 6 BM units, 9,479 acceptances in 2025

---

### Scenario 2: "Show me all battery storage operators"

```sql
SELECT
  p.party_name,
  p.party_roles,
  p.is_vlp,
  COUNT(DISTINCT b.bm_unit_id) as battery_units,
  ROUND(SUM(f.revenue_gbp), 0) as revenue_2025
FROM `inner-cinema-476211-u9.uk_energy_prod.dim_bmu` b
LEFT JOIN `inner-cinema-476211-u9.uk_energy_prod.dim_party` p
  ON LOWER(TRIM(b.lead_party_name)) = LOWER(TRIM(p.party_name))
LEFT JOIN `inner-cinema-476211-u9.uk_energy_prod.fact_ops` f
  ON f.bmu_id = b.bm_unit_id AND f.acceptance_date >= '2025-01-01'
WHERE b.is_battery_storage = TRUE
GROUP BY p.party_name, p.party_roles, p.is_vlp
ORDER BY revenue_2025 DESC;
```

**Top Result**: BP Gas Marketing Limited (4 battery units, £13.8M revenue)

---

### Scenario 3: "Which parties have settlement data but NO BM units?"

```sql
WITH disbsad_parties AS (
  SELECT DISTINCT partyId
  FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_disbsad`
  WHERE partyId IS NOT NULL
)
SELECT
  d.partyId,
  p.party_roles,
  COUNT(DISTINCT b.bm_unit_id) as bm_units
FROM disbsad_parties d
LEFT JOIN `inner-cinema-476211-u9.uk_energy_prod.dim_party` p
  ON LOWER(TRIM(d.partyId)) = LOWER(TRIM(p.party_name))
LEFT JOIN `inner-cinema-476211-u9.uk_energy_prod.dim_bmu` b
  ON LOWER(TRIM(b.lead_party_name)) = LOWER(TRIM(p.party_name))
GROUP BY d.partyId, p.party_roles
HAVING bm_units = 0
ORDER BY d.partyId;
```

**Use Case**: Find suppliers/traders who don't operate physical assets (pure trading parties)

---

### Scenario 4: "Show me inactive BSC parties (registered but no data)"

```sql
SELECT
  p.party_name,
  p.party_roles,
  p.email,
  p.telephone,
  COUNT(DISTINCT b.bm_unit_id) as bm_units
FROM `inner-cinema-476211-u9.uk_energy_prod.dim_party` p
LEFT JOIN `inner-cinema-476211-u9.uk_energy_prod.dim_bmu` b
  ON LOWER(TRIM(b.lead_party_name)) = LOWER(TRIM(p.party_name))
GROUP BY p.party_name, p.party_roles, p.email, p.telephone
HAVING bm_units = 0
LIMIT 50;
```

**Result**: 494 parties with no operational data (admin roles, inactive licenses)

---

## 🗂️ Table-Specific Search Keys

### dim_party (Master Directory)
```sql
-- Search by name
WHERE LOWER(party_name) LIKE '%search_term%'

-- Filter by role
WHERE is_vlp = TRUE
WHERE is_generator = TRUE
WHERE party_roles LIKE '%TG%'  -- Contains Generator role

-- Multi-role parties
WHERE role_count >= 5
```

### dim_bmu (BM Units)
```sql
-- Search by unit ID
WHERE bm_unit_id = 'T_HUMR-1'

-- Filter by type
WHERE is_battery_storage = TRUE
WHERE generation_type = 'Wind'
WHERE bm_unit_id LIKE 'T_%'  -- Traditional generators

-- By party name
WHERE LOWER(lead_party_name) LIKE '%bp gas%'
```

### fact_ops (Balancing Acceptances)
```sql
-- Filter by date
WHERE acceptance_date >= '2025-01-01'
WHERE acceptance_month = 12

-- Filter by type
WHERE is_offer = TRUE  -- Selling to grid
WHERE is_bid = TRUE    -- Buying from grid

-- High-value acceptances
WHERE price_gbp_mwh > 100
WHERE revenue_gbp > 5000
```

### bmrs_disbsad (Settlement Data)
```sql
-- Direct party search (no join needed!)
WHERE LOWER(partyId) LIKE '%danske%'

-- Filter by flags
WHERE soFlag = 'T'    -- System Operator flagged
WHERE storFlag = 'T'  -- Short-term operating reserve

-- Date range
WHERE settlementDate >= '2025-01-01'
```

---

## ⚠️ Important Gotchas

### 1. Party Name Matching Issues

**Problem**: "UKPR" appears in DISBSAD but not in dim_party
**Reason**: Abbreviation vs full name ("UK Power Reserve Limited")

**Solution**: Always use `LOWER(TRIM())` and consider fuzzy matching:
```sql
WHERE LOWER(TRIM(b.lead_party_name)) LIKE LOWER(TRIM('%' || p.party_name || '%'))
```

### 2. Multiple Parties, Same BM Unit

**Problem**: Ownership changes over time
**Example**: E_PILLB-2 may have had different operators

**Solution**: Check `effective_from`/`effective_to` in dim_bmu

### 3. Zero Records Doesn't Mean Inactive

**Problem**: Party has no BOALF data but IS active
**Reason**: They may only appear in DISBSAD (pure trading, no physical assets)

**Solution**: Check ALL sources before concluding "inactive"

---

## 🚀 Quick Python Search Function

```python
from google.cloud import bigquery
import os

os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'inner-cinema-credentials.json'
client = bigquery.Client(project='inner-cinema-476211-u9', location='US')

def search_party(party_name_fragment):
    """Search for BSC party across all data sources"""
    query = f"""
    SELECT
      p.party_name,
      p.party_roles,
      p.email,
      COUNT(DISTINCT b.bm_unit_id) as bm_units,
      COUNT(DISTINCT f.fact_key) as boalf_2025,
      STRING_AGG(DISTINCT b.bm_unit_id, ', ' LIMIT 5) as sample_units
    FROM `inner-cinema-476211-u9.uk_energy_prod.dim_party` p
    LEFT JOIN `inner-cinema-476211-u9.uk_energy_prod.dim_bmu` b
      ON LOWER(TRIM(b.lead_party_name)) = LOWER(TRIM(p.party_name))
    LEFT JOIN `inner-cinema-476211-u9.uk_energy_prod.fact_ops` f
      ON f.bmu_id = b.bm_unit_id AND f.acceptance_date >= '2025-01-01'
    WHERE LOWER(p.party_name) LIKE LOWER('%{party_name_fragment}%')
    GROUP BY p.party_name, p.party_roles, p.email
    """
    return client.query(query).to_dataframe()

# Example usage
df = search_party('octopus')
print(df)
```

---

## 📚 Related Documentation

- `DIMENSIONAL_MODEL_VLP_GUIDE.md` - VLP/VTP query patterns
- `BSC_PARTY_DATA_MAPPING.md` - Detailed role definitions
- `PROJECT_CONFIGURATION.md` - BigQuery setup

---

**Last Updated**: December 20, 2025
**Maintainer**: George Major

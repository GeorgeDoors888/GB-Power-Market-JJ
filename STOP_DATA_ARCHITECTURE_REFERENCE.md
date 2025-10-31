# ⚠️ STOP: Data Architecture Quick Reference

**Purpose:** Prevent repeating data format/table confusion  
**Read this BEFORE writing ANY query or analysis script**  
**Last Updated:** 31 October 2025

---

## 🎯 THE CORE PROBLEM

We keep rediscovering that:
1. Historical data has different formats than real-time data
2. Some tables have full history, some only have recent data
3. Data types differ between tables (DATETIME vs STRING)

**This document exists to STOP this recurring issue.**

---

## 📋 GOLDEN RULES (Read Every Time)

### Rule 1: Check Table Coverage FIRST

**BEFORE writing any query, check date range:**

```bash
# Quick check template
bq query --use_legacy_sql=false "
SELECT 
  MIN(settlementDate) as min_date,
  MAX(settlementDate) as max_date,
  COUNT(DISTINCT settlementDate) as unique_dates
FROM \`inner-cinema-476211-u9.uk_energy_prod.TABLE_NAME\`
"
```

### Rule 2: Know Your Two Architectures

| Data Type | Tables | Date Range | Data Type | Use For |
|-----------|--------|------------|-----------|---------|
| **Historical** | `bmrs_*` | 2024-01-01 to recent | DATETIME | Long-term analysis |
| **Real-Time** | `bmrs_*_iris` | Recent only | Various | Current operations |
| **Hybrid** | `demand_outturn` | Recent only | STRING | ⚠️ Limited use |

### Rule 3: Use UNION Pattern for Complete Timeline

**Template:**
```sql
WITH combined AS (
  -- Historical
  SELECT CAST(settlementDate AS DATE) as date, ...
  FROM `bmrs_TABLE_NAME`
  WHERE settlementDate < '2025-XX-XX'  -- Cutoff date
  
  UNION ALL
  
  -- Real-time
  SELECT CAST(settlementDate AS DATE) as date, ...
  FROM `bmrs_TABLE_NAME_iris`
  WHERE settlementDate >= '2025-XX-XX'  -- Cutoff date
)
SELECT * FROM combined
```

---

## 📊 TABLE COVERAGE MATRIX (31 Oct 2025)

| Table | Type | Date Range | Days | Data Type | Status |
|-------|------|------------|------|-----------|--------|
| **bmrs_bod** | Historical | 2024-01-01 → 2025-10-28 | 667 | DATETIME | ✅ Full |
| **bmrs_fuelinst** | Historical | 2024-01-01 → recent | 669 | DATETIME | ✅ Full |
| **bmrs_freq** | Historical | Unknown | ? | DATETIME | ⚠️ Check |
| **bmrs_mid** | Historical | 2024-01-01 → recent | ? | DATETIME | ✅ Full |
| **demand_outturn** | Hybrid | 2025-09-27 → 2025-10-25 | 29 | **STRING** | ⚠️ Recent only |
| **bmrs_bod_iris** | Real-time | Recent | ? | DATETIME | 🟢 Live |
| **bmrs_fuelinst_iris** | Real-time | Recent | ? | DATETIME | 🟢 Live |
| **bmrs_freq_iris** | Real-time | Recent | ? | DATETIME | 🟢 Live |

**⚠️ KEY ISSUE:** `demand_outturn` only has 29 days (Sept-Oct 2025), not full history!

---

## 🔧 DATA TYPE INCOMPATIBILITY FIXES

### Problem: Cannot JOIN different date types

| Scenario | Table A Type | Table B Type | Fix |
|----------|--------------|--------------|-----|
| Historical + Historical | DATETIME | DATETIME | ✅ Works directly |
| Historical + Hybrid | DATETIME | STRING | ⚠️ Cast both to DATE |
| Real-time + Real-time | DATETIME | DATETIME | ✅ Works directly |
| Historical + Real-time | DATETIME | DATETIME | ✅ Works with UNION |

### Universal Fix: Cast to DATE

```sql
-- ❌ WRONG - Type mismatch
SELECT *
FROM bmrs_bod b
JOIN demand_outturn d USING (settlementDate, settlementPeriod)

-- ✅ CORRECT - Cast to DATE
SELECT *
FROM (
  SELECT CAST(settlementDate AS DATE) as date, settlementPeriod, ...
  FROM bmrs_bod
) b
JOIN (
  SELECT CAST(settlementDate AS DATE) as date, settlementPeriod, ...
  FROM demand_outturn
) d USING (date, settlementPeriod)
```

---

## 📖 DOCUMENTED SOLUTIONS (Reference These!)

### Full Documentation

1. **[UNIFIED_ARCHITECTURE_HISTORICAL_AND_REALTIME.md](UNIFIED_ARCHITECTURE_HISTORICAL_AND_REALTIME.md)**
   - Complete architecture overview
   - UNION query patterns
   - Table naming conventions
   - **READ THIS FIRST** when working with multiple tables

2. **[PROJECT_CONFIGURATION.md](PROJECT_CONFIGURATION.md)**
   - Table schemas with correct column names
   - Data types documented
   - Common pitfalls section
   - **READ THIS** before writing queries

3. **[PRICE_DEMAND_CORRELATION_FIX.md](PRICE_DEMAND_CORRELATION_FIX.md)**
   - Recent fix for date type mismatches
   - Shows DATE casting pattern
   - **READ THIS** when joining tables fails

### Quick Templates

**Location:** [PROJECT_CONFIGURATION.md](PROJECT_CONFIGURATION.md) - Section: "Script Templates"

Available templates:
1. Basic BigQuery script
2. Google Sheets integration
3. **UNION query for Historical + IRIS** ← Use this!

---

## 🚨 COMMON MISTAKES (Don't Repeat These!)

### Mistake 1: Assuming Full History Everywhere

**❌ WRONG:**
```sql
-- Assumes demand_outturn has full 2024-2025 data
SELECT * FROM demand_outturn
WHERE settlementDate >= '2024-01-01'
-- Result: Only gets 29 days (Sept-Oct 2025)
```

**✅ CORRECT:**
```sql
-- Check coverage first
SELECT MIN(settlementDate), MAX(settlementDate)
FROM demand_outturn
-- Then adjust query to actual range
```

### Mistake 2: Ignoring Data Type Differences

**❌ WRONG:**
```sql
-- Direct join fails: DATETIME vs STRING
FROM bmrs_bod 
JOIN demand_outturn USING (settlementDate)
-- Error: incompatible types
```

**✅ CORRECT:**
```sql
-- Cast both to DATE
FROM (SELECT CAST(settlementDate AS DATE) as date, ...
      FROM bmrs_bod) b
JOIN (SELECT CAST(settlementDate AS DATE) as date, ...
      FROM demand_outturn) d USING (date)
```

### Mistake 3: Not Using UNION for Complete Timeline

**❌ WRONG:**
```sql
-- Only gets historical data
SELECT * FROM bmrs_fuelinst
WHERE publishTime >= '2024-01-01'
-- Missing recent IRIS data!
```

**✅ CORRECT:**
```sql
-- Combine both sources
SELECT * FROM bmrs_fuelinst WHERE publishTime < '2025-10-01'
UNION ALL
SELECT * FROM bmrs_fuelinst_iris WHERE publishTime >= '2025-10-01'
```

### Mistake 4: Using Wrong Project/Region

**❌ WRONG:**
```python
PROJECT_ID = "jibber-jabber-knowledge"  # Wrong!
LOCATION = "europe-west2"  # Wrong!
```

**✅ CORRECT:**
```python
PROJECT_ID = "inner-cinema-476211-u9"  # ✅
LOCATION = "US"  # ✅
```

---

## ✅ PRE-QUERY CHECKLIST (Use Every Time!)

Before running ANY new query:

- [ ] **Read this file** (STOP_DATA_ARCHITECTURE_REFERENCE.md)
- [ ] **Check table coverage**: Run MIN/MAX date query
- [ ] **Verify data types**: Check schema with `bq show --schema`
- [ ] **Choose approach**:
  - [ ] Single table (historical only)?
  - [ ] UNION query (historical + IRIS)?
  - [ ] Recent data only?
- [ ] **Handle date types**: Cast to DATE if joining different types
- [ ] **Verify project**: `inner-cinema-476211-u9`, region `US`
- [ ] **Test with LIMIT 10** first

---

## 🎯 DECISION TREE

```
START: Need to query data
    │
    ├─→ Single data type needed?
    │   ├─→ Historical only → Use bmrs_* tables (DATETIME)
    │   ├─→ Real-time only → Use bmrs_*_iris tables (DATETIME)
    │   └─→ Recent only → Check table coverage first!
    │
    ├─→ Complete timeline needed?
    │   └─→ Use UNION query (Historical + IRIS)
    │       └─→ See UNIFIED_ARCHITECTURE doc for template
    │
    ├─→ Need to JOIN tables?
    │   ├─→ Same data type? → Use USING (settlementDate, settlementPeriod)
    │   └─→ Different types? → Cast both to DATE
    │       └─→ See PRICE_DEMAND_CORRELATION_FIX doc
    │
    └─→ Long-term analysis (multiple months)?
        ├─→ Check each table coverage first!
        ├─→ demand_outturn: ONLY 29 days ⚠️
        ├─→ bmrs_bod: 667 days ✅
        └─→ bmrs_fuelinst: 669 days ✅
```

---

## 📚 WHERE TO FIND ANSWERS

| Question | Document | Section |
|----------|----------|---------|
| "What tables exist?" | UNIFIED_ARCHITECTURE | Table Inventory |
| "What columns exist?" | PROJECT_CONFIGURATION | Table Schemas |
| "How to join tables?" | PRICE_DEMAND_CORRELATION_FIX | Fixed Query |
| "How to UNION data?" | UNIFIED_ARCHITECTURE | Query Patterns |
| "What date ranges?" | **Run bq query first!** | - |
| "What data types?" | PROJECT_CONFIGURATION | Schema section |
| "Common mistakes?" | **This file** | Common Mistakes |
| "Why is join failing?" | PRICE_DEMAND_CORRELATION_FIX | Root Causes |

---

## 🔄 WHY WE KEEP REPEATING THIS

### Root Causes Identified:

1. **Architecture documentation exists but not consulted first**
   - Solution: Read THIS file before ANY query

2. **Table coverage assumed, not verified**
   - Solution: Always check MIN/MAX dates first

3. **Data type differences not immediately obvious**
   - Solution: Check schema before joining

4. **Templates not used**
   - Solution: Copy from PROJECT_CONFIGURATION.md

5. **No pre-query checklist**
   - Solution: Use checklist above ☝️

---

## 🎯 NEW WORKFLOW (Follow This!)

### For ANY New Analysis Script:

```bash
# 1. READ THIS FILE
cat STOP_DATA_ARCHITECTURE_REFERENCE.md

# 2. CHECK TABLE COVERAGE
bq query "SELECT MIN(date_column), MAX(date_column) FROM table_name"

# 3. CHECK SCHEMA
bq show --schema inner-cinema-476211-u9:uk_energy_prod.table_name

# 4. COPY TEMPLATE (don't start from scratch!)
# From PROJECT_CONFIGURATION.md - Script Templates section

# 5. RUN WITH LIMIT 10 FIRST
bq query --max_rows=10 "YOUR QUERY LIMIT 10"

# 6. ONLY THEN run full analysis
```

### For Joining Tables:

```bash
# 1. CHECK BOTH TABLE SCHEMAS
bq show --schema table_a | grep "date_column" -A 2
bq show --schema table_b | grep "date_column" -A 2

# 2. IF DIFFERENT TYPES → Cast to DATE
# 3. IF SAME TYPE → Use directly
# 4. TEST JOIN with LIMIT 10 first
```

---

## 🚦 STATUS INDICATORS

Add these to your analysis scripts:

```python
# At the top of EVERY script
print("⚠️  ARCHITECTURE CHECK:")
print("Have you:")
print("  1. Read STOP_DATA_ARCHITECTURE_REFERENCE.md? (Y/N)")
print("  2. Checked table date coverage? (Y/N)")
print("  3. Verified data types match? (Y/N)")
print("  4. Used correct PROJECT_ID? (Y/N)")
print()
input("Press Enter to continue only if all YES...")
```

---

## 📞 QUICK REFERENCE CARD

**Print this and keep visible:**

```
┌─────────────────────────────────────────────┐
│     DATA ARCHITECTURE QUICK REF              │
├─────────────────────────────────────────────┤
│ PROJECT: inner-cinema-476211-u9             │
│ REGION:  US                                 │
│                                             │
│ HISTORICAL: bmrs_*       (DATETIME, 667d)  │
│ REAL-TIME:  bmrs_*_iris  (DATETIME, recent)│
│ HYBRID:     demand_*     (STRING, 29d!)    │
│                                             │
│ JOINING? → Cast to DATE if types differ    │
│ TIMELINE? → Use UNION pattern              │
│ UNSURE? → Check date range first!          │
│                                             │
│ READ: STOP_DATA_ARCHITECTURE_REFERENCE.md  │
└─────────────────────────────────────────────┘
```

---

## ✅ ACTION ITEMS TO PREVENT RECURRENCE

### Immediate (Do Now):

- [x] Create this reference document
- [ ] Update PROJECT_CONFIGURATION.md with table coverage matrix
- [ ] Add pre-query checklist to README.md
- [ ] Create bq_check_coverage.sh utility script

### Process Changes:

1. **Always check documentation first** (this file)
2. **Always verify table coverage** (bq query)
3. **Always check data types before joining** (bq show --schema)
4. **Always use templates** (don't start from scratch)
5. **Always test with LIMIT 10 first**

### Documentation Links:

All these already exist - **USE THEM:**
- [UNIFIED_ARCHITECTURE_HISTORICAL_AND_REALTIME.md](UNIFIED_ARCHITECTURE_HISTORICAL_AND_REALTIME.md)
- [PROJECT_CONFIGURATION.md](PROJECT_CONFIGURATION.md)
- [PRICE_DEMAND_CORRELATION_FIX.md](PRICE_DEMAND_CORRELATION_FIX.md)

---

## 🎯 THE ANSWER TO "WHY DOES THIS KEEP HAPPENING?"

**Because we don't follow this workflow:**

1. ❌ Assume table coverage → ✅ **Check coverage first**
2. ❌ Assume data types match → ✅ **Verify schemas first**
3. ❌ Start from scratch → ✅ **Use templates**
4. ❌ Write full query → ✅ **Test with LIMIT 10**
5. ❌ Forget architecture → ✅ **Read this file first**

**THIS FILE IS THE SOLUTION. READ IT EVERY TIME.** ⚠️

---

**Last Updated:** 31 October 2025  
**Maintainer:** Document any new discoveries here  
**Next Update:** When new tables added or coverage changes  

**FILE LOCATION:** `/Users/georgemajor/GB Power Market JJ/STOP_DATA_ARCHITECTURE_REFERENCE.md`

**BOOKMARK THIS FILE.** 📌

# Analysis Sheet System - Implementation Guide

## 📋 Overview

Party categorization system for BSC/CUSC market participants. Enables tracking which companies are generators, suppliers, storage operators, etc.

---

## 🏗️ Database Structure (4 Tabs)

### 1. **Categories Tab**
**Purpose**: Master list of BSC/CUSC roles
**Columns**:
- Category ID (1-19)
- Category Name
- Description
- Code (3-4 letter abbreviation)
- BSC/CUSC classification
- Active (TRUE/FALSE)
- Notes

**19 Categories**:
1. Generator - Physical electricity generator
2. Supplier - Licensed electricity supplier
3. Network Operator - Transmission/distribution operator
4. Interconnector - Cross-border electricity link
5. Virtual Lead Party - Aggregated flexible assets
6. Storage Operator - Battery/pumped hydro
7. Distribution System Operator (DSO)
8. Transmission System Operator (TSO)
9. Non-Physical Trader
10. Party Agent
11. Data Aggregator
12. Meter Operator (MOP)
13. Data Collector (DC)
14. Licensed Distributor (LDSO)
15. Supplier Agent
16. Half Hourly Data Collector (HHDC)
17. Non Half Hourly Data Collector (NHHDC)
18. Meter Administrator (MA)
19. Balancing Mechanism Unit (BMU)

### 2. **Parties Tab**
**Purpose**: List of all BSC signatories and market participants
**Columns**:
- Party ID (P001, P002, ...)
- Party Name (full legal name)
- Short Name (abbreviation)
- Categories (comma-separated list, auto-populated)
- Registration Date
- Status (Active/Inactive)
- BSC Party ID (Elexon ID)
- Company Number (Companies House)
- Address
- Contact
- Website
- Is Generator (TRUE/FALSE quick filter)
- Is Supplier (TRUE/FALSE quick filter)
- Is Storage (TRUE/FALSE quick filter)
- Notes

**Data Sources**:
- Elexon BSC Signatories list
- NESO generator registry
- Interconnector operators
- Known VLP operators (batteries)

### 3. **Party_Category Tab** (Link Table)
**Purpose**: Many-to-many relationships between parties and categories
**Structure**: One row per party-category combination

**Columns**:
- Party ID (foreign key to Parties)
- Category Name (foreign key to Categories)
- Source (where data came from: Elexon API, NESO API, Manual)
- Confidence (High/Medium/Low)
- Verified (TRUE/FALSE)
- Added Date
- Added By (user/system)
- Notes

**Example Data**:
```
Party ID | Category Name           | Source      | Confidence | Verified
---------|------------------------|-------------|------------|----------
P001     | Generator              | Elexon API  | High       | TRUE
P001     | Balancing Mechanism Unit| NESO API   | High       | TRUE
P002     | Supplier               | Elexon API  | High       | TRUE
P010     | Storage Operator       | Manual      | Medium     | FALSE
P010     | Virtual Lead Party     | Manual      | Medium     | FALSE
```

**Why Many-to-Many?**
- Companies can have multiple roles (e.g., EDF = Generator + Supplier)
- Flexibility to add new categories without restructuring
- Audit trail (who added, when, confidence level)

### 4. **Party_Wide Tab** (Boolean View)
**Purpose**: Pivot table showing TRUE/FALSE for each party-category combination
**Layout**: Each category becomes a column

**Structure**:
```
Party ID | Party Name | Generator | Supplier | Storage | ... | Total Categories
---------|------------|-----------|----------|---------|-----|------------------
P001     | Drax       | TRUE      | FALSE    | FALSE   | ... | 3
P002     | EDF        | TRUE      | TRUE     | FALSE   | ... | 5
P010     | Flexgen    | FALSE     | FALSE    | TRUE    | ... | 2
```

**Formulas** (row 2 template):
```javascript
// Column C (Generator check):
=IF(COUNTIFS(Party_Category!$A:$A,$A2,Party_Category!$B:$B,C$1)>0,"TRUE","FALSE")

// Column Z (Total Categories):
=COUNTIF(C2:Y2,"TRUE")
```

**Benefits**:
- Fast filtering (filter by TRUE/FALSE)
- Visual overview (see all roles at a glance)
- Export-friendly format

---

## 🚀 Implementation Steps

### Step 1: Create Sheet Structure
```bash
python3 create_analysis_sheet_structure.py
```

**Creates**:
- Categories tab with 19 BSC/CUSC roles
- Parties tab with sample data
- Party_Category link table with sample links
- Party_Wide boolean view with formulas

### Step 2: Import BSC Parties
```bash
python3 import_elexon_parties.py
```

**Imports**:
- Known generators (Drax, EDF, Sizewell, etc.)
- Interconnectors (IFA, IFA2, BritNed, Nemo)
- Storage/VLP operators (Flexgen, Harmony Energy)
- DNOs (UKPN, SSEN, NGED)
- Major suppliers (Octopus, OVO, Bulb)

**Auto-creates Party_Category links** based on party types

### Step 3: Query NESO APIs (Future)
```bash
python3 query_neso_generators.py  # TODO
```

**Will fetch**:
- TEC (Transmission Entry Capacity) holders
- BM Unit registrations
- Interconnector capacities

### Step 4: Manual Verification
1. Open Google Sheets: [Dashboard](https://docs.google.com/spreadsheets/d/1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA/edit)
2. Navigate to Analysis tabs
3. Review party data
4. Add missing parties manually
5. Verify Party_Category links
6. Check Party_Wide formulas populated correctly

---

## 📊 Use Cases

### 1. Find All Generators
```
Filter Parties tab: "Is Generator" = TRUE
OR
Filter Party_Wide tab: "Generator" column = TRUE
```

### 2. Find Multi-Role Companies
```
Sort Party_Wide tab by "Total Categories" (descending)
Companies with >1 categories shown first
```

### 3. Identify VLP Operators
```
Filter Party_Wide tab: "Virtual Lead Party" = TRUE
Cross-reference with "Storage Operator" = TRUE
```

### 4. Export for Analysis
```
Party_Wide tab → File → Download → CSV
Import into Python/Excel for further analysis
```

---

## 🔍 Data Sources

### Elexon (BSC Parties)
- **URL**: https://www.elexon.co.uk/bsc-related-documents/participant-information/
- **API**: Elexon API (requires API key)
- **Content**: BSC signatories, party IDs, contact details

### NESO (Generators/Interconnectors)
- **URL**: https://www.neso.energy/data-portal
- **Datasets**:
  - TEC Register (transmission-connected generators)
  - BM Unit data
  - Interconnector capacities
- **Format**: CSV downloads or API

### Companies House
- **URL**: https://find-and-update.company-information.service.gov.uk/
- **Content**: Company numbers, registered addresses, directors

---

## 🎯 Next Steps

1. **Run creation script** when network stable
2. **Verify formulas** in Party_Wide tab
3. **Query NESO APIs** for comprehensive generator list
4. **Manual additions**:
   - Small generators (<50MW)
   - Recent BSC signatories
   - Emerging storage operators
5. **Regular updates** (monthly):
   - New BSC signatories
   - Company name changes
   - Status updates (Active/Inactive)

---

## 📁 Related Files

- `create_analysis_sheet_structure.py` - Creates 4 tabs
- `import_elexon_parties.py` - Imports BSC parties
- `query_neso_generators.py` - NESO API queries (TODO)
- `ANALYSIS_SHEET_GUIDE.md` - This file

---

## ⚡ Quick Reference

### Add New Party (Manual)
1. Go to Parties tab
2. New row: Assign Party ID (next available P###)
3. Fill name, short name, BSC ID, status
4. Go to Party_Category tab
5. Add row for each category (e.g., P###, "Generator", "Manual", "High", "TRUE")
6. Party_Wide tab auto-updates via formulas

### Add New Category
1. Go to Categories tab
2. New row: Next Category ID, name, description, code
3. Party_Category dropdown auto-updates
4. Add new column to Party_Wide tab with formula

### Find Company's Roles
```
1. Search Parties tab for company name
2. Note Party ID (e.g., P015)
3. Filter Party_Category tab: Party ID = P015
4. All categories listed
```

---

**Created**: December 30, 2025
**Status**: Structure designed, awaiting network-stable deployment
**Priority**: Medium (analysis feature, not critical path)


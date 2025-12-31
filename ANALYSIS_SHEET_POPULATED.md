# Analysis Sheet Database - Population Complete ✅

**Date**: December 30, 2025  
**Status**: Fully populated and operational

## 📊 System Overview

4-tab relational database for UK energy market party categorization:

| Tab | Purpose | Records | Status |
|-----|---------|---------|--------|
| **Categories** | BSC/CUSC role definitions | 19 | ✅ Complete |
| **Parties** | Market participants | 18 | ✅ Populated |
| **Party_Category** | Many-to-many links | 35 | ✅ Populated |
| **Party_Wide** | Boolean pivot view | 18×20 | ✅ Formulas active |

## 🎯 Populated Data

### Categories (19 BSC/CUSC Roles)
- Generator (GENR)
- Supplier (SUPP)
- Network Operator (NETO)
- Interconnector (INTC)
- Virtual Lead Party (VLP)
- Balancing Mechanism Unit (BMU)
- Distribution System Operator (DSO)
- Transmission System Operator (TSO)
- Electricity Storage (STOR)
- Demand Side Response (DSR)
- Aggregator (AGGR)
- Licensed Distribution Network (LDN)
- Transmission Owner (TO)
- Non-Physical Trader (NPT)
- Offshore Transmission Owner (OFTO)
- Embedded Generator (EG)
- CHP Unit (CHP)
- Licensed Supplier (LS)
- Party Agent (PA)

### Parties (18 Market Participants)

**Generators**:
- Drax Power Limited (DRAX)
- EDF Energy (EDF)
- RWE Generation UK (RWE)
- SSE Generation Limited (SSE)

**Interconnectors**:
- BritNed Interconnector (BRITN)
- ElecLink (ELECL)
- IFA Interconnector (IFA)
- IFA2 Interconnector (IFA2)

**Suppliers**:
- Bulb Energy Limited (BULB)
- Octopus Energy Limited (OCTOP)
- OVO Energy Limited (OVO)

**Distribution Network Operators**:
- Northern Powergrid (NPG)
- Scottish and Southern Electricity Networks (SSEN)
- UK Power Networks (UKPN)

**Storage/VLP**:
- Flexgen Battery Storage (FBPGM)
- Gresham House VLP (FFSEN)

**TSO**:
- National Energy System Operator (NESO)

**DSR**:
- Kiwi Power (KIWI)

## 🔗 Sample Party-Category Links

| Party | Categories |
|-------|-----------|
| Drax | Generator, Balancing Mechanism Unit |
| BritNed | Interconnector, Balancing Mechanism Unit |
| Bulb Energy | Supplier, Licensed Supplier |
| UKPN | Distribution System Operator, Network Operator |
| Flexgen | Electricity Storage, Virtual Lead Party, Balancing Mechanism Unit |
| NESO | Transmission System Operator |

## 📈 Party_Wide Boolean Matrix

**Structure**: Party ID | Party Name | [19 Category Columns] | Total Categories

**Formulas**:
- Party Name: `=IFERROR(VLOOKUP(A2,Parties!A:B,2,FALSE),"")`
- Each category: `=IF(COUNTIFS(Party_Category!$A:$A,$A2,Party_Category!$B:$B,C$1)>0,"TRUE","FALSE")`
- Total: `=COUNTIF(C2:U2,"TRUE")`

**Example Output**:
```
P003 | Drax Power Ltd | TRUE  | FALSE | FALSE | FALSE | FALSE | TRUE  | ...
P001 | BritNed        | FALSE | FALSE | FALSE | TRUE  | FALSE | TRUE  | ...
P002 | Bulb Energy    | FALSE | TRUE  | FALSE | FALSE | FALSE | FALSE | ...
```

## 🚀 Usage Examples

### 1. Find All Generators
**Query**: Filter Parties tab where Party_Category contains "Generator"
```
Party_Category tab → Filter Column B = "Generator"
Result: P003 (Drax), P004 (EDF), P011 (RWE), P012 (SSE)
```

### 2. Find Multi-Role Companies
**Query**: Party_Wide tab → Filter "Total Categories" > 2
```
Parties with multiple roles (e.g., generator + storage + VLP)
```

### 3. List All VLP Operators
**Query**: Party_Wide tab → Filter "Virtual Lead Party" = TRUE
```
Result: Flexgen (P015), Gresham House (P016)
```

### 4. Add New Party
1. **Parties tab**: Add row with Party ID, name, BSC ID
2. **Party_Category tab**: Add links to relevant categories
3. **Party_Wide tab**: Copy formula row down to new party
4. **Auto-update**: TRUE/FALSE flags populate automatically

## 📋 Data Sources

### Current Import (18 parties)
- **BM Units**: Elexon API query (3 parties)
- **Suppliers**: Manual list (3 parties)
- **Known Major Players**: Curated list (12 parties)

### Future Enhancements
- **NESO TEC Register**: Transmission-connected generators
- **NESO Data Portal**: All BM Unit registrations
- **Elexon Party List**: Complete BSC signatories (target: 500+)
- **Companies House**: Company details verification

## 🔧 Maintenance

### Adding More Parties
```bash
# Edit import_elexon_parties.py to add more parties
python3 import_elexon_parties.py

# Or manually:
# 1. Add to Parties tab
# 2. Add links in Party_Category tab
# 3. Copy Party_Wide formulas down
```

### Verifying Data Integrity
```bash
python3 <<'EOF'
import gspread
from google.oauth2.service_account import Credentials

SHEET_ID = "1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA"
creds = Credentials.from_service_account_file("inner-cinema-credentials.json", scopes=['https://www.googleapis.com/auth/spreadsheets'])
gc = gspread.authorize(creds)
wb = gc.open_by_key(SHEET_ID)

# Check for orphaned links
party_cat = wb.worksheet('Party_Category')
parties = wb.worksheet('Parties')
categories = wb.worksheet('Categories')

links = party_cat.get('A2:B100')
party_ids = [r[0] for r in parties.get('A2:A100') if r]
cat_names = [r[1] for r in categories.get('B2:B30') if r]

orphaned = []
for link in links:
    if link and len(link) >= 2:
        if link[0] not in party_ids:
            orphaned.append(f"Party {link[0]} not found")
        if link[1] not in cat_names:
            orphaned.append(f"Category {link[1]} not found")

if orphaned:
    print("⚠️  Data integrity issues:")
    for issue in orphaned:
        print(f"   • {issue}")
else:
    print("✅ Data integrity check passed")
EOF
```

## 📊 Access

**Google Sheets**: https://docs.google.com/spreadsheets/d/1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA/edit

**Navigate to**:
- Categories tab: Role definitions
- Parties tab: All market participants
- Party_Category tab: Relationship mapping
- Party_Wide tab: Boolean matrix view

## 🎉 Completion Status

- ✅ All 4 tabs created
- ✅ 19 categories defined
- ✅ 18 parties populated
- ✅ 35 relationships mapped
- ✅ Boolean formulas active
- ✅ Data validation working
- ✅ Import script tested
- ✅ Documentation complete

**Next Steps**:
1. Query NESO APIs for more generator data (future)
2. Add remaining BSC signatories (target: 500+)
3. Create analysis dashboards (charts, summaries)
4. Integrate with battery VLP revenue analysis

---

*Last Updated: December 30, 2025*  
*See: ANALYSIS_SHEET_GUIDE.md for detailed system documentation*

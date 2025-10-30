# DNO COVERAGE ANALYSIS REPORT
**Analysis Date:** September 13, 2025
**Dataset:** jibber-jabber-knowledge.uk_energy_insights

## 📊 COMPLETE UK DNO LIST vs OUR COVERAGE

| MPAN ID | DNO Key         | DNO Name                                                      | ✅ Have Data | 📊 Data Type                      | 🗂️ Tables  |
| ------- | --------------- | ------------------------------------------------------------- | ----------- | -------------------------------- | --------- |
| 10      | UKPN-EPN        | UK Power Networks (Eastern)                                   | ✅ **YES**   | DUoS, Network, Transformers, LCT | 10 tables |
| 11      | NGED-EM         | National Grid Electricity Distribution – East Midlands (EMID) | ❌ No        | -                                | -         |
| 12      | UKPN-LPN        | UK Power Networks (London)                                    | ✅ **YES**   | DUoS, Network, Fault Levels, LCT | 6 tables  |
| 13      | SP-Manweb       | SP Energy Networks (SPM)                                      | ❌ No        | -                                | -         |
| 14      | NGED-WM         | National Grid Electricity Distribution – West Midlands (WMID) | ❌ No        | -                                | -         |
| 15      | NPg-NE          | Northern Powergrid (North East)                               | ❌ No        | -                                | -         |
| 16      | ENWL            | Electricity North West                                        | ❌ No        | -                                | -         |
| 17      | SSE-SHEPD       | Scottish Hydro Electric Power Distribution (SHEPD)            | ❌ No        | -                                | -         |
| 18      | SP-Distribution | SP Energy Networks (SPD)                                      | ❌ No        | -                                | -         |
| 19      | UKPN-SPN        | UK Power Networks (South Eastern)                             | ✅ **YES**   | DUoS, 33kV Circuits, Losses, LCT | 4 tables  |
| 20      | SSE-SEPD        | Southern Electric Power Distribution (SEPD)                   | ❌ No        | -                                | -         |
| 21      | NGED-SWales     | National Grid Electricity Distribution – South Wales (SWALES) | ❌ No        | -                                | -         |
| 22      | NGED-SW         | National Grid Electricity Distribution – South West (SWEST)   | ❌ No        | -                                | -         |
| 23      | NPg-Y           | Northern Powergrid (Yorkshire)                                | ❌ No        | -                                | -         |

## 📈 COVERAGE SUMMARY

- **✅ DNOs with Data:** 3 out of 14 (21.4% coverage)
- **❌ Missing DNOs:** 11 out of 14 (78.6% missing)

### ✅ COMPLETE COVERAGE (3/14 DNOs):
1. **UKPN-EPN** (MPAN 10): UK Power Networks (Eastern)
2. **UKPN-LPN** (MPAN 12): UK Power Networks (London)
3. **UKPN-SPN** (MPAN 19): UK Power Networks (South Eastern)

### ❌ MISSING COVERAGE (11/14 DNOs):
1. **NGED-EM** (MPAN 11): National Grid Electricity Distribution – East Midlands
2. **SP-Manweb** (MPAN 13): SP Energy Networks (SPM)
3. **NGED-WM** (MPAN 14): National Grid Electricity Distribution – West Midlands
4. **NPg-NE** (MPAN 15): Northern Powergrid (North East)
5. **ENWL** (MPAN 16): Electricity North West
6. **SSE-SHEPD** (MPAN 17): Scottish Hydro Electric Power Distribution
7. **SP-Distribution** (MPAN 18): SP Energy Networks (SPD)
8. **SSE-SEPD** (MPAN 20): Southern Electric Power Distribution
9. **NGED-SWales** (MPAN 21): National Grid Electricity Distribution – South Wales
10. **NGED-SW** (MPAN 22): National Grid Electricity Distribution – South West
11. **NPg-Y** (MPAN 23): Northern Powergrid (Yorkshire)

## 📋 DETAILED DATA INVENTORY

### ✅ UKPN (Complete Coverage - 3/3 License Areas)

#### DUoS Charging Data:
- **ukpn_duos_charges_annex1**: 243 statements (domestic/commercial tariffs)
  - Coverage: All 3 areas (EPN, LPN, SPN)
  - Years: 2024/25, 2025/26, 2026/27
- **ukpn_duos_charges_annex2**: 1,325 statements (EHV/LDNO charges)
  - Coverage: EPN area only
  - Years: 2024/25, 2025/26, 2026/27

#### Network Infrastructure Data by Area:

**UKPN-EPN (Eastern - MPAN 10)** - Most Comprehensive:
- **ukpn_ltds_circuit_data**: 4,990 circuit records (shared with LPN)
- **ukpn_ltds_fault_levels**: 2,026 fault level records (shared with LPN)
- **ukpn_ltds_operational_restrictions**: 93 operational constraint records
- **ukpn_primary_transformer_flows**: 82,739 transformer flow records
- **ukpn_secondary_transformers**: 74,719 secondary transformer records
- **ukpn_network_losses**: 36 loss records (shared across all areas)
- **ukpn_low_carbon_technologies**: 34,845 LCT connection records (shared)

**UKPN-LPN (London - MPAN 12)** - Moderate Coverage:
- **ukpn_ltds_circuit_data**: Shared with EPN (4,990 records)
- **ukpn_ltds_fault_levels**: Shared with EPN (2,026 records)
- **ukpn_network_losses**: Shared across all areas (36 records)
- **ukpn_low_carbon_technologies**: Shared across all areas (34,845 records)

**UKPN-SPN (South Eastern - MPAN 19)** - Limited Coverage:
- **ukpn_33kv_circuit_data**: 73,315 circuit records (SPN only)
- **ukpn_network_losses**: Shared across all areas (36 records)
- **ukpn_low_carbon_technologies**: Shared across all areas (34,845 records)

#### Total UKPN Data Volume:
- **Total Records**: 274,278 across 10 tables
- **DUoS Statements**: 1,568 charging statements
- **Network Assets**: 272,710 infrastructure records

### 🔍 Other Potential DNO Tables Found:
- **dno_distribution_data_view**: Index of DNO-related tables
- **gis_boundaries_for_gb_dno_license_areas**: Geographic boundaries
- **postcode_dno_gsp_mapping**: Postcode to DNO mapping (appears empty)

## 💡 RECOMMENDATIONS

### Priority 1: High-Value DNOs (Large Coverage Areas)
1. **SSEN** (SSE-SHEPD + SSE-SEPD): Scotland + Southern England
2. **NGED** (4 license areas): Midlands + South West + Wales
3. **Northern Powergrid** (NPg-NE + NPg-Y): North East + Yorkshire

### Priority 2: Remaining Networks
4. **SP Energy Networks** (SP-Distribution + SP-Manweb): Scotland + North Wales
5. **ENWL**: North West England

### Data Collection Strategy:
- **UKPN**: ✅ Complete - use as template for other DNOs
- **Target Data Types**: DUoS charges, network capacity, outage data, connection data
- **Geographic Priority**: Focus on high-density population areas first
- **Data Standards**: Standardize collection format based on UKPN success

## 🎯 IMPACT ANALYSIS

### Current Coverage:
- **Geographic**: Primarily London, Eastern, and South Eastern England (UKPN areas)
- **Population**: ~18 million people (approximately 25% of UK population)
- **Data Quality**: High - comprehensive DUoS and network infrastructure data

### Missing Coverage:
- **Scotland**: No SSEN data (SHEPD/SEPD)
- **North England**: No Northern Powergrid data
- **Midlands**: No NGED data
- **Wales**: No NGED/SP Manweb data
- **North West**: No ENWL data

**Business Impact**: Limited ability to perform nationwide distribution analysis, pricing comparisons, or network planning across all UK regions.

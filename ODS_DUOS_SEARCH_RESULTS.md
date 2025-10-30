# OpenDataSoft DUoS Data Search Results
**Date:** 29 October 2025  
**Search Scope:** All 4 DNO OpenDataSoft Portals + Huwise Hub  
**Total Datasets Found:** 157

---

## 🔍 Search Summary

Automated discovery of **all datasets** across DNO OpenDataSoft portals to find DUoS charging rate data.

### Portals Searched
- ✅ **UKPN** - ukpowernetworks.opendatasoft.com (123 datasets)
- ✅ **NPg** - northernpowergrid.opendatasoft.com (86 datasets)
- ✅ **ENWL** - electricitynorthwest.opendatasoft.com (85 datasets)
- ✅ **SPEN** - spenergynetworks.opendatasoft.com (118 datasets)
- ✅ **Public Hub** - public.opendatasoft.com (372 datasets)

---

## 📊 DUoS Charging Data Found

### ✅ UKPN - Complete DUoS Data Available

**Dataset 1: Annex 1 (Time-of-Use Rates)** ✅ ALREADY DOWNLOADED
- **Dataset ID:** `ukpn-distribution-use-of-system-charges-annex-1`
- **Records:** 243
- **License:** CC BY 4.0
- **Last Updated:** 2025-02-28
- **Content:** Time-of-use charging bands (Red/Amber/Green) with unit rates
- **Export URL:** https://ukpowernetworks.opendatasoft.com/explore/dataset/ukpn-distribution-use-of-system-charges-annex-1/export/?format=csv
- **Status:** ✅ Downloaded (729 records across EPN/LPN/SPN)

**Dataset 2: Annex 2 (EHV/LDNO Charges)**
- **Dataset ID:** `ukpn-distribution-use-of-system-charges-annex-2`
- **Records:** 1,325
- **License:** CC BY 4.0
- **Last Updated:** 2025-02-18
- **Content:** Extra High Voltage properties and LDNO charges
- **Export URL:** https://ukpowernetworks.opendatasoft.com/explore/dataset/ukpn-distribution-use-of-system-charges-annex-2/export/?format=csv
- **Status:** ⏳ Not yet downloaded (may be useful for commercial customers)

---

### ❌ NPg - NO DUoS Charging Data on ODS

**Datasets Found (17 total):**
- ✅ DFES (Distribution Future Energy Scenarios) - forecasts and scenarios
- ✅ Site utilisation - capacity and headroom
- ✅ Primary operational metering - network monitoring
- ✅ LTDS Appendix 9 - development proposals
- ✅ Embedded Capacity Register
- ✅ DNO boundary data

**DUoS Data Status:** ❌ **NONE FOUND**

**What's Missing:**
- No time-of-use charging bands
- No unit rate schedules
- No Annex 1/2 charging statements

**Required Action:**
Download DUoS charging statements from NPg website:
- Website: https://www.northernpowergrid.com/asset-owner-our-network/charging-methodology
- Format: Excel/PDF statements
- DNOs: NE (15), Y (23)

---

### ❌ ENWL - NO DUoS Charging Data on ODS

**Datasets Found (32 total):**
- ✅ DFES data (primary sites, BSP sites, local authority breakdowns)
- ✅ Network capacity (11kV, 6.6kV, distribution transformers)
- ✅ Substation polygons and service areas
- ✅ LV headroom and peak demand (monitored/unmonitored)
- ✅ Embedded Capacity Registers (1-3)
- ✅ Smart meter installations
- ✅ Low Carbon Technology (LCT) data

**DUoS Data Status:** ❌ **NONE FOUND**

**What's Missing:**
- No charging schedules
- No unit rates or tariff information
- No time-of-use bands

**Required Action:**
Download DUoS charging statements from ENWL website:
- Website: https://www.enwl.co.uk/about-us/regulatory-information/
- Format: Excel/PDF statements
- DNO: ENWL (16)

---

### ❌ SPEN - NO DUoS Charging Data on ODS

**Datasets Found (66 total):**
- ✅ LTDS (Long Term Development Statement) appendices:
  - Circuit data, system loads, transformer data
  - Fault levels, embedded generation
  - Connection activity, predicted changes
  - Substation abbreviation codes
- ✅ DFES data (site forecasts, licence breakdowns)
- ✅ Network Development Plan (NDP) data
- ✅ Customer connection profiles (census areas, primary substations, LV transformers, HV feeders)
- ✅ Operational forecasting (6.4M+ records!)
- ✅ Network flow dataset (16M+ records!)
- ✅ Embedded Capacity Register
- ✅ Distribution Network Options Assessments (DNOA)

**DUoS Data Status:** ❌ **NONE FOUND**

**What's Missing:**
- No DUoS charging schedules
- No time-of-use tariff bands
- No unit rate tables

**Required Action:**
Download DUoS charging statements from SPEN website:
- Website: https://www.spenergynetworks.co.uk/pages/use_of_system_charges.aspx
- Format: Excel/PDF statements
- DNOs: SPM (13), SPD (18)

---

## 📋 Summary Table

| DNO Group | Portal | Datasets | DUoS Data? | Action Required |
|-----------|--------|----------|------------|-----------------|
| **UKPN** | ✅ Yes | 39 | ✅ **YES** | ✅ Already downloaded |
| **NPg** | ✅ Yes | 17 | ❌ No | 🌐 Download from website |
| **ENWL** | ✅ Yes | 32 | ❌ No | 🌐 Download from website |
| **SPEN** | ✅ Yes | 66 | ❌ No | 🌐 Download from website |
| **NGED** | ❌ No portal | - | ❌ No | 🌐 Download from website |
| **SSEN** | ❌ No portal | - | ❌ No | 🌐 Download from website |

---

## 🎯 Key Findings

### Why Only UKPN Has DUoS Data on ODS

**UKPN is unique** in publishing their charging schedules via OpenDataSoft API. The data includes:
- Complete time-of-use bands (Red/Amber/Green)
- Unit rates (p/kWh) by voltage class
- Valid date ranges
- All three license areas (EPN, LPN, SPN)

**Other DNOs** publish DUoS data on their own websites as:
- Excel workbooks (NGED, SPEN, NPg)
- PDF statements (SSEN)
- Interactive web calculators (some)

### What Data IS Available on Other ODS Portals

All DNO portals share similar types of operational data:
1. **Network Capacity** - Headroom, utilisation, constraints
2. **DFES** - Future energy scenario forecasts
3. **Embedded Generation** - Solar, wind, storage connections
4. **Network Topology** - Substations, circuits, transformers
5. **LTDS** - Long-term development plans
6. **Demand Profiles** - Load curves, peak demand

**But NOT charging/tariff information!**

---

## 📁 Files Generated

1. **ods_datasets_discovery_20251029_190936.csv** - Complete dataset catalog (157 rows)
2. **ods_datasets_discovery_20251029_190936.json** - Detailed metadata with export URLs
3. **THIS FILE** - Summary analysis and findings

---

## 🔄 Next Steps

### Immediate (Can Do Now)
1. ✅ **UKPN Annex 1** - Already downloaded ✅
2. ⏳ **UKPN Annex 2** - Download for commercial/EHV customers (optional)

### Short Term (Website Downloads)
3. 🌐 **NPg** - Download 2 license areas from website
4. 🌐 **ENWL** - Download 1 license area from website
5. 🌐 **SPEN** - Download 2 license areas from website
6. 🌐 **NGED** - Download 4 license areas from website (no ODS portal)
7. 🌐 **SSEN** - Download 2 license areas from website (no ODS portal)

### Medium Term (Parsing & Integration)
8. 📊 Parse all Excel/PDF files to extract charging schedules
9. 🔄 Normalize all data to standard schema (14 columns per CLAUDE_duos.md)
10. 💾 Upload to BigQuery table
11. 📈 Add to dashboard

---

## 🌐 Website Download URLs

### NPg (Northern Powergrid)
- **Website:** https://www.northernpowergrid.com/asset-owner-our-network/charging-methodology
- **Page:** Charging Statements Archive
- **Format:** Excel workbooks
- **DNOs:** NE (15), Y (23)

### ENWL (Electricity North West)
- **Website:** https://www.enwl.co.uk/about-us/regulatory-information/
- **Page:** Use of System Charges
- **Format:** Excel workbooks
- **DNO:** ENWL (16)

### SPEN (SP Energy Networks)
- **Website:** https://www.spenergynetworks.co.uk/pages/use_of_system_charges.aspx
- **Page:** Use of System Charges
- **Format:** Excel workbooks
- **DNOs:** SPM (13), SPD (18)

### NGED (National Grid Electricity Distribution)
- **Website:** https://www.nationalgrid.co.uk/electricity-distribution/network-and-assets/charging-statements
- **Page:** Charging Statements Archive
- **Format:** Excel workbooks
- **DNOs:** EMID (11), WMID (14), SWALES (21), SWEST (22)

### SSEN (Scottish & Southern Electricity Networks)
- **Website:** https://www.ssen.co.uk/about-ssen/dso/charging-and-network-access/
- **Page:** Schedule of Charges
- **Format:** Excel/PDF
- **DNOs:** SHEPD (17), SEPD (20)

---

## 📊 Progress Tracker

### DUoS Data Collection Status

**Completed: 3/14 DNOs (21.4%)**
- ✅ EPN (Eastern Power Networks) - UKPN
- ✅ LPN (London Power Networks) - UKPN
- ✅ SPN (South Eastern Power Networks) - UKPN

**Pending: 11/14 DNOs (78.6%)**
- ⏳ EMID, WMID, SWALES, SWEST (NGED) - 4 DNOs
- ⏳ NE, Y (NPg) - 2 DNOs
- ⏳ ENWL (ENWL) - 1 DNO
- ⏳ SPM, SPD (SPEN) - 2 DNOs
- ⏳ SHEPD, SEPD (SSEN) - 2 DNOs

---

## 💡 Lessons Learned

1. **UKPN is the exception, not the rule** - They're the only DNO with DUoS data on OpenDataSoft
2. **ODS portals focus on network operations** - Capacity, forecasts, topology - not tariffs
3. **Charging data lives on DNO websites** - Excel/PDF format, manual download required
4. **No universal API for DUoS data** - Each DNO has own publishing approach
5. **Website scraping will be necessary** - For 11 remaining DNOs

---

## 🔧 Technical Notes

### Search Methodology
- Used OpenDataSoft v1 API: `/api/datasets/1.0/search/`
- Listed ALL datasets (up to 1000 per portal)
- Filtered by keywords: duos, distribution, charges, charging, tariff, unit rate, etc.
- Exported full metadata including licenses, record counts, export URLs

### Discovery Script
- **File:** `discover_ods_datasets.py`
- **Runtime:** ~12 seconds
- **Rate Limiting:** 1 second between requests (respectful)
- **Output:** CSV + JSON with full metadata

---

**Report Generated:** 2025-10-29 19:15 UTC  
**Author:** GB Power Market JJ Project  
**Status:** Discovery Complete ✅

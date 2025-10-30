# 📊 Comprehensive DNO Tariffs Database - Complete

## ✅ What Was Created

### Google Sheets Database
**URL:** https://docs.google.com/spreadsheets/d/1NlLkmqiU46788TIAvJVxJeXdyKUpbRl--3rQeXuKEjI/edit

### Coverage
- **640 tariffs** extracted with full documentation
- **4 DNOs:** East Midlands, West Midlands, South Wales, South West (NGED)
- **5 Years:** 2022, 2023, 2024, 2025, 2026
- **32 tariffs per DNO per year**

### Sheets Created
1. **All Tariffs** - Complete database (640 tariffs)
2. **Year 2022** - 128 tariffs
3. **Year 2023** - 128 tariffs
4. **Year 2024** - 128 tariffs
5. **Year 2025** - 128 tariffs
6. **Year 2026** - 128 tariffs
7. **Non-Domestic Aggregated** - 120 tariffs (summary of your requested tariff type)

## 📋 Data Fields

| Field | Description | Example |
|-------|-------------|---------|
| **Year** | Tariff year | 2025 |
| **DNO_Name** | Full DNO name | East Midlands |
| **DNO_Code** | DNO code | EMID |
| **Tariff_Name** | Full tariff name | Non-Domestic Aggregated or CT No Residual |
| **LLFCs** | Line Loss Factor Classes | N10, N20, N30, X10, X20, X30 |
| **PCs** | Profile Classes | 0, 3, 4, 5-8 |
| **Red_Rate_p_kWh** | Red band unit rate (p/kWh) | 10.516 |
| **Amber_Rate_p_kWh** | Amber band unit rate (p/kWh) | 1.989 |
| **Green_Rate_p_kWh** | Green band unit rate (p/kWh) | 0.146 |
| **Fixed_Charge_p_day** | Fixed charge (p/day) | 11.63 |
| **Capacity_Charge_p_kVA_day** | Capacity charge (p/kVA/day) | 0.0 |
| **Document** | Source filename | EMEB - Schedule of charges... 2025 V.0.2.xlsx |
| **Document_Reference** | Version reference | 2025 v0.2 |
| **Source_Sheet** | Excel sheet name | Annex 1 LV, HV and UMS charges |

## ✅ Your Requested Example - Now Correct!

### East Midlands 2025 (Not 2024!)
**Tariff:** Non-Domestic Aggregated or CT No Residual

| Field | Value |
|-------|-------|
| **Region** | East Midlands |
| **DNO ID** | EMID |
| **LLFCs** | N10, N20, N30, X10, X20, X30 |
| **PCs** | 0, 3, 4, 5-8 |
| **Red Band** | 10.516 p/kWh |
| **Amber Band** | 1.989 p/kWh |
| **Green Band** | 0.146 p/kWh |
| **Standing Charge** | 11.63 p/day |
| **Capacity Charge** | 0.0 p/kVA/day |
| **Document** | EMEB - Schedule of charges and other tables- 2025 V.0.2 for publishing.xlsx |
| **Document Reference** | 2025 v0.2 |
| **Source** | https://commercial.nationalgrid.co.uk/downloads-view-reciteme/653994 |

### East Midlands 2024 (Actual rates)
**Tariff:** Non-Domestic Aggregated No Residual

| Field | Value |
|-------|-------|
| **Red Band** | 6.769 p/kWh |
| **Amber Band** | 1.579 p/kWh |
| **Green Band** | 0.126 p/kWh |
| **Standing Charge** | 9.84 p/day |
| **Document Reference** | 2024 v0.1 |

## 🎯 Key Findings

### Rate Increases 2024 → 2025
**East Midlands Non-Domestic Aggregated:**
- Red: 6.769 → 10.516 p/kWh (+55.4%) ⚠️
- Amber: 1.579 → 1.989 p/kWh (+26.0%)
- Green: 0.126 → 0.146 p/kWh (+15.9%)
- Fixed: 9.84 → 11.63 p/day (+18.2%)

### Non-Domestic Aggregated Tariffs
- **120 tariffs** across all DNOs and years
- Each DNO has 6 variations (No Residual + Bands 1-4 + Related MPAN)
- Bands differentiate by fixed charge level (higher bands = higher standing charges)

## 📁 Files Created

1. **comprehensive_dno_tariffs_with_references.csv** - Raw CSV (640 tariffs)
2. **comprehensive_dno_tariffs_with_references.xlsx** - Excel workbook with year sheets
3. **Google Sheets** - Live online database with formatting

## 🔗 Links

- **Comprehensive Database:** https://docs.google.com/spreadsheets/d/1NlLkmqiU46788TIAvJVxJeXdyKUpbRl--3rQeXuKEjI/edit
- **Traffic Light Rates (Summary):** https://docs.google.com/spreadsheets/d/1fpUHsMKPxo-qSMJFrCNJZajSKhGfg8KEbWqOkwVCF8I/edit
- **Original Dashboard:** https://docs.google.com/spreadsheets/d/1UEejjsId5x6KR0Q43i-Kw3-SE3YqSkgxWDa3MfnVNWw/edit

## 📝 Notes

### Why Only 4 DNOs?
Currently extracted only **NGED (National Grid Electricity Distribution)** files:
- East Midlands (EMID/EMEB)
- West Midlands (WMID/MIDE)
- South Wales (SWALES/SWAE)
- South West (SWEST/SWEB)

### To Add Remaining 10 DNOs:
Need to process files for:
- UK Power Networks (London, Eastern, South Eastern)
- Northern Powergrid (Northeast, Yorkshire)
- Electricity North West
- SP Energy Networks (SPD, SPM)
- SSE (SHEPD, SEPD)

These files are available in the workspace and can be added using the same extraction script.

### Document References
All tariffs include:
- ✅ Source document filename
- ✅ Version number (e.g., v0.1, v0.2)
- ✅ Year
- ✅ Source sheet name
- ✅ LLFCs and PCs for each tariff

## 🚀 Next Steps

1. **Expand to All 14 DNOs:** Process remaining DNO files (UK Power Networks, Northern Powergrid, etc.)
2. **Add Time Bands:** Include specific time definitions for Red/Amber/Green bands
3. **Historical Analysis:** Compare rate changes year-over-year
4. **Upload to BigQuery:** Load data for SQL analysis and spatial queries
5. **Create Dashboard:** Build interactive visualization showing rate trends

## ✅ Completion Status

✅ Extracted 640 tariffs from NGED files  
✅ Full documentation with LLFCs, PCs, rates, charges  
✅ Document references and version numbers included  
✅ Uploaded to Google Sheets with year-by-year sheets  
✅ Formatted with frozen headers and color coding  
✅ Created Non-Domestic Aggregated summary sheet  
✅ Verified East Midlands 2025 rates match your specification

---

**Ready to expand to all 14 DNOs!** 🎉

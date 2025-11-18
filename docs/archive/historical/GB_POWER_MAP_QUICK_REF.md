# GB Power Complete Map - Quick Reference

**File**: `gb_power_complete_map.html`  
**Created**: 2 November 2025  
**Status**: ✅ Production Ready

---

## Quick Start

```bash
# Regenerate map with latest data
python3 create_complete_gb_power_map.py

# Open map
open gb_power_complete_map.html
```

---

## What's On The Map

| Layer | Count | Color | Source |
|-------|-------|-------|--------|
| **DNO Boundaries** | 14 | Green polygons | `dno_regions.geojson` |
| **GSP Flow Points** | 18 | Blue/Orange circles | `bmrs_indgen` + `bmrs_inddem` |
| **Offshore Wind** | 35 | Cyan circles | `offshore_wind_farms` |
| **CVA Plants** | 1,581 | Color by fuel | `cva_plants` |
| **SVA Generators** | 7,072 | Color by fuel | `sva_generators_with_coords` |
| **TOTAL** | **8,720** | — | — |

---

## GSP Status (Latest)

**12 Exporters** (Blue) - Generation > Demand:
- N, B1, B2, B3, B4, B5, B6, B7, B8, B9, B11, B15, B16

**6 Importers** (Orange) - Demand > Generation:
- B10, B12, B13, B14, B17, B3

---

## Fuel Type Colors

| Fuel | Color | Marker |
|------|-------|--------|
| Offshore Wind | Cyan | ● |
| Onshore Wind | Blue | ● |
| Solar | Orange | ● |
| Gas/CCGT | Red | ● |
| Biomass | Green | ● |
| Nuclear | Purple | ● |
| Hydro | Light Blue | ● |
| Other | Gray | ● |

---

## Layer Toggles

Click checkboxes in top-left control panel:
- ☑️ DNO Boundaries (14)
- ☑️ GSP Flow (18)
- ☑️ Offshore Wind (35)
- ☑️ CVA Plants (1,581)
- ☑️ SVA Generators (7,072)

---

## Key Statistics

- **Total Offshore Wind**: 14,267 MW (14.3 GW)
- **Largest Offshore Wind**: Hornsea Two (1,386 MW)
- **Total Generators**: 8,653 sites
- **GSP Net Exporters**: 12 of 18
- **DNO Regions Covered**: All 14 GB regions

---

## Click Actions

- **DNO polygon** → See DNO name, area, region
- **GSP circle** → See generation, demand, net flow
- **Offshore wind** → See capacity, GSP zone, region
- **Generator** → See type, fuel, capacity, DNO

---

## Files

```
gb_power_complete_map.html           # Map (214 KB)
create_complete_gb_power_map.py      # Generator script
dno_regions.geojson                  # DNO boundaries
GB_POWER_COMPLETE_MAP_DOCS.md        # Full documentation
GB_POWER_MAP_QUICK_REF.md           # This file
```

---

## BigQuery Tables Used

```sql
-- GSP Generation
inner-cinema-476211-u9.uk_energy_prod.bmrs_indgen

-- GSP Demand  
inner-cinema-476211-u9.uk_energy_prod.bmrs_inddem

-- Offshore Wind
inner-cinema-476211-u9.uk_energy_prod.offshore_wind_farms

-- CVA Plants
inner-cinema-476211-u9.uk_energy_prod.cva_plants

-- SVA Generators
inner-cinema-476211-u9.uk_energy_prod.sva_generators_with_coords
```

---

## Common Tasks

### Update GSP Flow Data
Map automatically uses latest settlement period from BigQuery.

### Regenerate Map
```bash
python3 create_complete_gb_power_map.py
```

### Check Data Freshness
```bash
bq query --use_legacy_sql=false "
SELECT MAX(settlementDate) as latest_date,
       MAX(settlementPeriod) as latest_period
FROM \`inner-cinema-476211-u9.uk_energy_prod.bmrs_indgen\`"
```

### Count Generators by Type
```bash
bq query --use_legacy_sql=false "
SELECT 'CVA' as type, COUNT(*) as count 
FROM \`inner-cinema-476211-u9.uk_energy_prod.cva_plants\`
UNION ALL
SELECT 'SVA' as type, COUNT(*) as count
FROM \`inner-cinema-476211-u9.uk_energy_prod.sva_generators_with_coords\`"
```

---

## Troubleshooting

**Map not loading?**
- Check browser console for errors
- Try Chrome/Firefox (IE not supported)

**No GSP data?**
- Verify BigQuery access
- Check bmrs_indgen/bmrs_inddem tables exist

**Missing DNO boundaries?**
- Ensure `dno_regions.geojson` in working directory
- Check file size (~500 KB)

**Generators not showing?**
- Zoom in to expand clusters
- Toggle SVA/CVA layers on

**Slow performance?**
- Disable some layers
- Close other browser tabs
- Use Chrome for best performance

---

## Next Steps

1. ✅ Map is production-ready
2. ✅ All data layers included
3. ✅ Documentation complete
4. 🔄 Ready for ongoing use

**For detailed info, see**: `GB_POWER_COMPLETE_MAP_DOCS.md`

---

**Last Updated**: 2 November 2025

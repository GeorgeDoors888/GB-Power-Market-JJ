# CVA vs SVA Sites - Analysis Summary

## ✅ What We Have: SVA Sites (Embedded Generation)

**Current Dataset:**
- **7,072 generators** with coordinates
- **182,960 MW** total capacity
- **Source:** NESO All_Generators.xlsx
- **Type:** SVA (Supplier Volume Allocation)

**SVA Characteristics:**
- Connected to Distribution Network (DNO level)
- Mostly smaller embedded generation
- Includes: Solar farms, small wind, small gas, storage, small hydro
- Size range: 0.001 MW to 1,484 MW
- Median size: 10.53 MW

---

## ❌ What We Need: CVA Sites (Large Power Stations)

**CVA Characteristics:**
- Connected directly to Transmission Network (400kV, 275kV, 132kV)
- Large conventional power stations
- Includes: Nuclear, large CCGT, offshore wind farms, interconnectors
- Participate in Balancing Mechanism (BMUs)
- Typically > 50-100 MW

---

## 🔍 What We Found in BigQuery

### ✅ BMU List Extracted (469 Units)

From Elexon data in BigQuery (`uk_energy_prod.uou2t14d_2025`):

| Fuel Type | Count | % of Total |
|-----------|-------|------------|
| **WIND** | 246 | 52.5% |
| **CCGT** (Gas Turbines) | 61 | 13.0% |
| **OTHER** | 52 | 11.1% |
| **NPSHYD** (Pumped Storage Hydro) | 36 | 7.7% |
| **OCGT** (Peaking Gas) | 21 | 4.5% |
| **PS** (Pumped Storage) | 16 | 3.4% |
| **BIOMASS** | 15 | 3.2% |
| **NUCLEAR** | 10 | 2.1% |
| **COAL** | 2 | 0.4% |
| **Interconnectors** (9 types) | 9 | 1.9% |
| **TOTAL** | **469** | **100%** |

**Sample BMUs:**
```
Wind:    ABRBO-1, ABRTW-1, ACHLW-1 (Offshore wind farms)
CCGT:    CARR-1, CARR-2 (Carrington gas station)
Nuclear: HEYM11, HEYM12 (Heysham nuclear)
         HRTL-1 (Hartlepool nuclear)
         SIZB-1 (Sizewell B nuclear)
Coal:    DRAXX-5, DRAXX-6 (Drax coal units)
Biomass: DRAXX-1 to 4 (Drax biomass units)
Interconn: IEG-FRAN1 (IFA France), IEG-NSL1 (Norway), etc.
```

---

## ⚠️ Missing Data for CVA Sites

We have **BMU IDs** but missing:
1. **Geographic coordinates** (lat/long)
2. **Installed capacity** (MW per unit)
3. **Station names** (full names)
4. **Location/address**
5. **Operating company**

---

## 📥 Where to Get CVA Data

### Option 1: NESO Data Portal ⭐ (Recommended)
**URL:** https://data.nationalgrideso.com/

**Available Datasets:**
1. **BMU Fuel Type** - Links BMU IDs to fuel types
2. **Registered BMUs** - Full BMU registry with details
3. **Generation Assets** - Power station details including location

**Direct Download Links:**
```
BMU Fuel Type:
https://data.nationalgrideso.com/backend/dataset/2810092e-d4b2-472f-b955-d8ae59499f1c/resource/ae0d835e-28f7-4651-a12f-a5f2f2d89043/download/bmu-fuel-type.csv

Registered BMUs:
https://data.nationalgrideso.com/backend/dataset/2810092e-d4b2-472f-b955-d8ae59499f1c/resource/f7c876eb-f662-4de0-83da-6f74ca5b0e84/download/registered-bmus.csv
```

### Option 2: Elexon Portal
**URL:** https://www.elexonportal.co.uk/

**Datasets:**
- BMUNITS_FILE - BMU registration data
- Requires authentication key

### Option 3: Manual Compilation
**Use publicly available data:**
1. **Nuclear stations** (10 units) - Locations well-known
2. **Major CCGT stations** (61 units) - Can find via Google Maps
3. **Offshore wind farms** (246 units) - Crown Estate has locations
4. **Interconnectors** (9 units) - Landing points documented

---

## 🎯 Next Steps

### Immediate Actions:

1. **Download NESO BMU Registry**
   - Visit: https://data.nationalgrideso.com/
   - Search for "BMU" or "Generation"
   - Download CSV files with BMU details

2. **Match BMUs to Coordinates**
   - Option A: NESO may have coordinates in dataset
   - Option B: Google Maps API lookup by station name
   - Option C: Manual geocoding for major stations

3. **Extract Capacity Data**
   - NESO publishes installed capacity per BMU
   - Or query BigQuery for max output from `output_usable_2_14d` table

### Alternative Quick Win:

**Create CVA layer from known major stations:**

We can manually compile the **~50 largest power stations** that represent 80%+ of CVA capacity:

**Nuclear (10 stations):**
- Sizewell B: 1,198 MW
- Heysham 1 & 2: 1,165 MW
- Hartlepool: 1,190 MW
- Torness: 1,185 MW
- Hinkley Point B: 965 MW
- etc.

**Major CCGT (top 20):**
- Drax (gas): 2,600 MW
- Pembroke: 2,180 MW
- West Burton: 1,332 MW
- Grain: 1,275 MW
- Peterhead: 1,180 MW
- etc.

**Major Offshore Wind (top 20):**
- Hornsea One: 1,218 MW
- Hornsea Two: 1,386 MW
- Dogger Bank: 3,600 MW (under construction)
- London Array: 630 MW
- etc.

**Interconnectors (9 total):**
- IFA (France): 2,000 MW
- IFA2 (France): 1,000 MW
- BritNed (Netherlands): 1,000 MW
- NSL (Norway): 1,400 MW
- etc.

---

## 📊 Combined Dataset Target

**Final Goal:**

| Type | Count | Capacity (MW) | Data Source |
|------|-------|---------------|-------------|
| **SVA Sites** | 7,072 | 182,960 | ✅ **Complete** |
| **CVA Sites** | ~469 BMUs | ~60,000-80,000 | ⚠️ **Needs coordinates** |
| **TOTAL** | ~7,541 | ~250,000 | Target |

**Why Both Matter:**
- **SVA** = Distributed generation landscape
- **CVA** = Backbone of GB power system
- Together = Complete generation picture

---

## 🔧 Technical Implementation Plan

### Phase 1: Download NESO Data ⭐
```bash
# Download from NESO portal
wget https://data.nationalgrideso.com/.../bmu-fuel-type.csv
wget https://data.nationalgrideso.com/.../registered-bmus.csv
```

### Phase 2: Extract Capacity from BigQuery
```sql
SELECT 
    nationalGridBmUnit,
    bmUnit,
    fuelType,
    MAX(outputUsable) as max_capacity_mw
FROM `uk_energy_prod.uou2t14d_2025`
GROUP BY nationalGridBmUnit, bmUnit, fuelType
```

### Phase 3: Geocode Stations
```python
# Option A: If NESO has coordinates - use directly
# Option B: Google Maps API
# Option C: Manual for top 50 stations
```

### Phase 4: Combine Datasets
```python
# Merge:
# - SVA sites (7,072) - already have lat/long, capacity
# - CVA sites (469) - add lat/long, capacity
# 
# Create combined generators.json with:
# - type: 'SVA' or 'CVA'
# - All other fields same format
```

### Phase 5: Update Map
```javascript
// Add different styling for CVA vs SVA:
// - CVA: Larger markers, different shapes (triangles?)
// - SVA: Current circles
// - Toggle between both
```

---

## 💾 Files Created

1. **`cva_bmu_list.json`** (✅ Complete)
   - 469 BMUs with fuel types
   - Missing: coordinates, capacity

2. **`extract_cva_bmus.py`** (✅ Working)
   - Extracts BMUs from BigQuery

3. **`download_neso_bmu_data.py`** (⚠️ Network issue)
   - Ready to download NESO data when network available

---

## 🎯 Recommended Next Step

**Try downloading NESO data manually:**

1. Open browser: https://data.nationalgrideso.com/
2. Search for: "BMU" or "Balancing Mechanism" or "Generation Assets"
3. Download CSV files
4. Share with me to process

**Or I can create a manual CSV of the top 50 CVA stations** using publicly known data (Wikipedia, power station lists, etc.)

---

**Status:** We have the BMU IDs, now need coordinates and capacity data from NESO portal.

**Created:** November 1, 2025

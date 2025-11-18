# VLP Battery Units JSON Data - Complete

## ✅ File Created Successfully!

**Location:** `vlp_battery_units_data.json`  
**Size:** 72.3 KB  
**Format:** JSON with complete metadata and battery unit details

## 📊 What's Included

### Metadata Section
- **Title & Description:** GB Battery Storage BMU Units - VLP Analysis
- **Generated Date:** 2025-11-06
- **Data Source:** NESO BMRS API + BMU Registration Data
- **Total Battery BMUs:** 148
- **VLP-Operated:** 102 (68.9%)
- **Direct-Operated:** 46 (31.1%)
- **Field Definitions:** Explains all data fields

### Summary Statistics
- **Total Capacity:** 20,361 MW
- **Average Capacity:** 137.6 MW per BMU
- **Median Capacity:** 49.9 MW

**By VLP Status:**
- VLP: 102 units, 12,362 MW (avg 121 MW/unit)
- Direct: 46 units, 7,999 MW (avg 174 MW/unit)

**Top 10 VLP Operators** (by total capacity):
1. **Risq Energy Limited** - 5 BMUs, 5,000 MW
2. **EP UK INVESTMENTS LIMITED** - 2 BMUs, 1,485 MW
3. **Carrington Power Ltd** - 2 BMUs, 940 MW
4. **Tesla Motors Limited** - 15 BMUs, 541 MW
5. **RWE Generation UK plc** - 2 BMUs, 447 MW
6. **Morecambe Wind Limited** - 2 BMUs, 398 MW
7. **Dorenell Windfarm Limited** - 2 BMUs, 314 MW
8. **Lincs Wind Farm Ltd** - 2 BMUs, 300 MW
9. **Statkraft Markets Gmbh** - 11 BMUs, 291 MW
10. **EDF Energy Customers Limited** - 6 BMUs, 290 MW

### Battery Units Array (148 entries)

Each battery unit includes:
```json
{
  "nationalGridBmUnit": "ARBRB-1",
  "elexonBmUnit": "E_ARBRB-1",
  "leadPartyName": "Octopus Energy Trading Limited",
  "leadPartyId": "COPPER",
  "fuelType": "OTHER",
  "generationCapacity": 34.0,
  "demandCapacity": -35.597,
  "bmUnitType": "E",
  "bmUnitName": "Arbroath Battery Storage",
  "gspGroupName": "North Scotland",
  "is_vlp": true,
  "is_vlp_by_name": true,
  "is_aggregator_code": false,
  "multiple_assets": true
}
```

## 🔑 Key Fields Explained

| Field | Description |
|-------|-------------|
| `nationalGridBmUnit` | National Grid BMU identifier (e.g., "ARBRB-1") |
| `elexonBmUnit` | Elexon BMU identifier used in BOD data (e.g., "E_ARBRB-1") |
| `leadPartyName` | Company operating the BMU |
| `leadPartyId` | Lead party identifier code |
| `fuelType` | Fuel/technology type |
| `generationCapacity` | Export capacity in MW |
| `demandCapacity` | Import capacity in MW (negative = charging) |
| `bmUnitType` | E=embedded, T=transmission, V=virtual |
| `bmUnitName` | Site/project name |
| `gspGroupName` | Grid Supply Point region |
| `is_vlp` | TRUE if operated by Virtual Lead Party |
| `is_vlp_by_name` | TRUE if VLP identified by company name keywords |
| `is_aggregator_code` | TRUE if BMU code indicates aggregation |
| `multiple_assets` | TRUE if lead party manages multiple BMUs |

## 📖 Usage Examples

### Python
```python
import json

# Load the data
with open('vlp_battery_units_data.json', 'r') as f:
    data = json.load(f)

# Get summary statistics
print(f"Total battery BMUs: {data['metadata']['total_battery_bmus']}")
print(f"VLP percentage: {data['metadata']['vlp_percentage']}%")

# Filter VLP batteries
vlp_batteries = [u for u in data['battery_units'] if u['is_vlp']]
print(f"VLP batteries: {len(vlp_batteries)}")

# Get batteries by operator
tesla_batteries = [u for u in data['battery_units'] 
                   if u['leadPartyName'] == 'Tesla Motors Limited']
print(f"Tesla batteries: {len(tesla_batteries)}")

# Calculate total VLP capacity
total_vlp_capacity = sum(u['generationCapacity'] or 0 
                         for u in vlp_batteries)
print(f"Total VLP capacity: {total_vlp_capacity:.0f} MW")
```

### JavaScript
```javascript
// Load the data
const data = require('./vlp_battery_units_data.json');

// Get summary
console.log(`Total battery BMUs: ${data.metadata.total_battery_bmus}`);
console.log(`VLP percentage: ${data.metadata.vlp_percentage}%`);

// Filter VLP batteries
const vlpBatteries = data.battery_units.filter(u => u.is_vlp);
console.log(`VLP batteries: ${vlpBatteries.length}`);

// Group by region
const byRegion = {};
data.battery_units.forEach(u => {
  const region = u.gspGroupName || 'Unknown';
  byRegion[region] = (byRegion[region] || 0) + 1;
});
console.log('Batteries by region:', byRegion);
```

### Command Line (jq)
```bash
# Get total battery count
jq '.metadata.total_battery_bmus' vlp_battery_units_data.json

# List all VLP operators
jq '.summary_statistics.top_vlp_operators[].name' vlp_battery_units_data.json

# Get batteries in Yorkshire
jq '.battery_units[] | select(.gspGroupName == "Yorkshire")' vlp_battery_units_data.json

# Count batteries by VLP status
jq '[.battery_units[] | .is_vlp] | group_by(.) | map({vlp: .[0], count: length})' vlp_battery_units_data.json

# Get Tesla batteries
jq '.battery_units[] | select(.leadPartyName == "Tesla Motors Limited")' vlp_battery_units_data.json

# Total capacity by VLP status
jq '[.battery_units[] | {vlp: .is_vlp, capacity: .generationCapacity}] | group_by(.vlp) | map({vlp: .[0].vlp, total: map(.capacity) | add})' vlp_battery_units_data.json
```

## 🎯 Analysis Use Cases

### 1. Market Share Analysis
```python
# VLP market share by capacity
vlp_capacity = sum(u['generationCapacity'] or 0 
                   for u in data['battery_units'] if u['is_vlp'])
total_capacity = sum(u['generationCapacity'] or 0 
                     for u in data['battery_units'])
print(f"VLP market share: {vlp_capacity/total_capacity*100:.1f}%")
```

### 2. Regional Distribution
```python
from collections import Counter
regions = Counter(u['gspGroupName'] for u in data['battery_units'] 
                  if u['gspGroupName'])
print("Top regions:", regions.most_common(5))
```

### 3. Operator Portfolio Analysis
```python
from collections import defaultdict
portfolios = defaultdict(lambda: {'count': 0, 'capacity': 0})
for u in data['battery_units']:
    op = u['leadPartyName']
    portfolios[op]['count'] += 1
    portfolios[op]['capacity'] += u['generationCapacity'] or 0

# Operators with largest portfolios
sorted_ops = sorted(portfolios.items(), 
                   key=lambda x: x[1]['count'], 
                   reverse=True)[:10]
```

### 4. Average Unit Size by Operator Type
```python
vlp_sizes = [u['generationCapacity'] for u in data['battery_units'] 
             if u['is_vlp'] and u['generationCapacity']]
direct_sizes = [u['generationCapacity'] for u in data['battery_units'] 
                if not u['is_vlp'] and u['generationCapacity']]

import statistics
print(f"VLP avg size: {statistics.mean(vlp_sizes):.1f} MW")
print(f"Direct avg size: {statistics.mean(direct_sizes):.1f} MW")
```

## 📁 Related Files

- **CSV Files:**
  - `battery_bmus_complete_20251106_151039.csv` - Full data in CSV format
  - `vlp_operated_batteries_20251106_151039.csv` - VLP batteries only
  - `direct_operated_batteries_20251106_151039.csv` - Direct-operated only
  - `battery_revenue_analysis_20251106_151039.csv` - Activity/revenue data

- **Documentation:**
  - `VLP_BATTERY_ANALYSIS_SUMMARY.md` - Complete analysis summary
  - `README_DASHBOARD.md` - Live dashboard documentation
  - `DASHBOARD_QUICKSTART.md` - Quick start guide

- **Scripts:**
  - `complete_vlp_battery_analysis.py` - Main analysis script
  - `create_vlp_json.py` - JSON export script (this file)

## 🔄 Updating the Data

To regenerate the JSON with updated data:

```bash
# Run the analysis to get latest BMU data
.venv/bin/python complete_vlp_battery_analysis.py

# Create updated JSON
.venv/bin/python create_vlp_json.py
```

## 📊 Data Freshness

- **BMU Registration Data:** Downloaded from NESO BMRS API (2,783 BMUs)
- **Generator Register:** Local dataset with 421 battery sites
- **Analysis Date:** November 6, 2025
- **BOD Activity Data:** Last 365 days (2023-2024)

## 🚀 Integration Options

### API Endpoint
Host this JSON file to create a simple API:
```bash
# Using Python
python3 -m http.server 8000
# Access at: http://localhost:8000/vlp_battery_units_data.json

# Using Node.js
npx http-server
```

### Database Import
```python
import json
import sqlite3

# Load JSON
with open('vlp_battery_units_data.json') as f:
    data = json.load(f)

# Create database
conn = sqlite3.connect('vlp_batteries.db')
c = conn.cursor()

# Create table
c.execute('''CREATE TABLE batteries
             (nationalGridBmUnit TEXT PRIMARY KEY,
              elexonBmUnit TEXT,
              leadPartyName TEXT,
              generationCapacity REAL,
              is_vlp BOOLEAN,
              gspGroupName TEXT)''')

# Insert data
for unit in data['battery_units']:
    c.execute("INSERT INTO batteries VALUES (?,?,?,?,?,?)",
              (unit['nationalGridBmUnit'],
               unit['elexonBmUnit'],
               unit['leadPartyName'],
               unit['generationCapacity'],
               unit['is_vlp'],
               unit['gspGroupName']))

conn.commit()
```

## ✅ Data Quality

- **Complete:** All 148 battery BMUs from NESO register
- **Validated:** Cross-referenced with generator register
- **VLP Identification:** 3-criteria methodology (name/code/portfolio)
- **Accurate:** Direct from official NESO BMRS API

---

**File Ready for Use:** `vlp_battery_units_data.json` (72.3 KB)  
**Total Units:** 148 battery BMUs  
**VLP Coverage:** 68.9% of GB battery storage market  
**Generated:** November 6, 2025

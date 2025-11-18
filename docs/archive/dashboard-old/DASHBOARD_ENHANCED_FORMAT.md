# Dashboard Enhanced Format - November 10, 2025

## ✅ Updates Implemented

### 1. **System Metrics Row (Row 5) - YES, This Updates Automatically**

**Display**:
```
Total Generation: 31.8 GW | Supply: 32.7 GW | Renewables: 52% | 💰 Price: (pending data)
```

**What Updates**:
- ✅ **Total Generation**: Sum of all fuel types (updates every refresh)
- ✅ **Supply**: Total generation + net imports (updates every refresh)
- ✅ **Renewables**: Percentage from wind, solar, hydro, biomass (updates every refresh)
- 💰 **Price**: Market imbalance price when available (currently pending data)

**Update Frequency**: Every time you run `python3 update_dashboard_enhanced.py`

### 2. **Price Data Added to Header**

**Location**: Row 5 (in system metrics line)

**What It Shows**:
- Market Imbalance Price (£/MWh) when available
- Falls back to "(pending data)" if no price data

**Note**: Price data comes from `bmrs_mid` table. If showing "pending", it means no data available for current settlement period yet.

**Future Enhancement**: Can add System Buy Price and System Sell Price when we identify the correct table/columns.

### 3. **Complete Generator List (Row 16+)**

**Format**:
```
Row 7:   🔥 Fuel Breakdown  |  🌍 Interconnectors
Row 8-15: Main generators    |  Interconnectors with flags
Row 16:  (blank separator)
Row 17:  ⚡ OTHER GENERATORS
Row 18+: All other fuel types including:
         - 🔋 PS (Pumped Storage)
         - 🔥 OCGT (Open Cycle Gas Turbines - gas peaking)
         - 🛢️ OIL (Oil-fired generators)
         - ⛏️ COAL (Coal-fired generators)
         - ⚡ OTHER (Other sources)
```

**Why This Format?**:
- **Main generators** (Wind, CCGT, Biomass, Nuclear, Hydro) stay at top for quick view
- **Other generators** below row 16 so they don't clutter the main view
- **All fuel types included** - nothing hidden
- **Easy to scan** - main generators are prominent, detailed breakdown below

### 4. **Generator Categories**

#### **Main Generators** (Rows 8-15):
```
💨 WIND          13.3 GW   ← Primary renewable
🔥 CCGT          11.0 GW   ← Combined Cycle Gas Turbines (base load)
🌱 BIOMASS        3.3 GW   ← Renewable biomass plants
⚛️ NUCLEAR       3.2 GW   ← Base load nuclear
💧 NPSHYD         0.6 GW   ← Pumped storage hydro (primary)
```

#### **Other Generators** (Row 18+):
```
⚡ OTHER          0.4 GW   ← Miscellaneous sources
🔥 OCGT           0.0 GW   ← Open Cycle Gas (peaking plants)
🛢️ OIL            0.0 GW   ← Oil-fired (rarely used)
⛏️ COAL           0.0 GW   ← Coal-fired (being phased out)
🔋 PS            -0.0 GW   ← Pumped storage (charging mode shows negative)
```

**Generator Explanations**:

| Type | Emoji | Purpose | Typical Use |
|------|-------|---------|-------------|
| **WIND** | 💨 | Renewable generation | Continuous when windy |
| **CCGT** | 🔥 | Combined cycle gas | Base load, flexible |
| **OCGT** | 🔥 | Open cycle gas | Peak demand only (expensive) |
| **NUCLEAR** | ⚛️ | Nuclear reactors | Base load, always on |
| **BIOMASS** | 🌱 | Biomass plants | Renewable base load |
| **NPSHYD** | 💧 | Pumped storage hydro | Energy storage, peaks |
| **PS** | 🔋 | Pumped storage | Charging/discharging |
| **HYDRO** | 💧 | Hydroelectric | Run-of-river, flexible |
| **SOLAR** | ☀️ | Solar PV | Daytime only |
| **COAL** | ⛏️ | Coal plants | Being phased out |
| **OIL** | 🛢️ | Oil-fired | Emergency backup only |
| **OTHER** | ⚡ | Other sources | Various small sources |

## Dashboard Structure (Enhanced)

```
Row 1:  File: Dashboard
Row 2:  ⏰ Last Updated: 2025-11-10 13:15:00 | ✅ FRESH
Row 3:  Data Freshness: ✅ <10min | ⚠️ 10-60min | 🔴 >60min
Row 4:  📊 SYSTEM METRICS
Row 5:  Total Generation: 31.8 GW | Supply: 32.7 GW | Renewables: 52% | 💰 Price: (pending)
Row 6:  (blank)
Row 7:  🔥 Fuel Breakdown | 🌍 Interconnectors

MAIN GENERATORS SECTION:
Row 8:   💨 WIND 13.3 GW    | 🇫🇷 ElecLink (France) 999 MW Import
Row 9:   🔥 CCGT 11.0 GW    | 🇮🇪 East-West (Ireland) 0 MW Balanced
Row 10:  🌱 BIOMASS 3.3 GW  | 🇫🇷 IFA (France) 1509 MW Import
Row 11:  ⚛️ NUCLEAR 3.2 GW  | 🇮🇪 Greenlink (Ireland) 513 MW Export
Row 12:  💧 NPSHYD 0.6 GW   | 🇫🇷 IFA2 (France) 1 MW Export
Row 13-15: (more if needed) | 🇮🇪 Moyle, 🇳🇱 BritNed, 🇧🇪 Nemo, 🇳🇴 NSL, 🇩🇰 Viking

Row 16: (blank separator)

OTHER GENERATORS SECTION:
Row 17: ⚡ OTHER GENERATORS
Row 18: ⚡ OTHER 0.4 GW
Row 19: 🔥 OCGT 0.0 GW      (gas peaking plants)
Row 20: 🛢️ OIL 0.0 GW       (oil-fired backup)
Row 21: ⛏️ COAL 0.0 GW      (coal being phased out)
Row 22: 🔋 PS -0.0 GW       (pumped storage charging)

Row 70+: ⚠️ LIVE POWER STATION OUTAGES
```

## How to Update Dashboard

### **Quick Update** (most common):
```bash
cd "/Users/georgemajor/GB Power Market JJ"
python3 update_dashboard_enhanced.py
```

This updates:
- ✅ System metrics (Total Generation, Supply, Renewables, Price)
- ✅ All fuel types (main + other generators)
- ✅ Interconnectors with flags
- ✅ Timestamp and data freshness

### **Full System Update** (includes outages):
```bash
cd "/Users/georgemajor/GB Power Market JJ"
python3 update_dashboard_enhanced.py
python3 auto_refresh_outages.py
python3 create_sp_data_sheet.py
```

## What Gets Updated When

| Component | Updates With | Frequency |
|-----------|-------------|-----------|
| **Total Generation** | `update_dashboard_enhanced.py` | Every run |
| **Supply** | `update_dashboard_enhanced.py` | Every run |
| **Renewables %** | `update_dashboard_enhanced.py` | Every run |
| **Price** | `update_dashboard_enhanced.py` | When available |
| **Fuel Breakdown** | `update_dashboard_enhanced.py` | Every run |
| **Interconnectors** | `update_dashboard_enhanced.py` | Every run |
| **Outages** | `auto_refresh_outages.py` | Separate script |
| **Settlement Periods** | `create_sp_data_sheet.py` | Separate script |

## Format Benefits

✅ **Clean main view** - Key generators at top  
✅ **Complete data** - All generators included (nothing missing)  
✅ **Easy scanning** - Main metrics in one line  
✅ **Documented** - Clear labeling of sections  
✅ **Flexible** - Can add more generators without cluttering main view  
✅ **Price visibility** - Market price shown in header when available  

## Price Data Notes

**Current Status**: Showing "(pending data)" because `bmrs_mid` table doesn't have data for current settlement period yet.

**When Price Will Show**: 
- Once settlement period closes (every 30 minutes)
- Price data gets published to BigQuery
- Next refresh will pick it up automatically

**Alternative**: If you need real-time prices, we can query a different table (TBD - need to identify correct IRIS table for live prices).

---

**Status**: ✅ Enhanced format implemented and documented  
**Dashboard URL**: https://docs.google.com/spreadsheets/d/12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8  
**Update Script**: `update_dashboard_enhanced.py`  
**Last Updated**: November 10, 2025

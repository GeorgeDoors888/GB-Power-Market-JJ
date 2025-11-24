# Interactive Map - Quick Reference Guide

## 🎮 Controls Overview

```
┌─────────────────────────────────────────────────────────────┐
│  🏢 DNO Region: [National ▼]  🎨 Overlay: [None ▼]  🔌 IC: [All ▼]  │
└─────────────────────────────────────────────────────────────┘
```

## 📍 DNO Region Filter

| Selection | Coverage | GSPs Shown |
|-----------|----------|------------|
| **National** | All of GB | All 20 GSPs |
| **Western Power** | South West, Wales | B11, B17 |
| **UKPN** | London, South East | N, B9 |
| **ENWL** | North West | B8, B13, B18 |
| **SPEN** | Scotland, North Wales | (Scotland GSPs) |
| **SSEN** | Central Scotland, South | (Scotland + South GSPs) |
| **Northern Powergrid** | North East, Yorkshire | B14, B15, B16 |

## 🎨 Overlay Types

### None (Default)
- 🟢 Green circles sized by demand
- Larger circle = higher load

### Demand Heatmap
```
🔴 Red      >10,000 MW   (London, major cities)
🟠 Orange   5,000-10k MW (Regional centers)
🟡 Amber    1,000-5k MW  (Medium towns)
🟢 Green    <1,000 MW    (Rural areas)
```

### Generation Heatmap
```
🔵 Dark Blue   >10,000 MW  (Major power stations)
🔷 Light Blue  5,000-10k MW (Wind/solar farms)
🟢 Green       <5,000 MW   (Distributed generation)
```

### Constraint Zones
```
🟣 Purple   >100 MW constraint  (Network congestion)
🟢 Green    Normal operation    (No constraints)
```

### Frequency Gradient
```
🔴 Red     <49.8 Hz   (Under-frequency, deficit)
🟢 Green   49.8-50.2  (Normal operation)
🟡 Amber   >50.2 Hz   (Over-frequency, surplus)
```

## 🔌 Interconnector Views

### All (Default)
- Shows all 8 interconnectors
- 🟢 Green lines = Import (positive flow)
- 🔴 Red lines = Export (negative flow)
- Line thickness = Flow magnitude

### Imports
- Only ICs with flow > 0
- All shown in green
- Thicker = larger import

### Exports
- Only ICs with flow < 0
- All shown in red
- Thicker = larger export

### Outages
- Only ICs with status = 'Outage'
- Gray lines (no flow)

## 📊 Interconnector Capacities

| Name | Country | Capacity | Typical Use |
|------|---------|----------|-------------|
| **IFA** | 🇫🇷 France | 2000 MW | Baseload import |
| **IFA2** | 🇫🇷 France | 1000 MW | Peak support |
| **ElecLink** | 🇫🇷 France | 1000 MW | Channel Tunnel |
| **BritNed** | 🇳🇱 Netherlands | 1000 MW | Wind export |
| **NSL** | 🇳🇴 Norway | 1400 MW | Hydro import |
| **Viking Link** | 🇩🇰 Denmark | 1400 MW | Wind balancing |
| **Nemo** | 🇧🇪 Belgium | 1000 MW | EU coupling |
| **Moyle** | 🇮🇪 Ireland | 500 MW | Island link |

## 🖱️ Interactive Features

### Click on GSP (Circle)
Shows tooltip with:
- GSP name and ID
- Current load (MW)
- Generation (MW)
- Grid frequency (Hz)
- Constraints (if any)
- DNO region

### Click on Interconnector (Line)
Shows tooltip with:
- Interconnector name
- Connected country
- Flow direction and MW
- Capacity and utilization %
- Operational status

### Click on DNO Boundary (Polygon)
Shows tooltip with:
- DNO name
- Total load (MW)
- Total generation (MW)
- Coverage area (km²)

## 🎯 Common Use Cases

### 1. Check Regional Demand
```
Action: Select DNO region → Choose "Demand Heatmap"
Result: See which areas have highest load
```

### 2. Monitor Grid Frequency
```
Action: National view → "Frequency Gradient"
Result: Red areas = low frequency (need more generation)
        Amber = high frequency (excess generation)
```

### 3. Identify Constraints
```
Action: National view → "Constraint Zones"
Result: Purple circles = network congestion
        Check balancing market for high prices in these areas
```

### 4. Track Interconnector Flows
```
Action: "All" ICs → Hover over lines
Result: Green thick = large import (Europe helping GB)
        Red thick = large export (GB helping Europe)
```

### 5. Find Generation Surplus
```
Action: National → "Generation Heatmap"
Result: Blue areas = high generation
        Compare with demand to find export opportunities
```

## 🔄 Data Refresh

### Manual Refresh
1. In Google Sheets menu: **🗺️ Map Tools → 📊 Refresh Map Data**
2. Or run: `python3 refresh_map_data.py`

### Auto-Refresh (Optional)
Set up cron on server:
```bash
*/15 * * * * /opt/map-data-refresh.sh
```
Updates data every 15 minutes

### Check Freshness
- Look at "Last_Updated" column in Map_Data_* sheets
- Should be within last 15-30 minutes

## 🐛 Quick Fixes

### Map is blank
- Check Map_Data_GSP sheet has data (not just headers)
- Run `python3 refresh_map_data.py`

### Dropdowns don't filter
- Refresh browser (F5)
- Check JavaScript console (F12) for errors

### No interconnector lines
- Check Map_Data_IC sheet has coordinate data
- Verify Start_Lat, Start_Lng, End_Lat, End_Lng columns

### Colors wrong
- Check Overlay Type dropdown selection
- Verify data values in sheets (not blank or zero)

## 📱 Keyboard Shortcuts

| Key | Action |
|-----|--------|
| **+** | Zoom in |
| **-** | Zoom out |
| **↑↓←→** | Pan map |
| **Home** | Reset to GB view |
| **Esc** | Close info tooltip |

## 💡 Pro Tips

1. **Compare demand vs generation**: Switch between overlays quickly to spot imbalances

2. **Watch frequency**: Red in Frequency Gradient = system under stress, expect high balancing prices

3. **Track constraints**: Purple zones = opportunity for local battery arbitrage

4. **Monitor ICs**: Large imports + high frequency = cheap power, good time to charge batteries

5. **Regional focus**: Filter to your DNO to see local grid conditions

6. **Time of day patterns**:
   - Morning (7-9am): Red demand, green imports
   - Midday (12-2pm): Blue generation (solar peak)
   - Evening (5-7pm): Red demand, purple constraints

---

**Quick Access**: `🗺️ Map Tools → 🌍 Open Interactive Map`  
**Full Docs**: `ENERGY_DASHBOARD_MAPS_INTEGRATION.md`  
**Support**: george@upowerenergy.uk

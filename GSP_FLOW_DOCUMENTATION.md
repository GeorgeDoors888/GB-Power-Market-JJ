# GSP Flow Analysis - Grid Supply Point Import/Export Documentation

## Overview
This document explains the GSP (Grid Supply Point) flow analysis showing which areas are net exporters vs net importers of electricity.

**Created**: 2 November 2025  
**Data Source**: Elexon BMRS API via BigQuery

## What is GSP Flow?

### Grid Supply Points (GSPs)
- **18 GSP areas** cover Great Britain
- Each GSP connects the transmission grid to distribution networks
- GSPs are boundary measurement points between transmission and distribution

### Net Flow Calculation
```
Net Flow = Generation - Demand

Positive Net Flow = EXPORTER (Generation > Demand)
Negative Net Flow = IMPORTER (Demand > Generation)
```

### Data Sources
- **Generation**: `bmrs_indgen` table (Indicated Generation at GSP level)
- **Demand**: `bmrs_inddem` table (Indicated Demand at GSP level, stored as negative values)
- **Frequency**: 48 settlement periods per day (30-minute intervals)

## GSP Area Codes

| Code | Name | Location |
|------|------|----------|
| N | National Grid | Central coordination point |
| B1 | Barking | East London |
| B2 | Ealing | West London |
| B3 | Wimbledon | South London |
| B4 | Brixton | South London |
| B5 | City Road | Central London |
| B6 | Willesden | North West London |
| B7 | Hurst | West of London (Berkshire) |
| B8 | Sundon | Bedfordshire |
| B9 | Pelham | Hertfordshire |
| B10 | Bramley | Hampshire |
| B11 | Melksham | Wiltshire |
| B12 | Exeter | Devon |
| B13 | Bristol | Bristol |
| B14 | Indian Queens | Cornwall |
| B15 | Landulph | Cornwall/Devon border |
| B16 | Pembroke | South Wales |
| B17 | Swansea North | South Wales |

## Net Exporter vs Importer

### Net Exporters (Blue)
- Generate MORE electricity than local demand
- Export surplus to other areas via transmission grid
- Typically areas with:
  - Large power stations (gas, nuclear, coal)
  - Significant renewable generation (wind, solar farms)
  - Lower population density
  
**Examples**: Pembroke (large gas plant), Sundon (solar/wind), Melksham (renewable rich)

### Net Importers (Orange)
- Local demand EXCEEDS generation
- Import electricity from other areas
- Typically areas with:
  - High population density
  - Limited generation capacity
  - Major urban centers

**Examples**: London GSPs (B1-B6), Bristol, Exeter during peak demand

## SQL Query for Live Data

```sql
WITH latest_data AS (
  SELECT 
    MAX(CONCAT(settlementDate, '-', settlementPeriod)) as latest
  FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_indgen`
)
SELECT 
  COALESCE(g.boundary, d.boundary) as gsp,
  COALESCE(SUM(g.quantity), 0) as generation_mw,
  COALESCE(SUM(d.quantity), 0) as demand_mw,
  COALESCE(SUM(g.quantity), 0) + COALESCE(SUM(d.quantity), 0) as net_flow_mw,
  CASE 
    WHEN COALESCE(SUM(g.quantity), 0) + COALESCE(SUM(d.quantity), 0) > 0 
    THEN 'EXPORTER' 
    ELSE 'IMPORTER' 
  END as flow_status
FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_indgen` g
FULL OUTER JOIN `inner-cinema-476211-u9.uk_energy_prod.bmrs_inddem` d
  ON g.boundary = d.boundary
  AND g.settlementDate = d.settlementDate
  AND g.settlementPeriod = d.settlementPeriod
WHERE CONCAT(g.settlementDate, '-', g.settlementPeriod) = (SELECT latest FROM latest_data)
  OR CONCAT(d.settlementDate, '-', d.settlementPeriod) = (SELECT latest FROM latest_data)
GROUP BY gsp
ORDER BY net_flow_mw DESC
```

## Visualization Features

### Interactive Map (gsp_live_flow_map.html)
1. **Color Coding**:
   - 🟦 Blue circles = Net exporters
   - 🟧 Orange circles = Net importers

2. **Circle Size**: Proportional to absolute net flow magnitude
   - Larger circles = greater import/export volume

3. **Data Display**:
   - GSP code and name
   - Generation (MW)
   - Demand (MW)
   - Net flow (MW)
   - Flow status

4. **Info Panel**:
   - Count of exporters vs importers
   - Total export/import volumes
   - Latest data timestamp

## Typical Patterns

### Daytime (Settlement Periods 1-32, 00:00-16:00)
- Solar generation peak (SP24-32, 12:00-16:00)
- More areas become exporters
- Urban areas still import

### Evening Peak (Settlement Periods 33-40, 16:30-20:00)
- Demand surge as people return home
- More areas become importers
- Even generation-heavy areas may import

### Night (Settlement Periods 41-48, 20:30-00:00)
- Lower demand
- Wind generation often strong
- More exporters, especially Scotland/offshore wind areas

### Seasonal Variations
- **Summer**: More solar, lower heating demand = more exporters
- **Winter**: Higher demand, less solar = more importers
- **Spring/Autumn**: Balanced, variable with weather

## Use Cases

### 1. Grid Operations
- Identify congestion points
- Balance flows between regions
- Plan transmission upgrades

### 2. Trading & Arbitrage
- Zonal price differences
- Import/export opportunities
- Demand response targeting

### 3. Renewable Integration
- Track renewable generation impact on flows
- Identify curtailment risks
- Plan storage locations

### 4. Infrastructure Planning
- Where to build new generation
- Transmission reinforcement needs
- Distribution network upgrades

## Data Accuracy Notes

### BMRS Data Conventions
- Demand stored as **NEGATIVE values** in database
- Net flow = Generation + Demand (adding a negative)
- Always verify sign conventions when querying

### Data Frequency
- Updated every 30 minutes (48 periods/day)
- ~2-5 minute lag from real-time
- Historical data available from 2020

### Known Issues
- Settlement Period 48 on clock change days (50 periods)
- Occasional missing data points
- National Grid (N) aggregation method varies

## Files & Scripts

### Visualization
- `gsp_live_flow_map.html` - Interactive map showing current flows
- `create_gsp_flow_map.py` - Python script to generate map with latest data

### Data Queries
- `check_gsp_flow.py` - Quick check of current GSP flows
- `gsp_flow_history.py` - Historical flow analysis

### Documentation
- `GSP_FLOW_DOCUMENTATION.md` - This file
- `README.md` - Main project documentation (Data Sources section)

## Quick Commands

### Check Latest GSP Flows
```bash
bq query --use_legacy_sql=false "
SELECT boundary, 
  SUM(quantity) as total_mw,
  COUNT(*) as records
FROM \`inner-cinema-476211-u9.uk_energy_prod.bmrs_indgen\`
WHERE settlementDate = CURRENT_DATE()
GROUP BY boundary
ORDER BY total_mw DESC
LIMIT 18"
```

### Generate Latest Map
```bash
python3 create_gsp_flow_map.py
open gsp_live_flow_map.html
```

## References

- [Elexon BMRS API Documentation](https://www.elexon.co.uk/documents/training-guidance/bsc-guidance-notes/bmrs-api-data-push-user-guide-2/)
- [National Grid ESO](https://www.nationalgrideso.com/)
- [Settlement Period Definition](https://www.elexon.co.uk/knowledgebase/what-is-a-settlement-period/)

---

**Last Updated**: 2 November 2025  
**Status**: ✅ Active Documentation

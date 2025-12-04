# BESS Sheet Structure Documentation

**Generated:** 2025-12-02  
**Spreadsheet:** https://docs.google.com/spreadsheets/d/1LmMq4OEE639Y-XXpOJ3xnvpAmHB6vUovh5g6gaU_vzc/

## Critical Cell Mappings

All scripts that read/write to the BESS sheet MUST use these cell references:

### Input Cells (Read by scripts)

| Cell | Description | Type | Example |
|------|-------------|------|---------|
| **F13** | Import Capacity (kW) | float | 2500 |
| **F14** | Export Capacity (kW) | float | 2500 |
| **F15** | Duration (hours) | float | 2.0 |
| **F16** | Max Cycles/Day | float | 4.0 |
| **B10** | Red DUoS Rate (p/kWh) | float | 1.764 |
| **C10** | Amber DUoS Rate (p/kWh) | float | 0.205 |
| **D10** | Green DUoS Rate (p/kWh) | float | 0.011 |
| **D43** | PPA Price (£/MWh) | float | 150 |

⚠️ **IMPORTANT**: DNO DUoS rates are in **ROW 10** (data), NOT row 9 (header)!

### Output Cells (Written by calculate_bess_element_costs.py)

#### DUoS Costs (Rows 28-30)
| Row | Column F (Rate) | Column G (kWh) | Column H (Cost £) | Description |
|-----|-----------------|----------------|-------------------|-------------|
| 28 | `1.764 p/kWh` | `0` | `£0.00` | **Red** (16:00-19:30 weekdays) - Should be 0! |
| 29 | `0.205 p/kWh` | `362,018` | `£742.14` | **Amber** (08:00-16:00, 19:30-22:00) |
| 30 | `0.011 p/kWh` | `721,132` | `£79.32` | **Green** (off-peak + weekends) - Largest! |

#### Network Costs (Rows 31-32)
| Row | Column F (Rate) | Column G (kWh) | Column H (Cost £) | Description |
|-----|-----------------|----------------|-------------------|-------------|
| 31 | `£12.50/MWh` | `1,083,150` | `£13,539.37` | TNUoS (transmission) |
| 32 | `£4.50/MWh` | `1,083,150` | `£4,874.17` | BNUoS (balancing) |

#### Environmental Levies (Rows 34-37)
| Row | Column F (Rate) | Column G (kWh) | Column H (Cost £) | Description |
|-----|-----------------|----------------|-------------------|-------------|
| 34 | `Total` | `1,083,150` | `£87,897.61` | Environmental levies total |
| 35 | `£7.75/MWh` | `1,083,150` | `£8,394.41` | CCL (Climate Change Levy) |
| 36 | `£61.90/MWh` | `1,083,150` | `£67,046.98` | RO (Renewables Obligation) |
| 37 | `£11.50/MWh` | `1,083,150` | `£12,456.22` | FiT (Feed-in Tariff) |

## Layout Structure

```
┌─────────────────────────────────────────┐  ┌─────────────────────────────────────────┐
│  COLUMNS A-C: Non-BESS Element Costs   │  │  COLUMNS F-H: BESS Element Costs       │
│  (Direct grid import without battery)   │  │  (Battery charging costs only)          │
├─────────────────────────────────────────┤  ├─────────────────────────────────────────┤
│  A: Cost category label                 │  │  F: Rate (p/kWh or £/MWh)              │
│  B: kWh consumed from grid              │  │  G: kWh charged by BESS                │
│  C: Total cost (£)                      │  │  H: Total cost (£)                     │
└─────────────────────────────────────────┘  └─────────────────────────────────────────┘
```

## BESS Charging Strategy (DUoS-Aware)

The script implements optimal arbitrage:

1. **CHARGE during GREEN** (0.011 p/kWh) - 67% of energy
2. **CHARGE during AMBER** (0.205 p/kWh) - 33% of energy, only if system price < £40/MWh
3. **NEVER CHARGE during RED** (1.764 p/kWh) - G28 should always be 0!

4. **DISCHARGE during RED** (100% of discharge) - Displaces expensive grid import
5. DUoS arbitrage spread: **1.753 p/kWh** (£17.53/MWh)

## Scripts Using This Structure

### calculate_bess_element_costs.py
- **Reads:** F13:F16 (BESS config), B10:D10 (DNO rates), D43 (PPA price)
- **Writes:** F28:H37 (BESS costs with rates, kWh, costs)
- **Logic:** DUoS-aware charging (GREEN priority, avoid RED)

### Future Scripts Should:
1. Import cell constants from `bess_sheet_constants.py`
2. Use named constants instead of hardcoded cell refs
3. Validate DNO rates from **row 10**, not row 9
4. Preserve all manual edits and formulas

## Validation Rules

✅ **G28 = 0** (Red charging should be zero)  
✅ **G30 > G29** (Green charging > Amber charging)  
✅ **Total charging ≈ 1,083,150 kWh/year** (based on 2025 data)  
✅ **Cycles ≈ 217/year** (0.59 cycles/day, well within 4/day limit)  

## Fixed Cost Rates

These are constants used in calculations:

```python
FIXED_COSTS = {
    'tnuos': 12.50,   # £/MWh
    'bnuos': 4.50,    # £/MWh
    'ccl': 7.75,      # £/MWh
    'ro': 61.90,      # £/MWh
    'fit': 11.50      # £/MWh
}
```

## Change Log

**2025-12-02**: 
- Documented complete BESS sheet structure
- Created cell mapping constants
- Fixed DNO rate reference (row 10, not row 9)
- Implemented DUoS-aware charging (avoid RED, prefer GREEN)
- Updated calculate_bess_element_costs.py to use constants

## Regenerating Documentation

To update this documentation after sheet changes:

```bash
python3 document_bess_structure.py
```

This will regenerate:
- `BESS_SHEET_STRUCTURE.json` (complete structure)
- `bess_sheet_constants.py` (Python constants)
- This README

---

**Maintainer**: George Major (george@upowerenergy.uk)  
**Repository**: https://github.com/GeorgeDoors888/GB-Power-Market-JJ

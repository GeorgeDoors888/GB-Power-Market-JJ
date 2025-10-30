# BMRS Data Catalogue Reference
## Version 5.0 - Effective 26 June 2025

## Source
**Document**: BMRS Data Catalogue V5.0  
**Authority**: Elexon Limited - Balancing and Settlement Code (BSC)  
**Effective Date**: 26 June 2025  
**Status**: LIVE  
**URL**: https://www.elexon.co.uk

## Key Data Sources Used in This Project

### 1. Generation Data (FUELINST)
- **Frequency**: Half-hourly (Settlement Periods)
- **Format**: Tabular
- **Content**: BM Unit fuel type generation by Settlement Period
- **Our Usage**: Primary source for gas, nuclear, wind, biomass, hydro, coal generation
- **Endpoint**: `/datasets/FUELINST/stream`

### 2. Wind & Solar Generation (Transparency Regulation - Article 16)
- **Frequency**: As received (typically every 30 minutes)
- **Format**: Tabular
- **Content**: Solar, Wind Onshore, Wind Offshore generation
- **Our Usage**: Solar generation data (not included in FUELINST)
- **Endpoint**: `/generation/actual/per-type/wind-and-solar`

### 3. System Frequency (FREQ)
- **Frequency**: Every 2 minutes
- **Format**: Tabular and graphic
- **Content**: Transmission System Frequency spot values
- **Our Usage**: Grid frequency monitoring

### 4. Demand Data
- **INDO** (Initial National Demand Out-turn): Half-hourly
- **ITSDO** (Initial Transmission System Demand Out-Turn): Half-hourly
- **Format**: Tabular and graphic
- **Our Usage**: System demand calculations

### 5. Balancing Services Adjustment Data (BSAD)
- **Frequency**: Daily
- **Format**: Tabular
- **Content**: System buy/sell price adjustments
- **Our Usage**: Price calculation inputs

## Data Retention Policy
Per Section 2.3.1:
- All BMRS data available for minimum **12 months** after Settlement Day
- Errors may be corrected during retention period
- Forecast data: 12 months from provision date

## Fuel Type Categories Defined by BMRS

Per Table 1, the NETSO provides data by Fuel Type Category:
- **CCGT** (Combined Cycle Gas Turbine) - Our "Gas"
- **NUCLEAR**
- **WIND** (includes onshore and offshore)
- **SOLAR** (via Transparency Regulation data)
- **BIOMASS**
- **NPSHYD** (Non-Pumped Storage Hydro) - Our "Hydro"
- **COAL**
- **OCGT** (Open Cycle Gas Turbine)
- **OIL**
- **OTHER**
- **PS** (Pumped Storage)
- **INT*** (Interconnectors - various codes)

## Data Availability Standards

### Publication Timing (from documentation)
1. **Real-time data**: Every 5 minutes (system generation by fuel type)
2. **Settlement Period data**: Half-hourly
3. **Day-ahead forecasts**: Published daily
4. **System warnings**: As received (text message)

### Data Lag (Our Observations)
- **FUELINST**: 5-15 minutes typical
- **WIND_SOLAR_GEN**: Up to 1 hour after Settlement Period ends
- **Frequency data**: 2-minute intervals

## Transparency Regulation Data (Table 2)

The BMRS publishes EU Transparency Regulation data including:
- **Article 6**: Load and consumption data
- **Article 8**: Unavailability of generation units
- **Article 13**: Cross-border balancing
- **Article 14**: Prices (day-ahead, intra-day)
- **Article 16**: Actual generation by fuel type ⭐ (Our solar source)
- **Article 17**: Wind and solar power forecasts

## Our Data Mapping to BMRS Catalogue

| Dashboard Item | BMRS Source | BMRS Code | Frequency | Table Reference |
|---------------|-------------|-----------|-----------|-----------------|
| Gas Generation | FUELINST | CCGT | Half-hourly | Table 1 |
| Nuclear | FUELINST | NUCLEAR | Half-hourly | Table 1 |
| Wind | FUELINST + Article 16 | WIND | Half-hourly | Table 1 & 2 |
| Solar | Article 16 (Transparency) | SOLAR | Half-hourly | Table 2 |
| Biomass | FUELINST | BIOMASS | Half-hourly | Table 1 |
| Hydro | FUELINST | NPSHYD | Half-hourly | Table 1 |
| Coal | FUELINST | COAL | Half-hourly | Table 1 |
| Interconnectors | FUELINST | INT* | Half-hourly | Table 1 |
| Frequency | System data | FREQ | 2 minutes | Table 1 |
| Demand | System data | INDO/ITSDO | Half-hourly | Table 1 |

## API Access Standards (Per BMRS)

### Machine-Readable Format (Section 2.2.3)
"Where possible, BMRS data should be made available in a machine readable format."

Our implementation uses:
- JSON format via REST API
- No API key required (public access)
- Developer portal: https://data.elexon.co.uk

### Data Validation (Section 2.1)
The BMRA validates:
- Energy adjustments (buy/sell price volumes)
- System adjustments
- Zero-sum constraints

## Settlement Periods

**Definition**: 30-minute intervals
- **Period 1**: 00:00-00:30
- **Period 2**: 00:30-01:00
- ...
- **Period 48**: 23:30-24:00

**Our Period 26**: 12:30-13:00 (typical solar peak in our data)

## Compliance Notes

### BSC Section V Requirements
This project complies with BSC Section V requirements for:
1. ✅ Using official BMRS data sources
2. ✅ Proper data attribution (Elexon/NETSO)
3. ✅ Machine-readable format consumption
4. ✅ Appropriate use of Transparency Regulation data

### Data Licence Terms
Usage subject to BMRS Data Licence Terms:
- ✅ Non-commercial use permitted
- ✅ Proper copyright notices maintained
- ✅ No misrepresentation of data accuracy
- ✅ ELEXON not liable for errors/omissions

## Reference Documents (Section 1.4)

Our project interfaces with:
1. **Balancing Mechanism Reporting Agent User Requirements Specification**
2. **Service Description for Balancing Mechanism Reporting**
3. **This BMRS Data Catalogue** (V5.0)

## Changes from Previous Versions

### Version 5.0 (26 June 2025) - Current
- Modification: P480
- Panel Reference: P356/06

### Version 4.0 (24 February 2025)
- Modification: P442
- Standard Release

### Version 3.0 (02 November 2023)
- Change: CP1583

## Contact Information

**ELEXON Limited**  
Balancing and Settlement Code Company (BSCCo)  
Website: https://www.elexon.co.uk  
BMRS Portal: https://www.bmreports.com

## Key Acronyms Used in Our Project

- **BM**: Balancing Mechanism
- **BMRA**: Balancing Mechanism Reporting Agent
- **BMRS**: Balancing Mechanism Reporting Service (our data source)
- **BSC**: Balancing and Settlement Code
- **NETSO**: National Electricity Transmission System Operator
- **SP**: Settlement Period (30 minutes)

## Data Quality Assurance

Per Section 2.3:
- Errors in data may be corrected by BMRS
- Default values provided for certain data types (Table 1, Column 4)
- Our system handles missing data gracefully (returns 0.0 or previous value)

---

**This Reference Document**: Created 29 October 2025  
**Purpose**: Quick reference for BMRS data sources used in UK Power Dashboard  
**Compliance**: BSC Section V, BMRS Data Catalogue V5.0  
**Data Provider**: ELEXON Limited / NETSO

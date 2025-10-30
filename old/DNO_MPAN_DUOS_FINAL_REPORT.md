# DNO DUoS Rate Analysis Report - Final
*Generated: September 15, 2025*

## Overview
This report presents an analysis of Distribution Use of System (DUoS) rates across different Distribution Network Operators (DNOs) in the UK. The analysis focuses on the relationship between MPAN codes (Meter Point Administration Number) and DNO information, as well as trends in DUoS rates over time.

## DNO Identification from MPAN Codes
The first two digits of an MPAN core (the distributor ID) can be used to identify the DNO. We've established the following comprehensive mapping:

| MPAN Code | DNO Name | DNO Key | Short Code | GSP Group | Region |
|-----------|----------|---------|------------|-----------|--------|
| 10 | UKPN – Eastern Power Networks | UKPN-E | Eastern | A | East Anglia |
| 11 | NGED – East Midlands | NGED-EM | EastMidlands | B | Nottingham, Leicester |
| 12 | UKPN – London Power Networks | UKPN-L | London | C | Greater London |
| 13 | SPEN – Manweb (Merseyside/N Wales) | SP-MW | Manweb | D | Liverpool, North Wales |
| 14 | NGED – Midlands | NGED-M | Midlands | E | Birmingham, Coventry |
| 15 | NPg – North East | NPg-NE | NorthEast | F | Newcastle, Durham |
| 16 | Electricity North West | ENWL | NorthWest | G | Manchester, Cumbria |
| 17 | UKPN – South Eastern | UKPN-SE | SouthEastern | H | Kent, Sussex |
| 18 | SSEN – Southern (SEPD) | SSE-S | Southern | J | Hampshire, Surrey, Berks |
| 19 | NGED – South Wales | NGED-SW | SouthWales | K | Cardiff, Swansea |
| 20 | NGED – South West | NGED-SW | SouthWest | L | Cornwall, Devon, Somerset |
| 21 | NPg – Yorkshire | NPg-Y | Yorkshire | M | Leeds, Sheffield |
| 22 | SSEN – Hydro (SHEPD) | SSE-H | Hydro | N | North Scotland (Highlands) |
| 23 | SPEN – Scottish Power (SPD) | SP-S | SPDistribution | P | Central & Southern Scotland |

## Key Findings

### Rate Variations Across DNOs
Based on our analysis of DUoS rates by DNO and year:

- **Highest Average Rate**: SSEN – Hydro (SHEPD) has the highest average mean rate at 4.29 p/kWh
- **Lowest Average Rate**: NPg – North East has the lowest average mean rate at 2.62 p/kWh
- **Widest Rate Range**: NPg – Yorkshire has the widest range of rates over time, with a maximum rate of 9.70 p/kWh
- **Most Stable Rates**: Electricity North West (ENWL) shows the most consistent rates over the years, with a standard deviation of 0.83 p/kWh

### Regional Patterns
- **Scotland**: Northern Scotland (SSE-H) has significantly higher rates than the rest of the UK
- **London**: Despite being a major urban area, London (UKPN-L) has midrange rates at 2.94 p/kWh
- **South East**: The South East (UKPN-SE) shows some of the lowest rates at 2.57 p/kWh
- **North-South Divide**: There is no clear north-south divide in rates, with both high and low rates found across the UK

### Time Trends
- Most DNOs show an increasing trend in DUoS rates over the years, with a particularly steep increase between 2022-2025
- The rate of increase varies significantly between DNOs, with some showing more gradual increases
- Recent years (2025-2026) show the highest rates across most DNOs

## Data Processing Steps
1. Created a comprehensive DNO reference mapping from MPAN codes to DNO information
2. Loaded and processed the DUoS data, linking it to the DNO information
3. Organized the data by DNO and year, calculating rate statistics
4. Generated visualizations to analyze trends and patterns

## Visualizations

### Mean Rates by DNO Over Time
The line chart shows how mean DUoS rates have changed over time for each DNO. This visualization reveals which DNOs have had the steepest increases and which have maintained more stable rates.

### Min/Max Rate Ranges
This visualization shows the range between minimum and maximum DUoS rates for each DNO, highlighting the variability within each distribution network.

### DUoS Rate Heatmap
The heatmap provides a clear view of how rates vary across both DNOs and years, making it easy to spot patterns and outliers.

### Median Rates Comparison
The bar chart compares median rates across DNOs for the most recent year, providing a snapshot of current pricing differences.

## Files Created
- **DNO_Reference_Complete.csv**: Comprehensive mapping of MPAN codes to DNO information
- **Organised_DNO_By_Date_Fixed.csv**: DUoS rates organized by DNO and year with proper DNO identification
- **dno_analysis_plots/**: Directory containing all visualizations
- **dno_analysis_plots/dno_rate_statistics.csv**: Summary statistics for each DNO

## Usage Guide
To identify a DNO from an MPAN:
1. Extract the first two digits of the MPAN core (positions 1-2 of the 13-digit core)
2. Look up this distributor ID in the DNO reference table
3. The corresponding row provides the DNO name, key, short code, and GSP group

For analyzing DUoS rates:
1. Use the `Organised_DNO_By_Date_Fixed.csv` file which contains rates by DNO and year
2. Refer to the visualizations in the `dno_analysis_plots` directory for trends and patterns
3. Use the `dno_rate_statistics.csv` file for summary statistics

## Conclusion
This analysis provides a clear understanding of how DUoS rates vary across different DNOs and over time. The proper mapping between MPAN codes and DNO information enables accurate identification of distribution networks from meter data, which is essential for energy suppliers, consumers, and regulatory bodies.

The significant variations in rates between DNOs highlight the importance of understanding regional differences in electricity distribution costs. This information can be valuable for energy cost forecasting, policy development, and consumer education about the regional components of their electricity bills.

# DNO DUoS Rate Analysis Report
*Generated: September 15, 2025*

## Overview
This report presents an analysis of Distribution Use of System (DUoS) rates across different Distribution Network Operators (DNOs) in the UK. The analysis focuses on the relationship between MPAN codes (Meter Point Administration Number) and DNO information, as well as trends in DUoS rates over time.

## DNO Identification from MPAN Codes
We've established a proper mapping between MPAN distributor IDs (the first two digits of the MPAN core) and the corresponding DNO information:

| MPAN Code | DNO Name | DNO Key | GSP Group | Region |
|-----------|----------|---------|-----------|--------|
| 10 | UK Power Networks (Eastern) | UKPN-EPN | A | East Anglia |
| 11 | National Grid Electricity Distribution – East Midlands | NGED-EM | B | Nottingham, Leicester |
| 12 | UK Power Networks (London) | UKPN-LPN | C | Greater London |
| 13 | SP Energy Networks – Manweb | SP-MW | D | Liverpool, North Wales |
| 14 | National Grid Electricity Distribution – Midlands | NGED-M | E | Birmingham, Coventry |
| 15 | Northern Powergrid – North East | NPg-NE | F | Newcastle, Durham |
| 16 | Electricity North West | ENWL | G | Manchester, Cumbria |
| 17 | UK Power Networks (South Eastern) | UKPN-SE | H | Kent, Sussex |
| 18 | SSEN – Southern (SEPD) | SSE-S | J | Hampshire, Surrey, Berks |
| 19 | National Grid Electricity Distribution – South Wales | NGED-SW | K | Cardiff, Swansea |
| 20 | National Grid Electricity Distribution – South West | NGED-SW | L | Cornwall, Devon, Somerset |
| 21 | Northern Powergrid – Yorkshire | NPg-Y | M | Leeds, Sheffield |
| 22 | SSEN – Hydro (SHEPD) | SSE-H | N | North Scotland (Highlands) |
| 23 | SP Energy Networks – Scottish Power (SPD) | SP-S | P | Central & Southern Scotland |

## Key Findings

### Rate Variations Across DNOs
- **Highest Average Rate**: SSEN – Hydro (SHEPD) has the highest average mean rate at 4.29 p/kWh
- **Lowest Average Rate**: Northern Powergrid – North East has the lowest average mean rate at 2.62 p/kWh
- **Widest Rate Range**: Northern Powergrid – Yorkshire has the widest range of rates over time
- **Most Stable Rates**: Electricity North West (ENWL) shows the most consistent rates over the years

### Time Trends
- Most DNOs show an increasing trend in DUoS rates over the years, with a particularly steep increase between 2022-2025
- The rate of increase varies significantly between DNOs, with some showing more gradual increases
- Regional variations are evident, with northern regions generally showing higher recent increases

### Data Coverage
- Years covered range from 2014 to 2026
- The most comprehensive data is available for National Grid Electricity Distribution areas
- Some DNOs have more limited historical data, particularly for earlier years

## Data Processing Steps
1. Created a comprehensive DNO reference mapping from MPAN codes
2. Loaded and processed the DUoS data, linking it to the DNO information
3. Organized the data by DNO and year, calculating rate statistics
4. Generated visualizations to analyze trends and patterns

## Visualizations

### Mean Rates by DNO Over Time
The line chart shows how mean DUoS rates have changed over time for each DNO. This helps identify which DNOs have had the steepest increases and which have maintained more stable rates.

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

## Conclusion
This analysis provides a clear understanding of how DUoS rates vary across different DNOs and over time. The proper mapping between MPAN codes and DNO information enables accurate identification of distribution networks from meter data, which is essential for energy suppliers, consumers, and regulatory bodies.

The significant variations in rates between DNOs and the general upward trend highlight the importance of understanding these patterns for energy cost forecasting and policy development.

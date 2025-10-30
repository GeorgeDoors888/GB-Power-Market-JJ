# UK DNO DUoS Charging Methodology - Complete Collection Guide

## Summary of Automated Downloads

We've successfully downloaded DUoS charging methodology files for the following DNOs:

1. **Scottish Hydro Electric Power Distribution (SHEPD)** - MPAN 17 (North Scotland)
   - All files successfully downloaded to `duos_ssen_data/shepd/`
   - Success rate: 100% (6/6 files)

2. **Southern Electric Power Distribution (SEPD)** - MPAN 20 (Southern England)
   - Most files successfully downloaded to `duos_ssen_data/sepd/`
   - Success rate: 83% (5/6 files)

## Manual Collection Required

The following DNOs require manual collection of files due to website access restrictions:

### SP Manweb (SPM) - MPAN 13 (Merseyside and North Wales)

The automatic downloads failed with 403 Forbidden errors. This suggests the website requires additional authorization or does not allow direct file downloads via scripts.

1. Visit the SP Energy Networks charging statement page:
   [https://www.spenergynetworks.co.uk/pages/use_of_system_charging_statements.aspx](https://www.spenergynetworks.co.uk/pages/use_of_system_charging_statements.aspx)

2. Look for the "SP Manweb" section and download:
   - SP Manweb Schedule of Charges (April 2025)
   - SP Manweb CDCM Model (2025-26)
   - SP Manweb Schedule of Charges (April 2026) if available
   - SP Manweb CDCM Model (2026-27) if available

3. Save the files to the `duos_spm_data` directory.

### National Grid Electricity Distribution (formerly Western Power Distribution)

The automatic downloads failed with 404 Not Found errors. The document library URL we tried to access also returned a 404 error, suggesting the page structure has changed since our script was created.

1. Visit the National Grid Electricity Distribution main page:
   [https://www.nationalgrid.com/electricity-distribution/](https://www.nationalgrid.com/electricity-distribution/)

2. Navigate to the charging statements section, likely under "About us" or "Document library"

3. For each region, download the following documents:
   - **East Midlands** (MPAN 11):
     - Schedule of Charges (2025-26)
     - CDCM Model (2025-26)
     - Schedule of Charges (2026-27) if available
     - CDCM Model (2026-27) if available

   - **West Midlands** (MPAN 14):
     - Schedule of Charges (2025-26)
     - CDCM Model (2025-26)
     - Schedule of Charges (2026-27) if available
     - CDCM Model (2026-27) if available

   - **South Wales** (MPAN 21):
     - Schedule of Charges (2025-26)
     - CDCM Model (2025-26)
     - Schedule of Charges (2026-27) if available
     - CDCM Model (2026-27) if available

   - **South West** (MPAN 22):
     - Schedule of Charges (2025-26)
     - CDCM Model (2025-26)
     - Schedule of Charges (2026-27) if available
     - CDCM Model (2026-27) if available

4. Save the files to the corresponding directories:
   - `duos_nged_data/east_midlands/`
   - `duos_nged_data/west_midlands/`
   - `duos_nged_data/south_wales/`
   - `duos_nged_data/south_west/`

## Alternative Approach for SP Manweb

If you're still having trouble accessing the SP Manweb files, you can try the following alternative sources:

1. **Ofgem's Website**: Ofgem sometimes publishes or links to DNO charging statements:
   [https://www.ofgem.gov.uk/energy-policy-and-regulation/policy-and-regulatory-programmes/network-price-controls](https://www.ofgem.gov.uk/energy-policy-and-regulation/policy-and-regulatory-programmes/network-price-controls)

2. **The Energy Networks Association (ENA)**: They sometimes collate DNO charging information:
   [https://www.energynetworks.org/](https://www.energynetworks.org/)

3. **Direct Contact**: Contact SP Energy Networks directly to request the charging methodology documents:
   - Email: customercare@spenergynetworks.com
   - Phone: 0330 1010 300

## Alternative Approach for National Grid

For National Grid Electricity Distribution, you can also try:

1. **Direct Document ID Access**: Sometimes you can access documents directly if you know the document ID:
   `https://www.nationalgrid.com/document/DOCUMENT_ID/download`

   Try different document IDs in the range of 160000-162000, as these appear to be the current range based on our testing.

2. **Distribution Charging Methodologies Forum (DCMF)**: National Grid might publish their charging methodologies through this forum:
   [https://www.dcmf.co.uk/](https://www.dcmf.co.uk/)

3. **Direct Contact**: Contact National Grid directly to request the charging methodology documents:
   - Email: info@nationalgrid.com
   - Customer Service: 0800 096 3080

## MPAN Codes Reference

For your reference, here are the MPAN codes for each DNO region:

- Scottish Hydro Electric Power Distribution (SHEPD): 17 (North Scotland)
- Southern Electric Power Distribution (SEPD): 20 (Southern England)
- SP Manweb: 13 (Merseyside and North Wales)
- SP Distribution: 18 (Central & Southern Scotland)
- National Grid Electricity Distribution (East Midlands): 11 (East Midlands)
- National Grid Electricity Distribution (West Midlands): 14 (West Midlands)
- National Grid Electricity Distribution (South Wales): 21 (South Wales)
- National Grid Electricity Distribution (South West): 22 (South West England)
- Northern Powergrid (Northeast): 15 (Northeast England)
- Northern Powergrid (Yorkshire): 23 (Yorkshire)
- UK Power Networks (Eastern): 10 (Eastern England)
- UK Power Networks (London): 12 (London)
- UK Power Networks (South Eastern): 19 (South Eastern England)
- Electricity North West: 16 (North West England)

## Processing the Downloaded Files

Once you've collected all the files, you can process them using your existing scripts such as `duos_tariff_extractor.py` to extract the relevant information.

## Completion Checklist

- [x] SHEPD (MPAN 17) - 6/6 files downloaded
- [x] SEPD (MPAN 20) - 5/6 files downloaded
- [ ] SP Manweb (MPAN 13) - 0/4 files downloaded - Manual collection required
- [ ] NGED East Midlands (MPAN 11) - 0/4 files downloaded - Manual collection required
- [ ] NGED West Midlands (MPAN 14) - 0/4 files downloaded - Manual collection required
- [ ] NGED South Wales (MPAN 21) - 0/4 files downloaded - Manual collection required
- [ ] NGED South West (MPAN 22) - 0/4 files downloaded - Manual collection required

Once you've completed the manual collection, you'll have 100% coverage of all the required UK DNO DUoS charging methodologies!

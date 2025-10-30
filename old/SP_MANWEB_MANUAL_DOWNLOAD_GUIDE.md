# SP Manweb DUoS Charging Methodology - Manual Download Guide

Since the automated download attempts are resulting in 403 Forbidden errors, you'll need to manually download the SP Manweb files from the Scottish Power website.

## Files to Download

### For Year 2026:

1. **SPM LC14 Charging Statement – April 2026**
   - URL: [LC14-Statement-2026_SPM_v01.pdf](https://www.scottishpower.com/userfiles/file/LC14-Statement-2026_SPM_v01.pdf)
   - Save as: `duos_spm_data/SPM_LC14_Charging_Statement_2026.pdf`

2. **SPM Schedule of Charges and Other Tables - April 2026**
   - URL: [SPM-Schedule-of-charges-and-other-tables-2026-V0.1-Annex-6.xlsx](https://www.scottishpower.com/userfiles/file/SPM-Schedule-of-charges-and-other-tables-2026-V0.1-Annex-6.xlsx)
   - Save as: `duos_spm_data/SPM-Schedule-of-charges-and-other-tables-2026-V0.1-Annex-6.xlsx`

3. **SPM CDCM Model - April 2026**
   - URL: [SPM 2026_27 CDCM_v11_20241025_Published.xlsx](https://www.scottishpower.com/userfiles/file/SPM%202026_27%20CDCM_v11_20241025_Published.xlsx)
   - Save as: `duos_spm_data/SPM_2026_27_CDCM_v11_20241025_Published.xlsx`

### For Year 2025:

1. **SPM LC14 Charging Statement – April 2025**
   - URL: [SPM_LC14_Statement_2025_V05.pdf](https://www.scottishpower.com/userfiles/file/SPM_LC14_Statement_2025_V05.pdf)
   - Save as: `duos_spm_data/SPM_LC14_Statement_2025_V05.pdf`

2. **SPM Schedule of Charges and Other Tables - April 2025**
   - URL: [SPM-Schedule-of-charges-and-other-tables-2025-V.0.7-Annex-6.xlsx](https://www.scottishpower.com/userfiles/file/SPM-Schedule-of-charges-and-other-tables-2025-V.0.7-Annex-6.xlsx)
   - Save as: `duos_spm_data/SPM-Schedule-of-charges-and-other-tables-2025-V.0.7-Annex-6.xlsx`

3. **SPM CDCM Model - April 2025**
   - URL: [SPM_2025_26_CDCM_v10_20231106.xlsx](https://www.scottishpower.com/userfiles/file/SPM_2025_26_CDCM_v10_20231106.xlsx)
   - Save as: `duos_spm_data/SPM_2025_26_CDCM_v10_20231106.xlsx`

## Step-by-Step Instructions

1. Visit the SP Manweb charging statement page:
   [https://www.scottishpower.com/pages/connections_use_of_system_and_metering_services.aspx](https://www.scottishpower.com/pages/connections_use_of_system_and_metering_services.aspx)

2. Navigate to the "SP Manweb" section

3. For each file:
   - Find the link in the list
   - Right-click and select "Save Link As" or "Download Linked File"
   - Navigate to the `duos_spm_data` directory
   - Save the file with the suggested filename

4. Once all files are downloaded, you can process them with your existing scripts

## Alternative Method

If you encounter issues with direct downloads, you can also:

1. Open each file in your browser by clicking the link
2. Use the browser's "Save As" option to save the file to your computer
3. Move the downloaded files to the `duos_spm_data` directory

## Important Note

The Scottish Power website uses protection measures that prevent automated downloads directly using scripts. This is why you're seeing 403 Forbidden errors in your automated download attempts. Manual download through a web browser is the most reliable method to obtain these files.

# DNO Charging Methodology - Manual Download Guide

This guide provides direct links to the websites where you can manually download DUoS charging methodology files for the DNOs that couldn't be automatically downloaded.

## Scottish Power Manweb (SPM)

SP Manweb files can be downloaded from the Scottish Power Energy Networks website. The automatic downloads failed due to website restrictions (403 Forbidden errors).

1. Visit the SP Energy Networks charging statement page:
   [https://www.spenergynetworks.co.uk/pages/use_of_system_charging_statements.aspx](https://www.spenergynetworks.co.uk/pages/use_of_system_charging_statements.aspx)

2. Look for "SP Manweb" section and download:
   - SP Manweb Schedule of Charges (April 2025)
   - SP Manweb CDCM Model (2025-26)
   - SP Manweb Schedule of Charges (April 2026) if available
   - SP Manweb CDCM Model (2026-27) if available

3. Save the files to the `duos_spm_data` directory.

## National Grid Electricity Distribution (formerly Western Power Distribution)

National Grid files can be downloaded from their website. The automatic downloads failed due to incorrect document IDs (404 Not Found errors).

1. Visit the National Grid Electricity Distribution charging statements page:
   [https://www.nationalgrid.com/electricity-distribution/document-library/charging-statements](https://www.nationalgrid.com/electricity-distribution/document-library/charging-statements)

2. Filter by region:
   - East Midlands
   - West Midlands
   - South Wales
   - South West

3. For each region, download:
   - Schedule of Charges (2025-26)
   - CDCM Model (2025-26)
   - Schedule of Charges (2026-27) if available
   - CDCM Model (2026-27) if available

4. Save the files to the corresponding directories:
   - `duos_nged_data/east_midlands/`
   - `duos_nged_data/west_midlands/`
   - `duos_nged_data/south_wales/`
   - `duos_nged_data/south_west/`

## Alternative: Use Web Browser Automation

If you want to automate this process, consider using a browser automation tool like Selenium. This would allow you to:

1. Navigate to the website
2. Interact with the page (click on links, fill forms, etc.)
3. Download files directly

Here's a simple example of how you could use Selenium to download SP Manweb files:

```python
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import os

# Set up the browser
driver = webdriver.Chrome()  # or Firefox, Edge, etc.

# Create download directory
os.makedirs("duos_spm_data", exist_ok=True)

# Navigate to the SP Energy Networks website
driver.get("https://www.spenergynetworks.co.uk/pages/use_of_system_charging_statements.aspx")

# Wait for page to load
WebDriverWait(driver, 10).until(
    EC.presence_of_element_located((By.ID, "content"))
)

# Find SP Manweb section and download links
sp_manweb_links = driver.find_elements(By.XPATH, "//a[contains(text(), 'SP Manweb') and contains(text(), 'xlsx')]")

# Download each file
for link in sp_manweb_links:
    link.click()
    time.sleep(3)  # Wait for download to start

# Close the browser
driver.quit()
```

Similarly, you could create scripts for National Grid Electricity Distribution.

## Direct Download Links (If Discovered)

If we discover the exact direct download links during manual exploration, we'll update this guide with those links for future automation.

## MPAN Codes for Reference

For reference, here are the MPAN codes for each DNO region:

- Scottish Hydro Electric Power Distribution (SHEPD): 17 (North Scotland)
- Southern Electric Power Distribution (SEPD): 20 (Southern England)
- SP Manweb: 13 (Merseyside and North Wales)
- National Grid Electricity Distribution (East Midlands): 11 (East Midlands)
- National Grid Electricity Distribution (West Midlands): 14 (West Midlands)
- National Grid Electricity Distribution (South Wales): 21 (South Wales)
- National Grid Electricity Distribution (South West): 22 (South West England)

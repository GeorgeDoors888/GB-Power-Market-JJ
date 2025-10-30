#!/usr/bin/env python3
"""
Complete DUoS Data & Methodology Downloader
Following CLAUDE_duos.md specifications

Downloads:
1. DUoS time bands (Red/Amber/Green) and unit rates for all 14 DNO license areas
2. Charging methodologies and statements
3. Creates comprehensive reference MD file
4. Uploads to Google Drive with proper folder structure

Methodology per CLAUDE_duos.md:
- OpenDataSoft API for: UKPN (3), NPg (2), ENWL (1), SPEN (2)
- Charging Statement downloads for: NGED (4), SSEN (2)
"""

import requests
import json
import os
from pathlib import Path
from datetime import datetime
import time
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import pickle
import io
from googleapiclient.http import MediaIoBaseDownload
import pandas as pd

# Configuration from CLAUDE_duos.md
DNOS = {
    # UK Power Networks (ODS API)
    '10': {'mpan': 10, 'licence': 'EPN', 'name': 'Eastern', 'company': 'UKPN', 'source': 'ODS'},
    '12': {'mpan': 12, 'licence': 'LPN', 'name': 'London', 'company': 'UKPN', 'source': 'ODS'},
    '19': {'mpan': 19, 'licence': 'SPN', 'name': 'South Eastern', 'company': 'UKPN', 'source': 'ODS'},
    
    # NGED (Website Downloads)
    '11': {'mpan': 11, 'licence': 'EMID', 'name': 'East Midlands', 'company': 'NGED', 'source': 'WEB'},
    '14': {'mpan': 14, 'licence': 'WMID', 'name': 'West Midlands', 'company': 'NGED', 'source': 'WEB'},
    '21': {'mpan': 21, 'licence': 'SWALES', 'name': 'South Wales', 'company': 'NGED', 'source': 'WEB'},
    '22': {'mpan': 22, 'licence': 'SWEST', 'name': 'South Western', 'company': 'NGED', 'source': 'WEB'},
    
    # Northern Powergrid (ODS + Website)
    '15': {'mpan': 15, 'licence': 'NE', 'name': 'North East', 'company': 'NPg', 'source': 'ODS+WEB'},
    '23': {'mpan': 23, 'licence': 'Y', 'name': 'Yorkshire', 'company': 'NPg', 'source': 'ODS+WEB'},
    
    # Electricity North West (ODS + Website)
    '16': {'mpan': 16, 'licence': 'ENWL', 'name': 'North West', 'company': 'ENWL', 'source': 'ODS+WEB'},
    
    # SP Energy Networks (ODS + Website)
    '13': {'mpan': 13, 'licence': 'SPM', 'name': 'Merseyside & N Wales', 'company': 'SPEN', 'source': 'ODS+WEB'},
    '18': {'mpan': 18, 'licence': 'SPD', 'name': 'South Scotland', 'company': 'SPEN', 'source': 'ODS+WEB'},
    
    # SSEN Distribution (Website)
    '17': {'mpan': 17, 'licence': 'SHEPD', 'name': 'North Scotland', 'company': 'SSEN', 'source': 'WEB'},
    '20': {'mpan': 20, 'licence': 'SEPD', 'name': 'Southern', 'company': 'SSEN', 'source': 'WEB'},
}

# Years to download (charging years run Apr-Mar)
CHARGING_YEARS = [f"{y}/{str(y+1)[-2:]}" for y in range(2016, 2026)]  # 2016/17 to 2025/26

# OpenDataSoft API URLs (from CLAUDE_duos.md)
ODS_APIS = {
    'UKPN': {
        'base': 'https://ukpowernetworks.opendatasoft.com/api/records/1.0/search/',
        'dataset': 'ukpn-distribution-use-of-system-charges-annex-1'
    },
    'NPg': {
        'base': 'https://northernpowergrid.opendatasoft.com/api/records/1.0/search/',
        'dataset': None  # To be discovered
    },
    'ENWL': {
        'base': 'https://electricitynorthwest.opendatasoft.com/api/records/1.0/search/',
        'dataset': None  # To be discovered
    },
    'SPEN': {
        'base': 'https://spenergynetworks.opendatasoft.com/api/records/1.0/search/',
        'dataset': None  # To be discovered
    }
}

# Charging Statement URLs (from CLAUDE_duos.md)
CHARGING_STATEMENT_URLS = {
    'NGED': 'https://commercial.nationalgrid.co.uk/our-network/use-of-system-charges/charging-statements-archive',
    'SSEN_SHEPD': 'https://www.ssen.co.uk/about-ssen/library/charging-statements-and-information/scottish-hydro-electric-power-distribution/',
    'SSEN_SEPD': 'https://www.ssen.co.uk/about-ssen/library/charging-statements-and-information/southern-electric-power-distribution/',
    'NPg': 'https://www.northernpowergrid.com/use-of-system-charges',
    'ENWL': 'https://www.enwl.co.uk/about-us/regulatory-information/use-of-system-charges/',
    'SPEN': 'https://www.spenergynetworks.co.uk/pages/distribution_code.aspx'
}

# Methodology URLs
METHODOLOGY_URLS = {
    'UKPN': 'https://ukpowernetworks.opendatasoft.com/pages/charging-methodology/',
    'NGED': 'https://commercial.nationalgrid.co.uk/our-network/use-of-system-charges/charging-methodology/',
    'NPg': 'https://www.northernpowergrid.com/our-network/charging-methodology',
    'ENWL': 'https://www.enwl.co.uk/about-us/regulatory-information/charging-methodology/',
    'SPEN': 'https://www.spenergynetworks.co.uk/pages/charging_methodology.aspx',
    'SSEN': 'https://www.ssen.co.uk/about-ssen/dso/charging-and-network-access/'
}

# Local directories
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / 'duos_data_complete'
DATA_DIR.mkdir(exist_ok=True)

# Create subdirectories
API_DATA_DIR = DATA_DIR / 'api_data'
STATEMENTS_DIR = DATA_DIR / 'charging_statements'
METHODOLOGIES_DIR = DATA_DIR / 'methodologies'
PROCESSED_DIR = DATA_DIR / 'processed'

for d in [API_DATA_DIR, STATEMENTS_DIR, METHODOLOGIES_DIR, PROCESSED_DIR]:
    d.mkdir(exist_ok=True)

def get_drive_service():
    """Get Google Drive service with OAuth"""
    creds = None
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            print("⚠️  Run oauth_with_sheets.py first to authenticate")
            return None
    
    return build('drive', 'v3', credentials=creds)

def create_drive_folder(service, folder_name, parent_id=None):
    """Create folder in Google Drive"""
    file_metadata = {
        'name': folder_name,
        'mimeType': 'application/vnd.google-apps.folder'
    }
    if parent_id:
        file_metadata['parents'] = [parent_id]
    
    try:
        folder = service.files().create(body=file_metadata, fields='id').execute()
        return folder.get('id')
    except Exception as e:
        print(f"  ⚠️  Folder creation error: {e}")
        return None

def upload_to_drive(service, file_path, folder_id=None):
    """Upload file to Google Drive"""
    try:
        file_metadata = {'name': file_path.name}
        if folder_id:
            file_metadata['parents'] = [folder_id]
        
        media = MediaFileUpload(str(file_path), resumable=True)
        file = service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id, webViewLink'
        ).execute()
        
        return file.get('webViewLink')
    except Exception as e:
        print(f"  ❌ Upload error: {e}")
        return None

def fetch_ods_data(company, licence, max_records=10000):
    """Fetch DUoS data from OpenDataSoft API"""
    api_config = ODS_APIS.get(company)
    if not api_config or not api_config['dataset']:
        print(f"  ⚠️  ODS dataset not configured for {company}")
        return None
    
    url = api_config['base']
    params = {
        'dataset': api_config['dataset'],
        'rows': max_records
    }
    
    # Add license filter for UKPN
    if company == 'UKPN':
        params['refine.licence'] = licence
    
    try:
        print(f"  📡 Fetching from ODS API: {api_config['dataset']}")
        response = requests.get(url, params=params, timeout=60)
        response.raise_for_status()
        data = response.json()
        
        records = data.get('records', [])
        print(f"  ✅ Retrieved {len(records)} records")
        
        return records
    except Exception as e:
        print(f"  ❌ ODS API error: {e}")
        return None

def parse_ods_to_schema(records, licence, company):
    """Parse ODS records to standard schema (from CLAUDE_duos.md)"""
    parsed_data = []
    
    for record in records:
        fields = record.get('fields', {})
        
        # Helper function to safely convert to string and lowercase
        def safe_lower(value, default=''):
            if value is None:
                return default
            return str(value).lower()
        
        # Extract fields (field names may vary by DNO)
        row = {
            'licence': licence,
            'dno_group': company,
            'charging_year': str(fields.get('charging_year', '')),
            'band': safe_lower(fields.get('band', fields.get('time_band', ''))),
            'day_type': safe_lower(fields.get('day_type', fields.get('day', 'all'))),
            'start_time': str(fields.get('start_time', fields.get('from_time', ''))),
            'end_time': str(fields.get('end_time', fields.get('to_time', ''))),
            'unit_rate_p_per_kwh': float(fields.get('unit_rate_p_per_kwh', fields.get('rate', 0))) if fields.get('unit_rate_p_per_kwh', fields.get('rate', 0)) else 0,
            'voltage_class': str(fields.get('voltage_class', fields.get('voltage', 'LV'))),
            'valid_from': str(fields.get('valid_from', '')),
            'valid_to': str(fields.get('valid_to', '')),
            'source_url': ODS_APIS[company]['base'],
            'source_format': 'json',
            'last_seen_utc': datetime.utcnow().isoformat()
        }
        parsed_data.append(row)
    
    return parsed_data

def search_drive_for_statements(service, company, licence):
    """Search Google Drive for existing charging statements"""
    if not service:
        return []
    
    search_terms = {
        'NGED': f"(NGED OR 'National Grid') AND {licence} AND ('Schedule of Charges' OR 'Charging Statement')",
        'SSEN': f"SSEN AND {licence} AND ('Schedule of Charges' OR 'Statement of Use of System')",
        'NPg': f"'Northern Powergrid' AND {licence} AND 'Schedule of Charges'",
        'ENWL': f"ENWL AND 'Schedule of Charges'",
        'SPEN': f"'SP Energy Networks' AND {licence} AND 'Schedule of Charges'"
    }
    
    query = search_terms.get(company, f"{company} {licence} charging")
    
    try:
        results = service.files().list(
            q=f"name contains 'Charges' or name contains 'Statement'",
            spaces='drive',
            fields='files(id, name, mimeType, webViewLink, modifiedTime, size)',
            pageSize=50
        ).execute()
        
        files = results.get('files', [])
        
        # Filter by company/licence
        relevant_files = []
        for f in files:
            name_lower = f['name'].lower()
            if licence.lower() in name_lower or company.lower() in name_lower:
                relevant_files.append(f)
        
        return relevant_files
    except Exception as e:
        print(f"  ❌ Drive search error: {e}")
        return []

def generate_markdown_reference(all_results, drive_links):
    """Generate comprehensive markdown reference document"""
    
    md_content = f"""# DUoS Data & Methodology Reference
**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}  
**Project:** GB Power Market JJ - Distribution Use of System Data

---

## Overview

This document provides a comprehensive reference for all DUoS (Distribution Use of System) data and methodologies downloaded for the 14 GB electricity distribution network operator license areas.

**Data Coverage:**
- **Time Period:** 2016/17 to 2025/26 (10 charging years)
- **License Areas:** All 14 GB DNO license areas
- **Data Types:** 
  - Time-of-Use bands (Red/Amber/Green)
  - Half-hourly unit rates (p/kWh)
  - Charging methodologies and statements

**Methodology:** Following specifications in `CLAUDE_duos.md`

---

## Data Sources by DNO

### UK Power Networks (UKPN) - 3 License Areas

**Data Source:** OpenDataSoft API  
**API URL:** https://ukpowernetworks.opendatasoft.com/api/records/1.0/search/  
**Dataset ID:** `ukpn-distribution-use-of-system-charges-annex-1`

"""
    
    # Add details for each DNO
    for mpan_id, result in sorted(all_results.items()):
        dno = DNOS[mpan_id]
        md_content += f"\n#### {dno['licence']} - {dno['name']} (MPAN {mpan_id})\n"
        md_content += f"**Company:** {dno['company']}  \n"
        md_content += f"**Data Source:** {dno['source']}  \n"
        
        # API data
        if result.get('api_records'):
            records_count = len(result['api_records'])
            md_content += f"**API Records:** {records_count} records downloaded  \n"
            
            # Local file
            if result.get('local_api_file'):
                md_content += f"**Local File:** `{result['local_api_file']}`  \n"
            
            # Drive link
            if result.get('drive_api_link'):
                md_content += f"**Google Drive:** [{result['local_api_file'].name}]({result['drive_api_link']})  \n"
        
        # Statement files
        if result.get('statement_files'):
            md_content += f"**Charging Statements:** {len(result['statement_files'])} files found  \n"
            for file_info in result['statement_files'][:5]:  # Show first 5
                md_content += f"  - {file_info.get('name', 'Unknown')}  \n"
            if len(result['statement_files']) > 5:
                md_content += f"  - ... and {len(result['statement_files']) - 5} more  \n"
        
        # Methodology
        if result.get('methodology_url'):
            md_content += f"**Methodology URL:** {result['methodology_url']}  \n"
        
        # Status
        status = result.get('status', 'Unknown')
        status_emoji = {
            'Complete': '✅',
            'Partial': '🟡',
            'Pending': '⏳',
            'Error': '❌'
        }.get(status, '❓')
        
        md_content += f"**Status:** {status_emoji} {status}  \n\n"
    
    # Add data schema section
    md_content += """
---

## Data Schema

All downloaded data is normalized to the following schema (per `CLAUDE_duos.md`):

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| `licence` | string | License area short code | `LPN`, `EPN`, `EMID` |
| `dno_group` | string | Company group | `UKPN`, `NGED`, `NPg` |
| `charging_year` | string | Charging year (Apr-Mar) | `2024/25` |
| `band` | string | Time-of-use band | `red`, `amber`, `green` |
| `day_type` | string | Day classification | `weekday`, `weekend`, `all` |
| `start_time` | string | Period start time (24h) | `16:00` |
| `end_time` | string | Period end time (24h) | `19:00` |
| `unit_rate_p_per_kwh` | float | Energy charge | `12.345` |
| `voltage_class` | string | Voltage level | `LV`, `HV`, `EHV` |
| `valid_from` | date | Start date (ISO) | `2024-04-01` |
| `valid_to` | date | End date (ISO) | `2025-03-31` |
| `source_url` | string | Data source URL | API or file URL |
| `source_format` | string | Source format | `json`, `csv`, `xlsx`, `pdf` |
| `last_seen_utc` | datetime | Extraction timestamp | ISO 8601 UTC |

---

## Processed Data Files

### Master CSV File
**Location:** `duos_data_complete/processed/duos_rates_times.csv`  
**Description:** Normalized data from all 14 DNO license areas  
**Schema:** As defined above  
**Rows:** [To be calculated after parsing]

### Google Drive Structure
**Root Folder:** DUoS Data Complete  
"""
    
    # Add Drive folder structure
    if drive_links.get('root_folder_id'):
        md_content += f"**Folder ID:** {drive_links['root_folder_id']}  \n\n"
        md_content += "**Subfolders:**\n"
        for folder_name, folder_id in drive_links.get('subfolders', {}).items():
            md_content += f"- {folder_name}: [{folder_id}](https://drive.google.com/drive/folders/{folder_id})  \n"
    
    md_content += """
---

## Charging Methodologies

### UKPN (UK Power Networks)
**Methodology URL:** https://ukpowernetworks.opendatasoft.com/pages/charging-methodology/  
**Document Type:** CDCM (Common Distribution Charging Methodology)  
**Key Features:**
- Time-of-use bands: Red/Amber/Green
- Voltage levels: LV, HV, EHV
- Super-red days (critical peak pricing)

### NGED (National Grid Electricity Distribution)
**Methodology URL:** https://commercial.nationalgrid.co.uk/our-network/use-of-system-charges/charging-methodology/  
**Document Type:** CDCM  
**Coverage:** 4 license areas (EMID, WMID, SWALES, SWEST)

### Northern Powergrid (NPg)
**Methodology URL:** https://www.northernpowergrid.com/our-network/charging-methodology  
**Coverage:** 2 license areas (NE, Y)

### Electricity North West (ENWL)
**Methodology URL:** https://www.enwl.co.uk/about-us/regulatory-information/charging-methodology/  
**Coverage:** 1 license area (ENWL)

### SP Energy Networks (SPEN)
**Methodology URL:** https://www.spenergynetworks.co.uk/pages/charging_methodology.aspx  
**Coverage:** 2 license areas (SPD, SPM)

### SSEN Distribution
**Methodology URL:** https://www.ssen.co.uk/about-ssen/dso/charging-and-network-access/  
**Coverage:** 2 license areas (SHEPD, SEPD)

---

## Validation Rules

Per `CLAUDE_duos.md` Section 5:

### Band Coverage
- [ ] Red + Amber + Green should cover full 24-hour day
- [ ] Weekday vs Weekend bands documented
- [ ] No gaps or overlaps in time windows

### Time Windows
- [ ] All times in HH:MM format (24-hour)
- [ ] Start time < End time (or spans midnight)
- [ ] Consistent across charging year

### Rate Reasonableness
- [ ] LV rates typically: 1-30 p/kWh
- [ ] HV rates typically: 0.5-15 p/kWh
- [ ] Flag outliers > 50 p/kWh for review

### Completeness
- [ ] All 14 DNOs represented
- [ ] Each DNO has data for charging years 2016/17 - 2025/26
- [ ] All required schema columns populated

---

## Key DUoS Reforms

### DCP228 (April 2018)
- Changed time-of-use band definitions
- Introduced "super-red" days for some DNOs
- Updated unit rate calculations

### TCR (Targeted Charging Review) - From 2022
- Shifted from volumetric to capacity-based charges
- Changed residual charging approach
- Impacted standing charges

### EDCM/CDCM Split
- **EDCM** (Extra High Voltage) - Demand > 1 MVA
- **CDCM** (Common) - LV and HV customers
- Different methodologies and rate structures

---

## Usage Examples

### Query Red Band Rates for London (LPN)
```python
import pandas as pd

df = pd.read_csv('duos_data_complete/processed/duos_rates_times.csv')

london_red = df[
    (df['licence'] == 'LPN') & 
    (df['band'] == 'red') &
    (df['charging_year'] == '2024/25')
]

print(london_red[['day_type', 'start_time', 'end_time', 'unit_rate_p_per_kwh']])
```

### Compare Rates Across DNOs
```python
# Average red band rate by DNO for 2024/25
avg_rates = df[
    (df['band'] == 'red') &
    (df['charging_year'] == '2024/25') &
    (df['voltage_class'] == 'LV')
].groupby('licence')['unit_rate_p_per_kwh'].mean().sort_values(ascending=False)

print(avg_rates)
```

### Time Coverage Check
```python
# Verify 24-hour coverage for each DNO
for licence in df['licence'].unique():
    licence_data = df[
        (df['licence'] == licence) &
        (df['charging_year'] == '2024/25') &
        (df['day_type'] == 'weekday')
    ]
    
    # Calculate total hours covered
    # (implementation depends on time format)
    print(f"{licence}: {len(licence_data)} time periods")
```

---

## Next Steps

### Parsing & Normalization
1. Parse UKPN ODS JSON files to schema
2. Parse NGED Excel charging statements (Annex 1 + unit rate tables)
3. Parse SSEN Excel charging statements
4. Merge all sources to master CSV

### Upload to BigQuery
1. Create table: `inner-cinema-476211-u9.uk_energy_prod.duos_rates`
2. Define schema matching CSV columns
3. Upload master CSV with timestamps
4. Create views for common queries

### Dashboard Integration
1. Add cell A14: Current DUoS band based on time
2. Add cell A15: Current DUoS rate for selected license area
3. Create time-of-day visualization (Red/Amber/Green bands)

---

## References

### Internal Documentation
- `CLAUDE_duos.md` - Technical specification (this methodology)
- `CLAUDE_energy_data.md` - Complete energy data guide
- `DNO_LICENSE_AREAS.md` - DNO reference with download status
- `PROJECT_SUMMARY.md` - Project status report

### External Resources
- Ofgem DUoS Guidance: https://www.ofgem.gov.uk/electricity/distribution-networks/charging
- Energy Networks Association: https://www.energynetworks.org/
- Open Networks Project: https://www.energynetworks.org/industry-hub/resource-library/on-2023-duos-charging

### API Documentation
- UKPN ODS: https://ukpowernetworks.opendatasoft.com/api/
- Northern Powergrid ODS: https://northernpowergrid.opendatasoft.com/api/
- ENWL ODS: https://electricitynorthwest.opendatasoft.com/api/
- SPEN ODS: https://spenergynetworks.opendatasoft.com/api/

---

## Download Summary

**Total DNOs:** 14  
**Charging Years:** 10 (2016/17 - 2025/26)  
**Expected Records:** ~140 time period definitions × 14 DNOs = ~2,000 records  
**Download Date:** {datetime.now().strftime('%Y-%m-%d')}  
**Download Method:** API (8 DNOs) + Website Files (6 DNOs)

---

## Contact & Support

**Project:** GB Power Market JJ  
**Repository:** jibber-jabber-24-august-2025-big-bop  
**Owner:** GeorgeDoors888  
**Documentation:** See `DOCUMENTATION_INDEX.md` for complete file list

For questions about DUoS data methodology, refer to individual DNO websites or Ofgem guidance.

---

**Document Version:** 1.0  
**Last Updated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}
"""
    
    return md_content

def main():
    """Main execution function"""
    print("="*80)
    print("DUoS COMPLETE DATA & METHODOLOGY DOWNLOADER")
    print("="*80)
    print(f"\nFollowing methodology from: CLAUDE_duos.md")
    print(f"Output directory: {DATA_DIR}")
    print(f"Charging years: {', '.join(CHARGING_YEARS)}")
    print(f"\nStarting download: {datetime.now().isoformat()}\n")
    
    # Get Drive service
    drive_service = get_drive_service()
    drive_links = {}
    
    # Create root folder in Drive
    if drive_service:
        print("📁 Creating Google Drive folder structure...")
        root_folder_id = create_drive_folder(drive_service, "DUoS Data Complete")
        if root_folder_id:
            drive_links['root_folder_id'] = root_folder_id
            
            # Create subfolders
            drive_links['subfolders'] = {}
            for subfolder in ['API Data', 'Charging Statements', 'Methodologies', 'Processed']:
                folder_id = create_drive_folder(drive_service, subfolder, root_folder_id)
                if folder_id:
                    drive_links['subfolders'][subfolder] = folder_id
            
            print(f"✅ Drive folder created: {root_folder_id}\n")
    
    all_results = {}
    
    # Process each DNO
    for mpan_id in sorted(DNOS.keys()):
        dno = DNOS[mpan_id]
        
        print(f"\n{'='*80}")
        print(f"DNO: {dno['licence']} - {dno['name']} (MPAN {mpan_id})")
        print(f"Company: {dno['company']} | Source: {dno['source']}")
        print(f"{'='*80}\n")
        
        result = {
            'dno': dno,
            'api_records': None,
            'statement_files': [],
            'methodology_url': METHODOLOGY_URLS.get(dno['company']),
            'status': 'Pending'
        }
        
        # Method 1: ODS API
        if dno['source'] in ['ODS', 'ODS+WEB']:
            api_data = fetch_ods_data(dno['company'], dno['licence'])
            
            if api_data:
                # Parse to schema
                parsed_data = parse_ods_to_schema(api_data, dno['licence'], dno['company'])
                result['api_records'] = parsed_data
                
                # Save locally
                local_file = API_DATA_DIR / f"{dno['licence']}_duos_data.json"
                with open(local_file, 'w') as f:
                    json.dump(parsed_data, f, indent=2)
                result['local_api_file'] = local_file
                print(f"  💾 Saved: {local_file}")
                
                # Upload to Drive
                if drive_service and drive_links.get('subfolders', {}).get('API Data'):
                    drive_link = upload_to_drive(
                        drive_service, 
                        local_file, 
                        drive_links['subfolders']['API Data']
                    )
                    if drive_link:
                        result['drive_api_link'] = drive_link
                        print(f"  ☁️  Uploaded to Drive: {drive_link}")
                
                result['status'] = 'Complete'
        
        # Method 2: Search for existing statements in Drive
        if dno['source'] in ['WEB', 'ODS+WEB'] and drive_service:
            statements = search_drive_for_statements(drive_service, dno['company'], dno['licence'])
            if statements:
                result['statement_files'] = statements
                print(f"  📄 Found {len(statements)} charging statement files")
                if result['status'] == 'Pending':
                    result['status'] = 'Partial'
        
        # Add URL references
        result['statement_url'] = CHARGING_STATEMENT_URLS.get(dno['company'], '')
        
        all_results[mpan_id] = result
        time.sleep(1)  # Rate limiting
    
    # Generate markdown reference
    print(f"\n{'='*80}")
    print("GENERATING MARKDOWN REFERENCE")
    print(f"{'='*80}\n")
    
    md_content = generate_markdown_reference(all_results, drive_links)
    md_file = DATA_DIR / 'DUOS_DATA_REFERENCE.md'
    
    with open(md_file, 'w') as f:
        f.write(md_content)
    
    print(f"✅ Markdown reference created: {md_file}")
    
    # Upload markdown to Drive
    if drive_service and drive_links.get('root_folder_id'):
        md_link = upload_to_drive(drive_service, md_file, drive_links['root_folder_id'])
        if md_link:
            print(f"☁️  Uploaded to Drive: {md_link}")
    
    # Save summary JSON
    summary_file = DATA_DIR / f"download_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(summary_file, 'w') as f:
        json.dump({
            'timestamp': datetime.now().isoformat(),
            'dnos': all_results,
            'drive_links': drive_links
        }, f, indent=2, default=str)
    
    print(f"\n💾 Summary saved: {summary_file}")
    
    # Print final summary
    print(f"\n{'='*80}")
    print("DOWNLOAD SUMMARY")
    print(f"{'='*80}\n")
    
    complete = sum(1 for r in all_results.values() if r['status'] == 'Complete')
    partial = sum(1 for r in all_results.values() if r['status'] == 'Partial')
    pending = sum(1 for r in all_results.values() if r['status'] == 'Pending')
    
    print(f"✅ Complete: {complete}/14 DNOs")
    print(f"🟡 Partial: {partial}/14 DNOs")
    print(f"⏳ Pending: {pending}/14 DNOs")
    
    total_api_records = sum(len(r.get('api_records', [])) for r in all_results.values() if r.get('api_records'))
    print(f"\n📊 Total API records downloaded: {total_api_records}")
    
    print(f"\n📝 Reference document: {md_file}")
    if drive_links.get('root_folder_id'):
        print(f"☁️  Google Drive folder: https://drive.google.com/drive/folders/{drive_links['root_folder_id']}")
    
    print(f"\n{'='*80}")
    print("NEXT STEPS")
    print(f"{'='*80}\n")
    print("1. Review DUOS_DATA_REFERENCE.md for complete data inventory")
    print("2. Download missing charging statements from DNO websites")
    print("3. Parse Excel files using parse_duos_excel.py")
    print("4. Normalize all data to duos_rates_times.csv")
    print("5. Upload to BigQuery table: duos_rates")
    print("6. Add to dashboard (cell A14 - current DUoS band)")
    
    return all_results

if __name__ == '__main__':
    results = main()

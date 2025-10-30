#!/usr/bin/env python3
"""
Download DUoS Data for All 14 DNO License Areas (2016-Present)

This script systematically downloads Distribution Use of System (DUoS) charges
data for all 14 GB electricity distribution network license areas.

Methodology:
1. API-based (OpenDataSoft) for: UKPN (3), NPg (2), ENWL (1), SPEN (2)
2. File-based (Charging Statements) for: NGED (4), SSEN (2)

DNO License Areas:
- 10: UKPN-EPN (Eastern)
- 11: NGED-EM (East Midlands)
- 12: UKPN-LPN (London)
- 13: SP-Manweb (SPM)
- 14: NGED-WM (West Midlands)
- 15: NPg-NE (North East)
- 16: ENWL (North West)
- 17: SSE-SHEPD (North Scotland)
- 18: SP-Distribution (SPD)
- 19: UKPN-SPN (South Eastern)
- 20: SSE-SEPD (Southern)
- 21: NGED-SWales (South Wales)
- 22: NGED-SW (South West)
- 23: NPg-Y (Yorkshire)
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
import pickle
import io
from googleapiclient.http import MediaIoBaseDownload

# DNO Configuration
DNOS = {
    # UK Power Networks (OpenDataSoft)
    '10': {
        'mpan': 10, 'key': 'UKPN-EPN', 'name': 'UK Power Networks (Eastern)',
        'short': 'EPN', 'gsp_group': 'A', 'gsp_name': 'Eastern',
        'source': 'ODS', 'group': 'UKPN'
    },
    '12': {
        'mpan': 12, 'key': 'UKPN-LPN', 'name': 'UK Power Networks (London)',
        'short': 'LPN', 'gsp_group': 'C', 'gsp_name': 'London',
        'source': 'ODS', 'group': 'UKPN'
    },
    '19': {
        'mpan': 19, 'key': 'UKPN-SPN', 'name': 'UK Power Networks (South Eastern)',
        'short': 'SPN', 'gsp_group': 'J', 'gsp_name': 'South Eastern',
        'source': 'ODS', 'group': 'UKPN'
    },
    
    # Northern Powergrid (OpenDataSoft + Files)
    '15': {
        'mpan': 15, 'key': 'NPg-NE', 'name': 'Northern Powergrid (North East)',
        'short': 'NE', 'gsp_group': 'F', 'gsp_name': 'North East',
        'source': 'ODS+Files', 'group': 'NPg'
    },
    '23': {
        'mpan': 23, 'key': 'NPg-Y', 'name': 'Northern Powergrid (Yorkshire)',
        'short': 'Y', 'gsp_group': 'M', 'gsp_name': 'Yorkshire',
        'source': 'ODS+Files', 'group': 'NPg'
    },
    
    # Electricity North West (OpenDataSoft + Files)
    '16': {
        'mpan': 16, 'key': 'ENWL', 'name': 'Electricity North West',
        'short': 'ENWL', 'gsp_group': 'G', 'gsp_name': 'North West',
        'source': 'ODS+Files', 'group': 'ENWL'
    },
    
    # SP Energy Networks (OpenDataSoft + Files)
    '13': {
        'mpan': 13, 'key': 'SP-Manweb', 'name': 'SP Energy Networks (SPM)',
        'short': 'SPM', 'gsp_group': 'D', 'gsp_name': 'Merseyside & North Wales',
        'source': 'ODS+Files', 'group': 'SPEN'
    },
    '18': {
        'mpan': 18, 'key': 'SP-Distribution', 'name': 'SP Energy Networks (SPD)',
        'short': 'SPD', 'gsp_group': 'N', 'gsp_name': 'South Scotland',
        'source': 'ODS+Files', 'group': 'SPEN'
    },
    
    # National Grid Electricity Distribution (Files only)
    '11': {
        'mpan': 11, 'key': 'NGED-EM', 'name': 'National Grid Electricity Distribution – East Midlands',
        'short': 'EMID', 'gsp_group': 'B', 'gsp_name': 'East Midlands',
        'source': 'Files', 'group': 'NGED'
    },
    '14': {
        'mpan': 14, 'key': 'NGED-WM', 'name': 'National Grid Electricity Distribution – West Midlands',
        'short': 'WMID', 'gsp_group': 'E', 'gsp_name': 'West Midlands',
        'source': 'Files', 'group': 'NGED'
    },
    '21': {
        'mpan': 21, 'key': 'NGED-SWales', 'name': 'National Grid Electricity Distribution – South Wales',
        'short': 'SWALES', 'gsp_group': 'K', 'gsp_name': 'South Wales',
        'source': 'Files', 'group': 'NGED'
    },
    '22': {
        'mpan': 22, 'key': 'NGED-SW', 'name': 'National Grid Electricity Distribution – South West',
        'short': 'SWEST', 'gsp_group': 'L', 'gsp_name': 'South Western',
        'source': 'Files', 'group': 'NGED'
    },
    
    # SSEN Distribution (Files only)
    '17': {
        'mpan': 17, 'key': 'SSE-SHEPD', 'name': 'Scottish Hydro Electric Power Distribution',
        'short': 'SHEPD', 'gsp_group': 'P', 'gsp_name': 'North Scotland',
        'source': 'Files', 'group': 'SSEN'
    },
    '20': {
        'mpan': 20, 'key': 'SSE-SEPD', 'name': 'Southern Electric Power Distribution',
        'short': 'SEPD', 'gsp_group': 'H', 'gsp_name': 'Southern',
        'source': 'Files', 'group': 'SSEN'
    },
}

# OpenDataSoft API URLs
ODS_APIS = {
    'UKPN': 'https://ukpowernetworks.opendatasoft.com/api/records/1.0/search/',
    'NPg': 'https://northernpowergrid.opendatasoft.com/api/records/1.0/search/',
    'ENWL': 'https://electricitynorthwest.opendatasoft.com/api/records/1.0/search/',
    'SPEN': 'https://spenergynetworks.opendatasoft.com/api/records/1.0/search/',
}

# Known ODS dataset IDs (to be discovered/confirmed)
ODS_DATASETS = {
    'UKPN': 'ukpn-distribution-use-of-system-charges-annex-1',
    # Others to be discovered
}

# Google Drive search patterns for charging statements
DRIVE_SEARCH_PATTERNS = {
    'NGED': 'NGED "Schedule of Charges" OR "Charging Statement" (EMID OR WMID OR SWALES OR SWEST)',
    'SSEN': 'SSEN "Schedule of Charges" OR "Charging Statement" (SHEPD OR SEPD)',
    'NPg': 'Northern Powergrid "Schedule of Charges" OR "Charging Statement"',
    'ENWL': 'ENWL "Schedule of Charges" OR "Charging Statement"',
    'SPEN': 'SP Energy Networks "Schedule of Charges" OR "Charging Statement"',
}

# Output directories
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / 'data' / 'duos'
DATA_DIR.mkdir(parents=True, exist_ok=True)

# Subdirectories by source
ODS_DIR = DATA_DIR / 'ods_api'
FILES_DIR = DATA_DIR / 'charging_statements'
ODS_DIR.mkdir(exist_ok=True)
FILES_DIR.mkdir(exist_ok=True)

# Years to download
YEARS = [f"{y}/{y+1-2000:02d}" for y in range(2016, 2026)]  # 2016/17 to 2025/26

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
            print("⚠️  OAuth token not found or invalid. Run oauth_with_sheets.py first.")
            return None
    
    return build('drive', 'v3', credentials=creds)

def fetch_ods_dataset(group, dataset_id, license_area=None):
    """Fetch data from OpenDataSoft API"""
    url = ODS_APIS.get(group)
    if not url:
        print(f"  ⚠️  No ODS API URL for {group}")
        return None
    
    params = {
        'dataset': dataset_id,
        'rows': 10000,
    }
    
    if license_area:
        params['refine.licence'] = license_area
    
    try:
        print(f"  📡 Fetching from ODS API: {dataset_id}")
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        records = data.get('records', [])
        print(f"  ✅ Retrieved {len(records)} records")
        return records
    
    except Exception as e:
        print(f"  ❌ ODS API error: {e}")
        return None

def search_drive_for_statements(drive_service, search_pattern, dno_group):
    """Search Google Drive for charging statement files"""
    if not drive_service:
        return []
    
    try:
        print(f"  🔍 Searching Drive: {search_pattern}")
        results = drive_service.files().list(
            q=f"name contains 'Schedule of Charges' or name contains 'Charging Statement'",
            spaces='drive',
            fields='files(id, name, mimeType, createdTime, size)',
            pageSize=100
        ).execute()
        
        files = results.get('files', [])
        
        # Filter by DNO group
        filtered = []
        for f in files:
            name_lower = f['name'].lower()
            if dno_group == 'NGED' and any(x in name_lower for x in ['emid', 'wmid', 'swales', 'swest', 'national grid electricity distribution']):
                filtered.append(f)
            elif dno_group == 'SSEN' and any(x in name_lower for x in ['shepd', 'sepd', 'ssen', 'scottish hydro', 'southern electric']):
                filtered.append(f)
            elif dno_group == 'NPg' and any(x in name_lower for x in ['northern powergrid', 'npg', 'nedl', 'yedl']):
                filtered.append(f)
            elif dno_group == 'ENWL' and any(x in name_lower for x in ['enwl', 'electricity north west']):
                filtered.append(f)
            elif dno_group == 'SPEN' and any(x in name_lower for x in ['spen', 'sp energy', 'manweb', 'spd', 'spm']):
                filtered.append(f)
        
        print(f"  ✅ Found {len(filtered)} relevant files")
        return filtered
    
    except Exception as e:
        print(f"  ❌ Drive search error: {e}")
        return []

def download_drive_file(drive_service, file_id, file_name, output_dir):
    """Download file from Google Drive"""
    try:
        request = drive_service.files().get_media(fileId=file_id)
        
        output_path = output_dir / file_name
        fh = io.FileIO(str(output_path), 'wb')
        downloader = MediaIoBaseDownload(fh, request)
        
        done = False
        while not done:
            status, done = downloader.next_chunk()
            if status:
                print(f"  📥 Download progress: {int(status.progress() * 100)}%", end='\r')
        
        print(f"  ✅ Downloaded: {file_name}")
        return output_path
    
    except Exception as e:
        print(f"  ❌ Download error: {e}")
        return None

def download_dno_data(mpan_id):
    """Download DUoS data for a specific DNO"""
    dno = DNOS[str(mpan_id)]
    
    print(f"\n{'='*80}")
    print(f"DNO: {dno['name']}")
    print(f"License: {dno['short']} (MPAN {mpan_id})")
    print(f"GSP Group: {dno['gsp_group']} ({dno['gsp_name']})")
    print(f"Source: {dno['source']}")
    print(f"{'='*80}\n")
    
    # Create output directory for this DNO
    dno_dir = FILES_DIR / dno['short']
    dno_dir.mkdir(exist_ok=True)
    
    results = {
        'dno': dno,
        'ods_data': None,
        'files_downloaded': []
    }
    
    # Method 1: OpenDataSoft API (if available)
    if dno['source'] in ['ODS', 'ODS+Files']:
        dataset_id = ODS_DATASETS.get(dno['group'])
        if dataset_id:
            ods_data = fetch_ods_dataset(dno['group'], dataset_id, dno['short'])
            if ods_data:
                # Save ODS data to JSON
                ods_file = ODS_DIR / f"{dno['short']}_ods_data.json"
                with open(ods_file, 'w') as f:
                    json.dump(ods_data, f, indent=2)
                print(f"  💾 Saved ODS data: {ods_file}")
                results['ods_data'] = ods_file
        else:
            print(f"  ⚠️  ODS dataset ID not known for {dno['group']}")
            print(f"      Manual discovery required at: {ODS_APIS.get(dno['group'])}")
    
    # Method 2: Charging Statement Files (if needed)
    if dno['source'] in ['Files', 'ODS+Files']:
        drive_service = get_drive_service()
        if drive_service:
            search_pattern = DRIVE_SEARCH_PATTERNS.get(dno['group'])
            if search_pattern:
                files = search_drive_for_statements(drive_service, search_pattern, dno['group'])
                
                # Download first 10 files (or all if < 10)
                for file_info in files[:10]:
                    downloaded = download_drive_file(
                        drive_service,
                        file_info['id'],
                        file_info['name'],
                        dno_dir
                    )
                    if downloaded:
                        results['files_downloaded'].append({
                            'name': file_info['name'],
                            'path': str(downloaded),
                            'size': file_info.get('size', 'Unknown')
                        })
                    time.sleep(1)  # Rate limiting
        else:
            print(f"  ⚠️  Drive service not available. Cannot download files.")
    
    return results

def download_all_dnos():
    """Download DUoS data for all 14 DNOs"""
    print("="*80)
    print("DUoS DATA DOWNLOAD - ALL 14 DNO LICENSE AREAS")
    print("="*80)
    print(f"\nOutput directories:")
    print(f"  ODS API data: {ODS_DIR}")
    print(f"  Charging statements: {FILES_DIR}")
    print(f"\nYears: {', '.join(YEARS)}")
    print(f"\nStarting download at: {datetime.now().isoformat()}")
    
    all_results = {}
    
    # Download for each DNO
    for mpan_id in sorted(DNOS.keys()):
        try:
            results = download_dno_data(mpan_id)
            all_results[mpan_id] = results
            time.sleep(2)  # Rate limiting between DNOs
        except Exception as e:
            print(f"\n❌ Error downloading DNO {mpan_id}: {e}")
            all_results[mpan_id] = {'error': str(e)}
    
    # Save summary
    summary_file = DATA_DIR / f'download_summary_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
    with open(summary_file, 'w') as f:
        json.dump(all_results, f, indent=2, default=str)
    
    # Print summary
    print("\n" + "="*80)
    print("DOWNLOAD SUMMARY")
    print("="*80)
    
    total_ods = sum(1 for r in all_results.values() if r.get('ods_data'))
    total_files = sum(len(r.get('files_downloaded', [])) for r in all_results.values())
    
    print(f"\n✅ DNOs processed: {len(all_results)}/14")
    print(f"📡 ODS datasets retrieved: {total_ods}")
    print(f"📥 Files downloaded: {total_files}")
    print(f"\n💾 Summary saved: {summary_file}")
    
    print("\n" + "="*80)
    print("DETAILED RESULTS BY DNO")
    print("="*80)
    
    for mpan_id, results in sorted(all_results.items()):
        if 'error' in results:
            print(f"\n❌ {mpan_id}: {results['error']}")
            continue
        
        dno = results['dno']
        print(f"\n{dno['short']} ({dno['name']})")
        
        if results.get('ods_data'):
            print(f"  ✅ ODS data: {results['ods_data']}")
        
        if results.get('files_downloaded'):
            print(f"  ✅ Files downloaded: {len(results['files_downloaded'])}")
            for f in results['files_downloaded'][:3]:  # Show first 3
                print(f"     - {f['name']}")
            if len(results['files_downloaded']) > 3:
                print(f"     ... and {len(results['files_downloaded'])-3} more")
    
    print("\n" + "="*80)
    print("NEXT STEPS")
    print("="*80)
    print("\n1. Parse downloaded files using parse_duos_files.py")
    print("2. Normalize data to common schema")
    print("3. Create duos_rates_times.csv master file")
    print("4. Upload to BigQuery table: duos_rates")
    print("5. Add to dashboard display")
    
    return all_results

if __name__ == '__main__':
    results = download_all_dnos()

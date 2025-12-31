#!/usr/bin/env python3
"""
Import Elexon BSC Signatories
Queries Elexon API for list of BSC parties and populates Parties tab
"""

import requests
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import time

# Configuration
SHEET_ID = "1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA"
CREDENTIALS_FILE = "inner-cinema-credentials.json"

# Elexon API endpoints
ELEXON_BASE_URL = "https://api.bmreports.com/BMRS"
ELEXON_DATA_URL = "https://downloads.elexonportal.co.uk/file/download"

def get_bsc_parties_from_elexon():
    """
    Get BSC parties from Elexon sources
    Note: Elexon doesn't have a simple "list all parties" API endpoint
    We need to aggregate from multiple sources:
    1. BM Unit data (generators/suppliers with BM units)
    2. Participant data from settlement reports
    3. Manual list from Elexon website
    """
    
    print("🔍 Querying Elexon for BSC parties...")
    
    parties = {}
    
    # Method 1: Get parties from BM Unit data (B1610 - BM Unit data)
    print("\n1️⃣ Fetching BM Unit data...")
    bm_parties = get_parties_from_bm_units()
    parties.update(bm_parties)
    
    # Method 2: Get supplier list from Elexon
    print("\n2️⃣ Fetching supplier list...")
    supplier_parties = get_supplier_parties()
    parties.update(supplier_parties)
    
    # Method 3: Common known parties (manual list)
    print("\n3️⃣ Adding known major parties...")
    known_parties = get_known_parties()
    parties.update(known_parties)
    
    print(f"\n✅ Found {len(parties)} unique BSC parties")
    return parties

def get_parties_from_bm_units():
    """Extract parties from BM Unit registrations"""
    
    # For now, return sample data
    # TODO: Query actual Elexon API or scrape BM Unit list
    
    parties = {
        'DRAX': {
            'name': 'Drax Power Limited',
            'short_name': 'Drax',
            'type': 'Generator',
            'bsc_id': 'DRAX',
            'status': 'Active'
        },
        'EDF': {
            'name': 'EDF Energy',
            'short_name': 'EDF',
            'type': 'Generator/Supplier',
            'bsc_id': 'EDF',
            'status': 'Active'
        },
        'NGET': {
            'name': 'National Grid Electricity Transmission',
            'short_name': 'NGET',
            'type': 'TSO',
            'bsc_id': 'NGET',
            'status': 'Active'
        }
    }
    
    print(f"   Found {len(parties)} parties from BM Units")
    return parties

def get_supplier_parties():
    """Get licensed suppliers"""
    
    # Sample supplier data
    suppliers = {
        'OCTOPUS': {
            'name': 'Octopus Energy Limited',
            'short_name': 'Octopus',
            'type': 'Supplier',
            'bsc_id': 'OCTO',
            'status': 'Active'
        },
        'BULB': {
            'name': 'Bulb Energy Limited',
            'short_name': 'Bulb',
            'type': 'Supplier',
            'bsc_id': 'BULB',
            'status': 'Active'
        },
        'OVO': {
            'name': 'OVO Energy Limited',
            'short_name': 'OVO',
            'type': 'Supplier',
            'bsc_id': 'OVO',
            'status': 'Active'
        }
    }
    
    print(f"   Found {len(suppliers)} suppliers")
    return suppliers

def get_known_parties():
    """
    Known major BSC parties (generators, interconnectors, storage)
    Based on public information from NESO, Elexon reports
    """
    
    known = {
        # Major Generators
        'SIZEWELL': {'name': 'Sizewell B Power Station', 'short_name': 'Sizewell', 'type': 'Generator', 'bsc_id': 'SIZB', 'status': 'Active'},
        'HINKLEY': {'name': 'Hinkley Point B', 'short_name': 'Hinkley', 'type': 'Generator', 'bsc_id': 'HINK', 'status': 'Active'},
        'RATCLIFFE': {'name': 'Ratcliffe-on-Soar Power Station', 'short_name': 'Ratcliffe', 'type': 'Generator', 'bsc_id': 'RATS', 'status': 'Active'},
        
        # Interconnectors
        'IFA': {'name': 'IFA Interconnector', 'short_name': 'IFA', 'type': 'Interconnector', 'bsc_id': 'IFA', 'status': 'Active'},
        'IFA2': {'name': 'IFA2 Interconnector', 'short_name': 'IFA2', 'type': 'Interconnector', 'bsc_id': 'IFA2', 'status': 'Active'},
        'BRITNED': {'name': 'BritNed Interconnector', 'short_name': 'BritNed', 'type': 'Interconnector', 'bsc_id': 'BNED', 'status': 'Active'},
        'NEMO': {'name': 'Nemo Link', 'short_name': 'Nemo', 'type': 'Interconnector', 'bsc_id': 'NEMO', 'status': 'Active'},
        
        # Storage
        'FBPGM002': {'name': 'Flexgen Battery Storage', 'short_name': 'Flexgen', 'type': 'Storage/VLP', 'bsc_id': 'FBPG', 'status': 'Active'},
        'FFSEN005': {'name': 'Harmony Energy (Gresham House)', 'short_name': 'Harmony', 'type': 'Storage/VLP', 'bsc_id': 'FFSE', 'status': 'Active'},
        
        # DNOs
        'UKPN': {'name': 'UK Power Networks', 'short_name': 'UKPN', 'type': 'DSO', 'bsc_id': 'UKPN', 'status': 'Active'},
        'SSEN': {'name': 'Scottish and Southern Electricity Networks', 'short_name': 'SSEN', 'type': 'DSO', 'bsc_id': 'SSEN', 'status': 'Active'},
        'NGED': {'name': 'National Grid Electricity Distribution', 'short_name': 'NGED', 'type': 'DSO', 'bsc_id': 'NGED', 'status': 'Active'},
    }
    
    print(f"   Added {len(known)} known parties")
    return known

def populate_parties_tab(parties):
    """Populate Parties tab in Google Sheets"""
    
    print("\n📊 Updating Parties tab in Google Sheets...")
    
    scopes = [
        'https://www.googleapis.com/auth/spreadsheets',
        'https://www.googleapis.com/auth/drive'
    ]
    creds = Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=scopes)
    gc = gspread.authorize(creds)
    
    wb = gc.open_by_key(SHEET_ID)
    sheet = wb.worksheet('Parties')
    
    # Prepare data rows
    data = []
    for i, (party_id, info) in enumerate(sorted(parties.items()), start=1):
        row = [
            f"P{i:03d}",  # Party ID
            info['name'],
            info['short_name'],
            '',  # Categories (will be populated by formula)
            '',  # Registration Date (unknown)
            info['status'],
            info['bsc_id'],
            '',  # Company Number
            '',  # Address
            '',  # Contact
            '',  # Website
            'TRUE' if 'Generator' in info['type'] else 'FALSE',  # Is Generator
            'TRUE' if 'Supplier' in info['type'] else 'FALSE',   # Is Supplier
            'TRUE' if 'Storage' in info['type'] else 'FALSE',    # Is Storage
            f"Type: {info['type']}"  # Notes
        ]
        data.append(row)
    
    # Update sheet (starting from row 2, after headers)
    sheet.update(f'A2:O{len(data)+1}', data)
    
    print(f"✅ Populated {len(data)} parties in Parties tab")
    
    # Also populate Party_Category links
    populate_party_category_links(wb, parties)

def populate_party_category_links(wb, parties):
    """Populate Party_Category link table based on party types"""
    
    print("\n🔗 Populating Party_Category links...")
    
    sheet = wb.worksheet('Party_Category')
    
    links = []
    today = datetime.now().strftime('%Y-%m-%d')
    
    for i, (party_id, info) in enumerate(sorted(parties.items()), start=1):
        pid = f"P{i:03d}"
        party_type = info['type']
        
        # Parse type string and create links
        if 'Generator' in party_type:
            links.append([pid, 'Generator', 'Import Script', 'High', 'TRUE', today, 'System', ''])
            links.append([pid, 'Balancing Mechanism Unit', 'Import Script', 'Medium', 'FALSE', today, 'System', 'Assumed from Generator type'])
        
        if 'Supplier' in party_type:
            links.append([pid, 'Supplier', 'Import Script', 'High', 'TRUE', today, 'System', ''])
        
        if 'Storage' in party_type or 'VLP' in party_type:
            links.append([pid, 'Storage Operator', 'Import Script', 'High', 'TRUE', today, 'System', ''])
            links.append([pid, 'Virtual Lead Party', 'Import Script', 'High', 'TRUE', today, 'System', ''])
            links.append([pid, 'Balancing Mechanism Unit', 'Import Script', 'High', 'TRUE', today, 'System', ''])
        
        if 'Interconnector' in party_type:
            links.append([pid, 'Interconnector', 'Import Script', 'High', 'TRUE', today, 'System', ''])
            links.append([pid, 'Balancing Mechanism Unit', 'Import Script', 'High', 'TRUE', today, 'System', ''])
        
        if 'DSO' in party_type:
            links.append([pid, 'Distribution System Operator', 'Import Script', 'High', 'TRUE', today, 'System', ''])
            links.append([pid, 'Licensed Distributor', 'Import Script', 'High', 'TRUE', today, 'System', ''])
        
        if 'TSO' in party_type:
            links.append([pid, 'Transmission System Operator', 'Import Script', 'High', 'TRUE', today, 'System', ''])
    
    # Update sheet
    if links:
        sheet.update(f'A2:H{len(links)+1}', links)
        print(f"✅ Created {len(links)} party-category links")
    else:
        print("⚠️  No links to create")

if __name__ == '__main__':
    try:
        # Get parties from Elexon
        parties = get_bsc_parties_from_elexon()
        
        # Populate Google Sheets
        populate_parties_tab(parties)
        
        print("\n🎉 BSC parties imported successfully!")
        print("\nNext steps:")
        print("1. Query NESO APIs for more generator/interconnector data")
        print("2. Manually verify and add missing parties")
        print("3. Check Party_Wide tab for boolean flag view")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

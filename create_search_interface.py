#!/usr/bin/env python3
"""
Create Search Interface in Google Sheets
Builds professional search UI with dropdowns, results table, and party details panel
"""

import gspread
from google.oauth2.service_account import Credentials
from google.cloud import bigquery
from typing import List, Dict

# Configuration
SHEET_ID = "1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA"
CREDS_FILE = "inner-cinema-credentials.json"
PROJECT_ID = "inner-cinema-476211-u9"
DATASET = "uk_energy_prod"

# CUSC/BSC Role Categories (CUSC Section 1 definitions)
CUSC_ROLES = [
    "Power Station (Directly Connected)",
    "Large Power Station",
    "Non-Embedded Customer",
    "Distribution System (DNO/IDNO)",
    "Supplier",
    "Embedded Power Station",
    "Embedded Exemptable Large Power Station",
    "Small Power Station Trading Party",
    "Virtual Lead Party (VLP)",
    "Virtual Trading Party (VTP)",
    "Interconnector User",
]

# ============================================================================
# DATA FETCHERS
# ============================================================================

def fetch_bmu_list() -> List[str]:
    """Fetch all BMU IDs from BigQuery"""
    client = bigquery.Client(project=PROJECT_ID, location="US")

    query = f"""
    SELECT DISTINCT elexonbmunit
    FROM `{PROJECT_ID}.{DATASET}.bmu_registration_data`
    WHERE elexonbmunit IS NOT NULL
    ORDER BY elexonbmunit
    """

    df = client.query(query).to_dataframe()
    return df['elexonbmunit'].tolist()

def fetch_fuel_types() -> List[str]:
    """Fetch unique fuel types"""
    client = bigquery.Client(project=PROJECT_ID, location="US")

    query = f"""
    SELECT DISTINCT fueltype
    FROM `{PROJECT_ID}.{DATASET}.bmu_registration_data`
    WHERE fueltype IS NOT NULL
    ORDER BY fueltype
    """

    df = client.query(query).to_dataframe()
    return df['fueltype'].tolist()

def fetch_organizations() -> List[str]:
    """Fetch unique organization/company names from BigQuery"""
    client = bigquery.Client(project=PROJECT_ID, location="US")

    query = f"""
    SELECT DISTINCT leadpartyname as organization
    FROM `{PROJECT_ID}.{DATASET}.bmu_registration_data`
    WHERE leadpartyname IS NOT NULL
    UNION DISTINCT
    SELECT DISTINCT party_name as organization
    FROM `{PROJECT_ID}.{DATASET}.dim_party`
    WHERE party_name IS NOT NULL
    ORDER BY organization
    """

    df = client.query(query).to_dataframe()
    return df['organization'].tolist()

def fetch_connection_sites() -> List[str]:
    """Fetch TEC connection sites (placeholder for now)"""
    # TODO: Query NESO TEC dataset when available
    return [
        "Beauly", "Bicker Fen", "Bramford", "Braintree", "Burwell",
        "Canterbury", "Chesterfield", "Deeside", "Drax", "Eaton Socon",
        "Ferrybridge", "Grain", "Hams Hall", "Harker", "Indian Queens",
        "Keith", "Killingholme", "Norwich Main", "Peterborough",
        "Saltend", "Spalding", "Stallingborough", "Tilbury", "Walpole"
    ]

def format_dropdown_list(items: List[str], include_none_all: bool = True) -> List[str]:
    """Format dropdown list with None, All at top, rest sorted"""
    # Remove None/All if present
    filtered = [x for x in items if x not in ["None", "All", "", None]]

    # Sort alphabetically (case-insensitive)
    sorted_items = sorted(set(filtered), key=lambda x: str(x).lower())

    if include_none_all:
        return ["None", "All"] + sorted_items
    else:
        return sorted_items

# ============================================================================
# SHEET CREATOR
# ============================================================================

class SearchInterfaceCreator:
    """Create comprehensive search interface in Google Sheets"""

    def __init__(self, sheet_id: str, creds_file: str):
        self.sheet_id = sheet_id
        credentials = Credentials.from_service_account_file(
            creds_file,
            scopes=['https://www.googleapis.com/auth/spreadsheets']
        )
        self.gc = gspread.authorize(credentials)
        self.wb = self.gc.open_by_key(sheet_id)

    def create_search_sheet(self):
        """Create or update Search sheet"""
        print("📄 Creating Search interface...\n")

        # Get or create sheet
        try:
            sheet = self.wb.worksheet('Search')
            print("   ✅ Found existing 'Search' sheet")
        except:
            sheet = self.wb.add_worksheet(title='Search', rows=100, cols=20)
            print("   ✅ Created new 'Search' sheet")

        # Clear existing content
        sheet.clear()

        # Build interface
        self._create_header(sheet)
        self._create_search_criteria(sheet)
        self._create_results_section(sheet)
        self._create_party_details_panel(sheet)
        self._apply_formatting(sheet)

        print("\n✅ Search interface created successfully!")

    def _create_header(self, sheet):
        """Create title header"""
        print("1️⃣ Creating header...")

        header_data = [
            ['🔍 ADVANCED PARTY & ASSET SEARCH', '', '', '', '', '', '', '', '', ''],
            ['', '', '', '', '', '', '', '', '', '']
        ]

        sheet.update(values=header_data, range_name='A1:J2')

        # Merge and format header
        sheet.merge_cells('A1:J1')

    def _create_search_criteria(self, sheet):
        """Create search input fields"""
        print("2️⃣ Creating search criteria...")

        criteria_data = [
            ['📝 SEARCH CRITERIA', '', '', '', '', '', '', '', '', ''],
            ['Date Range:', '', 'to', '', '', '', '', '', '', ''],
            ['Party/Name Search:', '', '', 'Search Mode:', 'OR'],
            ['Record Type:', 'None'],
            ['CUSC/BSC Role (comma-separated):', 'None'],
            ['Fuel/Technology Type (comma-separated):', 'None'],
            ['BM Unit ID:', 'None'],
            ['Organization:', 'None'],
            ['Capacity Range (MW):', '', 'to', ''],
            ['TEC Project Search:', ''],
            ['Connection Site:', 'None'],
            ['Project Status:', 'None'],
            ['', '', '', '', '', '', '', '', '', ''],
            ['', '', '', '', '', '', '', '', '', ''],
            ['', '', '', '', '', '', '', '', '', '']
        ]

        sheet.update(values=criteria_data, range_name='A3:J17')

        # Add placeholder dates
        sheet.update(values=[['01/01/2025']], range_name='B4')
        sheet.update(values=[['31/12/2025']], range_name='D4')

        # Add search buttons in row 16 (via Apps Script)
        sheet.update(values=[['🔍 Search', '🧹 Clear', 'ℹ️ Help']], range_name='A16:C16')

    def _create_dropdowns(self, sheet):
        """Create dropdown validations"""
        print("3️⃣ Creating dropdowns...")

        # Fetch dropdown data
        print("   📥 Fetching BMU IDs from BigQuery...")
        bmu_list = format_dropdown_list(fetch_bmu_list())

        print("   📥 Fetching fuel types from BigQuery...")
        fuel_types = format_dropdown_list(fetch_fuel_types())

        print("   📥 Fetching organizations from BigQuery...")
        organizations = format_dropdown_list(fetch_organizations())

        print("   📥 Fetching connection sites...")
        connection_sites = format_dropdown_list(fetch_connection_sites())

        # Create DropdownData sheet for options
        try:
            dropdown_sheet = self.wb.worksheet('SearchDropdowns')
        except:
            dropdown_sheet = self.wb.add_worksheet(title='SearchDropdowns', rows=500, cols=10)

        dropdown_sheet.clear()

        # Write dropdown options
        record_types = format_dropdown_list([
            'BSC Party', 'BM Unit', 'NESO Project', 'TEC Project',
            'Generator', 'Supplier', 'Interconnector'
        ])

        cusc_roles = format_dropdown_list(CUSC_ROLES)

        fuel_tech_types = format_dropdown_list([
            'Battery Storage', 'Biomass', 'CCGT (Gas)', 'Coal',
            'Demand Side Response', 'Hydro', 'Interconnector',
            'Nuclear', 'OCGT (Gas)', 'Offshore Wind', 'Onshore Wind',
            'Pumped Storage', 'Solar', 'Wave/Tidal'
        ])

        project_status = format_dropdown_list([
            'Accepted', 'Active', 'Completed', 'Connection Offer Made',
            'Contracted', 'Energised', 'Modification Accepted',
            'Scoping Ongoing', 'Withdrawn'
        ])

        # Write to columns
        dropdown_sheet.update(values=[[x] for x in record_types], range_name='A1:A50')
        dropdown_sheet.update(values=[[x] for x in cusc_roles], range_name='B1:B50')
        dropdown_sheet.update(values=[[x] for x in fuel_tech_types], range_name='C1:C50')
        dropdown_sheet.update(values=[[x] for x in bmu_list[:400]], range_name='D1:D400')
        dropdown_sheet.update(values=[[x] for x in organizations[:400]], range_name='E1:E400')
        dropdown_sheet.update(values=[[x] for x in connection_sites], range_name='F1:F50')
        dropdown_sheet.update(values=[[x] for x in project_status], range_name='G1:G50')

        print(f"   ✅ Loaded {len(bmu_list)} BMU IDs")
        print(f"   ✅ Loaded {len(organizations)} organizations")
        print(f"   ✅ Loaded {len(fuel_types)} fuel types")
        print(f"   ✅ Loaded {len(connection_sites)} connection sites")

        # Apply validations
        sheet_id = sheet.id

        requests = [
            # B6: Record Type
            self._create_validation(sheet_id, 5, 6, f'SearchDropdowns!A1:A{len(record_types)}'),
            # B9: BM Unit ID
            self._create_validation(sheet_id, 8, 9, f'SearchDropdowns!D1:D{min(400, len(bmu_list))}'),
            # B10: Organization
            self._create_validation(sheet_id, 9, 10, f'SearchDropdowns!E1:E{min(400, len(organizations))}'),
            # B13: Connection Site
            self._create_validation(sheet_id, 12, 13, f'SearchDropdowns!F1:F{len(connection_sites)}'),
            # B14: Project Status
            self._create_validation(sheet_id, 13, 14, f'SearchDropdowns!G1:G{len(project_status)}'),
        ]

        self.wb.batch_update({'requests': requests})
        print("   ✅ Applied dropdown validations")

    def _create_validation(self, sheet_id: int, start_row: int, end_row: int, range_name: str) -> Dict:
        """Create data validation request"""
        return {
            'setDataValidation': {
                'range': {
                    'sheetId': sheet_id,
                    'startRowIndex': start_row,
                    'endRowIndex': end_row,
                    'startColumnIndex': 1,  # Column B
                    'endColumnIndex': 2
                },
                'rule': {
                    'condition': {
                        'type': 'ONE_OF_RANGE',
                        'values': [{'userEnteredValue': f'={range_name}'}]
                    },
                    'showCustomUi': True,
                    'strict': False
                }
            }
        }

    def _create_results_section(self, sheet):
        """Create results table"""
        print("4️⃣ Creating results section...")

        results_data = [
            ['', '', '', '', '', '', '', '', '', '', ''],
            ['📊 SEARCH RESULTS', '', 'Last Search:', '', '', 'Results:', '0'],
            ['', '', '', '', '', '', '', '', '', '', ''],
            [
                'Record Type', 'Identifier (ID)', 'Name', 'Role',
                'Organization', 'Extra Info', 'Capacity (MW)', 'Fuel Type',
                'Status', 'Dataset Source', 'Match Score'
            ]
        ]

        sheet.update(values=results_data, range_name='A18:K21')

        # Merge header cells
        sheet.merge_cells('A19:B19')

    def _create_party_details_panel(self, sheet):
        """Create party details panel"""
        print("5️⃣ Creating party details panel...")

        details_data = [
            ['📋 PARTY DETAILS'],
            [''],
            ['Selected:', '[Click a result row]'],
            [''],
            ['Party ID:', ''],
            ['Record Type:', ''],
            ['CUSC/BSC Role:', ''],
            ['Organization:', ''],
            [''],
            ['📊 ROLES & QUALIFICATIONS'],
            ['BSC Roles:', ''],
            ['VLP Status:', ''],
            ['VTP Status:', ''],
            ['Qualification:', ''],
            [''],
            ['🏭 ASSETS OWNED'],
            ['BM Units:', ''],
            ['Total Capacity:', ''],
            ['Fuel Types:', ''],
            [''],
            ['📅 LAST UPDATED'],
            ['Date:', '']
        ]

        sheet.update(values=details_data, range_name='L6:M27')

        # Merge header
        sheet.merge_cells('L6:M6')

    def _apply_formatting(self, sheet):
        """Apply professional formatting"""
        print("6️⃣ Applying formatting...")

        sheet_id = sheet.id

        requests = [
            # Title header (Row 1)
            {
                'repeatCell': {
                    'range': {
                        'sheetId': sheet_id,
                        'startRowIndex': 0,
                        'endRowIndex': 1
                    },
                    'cell': {
                        'userEnteredFormat': {
                            'backgroundColor': {'red': 0.2, 'green': 0.4, 'blue': 0.6},
                            'textFormat': {
                                'foregroundColor': {'red': 1, 'green': 1, 'blue': 1},
                                'bold': True,
                                'fontSize': 16
                            },
                            'horizontalAlignment': 'CENTER',
                            'verticalAlignment': 'MIDDLE'
                        }
                    },
                    'fields': 'userEnteredFormat'
                }
            },
            # Section headers (Rows 3, 17)
            {
                'repeatCell': {
                    'range': {
                        'sheetId': sheet_id,
                        'startRowIndex': 2,
                        'endRowIndex': 3
                    },
                    'cell': {
                        'userEnteredFormat': {
                            'backgroundColor': {'red': 1, 'green': 0.6, 'blue': 0},
                            'textFormat': {'bold': True, 'fontSize': 12},
                        }
                    },
                    'fields': 'userEnteredFormat'
                }
            },
            # Results header row (Row 21)
            {
                'repeatCell': {
                    'range': {
                        'sheetId': sheet_id,
                        'startRowIndex': 20,
                        'endRowIndex': 21
                    },
                    'cell': {
                        'userEnteredFormat': {
                            'backgroundColor': {'red': 0.85, 'green': 0.85, 'blue': 0.85},
                            'textFormat': {'bold': True},
                            'horizontalAlignment': 'CENTER'
                        }
                    },
                    'fields': 'userEnteredFormat'
                }
            },
            # Party details header (L6)
            {
                'repeatCell': {
                    'range': {
                        'sheetId': sheet_id,
                        'startRowIndex': 5,
                        'endRowIndex': 6,
                        'startColumnIndex': 11,
                        'endColumnIndex': 13
                    },
                    'cell': {
                        'userEnteredFormat': {
                            'backgroundColor': {'red': 0.8, 'green': 0.9, 'blue': 1},
                            'textFormat': {'bold': True, 'fontSize': 12},
                        }
                    },
                    'fields': 'userEnteredFormat'
                }
            },
            # Set column widths
            {'updateDimensionProperties': {
                'range': {'sheetId': sheet_id, 'dimension': 'COLUMNS', 'startIndex': 0, 'endIndex': 1},
                'properties': {'pixelSize': 130},
                'fields': 'pixelSize'
            }},
            {'updateDimensionProperties': {
                'range': {'sheetId': sheet_id, 'dimension': 'COLUMNS', 'startIndex': 1, 'endIndex': 2},
                'properties': {'pixelSize': 150},
                'fields': 'pixelSize'
            }},
            {'updateDimensionProperties': {
                'range': {'sheetId': sheet_id, 'dimension': 'COLUMNS', 'startIndex': 2, 'endIndex': 3},
                'properties': {'pixelSize': 200},
                'fields': 'pixelSize'
            }},
            # Freeze rows 1-21
            {
                'updateSheetProperties': {
                    'properties': {
                        'sheetId': sheet_id,
                        'gridProperties': {'frozenRowCount': 21}
                    },
                    'fields': 'gridProperties.frozenRowCount'
                }
            }
        ]

        self.wb.batch_update({'requests': requests})
        print("   ✅ Applied professional formatting")

# ============================================================================
# MAIN
# ============================================================================

def main():
    """Create search interface"""
    print("=" * 80)
    print("🔍 CREATING SEARCH INTERFACE")
    print("=" * 80)
    print()

    creator = SearchInterfaceCreator(SHEET_ID, CREDS_FILE)
    creator.create_search_sheet()
    creator._create_dropdowns(creator.wb.worksheet('Search'))

    print()
    print("=" * 80)
    print("✅ SEARCH INTERFACE READY!")
    print("=" * 80)
    print()
    print(f"📄 Sheet: https://docs.google.com/spreadsheets/d/{SHEET_ID}")
    print("📋 Next steps:")
    print("   1. Test dropdowns in Search sheet")
    print("   2. Install Apps Script buttons (search_interface.gs)")
    print("   3. Run advanced_search_tool_enhanced.py to populate results")
    print()

if __name__ == "__main__":
    main()

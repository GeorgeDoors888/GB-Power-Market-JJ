#!/usr/bin/env python3
"""
Comprehensive DATA sheet update - includes 873 .md files + enhanced documentation
"""

import gspread
from google.oauth2.service_account import Credentials
import os
import glob

SPREADSHEET_ID = "1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA"

# Initialize gspread
scopes = ['https://www.googleapis.com/auth/spreadsheets']
creds = Credentials.from_service_account_file('inner-cinema-credentials.json', scopes=scopes)
gc = gspread.authorize(creds)
spreadsheet = gc.open_by_key(SPREADSHEET_ID)

# Get existing sheet
try:
    worksheet = spreadsheet.worksheet('DATA')
    print("📝 Found existing DATA sheet, updating...")
except gspread.WorksheetNotFound:
    print("❌ DATA sheet not found! Run create_data_sheet.py first")
    exit(1)

# ============================================================================
# FIND ALL MARKDOWN FILES
# ============================================================================
print("🔍 Scanning workspace for markdown files...")
md_files = sorted(glob.glob('/home/george/GB-Power-Market-JJ/**/*.md', recursive=True))
print(f"✅ Found {len(md_files)} markdown files")

# Categorize markdown files
doc_categories = {
    'Dashboard & Deployment': [],
    'Data Architecture & Analysis': [],
    'BESS & Battery Trading': [],
    'VLP & Revenue Models': [],
    'API & Integration': [],
    'Configuration & Setup': [],
    'Diagnostic & Fixes': [],
    'Apps Script & Automation': [],
    'Project Documentation': []
}

for md_file in md_files:
    basename = os.path.basename(md_file)
    rel_path = md_file.replace('/home/george/GB-Power-Market-JJ/', '')

    # Categorize based on filename patterns
    if any(kw in basename.upper() for kw in ['DASHBOARD', 'DEPLOYMENT', 'LIVE']):
        doc_categories['Dashboard & Deployment'].append((basename, rel_path))
    elif any(kw in basename.upper() for kw in ['DATA', 'BIGQUERY', 'ARCHITECTURE', 'ANALYSIS', 'STATISTICAL']):
        doc_categories['Data Architecture & Analysis'].append((basename, rel_path))
    elif any(kw in basename.upper() for kw in ['BESS', 'BATTERY', 'BTM', 'CHP']):
        doc_categories['BESS & Battery Trading'].append((basename, rel_path))
    elif any(kw in basename.upper() for kw in ['VLP', 'VTP', 'REVENUE', 'ARBITRAGE']):
        doc_categories['VLP & Revenue Models'].append((basename, rel_path))
    elif any(kw in basename.upper() for kw in ['API', 'VERCEL', 'CHATGPT', 'PROXY', 'IRIS']):
        doc_categories['API & Integration'].append((basename, rel_path))
    elif any(kw in basename.upper() for kw in ['CONFIG', 'SETUP', 'INSTRUCTION', 'QUICKSTART']):
        doc_categories['Configuration & Setup'].append((basename, rel_path))
    elif any(kw in basename.upper() for kw in ['FIX', 'DIAGNOSTIC', 'DEBUG', 'ISSUE', 'ERROR']):
        doc_categories['Diagnostic & Fixes'].append((basename, rel_path))
    elif any(kw in basename.upper() for kw in ['APPS', 'SCRIPT', 'CLASP', 'SHEETS']):
        doc_categories['Apps Script & Automation'].append((basename, rel_path))
    else:
        doc_categories['Project Documentation'].append((basename, rel_path))

# ============================================================================
# BUILD EXPANDED DOCUMENTATION SECTION
# ============================================================================
doc_rows = [
    [''],
    ['═══════════════════════════════════════════════════════════════════════', '', '', '', '', '', '', '', '', '', ''],
    ['📚 MARKDOWN DOCUMENTATION FILES (873 FILES)', '', '', '', '', '', '', '', '', '', ''],
    ['═══════════════════════════════════════════════════════════════════════', '', '', '', '', '', '', '', '', '', ''],
    [''],
    ['Category', 'File Count', 'Description'],
    ['Dashboard & Deployment', str(len(doc_categories['Dashboard & Deployment'])), 'Dashboard configuration, deployment guides, live metrics setup'],
    ['Data Architecture & Analysis', str(len(doc_categories['Data Architecture & Analysis'])), 'BigQuery schemas, data flow, statistical analysis guides'],
    ['BESS & Battery Trading', str(len(doc_categories['BESS & Battery Trading'])), 'Battery storage calculations, DUoS rates, arbitrage models'],
    ['VLP & Revenue Models', str(len(doc_categories['VLP & Revenue Models'])), 'Virtual Lead Party revenue tracking, balancing mechanism analysis'],
    ['API & Integration', str(len(doc_categories['API & Integration'])), 'Elexon API, IRIS pipeline, ChatGPT proxy, Vercel deployment'],
    ['Configuration & Setup', str(len(doc_categories['Configuration & Setup'])), 'Project setup guides, environment configuration, quick starts'],
    ['Diagnostic & Fixes', str(len(doc_categories['Diagnostic & Fixes'])), 'Troubleshooting guides, bug fixes, data validation reports'],
    ['Apps Script & Automation', str(len(doc_categories['Apps Script & Automation'])), 'Google Sheets automation, CLASP deployment, Apps Script functions'],
    ['Project Documentation', str(len(doc_categories['Project Documentation'])), 'READMEs, project overviews, general documentation'],
    [''],
    ['TOTAL DOCUMENTATION', str(len(md_files)), '873 markdown files covering all aspects of the platform'],
    ['']
]

# Add detailed file listings for each category (limit to top 20 per category for space)
for category, files in doc_categories.items():
    if files:
        doc_rows.append([''])
        doc_rows.append([f'📂 {category.upper()} ({len(files)} files)', '', ''])
        doc_rows.append(['Filename', 'Path', 'Purpose'])

        for filename, rel_path in files[:20]:  # Top 20 per category
            # Extract purpose from filename
            purpose = filename.replace('.md', '').replace('_', ' ').replace('-', ' ').title()
            if len(purpose) > 50:
                purpose = purpose[:47] + '...'

            doc_rows.append([filename, rel_path, purpose])

        if len(files) > 20:
            doc_rows.append([f'...and {len(files) - 20} more files', '', ''])

# ============================================================================
# FIND INSERT POSITION (after current python scripts section)
# ============================================================================
print("📍 Finding insertion point in sheet...")

# Read all current data
all_data = worksheet.get_all_values()
insert_row = None

# Find row with "EXAMPLE SQL QUERIES" or similar marker
for idx, row in enumerate(all_data):
    if row and len(row) > 0:
        if 'ORDER BY date' in row[0] or 'LIMIT 48' in row[0]:
            insert_row = idx + 2  # Insert after SQL examples
            break

if not insert_row:
    # Fallback: find last non-empty row
    for idx in range(len(all_data) - 1, -1, -1):
        if any(cell.strip() for cell in all_data[idx]):
            insert_row = idx + 2
            break

if not insert_row:
    insert_row = 150  # Default fallback

print(f"📍 Inserting documentation at row {insert_row}")

# ============================================================================
# ELEXON API REFERENCE SECTION
# ============================================================================
elexon_api_rows = [
    [''],
    ['═══════════════════════════════════════════════════════════════════════', '', '', '', '', '', '', '', '', '', ''],
    ['⚡ ELEXON INSIGHTS SOLUTION API REFERENCE', '', '', '', '', '', '', '', '', '', ''],
    ['═══════════════════════════════════════════════════════════════════════', '', '', '', '', '', '', '', '', '', ''],
    [''],
    ['What is Elexon?', 'Administers the Balancing and Settlement Code (BSC)', '', 'Runs services to compare traded vs metered volumes, calculate imbalance price, transfer funds'],
    [''],
    ['API Type', 'Description', 'Access', 'Documentation'],
    ['REST API (Dataset)', 'Pull-based dataset endpoints (stream variants available)', 'No API key required', 'https://developer.data.elexon.co.uk/'],
    ['IRIS', 'Push-based near real-time stream + public archive', 'Azure Service Bus', 'https://bmrs.elexon.co.uk/api-documentation'],
    ['OpenAPI Spec', 'Swagger definitions for all endpoints', 'Public', 'https://data.elexon.co.uk/swagger/v1/swagger.json'],
    [''],
    ['KEY DATASETS', '', '', ''],
    ['Dataset Code', 'Description', 'Example Use Case', 'Update Frequency'],
    ['FREQ', 'System frequency (Hz)', 'Grid stability, frequency response events', 'Real-time (~10s)'],
    ['FUELHH', 'Half-hourly generation by fuel type', 'Fuel mix analysis, renewables tracking', '30 minutes'],
    ['MID', 'Market Index Data (wholesale prices)', 'BM-MID spread calculation', 'Real-time'],
    ['BOAL', 'Balancing acceptance levels (no prices)', 'Dispatch intensity, workhorse index', '~2-4 hours'],
    ['BOD', 'Bid-Offer Data (price submissions)', 'Price discovery, revenue analysis', '~30-60 min'],
    ['PN', 'Physical notifications', 'Generation schedules', '~30-60 min'],
    ['NETBSAD', 'Net balancing system adjustment data', 'Settlement calculations', '~2-4 hours'],
    ['REMIT', 'Generation unavailability messages', 'Outages tracking', 'Real-time'],
    [''],
    ['EXAMPLE API CALLS', '', '', ''],
    [''],
    ['# Curl example - FUELHH dataset stream', '', '', ''],
    ['curl -s "https://data.elexon.co.uk/bmrs/api/v1/datasets/FUELHH/stream?publishDateTimeFrom=2025-12-01T00:00:00Z&publishDateTimeTo=2025-12-02T00:00:00Z"', '', '', ''],
    [''],
    ['# Python example - Generic dataset query', '', '', ''],
    ['import requests', '', '', ''],
    ['url = "https://data.elexon.co.uk/bmrs/api/v1/datasets/FUELHH/stream"', '', '', ''],
    ['params = {"publishDateTimeFrom": "2025-12-01T00:00:00Z", "publishDateTimeTo": "2025-12-02T00:00:00Z"}', '', '', ''],
    ['r = requests.get(url, params=params, timeout=60)', '', '', ''],
    ['data = r.json()  # Returns array of records', '', '', ''],
    [''],
    ['ELEXON RESOURCES', '', '', ''],
    ['BSC Glossary', 'https://www.elexon.co.uk/bsc/glossary/', '', 'Official term definitions'],
    ['Technical Glossary', 'https://bscdocs.elexon.co.uk/guidance-notes/', '', 'Detailed technical documentation'],
    ['Imbalance Pricing', 'https://bscdocs.elexon.co.uk/guidance-notes/imbalance-pricing-guidance', '', 'SSP/SBP calculation methodology'],
    ['API Documentation', 'https://bmrs.elexon.co.uk/api-documentation', '', 'Complete API reference'],
    ['GitHub Docs', 'https://github.com/elexon-data/insights-docs/', '', 'Open source documentation'],
    ['']
]

# ============================================================================
# NESO REFERENCE SECTION
# ============================================================================
neso_rows = [
    [''],
    ['═══════════════════════════════════════════════════════════════════════', '', '', '', '', '', '', '', '', '', ''],
    ['⚡ NESO (NATIONAL GRID ESO) REFERENCE', '', '', '', '', '', '', '', '', '', ''],
    ['═══════════════════════════════════════════════════════════════════════', '', '', '', '', '', '', '', '', '', ''],
    [''],
    ['What is NESO?', 'National Energy System Operator (formerly National Grid ESO)', '', 'Operates the GB transmission system, runs the Balancing Mechanism'],
    [''],
    ['KEY NESO RESOURCES', '', '', ''],
    ['Resource', 'URL', 'Description', 'Use Case'],
    ['NESO Glossary', 'https://www.neso.energy/industry-information/connections/help-and-support/glossary-terms', 'Official term definitions', 'Understanding market terminology'],
    ['Balancing Mechanism Guide', 'https://www.neso.energy/what-we-do/systems-operations/what-balancing-mechanism', 'How BM works', 'Understanding dispatch process'],
    ['Grid Code', 'https://www.nationalgrid.com/sites/default/files/documents/8589935286-04_GLOSSARY__DEFINITIONS_I5R20.pdf', 'Technical definitions', 'Compliance and technical specs'],
    ['Data Portal', 'https://dcm.nationalenergyso.com/', 'Distribution Connection and Use of System', 'DNO data, connection info'],
    ['']
]

# Combine all new sections
all_new_rows = doc_rows + elexon_api_rows + neso_rows

# Normalize all rows to 11 columns
for row in all_new_rows:
    while len(row) < 11:
        row.append('')
    row[:] = row[:11]

# ============================================================================
# INSERT NEW DATA
# ============================================================================
print(f"📝 Inserting {len(all_new_rows)} rows of enhanced documentation...")

# Calculate range
start_cell = f'A{insert_row}'
end_col_letter = 'K'  # Column K = 11 columns (A-K)
end_cell = f'{end_col_letter}{insert_row + len(all_new_rows) - 1}'
range_name = f'{start_cell}:{end_cell}'

print(f"📍 Writing to range: {range_name}")

worksheet.update(values=all_new_rows, range_name=range_name)

print(f"✅ DATA sheet updated successfully! 📊")
print(f"   • Added {len(md_files)} markdown file references")
print(f"   • Added Elexon API reference (40+ rows)")
print(f"   • Added NESO resource links")
print(f"   • Total new rows: {len(all_new_rows)}")

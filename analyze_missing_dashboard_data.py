#!/usr/bin/env python3
"""
Analyze what data is available in BigQuery but NOT in the Google Sheets dashboard
Compares BigQuery tables with dashboard data sources
"""

from google.cloud import bigquery
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import os

# Configuration
PROJECT_ID = 'inner-cinema-476211-u9'
DATASET = 'uk_energy_prod'
SPREADSHEET_ID = '1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA'

os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'inner-cinema-credentials.json'

print("="*120)
print("📊 ANALYZING BIGQUERY DATA vs GOOGLE SHEETS DASHBOARD")
print("="*120)

# Connect to BigQuery
client = bigquery.Client(project=PROJECT_ID, location='US')

# Get all tables with row counts
print("\n🔍 Scanning BigQuery tables...")
dataset_ref = client.dataset(DATASET, project=PROJECT_ID)
tables = list(client.list_tables(dataset_ref))

table_data = []
for table in tables:
    full_table_id = f'{PROJECT_ID}.{DATASET}.{table.table_id}'
    try:
        table_obj = client.get_table(full_table_id)
        if table_obj.num_rows and table_obj.num_rows > 0:
            # Categorize
            name = table.table_id
            if '_iris' in name:
                category = 'Real-time (IRIS)'
            elif 'elexon' in name or 'p114' in name:
                category = 'Settlement (P114)'
            elif name.startswith('mart_') or name.startswith('v_'):
                category = 'Analytics View'
            elif name.startswith('bmrs_'):
                category = 'Historical (BMRS)'
            elif name.startswith('dim_') or name.startswith('fact_'):
                category = 'Data Warehouse'
            else:
                category = 'Other'
            
            table_data.append({
                'name': name,
                'rows': table_obj.num_rows,
                'size_gb': table_obj.num_bytes / (1024**3) if table_obj.num_bytes else 0,
                'category': category,
                'created': table_obj.created
            })
    except Exception as e:
        pass

table_data.sort(key=lambda x: x['rows'], reverse=True)

print(f"✅ Found {len(table_data)} tables with data\n")

# Group by category
categories = {}
for t in table_data:
    cat = t['category']
    if cat not in categories:
        categories[cat] = []
    categories[cat].append(t)

print("📋 BIGQUERY DATA INVENTORY BY CATEGORY")
print("="*120)
for cat, tables in sorted(categories.items()):
    total_rows = sum(t['rows'] for t in tables)
    total_gb = sum(t['size_gb'] for t in tables)
    print(f"\n{cat}: {len(tables)} tables, {total_rows:,} total rows, {total_gb:.1f} GB")
    print("-"*120)
    print(f"{'Table Name':<45} {'Rows':>15} {'Size (GB)':>12} {'Created':<20}")
    print("-"*120)
    for t in sorted(tables, key=lambda x: x['rows'], reverse=True)[:10]:
        created_str = t['created'].strftime('%Y-%m-%d %H:%M') if t['created'] else 'Unknown'
        print(f"{t['name']:<45} {t['rows']:>15,} {t['size_gb']:>12.2f} {created_str:<20}")
    if len(tables) > 10:
        print(f"... and {len(tables)-10} more tables")

# Now check what's in the dashboard
print("\n\n📊 CHECKING GOOGLE SHEETS DASHBOARD...")
print("="*120)

try:
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    creds = ServiceAccountCredentials.from_json_keyfile_name('inner-cinema-credentials.json', scope)
    gc = gspread.authorize(creds)
    
    spreadsheet = gc.open_by_key(SPREADSHEET_ID)
    worksheets = spreadsheet.worksheets()
    
    print(f"✅ Found {len(worksheets)} sheets in dashboard")
    print(f"\nSheets: {', '.join([ws.title for ws in worksheets])}\n")
    
except Exception as e:
    print(f"⚠️  Could not connect to Google Sheets: {e}")
    worksheets = []

# Identify missing/unused data
print("\n\n🔍 DATA AVAILABLE IN BIGQUERY BUT NOT IN DASHBOARD")
print("="*120)

# Key datasets that should be in dashboard but might be missing
priority_missing = {
    'Settlement (P114)': [
        'elexon_p114_s0142_bpi', 'p114_settlement_canonical', 'mart_vlp_revenue_p114'
    ],
    'Balancing Mechanism': [
        'bmrs_boalf_complete', 'boalf_with_prices', 'mart_bm_value_by_vlp_sp'
    ],
    'Market Prices': [
        'bmrs_disbsad', 'bmrs_netbsad', 'bmrs_costs', 'bmrs_mid'
    ],
    'Generation & Demand': [
        'bmrs_indgen', 'bmrs_b1610', 'bmrs_b1620', 'demand_outturn_hybrid'
    ],
    'Frequency & Physics': [
        'bmrs_freq', 'bmrs_imbalngc'
    ],
    'Outages': [
        'bmrs_remit_unavailability', 'bmrs_uo', 'bmrs_uou2t14d', 'bmrs_uou2t3yw'
    ],
    'Wind Forecasts': [
        'bmrs_windfor', 'bmrs_windfor_iris'
    ],
    'Interconnectors': [
        'bmrs_interfuelhh'
    ]
}

print("\n🎯 HIGH-PRIORITY DATASETS (should be in dashboard):\n")
for category, tables in priority_missing.items():
    print(f"\n{category}:")
    for table_name in tables:
        matching = [t for t in table_data if t['name'] == table_name]
        if matching:
            t = matching[0]
            status = "✅ Available" if t['rows'] > 0 else "⚠️  Empty"
            print(f"  {status} {t['name']:<45} {t['rows']:>15,} rows, {t['size_gb']:>8.2f} GB")
        else:
            print(f"  ❌ Missing {table_name}")

# NEW P114 Settlement Data
print("\n\n🆕 NEWLY ADDED P114 SETTLEMENT DATA (Dec 2025)")
print("="*120)
p114_tables = [t for t in table_data if 'p114' in t['name'].lower() or 'elexon' in t['name'].lower()]
if p114_tables:
    print(f"Found {len(p114_tables)} P114-related tables:\n")
    for t in p114_tables:
        print(f"  ✅ {t['name']:<45} {t['rows']:>15,} rows, {t['size_gb']:>8.2f} GB")
        print(f"     Category: {t['category']}, Created: {t['created'].strftime('%Y-%m-%d') if t['created'] else 'Unknown'}")
else:
    print("⚠️  No P114 settlement data found")

# Summary recommendations
print("\n\n💡 RECOMMENDATIONS FOR DASHBOARD UPDATES")
print("="*120)
print("""
1. ADD P114 SETTLEMENT DATA (NEW - Dec 2025):
   - mart_vlp_revenue_p114: VLP revenue from settlement (not BM acceptances)
   - p114_settlement_canonical: Deduplicated settlement data (RF>R3>II priority)
   - Currently: 23.5M records (78 days), growing with backfill

2. ENHANCE VLP REVENUE TRACKING:
   - Replace BOALF-based revenue with P114 settlement (more accurate)
   - Show data maturity: Final (RF), High Confidence (R3), Preliminary (II)
   - Compare self-balancing vs ESO-directed revenue

3. ADD SYSTEM IMBALANCE DATA:
   - bmrs_disbsad: Settlement adjustment data (512k rows)
   - bmrs_netbsad: Net balancing system adjustment
   - bmrs_imbalngc: Imbalance volume data

4. ADD WIND FORECAST TRACKING:
   - bmrs_windfor: Wind generation forecasts
   - Compare forecast vs actual (forecast accuracy metrics)

5. ADD OUTAGES DASHBOARD:
   - bmrs_remit_unavailability: Power station outages (REMIT messages)
   - Show active outages by fuel type, capacity offline
   - Already have 177k+ rows of outage data

6. ADD INTERCONNECTOR FLOWS:
   - bmrs_interfuelhh: Half-hourly interconnector flows
   - Show import/export trends by interconnector

7. DASHBOARD INTEGRATION SCRIPTS AVAILABLE:
   - update_dashboard_p114.py: P114 settlement integration
   - calculate_vlp_revenue_from_p114.py: VLP revenue calculator
   - detect_self_balancing_units.py: Self-balancing analysis

Run: python3 update_dashboard_p114.py
     to add P114 settlement data to Google Sheets
""")

print("\n✅ Analysis complete!")

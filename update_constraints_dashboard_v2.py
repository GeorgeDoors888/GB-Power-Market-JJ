#!/usr/bin/env python3
"""
Update Dashboard with live constraint data - simplified version
Uses actual column names from NESO data
"""

import gspread
from oauth2client.service_account import ServiceAccountCredentials
from google.cloud import bigquery
import os
from datetime import datetime

os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'inner-cinema-credentials.json'

scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
creds = ServiceAccountCredentials.from_json_keyfile_name('inner-cinema-credentials.json', scope)
gc = gspread.authorize(creds)

PROJECT_ID = "inner-cinema-476211-u9"
DATASET = "uk_constraints"
bq_client = bigquery.Client(project=PROJECT_ID, location="US")

sheet_id = '1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA'
sh = gc.open_by_key(sheet_id)
dashboard = sh.worksheet('Dashboard')

print("🔄 Updating Dashboard constraint section...")

HEADER_ROW = 112
BOUNDARY_ROW = 116
CMIS_ROW = 130
SOURCES_ROW = 159

# Update timestamp
dashboard.update(values=[[f"Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | Data Source: NESO Connected Data Portal"]], range_name=f'A{HEADER_ROW}')

# ============================================================================
# 1. UPDATE KEY BOUNDARIES - Latest data by constraint group
# ============================================================================
print("📊 Updating boundary data...")

boundary_query = """
SELECT
  constraint_group,
  AVG(flow_mw) as avg_flow,
  AVG(limit_mw) as avg_limit,
  COUNT(*) as record_count
FROM `inner-cinema-476211-u9.uk_constraints.constraint_flows_da`
WHERE constraint_group IS NOT NULL
GROUP BY constraint_group
ORDER BY constraint_group
LIMIT 10
"""

try:
    boundary_df = bq_client.query(boundary_query).to_dataframe()
    
    if len(boundary_df) > 0:
        boundary_updates = []
        for _, row in boundary_df.iterrows():
            flow = row['avg_flow'] if row['avg_flow'] else 0
            limit = row['avg_limit'] if row['avg_limit'] else 0
            util = (flow / limit * 100) if limit > 0 else 0
            margin = limit - flow if limit > 0 and flow else 0
            
            if util >= 90:
                status = "🔴 Critical"
            elif util >= 75:
                status = "🟠 High"
            elif util >= 50:
                status = "🟡 Moderate"
            else:
                status = "🟢 Normal"
            
            # Extract boundary ID from constraint_group
            boundary_id = row['constraint_group'][:10] if row['constraint_group'] else "—"
            
            boundary_updates.append([
                boundary_id,
                row['constraint_group'],
                f"{flow:.0f}" if flow else "—",
                f"{limit:.0f}" if limit else "—",
                f"{util:.1f}%",
                f"{margin:.0f}" if margin else "—",
                status,
                "—"
            ])
        
        dashboard.update(values=boundary_updates, range_name=f'A{BOUNDARY_ROW+1}:H{BOUNDARY_ROW+len(boundary_updates)}')
        print(f"   ✅ Updated {len(boundary_updates)} boundary groups")
    else:
        print("   ⚠️  No boundary data")
except Exception as e:
    print(f"   ❌ Error: {e}")

# ============================================================================
# 2. UPDATE CMIS EVENTS - Recent arming/disarming
# ============================================================================
print("⚡ Updating CMIS data...")

cmis_query = """
SELECT
  bmu_id,
  arming_date_time,
  disarming_date_time,
  current_arming_fee_mwh,
  b6_ec5 as boundary
FROM `inner-cinema-476211-u9.uk_constraints.cmis_arming`
WHERE bmu_id IS NOT NULL
ORDER BY arming_date_time DESC
LIMIT 10
"""

try:
    cmis_df = bq_client.query(cmis_query).to_dataframe()
    
    if len(cmis_df) > 0:
        cmis_updates = []
        for _, row in cmis_df.iterrows():
            armed = "✅ Disarmed" if row['disarming_date_time'] else "🔴 Armed"
            
            cmis_updates.append([
                row['bmu_id'][:15] if row['bmu_id'] else "—",
                row['boundary'][:10] if row['boundary'] else "—",
                str(row['arming_date_time'])[:16] if row['arming_date_time'] else "—",
                str(row['disarming_date_time'])[:16] if row['disarming_date_time'] else "—",
                "—",
                "—",
                armed,
                f"£{row['current_arming_fee_mwh']:.2f}" if row['current_arming_fee_mwh'] else "—"
            ])
        
        dashboard.update(values=cmis_updates, range_name=f'A{CMIS_ROW+3}:H{CMIS_ROW+3+len(cmis_updates)-1}')
        print(f"   ✅ Updated {len(cmis_updates)} CMIS events")
    else:
        print("   ⚠️  No CMIS data")
except Exception as e:
    print(f"   ❌ Error: {e}")

# ============================================================================
# 3. UPDATE DATA SOURCE STATUS
# ============================================================================
print("📡 Updating data source status...")

tables = [
    ("constraint_flows_da", "Day-Ahead Constraint Flows", SOURCES_ROW+4),
    ("constraint_limits_24m", "24-Month Constraint Limits", SOURCES_ROW+5),
    ("cmis_arming", "CMIS Arming Events", SOURCES_ROW+6),
    ("cmz_forecasts", "CMZ Forecasts", SOURCES_ROW+7),
]

for table_name, display_name, row_num in tables:
    try:
        check_query = f"SELECT COUNT(*) as cnt FROM `{PROJECT_ID}.{DATASET}.{table_name}`"
        result = bq_client.query(check_query).to_dataframe()
        
        if len(result) > 0:
            count = result['cnt'][0]
            dashboard.update(values=[[display_name, "✅ Active", datetime.now().strftime('%Y-%m-%d %H:%M'), f"{count:,}", "NESO Portal", ""]], range_name=f'A{row_num}:F{row_num}')
            print(f"   ✅ {display_name}: {count:,} records")
    except Exception as e:
        print(f"   ⚠️  {display_name}: {e}")

print("\n✅ Dashboard update complete!")
print(f"🔗 View: https://docs.google.com/spreadsheets/d/{sheet_id}/edit#gid=0&range=A110")

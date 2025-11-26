#!/usr/bin/env python3
"""
Update Dashboard with live constraint data from BigQuery
Queries uk_constraints.* tables and updates Dashboard sheet

Run every 5 minutes via cron for near-real-time updates
"""

import gspread
from oauth2client.service_account import ServiceAccountCredentials
from google.cloud import bigquery
import os
from datetime import datetime, timedelta

# Set credentials
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'inner-cinema-credentials.json'

# Google Sheets setup
scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
creds = ServiceAccountCredentials.from_json_keyfile_name('inner-cinema-credentials.json', scope)
gc = gspread.authorize(creds)

# BigQuery setup
PROJECT_ID = "inner-cinema-476211-u9"
DATASET = "uk_constraints"
bq_client = bigquery.Client(project=PROJECT_ID, location="US")

sheet_id = '12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8'
sh = gc.open_by_key(sheet_id)
dashboard = sh.worksheet('Dashboard')

print("🔄 Updating Dashboard with constraint data...")

# Row positions (matching implement_constraints_dashboard.py)
HEADER_ROW = 112
BOUNDARY_ROW = 116
CMIS_ROW = 130
CMZ_ROW = 138
COST_ROW = 146
SOURCES_ROW = 159

# ============================================================================
# 1. UPDATE TIMESTAMP
# ============================================================================
dashboard.update(values=[[f"Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | Data Source: NESO Connected Data Portal"]], range_name=f'A{HEADER_ROW}')

# ============================================================================
# 2. UPDATE KEY BOUNDARIES
# ============================================================================
print("📊 Updating boundary data...")

boundary_query = """
SELECT
  boundary_id,
  boundary_name,
  AVG(flow_mw) as avg_flow_mw,
  AVG(limit_mw) as avg_limit_mw,
  AVG(SAFE_DIVIDE(flow_mw, limit_mw)) as avg_utilisation
FROM `inner-cinema-476211-u9.uk_constraints.constraint_flows_da`
WHERE delivery_datetime_utc >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 1 HOUR)
GROUP BY boundary_id, boundary_name
ORDER BY boundary_id
"""

try:
    boundary_df = bq_client.query(boundary_query).to_dataframe()
    
    if len(boundary_df) > 0:
        boundary_updates = []
        for _, row in boundary_df.iterrows():
            util = row['avg_utilisation'] * 100 if row['avg_utilisation'] else 0
            margin = row['avg_limit_mw'] - row['avg_flow_mw'] if row['avg_limit_mw'] and row['avg_flow_mw'] else 0
            
            if util >= 90:
                status = "🔴 Critical"
            elif util >= 75:
                status = "🟠 High"
            elif util >= 50:
                status = "🟡 Moderate"
            else:
                status = "🟢 Normal"
            
            boundary_updates.append([
                row['boundary_id'],
                row['boundary_name'],
                f"{row['avg_flow_mw']:.0f}" if row['avg_flow_mw'] else "—",
                f"{row['avg_limit_mw']:.0f}" if row['avg_limit_mw'] else "—",
                f"{util:.1f}%",
                f"{margin:.0f}",
                status,
                "N→S"  # TODO: Get from metadata
            ])
        
        dashboard.update(values=boundary_updates, range_name=f'A{BOUNDARY_ROW+1}:H{BOUNDARY_ROW+len(boundary_updates)}')
        print(f"   ✅ Updated {len(boundary_updates)} boundaries")
    else:
        print("   ⚠️  No boundary data available")
except Exception as e:
    print(f"   ❌ Error: {e}")

# ============================================================================
# 3. UPDATE CMIS EVENTS
# ============================================================================
print("⚡ Updating CMIS data...")

cmis_query = """
SELECT
  unit_id,
  boundary_id,
  arm_datetime_utc,
  disarm_datetime_utc,
  TIMESTAMP_DIFF(disarm_datetime_utc, arm_datetime_utc, MINUTE) as duration_min,
  mw_available
FROM `inner-cinema-476211-u9.uk_constraints.cmis_arming`
WHERE arm_datetime_utc >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 24 HOUR)
ORDER BY arm_datetime_utc DESC
LIMIT 5
"""

try:
    cmis_df = bq_client.query(cmis_query).to_dataframe()
    
    if len(cmis_df) > 0:
        cmis_updates = []
        for _, row in cmis_df.iterrows():
            arm_time = row['arm_datetime_utc'].strftime('%Y-%m-%d %H:%M') if row['arm_datetime_utc'] else "—"
            disarm_time = row['disarm_datetime_utc'].strftime('%Y-%m-%d %H:%M') if row['disarm_datetime_utc'] else "Armed"
            
            cmis_updates.append([
                row['unit_id'],
                row['boundary_id'],
                arm_time,
                disarm_time,
                f"{row['duration_min']:.0f}" if row['duration_min'] else "—",
                f"{row['mw_available']:.0f}" if row['mw_available'] else "—",
                "✅ Disarmed" if row['disarm_datetime_utc'] else "🔴 Armed",
                "—"
            ])
        
        dashboard.update(values=cmis_updates, range_name=f'A{CMIS_ROW+3}:H{CMIS_ROW+3+len(cmis_updates)-1}')
        print(f"   ✅ Updated {len(cmis_updates)} CMIS events")
    else:
        print("   ⚠️  No CMIS data available")
except Exception as e:
    print(f"   ❌ Error: {e}")

# ============================================================================
# 4. UPDATE CMZ DATA
# ============================================================================
print("🏘️  Updating CMZ data...")

cmz_query = """
SELECT
  cmz_id,
  zone_type,
  gsp_id,
  AVG(forecast_flow_mw) as avg_flow_mw,
  AVG(limit_mw) as avg_limit_mw
FROM `inner-cinema-476211-u9.uk_constraints.cmz_forecasts`
WHERE datetime_utc >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 1 HOUR)
GROUP BY cmz_id, zone_type, gsp_id
ORDER BY cmz_id
LIMIT 5
"""

try:
    cmz_df = bq_client.query(cmz_query).to_dataframe()
    
    if len(cmz_df) > 0:
        cmz_updates = []
        for _, row in cmz_df.iterrows():
            util = (row['avg_flow_mw'] / row['avg_limit_mw'] * 100) if row['avg_limit_mw'] else 0
            status = "🔴 Overload" if util > 100 else "🟢 Normal"
            
            cmz_updates.append([
                row['cmz_id'],
                row['zone_type'],
                row['gsp_id'],
                f"{row['avg_flow_mw']:.0f}" if row['avg_flow_mw'] else "—",
                f"{row['avg_limit_mw']:.0f}" if row['avg_limit_mw'] else "—",
                f"{util:.1f}%",
                status,
                "—"
            ])
        
        dashboard.update(values=cmz_updates, range_name=f'A{CMZ_ROW+3}:H{CMZ_ROW+3+len(cmz_updates)-1}')
        print(f"   ✅ Updated {len(cmz_updates)} CMZ zones")
    else:
        print("   ⚠️  No CMZ data available")
except Exception as e:
    print(f"   ❌ Error: {e}")

# ============================================================================
# 5. UPDATE DATA SOURCE STATUS
# ============================================================================
print("📡 Updating data source status...")

# Check each table for last update and record count
tables_to_check = [
    ("constraint_flows_da", "Day-Ahead Constraint Flows", SOURCES_ROW+4),
    ("constraint_limits_24m", "24-Month Constraint Limits", SOURCES_ROW+5),
    ("cmis_arming", "CMIS Arming Events", SOURCES_ROW+6),
    ("cmz_forecasts", "CMZ Forecasts", SOURCES_ROW+7),
    ("cmz_requirements", "CMZ Flexibility Trades", SOURCES_ROW+8),
]

for table_name, display_name, row_num in tables_to_check:
    try:
        check_query = f"""
        SELECT 
            COUNT(*) as record_count,
            MAX(CAST(ingested_utc AS TIMESTAMP)) as last_update
        FROM `{PROJECT_ID}.{DATASET}.{table_name}`
        """
        
        result = bq_client.query(check_query).to_dataframe()
        
        if len(result) > 0 and result['record_count'][0] > 0:
            count = result['record_count'][0]
            last_update = result['last_update'][0]
            
            # Calculate freshness
            if last_update:
                age_hours = (datetime.now() - last_update.to_pydatetime().replace(tzinfo=None)).total_seconds() / 3600
                if age_hours < 24:
                    status = "✅ Fresh"
                elif age_hours < 168:  # 1 week
                    status = "⚠️  Stale"
                else:
                    status = "🔴 Old"
                
                last_update_str = last_update.strftime('%Y-%m-%d %H:%M')
            else:
                status = "⚠️  Unknown"
                last_update_str = "—"
            
            dashboard.update(values=[[display_name, status, last_update_str, f"{count:,}", "", ""]], range_name=f'A{row_num}:F{row_num}')
            print(f"   ✅ {display_name}: {count:,} records")
        else:
            dashboard.update(values=[[display_name, "❌ Not Configured", "—", "0", "", ""]], range_name=f'A{row_num}:F{row_num}')
    except Exception as e:
        # Table doesn't exist yet
        dashboard.update(values=[[display_name, "❌ Not Configured", "—", "0", "", ""]], range_name=f'A{row_num}:F{row_num}')

print("\n✅ Dashboard constraint update complete!")

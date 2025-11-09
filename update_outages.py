#!/usr/bin/env python3
"""
Update Power Station Outages Section
"""

import gspread
from oauth2client.service_account import ServiceAccountCredentials
from google.cloud import bigquery
from datetime import datetime
import os

os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'inner-cinema-credentials.json'

PROJECT_ID = "inner-cinema-476211-u9"
DATASET = "uk_energy_prod"

print("\n🔴 UPDATING POWER STATION OUTAGES...")
print("=" * 70)

# Setup
scope = ['https://spreadsheets.google.com/feeds', 
         'https://www.googleapis.com/auth/drive']
creds = ServiceAccountCredentials.from_json_keyfile_name('inner-cinema-credentials.json', scope)
gc = gspread.authorize(creds)
bq_client = bigquery.Client(project=PROJECT_ID)

ss = gc.open_by_key('12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8')
dashboard = ss.worksheet('Dashboard')

# Query current outages
query = f"""
SELECT 
  publishedDateTime,
  bmUnitId,
  fuelType,
  normalMW,
  unavailableMW,
  unavailableMW / NULLIF(normalMW, 0) * 100 as pct_unavailable,
  eventStart,
  eventEnd,
  message
FROM `{PROJECT_ID}.{DATASET}.bmrs_remit_unavailability`
WHERE eventStart <= CURRENT_TIMESTAMP()
  AND (eventEnd >= CURRENT_TIMESTAMP() OR eventEnd IS NULL)
  AND unavailableMW > 0
ORDER BY publishedDateTime DESC
LIMIT 20
"""

try:
    df = bq_client.query(query).to_dataframe()
    
    if len(df) > 0:
        print(f"✅ Found {len(df)} active outages")
        
        # Get current price for impact calculation
        price_query = f"""
        SELECT AVG(price) as current_price
        FROM `{PROJECT_ID}.{DATASET}.bmrs_mid`
        WHERE CAST(settlementDate AS DATE) = CURRENT_DATE()
          AND settlementPeriod = (
            SELECT MAX(settlementPeriod) 
            FROM `{PROJECT_ID}.{DATASET}.bmrs_mid`
            WHERE CAST(settlementDate AS DATE) = CURRENT_DATE()
          )
        """
        
        price_df = bq_client.query(price_query).to_dataframe()
        current_price = float(price_df['current_price'].iloc[0]) if len(price_df) > 0 else 70.0
        
        print(f"📊 Current market price: £{current_price:.2f}/MWh")
        
        # Find outages section in dashboard
        all_values = dashboard.get_all_values()
        outages_start = None
        
        for i, row in enumerate(all_values, 1):
            if any('ALL STATION OUTAGES' in str(cell) for cell in row):
                outages_start = i + 3  # Skip header rows
                break
        
        if outages_start:
            print(f"📍 Outages table starts at row {outages_start}")
            
            # Prepare outage rows
            outage_rows = []
            
            for _, row in df.iterrows():
                # Status
                status = "🔴 Active"
                
                # Station name from bmUnitId
                bmu = row['bmUnitId']
                station_name = bmu.replace('T_', '').replace('E_', '').replace('-', ' ')
                
                # Fuel type
                fuel = row['fuelType'] if row['fuelType'] else 'UNKNOWN'
                
                # MW values
                normal_mw = int(row['normalMW']) if row['normalMW'] else 0
                unavail_mw = int(row['unavailableMW']) if row['unavailableMW'] else 0
                pct_unavail = float(row['pct_unavailable']) if row['pct_unavailable'] else 0
                
                # Progress bar (10 blocks)
                filled = int(pct_unavail / 10)
                bar = '🟥' * filled + '⬜' * (10 - filled)
                bar_text = f"{bar} {pct_unavail:.1f}%"
                
                # Cause from message (truncate if too long)
                cause = row['message'][:50] if row['message'] else 'Unspecified outage'
                
                outage_rows.append([
                    status,
                    station_name,
                    bmu,
                    fuel,
                    normal_mw,
                    unavail_mw,
                    bar_text,
                    cause
                ])
            
            # Update dashboard (max 10 rows to avoid overwriting other sections)
            if outage_rows:
                num_rows = min(len(outage_rows), 10)
                cell_range = f'A{outages_start}:H{outages_start + num_rows - 1}'
                dashboard.update(cell_range, outage_rows[:num_rows], value_input_option='USER_ENTERED')
                print(f"✅ Updated {num_rows} outage rows")
                
                # Update active outages count
                for i, row in enumerate(all_values, 1):
                    if 'Active Outages:' in str(row):
                        dashboard.update_acell(f'B{i}', f'Active Outages: {len(df)} events')
                        print(f"✅ Updated outage count: {len(df)} events")
                        break
            
            # Calculate total unavailable capacity and price impact
            total_unavail = df['unavailableMW'].sum()
            est_impact = (total_unavail / 50000) * current_price  # Rough estimate
            
            print(f"\n📊 Outage Summary:")
            print(f"   Total Unavailable: {total_unavail:,.0f} MW")
            print(f"   Est. Price Impact: +£{est_impact:.2f}/MWh")
            print(f"   Number of Events: {len(df)}")
            
        else:
            print("⚠️  Could not find outages section in dashboard")
    
    else:
        print("✅ No active outages found")
        print("   (This is good news!)")

except Exception as e:
    print(f"❌ Error querying outages: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 70)
print("✅ OUTAGES SECTION UPDATE COMPLETE")
print("=" * 70)

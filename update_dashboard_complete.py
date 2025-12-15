#!/usr/bin/env python3
"""
Complete Dashboard Update: Graphics + Current Data
"""

import gspread
from oauth2client.service_account import ServiceAccountCredentials
from google.cloud import bigquery
from datetime import datetime
import os

os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'inner-cinema-credentials.json'

PROJECT_ID = "inner-cinema-476211-u9"
DATASET = "uk_energy_prod"

print("\n" + "=" * 70)
print("🔄 COMPREHENSIVE DASHBOARD UPDATE")
print("=" * 70)

# Setup
scope = ['https://spreadsheets.google.com/feeds', 
         'https://www.googleapis.com/auth/drive']
creds = ServiceAccountCredentials.from_json_keyfile_name('inner-cinema-credentials.json', scope)
gc = gspread.authorize(creds)
bq_client = bigquery.Client(project=PROJECT_ID)

ss = gc.open_by_key('1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA')
dashboard = ss.worksheet('Dashboard')

date_today = datetime.now().date()
current_sp = (datetime.now().hour * 2) + (1 if datetime.now().minute < 30 else 2)

# STEP 1: Add Graphics to Interconnectors and Pumped Storage
print("\n📊 STEP 1: Adding Graphics...")
print("-" * 70)

graphics_updates = [
    ('A10', '⚡ IFA (France) 🇫🇷'),
    ('A10', '⚡ IFA2 (France) 🇫🇷'),  
    ('A11', '⚡ ElecLink (France) 🇫🇷'),
    ('A12', '⚡ Nemo (Belgium) 🇧🇪'),
    ('A13', '💧 Pumped Storage 🔋'),
    ('A13', '⚡ Viking Link (Denmark) 🇩🇰'),
    ('A15', '⚡ Moyle (N.Ireland) 🇮🇪'),
    ('A16', '⚡ East-West (Ireland) 🇮🇪'),
    ('A17', '⚡ Greenlink (Ireland) 🇮🇪'),
]

# Read current values and update with graphics
all_values = dashboard.get_all_values()

for row_idx, row in enumerate(all_values, 1):
    row_text = ' '.join(str(cell) for cell in row).lower()
    
    if 'pumped storage' in row_text and '💧' not in row[0]:
        current_val = row[0] if row else ''
        if 'pumped' not in current_val.lower():
            dashboard.update_acell(f'A{row_idx}', f'💧 {current_val} 🔋')
            print(f"✅ Row {row_idx}: Added graphics to Pumped Storage")
    
    if 'ifa' in row_text and 'france' in row_text and 'ifa2' not in row_text and '🇫🇷' not in row[0]:
        current_val = row[0] if row else ''
        dashboard.update_acell(f'A{row_idx}', f'⚡ {current_val} 🇫🇷')
        print(f"✅ Row {row_idx}: Added graphics to IFA (France)")
    
    if 'ifa2' in row_text and '🇫🇷' not in row[0]:
        current_val = row[0] if row else ''
        dashboard.update_acell(f'A{row_idx}', f'⚡ {current_val} 🇫🇷')
        print(f"✅ Row {row_idx}: Added graphics to IFA2 (France)")
    
    if 'eleclink' in row_text and '🇫🇷' not in row[0]:
        current_val = row[0] if row else ''
        dashboard.update_acell(f'A{row_idx}', f'⚡ {current_val} 🇫🇷')
        print(f"✅ Row {row_idx}: Added graphics to ElecLink (France)")
    
    if 'nemo' in row_text and 'belgium' in row_text and '🇧🇪' not in row[0]:
        current_val = row[0] if row else ''
        dashboard.update_acell(f'A{row_idx}', f'⚡ {current_val} 🇧🇪')
        print(f"✅ Row {row_idx}: Added graphics to Nemo (Belgium)")
    
    if 'viking' in row_text and 'denmark' in row_text and '🇩🇰' not in row[0]:
        current_val = row[0] if row else ''
        dashboard.update_acell(f'A{row_idx}', f'⚡ {current_val} 🇩🇰')
        print(f"✅ Row {row_idx}: Added graphics to Viking Link (Denmark)")
    
    if 'moyle' in row_text and 'ireland' in row_text and '🇮🇪' not in row[0]:
        current_val = row[0] if row else ''
        dashboard.update_acell(f'A{row_idx}', f'⚡ {current_val} 🇮🇪')
        print(f"✅ Row {row_idx}: Added graphics to Moyle (N.Ireland)")
    
    if 'east-west' in row_text and 'ireland' in row_text and '🇮🇪' not in row[0]:
        current_val = row[0] if row else ''
        dashboard.update_acell(f'A{row_idx}', f'⚡ {current_val} 🇮🇪')
        print(f"✅ Row {row_idx}: Added graphics to East-West (Ireland)")
    
    if 'greenlink' in row_text and 'ireland' in row_text and '🇮🇪' not in row[0]:
        current_val = row[0] if row else ''
        dashboard.update_acell(f'A{row_idx}', f'⚡ {current_val} 🇮🇪')
        print(f"✅ Row {row_idx}: Added graphics to Greenlink (Ireland)")

# STEP 2: Update Settlement Period Data
print("\n📈 STEP 2: Updating Settlement Period Data...")
print("-" * 70)

# Query today's SP data
query = f"""
WITH combined AS (
  SELECT 
    settlementPeriod,
    SUM(generation) as total_gen
  FROM `{PROJECT_ID}.{DATASET}.bmrs_fuelinst`
  WHERE CAST(settlementDate AS DATE) = '{date_today}'
  GROUP BY settlementPeriod
  
  UNION ALL
  
  SELECT 
    settlementPeriod,
    SUM(generation) as total_gen
  FROM `{PROJECT_ID}.{DATASET}.bmrs_fuelinst_iris`
  WHERE CAST(settlementDate AS DATE) = '{date_today}'
  GROUP BY settlementPeriod
),
freq_data AS (
  SELECT 
    EXTRACT(HOUR FROM measurementTime) * 2 + 
    (CASE WHEN EXTRACT(MINUTE FROM measurementTime) >= 30 THEN 2 ELSE 1 END) as sp,
    AVG(frequency) as avg_freq
  FROM `{PROJECT_ID}.{DATASET}.bmrs_freq`
  WHERE CAST(measurementTime AS DATE) = '{date_today}'
  GROUP BY sp
),
price_data AS (
  SELECT 
    settlementPeriod as sp,
    AVG(price) as avg_price
  FROM `{PROJECT_ID}.{DATASET}.bmrs_mid`
  WHERE CAST(settlementDate AS DATE) = '{date_today}'
  GROUP BY sp
)
SELECT 
  c.settlementPeriod as sp,
  SUM(c.total_gen) / 1000 as gen_gw,
  COALESCE(f.avg_freq, 50.0) as freq,
  COALESCE(p.avg_price, 0) as price
FROM combined c
LEFT JOIN freq_data f ON c.settlementPeriod = f.sp
LEFT JOIN price_data p ON c.settlementPeriod = p.sp
GROUP BY c.settlementPeriod, f.avg_freq, p.avg_price
ORDER BY c.settlementPeriod
LIMIT 48
"""

df_sp = bq_client.query(query).to_dataframe()

if len(df_sp) > 0:
    print(f"✅ Retrieved {len(df_sp)} settlement periods")
    
    # Find SP data table start
    sp_table_start = None
    for i, row in enumerate(all_values, 1):
        if any('SP01' in str(cell) or 'SP1' in str(cell) for cell in row):
            sp_table_start = i
            break
    
    if sp_table_start:
        print(f"📍 SP table starts at row {sp_table_start}")
        
        # Update SP rows
        updates = []
        for _, row in df_sp.iterrows():
            sp_num = int(row['sp'])
            sp_label = f"SP{sp_num:02d}"
            gen_gw = f"{row['gen_gw']:.1f}"
            freq = f"{row['freq']:.2f}" if row['freq'] else "50.00"
            price = f"£{row['price']:.2f}" if row['price'] > 0 else "£0.00"
            
            updates.append([sp_label, gen_gw, freq, price])
        
        if updates:
            # Update range starting from SP table
            cell_range = f'A{sp_table_start}:D{sp_table_start + len(updates) - 1}'
            dashboard.update(cell_range, updates, value_input_option='USER_ENTERED')
            print(f"✅ Updated {len(updates)} settlement periods")
            print(f"   Current SP: SP{current_sp:02d}")
            print(f"   Latest data: SP{df_sp['sp'].max():02d}")
else:
    print("⚠️  No settlement period data found")

# STEP 3: Update Current SP indicator
print("\n📌 STEP 3: Updating Current SP indicator...")
print("-" * 70)

for i, row in enumerate(all_values, 1):
    if '→ Current' in str(row):
        dashboard.update_acell(f'A{i}', f'→ Current: SP{current_sp:02d}')
        print(f"✅ Updated current SP indicator to SP{current_sp:02d}")
        break

print("\n" + "=" * 70)
print("✅ DASHBOARD UPDATE COMPLETE")
print("=" * 70)
print(f"\n📊 Summary:")
print(f"   • Graphics added to interconnectors and pumped storage")
print(f"   • Settlement Period Data updated through SP{df_sp['sp'].max():02d}")
print(f"   • Current SP: SP{current_sp:02d}")
print(f"   • Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print()

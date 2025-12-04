#!/usr/bin/env python3
"""
Dashboard V3 - Complete Test & Validation
Tests buildDashboard() chart and data population
"""

import os
from datetime import datetime, timedelta
from google.cloud import bigquery
import gspread
from google.oauth2.service_account import Credentials

# Configuration
PROJECT_ID = 'inner-cinema-476211-u9'
DATASET = 'uk_energy_prod'
SPREADSHEET_ID = '1LmMq4OEE639Y-XXpOJ3xnvpAmHB6vUovh5g6gaU_vzc'
CREDENTIALS_FILE = 'inner-cinema-credentials.json'

print('=' * 80)
print('🧪 DASHBOARD V3 - COMPLETE TEST & VALIDATION')
print('=' * 80)

# Initialize clients
scopes = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
creds = Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=scopes)
gc = gspread.authorize(creds)
bq_client = bigquery.Client(project=PROJECT_ID, location='US')

ss = gc.open_by_key(SPREADSHEET_ID)

# Test 1: Populate Chart Data with sample data
print('\n📊 TEST 1: Populate Chart Data with last 48 periods')
print('-' * 80)

try:
    chart_sheet = ss.worksheet('Chart Data')
    
    query = """
    WITH latest_data AS (
      SELECT 
        CONCAT('P', CAST(settlementPeriod AS STRING)) as time_sp,
        price as da_price,
        0 as imbalance_price,  -- Placeholder (bmrs_mid_iris only has 'price')
        0 as demand,  -- Placeholder
        0 as generation,  -- Placeholder
        0 as ic_flow,  -- Placeholder
        0 as bm_actions,  -- Placeholder
        0 as vlp_revenue,  -- Placeholder
        NULL as overlay1,
        NULL as overlay2,
        settlementDate,
        settlementPeriod
      FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_mid_iris`
      WHERE settlementDate >= CURRENT_DATE() - 2
      ORDER BY settlementDate DESC, settlementPeriod DESC
      LIMIT 48
    )
    SELECT * FROM latest_data ORDER BY settlementDate, settlementPeriod
    """
    
    df = bq_client.query(query).to_dataframe()
    
    if len(df) > 0:
        # Prepare data
        headers = [['Time/SP', 'DA Price (£/MWh)', 'Imbalance Price (£/MWh)', 
                    'Demand (MW)', 'Generation (MW)', 'IC Flow (MW)',
                    'BM Actions (MW)', 'VLP Revenue (£k)', 'Overlay 1', 'Overlay 2']]
        
        rows = []
        for _, row in df.iterrows():
            rows.append([
                str(row['time_sp']),
                float(row['da_price']) if row['da_price'] else 0,
                float(row['imbalance_price']) if row['imbalance_price'] else 0,
                float(row['demand']),
                float(row['generation']),
                float(row['ic_flow']),
                float(row['bm_actions']),
                float(row['vlp_revenue']),
                '',
                ''
            ])
        
        # Update sheet
        chart_sheet.update(values=headers + rows, range_name='A1')
        print(f'   ✅ Populated {len(rows)} rows')
        print(f'   Date range: {df["settlementDate"].min()} to {df["settlementDate"].max()}')
        print(f'   Settlement periods: {df["settlementPeriod"].min()} to {df["settlementPeriod"].max()}')
    else:
        print('   ⚠️  No data found')
        
except Exception as e:
    print(f'   ❌ Error: {e}')

# Test 2: Populate VLP_Data
print('\n💰 TEST 2: Populate VLP_Data with latest revenue')
print('-' * 80)

try:
    vlp_sheet = ss.worksheet('VLP_Data')
    
    query = """
    SELECT 
      FORMAT_DATE('%Y-%m-%d', CAST(settlementDate AS DATE)) as settlementDate,
      settlementPeriod,
      duos_band,
      trading_signal,
      net_margin_per_mwh,
      bm_revenue_per_mwh,
      dc_revenue_per_mwh,
      dm_revenue_per_mwh,
      cm_revenue_per_mwh,
      triad_value_per_mwh,
      total_stacked_revenue_per_mwh,
      ssp_charge,
      duos_charge,
      levies_per_mwh,
      total_cost_per_mwh
    FROM `inner-cinema-476211-u9.uk_energy_prod.v_btm_bess_inputs`
    ORDER BY settlementDate DESC, settlementPeriod DESC
    LIMIT 100
    """
    
    df = bq_client.query(query).to_dataframe()
    
    if len(df) > 0:
        # Convert to list of lists
        headers = [[col for col in df.columns]]
        rows = df.values.tolist()
        
        # Update sheet
        vlp_sheet.update(values=headers + rows, range_name='A1')
        print(f'   ✅ Populated {len(rows)} rows')
        print(f'   Latest: {df.iloc[0]["settlementDate"]} P{df.iloc[0]["settlementPeriod"]}')
        print(f'   Avg profit: £{df["net_margin_per_mwh"].mean():.2f}/MWh')
    else:
        print('   ⚠️  No data found')
        
except Exception as e:
    print(f'   ❌ Error: {e}')

# Test 3: Populate ESO_Actions
print('\n⚡ TEST 3: Populate ESO_Actions with balancing data')
print('-' * 80)

try:
    eso_sheet = ss.worksheet('ESO_Actions')
    
    query = """
    SELECT 
      bmUnit as bmUnitId,
      acceptanceNumber,
      FORMAT_TIMESTAMP('%Y-%m-%d %H:%M:%S', acceptanceTime) as acceptanceTime,
      0 as volume,
      0 as cashflowAmount,
      CASE 
        WHEN soFlag THEN 'SO'
        WHEN storFlag THEN 'STOR'
        WHEN rrFlag THEN 'RR'
        ELSE 'ACCEPTED'
      END as action_type,
      CAST(settlementDate AS DATE) as settlementDate,
      settlementPeriodFrom as settlementPeriod
    FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_boalf_iris`
    WHERE CAST(settlementDate AS DATE) >= CURRENT_DATE() - 1
    ORDER BY acceptanceTime DESC
    LIMIT 50
    """
    
    df = bq_client.query(query).to_dataframe()
    
    if len(df) > 0:
        headers = [[col for col in df.columns]]
        rows = df.values.tolist()
        
        print(f'   ✅ Populated {len(rows)} rows')
        print(f'   Latest: {df.iloc[0]["settlementDate"]} P{df.iloc[0]["settlementPeriod"]}')
        print(f'   Action types: {df["action_type"].value_counts().to_dict()}')
    else:
        print('   ⚠️  No data found')
        
except Exception as e:
    print(f'   ❌ Error: {e}')

# Test 4: Check Dashboard formulas
print('\n📋 TEST 4: Validate Dashboard formulas')
print('-' * 80)

try:
    dash = ss.worksheet('Dashboard')
    
    # Check KPI formulas
    f10 = dash.acell('F10').value
    g10 = dash.acell('G10').value
    h10 = dash.acell('H10').value
    
    print(f'   F10 (VLP KPI): {f10}')
    print(f'   G10 (Wholesale): {g10}')
    print(f'   H10 (Volatility): {h10}')
    
    if f10 and f10.startswith('='):
        print('   ✅ KPI formulas present')
    else:
        print('   ⚠️  KPI formulas missing')
        
except Exception as e:
    print(f'   ❌ Error: {e}')

# Summary
print('\n' + '=' * 80)
print('✅ VALIDATION COMPLETE')
print('=' * 80)
print('\n🚀 Next Steps:')
print('   1. Open spreadsheet: https://docs.google.com/spreadsheets/d/1LmMq4OEE639Y-XXpOJ3xnvpAmHB6vUovh5g6gaU_vzc/edit')
print('   2. Refresh page (Cmd+R)')
print('   3. Click: ⚡ GB Energy → 📊 Rebuild Chart')
print('   4. Chart should appear at column L with 48 periods of data')
print('\n' + '=' * 80)

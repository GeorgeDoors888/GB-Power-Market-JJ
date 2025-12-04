#!/usr/bin/env python3
"""
Dashboard V3 - Data Refresh Script
Populates Chart Data, VLP_Data, and ESO_Actions sheets from BigQuery
"""

import os
import pandas as pd
from datetime import datetime
from google.cloud import bigquery
import gspread
from google.oauth2.service_account import Credentials

# Configuration
PROJECT_ID = 'inner-cinema-476211-u9'
DATASET = 'uk_energy_prod'
SPREADSHEET_ID = '1LmMq4OEE639Y-XXpOJ3xnvpAmHB6vUovh5g6gaU_vzc'
CREDENTIALS_FILE = 'inner-cinema-credentials.json'

def get_clients():
    """Initialize BigQuery and Sheets clients"""
    # BigQuery
    bq_client = bigquery.Client(project=PROJECT_ID, location='US')
    
    # Sheets
    scopes = [
        'https://www.googleapis.com/auth/spreadsheets',
        'https://www.googleapis.com/auth/drive'
    ]
    creds = Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=scopes)
    sheets_client = gspread.authorize(creds)
    
    return bq_client, sheets_client

def refresh_chart_data(bq_client, worksheet):
    """Populate Chart Data with last 48 periods from IRIS using batch updates."""
    print("\n📊 Refreshing Chart Data...")
    
    query = f"""
    SELECT 
      CONCAT('P', CAST(settlementPeriod AS STRING)) as time_sp,
      ROUND(AVG(price), 2) as da_price,
      0 as imbalance_price,
      0 as demand,
      0 as generation,
      0 as ic_flow,
      0 as bm_actions,
      0 as vlp_revenue,
      '' as overlay1,
      '' as overlay2,
      settlementDate,
      settlementPeriod
    FROM `{PROJECT_ID}.{DATASET}.bmrs_mid_iris`
    WHERE settlementDate >= CURRENT_DATE() - 2
    GROUP BY settlementDate, settlementPeriod
    ORDER BY settlementDate DESC, settlementPeriod DESC
    LIMIT 48
    """
    
    df = bq_client.query(query).to_dataframe()
    
    if len(df) > 0:
        headers = [[
            'Time/SP', 'DA Price (£/MWh)', 'Imbalance Price (£/MWh)',
            'Demand (MW)', 'Generation (MW)', 'IC Flow (MW)',
            'BM Actions (MW)', 'VLP Revenue (£k)', 'Overlay 1', 'Overlay 2'
        ]]
        df_output = df.drop(columns=['settlementDate', 'settlementPeriod'])
        rows = df_output.replace({pd.NA: '', pd.NaT: ''}).values.tolist()
        
        worksheet.batch_clear(['A1:Z1000'])
        worksheet.update(values=headers + rows, range_name='A1')
        print(f"   ✅ {len(rows)} periods | Latest: {df.iloc[-1]['time_sp']}")
        return True
    else:
        print("   ⚠️  No data available")
        return False

def refresh_vlp_data(bq_client, worksheet):
    """Populate VLP_Data with latest revenue metrics using batch updates."""
    print("\n💰 Refreshing VLP_Data...")
    
    query = f"""
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
    FROM `{PROJECT_ID}.{DATASET}.v_btm_bess_inputs`
    ORDER BY settlementDate DESC, settlementPeriod DESC
    LIMIT 100
    """
    
    df = bq_client.query(query).to_dataframe()
    
    if len(df) > 0:
        headers = [list(df.columns)]
        rows = df.replace({pd.NA: '', pd.NaT: ''}).values.tolist()
        
        worksheet.batch_clear(['A1:Z1000'])
        worksheet.update(values=headers + rows, range_name='A1')
        
        avg_profit = df['net_margin_per_mwh'].mean()
        print(f"   ✅ {len(rows)} rows | Avg profit: £{avg_profit:.2f}/MWh")
        return True
    else:
        print("   ⚠️  No data available")
        return False

def refresh_eso_actions(bq_client, worksheet):
    """Populate ESO_Actions with recent balancing acceptances using batch updates."""
    print("\n⚡ Refreshing ESO_Actions...")
    
    query = f"""
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
      FORMAT_DATE('%Y-%m-%d', CAST(settlementDate AS DATE)) as settlementDate,
      settlementPeriodFrom as settlementPeriod
    FROM `{PROJECT_ID}.{DATASET}.bmrs_boalf_iris`
    WHERE CAST(settlementDate AS DATE) >= CURRENT_DATE() - 1
    ORDER BY acceptanceTime DESC
    LIMIT 50
    """
    
    df = bq_client.query(query).to_dataframe()
    
    if len(df) > 0:
        headers = [list(df.columns)]
        rows = df.replace({pd.NA: '', pd.NaT: ''}).values.tolist()
        
        worksheet.batch_clear(['A1:Z1000'])
        worksheet.update(values=headers + rows, range_name='A1')
        
        action_counts = df['action_type'].value_counts()
        action_summary = ', '.join([f"{k}: {v}" for k, v in action_counts.items()])
        print(f"   ✅ {len(rows)} actions | {action_summary}")
        return True
    else:
        print("   ⚠️  No data available")
        return False

def update_dashboard_timestamp(worksheet):
    """Updates the timestamp formula in the Dashboard sheet."""
    try:
        # This ensures the formula is always correct and avoids unmanaged writes.
        worksheet.update('A2', '=CONCAT("Live Data: ", TEXT(NOW(), "YYYY-MM-DD HH:mm:ss"))')
        print(f"\n🕒 Verified timestamp formula in cell A2.")
    except Exception as e:
        print(f"   ⚠️  Could not update timestamp formula: {e}")

def main():
    print("=" * 70)
    print("🔄 DASHBOARD V3 - DATA REFRESH")
    print("=" * 70)
    
    try:
        # Initialize clients
        bq_client, sheets_client = get_clients()
        spreadsheet = sheets_client.open_by_key(SPREADSHEET_ID)
        
        # Get worksheets
        chart_sheet = spreadsheet.worksheet('Chart Data')
        vlp_sheet = spreadsheet.worksheet('VLP_Data')
        eso_sheet = spreadsheet.worksheet('ESO_Actions')
        dashboard_sheet = spreadsheet.worksheet('Dashboard')
        
        # Refresh all data
        success_count = 0
        
        if refresh_chart_data(bq_client, chart_sheet):
            success_count += 1
        
        if refresh_vlp_data(bq_client, vlp_sheet):
            success_count += 1
        
        if refresh_eso_actions(bq_client, eso_sheet):
            success_count += 1
        
        # Update timestamp
        update_dashboard_timestamp(dashboard_sheet)
        
        # Summary
        print("\n" + "=" * 70)
        print(f"✅ REFRESH COMPLETE: {success_count}/3 sheets updated")
        print("=" * 70)
        print(f"\n🔗 View: https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/edit")
        print("\n💡 Next: Open spreadsheet and click ⚡ GB Energy → 📊 Rebuild Chart")
        
        return success_count == 3
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = main()
    exit(0 if success else 1)

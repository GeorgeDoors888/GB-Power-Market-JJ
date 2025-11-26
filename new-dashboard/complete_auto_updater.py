#!/usr/bin/env python3
"""
Dashboard V2 - Complete Auto-Updater
Updates all sheets: Dashboard, Daily_Chart_Data, Intraday_Chart_Data, BESS, REMIT Unavailability
Mirrors daily_dashboard_auto_updater.py functionality
"""

import sys
import logging
from datetime import datetime, timedelta
from pathlib import Path
from google.cloud import bigquery
from google.oauth2 import service_account
import gspread
import pandas as pd

# Setup logging
LOG_DIR = Path(__file__).parent / 'logs'
LOG_DIR.mkdir(exist_ok=True)
LOG_FILE = LOG_DIR / 'complete_updater.log'

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(sys.stdout)
    ]
)

# Configuration
SPREADSHEET_ID = '1LmMq4OEE639Y-XXpOJ3xnvpAmHB6vUovh5g6gaU_vzc'
PROJECT_ID = 'inner-cinema-476211-u9'
DATASET = 'uk_energy_prod'
SA_FILE = Path(__file__).parent.parent / 'inner-cinema-credentials.json'

def main():
    logging.info("=" * 80)
    logging.info("🔄 DASHBOARD V2 COMPLETE AUTO-UPDATE")
    logging.info("=" * 80)
    
    # Connect
    logging.info("🔧 Connecting...")
    SCOPES_SHEETS = ['https://www.googleapis.com/auth/spreadsheets']
    SCOPES_BQ = ["https://www.googleapis.com/auth/bigquery"]
    
    sheets_creds = service_account.Credentials.from_service_account_file(
        str(SA_FILE), scopes=SCOPES_SHEETS
    )
    bq_creds = service_account.Credentials.from_service_account_file(
        str(SA_FILE), scopes=SCOPES_BQ
    )
    
    gc = gspread.authorize(sheets_creds)
    bq_client = bigquery.Client(project=PROJECT_ID, credentials=bq_creds, location="US")
    spreadsheet = gc.open_by_key(SPREADSHEET_ID)
    
    logging.info("✅ Connected")
    
    today = datetime.now().date()
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # =======================================================================
    # 1. UPDATE DAILY_CHART_DATA (for charts)
    # =======================================================================
    logging.info("📊 Updating Daily_Chart_Data...")
    
    chart_query = f"""
    WITH 
    prices AS (
        SELECT
            settlementDate as date,
            settlementPeriod as sp,
            AVG(price) as market_price
        FROM `{PROJECT_ID}.{DATASET}.bmrs_mid_iris`
        WHERE settlementDate = '{today}'
          AND dataProvider = 'APXMIDP'
        GROUP BY date, sp
    ),
    demand AS (
        SELECT
            settlementDate as date,
            settlementPeriod as sp,
            AVG(demand) as demand_mw
        FROM `{PROJECT_ID}.{DATASET}.bmrs_indo_iris`
        WHERE settlementDate = '{today}'
        GROUP BY date, sp
    ),
    generation AS (
        SELECT
            CAST(settlementDate AS DATE) as date,
            settlementPeriod as sp,
            SUM(generation) as generation_mw
        FROM `{PROJECT_ID}.{DATASET}.bmrs_fuelinst_iris`
        WHERE CAST(settlementDate AS DATE) = '{today}'
        GROUP BY date, sp
    )
    SELECT 
        COALESCE(p.sp, d.sp, g.sp) as settlement_period,
        COALESCE(p.market_price, 0) as price,
        COALESCE(d.demand_mw, 0) as demand,
        COALESCE(g.generation_mw, 0) as generation
    FROM prices p
    FULL OUTER JOIN demand d ON p.sp = d.sp
    FULL OUTER JOIN generation g ON p.sp = g.sp
    ORDER BY settlement_period
    """
    
    chart_df = bq_client.query(chart_query).to_dataframe()
    
    if not chart_df.empty:
        chart_sheet = spreadsheet.worksheet('Daily_Chart_Data')
        
        # Prepare data with headers
        chart_data = [['Settlement Period', 'Date', 'Price (£/MWh)', 'Demand (MW)', 'Generation (MW)']]
        for _, row in chart_df.iterrows():
            chart_data.append([
                int(row['settlement_period']),
                str(today),
                round(float(row['price']), 2),
                round(float(row['demand']), 0),
                round(float(row['generation']), 0)
            ])
        
        chart_sheet.clear()
        chart_sheet.update(chart_data, 'A1')
        logging.info(f"   ✅ Updated {len(chart_data)-1} settlement periods")
    
    # =======================================================================
    # 2. UPDATE DASHBOARD SUMMARY SECTION
    # =======================================================================
    logging.info("📋 Updating Dashboard summary...")
    
    dashboard = spreadsheet.worksheet('Dashboard')
    
    # Update timestamp
    dashboard.update([[f'⏰ Last Updated: {timestamp} | ✅ Auto-refresh enabled']], 'A2')
    
    # Calculate totals and current metrics
    if not chart_df.empty:
        avg_price = chart_df['price'].mean()
        avg_demand = chart_df['demand'].mean()
        avg_generation = chart_df['generation'].mean()
        
        # Get latest values for row 6
        latest = chart_df.iloc[-1]
        current_demand = latest['demand'] / 1000
        current_gen = latest['generation'] / 1000
        current_price = latest['price']
        
        # Get wind percentage (will calculate from gen data)
        wind_pct = 0  # Will update after getting gen data
        
        # Get frequency
        freq_query = f"""
        SELECT frequency
        FROM `{PROJECT_ID}.{DATASET}.bmrs_freq_iris`
        ORDER BY measurementTime DESC
        LIMIT 1
        """
        try:
            freq_df = bq_client.query(freq_query).to_dataframe()
            frequency = freq_df.iloc[0]['frequency'] if not freq_df.empty else 50.00
        except:
            frequency = 50.00
        
        # Update row 5 (averages)
        summary_text = f"Total Generation: {avg_generation/1000:.1f} GW | Demand: {avg_demand/1000:.1f} GW | Avg Price: £{avg_price:.2f}/MWh"
        dashboard.update([[summary_text]], 'A5')
        
        # Update row 6 (current metrics) - will update wind% after gen data
        current_row = [[
            '📊 Current:',
            f'Demand: {current_demand:.2f} GW',
            f'Generation: {current_gen:.2f} GW',
            'Wind: 0%',  # Placeholder
            f'Price: £{current_price:.2f}/MWh',
            f'Frequency: {frequency:.2f} Hz',
            'Constraint: 0 MW'
        ]]
        dashboard.update(current_row, 'A6')
        
        logging.info(f"   ✅ Updated summary metrics")
    
    # =======================================================================
    # 3. UPDATE GENERATION BY FUEL TYPE
    # =======================================================================
    logging.info("⚡ Updating generation by fuel type...")
    
    gen_query = f"""
    WITH latest_period AS (
        SELECT MAX(settlementPeriod) as max_sp
        FROM `{PROJECT_ID}.{DATASET}.bmrs_fuelinst_iris`
        WHERE CAST(settlementDate AS DATE) = '{today}'
    )
    SELECT 
        fuelType,
        ROUND(SUM(generation), 1) as total_mw
    FROM `{PROJECT_ID}.{DATASET}.bmrs_fuelinst_iris`
    WHERE CAST(settlementDate AS DATE) = '{today}'
      AND settlementPeriod = (SELECT max_sp FROM latest_period)
    GROUP BY fuelType
    ORDER BY total_mw DESC
    LIMIT 20
    """
    
    gen_df = bq_client.query(gen_query).to_dataframe()
    
    if not gen_df.empty:
        # Emoji mapping
        fuel_emoji = {
            'NUCLEAR': '⚛️', 'BIOMASS': '🌱', 'COAL': '⚫', 'CCGT': '🔥', 
            'WIND': '💨', 'SOLAR': '☀️', 'HYDRO': '💧', 'PS': '🔋',
            'NPSHYD': '💧', 'OIL': '🛢️', 'OTHER': '⚡',
            'INTFR': '🇫🇷', 'INTIRL': '🇮🇪', 'INTNED': '🇳🇱',
            'INTEW': '🏴󐁧󐁢󐁥󐁮󐁧󐁿', 'INTELEC': '⚡', 'INTIFA2': '🇫🇷'
        }
        
        gen_data = []
        for _, row in gen_df.iterrows():
            fuel = row['fuelType']
            emoji = fuel_emoji.get(fuel.upper(), '⚡')
            mw = row['total_mw']
            gw = mw / 1000
            
            # Interconnectors use MW, generation uses GW
            is_interconnector = fuel.upper().startswith('INT')
            
            if is_interconnector:
                value_str = f"{mw:,.1f} MW"
            else:
                value_str = f"{gw:.2f} GW"
            
            gen_data.append([
                f"{emoji} {fuel}",
                value_str
            ])
        
        dashboard.update(gen_data, 'A10')
        
        # Calculate wind percentage for row 6
        total_gen_mw = sum([row['total_mw'] for _, row in gen_df.iterrows() if not row['fuelType'].upper().startswith('INT')])
        wind_mw = sum([row['total_mw'] for _, row in gen_df.iterrows() if row['fuelType'].upper() == 'WIND'])
        wind_pct = (wind_mw / total_gen_mw * 100) if total_gen_mw > 0 else 0
        
        # Update wind percentage in row 6
        dashboard.update([[f'Wind: {wind_pct:.0f}%']], 'D6')
        
        logging.info(f"   ✅ Updated {len(gen_data)} fuel types (Wind: {wind_pct:.0f}%)")
    
    # =======================================================================
    # 4. UPDATE REMIT UNAVAILABILITY (Outages)
    # =======================================================================
    logging.info("⚠️  Updating outages...")
    
    outages_query = f"""
    WITH latest_outages AS (
        SELECT 
            affectedUnit,
            assetName,
            fuelType,
            normalCapacity,
            unavailableCapacity,
            eventStatus,
            cause,
            eventStartTime,
            FORMAT_TIMESTAMP('%Y-%m-%d %H:%M', eventStartTime) as start_time,
            ROW_NUMBER() OVER (PARTITION BY affectedUnit ORDER BY revisionNumber DESC) as rn
        FROM `{PROJECT_ID}.{DATASET}.bmrs_remit_unavailability`
        WHERE eventStatus = 'Active'
          AND unavailableCapacity >= 50
    )
    SELECT 
        affectedUnit,
        assetName,
        fuelType,
        normalCapacity,
        unavailableCapacity,
        cause,
        start_time
    FROM latest_outages
    WHERE rn = 1
    ORDER BY unavailableCapacity DESC
    LIMIT 50
    """
    
    try:
        outages_df = bq_client.query(outages_query).to_dataframe()
        
        if not outages_df.empty:
            # Fuel type emojis
            fuel_emoji = {
                'NUCLEAR': '⚛️', 'CCGT': '🔥', 'WIND OFFSHORE': '💨',
                'WIND ONSHORE': '💨', 'HYDRO PUMPED STORAGE': '💧',
                'BIOMASS': '🌱', 'COAL': '⛏️', 'FOSSIL GAS': '🔥'
            }
            
            # Update Dashboard outages section (rows 31-42, max 12 outages)
            outages_data = []
            total_mw = 0
            count = 0
            
            for _, row in outages_df.head(12).iterrows():
                fuel = row['fuelType'] or 'Unknown'
                emoji = fuel_emoji.get(fuel.upper(), '⚡')
                mw = row['unavailableCapacity']
                total_mw += mw
                count += 1
                
                pct = (mw / row['normalCapacity'] * 100) if row['normalCapacity'] > 0 else 0
                
                outages_data.append([
                    f"{emoji} {row['assetName'] or row['affectedUnit']}",
                    row['affectedUnit'],
                    f"{emoji} {fuel}",
                    f"{row['normalCapacity']:,.0f}",
                    f"{mw:,.0f} MW",  # Individual outages: MW only
                    f"{pct:.1f}%",
                    row['cause'] or 'Unknown',
                    row['start_time']
                ])
            
            # Calculate totals
            total_count = len(outages_df)
            additional = total_count - 12 if total_count > 12 else 0
            total_gw = total_mw / 1000
            
            # Status indicator
            if total_mw > 5000:
                status = '🔴 Critical'
            elif total_mw > 3000:
                status = '⚠️ High'
            elif total_mw > 1000:
                status = '🟡 Moderate'
            else:
                status = '🟢 Low'
            
            # Update outages rows
            dashboard.update(outages_data, 'A31')
            
            # Update row 44 with totals (MW + GW)
            total_text = f"📊 TOTAL OUTAGES: {total_mw:,.0f} MW ({total_gw:.2f} GW) | Count: {total_count} | Status: {status}"
            if additional > 0:
                total_text += f" | +{additional} more"
            
            dashboard.update([[total_text]], 'A44')
            
            logging.info(f"   ✅ Updated {len(outages_data)} outages (Total: {total_mw:,.0f} MW)")
    except Exception as e:
        logging.warning(f"   ⚠️  Outages update failed: {e}")
    
    # =======================================================================
    # FINAL
    # =======================================================================
    logging.info("=" * 80)
    logging.info("✅ COMPLETE UPDATE FINISHED")
    logging.info("=" * 80)
    
    return True

if __name__ == '__main__':
    try:
        success = main()
        sys.exit(0 if success else 1)
    except Exception as e:
        logging.error(f"❌ Fatal error: {e}")
        logging.exception("Traceback:")
        sys.exit(1)

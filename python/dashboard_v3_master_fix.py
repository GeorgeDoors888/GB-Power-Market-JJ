#!/usr/bin/env python3
"""
Dashboard V3 - MASTER FIX for ALL Issues

Fixes (runs every 15 min via cron):
1. ✅ Country flag emojis on interconnectors
2. ✅ TOP 15 outages only (deduplicated properly)
3. ✅ TOTAL row from ALL unique outages
4. ✅ Plant name lookup for BM units
5. ✅ % Lost calculation (vs 42 GW UK capacity)
6. ✅ Real data from IRIS + historical tables
"""

from google.oauth2 import service_account
from googleapiclient.discovery import build
from google.cloud import bigquery
import pandas as pd
from datetime import datetime
import sys

SPREADSHEET_ID = '1LmMq4OEE639Y-XXpOJ3xnvpAmHB6vUovh5g6gaU_vzc'
PROJECT_ID = "inner-cinema-476211-u9"
DATASET = "uk_energy_prod"
CREDS_FILE = '/Users/georgemajor/GB-Power-Market-JJ/inner-cinema-credentials.json'

# Emoji mapping for interconnectors
IC_EMOJI = {
    'INTFR': '🇫🇷 France (IFA)',
    'INTIFA2': '🇫🇷 France (IFA2)',
    'INTELEC': '🇧🇪 Belgium (IFA)',
    'INTNEM': '🇧🇪 Belgium (Nemo)',
    'INTNED': '🇳🇱 Netherlands',
    'INTNSL': '🇳🇴 Norway',
    'INTVKL': '🇩🇰 Denmark (Viking)',
    'INTIRL': '🇮🇪 Ireland (Moyle)',
    'INTGRNL': '🇮🇪 Ireland (Greenlink)',
    'INTEW': '🇮🇪 Ireland (EWIC)',
    'INTMOT': '🇬🇧 Isle of Man',
}

# Fuel type emoji mapping
FUEL_EMOJI = {
    'CCGT': '🔥 CCGT',
    'WIND': '💨 WIND',
    'NUCLEAR': '⚛️ NUCLEAR',
    'BIOMASS': '🌱 BIOMASS',
    'NPSHYD': '💧 NPSHYD',
    'OTHER': '⚙️ OTHER',
    'OCGT': '🔥 OCGT',
    'COAL': '⚫ COAL',
    'OIL': '🛢️ OIL',
    'PS': '⛰️ PS',  # Pumped Storage - water pumped uphill (can be negative when charging)
}


def get_clients():
    creds = service_account.Credentials.from_service_account_file(
        CREDS_FILE,
        scopes=[
            'https://www.googleapis.com/auth/spreadsheets',
            'https://www.googleapis.com/auth/bigquery'
        ]
    )
    sheets = build('sheets', 'v4', credentials=creds)
    bq = bigquery.Client(project=PROJECT_ID, credentials=creds, location="US")
    return sheets, bq


def refresh_fuel_mix_with_flags(sheets_service, bq_client):
    """Refresh fuel mix with EMOJI flags on interconnectors"""
    print("1️⃣  Refreshing Fuel Mix & ICs (with emojis)...")
    
    query = f"""
    WITH latest_data AS (
        SELECT fuelType, generation,
            ROW_NUMBER() OVER(PARTITION BY fuelType ORDER BY publishTime DESC) as rn
        FROM `{PROJECT_ID}.{DATASET}.bmrs_fuelinst_iris`
        WHERE publishTime > TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 30 MINUTE)
    )
    SELECT fuelType, generation FROM latest_data WHERE rn = 1 ORDER BY generation DESC
    """
    
    try:
        df = bq_client.query(query).to_dataframe()
        
        if df.empty:
            print("   ⚠️  No fuel data")
            return False
        
        total_gen = df['generation'].sum()
        df['pct'] = (df['generation'] / total_gen * 100).round(2)
        
        # Split fuel vs interconnectors
        fuel_df = df[~df['fuelType'].str.startswith('INT')].head(10)
        ic_df = df[df['fuelType'].str.startswith('INT')].copy()
        
        # Write fuel mix (A10:C19) - 10 rows with emojis
        fuel_values = []
        for _, row in fuel_df.iterrows():
            fuel_type = row['fuelType']
            fuel_name = FUEL_EMOJI.get(fuel_type, fuel_type)  # Add emoji or use plain name
            fuel_values.append([
                fuel_name, 
                round(row['generation']/1000, 2),  # GW
                f"{row['pct']:.2f}%"
            ])
        
        # Pad to 10 rows
        while len(fuel_values) < 10:
            fuel_values.append(['', '', ''])
        
        sheets_service.spreadsheets().values().update(
            spreadsheetId=SPREADSHEET_ID,
            range='Dashboard V3!A10:C19',
            valueInputOption='USER_ENTERED',
            body={'values': fuel_values}
        ).execute()
        
        # Write ICs with EMOJIS (D10:E18) - 9 rows
        ic_values = []
        for _, row in ic_df.head(9).iterrows():
            ic_code = row['fuelType']
            ic_name = IC_EMOJI.get(ic_code, ic_code)  # Get emoji name or fallback to code
            mw = int(row['generation'])
            ic_values.append([ic_name, mw])
        
        # Pad to 9 rows
        while len(ic_values) < 9:
            ic_values.append(['', ''])
        
        sheets_service.spreadsheets().values().update(
            spreadsheetId=SPREADSHEET_ID,
            range='Dashboard V3!D10:E18',
            valueInputOption='RAW',
            body={'values': ic_values}
        ).execute()
        
        print(f"   ✅ Updated {len(fuel_df)} fuels, {len(ic_values)} ICs with emojis")
        return True
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False


def refresh_outages_top15_with_total(sheets_service, bq_client):
    """
    TOP 15 CURRENTLY ACTIVE outages + TOTAL from ALL
    - Filter: eventEndTime > NOW (only show outages still active)
    - Proper deduplication: affectedUnit + eventStartTime + MAX(revisionNumber)
    - Plant name lookup from bmu_registration_data
    - % Lost vs REAL UK capacity from bmu_registration_data
    """
    print("2️⃣  Refreshing Outages (TOP 15 CURRENT + TOTAL)...")
    
    # Query 1: Get TOP 15 CURRENTLY ACTIVE outages with plant names
    # One row per BM unit showing their LATEST status
    query_top15 = f"""
    WITH uk_capacity AS (
        SELECT SUM(generationcapacity) as total_uk_mw
        FROM `{PROJECT_ID}.{DATASET}.bmu_registration_data`
        WHERE generationcapacity > 0
    ),
    latest_revisions AS (
        SELECT
            affectedUnit,
            MAX(revisionNumber) as max_revision,
            MAX(eventStartTime) as latest_event_start
        FROM `{PROJECT_ID}.{DATASET}.bmrs_remit_unavailability`
        WHERE eventStatus = 'Active'
          AND (normalCapacity - availableCapacity) >= 50
          AND eventEndTime > CURRENT_TIMESTAMP()
        GROUP BY affectedUnit
    ),
    current_outages AS (
        SELECT
            u.affectedUnit,
            u.eventStartTime,
            u.assetName,
            u.fuelType,
            u.normalCapacity,
            u.availableCapacity,
            (u.normalCapacity - u.availableCapacity) as unavailable_mw
        FROM `{PROJECT_ID}.{DATASET}.bmrs_remit_unavailability` u
        INNER JOIN latest_revisions lr
            ON u.affectedUnit = lr.affectedUnit
            AND u.revisionNumber = lr.max_revision
            AND u.eventStartTime = lr.latest_event_start
        WHERE u.eventStatus = 'Active'
          AND u.eventEndTime > CURRENT_TIMESTAMP()
    )
    SELECT
        c.affectedUnit as bm_unit,
        COALESCE(bmu.bmunitname, c.assetName, c.affectedUnit) as plant_name,
        c.fuelType as fuel_type,
        CAST(c.unavailable_mw AS INT64) as mw_lost,
        ROUND((c.unavailable_mw / uk.total_uk_mw) * 100, 2) as pct_lost,
        FORMAT_TIMESTAMP('%Y-%m-%d %H:%M', c.eventStartTime) as start_time
    FROM current_outages c
    CROSS JOIN uk_capacity uk
    LEFT JOIN `{PROJECT_ID}.{DATASET}.bmu_registration_data` bmu
        ON c.affectedUnit = bmu.elexonbmunit OR c.affectedUnit = bmu.nationalgridbmunit
    ORDER BY c.unavailable_mw DESC
    LIMIT 15
    """
    
    # Query 2: Get TOTAL from ALL CURRENTLY ACTIVE unique plants
    query_total = f"""
    WITH uk_capacity AS (
        SELECT SUM(generationcapacity) as total_uk_mw
        FROM `{PROJECT_ID}.{DATASET}.bmu_registration_data`
        WHERE generationcapacity > 0
    ),
    latest_revisions AS (
        SELECT
            affectedUnit,
            MAX(revisionNumber) as max_revision,
            MAX(eventStartTime) as latest_event_start
        FROM `{PROJECT_ID}.{DATASET}.bmrs_remit_unavailability`
        WHERE eventStatus = 'Active'
          AND (normalCapacity - availableCapacity) >= 50
          AND eventEndTime > CURRENT_TIMESTAMP()
        GROUP BY affectedUnit
    ),
    current_outages AS (
        SELECT
            u.affectedUnit,
            (u.normalCapacity - u.availableCapacity) as unavailable_mw
        FROM `{PROJECT_ID}.{DATASET}.bmrs_remit_unavailability` u
        INNER JOIN latest_revisions lr
            ON u.affectedUnit = lr.affectedUnit
            AND u.revisionNumber = lr.max_revision
            AND u.eventStartTime = lr.latest_event_start
        WHERE u.eventStatus = 'Active'
          AND u.eventEndTime > CURRENT_TIMESTAMP()
    )
    SELECT
        COUNT(DISTINCT affectedUnit) as outage_count,
        CAST(SUM(unavailable_mw) AS INT64) as total_mw,
        ROUND((SUM(unavailable_mw) / MAX(uk.total_uk_mw)) * 100, 2) as total_pct
    FROM current_outages
    CROSS JOIN uk_capacity uk
    """
    
    try:
        # Get TOP 15
        top15_df = bq_client.query(query_top15).to_dataframe()
        
        # Get TOTAL stats
        total_df = bq_client.query(query_total).to_dataframe()
        
        if top15_df.empty:
            print("   ⚠️  No active outages")
            # Clear outages section
            clear_values = [['', '', '', '', '', '']] * 18
            sheets_service.spreadsheets().values().update(
                spreadsheetId=SPREADSHEET_ID,
                range='Dashboard V3!A24:F41',
                valueInputOption='RAW',
                body={'values': clear_values}
            ).execute()
            return True
        
        # Build output rows
        rows = []
        
        # Row 1: Section header
        rows.append(['🚨 ACTIVE OUTAGES (TOP 15 by MW Lost)', '', '', '', '', ''])
        
        # Row 2: Column headers
        rows.append(['BM Unit', 'Plant Name', 'Fuel Type', 'MW Lost', '% Lost', 'Start Time'])
        
        # Rows 3-17: TOP 15 data (15 rows)
        for _, row in top15_df.iterrows():
            rows.append([
                row['bm_unit'],
                row['plant_name'],
                row['fuel_type'],
                int(row['mw_lost']),
                f"{row['pct_lost']:.2f}%",
                row['start_time']
            ])
        
        # Pad to 15 data rows if needed
        while len(rows) < 17:  # 1 header + 1 column headers + 15 data = 17
            rows.append(['', '', '', '', '', ''])
        
        # Row 18: Empty separator
        rows.append(['', '', '', '', '', ''])
        
        # Row 19: TOTAL row
        if not total_df.empty:
            outage_count = int(total_df.iloc[0]['outage_count'])
            total_mw = int(total_df.iloc[0]['total_mw'])
            total_pct = float(total_df.iloc[0]['total_pct'])
            
            rows.append([
                '═══════════',
                f'TOTAL UNAVAILABLE ({outage_count} outages)',
                '═══════════',
                total_mw,
                f"{total_pct:.2f}%",
                ''
            ])
        else:
            rows.append(['═══════════', 'TOTAL UNAVAILABLE', '═══════════', 0, '0.00%', ''])
        
        # Write all rows (A22:F40 = 19 rows)
        sheets_service.spreadsheets().values().update(
            spreadsheetId=SPREADSHEET_ID,
            range='Dashboard V3!A22:F40',
            valueInputOption='USER_ENTERED',
            body={'values': rows}
        ).execute()
        
        outage_count = int(total_df.iloc[0]['outage_count']) if not total_df.empty else 0
        total_mw = int(total_df.iloc[0]['total_mw']) if not total_df.empty else 0
        total_pct = float(total_df.iloc[0]['total_pct']) if not total_df.empty else 0
        
        print(f"   ✅ Updated TOP 15 outages + TOTAL ({outage_count} outages, {total_mw:,} MW = {total_pct:.2f}% of UK capacity)")
        return True
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def refresh_vlp_data(sheets_service, bq_client):
    """Refresh VLP_Data sheet with latest balancing actions"""
    print("3️⃣  Refreshing VLP_Data...")
    
    query = f"""
    WITH combined_actions AS (
        SELECT
            DATE(settlementDate) as date,
            bmUnit,
            soFlag, storFlag, rrFlag
        FROM `{PROJECT_ID}.{DATASET}.bmrs_boalf_iris`
        WHERE settlementDate >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)
        
        UNION ALL
        
        SELECT
            DATE(settlementDate) as date,
            bmUnit,
            soFlag, storFlag, rrFlag
        FROM `{PROJECT_ID}.{DATASET}.bmrs_boalf`
        WHERE settlementDate >= '2025-10-01'
          AND settlementDate < DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)
    )
    SELECT
        date,
        COUNT(*) as total_actions,
        SUM(CASE WHEN soFlag OR storFlag OR rrFlag THEN 1 ELSE 0 END) as vlp_actions,
        SUM(CASE WHEN soFlag THEN 1 ELSE 0 END) as so_flag_count
    FROM combined_actions
    GROUP BY date
    ORDER BY date DESC
    LIMIT 30
    """
    
    try:
        df = bq_client.query(query).to_dataframe()
        
        if df.empty:
            print("   ⚠️  No VLP data")
            return True
        
        df['date'] = pd.to_datetime(df['date']).dt.strftime('%Y-%m-%d')
        
        header = [['Date', 'Total Actions', 'VLP Actions', 'Total MW']]
        values = header + [[row['date'], int(row['total_actions']), int(row['vlp_actions']), 0] 
                          for _, row in df.iterrows()]
        
        sheets_service.spreadsheets().values().update(
            spreadsheetId=SPREADSHEET_ID,
            range='VLP_Data!A1',
            valueInputOption='RAW',
            body={'values': values}
        ).execute()
        
        print(f"   ✅ Updated {len(df)} rows")
        return True
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False


def refresh_market_prices(sheets_service, bq_client):
    """Refresh Market_Prices with IRIS + historic data"""
    print("4️⃣  Refreshing Market_Prices...")
    
    query = f"""
    WITH combined_prices AS (
        SELECT
            DATE(settlementDate) as date,
            price
        FROM `{PROJECT_ID}.{DATASET}.bmrs_mid_iris`
        WHERE settlementDate >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)
        
        UNION ALL
        
        SELECT
            DATE(settlementDate) as date,
            price
        FROM `{PROJECT_ID}.{DATASET}.bmrs_mid`
        WHERE settlementDate >= '2025-10-01'
          AND settlementDate < DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)
    )
    SELECT
        date,
        ROUND(AVG(price), 2) as avg_price,
        ROUND(MIN(price), 2) as min_price,
        ROUND(MAX(price), 2) as max_price,
        ROUND(STDDEV(price), 2) as volatility,
        COUNT(*) as volume
    FROM combined_prices
    GROUP BY date
    ORDER BY date DESC
    LIMIT 30
    """
    
    try:
        df = bq_client.query(query).to_dataframe()
        
        if df.empty:
            print("   ⚠️  No price data")
            return True
        
        df['date'] = pd.to_datetime(df['date']).dt.strftime('%Y-%m-%d')
        df = df.fillna(0)
        
        header = [['Date', 'Avg Price (£/MWh)', 'Min Price', 'Max Price', 'Volatility', 'Volume (MWh)']]
        values = header + df.values.tolist()
        
        sheets_service.spreadsheets().values().update(
            spreadsheetId=SPREADSHEET_ID,
            range='Market_Prices!A1',
            valueInputOption='RAW',
            body={'values': values}
        ).execute()
        
        print(f"   ✅ Updated {len(df)} rows")
        return True
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False


def refresh_balancing_summary(sheets_service, bq_client):
    """Add compact BOD/BOALF summary to Dashboard V3 - STATISTICS ONLY"""
    print("6️⃣  Refreshing Balancing Market Summary (BOD/BOALF)...")
    
    try:
        # Query: Last 7 days BOALF summary (accepted volumes)
        boalf_query = f"""
        SELECT
            COUNT(DISTINCT acceptanceNumber) as total_actions,
            COUNT(DISTINCT bmUnit) as active_units,
            SUM(CASE WHEN levelTo > levelFrom THEN (levelTo - levelFrom) ELSE 0 END) as increase_mw,
            SUM(CASE WHEN levelTo < levelFrom THEN ABS(levelTo - levelFrom) ELSE 0 END) as decrease_mw,
            AVG(ABS(levelTo - levelFrom)) as avg_volume_change
        FROM `{PROJECT_ID}.{DATASET}.bmrs_boalf`
        WHERE settlementDate >= DATE_SUB(DATE('2025-10-28'), INTERVAL 7 DAY)
        """
        
        # Query: Last 7 days BOD price statistics (filter out sentinel values)
        bod_query = f"""
        SELECT
            COUNT(DISTINCT bmUnit) as units_submitting,
            COUNT(DISTINCT pairId) as bid_offer_pairs,
            AVG(CASE WHEN bid > 0 AND bid < 9999 THEN bid END) as avg_bid_price,
            AVG(CASE WHEN offer > 0 AND offer < 9999 THEN offer END) as avg_offer_price,
            AVG(CASE 
              WHEN bid > 0 AND bid < 9999 
              AND offer > 0 AND offer < 9999 
              THEN offer - bid 
            END) as avg_spread
        FROM `{PROJECT_ID}.{DATASET}.bmrs_bod`
        WHERE settlementDate >= DATE_SUB(DATE('2025-10-28'), INTERVAL 7 DAY)
        """
        
        boalf_df = bq_client.query(boalf_query).to_dataframe()
        bod_df = bq_client.query(bod_query).to_dataframe()
        
        # Build compact summary for Dashboard V3
        rows = []
        
        # Row 1: Section header (A42:F42)
        rows.append(['', '', '', '', '', ''])
        rows.append(['⚡ BALANCING MARKET SUMMARY (Last 7 Days)', '', '', '', '', ''])
        
        # BOALF + BOD Statistics
        boalf_row = boalf_df.iloc[0]
        bod_row = bod_df.iloc[0] if not bod_df.empty else None
        
        summary_section = [
            ['📊 ACCEPTED ACTIONS (BOALF)', '', '', '📝 SUBMITTED PRICES (BOD)', '', ''],
            ['Total Actions:', f"{int(boalf_row['total_actions']):,}", '', 'Units Submitting:', int(bod_row['units_submitting']) if bod_row is not None else 'N/A', ''],
            ['Active Units:', int(boalf_row['active_units']), '', 'Bid-Offer Pairs:', f"{int(bod_row['bid_offer_pairs']):,}" if bod_row is not None else 'N/A', ''],
            ['Increase MW:', f"{int(boalf_row['increase_mw']):,}", '', 'Avg Bid Price:', f"£{bod_row['avg_bid_price']:.2f}/MWh" if bod_row is not None and pd.notna(bod_row['avg_bid_price']) else 'N/A', ''],
            ['Decrease MW:', f"{int(boalf_row['decrease_mw']):,}", '', 'Avg Offer Price:', f"£{bod_row['avg_offer_price']:.2f}/MWh" if bod_row is not None and pd.notna(bod_row['avg_offer_price']) else 'N/A', ''],
            ['Avg Change:', f"{boalf_row['avg_volume_change']:.1f} MW" if pd.notna(boalf_row['avg_volume_change']) else 'N/A', '', 'Avg Spread:', f"£{bod_row['avg_spread']:.2f}/MWh" if bod_row is not None and pd.notna(bod_row['avg_spread']) else 'N/A', '']
        ]
        rows.extend(summary_section)
        
        # Write to Dashboard V3 (below outages section)
        sheets_service.spreadsheets().values().update(
            spreadsheetId=SPREADSHEET_ID,
            range='Dashboard V3!A41:F48',
            valueInputOption='USER_ENTERED',
            body={'values': rows}
        ).execute()
        
        print(f"   ✅ Updated balancing summary: {int(boalf_row['total_actions']):,} actions, {int(bod_row['bid_offer_pairs']) if bod_row is not None else 0:,} price pairs")
        return True
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False


def main():
    print(f"🔄 Dashboard V3 Master Fix - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)
    
    sheets_service, bq_client = get_clients()
    
    success = True
    success &= refresh_fuel_mix_with_flags(sheets_service, bq_client)
    success &= refresh_outages_top15_with_total(sheets_service, bq_client)
    success &= refresh_vlp_data(sheets_service, bq_client)
    success &= refresh_market_prices(sheets_service, bq_client)
    success &= refresh_balancing_summary(sheets_service, bq_client)
    
    print("="*80)
    if success:
        print("✅ Dashboard V3 refresh complete")
    else:
        print("⚠️  Dashboard V3 refresh completed with errors")
    
    return 0 if success else 1


if __name__ == '__main__':
    sys.exit(main())

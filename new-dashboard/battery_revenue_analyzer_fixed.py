#!/usr/bin/env python3
"""
Battery Revenue Opportunity Analysis
=====================================
Analyzes BOALF acceptance data for battery units and matches with market prices
to estimate revenue opportunities. Integrates with Dashboard V2.

Data Sources:
- bmrs_boalf: Historical acceptances (2022-present)
- bmrs_boalf_iris: Real-time acceptances (last 22 days)
- bmrs_mid: Market Index Data (MID) prices

Author: GB Power Market JJ
Created: November 2025
"""

import logging
from datetime import datetime, timedelta
from google.cloud import bigquery
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# Configuration
PROJECT_ID = "inner-cinema-476211-u9"
DATASET = "uk_energy_prod"
LOCATION = "US"
CREDENTIALS_PATH = "/Users/georgemajor/GB Power Market JJ/inner-cinema-credentials.json"
DASHBOARD_SPREADSHEET_ID = "1LmMq4OEE639Y-XXpOJ3xnvpAmHB6vUovh5g6gaU_vzc"
BATTERY_ANALYSIS_SHEET = "Battery Revenue Analysis"

# Battery BM Units to track (identified from BOALF data)
BATTERY_UNITS = [
    'FBPGM002',      # Flexgen battery
    'FFSEN005',      # Battery (likely Gresham House/Harmony Energy)
    '2__DSTAT002',   # Battery unit
    '2__DSTAT004',   # Battery unit
    '2__GSTAT011',   # Battery unit
    '2__HANGE001',   # Hanger Lane battery
    '2__HANGE002',   # Hanger Lane battery
    '2__HANGE004',   # Hanger Lane battery
    '2__MSTAT001',   # Battery unit
    '2__NFLEX001',   # Battery unit
    '2__HLOND002',   # Battery unit
    '2__LANGE002'    # Battery unit
]

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

def connect_bigquery():
    """Connect to BigQuery with service account credentials"""
    from google.oauth2 import service_account
    
    credentials = service_account.Credentials.from_service_account_file(
        CREDENTIALS_PATH,
        scopes=["https://www.googleapis.com/auth/bigquery"]
    )
    
    client = bigquery.Client(
        project=PROJECT_ID, 
        location=LOCATION,
        credentials=credentials
    )
    logging.info(f"✅ Connected to BigQuery: {PROJECT_ID}.{DATASET}")
    return client

def connect_sheets():
    """Connect to Google Sheets with service account credentials"""
    scope = [
        'https://spreadsheets.google.com/feeds',
        'https://www.googleapis.com/auth/drive'
    ]
    credentials = ServiceAccountCredentials.from_json_keyfile_name(
        CREDENTIALS_PATH, scope
    )
    client = gspread.authorize(credentials)
    sheet = client.open_by_key(DASHBOARD_SPREADSHEET_ID)
    logging.info(f"✅ Connected to Google Sheets: {DASHBOARD_SPREADSHEET_ID}")
    return sheet

def analyze_battery_acceptances_today(bq_client):
    """
    Analyze today's battery acceptances with market price matching
    
    NOTE: Using bmrs_mid.price which represents Market Index Data (MID) price.
    This is a simplified revenue estimate. For actual balancing mechanism revenues,
    would need acceptance-specific prices (BOALF doesn't include price, only volume).
    
    Returns: DataFrame with acceptance details + matched market prices
    """
    query = f"""
    WITH todays_acceptances AS (
      SELECT 
        settlementDate,
        settlementPeriodFrom,
        bmUnit,
        acceptanceNumber,
        acceptanceTime,
        levelFrom,
        levelTo,
        (levelTo - levelFrom) as volume_mw,
        soFlag,
        storFlag,
        rrFlag
      FROM `{PROJECT_ID}.{DATASET}.bmrs_boalf_iris`
      WHERE CAST(settlementDate AS DATE) = CURRENT_DATE()
        AND bmUnit IN UNNEST(@battery_units)
      ORDER BY acceptanceTime DESC
    ),
    matched_prices AS (
      SELECT 
        a.*,
        apx.price as apx_price_gbp_mwh,
        apx.volume as apx_volume,
        n2ex.price as n2ex_price_gbp_mwh,
        -- Use APXMIDP for revenue calculations (active UK market price)
        CASE 
          WHEN a.volume_mw > 0 THEN a.volume_mw * apx.price / 2  -- Discharge revenue
          WHEN a.volume_mw < 0 THEN a.volume_mw * apx.price / 2  -- Charge cost (negative)
          ELSE 0
        END as estimated_value_gbp
      FROM todays_acceptances a
      LEFT JOIN (
        SELECT settlementDate, settlementPeriod, price, volume
        FROM `{PROJECT_ID}.{DATASET}.bmrs_mid_iris`
        WHERE dataProvider = 'APXMIDP'
      ) apx
        ON CAST(a.settlementDate AS DATE) = CAST(apx.settlementDate AS DATE)
        AND a.settlementPeriodFrom = apx.settlementPeriod
      LEFT JOIN (
        SELECT settlementDate, settlementPeriod, price
        FROM `{PROJECT_ID}.{DATASET}.bmrs_mid_iris`
        WHERE dataProvider = 'N2EXMIDP'
      ) n2ex
        ON CAST(a.settlementDate AS DATE) = CAST(n2ex.settlementDate AS DATE)
        AND a.settlementPeriodFrom = n2ex.settlementPeriod
    )
    SELECT * FROM matched_prices
    ORDER BY acceptanceTime DESC
    """
    
    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ArrayQueryParameter("battery_units", "STRING", BATTERY_UNITS)
        ]
    )
    
    df = bq_client.query(query, job_config=job_config).to_dataframe()
    logging.info(f"📊 Retrieved {len(df)} battery acceptances today")
    
    return df

def analyze_historical_battery_revenue(bq_client, days_back=30):
    """
    Analyze historical battery revenue opportunities with daily aggregation
    
    Combines:
    - Historical bmrs_boalf (before IRIS coverage)
    - Real-time bmrs_boalf_iris (last 22 days)
    - Market prices from bmrs_mid
    
    Returns: DataFrame with daily aggregated revenue metrics
    """
    query = f"""
    WITH combined_acceptances AS (
      -- Historical data (before IRIS coverage starts)
      SELECT 
        CAST(settlementDate AS DATE) as date,
        settlementPeriodFrom as settlement_period,
        bmUnit,
        acceptanceNumber,
        levelFrom,
        levelTo,
        (levelTo - levelFrom) as volume_mw,
        soFlag,
        storFlag
      FROM `{PROJECT_ID}.{DATASET}.bmrs_boalf`
      WHERE bmUnit IN UNNEST(@battery_units)
        AND CAST(settlementDate AS DATE) >= DATE_SUB(CURRENT_DATE(), INTERVAL @days_back DAY)
        AND CAST(settlementDate AS DATE) < '2025-11-04'  -- IRIS starts Nov 4
      
      UNION ALL
      
      -- IRIS real-time data (last 22 days)
      SELECT 
        CAST(settlementDate AS DATE) as date,
        settlementPeriodFrom as settlement_period,
        bmUnit,
        acceptanceNumber,
        levelFrom,
        levelTo,
        (levelTo - levelFrom) as volume_mw,
        soFlag,
        storFlag
      FROM `{PROJECT_ID}.{DATASET}.bmrs_boalf_iris`
      WHERE bmUnit IN UNNEST(@battery_units)
        AND CAST(settlementDate AS DATE) >= DATE_SUB(CURRENT_DATE(), INTERVAL @days_back DAY)
        AND CAST(settlementDate AS DATE) >= '2025-11-04'
    ),
    matched_with_prices AS (
      SELECT 
        a.date,
        a.settlement_period,
        a.bmUnit,
        a.volume_mw,
        m.price as market_price,
        -- Revenue calculation using APXMIDP market index price only
        CASE 
          WHEN a.volume_mw > 0 THEN a.volume_mw * m.price / 2  -- Discharge
          WHEN a.volume_mw < 0 THEN a.volume_mw * m.price / 2  -- Charge (negative = cost)
          ELSE 0
        END as estimated_value_gbp,
        CASE 
          WHEN a.volume_mw > 0 THEN 'DISCHARGE'
          WHEN a.volume_mw < 0 THEN 'CHARGE'
          ELSE 'NEUTRAL'
        END as action
      FROM combined_acceptances a
      LEFT JOIN (
        -- Historical prices
        SELECT settlementDate, settlementPeriod, price
        FROM `{PROJECT_ID}.{DATASET}.bmrs_mid`
        WHERE dataProvider = 'APXMIDP'
          AND CAST(settlementDate AS DATE) < '2025-11-04'
        
        UNION ALL
        
        -- IRIS real-time prices
        SELECT settlementDate, settlementPeriod, price
        FROM `{PROJECT_ID}.{DATASET}.bmrs_mid_iris`
        WHERE dataProvider = 'APXMIDP'
          AND CAST(settlementDate AS DATE) >= '2025-11-04'
      ) m
        ON a.date = CAST(m.settlementDate AS DATE)
        AND a.settlement_period = m.settlementPeriod
    ),
    daily_summary AS (
      SELECT 
        date,
        COUNT(*) as total_acceptances,
        SUM(CASE WHEN action = 'DISCHARGE' THEN 1 ELSE 0 END) as discharge_count,
        SUM(CASE WHEN action = 'CHARGE' THEN 1 ELSE 0 END) as charge_count,
        SUM(ABS(volume_mw)) as total_volume_mw,
        AVG(market_price) as avg_market_price_gbp_mwh,
        SUM(estimated_value_gbp) as daily_net_value_gbp,
        COUNT(DISTINCT bmUnit) as active_units
      FROM matched_with_prices
      GROUP BY date
    )
    SELECT * FROM daily_summary
    ORDER BY date DESC
    """
    
    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ArrayQueryParameter("battery_units", "STRING", BATTERY_UNITS),
            bigquery.ScalarQueryParameter("days_back", "INT64", days_back)
        ]
    )
    
    df = bq_client.query(query, job_config=job_config).to_dataframe()
    logging.info(f"📈 Retrieved {len(df)} days of historical battery data")
    
    return df

def get_vlp_ownership(bq_client):
    """
    Get VLP (Virtual Lead Party) ownership information for battery units
    
    Returns: Dict mapping bm_unit to vlp_name
    """
    query = f"""
    SELECT bm_unit, vlp_name
    FROM `{PROJECT_ID}.{DATASET}.vlp_unit_ownership`
    """
    
    try:
        df = bq_client.query(query).to_dataframe()
        vlp_map = dict(zip(df['bm_unit'], df['vlp_name']))
        logging.info(f"📋 Retrieved VLP ownership for {len(vlp_map)} units")
        return vlp_map
    except Exception as e:
        logging.warning(f"⚠️ Could not fetch VLP data: {e}")
        return {}

def analyze_unit_performance(bq_client, days_back=30):
    """
    Analyze performance by individual battery unit
    
    Returns: DataFrame with per-unit metrics (acceptances, volume, estimated value)
    """
    query = f"""
    WITH combined_acceptances AS (
      -- Historical
      SELECT 
        bmUnit,
        CAST(settlementDate AS DATE) as date,
        settlementPeriodFrom as period,
        (levelTo - levelFrom) as volume_mw,
        soFlag
      FROM `{PROJECT_ID}.{DATASET}.bmrs_boalf`
      WHERE CAST(settlementDate AS DATE) >= DATE_SUB(CURRENT_DATE(), INTERVAL @days_back DAY)
        AND bmUnit IN UNNEST(@battery_units)
        AND CAST(settlementDate AS DATE) < '2025-11-04'
      
      UNION ALL
      
      -- IRIS
      SELECT 
        bmUnit,
        CAST(settlementDate AS DATE) as date,
        settlementPeriodFrom as period,
        (levelTo - levelFrom) as volume_mw,
        soFlag
      FROM `{PROJECT_ID}.{DATASET}.bmrs_boalf_iris`
      WHERE CAST(settlementDate AS DATE) >= DATE_SUB(CURRENT_DATE(), INTERVAL @days_back DAY)
        AND bmUnit IN UNNEST(@battery_units)
        AND CAST(settlementDate AS DATE) >= '2025-11-04'
    ),
    matched_data AS (
      SELECT 
        a.bmUnit,
        a.date,
        a.volume_mw,
        m.price as market_price,
        CASE 
          WHEN a.volume_mw > 0 THEN a.volume_mw * m.price / 2
          WHEN a.volume_mw < 0 THEN a.volume_mw * m.price / 2
          ELSE 0
        END as estimated_value_gbp,
        a.soFlag
      FROM combined_acceptances a
      LEFT JOIN (
        SELECT settlementDate, settlementPeriod, price
        FROM `{PROJECT_ID}.{DATASET}.bmrs_mid`
        WHERE dataProvider = 'APXMIDP'
      ) m
        ON a.date = CAST(m.settlementDate AS DATE)
        AND a.period = m.settlementPeriod
    ),
    unit_summary AS (
      SELECT 
        bmUnit,
        COUNT(*) as total_acceptances,
        SUM(CASE WHEN volume_mw > 0 THEN 1 ELSE 0 END) as discharge_actions,
        SUM(CASE WHEN volume_mw < 0 THEN 1 ELSE 0 END) as charge_actions,
        SUM(ABS(volume_mw)) as total_volume_mw,
        AVG(ABS(volume_mw)) as avg_volume_per_acceptance,
        SUM(estimated_value_gbp) as total_estimated_value_gbp,
        SUM(CASE WHEN soFlag THEN 1 ELSE 0 END) as so_flag_count,
        COUNT(DISTINCT date) as days_active,
        MIN(date) as first_activity,
        MAX(date) as last_activity
      FROM matched_data
      GROUP BY bmUnit
    )
    SELECT * FROM unit_summary
    ORDER BY total_estimated_value_gbp DESC
    """
    
    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ArrayQueryParameter("battery_units", "STRING", BATTERY_UNITS),
            bigquery.ScalarQueryParameter("days_back", "INT64", days_back)
        ]
    )
    
    df = bq_client.query(query, job_config=job_config).to_dataframe()
    logging.info(f"⚡ Retrieved performance metrics for {len(df)} battery units")
    
    return df

def create_battery_analysis_sheet(sheets_client):
    """
    Create Battery Revenue Analysis sheet in Dashboard V2
    
    Layout:
    - Row 1-3: Header and KPIs
    - Row 5+: Today's Acceptances table (15 rows)
    - Row 25+: 7-Week Historical Trend table (50 rows for 49 days)
    - Row 80+: Unit Performance table
    """
    try:
        # Check if sheet exists
        try:
            sheet = sheets_client.worksheet(BATTERY_ANALYSIS_SHEET)
            logging.info(f"✅ Sheet '{BATTERY_ANALYSIS_SHEET}' already exists")
            return sheet
        except gspread.exceptions.WorksheetNotFound:
            pass
        
        # Create new sheet
        sheet = sheets_client.add_worksheet(
            title=BATTERY_ANALYSIS_SHEET,
            rows=150,
            cols=15
        )
        
        # Set up header
        sheet.update([[
            'Battery Revenue Analysis - BOALF Acceptances & Market Prices',
            '', '', '', '', '', '', '', '', '', '', '', '', '', ''
        ]], 'A1:O1')
        
        # Format header
        sheet.format('A1:O1', {
            'backgroundColor': {'red': 0.2, 'green': 0.3, 'blue': 0.5},
            'textFormat': {'foregroundColor': {'red': 1, 'green': 1, 'blue': 1}, 'bold': True, 'fontSize': 14},
            'horizontalAlignment': 'CENTER'
        })
        
        # Add section headers
        sheet.update([["Today's Battery Acceptances"]], 'A3')
        sheet.update([["7-Week Revenue Trend (49 days)"]], 'A25')
        sheet.update([["Unit Performance Summary"]], 'A80')
        
        logging.info(f"✅ Created sheet: {BATTERY_ANALYSIS_SHEET}")
        return sheet
        
    except Exception as e:
        logging.error(f"❌ Failed to create sheet: {e}")
        raise

def update_battery_analysis_sheet(sheets_client, today_df, historical_df, unit_df):
    """
    Update Battery Revenue Analysis sheet with latest data
    
    Args:
        sheets_client: gspread client
        today_df: Today's acceptances DataFrame
        historical_df: Historical trend DataFrame
        unit_df: Unit performance DataFrame
    """
    try:
        sheet = sheets_client.worksheet(BATTERY_ANALYSIS_SHEET)
        
        # Update KPIs (Row 2)
        if not today_df.empty:
            total_acceptances = len(today_df)
            total_volume = today_df['volume_mw'].abs().sum()
            avg_apx_price = today_df['apx_price_gbp_mwh'].mean()
            total_value = today_df['estimated_value_gbp'].sum()
        else:
            total_acceptances = 0
            total_volume = 0
            avg_apx_price = 0
            total_value = 0
        
        sheet.update([[
            f"Today's Acceptances: {total_acceptances}",
            f"Total Volume: {total_volume:.1f} MW",
            f"APX Price Avg: £{avg_apx_price:.2f}/MWh",
            f"Estimated Net Value: £{total_value:.2f}"
        ]], 'A2:D2')
        
        # Today's Acceptances Table (starting row 4)
        if not today_df.empty:
            # Clear old today's data (rows 3-22)
            sheet.batch_clear(['A3:L22'])
            
            # Section header
            sheet.update([["Today's Battery Acceptances"]], 'A3')
            
            # Headers
            sheet.update([[
                'Time', 'BM Unit', 'Accept #', 'Level From', 'Level To', 
                'Volume (MW)', 'APX Price', 'N2EX Price', 'Est. Value', 'SO Flag', 'STOR Flag', 'RR Flag'
            ]], 'A4:L4')
            
            # Add cell notes to explain columns
            sheet.update_note('C4', 'Unique acceptance ID from National Grid')
            sheet.update_note('D4', 'Starting power level (MW). Negative=charging, Positive=discharging')
            sheet.update_note('E4', 'Target power level (MW). Negative=charge, Positive=discharge')
            sheet.update_note('F4', 'Power change = ABS(Level To - Level From)')
            sheet.update_note('G4', 'System Sell Price - what you earn when discharging')
            sheet.update_note('H4', 'System Buy Price - what you pay when charging')
            sheet.update_note('I4', 'Revenue = Volume × Price × 0.5 hours. Negative=cost, Positive=income')
            sheet.update_note('J4', 'System Operator action (1=grid stability/constraints, pays premium). Target: 5-10%')
            sheet.update_note('K4', 'Short Term Operating Reserve (legacy service being phased out)')
            sheet.update_note('L4', 'Response & Reserve service dispatch')
            
            # Data (limit to 15 most recent)
            data_rows = []
            for _, row in today_df.head(15).iterrows():
                data_rows.append([
                    str(row['acceptanceTime']),
                    row['bmUnit'],
                    row['acceptanceNumber'],
                    f"{row['levelFrom']:.1f}",
                    f"{row['levelTo']:.1f}",
                    f"{row['volume_mw']:.1f}",
                    f"£{row['apx_price_gbp_mwh']:.2f}" if pd.notna(row['apx_price_gbp_mwh']) else 'N/A',
                    f"£{row['n2ex_price_gbp_mwh']:.2f}" if pd.notna(row['n2ex_price_gbp_mwh']) and row['n2ex_price_gbp_mwh'] > 0 else '£0.00',
                    f"£{row['estimated_value_gbp']:.2f}" if pd.notna(row['estimated_value_gbp']) else 'N/A',
                    'Yes' if row['soFlag'] else 'No',
                    'Yes' if row['storFlag'] else 'No',
                    'Yes' if row['rrFlag'] else 'No'
                ])
            
            sheet.update(data_rows, f'A5:L{4+len(data_rows)}')
        
        # 7-Week Historical Trend (starting row 26)
        if not historical_df.empty:
            # Clear old data in historical section (rows 25-75)
            sheet.batch_clear(['A25:H75'])
            
            # Section header
            sheet.update([["7-Week Revenue Trend (49 days)"]], 'A25')
            
            # Column headers
            sheet.update([[
                'Date', 'Acceptances', 'Discharge', 'Charge', 
                'Volume (MW)', 'Avg Price', 'Net Value (£)', 'Active Units'
            ]], 'A26:H26')
            
            # Historical data rows
            data_rows = []
            for _, row in historical_df.iterrows():
                data_rows.append([
                    str(row['date']),
                    int(row['total_acceptances']),
                    int(row['discharge_count']),
                    int(row['charge_count']),
                    f"{row['total_volume_mw']:.1f}",
                    f"£{row['avg_market_price_gbp_mwh']:.2f}" if pd.notna(row['avg_market_price_gbp_mwh']) else 'N/A',
                    f"£{row['daily_net_value_gbp']:.2f}" if pd.notna(row['daily_net_value_gbp']) else 'N/A',
                    int(row['active_units'])
                ])
            
            logging.info(f"📝 Writing {len(data_rows)} historical days to rows 27-{26+len(data_rows)}")
            sheet.update(data_rows, f'A27:H{26+len(data_rows)}')
        
        # Unit Performance Summary (starting row 81)
        if not unit_df.empty:
            # Clear old unit performance data (rows 80-95)
            sheet.batch_clear(['A80:L95'])
            
            # Section header
            sheet.update([["Unit Performance Summary"]], 'A80')
            
            sheet.update([[
                'BM Unit', 'VLP Owner', 'Acceptances', 'Discharge', 'Charge', 'Total Vol (MW)',
                'Avg Vol/Accept', 'Est. Value (£)', 'SO Flags', 'Days Active', 'First', 'Last'
            ]], 'A81:L81')
            
            data_rows = []
            for _, row in unit_df.iterrows():
                data_rows.append([
                    row['bmUnit'],
                    row.get('vlp_owner', 'Direct BM Unit'),
                    int(row['total_acceptances']),
                    int(row['discharge_actions']),
                    int(row['charge_actions']),
                    f"{row['total_volume_mw']:.1f}",
                    f"{row['avg_volume_per_acceptance']:.1f}",
                    f"£{row['total_estimated_value_gbp']:.2f}" if pd.notna(row['total_estimated_value_gbp']) else 'N/A',
                    int(row['so_flag_count']),
                    int(row['days_active']),
                    str(row['first_activity']),
                    str(row['last_activity'])
                ])
            
            sheet.update(data_rows, f'A82:L{81+len(data_rows)}')
        
        # Update timestamp
        sheet.update([[f"Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"]],  'M1')
        
        logging.info(f"✅ Updated {BATTERY_ANALYSIS_SHEET} sheet successfully")
        
    except Exception as e:
        logging.error(f"❌ Failed to update sheet: {e}")
        raise

def main():
    """
    Main execution flow:
    1. Connect to BigQuery and Google Sheets
    2. Analyze today's battery acceptances
    3. Analyze 30-day historical trend
    4. Analyze unit performance
    5. Update Dashboard V2 sheet
    """
    try:
        logging.info("="*60)
        logging.info("🔋 Battery Revenue Analysis - Starting...")
        logging.info("="*60)
        
        # Connect to services
        bq_client = connect_bigquery()
        sheets_client = connect_sheets()
        
        # Run analyses
        logging.info("\n📊 Analyzing today's battery acceptances...")
        today_df = analyze_battery_acceptances_today(bq_client)
        
        logging.info("\n📈 Analyzing 49-day (7 weeks) historical trend...")
        historical_df = analyze_historical_battery_revenue(bq_client, days_back=49)
        
        logging.info("\n⚡ Analyzing unit performance (7 weeks)...")
        unit_df = analyze_unit_performance(bq_client, days_back=49)
        
        logging.info("\n📋 Fetching VLP ownership data...")
        vlp_map = get_vlp_ownership(bq_client)
        
        # Add VLP info to unit dataframe
        unit_df['vlp_owner'] = unit_df['bmUnit'].map(vlp_map).fillna('Direct BM Unit')
        
        # Create/update sheet
        logging.info("\n📝 Updating Dashboard V2...")
        create_battery_analysis_sheet(sheets_client)
        update_battery_analysis_sheet(sheets_client, today_df, historical_df, unit_df)
        
        # Summary
        logging.info("\n" + "="*60)
        logging.info("✅ Battery Revenue Analysis Complete!")
        logging.info("="*60)
        logging.info(f"Today's Acceptances: {len(today_df)}")
        logging.info(f"Historical Days: {len(historical_df)}")
        logging.info(f"Battery Units Tracked: {len(unit_df)}")
        logging.info(f"Dashboard: https://docs.google.com/spreadsheets/d/{DASHBOARD_SPREADSHEET_ID}")
        logging.info("="*60)
        
    except Exception as e:
        logging.error(f"❌ Analysis failed: {e}")
        raise

if __name__ == "__main__":
    main()

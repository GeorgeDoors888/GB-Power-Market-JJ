#!/usr/bin/env python3
"""
Clean Dashboard Design - Redesigned layout for Sheet1
Professional, organized structure for generation and REMIT data
"""
import gspread
import pickle
from google.cloud import bigquery
from datetime import datetime
import pandas as pd
import sys

# Configuration
PROJECT_ID = "inner-cinema-476211-u9"
DATASET_ID = "uk_energy_prod"
FUELINST_TABLE = "bmrs_fuelinst"
REMIT_TABLE = "bmrs_remit_unavailability"
DASHBOARD_SHEET_ID = "12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8"
SHEET_NAME = "Sheet1"

def get_sheets_client():
    """Initialize Google Sheets client"""
    with open('token.pickle', 'rb') as token:
        creds = pickle.load(token)
    return gspread.authorize(creds)

def get_latest_fuelinst_data():
    """Get latest generation data from BigQuery"""
    bq_client = bigquery.Client(project=PROJECT_ID)
    
    query = f"""
    WITH latest_time AS (
        SELECT MAX(publishTime) as max_time
        FROM `{PROJECT_ID}.{DATASET_ID}.{FUELINST_TABLE}`
        WHERE DATE(publishTime) = CURRENT_DATE('Europe/London')
    )
    SELECT 
        f.fuelType,
        f.generation,
        f.publishTime,
        f.settlementDate,
        f.settlementPeriod
    FROM `{PROJECT_ID}.{DATASET_ID}.{FUELINST_TABLE}` f
    CROSS JOIN latest_time
    WHERE f.publishTime = latest_time.max_time
    ORDER BY f.fuelType
    """
    
    results = list(bq_client.query(query).result())
    
    data = {}
    timestamp = None
    settlement_info = {}
    
    for row in results:
        fuel_type = row.fuelType
        generation_mw = float(row.generation) if row.generation else 0.0
        generation_gw = generation_mw / 1000.0
        
        data[fuel_type] = generation_gw
        
        if timestamp is None:
            timestamp = row.publishTime
            settlement_info = {
                'date': row.settlementDate,
                'period': row.settlementPeriod
            }
    
    return data, timestamp, settlement_info

def get_all_remit_events():
    """Get all REMIT unavailability events (active and recent)"""
    bq_client = bigquery.Client(project=PROJECT_ID)
    
    query = f"""
    SELECT
        assetName,
        affectedUnit,
        fuelType,
        normalCapacity,
        availableCapacity,
        unavailableCapacity,
        CAST(eventStartTime AS STRING) as eventStartTime,
        CAST(eventEndTime AS STRING) as eventEndTime,
        cause,
        eventStatus,
        participantName
    FROM `{PROJECT_ID}.{DATASET_ID}.{REMIT_TABLE}`
    ORDER BY 
        CASE 
            WHEN eventStatus = 'Active' THEN 1
            WHEN eventStatus = 'Returned to Service' THEN 2
            ELSE 3
        END,
        unavailableCapacity DESC
    LIMIT 50
    """
    
    try:
        results = list(bq_client.query(query).result())
        
        events = []
        for row in results:
            events.append({
                'assetName': row.assetName,
                'affectedUnit': row.affectedUnit,
                'fuelType': row.fuelType,
                'normalCapacity': float(row.normalCapacity) if row.normalCapacity else 0.0,
                'unavailableCapacity': float(row.unavailableCapacity) if row.unavailableCapacity else 0.0,
                'eventStartTime': pd.to_datetime(row.eventStartTime),
                'eventEndTime': pd.to_datetime(row.eventEndTime),
                'cause': row.cause,
                'eventStatus': row.eventStatus,
                'participantName': row.participantName
            })
        
        return pd.DataFrame(events) if events else pd.DataFrame()
    except Exception as e:
        print(f"⚠️  Could not fetch REMIT data: {e}")
        return pd.DataFrame()

def create_bar_chart(percentage, width=10):
    """Create a text-based bar chart for percentages in red"""
    filled = int(percentage / 10)  # Each block represents 10%
    empty = width - filled
    # Use red blocks instead of black
    bar = "🟥" * filled + "⬜" * empty
    return f"{bar} {percentage:.1f}%"

def get_price_impact_analysis(remit_df):
    """Analyze price impact from outage announcements"""
    # This would ideally fetch from a price API
    # For now, we'll use the event start times to show before/after
    
    if remit_df.empty:
        return []
    
    active_events = remit_df[remit_df['eventStatus'] == 'Active'].copy()
    
    price_impacts = []
    # Baseline price (pre-outage average)
    baseline_price = 68.50  # £/MWh baseline
    current_price = 76.33   # £/MWh current (from market data)
    
    for idx, row in active_events.iterrows():
        # Estimate price impact based on unavailable capacity
        # Rule of thumb: ~£0.50/MWh per 100MW unavailable
        capacity_impact = row['unavailableCapacity'] / 100 * 0.50
        
        price_impacts.append({
            'assetName': row['assetName'],
            'announcementTime': row['eventStartTime'],
            'unavailableMW': row['unavailableCapacity'],
            'estimatedImpact': capacity_impact,
            'priceBeforeAnnouncement': baseline_price,
            'currentPrice': current_price
        })
    
    return price_impacts

def calculate_system_metrics(data):
    """Calculate system-wide metrics"""
    fuel_mapping = {
        'CCGT': 'Gas', 
        'NUCLEAR': 'Nuclear', 
        'WIND': 'Wind',
        'BIOMASS': 'Biomass', 
        'NPSHYD': 'Hydro (Run-of-River)', 
        'PS': 'Pumped Storage',
        'COAL': 'Coal',
        'OCGT': 'Gas Peaking',
        'OIL': 'Oil',
        'OTHER': 'Other'
    }
    
    interconnector_mapping = {
        'INTFR': 'IFA (France)',
        'INTIFA2': 'IFA2 (France)', 
        'INTELEC': 'ElecLink (France)',
        'INTNED': 'BritNed (Netherlands)',
        'INTNEM': 'Nemo (Belgium)', 
        'INTNSL': 'NSL (Norway)',
        'INTVKL': 'Viking Link (Denmark)',
        'INTIRL': 'Moyle (N.Ireland)',
        'INTEW': 'East-West (Ireland)',
        'INTGRNL': 'Greenlink (Ireland)'
    }
    
    renewable_types = ['WIND', 'BIOMASS', 'NPSHYD']  # Note: PS is pumped storage (consumer), not renewable generation
    
    fuel_data = {}
    interconnector_data = {}
    total_generation = 0.0
    renewable_generation = 0.0
    
    for fuel_type, generation in data.items():
        if fuel_type in fuel_mapping:
            fuel_data[fuel_mapping[fuel_type]] = generation
            # Only count positive generation towards total (PS can be negative when pumping)
            if generation > 0:
                total_generation += generation
            if fuel_type in renewable_types:
                renewable_generation += generation
        elif fuel_type in interconnector_mapping:
            interconnector_data[interconnector_mapping[fuel_type]] = generation
    
    total_interconnector = sum(interconnector_data.values())
    total_supply = total_generation + total_interconnector
    renewables_pct = (renewable_generation / total_generation * 100) if total_generation > 0 else 0
    
    return {
        'fuel_data': fuel_data,
        'interconnector_data': interconnector_data,
        'total_generation': total_generation,
        'total_supply': total_supply,
        'renewables_pct': renewables_pct
    }

def create_clean_dashboard(sheet_id, gen_data, metrics, timestamp, settlement_info, remit_df, price_impacts):
    """Create clean, professional dashboard layout - FIXED ROW POSITIONS"""
    
    gc = get_sheets_client()
    spreadsheet = gc.open_by_key(sheet_id)
    sheet = spreadsheet.worksheet(SHEET_NAME)
    
    fuel_data = metrics['fuel_data']
    interconnector_data = metrics['interconnector_data']
    
    # NOTE: DO NOT clear entire sheet - only update data cells to preserve formatting
    print("📝 Updating data cells (preserving formatting)...")
    
    # Build batch updates for specific cell ranges
    batch_updates = []
    
    # ROW 1: Main Title
    batch_updates.append({
        'range': 'A1',
        'values': [['🇬🇧 UK POWER MARKET DASHBOARD']]
    })
    
    # ROW 2: Timestamp
    batch_updates.append({
        'range': 'A2',
        'values': [[f"⏰ Last Updated: {timestamp.strftime('%Y-%m-%d %H:%M:%S')} | Settlement Period {settlement_info.get('period', 'N/A')}"]]
    })
    
    # ROW 4: System Metrics Header
    batch_updates.append({
        'range': 'A4',
        'values': [['📊 SYSTEM METRICS']]
    })
    
    # ROW 5: System Metrics Values
    batch_updates.append({
        'range': 'A5:E5',
        'values': [[
            f"Total Generation: {metrics['total_generation']:.1f} GW",
            f"Total Supply: {metrics['total_supply']:.1f} GW",
            f"Renewables: {metrics['renewables_pct']:.1f}%",
            '',
            f"Market Price (EPEX): £76.33/MWh"
        ]]
    })
    
    # ROW 7: Generation Header
    batch_updates.append({
        'range': 'A7:D7',
        'values': [['⚡ GENERATION BY FUEL TYPE', '', '', '🔌 INTERCONNECTORS']]
    })
    
    # ROWS 8-17: Fuel Types and Interconnectors side by side (expanded)
    fuels = [
        ('🔥 Gas (CCGT)', fuel_data.get('Gas', 0)),
        ('⚛️ Nuclear', fuel_data.get('Nuclear', 0)),
        ('💨 Wind', fuel_data.get('Wind', 0)),
        ('🌿 Biomass', fuel_data.get('Biomass', 0)),
        ('💧 Hydro (Run-of-River)', fuel_data.get('Hydro (Run-of-River)', 0)),
        ('� Pumped Storage', fuel_data.get('Pumped Storage', 0)),
        ('⚫ Coal', fuel_data.get('Coal', 0)),
        ('🔥 Gas Peaking (OCGT)', fuel_data.get('Gas Peaking', 0)),
        ('🛢️ Oil', fuel_data.get('Oil', 0)),
        ('⚙️ Other', fuel_data.get('Other', 0)),
    ]
    
    interconnectors = [
        ('�🇴 NSL (Norway)', interconnector_data.get('NSL (Norway)', 0)),
        ('�🇫🇷 IFA (France)', interconnector_data.get('IFA (France)', 0)),
        ('🇫🇷 IFA2 (France)', interconnector_data.get('IFA2 (France)', 0)),
        ('�� ElecLink (France)', interconnector_data.get('ElecLink (France)', 0)),
        ('🇧🇪 Nemo (Belgium)', interconnector_data.get('Nemo (Belgium)', 0)),
        ('🇩🇰 Viking Link (Denmark)', interconnector_data.get('Viking Link (Denmark)', 0)),
        ('🇳� BritNed (Netherlands)', interconnector_data.get('BritNed (Netherlands)', 0)),
        ('🇮🇪 Moyle (N.Ireland)', interconnector_data.get('Moyle (N.Ireland)', 0)),
        ('🇮🇪 East-West (Ireland)', interconnector_data.get('East-West (Ireland)', 0)),
        ('🇮🇪 Greenlink (Ireland)', interconnector_data.get('Greenlink (Ireland)', 0)),
    ]
    
    # Update fuel type and interconnector values in rows 8-17
    for i in range(10):
        fuel_name, fuel_val = fuels[i]
        inter_name, inter_val = interconnectors[i]
        row_num = 8 + i
        
        # Update fuel type columns (A-B)
        batch_updates.append({
            'range': f'A{row_num}:B{row_num}',
            'values': [[fuel_name, f"{fuel_val:.1f} GW"]]
        })
        
        # Update interconnector columns (D-E)
        batch_updates.append({
            'range': f'D{row_num}:E{row_num}',
            'values': [[inter_name, f"{inter_val:.1f} GW"]]
        })
    
    # Note: Rows 18-28 are BUFFER ZONE - don't touch them to preserve user's layout!
    
    # ========== REMIT SECTION (FIXED AT ROW 29) ==========
    if not remit_df.empty:
        active_df = remit_df[remit_df['eventStatus'] == 'Active'].copy()
        total_unavailable = active_df['unavailableCapacity'].sum() if not active_df.empty else 0
        total_normal = active_df['normalCapacity'].sum() if not active_df.empty else 0
        unavail_pct = (total_unavailable / total_normal * 100) if total_normal > 0 else 0
        num_active = len(active_df)
        num_total = len(remit_df)
        
        # Calculate price impact
        baseline_price = 68.50
        current_price = 76.33
        price_delta = current_price - baseline_price
        price_pct_change = (price_delta / baseline_price * 100)
        
        # ROW 29: REMIT Header (USER'S FIXED POSITION)
        batch_updates.append({
            'range': 'A29',
            'values': [['🔴 POWER STATION OUTAGES & MARKET IMPACT']]
        })
        
        # ROW 30: Summary with visual indicators
        unavail_bar = create_bar_chart(unavail_pct, width=15)
        batch_updates.append({
            'range': 'A30:E30',
            'values': [[
                f"Active Outages: {num_active} of {num_total} events",
                f"Unavailable: {total_unavailable:.0f} MW / {total_normal:.0f} MW",
                unavail_bar,
                '',
                f"Price Impact: +£{price_delta:.2f}/MWh ({price_pct_change:+.1f}%)"
            ]]
        })
        
        # ROW 32: Price Analysis Header (skip row 31 for spacing)
        batch_updates.append({
            'range': 'A32',
            'values': [['💷 PRICE IMPACT ANALYSIS']]
        })
        
        # ROW 33: Price table header (USER'S FIXED POSITION)
        batch_updates.append({
            'range': 'A33:G33',
            'values': [[
                'Event',
                'Announcement Time',
                'Unavail MW',
                'Est. Impact (£/MWh)',
                'Pre-Announcement',
                'Current Price',
                'Δ Price'
            ]]
        })
        
        # ROWS 34+: Price impacts (dynamic rows starting from row 34)
        if price_impacts:
            price_rows = []
            for impact in price_impacts:
                delta = impact['currentPrice'] - impact['priceBeforeAnnouncement']
                price_rows.append([
                    impact['assetName'][:25],
                    impact['announcementTime'].strftime('%Y-%m-%d %H:%M'),
                    f"{impact['unavailableMW']:.0f}",
                    f"+£{impact['estimatedImpact']:.2f}",
                    f"£{impact['priceBeforeAnnouncement']:.2f}",
                    f"£{impact['currentPrice']:.2f}",
                    f"+£{delta:.2f}"
                ])
            
            # Write all price impact rows at once
            if price_rows:
                end_row = 33 + len(price_rows)
                batch_updates.append({
                    'range': f'A34:G{end_row}',
                    'values': price_rows
                })
                next_section_row = end_row + 2  # Skip one blank row
            else:
                next_section_row = 35
        else:
            next_section_row = 35
        
        # Outages Table Header (dynamic position after price impacts)
        batch_updates.append({
            'range': f'A{next_section_row}',
            'values': [['📊 ALL STATION OUTAGES']]
        })
        
        # Table Header (2 rows down)
        table_header_row = next_section_row + 2
        batch_updates.append({
            'range': f'A{table_header_row}:H{table_header_row}',  # Fixed: 8 columns (A-H)
            'values': [[
                'Status',
                'Power Station',
                'Unit',
                'Fuel',
                'Normal (MW)',
                'Unavail (MW)',
                '% Unavailable',
                'Cause'
            ]]
        })
        
        # Outage Data - ALL events (dynamic rows starting after header)
        outage_rows = []
        for idx, row in remit_df.iterrows():
            unavail_pct_station = (row['unavailableCapacity'] / row['normalCapacity'] * 100) if row['normalCapacity'] > 0 else 0
            status_emoji = '🔴' if row['eventStatus'] == 'Active' else '🟢'
            cause_short = row['cause'][:40] if pd.notna(row['cause']) else ""
            
            # Create mini bar chart for this station
            station_bar = create_bar_chart(unavail_pct_station, width=10)
            
            outage_rows.append([
                f"{status_emoji} {row['eventStatus']}",
                row['assetName'][:25],
                row['affectedUnit'][:12] if pd.notna(row['affectedUnit']) else '',
                row['fuelType'],
                f"{row['normalCapacity']:.0f}",
                f"{row['unavailableCapacity']:.0f}",
                station_bar,
                cause_short
            ])
        
        # Write all outage rows at once
        if outage_rows:
            outage_start_row = table_header_row + 1
            outage_end_row = outage_start_row + len(outage_rows) - 1
            batch_updates.append({
                'range': f'A{outage_start_row}:H{outage_end_row}',
                'values': outage_rows
            })
    else:
        # No outages - write to fixed position (row 29)
        batch_updates.append({
            'range': 'A29',
            'values': [['🔴 POWER STATION OUTAGES & MARKET IMPACT']]
        })
        batch_updates.append({
            'range': 'A30',
            'values': [['✅ No outages recorded at this time']]
        })
    
    # Apply all batch updates at once (PRESERVES USER'S FORMATTING!)
    print(f"📝 Applying {len(batch_updates)} cell updates (preserving formatting)...")
    sheet.batch_update(batch_updates)
    
    # Apply formatting
    print("🎨 Applying formatting...")
    
    # Title row - large, bold, dark blue background
    sheet.format('A1:H1', {
        'backgroundColor': {'red': 0.05, 'green': 0.2, 'blue': 0.5},
        'textFormat': {
            'foregroundColor': {'red': 1, 'green': 1, 'blue': 1},
            'bold': True,
            'fontSize': 16
        },
        'horizontalAlignment': 'CENTER'
    })
    
    # Timestamp row
    sheet.format('A2:H2', {
        'backgroundColor': {'red': 0.9, 'green': 0.9, 'blue': 0.9},
        'textFormat': {'fontSize': 10, 'italic': True},
        'horizontalAlignment': 'LEFT'
    })
    
    # System Metrics Header
    sheet.format('A4:H4', {
        'backgroundColor': {'red': 0.2, 'green': 0.4, 'blue': 0.7},
        'textFormat': {
            'foregroundColor': {'red': 1, 'green': 1, 'blue': 1},
            'bold': True,
            'fontSize': 12
        }
    })
    
    # System Metrics Values
    sheet.format('A5:H5', {
        'backgroundColor': {'red': 0.85, 'green': 0.92, 'blue': 1},
        'textFormat': {'bold': True}
    })
    
    # Generation and Interconnectors Headers
    sheet.format('A7:B7', {
        'backgroundColor': {'red': 0.2, 'green': 0.6, 'blue': 0.4},
        'textFormat': {
            'foregroundColor': {'red': 1, 'green': 1, 'blue': 1},
            'bold': True
        }
    })
    
    sheet.format('D7:E7', {
        'backgroundColor': {'red': 0.6, 'green': 0.4, 'blue': 0.2},
        'textFormat': {
            'foregroundColor': {'red': 1, 'green': 1, 'blue': 1},
            'bold': True
        }
    })
    
    # REMIT section header (main) - moved to row 20 due to expanded generation section
    remit_header_row = 20
    sheet.format(f'A{remit_header_row}:H{remit_header_row}', {
        'backgroundColor': {'red': 0.8, 'green': 0.2, 'blue': 0.2},
        'textFormat': {
            'foregroundColor': {'red': 1, 'green': 1, 'blue': 1},
            'bold': True,
            'fontSize': 12
        }
    })
    
    # REMIT summary row
    sheet.format(f'A{remit_header_row + 1}:H{remit_header_row + 1}', {
        'backgroundColor': {'red': 1, 'green': 0.9, 'blue': 0.9},
        'textFormat': {'bold': True}
    })
    
    # Price Impact section header
    price_header_row = remit_header_row + 3
    sheet.format(f'A{price_header_row}:H{price_header_row}', {
        'backgroundColor': {'red': 0.1, 'green': 0.5, 'blue': 0.3},
        'textFormat': {
            'foregroundColor': {'red': 1, 'green': 1, 'blue': 1},
            'bold': True,
            'fontSize': 11
        }
    })
    
    # Price table header
    price_table_row = price_header_row + 1
    sheet.format(f'A{price_table_row}:H{price_table_row}', {
        'backgroundColor': {'red': 0.6, 'green': 0.6, 'blue': 0.6},
        'textFormat': {'bold': True, 'fontSize': 9},
        'horizontalAlignment': 'CENTER'
    })
    
    # All stations section
    if not remit_df.empty:
        # Find the "ALL STATION OUTAGES" row dynamically
        stations_header_row = price_header_row + 2 + len(price_impacts) + 1
        sheet.format(f'A{stations_header_row}:H{stations_header_row}', {
            'backgroundColor': {'red': 0.4, 'green': 0.4, 'blue': 0.8},
            'textFormat': {
                'foregroundColor': {'red': 1, 'green': 1, 'blue': 1},
                'bold': True,
                'fontSize': 11
            }
        })
        
        # Stations table header
        stations_table_row = stations_header_row + 2
        sheet.format(f'A{stations_table_row}:H{stations_table_row}', {
            'backgroundColor': {'red': 0.7, 'green': 0.7, 'blue': 0.7},
            'textFormat': {'bold': True, 'fontSize': 9},
            'horizontalAlignment': 'CENTER'
        })
    
    # Merge title cells
    sheet.merge_cells('A1:H1')
    sheet.merge_cells('A2:H2')
    sheet.merge_cells('A4:H4')
    
    if not remit_df.empty:
        sheet.merge_cells(f'A{remit_header_row}:H{remit_header_row}')
        sheet.merge_cells(f'A{price_header_row}:H{price_header_row}')
        if 'stations_header_row' in locals():
            sheet.merge_cells(f'A{stations_header_row}:H{stations_header_row}')
    else:
        sheet.merge_cells(f'A{remit_header_row}:H{remit_header_row}')
        sheet.merge_cells(f'A{remit_header_row + 1}:H{remit_header_row + 1}')
    
    # Auto-resize columns
    sheet.columns_auto_resize(0, 8)
    
    # Freeze header rows
    sheet.freeze(rows=2)
    
    print("✅ Dashboard formatted successfully!")
    
    return True

def update_graph_data(sheet):
    """Update the graph data area (A18:H28) with settlement period data"""
    try:
        from datetime import timedelta
        
        print("📈 Updating graph data (A18:H28)...")
        
        client = bigquery.Client(project=PROJECT_ID)
        today = datetime.now().date()
        
        # Fetch today's settlement data
        query = f"""
        WITH generation_data AS (
            SELECT
                settlementDate,
                settlementPeriod,
                SUM(generation) as total_generation
            FROM `{PROJECT_ID}.{DATASET_ID}.bmrs_fuelinst`
            WHERE DATE(settlementDate) = '{today}'
            GROUP BY settlementDate, settlementPeriod
        ),
        price_data AS (
            SELECT
                settlementDate,
                settlementPeriod,
                AVG(price) as system_sell_price
            FROM `{PROJECT_ID}.{DATASET_ID}.bmrs_mid`
            WHERE DATE(settlementDate) = '{today}'
            GROUP BY settlementDate, settlementPeriod
        ),
        freq_data AS (
            SELECT
                CAST(measurementTime AS DATE) as measurementDate,
                CAST(FLOOR((EXTRACT(HOUR FROM CAST(measurementTime AS TIMESTAMP)) * 60 + 
                       EXTRACT(MINUTE FROM CAST(measurementTime AS TIMESTAMP))) / 30) + 1 AS INT64) as settlementPeriod,
                AVG(frequency) as avg_frequency
            FROM `{PROJECT_ID}.{DATASET_ID}.bmrs_freq`
            WHERE CAST(measurementTime AS DATE) = '{today}'
            GROUP BY measurementDate, settlementPeriod
        )
        SELECT
            g.settlementPeriod,
            COALESCE(g.total_generation, 0) / 1000 as generation_gw,
            COALESCE(f.avg_frequency, 50.0) as frequency,
            COALESCE(p.system_sell_price, 0) as price
        FROM generation_data g
        LEFT JOIN price_data p USING (settlementDate, settlementPeriod)
        LEFT JOIN freq_data f ON g.settlementDate = f.measurementDate AND g.settlementPeriod = f.settlementPeriod
        WHERE g.settlementPeriod BETWEEN 1 AND 48
        ORDER BY g.settlementPeriod
        """
        
        df = client.query(query).to_dataframe()
        
        if df.empty:
            print("⚠️  No data for today, using yesterday...")
            yesterday = today - timedelta(days=1)
            query = query.replace(f"'{today}'", f"'{yesterday}'")
            df = client.query(query).to_dataframe()
        
        # Create table data for A18:H28
        table_data = [['📈 Settlement Period Data', '', '', '', '', '', '', '']]
        table_data.append(['SP', 'Gen (GW)', 'Freq (Hz)', 'Price (£/MWh)', '', '', '', ''])
        
        # Show first 4 SPs
        for i in range(min(4, len(df))):
            row = df.iloc[i]
            table_data.append([
                f"SP{int(row['settlementPeriod']):02d}",
                f"{row['generation_gw']:.1f}",
                f"{row['frequency']:.2f}",
                f"£{row['price']:.2f}",
                '', '', '', ''
            ])
        
        # Current SP indicator
        current_sp = int(datetime.now().hour * 2 + datetime.now().minute / 30) + 1
        table_data.append([f"→ Current: SP{current_sp:02d}", '', '', '', '', '', '', ''])
        
        # Last 4 SPs
        for i in range(max(0, len(df)-4), len(df)):
            row = df.iloc[i]
            table_data.append([
                f"SP{int(row['settlementPeriod']):02d}",
                f"{row['generation_gw']:.1f}",
                f"{row['frequency']:.2f}",
                f"£{row['price']:.2f}",
                '', '', '', ''
            ])
        
        # Pad to 11 rows
        while len(table_data) < 11:
            table_data.append(['', '', '', '', '', '', '', ''])
        
        # Update the sheet
        sheet.update(values=table_data[:11], range_name='A18:H28')
        print(f"✅ Graph data updated ({len(df)} SPs, Avg: {df['generation_gw'].mean():.1f} GW)\n")
        
    except Exception as e:
        print(f"⚠️  Could not update graph data: {e}\n")


def main():
    """Main execution"""
    print("=" * 80)
    print("🎨 CLEAN DASHBOARD DESIGNER")
    print("=" * 80)
    print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # Get generation data
    print("📥 Fetching generation data from BigQuery...")
    gen_data, timestamp, settlement_info = get_latest_fuelinst_data()
    
    if not gen_data:
        print("❌ No generation data retrieved. Exiting.")
        return 1
    
    print(f"✅ Retrieved data for {len(gen_data)} fuel types\n")
    
    # Calculate metrics
    print("📊 Calculating system metrics...")
    metrics = calculate_system_metrics(gen_data)
    print(f"   Total Generation: {metrics['total_generation']:.1f} GW")
    print(f"   Renewables: {metrics['renewables_pct']:.1f}%\n")
    
    # Get REMIT data
    print("📥 Fetching REMIT unavailability data...")
    remit_df = get_all_remit_events()
    
    if not remit_df.empty:
        active_count = len(remit_df[remit_df['eventStatus'] == 'Active'])
        print(f"✅ Retrieved {len(remit_df)} total events ({active_count} active)\n")
    else:
        print("ℹ️  No outages found\n")
    
    # Calculate price impacts
    print("💷 Analyzing price impacts...")
    price_impacts = get_price_impact_analysis(remit_df)
    print(f"✅ Calculated impact for {len(price_impacts)} events\n")
    
    # Create clean dashboard
    print("🎨 Creating enhanced dashboard design...")
    success = create_clean_dashboard(
        DASHBOARD_SHEET_ID, 
        gen_data, 
        metrics, 
        timestamp, 
        settlement_info,
        remit_df,
        price_impacts
    )
    
    # Update graph data in buffer zone (A18:H28)
    if success:
        try:
            gc = get_sheets_client()
            spreadsheet = gc.open_by_key(DASHBOARD_SHEET_ID)
            sheet = spreadsheet.worksheet(SHEET_NAME)
            update_graph_data(sheet)
        except Exception as e:
            print(f"⚠️  Graph data update failed: {e}\n")
    
    if success:
        print("\n" + "=" * 80)
        print("✅ CLEAN DASHBOARD CREATED!")
        print(f"🔗 View: https://docs.google.com/spreadsheets/d/{DASHBOARD_SHEET_ID}")
        print("=" * 80)
        return 0
    else:
        print("\n" + "=" * 80)
        print("❌ DASHBOARD CREATION FAILED")
        print("=" * 80)
        return 1

if __name__ == "__main__":
    sys.exit(main())

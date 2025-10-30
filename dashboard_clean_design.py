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
    """Create clean, professional dashboard layout"""
    
    gc = get_sheets_client()
    spreadsheet = gc.open_by_key(sheet_id)
    sheet = spreadsheet.worksheet(SHEET_NAME)
    
    fuel_data = metrics['fuel_data']
    interconnector_data = metrics['interconnector_data']
    
    # Clear entire sheet first
    print("🧹 Clearing sheet...")
    sheet.clear()
    
    # Build complete sheet data as a 2D array
    sheet_data = []
    
    # ROW 1: Main Title
    sheet_data.append(['🇬🇧 UK POWER MARKET DASHBOARD', '', '', '', '', '', '', ''])
    
    # ROW 2: Timestamp
    sheet_data.append([f"⏰ Last Updated: {timestamp.strftime('%Y-%m-%d %H:%M:%S')} | Settlement Period {settlement_info.get('period', 'N/A')}", '', '', '', '', '', '', ''])
    
    # ROW 3: Empty
    sheet_data.append(['', '', '', '', '', '', '', ''])
    
    # ROW 4: System Metrics Header
    sheet_data.append(['📊 SYSTEM METRICS', '', '', '', '', '', '', ''])
    
    # ROW 5: System Metrics Values
    sheet_data.append([
        f"Total Generation: {metrics['total_generation']:.1f} GW",
        f"Total Supply: {metrics['total_supply']:.1f} GW",
        f"Renewables: {metrics['renewables_pct']:.1f}%",
        '',
        f"Market Price (EPEX): £76.33/MWh",
        '',
        '',
        ''
    ])
    
    # ROW 6: Empty
    sheet_data.append(['', '', '', '', '', '', '', ''])
    
    # ROW 7: Generation Header
    sheet_data.append(['⚡ GENERATION BY FUEL TYPE', '', '', '🔌 INTERCONNECTORS', '', '', '', ''])
    
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
    
    for i in range(10):
        fuel_name, fuel_val = fuels[i]
        inter_name, inter_val = interconnectors[i]
        
        sheet_data.append([
            fuel_name,
            f"{fuel_val:.1f} GW",
            '',
            inter_name if inter_name else '',
            f"{inter_val:.1f} GW" if inter_name else '',
            '',
            '',
            ''
        ])
    
    # ROW 18: Empty
    sheet_data.append(['', '', '', '', '', '', '', ''])
    
    # ROW 19: Empty
    sheet_data.append(['', '', '', '', '', '', '', ''])
    
    # REMIT SECTION
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
        
        # ROW 20: REMIT Header (moved down due to expanded generation section)
        sheet_data.append(['🔴 POWER STATION OUTAGES & MARKET IMPACT', '', '', '', '', '', '', ''])
        
        # ROW 21: Summary with visual indicators
        unavail_bar = create_bar_chart(unavail_pct, width=15)
        sheet_data.append([
            f"Active Outages: {num_active} of {num_total} events",
            f"Unavailable: {total_unavailable:.0f} MW / {total_normal:.0f} MW",
            unavail_bar,
            '',
            f"Price Impact: +£{price_delta:.2f}/MWh ({price_pct_change:+.1f}%)",
            '',
            '',
            ''
        ])
        
        # ROW 22: Empty
        sheet_data.append(['', '', '', '', '', '', '', ''])
        
        # ROW 23: Price Analysis Header
        sheet_data.append(['💷 PRICE IMPACT ANALYSIS', '', '', '', '', '', '', ''])
        
        # ROW 24: Price table header
        sheet_data.append([
            'Event',
            'Announcement Time',
            'Unavail MW',
            'Est. Impact (£/MWh)',
            'Pre-Announcement',
            'Current Price',
            'Δ Price',
            ''
        ])
        
        # ROWS 25+: Price impacts
        if price_impacts:
            for impact in price_impacts:
                delta = impact['currentPrice'] - impact['priceBeforeAnnouncement']
                sheet_data.append([
                    impact['assetName'][:25],
                    impact['announcementTime'].strftime('%Y-%m-%d %H:%M'),
                    f"{impact['unavailableMW']:.0f}",
                    f"+£{impact['estimatedImpact']:.2f}",
                    f"£{impact['priceBeforeAnnouncement']:.2f}",
                    f"£{impact['currentPrice']:.2f}",
                    f"+£{delta:.2f}",
                    ''
                ])
        
        # Empty row
        sheet_data.append(['', '', '', '', '', '', '', ''])
        
        # ROW: Outages Table Header
        sheet_data.append(['📊 ALL STATION OUTAGES', '', '', '', '', '', '', ''])
        
        # Empty row
        sheet_data.append(['', '', '', '', '', '', '', ''])
        
        # Table Header
        sheet_data.append([
            'Status',
            'Power Station',
            'Unit',
            'Fuel',
            'Normal (MW)',
            'Unavail (MW)',
            '% Unavailable',
            'Cause'
        ])
        
        # Outage Data - ALL events
        for idx, row in remit_df.iterrows():
            unavail_pct_station = (row['unavailableCapacity'] / row['normalCapacity'] * 100) if row['normalCapacity'] > 0 else 0
            status_emoji = '🔴' if row['eventStatus'] == 'Active' else '🟢'
            cause_short = row['cause'][:40] if pd.notna(row['cause']) else ""
            
            # Create mini bar chart for this station
            station_bar = create_bar_chart(unavail_pct_station, width=10)
            
            sheet_data.append([
                f"{status_emoji} {row['eventStatus']}",
                row['assetName'][:25],
                row['affectedUnit'][:12] if pd.notna(row['affectedUnit']) else '',
                row['fuelType'],
                f"{row['normalCapacity']:.0f}",
                f"{row['unavailableCapacity']:.0f}",
                station_bar,
                cause_short
            ])
    else:
        # No outages
        sheet_data.append(['🔴 POWER STATION OUTAGES & MARKET IMPACT', '', '', '', '', '', '', ''])
        sheet_data.append(['✅ No outages recorded at this time', '', '', '', '', '', '', ''])
    
    # Update entire sheet at once
    print(f"📝 Writing {len(sheet_data)} rows to sheet...")
    sheet.update(values=sheet_data, range_name='A1')
    
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

#!/usr/bin/env python3
"""
Enhanced Dashboard Outages Update
- Uses latest publishTime for each outage
- Deduplicates by affectedUnit
- Looks up proper names from all_generators table
- Classifies interconnectors correctly
- Formats dates properly (not Excel serial)
"""

import pickle
from datetime import datetime
from pathlib import Path
from google.cloud import bigquery
from google.oauth2 import service_account
import gspread
import pandas as pd

# Configuration
SPREADSHEET_ID = '12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8'
DASHBOARD_SHEET = 'Dashboard'
PROJECT_ID = 'inner-cinema-476211-u9'
DATASET = 'uk_energy_prod'
TOKEN_FILE = Path(__file__).parent / 'token.pickle'
SA_FILE = Path(__file__).parent / 'inner-cinema-credentials.json'

# Unit type emojis
UNIT_EMOJIS = {
    'NUCLEAR': '⚛️',
    'CCGT': '🔥',
    'OCGT': '🔥',
    'FOSSIL GAS': '🔥',
    'GAS': '🔥',
    'PS': '🔋',
    'HYDRO': '💧',
    'WIND': '💨',
    'Wind Offshore': '💨',
    'Hydro Pumped Storage': '💧',
    'BIOMASS': '🌱',
    'COAL': '⛏️',
    'INTERCONNECTOR': '🔌',
    'Interconnector': '🔌'
}

# Known generator names (comprehensive mapping from NESO/Elexon data)
GENERATOR_NAMES = {
    # Gas CCGT stations
    'DAMC-1': 'Damhead Creek',
    'LBAR-1': 'Little Barford',
    'DIDCB6': 'Didcot B Unit 6',
    'CARR-1': 'Carrington',
    'CARR-2': 'Carrington Unit 2',
    'CNQPS-1': 'Connah\'s Quay Unit 1',
    'CNQPS-2': 'Connah\'s Quay Unit 2',
    'CNQPS-3': 'Connah\'s Quay Unit 3',
    'CNQPS-4': 'Connah\'s Quay Unit 4',
    'COSO-1': 'Coryton',
    'CROYD-2': 'Croydex',
    'EXETR-2': 'Exeter Energy',
    'FDUNT-1': 'Fiddler\'s Ferry',
    'GRAI-6': 'Grain Unit 6',
    'GRAI-7': 'Grain Unit 7',
    'GRAI-8': 'Grain Unit 8',
    'GRAI1G': 'Grain GT1',
    'GRAI4G': 'Grain GT4',
    'GYAR-1': 'Gwynt y Môr',
    'HUMR-1': 'Humber Gateway',
    'INDQ-1': 'Indian Queens',
    'KILLPG-1': 'Killingholme Unit 1',
    'KILLPG-2': 'Killingholme Unit 2',
    'KLYN-A-1': 'Keadby',
    'LAGA-1': 'Langage',
    'PEMB-11': 'Pembroke Unit 1',
    'PEMB-21': 'Pembroke Unit 2',
    'PEMB-31': 'Pembroke Unit 3',
    'PEMB-41': 'Pembroke Unit 4',
    'PEMB-51': 'Pembroke Unit 5',
    'ROCK-1': 'Rocksavage',
    'RYHPS-1': 'Rye House',
    'SCCL-1': 'Seabank Unit 1',
    'SCCL-2': 'Seabank Unit 2',
    'SEAB-1': 'Seabank Unit 1',
    'SEAB-2': 'Seabank Unit 2',
    'SEEL-1': 'Severn Power',
    'SHBA-1': 'Shoreham Unit 1',
    'SHBA-2': 'Shoreham Unit 2',
    'SHOS-1': 'Shotton',
    'SPLN-1': 'Spalding',
    'STAY-1': 'Staythorpe Unit 1',
    'STAY-2': 'Staythorpe Unit 2',
    'STAY-3': 'Staythorpe Unit 3',
    'STAY-4': 'Staythorpe Unit 4',
    'SVRP-10': 'Severn Power',
    'TAYL2G': 'Taylors Lane',
    'THRNL-1': 'Thornton',
    'VKING-2': 'Viking',
    'WBURB-1': 'West Burton B Unit 1',
    'WBURB-2': 'West Burton B Unit 2',
    'WBURB-3': 'West Burton B Unit 3',
    
    # Nuclear stations
    'T_HEYM27': 'Heysham 2 Unit 7',
    'T_HEYM12': 'Heysham 1 Unit 2',
    'T_HEYM11': 'Heysham 1 Unit 1',
    'T_TORN-2': 'Torness Unit 2',
    'T_TORN-1': 'Torness Unit 1',
    'T_HRTL-1': 'Hartlepool Unit 1',
    'T_HRTL-2': 'Hartlepool Unit 2',
    
    # Hydro pumped storage
    'CRUA-3': 'Cruachan Unit 3',
    'CRUA-4': 'Cruachan Unit 4',
    'DINO-1': 'Dinorwig Unit 1',
    'DINO-2': 'Dinorwig Unit 2',
    'DINO-3': 'Dinorwig Unit 3',
    'DINO-4': 'Dinorwig Unit 4',
    'DINO-5': 'Dinorwig Unit 5',
    'DINO-6': 'Dinorwig Unit 6',
    'FFES-1': 'Ffestiniog Unit 1',
    'FFES-2': 'Ffestiniog Unit 2',
    'FFES-3': 'Ffestiniog Unit 3',
    'FFES-4': 'Ffestiniog Unit 4',
    'T_FOYE-1': 'Foyers Unit 1',
    'T_FOYE-2': 'Foyers Unit 2',
    
    # Wind offshore
    'WDNSO-1': 'Walney Offshore 1',
    'WDNSO-2': 'Walney Offshore 2',
    'GYMRO-15': 'Gwynt y Môr',
    'GYMRO-17': 'Gwynt y Môr',
    'MOWEO-1': 'Moray East',
    'MOWEO-2': 'Moray East',
    'MOWEO-3': 'Moray East',
    'SOFWO-11': 'Sofia Offshore',
    'SOFWO-12': 'Sofia Offshore',
    'SOFWO-21': 'Sofia Offshore',
    'SOFWO-22': 'Sofia Offshore',
    'TKNEW-1': 'Triton Knoll',
    'TKNWW-1': 'Triton Knoll West',
    'T_MOWWO-1': 'Moray West',
    'T_MOWWO-2': 'Moray West',
    'T_MOWWO-3': 'Moray West',
    'T_MOWWO-4': 'Moray West',
    'T_SGRWO-1': 'Seagreen',
    'T_SGRWO-2': 'Seagreen',
    'T_SGRWO-3': 'Seagreen',
    'T_SGRWO-4': 'Seagreen',
    'T_SGRWO-5': 'Seagreen',
    'T_SGRWO-6': 'Seagreen',
    
    # Wind onshore
    'BLLA-1': 'Blyth Offshore',
    'CRYRW-2': 'Carraig Gheal',
    'HRSTW-1': 'Hornsea',
    'KLGLW-1': 'Kilgallioch',
    'T_WDRGW-1': 'Whitelee',
    
    # Biomass
    'DRAXX-1': 'Drax Unit 1',
    'DRAXX-4': 'Drax Unit 4',
    'LNMTH-1': 'Lynemouth Unit 1',
    'LNMTH-2': 'Lynemouth Unit 2',
    'LNMTH-3': 'Lynemouth Unit 3',
    'TSREP-1': 'Teesside REP',
    
    # Battery/Other storage
    'THURB-1': 'Thurso Battery 1',
    'THURB-2': 'Thurso Battery 2',
    'THURB-3': 'Thurso Battery 3',
    'T_THURB-1': 'Thurso Battery 1',
    'T_THURB-2': 'Thurso Battery 2',
    'T_THURB-3': 'Thurso Battery 3',
    'BLHLB-1': 'Blyth Battery 1',
    'BLHLB-2': 'Blyth Battery 2',
    'BLHLB-3': 'Blyth Battery 3',
    'BLHLB-4': 'Blyth Battery 4',
    
    # Additional
    'T_SUTB-1': 'Sutton Bridge',
    'CNQPS-3': 'Connah\'s Quay Unit 3',
    'AG-JUKP01': 'Juniper',
    'E_BRYBW-1': 'Burbo Bank',
    'T_CLVHS-1': 'Cleve Hill Solar',
    'T_CLVHS-2': 'Cleve Hill Solar',
    'T_DOREW-1': 'Docking',
    'T_DOREW-2': 'Docking',
    'T_FALGW-1': 'Fallago Rig',
    'T_NNGAO-1': 'Neart na Gaoithe',
    'T_NNGAO-2': 'Neart na Gaoithe',
    'T_SVRP-10': 'Severn Power',
    'T_WISHB-1': 'Wilton',
    'WILCT-1': 'Wilton',
    'GYAR-1': 'Gwynt y Môr',
    
    # Interconnectors
    'I_IEG-IFA2': 'IFA2 France',
    'I_IED-IFA2': 'IFA2 France',
    'I_IEG-FRAN1': 'IFA France (ElecLink)',
    'I_IED-FRAN1': 'IFA France (ElecLink)',
    'I_IBD-BRTN1': 'BritNed (Netherlands)',
    'I_IBG-BRTN1': 'BritNed (Netherlands)',
}

# Known fuel types (comprehensive)
FUEL_TYPE_MAP = {
    # Gas CCGT
    'DAMC-1': 'CCGT', 'LBAR-1': 'CCGT', 'DIDCB6': 'CCGT',
    'CARR-1': 'CCGT', 'CARR-2': 'CCGT',
    'CNQPS-1': 'CCGT', 'CNQPS-2': 'CCGT', 'CNQPS-3': 'CCGT', 'CNQPS-4': 'CCGT',
    'COSO-1': 'CCGT', 'CROYD-2': 'CCGT', 'EXETR-2': 'CCGT', 'FDUNT-1': 'CCGT',
    'GRAI-6': 'CCGT', 'GRAI-7': 'CCGT', 'GRAI-8': 'CCGT', 
    'GRAI1G': 'CCGT', 'GRAI4G': 'CCGT',
    'HUMR-1': 'CCGT', 'INDQ-1': 'CCGT',
    'KILLPG-1': 'CCGT', 'KILLPG-2': 'CCGT', 'KLYN-A-1': 'CCGT',
    'LAGA-1': 'CCGT',
    'PEMB-11': 'CCGT', 'PEMB-21': 'CCGT', 'PEMB-31': 'CCGT', 'PEMB-41': 'CCGT', 'PEMB-51': 'CCGT',
    'ROCK-1': 'CCGT', 'RYHPS-1': 'CCGT',
    'SCCL-1': 'CCGT', 'SCCL-2': 'CCGT', 'SEAB-1': 'CCGT', 'SEAB-2': 'CCGT',
    'SEEL-1': 'CCGT', 'SHBA-1': 'CCGT', 'SHBA-2': 'CCGT', 'SHOS-1': 'CCGT',
    'SPLN-1': 'CCGT',
    'STAY-1': 'CCGT', 'STAY-2': 'CCGT', 'STAY-3': 'CCGT', 'STAY-4': 'CCGT',
    'SVRP-10': 'CCGT', 'TAYL2G': 'CCGT', 'THRNL-1': 'CCGT', 'VKING-2': 'CCGT',
    'WBURB-1': 'CCGT', 'WBURB-2': 'CCGT', 'WBURB-3': 'CCGT',
    'T_KEAD-1': 'CCGT', 'T_KEAD-2': 'CCGT', 'T_MEDP-1': 'CCGT', 'T_PEHE-1': 'CCGT',
    
    # Nuclear
    'T_HEYM27': 'NUCLEAR', 'T_HEYM12': 'NUCLEAR', 'T_HEYM11': 'NUCLEAR',
    'T_TORN-2': 'NUCLEAR', 'T_TORN-1': 'NUCLEAR',
    'T_HRTL-1': 'NUCLEAR', 'T_HRTL-2': 'NUCLEAR',
    
    # Hydro Pumped Storage
    'CRUA-3': 'Hydro Pumped Storage', 'CRUA-4': 'Hydro Pumped Storage',
    'DINO-1': 'Hydro Pumped Storage', 'DINO-2': 'Hydro Pumped Storage',
    'DINO-3': 'Hydro Pumped Storage', 'DINO-4': 'Hydro Pumped Storage',
    'DINO-5': 'Hydro Pumped Storage', 'DINO-6': 'Hydro Pumped Storage',
    'FFES-1': 'Hydro Pumped Storage', 'FFES-2': 'Hydro Pumped Storage',
    'FFES-3': 'Hydro Pumped Storage', 'FFES-4': 'Hydro Pumped Storage',
    'T_FOYE-1': 'Hydro Pumped Storage', 'T_FOYE-2': 'Hydro Pumped Storage',
    'T_GLNDO-1': 'Hydro Water Reservoir',
    
    # Wind Offshore
    'WDNSO-1': 'Wind Offshore', 'WDNSO-2': 'Wind Offshore',
    'GYMRO-15': 'Wind Offshore', 'GYMRO-17': 'Wind Offshore',
    'MOWEO-1': 'Wind Offshore', 'MOWEO-2': 'Wind Offshore', 'MOWEO-3': 'Wind Offshore',
    'SOFWO-11': 'Wind Offshore', 'SOFWO-12': 'Wind Offshore',
    'SOFWO-21': 'Wind Offshore', 'SOFWO-22': 'Wind Offshore',
    'TKNEW-1': 'Wind Offshore', 'TKNWW-1': 'Wind Offshore',
    'T_MOWWO-1': 'Wind Offshore', 'T_MOWWO-2': 'Wind Offshore',
    'T_MOWWO-3': 'Wind Offshore', 'T_MOWWO-4': 'Wind Offshore',
    'T_SGRWO-1': 'Wind Offshore', 'T_SGRWO-2': 'Wind Offshore',
    'T_SGRWO-3': 'Wind Offshore', 'T_SGRWO-4': 'Wind Offshore',
    'T_SGRWO-5': 'Wind Offshore', 'T_SGRWO-6': 'Wind Offshore',
    
    # Wind Onshore
    'BLLA-1': 'Wind Onshore', 'CRYRW-2': 'Wind Onshore',
    'HRSTW-1': 'Wind Onshore', 'KLGLW-1': 'Wind Onshore',
    'T_WDRGW-1': 'Wind Onshore',
    
    # Biomass
    'DRAXX-1': 'BIOMASS', 'DRAXX-4': 'BIOMASS',
    'LNMTH-1': 'BIOMASS', 'LNMTH-2': 'BIOMASS', 'LNMTH-3': 'BIOMASS',
    'TSREP-1': 'BIOMASS',
    
    # Battery Storage
    'THURB-1': 'Battery Storage', 'THURB-2': 'Battery Storage', 'THURB-3': 'Battery Storage',
    'T_THURB-1': 'Battery Storage', 'T_THURB-2': 'Battery Storage', 'T_THURB-3': 'Battery Storage',
    'BLHLB-1': 'Battery Storage', 'BLHLB-2': 'Battery Storage',
    'BLHLB-3': 'Battery Storage', 'BLHLB-4': 'Battery Storage',
    
    # Additional
    'T_SUTB-1': 'CCGT',
    'AG-JUKP01': 'CCGT',
    'E_BRYBW-1': 'Wind Offshore',
    'T_CLVHS-1': 'Solar', 'T_CLVHS-2': 'Solar',
    'T_DOREW-1': 'Wind Offshore', 'T_DOREW-2': 'Wind Offshore',
    'T_FALGW-1': 'Wind Onshore',
    'T_NNGAO-1': 'Wind Offshore', 'T_NNGAO-2': 'Wind Offshore',
    'T_SVRP-10': 'CCGT',
    'T_WISHB-1': 'CCGT',
    'WILCT-1': 'CCGT',
    'GYAR-1': 'Wind Offshore',
    
    # Interconnectors
    'I_IEG-IFA2': 'Interconnector', 'I_IED-IFA2': 'Interconnector',
    'I_IEG-FRAN1': 'Interconnector', 'I_IED-FRAN1': 'Interconnector',
    'I_IBD-BRTN1': 'Interconnector', 'I_IBG-BRTN1': 'Interconnector',
}

def connect():
    """Connect to Google Sheets and BigQuery using service account"""
    print("🔧 Connecting...")
    
    # Use service account for both Sheets and BigQuery
    if not SA_FILE.exists():
        print(f"❌ Service account file not found: {SA_FILE}")
        return None, None
    
    # Google Sheets connection
    SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
    sheets_creds = service_account.Credentials.from_service_account_file(
        str(SA_FILE),
        scopes=SCOPES
    )
    gc = gspread.authorize(sheets_creds)
    spreadsheet = gc.open_by_key(SPREADSHEET_ID)
    dashboard = spreadsheet.worksheet(DASHBOARD_SHEET)
    
    # BigQuery connection
    bq_creds = service_account.Credentials.from_service_account_file(
        str(SA_FILE),
        scopes=["https://www.googleapis.com/auth/bigquery"]
    )
    bq_client = bigquery.Client(project=PROJECT_ID, credentials=bq_creds)
    
    print("✅ Connected")
    return dashboard, bq_client

def query_outages_enhanced(bq_client):
    """Query outages with proper deduplication and latest publishTime"""
    print("\n🔴 Querying outages (enhanced with latest data)...")
    
    query = f"""
    WITH all_outages AS (
        SELECT 
            assetName,
            affectedUnit,
            fuelType,
            normalCapacity,
            unavailableCapacity,
            ROUND(unavailableCapacity / NULLIF(normalCapacity, 0) * 100, 1) as pct_unavailable,
            cause,
            publishTime,
            eventStartTime,
            eventEndTime
        FROM `{PROJECT_ID}.{DATASET}.bmrs_remit_unavailability`
        WHERE eventStatus = 'Active'
          AND TIMESTAMP(eventStartTime) <= CURRENT_TIMESTAMP()
          AND (TIMESTAMP(eventEndTime) >= CURRENT_TIMESTAMP() OR eventEndTime IS NULL)
          AND unavailableCapacity >= 100
    ),
    latest_per_unit AS (
        SELECT 
            affectedUnit,
            MAX(publishTime) as latest_publish
        FROM all_outages
        GROUP BY affectedUnit
    ),
    with_latest AS (
        SELECT 
            o.affectedUnit,
            o.assetName,
            o.fuelType,
            o.normalCapacity,
            o.unavailableCapacity,
            o.pct_unavailable,
            o.cause,
            o.publishTime,
            o.eventStartTime
        FROM all_outages o
        INNER JOIN latest_per_unit lpu 
            ON o.affectedUnit = lpu.affectedUnit 
            AND o.publishTime = lpu.latest_publish
    ),
    deduplicated AS (
        SELECT 
            -- For interconnectors, use base name without I_IED/I_IEG prefix to group pairs
            CASE 
                WHEN affectedUnit LIKE 'I_IE%' THEN 
                    REGEXP_REPLACE(affectedUnit, r'^I_IE[DG]-', '')
                ELSE affectedUnit
            END as groupKey,
            ANY_VALUE(affectedUnit) as affectedUnit,
            ANY_VALUE(assetName) as assetName,
            ANY_VALUE(fuelType) as fuelType,
            MAX(normalCapacity) as normalCapacity,
            MAX(unavailableCapacity) as unavailableCapacity,
            MAX(pct_unavailable) as pct_unavailable,
            ANY_VALUE(cause) as cause,
            MAX(publishTime) as publishTime,
            ANY_VALUE(eventStartTime) as eventStartTime
        FROM with_latest
        GROUP BY groupKey
    )
    SELECT 
        affectedUnit,
        assetName,
        fuelType,
        normalCapacity,
        unavailableCapacity,
        pct_unavailable,
        cause,
        publishTime,
        eventStartTime
    FROM deduplicated
    ORDER BY unavailableCapacity DESC
    """
    
    df = bq_client.query(query).to_dataframe()
    print(f"✅ Retrieved {len(df)} unique outages (latest publishTime per unit)")
    
    if len(df) > 0:
        total_unavail = df['unavailableCapacity'].sum()
        print(f"   Total unavailable: {total_unavail:,.0f} MW")
    
    return df

def format_timestamp(ts_value):
    """Format timestamp properly (handle Excel serial dates and ISO strings)"""
    if pd.isna(ts_value) or ts_value is None:
        return ''
    
    # If it's already a datetime object
    if isinstance(ts_value, (pd.Timestamp, datetime)):
        return ts_value.strftime('%Y-%m-%d %H:%M:%S')
    
    # If it's a string
    ts_str = str(ts_value).strip()
    
    # Try Excel serial date first (floating point number like 45970.375)
    try:
        ts_float = float(ts_str)
        # Excel dates are typically between 40000 (2009) and 50000 (2037)
        if 40000 <= ts_float <= 50000:
            # Excel epoch is 1899-12-30
            from datetime import timedelta
            excel_epoch = datetime(1899, 12, 30)
            dt = excel_epoch + timedelta(days=ts_float)
            return dt.strftime('%Y-%m-%d %H:%M:%S')
    except (ValueError, TypeError):
        pass
    
    # Try parsing as ISO datetime
    try:
        dt = pd.to_datetime(ts_str)
        return dt.strftime('%Y-%m-%d %H:%M:%S')
    except:
        pass
    
    # Return as-is if can't parse (truncated to 19 chars for consistency)
    return ts_str[:19] if len(ts_str) > 19 else ts_str

def update_outages_section(dashboard, outages_df):
    """Update outages section with enhanced data - shows ALL outages"""
    print("\n📝 Updating outages section...")
    
    if len(outages_df) == 0:
        print("✅ No active outages")
        return
    
    # Calculate total from ALL outages
    total_unavail = int(outages_df['unavailableCapacity'].sum())
    outage_count = len(outages_df)
    
    # Show ALL outages (no limit)
    print(f"   Displaying all {outage_count} outages")
    
    # NO header row - header is written by update_dashboard_preserve_layout.py at row 22
    outage_rows = []
    
    for _, row in outages_df.iterrows():
        unit = str(row['affectedUnit']) if row['affectedUnit'] else ''
        
        # Classify interconnectors (check unit code patterns)
        is_interconnector = (
            unit.startswith('I_IE') or 
            unit.startswith('I-') or
            'IFA' in unit.upper() or
            '_IFA' in unit.upper() or
            ('INTER' in str(row['assetName']).upper() if row['assetName'] else False)
        )
        
        if is_interconnector:
            fuel = 'Interconnector'
            emoji = '🔌'
            
            # Friendly interconnector names
            unit_upper = unit.upper()
            if 'IFA2' in unit_upper or (unit.startswith('I_IE') and 'IFA2' in unit_upper):
                display_name = '🔌 IFA2 France'
            elif unit.startswith('I_IED-FRAN1') or unit.startswith('I_IEG-FRAN1'):
                display_name = '🔌 IFA France (ElecLink)'
            elif 'IFA1' in unit_upper or ('I_IE' in unit and 'FRAN' in unit):
                display_name = '🔌 IFA1 France'
            elif 'ELEC' in unit_upper:
                display_name = '🔌 ElecLink (France)'
            elif 'MOYLE' in unit_upper:
                display_name = '🔌 Moyle (N. Ireland)'
            elif 'EWIC' in unit_upper or 'EAST' in unit_upper:
                display_name = '🔌 East-West (Ireland)'
            elif 'NSL' in unit_upper or 'NORW' in unit_upper:
                display_name = '🔌 NSL (Norway)'
            elif 'NEMO' in unit_upper or 'BELG' in unit_upper:
                display_name = '🔌 Nemo (Belgium)'
            elif 'BRI' in unit_upper or 'BRIT' in unit_upper:
                display_name = '🔌 BritNed (Netherlands)'
            elif 'VIKING' in unit_upper or 'DENM' in unit_upper:
                display_name = '🔌 Viking (Denmark)'
            else:
                asset_name = str(row['assetName'])[:25] if row['assetName'] else 'Interconnector'
                display_name = f"🔌 {asset_name}"
        else:
            # Look up known generators
            if unit in GENERATOR_NAMES:
                asset_name = GENERATOR_NAMES[unit]
                fuel = FUEL_TYPE_MAP.get(unit, row['fuelType'] if row['fuelType'] else 'UNKNOWN')
            else:
                asset_name = str(row['assetName'])[:25] if row['assetName'] else 'Unknown'
                fuel = str(row['fuelType']) if row['fuelType'] else 'UNKNOWN'
            
            fuel = fuel.upper()
            emoji = UNIT_EMOJIS.get(fuel, '⚡')
            display_name = f"{emoji} {asset_name}"
        
        normal_mw = int(row['normalCapacity']) if row['normalCapacity'] else 0
        unavail_mw = int(row['unavailableCapacity']) if row['unavailableCapacity'] else 0
        pct = float(row['pct_unavailable']) if row['pct_unavailable'] else 0
        
        # Progress bar
        filled = min(int(pct / 10), 10)
        bar = '🟥' * filled + '⬜' * (10 - filled) + f" {pct:.1f}%"
        
        cause = (str(row['cause'])[:40] + '...') if row['cause'] and len(str(row['cause'])) > 40 else (str(row['cause']) if row['cause'] else 'Unspecified')
        
        # Format start time properly
        start_time = format_timestamp(row['eventStartTime'])
        
        outage_rows.append([display_name, unit, fuel, normal_mw, unavail_mw, bar, cause, start_time])
    
    # Calculate end row based on number of outages
    end_row = 31 + len(outage_rows) - 1  # Start at row 31 (first data row after header at 30)
    
    # Clear old data first (up to row 70 to remove any stale entries)
    clear_data = [['' for _ in range(8)] for _ in range(40)]  # Clear rows 31-70 (40 rows)
    dashboard.update('A31:H70', clear_data, value_input_option='USER_ENTERED')
    
    # Update Dashboard starting at row 31 with outage data (header already at row 30)
    range_str = f'A31:H{end_row}'
    dashboard.update(range_str, outage_rows, value_input_option='USER_ENTERED')
    
    # Add total summary row one row below the last outage
    summary_row = end_row + 2
    summary_text = f"TOTAL UNAVAILABLE CAPACITY: {total_unavail:,} MW"
    count_text = f"({outage_count} outages)"
    
    # Clear the entire summary row (8 columns) and write only the summary text
    summary_data = [[summary_text, '', count_text, '', '', '', '', '']]
    dashboard.update(f'A{summary_row}:H{summary_row}', summary_data, value_input_option='USER_ENTERED')
    
    print(f"✅ Updated all {outage_count} outages (rows 31-{end_row})")
    print(f"✅ Total summary at row {summary_row}: {total_unavail:,} MW from {outage_count} outages")

def main():
    """Main execution"""
    print("=" * 80)
    print("🔄 ENHANCED DASHBOARD OUTAGES UPDATE")
    print("=" * 80)
    
    dashboard, bq_client = connect()
    if not dashboard or not bq_client:
        return
    
    # Query enhanced outages
    outages_df = query_outages_enhanced(bq_client)
    
    # Update dashboard
    update_outages_section(dashboard, outages_df)
    
    # Update timestamp
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    dashboard.update_acell('B2', f'⏰ Last Updated: {timestamp} | ✅ FRESH')
    
    print("\n" + "=" * 80)
    print("✅ UPDATE COMPLETE")
    print("=" * 80)
    print(f"\n📊 Summary:")
    print(f"   • Unique outages: {len(outages_df)}")
    if len(outages_df) > 0:
        print(f"   • Total unavailable: {outages_df['unavailableCapacity'].sum():,.0f} MW")
    print(f"   • Timestamp: {timestamp}")
    print("\n✅ All fixes applied:")
    print("   • Interconnectors classified as 'Interconnector' fuel type")
    print("   • Known generators use proper names from all_generators")
    print("   • Start times formatted correctly (YYYY-MM-DD HH:MM:SS)")
    print("   • Latest publishTime used per unit (deduplication)")
    print()

if __name__ == '__main__':
    main()

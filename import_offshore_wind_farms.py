#!/usr/bin/env python3
"""
Import and update offshore wind farm data from Wikipedia list
Cross-reference with BMU registration data
Upload to BigQuery offshore_wind_farms table
"""

import os
import pandas as pd
from google.cloud import bigquery
from datetime import datetime
import re

# Configuration
PROJECT_ID = "inner-cinema-476211-u9"
DATASET = "uk_energy_prod"
TABLE = "offshore_wind_farms"

os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'inner-cinema-credentials.json'

# Wikipedia offshore wind farm data (July 2025)
OFFSHORE_WIND_DATA = [
    # Format: Name, Country, Lat, Lon, Capacity_MW, Turbines, Manufacturer, Model, Year, Strike_Price, Owner
    ("Barrow", "England", 53.983333, -3.283333, 90, 30, "Vestas", "V90-3.0MW", 2006, None, "Ørsted"),
    ("Beatrice", "Scotland", 58.105556, -3.092778, 10, 2, "REpower", "5M", 2007, None, "SSE, Talisman Energy"),
    ("Beatrice extension", "Scotland", 58.105556, -3.092778, 588, 84, "Siemens Gamesa", "SWT-7.0-154", 2019, 140, "SSE, Talisman Energy"),
    ("Blyth Offshore Demonstrator", "England", None, None, 41.5, 5, "Vestas", "V164-8MW", 2017, None, "EDF Renewables"),
    ("Burbo Bank", "England", 53.483333, -3.183333, 90, 25, "Siemens", "SWT-3.6-107", 2007, None, "Ørsted"),
    ("Burbo Bank Extension", "England", 53.483333, -3.183333, 258, 32, "Vestas", "V164 8.0 MW", 2017, None, "Ørsted"),
    ("Dudgeon", "England", 53.25, 1.383333, 402, 67, "Siemens", "SWT-6.0-154", 2017, None, "Equinor, Statkraft"),
    ("East Anglia One", "England", 52.234444, 2.488333, 714, 102, "Siemens", "SWT-7.0-154", 2020, 119.89, None),
    ("European Offshore Wind Deployment Centre", "Scotland", 57.216667, -1.983333, 93, 11, "Vestas", "V164 8MW", 2018, None, "EOWDC"),
    ("Galloper", "England", None, None, 353, 56, "Siemens", "SWT-6.0-154", 2018, None, "RWE"),
    ("Greater Gabbard", "England", 51.933333, 1.883333, 504, 140, "Siemens", "SWT-3.6-107", 2012, None, "SSE Renewables"),
    ("Gunfleet Sands 1 & 2", "England", 51.716667, 1.213889, 172, 48, "Siemens", "SWT-3.6-107", 2010, None, "Ørsted"),
    ("Gunfleet Sands 3", "England", 51.716667, 1.213889, 12, 2, "Siemens", "SWT-6.0-120", 2013, None, "Ørsted"),
    ("Gwynt y Môr", "Wales", 53.45, -3.583333, 576, 160, "Siemens", "SWT-3.6-107", 2015, None, "RWE Npower, Stadtwerke München"),
    ("Hornsea One", "England", 53.885, 1.791111, 1218, 174, "Siemens", "SWT-7.0-154", 2020, 140, "Ørsted, Global Infrastructure Partners"),
    ("Hornsea Two", "England", 53.885, 1.791111, 1386, 165, "Siemens", "SG 8.0-167 DD", 2022, 57.50, "Ørsted, Global Infrastructure Partners"),
    ("Humber Gateway", "England", 53.643889, 0.292778, 219, 73, "Vestas", "V112 3.0MW", 2015, None, "E.ON"),
    ("Hywind Scotland", "Scotland", 57.483333, -1.35, 30, 5, "Siemens", "SWT-6.0-154", 2017, None, "Equinor, Masdar"),
    ("Kentish Flats", "England", 51.46, 1.09, 140, 30, "Vestas", "V90-3.0MW / V112-3.3MW", 2005, None, "Vattenfall"),
    ("Kincardine", "Scotland", 57.006111, -1.852222, 49.5, 6, "Vestas", "V164-9.5 MW / V80-2 MW", 2021, None, "Principle Power, Flotation Energy"),
    ("Lincs", "England", 53.183333, 0.483333, 270, 75, "Siemens", "SWT-3.6-120", 2013, None, "Centrica, Siemens, Ørsted"),
    ("London Array", "England", 51.643889, 1.553611, 630, 175, "Siemens", "SWT-3.6-107", 2013, None, "Ørsted, E.ON UK, Masdar"),
    ("Lynn and Inner Dowsing", "England", 53.127778, 0.436111, 194, 54, "Siemens", "SWP-3.6-107", 2009, None, "Centrica 50%, TCW 50%"),
    ("Methil", "Scotland", 56.162778, -3.008889, 7, 1, "Samsung", "7 MW", 2013, None, "Samsung, 2-B Energy"),
    ("Moray East", "Scotland", 58.1, -2.8, 950, 100, "Vestas", "V164-9.5 MW", 2022, 57.50, "Ocean Winds"),
    ("Moray West", "Scotland", 58.1, -3.1, 882, 60, "Siemens Gamesa", "SG 14-222 DD", 2025, 37.35, "Ocean Winds"),
    ("Neart Na Gaoithe", "Scotland", 56.267778, -2.320833, 450, 54, "Siemens Gamesa", "SG 8.0-167 DD", 2025, 114.39, "EDF R / ESB"),
    ("North Hoyle", "Wales", 53.433333, -3.4, 60, 30, "Vestas", "V80-2MW", 2003, None, "Greencoat UK Wind"),
    ("Ormonde", "England", 54.1, -3.4, 150, 30, "REpower", "5MW", 2012, None, "Vattenfall"),
    ("Race Bank", "England", 53.275, 0.841667, 580, 91, "Siemens", "SWT-6.0-154", 2018, None, "Ørsted"),
    ("Rampion", "England", 50.666667, -0.266667, 400, 116, "Vestas", "V112-3.45MW", 2018, None, "E.ON"),
    ("Rhyl Flats", "Wales", 53.366667, -3.65, 90, 25, "Siemens", "SWT-3.6-107", 2009, None, "RWE Npower"),
    ("Robin Rigg", "Scotland", 54.75, -3.716667, 180, 60, "Vestas", "V90-3.0MW", 2010, None, "E.ON"),
    ("Scroby Sands", "England", 52.633333, 1.783333, 60, 30, "Vestas", "V80-2MW", 2004, None, "E.ON"),
    ("Seagreen Phase 1", "Scotland", 56.584889, -1.759278, 1400, 114, "Vestas", "V164-10.0 MW", 2023, 41.61, "SSE Renewables, TotalEnergies"),
    ("Sheringham Shoal", "England", 53.116667, 1.133333, 317, 88, "Siemens", "SWT-3.6-107", 2012, None, "Equinor 50%, Statkraft 50%"),
    ("Teesside", "England", 54.647222, -1.094444, 62, 27, "Siemens", "SWT-2.3-93", 2013, None, "EDF-EN"),
    ("Thanet", "England", 51.433333, 1.633333, 300, 100, "Vestas", "V90-3.0MW", 2010, None, "Vattenfall"),
    ("Triton Knoll", "England", 53.5, 0.8, 857, 90, "Vestas", "V164-9.5 MW", 2022, 74.75, "RWE"),
    ("Walney", "England", 54.05, -3.516667, 367, 102, "Siemens", "SWT-3.6-107", 2010, None, "Ørsted, SSE, OPW"),
    ("Walney Extension", "England", 54.087778, -3.738056, 659, 87, "Siemens / Vestas", "SWT-7.0-154 / V164-8.25", 2018, 150.00, "Ørsted"),
    ("Westermost Rough", "England", 53.805, 0.148889, 210, 35, "Siemens", "SWT-6.0-154", 2015, None, "Ørsted, Marubeni, GIB"),
    ("West of Duddon Sands", "England", 53.983333, -3.466667, 389, 108, "Siemens", "SWT-3.6-120", 2014, None, "Ørsted, Scottish Power"),
]


def create_dataframe():
    """Create DataFrame from offshore wind data"""
    df = pd.DataFrame(OFFSHORE_WIND_DATA, columns=[
        'name', 'country', 'latitude', 'longitude', 'capacity_mw', 
        'turbine_count', 'manufacturer', 'model', 'commissioned_year',
        'strike_price', 'owner'
    ])
    
    # Add metadata
    df['status'] = 'Operational'
    df['source'] = 'Wikipedia UK offshore wind farms (July 2025)'
    df['_uploaded_at'] = datetime.utcnow()
    
    # Assign GSP regions based on location
    df['gsp_zone'] = None
    df['gsp_region'] = None
    
    # Map to GSP zones (approximate)
    for idx, row in df.iterrows():
        if pd.isna(row['latitude']):
            continue
            
        lat, lon = row['latitude'], row['longitude']
        
        # Scotland North
        if row['country'] == 'Scotland' and lat > 57.5:
            df.at[idx, 'gsp_zone'] = 'SCO2'
            df.at[idx, 'gsp_region'] = 'Scotland North'
        # Scotland South
        elif row['country'] == 'Scotland':
            df.at[idx, 'gsp_zone'] = 'SCO1'
            df.at[idx, 'gsp_region'] = 'Scotland South'
        # Yorkshire/East Coast
        elif lon > 0 and lat > 53:
            df.at[idx, 'gsp_zone'] = 'YEA1'
            df.at[idx, 'gsp_region'] = 'Yorkshire East'
        # East Anglia
        elif lon > 0 and lat < 53:
            df.at[idx, 'gsp_zone'] = 'EEA1'
            df.at[idx, 'gsp_region'] = 'East Anglia'
        # North Wales / Irish Sea
        elif lon < 0 and lat > 53:
            df.at[idx, 'gsp_zone'] = 'NWA1'
            df.at[idx, 'gsp_region'] = 'North Wales'
        # South East
        elif lon < 2 and lat < 52:
            df.at[idx, 'gsp_zone'] = 'SEE1'
            df.at[idx, 'gsp_region'] = 'South East'
    
    return df


def get_bmu_wind_data():
    """Get wind generator data from BMU registration"""
    client = bigquery.Client(project=PROJECT_ID, location='US')
    
    query = f"""
    SELECT 
        nationalgridbmunit as bmu_id,
        bmunitname as name,
        generationcapacity as capacity_mw,
        leadpartyname as operator,
        gspgroupid,
        gspgroupname
    FROM `{PROJECT_ID}.{DATASET}.bmu_registration_data`
    WHERE fueltype = 'WIND'
    ORDER BY generationcapacity DESC
    """
    
    return client.query(query).to_dataframe()


def cross_reference_data(offshore_df, bmu_df):
    """Cross-reference offshore wind farms with BMU data"""
    print("\n" + "="*80)
    print("CROSS-REFERENCE ANALYSIS: Offshore Wind Farms vs BMU Registration")
    print("="*80)
    
    # Find potential matches by name similarity
    matches = []
    missing_from_bmu = []
    
    for _, offshore in offshore_df.iterrows():
        offshore_name = offshore['name'].lower()
        
        # Try to find BMU match
        bmu_match = bmu_df[bmu_df['name'].str.lower().str.contains(offshore_name.split()[0], na=False)]
        
        if len(bmu_match) > 0:
            match_info = {
                'offshore_name': offshore['name'],
                'offshore_capacity': offshore['capacity_mw'],
                'bmu_id': bmu_match.iloc[0]['bmu_id'],
                'bmu_name': bmu_match.iloc[0]['name'],
                'bmu_capacity': bmu_match.iloc[0]['capacity_mw'],
                'capacity_diff': abs(offshore['capacity_mw'] - bmu_match.iloc[0]['capacity_mw'])
            }
            matches.append(match_info)
        else:
            missing_from_bmu.append({
                'name': offshore['name'],
                'capacity_mw': offshore['capacity_mw'],
                'commissioned': offshore['commissioned_year'],
                'owner': offshore['owner']
            })
    
    # Print matches
    print(f"\n✅ Found {len(matches)} potential BMU matches:")
    if matches:
        match_df = pd.DataFrame(matches).head(10)
        print(match_df.to_string(index=False))
    
    # Print missing
    print(f"\n❌ {len(missing_from_bmu)} offshore farms NOT found in BMU:")
    if missing_from_bmu:
        missing_df = pd.DataFrame(missing_from_bmu)
        print(missing_df.to_string(index=False))
    
    # Summary stats
    total_offshore_capacity = offshore_df['capacity_mw'].sum()
    total_bmu_capacity = bmu_df['capacity_mw'].sum()
    matched_capacity = sum(m['offshore_capacity'] for m in matches)
    missing_capacity = sum(m['capacity_mw'] for m in missing_from_bmu)
    
    print(f"\n📊 SUMMARY:")
    print(f"   Wikipedia Offshore Wind: {len(offshore_df)} farms, {total_offshore_capacity:,.0f} MW")
    print(f"   BMU Wind (all types): {len(bmu_df)} units, {total_bmu_capacity:,.0f} MW")
    print(f"   Matched offshore: {len(matches)} farms, {matched_capacity:,.0f} MW")
    print(f"   Missing from BMU: {len(missing_from_bmu)} farms, {missing_capacity:,.0f} MW")
    
    return matches, missing_from_bmu


def upload_to_bigquery(df):
    """Upload offshore wind data to BigQuery"""
    client = bigquery.Client(project=PROJECT_ID, location='US')
    
    table_id = f"{PROJECT_ID}.{DATASET}.{TABLE}"
    
    # Configure job
    job_config = bigquery.LoadJobConfig(
        write_disposition="WRITE_TRUNCATE",  # Replace existing data
        schema=[
            bigquery.SchemaField("name", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("country", "STRING"),
            bigquery.SchemaField("latitude", "FLOAT64"),
            bigquery.SchemaField("longitude", "FLOAT64"),
            bigquery.SchemaField("capacity_mw", "FLOAT64"),
            bigquery.SchemaField("turbine_count", "INT64"),
            bigquery.SchemaField("manufacturer", "STRING"),
            bigquery.SchemaField("model", "STRING"),
            bigquery.SchemaField("commissioned_year", "INT64"),
            bigquery.SchemaField("strike_price", "FLOAT64"),
            bigquery.SchemaField("owner", "STRING"),
            bigquery.SchemaField("status", "STRING"),
            bigquery.SchemaField("source", "STRING"),
            bigquery.SchemaField("gsp_zone", "STRING"),
            bigquery.SchemaField("gsp_region", "STRING"),
            bigquery.SchemaField("_uploaded_at", "TIMESTAMP"),
        ]
    )
    
    # Upload
    print(f"\n📤 Uploading {len(df)} offshore wind farms to BigQuery...")
    job = client.load_table_from_dataframe(df, table_id, job_config=job_config)
    job.result()  # Wait for completion
    
    print(f"✅ Successfully uploaded to {table_id}")
    print(f"   Total capacity: {df['capacity_mw'].sum():,.0f} MW")
    print(f"   Total turbines: {df['turbine_count'].sum():,}")
    
    return table_id


def main():
    print("="*80)
    print("OFFSHORE WIND FARM DATA IMPORT")
    print("="*80)
    
    # Create DataFrame from Wikipedia data
    print("\n📋 Creating DataFrame from Wikipedia offshore wind data...")
    offshore_df = create_dataframe()
    print(f"✅ Loaded {len(offshore_df)} offshore wind farms")
    print(f"   Total capacity: {offshore_df['capacity_mw'].sum():,.0f} MW")
    print(f"   Total turbines: {offshore_df['turbine_count'].sum():,}")
    
    # Show sample
    print("\n📊 Sample data:")
    print(offshore_df.head(5)[['name', 'capacity_mw', 'turbine_count', 'commissioned_year', 'gsp_region']].to_string(index=False))
    
    # Get BMU data
    print("\n🔌 Fetching BMU wind generator data...")
    bmu_df = get_bmu_wind_data()
    print(f"✅ Found {len(bmu_df)} BMU-registered wind units")
    
    # Cross-reference
    matches, missing = cross_reference_data(offshore_df, bmu_df)
    
    # Upload to BigQuery
    response = input("\n📤 Upload to BigQuery? (yes/no): ")
    if response.lower() in ['yes', 'y']:
        table_id = upload_to_bigquery(offshore_df)
        
        # Save to CSV backup
        csv_file = f"offshore_wind_farms_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        offshore_df.to_csv(csv_file, index=False)
        print(f"💾 Backup saved to {csv_file}")
    else:
        print("⏭️  Skipped BigQuery upload")
    
    print("\n✅ COMPLETE!")


if __name__ == "__main__":
    main()

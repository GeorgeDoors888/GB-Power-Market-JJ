#!/usr/bin/env python3
"""
Add Turbine Specifications to BigQuery - Todo #2
Creates wind_turbine_specs table with detailed turbine metadata for all 29 farms

Author: AI Coding Agent
Date: December 30, 2025
"""

from google.cloud import bigquery
import pandas as pd

PROJECT_ID = "inner-cinema-476211-u9"
DATASET = "uk_energy_prod"

# Turbine specifications for UK offshore wind farms
# Sources: 4COffshore, manufacturer specs, NESO publications
TURBINE_SPECS = [
    # Farm, Manufacturer, Model, Hub Height (m), Rotor Diam (m), Rated Cap (MW), Cut-in (m/s), Rated (m/s), Cut-out (m/s), Ice Protection, Turbine Count
    {"farm_name": "Hornsea One", "manufacturer": "Siemens Gamesa", "model": "SWT-7.0-154", "hub_height_m": 105, "rotor_diameter_m": 154, "rated_capacity_mw": 7.0, "cut_in_speed_ms": 3.0, "rated_speed_ms": 13.0, "cut_out_speed_ms": 25.0, "has_ice_protection": True, "turbine_count": 174},
    {"farm_name": "Hornsea Two", "manufacturer": "Siemens Gamesa", "model": "SG 8.0-167 DD", "hub_height_m": 108, "rotor_diameter_m": 167, "rated_capacity_mw": 8.0, "cut_in_speed_ms": 3.0, "rated_speed_ms": 13.0, "cut_out_speed_ms": 25.0, "has_ice_protection": True, "turbine_count": 165},
    {"farm_name": "Seagreen Phase 1", "manufacturer": "Vestas", "model": "V164-10.0 MW", "hub_height_m": 112, "rotor_diameter_m": 164, "rated_capacity_mw": 10.0, "cut_in_speed_ms": 3.5, "rated_speed_ms": 12.5, "cut_out_speed_ms": 25.0, "has_ice_protection": True, "turbine_count": 114},
    {"farm_name": "Triton Knoll", "manufacturer": "Vestas", "model": "V164-9.5 MW", "hub_height_m": 112, "rotor_diameter_m": 164, "rated_capacity_mw": 9.5, "cut_in_speed_ms": 3.5, "rated_speed_ms": 12.5, "cut_out_speed_ms": 25.0, "has_ice_protection": True, "turbine_count": 90},
    {"farm_name": "Moray East", "manufacturer": "Siemens Gamesa", "model": "SG 8.4-167 DD", "hub_height_m": 111, "rotor_diameter_m": 167, "rated_capacity_mw": 8.4, "cut_in_speed_ms": 3.0, "rated_speed_ms": 13.0, "cut_out_speed_ms": 25.0, "has_ice_protection": True, "turbine_count": 100},
    {"farm_name": "Moray West", "manufacturer": "Siemens Gamesa", "model": "SG 14-222 DD", "hub_height_m": 125, "rotor_diameter_m": 222, "rated_capacity_mw": 14.7, "cut_in_speed_ms": 3.0, "rated_speed_ms": 12.0, "cut_out_speed_ms": 25.0, "has_ice_protection": True, "turbine_count": 60},
    {"farm_name": "East Anglia One", "manufacturer": "Siemens Gamesa", "model": "SWT-7.0-154", "hub_height_m": 105, "rotor_diameter_m": 154, "rated_capacity_mw": 7.0, "cut_in_speed_ms": 3.0, "rated_speed_ms": 13.0, "cut_out_speed_ms": 25.0, "has_ice_protection": True, "turbine_count": 102},
    {"farm_name": "Rampion", "manufacturer": "Vestas", "model": "V112-3.45 MW", "hub_height_m": 98, "rotor_diameter_m": 112, "rated_capacity_mw": 3.45, "cut_in_speed_ms": 3.0, "rated_speed_ms": 12.0, "cut_out_speed_ms": 25.0, "has_ice_protection": False, "turbine_count": 116},
    {"farm_name": "Race Bank", "manufacturer": "Siemens Gamesa", "model": "SWT-6.0-154", "hub_height_m": 105, "rotor_diameter_m": 154, "rated_capacity_mw": 6.0, "cut_in_speed_ms": 3.0, "rated_speed_ms": 13.0, "cut_out_speed_ms": 25.0, "has_ice_protection": True, "turbine_count": 91},
    {"farm_name": "Walney Extension", "manufacturer": "Vestas", "model": "V164-8.25 MW", "hub_height_m": 112, "rotor_diameter_m": 164, "rated_capacity_mw": 8.25, "cut_in_speed_ms": 3.5, "rated_speed_ms": 12.5, "cut_out_speed_ms": 25.0, "has_ice_protection": True, "turbine_count": 87},
    {"farm_name": "London Array", "manufacturer": "Siemens", "model": "SWT-3.6-120", "hub_height_m": 87, "rotor_diameter_m": 120, "rated_capacity_mw": 3.6, "cut_in_speed_ms": 3.0, "rated_speed_ms": 13.0, "cut_out_speed_ms": 25.0, "has_ice_protection": False, "turbine_count": 175},
    {"farm_name": "Beatrice extension", "manufacturer": "Siemens Gamesa", "model": "SWT-7.0-154", "hub_height_m": 105, "rotor_diameter_m": 154, "rated_capacity_mw": 7.0, "cut_in_speed_ms": 3.0, "rated_speed_ms": 13.0, "cut_out_speed_ms": 25.0, "has_ice_protection": True, "turbine_count": 84},
    {"farm_name": "Greater Gabbard", "manufacturer": "Siemens", "model": "SWT-3.6-107", "hub_height_m": 74, "rotor_diameter_m": 107, "rated_capacity_mw": 3.6, "cut_in_speed_ms": 3.0, "rated_speed_ms": 13.0, "cut_out_speed_ms": 25.0, "has_ice_protection": False, "turbine_count": 140},
    {"farm_name": "Dudgeon", "manufacturer": "Siemens", "model": "SWT-6.0-154", "hub_height_m": 105, "rotor_diameter_m": 154, "rated_capacity_mw": 6.0, "cut_in_speed_ms": 3.0, "rated_speed_ms": 13.0, "cut_out_speed_ms": 25.0, "has_ice_protection": True, "turbine_count": 67},
    {"farm_name": "Sheringham Shoal", "manufacturer": "Siemens", "model": "SWT-3.6-107", "hub_height_m": 74, "rotor_diameter_m": 107, "rated_capacity_mw": 3.6, "cut_in_speed_ms": 3.0, "rated_speed_ms": 13.0, "cut_out_speed_ms": 25.0, "has_ice_protection": False, "turbine_count": 88},
    {"farm_name": "Thanet", "manufacturer": "Vestas", "model": "V90-3.0 MW", "hub_height_m": 70, "rotor_diameter_m": 90, "rated_capacity_mw": 3.0, "cut_in_speed_ms": 3.5, "rated_speed_ms": 15.0, "cut_out_speed_ms": 25.0, "has_ice_protection": False, "turbine_count": 100},
    {"farm_name": "Lincs", "manufacturer": "Siemens", "model": "SWT-3.6-120", "hub_height_m": 87, "rotor_diameter_m": 120, "rated_capacity_mw": 3.6, "cut_in_speed_ms": 3.0, "rated_speed_ms": 13.0, "cut_out_speed_ms": 25.0, "has_ice_protection": False, "turbine_count": 75},
    {"farm_name": "Gunfleet Sands 1 & 2", "manufacturer": "Siemens", "model": "SWT-3.6-107", "hub_height_m": 74, "rotor_diameter_m": 107, "rated_capacity_mw": 3.6, "cut_in_speed_ms": 3.0, "rated_speed_ms": 13.0, "cut_out_speed_ms": 25.0, "has_ice_protection": False, "turbine_count": 48},
    {"farm_name": "West of Duddon Sands", "manufacturer": "Siemens", "model": "SWT-3.6-120", "hub_height_m": 87, "rotor_diameter_m": 120, "rated_capacity_mw": 3.6, "cut_in_speed_ms": 3.0, "rated_speed_ms": 13.0, "cut_out_speed_ms": 25.0, "has_ice_protection": False, "turbine_count": 108},
    {"farm_name": "Walney", "manufacturer": "Siemens", "model": "SWT-3.6-107", "hub_height_m": 74, "rotor_diameter_m": 107, "rated_capacity_mw": 3.6, "cut_in_speed_ms": 3.0, "rated_speed_ms": 13.0, "cut_out_speed_ms": 25.0, "has_ice_protection": False, "turbine_count": 102},
    {"farm_name": "Ormonde", "manufacturer": "REpower", "model": "5M", "hub_height_m": 92, "rotor_diameter_m": 126, "rated_capacity_mw": 5.0, "cut_in_speed_ms": 3.5, "rated_speed_ms": 13.0, "cut_out_speed_ms": 25.0, "has_ice_protection": False, "turbine_count": 30},
    {"farm_name": "Humber Gateway", "manufacturer": "Vestas", "model": "V112-3.0 MW", "hub_height_m": 94, "rotor_diameter_m": 112, "rated_capacity_mw": 3.0, "cut_in_speed_ms": 3.0, "rated_speed_ms": 12.0, "cut_out_speed_ms": 25.0, "has_ice_protection": False, "turbine_count": 73},
    {"farm_name": "Burbo Bank Extension", "manufacturer": "MHI Vestas", "model": "V164-8.0 MW", "hub_height_m": 112, "rotor_diameter_m": 164, "rated_capacity_mw": 8.0, "cut_in_speed_ms": 3.5, "rated_speed_ms": 12.5, "cut_out_speed_ms": 25.0, "has_ice_protection": True, "turbine_count": 32},
    {"farm_name": "Burbo Bank", "manufacturer": "Siemens", "model": "SWT-3.6-107", "hub_height_m": 74, "rotor_diameter_m": 107, "rated_capacity_mw": 3.6, "cut_in_speed_ms": 3.0, "rated_speed_ms": 13.0, "cut_out_speed_ms": 25.0, "has_ice_protection": False, "turbine_count": 25},
    {"farm_name": "Barrow", "manufacturer": "Vestas", "model": "V90-3.0 MW", "hub_height_m": 70, "rotor_diameter_m": 90, "rated_capacity_mw": 3.0, "cut_in_speed_ms": 3.5, "rated_speed_ms": 15.0, "cut_out_speed_ms": 25.0, "has_ice_protection": False, "turbine_count": 30},
    {"farm_name": "Westermost Rough", "manufacturer": "Siemens", "model": "SWT-6.0-154", "hub_height_m": 105, "rotor_diameter_m": 154, "rated_capacity_mw": 6.0, "cut_in_speed_ms": 3.0, "rated_speed_ms": 13.0, "cut_out_speed_ms": 25.0, "has_ice_protection": True, "turbine_count": 35},
    {"farm_name": "Neart Na Gaoithe", "manufacturer": "Siemens Gamesa", "model": "SG 8.0-167 DD", "hub_height_m": 108, "rotor_diameter_m": 167, "rated_capacity_mw": 8.0, "cut_in_speed_ms": 3.0, "rated_speed_ms": 13.0, "cut_out_speed_ms": 25.0, "has_ice_protection": True, "turbine_count": 54},
    {"farm_name": "Hywind Scotland", "manufacturer": "Siemens Gamesa", "model": "SWT-6.0-154 (Floating)", "hub_height_m": 105, "rotor_diameter_m": 154, "rated_capacity_mw": 6.0, "cut_in_speed_ms": 3.0, "rated_speed_ms": 13.0, "cut_out_speed_ms": 25.0, "has_ice_protection": True, "turbine_count": 5},
    {"farm_name": "Kincardine", "manufacturer": "Vestas", "model": "V164-9.5 MW (Floating)", "hub_height_m": 112, "rotor_diameter_m": 164, "rated_capacity_mw": 9.5, "cut_in_speed_ms": 3.5, "rated_speed_ms": 12.5, "cut_out_speed_ms": 25.0, "has_ice_protection": True, "turbine_count": 5},
]

def main():
    print("="*70)
    print("Adding Turbine Specifications to BigQuery - Todo #2")
    print("="*70)
    
    client = bigquery.Client(project=PROJECT_ID, location="US")
    
    # Create dataframe
    df = pd.DataFrame(TURBINE_SPECS)
    
    # Add computed fields
    df['swept_area_m2'] = (df['rotor_diameter_m'] / 2) ** 2 * 3.14159
    df['total_capacity_mw'] = df['rated_capacity_mw'] * df['turbine_count']
    df['specific_power_w_m2'] = (df['rated_capacity_mw'] * 1e6) / df['swept_area_m2']
    
    print(f"\n✅ Created specs for {len(df)} wind farms")
    print(f"   Total turbines: {df['turbine_count'].sum()}")
    print(f"   Total capacity: {df['total_capacity_mw'].sum():.0f} MW")
    print(f"\nManufacturer breakdown:")
    print(df.groupby('manufacturer')['turbine_count'].sum().sort_values(ascending=False))
    
    # Upload to BigQuery
    table_id = f"{PROJECT_ID}.{DATASET}.wind_turbine_specs"
    
    job_config = bigquery.LoadJobConfig(
        write_disposition="WRITE_TRUNCATE",
        schema=[
            bigquery.SchemaField("farm_name", "STRING"),
            bigquery.SchemaField("manufacturer", "STRING"),
            bigquery.SchemaField("model", "STRING"),
            bigquery.SchemaField("hub_height_m", "FLOAT64"),
            bigquery.SchemaField("rotor_diameter_m", "FLOAT64"),
            bigquery.SchemaField("rated_capacity_mw", "FLOAT64"),
            bigquery.SchemaField("cut_in_speed_ms", "FLOAT64"),
            bigquery.SchemaField("rated_speed_ms", "FLOAT64"),
            bigquery.SchemaField("cut_out_speed_ms", "FLOAT64"),
            bigquery.SchemaField("has_ice_protection", "BOOL"),
            bigquery.SchemaField("turbine_count", "INT64"),
            bigquery.SchemaField("swept_area_m2", "FLOAT64"),
            bigquery.SchemaField("total_capacity_mw", "FLOAT64"),
            bigquery.SchemaField("specific_power_w_m2", "FLOAT64"),
        ]
    )
    
    job = client.load_table_from_dataframe(df, table_id, job_config=job_config)
    job.result()
    
    print(f"\n✅ Uploaded to {table_id}")
    print(f"   Rows: {len(df)}")
    print("\n" + "="*70)
    print("✅ TODO #2 COMPLETE - Turbine specs in BigQuery")
    print("="*70)

if __name__ == "__main__":
    main()

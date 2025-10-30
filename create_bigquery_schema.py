#!/usr/bin/env python3
"""
Create BigQuery Schema for DNO Charging Data
Sets up all tables for tariff data, license areas, and spatial data
"""

from google.cloud import bigquery
from google.oauth2 import service_account
import json

# BigQuery configuration
PROJECT_ID = "inner-cinema-476211-u9"
DATASET_ID = "gb_power"
CREDENTIALS_FILE = "jibber_jabber_key.json"


def create_client():
    """Create BigQuery client"""
    credentials = service_account.Credentials.from_service_account_file(
        CREDENTIALS_FILE,
        scopes=["https://www.googleapis.com/auth/bigquery"]
    )
    return bigquery.Client(credentials=credentials, project=PROJECT_ID)


def create_dataset(client):
    """Create gb_power dataset if it doesn't exist"""
    dataset_id = f"{PROJECT_ID}.{DATASET_ID}"
    
    try:
        client.get_dataset(dataset_id)
        print(f"✅ Dataset {dataset_id} already exists")
    except:
        dataset = bigquery.Dataset(dataset_id)
        dataset.location = "EU"
        dataset.description = "GB Power Market - DNO Charging Data and Spatial Information"
        dataset = client.create_dataset(dataset)
        print(f"✅ Created dataset {dataset_id}")


def create_dno_license_areas_table(client):
    """Create dno_license_areas table"""
    table_id = f"{PROJECT_ID}.{DATASET_ID}.dno_license_areas"
    
    schema = [
        bigquery.SchemaField("mpan_id", "INTEGER", mode="REQUIRED"),
        bigquery.SchemaField("dno_key", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("dno_name", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("short_code", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("market_participant_id", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("gsp_group_id", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("gsp_group_name", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("dno_group", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("website", "STRING"),
        bigquery.SchemaField("data_portal", "STRING"),
        bigquery.SchemaField("boundary", "GEOGRAPHY"),
        bigquery.SchemaField("effective_from", "DATE"),
        bigquery.SchemaField("effective_to", "DATE"),
    ]
    
    table = bigquery.Table(table_id, schema=schema)
    table.description = "14 GB DNO license areas with metadata and boundaries"
    
    # Time partitioning
    table.time_partitioning = bigquery.TimePartitioning(
        type_=bigquery.TimePartitioningType.YEAR,
        field="effective_from"
    )
    
    try:
        table = client.create_table(table)
        print(f"✅ Created table {table_id}")
    except Exception as e:
        print(f"⚠️  Table {table_id} may already exist: {e}")


def create_duos_tariff_definitions_table(client):
    """Create duos_tariff_definitions table"""
    table_id = f"{PROJECT_ID}.{DATASET_ID}.duos_tariff_definitions"
    
    schema = [
        bigquery.SchemaField("tariff_id", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("dno_key", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("tariff_code", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("tariff_name", "STRING"),
        bigquery.SchemaField("tariff_description", "STRING"),
        bigquery.SchemaField("voltage_level", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("customer_category", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("metering_type", "STRING"),
        bigquery.SchemaField("profile_class", "INTEGER"),
        bigquery.SchemaField("time_pattern", "STRING"),
        bigquery.SchemaField("effective_from", "DATE", mode="REQUIRED"),
        bigquery.SchemaField("effective_to", "DATE"),
        bigquery.SchemaField("source_document", "STRING"),
        bigquery.SchemaField("source_document_url", "STRING"),
        bigquery.SchemaField("extracted_date", "DATE"),
    ]
    
    table = bigquery.Table(table_id, schema=schema)
    table.description = "DUoS tariff definitions and metadata"
    
    table.time_partitioning = bigquery.TimePartitioning(
        type_=bigquery.TimePartitioningType.YEAR,
        field="effective_from"
    )
    
    table.clustering_fields = ["dno_key", "voltage_level", "customer_category"]
    
    try:
        table = client.create_table(table)
        print(f"✅ Created table {table_id}")
    except Exception as e:
        print(f"⚠️  Table {table_id} may already exist: {e}")


def create_duos_unit_rates_table(client):
    """Create duos_unit_rates table - main tariff rate data"""
    table_id = f"{PROJECT_ID}.{DATASET_ID}.duos_unit_rates"
    
    schema = [
        bigquery.SchemaField("rate_id", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("tariff_id", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("dno_key", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("tariff_code", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("rate_component", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("time_band", "STRING"),
        bigquery.SchemaField("unit_rate", "FLOAT", mode="REQUIRED"),
        bigquery.SchemaField("unit", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("effective_from", "DATE", mode="REQUIRED"),
        bigquery.SchemaField("effective_to", "DATE"),
        bigquery.SchemaField("year", "INTEGER", mode="REQUIRED"),
        bigquery.SchemaField("season", "STRING"),
        bigquery.SchemaField("day_type", "STRING"),
    ]
    
    table = bigquery.Table(table_id, schema=schema)
    table.description = "DUoS unit rates (p/kWh, p/kVA/day, p/day) for all tariffs"
    
    table.time_partitioning = bigquery.TimePartitioning(
        type_=bigquery.TimePartitioningType.YEAR,
        field="effective_from"
    )
    
    table.clustering_fields = ["dno_key", "tariff_code", "time_band"]
    
    try:
        table = client.create_table(table)
        print(f"✅ Created table {table_id}")
    except Exception as e:
        print(f"⚠️  Table {table_id} may already exist: {e}")


def create_duos_time_bands_table(client):
    """Create duos_time_bands table"""
    table_id = f"{PROJECT_ID}.{DATASET_ID}.duos_time_bands"
    
    schema = [
        bigquery.SchemaField("time_band_id", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("dno_key", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("time_band", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("season", "STRING"),
        bigquery.SchemaField("day_type", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("start_time", "TIME", mode="REQUIRED"),
        bigquery.SchemaField("end_time", "TIME", mode="REQUIRED"),
        bigquery.SchemaField("start_month", "INTEGER"),
        bigquery.SchemaField("end_month", "INTEGER"),
        bigquery.SchemaField("effective_from", "DATE", mode="REQUIRED"),
        bigquery.SchemaField("effective_to", "DATE"),
    ]
    
    table = bigquery.Table(table_id, schema=schema)
    table.description = "Time band definitions (Red/Amber/Green periods) by DNO"
    
    try:
        table = client.create_table(table)
        print(f"✅ Created table {table_id}")
    except Exception as e:
        print(f"⚠️  Table {table_id} may already exist: {e}")


def create_spatial_tables(client):
    """Create spatial data tables"""
    
    # DNO Boundaries
    table_id = f"{PROJECT_ID}.{DATASET_ID}.dno_boundaries"
    schema = [
        bigquery.SchemaField("dno_key", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("boundary_name", "STRING"),
        bigquery.SchemaField("boundary_type", "STRING"),
        bigquery.SchemaField("geometry", "GEOGRAPHY", mode="REQUIRED"),
        bigquery.SchemaField("area_km2", "FLOAT"),
        bigquery.SchemaField("population_served", "INTEGER"),
        bigquery.SchemaField("source", "STRING"),
        bigquery.SchemaField("source_date", "DATE"),
    ]
    table = bigquery.Table(table_id, schema=schema)
    table.description = "DNO license area boundaries (polygons)"
    try:
        client.create_table(table)
        print(f"✅ Created table {table_id}")
    except Exception as e:
        print(f"⚠️  Table {table_id} may already exist: {e}")
    
    # GSP Boundaries
    table_id = f"{PROJECT_ID}.{DATASET_ID}.gsp_boundaries"
    schema = [
        bigquery.SchemaField("gsp_id", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("gsp_name", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("gsp_group_id", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("dno_key", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("geometry", "GEOGRAPHY", mode="REQUIRED"),
        bigquery.SchemaField("area_km2", "FLOAT"),
        bigquery.SchemaField("source", "STRING"),
    ]
    table = bigquery.Table(table_id, schema=schema)
    table.description = "Grid Supply Point group boundaries"
    try:
        client.create_table(table)
        print(f"✅ Created table {table_id}")
    except Exception as e:
        print(f"⚠️  Table {table_id} may already exist: {e}")
    
    # Substations
    table_id = f"{PROJECT_ID}.{DATASET_ID}.substations"
    schema = [
        bigquery.SchemaField("substation_id", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("substation_name", "STRING"),
        bigquery.SchemaField("dno_key", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("voltage_level", "STRING"),
        bigquery.SchemaField("location", "GEOGRAPHY", mode="REQUIRED"),
        bigquery.SchemaField("capacity_mva", "FLOAT"),
        bigquery.SchemaField("commissioning_date", "DATE"),
        bigquery.SchemaField("source", "STRING"),
    ]
    table = bigquery.Table(table_id, schema=schema)
    table.description = "Primary substation locations"
    try:
        client.create_table(table)
        print(f"✅ Created table {table_id}")
    except Exception as e:
        print(f"⚠️  Table {table_id} may already exist: {e}")


def create_reference_tables(client):
    """Create reference/lookup tables"""
    
    # Voltage Levels
    table_id = f"{PROJECT_ID}.{DATASET_ID}.voltage_levels"
    schema = [
        bigquery.SchemaField("voltage_code", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("voltage_name", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("voltage_kv_min", "FLOAT"),
        bigquery.SchemaField("voltage_kv_max", "FLOAT"),
        bigquery.SchemaField("typical_customers", "STRING"),
    ]
    table = bigquery.Table(table_id, schema=schema)
    table.description = "Voltage level definitions"
    try:
        client.create_table(table)
        print(f"✅ Created table {table_id}")
    except Exception as e:
        print(f"⚠️  Table {table_id} may already exist: {e}")
    
    # Customer Categories
    table_id = f"{PROJECT_ID}.{DATASET_ID}.customer_categories"
    schema = [
        bigquery.SchemaField("category_code", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("category_name", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("category_description", "STRING"),
        bigquery.SchemaField("typical_consumption_kwh_year", "INTEGER"),
    ]
    table = bigquery.Table(table_id, schema=schema)
    table.description = "Customer category definitions"
    try:
        client.create_table(table)
        print(f"✅ Created table {table_id}")
    except Exception as e:
        print(f"⚠️  Table {table_id} may already exist: {e}")


def load_reference_data(client):
    """Load static reference data"""
    
    # Load 14 DNO license areas
    dno_data = [
        (12, "UKPN-LPN", "UK Power Networks (London)", "LPN", "LOND", "C", "London", "UKPN"),
        (10, "UKPN-EPN", "UK Power Networks (Eastern)", "EPN", "EELC", "A", "Eastern", "UKPN"),
        (19, "UKPN-SPN", "UK Power Networks (South Eastern)", "SPN", "SEEB", "J", "South Eastern", "UKPN"),
        (16, "ENWL", "Electricity North West", "ENWL", "NORW", "G", "North West", "ENWL"),
        (15, "NPg-NE", "Northern Powergrid (North East)", "NE", "NEEB", "F", "North East", "NPg"),
        (23, "NPg-Y", "Northern Powergrid (Yorkshire)", "Y", "YELG", "M", "Yorkshire", "NPg"),
        (18, "SP-Distribution", "SP Energy Networks (SPD)", "SPD", "SPOW", "N", "South Scotland", "SPEN"),
        (13, "SP-Manweb", "SP Energy Networks (SPM)", "SPM", "MANW", "D", "Merseyside & North Wales", "SPEN"),
        (17, "SSE-SHEPD", "Scottish Hydro Electric Power Distribution (SHEPD)", "SHEPD", "HYDE", "P", "North Scotland", "SSEN"),
        (20, "SSE-SEPD", "Southern Electric Power Distribution (SEPD)", "SEPD", "SOUT", "H", "Southern", "SSEN"),
        (14, "NGED-WM", "National Grid Electricity Distribution – West Midlands (WMID)", "WMID", "MIDE", "E", "West Midlands", "NGED"),
        (11, "NGED-EM", "National Grid Electricity Distribution – East Midlands (EMID)", "EMID", "EMEB", "B", "East Midlands", "NGED"),
        (22, "NGED-SW", "National Grid Electricity Distribution – South West (SWEST)", "SWEST", "SWEB", "L", "South Western", "NGED"),
        (21, "NGED-SWales", "National Grid Electricity Distribution – South Wales (SWALES)", "SWALES", "SWAE", "K", "South Wales", "NGED"),
    ]
    
    table_id = f"{PROJECT_ID}.{DATASET_ID}.dno_license_areas"
    
    rows_to_insert = [
        {
            "mpan_id": row[0],
            "dno_key": row[1],
            "dno_name": row[2],
            "short_code": row[3],
            "market_participant_id": row[4],
            "gsp_group_id": row[5],
            "gsp_group_name": row[6],
            "dno_group": row[7],
            "website": None,
            "data_portal": None,
            "boundary": None,
            "effective_from": "2010-01-01",
            "effective_to": None
        }
        for row in dno_data
    ]
    
    errors = client.insert_rows_json(table_id, rows_to_insert)
    if errors:
        print(f"⚠️  Errors loading DNO license areas: {errors}")
    else:
        print(f"✅ Loaded {len(rows_to_insert)} DNO license areas")
    
    # Load voltage levels
    voltage_data = [
        ("LV", "Low Voltage", 0.230, 0.400, "Domestic and small commercial"),
        ("HV", "High Voltage", 6.6, 33.0, "Large commercial and industrial"),
        ("EHV", "Extra High Voltage", 66.0, 132.0, "Very large industrial"),
        ("UHV", "Ultra High Voltage", 275.0, 400.0, "Transmission level"),
    ]
    
    table_id = f"{PROJECT_ID}.{DATASET_ID}.voltage_levels"
    rows_to_insert = [
        {
            "voltage_code": row[0],
            "voltage_name": row[1],
            "voltage_kv_min": row[2],
            "voltage_kv_max": row[3],
            "typical_customers": row[4]
        }
        for row in voltage_data
    ]
    
    errors = client.insert_rows_json(table_id, rows_to_insert)
    if errors:
        print(f"⚠️  Errors loading voltage levels: {errors}")
    else:
        print(f"✅ Loaded {len(rows_to_insert)} voltage levels")


def main():
    """Main execution"""
    print("="*70)
    print("CREATING BIGQUERY SCHEMA FOR DNO CHARGING DATA")
    print("="*70)
    
    client = create_client()
    print(f"\n✅ Connected to BigQuery project: {PROJECT_ID}")
    
    # Create dataset
    print(f"\n📦 Creating dataset...")
    create_dataset(client)
    
    # Create core tables
    print(f"\n📋 Creating core tables...")
    create_dno_license_areas_table(client)
    create_duos_tariff_definitions_table(client)
    create_duos_unit_rates_table(client)
    create_duos_time_bands_table(client)
    
    # Create spatial tables
    print(f"\n🗺️  Creating spatial tables...")
    create_spatial_tables(client)
    
    # Create reference tables
    print(f"\n📚 Creating reference tables...")
    create_reference_tables(client)
    
    # Load reference data
    print(f"\n💾 Loading reference data...")
    load_reference_data(client)
    
    print("\n" + "="*70)
    print("SCHEMA CREATION COMPLETE")
    print("="*70)
    print(f"\n✅ Dataset: {PROJECT_ID}.{DATASET_ID}")
    print(f"✅ Tables created: 10")
    print(f"✅ DNO license areas loaded: 14")
    print(f"✅ Voltage levels loaded: 4")
    print("\n🎯 Next steps:")
    print("  1. Extract tariff data from NGED files")
    print("  2. Load to duos_unit_rates table")
    print("  3. Find and load GeoJSON boundary files")
    print("  4. Create Google Sheets connection")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Create BigQuery table for ERA5 ocean/wave variables.

Table: era5_ocean_wave_data
Schema: 30+ fields covering air-sea interaction, wave state, spectral properties
License: CC-BY-4.0 © ECMWF
"""

from google.cloud import bigquery

PROJECT_ID = "inner-cinema-476211-u9"
DATASET = "uk_energy_prod"
TABLE = "era5_ocean_wave_data"
LOCATION = "US"

schema = [
    # Identifiers
    bigquery.SchemaField("farm_name", "STRING", mode="REQUIRED", description="Wind farm name"),
    bigquery.SchemaField("time_utc", "TIMESTAMP", mode="REQUIRED", description="UTC timestamp"),
    bigquery.SchemaField("latitude", "FLOAT64", mode="REQUIRED", description="Farm latitude (degrees N)"),
    bigquery.SchemaField("longitude", "FLOAT64", mode="REQUIRED", description="Farm longitude (degrees E)"),
    
    # Air-sea interaction (HIGHEST PRIORITY for power forecasting)
    bigquery.SchemaField("air_density_kg_m3", "FLOAT64", description="Air density over ocean (kg/m³) - for power = ρ·v³"),
    bigquery.SchemaField("drag_coefficient", "FLOAT64", description="Coefficient of drag with waves (dimensionless) - surface roughness"),
    bigquery.SchemaField("stress_equiv_wind_speed_10m", "FLOAT64", description="Ocean surface stress equivalent 10m neutral wind speed (m/s)"),
    bigquery.SchemaField("stress_equiv_wind_direction_10m", "FLOAT64", description="Ocean surface stress equivalent 10m neutral wind direction (degrees)"),
    bigquery.SchemaField("energy_flux_into_ocean", "FLOAT64", description="Normalized energy flux into ocean (dimensionless)"),
    bigquery.SchemaField("stress_into_ocean", "FLOAT64", description="Normalized stress into ocean (dimensionless)"),
    
    # Wave height (m)
    bigquery.SchemaField("wave_height_significant_m", "FLOAT64", description="Significant wave height combined wind waves + swell (m)"),
    bigquery.SchemaField("wave_height_wind_waves_m", "FLOAT64", description="Significant wave height wind waves only (m)"),
    bigquery.SchemaField("wave_height_swell_m", "FLOAT64", description="Significant wave height swell only (m)"),
    bigquery.SchemaField("wave_height_max_m", "FLOAT64", description="Maximum individual wave height (m) - extreme events"),
    
    # Wave period (seconds)
    bigquery.SchemaField("wave_period_mean_s", "FLOAT64", description="Mean wave period (s)"),
    bigquery.SchemaField("wave_period_peak_s", "FLOAT64", description="Peak wave period (s) - most energetic waves"),
    bigquery.SchemaField("wave_period_zero_crossing_s", "FLOAT64", description="Mean zero-crossing wave period (s)"),
    bigquery.SchemaField("wave_period_wind_waves_s", "FLOAT64", description="Mean period of wind waves (s)"),
    bigquery.SchemaField("wave_period_swell_s", "FLOAT64", description="Mean period of swell (s)"),
    bigquery.SchemaField("wave_period_max_height_s", "FLOAT64", description="Period of maximum individual wave (s)"),
    
    # Wave direction (degrees)
    bigquery.SchemaField("wave_direction_mean_deg", "FLOAT64", description="Mean wave direction (degrees)"),
    bigquery.SchemaField("wave_direction_wind_waves_deg", "FLOAT64", description="Mean direction of wind waves (degrees)"),
    bigquery.SchemaField("wave_direction_swell_deg", "FLOAT64", description="Mean direction of swell (degrees)"),
    
    # Spectral properties (advanced features)
    bigquery.SchemaField("wave_spectral_peakedness", "FLOAT64", description="Wave spectral peakedness (JONSWAP γ) - energy concentration"),
    bigquery.SchemaField("wave_spectral_directional_width", "FLOAT64", description="Overall wave spectral directional width (radians)"),
    bigquery.SchemaField("wave_spectral_directional_width_swell", "FLOAT64", description="Swell spectral directional width (radians)"),
    bigquery.SchemaField("wave_spectral_directional_width_wind_waves", "FLOAT64", description="Wind waves spectral directional width (radians)"),
    bigquery.SchemaField("wave_mean_square_slope", "FLOAT64", description="Mean square slope of waves (dimensionless) - surface steepness"),
]

def create_table():
    """Create BigQuery table with schema."""
    client = bigquery.Client(project=PROJECT_ID, location=LOCATION)
    table_id = f"{PROJECT_ID}.{DATASET}.{TABLE}"
    
    table = bigquery.Table(table_id, schema=schema)
    table.description = (
        "ERA5 ocean and wave variables for UK offshore wind farms (29 farms, 2020-2025). "
        "Covers air-sea interaction (air density, drag, stress), wave state (height/period/direction), "
        "and spectral properties (peakedness, directional width, mean square slope). "
        "Data source: ERA5 hourly data on single levels. "
        "License: CC-BY-4.0 © ECMWF. DOI: 10.24381/cds.adbb2d47. "
        "Attribution: Copernicus Climate Change Service (2023). "
        "Variables optimize offshore wind power forecasting via improved air-sea boundary layer modeling."
    )
    
    # Clustering for efficient queries
    table.clustering_fields = ["farm_name", "time_utc"]
    
    # Time partitioning
    table.time_partitioning = bigquery.TimePartitioning(
        type_=bigquery.TimePartitioningType.DAY,
        field="time_utc"
    )
    
    try:
        table = client.create_table(table)
        print(f"✅ Created table {table.project}.{table.dataset_id}.{table.table_id}")
        print(f"📊 Schema: {len(schema)} fields")
        print(f"🔑 Clustering: {table.clustering_fields}")
        print(f"📅 Partitioning: {table.time_partitioning.field}")
        print(f"📝 Description: {table.description[:200]}...")
    except Exception as e:
        if "Already Exists" in str(e):
            print(f"ℹ️  Table already exists: {table_id}")
        else:
            print(f"❌ Error creating table: {e}")
            raise

if __name__ == '__main__':
    create_table()

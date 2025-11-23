#!/usr/bin/env python3
"""
Ingest DUoS (Distribution Use of System) Tariff Data for All 14 UK DNOs
Populates Red, Amber, Green time-of-use charges for battery arbitrage analysis
"""
import os
from datetime import date, time
from google.cloud import bigquery
from google.oauth2 import service_account

PROJECT_ID = "inner-cinema-476211-u9"
DATASET = "gb_power"  # EU region
LOCATION = "EU"

# 14 UK DNO License Areas - OFFICIAL CODES from NESO reference data
# Matches neso_dno_reference table exactly
DNO_LICENSE_AREAS = [
    {"mpan_id": 10, "code": "UKPN-EPN", "name": "UK Power Networks (Eastern)", "short_code": "EPN", "market_participant": "EELC", "gsp_group": "A", "gsp_name": "Eastern"},
    {"mpan_id": 11, "code": "NGED-EM", "name": "National Grid Electricity Distribution – East Midlands (EMID)", "short_code": "EMID", "market_participant": "EMEB", "gsp_group": "B", "gsp_name": "East Midlands"},
    {"mpan_id": 12, "code": "UKPN-LPN", "name": "UK Power Networks (London)", "short_code": "LPN", "market_participant": "LOND", "gsp_group": "C", "gsp_name": "London"},
    {"mpan_id": 13, "code": "SP-Manweb", "name": "SP Energy Networks (SPM)", "short_code": "SPM", "market_participant": "MANW", "gsp_group": "D", "gsp_name": "Merseyside & North Wales"},
    {"mpan_id": 14, "code": "NGED-WM", "name": "National Grid Electricity Distribution – West Midlands (WMID)", "short_code": "WMID", "market_participant": "MIDE", "gsp_group": "E", "gsp_name": "West Midlands"},
    {"mpan_id": 15, "code": "NPg-NE", "name": "Northern Powergrid (North East)", "short_code": "NE", "market_participant": "NEEB", "gsp_group": "F", "gsp_name": "North East"},
    {"mpan_id": 16, "code": "ENWL", "name": "Electricity North West", "short_code": "ENWL", "market_participant": "NORW", "gsp_group": "G", "gsp_name": "North West"},
    {"mpan_id": 17, "code": "SSE-SHEPD", "name": "Scottish Hydro Electric Power Distribution (SHEPD)", "short_code": "SHEPD", "market_participant": "HYDE", "gsp_group": "P", "gsp_name": "North Scotland"},
    {"mpan_id": 18, "code": "SP-Distribution", "name": "SP Energy Networks (SPD)", "short_code": "SPD", "market_participant": "SPOW", "gsp_group": "N", "gsp_name": "South Scotland"},
    {"mpan_id": 19, "code": "UKPN-SPN", "name": "UK Power Networks (South Eastern)", "short_code": "SPN", "market_participant": "SEEB", "gsp_group": "J", "gsp_name": "South Eastern"},
    {"mpan_id": 20, "code": "SSE-SEPD", "name": "Southern Electric Power Distribution (SEPD)", "short_code": "SEPD", "market_participant": "SOUT", "gsp_group": "H", "gsp_name": "Southern"},
    {"mpan_id": 21, "code": "NGED-SWales", "name": "National Grid Electricity Distribution – South Wales (SWALES)", "short_code": "SWALES", "market_participant": "SWAE", "gsp_group": "K", "gsp_name": "South Wales"},
    {"mpan_id": 22, "code": "NGED-SW", "name": "National Grid Electricity Distribution – South West (SWEST)", "short_code": "SWEST", "market_participant": "SWEB", "gsp_group": "L", "gsp_name": "South Western"},
    {"mpan_id": 23, "code": "NPg-Y", "name": "Northern Powergrid (Yorkshire)", "short_code": "Y", "market_participant": "YELG", "gsp_group": "M", "gsp_name": "Yorkshire"},
]

# Standard UK DUoS Time Band Definitions
# Note: Each DNO may have slight variations - this is the common structure
TIME_BAND_DEFINITIONS = {
    "Red": {
        "description": "Peak demand periods - highest cost",
        "typical_times": [
            {"season": "Winter", "day_type": "Weekday", "start": "16:00", "end": "19:00", "months": (11, 2)},  # Nov-Feb
        ]
    },
    "Amber": {
        "description": "Shoulder periods - medium cost",
        "typical_times": [
            {"season": "Winter", "day_type": "Weekday", "start": "07:00", "end": "16:00", "months": (11, 2)},
            {"season": "Winter", "day_type": "Weekday", "start": "19:00", "end": "23:00", "months": (11, 2)},
            {"season": "Summer", "day_type": "Weekday", "start": "07:00", "end": "23:00", "months": (3, 10)},
        ]
    },
    "Green": {
        "description": "Off-peak periods - lowest cost",
        "typical_times": [
            {"season": "All-year", "day_type": "Weekday", "start": "23:00", "end": "07:00", "months": (1, 12)},
            {"season": "All-year", "day_type": "Weekend", "start": "00:00", "end": "23:59", "months": (1, 12)},
        ]
    }
}

# Typical DUoS rates (p/kWh) - PLACEHOLDER DATA
# In production, these should be sourced from official DNO tariff documents
# Using correct DNO keys from neso_dno_reference table
PLACEHOLDER_RATES = {
    "UKPN-EPN": {"Red": 5.5, "Amber": 1.8, "Green": 0.4, "year": "2025-26"},
    "UKPN-LPN": {"Red": 6.2, "Amber": 2.1, "Green": 0.5, "year": "2025-26"},
    "UKPN-SPN": {"Red": 5.8, "Amber": 1.9, "Green": 0.4, "year": "2025-26"},
    "NGED-EM": {"Red": 5.2, "Amber": 1.7, "Green": 0.4, "year": "2025-26"},
    "NGED-WM": {"Red": 5.3, "Amber": 1.7, "Green": 0.4, "year": "2025-26"},
    "NGED-SW": {"Red": 5.6, "Amber": 1.8, "Green": 0.4, "year": "2025-26"},
    "NGED-SWales": {"Red": 5.5, "Amber": 1.8, "Green": 0.4, "year": "2025-26"},
    "SSE-SEPD": {"Red": 5.4, "Amber": 1.8, "Green": 0.4, "year": "2025-26"},
    "SSE-SHEPD": {"Red": 4.8, "Amber": 1.6, "Green": 0.3, "year": "2025-26"},
    "NPg-NE": {"Red": 5.1, "Amber": 1.6, "Green": 0.4, "year": "2025-26"},
    "NPg-Y": {"Red": 5.0, "Amber": 1.6, "Green": 0.4, "year": "2025-26"},
    "ENWL": {"Red": 5.3, "Amber": 1.7, "Green": 0.4, "year": "2025-26"},
    "SP-Distribution": {"Red": 4.9, "Amber": 1.6, "Green": 0.3, "year": "2025-26"},
    "SP-Manweb": {"Red": 5.2, "Amber": 1.7, "Green": 0.4, "year": "2025-26"},
}


def get_settlement_period_from_time(time_str):
    """Convert HH:MM to settlement period (1-48)"""
    h, m = map(int, time_str.split(':'))
    return (h * 2) + (1 if m == 0 else 2)


def generate_time_band_rows(dno_code):
    """Generate time band definition rows for a DNO"""
    rows = []
    
    for band_name, band_info in TIME_BAND_DEFINITIONS.items():
        for time_slot in band_info["typical_times"]:
            # Generate one row per month-day combination
            start_month, end_month = time_slot["months"]
            
            if start_month <= end_month:
                months = range(start_month, end_month + 1)
            else:  # Wraps year (e.g., Nov-Feb = 11,12,1,2)
                months = list(range(start_month, 13)) + list(range(1, end_month + 1))
            
            for month in months:
                # Generate for each day type
                day_types = ["Weekday", "Saturday", "Sunday"] if time_slot["day_type"] == "All" else [time_slot["day_type"]]
                
                for day_type in day_types:
                    if time_slot["day_type"] == "Weekend" and day_type == "Weekday":
                        continue
                    
                    time_band_id = f"{dno_code}_{band_name}_{time_slot['season']}_{day_type}_{month:02d}_{time_slot['start'].replace(':', '')}"
                    
                    rows.append({
                        "time_band_id": time_band_id,
                        "dno_key": dno_code,
                        "time_band_name": band_name,
                        "time_band_type": band_name,
                        "season": time_slot["season"],
                        "day_type": day_type,
                        "start_time": time_slot["start"] + ":00" if len(time_slot["start"]) == 5 else time_slot["start"],
                        "end_time": time_slot["end"] + ":00" if len(time_slot["end"]) == 5 else time_slot["end"],
                        "start_month": month,
                        "end_month": month,
                        "description": f"{band_name} band - {band_info['description']}",
                        "extracted_date": str(date.today()),
                    })
    
    return rows


def generate_unit_rate_rows(dno_code):
    """Generate unit rate rows for a DNO"""
    rows = []
    rates = PLACEHOLDER_RATES.get(dno_code, {"Red": 5.0, "Amber": 1.5, "Green": 0.3})
    
    voltage_levels = ["LV", "HV", "EHV"]
    
    for voltage in voltage_levels:
        # Adjust rates by voltage (HV is ~20% cheaper, EHV ~40% cheaper)
        multiplier = {"LV": 1.0, "HV": 0.8, "EHV": 0.6}[voltage]
        
        for band in ["Red", "Amber", "Green"]:
            rate_id = f"{dno_code}_{band}_{voltage}_2025"
            
            rows.append({
                "rate_id": rate_id,
                "dno_key": dno_code,
                "tariff_code": f"{dno_code}_STANDARD",
                "time_band_name": band,
                "voltage_level": voltage,
                "unit_rate_p_kwh": round(rates[band] * multiplier, 3),
                "fixed_charge_p_mpan_day": 10.0 if voltage == "LV" else 20.0,  # Placeholder
                "capacity_charge_p_kva_day": 2.0 if voltage != "LV" else 0.0,  # Placeholder
                "effective_from": str(date(2025, 4, 1)),
                "effective_to": str(date(2026, 3, 31)),
            })
    
    return rows


def main():
    print("🔌 DUoS TARIFF DATA INGESTION - ALL 14 UK DNOs")
    print("=" * 100)
    print()
    
    # Initialize BigQuery client
    credentials = service_account.Credentials.from_service_account_file(
        'inner-cinema-credentials.json'
    )
    client = bigquery.Client(project=PROJECT_ID, credentials=credentials, location=LOCATION)
    
    print(f"📊 Target: {PROJECT_ID}.{DATASET}")
    print(f"   Location: {LOCATION}")
    print()
    
    # Track statistics
    stats = {
        "time_bands_inserted": 0,
        "unit_rates_inserted": 0,
        "dnos_processed": 0,
    }
    
    # Process each DNO
    for dno in DNO_LICENSE_AREAS:
        dno_code = dno["code"]
        dno_name = dno["name"]
        
        print(f"🔧 Processing: {dno_code} - {dno_name}")
        
        # 1. Generate time band definitions
        time_band_rows = generate_time_band_rows(dno_code)
        print(f"   Generated {len(time_band_rows)} time band definitions")
        
        # Insert time bands (append mode to preserve existing data)
        if time_band_rows:
            table_ref = f"{PROJECT_ID}.{DATASET}.duos_time_bands"
            job_config = bigquery.LoadJobConfig(
                write_disposition=bigquery.WriteDisposition.WRITE_APPEND,
                schema=[
                    bigquery.SchemaField("time_band_id", "STRING"),
                    bigquery.SchemaField("dno_key", "STRING"),
                    bigquery.SchemaField("time_band_name", "STRING"),
                    bigquery.SchemaField("time_band_type", "STRING"),
                    bigquery.SchemaField("season", "STRING"),
                    bigquery.SchemaField("day_type", "STRING"),
                    bigquery.SchemaField("start_time", "TIME"),
                    bigquery.SchemaField("end_time", "TIME"),
                    bigquery.SchemaField("start_month", "INTEGER"),
                    bigquery.SchemaField("end_month", "INTEGER"),
                    bigquery.SchemaField("description", "STRING"),
                    bigquery.SchemaField("extracted_date", "DATE"),
                ]
            )
            
            job = client.load_table_from_json(time_band_rows, table_ref, job_config=job_config)
            job.result()
            stats["time_bands_inserted"] += len(time_band_rows)
        
        # 2. Generate unit rates
        unit_rate_rows = generate_unit_rate_rows(dno_code)
        print(f"   Generated {len(unit_rate_rows)} unit rate rows (Red/Amber/Green × LV/HV/EHV)")
        
        # Insert unit rates
        if unit_rate_rows:
            table_ref = f"{PROJECT_ID}.{DATASET}.duos_unit_rates"
            job_config = bigquery.LoadJobConfig(
                write_disposition=bigquery.WriteDisposition.WRITE_APPEND,
                schema=[
                    bigquery.SchemaField("rate_id", "STRING"),
                    bigquery.SchemaField("dno_key", "STRING"),
                    bigquery.SchemaField("tariff_code", "STRING"),
                    bigquery.SchemaField("time_band_name", "STRING"),
                    bigquery.SchemaField("voltage_level", "STRING"),
                    bigquery.SchemaField("unit_rate_p_kwh", "FLOAT"),
                    bigquery.SchemaField("fixed_charge_p_mpan_day", "FLOAT"),
                    bigquery.SchemaField("capacity_charge_p_kva_day", "FLOAT"),
                    bigquery.SchemaField("effective_from", "DATE"),
                    bigquery.SchemaField("effective_to", "DATE"),
                ]
            )
            
            job = client.load_table_from_json(unit_rate_rows, table_ref, job_config=job_config)
            job.result()
            stats["unit_rates_inserted"] += len(unit_rate_rows)
        
        stats["dnos_processed"] += 1
        print(f"   ✅ Complete")
        print()
    
    # Summary
    print("=" * 100)
    print("✅ DUoS INGESTION COMPLETE")
    print()
    print(f"📊 Summary:")
    print(f"   DNOs processed: {stats['dnos_processed']}")
    print(f"   Time band definitions: {stats['time_bands_inserted']:,}")
    print(f"   Unit rate rows: {stats['unit_rates_inserted']:,}")
    print()
    
    # Validation queries
    print("🔍 Validation:")
    
    query = f"""
    SELECT dno_key, COUNT(*) as time_bands
    FROM `{PROJECT_ID}.{DATASET}.duos_time_bands`
    GROUP BY dno_key
    ORDER BY dno_key
    """
    df = client.query(query).to_dataframe()
    print("\nTime Bands by DNO:")
    print(df.to_string(index=False))
    
    query = f"""
    SELECT 
        dno_key,
        time_band_name,
        voltage_level,
        unit_rate_p_kwh
    FROM `{PROJECT_ID}.{DATASET}.duos_unit_rates`
    WHERE effective_to >= CURRENT_DATE()
    ORDER BY dno_key, time_band_name, voltage_level
    LIMIT 20
    """
    df = client.query(query).to_dataframe()
    print("\nSample Unit Rates:")
    print(df.to_string(index=False))
    
    print()
    print("✅ All DUoS data ingested successfully!")
    print()
    print("⚠️  NOTE: This script uses PLACEHOLDER rates.")
    print("   For production use, update PLACEHOLDER_RATES with official DNO tariff data.")
    print("   Sources: Each DNO's website under 'Use of System Charges' or 'LCTA'")


if __name__ == "__main__":
    main()

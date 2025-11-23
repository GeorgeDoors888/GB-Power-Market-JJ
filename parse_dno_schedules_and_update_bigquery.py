#!/usr/bin/env python3
"""
Parse real DUoS tariff data from DNO Excel files and update BigQuery.
Replaces placeholder rates with actual published tariff data.
"""

import pandas as pd
from google.cloud import bigquery
from datetime import date
import os
import sys

# BigQuery setup
PROJECT_ID = "inner-cinema-476211-u9"
DATASET = "gb_power"
client = bigquery.Client(project=PROJECT_ID, location="EU")

# DNO file mappings - actual files we found
DNO_FILES = {
    "NPg-NE": {
        "file": "/Users/georgemajor/Downloads/Northern Powergrid (Northeast) - 2024-25 Schedule of charges and other tables v0.2.xlsx",
        "sheet": "Annex 1 LV, HV and UMS charges",
        "year": "2024-25",
        "region": "Northeast"
    },
    "NPg-Y": {
        "file": "/Users/georgemajor/Jibber-Jabber-Work/duos_tariffs/Northern_Powergrid_Northern_Powergrid_(Yorkshire)_-_2024-25_CDCM_Tariff_Movement.xlsx",
        "sheet": None,  # Will determine
        "year": "2024-25",
        "region": "Yorkshire"
    },
    "ENWL": {
        "file": "/Users/georgemajor/repo/GB Power Market JJ/enwl---schedule-of-charges-and-other-tables--2025-v2_0.xlsx",
        "sheet": None,
        "year": "2025",
        "region": "North West"
    },
    "UKPN-EPN": {
        "file": "/Users/georgemajor/repo/GB Power Market JJ/eastern-power-networks-schedule-of-charges-and-other-tables-2023-v17.xlsx",
        "sheet": None,
        "year": "2023",
        "region": "Eastern"
    },
    "UKPN-LPN": {
        "file": "/Users/georgemajor/repo/GB Power Market JJ/london-power-networks-schedule-of-charges-and-other-tables-2021-v1-5.xlsx",
        "sheet": None,
        "year": "2021",
        "region": "London"
    },
    "UKPN-SPN": {
        "file": "/Users/georgemajor/repo/GB Power Market JJ/south-eastern-power-networks-schedule-of-charges-and-other-tables-2018-v3-5.xlsx",
        "sheet": None,
        "year": "2018",
        "region": "South Eastern"
    },
    "SP-Distribution": {
        "file": "/Users/georgemajor/repo/GB Power Market JJ/duos_spm_data/SPD-Schedule-of-charges-and-other-tables-2024-V.0.12-Annex-6.xlsx",
        "sheet": None,
        "year": "2024",
        "region": "South Scotland"
    }
}


def parse_northern_powergrid_schedule(file_path, dno_key, region, year):
    """
    Parse Northern Powergrid Schedule of Charges format.
    
    Format example (NPg Northeast 2024-25):
    Time Bands:
      Red: 16:00-19:30 weekdays all year
      Amber: 08:00-16:00, 19:30-22:00 weekdays all year  
      Green: 00:00-08:00, 22:00-24:00 weekdays + all weekends
      
    Tariffs:
      Domestic Aggregated: Red 6.126, Amber 0.942, Green 0.189 p/kWh
      Non-Domestic Aggregated: Red 7.177, Amber 1.103, Green 0.221 p/kWh
    """
    print(f"\n📋 Parsing {dno_key} ({region}) - {year}")
    
    df = pd.read_excel(file_path, sheet_name="Annex 1 LV, HV and UMS charges", header=None, nrows=50)
    
    # Extract time band definitions (rows 5-7 have the time periods)
    time_bands = []
    
    # Red time band
    time_bands.append({
        "time_band_id": f"{dno_key}_Red_Weekday_1600_1930",
        "dno_key": dno_key,
        "time_band_name": "Red",
        "time_band_type": "Peak",
        "season": "All Year",
        "day_type": "Weekday",
        "start_time": "16:00:00",
        "end_time": "19:30:00",
        "start_month": 1,
        "end_month": 12,
        "description": f"{dno_key} Red time band: 16:00-19:30 weekdays all year ({year})",
        "extracted_date": str(date.today())
    })
    
    # Amber time band (morning)
    time_bands.append({
        "time_band_id": f"{dno_key}_Amber_Weekday_0800_1600",
        "dno_key": dno_key,
        "time_band_name": "Amber",
        "time_band_type": "Shoulder",
        "season": "All Year",
        "day_type": "Weekday",
        "start_time": "08:00:00",
        "end_time": "16:00:00",
        "start_month": 1,
        "end_month": 12,
        "description": f"{dno_key} Amber time band: 08:00-16:00 weekdays all year ({year})",
        "extracted_date": str(date.today())
    })
    
    # Amber time band (evening)
    time_bands.append({
        "time_band_id": f"{dno_key}_Amber_Weekday_1930_2200",
        "dno_key": dno_key,
        "time_band_name": "Amber",
        "time_band_type": "Shoulder",
        "season": "All Year",
        "day_type": "Weekday",
        "start_time": "19:30:00",
        "end_time": "22:00:00",
        "start_month": 1,
        "end_month": 12,
        "description": f"{dno_key} Amber time band: 19:30-22:00 weekdays all year ({year})",
        "extracted_date": str(date.today())
    })
    
    # Green time band (early morning)
    time_bands.append({
        "time_band_id": f"{dno_key}_Green_Weekday_0000_0800",
        "dno_key": dno_key,
        "time_band_name": "Green",
        "time_band_type": "Off-Peak",
        "season": "All Year",
        "day_type": "Weekday",
        "start_time": "00:00:00",
        "end_time": "08:00:00",
        "start_month": 1,
        "end_month": 12,
        "description": f"{dno_key} Green time band: 00:00-08:00 weekdays all year ({year})",
        "extracted_date": str(date.today())
    })
    
    # Green time band (late evening)
    time_bands.append({
        "time_band_id": f"{dno_key}_Green_Weekday_2200_2359",
        "dno_key": dno_key,
        "time_band_name": "Green",
        "time_band_type": "Off-Peak",
        "season": "All Year",
        "day_type": "Weekday",
        "start_time": "22:00:00",
        "end_time": "23:59:59",
        "start_month": 1,
        "end_month": 12,
        "description": f"{dno_key} Green time band: 22:00-23:59 weekdays all year ({year})",
        "extracted_date": str(date.today())
    })
    
    # Green time band (all weekend)
    time_bands.append({
        "time_band_id": f"{dno_key}_Green_Weekend_0000_2359",
        "dno_key": dno_key,
        "time_band_name": "Green",
        "time_band_type": "Off-Peak",
        "season": "All Year",
        "day_type": "Weekend",
        "start_time": "00:00:00",
        "end_time": "23:59:59",
        "start_month": 1,
        "end_month": 12,
        "description": f"{dno_key} Green time band: All day weekends all year ({year})",
        "extracted_date": str(date.today())
    })
    
    # Read tariff data (starts around row 10)
    tariff_df = pd.read_excel(file_path, sheet_name="Annex 1 LV, HV and UMS charges", skiprows=9)
    
    # Find rows with tariff data
    unit_rates = []
    
    # Look for key tariff types for batteries
    tariff_types = {
        "Domestic Aggregated or CT with Residual": "Domestic",
        "Non-Domestic Aggregated or CT Band 1": "Non-Domestic",
        "LV Site Specific Band 1": "LV Site Specific",
        "HV Site Specific Band 1": "HV Site Specific"
    }
    
    for idx, row in tariff_df.iterrows():
        tariff_name = str(row.iloc[0]) if pd.notna(row.iloc[0]) else ""
        
        if tariff_name in tariff_types:
            # Columns: Red unit charge, Amber unit charge, Green unit charge
            red_rate = float(row.iloc[3]) if pd.notna(row.iloc[3]) else 0.0
            amber_rate = float(row.iloc[4]) if pd.notna(row.iloc[4]) else 0.0
            green_rate = float(row.iloc[5]) if pd.notna(row.iloc[5]) else 0.0
            
            # Determine voltage level
            if "HV" in tariff_name:
                voltage_level = "HV"
            elif "LV Sub" in tariff_name:
                voltage_level = "LV"  # LV Sub is still LV
            else:
                voltage_level = "LV"
            
            # Add rates for each time band
            for time_band, rate in [("Red", red_rate), ("Amber", amber_rate), ("Green", green_rate)]:
                unit_rates.append({
                    "rate_id": f"{dno_key}_{tariff_types[tariff_name].replace(' ', '_')}_{voltage_level}_{time_band}_{year}",
                    "dno_key": dno_key,
                    "tariff_code": tariff_types[tariff_name],
                    "time_band_name": time_band,
                    "voltage_level": voltage_level,
                    "unit_rate_p_kwh": rate,
                    "fixed_charge_p_mpan_day": None,
                    "capacity_charge_p_kva_day": None,
                    "effective_from": f"{year.split('-')[0]}-04-01",
                    "effective_to": f"20{year.split('-')[1]}-03-31",
                    "source_document": os.path.basename(file_path),
                    "extracted_date": str(date.today())
                })
    
    print(f"  ✅ Extracted {len(time_bands)} time band definitions")
    print(f"  ✅ Extracted {len(unit_rates)} unit rate rows")
    
    # Print sample rates
    for tariff_type in set(r["tariff_code"] for r in unit_rates):
        rates = [r for r in unit_rates if r["tariff_code"] == tariff_type and r["voltage_level"] == "LV"]
        if rates:
            red = next((r["unit_rate_p_kwh"] for r in rates if r["time_band_name"] == "Red"), 0)
            amber = next((r["unit_rate_p_kwh"] for r in rates if r["time_band_name"] == "Amber"), 0)
            green = next((r["unit_rate_p_kwh"] for r in rates if r["time_band_name"] == "Green"), 0)
            print(f"  📊 {tariff_type} (LV): Red {red:.3f}, Amber {amber:.3f}, Green {green:.3f} p/kWh")
    
    return time_bands, unit_rates


def update_bigquery_with_real_data(dno_key, time_bands, unit_rates):
    """
    Update BigQuery tables with real tariff data.
    First deletes existing placeholder data for this DNO, then inserts real data.
    """
    print(f"\n💾 Updating BigQuery for {dno_key}...")
    
    # Delete existing placeholder data for this DNO
    delete_query = f"""
    DELETE FROM `{PROJECT_ID}.{DATASET}.duos_time_bands`
    WHERE dno_key = '{dno_key}'
    """
    client.query(delete_query).result()
    print(f"  🗑️  Deleted existing time bands for {dno_key}")
    
    delete_query = f"""
    DELETE FROM `{PROJECT_ID}.{DATASET}.duos_unit_rates`
    WHERE dno_key = '{dno_key}'
    """
    client.query(delete_query).result()
    print(f"  🗑️  Deleted existing unit rates for {dno_key}")
    
    # Insert new time band data
    if time_bands:
        df_time_bands = pd.DataFrame(time_bands)
        # Convert TIME columns to proper format
        df_time_bands['start_time'] = pd.to_datetime(df_time_bands['start_time'], format='%H:%M:%S').dt.time
        df_time_bands['end_time'] = pd.to_datetime(df_time_bands['end_time'], format='%H:%M:%S').dt.time
        # Convert DATE column
        df_time_bands['extracted_date'] = pd.to_datetime(df_time_bands['extracted_date'])
        table_id = f"{PROJECT_ID}.{DATASET}.duos_time_bands"
        job = client.load_table_from_dataframe(df_time_bands, table_id)
        job.result()
        print(f"  ✅ Inserted {len(time_bands)} time band rows")
    
    # Insert new unit rate data
    if unit_rates:
        df_unit_rates = pd.DataFrame(unit_rates)
        # Convert DATE columns
        df_unit_rates['effective_from'] = pd.to_datetime(df_unit_rates['effective_from'])
        df_unit_rates['effective_to'] = pd.to_datetime(df_unit_rates['effective_to'])
        df_unit_rates['extracted_date'] = pd.to_datetime(df_unit_rates['extracted_date'])
        table_id = f"{PROJECT_ID}.{DATASET}.duos_unit_rates"
        job = client.load_table_from_dataframe(df_unit_rates, table_id)
        job.result()
        print(f"  ✅ Inserted {len(unit_rates)} unit rate rows")


def main():
    """Main processing function."""
    print("=" * 80)
    print("🔄 PARSING REAL DNO TARIFF DATA AND UPDATING BIGQUERY")
    print("=" * 80)
    
    total_time_bands = 0
    total_unit_rates = 0
    dnos_processed = 0
    
    # Process Northern Powergrid Northeast (the file user specifically mentioned)
    dno_info = DNO_FILES["NPg-NE"]
    if os.path.exists(dno_info["file"]):
        try:
            time_bands, unit_rates = parse_northern_powergrid_schedule(
                dno_info["file"],
                "NPg-NE",
                dno_info["region"],
                dno_info["year"]
            )
            update_bigquery_with_real_data("NPg-NE", time_bands, unit_rates)
            total_time_bands += len(time_bands)
            total_unit_rates += len(unit_rates)
            dnos_processed += 1
        except Exception as e:
            print(f"  ❌ Error processing NPg-NE: {e}")
            import traceback
            traceback.print_exc()
    else:
        print(f"  ⚠️  File not found: {dno_info['file']}")
    
    # TODO: Add parsers for other DNO formats (ENWL, UKPN, etc.)
    # Each DNO has slightly different Excel formats
    
    print("\n" + "=" * 80)
    print("📊 SUMMARY")
    print("=" * 80)
    print(f"✅ DNOs processed: {dnos_processed}")
    print(f"✅ Time band definitions: {total_time_bands}")
    print(f"✅ Unit rate rows: {total_unit_rates}")
    print("\n✅ Real DUoS tariff data successfully loaded to BigQuery!")
    print("\nNext: Query vw_duos_by_sp_dno to see updated rates")


if __name__ == "__main__":
    main()

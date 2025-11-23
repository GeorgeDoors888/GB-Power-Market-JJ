#!/usr/bin/env python3
"""
LLFC/DUoS Tariff Loader
Loads and parses DNO charging statements to map LLFC → R/A/G rates
"""

import pandas as pd
from pathlib import Path
from typing import Dict, List, Optional
import re
from google.cloud import bigquery

PROJECT_ID = "inner-cinema-476211-u9"
DATASET = "gb_power"

class LLFCTariffLoader:
    """Load and query LLFC-based DUoS tariffs for all GB DNOs"""
    
    def __init__(self):
        self.client = bigquery.Client(project=PROJECT_ID, location="EU")
        self.tariffs_df = None
        self.time_bands_df = None
    
    def load_from_bigquery(self):
        """Load existing tariff data from BigQuery"""
        
        # Load tariff rates
        rates_query = f"""
        SELECT 
            dno_key,
            tariff_code,
            time_band_name,
            voltage_level,
            unit_rate_p_kwh,
            fixed_charge_p_mpan_day,
            capacity_charge_p_kva_day
        FROM `{PROJECT_ID}.{DATASET}.duos_unit_rates`
        ORDER BY dno_key, tariff_code, time_band_name
        """
        
        self.tariffs_df = self.client.query(rates_query).to_dataframe()
        
        # Load time bands
        bands_query = f"""
        SELECT 
            dno_key,
            time_band_name,
            day_type,
            start_time,
            end_time
        FROM `{PROJECT_ID}.{DATASET}.duos_time_bands`
        ORDER BY dno_key, time_band_name, day_type, start_time
        """
        
        self.time_bands_df = self.client.query(bands_query).to_dataframe()
        
        print(f"✅ Loaded {len(self.tariffs_df)} tariff records")
        print(f"✅ Loaded {len(self.time_bands_df)} time band records")
    
    def lookup_rates_by_llfc(self, dno_key: str, llfc: str, voltage: str = "LV") -> Dict:
        """
        Look up R/A/G rates for a specific LLFC
        
        Args:
            dno_key: DNO identifier (e.g., "UKPN-EPN")
            llfc: Line Loss Factor Class / DUoS Tariff ID (e.g., "0840")
            voltage: Voltage level (LV, HV, EHV)
        
        Returns:
            Dict with rates and tariff details
        """
        if self.tariffs_df is None:
            self.load_from_bigquery()
        
        # Normalize LLFC (zero-pad to 3-4 digits)
        llfc_clean = str(llfc).zfill(4)
        
        # Filter tariffs for this DNO and voltage
        mask = (
            (self.tariffs_df['dno_key'] == dno_key) &
            (self.tariffs_df['voltage_level'] == voltage)
        )
        
        matches = self.tariffs_df[mask]
        
        if matches.empty:
            raise ValueError(f"No tariffs found for {dno_key} {voltage}")
        
        # For now, aggregate by time band (future: parse LLFC from tariff_code)
        rates = {}
        for band in ['Red', 'Amber', 'Green']:
            band_data = matches[matches['time_band_name'] == band]
            if not band_data.empty:
                rates[band] = {
                    'rate': float(band_data['unit_rate_p_kwh'].mean()),
                    'fixed': float(band_data['fixed_charge_p_mpan_day'].mean()),
                    'capacity': float(band_data['capacity_charge_p_kva_day'].mean())
                }
            else:
                rates[band] = {'rate': 0, 'fixed': 0, 'capacity': 0}
        
        # Get time bands
        time_bands = self._get_time_bands(dno_key)
        
        return {
            'dno_key': dno_key,
            'llfc': llfc,
            'voltage': voltage,
            'rates': rates,
            'time_bands': time_bands,
            'tariff_code': matches['tariff_code'].iloc[0] if not matches.empty else None
        }
    
    def _get_time_bands(self, dno_key: str) -> Dict:
        """Get time band schedule for DNO"""
        if self.time_bands_df is None:
            self.load_from_bigquery()
        
        bands = self.time_bands_df[self.time_bands_df['dno_key'] == dno_key]
        
        result = {'Red': [], 'Amber': [], 'Green': []}
        
        for _, row in bands.iterrows():
            band = row['time_band_name']
            day_type = row['day_type']
            start = str(row['start_time'])[:5]
            end = str(row['end_time'])[:5]
            
            time_str = f"{start}-{end} {day_type}"
            if time_str not in result[band]:
                result[band].append(time_str)
        
        return result
    
    def create_llfc_mapping_table(self):
        """
        Create a BigQuery table to store LLFC → Tariff mappings
        This would be populated from DNO XLSX files
        """
        
        schema = [
            bigquery.SchemaField("llfc_id", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("dno_key", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("tariff_code", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("voltage_level", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("import_export", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("description", "STRING"),
            bigquery.SchemaField("effective_from", "DATE"),
            bigquery.SchemaField("effective_to", "DATE"),
        ]
        
        table_id = f"{PROJECT_ID}.{DATASET}.llfc_tariff_mapping"
        
        table = bigquery.Table(table_id, schema=schema)
        table = self.client.create_table(table, exists_ok=True)
        
        print(f"✅ Created table: {table_id}")
        return table_id


def test_llfc_lookup():
    """Test LLFC lookup"""
    loader = LLFCTariffLoader()
    
    print("=" * 80)
    print("LLFC Tariff Lookup Test")
    print("=" * 80)
    
    # Test case: UKPN-EPN, LLFC 0840, HV
    try:
        result = loader.lookup_rates_by_llfc("UKPN-EPN", "0840", "HV")
        
        print(f"\nDNO: {result['dno_key']}")
        print(f"LLFC: {result['llfc']}")
        print(f"Voltage: {result['voltage']}")
        print(f"\nRates:")
        for band, data in result['rates'].items():
            print(f"  {band}: {data['rate']:.4f} p/kWh")
        
        print(f"\nTime Bands:")
        for band, times in result['time_bands'].items():
            print(f"  {band}:")
            for time in times:
                print(f"    {time}")
    
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    test_llfc_lookup()

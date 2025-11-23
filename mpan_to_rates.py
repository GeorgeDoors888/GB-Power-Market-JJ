#!/usr/bin/env python3
"""
Complete MPAN → DNO → LLFC → R/A/G Rates Pipeline
Automated end-to-end lookup system for all GB DNOs
"""

from mpan_parser import MPANParser
from llfc_tariff_loader import LLFCTariffLoader
import sys

class MPANRatesLookup:
    """
    Complete pipeline: MPAN → DNO → LLFC → DUoS Rates
    """
    
    def __init__(self):
        self.parser = MPANParser()
        self.loader = LLFCTariffLoader()
    
    def lookup(self, mpan_string: str, voltage: str = None) -> dict:
        """
        Complete lookup from MPAN to rates
        
        Args:
            mpan_string: Full MPAN (with or without top line)
            voltage: Optional voltage override (LV/HV/EHV)
        
        Returns:
            Complete dict with MPAN details, DNO info, and R/A/G rates
        """
        
        # Step 1: Parse MPAN
        print(f"📋 Parsing MPAN: {mpan_string}")
        mpan_data = self.parser.parse_full_mpan(mpan_string)
        
        if not mpan_data['valid']:
            raise ValueError(f"❌ Invalid MPAN checksum: {mpan_string}")
        
        print(f"✅ Valid MPAN")
        print(f"   DNO: {mpan_data['dno_name']} ({mpan_data['dno_key']})")
        print(f"   Distributor ID: {mpan_data['distributor_id']}")
        
        # Step 2: Determine voltage level
        if voltage is None:
            # Try to infer from LLFC or default to LV
            voltage = "LV"  # Default
        
        print(f"   Voltage: {voltage}")
        
        # Step 3: Look up LLFC tariff (if available)
        if mpan_data['has_top_line'] and mpan_data['llfc']:
            print(f"   LLFC: {mpan_data['llfc']}")
            
            try:
                rates_data = self.loader.lookup_rates_by_llfc(
                    mpan_data['dno_key'],
                    mpan_data['llfc'],
                    voltage
                )
                
                print(f"\n💰 DUoS Rates (via LLFC):")
                for band, data in rates_data['rates'].items():
                    print(f"   {band}: {data['rate']:.4f} p/kWh")
                
            except Exception as e:
                print(f"⚠️ LLFC lookup failed: {e}")
                print(f"   Falling back to average rates for {voltage}")
                rates_data = self._fallback_rates(mpan_data['dno_key'], voltage)
        
        else:
            print(f"   ℹ️ No LLFC in MPAN (core only)")
            print(f"   Using average {voltage} rates for {mpan_data['dno_key']}")
            rates_data = self._fallback_rates(mpan_data['dno_key'], voltage)
        
        # Combine all data
        return {
            'mpan': mpan_data,
            'rates': rates_data,
            'summary': self._format_summary(mpan_data, rates_data)
        }
    
    def _fallback_rates(self, dno_key: str, voltage: str) -> dict:
        """Fallback to average rates when LLFC not available"""
        self.loader.load_from_bigquery()
        
        mask = (
            (self.loader.tariffs_df['dno_key'] == dno_key) &
            (self.loader.tariffs_df['voltage_level'] == voltage)
        )
        
        matches = self.loader.tariffs_df[mask]
        
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
        
        time_bands = self.loader._get_time_bands(dno_key)
        
        return {
            'dno_key': dno_key,
            'voltage': voltage,
            'rates': rates,
            'time_bands': time_bands,
            'fallback': True
        }
    
    def _format_summary(self, mpan_data: dict, rates_data: dict) -> str:
        """Format a human-readable summary"""
        lines = [
            "=" * 80,
            "MPAN → DNO → DUoS Rates Summary",
            "=" * 80,
            f"MPAN: {mpan_data['core_mpan']}",
            f"DNO: {mpan_data['dno_name']} ({mpan_data['dno_key']})",
            f"Region: {mpan_data['dno_region']}",
            f"Voltage: {rates_data['voltage']}",
            ""
        ]
        
        if mpan_data['has_top_line']:
            lines.extend([
                f"Profile Class: {mpan_data['pc']}",
                f"MTC: {mpan_data['mtc']}",
                f"LLFC: {mpan_data['llfc']}",
                ""
            ])
        
        lines.append("DUoS Rates:")
        for band, data in rates_data['rates'].items():
            lines.append(f"  {band}: {data['rate']:.4f} p/kWh = £{data['rate']*10:.2f}/MWh")
        
        lines.append("\nTime Bands:")
        for band, times in rates_data['time_bands'].items():
            lines.append(f"  {band}:")
            for time in times[:3]:  # Show first 3 time periods
                lines.append(f"    {time}")
        
        lines.append("=" * 80)
        
        return "\n".join(lines)


def main():
    """CLI interface"""
    if len(sys.argv) < 2:
        print("Usage: python3 mpan_to_rates.py <MPAN> [voltage]")
        print("\nExamples:")
        print("  python3 mpan_to_rates.py 1234567890123")
        print("  python3 mpan_to_rates.py '00 801 0840 1234567890123' HV")
        sys.exit(1)
    
    mpan = sys.argv[1]
    voltage = sys.argv[2] if len(sys.argv) > 2 else None
    
    lookup = MPANRatesLookup()
    
    try:
        result = lookup.lookup(mpan, voltage)
        print("\n" + result['summary'])
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

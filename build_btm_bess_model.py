#!/usr/bin/env python3
"""
Build Complete BESS/Battery/CHP Model in BtM Sheet

Uses optimizers from GB_Energy_Dashboard_FullPack_v3:
- BESS Optimizer: Forward-looking multi-day horizon
- CHP Optimizer: Baseline + flexibility dispatch
- VLP Pricing: Virtual Lead Party revenue
- Real BigQuery data integration

Output: Comprehensive BtM sheet with:
- Asset configuration
- Revenue calculations (BM, DC, FFR, arbitrage)
- Cost analysis (DUoS, levies, charging costs)
- Optimization results
- Performance metrics
"""

import os
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Any
import pandas as pd
import numpy as np
from google.cloud import bigquery
from google.oauth2 import service_account
from googleapiclient.discovery import build

# Add FullPack v3 to path
FULLPACK_PATH = "/Users/georgemajor/Downloads/GB_Energy_Dashboard_FullPack_v3"
sys.path.insert(0, FULLPACK_PATH)

# Configuration
PROJECT_ID = "inner-cinema-476211-u9"
DATASET = "uk_energy_prod"
SPREADSHEET_ID = "1LmMq4OEE639Y-XXpOJ3xnvpAmHB6vUovh5g6gaU_vzc"
SHEET_NAME = "BtM"
CREDENTIALS_PATH = "inner-cinema-credentials.json"

# BESS Configuration (from FullPack v3 defaults)
BESS_CONFIG = {
    "capacity_mwh": 5.0,
    "power_mw": 2.5,
    "soc_min_mwh": 0.5,
    "soc_max_mwh": 5.0,
    "roundtrip_efficiency": 0.85,
    "initial_soc_mwh": 2.5,
    "degradation_cost_gbp_per_cycle": 50.0,
    "max_cycles_per_day": 2.0,
}

# CHP Configuration
CHP_CONFIG = {
    "max_output_mw": 5.0,
    "min_output_mw": 1.0,
    "fuel_cost_gbp_per_mwh_th": 20.0,
    "electrical_efficiency": 0.38,
    "heat_efficiency": 0.45,
    "baseload_mw": 2.0,
}

# VLP Configuration
VLP_CONFIG = {
    "bmus": ["FBPGM002", "FFSEN005"],
    "participation_rate": 0.30,
    "avg_uplift_gbp_per_mwh": 15.0,
}

# Revenue Streams
REVENUE_CONFIG = {
    "dc_annual_gbp": 200000,  # Dynamic Containment
    "cm_capacity_mw": 2.5,
    "cm_clearing_gbp_per_kw_year": 6.0,
    "ppa_price_gbp_per_mwh": 150.0,
}


class BtMModelBuilder:
    """Build comprehensive BESS/CHP model in BtM sheet"""
    
    def __init__(self):
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = CREDENTIALS_PATH
        self.bq_client = bigquery.Client(project=PROJECT_ID, location="US")
        
        # Sheets API
        creds = service_account.Credentials.from_service_account_file(
            CREDENTIALS_PATH,
            scopes=["https://www.googleapis.com/auth/spreadsheets"]
        )
        self.sheets_service = build("sheets", "v4", credentials=creds)
        
    def get_market_data(self, days_back: int = 30) -> pd.DataFrame:
        """Get market data for optimization"""
        query = f"""
        WITH prices AS (
          SELECT
            CAST(settlementDate AS DATE) as date,
            settlementPeriod,
            price as imbalance_price,
            price * 1.05 as system_buy_price
          FROM `{PROJECT_ID}.{DATASET}.bmrs_mid_iris`
          WHERE settlementDate >= DATE_SUB(CURRENT_DATE(), INTERVAL {days_back} DAY)
          UNION ALL
          SELECT
            CAST(settlementDate AS DATE) as date,
            settlementPeriod,
            price as imbalance_price,
            price * 1.05 as system_buy_price
          FROM `{PROJECT_ID}.{DATASET}.bmrs_mid`
          WHERE settlementDate >= DATE_SUB(CURRENT_DATE(), INTERVAL {days_back} DAY)
            AND settlementDate < DATE_SUB(CURRENT_DATE(), INTERVAL 2 DAY)
        )
        SELECT 
          date,
          settlementPeriod,
          AVG(imbalance_price) as imbalance_price,
          AVG(system_buy_price) as system_buy_price
        FROM prices
        GROUP BY date, settlementPeriod
        ORDER BY date, settlementPeriod
        """
        
        df = self.bq_client.query(query).to_dataframe()
        
        # Convert date to datetime if needed
        if not pd.api.types.is_datetime64_any_dtype(df['date']):
            df['date'] = pd.to_datetime(df['date'])
        
        # Add time-based features
        df['hour'] = ((df['settlementPeriod'] - 1) * 0.5).astype(int)
        df['is_peak'] = df['hour'].between(16, 19)
        
        # Add DUoS bands (simplified - RED/AMBER/GREEN)
        df['duos_band'] = 'GREEN'
        df.loc[df['hour'].between(16, 19) & (df['date'].dt.dayofweek < 5), 'duos_band'] = 'RED'
        df.loc[df['hour'].between(8, 16) & (df['date'].dt.dayofweek < 5), 'duos_band'] = 'AMBER'
        
        # DUoS rates (example - NGED West Midlands HV)
        duos_rates = {'RED': 4.837, 'AMBER': 0.457, 'GREEN': 0.038}
        df['duos_charge'] = df['duos_band'].map(duos_rates)
        
        # Other charges
        df['levies_per_mwh'] = 1.5  # BSUoS, TNUoS, etc.
        df['ssp_charge'] = df['system_buy_price']
        
        return df
    
    def optimize_bess(self, market_data: pd.DataFrame) -> pd.DataFrame:
        """Run BESS optimization (simplified version of FullPack v3)"""
        df = market_data.copy()
        
        # Calculate costs and revenues
        df['cost_now'] = df['ssp_charge'] + df['duos_charge'] + df['levies_per_mwh']
        df['r_now'] = REVENUE_CONFIG['ppa_price_gbp_per_mwh']
        
        # Simple arbitrage strategy: charge when cheap, discharge when expensive
        df['charge_signal'] = df['cost_now'] < df['cost_now'].quantile(0.25)
        df['discharge_signal'] = df['imbalance_price'] > df['imbalance_price'].quantile(0.75)
        
        # Prevent simultaneous charge/discharge
        both = df['charge_signal'] & df['discharge_signal']
        df.loc[both, ['charge_signal', 'discharge_signal']] = False
        
        # Power dispatch
        sp_hours = 0.5
        df['charge_mw_cmd'] = df['charge_signal'].astype(float) * BESS_CONFIG['power_mw']
        df['discharge_mw_cmd'] = df['discharge_signal'].astype(float) * BESS_CONFIG['power_mw']
        
        # Energy (MWh)
        eta = np.sqrt(BESS_CONFIG['roundtrip_efficiency'])
        df['charge_mwh_net'] = (df['charge_mw_cmd'] * sp_hours) / eta
        df['discharge_mwh_net'] = (df['discharge_mw_cmd'] * sp_hours) * eta
        
        # SoC simulation
        soc = []
        soc_prev = BESS_CONFIG['initial_soc_mwh']
        for chg, dischg in zip(df['charge_mwh_net'], df['discharge_mwh_net']):
            soc_new = soc_prev + chg - dischg
            soc_new = np.clip(soc_new, BESS_CONFIG['soc_min_mwh'], BESS_CONFIG['soc_max_mwh'])
            soc.append(soc_new)
            soc_prev = soc_new
        df['soc_mwh'] = soc
        
        # Revenue calculations
        df['import_cost_gbp'] = df['charge_mwh_net'] * df['cost_now']
        df['export_revenue_gbp'] = df['discharge_mwh_net'] * df['r_now']
        df['vlp_revenue_gbp'] = df['discharge_mwh_net'] * VLP_CONFIG['participation_rate'] * VLP_CONFIG['avg_uplift_gbp_per_mwh']
        df['net_profit_gbp'] = df['export_revenue_gbp'] + df['vlp_revenue_gbp'] - df['import_cost_gbp']
        
        return df
    
    def optimize_chp(self, market_data: pd.DataFrame) -> pd.DataFrame:
        """Run CHP optimization"""
        df = market_data.copy()
        
        # Marginal cost calculation
        fuel_input_per_mwh_el = 1.0 / CHP_CONFIG['electrical_efficiency']
        base_cost = CHP_CONFIG['fuel_cost_gbp_per_mwh_th'] * fuel_input_per_mwh_el
        heat_credit = (CHP_CONFIG['fuel_cost_gbp_per_mwh_th'] * 
                      (CHP_CONFIG['heat_efficiency'] / CHP_CONFIG['electrical_efficiency']) * 0.5)
        df['chp_marginal_cost_gbp_per_mwh'] = base_cost - heat_credit
        
        # Flexibility dispatch
        df['flex_up_mw'] = CHP_CONFIG['max_output_mw'] - CHP_CONFIG['baseload_mw']
        df['flex_down_mw'] = CHP_CONFIG['baseload_mw'] - CHP_CONFIG['min_output_mw']
        
        df['flex_up_profitable'] = df['imbalance_price'] > df['chp_marginal_cost_gbp_per_mwh']
        df['flex_down_profitable'] = df['imbalance_price'] < df['chp_marginal_cost_gbp_per_mwh']
        
        # Dispatch
        df['chp_output_mw'] = CHP_CONFIG['baseload_mw']
        df.loc[df['flex_up_profitable'], 'chp_output_mw'] += df['flex_up_mw']
        df.loc[df['flex_down_profitable'], 'chp_output_mw'] -= df['flex_down_mw']
        
        df['chp_output_mw'] = df['chp_output_mw'].clip(
            CHP_CONFIG['min_output_mw'], 
            CHP_CONFIG['max_output_mw']
        )
        
        sp_hours = 0.5
        df['chp_mwh'] = df['chp_output_mw'] * sp_hours
        df['chp_revenue_gbp'] = df['chp_mwh'] * df['imbalance_price']
        df['chp_cost_gbp'] = df['chp_mwh'] * df['chp_marginal_cost_gbp_per_mwh']
        df['chp_profit_gbp'] = df['chp_revenue_gbp'] - df['chp_cost_gbp']
        
        return df
    
    def calculate_summary_metrics(self, bess_df: pd.DataFrame, chp_df: pd.DataFrame) -> Dict[str, Any]:
        """Calculate summary metrics"""
        
        # BESS metrics
        total_charged = bess_df['charge_mwh_net'].sum()
        total_discharged = bess_df['discharge_mwh_net'].sum()
        cycles = total_charged / BESS_CONFIG['capacity_mwh'] if BESS_CONFIG['capacity_mwh'] > 0 else 0
        
        bess_metrics = {
            'total_charged_mwh': total_charged,
            'total_discharged_mwh': total_discharged,
            'cycles_per_period': cycles,
            'total_import_cost': bess_df['import_cost_gbp'].sum(),
            'total_export_revenue': bess_df['export_revenue_gbp'].sum(),
            'total_vlp_revenue': bess_df['vlp_revenue_gbp'].sum(),
            'net_profit': bess_df['net_profit_gbp'].sum(),
            'avg_soc_pct': (bess_df['soc_mwh'].mean() / BESS_CONFIG['capacity_mwh']) * 100,
        }
        
        # CHP metrics
        chp_metrics = {
            'total_output_mwh': chp_df['chp_mwh'].sum(),
            'avg_output_mw': chp_df['chp_output_mw'].mean(),
            'total_revenue': chp_df['chp_revenue_gbp'].sum(),
            'total_cost': chp_df['chp_cost_gbp'].sum(),
            'net_profit': chp_df['chp_profit_gbp'].sum(),
        }
        
        # Combined
        combined = {
            'total_profit': bess_metrics['net_profit'] + chp_metrics['net_profit'] + REVENUE_CONFIG['dc_annual_gbp'] / 12,
            'dc_revenue_monthly': REVENUE_CONFIG['dc_annual_gbp'] / 12,
            'cm_revenue_annual': REVENUE_CONFIG['cm_capacity_mw'] * 1000 * REVENUE_CONFIG['cm_clearing_gbp_per_kw_year'],
        }
        
        return {
            'bess': bess_metrics,
            'chp': chp_metrics,
            'combined': combined,
        }
    
    def build_sheet_layout(self, summary: Dict[str, Any]) -> List[List[Any]]:
        """Build comprehensive sheet layout"""
        
        data = []
        
        # Header
        data.append(['GB POWER MARKET - BtM BESS/CHP MODEL', '', '', '', ''])
        data.append([f'Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}', '', '', '', ''])
        data.append(['', '', '', '', ''])
        
        # ASSET CONFIGURATION
        data.append(['═══════════════════════════════════════════════════════', '', '', '', ''])
        data.append(['ASSET CONFIGURATION', '', '', '', ''])
        data.append(['═══════════════════════════════════════════════════════', '', '', '', ''])
        data.append(['', '', '', '', ''])
        
        data.append(['BESS Specification', '', '', '', ''])
        data.append(['Capacity (MWh)', BESS_CONFIG['capacity_mwh'], '', '', ''])
        data.append(['Power (MW)', BESS_CONFIG['power_mw'], '', '', ''])
        data.append(['Round-trip Efficiency', f"{BESS_CONFIG['roundtrip_efficiency']:.1%}", '', '', ''])
        data.append(['Max Cycles/Day', BESS_CONFIG['max_cycles_per_day'], '', '', ''])
        data.append(['Degradation Cost (£/cycle)', BESS_CONFIG['degradation_cost_gbp_per_cycle'], '', '', ''])
        data.append(['', '', '', '', ''])
        
        data.append(['CHP Specification', '', '', '', ''])
        data.append(['Max Output (MW)', CHP_CONFIG['max_output_mw'], '', '', ''])
        data.append(['Min Output (MW)', CHP_CONFIG['min_output_mw'], '', '', ''])
        data.append(['Electrical Efficiency', f"{CHP_CONFIG['electrical_efficiency']:.1%}", '', '', ''])
        data.append(['Heat Efficiency', f"{CHP_CONFIG['heat_efficiency']:.1%}", '', '', ''])
        data.append(['Fuel Cost (£/MWh_th)', CHP_CONFIG['fuel_cost_gbp_per_mwh_th'], '', '', ''])
        data.append(['', '', '', '', ''])
        
        # PERFORMANCE SUMMARY
        data.append(['═══════════════════════════════════════════════════════', '', '', '', ''])
        data.append(['PERFORMANCE SUMMARY (30-DAY PERIOD)', '', '', '', ''])
        data.append(['═══════════════════════════════════════════════════════', '', '', '', ''])
        data.append(['', '', '', '', ''])
        
        bess = summary['bess']
        data.append(['BESS Performance', '', '', '', ''])
        data.append(['Total Charged (MWh)', f"{bess['total_charged_mwh']:.1f}", '', '', ''])
        data.append(['Total Discharged (MWh)', f"{bess['total_discharged_mwh']:.1f}", '', '', ''])
        data.append(['Cycles Completed', f"{bess['cycles_per_period']:.1f}", '', '', ''])
        data.append(['Avg SoC', f"{bess['avg_soc_pct']:.1f}%", '', '', ''])
        data.append(['', '', '', '', ''])
        
        chp = summary['chp']
        data.append(['CHP Performance', '', '', '', ''])
        data.append(['Total Output (MWh)', f"{chp['total_output_mwh']:.1f}", '', '', ''])
        data.append(['Avg Output (MW)', f"{chp['avg_output_mw']:.2f}", '', '', ''])
        data.append(['', '', '', '', ''])
        
        # REVENUE BREAKDOWN
        data.append(['═══════════════════════════════════════════════════════', '', '', '', ''])
        data.append(['REVENUE BREAKDOWN', '', '', '', ''])
        data.append(['═══════════════════════════════════════════════════════', '', '', '', ''])
        data.append(['', '', '', '', ''])
        
        data.append(['Revenue Stream', 'Amount (£)', 'Annual (£)', 'Notes', ''])
        data.append(['', '', '', '', ''])
        
        # BESS Revenue
        data.append(['BESS Export Revenue', f"{bess['total_export_revenue']:,.0f}", 
                    f"{bess['total_export_revenue'] * 12:,.0f}", 'PPA discharge', ''])
        data.append(['BESS VLP Revenue', f"{bess['total_vlp_revenue']:,.0f}", 
                    f"{bess['total_vlp_revenue'] * 12:,.0f}", 'Balancing mechanism', ''])
        data.append(['BESS Import Cost', f"({bess['total_import_cost']:,.0f})", 
                    f"({bess['total_import_cost'] * 12:,.0f})", 'Charging costs', ''])
        data.append(['BESS Net Profit', f"{bess['net_profit']:,.0f}", 
                    f"{bess['net_profit'] * 12:,.0f}", 'Arbitrage profit', ''])
        data.append(['', '', '', '', ''])
        
        # CHP Revenue
        data.append(['CHP Export Revenue', f"{chp['total_revenue']:,.0f}", 
                    f"{chp['total_revenue'] * 12:,.0f}", 'Electricity sales', ''])
        data.append(['CHP Fuel Cost', f"({chp['total_cost']:,.0f})", 
                    f"({chp['total_cost'] * 12:,.0f})", 'Gas consumption', ''])
        data.append(['CHP Net Profit', f"{chp['net_profit']:,.0f}", 
                    f"{chp['net_profit'] * 12:,.0f}", 'Operating profit', ''])
        data.append(['', '', '', '', ''])
        
        # Other Revenue
        combined = summary['combined']
        data.append(['Dynamic Containment', f"{combined['dc_revenue_monthly']:,.0f}", 
                    f"{REVENUE_CONFIG['dc_annual_gbp']:,.0f}", 'FFR service', ''])
        data.append(['Capacity Market', 'N/A', 
                    f"{combined['cm_revenue_annual']:,.0f}", 'Capacity payments', ''])
        data.append(['', '', '', '', ''])
        
        # Total
        total_monthly = bess['net_profit'] + chp['net_profit'] + combined['dc_revenue_monthly']
        total_annual = total_monthly * 12 + combined['cm_revenue_annual']
        data.append(['TOTAL PROFIT', f"{total_monthly:,.0f}", f"{total_annual:,.0f}", 'Combined portfolio', ''])
        data.append(['', '', '', '', ''])
        
        # KEY INSIGHTS
        data.append(['═══════════════════════════════════════════════════════', '', '', '', ''])
        data.append(['KEY INSIGHTS', '', '', '', ''])
        data.append(['═══════════════════════════════════════════════════════', '', '', '', ''])
        data.append(['', '', '', '', ''])
        
        roi_pct = (total_annual / (BESS_CONFIG['capacity_mwh'] * 500000 + CHP_CONFIG['max_output_mw'] * 800000)) * 100
        data.append([f"• Portfolio ROI: {roi_pct:.1f}% per year", '', '', '', ''])
        data.append([f"• BESS cycles/year: {bess['cycles_per_period'] * 12:.0f} (max: {BESS_CONFIG['max_cycles_per_day'] * 365:.0f})", '', '', '', ''])
        data.append([f"• CHP capacity factor: {(chp['avg_output_mw'] / CHP_CONFIG['max_output_mw']) * 100:.1f}%", '', '', '', ''])
        data.append([f"• Revenue mix: {(bess['net_profit'] / total_monthly * 100):.0f}% BESS, {(chp['net_profit'] / total_monthly * 100):.0f}% CHP, {(combined['dc_revenue_monthly'] / total_monthly * 100):.0f}% FFR", '', '', '', ''])
        
        return data
    
    def write_to_sheet(self, data: List[List[Any]]):
        """Write data to BtM sheet"""
        
        # Clear existing content
        clear_body = {}
        self.sheets_service.spreadsheets().values().clear(
            spreadsheetId=SPREADSHEET_ID,
            range=f"{SHEET_NAME}!A1:Z1000",
            body=clear_body
        ).execute()
        
        # Write new data
        body = {'values': data}
        self.sheets_service.spreadsheets().values().update(
            spreadsheetId=SPREADSHEET_ID,
            range=f"{SHEET_NAME}!A1",
            valueInputOption='USER_ENTERED',
            body=body
        ).execute()
        
        print(f"✅ Written {len(data)} rows to {SHEET_NAME} sheet")
    
    def run(self):
        """Run complete model build"""
        print("\n🔋 GB POWER MARKET - BtM BESS/CHP MODEL BUILDER")
        print("=" * 60)
        
        # Get market data
        print("\n1️⃣  Fetching market data from BigQuery...")
        market_data = self.get_market_data(days_back=30)
        print(f"   Retrieved {len(market_data)} settlement periods")
        
        # Run optimizations
        print("\n2️⃣  Running BESS optimization...")
        bess_results = self.optimize_bess(market_data)
        
        print("\n3️⃣  Running CHP optimization...")
        chp_results = self.optimize_chp(market_data)
        
        # Calculate summary
        print("\n4️⃣  Calculating summary metrics...")
        summary = self.calculate_summary_metrics(bess_results, chp_results)
        
        # Build sheet layout
        print("\n5️⃣  Building sheet layout...")
        sheet_data = self.build_sheet_layout(summary)
        
        # Write to sheet
        print("\n6️⃣  Writing to Google Sheets...")
        self.write_to_sheet(sheet_data)
        
        # Print summary
        print("\n" + "=" * 60)
        print("📊 SUMMARY")
        print("=" * 60)
        print(f"\nBESS Performance:")
        print(f"  • Cycles: {summary['bess']['cycles_per_period']:.1f}")
        print(f"  • Net Profit: £{summary['bess']['net_profit']:,.0f}")
        print(f"\nCHP Performance:")
        print(f"  • Output: {summary['chp']['total_output_mwh']:.1f} MWh")
        print(f"  • Net Profit: £{summary['chp']['net_profit']:,.0f}")
        print(f"\nTotal Monthly Profit: £{summary['combined']['total_profit']:,.0f}")
        print(f"Total Annual Profit: £{(summary['combined']['total_profit'] * 12 + summary['combined']['cm_revenue_annual']):,.0f}")
        print("\n✅ BtM sheet updated successfully!")
        print(f"\nView: https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/edit#gid=0&range=A1")


if __name__ == "__main__":
    try:
        builder = BtMModelBuilder()
        builder.run()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

#!/usr/bin/env python3
"""
BESS Revenue & Profit Calculator
Calculates comprehensive battery storage revenue streams:
1. Energy Arbitrage (buy low, sell high)
2. System Operator (SO) Payments:
   - BID (Bid Offer Data) - paid to reduce demand
   - BOD (Bid Offer Data) - paid to increase supply
   - FFR (Firm Frequency Response)
   - DCR (Dynamic Containment Response)
   - DM (Dynamic Moderation)
   - DR (Dynamic Regulation)
3. Capacity Market payments
4. PPA contract revenue
5. Cost analysis (all levies included)

Uses Min/Avg/Max kW demand parameters from B17:B19
"""

import gspread
from google.oauth2.service_account import Credentials
from google.cloud import bigquery
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

# Configuration
DASHBOARD_V2_ID = '1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA'
CREDENTIALS_FILE = 'inner-cinema-credentials.json'
PROJECT_ID = 'inner-cinema-476211-u9'

# Energy cost rates (2025/26)
COST_RATES = {
    'ccl': 0.00775,      # Climate Change Levy (£/kWh)
    'ro': 0.0619,        # Renewables Obligation (£/kWh)
    'fit': 0.0115,       # Feed-in Tariff (£/kWh)
    'bsuos_avg': 0.0045, # BSUoS average (£/kWh)
    'tnuos_hv': 0.0125,  # TNUoS HV (£/kWh)
}

# SO Payment typical rates (£/MWh) - these vary by auction
SO_RATES = {
    'ffr_primary': 12.0,      # Firm Frequency Response Primary (£/MW/h)
    'ffr_secondary': 8.0,     # FFR Secondary (£/MW/h)
    'dcr_high': 17.0,         # Dynamic Containment High (£/MW/h)
    'dcr_low': 11.0,          # Dynamic Containment Low (£/MW/h)
    'dm': 9.0,                # Dynamic Moderation (£/MW/h)
    'dr': 10.0,               # Dynamic Regulation (£/MW/h)
    'bid_acceptance': 0.85,   # % of BID offers typically accepted
    'bod_acceptance': 0.75,   # % of BOD offers typically accepted
}

# Capacity Market (typical £/kW/year)
CAPACITY_MARKET_RATE = 6.0  # £6/kW/year typical for BESS

def connect():
    """Connect to Google Sheets and BigQuery"""
    creds = Credentials.from_service_account_file(
        CREDENTIALS_FILE,
        scopes=[
            'https://www.googleapis.com/auth/spreadsheets',
            'https://www.googleapis.com/auth/bigquery'
        ]
    )
    
    gs_client = gspread.authorize(creds)
    bq_client = bigquery.Client(credentials=creds, project=PROJECT_ID)
    
    return gs_client, bq_client

def get_system_prices(bq_client, months_back=3):
    """Get System prices (SSP, SBP, BID, BOD) from BigQuery"""
    query = f"""
    SELECT 
      settlement_date,
      settlement_period,
      system_sell_price as ssp,
      system_buy_price as sbp
    FROM `{PROJECT_ID}.uk_energy_prod.balancing_prices`
    WHERE settlement_date >= DATE_SUB(CURRENT_DATE(), INTERVAL {months_back} MONTH)
      AND settlement_date <= CURRENT_DATE()
      AND system_sell_price IS NOT NULL
    ORDER BY settlement_date DESC, settlement_period DESC
    """
    
    try:
        print(f"   📊 Querying {months_back} months of price data...")
        df = bq_client.query(query).to_dataframe()
        print(f"   ✅ Retrieved {len(df):,} settlement periods")
        return df
    except Exception as e:
        print(f"   ⚠️  Could not fetch prices: {e}")
        print(f"   ℹ️  Generating sample data...")
        
        # Generate realistic sample data
        dates = []
        sps = []
        ssps = []
        sbps = []
        
        start_date = datetime.now().date() - timedelta(days=months_back * 30)
        for day_offset in range(months_back * 30):
            current_date = start_date + timedelta(days=day_offset)
            for sp in range(1, 49):
                dates.append(current_date)
                sps.append(sp)
                
                # Realistic price simulation
                hour = (sp - 1) // 2
                base_price = 45.0
                
                # Peak pricing
                if 16 <= hour < 20:  # Peak
                    time_premium = 30.0
                elif 8 <= hour < 16:  # Day
                    time_premium = 15.0
                else:  # Night
                    time_premium = -20.0
                
                noise = np.random.normal(0, 8)
                ssp = max(5.0, base_price + time_premium + noise)
                sbp = ssp + np.random.uniform(0.5, 3.0)  # SBP higher than SSP
                
                ssps.append(ssp)
                sbps.append(sbp)
        
        return pd.DataFrame({
            'settlement_date': dates,
            'settlement_period': sps,
            'ssp': ssps,
            'sbp': sbps
        })

def get_time_band_for_sp(settlement_period):
    """Determine time band (RED/AMBER/GREEN) for settlement period"""
    if 32 <= settlement_period <= 39:
        return "RED"
    if (17 <= settlement_period <= 32) or (40 <= settlement_period <= 44):
        return "AMBER"
    return "GREEN"

def calculate_energy_costs(energy_kwh, duos_rates, time_band):
    """Calculate total energy costs including all levies"""
    duos_kwh = duos_rates[time_band.lower()]
    
    total_cost_per_kwh = (
        duos_kwh +
        COST_RATES['ccl'] +
        COST_RATES['ro'] +
        COST_RATES['fit'] +
        COST_RATES['bsuos_avg'] +
        COST_RATES['tnuos_hv']
    )
    
    return energy_kwh * total_cost_per_kwh

def calculate_arbitrage_revenue(prices_df, battery_params, duos_rates):
    """
    Calculate energy arbitrage revenue
    Buy when cheap (GREEN periods), sell when expensive (RED/AMBER periods)
    
    Args:
        prices_df: DataFrame with SSP/SBP prices
        battery_params: Dict with min_kw, avg_kw, max_kw, capacity_kwh, efficiency
        duos_rates: DUoS rates by time band
    """
    results = []
    
    for _, row in prices_df.iterrows():
        sp = row['settlement_period']
        ssp = row['ssp']
        sbp = row['sbp']
        date = row['settlement_date']
        time_band = get_time_band_for_sp(sp)
        
        # Determine operation mode based on time band
        if time_band == "GREEN":
            # CHARGE mode - buy energy at SBP
            energy_kwh = battery_params['min_kw'] * 0.5  # 30 min period
            buy_cost = (sbp / 1000) * energy_kwh  # £/MWh to £/kWh
            levies_cost = calculate_energy_costs(energy_kwh, duos_rates, time_band)
            total_cost = buy_cost + levies_cost
            revenue = 0
            net_profit = -total_cost
            mode = "CHARGE"
            
        elif time_band == "RED":
            # DISCHARGE mode - sell energy at SSP
            energy_kwh = battery_params['max_kw'] * 0.5 * battery_params['efficiency']
            sell_revenue = (ssp / 1000) * energy_kwh
            # No costs when discharging (already paid when charging)
            total_cost = 0
            revenue = sell_revenue
            net_profit = revenue
            mode = "DISCHARGE"
            
        else:  # AMBER
            # Selective operation based on price
            if ssp > sbp * 1.2:  # 20% spread makes it worthwhile
                energy_kwh = battery_params['avg_kw'] * 0.5 * battery_params['efficiency']
                sell_revenue = (ssp / 1000) * energy_kwh
                revenue = sell_revenue
                total_cost = 0
                net_profit = revenue
                mode = "DISCHARGE"
            else:
                # Hold or light charge
                energy_kwh = battery_params['min_kw'] * 0.5
                buy_cost = (sbp / 1000) * energy_kwh
                levies_cost = calculate_energy_costs(energy_kwh, duos_rates, time_band)
                total_cost = buy_cost + levies_cost
                revenue = 0
                net_profit = -total_cost
                mode = "CHARGE"
        
        results.append({
            'date': date,
            'sp': sp,
            'band': time_band,
            'mode': mode,
            'energy_kwh': energy_kwh,
            'ssp': ssp,
            'sbp': sbp,
            'revenue': revenue,
            'costs': total_cost,
            'net_profit': net_profit
        })
    
    return pd.DataFrame(results)

def calculate_so_payments(battery_params, days=30):
    """
    Calculate System Operator service payments (BID/BOD/FFR/DCR/DM/DR)
    
    Args:
        battery_params: Dict with capacity_mw, availability_hours
        days: Number of days to calculate for
    """
    capacity_mw = battery_params['max_kw'] / 1000  # Convert kW to MW
    
    # FFR (Firm Frequency Response) - 24/7 availability payment
    # Typical: 4 hours/day at £12/MW/h
    ffr_hours = 4 * days
    ffr_revenue = capacity_mw * ffr_hours * SO_RATES['ffr_primary']
    
    # DCR (Dynamic Containment) - high value, 24/7 availability
    # Typical: 6 hours/day at £17/MW/h
    dcr_hours = 6 * days
    dcr_revenue = capacity_mw * dcr_hours * SO_RATES['dcr_high']
    
    # Dynamic Moderation - medium value
    # Typical: 3 hours/day at £9/MW/h
    dm_hours = 3 * days
    dm_revenue = capacity_mw * dm_hours * SO_RATES['dm']
    
    # Dynamic Regulation - medium value
    # Typical: 3 hours/day at £10/MW/h
    dr_hours = 3 * days
    dr_revenue = capacity_mw * dr_hours * SO_RATES['dr']
    
    # BID/BOD (Balancing Mechanism) - utilization payments
    # Estimate: 2 BID events/day at 1 hour each, 85% acceptance
    bid_events = 2 * days
    bid_hours = bid_events * 1.0  # 1 hour per event
    # BID payment is typically price spread × volume
    bid_avg_payment = 50.0  # £50/MWh typical BID premium
    bid_volume_mwh = capacity_mw * bid_hours * SO_RATES['bid_acceptance']
    bid_revenue = bid_volume_mwh * bid_avg_payment
    
    # BOD (offer to increase generation/reduce demand)
    # Estimate: 1 BOD event/day, 75% acceptance
    bod_events = 1 * days
    bod_hours = bod_events * 1.0
    bod_avg_payment = 40.0  # £40/MWh typical BOD premium
    bod_volume_mwh = capacity_mw * bod_hours * SO_RATES['bod_acceptance']
    bod_revenue = bod_volume_mwh * bod_avg_payment
    
    return {
        'ffr': {'hours': ffr_hours, 'revenue': ffr_revenue},
        'dcr': {'hours': dcr_hours, 'revenue': dcr_revenue},
        'dm': {'hours': dm_hours, 'revenue': dm_revenue},
        'dr': {'hours': dr_hours, 'revenue': dr_revenue},
        'bid': {'events': bid_events, 'volume_mwh': bid_volume_mwh, 'revenue': bid_revenue},
        'bod': {'events': bod_events, 'volume_mwh': bod_volume_mwh, 'revenue': bod_revenue},
        'total': ffr_revenue + dcr_revenue + dm_revenue + dr_revenue + bid_revenue + bod_revenue
    }

def calculate_capacity_market(battery_params):
    """Calculate annual Capacity Market revenue"""
    capacity_kw = battery_params['max_kw']
    annual_revenue = capacity_kw * CAPACITY_MARKET_RATE
    return annual_revenue

def calculate_ppa_revenue(battery_params, ppa_price, days=30):
    """
    Calculate PPA contract revenue
    Assumes discharge during peak periods
    """
    # Typical discharge pattern: 2-3 hours/day during RED periods
    discharge_hours_per_day = 2.5
    discharge_days = days
    
    total_discharge_hours = discharge_hours_per_day * discharge_days
    energy_discharged_mwh = (battery_params['max_kw'] / 1000) * total_discharge_hours * battery_params['efficiency']
    
    ppa_revenue = energy_discharged_mwh * ppa_price
    
    return {
        'discharge_hours': total_discharge_hours,
        'energy_mwh': energy_discharged_mwh,
        'revenue': ppa_revenue
    }

def main():
    """Main execution"""
    print("=" * 80)
    print("💰 BESS REVENUE & PROFIT CALCULATOR")
    print("=" * 80)
    print("\n✅ Revenue Streams Calculated:")
    print("   1. Energy Arbitrage (buy low GREEN, sell high RED)")
    print("   2. System Operator Payments:")
    print("      • FFR (Firm Frequency Response)")
    print("      • DCR (Dynamic Containment)")
    print("      • DM/DR (Dynamic Moderation/Regulation)")
    print("      • BID/BOD (Balancing Mechanism)")
    print("   3. Capacity Market payments")
    print("   4. PPA contract revenue")
    print("   5. Total costs (all levies)")
    
    try:
        # Connect
        print("\n🔐 Connecting...")
        gs_client, bq_client = connect()
        ss = gs_client.open_by_key(DASHBOARD_V2_ID)
        bess = ss.worksheet('BESS')
        print("   ✅ Connected")
        
        # Read battery parameters
        print("\n📊 Reading battery parameters...")
        params_range = bess.get('B17:B19')
        
        if params_range and len(params_range) >= 3:
            min_kw = float(str(params_range[0][0]).replace(',', ''))
            avg_kw = float(str(params_range[1][0]).replace(',', ''))
            max_kw = float(str(params_range[2][0]).replace(',', ''))
            
            # Calculate capacity (assume 2 hour duration)
            capacity_kwh = max_kw * 2
            efficiency = 0.90  # 90% round-trip efficiency typical for Li-ion
            
            battery_params = {
                'min_kw': min_kw,
                'avg_kw': avg_kw,
                'max_kw': max_kw,
                'capacity_kwh': capacity_kwh,
                'efficiency': efficiency
            }
            
            print(f"   Min Power: {min_kw:,.0f} kW")
            print(f"   Avg Power: {avg_kw:,.0f} kW")
            print(f"   Max Power: {max_kw:,.0f} kW")
            print(f"   Capacity: {capacity_kwh:,.0f} kWh (2hr duration)")
            print(f"   Efficiency: {efficiency*100:.0f}%")
        else:
            print("   ⚠️  No battery parameters found, using defaults")
            battery_params = {
                'min_kw': 500,
                'avg_kw': 1000,
                'max_kw': 2000,
                'capacity_kwh': 4000,
                'efficiency': 0.90
            }
        
        # Read PPA price
        print("\n💷 Reading PPA price from B21...")
        ppa_cell = bess.acell('B21').value
        if ppa_cell:
            ppa_price = float(str(ppa_cell).replace('£', '').replace(',', ''))
            print(f"   ✅ PPA Price: £{ppa_price:.2f}/MWh")
        else:
            ppa_price = 85.0
            print(f"   ℹ️  Using default PPA: £{ppa_price}/MWh")
        
        # Read DUoS rates
        print("\n📊 Reading DUoS rates...")
        duos_values = bess.get('B10:D10')
        if duos_values and len(duos_values[0]) >= 3:
            duos_rates = {
                'red': float(duos_values[0][0].split()[0]) / 100,
                'amber': float(duos_values[0][1].split()[0]) / 100,
                'green': float(duos_values[0][2].split()[0]) / 100
            }
        else:
            duos_rates = {'red': 0.01764, 'amber': 0.00205, 'green': 0.00011}
        
        # Get system prices (3 months for detailed analysis)
        print("\n🔍 Fetching system prices...")
        prices_df = get_system_prices(bq_client, months_back=3)
        
        # Calculate energy arbitrage
        print("\n⚙️  Calculating energy arbitrage revenue...")
        arbitrage_df = calculate_arbitrage_revenue(prices_df, battery_params, duos_rates)
        
        arb_revenue = arbitrage_df['revenue'].sum()
        arb_costs = arbitrage_df['costs'].sum()
        arb_profit = arbitrage_df['net_profit'].sum()
        days_analyzed = len(prices_df['settlement_date'].unique())
        
        print(f"   Period: {days_analyzed} days")
        print(f"   Revenue: £{arb_revenue:,.2f}")
        print(f"   Costs: £{arb_costs:,.2f}")
        print(f"   Net Profit: £{arb_profit:,.2f}")
        print(f"   Daily Average: £{arb_profit/days_analyzed:,.2f}/day")
        
        # Calculate SO payments (use same period)
        print("\n⚙️  Calculating System Operator payments...")
        so_payments = calculate_so_payments(battery_params, days=days_analyzed)
        
        print(f"   FFR: £{so_payments['ffr']['revenue']:,.2f} ({so_payments['ffr']['hours']:.0f} hours)")
        print(f"   DCR: £{so_payments['dcr']['revenue']:,.2f} ({so_payments['dcr']['hours']:.0f} hours)")
        print(f"   DM: £{so_payments['dm']['revenue']:,.2f} ({so_payments['dm']['hours']:.0f} hours)")
        print(f"   DR: £{so_payments['dr']['revenue']:,.2f} ({so_payments['dr']['hours']:.0f} hours)")
        print(f"   BID: £{so_payments['bid']['revenue']:,.2f} ({so_payments['bid']['events']:.0f} events)")
        print(f"   BOD: £{so_payments['bod']['revenue']:,.2f} ({so_payments['bod']['events']:.0f} events)")
        print(f"   Total SO: £{so_payments['total']:,.2f}")
        print(f"   Daily Average: £{so_payments['total']/days_analyzed:,.2f}/day")
        
        # Calculate Capacity Market
        print("\n⚙️  Calculating Capacity Market revenue...")
        cm_annual = calculate_capacity_market(battery_params)
        cm_period = cm_annual * (days_analyzed / 365)
        print(f"   Annual: £{cm_annual:,.2f}")
        print(f"   Period ({days_analyzed} days): £{cm_period:,.2f}")
        print(f"   Daily Average: £{cm_period/days_analyzed:,.2f}/day")
        
        # Calculate PPA revenue
        print("\n⚙️  Calculating PPA contract revenue...")
        ppa_result = calculate_ppa_revenue(battery_params, ppa_price, days=days_analyzed)
        print(f"   Energy: {ppa_result['energy_mwh']:,.2f} MWh")
        print(f"   Revenue: £{ppa_result['revenue']:,.2f}")
        print(f"   Daily Average: £{ppa_result['revenue']/days_analyzed:,.2f}/day")
        
        # Total summary
        total_revenue = arb_revenue + so_payments['total'] + cm_period + ppa_result['revenue']
        total_costs = arb_costs
        total_profit = total_revenue - total_costs
        
        print("\n" + "=" * 80)
        print("📊 TOTAL REVENUE & PROFIT SUMMARY")
        print("=" * 80)
        print(f"\n Period: {days_analyzed} days")
        print(f"\n REVENUE BREAKDOWN:")
        print(f"   Energy Arbitrage:    £{arb_revenue:>12,.2f} ({arb_revenue/total_revenue*100:5.1f}%)")
        print(f"   SO Payments:         £{so_payments['total']:>12,.2f} ({so_payments['total']/total_revenue*100:5.1f}%)")
        print(f"   Capacity Market:     £{cm_period:>12,.2f} ({cm_period/total_revenue*100:5.1f}%)")
        print(f"   PPA Revenue:         £{ppa_result['revenue']:>12,.2f} ({ppa_result['revenue']/total_revenue*100:5.1f}%)")
        print(f"   ────────────────────────────────")
        print(f"   TOTAL REVENUE:       £{total_revenue:>12,.2f}")
        
        print(f"\n COSTS:")
        print(f"   Energy & Levies:     £{total_costs:>12,.2f}")
        
        print(f"\n NET PROFIT:")
        print(f"   Period Profit:       £{total_profit:>12,.2f}")
        print(f"   Daily Average:       £{total_profit/days_analyzed:>12,.2f}/day")
        print(f"   Annual Projection:   £{total_profit/days_analyzed*365:>12,.2f}/year")
        
        print(f"\n MARGINS:")
        print(f"   Gross Margin:        {(total_profit/total_revenue*100):>12.1f}%")
        print(f"   ROI per cycle:       {(total_profit/arb_costs*100) if arb_costs > 0 else 0:>12.1f}%")
        
        # Write to sheet
        print("\n📝 Writing results to BESS sheet...")
        
        output = [
            [""],
            ["BESS REVENUE & PROFIT ANALYSIS"],
            ["Analysis Date:", datetime.now().strftime('%Y-%m-%d %H:%M')],
            ["Period:", f"{days_analyzed} days"],
            ["Battery:", f"{battery_params['max_kw']:,.0f} kW / {battery_params['capacity_kwh']:,.0f} kWh"],
            [""],
            ["REVENUE STREAMS", "Amount", "% of Total", "Daily Avg"],
            ["Energy Arbitrage", f"£{arb_revenue:,.2f}", f"{arb_revenue/total_revenue*100:.1f}%", f"£{arb_revenue/days_analyzed:.2f}"],
            ["SO Payments (FFR/DCR/DM/DR/BID/BOD)", f"£{so_payments['total']:,.2f}", f"{so_payments['total']/total_revenue*100:.1f}%", f"£{so_payments['total']/days_analyzed:.2f}"],
            ["Capacity Market", f"£{cm_period:,.2f}", f"{cm_period/total_revenue*100:.1f}%", f"£{cm_period/days_analyzed:.2f}"],
            ["PPA Revenue", f"£{ppa_result['revenue']:,.2f}", f"{ppa_result['revenue']/total_revenue*100:.1f}%", f"£{ppa_result['revenue']/days_analyzed:.2f}"],
            ["TOTAL REVENUE", f"£{total_revenue:,.2f}", "100.0%", f"£{total_revenue/days_analyzed:.2f}"],
            [""],
            ["COSTS", "", "", ""],
            ["Energy & All Levies", f"£{total_costs:,.2f}", "", f"£{total_costs/days_analyzed:.2f}"],
            [""],
            ["NET PROFIT", f"£{total_profit:,.2f}", "", f"£{total_profit/days_analyzed:.2f}"],
            ["Annual Projection", f"£{total_profit/days_analyzed*365:,.2f}", "", ""],
            [""],
            ["SO PAYMENTS DETAIL"],
            ["Service", "Hours/Events", "Revenue"],
            ["FFR (Firm Frequency Response)", f"{so_payments['ffr']['hours']:.0f} hours", f"£{so_payments['ffr']['revenue']:,.2f}"],
            ["DCR (Dynamic Containment)", f"{so_payments['dcr']['hours']:.0f} hours", f"£{so_payments['dcr']['revenue']:,.2f}"],
            ["DM (Dynamic Moderation)", f"{so_payments['dm']['hours']:.0f} hours", f"£{so_payments['dm']['revenue']:,.2f}"],
            ["DR (Dynamic Regulation)", f"{so_payments['dr']['hours']:.0f} hours", f"£{so_payments['dr']['revenue']:,.2f}"],
            ["BID (Balancing Bids)", f"{so_payments['bid']['events']:.0f} events", f"£{so_payments['bid']['revenue']:,.2f}"],
            ["BOD (Balancing Offers)", f"{so_payments['bod']['events']:.0f} events", f"£{so_payments['bod']['revenue']:,.2f}"],
            [""],
            ["KEY METRICS"],
            ["Gross Margin:", f"{(total_profit/total_revenue*100):.1f}%"],
            ["ROI per Cycle:", f"{(total_profit/arb_costs*100) if arb_costs > 0 else 0:.1f}%"],
            ["Revenue per kW (annual):", f"£{(total_profit/days_analyzed*365)/battery_params['max_kw']:.2f}/kW"],
        ]
        
        # Write starting at row 170 to avoid PPA analysis
        bess.update(values=output, range_name='A170:D205')
        print(f"   ✅ Written to A170:D205")
        
        # Update summary in A20
        summary = f"Revenue: £{total_profit/days_analyzed:,.0f}/day | SO: £{so_payments['total']/days_analyzed:,.0f}/day | Annual: £{total_profit/days_analyzed*365:,.0f}"
        bess.update(values=[[summary]], range_name='A20')
        
        print("\n" + "=" * 80)
        print("✅ REVENUE & PROFIT ANALYSIS COMPLETE!")
        print("=" * 80)
        
        print(f"\n💡 Key Insights:")
        
        # Revenue mix
        so_pct = so_payments['total'] / total_revenue * 100
        arb_pct = arb_revenue / total_revenue * 100
        
        if so_pct > 50:
            print(f"   🎯 SO Services are your primary revenue ({so_pct:.0f}%)")
            print(f"      Focus: Maximize FFR/DCR availability")
        elif arb_pct > 50:
            print(f"   🎯 Energy Arbitrage is your primary revenue ({arb_pct:.0f}%)")
            print(f"      Focus: Optimize charge/discharge timing")
        else:
            print(f"   🎯 Balanced revenue mix:")
            print(f"      SO Services: {so_pct:.0f}% | Arbitrage: {arb_pct:.0f}%")
        
        # Profitability
        annual_profit = total_profit / days_analyzed * 365
        if annual_profit > battery_params['capacity_kwh'] * 200:  # £200/kWh is good
            print(f"   🟢 EXCELLENT profitability: £{annual_profit:,.0f}/year")
        elif annual_profit > battery_params['capacity_kwh'] * 100:
            print(f"   🟡 GOOD profitability: £{annual_profit:,.0f}/year")
        else:
            print(f"   🔴 Review opportunities: £{annual_profit:,.0f}/year")
        
        print(f"\n🔗 View: https://docs.google.com/spreadsheets/d/{DASHBOARD_V2_ID}/edit")
        
        return 0
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == '__main__':
    exit(main())

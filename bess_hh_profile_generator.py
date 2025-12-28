#!/usr/bin/env python3
"""
BESS Half-Hourly Profile Generator
Generates optimal charge/discharge schedules based on:
- System imbalance prices (bmrs_costs)
- DUoS time bands (Red/Amber/Green)
- Battery constraints (capacity, power, efficiency)
- Revenue optimization

Output: CSV or Google Sheets with 48 settlement periods per day
"""

import gspread
from google.oauth2.service_account import Credentials
from google.cloud import bigquery
from datetime import datetime, timedelta, time
import pandas as pd
import pytz
import sys
import os

# Configuration
SHEET_ID = '1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA'  # GB Live 2 - CORRECT!
PROJECT_ID = "inner-cinema-476211-u9"
DATASET = "uk_energy_prod"
DATASET_GB = "gb_power"
CREDS_PATH = '/home/george/inner-cinema-credentials.json'

# DUoS time bands (UK time) - Standard configuration
DUOS_BANDS = {
    'RED': {
        'periods': [(16, 0, 19, 30)],  # 16:00-19:30 weekdays
        'weekdays_only': True,
        'color': '#FF4444'
    },
    'AMBER': {
        'periods': [(8, 0, 16, 0), (19, 30, 22, 0)],  # 08:00-16:00, 19:30-22:00 weekdays
        'weekdays_only': True,
        'color': '#FFA500'
    },
    'GREEN': {
        'periods': [(0, 0, 8, 0), (22, 0, 23, 59)],  # 00:00-08:00, 22:00-23:59 + all weekend
        'weekdays_only': False,
        'color': '#00FF00'
    }
}

# Default battery parameters (can be overridden)
DEFAULT_BATTERY = {
    'capacity_mwh': 2.0,        # Battery capacity (MWh)
    'max_charge_mw': 1.0,       # Max charge rate (MW)
    'max_discharge_mw': 1.0,    # Max discharge rate (MW)
    'efficiency': 0.90,         # Round-trip efficiency (90%)
    'min_soc': 0.10,           # Minimum state of charge (10%)
    'max_soc': 0.95            # Maximum state of charge (95%)
}


def get_duos_band(dt, is_weekend):
    """
    Determine DUoS band for a given datetime
    Args:
        dt: datetime object (UK time)
        is_weekend: boolean
    Returns:
        band name ('RED', 'AMBER', 'GREEN')
    """
    if is_weekend:
        return 'GREEN'
    
    hour = dt.hour
    minute = dt.minute
    current_mins = hour * 60 + minute
    
    # Check RED (16:00-19:30 weekdays)
    if 16 * 60 <= current_mins < 19 * 60 + 30:
        return 'RED'
    
    # Check AMBER (08:00-16:00, 19:30-22:00 weekdays)
    if (8 * 60 <= current_mins < 16 * 60) or (19 * 60 + 30 <= current_mins < 22 * 60):
        return 'AMBER'
    
    # Otherwise GREEN
    return 'GREEN'


def get_duos_rates_from_bq(dno_key, voltage_level):
    """
    Fetch DUoS rates from BigQuery
    NOTE: gb_power dataset is in EU location
    """
    client = bigquery.Client(project=PROJECT_ID, location="EU")
    
    query = f"""
    SELECT 
        time_band_name,
        ROUND(AVG(unit_rate_p_kwh), 4) as rate_p_kwh
    FROM `{PROJECT_ID}.{DATASET_GB}.duos_unit_rates`
    WHERE dno_key = '{dno_key}'
      AND voltage_level = '{voltage_level}'
    GROUP BY time_band_name
    ORDER BY time_band_name
    """
    
    df = client.query(query).to_dataframe()
    
    if df.empty:
        print(f"⚠️  No DUoS rates found for {dno_key} {voltage_level}, using defaults")
        return {'RED': 1.764, 'AMBER': 0.205, 'GREEN': 0.011}
    
    rates = {}
    for _, row in df.iterrows():
        band = row['time_band_name'].upper()
        rates[band] = float(row['rate_p_kwh'])
    
    return rates


def get_imbalance_prices(start_date, end_date):
    """
    Fetch system imbalance prices from BigQuery
    Uses bmrs_costs (historical) and bmrs_disbsad (settlement proxy)
    """
    client = bigquery.Client(project=PROJECT_ID, location="US")
    
    # Try bmrs_costs first (has SSP/SBP - identical since Nov 2015)
    query = f"""
    SELECT 
        CAST(settlementDate AS DATE) as date,
        settlementPeriod as period,
        ROUND(AVG(systemSellPrice), 2) as price_gbp_mwh
    FROM `{PROJECT_ID}.{DATASET}.bmrs_costs`
    WHERE CAST(settlementDate AS DATE) BETWEEN '{start_date}' AND '{end_date}'
    GROUP BY date, period
    ORDER BY date, period
    """
    
    df = client.query(query).to_dataframe()
    
    if df.empty:
        print(f"❌ No price data found for {start_date} to {end_date}")
        return None
    
    print(f"✅ Retrieved {len(df)} settlement periods")
    return df


def generate_hh_profile(start_date, end_date, dno_key='NGED-WM', voltage='HV', battery_params=None):
    """
    Generate half-hourly charge/discharge profile
    
    Args:
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
        dno_key: DNO identifier (default: NGED-WM)
        voltage: Voltage level (LV/HV, default: HV)
        battery_params: Battery configuration dict (uses DEFAULT_BATTERY if None)
    
    Returns:
        DataFrame with columns: datetime, period, band, price, duos_rate, action, power_mw, soc, revenue
    """
    
    if battery_params is None:
        battery_params = DEFAULT_BATTERY
    
    print(f"\n🔋 BESS HH Profile Generator")
    print(f"={'='*70}")
    print(f"Date Range: {start_date} to {end_date}")
    print(f"DNO: {dno_key} ({voltage})")
    print(f"Battery: {battery_params['capacity_mwh']} MWh, {battery_params['max_discharge_mw']} MW")
    print(f"Efficiency: {battery_params['efficiency']*100:.0f}%")
    print(f"{'='*70}\n")
    
    # 1. Fetch DUoS rates
    print("📊 Step 1: Fetching DUoS rates...")
    duos_rates = get_duos_rates_from_bq(dno_key, voltage)
    print(f"   Red:   {duos_rates.get('RED', 0):.4f} p/kWh")
    print(f"   Amber: {duos_rates.get('AMBER', 0):.4f} p/kWh")
    print(f"   Green: {duos_rates.get('GREEN', 0):.4f} p/kWh")
    
    # 2. Fetch imbalance prices
    print("\n💷 Step 2: Fetching imbalance prices...")
    prices_df = get_imbalance_prices(start_date, end_date)
    
    if prices_df is None:
        return None
    
    # 3. Build half-hourly profile
    print("\n⚙️  Step 3: Building HH profile...")
    
    uk_tz = pytz.timezone('Europe/London')
    results = []
    
    # Initialize battery state
    soc = 0.5  # Start at 50% SOC
    
    for _, row in prices_df.iterrows():
        date = row['date']
        period = int(row['period'])
        price_gbp_mwh = row['price_gbp_mwh']
        
        # Calculate datetime for this settlement period
        # Period 1 = 00:00-00:30, Period 2 = 00:30-01:00, etc.
        hour = (period - 1) // 2
        minute = 30 if (period % 2 == 0) else 0
        dt = uk_tz.localize(datetime.combine(date, time(hour, minute)))
        
        is_weekend = dt.weekday() >= 5
        band = get_duos_band(dt, is_weekend)
        duos_rate_p_kwh = duos_rates.get(band, 0)
        
        # Convert DUoS rate from p/kWh to £/MWh
        duos_rate_gbp_mwh = duos_rate_p_kwh * 10
        
        # Total cost = imbalance price + DUoS charge
        total_cost_charge = price_gbp_mwh + duos_rate_gbp_mwh
        total_revenue_discharge = price_gbp_mwh - duos_rate_gbp_mwh
        
        # Simple strategy: Discharge if price > threshold, charge if price < threshold
        # Threshold = average price of the day (can be improved with optimization)
        avg_price = prices_df[prices_df['date'] == date]['price_gbp_mwh'].mean()
        
        # Decision logic
        action = 'HOLD'
        power_mw = 0
        revenue = 0
        
        if price_gbp_mwh > avg_price * 1.2 and soc > battery_params['min_soc']:
            # High price - DISCHARGE
            action = 'DISCHARGE'
            power_mw = min(battery_params['max_discharge_mw'], 
                          (soc - battery_params['min_soc']) * battery_params['capacity_mwh'] * 2)
            energy_mwh = power_mw * 0.5  # Half hour
            revenue = energy_mwh * total_revenue_discharge
            soc -= energy_mwh / battery_params['capacity_mwh']
            
        elif price_gbp_mwh < avg_price * 0.8 and soc < battery_params['max_soc']:
            # Low price - CHARGE
            action = 'CHARGE'
            power_mw = min(battery_params['max_charge_mw'],
                          (battery_params['max_soc'] - soc) * battery_params['capacity_mwh'] * 2)
            energy_mwh = power_mw * 0.5  # Half hour
            revenue = -energy_mwh * total_cost_charge  # Negative = cost
            soc += (energy_mwh * battery_params['efficiency']) / battery_params['capacity_mwh']
        
        # Clamp SOC
        soc = max(battery_params['min_soc'], min(battery_params['max_soc'], soc))
        
        results.append({
            'datetime': dt,
            'date': date,
            'period': period,
            'band': band,
            'is_weekend': is_weekend,
            'price_gbp_mwh': price_gbp_mwh,
            'duos_p_kwh': duos_rate_p_kwh,
            'duos_gbp_mwh': duos_rate_gbp_mwh,
            'action': action,
            'power_mw': round(power_mw, 3),
            'energy_mwh': round(power_mw * 0.5, 3),
            'soc': round(soc, 3),
            'revenue_gbp': round(revenue, 2)
        })
    
    profile_df = pd.DataFrame(results)
    
    # Summary statistics
    print(f"\n📈 Profile Summary:")
    print(f"   Total periods: {len(profile_df)}")
    print(f"   Charge periods: {len(profile_df[profile_df['action'] == 'CHARGE'])}")
    print(f"   Discharge periods: {len(profile_df[profile_df['action'] == 'DISCHARGE'])}")
    print(f"   Total revenue: £{profile_df['revenue_gbp'].sum():,.2f}")
    print(f"   Avg SOC: {profile_df['soc'].mean():.1%}")
    
    return profile_df


def export_to_csv(profile_df, filename='bess_hh_profile.csv'):
    """Export profile to CSV"""
    profile_df.to_csv(filename, index=False)
    print(f"\n✅ Exported to {filename}")


def export_to_sheets(profile_df, sheet_name='HH Profile'):
    """Export profile to Google Sheets"""
    scope = ['https://spreadsheets.google.com/feeds',
             'https://www.googleapis.com/auth/drive']
    creds = Credentials.from_service_account_file(CREDS_PATH, scopes=scope)
    gc = gspread.authorize(creds)
    
    try:
        ss = gc.open_by_key(SHEET_ID)
        
        # Try to get or create sheet
        try:
            ws = ss.worksheet(sheet_name)
            ws.clear()
        except:
            ws = ss.add_worksheet(title=sheet_name, rows=1000, cols=20)
        
        # Format datetime as string for sheets
        export_df = profile_df.copy()
        export_df['datetime'] = export_df['datetime'].dt.strftime('%Y-%m-%d %H:%M')
        export_df['date'] = export_df['date'].astype(str)
        
        # Write headers
        headers = list(export_df.columns)
        ws.update('A1', [headers])
        
        # Write data
        data = export_df.values.tolist()
        if len(data) > 0:
            ws.update(f'A2:M{len(data)+1}', data)
        
        print(f"\n✅ Exported to Google Sheets: {sheet_name}")
        print(f"   Spreadsheet: {SHEET_ID}")
        print(f"   Rows: {len(data)}")
        
    except Exception as e:
        print(f"\n❌ Error exporting to sheets: {e}")


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate BESS HH charge/discharge profile')
    parser.add_argument('--start-date', required=True, help='Start date (YYYY-MM-DD)')
    parser.add_argument('--end-date', required=True, help='End date (YYYY-MM-DD)')
    parser.add_argument('--dno', default='NGED-WM', help='DNO key (default: NGED-WM)')
    parser.add_argument('--voltage', default='HV', help='Voltage level (default: HV)')
    parser.add_argument('--capacity', type=float, default=2.0, help='Battery capacity MWh (default: 2.0)')
    parser.add_argument('--power', type=float, default=1.0, help='Max power MW (default: 1.0)')
    parser.add_argument('--efficiency', type=float, default=0.90, help='Round-trip efficiency (default: 0.90)')
    parser.add_argument('--output', choices=['csv', 'sheets', 'both'], default='both', 
                       help='Output format (default: both)')
    parser.add_argument('--csv-file', default='bess_hh_profile.csv', help='CSV filename')
    
    args = parser.parse_args()
    
    # Build battery parameters
    battery_params = {
        'capacity_mwh': args.capacity,
        'max_charge_mw': args.power,
        'max_discharge_mw': args.power,
        'efficiency': args.efficiency,
        'min_soc': 0.10,
        'max_soc': 0.95
    }
    
    # Generate profile
    profile_df = generate_hh_profile(
        args.start_date,
        args.end_date,
        dno_key=args.dno,
        voltage=args.voltage,
        battery_params=battery_params
    )
    
    if profile_df is None:
        print("❌ Profile generation failed")
        sys.exit(1)
    
    # Export
    if args.output in ['csv', 'both']:
        export_to_csv(profile_df, args.csv_file)
    
    if args.output in ['sheets', 'both']:
        export_to_sheets(profile_df)
    
    print("\n✅ BESS HH Profile generation complete!")


if __name__ == '__main__':
    main()

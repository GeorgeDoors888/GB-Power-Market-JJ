#!/usr/bin/env python3
"""
Settlement Period Market Narrative Generator
Creates SP-by-SP market story with demand, balancing, and battery behavior

Date: December 12, 2025
Author: GB Power Market JJ
"""

import requests
from datetime import datetime, timedelta
from google.cloud import bigquery
import pandas as pd
import time

# Configuration
PROJECT_ID = "inner-cinema-476211-u9"
DATASET = "uk_energy_prod"

def get_demand_data(date_str):
    """Get actual vs forecast demand from BigQuery"""
    client = bigquery.Client(project=PROJECT_ID, location="US")
    
    query = f"""
    SELECT 
        settlementPeriod as sp,
        settlementDate as date,
        quantity as actual_gw
    FROM `{PROJECT_ID}.{DATASET}.bmrs_fuelinst_iris`
    WHERE settlementDate = '{date_str}'
        AND fuelType = 'TOTAL'
    ORDER BY settlementPeriod
    """
    
    try:
        df = client.query(query).to_dataframe()
        return df
    except Exception as e:
        print(f"Warning: Could not fetch demand data: {e}")
        return pd.DataFrame()


def get_battery_bm_data(date_str, batteries):
    """Get detailed BM data for all batteries across all SPs"""
    
    all_sp_data = []
    
    for sp in range(1, 49):
        sp_total_offer_vol = 0
        sp_total_offer_cash = 0
        sp_total_bid_vol = 0
        sp_total_bid_cash = 0
        sp_battery_data = []
        
        for bmu_id, name in batteries:
            bmu_offer_vol = 0
            bmu_offer_cash = 0
            bmu_bid_vol = 0
            bmu_bid_cash = 0
            
            try:
                # BID data
                url_bid = f"https://data.elexon.co.uk/bmrs/api/v1/balancing/settlement/indicative/cashflows/all/bid/{date_str}/{sp}?bmUnit={bmu_id}"
                r_bid = requests.get(url_bid, timeout=5)
                
                url_bid_vol = f"https://data.elexon.co.uk/bmrs/api/v1/balancing/settlement/acceptance/volumes/all/bid/{date_str}/{sp}?bmUnit={bmu_id}"
                r_bid_vol = requests.get(url_bid_vol, timeout=5)
                
                if r_bid.status_code == 200:
                    data = r_bid.json()
                    if 'data' in data and len(data['data']) > 0:
                        cf = data['data'][0].get('bidOfferPairCashflows', {})
                        for key, val in cf.items():
                            if val is not None and key != 'totalCashflow':
                                bmu_bid_cash += abs(val)
                
                if r_bid_vol.status_code == 200:
                    data = r_bid_vol.json()
                    if 'data' in data and len(data['data']) > 0:
                        pv = data['data'][0].get('pairVolumes', {})
                        for key, val in pv.items():
                            if val is not None and key != 'totalVolume':
                                bmu_bid_vol += abs(val)
                
                # OFFER data
                url_offer = f"https://data.elexon.co.uk/bmrs/api/v1/balancing/settlement/indicative/cashflows/all/offer/{date_str}/{sp}?bmUnit={bmu_id}"
                r_offer = requests.get(url_offer, timeout=5)
                
                url_offer_vol = f"https://data.elexon.co.uk/bmrs/api/v1/balancing/settlement/acceptance/volumes/all/offer/{date_str}/{sp}?bmUnit={bmu_id}"
                r_offer_vol = requests.get(url_offer_vol, timeout=5)
                
                if r_offer.status_code == 200:
                    data = r_offer.json()
                    if 'data' in data and len(data['data']) > 0:
                        cf = data['data'][0].get('bidOfferPairCashflows', {})
                        for key, val in cf.items():
                            if val is not None and key != 'totalCashflow':
                                bmu_offer_cash += abs(val)
                
                if r_offer_vol.status_code == 200:
                    data = r_offer.json()
                    if 'data' in data and len(data['data']) > 0:
                        pv = data['data'][0].get('pairVolumes', {})
                        for key, val in pv.items():
                            if val is not None and key != 'totalVolume':
                                bmu_offer_vol += abs(val)
                
                time.sleep(0.05)
                
            except:
                continue
            
            sp_total_offer_vol += bmu_offer_vol
            sp_total_offer_cash += bmu_offer_cash
            sp_total_bid_vol += bmu_bid_vol
            sp_total_bid_cash += bmu_bid_cash
            
            total_cash = bmu_offer_cash + bmu_bid_cash
            total_vol = bmu_offer_vol + bmu_bid_vol
            
            if total_cash > 0:
                sp_battery_data.append({
                    'bmu_id': bmu_id,
                    'name': name,
                    'total_cash': total_cash,
                    'total_vol': total_vol,
                    'offer_cash': bmu_offer_cash,
                    'bid_cash': bmu_bid_cash,
                    'offer_vol': bmu_offer_vol,
                    'bid_vol': bmu_bid_vol
                })
        
        # Find top BMU for this SP
        top_bmu = None
        top_bmu_share = 0
        if sp_battery_data:
            sp_battery_data.sort(key=lambda x: x['total_cash'], reverse=True)
            top_bmu = sp_battery_data[0]
            sp_total_cash = sp_total_offer_cash + sp_total_bid_cash
            top_bmu_share = (top_bmu['total_cash'] / sp_total_cash * 100) if sp_total_cash > 0 else 0
        
        # Calculate weighted average prices
        offer_ewap = (sp_total_offer_cash / sp_total_offer_vol) if sp_total_offer_vol > 0 else 0
        bid_ewap = (sp_total_bid_cash / sp_total_bid_vol) if sp_total_bid_vol > 0 else 0
        
        all_sp_data.append({
            'sp': sp,
            'offer_mwh': sp_total_offer_vol,
            'bid_mwh': sp_total_bid_vol,
            'net_mwh': sp_total_offer_vol - sp_total_bid_vol,
            'offer_ewap': offer_ewap,
            'bid_ewap': bid_ewap,
            'offer_cash': sp_total_offer_cash,
            'bid_cash': sp_total_bid_cash,
            'net_cash': sp_total_offer_cash - sp_total_bid_cash,
            'top_bmu': top_bmu,
            'top_bmu_share': top_bmu_share
        })
        
        if sp % 10 == 0:
            print(f"  Processed SP {sp}/48...")
    
    return all_sp_data


def classify_market_state(actual_gw, forecast_gw, net_mwh):
    """Classify market tightness and BM intensity"""
    
    # Tightness classification
    if forecast_gw and forecast_gw > 0:
        delta_gw = actual_gw - forecast_gw
        if delta_gw > 0.5:
            tightness = "Tight"
            shortage = "Short power"
        elif delta_gw < -0.5:
            tightness = "Long"
            shortage = "Surplus power"
        else:
            tightness = "Balanced"
            shortage = "Matched"
    else:
        # No forecast - infer from BM actions
        if net_mwh > 50:
            tightness = "Tight"
            shortage = "Short power"
        elif net_mwh < -50:
            tightness = "Long"
            shortage = "Surplus power"
        else:
            tightness = "Balanced"
            shortage = "Matched"
    
    return tightness, shortage


def classify_bm_intensity(total_vol, percentiles):
    """Classify BM activity level"""
    if total_vol < percentiles[33]:
        return "Low"
    elif total_vol < percentiles[66]:
        return "Med"
    else:
        return "High"


def generate_headline(tightness, shortage, bm_intensity, net_mwh, top_bmu):
    """Generate one-sentence market headline"""
    
    if tightness == "Tight" and net_mwh > 50:
        if bm_intensity == "High":
            return "NESO buying power: high discharge utilization"
        else:
            return "System short: moderate discharge activity"
    
    elif tightness == "Long" and net_mwh < -50:
        if bm_intensity == "High":
            return "NESO absorbing surplus: charging/demand increase dominant"
        else:
            return "System long: moderate charge activity"
    
    elif bm_intensity == "Low":
        return "Quiet SP: minimal balancing actions"
    
    elif top_bmu and top_bmu['total_cash'] > 1000:
        action = "discharge" if top_bmu['offer_cash'] > top_bmu['bid_cash'] else "charge"
        return f"{top_bmu['name']} {action} dominant: £{top_bmu['total_cash']:,.0f}"
    
    else:
        return "Standard balancing: mixed actions"


def generate_narrative(date_str, batteries):
    """Generate full SP-by-SP market narrative"""
    
    print(f"Generating market narrative for {date_str}...")
    print("=" * 120)
    
    # Get demand data
    print("\nFetching demand data from BigQuery...")
    demand_df = get_demand_data(date_str)
    
    # Get battery BM data
    print("\nFetching battery BM data from BOAV + EBOCF endpoints...")
    sp_data = get_battery_bm_data(date_str, batteries)
    
    # Calculate percentiles for BM intensity classification
    total_vols = [abs(sp['net_mwh']) for sp in sp_data]
    percentiles = {
        33: pd.Series(total_vols).quantile(0.33),
        66: pd.Series(total_vols).quantile(0.66)
    }
    
    print("\n" + "=" * 120)
    print("SETTLEMENT PERIOD MARKET NARRATIVE")
    print(f"Date: {date_str}")
    print("=" * 120)
    
    # Generate narrative for each SP
    narratives = []
    
    for sp in range(1, 49):
        sp_info = sp_data[sp - 1]
        
        # Get demand info
        actual_gw = 0
        forecast_gw = 0
        if not demand_df.empty and sp in demand_df['sp'].values:
            actual_gw = demand_df[demand_df['sp'] == sp]['actual_gw'].values[0]
        
        # Calculate time window
        hour = (sp - 1) // 2
        minute = 0 if (sp % 2 == 1) else 30
        time_start = f"{hour:02d}:{minute:02d}"
        time_end = f"{hour:02d}:{minute+30:02d}" if minute == 0 else f"{(hour+1):02d}:00"
        
        # Classify market state
        tightness, shortage = classify_market_state(actual_gw, forecast_gw, sp_info['net_mwh'])
        total_vol = abs(sp_info['offer_mwh']) + abs(sp_info['bid_mwh'])
        bm_intensity = classify_bm_intensity(total_vol, percentiles)
        
        # Generate headline
        headline = generate_headline(tightness, shortage, bm_intensity, sp_info['net_mwh'], sp_info['top_bmu'])
        
        # Build narrative
        narrative = {
            'sp': sp,
            'time': f"{time_start}-{time_end}",
            'actual_gw': actual_gw,
            'forecast_gw': forecast_gw,
            'delta_gw': actual_gw - forecast_gw if forecast_gw > 0 else 0,
            'tightness': tightness,
            'shortage': shortage,
            'bm_intensity': bm_intensity,
            'offer_mwh': sp_info['offer_mwh'],
            'bid_mwh': sp_info['bid_mwh'],
            'net_mwh': sp_info['net_mwh'],
            'offer_ewap': sp_info['offer_ewap'],
            'bid_ewap': sp_info['bid_ewap'],
            'net_cash': sp_info['net_cash'],
            'top_bmu_name': sp_info['top_bmu']['name'] if sp_info['top_bmu'] else '-',
            'top_bmu_cash': sp_info['top_bmu']['total_cash'] if sp_info['top_bmu'] else 0,
            'top_bmu_share': sp_info['top_bmu_share'],
            'headline': headline
        }
        
        narratives.append(narrative)
        
        # Print sample (every 6 SPs = every 3 hours)
        if sp % 6 == 1:
            print(f"\n{'─' * 120}")
            print(f"SP{sp:2d} ({narrative['time']}) — {tightness} | {shortage} | BM intensity: {bm_intensity}")
            print(f"{'─' * 120}")
            print(f"  • Demand: {actual_gw:.2f} GW actual" + (f", {forecast_gw:.2f} GW forecast, Δ{narrative['delta_gw']:+.2f} GW" if forecast_gw > 0 else " (no forecast)"))
            print(f"  • Balancing: {sp_info['offer_mwh']:.1f} MWh discharged (£{sp_info['offer_ewap']:.0f}/MWh), {sp_info['bid_mwh']:.1f} MWh charged (£{sp_info['bid_ewap']:.0f}/MWh)")
            print(f"  • Battery: {narrative['top_bmu_name']} leading with £{narrative['top_bmu_cash']:,.0f} ({narrative['top_bmu_share']:.0f}% of SP revenue)")
            print(f"  • Headline: {headline}")
    
    print("\n" + "=" * 120)
    print(f"Generated {len(narratives)} settlement period narratives")
    
    return narratives


def export_to_dataframe(narratives):
    """Convert narratives to DataFrame for export"""
    return pd.DataFrame(narratives)


def main():
    """Main execution"""
    batteries = [
        ('T_LKSDB-1', 'Lakeside'),
        ('E_CONTB-1', 'Tesla'),
        ('T_WHLWB-1', 'Whitelee'),
        ('T_CAMLB-1', 'Camlan'),
        ('E_CLEBL-1', 'Cleator'),
        ('T_DRAXX-2', 'Drax'),
        ('E_CELRB-1', 'Cellarhead'),
        ('T_GRIFW-1', 'Grindon'),
        ('E_LNCSB-1', 'Landes'),
        ('T_NEDHB-1', 'Nedham')
    ]
    
    date = (datetime.now() - timedelta(days=2)).strftime('%Y-%m-%d')
    
    narratives = generate_narrative(date, batteries)
    
    # Export to CSV
    df = export_to_dataframe(narratives)
    filename = f"sp_market_narrative_{date}.csv"
    df.to_csv(filename, index=False)
    
    print(f"\n✅ Exported to {filename}")
    print(f"\nColumn structure:")
    for col in df.columns:
        print(f"  - {col}")


if __name__ == '__main__':
    main()

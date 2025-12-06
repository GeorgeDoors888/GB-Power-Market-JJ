"""
Validate BESS Revenue Model Assumptions
Checks current market rates vs model assumptions for DC, CM, BM, and PPA
"""

from google.cloud import bigquery
import pandas as pd
from datetime import datetime, timedelta
import os

PROJECT_ID = "inner-cinema-476211-u9"
DATASET = "uk_energy_prod"

# Current model assumptions (to be validated)
MODEL_ASSUMPTIONS = {
    'dc_rate': 8.50,      # £/MW/h - Dynamic Containment
    'cm_rate': 5.14,      # £/MW/h - Capacity Market (£45/kW/year)
    'bm_rate': 25.00,     # £/MWh - Balancing Mechanism avg
    'bm_hours_per_day': 2.0,  # Utilization assumption
    'ppa_profit': 23.00,  # £/MWh - Profitable arbitrage spread
    'ppa_profitable_pct': 18.8,  # % of time profitable
}

def check_bm_actual_utilization():
    """Check actual BM dispatch hours from BOALF data"""
    print("\n📊 VALIDATING BM UTILIZATION...")
    
    client = bigquery.Client(project=PROJECT_ID, location="US")
    
    # Query last 90 days of accepted BM actions
    query = f"""
    WITH daily_actions AS (
        SELECT 
            DATE(acceptanceTime) as date,
            bmUnit,
            COUNT(*) as acceptances_per_day
        FROM `{PROJECT_ID}.{DATASET}.bmrs_boalf`
        WHERE acceptanceTime >= DATE_SUB(CURRENT_DATE(), INTERVAL 90 DAY)
            AND acceptanceTime < CURRENT_DATE()
        GROUP BY date, bmUnit
    )
    SELECT 
        AVG(acceptances_per_day) as avg_acceptances_per_unit_per_day,
        COUNT(DISTINCT date) as days_analyzed,
        COUNT(DISTINCT bmUnit) as unique_units
    FROM daily_actions
    """
    
    try:
        df = client.query(query).to_dataframe()
        if len(df) > 0:
            avg_acceptances = df['avg_acceptances_per_unit_per_day'].iloc[0]
            days = df['days_analyzed'].iloc[0]
            units = df['unique_units'].iloc[0]
            
            # Each acceptance is ~30 min, so acceptances * 0.5 = hours
            avg_hours_per_day = avg_acceptances * 0.5
            
            print(f"   ✅ Analyzed {days} days, {units} unique units")
            print(f"   Avg acceptances per unit per day: {avg_acceptances:.2f}")
            print(f"   Estimated BM hours per day: {avg_hours_per_day:.2f} hours")
            print(f"   Model assumption: {MODEL_ASSUMPTIONS['bm_hours_per_day']:.2f} hours")
            
            variance = abs(avg_hours_per_day - MODEL_ASSUMPTIONS['bm_hours_per_day'])
            if variance < 0.5:
                print(f"   ✅ VALID - Within 0.5 hours")
            else:
                print(f"   ⚠️  VARIANCE - Difference: {variance:.2f} hours")
            
            return avg_hours_per_day
        else:
            print("   ⚠️  No BOALF data available")
            return None
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return None

def check_bm_avg_prices():
    """Check actual BM bid-offer prices from BOD table"""
    print("\n📊 VALIDATING BM PRICES...")
    
    client = bigquery.Client(project=PROJECT_ID, location="US")
    
    # Query last 90 days of bid-offer prices (BOD table, not BOALF which has no prices)
    query = f"""
    SELECT 
        AVG(ABS(offer)) as avg_offer_price,
        AVG(ABS(bid)) as avg_bid_price,
        COUNT(*) as total_pairs
    FROM `{PROJECT_ID}.{DATASET}.bmrs_bod`
    WHERE settlementDate >= DATE_SUB(CURRENT_DATE(), INTERVAL 90 DAY)
        AND settlementDate < CURRENT_DATE()
        AND (offer IS NOT NULL OR bid IS NOT NULL)
        AND offer > 0  -- Filter out zero prices
    """
    
    try:
        df = client.query(query).to_dataframe()
        if len(df) > 0 and df['total_pairs'].iloc[0] > 0:
            avg_offer = df['avg_offer_price'].iloc[0]
            avg_bid = df['avg_bid_price'].iloc[0]
            total = df['total_pairs'].iloc[0]
            
            # Weighted average of offer and bid prices
            avg_bm_price = (avg_offer + avg_bid) / 2 if avg_offer and avg_bid else (avg_offer or avg_bid or 0)
            
            print(f"   ✅ Analyzed {total:,} bid-offer pairs (90 days)")
            print(f"   Avg offer price: £{avg_offer:.2f}/MWh" if avg_offer else "   No offer data")
            print(f"   Avg bid price: £{avg_bid:.2f}/MWh" if avg_bid else "   No bid data")
            print(f"   Model assumption: £{MODEL_ASSUMPTIONS['bm_rate']:.2f}/MWh")
            
            if avg_bm_price > 0:
                variance_pct = abs(avg_bm_price - MODEL_ASSUMPTIONS['bm_rate']) / MODEL_ASSUMPTIONS['bm_rate'] * 100
                if variance_pct < 20:
                    print(f"   ✅ VALID - Within 20%")
                else:
                    print(f"   ⚠️  VARIANCE - {variance_pct:.1f}% difference")
            
            return avg_bm_price
        else:
            print("   ⚠️  No BM bid-offer price data available")
            return None
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return None

def check_imbalance_prices():
    """Check actual imbalance prices (SSP/SBP) for arbitrage profitability"""
    print("\n📊 VALIDATING ARBITRAGE PRICES...")
    
    client = bigquery.Client(project=PROJECT_ID, location="US")
    
    # Query last 90 days of imbalance prices
    query = f"""
    WITH prices AS (
        SELECT 
            settlementDate,
            settlementPeriod,
            systemSellPrice as ssp,
            systemBuyPrice as sbp
        FROM `{PROJECT_ID}.{DATASET}.bmrs_costs`
        WHERE settlementDate >= DATE_SUB(CURRENT_DATE(), INTERVAL 90 DAY)
            AND settlementDate < CURRENT_DATE()
    )
    SELECT 
        AVG(ssp) as avg_price,
        STDDEV(ssp) as price_volatility,
        COUNT(*) as total_periods,
        SUM(CASE WHEN ssp > 100 THEN 1 ELSE 0 END) as high_price_periods,
        SUM(CASE WHEN ssp < 50 THEN 1 ELSE 0 END) as low_price_periods
    FROM prices
    WHERE ssp IS NOT NULL
    """
    
    try:
        df = client.query(query).to_dataframe()
        if len(df) > 0:
            avg_price = df['avg_price'].iloc[0]
            volatility = df['price_volatility'].iloc[0]
            total = df['total_periods'].iloc[0]
            high_periods = df['high_price_periods'].iloc[0]
            low_periods = df['low_price_periods'].iloc[0]
            
            profitable_pct = (high_periods + low_periods) / total * 100 if total > 0 else 0
            
            print(f"   ✅ Analyzed {total:,} settlement periods (90 days)")
            print(f"   Avg price: £{avg_price:.2f}/MWh")
            print(f"   Price volatility (stddev): £{volatility:.2f}/MWh")
            print(f"   High price periods (>£100): {high_periods:,} ({high_periods/total*100:.1f}%)")
            print(f"   Low price periods (<£50): {low_periods:,} ({low_periods/total*100:.1f}%)")
            print(f"   Potential arbitrage periods: {profitable_pct:.1f}%")
            print(f"   Model assumption: {MODEL_ASSUMPTIONS['ppa_profitable_pct']:.1f}% profitable")
            
            variance = abs(profitable_pct - MODEL_ASSUMPTIONS['ppa_profitable_pct'])
            if variance < 5:
                print(f"   ✅ VALID - Within 5%")
            else:
                print(f"   ⚠️  VARIANCE - {variance:.1f}% difference")
            
            return {'avg_price': avg_price, 'volatility': volatility, 'profitable_pct': profitable_pct}
        else:
            print("   ⚠️  No imbalance price data available")
            return None
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return None

def check_eso_rates():
    """Check ESO published rates for DC/DR/DM (manual lookup required)"""
    print("\n📊 ESO ANCILLARY SERVICE RATES (Manual Validation Required)")
    print("   Current model assumptions:")
    print(f"      DC Rate: £{MODEL_ASSUMPTIONS['dc_rate']:.2f}/MW/h")
    print(f"      CM Rate: £{MODEL_ASSUMPTIONS['cm_rate']:.2f}/MW/h (£45/kW/year)")
    print("\n   ⚠️  MANUAL ACTION REQUIRED:")
    print("      1. Check ESO website: https://www.nationalgrideso.com/industry-information/balancing-services")
    print("      2. Verify Dynamic Containment clearing prices")
    print("      3. Check latest Capacity Market auction results: https://www.emrdeliverybody.com/CM/Auctions-Results.aspx")
    print("      4. Update MODEL_ASSUMPTIONS in bess_revenue_stack_analyzer.py if rates changed >10%")

def generate_validation_report():
    """Generate comprehensive validation report"""
    print("\n" + "="*70)
    print("🔍 BESS REVENUE MODEL VALIDATION REPORT")
    print("="*70)
    print(f"Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Validation Period: Last 90 days")
    
    # Check each component
    bm_hours = check_bm_actual_utilization()
    bm_price = check_bm_avg_prices()
    arbitrage = check_imbalance_prices()
    check_eso_rates()
    
    # Summary
    print("\n" + "="*70)
    print("📋 VALIDATION SUMMARY")
    print("="*70)
    
    validation_results = []
    
    if bm_hours is not None:
        bm_hours_valid = abs(bm_hours - MODEL_ASSUMPTIONS['bm_hours_per_day']) < 0.5
        validation_results.append(('BM Utilization', bm_hours_valid, f"{bm_hours:.2f}h actual vs {MODEL_ASSUMPTIONS['bm_hours_per_day']:.2f}h model"))
    
    if bm_price is not None and bm_price > 0:
        bm_price_valid = abs(bm_price - MODEL_ASSUMPTIONS['bm_rate']) / MODEL_ASSUMPTIONS['bm_rate'] < 0.20
        validation_results.append(('BM Price', bm_price_valid, f"£{bm_price:.2f}/MWh actual vs £{MODEL_ASSUMPTIONS['bm_rate']:.2f}/MWh model"))
    
    if arbitrage is not None:
        arb_valid = abs(arbitrage['profitable_pct'] - MODEL_ASSUMPTIONS['ppa_profitable_pct']) < 5
        validation_results.append(('Arbitrage Opportunities', arb_valid, f"{arbitrage['profitable_pct']:.1f}% actual vs {MODEL_ASSUMPTIONS['ppa_profitable_pct']:.1f}% model"))
    
    for name, valid, details in validation_results:
        status = "✅ VALID" if valid else "⚠️  NEEDS REVIEW"
        print(f"   {status}: {name}")
        print(f"      {details}")
    
    # Overall assessment
    valid_count = sum(1 for _, valid, _ in validation_results if valid)
    total_count = len(validation_results)
    
    print(f"\n   Overall: {valid_count}/{total_count} assumptions validated")
    
    if valid_count == total_count:
        print("   ✅ MODEL IS VALID - All assumptions within acceptable ranges")
    elif valid_count >= total_count * 0.7:
        print("   ⚠️  MODEL MOSTLY VALID - Some assumptions need review")
    else:
        print("   ❌ MODEL NEEDS UPDATE - Multiple assumptions out of range")
    
    print("\n   💡 RECOMMENDATION:")
    if valid_count == total_count:
        print("      Continue using current model. Re-validate in 30 days.")
    else:
        print("      Update bess_revenue_stack_analyzer.py with validated rates.")
        print("      Re-run revenue analysis with new assumptions.")
    
    print("="*70)

if __name__ == "__main__":
    # Set credentials
    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = '/home/george/inner-cinema-credentials.json'
    
    generate_validation_report()

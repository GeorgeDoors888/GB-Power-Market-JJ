"""
Contract Selection Optimizer
Evaluates DC vs DR vs DM combinations to maximize revenue
"""

import pandas as pd

# Battery specs
BATTERY_POWER_MW = 2.5
BATTERY_CAPACITY_MWH = 5.0

# Contract rates (£/MW/h for availability)
CONTRACTS = {
    'DC': {'rate': 8.50, 'name': 'Dynamic Containment', 'response': '1s', 'constraint': 'Fastest response'},
    'DR': {'rate': 6.00, 'name': 'Dynamic Regulation', 'response': '1s', 'constraint': 'Similar to DC'},
    'DM': {'rate': 4.50, 'name': 'Dynamic Moderation', 'response': '5s', 'constraint': 'Slower response'},
    'CM': {'rate': 5.14, 'name': 'Capacity Market', 'response': 'N/A', 'constraint': 'Winter availability'},
}

# Utilization revenues (can stack with any FR contract)
BM_REVENUE_ANNUAL = 91_250  # From revenue model
PPA_REVENUE_ANNUAL = 7_891
GREEN_SAVING_ANNUAL = 104_591

def calculate_contract_revenue(fr_contract):
    """Calculate total revenue for a given FR contract"""
    # FR availability revenue (8,760 hours per year)
    fr_revenue = CONTRACTS[fr_contract]['rate'] * BATTERY_POWER_MW * 8760
    
    # CM availability revenue (stackable)
    cm_revenue = CONTRACTS['CM']['rate'] * BATTERY_POWER_MW * 8760
    
    # Utilization revenues (same regardless of FR contract)
    bm_revenue = BM_REVENUE_ANNUAL
    ppa_revenue = PPA_REVENUE_ANNUAL
    green_saving = GREEN_SAVING_ANNUAL
    
    total = fr_revenue + cm_revenue + bm_revenue + ppa_revenue + green_saving
    
    return {
        'fr_contract': fr_contract,
        'fr_revenue': fr_revenue,
        'cm_revenue': cm_revenue,
        'bm_revenue': bm_revenue,
        'ppa_revenue': ppa_revenue,
        'green_saving': green_saving,
        'total_revenue': total
    }

def evaluate_all_contract_combinations():
    """Evaluate all FR contract options"""
    print("="*70)
    print("🔧 CONTRACT SELECTION OPTIMIZER")
    print("="*70)
    print(f"Battery: {BATTERY_POWER_MW} MW / {BATTERY_CAPACITY_MWH} MWh\n")
    
    print("📊 AVAILABLE CONTRACTS:")
    for contract, details in CONTRACTS.items():
        if contract != 'CM':  # CM is always stackable
            print(f"   {contract}: £{details['rate']}/MW/h - {details['name']} ({details['response']} response)")
    
    print(f"\n   CM (stackable with any FR): £{CONTRACTS['CM']['rate']}/MW/h - {CONTRACTS['CM']['name']}")
    
    print(f"\n💰 UTILIZATION REVENUES (same for all contracts):")
    print(f"   BM Dispatch: £{BM_REVENUE_ANNUAL:,.0f}/year")
    print(f"   PPA Arbitrage: £{PPA_REVENUE_ANNUAL:,.0f}/year")
    print(f"   GREEN DUoS Savings: £{GREEN_SAVING_ANNUAL:,.0f}/year")
    
    # Evaluate each FR option
    results = []
    for fr_contract in ['DC', 'DR', 'DM']:
        result = calculate_contract_revenue(fr_contract)
        results.append(result)
    
    df = pd.DataFrame(results)
    df = df.sort_values('total_revenue', ascending=False)
    
    print(f"\n" + "="*70)
    print("📈 CONTRACT COMPARISON")
    print("="*70)
    
    for idx, row in df.iterrows():
        print(f"\n{row['fr_contract']} + CM STACK:")
        print(f"   {row['fr_contract']} Availability: £{row['fr_revenue']:,.0f}/year")
        print(f"   CM Availability: £{row['cm_revenue']:,.0f}/year")
        print(f"   BM Dispatch: £{row['bm_revenue']:,.0f}/year")
        print(f"   PPA Arbitrage: £{row['ppa_revenue']:,.0f}/year")
        print(f"   GREEN Savings: £{row['green_saving']:,.0f}/year")
        print(f"   " + "-"*50)
        print(f"   TOTAL: £{row['total_revenue']:,.0f}/year")
    
    # Recommendation
    best_contract = df.iloc[0]['fr_contract']
    best_revenue = df.iloc[0]['total_revenue']
    worst_contract = df.iloc[-1]['fr_contract']
    worst_revenue = df.iloc[-1]['total_revenue']
    difference = best_revenue - worst_revenue
    
    print(f"\n" + "="*70)
    print("💡 RECOMMENDATION")
    print("="*70)
    print(f"✅ OPTIMAL CONTRACT: {best_contract} + CM")
    print(f"   Total Revenue: £{best_revenue:,.0f}/year")
    print(f"   Advantage over {worst_contract}: £{difference:,.0f}/year ({difference/worst_revenue*100:.1f}% higher)")
    
    print(f"\n   Why {best_contract}?")
    if best_contract == 'DC':
        print(f"      - Highest availability rate (£{CONTRACTS['DC']['rate']}/MW/h)")
        print(f"      - Fast response (1s) enables premium pricing")
        print(f"      - Market demand high for frequency containment")
    
    print(f"\n   Contract Strategy:")
    print(f"      1. Secure {best_contract} contract with ESO (8,760 hours/year)")
    print(f"      2. Stack CM contract (winter capacity)")
    print(f"      3. Optimize BM dispatch for high-price periods")
    print(f"      4. Charge during GREEN periods for DUoS savings")
    print(f"      5. Arbitrage when profitable (18.8% of time)")
    
    # Financial metrics
    opex = best_revenue * 0.05
    net_revenue = best_revenue - opex
    capex = 1_000_000  # £1M
    payback = capex / net_revenue
    
    print(f"\n   Financial Impact:")
    print(f"      Gross Revenue: £{best_revenue:,.0f}/year")
    print(f"      OPEX (5%): £{opex:,.0f}/year")
    print(f"      Net Revenue: £{net_revenue:,.0f}/year")
    print(f"      Simple Payback: {payback:.2f} years")
    
    # Save results
    df.to_csv('contract_comparison.csv', index=False)
    print(f"\n✅ Contract comparison saved: contract_comparison.csv")
    
    print("="*70)

if __name__ == "__main__":
    evaluate_all_contract_combinations()

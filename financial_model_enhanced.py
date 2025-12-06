"""
Enhanced Financial Model with Debt, Tax, and Depreciation
Calculates levered IRR and after-tax cashflows
"""

import pandas as pd
import numpy as np

# Project parameters
CAPEX = 1_000_000  # £1M for 2.5 MW battery
ANNUAL_REVENUE_GROSS = 502_448  # From revenue stack model
OPEX_PCT = 0.05  # 5% of revenue
LIFETIME_YEARS = 15

# Debt parameters
DEBT_RATIO = 0.60  # 60% debt, 40% equity
INTEREST_RATE = 0.05  # 5% interest on debt
LOAN_TERM_YEARS = 10

# Tax parameters
CORP_TAX_RATE = 0.25  # 25% UK corporation tax
CAPITAL_ALLOWANCES_RATE = 0.18  # 18% reducing balance

def calculate_debt_schedule():
    """Calculate debt amortization schedule"""
    print("\n💰 DEBT FINANCING SCHEDULE")
    print("="*70)
    
    debt_amount = CAPEX * DEBT_RATIO
    equity_amount = CAPEX * (1 - DEBT_RATIO)
    
    print(f"Total CAPEX: £{CAPEX:,.0f}")
    print(f"Debt (60%): £{debt_amount:,.0f} @ {INTEREST_RATE*100:.1f}% interest")
    print(f"Equity (40%): £{equity_amount:,.0f}")
    
    # Annual payment (principal + interest)
    if INTEREST_RATE > 0:
        annual_payment = debt_amount * (INTEREST_RATE * (1 + INTEREST_RATE)**LOAN_TERM_YEARS) / ((1 + INTEREST_RATE)**LOAN_TERM_YEARS - 1)
    else:
        annual_payment = debt_amount / LOAN_TERM_YEARS
    
    print(f"\nAnnual debt service: £{annual_payment:,.0f}/year for {LOAN_TERM_YEARS} years")
    
    # Build amortization schedule
    schedule = []
    balance = debt_amount
    
    for year in range(1, LOAN_TERM_YEARS + 1):
        interest = balance * INTEREST_RATE
        principal = annual_payment - interest
        balance -= principal
        
        schedule.append({
            'year': year,
            'payment': annual_payment,
            'interest': interest,
            'principal': principal,
            'balance': max(0, balance)
        })
    
    df = pd.DataFrame(schedule)
    print(f"\nDebt Schedule (First 5 years):")
    print(df.head().to_string(index=False))
    
    return df, equity_amount

def calculate_capital_allowances():
    """Calculate capital allowances (depreciation for tax purposes)"""
    print("\n📉 CAPITAL ALLOWANCES (18% Reducing Balance)")
    print("="*70)
    
    allowances = []
    wdv = CAPEX  # Written down value
    
    for year in range(1, LIFETIME_YEARS + 1):
        allowance = wdv * CAPITAL_ALLOWANCES_RATE
        wdv -= allowance
        
        allowances.append({
            'year': year,
            'allowance': allowance,
            'wdv': wdv
        })
    
    df = pd.DataFrame(allowances)
    print(f"\nCapital Allowances (First 5 years):")
    print(df.head().to_string(index=False))
    
    return df

def calculate_levered_cashflows(debt_schedule, cap_allowances):
    """Calculate after-tax equity cashflows with debt"""
    print("\n💵 LEVERED EQUITY CASHFLOWS (After-Tax)")
    print("="*70)
    
    cashflows = []
    
    # Year 0: Equity investment
    equity_investment = CAPEX * (1 - DEBT_RATIO)
    cashflows.append({
        'year': 0,
        'revenue': 0,
        'opex': 0,
        'ebitda': 0,
        'interest': 0,
        'depreciation': 0,
        'taxable_income': 0,
        'tax': 0,
        'debt_principal': 0,
        'equity_cashflow': -equity_investment
    })
    
    # Operating years
    for year in range(1, LIFETIME_YEARS + 1):
        # Revenue (with 2.5% annual degradation)
        degradation_factor = (1 - 0.025) ** (year - 1)
        revenue = ANNUAL_REVENUE_GROSS * degradation_factor
        
        # OPEX
        opex = revenue * OPEX_PCT
        
        # EBITDA
        ebitda = revenue - opex
        
        # Interest expense (if debt still outstanding)
        if year <= LOAN_TERM_YEARS:
            interest = debt_schedule[debt_schedule['year'] == year]['interest'].iloc[0]
            debt_principal = debt_schedule[debt_schedule['year'] == year]['principal'].iloc[0]
        else:
            interest = 0
            debt_principal = 0
        
        # Capital allowances (depreciation)
        depreciation = cap_allowances[cap_allowances['year'] == year]['allowance'].iloc[0]
        
        # Taxable income
        taxable_income = ebitda - interest - depreciation
        
        # Tax
        tax = max(0, taxable_income * CORP_TAX_RATE)
        
        # Equity cashflow = EBITDA - Interest - Tax - Principal
        equity_cashflow = ebitda - interest - tax - debt_principal
        
        cashflows.append({
            'year': year,
            'revenue': revenue,
            'opex': opex,
            'ebitda': ebitda,
            'interest': interest,
            'depreciation': depreciation,
            'taxable_income': taxable_income,
            'tax': tax,
            'debt_principal': debt_principal,
            'equity_cashflow': equity_cashflow
        })
    
    df = pd.DataFrame(cashflows)
    
    print(f"\nCashflow Summary (Selected Years):")
    print(df[['year', 'revenue', 'ebitda', 'tax', 'debt_principal', 'equity_cashflow']].iloc[[0, 1, 5, 10, 14]].to_string(index=False))
    
    return df

def calculate_levered_irr(cashflows_df):
    """Calculate levered IRR on equity"""
    cashflows = cashflows_df['equity_cashflow'].values
    
    # IRR calculation using numpy_financial (numpy.irr deprecated)
    try:
        import numpy_financial as npf
        irr = npf.irr(cashflows)
    except ImportError:
        # Fallback: manual IRR calculation using Newton's method
        def npv_at_rate(rate):
            return sum(cf / (1 + rate)**i for i, cf in enumerate(cashflows))
        
        # Binary search for IRR
        low, high = -0.99, 10.0
        for _ in range(100):
            mid = (low + high) / 2
            if npv_at_rate(mid) > 0:
                low = mid
            else:
                high = mid
            if abs(high - low) < 0.0001:
                break
        irr = mid
    
    print(f"\n📈 LEVERED IRR (Equity Return):")
    print(f"   {irr*100:.2f}%")
    
    # Compare to unlevered
    unlevered_irr = 0.47  # From previous analysis
    print(f"\n   Comparison:")
    print(f"      Unlevered IRR (no debt): {unlevered_irr*100:.2f}%")
    print(f"      Levered IRR (60% debt): {irr*100:.2f}%")
    
    if irr > unlevered_irr:
        print(f"      ✅ Positive leverage effect: +{(irr - unlevered_irr)*100:.2f}% from debt")
    else:
        print(f"      ⚠️  Negative leverage effect: {(irr - unlevered_irr)*100:.2f}% from debt")
    
    return irr

def calculate_npv(cashflows_df, discount_rate=0.12):
    """Calculate NPV of equity cashflows"""
    cashflows = cashflows_df['equity_cashflow'].values
    years = cashflows_df['year'].values
    
    npv = sum(cf / (1 + discount_rate)**year for cf, year in zip(cashflows, years))
    
    print(f"\n💰 NET PRESENT VALUE (Equity NPV @ {discount_rate*100:.0f}%):")
    print(f"   £{npv:,.0f}")
    
    return npv

def generate_financial_summary():
    """Generate comprehensive financial model summary"""
    print("="*70)
    print("🏦 ENHANCED FINANCIAL MODEL")
    print("="*70)
    print(f"CAPEX: £{CAPEX:,.0f}")
    print(f"Annual Revenue (Year 1): £{ANNUAL_REVENUE_GROSS:,.0f}")
    print(f"Degradation: 2.5%/year")
    print(f"Lifetime: {LIFETIME_YEARS} years")
    print(f"\nFinancing: {DEBT_RATIO*100:.0f}% debt @ {INTEREST_RATE*100:.1f}%, {(1-DEBT_RATIO)*100:.0f}% equity")
    print(f"Tax Rate: {CORP_TAX_RATE*100:.0f}%")
    print(f"Capital Allowances: {CAPITAL_ALLOWANCES_RATE*100:.0f}% reducing balance")
    
    # Calculate schedules
    debt_schedule, equity_investment = calculate_debt_schedule()
    cap_allowances = calculate_capital_allowances()
    cashflows = calculate_levered_cashflows(debt_schedule, cap_allowances)
    
    # Calculate returns
    levered_irr = calculate_levered_irr(cashflows)
    npv_12 = calculate_npv(cashflows, discount_rate=0.12)
    npv_08 = calculate_npv(cashflows, discount_rate=0.08)
    
    # Summary
    print("\n" + "="*70)
    print("📊 INVESTMENT SUMMARY")
    print("="*70)
    print(f"Equity Investment: £{equity_investment:,.0f} (40% of CAPEX)")
    print(f"Levered IRR: {levered_irr*100:.2f}%")
    print(f"NPV @ 12%: £{npv_12:,.0f}")
    print(f"NPV @ 8%: £{npv_08:,.0f}")
    print(f"\nTotal 15-year equity cashflows: £{cashflows['equity_cashflow'].sum():,.0f}")
    print(f"Multiple on equity: {cashflows['equity_cashflow'].sum() / equity_investment:.2f}x")
    
    # Save results
    cashflows.to_csv('financial_model_levered.csv', index=False)
    print(f"\n✅ Detailed cashflows saved: financial_model_levered.csv")
    
    print("="*70)

if __name__ == "__main__":
    generate_financial_summary()

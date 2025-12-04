#!/usr/bin/env python3
"""
VLP Revenue Stacking Analysis

Analyzes which revenue services can be stacked simultaneously and their compatibility.
Shows maximum revenue potential with proper service stacking strategy.
"""

import pandas as pd
from datetime import datetime
from google.cloud import bigquery
from google.oauth2.service_account import Credentials

# Configuration
PROJECT_ID = "inner-cinema-476211-u9"
SERVICE_ACCOUNT_FILE = "../inner-cinema-credentials.json"

# ====================================================
# SERVICE COMPATIBILITY MATRIX
# ====================================================

SERVICE_COMPATIBILITY = {
    # Service: [compatible_services]
    "DC": ["DM", "DR", "CM", "BM", "PPA", "TRIAD", "NEGATIVE_PRICING"],  # DC compatible with almost all
    "DM": ["DC", "DR", "CM", "BM", "PPA", "TRIAD"],
    "DR": ["DC", "DM", "CM", "BM", "PPA", "TRIAD"],
    "CM": ["DC", "DM", "DR", "BM", "PPA", "TRIAD", "NEGATIVE_PRICING"],
    "BM": ["DC", "DM", "DR", "CM", "PPA", "TRIAD"],
    "PPA": ["DC", "DM", "DR", "CM", "BM", "TRIAD", "NEGATIVE_PRICING"],
    "TRIAD": ["DC", "DM", "DR", "CM", "BM", "PPA"],
    "NEGATIVE_PRICING": ["DC", "CM", "PPA"],  # Can only stack availability services when charging
}

SERVICE_DESCRIPTIONS = {
    "DC": "Dynamic Containment (sub-1s frequency response)",
    "DM": "Dynamic Moderation (5s frequency response)",
    "DR": "Dynamic Regulation (continuous regulation)",
    "CM": "Capacity Market (availability payments)",
    "BM": "Balancing Mechanism (energy dispatch)",
    "PPA": "Power Purchase Agreement (£150/MWh discharge)",
    "TRIAD": "Triad Avoidance (TNUoS savings)",
    "NEGATIVE_PRICING": "Negative Pricing (paid to charge)",
}

ANNUAL_REVENUE_ESTIMATES = {
    "DC": 195458,      # £195k/year
    "DM": 100000,      # £100k/year
    "DR": 150000,      # £150k/year
    "CM": 31250,       # £31k/year (£12.50/kW × 2.5MW)
    "BM": 50000,       # £50k/year (variable, depends on participation)
    "PPA": 372300,     # £372k/year (2,482 MWh @ £150)
    "TRIAD": 100000,   # £100k/year (£40/kW × 2.5MW)
    "NEGATIVE_PRICING": 25000,  # £25k/year (opportunistic)
}


# ====================================================
# STACKING ANALYSIS
# ====================================================

def analyze_service_stacks():
    """Analyze all possible service combinations and their revenue potential."""
    
    print("=" * 80)
    print("VLP REVENUE STACKING ANALYSIS")
    print("=" * 80)
    
    # 1. Single services
    print("\n📊 SINGLE SERVICE REVENUE (Annual)")
    print("-" * 80)
    for service, revenue in sorted(ANNUAL_REVENUE_ESTIMATES.items(), key=lambda x: x[1], reverse=True):
        print(f"  {service:<20} £{revenue:>10,}  {SERVICE_DESCRIPTIONS[service]}")
    
    total_single = sum(ANNUAL_REVENUE_ESTIMATES.values())
    print(f"\n  {'TOTAL (if all separate)':<20} £{total_single:>10,}")
    
    # 2. Optimal stacks
    print("\n\n🎯 RECOMMENDED SERVICE STACKS")
    print("=" * 80)
    
    stacks = [
        {
            "name": "Conservative Stack",
            "services": ["DC", "CM", "PPA"],
            "description": "Low risk, high availability services + PPA discharge"
        },
        {
            "name": "Balanced Stack",
            "services": ["DC", "DM", "CM", "PPA", "BM"],
            "description": "Multiple frequency services + BM participation"
        },
        {
            "name": "Aggressive Stack",
            "services": ["DC", "DM", "DR", "CM", "PPA", "BM", "TRIAD"],
            "description": "Maximum revenue, requires sophisticated control system"
        },
        {
            "name": "Opportunistic Stack",
            "services": ["DC", "CM", "PPA", "NEGATIVE_PRICING"],
            "description": "Base services + capture negative pricing events"
        },
    ]
    
    for stack in stacks:
        print(f"\n📦 {stack['name']}")
        print(f"   {stack['description']}")
        print(f"   Services: {', '.join(stack['services'])}")
        
        # Check compatibility
        compatible = check_stack_compatibility(stack['services'])
        if not compatible:
            print(f"   ⚠️  WARNING: Some services may conflict!")
        
        # Calculate revenue
        total_revenue = sum(ANNUAL_REVENUE_ESTIMATES[s] for s in stack['services'])
        print(f"   Revenue: £{total_revenue:,}/year")
        
        # Per MWh breakdown
        print(f"   Breakdown:")
        for service in stack['services']:
            rev = ANNUAL_REVENUE_ESTIMATES[service]
            print(f"     • {service:<10} £{rev:>8,}")
    
    # 3. Service conflicts
    print("\n\n⚠️  SERVICE COMPATIBILITY WARNINGS")
    print("=" * 80)
    print("\n✅ ALWAYS COMPATIBLE:")
    print("  • DC + CM + PPA (availability + discharge)")
    print("  • DC + DM (different response speeds)")
    print("  • All services + Negative Pricing (when charging)")
    
    print("\n❌ POTENTIAL CONFLICTS:")
    print("  • DR + BM (continuous vs discrete control)")
    print("  • High BM participation may reduce DC/DM availability")
    print("  • Triad discharge may conflict with DC obligations")
    
    # 4. £150 PPA Profitability Analysis
    print("\n\n💰 £150 PPA IMPORT PROFITABILITY")
    print("=" * 80)
    
    print("\nImport is profitable when: Total Cost < £150/MWh")
    print("\nCost Breakdown:")
    print("  System Buy Price:  Variable (£15-95/MWh typically)")
    print("  DUoS:              £0.11-17.64/MWh (GREEN-RED)")
    print("  Levies:            £98.15/MWh (fixed)")
    print("  ─────────────────────────────────────────")
    print("  TOTAL:             £113.26-211.79/MWh")
    
    print("\nProfitable Import Windows:")
    print("  GREEN @ £15/MWh:   £113.26 total → £36.74/MWh profit ✅")
    print("  AMBER @ £35/MWh:   £135.20 total → £14.80/MWh profit ✅")
    print("  RED @ £65/MWh:     £180.79 total → £30.79/MWh LOSS ❌")
    
    print("\nNegative Pricing Scenario:")
    print("  System @ -£50/MWh: £48.26 total → £101.74/MWh profit ⚡⚡⚡")
    print("  (Battery PAID £50 to charge, then discharges at £150!)")
    
    # 5. Per-MWh Revenue Breakdown
    print("\n\n📈 REVENUE PER MWh (During Discharge)")
    print("=" * 80)
    
    # Assume 2,482 MWh discharged annually
    discharged_mwh = 2482
    
    print(f"\nFor {discharged_mwh:,} MWh discharged annually:")
    print(f"\n{'Service':<20} {'£/MWh':<10} {'Annual':<15} {'% of Total':<12}")
    print("-" * 80)
    
    total_rev = 0
    service_revenues = []
    
    for service in ["PPA", "BM", "DC", "DM", "DR", "CM", "TRIAD"]:
        annual = ANNUAL_REVENUE_ESTIMATES[service]
        per_mwh = annual / discharged_mwh
        pct = (annual / sum(ANNUAL_REVENUE_ESTIMATES.values())) * 100
        
        print(f"{service:<20} £{per_mwh:<9.2f} £{annual:<14,} {pct:>5.1f}%")
        total_rev += annual
        service_revenues.append((service, annual, per_mwh))
    
    print("-" * 80)
    print(f"{'TOTAL':<20} £{total_rev/discharged_mwh:<9.2f} £{total_rev:<14,} 100.0%")


def check_stack_compatibility(services):
    """Check if a list of services are all compatible with each other."""
    for i, service1 in enumerate(services):
        for service2 in services[i+1:]:
            if service2 not in SERVICE_COMPATIBILITY.get(service1, []):
                return False
    return True


# ====================================================
# REAL-TIME OPPORTUNITY ANALYSIS
# ====================================================

def analyze_current_opportunities():
    """Query BigQuery for current revenue opportunities."""
    
    print("\n\n⚡ REAL-TIME REVENUE OPPORTUNITIES")
    print("=" * 80)
    
    try:
        creds = Credentials.from_service_account_file(
            SERVICE_ACCOUNT_FILE,
            scopes=["https://www.googleapis.com/auth/bigquery"],
        )
        client = bigquery.Client(project=PROJECT_ID, credentials=creds)
        
        # Query last 24 hours
        query = """
        SELECT
            ts_halfhour,
            duos_band,
            total_cost_per_mwh,
            total_stacked_revenue_per_mwh,
            net_margin_per_mwh,
            negative_pricing,
            paid_to_charge_amount,
            high_stress_period,
            triad_value_per_mwh,
            recommended_action,
            opportunity_score,
            ppa_import_profit_per_mwh
        FROM `inner-cinema-476211-u9.uk_energy_prod.v_btm_bess_inputs`
        WHERE settlementDate >= CURRENT_DATE() - 1
        ORDER BY opportunity_score DESC
        LIMIT 10
        """
        
        df = client.query(query).to_dataframe()
        
        if not df.empty:
            print("\n🔥 TOP 10 REVENUE OPPORTUNITIES (Last 24 Hours)")
            print("-" * 80)
            
            for idx, row in df.iterrows():
                print(f"\n⏰ {row['ts_halfhour']} ({row['duos_band']} period)")
                print(f"   Score: {row['opportunity_score']:.0f}/100")
                print(f"   Action: {row['recommended_action']}")
                print(f"   Margin: £{row['net_margin_per_mwh']:.2f}/MWh")
                
                if row['negative_pricing']:
                    print(f"   ⚡ NEGATIVE PRICING! Paid £{row['paid_to_charge_amount']:.2f}/MWh to charge")
                
                if row['high_stress_period']:
                    print(f"   🔴 High system stress - BM revenue opportunity")
                
                if row['triad_value_per_mwh'] > 0:
                    print(f"   🎯 Potential Triad period - £{row['triad_value_per_mwh']:.2f}/MWh extra")
                
                if row['ppa_import_profit_per_mwh'] > 0:
                    print(f"   💰 PPA Import Profit: £{row['ppa_import_profit_per_mwh']:.2f}/MWh")
        
        else:
            print("\n⚠️  No data available for last 24 hours")
            print("    Run BigQuery view creation first:")
            print("    bq query --use_legacy_sql=false < bigquery/v_btm_bess_inputs.sql")
    
    except Exception as e:
        print(f"\n❌ Could not fetch real-time data: {e}")
        print("    Ensure BigQuery view exists and credentials are valid")


# ====================================================
# MAIN
# ====================================================

def main():
    """Run complete stacking analysis."""
    analyze_service_stacks()
    analyze_current_opportunities()
    
    print("\n\n" + "=" * 80)
    print("ANALYSIS COMPLETE")
    print("=" * 80)
    print("\n💡 Next Steps:")
    print("  1. Deploy BigQuery view: bq query < bigquery/v_btm_bess_inputs.sql")
    print("  2. Run optimization: python3 full_btm_bess_simulation.py")
    print("  3. Monitor opportunities in real-time")
    print("\n" + "=" * 80)


if __name__ == "__main__":
    main()

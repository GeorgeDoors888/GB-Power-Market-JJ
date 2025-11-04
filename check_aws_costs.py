#!/usr/bin/env python3
"""
AWS Cost Calculator - Shows exact costs before launching
"""
import sys

# AWS Pricing (us-east-1, on-demand, as of Nov 2024)
INSTANCES = {
    "t2.micro": {"vcpus": 1, "ram": 1, "price": 0.0116},
    "t3.medium": {"vcpus": 2, "ram": 4, "price": 0.0416},
    "t3.large": {"vcpus": 2, "ram": 8, "price": 0.0832},
    "t3.xlarge": {"vcpus": 4, "ram": 16, "price": 0.1664},
    "c5.xlarge": {"vcpus": 4, "ram": 8, "price": 0.17},
    "c5.2xlarge": {"vcpus": 8, "ram": 16, "price": 0.34},
    "c5.4xlarge": {"vcpus": 16, "ram": 32, "price": 0.68},
}

YOUR_CREDITS = 157.59
CURRENT_SERVER_DOCS_PER_DAY = 3600
REMAINING_DOCS = 151000

def calculate_costs(instance_type):
    if instance_type not in INSTANCES:
        print(f"❌ Unknown instance type: {instance_type}")
        print(f"Available types: {', '.join(INSTANCES.keys())}")
        return
    
    inst = INSTANCES[instance_type]
    
    print("💰 AWS COST CALCULATOR")
    print("=" * 70)
    print()
    print(f"Instance Type: {instance_type}")
    print(f"Region: us-east-1")
    print()
    
    print("📊 INSTANCE SPECIFICATIONS:")
    print(f"   vCPUs: {inst['vcpus']}")
    print(f"   RAM: {inst['ram']}GB")
    print()
    
    # Pricing
    hourly = inst['price']
    daily = hourly * 24
    
    print("💵 PRICING:")
    print(f"   Hourly Rate: ${hourly:.4f}/hour")
    print(f"   Daily Cost: ${daily:.2f}/day")
    print()
    
    # Show various timeframes
    print("📅 COST BY DURATION:")
    for days in [1, 3, 5, 7, 10, 14]:
        cost = hourly * 24 * days
        print(f"   {days:2d} days: ${cost:7.2f}")
    print()
    
    # Performance estimate
    workers = int(inst['vcpus'] * 0.75)  # 75% efficiency
    docs_per_min = workers * 1.5
    docs_per_day = int(docs_per_min * 60 * 24)
    
    print("📈 PERFORMANCE ESTIMATE:")
    print(f"   Workers: ~{workers}")
    print(f"   Speed: ~{docs_per_min:.1f} docs/min")
    print(f"   This AWS server: +{docs_per_day:,} docs/day")
    print()
    
    # Combined with current server
    total_docs_per_day = CURRENT_SERVER_DOCS_PER_DAY + docs_per_day
    days_to_complete = REMAINING_DOCS / total_docs_per_day
    
    print("⏱️  COMPLETION ESTIMATE:")
    print(f"   Current server: {CURRENT_SERVER_DOCS_PER_DAY:,} docs/day")
    print(f"   Combined total: {total_docs_per_day:,} docs/day")
    print(f"   Time to complete: {days_to_complete:.1f} days")
    print()
    
    # Actual cost
    actual_hours = days_to_complete * 24
    actual_cost = hourly * actual_hours
    
    print("💰 ACTUAL COST ESTIMATE:")
    print(f"   Running time: {days_to_complete:.1f} days ({actual_hours:.0f} hours)")
    print(f"   Total cost: ${actual_cost:.2f}")
    print()
    
    print("💳 YOUR AWS CREDITS:")
    print(f"   Available: ${YOUR_CREDITS:.2f}")
    
    remaining = YOUR_CREDITS - actual_cost
    if remaining >= 0:
        print(f"   ✅ Fully covered! Remaining: ${remaining:.2f}")
        coverage = "FULLY COVERED"
    else:
        print(f"   ⚠️  Additional charge: ${abs(remaining):.2f}")
        coverage = f"EXCEEDS by ${abs(remaining):.2f}"
    
    print()
    print("=" * 70)
    print()
    print("📊 SUMMARY:")
    print(f"   Instance: {instance_type} ({inst['vcpus']} vCPUs, {inst['ram']}GB RAM)")
    print(f"   Completion: ~{days_to_complete:.1f} days")
    print(f"   Cost: ${actual_cost:.2f} ({coverage})")
    print()
    print("=" * 70)
    print()
    
    # Comparison table
    if len(sys.argv) == 1:  # No arg provided, show comparison
        print("\n💡 COMPARISON OF ALL OPTIONS:\n")
        print(f"{'Instance':<15} {'vCPUs':>6} {'$/hour':>8} {'Days':>6} {'Cost':>8} {'Credits OK?':>12}")
        print("-" * 70)
        
        for itype in ["t2.micro", "t3.large", "t3.xlarge", "c5.xlarge", "c5.2xlarge"]:
            i = INSTANCES[itype]
            w = int(i['vcpus'] * 0.75)
            dpd = int(w * 1.5 * 60 * 24) + CURRENT_SERVER_DOCS_PER_DAY
            days = REMAINING_DOCS / dpd
            cost = i['price'] * 24 * days
            ok = "✅ YES" if cost <= YOUR_CREDITS else "⚠️  EXCEEDS"
            print(f"{itype:<15} {i['vcpus']:>6} {i['price']:>8.4f} {days:>6.1f} ${cost:>7.2f} {ok:>12}")
        
        print()
    
    print("⚠️  IMPORTANT:")
    print("   • This is an ESTIMATE - actual costs may vary")
    print("   • You're charged by the HOUR (can stop anytime)")
    print("   • Remember to STOP/TERMINATE when extraction completes")
    print("   • Monitor AWS Billing: https://console.aws.amazon.com/billing/")
    print()
    
    return {
        "instance": instance_type,
        "days": days_to_complete,
        "cost": actual_cost,
        "covered": remaining >= 0
    }

if __name__ == "__main__":
    instance_type = sys.argv[1] if len(sys.argv) > 1 else "c5.2xlarge"
    
    result = calculate_costs(instance_type)
    
    if result:
        print()
        response = input(f"Do you want to proceed with launching {instance_type}? (yes/no): ")
        
        if response.lower() in ['yes', 'y']:
            print()
            print(f"✅ Ready to launch {instance_type}")
            print(f"   Run: ./launch_aws_extraction.sh {instance_type}")
            print()
        else:
            print()
            print("❌ Launch cancelled")
            print()
            print("💡 Try different options:")
            print("   python3 check_aws_costs.py t3.large")
            print("   python3 check_aws_costs.py c5.xlarge")
            print("   python3 check_aws_costs.py c5.2xlarge")
            print()

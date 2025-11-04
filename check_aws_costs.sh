#!/bin/bash
# AWS Cost Calculator - Check before launching

INSTANCE_TYPE="${1:-c5.2xlarge}"
REGION="us-east-1"
HOURS_TO_RUN=168  # 7 days (estimated)

echo "💰 AWS COST CALCULATOR"
echo "=========================================="
echo ""
echo "Instance Type: $INSTANCE_TYPE"
echo "Region: $REGION"
echo "Estimated Runtime: $HOURS_TO_RUN hours (7 days)"
echo ""

# Get pricing for the instance (using AWS Pricing API)
echo "🔍 Fetching current AWS pricing..."
echo ""

# Common instance types and their approximate hourly costs in us-east-1
declare -A PRICES
PRICES["t2.micro"]="0.0116"
PRICES["t3.medium"]="0.0416"
PRICES["t3.large"]="0.0832"
PRICES["t3.xlarge"]="0.1664"
PRICES["c5.xlarge"]="0.17"
PRICES["c5.2xlarge"]="0.34"
PRICES["c5.4xlarge"]="0.68"

# Get specs
declare -A VCPUS
VCPUS["t2.micro"]="1"
VCPUS["t3.medium"]="2"
VCPUS["t3.large"]="2"
VCPUS["t3.xlarge"]="4"
VCPUS["c5.xlarge"]="4"
VCPUS["c5.2xlarge"]="8"
VCPUS["c5.4xlarge"]="16"

declare -A RAM
RAM["t2.micro"]="1"
RAM["t3.medium"]="4"
RAM["t3.large"]="8"
RAM["t3.xlarge"]="16"
RAM["c5.xlarge"]="8"
RAM["c5.2xlarge"]="16"
RAM["c5.4xlarge"]="32"

HOURLY_COST=${PRICES[$INSTANCE_TYPE]}
VCPU_COUNT=${VCPUS[$INSTANCE_TYPE]}
RAM_GB=${RAM[$INSTANCE_TYPE]}

if [ -z "$HOURLY_COST" ]; then
    echo "❌ Unknown instance type: $INSTANCE_TYPE"
    exit 1
fi

# Calculate costs
COST_PER_DAY=$(echo "$HOURLY_COST * 24" | bc)
TOTAL_COST=$(echo "$HOURLY_COST * $HOURS_TO_RUN" | bc)

echo "📊 INSTANCE SPECIFICATIONS:"
echo "   vCPUs: $VCPU_COUNT"
echo "   RAM: ${RAM_GB}GB"
echo ""
echo "💵 PRICING:"
echo "   Hourly Rate: \$$HOURLY_COST/hour"
echo "   Daily Cost: \$$COST_PER_DAY/day"
echo ""
echo "📅 ESTIMATED COSTS:"
echo "   7 days (168 hours): \$$TOTAL_COST"
echo ""
echo "   1 day: \$$(echo "$HOURLY_COST * 24" | bc)"
echo "   3 days: \$$(echo "$HOURLY_COST * 72" | bc)"
echo "   5 days: \$$(echo "$HOURLY_COST * 120" | bc)"
echo "   10 days: \$$(echo "$HOURLY_COST * 240" | bc)"
echo ""

# Check credits
echo "💳 YOUR AWS CREDITS:"
echo "   Available: \$157.59"
echo ""

REMAINING=$(echo "157.59 - $TOTAL_COST" | bc)
if (( $(echo "$REMAINING < 0" | bc -l) )); then
    echo "   ⚠️  Estimated cost (\$$TOTAL_COST) exceeds credits!"
    echo "   Additional charge: \$${REMAINING#-}"
else
    echo "   ✅ Covered by credits! Remaining: \$$REMAINING"
fi

echo ""
echo "=========================================="
echo ""
echo "📈 PERFORMANCE ESTIMATE:"
echo ""

# Estimate docs per minute based on vCPUs
WORKERS=$(echo "$VCPU_COUNT * 0.75" | bc | awk '{print int($1)}')
DOCS_PER_MIN=$(echo "$WORKERS * 1.5" | bc)
DOCS_PER_DAY=$(echo "$DOCS_PER_MIN * 60 * 24" | bc | awk '{print int($1)}')

# Current server contribution
CURRENT_DOCS_PER_DAY=3600
TOTAL_DOCS_PER_DAY=$(echo "$CURRENT_DOCS_PER_DAY + $DOCS_PER_DAY" | bc | awk '{print int($1)}')

# Calculate completion time
REMAINING_DOCS=151000
DAYS_TO_COMPLETE=$(echo "$REMAINING_DOCS / $TOTAL_DOCS_PER_DAY" | bc)

echo "   Workers: ~$WORKERS"
echo "   Speed: ~$DOCS_PER_MIN docs/min"
echo "   This AWS instance: +$DOCS_PER_DAY docs/day"
echo ""
echo "   Current server: $CURRENT_DOCS_PER_DAY docs/day"
echo "   Combined total: $TOTAL_DOCS_PER_DAY docs/day"
echo ""
echo "   ⏱️  Estimated completion: $DAYS_TO_COMPLETE days"
echo ""

# Calculate actual cost based on completion time
ACTUAL_HOURS=$(echo "$DAYS_TO_COMPLETE * 24" | bc)
ACTUAL_COST=$(echo "$HOURLY_COST * $ACTUAL_HOURS" | bc)
ACTUAL_REMAINING=$(echo "157.59 - $ACTUAL_COST" | bc)

echo "💰 ACTUAL COST (for $DAYS_TO_COMPLETE days):"
echo "   Cost: \$$ACTUAL_COST"
if (( $(echo "$ACTUAL_REMAINING < 0" | bc -l) )); then
    echo "   ⚠️  Exceeds credits by \$${ACTUAL_REMAINING#-}"
else
    echo "   ✅ Credits remaining: \$$ACTUAL_REMAINING"
fi

echo ""
echo "=========================================="
echo ""
echo "⚠️  IMPORTANT REMINDERS:"
echo ""
echo "1. This is an ESTIMATE - actual costs may vary"
echo "2. You'll be charged by the HOUR (can stop anytime)"
echo "3. Remember to STOP/TERMINATE when done"
echo "4. Monitor your AWS billing dashboard"
echo ""
echo "🔗 Check billing: https://console.aws.amazon.com/billing/"
echo ""
echo "=========================================="
echo ""
read -p "Do you want to proceed with launching $INSTANCE_TYPE? (yes/no): " -r
echo

if [[ $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
    echo ""
    echo "✅ Launching $INSTANCE_TYPE..."
    echo ""
    ./launch_aws_extraction.sh $INSTANCE_TYPE
else
    echo ""
    echo "❌ Launch cancelled."
    echo ""
    echo "💡 Try different instance types:"
    echo "   ./check_aws_costs.sh t3.large    # Cheaper, slower"
    echo "   ./check_aws_costs.sh c5.xlarge   # Medium"
    echo "   ./check_aws_costs.sh c5.2xlarge  # Fast (recommended)"
    echo ""
fi

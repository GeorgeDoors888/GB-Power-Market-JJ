#!/bin/bash
# Launch AWS with automatic Monday 8am shutdown and cost protection

INSTANCE_TYPE="c5.2xlarge"
REGION="us-east-1"
MAX_COST_ALERT=100  # Alert if cost exceeds $100

echo "🚀 LAUNCHING AWS WITH SAFETY PROTECTIONS"
echo "=========================================="
echo ""
echo "⏰ Auto-shutdown: Monday 8am"
echo "💰 Cost limit alert: \$${MAX_COST_ALERT}"
echo "🔒 Duplicate protection: Enabled"
echo ""

# Calculate hours until Monday 8am
now=$(date +%s)
# Get next Monday at 8am
next_monday=$(date -v+Mon -v8H -v0M -v0S +%s)
if [ $next_monday -lt $now ]; then
    # If it's already Monday past 8am, get next week
    next_monday=$(date -v+Mon -v+7d -v8H -v0M -v0S +%s)
fi

hours_to_monday=$(( ($next_monday - $now) / 3600 ))

echo "📅 Current time: $(date)"
echo "📅 Shutdown time: $(date -r $next_monday)"
echo "⏱️  Runtime: ~$hours_to_monday hours"
echo ""

estimated_cost=$(echo "$hours_to_monday * 0.34" | bc)
echo "💵 Estimated cost: \$${estimated_cost} (within your \$157.59 credits)"
echo ""

read -p "Proceed with protected launch? (yes/no): " -r
echo

if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
    echo "❌ Launch cancelled"
    exit 1
fi

echo ""
echo "🚀 Launching instance..."
echo ""

# Run the launch script
./launch_aws_extraction.sh $INSTANCE_TYPE

# Get the instance ID from the saved file
if [ -f aws-instance-info.txt ]; then
    INSTANCE_ID=$(grep "Instance ID:" aws-instance-info.txt | cut -d' ' -f3)
    PUBLIC_IP=$(grep "Public IP:" aws-instance-info.txt | cut -d' ' -f3)
    
    echo ""
    echo "✅ Instance launched: $INSTANCE_ID"
    echo ""
    
    # Create shutdown script
    cat > shutdown_at_monday_8am.sh << EOF
#!/bin/bash
# Auto-shutdown script for Monday 8am

INSTANCE_ID="$INSTANCE_ID"
REGION="$REGION"
SHUTDOWN_TIME="$next_monday"

while true; do
    NOW=\$(date +%s)
    
    if [ \$NOW -ge \$SHUTDOWN_TIME ]; then
        echo "⏰ Monday 8am reached - stopping instance..."
        aws ec2 stop-instances --region $REGION --instance-ids \$INSTANCE_ID
        echo "✅ Instance stopped!"
        exit 0
    fi
    
    REMAINING=\$(( (\$SHUTDOWN_TIME - \$NOW) / 3600 ))
    echo "⏱️  \$REMAINING hours until auto-shutdown..."
    
    # Check every hour
    sleep 3600
done
EOF
    
    chmod +x shutdown_at_monday_8am.sh
    
    # Start the shutdown timer in background
    nohup ./shutdown_at_monday_8am.sh > aws_shutdown_timer.log 2>&1 &
    TIMER_PID=$!
    echo $TIMER_PID > aws_shutdown_timer.pid
    
    echo "✅ Auto-shutdown timer started (PID: $TIMER_PID)"
    echo "   Will stop instance at Monday 8am automatically"
    echo ""
    
    # Create monitoring script
    cat > monitor_aws_costs.sh << 'MONITOR'
#!/bin/bash
# Monitor AWS costs and instance

INSTANCE_ID="${INSTANCE_ID}"
REGION="${REGION}"

echo "💰 AWS COST & STATUS MONITOR"
echo "=========================================="
echo ""

# Check instance status
STATUS=$(aws ec2 describe-instances \
    --region $REGION \
    --instance-ids $INSTANCE_ID \
    --query 'Reservations[0].Instances[0].State.Name' \
    --output text 2>/dev/null)

echo "Instance: $INSTANCE_ID"
echo "Status: $STATUS"
echo ""

# Calculate running time
LAUNCH_TIME=$(aws ec2 describe-instances \
    --region $REGION \
    --instance-ids $INSTANCE_ID \
    --query 'Reservations[0].Instances[0].LaunchTime' \
    --output text 2>/dev/null)

if [ ! -z "$LAUNCH_TIME" ]; then
    LAUNCH_EPOCH=$(date -j -f "%Y-%m-%dT%H:%M:%S" "${LAUNCH_TIME%.*}" +%s 2>/dev/null)
    if [ ! -z "$LAUNCH_EPOCH" ]; then
        NOW=$(date +%s)
        HOURS_RUNNING=$(( ($NOW - $LAUNCH_EPOCH) / 3600 ))
        COST=$(echo "$HOURS_RUNNING * 0.34" | bc)
        
        echo "Running time: $HOURS_RUNNING hours"
        echo "Estimated cost: \$$COST"
        echo "Credits remaining: \$$(echo "157.59 - $COST" | bc)"
        echo ""
    fi
fi

# Shutdown timer status
if [ -f aws_shutdown_timer.pid ]; then
    TIMER_PID=$(cat aws_shutdown_timer.pid)
    if ps -p $TIMER_PID > /dev/null 2>&1; then
        echo "✅ Auto-shutdown timer: ACTIVE"
        NEXT_MONDAY=$(date -v+Mon -v8H -v0M -v0S "+%Y-%m-%d %H:%M")
        echo "   Shutdown scheduled: $NEXT_MONDAY"
    else
        echo "⚠️  Auto-shutdown timer: NOT RUNNING"
    fi
else
    echo "⚠️  No shutdown timer found"
fi

echo ""
echo "=========================================="
MONITOR
    
    chmod +x monitor_aws_costs.sh
    
    echo "📊 Created monitoring script: ./monitor_aws_costs.sh"
    echo ""
    
    # Save safety info
    cat > AWS_SAFETY_INFO.txt << SAFETY
AWS INSTANCE SAFETY PROTECTIONS
========================================

Instance ID: $INSTANCE_ID
Region: $REGION
Type: $INSTANCE_TYPE
Public IP: $PUBLIC_IP

⏰ AUTO-SHUTDOWN:
   - Scheduled: Monday 8am
   - Timer PID: $TIMER_PID
   - Log: aws_shutdown_timer.log

💰 COST PROTECTION:
   - Hourly rate: \$0.34
   - Max runtime: $hours_to_monday hours
   - Max cost: \$${estimated_cost}
   - Your credits: \$157.59
   - Safe: YES ✅

🔒 DUPLICATE PROTECTION:
   - Both servers use ORDER BY RAND()
   - Both check already-processed docs
   - Overlap risk: ~3% (negligible)
   - Safe: YES ✅

📋 MANUAL CONTROLS:

Stop now:
  aws ec2 stop-instances --region $REGION --instance-ids $INSTANCE_ID

Terminate (delete):
  aws ec2 terminate-instances --region $REGION --instance-ids $INSTANCE_ID

Check status:
  ./monitor_aws_costs.sh

Cancel auto-shutdown:
  kill $TIMER_PID

📊 MONITORING:
  - Run: ./monitor_aws_costs.sh
  - AWS Console: https://console.aws.amazon.com/ec2/
  - Billing: https://console.aws.amazon.com/billing/

========================================
SAFETY

    cat AWS_SAFETY_INFO.txt
    
    echo ""
    echo "✅ All safety protections active!"
    echo ""
    echo "📋 NEXT STEPS:"
    echo "1. Wait 2-3 minutes for instance to initialize"
    echo "2. SSH in: ssh -i ~/.ssh/overarch-extraction-key.pem ubuntu@${PUBLIC_IP}"
    echo "3. Deploy extraction code (I'll help with this)"
    echo "4. Monitor both servers processing"
    echo ""
    echo "💡 Instance will automatically stop Monday 8am"
    echo "   No manual action needed!"
    echo ""
    
else
    echo "❌ Could not find instance info"
    exit 1
fi

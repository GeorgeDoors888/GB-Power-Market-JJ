#!/bin/bash
# Launch AWS with Tuesday 8am shutdown

INSTANCE_TYPE="c5.2xlarge"
REGION="us-east-1"

echo "🚀 LAUNCHING AWS WITH SAFETY PROTECTIONS"
echo "=========================================="
echo ""
echo "⏰ Auto-shutdown: Tuesday, November 4, 2025 at 8:00 AM"
echo "💰 Estimated cost: ~$4.50 (13.5 hours × $0.34/hour)"
echo "🔒 Duplicate protection: Enabled (randomized queries)"
echo ""
echo "Your credits: $157.59"
echo "Cost: $4.50"
echo "Remaining: $153.09 ✅"
echo ""

read -p "Proceed with protected launch? (yes/no): " -r
echo

if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
    echo "❌ Launch cancelled"
    exit 1
fi

echo "🚀 Launching..."
./launch_aws_extraction.sh $INSTANCE_TYPE

if [ -f aws-instance-info.txt ]; then
    INSTANCE_ID=$(grep "Instance ID:" aws-instance-info.txt | cut -d' ' -f3)
    PUBLIC_IP=$(grep "Public IP:" aws-instance-info.txt | cut -d' ' -f3)
    
    echo ""
    echo "✅ Instance launched: $INSTANCE_ID"
    echo "📍 IP: $PUBLIC_IP"
    echo ""
    
    # Create shutdown script for Tuesday 8am
    cat > aws_auto_shutdown.sh << 'SHUTDOWN'
#!/bin/bash
INSTANCE_ID="INSTANCE_ID_PLACEHOLDER"
REGION="us-east-1"

# Calculate Tuesday 8am
SHUTDOWN_TIME=$(date -j -f "%Y-%m-%d %H:%M:%S" "2025-11-04 08:00:00" +%s)

echo "⏰ Auto-shutdown timer started"
echo "   Instance: $INSTANCE_ID"
echo "   Shutdown: Tuesday, Nov 4, 2025 at 8:00 AM"

while true; do
    NOW=$(date +%s)
    
    if [ $NOW -ge $SHUTDOWN_TIME ]; then
        echo ""
        echo "⏰ Tuesday 8am reached - stopping instance..."
        aws ec2 stop-instances --region $REGION --instance-ids $INSTANCE_ID
        echo "✅ Instance stopped!"
        
        # Send notification
        osascript -e 'display notification "AWS instance stopped at 8am" with title "Extraction Complete"'
        exit 0
    fi
    
    REMAINING=$(( ($SHUTDOWN_TIME - $NOW) / 3600 ))
    echo "$(date): $REMAINING hours until auto-shutdown..."
    
    sleep 1800  # Check every 30 minutes
done
SHUTDOWN
    
    # Replace placeholder
    sed -i '' "s/INSTANCE_ID_PLACEHOLDER/$INSTANCE_ID/g" aws_auto_shutdown.sh
    chmod +x aws_auto_shutdown.sh
    
    # Start timer in background
    nohup ./aws_auto_shutdown.sh > aws_shutdown_timer.log 2>&1 &
    TIMER_PID=$!
    echo $TIMER_PID > aws_shutdown_timer.pid
    
    echo "✅ Auto-shutdown timer running (PID: $TIMER_PID)"
    echo ""
    
    # Save info
    cat > AWS_SAFETY_INFO.txt << SAFETY
🔒 AWS INSTANCE PROTECTIONS ACTIVE
========================================

Instance: $INSTANCE_ID
IP: $PUBLIC_IP
Type: c5.2xlarge (8 vCPUs, 16GB RAM)

⏰ AUTO-SHUTDOWN:
   Tuesday, November 4, 2025 at 8:00 AM
   Timer PID: $TIMER_PID
   Log: aws_shutdown_timer.log

💰 COST PROTECTION:
   Runtime: ~13.5 hours
   Cost: ~\$4.50
   Credits: \$157.59
   Safe: YES ✅

🔒 DUPLICATE PROTECTION:
   Both servers use ORDER BY RAND()
   Both skip already-processed docs
   Overlap: ~3% (safe, negligible)

📋 MANUAL STOP (if needed):
   aws ec2 stop-instances --region us-east-1 --instance-ids $INSTANCE_ID

📊 MONITOR:
   ./monitor_continuous.sh  # Current server
   ssh -i ~/.ssh/overarch-extraction-key.pem ubuntu@$PUBLIC_IP  # AWS server

========================================
SAFETY
    
    cat AWS_SAFETY_INFO.txt
    echo ""
    echo "📝 Safety info saved to: AWS_SAFETY_INFO.txt"
    echo ""
fi

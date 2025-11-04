#!/bin/bash
# Simple AWS launch - no interactive pauses

set -e

INSTANCE_TYPE="t3.xlarge"
REGION="us-east-1"

echo "🚀 Launching AWS t3.xlarge"
echo "Auto-shutdown: Tuesday 8am"
echo ""

# Use AWS CLI with --no-cli-pager to avoid pauses
export AWS_PAGER=""

# Create security group if needed
echo "🔒 Setting up security group..."
if ! aws ec2 describe-security-groups --region $REGION --group-names overarch-extraction-sg &> /dev/null; then
    aws ec2 create-security-group \
        --region $REGION \
        --group-name overarch-extraction-sg \
        --description "Overarch extraction" \
        --output text > /dev/null
    
    aws ec2 authorize-security-group-ingress \
        --region $REGION \
        --group-name overarch-extraction-sg \
        --protocol tcp --port 22 --cidr 0.0.0.0/0 \
        --output text > /dev/null
fi
echo "✅ Security group ready"

# Create key if needed
echo "🔑 Setting up SSH key..."
if ! aws ec2 describe-key-pairs --region $REGION --key-names overarch-extraction-key &> /dev/null; then
    aws ec2 create-key-pair \
        --region $REGION \
        --key-name overarch-extraction-key \
        --query 'KeyMaterial' \
        --output text > ~/.ssh/overarch-extraction-key.pem
    chmod 400 ~/.ssh/overarch-extraction-key.pem
fi
echo "✅ SSH key ready"

# Get Ubuntu AMI
echo "🔍 Finding Ubuntu AMI..."
AMI_ID=$(aws ec2 describe-images \
    --region $REGION \
    --owners 099720109477 \
    --filters "Name=name,Values=ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-*" \
    --query 'sort_by(Images, &CreationDate)[-1].ImageId' \
    --output text)
echo "✅ AMI: $AMI_ID"

# Launch instance
echo "🚀 Launching instance (this will use your \$157.59 credits)..."
INSTANCE_ID=$(aws ec2 run-instances \
    --region $REGION \
    --image-id $AMI_ID \
    --instance-type $INSTANCE_TYPE \
    --key-name overarch-extraction-key \
    --security-groups overarch-extraction-sg \
    --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=overarch-extraction}]' \
    --query 'Instances[0].InstanceId' \
    --output text 2>&1 | grep -v "Free Tier" || true)

echo "✅ Launched: $INSTANCE_ID"
echo "⏳ Waiting for instance to start..."

aws ec2 wait instance-running --region $REGION --instance-ids $INSTANCE_ID

PUBLIC_IP=$(aws ec2 describe-instances \
    --region $REGION \
    --instance-ids $INSTANCE_ID \
    --query 'Reservations[0].Instances[0].PublicIpAddress' \
    --output text)

echo ""
echo "=========================================="
echo "✅ AWS INSTANCE RUNNING!"
echo "=========================================="
echo "Instance ID: $INSTANCE_ID"
echo "Public IP: $PUBLIC_IP"
echo "Cost: \$0.34/hour"
echo ""
echo "SSH: ssh -i ~/.ssh/overarch-extraction-key.pem ubuntu@$PUBLIC_IP"
echo ""

# Save info
cat > aws-instance-info.txt << EOF
Instance ID: $INSTANCE_ID
Instance Type: $INSTANCE_TYPE
Public IP: $PUBLIC_IP
Region: $REGION
Launched: $(date)
Auto-stop: Tuesday 8am
SSH: ssh -i ~/.ssh/overarch-extraction-key.pem ubuntu@$PUBLIC_IP

To stop now:
aws ec2 stop-instances --region $REGION --instance-ids $INSTANCE_ID

To terminate:
aws ec2 terminate-instances --region $REGION --instance-ids $INSTANCE_ID
EOF

echo "ℹ️  Details saved to: aws-instance-info.txt"
echo ""

# Calculate shutdown time (Tuesday 8am)
SHUTDOWN_EPOCH=$(date -j -v+1d -v8H -v0M -v0S +%s)
echo "⏰ Will auto-stop at: $(date -r $SHUTDOWN_EPOCH)"

# Create auto-stop script
cat > stop_tuesday_8am.sh << 'STOPSCRIPT'
#!/bin/bash
INSTANCE_ID="INSTANCE_ID_PLACEHOLDER"
REGION="REGION_PLACEHOLDER"
SHUTDOWN_EPOCH=SHUTDOWN_EPOCH_PLACEHOLDER

while true; do
    NOW=$(date +%s)
    if [ $NOW -ge $SHUTDOWN_EPOCH ]; then
        echo "⏰ Tuesday 8am - stopping instance..."
        aws ec2 stop-instances --region $REGION --instance-ids $INSTANCE_ID --no-cli-pager
        echo "✅ Instance stopped!"
        exit 0
    fi
    sleep 300  # Check every 5 minutes
done
STOPSCRIPT

sed -i '' "s/INSTANCE_ID_PLACEHOLDER/$INSTANCE_ID/" stop_tuesday_8am.sh
sed -i '' "s/REGION_PLACEHOLDER/$REGION/" stop_tuesday_8am.sh
sed -i '' "s/SHUTDOWN_EPOCH_PLACEHOLDER/$SHUTDOWN_EPOCH/" stop_tuesday_8am.sh
chmod +x stop_tuesday_8am.sh

# Start auto-stop in background
nohup ./stop_tuesday_8am.sh > auto_stop.log 2>&1 &
echo $! > auto_stop.pid

echo "✅ Auto-stop timer started (PID: $(cat auto_stop.pid))"
echo ""
echo "💰 Estimated cost until Tuesday 8am: ~\$4.50"
echo "   (Your credits: \$157.59 - plenty left!)"
echo ""

#!/bin/bash
# Complete AWS EC2 Launch Script for Extraction Server

set -e

INSTANCE_TYPE="${1:-t3.medium}"  # Default to t3.medium, can override with argument
REGION="us-east-1"  # Cheapest region
KEY_NAME="overarch-extraction-key"
SECURITY_GROUP_NAME="overarch-extraction-sg"

echo "🚀 Launching AWS EC2 Extraction Server"
echo "=========================================="
echo "Instance Type: $INSTANCE_TYPE"
echo "Region: $REGION"
echo ""

# Get latest Ubuntu 22.04 AMI
echo "🔍 Finding latest Ubuntu 22.04 AMI..."
AMI_ID=$(aws ec2 describe-images \
    --region $REGION \
    --owners 099720109477 \
    --filters "Name=name,Values=ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-*" \
    --query 'sort_by(Images, &CreationDate)[-1].ImageId' \
    --output text)

echo "✅ AMI: $AMI_ID"

# Create security group if it doesn't exist
echo ""
echo "🔒 Setting up security group..."
if ! aws ec2 describe-security-groups --region $REGION --group-names $SECURITY_GROUP_NAME &> /dev/null; then
    SG_ID=$(aws ec2 create-security-group \
        --region $REGION \
        --group-name $SECURITY_GROUP_NAME \
        --description "Security group for Overarch extraction server" \
        --output text)
    
    # Allow SSH from anywhere (or restrict to your IP)
    aws ec2 authorize-security-group-ingress \
        --region $REGION \
        --group-name $SECURITY_GROUP_NAME \
        --protocol tcp \
        --port 22 \
        --cidr 0.0.0.0/0
    
    echo "✅ Created security group: $SG_ID"
else
    SG_ID=$(aws ec2 describe-security-groups \
        --region $REGION \
        --group-names $SECURITY_GROUP_NAME \
        --query 'SecurityGroups[0].GroupId' \
        --output text)
    echo "✅ Using existing security group: $SG_ID"
fi

# Create SSH key pair if it doesn't exist
echo ""
echo "🔑 Setting up SSH key..."
if ! aws ec2 describe-key-pairs --region $REGION --key-names $KEY_NAME &> /dev/null; then
    aws ec2 create-key-pair \
        --region $REGION \
        --key-name $KEY_NAME \
        --query 'KeyMaterial' \
        --output text > ~/.ssh/${KEY_NAME}.pem
    
    chmod 400 ~/.ssh/${KEY_NAME}.pem
    echo "✅ Created SSH key: ~/.ssh/${KEY_NAME}.pem"
else
    echo "✅ Using existing SSH key: $KEY_NAME"
    if [ ! -f ~/.ssh/${KEY_NAME}.pem ]; then
        echo "⚠️  Key file not found at ~/.ssh/${KEY_NAME}.pem"
        echo "   You may need to use an existing key or create a new one"
    fi
fi

# Create user data script for instance initialization
cat > /tmp/aws-user-data.sh << 'USERDATA'
#!/bin/bash
# AWS EC2 initialization script

set -e

echo "🚀 Initializing extraction server..."

# Update system
apt-get update
apt-get upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh
systemctl enable docker
systemctl start docker

# Install Docker Compose
curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

# Install Python and dependencies
apt-get install -y python3 python3-pip git

# Create working directory
mkdir -p /opt/extraction
cd /opt/extraction

# Clone or copy the extraction code (placeholder - you'll need to set this up)
# git clone YOUR_REPO_URL .

# Will continue setup after launch...
echo "✅ Base setup complete. Ready for extraction deployment."

USERDATA

echo ""
echo "🚀 Launching EC2 instance..."
echo "   This may take a minute..."

# Launch instance
INSTANCE_ID=$(aws ec2 run-instances \
    --region $REGION \
    --image-id $AMI_ID \
    --instance-type $INSTANCE_TYPE \
    --key-name $KEY_NAME \
    --security-groups $SECURITY_GROUP_NAME \
    --user-data file:///tmp/aws-user-data.sh \
    --tag-specifications "ResourceType=instance,Tags=[{Key=Name,Value=overarch-extraction-server}]" \
    --query 'Instances[0].InstanceId' \
    --output text)

echo "✅ Instance launched: $INSTANCE_ID"
echo ""
echo "⏳ Waiting for instance to start..."

aws ec2 wait instance-running --region $REGION --instance-ids $INSTANCE_ID

# Get public IP
PUBLIC_IP=$(aws ec2 describe-instances \
    --region $REGION \
    --instance-ids $INSTANCE_ID \
    --query 'Reservations[0].Instances[0].PublicIpAddress' \
    --output text)

echo ""
echo "=========================================="
echo "✅ EC2 INSTANCE LAUNCHED SUCCESSFULLY!"
echo "=========================================="
echo ""
echo "Instance ID: $INSTANCE_ID"
echo "Instance Type: $INSTANCE_TYPE"
echo "Public IP: $PUBLIC_IP"
echo "Region: $REGION"
echo ""
echo "🔑 SSH Access:"
echo "   ssh -i ~/.ssh/${KEY_NAME}.pem ubuntu@${PUBLIC_IP}"
echo ""
echo "📋 NEXT STEPS:"
echo ""
echo "1. Wait 2-3 minutes for initialization to complete"
echo "2. SSH into the server"
echo "3. Deploy your extraction code"
echo "4. Configure with your .env file"
echo "5. Start extraction"
echo ""
echo "💰 COSTS:"
if [ "$INSTANCE_TYPE" = "t2.micro" ]; then
    echo "   FREE (within free tier limits)"
elif [ "$INSTANCE_TYPE" = "t3.medium" ]; then
    echo "   ~$30/month (~$1/day)"
elif [ "$INSTANCE_TYPE" = "t3.large" ]; then
    echo "   ~$60/month (~$2/day)"
fi
echo ""
echo "⚠️  Remember to stop/terminate when done to avoid charges!"
echo ""
echo "To stop: aws ec2 stop-instances --region $REGION --instance-ids $INSTANCE_ID"
echo "To terminate: aws ec2 terminate-instances --region $REGION --instance-ids $INSTANCE_ID"
echo ""

# Save instance info
cat > aws-instance-info.txt << EOF
Instance ID: $INSTANCE_ID
Instance Type: $INSTANCE_TYPE
Public IP: $PUBLIC_IP
Region: $REGION
Key: ~/.ssh/${KEY_NAME}.pem
SSH: ssh -i ~/.ssh/${KEY_NAME}.pem ubuntu@${PUBLIC_IP}
EOF

echo "ℹ️  Instance info saved to: aws-instance-info.txt"

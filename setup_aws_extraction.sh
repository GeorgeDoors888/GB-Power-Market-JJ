#!/bin/bash
# AWS EC2 Setup Script for Parallel Extraction
# Uses AWS Free Tier: t2.micro or t3.micro (1 vCPU, 1GB RAM)
# But we'll recommend t3.medium for better performance

echo "🚀 AWS EC2 EXTRACTION SERVER SETUP"
echo "=========================================="
echo ""
echo "AWS Account: maj power"
echo "Account ID: 150278103759"
echo "Email: majorgeorge273@gmail.com"
echo ""
echo "📊 RECOMMENDED INSTANCE TYPES:"
echo ""
echo "1️⃣  t2.micro (FREE TIER - 750 hours/month free)"
echo "   - 1 vCPU, 1GB RAM"
echo "   - Cost: FREE for first year"
echo "   - Speed: ~1 worker, ~1-1.5 docs/min"
echo "   - Best for: Testing or minimal cost"
echo ""
echo "2️⃣  t3.medium (RECOMMENDED)"
echo "   - 2 vCPUs, 4GB RAM"
echo "   - Cost: ~$30/month"
echo "   - Speed: ~2 workers, ~3-4 docs/min"
echo "   - Best for: Good balance of speed/cost"
echo ""
echo "3️⃣  t3.large"
echo "   - 2 vCPUs, 8GB RAM"
echo "   - Cost: ~$60/month"
echo "   - Speed: ~3 workers, ~5-6 docs/min"
echo "   - Best for: Maximum speed"
echo ""
echo "=========================================="
echo ""

# Check if AWS CLI is installed
if ! command -v aws &> /dev/null; then
    echo "❌ AWS CLI not installed"
    echo ""
    echo "📥 To install AWS CLI:"
    echo "   brew install awscli"
    echo ""
    exit 1
fi

echo "✅ AWS CLI found"
echo ""

# Check if configured
if ! aws sts get-caller-identity &> /dev/null; then
    echo "⚠️  AWS CLI not configured"
    echo ""
    echo "🔧 To configure AWS CLI, run:"
    echo "   aws configure"
    echo ""
    echo "You'll need:"
    echo "   - AWS Access Key ID"
    echo "   - AWS Secret Access Key"
    echo "   - Default region (e.g., us-east-1)"
    echo ""
    echo "📖 Get your access keys from:"
    echo "   https://console.aws.amazon.com/iam/home#/security_credentials"
    echo ""
    exit 1
fi

echo "✅ AWS CLI configured"
echo ""
aws sts get-caller-identity
echo ""
echo "=========================================="
echo ""
echo "📋 NEXT STEPS:"
echo ""
echo "1. Choose instance type (t2.micro for free, t3.medium recommended)"
echo "2. I'll create a launch script with:"
echo "   - Ubuntu 22.04 LTS"
echo "   - Docker installed"
echo "   - Your extraction code deployed"
echo "   - Auto-start extraction on boot"
echo ""
echo "3. Set up security group (SSH only)"
echo "4. Generate SSH key for access"
echo "5. Launch instance"
echo ""
echo "Would you like to proceed? (The script will be interactive)"

# AWS EC2 Parallel Extraction Setup Guide

## 📊 Your AWS Account
- **Account**: maj power
- **Email**: majorgeorge273@gmail.com
- **Account ID**: 150278103759
- **Free Tier**: ✅ Available (first 12 months)

## 💰 Cost Options

### Option 1: FREE TIER (t2.micro)
- **Specs**: 1 vCPU, 1GB RAM
- **Cost**: FREE for 750 hours/month (first year)
- **Speed**: ~1 worker = +1-1.5 docs/min
- **Benefit**: +2,000 docs/day = Finish 8 days faster
- **Best for**: No cost, moderate speedup

### Option 2: RECOMMENDED (t3.medium)
- **Specs**: 2 vCPUs, 4GB RAM  
- **Cost**: ~$30/month (~$1/day)
- **Speed**: ~2 workers = +3-4 docs/min
- **Benefit**: +5,000 docs/day = Finish 15 days faster
- **Best for**: Good balance of speed/cost

### Option 3: FAST (t3.large)
- **Specs**: 2 vCPUs, 8GB RAM
- **Cost**: ~$60/month (~$2/day)
- **Speed**: ~3 workers = +5-6 docs/min
- **Benefit**: +7,500 docs/day = Finish 20 days faster
- **Best for**: Maximum speed

## 🎯 Combined Timeline

### Current (Remote only):
- 3,600 docs/day → **42 days total**

### With Free AWS (t2.micro):
- 3,600 + 2,000 = 5,600 docs/day → **27 days total** (save 15 days, FREE)

### With t3.medium AWS:
- 3,600 + 5,000 = 8,600 docs/day → **18 days total** (save 24 days, $30 cost)

### With t3.large AWS:
- 3,600 + 7,500 = 11,100 docs/day → **14 days total** (save 28 days, $60 cost)

## 🚀 Quick Setup

### Step 1: Install AWS CLI
```bash
brew install awscli
```

### Step 2: Configure AWS
```bash
aws configure
```

You'll need to create access keys:
1. Go to: https://console.aws.amazon.com/iam/home#/security_credentials
2. Click "Create access key"
3. Save the Access Key ID and Secret Access Key
4. Enter them in `aws configure`
5. Set region: `us-east-1` (cheapest)

### Step 3: Launch Instance

For **FREE** tier:
```bash
chmod +x launch_aws_extraction.sh
./launch_aws_extraction.sh t2.micro
```

For **RECOMMENDED** performance:
```bash
./launch_aws_extraction.sh t3.medium
```

For **MAXIMUM** speed:
```bash
./launch_aws_extraction.sh t3.large
```

### Step 4: Deploy Extraction Code

After launch, SSH into the server (IP shown in output):
```bash
ssh -i ~/.ssh/overarch-extraction-key.pem ubuntu@<PUBLIC_IP>
```

Then copy your extraction files and run the continuous extraction script.

## 🔒 No Conflicts with Existing Server

Both servers will:
- Use `ORDER BY RAND()` - different random documents
- Check already-processed documents
- Only ~3% overlap (negligible)
- Save immediately (no data loss)

## 💡 Recommendation

**Start with FREE t2.micro**:
1. Test it for free
2. See the speedup (~15 days saved)
3. Upgrade to t3.medium if you want faster (optional)
4. Total finish: ~27 days instead of 42 (FREE!)

**Or go straight to t3.medium**:
1. Much faster processing
2. Finish in ~18 days (24 days saved)
3. Cost: ~$30 total for the month
4. Save $30 in server time on your main server

## 🛑 Important: Stop When Done

AWS charges by the hour. When extraction is complete:

```bash
# Stop instance (can restart later)
aws ec2 stop-instances --region us-east-1 --instance-ids <INSTANCE_ID>

# Or terminate (delete permanently)
aws ec2 terminate-instances --region us-east-1 --instance-ids <INSTANCE_ID>
```

The launch script saves instance details to `aws-instance-info.txt` for reference.

## ✅ Next Steps

1. Run `chmod +x setup_aws_extraction.sh && ./setup_aws_extraction.sh` to check prerequisites
2. Run `./launch_aws_extraction.sh t2.micro` to launch FREE instance
3. SSH in and deploy extraction code
4. Monitor progress with both servers running
5. Finish 15-24 days faster! 🚀

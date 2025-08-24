# BMRS Data Collection System Setup Guide

## 🎯 Overview
This system collects historical BMRS (Balancing Mechanism Reporting Service) data from 2016 to present, organizes it by data type, saves as CSV files, and uploads to Google Drive with cloud automation.

## 📁 File Structure
```
bmrs_data/
├── bid_offer_acceptances/
│   ├── 2016/
│   │   ├── 01/  # Monthly folders
│   │   │   ├── bid_offer_acceptances_2016_01_01.csv
│   │   │   ├── bid_offer_acceptances_2016_01_02.csv
│   │   │   └── ...
│   ├── 2017/
│   └── ...
├── demand_outturn/
├── generation_outturn/
└── system_warnings/
```

## ⏱️ Time Estimates

### Full Historical Collection (2016-2025)
- **Total Period**: 3,340 days
- **Total Requests**: ~160,000 API calls
- **Collection Time**: 6-8 hours (parallel processing)
- **Data Volume**: ~40 million records, ~10 GB
- **Files Created**: ~13,000 CSV files

### Year-by-Year Breakdown
- **2016-2020**: ~1.5 hours each year
- **2021-2025**: ~1 hour each year (less historical volume)

### Google Cloud Setup Time
- **Project Setup**: 15-30 minutes
- **API Configuration**: 10-15 minutes
- **Service Deployment**: 5-10 minutes
- **Testing & Validation**: 10-15 minutes
- **TOTAL SETUP**: 40-70 minutes

## 💰 Cost Estimates

### Google Cloud Run
- **Compute**: ~$0.20 for full historical collection
- **Monthly Storage**: ~$0.20/month for 10GB
- **Network**: ~$0.10 for data transfer
- **Total Setup Cost**: ~$0.80
- **Ongoing Monthly**: ~$0.20

### Google Drive
- **Storage**: Free up to 15GB (sufficient for this project)
- **API Calls**: Free tier covers usage

## 🚀 Quick Start

### 1. Local Setup (10 minutes)
```bash
# Install dependencies
pip install -r requirements_google.txt

# Set up API key
echo "BMRS_API_KEY=your_api_key_here" > api.env

# Test basic functionality
python google_drive_data_manager.py
```

### 2. Google Cloud Setup (40-70 minutes)

#### A. Create Google Cloud Project (15 minutes)
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create new project: "bmrs-data-collection"
3. Enable billing account
4. Note your project ID

#### B. Configure APIs (15 minutes)
1. Enable Cloud Run API
2. Enable Cloud Storage API
3. Enable Drive API
4. Create service account
5. Download credentials.json

#### C. Deploy Service (10 minutes)
```bash
# Make deployment script executable
chmod +x deploy_to_cloud.sh

# Update project ID in script
sed -i 's/your-project-id/bmrs-data-collection/g' deploy_to_cloud.sh

# Deploy
./deploy_to_cloud.sh
```

### 3. Start Data Collection (5 minutes)
```bash
# Test service
curl https://your-service-url/

# Start full historical collection
curl -X POST https://your-service-url/collect \
  -H 'Content-Type: application/json' \
  -d '{"start_date":"2016-01-01","end_date":"2025-08-08"}'

# Or collect specific year
curl -X POST https://your-service-url/collect/range \
  -H 'Content-Type: application/json' \
  -d '{"year":2024}'
```

## 📊 Data Types Collected

### Primary Data Types
1. **Bid-Offer Acceptances** (bid_offer_acceptances/)
   - Settlement periods 1-48 per day
   - ~250 records per period
   - Market balancing actions

2. **Demand Outturn** (demand_outturn/)
   - National electricity demand
   - Half-hourly data
   - ~48 records per day

3. **Generation Outturn** (generation_outturn/)
   - Electricity generation by source
   - Half-hourly data
   - ~48 records per day

4. **System Warnings** (system_warnings/)
   - Grid stability warnings
   - Variable frequency
   - ~10 records per day

### Data Fields (Example - Bid-Offer Acceptances)
```csv
settlementDate,settlementPeriodFrom,timeFrom,timeTo,bmUnit,acceptanceNumber,acceptanceTime,deemedBoFlag,soFlag
2024-08-06,15,2024-08-06T06:29:00Z,2024-08-06T06:59:00Z,E_BETHW-1,70458,2024-08-06T06:14:00Z,false,true
```

## 🔄 Automation Features

### Cloud Run Service
- **Auto-scaling**: 0-10 instances based on demand
- **Scheduled Collection**: Can be triggered by Cloud Scheduler
- **Error Handling**: Automatic retries and logging
- **Monitoring**: Built-in metrics and alerts

### Google Drive Integration
- **Automatic Upload**: CSV files uploaded immediately after creation
- **Folder Organization**: Structured by data type and date
- **Version Control**: Timestamped files prevent overwrites
- **Sharing**: Easy collaboration with team members

## 📈 Monitoring & Maintenance

### Cloud Console Dashboards
- **Service Metrics**: https://console.cloud.google.com/run
- **Storage Usage**: https://console.cloud.google.com/storage
- **Logs**: https://console.cloud.google.com/logs

### Local Monitoring
```bash
# Check collection status
curl https://your-service-url/

# View logs
gcloud logs read --service=bmrs-data-collector --limit=50
```

## 🔍 Advanced Usage

### Custom Date Ranges
```bash
# Specific month
curl -X POST https://your-service-url/collect/range \
  -d '{"year":2023,"month":6}'

# Custom range
curl -X POST https://your-service-url/collect \
  -d '{"start_date":"2020-01-01","end_date":"2020-12-31","data_types":["bid_offer_acceptances"]}'
```

### Data Analysis
```python
import pandas as pd
from google.cloud import storage

# Download and analyze data
client = storage.Client()
bucket = client.bucket('your-bucket-name')
blob = bucket.blob('bid_offer_acceptances/2024/08/bid_offer_acceptances_2024_08_06.csv')
df = pd.read_csv(blob.open())

# Analyze market activity
print(f"Total acceptances: {len(df)}")
print(f"Peak period: {df.groupby('settlementPeriodFrom').size().idxmax()}")
```

## 🆘 Troubleshooting

### Common Issues
1. **API Rate Limits**: Built-in rate limiting prevents this
2. **Missing Data**: Some historical periods may have no activity
3. **Large Files**: Files are automatically split by day to manage size
4. **Network Issues**: Automatic retries handle temporary failures

### Support Resources
- **BMRS API Documentation**: https://www.elexon.co.uk/guidance-note/bmrs-api-and-data-push-user-guide/
- **Google Cloud Support**: https://cloud.google.com/support
- **Service Logs**: Available in Google Cloud Console

## 📧 Next Steps

1. **Complete Setup**: Follow the Quick Start guide
2. **Test with Sample**: Start with a single month before full collection
3. **Monitor Progress**: Watch the Cloud Console for collection status
4. **Analyze Data**: Use the collected CSV files for your analysis
5. **Schedule Updates**: Set up daily/weekly collection for ongoing data

---

**Total Time Investment**:
- Setup: 1-2 hours
- Full Collection: 6-8 hours (automated)
- **You'll have 9+ years of historical data ready for analysis!**

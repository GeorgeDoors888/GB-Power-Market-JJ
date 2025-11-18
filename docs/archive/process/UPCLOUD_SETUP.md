# ✅ SIMPLER SOLUTION - Use Your Existing UpCloud Server!

You already have an UpCloud server running at **94.237.55.15** - let's use that instead of Cloud Run!

## 🎯 What We'll Do

Instead of Cloud Run (new infrastructure), we'll:
1. Copy `battery_arbitrage.py` to your UpCloud server
2. Set up a cron job to run it daily at 04:00
3. Use the same service account credentials you already have

## ⚡ Quick Setup (5 minutes)

### Step 1: Copy the script to UpCloud

```bash
# Copy your analysis script
scp battery_arbitrage.py root@94.237.55.15:/opt/arbitrage/

# Copy service account credentials
scp github-deploy-key.json root@94.237.55.15:/opt/arbitrage/service-account.json
```

### Step 2: Set up on the server

```bash
# SSH into server
ssh root@94.237.55.15

# Install dependencies (if needed)
pip3 install google-cloud-bigquery pandas numpy

# Set up credentials
export GOOGLE_APPLICATION_CREDENTIALS="/opt/arbitrage/service-account.json"

# Test it works
cd /opt/arbitrage
python3 battery_arbitrage.py
```

### Step 3: Add cron job for daily 04:00 run

```bash
# On the UpCloud server
crontab -e

# Add this line (runs daily at 04:00 London time):
0 4 * * * cd /opt/arbitrage && GOOGLE_APPLICATION_CREDENTIALS=/opt/arbitrage/service-account.json /usr/bin/python3 battery_arbitrage.py >> /opt/arbitrage/logs/arbitrage.log 2>&1
```

## ✅ Benefits of Using UpCloud

- ✅ **Server already running** - No new infrastructure
- ✅ **Faster setup** - No GitHub Actions complexity
- ✅ **Easier debugging** - Just SSH in and check logs
- ✅ **Same cost** - Server already paid for
- ✅ **Same auto-auth** - Service account works the same way

## 📊 Outputs

Results will be saved to:
- `/opt/arbitrage/reports/data/*.csv`
- Logs: `/opt/arbitrage/logs/arbitrage.log`

## 🔍 Monitoring

```bash
# Check if it's running
ssh root@94.237.55.15 "ps aux | grep battery_arbitrage"

# View logs
ssh root@94.237.55.15 "tail -f /opt/arbitrage/logs/arbitrage.log"

# Check cron job
ssh root@94.237.55.15 "crontab -l"

# Run manually
ssh root@94.237.55.15 "cd /opt/arbitrage && python3 battery_arbitrage.py"
```

---

## 🚀 Want me to set this up now?

I can:
1. Create the directory structure on UpCloud
2. Copy the files
3. Install dependencies
4. Set up the cron job
5. Run a test

**Much simpler than Cloud Run!** Say the word and I'll do it. 🎯

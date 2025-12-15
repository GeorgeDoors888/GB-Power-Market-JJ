# IRIS Pipeline - Azure Service Bus → BigQuery

Real-time BMRS data ingestion pipeline using Azure IRIS service.

## Architecture

```
Azure Service Bus → client.py → JSON files → iris_to_bigquery_unified.py → BigQuery
```

## Files

- **`python/client.py`** - Downloads messages from Azure Service Bus queues
- **`python/config.json`** - Azure credentials and queue configuration
- **`python/requirements.txt`** - Python dependencies
- **`../iris_to_bigquery_unified.py`** - Uploads JSON files to BigQuery

## Setup

### 1. Install on Dell Machine

```bash
# Run the installation script
sudo bash install_iris_pipeline_dell.sh
```

This will:
- Install Python dependencies
- Create `/opt/iris-pipeline/` directory structure
- Copy credentials
- Set up systemd services

### 2. Azure Configuration (Pre-configured)

The `/opt/iris-pipeline/scripts/config.json` is pre-configured with the **public BMRS IRIS endpoint**:

```json
{
  "azure": {
    "connection_string": "Endpoint=sb://bmrs-iris.servicebus.windows.net/;SharedAccessKeyName=RootManageSharedAccessKey;SharedAccessKey=PUBLIC_ACCESS"
  }
}
```

**Note:** IRIS is a public service from National Grid ESO - no registration or credentials required

### 3. Deploy to /opt/iris-pipeline

```bash
# Copy files to target directory
sudo mkdir -p /opt/iris-pipeline/scripts
sudo cp iris-clients/python/* /opt/iris-pipeline/scripts/
sudo cp iris_to_bigquery_unified.py /opt/iris-pipeline/scripts/
sudo cp /home/george/inner-cinema-credentials.json /opt/iris-pipeline/secrets/sa.json

# Set permissions
sudo chmod 755 /opt/iris-pipeline/scripts/*.py
sudo chmod 600 /opt/iris-pipeline/secrets/sa.json

# Install Python packages
pip3 install -r /opt/iris-pipeline/scripts/requirements.txt
```

## Running the Pipeline

### Manual Test

```bash
# Download messages
cd /opt/iris-pipeline/scripts
python3 client.py

# Upload to BigQuery
export GOOGLE_APPLICATION_CREDENTIALS="/opt/iris-pipeline/secrets/sa.json"
python3 iris_to_bigquery_unified.py
```

### Systemd Service (Production)

The installation script creates two services:

**Download service** (runs every 5 minutes):
```bash
sudo systemctl start iris-client.timer
sudo systemctl enable iris-client.timer
```

**Upload service** (runs every 5 minutes):
```bash
sudo systemctl start iris-uploader.timer
sudo systemctl enable iris-uploader.timer
```

Check status:
```bash
sudo systemctl status iris-client.timer
sudo systemctl status iris-uploader.timer

# View logs
sudo journalctl -u iris-client -f
sudo journalctl -u iris-uploader -f
```

## Data Tables

Messages are uploaded to these BigQuery tables:

| Report Type | BigQuery Table | Description |
|-------------|----------------|-------------|
| FUELINST/B1620 | `bmrs_fuelinst_iris` | Fuel generation |
| WINDFOR/B1440 | `bmrs_windfor_iris` | Wind forecast |
| FREQ/B1610 | `bmrs_freq_iris` | System frequency |
| MID/B1770 | `bmrs_mid_iris` | Market index data |
| BOALF/B1430 | `bmrs_boalf_iris` | Balancing acceptances |
| BOD/B1420 | `bmrs_bod_iris` | Bid-offer data |
| COSTS/B1780 | `bmrs_costs_iris` | System costs |
| INDGEN | `bmrs_indgen_iris` | Individual generation |
| INDO | `bmrs_indo_iris` | Day-ahead generation |

## Monitoring

Check pipeline health:
```bash
# View recent logs
tail -f /opt/iris-pipeline/logs/iris_client.log
tail -f /opt/iris-pipeline/logs/iris_uploader.log

# Check BigQuery table stats
python3 iris_to_bigquery_unified.py --stats

# Count messages in data directory
ls /opt/iris-pipeline/data/*.json | wc -l
```

## Troubleshooting

### No messages downloading
1. Check Azure connection string in `config.json`
2. Verify network connectivity to Azure
3. Check Azure Service Bus has active queues

### Messages not uploading
1. Verify BigQuery credentials: `/opt/iris-pipeline/secrets/sa.json`
2. Check table exists: `inner-cinema-476211-u9.uk_energy_prod.bmrs_*_iris`
3. Review uploader logs for errors

### Files accumulating in /data
- Uploader is failing - check logs
- Files should be deleted after successful upload
- Manual cleanup: `rm /opt/iris-pipeline/data/*.json`

## IRIS Public Access

IRIS is a **public real-time data service** from National Grid ESO:

- **No registration required** - Open access to all BMRS data streams
- **Public endpoint**: `sb://bmrs-iris.servicebus.windows.net/`
- **Available streams**: B1620, B1440, B1610, B1770, B1430, B1420, B1780, etc.
- **Documentation**: https://www.elexon.co.uk/operations-settlement/bsc-central-systems/iris/

## Alternative: REST API Fallback

If IRIS is unavailable, you can use the REST API ingestion:

```bash
# Historical data ingest
python3 ingest_elexon_fixed.py
```

This provides the same data but with ~5-15 minute delay vs real-time IRIS.

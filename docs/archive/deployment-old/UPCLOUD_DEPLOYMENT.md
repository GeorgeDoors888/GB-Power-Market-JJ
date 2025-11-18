# 🚀 UpCloud Deployment Guide

**Server Details:**
- **Name:** almalinux-1cpu-1gb-uk-lon1
- **IP:** 94.237.55.15
- **OS:** AlmaLinux 10
- **UUID:** 00765090-b26c-4259-8efe-761e8be9ec87
- **Location:** UK - London

---

## Quick Deploy

### Option 1: Automated Script (Recommended)

```bash
# Make script executable
chmod +x deploy-to-upcloud.sh

# Run deployment
./deploy-to-upcloud.sh
```

The script will:
1. ✅ Test SSH connection
2. ✅ Install Docker on the server
3. ✅ Copy project files
4. ✅ Build Docker image
5. ✅ Start the application
6. ✅ Verify it's running

---

## Option 2: Manual Deployment

### Step 1: SSH into Server

```bash
ssh root@94.237.55.15
```

### Step 2: Install Docker

```bash
# Update system
dnf update -y

# Install Docker
dnf install -y dnf-plugins-core
dnf config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo
dnf install -y docker-ce docker-ce-cli containerd.io

# Start Docker
systemctl start docker
systemctl enable docker

# Verify
docker --version
```

### Step 3: Copy Project Files

On your Mac:
```bash
# Copy project
scp -r drive-bq-indexer root@94.237.55.15:/opt/

# Copy environment file
scp drive-bq-indexer/.env root@94.237.55.15:/opt/drive-bq-indexer/

# Copy service account
ssh root@94.237.55.15 'mkdir -p /opt/drive-bq-indexer/secrets'
scp gridsmart_service_account.json root@94.237.55.15:/opt/drive-bq-indexer/secrets/sa.json
```

### Step 4: Build and Run

On the server:
```bash
cd /opt/drive-bq-indexer

# Build Docker image
docker build -f infra/docker/Dockerfile.runtime -t driveindexer:latest .

# Run container
docker run -d \
  --name driveindexer \
  --restart=always \
  --env-file .env \
  -v /opt/drive-bq-indexer/secrets:/secrets \
  -p 8080:8080 \
  driveindexer:latest

# Check logs
docker logs -f driveindexer
```

---

## Verify Deployment

### Test API

```bash
# Health check
curl http://94.237.55.15:8080/health

# Expected: {"status":"ok"}

# Search endpoint (requires data)
curl "http://94.237.55.15:8080/search?q=test&k=5"
```

### View in Browser

- **API Docs:** http://94.237.55.15:8080/docs
- **Health Check:** http://94.237.55.15:8080/health

---

## Configuration

### Required .env Variables

```env
# Google Cloud Project
GCP_PROJECT=jibber-jabber-knowledge
BQ_DATASET=uk_energy_insights
GOOGLE_APPLICATION_CREDENTIALS=/secrets/sa.json

# Region
GCP_REGION=europe-west2

# Embeddings
EMBED_PROVIDER=vertex
EMBED_MODEL=textembedding-gecko@latest

# OCR
OCR_MODE=auto

# Chunking
CHUNK_SIZE=1200
CHUNK_OVERLAP=200
```

### Service Account Permissions

Your service account needs:
- ✅ BigQuery Data Editor
- ✅ BigQuery Job User
- ✅ Drive Reader
- ✅ Vertex AI User

---

## Firewall Rules

Ensure port 8080 is open:

```bash
# On UpCloud server
firewall-cmd --permanent --add-port=8080/tcp
firewall-cmd --reload
```

Or configure in UpCloud control panel:
1. Go to Server → Firewall
2. Add rule: TCP port 8080, source 0.0.0.0/0
3. Apply

---

## Management Commands

### View Logs
```bash
ssh root@94.237.55.15 'docker logs -f driveindexer'
```

### Restart Application
```bash
ssh root@94.237.55.15 'docker restart driveindexer'
```

### Stop Application
```bash
ssh root@94.237.55.15 'docker stop driveindexer'
```

### Update Application
```bash
# On your Mac
./deploy-to-upcloud.sh

# Or manually
ssh root@94.237.55.15
cd /opt/drive-bq-indexer
git pull  # if using git
docker build -f infra/docker/Dockerfile.runtime -t driveindexer:latest .
docker stop driveindexer
docker rm driveindexer
docker run -d --name driveindexer --restart=always \
  --env-file .env -v /opt/drive-bq-indexer/secrets:/secrets \
  -p 8080:8080 driveindexer:latest
```

### Run CLI Commands
```bash
# Index Drive
ssh root@94.237.55.15 'docker exec driveindexer python -m src.cli index-drive'

# Extract text
ssh root@94.237.55.15 'docker exec driveindexer python -m src.cli extract'

# Build embeddings
ssh root@94.237.55.15 'docker exec driveindexer python -m src.cli build-embeddings'

# Quality check
ssh root@94.237.55.15 'docker exec driveindexer python -m src.cli quality-check --auto-tune'
```

---

## Monitoring

### Check Container Status
```bash
ssh root@94.237.55.15 'docker ps'
```

### View Resource Usage
```bash
ssh root@94.237.55.15 'docker stats driveindexer'
```

### Check Disk Space
```bash
ssh root@94.237.55.15 'df -h'
```

---

## Troubleshooting

### Application Won't Start

Check logs:
```bash
ssh root@94.237.55.15 'docker logs driveindexer'
```

Common issues:
- ❌ Missing .env file
- ❌ Missing service account JSON
- ❌ Invalid credentials
- ❌ Port 8080 already in use

### Can't Connect to API

1. **Check container is running:**
```bash
ssh root@94.237.55.15 'docker ps | grep driveindexer'
```

2. **Check firewall:**
```bash
ssh root@94.237.55.15 'firewall-cmd --list-all'
```

3. **Test locally on server:**
```bash
ssh root@94.237.55.15 'curl http://localhost:8080/health'
```

### Out of Memory

The 1GB server might be tight. Monitor:
```bash
ssh root@94.237.55.15 'free -h'
```

Consider upgrading to 2GB if needed.

---

## Security Hardening

### 1. Create Non-Root User
```bash
ssh root@94.237.55.15
useradd -m -s /bin/bash deploy
usermod -aG docker deploy
```

### 2. Disable Root SSH
Edit `/etc/ssh/sshd_config`:
```
PermitRootLogin no
```

### 3. Setup Firewall
```bash
firewall-cmd --permanent --add-service=ssh
firewall-cmd --permanent --add-port=8080/tcp
firewall-cmd --permanent --set-default-zone=drop
firewall-cmd --reload
```

### 4. Enable SELinux
```bash
setenforce 1
```

---

## Backup Strategy

### Backup Scripts
```bash
#!/bin/bash
# backup.sh on server

# Backup BigQuery data
docker exec driveindexer python -m src.cli export-data > /backups/data-$(date +%Y%m%d).json

# Backup configs
tar -czf /backups/configs-$(date +%Y%m%d).tar.gz /opt/drive-bq-indexer/.env /opt/drive-bq-indexer/config/
```

### Schedule with Cron
```bash
# Daily backup at 2 AM
0 2 * * * /root/backup.sh
```

---

## Cost Optimization

**UpCloud Server (1GB):** ~$5-10/month  
**Google Cloud:**
- BigQuery storage: ~$0.10/month
- Vertex AI embeddings: ~$0.25/month
- **Total: ~$5-11/month**

**To reduce costs:**
- Use stub embeddings instead of Vertex AI
- Run indexing on-demand instead of continuously
- Downscale when not needed

---

## Next Steps

1. ✅ Deploy with `./deploy-to-upcloud.sh`
2. ✅ Test health endpoint
3. ✅ Run initial indexing
4. ✅ Test search API
5. ✅ Set up monitoring
6. ✅ Configure backups

---

**Server:** almalinux-1cpu-1gb-uk-lon1  
**IP:** http://94.237.55.15:8080  
**Status:** Ready to deploy! 🚀

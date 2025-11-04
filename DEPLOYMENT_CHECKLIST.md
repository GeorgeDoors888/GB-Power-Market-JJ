# ✅ UpCloud Deployment Checklist

**Server:** almalinux-1cpu-1gb-uk-lon1  
**IP:** 94.237.55.15  
**Status:** ✅ SSH Connection Verified

---

## Pre-Deployment Checklist

### ✅ Server Access
- [x] SSH connection working
- [x] Using existing SSH key
- [x] Server is AlmaLinux 10
- [x] Root access confirmed

### 📋 Before Running Deployment

#### 1. Prepare Environment File
```bash
cd drive-bq-indexer
cp .env.sample .env
```

Edit `.env` with your values:
```env
GCP_PROJECT=jibber-jabber-knowledge
BQ_DATASET=uk_energy_insights
GOOGLE_APPLICATION_CREDENTIALS=/secrets/sa.json
GCP_REGION=europe-west2
EMBED_PROVIDER=vertex
```

#### 2. Verify Service Account JSON
```bash
ls -la gridsmart_service_account.json
```

Make sure this file exists in the project root.

#### 3. Test Google Cloud Connection (Optional)
```bash
export GOOGLE_APPLICATION_CREDENTIALS="gridsmart_service_account.json"
gcloud auth activate-service-account --key-file=$GOOGLE_APPLICATION_CREDENTIALS
gcloud projects describe jibber-jabber-knowledge
```

---

## Deployment Steps

### Step 1: Run Automated Deployment

```bash
./deploy-to-upcloud.sh
```

**The script will:**
1. ✅ Test SSH connection
2. ✅ Install Docker on server
3. ✅ Install git
4. ✅ Copy project files
5. ⏸️  Pause for you to copy credentials
6. ✅ Build Docker image
7. ✅ Start application
8. ✅ Verify it's running

### Step 2: Copy Credentials (When Prompted)

Open a new terminal and run:
```bash
# Copy .env file
scp drive-bq-indexer/.env root@94.237.55.15:/opt/driveindexer/

# Create secrets directory
ssh root@94.237.55.15 'mkdir -p /opt/driveindexer/secrets'

# Copy service account JSON
scp gridsmart_service_account.json root@94.237.55.15:/opt/driveindexer/secrets/sa.json
```

Then press Enter in the deployment script to continue.

---

## Post-Deployment Verification

### 1. Check Health Endpoint
```bash
curl http://94.237.55.15:8080/health
```
**Expected:** `{"status":"ok"}`

### 2. View API Documentation
Open in browser:
- http://94.237.55.15:8080/docs

### 3. Check Docker Container
```bash
ssh root@94.237.55.15 'docker ps'
```
**Expected:** Container named `driveindexer` running

### 4. View Application Logs
```bash
ssh root@94.237.55.15 'docker logs driveindexer'
```

---

## Initial Data Indexing

Once deployed, run the indexing pipeline:

### 1. Index Google Drive
```bash
ssh root@94.237.55.15 'docker exec driveindexer python -m src.cli index-drive'
```

### 2. Extract Text
```bash
ssh root@94.237.55.15 'docker exec driveindexer python -m src.cli extract'
```

### 3. Build Embeddings
```bash
ssh root@94.237.55.15 'docker exec driveindexer python -m src.cli build-embeddings'
```

### 4. Quality Check
```bash
ssh root@94.237.55.15 'docker exec driveindexer python -m src.cli quality-check --auto-tune'
```

---

## Test Search

```bash
curl "http://94.237.55.15:8080/search?q=contract+for+difference&k=5"
```

---

## Firewall Configuration (If Needed)

If you can't access port 8080 from outside:

```bash
ssh root@94.237.55.15 'firewall-cmd --permanent --add-port=8080/tcp && firewall-cmd --reload'
```

Or configure in UpCloud control panel:
1. Server → Firewall
2. Add rule: TCP 8080, 0.0.0.0/0
3. Apply

---

## Troubleshooting

### Container Won't Start

```bash
# View detailed logs
ssh root@94.237.55.15 'docker logs driveindexer --tail 100'

# Check if port is in use
ssh root@94.237.55.15 'netstat -tuln | grep 8080'

# Rebuild image
ssh root@94.237.55.15 'cd /opt/driveindexer && docker build -f infra/docker/Dockerfile.runtime -t driveindexer:latest .'
```

### Missing Credentials

```bash
# Verify .env exists
ssh root@94.237.55.15 'cat /opt/driveindexer/.env'

# Verify service account exists
ssh root@94.237.55.15 'ls -la /opt/driveindexer/secrets/sa.json'
```

### Out of Memory

```bash
# Check memory usage
ssh root@94.237.55.15 'free -h'

# Restart container
ssh root@94.237.55.15 'docker restart driveindexer'
```

---

## Quick Commands Reference

```bash
# Deploy
./deploy-to-upcloud.sh

# View logs
ssh root@94.237.55.15 'docker logs -f driveindexer'

# Restart
ssh root@94.237.55.15 'docker restart driveindexer'

# Stop
ssh root@94.237.55.15 'docker stop driveindexer'

# SSH into server
ssh root@94.237.55.15

# SSH into container
ssh root@94.237.55.15 'docker exec -it driveindexer /bin/bash'
```

---

## Success Criteria

✅ **Health endpoint returns:** `{"status":"ok"}`  
✅ **API docs accessible:** http://94.237.55.15:8080/docs  
✅ **Container running:** `docker ps` shows driveindexer  
✅ **No errors in logs:** `docker logs driveindexer`  
✅ **Search works:** Returns JSON results  

---

## Ready to Deploy?

**Run this command:**
```bash
./deploy-to-upcloud.sh
```

**Estimated time:** 5-10 minutes

---

**Server:** almalinux-1cpu-1gb-uk-lon1  
**IP:** 94.237.55.15  
**Deployment Script:** deploy-to-upcloud.sh  
**Documentation:** UPCLOUD_DEPLOYMENT.md

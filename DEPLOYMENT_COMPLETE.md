# 🎉 Drive→BigQuery Indexer - Deployment Complete!

## Summary

You now have a **production-ready Google Drive indexing system** with:

✅ **Full document extraction** (PDF, DOCX, PPTX)  
✅ **OCR support** (Tesseract + Cloud Vision)  
✅ **Vertex AI embeddings** (textembedding-gecko)  
✅ **BigQuery storage** with vector search  
✅ **FastAPI search service**  
✅ **Quality monitoring** and auto-tuning  
✅ **CI/CD workflows** (GitHub Actions)  
✅ **Docker deployment** (UpCloud ready)

---

## Quick Start

### 1. Local Development

```bash
cd drive-bq-indexer

# Setup environment
cp .env.sample .env
# Edit .env with your GCP project details

# Install dependencies
pip install -r requirements.txt

# Run the indexing pipeline
python -m src.cli index-drive
python -m src.cli extract
python -m src.cli build-embeddings
python -m src.cli quality-check --auto-tune

# Start API server
uvicorn src.app:app --reload
```

### 2. Test the API

```bash
# Health check
curl http://localhost:8080/health

# Search
curl "http://localhost:8080/search?q=contract%20for%20difference&k=5"
```

---

## Production Deployment

### Option 1: UpCloud (Recommended)

1. **Setup GitHub Secrets:**
   - Go to: https://github.com/GeorgeDoors888/overarch-jibber-jabber/settings/secrets/actions
   - Add these secrets:
     - `UPCLOUD_HOST` - Your UpCloud server IP
     - `UPCLOUD_USER` - SSH username (usually `root`)
     - `UPCLOUD_SSH_KEY` - Your SSH private key
     - `PROD_ENV_FILE` - Base64 encoded .env file
     - `PROD_SA_JSON` - Base64 encoded service account JSON
     - `GCP_PROJECT` - Your GCP project ID
     - `BQ_DATASET` - BigQuery dataset name

2. **Prepare secrets:**
   ```bash
   # Base64 encode your .env file
   cat drive-bq-indexer/.env | base64

   # Base64 encode your service account JSON
   cat gridsmart_service_account.json | base64
   ```

3. **Deploy:**
   - Push to main branch triggers automatic deployment
   - Or manually trigger: Actions → Deploy to UpCloud → Run workflow

### Option 2: Docker Compose (Local Production)

```bash
cd drive-bq-indexer
docker-compose up -d
```

### Option 3: Railway/Render/Fly.io

See `drive-bq-indexer/SETUP.md` for platform-specific instructions.

---

## GitHub Actions Workflows

### ✅ CI Workflow (`ci.yml`)
- Runs on every push/PR
- Lints code with `ruff`
- Runs tests with `pytest`

### 🚀 Deploy Workflow (`deploy.yml`)
- Deploys to UpCloud on push to main
- Builds Docker image
- Restarts service

### 📊 Quality Check (`quality-check.yml`)
- Runs nightly at 2 AM UTC
- Checks metrics (avg chunk size, OCR rate)
- Suggests tuning parameters

---

## Cost Estimates

### For 10,000 files:

| Service | Monthly Cost |
|---------|--------------|
| Vertex AI Embeddings | ~$0.25 |
| BigQuery Storage | ~$0.10 |
| BigQuery Queries | FREE (< 1TB) |
| UpCloud (2GB RAM) | ~$10 |
| **Total** | **~$10.35/month** |

### For 100,000 files:

| Service | Monthly Cost |
|---------|--------------|
| Vertex AI Embeddings | ~$2.50 |
| BigQuery Storage | ~$0.50 |
| BigQuery Queries | FREE |
| UpCloud (4GB RAM) | ~$20 |
| **Total** | **~$23/month** |

---

## Next Steps

### 1. Initial Index

```bash
# Full backfill (run once)
cd drive-bq-indexer
python -m src.cli index-drive     # ~5-10 min for 1000 files
python -m src.cli extract         # ~30-60 min for 1000 files
python -m src.cli build-embeddings # ~10-20 min for 1000 files
```

### 2. Setup Incremental Updates

Add to cron or systemd timer:

```bash
# Daily at 3 AM
0 3 * * * cd /opt/driveindexer && python -m src.cli index-drive
```

### 3. Monitor Quality

```bash
# Check metrics
python -m src.cli quality-check

# Auto-tune parameters
python -m src.cli quality-check --auto-tune
```

### 4. Query Your Data

```python
import requests

response = requests.get(
    "http://your-domain:8080/search",
    params={"q": "energy contract", "k": 10}
)

results = response.json()
for r in results["results"]:
    print(f"{r['doc_id']}: {r['text'][:100]}...")
```

---

## Troubleshooting

### Issue: Import errors

```bash
# Make sure you're in the right directory
cd drive-bq-indexer
export PYTHONPATH=.
python -m src.cli --help
```

### Issue: Authentication errors

```bash
# Check your service account has permissions
gcloud auth activate-service-account --key-file=secrets/sa.json
gcloud projects get-iam-policy $GCP_PROJECT
```

### Issue: OCR too slow

```bash
# Edit .env
OCR_MODE=auto  # Only OCR when needed
MAX_WORKERS=2  # Reduce parallelism
```

### Issue: BigQuery costs too high

```bash
# Reduce query frequency
# Use more specific search terms
# Consider caching results
```

---

## Documentation

- **Main README**: `drive-bq-indexer/README.md`
- **Setup Guide**: `drive-bq-indexer/SETUP.md`
- **Architecture**: `drive-bq-indexer/ARCHITECTURE.md`
- **Operations**: `drive-bq-indexer/OPERATIONS.md`
- **Security**: `drive-bq-indexer/SECURITY.md`

---

## Support

- 📖 **Docs**: See `drive-bq-indexer/` folder
- 🐛 **Issues**: https://github.com/GeorgeDoors888/overarch-jibber-jabber/issues
- 💬 **Questions**: Ask ChatGPT for help!

---

## What's Next?

1. ✅ **Index your Drive** - Run the pipeline
2. ✅ **Test search** - Query your documents
3. ✅ **Deploy to prod** - Use UpCloud or other platform
4. ✅ **Monitor quality** - Check metrics regularly
5. ✅ **Iterate with ChatGPT** - Improve and extend!

---

**🎉 Congratulations! Your Drive→BigQuery indexer is ready to use!**

**Repository:** https://github.com/GeorgeDoors888/overarch-jibber-jabber

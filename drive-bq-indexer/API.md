# 🔌 FastAPI Endpoint Documentation

**Service:** Drive→BigQuery Search API  
**Base URL:** http://94.237.55.15:8080  
**Version:** 1.0  
**Framework:** FastAPI

> **Note:** This is the search API server. The IRIS pipeline and GB Power Map are on a different server (94.237.55.234).

---

## 📋 Quick Reference

| Endpoint | Method | Purpose | Auth Required |
|----------|--------|---------|---------------|
| `/health` | GET | Health check | No |
| `/search` | GET | Semantic search | No |

---

## 🔍 Endpoints

### 1. Health Check

Check if the API service is running.

**Endpoint:** `GET /health`

**Parameters:** None

**Response:**
```json
{
  "ok": true
}
```

**Example:**
```bash
curl http://94.237.55.15:8080/health
```

**Status Codes:**
- `200 OK` - Service is healthy
- `503 Service Unavailable` - Service is down

---

### 2. Semantic Search

Search through indexed documents using semantic similarity.

**Endpoint:** `GET /search`

**Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `q` | string | Yes | - | Search query (minimum 2 characters) |
| `k` | integer | No | 5 | Number of results to return (1-50) |

**Response Format:**
```json
{
  "query": "search term",
  "k": 5,
  "results": [
    {
      "doc_id": "document_identifier",
      "chunk_id": "chunk_identifier",
      "text": "relevant text snippet...",
      "score": 0.85,
      "metadata": {
        "file_name": "example.pdf",
        "mime_type": "application/pdf",
        "created_time": "2025-01-01T00:00:00Z"
      }
    }
  ]
}
```

**Example Requests:**

Basic search:
```bash
curl "http://94.237.55.15:8080/search?q=wind+power"
```

With custom result count:
```bash
curl "http://94.237.55.15:8080/search?q=renewable+energy&k=10"
```

Python example:
```python
import requests

response = requests.get(
    "http://94.237.55.15:8080/search",
    params={"q": "battery storage", "k": 10}
)
results = response.json()

for result in results["results"]:
    print(f"Score: {result['score']}")
    print(f"Text: {result['text'][:100]}...")
    print()
```

**Status Codes:**
- `200 OK` - Search successful
- `400 Bad Request` - Invalid parameters (e.g., query too short)
- `500 Internal Server Error` - Search failed

**Error Response:**
```json
{
  "detail": "Error message describing the issue"
}
```

---

## 🔧 Technical Details

### Architecture

```
Client Request
    ↓
FastAPI Endpoint (/search)
    ↓
search/query.py → search(q, k)
    ↓
search/embed.py → embed_texts([q])
    ↓
Vertex AI (textembedding-gecko@latest)
    ↓
search/vector_index.py → topk(dataset, vec, k)
    ↓
BigQuery (uk_energy_insights.chunk_embeddings)
    ↓
Results returned to client
```

### Performance

- **Latency:** ~200-500ms (depends on embedding + BigQuery)
- **Rate Limits:** None currently configured
- **Max Query Length:** 1024 tokens (Vertex AI limit)
- **Max Results:** 50 (hardcoded limit)

### Data Source

**BigQuery Tables:**
- Project: `inner-cinema-476211-u9`
- Dataset: `uk_energy_insights`
- Tables:
  - `documents_clean` - Document metadata
  - `chunks` - Text chunks
  - `chunk_embeddings` - Vector embeddings

### Embedding Model

- **Provider:** Google Cloud Vertex AI
- **Model:** `textembedding-gecko@latest`
- **Dimensions:** 768
- **Similarity:** Cosine similarity

---

## 🚀 Deployment

### Docker

The API runs in a Docker container:

```bash
docker run -d --name driveindexer \
  --restart=always \
  --env-file .env \
  -v $(pwd)/secrets:/secrets \
  -p 8080:8080 \
  driveindexer:latest
```

### Environment Variables

Required in `.env`:
```bash
GOOGLE_APPLICATION_CREDENTIALS=/secrets/sa.json
BQ_PROJECT=inner-cinema-476211-u9
BQ_DATASET=uk_energy_insights
```

### Auto-Deployment

GitHub Actions workflow automatically deploys on push to `main`:

```yaml
# .github/workflows/deploy.yml
name: Deploy to UpCloud
on:
  push:
    branches: [ main ]
  workflow_dispatch:
```

Manual trigger:
```bash
# GitHub UI: Actions → Deploy to UpCloud → Run workflow
```

---

## 🧪 Testing

### Health Check Test

```bash
# Should return {"ok": true}
curl http://94.237.55.15:8080/health

# Python
import requests
assert requests.get("http://94.237.55.15:8080/health").json()["ok"]
```

### Search Test

```bash
# Basic search
curl "http://94.237.55.15:8080/search?q=test"

# Should return results array
curl "http://94.237.55.15:8080/search?q=energy&k=3" | jq '.results | length'
# Output: 3
```

### Error Handling Test

```bash
# Query too short (< 2 chars)
curl "http://94.237.55.15:8080/search?q=a"
# Should return 400 error

# Invalid parameter
curl "http://94.237.55.15:8080/search?q=test&k=invalid"
# Should return 422 validation error
```

---

## 📚 Related Documentation

- **Deployment:** [DEPLOYMENT_COMPLETE.md](../DEPLOYMENT_COMPLETE.md)
- **Architecture:** [ARCHITECTURE_VERIFIED.md](../ARCHITECTURE_VERIFIED.md)
- **Setup Guide:** [drive-bq-indexer/SETUP.md](./SETUP.md)
- **Operations:** [drive-bq-indexer/OPERATIONS.md](./OPERATIONS.md)

---

## 🐛 Troubleshooting

### API Not Responding

```bash
# Check if container is running
ssh root@94.237.55.15 "docker ps | grep driveindexer"

# Check logs
ssh root@94.237.55.15 "docker logs driveindexer --tail 50"

# Restart container
ssh root@94.237.55.15 "docker restart driveindexer"
```

### Search Returns No Results

1. **Check if embeddings exist:**
   ```sql
   SELECT COUNT(*) FROM `inner-cinema-476211-u9.uk_energy_insights.chunk_embeddings`
   ```

2. **Verify Vertex AI access:**
   ```bash
   # Test embedding generation
   python -m src.cli test-embeddings
   ```

3. **Check BigQuery permissions:**
   ```bash
   # Verify service account has BigQuery access
   cat secrets/sa.json | jq .client_email
   ```

### 500 Internal Server Error

Check container logs for Python errors:
```bash
docker logs driveindexer --tail 100 | grep ERROR
```

Common causes:
- Missing environment variables
- BigQuery authentication failed
- Vertex AI quota exceeded
- Network connectivity issues

---

## 📧 Support

- **Issues:** https://github.com/GeorgeDoors888/overarch-jibber-jabber/issues
- **Documentation:** See [DOCUMENTATION_INDEX.md](../DOCUMENTATION_INDEX.md)

---

**Last Updated:** November 5, 2025  
**API Version:** 1.0  
**Status:** ✅ Production

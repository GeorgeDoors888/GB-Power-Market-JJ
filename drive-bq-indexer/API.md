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

**BigQuery Repository:**
- **Project:** `inner-cinema-476211-u9`
- **Primary Datasets:**
  - `uk_energy_insights` - Document search and embeddings
  - `uk_energy_prod` - GB power market data (200+ tables)
- **Region:** `europe-west2` (London)
- **Total Storage:** ~50+ GB structured data

**uk_energy_insights Dataset (Search API):**
- `documents_clean` - 153,201 unique documents
- `chunks` - Text chunks from extracted documents
- `chunk_embeddings` - 768-dimensional vectors for semantic search

**uk_energy_prod Dataset (Energy Market Data):**
- **Historical Data:** 391M+ rows across 200+ tables
- **Real-Time IRIS Data:** Streaming updates every 30 minutes
- **Date Range:** 2022-01-01 to present (3.8+ years)
- **Key Tables:**
  - `bmrs_bod` - 391M rows (Bid-Offer Data)
  - `bmrs_fuelinst` - 5.7M rows (Fuel generation)
  - `bmrs_freq` - Grid frequency data
  - `bmrs_mid` - Market prices
  - `bmrs_indo_iris` - National demand (real-time)
  - `bmrs_indgen_iris` - Generation by boundary
  - Plus 194+ other BMRS datasets

### Embedding Model

- **Provider:** Google Cloud Vertex AI
- **Model:** `textembedding-gecko@latest`
- **Dimensions:** 768
- **Similarity:** Cosine similarity

---

## 📊 BigQuery Data Repository

### Overview

Energy Jibber Jabber integrates **generative AI (ChatGPT)** with cloud-based data analytics, storing structured energy market data and document embeddings in Google BigQuery.

### Data Architecture

```
Energy Jibber Jabber Platform
    ↓
ChatGPT (AI Interface)
    ↓
Codex Server (Execution Layer) → GitHub Codespaces / UpCloud
    ↓
Google BigQuery (Data Layer)
    ├── uk_energy_insights (Document Search)
    └── uk_energy_prod (Market Data)
    ↓
Vertex AI (ML Layer) → Embeddings & Semantic Analysis
    ↓
Reports & Visualizations → Google Docs / Dashboards
```

### Dataset: uk_energy_insights

**Purpose:** Document intelligence and semantic search

**Storage:** 153,201 indexed documents from Google Drive

**Tables:**

1. **documents_clean** (153,201 rows)
   - Document metadata
   - File types: PDFs (139K), Excel (6.8K), Sheets (5.7K), Word (1.3K)
   - Created dates, modified dates, MIME types
   - Google Drive IDs and paths

2. **chunks** (Variable rows)
   - Extracted text chunks (256-512 tokens each)
   - Chunk IDs, document references
   - Overlapping windows for context preservation

3. **chunk_embeddings** (Variable rows)
   - 768-dimensional vectors from Vertex AI
   - Enables semantic similarity search
   - Cosine similarity for ranking results

**Example Queries:**

```sql
-- Find documents about renewable energy
SELECT doc_id, file_name, created_time
FROM `inner-cinema-476211-u9.uk_energy_insights.documents_clean`
WHERE LOWER(file_name) LIKE '%renewable%'
   OR LOWER(file_name) LIKE '%wind%'
   OR LOWER(file_name) LIKE '%solar%'
LIMIT 100;

-- Count documents by file type
SELECT mime_type, COUNT(*) as count
FROM `inner-cinema-476211-u9.uk_energy_insights.documents_clean`
GROUP BY mime_type
ORDER BY count DESC;
```

### Dataset: uk_energy_prod

**Purpose:** GB power market operational and market data

**Storage:** 391M+ rows, 200+ tables, 3.8+ years of history

**Coverage:** January 2022 - Present (continuous updates)

**Data Sources:**
- **Historical:** Elexon BMRS API (batch downloads)
- **Real-Time:** IRIS Azure Service Bus (streaming)

**Major Tables:**

1. **bmrs_bod** (391,287,533 rows)
   - Bid-Offer Data for all BMUs
   - Settlement periods (48 per day)
   - Date range: 2022-01-01 to 2025-10-28
   - Use cases: Market analysis, price forecasting

2. **bmrs_fuelinst** (5,691,925 rows)
   - Fuel generation by type (coal, gas, wind, solar, nuclear, etc.)
   - Half-hourly settlement data
   - Date range: 2022-12-31 to 2025-10-30
   - Use cases: Generation mix analysis, renewable contribution

3. **bmrs_freq** + **bmrs_freq_iris** (Combined)
   - System frequency measurements
   - Historical: Daily averages
   - Real-time: Per-minute updates
   - Use cases: Grid stability monitoring, frequency anomaly detection

4. **bmrs_mid** (155,405 rows)
   - Market Index Data (prices)
   - £/MWh values
   - Date range: 2022-01-01 to 2025-10-30
   - Use cases: Price analysis, cost forecasting

5. **bmrs_indo_iris** (375 rows - real-time)
   - National demand (GB total)
   - Settlement period data (48 periods/day)
   - Date range: 2025-10-28 to present
   - Use cases: Demand forecasting, load balancing

6. **bmrs_indgen_iris** (284,364 rows - real-time)
   - Generation by transmission boundary (18 zones)
   - Settlement period data
   - Date range: 2025-10-30 to present
   - Use cases: Regional generation analysis

7. **bmrs_boalf** (11,330,547 rows)
   - BOA Lift Forecast
   - Balancing mechanism forecasts
   - Date range: 2022-01-01 to 2025-10-28

**Additional Tables (194+ more):**
- MELS, MILS (Export/Import limits)
- NETBSAD (Balancing costs)
- QPN, PN (Physical notifications)
- DISBSAD (Disaggregated balancing)
- REMIT (Market messages)
- And 180+ other BMRS datasets

**Table Naming Convention:**
- `bmrs_*` - Historical data (Elexon API)
- `bmrs_*_iris` - Real-time data (IRIS streaming)

### Query Capabilities

**1. Operational Performance Reports**

```sql
-- Grid frequency stability (last 7 days)
SELECT 
  DATE(measurementTime) as date,
  AVG(frequency) as avg_frequency,
  MIN(frequency) as min_frequency,
  MAX(frequency) as max_frequency,
  STDDEV(frequency) as frequency_stddev
FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_freq_iris`
WHERE measurementTime >= DATETIME_SUB(CURRENT_DATETIME(), INTERVAL 7 DAY)
GROUP BY date
ORDER BY date;

-- Generation by fuel type (today)
SELECT 
  fuelType,
  SUM(generation) as total_mwh
FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_fuelinst`
WHERE DATE(startTime) = CURRENT_DATE()
GROUP BY fuelType
ORDER BY total_mwh DESC;
```

**2. Market Analytics**

```sql
-- Average market prices by month
SELECT 
  FORMAT_DATE('%Y-%m', DATE(settlementDate)) as month,
  AVG(price) as avg_price_gbp_per_mwh,
  MIN(price) as min_price,
  MAX(price) as max_price
FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_mid`
WHERE settlementDate >= '2024-01-01'
GROUP BY month
ORDER BY month;

-- Renewable vs non-renewable generation
SELECT 
  CASE 
    WHEN fuelType IN ('WIND', 'SOLAR', 'HYDRO', 'BIOMASS') THEN 'Renewable'
    ELSE 'Non-Renewable'
  END as category,
  SUM(generation) as total_mwh,
  COUNT(DISTINCT DATE(startTime)) as days_covered
FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_fuelinst`
WHERE startTime >= DATETIME_SUB(CURRENT_DATETIME(), INTERVAL 30 DAY)
GROUP BY category;
```

**3. Real-Time Monitoring**

```sql
-- Current national demand
SELECT 
  settlementDate,
  settlementPeriod,
  demand as demand_mw,
  publishTime
FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_indo_iris`
ORDER BY publishTime DESC
LIMIT 1;

-- Latest generation by boundary
SELECT 
  boundary,
  generation as generation_mw,
  settlementDate,
  settlementPeriod
FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_indgen_iris`
WHERE settlementDate = CURRENT_DATE()
ORDER BY boundary;
```

**4. Historical Trends**

```sql
-- 3-year demand patterns
SELECT 
  EXTRACT(YEAR FROM settlementDate) as year,
  EXTRACT(MONTH FROM settlementDate) as month,
  AVG(demand) as avg_demand_mw,
  MAX(demand) as peak_demand_mw
FROM `inner-cinema-476211-u9.uk_energy_prod.demand_outturn`
WHERE settlementDate >= '2022-01-01'
GROUP BY year, month
ORDER BY year, month;
```

**5. Document Intelligence**

```sql
-- Search embeddings for relevant documents
-- (Executed via FastAPI /search endpoint with Vertex AI)
```

### Statistics & Metrics

**Data Volume:**
- **Total Rows:** 391M+ across all tables
- **Largest Table:** bmrs_bod (391M rows)
- **Update Frequency:** 
  - Historical: On-demand / daily backfill
  - Real-time: Every 30 minutes (IRIS)
- **Data Freshness:**
  - IRIS tables: < 5 minutes lag
  - Historical tables: Updated daily

**Coverage:**
- **Time Span:** 3.8 years (2022-01-01 to present)
- **Data Points per Day:** 48 settlement periods
- **Fuel Types:** 20+ (wind, solar, gas, nuclear, coal, biomass, hydro, etc.)
- **Geographic:** GB transmission system (18 boundaries)

**Storage & Cost:**
- **Active Storage:** ~50 GB
- **BigQuery Cost:** ~$0.50/month (storage)
- **Query Cost:** Free tier (< 1TB/month)

### Data Quality & Governance

**Security:**
- Service account authentication
- Token-based API access
- IAM role-based permissions
- Data encryption at rest

**Quality Assurance:**
- Automated validation checks
- Duplicate detection and removal
- Schema enforcement
- Timestamp consistency verification

**Compliance:**
- Data sourced from Elexon (official GB market operator)
- REMIT-compliant market data
- Audit trails for all data ingestion

### Supported Report Types

**Via ChatGPT Integration:**

1. **Operational Performance Reports**
   - Grid capacity utilization
   - BMU availability and utilization
   - System frequency stability
   - Generation mix analysis

2. **Market Analytics**
   - Price trends and forecasts
   - Imbalance costs analysis
   - Supply/demand correlation
   - Renewable contribution metrics

3. **Predictive Forecasts**
   - AI-driven trend extrapolation
   - Anomaly detection (frequency, prices)
   - Demand forecasting models

4. **Document Intelligence**
   - Semantic search across 153K documents
   - Regulatory paper summaries
   - Technical specification extraction

5. **Quality & Compliance**
   - Data completeness audits
   - Schema validation reports
   - Coverage gap detection

### Integration with AI Platform

**ChatGPT ↔ BigQuery Flow:**

```
User Query (Natural Language)
    ↓
ChatGPT (Intent Recognition)
    ↓
Code Generation (SQL/Python)
    ↓
Codex Server Execution (UpCloud/GitHub Codespaces)
    ↓
BigQuery Query Execution
    ↓
Data Retrieval & Processing
    ↓
ChatGPT Analysis & Formatting
    ↓
Report Generation (Google Docs/Dashboard)
```

**Vertex AI Integration:**

```
User Search Query
    ↓
FastAPI /search Endpoint
    ↓
Vertex AI Embedding (768 dimensions)
    ↓
BigQuery Vector Search (chunk_embeddings)
    ↓
Top K Results (cosine similarity)
    ↓
Semantic Results Returned
```

### Future Enhancements

**Planned:**
- ✅ Daily INDO backfill automation (script created)
- 🔄 Power BI and Tableau connectors
- 🔄 Real-time ChatGPT audit agents
- 🔄 Reinforcement learning for report optimization
- 🔄 Kubernetes deployment for scalability

**Under Consideration:**
- Azure Container Apps integration
- Real-time streaming dashboards
- Predictive ML models for price forecasting
- Advanced anomaly detection algorithms

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

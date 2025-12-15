# 🚀 System Capabilities Overview
## GB Power Market JJ (Jibber Jabber)

**Last Updated**: November 6, 2025  
**Purpose**: Comprehensive overview of all system capabilities

---

## 📊 What This System Does

The **GB Power Market JJ** system is a comprehensive **data pipeline, analysis, and search platform** with two distinct capabilities:

### 1️⃣ **GB Power Market Analytics** (Primary System)
Real-time and historical analysis of the UK electricity market

### 2️⃣ **Document Intelligence** (Drive→BigQuery Indexer)
Semantic search across Google Drive documents with AI-powered text extraction

---

## 🔋 Part 1: GB Power Market Analytics System

### Core Capabilities

#### 📥 **Dual Data Pipeline Architecture**

**Historical Pipeline** (Batch Processing)
- **Source**: Elexon BMRS API (official UK power market data)
- **Data Range**: 2020-2025 (5+ years of history)
- **Tables**: 174 BigQuery tables with `bmrs_*` prefix
- **Update Frequency**: On-demand or 15-minute cron jobs
- **Volume**: 391M+ rows in `bmrs_bod` table alone
- **Purpose**: Long-term analysis, trends, forecasting

**Real-Time Pipeline** (IRIS Streaming)
- **Source**: Azure Service Bus IRIS messages
- **Data Range**: Last 24-48 hours (rolling window)
- **Tables**: 8+ BigQuery tables with `_iris` suffix
- **Update Frequency**: Continuous (30s-2min latency)
- **Volume**: Growing continuously
- **Purpose**: Live monitoring, instant alerts, grid stability

**Key Innovation**: Both pipelines write to the same BigQuery project (`inner-cinema-476211-u9`) but use different table names, allowing seamless UNION queries for complete time series data.

#### 📊 **Data Categories**

| Category | What It Tracks | Example Use Cases |
|----------|---------------|-------------------|
| **Generation Mix** | Power by source (Wind, Solar, Gas, Nuclear, etc.) | Renewable energy trends, fuel mix analysis |
| **System Frequency** | Grid frequency (50 Hz target) | Grid stability monitoring, fault detection |
| **Market Prices** | System Buy/Sell prices (£/MWh) | Cost optimization, price forecasting |
| **Balancing** | Grid balancing costs and actions | NESO operational analysis |
| **Demand** | Electricity demand patterns | Load forecasting, capacity planning |
| **Bid-Offer Data** | Market participant bids/offers | Trading strategy, market behavior |

#### 🎯 **Business Intelligence Dashboard**

**Live Dashboard**: [Google Sheets BI Dashboard](https://docs.google.com/spreadsheets/d/1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA/)

**Features**:
- 📈 10 interactive sheets with real-time data
- 🔄 Auto-refresh capability via Apps Script
- 📊 4 main sections: Generation, Frequency, Prices, Balancing
- 📉 Advanced calculations: capacity factors, quality scores, curtailment
- 🎚️ Dropdown controls for date ranges and views
- 🌍 Generator map with coordinates
- 📱 Mobile-friendly interface

**Sample Metrics**:
- Total Generation (MWh)
- Renewable Percentage
- System Frequency Stability
- Price Spreads (Buy vs Sell)
- Peak Demand Times
- Wind Curtailment Estimates
- Balancing Costs by Category

#### 📈 **Statistical Analysis Suite**

**9 Advanced Outputs**:

1. **Descriptive Statistics** - Mean, median, std dev, quartiles
2. **Time Series Components** - Trend, seasonal, residual decomposition
3. **Correlation Matrices** - Price vs demand, renewables vs frequency
4. **Regression Analysis** - Predictive models for prices, demand
5. **Autocorrelation** - Pattern detection in time series
6. **Distribution Analysis** - Histograms, Q-Q plots, normality tests
7. **Outlier Detection** - Identify anomalies in market data
8. **Forecasting** - ARIMA models for demand/price prediction
9. **Volatility Metrics** - Rolling std dev, coefficient of variation

**Business Applications**:
- Battery arbitrage strategy
- Solar generation forecasting
- Market price modeling
- Grid stability prediction
- Renewable integration planning

#### 🗺️ **Interactive Maps**

**GB Power Comprehensive Map**: [View Map](http://94.237.55.15/gb_power_comprehensive_map.html)

**Features**:
- All UK power stations with coordinates
- Color-coded by fuel type
- Capacity information (MW)
- CVA (Central Volume Allocation) plants
- SVA (Supplier Volume Allocation) plants
- Grid Supply Point (GSP) boundaries
- Distribution Network Operator (DNO) regions
- Live generation overlay (IRIS data)
- Interactive filtering and search

#### 🔌 **APIs and Automation**

**FastAPI Search Service**: http://94.237.55.15:8080

**Endpoints**:
- `GET /health` - Service health check
- `GET /search?q=query&k=5` - Semantic document search

**Automation Capabilities**:
- Scheduled data updates (cron jobs)
- Email reports generation
- Alert systems (frequency deviation, price spikes)
- Auto-refresh dashboards
- Chart generation (matplotlib + Google Sheets)
- API integrations for external systems

#### 💾 **Data Storage**

**BigQuery Configuration**:
- **Project**: `inner-cinema-476211-u9`
- **Dataset**: `uk_energy_prod`
- **Region**: US
- **Total Tables**: 182+ (174 historical + 8 IRIS)
- **Total Rows**: 400M+ across all tables
- **Storage Size**: Multi-TB dataset

**Key Tables**:
| Table | Rows | Purpose |
|-------|------|---------|
| `bmrs_bod` | 391M+ | Bid-Offer Data (market pricing) |
| `bmrs_fuelinst` | 5.7M+ | Generation by fuel type |
| `bmrs_freq` | Large | System frequency measurements |
| `bmrs_mid` | 155K+ | Market Index Data (system prices) |
| `bmrs_fuelinst_iris` | Growing | Live generation (last 24h) |
| `bmrs_freq_iris` | Growing | Live frequency (last 24h) |

---

## 🔍 Part 2: Document Intelligence System

### Core Capabilities

#### 📂 **Google Drive Integration**

**What It Does**:
- Crawls entire Google Drive (or specified folders)
- Indexes all documents with metadata
- Detects changes to avoid re-processing
- Handles permissions and shared drives
- Supports incremental updates

**Supported File Types**:
- ✅ **PDF** - Full text extraction + OCR fallback
- ✅ **DOCX** - Microsoft Word documents
- ✅ **PPTX** - PowerPoint presentations
- ✅ **Images** (via OCR) - Tesseract or Cloud Vision

#### 🤖 **AI-Powered Text Extraction**

**Multi-Layer Extraction Strategy**:

1. **Direct Text Extraction**:
   - PDF: `pdfminer.six` library
   - DOCX: `python-docx` parser
   - PPTX: `python-pptx` parser
   - Fast and accurate for text-based documents

2. **OCR Fallback** (for scanned PDFs/images):
   - **Tesseract OCR**: Local, free, decent quality
   - **Cloud Vision API**: Google's AI, premium quality
   - Automatically triggers when direct extraction fails
   - Configurable OCR threshold (auto-tuning)

3. **Quality Checks**:
   - Text length validation
   - Character-to-whitespace ratio
   - Language detection
   - Confidence scoring

#### 🧩 **Intelligent Chunking**

**Token-Aware Splitting**:
- Breaks documents into searchable chunks (e.g., 500 tokens)
- Configurable overlap (e.g., 100 tokens) for context continuity
- Preserves sentence boundaries
- Maintains paragraph structure
- Self-tuning based on search quality

**Benefits**:
- More relevant search results
- Better context for AI understanding
- Efficient storage and retrieval
- Optimized for LLM token limits

#### 🔎 **Vector Search Engine**

**Vertex AI Embeddings**:
- **Model**: `textembedding-gecko` (Google's latest)
- **Region**: europe-west2
- **Dimension**: 768-dimensional vectors
- **Similarity**: Dot-product scoring
- **Fallback**: BM25 keyword search

**Search Capabilities**:
- Semantic similarity (understands meaning, not just keywords)
- Multi-document search
- Ranked results with confidence scores
- Fast retrieval (BigQuery-powered)
- API access for integration

**Example Query**:
```bash
GET /search?q=contract%20for%20difference&k=5
```

**Response**:
```json
{
  "query": "contract for difference",
  "k": 5,
  "results": [
    {
      "doc_id": "abc123",
      "chunk_id": "chunk_5",
      "text": "...relevant contract text...",
      "score": 0.89,
      "metadata": {
        "file_name": "CFD_Policy_2025.pdf",
        "mime_type": "application/pdf"
      }
    }
  ]
}
```

#### 📊 **BigQuery Storage**

**Dataset**: `jibber-jabber-knowledge.uk_energy_insights` (europe-west2)

**Tables**:
1. **`documents`** - Metadata for all indexed files
   - doc_id, name, mime_type, created_time, size, etc.
   
2. **`documents_clean`** - Deduplicated, processed documents
   - Same structure as `documents` but cleaned
   
3. **`chunks`** - Text chunks from documents
   - chunk_id, doc_id, text, chunk_index, token_count
   
4. **`chunk_embeddings`** - Vector embeddings
   - chunk_id, embedding (768-dim vector), model_version

**Current Status** (as of Nov 6, 2025):
- **Total Documents**: 140,434 indexed
- **Processed**: 8,529 documents (6.1%)
- **Remaining**: 131,905 documents
- **Processing Rate**: 400-500 docs/hour
- **ETA**: ~12 days to complete

#### 🔧 **Self-Optimization**

**Auto-Tuning Features**:
- Adjusts chunk size based on search quality
- Optimizes overlap based on context needs
- Switches OCR mode based on accuracy
- Monitors extraction quality metrics
- Adapts to different document types

**Quality Metrics Tracked**:
- Text extraction success rate
- OCR accuracy
- Search relevance scores
- Chunk coverage
- Processing speed
- Memory usage

#### 🚀 **Deployment Architecture**

**Production Server**: 94.237.55.15 (UpCloud)
- **OS**: AlmaLinux 9
- **RAM**: 1 GB (optimized for low memory)
- **CPU**: 1 core
- **Docker**: Container `driveindexer`
- **Systemd**: Service `extraction.service` (auto-restart)
- **Workers**: 2 concurrent (optimized for 1GB RAM)
- **Batch Size**: 100 documents
- **Memory Usage**: ~580 MB stable

**Development**: GitHub Codespaces
- Lightweight testing environment
- PR validation
- Quick experiments
- Not for production runs

#### 📈 **Recent Optimizations** (Nov 6, 2025)

**Memory Issue Fixed**:
- **Problem**: Memory grew to 7.2 GB, speed degraded to 193 sec/doc
- **Root Cause #1**: Unlimited queue (500 docs × 20MB = 10GB)
- **Root Cause #2**: Loading all 140K docs into memory (210MB wasted)
- **Solution**: Limited queue (4 docs max) + query-based filtering (300 docs at a time)
- **Result**: Memory reduced to 580 MB (92% reduction), speed improved to 7-9 sec/doc (20x faster)

**Performance Metrics**:
- Before: 40 docs/hour, 7.2 GB memory, 193 sec/doc
- After: 450 docs/hour, 580 MB memory, 7 sec/doc
- Improvement: 11x faster, 92% less memory

---

## 🛠️ How the Systems Work Together

### Data Flow

```
┌─────────────────────────────────────────────────────────┐
│              GB POWER MARKET SYSTEM                      │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  Elexon BMRS API ──┐                                    │
│                    ├──> Python Scripts ──> BigQuery     │
│  Azure IRIS Bus ───┘         ↓                          │
│                              ↓                          │
│                    Google Sheets Dashboard              │
│                    Statistical Analysis                 │
│                    Interactive Maps                     │
│                                                          │
└─────────────────────────────────────────────────────────┘
                              
                              │
                              │ Document Indexing
                              ▼
                              
┌─────────────────────────────────────────────────────────┐
│           DOCUMENT INTELLIGENCE SYSTEM                   │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  Google Drive ──> Index ──> Extract (PDF/DOCX/PPTX)    │
│                              ↓                          │
│                         OCR (if needed)                 │
│                              ↓                          │
│                     Chunk Documents                     │
│                              ↓                          │
│                   Generate Embeddings                   │
│                              ↓                          │
│                     BigQuery Storage                    │
│                              ↓                          │
│                   FastAPI Search Service                │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

### Use Cases

#### Power Market Analytics
1. **Energy Traders**: Monitor real-time prices, identify arbitrage opportunities
2. **Grid Operators**: Track frequency stability, predict demand
3. **Renewable Developers**: Analyze wind/solar patterns, curtailment
4. **Policy Makers**: Understand market dynamics, balancing costs
5. **Researchers**: Historical analysis, forecasting models

#### Document Intelligence
1. **Legal Teams**: Search contracts for specific clauses
2. **Compliance**: Find policy documents, regulatory references
3. **Research**: Discover relevant technical documentation
4. **Knowledge Management**: Organize and retrieve institutional knowledge
5. **Due Diligence**: Quick document review and analysis

---

## 🚀 Quick Start Commands

### Power Market Analytics

```bash
# Navigate to project
cd ~/GB\ Power\ Market\ JJ

# Refresh dashboard data
python3 update_analysis_bi_enhanced.py

# Run statistical analysis
python3 advanced_statistical_analysis_enhanced.py

# Query BigQuery directly
python3 -c '
from google.cloud import bigquery
client = bigquery.Client(project="inner-cinema-476211-u9")
query = "SELECT fuelType, SUM(generation) as total FROM bmrs_fuelinst GROUP BY fuelType"
print(client.query(query).to_dataframe())
'

# Check IRIS pipeline status
ps aux | grep "client.py"
tail -50 iris_client.log

# View live dashboard
open https://docs.google.com/spreadsheets/d/1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA/

# Check generator map
open http://94.237.55.15/gb_power_comprehensive_map.html
```

### Document Intelligence

```bash
# Check extraction status
ssh root@94.237.55.15 'docker stats driveindexer --no-stream'
ssh root@94.237.55.15 'tail -10 /var/log/extraction.log'

# Monitor progress
ssh root@94.237.55.15 'systemctl status extraction.service'

# Search documents
curl "http://94.237.55.15:8080/search?q=renewable%20energy&k=10"

# Health check
curl http://94.237.55.15:8080/health

# Manual extraction (if needed)
cd ~/GB\ Power\ Market\ JJ/drive-bq-indexer
python -m src.cli index-drive
python -m src.cli extract
python -m src.cli build-embeddings
```

---

## 📊 System Status (November 6, 2025)

### Power Market Analytics
- ✅ **Historical Pipeline**: Operational, 391M+ rows
- ✅ **IRIS Pipeline**: Operational, continuous streaming
- ✅ **Dashboard**: Live, auto-refresh enabled
- ✅ **APIs**: FastAPI service running
- ✅ **Maps**: Interactive generator map deployed

### Document Intelligence
- 🟢 **Extraction Service**: Active and stable
- 📈 **Progress**: 8,529 / 140,434 documents (6.1%)
- ⚡ **Speed**: 450 docs/hour (7 sec/doc)
- 💾 **Memory**: 580 MB stable (optimized)
- 🎯 **ETA**: ~12 days to completion
- ✅ **Search API**: Operational at port 8080

---

## 📚 Key Documentation

### Must-Read First
1. **[STOP_DATA_ARCHITECTURE_REFERENCE.md](STOP_DATA_ARCHITECTURE_REFERENCE.md)** - Read before ANY query!
2. **[PROJECT_CONFIGURATION.md](PROJECT_CONFIGURATION.md)** - Configuration master
3. **[README.md](README.md)** - Main documentation

### Architecture & Design
4. **[UNIFIED_ARCHITECTURE_HISTORICAL_AND_REALTIME.md](UNIFIED_ARCHITECTURE_HISTORICAL_AND_REALTIME.md)** - System architecture
5. **[drive-bq-indexer/ARCHITECTURE.md](drive-bq-indexer/ARCHITECTURE.md)** - Indexer architecture

### User Guides
6. **[ENHANCED_BI_ANALYSIS_README.md](ENHANCED_BI_ANALYSIS_README.md)** - Dashboard guide
7. **[STATISTICAL_ANALYSIS_GUIDE.md](STATISTICAL_ANALYSIS_GUIDE.md)** - Analytics guide
8. **[drive-bq-indexer/API.md](drive-bq-indexer/API.md)** - API documentation

### Operations
9. **[EXTRACTION_SYSTEMD_SETUP.md](EXTRACTION_SYSTEMD_SETUP.md)** - Extraction service management
10. **[MEMORY_ISSUE_ROOT_CAUSE.md](MEMORY_ISSUE_ROOT_CAUSE.md)** - Recent memory optimization
11. **[DEPLOYMENT_COMPLETE.md](DEPLOYMENT_COMPLETE.md)** - Deployment guide

### Complete Index
12. **[DOCUMENTATION_INDEX.md](DOCUMENTATION_INDEX.md)** - All 22+ documentation files

---

## 🎯 System Strengths

### Technical Capabilities
- ✅ Real-time + historical data integration
- ✅ Multi-source data fusion (API + streaming)
- ✅ Scalable BigQuery architecture (400M+ rows)
- ✅ AI-powered document understanding
- ✅ Self-optimizing extraction pipeline
- ✅ Low-memory optimization (1GB server)
- ✅ Auto-restart fault tolerance
- ✅ Interactive visualizations
- ✅ RESTful API access

### Business Value
- 📊 Comprehensive market visibility
- ⚡ Near real-time insights (30s latency)
- 📈 Advanced analytics suite
- 🔍 Intelligent document search
- 🗺️ Geographic visualization
- 📱 Mobile-friendly dashboards
- 🤖 Automation-ready
- 🔌 Integration-friendly APIs

---

## 🤖 ChatGPT & AI Integration

### ChatGPT Integration Capabilities

#### 1️⃣ **Google Drive OAuth Connection**

**Purpose**: Direct access to your Google Drive files within ChatGPT conversations

**Features**:
- ✅ Browse your Google Drive files in ChatGPT
- ✅ Read Google Sheets data
- ✅ Access Google Docs
- ✅ Interactive file queries

**Setup Documentation**: `FIX_CHATGPT_OAUTH.md`

**How to Connect**:
1. Go to ChatGPT Settings → Data Controls
2. Connect Google Drive
3. Authorize with `george@upowerenergy.uk`
4. Grant permissions (Drive, Sheets, Docs)

**Sample Queries**:
```
"List my recent Google Drive files"
"Open sheet 1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA"
"Read the Latest Generation data from my power dashboard"
```

**Authentication**:
- Uses OAuth 2.0 (personal account access)
- Separate from service account credentials
- Only needed for interactive ChatGPT access

#### 2️⃣ **Code Execution Server (Codex Server)**

**Purpose**: Execute Python and JavaScript code remotely from ChatGPT

**Server Details**:
- **Location**: GitHub Codespaces (development)
- **Framework**: FastAPI
- **Port**: 8000
- **Languages**: Python, JavaScript/Node.js

**Capabilities**:
- Execute code snippets remotely
- Safe sandboxed environment
- Configurable timeouts (1-30 seconds)
- Real-time output streaming
- Error handling and reporting

**Endpoints**:
```
GET  /health        - Health check
POST /execute       - Execute code
GET  /languages     - List supported languages
```

**Example Request**:
```python
POST /execute
{
  "code": "print('Hello from ChatGPT!')",
  "language": "python",
  "timeout": 10
}
```

**Response**:
```json
{
  "output": "Hello from ChatGPT!\n",
  "error": "",
  "exit_code": 0,
  "execution_time": 0.023,
  "timestamp": "2025-11-06T12:00:00Z"
}
```

**Security Options**:

1. **Open Access** (Current):
   - No authentication required
   - Public port in Codespaces
   - Fast for development

2. **Token Authentication** (Recommended for Production):
   ```python
   Authorization: Bearer codex_abc123xyz456...
   ```

3. **Custom GPT Action** (Best Integration):
   - OpenAPI schema provided
   - Native ChatGPT integration
   - Seamless code execution in conversations

**Documentation**: `codex-server/CHATGPT_INTEGRATION.md`

**Sample ChatGPT Workflow**:
```
You: "Execute this Python code on my server:
     import requests
     r = requests.get('https://api.github.com/users/github')
     print(r.json()['name'])"

ChatGPT: [Sends request to your Codex server]
         "Output: GitHub
          Exit Code: 0
          Execution Time: 0.45s"
```

#### 3️⃣ **GitHub Integration**

**Purpose**: Secure code management workflow with ChatGPT guidance

**Status**: ✅ Fully configured (November 2, 2025)

**What's Set Up**:
- GitHub CLI authenticated on your Mac
- Token stored securely in macOS keyring
- Full write access to repositories
- Quick-push script for easy commits

**Security Model**:
- ⚠️ ChatGPT **cannot** accept or store your GitHub token (by design)
- ✅ Token stays on YOUR Mac only
- ✅ ChatGPT provides code/guidance
- ✅ YOU push changes using local authentication

**Workflow**:
1. **Ask ChatGPT** for code/solutions
2. **Save files** locally (VS Code or Copilot)
3. **Push to GitHub**:
   ```bash
   ./quick-push.sh "Description of changes"
   ```

**Quick Commands**:
```bash
# Easy push
./quick-push.sh "Added new feature from ChatGPT"

# Check auth status
gh auth status

# View repo on GitHub
gh repo view --web

# Manual git (if needed)
git add .
git commit -m "message"
git push
```

**Documentation**: `CHATGPT_SETUP_COMPLETE.md`

**Example Workflow**:
```
[In ChatGPT]
"Create a Python script that backs up files to Google Drive"
→ ChatGPT provides code

[In VS Code with Copilot]
"Create backup.py with [paste code]"

[In Terminal]
./quick-push.sh "Add backup script from ChatGPT"

[Back to ChatGPT]
"I pushed it. Can you add error handling?"
```

### Google Gemini AI Integration

#### 📊 **AI-Powered Analysis**

**Purpose**: Get AI insights from your power market data

**Features**:
- **Key observations** from current data
- **Grid health assessment** (frequency stability)
- **Renewable performance** analysis
- **Market insights** (prices, balancing costs)
- **Concerns & opportunities** identification
- **Actionable recommendations**

**Model**: Google Gemini 1.5 Flash
- Fast inference (10-20 seconds)
- Large context window
- Free tier available
- Multi-modal capabilities

**How It Works**:
1. Script reads current data from Google Sheets
2. Formats summary (generation, frequency, prices, balancing)
3. Sends to Gemini API with analysis prompt
4. Gemini returns insights
5. Results written back to sheet

**Setup** (2 minutes):
```bash
# Get API key (free): https://makersuite.google.com/app/apikey

# Option A: Environment variable
export GEMINI_API_KEY='your-api-key-here'

# Option B: File
echo "your-api-key-here" > gemini_api_key.txt

# Install library (if needed)
pip3 install --user google-generativeai
```

**Usage**:
```bash
# Run analysis
cd ~/GB\ Power\ Market\ JJ
python3 ask_gemini_analysis.py

# Combine with data refresh
python3 update_analysis_bi_enhanced.py && python3 ask_gemini_analysis.py

# Automate (hourly analysis)
# Add to crontab:
# 0 * * * * cd ~/GB\ Power\ Market\ JJ && python3 update_analysis_bi_enhanced.py && python3 ask_gemini_analysis.py >> gemini_analysis.log 2>&1
```

**Sample Output**:
```
🤖 GEMINI ANALYSIS

📊 KEY OBSERVATIONS:
- Wind generation at 42.3% of total mix (strong performance)
- System frequency stable at 49.98 Hz (within normal bounds)
- Renewable penetration at 68.4% (above average)

⚡ GRID HEALTH:
- Status: HEALTHY
- Frequency deviation: -0.02 Hz (minimal)
- No frequency alerts in last hour

🌱 RENEWABLE PERFORMANCE:
- Wind: 15,240 MW (excellent conditions)
- Solar: 3,120 MW (midday peak)
- Combined renewables: 18,360 MW

💰 MARKET INSIGHTS:
- System prices: £45.20/MWh (moderate)
- Price spread: £2.80/MWh (normal range)
- Balancing costs: £1.2M (24h period)

🎯 RECOMMENDATIONS:
1. Monitor wind curtailment in Scotland (potential constraints)
2. Battery storage opportunity during solar peak
3. Consider forward contracts at current price levels
```

**What Gemini Sees**:
- Summary metrics (generation, renewable %, frequency, prices)
- Generation mix (top 10 fuel types)
- Recent frequency measurements (last 5)
- Recent market prices (last 5)
- Recent balancing costs (last 5)

**Documentation**: `GEMINI_AI_SETUP.md`

#### 🔍 **Vertex AI Embeddings** (Document Search)

**Model**: `textembedding-gecko`
- **Region**: europe-west2
- **Dimensions**: 768
- **Provider**: Google Cloud Vertex AI

**Purpose**: Power the semantic search engine in document intelligence system

**Cost**: ~$0.25-$2.50/month (based on usage)

**How It Works**:
1. Documents chunked into searchable segments
2. Each chunk converted to 768-dim vector
3. Vectors stored in BigQuery
4. Queries also converted to vectors
5. Dot-product similarity finds relevant chunks

**Benefits**:
- Understands meaning, not just keywords
- Finds semantically similar content
- Handles synonyms and context
- Multi-language support
- Production-grade quality

### Integration Summary

| Integration | Purpose | Status | Documentation |
|------------|---------|--------|---------------|
| **ChatGPT Drive** | Interactive file access in ChatGPT | ✅ Ready | FIX_CHATGPT_OAUTH.md |
| **Codex Server** | Remote code execution | ✅ Operational | codex-server/CHATGPT_INTEGRATION.md |
| **GitHub CLI** | Secure code management | ✅ Configured | CHATGPT_SETUP_COMPLETE.md |
| **Gemini Analysis** | AI insights on power data | ✅ Ready | GEMINI_AI_SETUP.md |
| **Vertex AI** | Document search embeddings | ✅ Active | drive-bq-indexer/README.md |

### AI-Enhanced Workflows

#### Workflow 1: Conversational Data Analysis
```
User in ChatGPT: "What's the current renewable percentage?"
↓
ChatGPT (with Drive access): [Reads Google Sheet]
"Current renewable percentage is 68.4% with wind at 42.3% 
and solar at 26.1%"
```

#### Workflow 2: Code Development & Deployment
```
User: "Create a script to alert when frequency drops below 49.8 Hz"
↓
ChatGPT: [Provides Python code]
↓
User: [Saves to alert_frequency.py via Copilot]
↓
User: ./quick-push.sh "Add frequency alert system"
↓
GitHub: Code committed and pushed
```

#### Workflow 3: AI-Powered Insights
```
User: python3 update_analysis_bi_enhanced.py && python3 ask_gemini_analysis.py
↓
System: [Refreshes latest data from BigQuery]
↓
Gemini AI: [Analyzes patterns and generates insights]
↓
Sheet: Updated with AI recommendations
↓
User: [Reviews insights, takes action]
```

#### Workflow 4: Document Intelligence Query
```
User: curl "http://94.237.55.15:8080/search?q=contract%20for%20difference&k=5"
↓
System: [Converts query to 768-dim vector via Vertex AI]
↓
BigQuery: [Finds similar document chunks via dot-product]
↓
API: Returns top 5 relevant passages with scores
↓
User: [Reviews results, drills into documents]
```

---

## 🔮 Future AI/ChatGPT Enhancements (Roadmap)

### Power Market Analytics
- [ ] ChatGPT plugin for live dashboard queries
- [ ] Gemini-powered price forecasting
- [ ] Automated trading signals via AI analysis
- [ ] Enhanced real-time alerting with NLP
- [ ] Voice interface for mobile queries
- [ ] Multi-model ensemble predictions

### Document Intelligence
- [ ] ChatGPT Q&A chatbot over indexed documents
- [ ] Multi-language document support (translate + search)
- [ ] Audio/video transcription and indexing
- [ ] Graph database for document relationships
- [ ] Automated document summarization
- [ ] Change detection alerts via embeddings
- [ ] LLM-powered document classification

### Code & Automation
- [ ] Custom GPT with direct BigQuery access
- [ ] Automated report generation via Gemini
- [ ] Natural language to SQL conversion
- [ ] Self-healing pipelines with AI monitoring
- [ ] Predictive maintenance using ML

---

**Last Updated**: November 6, 2025  
**System Version**: 2.0 (Dual Pipeline + Document Intelligence + AI Integration)  
**Status**: ✅ Fully Operational with AI Capabilities

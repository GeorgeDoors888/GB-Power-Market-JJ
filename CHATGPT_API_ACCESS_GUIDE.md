# ChatGPT API Access Guide
## Codex Server Integration for BigQuery & Code Execution

**Last Updated**: November 6, 2025  
**Server Status**: ✅ Fully Operational  
**Server Version**: 1.0.0

---

## 🔗 Server Connection Details

### Base URL
```
https://super-duper-engine-wr46657556g6f5jpq-8000.app.github.dev
```

### API Documentation
```
https://super-duper-engine-wr46657556g6f5jpq-8000.app.github.dev/docs
```

### Server Status
- **Port**: 8000 (Public)
- **CORS**: Enabled (allows all origins)
- **Authentication**: None required
- **Rate Limiting**: None
- **Timeout**: Configurable per request

---

## 📋 Available Endpoints

### 1. Health Check
**Endpoint**: `GET /health`  
**Purpose**: Verify server is running  
**Response**:
```json
{
  "status": "running",
  "version": "1.0.0",
  "languages": ["python", "javascript"],
  "timestamp": "2025-11-06T20:35:00.000000"
}
```

### 2. Execute Code
**Endpoint**: `POST /execute`  
**Purpose**: Run Python or JavaScript code in a sandboxed environment  

**Request Body**:
```json
{
  "code": "print('Hello World')",
  "language": "python",
  "timeout": 30,
  "args": []
}
```

**Response**:
```json
{
  "output": "Hello World\n",
  "error": null,
  "exit_code": 0,
  "execution_time": 0.123,
  "timestamp": "2025-11-06T20:35:00.000000"
}
```

**Supported Languages**:
- `python` (Python 3.14)
- `javascript` (Node.js via subprocess)

**Example - Python**:
```bash
curl -X POST "https://super-duper-engine-wr46657556g6f5jpq-8000.app.github.dev/execute" \
  -H "Content-Type: application/json" \
  -d '{
    "code": "import sys\nprint(f\"Python {sys.version}\")",
    "language": "python",
    "timeout": 30
  }'
```

**Example - JavaScript**:
```bash
curl -X POST "https://super-duper-engine-wr46657556g6f5jpq-8000.app.github.dev/execute" \
  -H "Content-Type: application/json" \
  -d '{
    "code": "console.log(\"Hello from JavaScript\")",
    "language": "javascript",
    "timeout": 30
  }'
```

### 3. Query BigQuery ⭐ **NEW**
**Endpoint**: `POST /query_bigquery`  
**Purpose**: Execute SQL queries against Google BigQuery  
**Project**: `jibber-jabber-knowledge`  

**Request Body**:
```json
{
  "sql": "SELECT * FROM `dataset.table` LIMIT 10",
  "timeout": 60,
  "max_results": 1000
}
```

**Response**:
```json
{
  "success": true,
  "data": [
    {"column1": "value1", "column2": "value2"},
    {"column1": "value3", "column2": "value4"}
  ],
  "row_count": 2,
  "error": null,
  "execution_time": 2.091,
  "timestamp": "2025-11-06T20:35:23.000000"
}
```

**Parameters**:
- `sql` (string, required): SQL query to execute
- `timeout` (integer, optional): Query timeout in seconds (default: 60)
- `max_results` (integer, optional): Maximum rows to return (default: 1000)

**Important Notes**:
- All queries run in the `jibber-jabber-knowledge` Google Cloud project
- Service account credentials are pre-configured on the server
- Standard SQL syntax is used (not legacy SQL)
- Use backticks for table references: `` `project.dataset.table` ``

**Example - Simple Query**:
```bash
curl -X POST "https://super-duper-engine-wr46657556g6f5jpq-8000.app.github.dev/query_bigquery" \
  -H "Content-Type: application/json" \
  -d '{
    "sql": "SELECT 1 as test_number, \"Hello BigQuery\" as message",
    "timeout": 60
  }'
```

**Example - Real Data Query**:
```bash
curl -X POST "https://super-duper-engine-wr46657556g6f5jpq-8000.app.github.dev/query_bigquery" \
  -H "Content-Type: application/json" \
  -d '{
    "sql": "SELECT COUNT(*) as total_rows FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_fuelinst_iris`",
    "timeout": 60
  }'
```

### 4. Get Supported Languages
**Endpoint**: `GET /languages`  
**Purpose**: List all supported programming languages  
**Response**:
```json
{
  "languages": ["python", "javascript"]
}
```

---

## 🔧 Technical Specifications

### Server Infrastructure
- **Platform**: GitHub Codespaces (Debian GNU/Linux 13)
- **Runtime**: Python 3.14
- **Web Framework**: FastAPI 0.121.0
- **ASGI Server**: Uvicorn 0.38.0
- **Process Manager**: systemd-compatible

### Dependencies
```
fastapi>=0.115.0
uvicorn[standard]>=0.30.0
pydantic>=2.9.0
python-multipart>=0.0.6
requests>=2.31.0
google-cloud-bigquery>=3.11.0
```

### Security Features
- Sandboxed code execution (subprocess isolation)
- Timeout enforcement (prevents infinite loops)
- Memory limits (prevents resource exhaustion)
- No shell access (code runs in controlled environment)
- CORS enabled (allows cross-origin requests)

### Limitations
- **Execution timeout**: 30 seconds (code execution), 60 seconds (BigQuery)
- **Max results**: 1000 rows per BigQuery query
- **No file system access**: Code cannot write to disk
- **No network access**: Code cannot make external requests
- **Memory**: Limited by container resources

---

## 📊 BigQuery Access Details

### Google Cloud Project
- **Project ID**: `jibber-jabber-knowledge`
- **Service Account**: Pre-configured on server
- **Credentials Location**: `/workspace/gridsmart_service_account.json`

### Available Datasets
The service account has access to datasets in the `jibber-jabber-knowledge` project. To query tables from other projects (like `inner-cinema-476211-u9`), use fully qualified table names:

```sql
SELECT * FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_fuelinst_iris` LIMIT 10
```

### Query Best Practices
1. **Always use LIMIT**: Prevent large result sets
2. **Use specific columns**: Don't use `SELECT *` on large tables
3. **Add WHERE clauses**: Filter data at query time
4. **Use backticks**: Properly escape table names with special characters
5. **Test queries**: Start with `LIMIT 1` to verify schema

### Example Queries

**Get row count**:
```sql
SELECT COUNT(*) as total FROM `project.dataset.table`
```

**Get latest data**:
```sql
SELECT * FROM `project.dataset.table`
ORDER BY timestamp DESC
LIMIT 10
```

**Filter by date**:
```sql
SELECT * FROM `project.dataset.table`
WHERE DATE(timestamp) = CURRENT_DATE()
LIMIT 100
```

**Aggregate data**:
```sql
SELECT 
  DATE(timestamp) as date,
  COUNT(*) as records,
  AVG(value) as avg_value
FROM `project.dataset.table`
GROUP BY date
ORDER BY date DESC
LIMIT 30
```

---

## 🧪 Testing the API

### Quick Health Check
```bash
curl https://super-duper-engine-wr46657556g6f5jpq-8000.app.github.dev/health
```

### Test Code Execution
```bash
curl -X POST "https://super-duper-engine-wr46657556g6f5jpq-8000.app.github.dev/execute" \
  -H "Content-Type: application/json" \
  -d '{
    "code": "import datetime; print(datetime.datetime.now())",
    "language": "python"
  }'
```

### Test BigQuery
```bash
curl -X POST "https://super-duper-engine-wr46657556g6f5jpq-8000.app.github.dev/query_bigquery" \
  -H "Content-Type: application/json" \
  -d '{
    "sql": "SELECT 1 as test_number, CURRENT_TIMESTAMP() as current_time",
    "timeout": 30
  }'
```

---

## 🔍 Error Handling

### Common Error Responses

**Invalid Request**:
```json
{
  "detail": [
    {
      "loc": ["body", "code"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

**Code Execution Error**:
```json
{
  "output": "",
  "error": "NameError: name 'undefined_variable' is not defined",
  "exit_code": 1,
  "execution_time": 0.045,
  "timestamp": "2025-11-06T20:35:00.000000"
}
```

**BigQuery Error**:
```json
{
  "success": false,
  "data": null,
  "row_count": null,
  "error": "Syntax error: Expected end of input but got keyword SELECT",
  "execution_time": 0.123,
  "timestamp": "2025-11-06T20:35:00.000000"
}
```

**Timeout Error**:
```json
{
  "output": "",
  "error": "Command timed out after 30 seconds",
  "exit_code": -1,
  "execution_time": 30.0,
  "timestamp": "2025-11-06T20:35:00.000000"
}
```

---

## 💡 Usage Examples for ChatGPT

### Example 1: Get Current Data from BigQuery
```json
{
  "sql": "SELECT * FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_fuelinst_iris` WHERE DATE(settlementDate) = CURRENT_DATE() LIMIT 10"
}
```

### Example 2: Calculate Statistics
```json
{
  "sql": "SELECT fuel_type, COUNT(*) as records, AVG(generation) as avg_generation FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_fuelinst_iris` WHERE DATE(settlementDate) >= DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY) GROUP BY fuel_type ORDER BY avg_generation DESC"
}
```

### Example 3: Execute Python Data Analysis
```json
{
  "code": "import json\nimport statistics\ndata = [1, 2, 3, 4, 5]\nresult = {\n    'mean': statistics.mean(data),\n    'median': statistics.median(data),\n    'stdev': statistics.stdev(data)\n}\nprint(json.dumps(result))",
  "language": "python",
  "timeout": 30
}
```

### Example 4: Complex BigQuery with Joins
```json
{
  "sql": "SELECT a.*, b.additional_field FROM `project.dataset.table_a` a LEFT JOIN `project.dataset.table_b` b ON a.id = b.id WHERE a.status = 'active' LIMIT 50",
  "timeout": 90,
  "max_results": 50
}
```

---

## 🚀 Integration Checklist

For ChatGPT to successfully use this API:

- [x] Server is running and accessible
- [x] Port 8000 is public
- [x] CORS is enabled
- [x] BigQuery endpoint is functional
- [x] Service account credentials are configured
- [x] Project ID is correct (`jibber-jabber-knowledge`)
- [x] All dependencies are installed
- [x] API documentation is accessible
- [x] Health check returns 200 OK
- [x] Test queries execute successfully

---

## 📞 Support & Troubleshooting

### Check Server Status
```bash
curl https://super-duper-engine-wr46657556g6f5jpq-8000.app.github.dev/health
```

### View Server Logs
```bash
tail -f /workspaces/overarch-jibber-jabber/codex-server/server.log
```

### Restart Server
```bash
cd /workspaces/overarch-jibber-jabber
bash codex-server/server-stop.sh
bash codex-server/server-start.sh
```

### Common Issues

**Issue**: "Service account not found"  
**Solution**: Ensure `/workspace/gridsmart_service_account.json` exists

**Issue**: "403 Access Denied" on BigQuery  
**Solution**: Verify service account has BigQuery permissions in the project

**Issue**: "Timeout" errors  
**Solution**: Increase timeout value in request or optimize query

**Issue**: Connection refused  
**Solution**: Check if server is running and port is public

---

## 📝 Notes

- Server URL may change if Codespace is restarted
- Service account credentials are environment-specific
- All timestamps are in ISO 8601 format (UTC)
- BigQuery queries use Standard SQL (not Legacy SQL)
- Code execution is sandboxed and stateless

---

**Document Version**: 1.0  
**Server Uptime**: Started November 6, 2025  
**Maintained by**: George Major (@GeorgeDoors888)

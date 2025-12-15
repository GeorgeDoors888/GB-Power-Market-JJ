# GitHub Copilot Prompt Library

This is a collection of **tested, working prompts** for common tasks in the GB Power Market JJ project. Copy/paste and adapt as needed.

---

## 🔍 Exploration & Understanding

### Understand Architecture
```
"Explain the difference between the IRIS real-time pipeline and the historical batch pipeline. #reader #codebase"

"How does the dual-pipeline architecture work for getting complete timelines? Show me query patterns. #reader"

"Where is the bmrs_costs table queried in the codebase? #codebase #usages"

"Explain how battery VLP revenue calculation works. #reader"
```

### Find Code
```
"Show me all files that query BigQuery. #codebase"

"Where is MPAN parsing implemented? #usages"

"Find all references to the inner-cinema-476211-u9 project ID. #codebase"

"What functions call the BigQuery client? #usages"
```

### Understand Data
```
"What columns are available in bmrs_bod table? Check STOP_DATA_ARCHITECTURE_REFERENCE.md #fetch"

"Explain the difference between SSP and SBP in bmrs_costs. #reader"

"What's the schema for bmrs_fuelinst vs bmrs_fuelinst_iris? #codebase"

"Show me how to handle duplicates in bmrs_costs. #reader"
```

---

## 🐛 Debugging

### Find Issues
```
"What's currently failing in the workspace? #problems"

"Why is this BigQuery query returning duplicates? #reader #codebase"

"Debug why the DNO lookup is returning the wrong distributor ID. #reader #usages"

"Check for common BigQuery mistakes in this file. #reader"
```

### Trace Execution
```
"Trace through the IRIS upload pipeline from Azure Service Bus to BigQuery. #codebase"

"How does data flow from ingest_elexon_fixed.py to BigQuery? #reader"

"Show me the execution path for the DNO webhook. #usages"
```

### Analyze Errors
```
"Analyze this error and suggest fixes: [paste error]. #reader #problems"

"Why am I getting 'Table not found in europe-west2' errors? #reader"

"Debug this 'Unrecognized name: recordTime' BigQuery error. #reader"
```

---

## ✏️ Code Changes

### Fix Issues
```
"Fix all lint errors in this file. #ship"

"Fix the BigQuery location error - should use 'US' not 'europe-west2'. #ship"

"Update this query to use the correct project ID (inner-cinema-476211-u9). #ship"

"Add error handling to this BigQuery query with retry logic. #ship"
```

### Add Features
```
"Add type hints to all function signatures in this file. #ship"

"Add comprehensive logging using Python's logging module. #ship"

"Add docstrings to all public functions following Google style. #ship"

"Add validation for MPAN format before parsing. #ship"
```

### Refactor
```
"Extract these BigQuery queries into a separate queries.py module. #ship"

"Refactor this duplicated code into a reusable utility function. #ship"

"Simplify this nested logic using early returns. #ship"

"Convert this script to use environment variables for configuration. #ship"
```

---

## 🧪 Testing

### Write Tests
```
"Write pytest unit tests for the extract_core_from_full_mpan function. #ship"

"Add integration tests for the BigQuery query in this file. #ship"

"Create mock responses for the BigQuery client. #ship"

"Add test cases for edge cases: empty input, invalid MPAN, missing data. #ship"
```

### Run Tests
```
"Run the tests and show me failures. #ship #terminal"

"Run only the tests in test_dno_lookup.py. #ship #terminal"

"Fix failing tests in this file. #ship"
```

---

## 📊 BigQuery Queries

### Write Queries
```
"Write a BigQuery query to get daily average System Sell Price for last 30 days 
from bmrs_costs and bmrs_costs_iris. Use UNION pattern for complete timeline. #ship"

"Create a query to find top 10 VLP units by total volume in last 7 days. 
Use bmrs_boalf table. #ship"

"Write a query to calculate battery arbitrage potential (2hr discharge) 
using price spreads from bmrs_costs. Handle duplicates with GROUP BY. #ship"
```

### Optimize Queries
```
"Optimize this query to reduce cost - add filters before aggregations. #ship"

"Add date range filters to this query to avoid scanning full table. #ship"

"Rewrite this query to use partitioning efficiently. #ship"
```

### Debug Queries
```
"Why is this query returning unexpected duplicates? #reader"

"Check this query for schema errors - verify column names exist. #reader"

"Test this query with LIMIT 100 first. #ship #terminal"
```

---

## 📝 Documentation

### Generate Docs
```
"Generate API documentation for all functions in this module. #ship"

"Add a README.md for this directory explaining its purpose. #ship"

"Create inline comments explaining this complex logic. #ship"

"Document the environment variables required by this script. #ship"
```

### Update Docs
```
"Update STOP_DATA_ARCHITECTURE_REFERENCE.md with schema for new IRIS tables. #ship"

"Add this feature to the main README.md. #ship"

"Document the webhook endpoint in API_REFERENCE.md. #ship"
```

---

## 🔐 Security & Quality

### Security Review
```
"Review this file for security issues: hardcoded secrets, exposed credentials. #reader"

"Check for SQL injection vulnerabilities in this query builder. #reader"

"Scan for accidentally committed API keys or tokens. #codebase"

"Audit this webhook endpoint for security best practices. #reader"
```

### Code Quality
```
"Review this code for Python best practices. #reader"

"Check for type safety issues. #reader"

"Suggest improvements for error handling. #reader"

"Find potential performance bottlenecks. #reader"
```

---

## 🚀 Deployment & Ops

### Deploy
```
"Show me the steps to deploy the IRIS pipeline to production. #reader"

"Generate systemd service file for this Python script. #ship"

"Create a Dockerfile for this application. #ship"
```

### Monitor
```
"Add health check endpoint to this Flask app. #ship"

"Create a monitoring script that checks BigQuery table freshness. #ship"

"Add metrics logging for query performance. #ship"
```

---

## 📊 Dashboard & Sheets

### Google Sheets
```
"Write code to update Google Sheet [ID] with BigQuery results using gspread. #ship"

"Add error handling for Sheets API rate limits. #ship"

"Create Apps Script code to call this webhook endpoint. #ship"
```

### Dashboard Updates
```
"Refresh the dashboard by running update_analysis_bi_enhanced.py. #ship #terminal"

"Add a new chart to the dashboard showing frequency trends. #ship"

"Format the BESS sheet with proper headers and number formatting. #ship"
```

---

## 🔧 Git & Version Control

### Commits
```
"Generate a commit message for my staged changes."

"Review my staged changes and summarize what changed. #changes"

"Check if I accidentally staged any secrets or credentials. #changes"
```

### PRs
```
"Create a PR description for these changes using #github-pull-request_copilot-coding-agent"

"Summarize the diff between main and this branch. #changes"

"Check what files changed and why. #changes"
```

---

## 🎯 Project-Specific Prompts

### MPAN/DNO Lookup
```
"Parse this MPAN and extract the distributor ID: [MPAN]. Use mpan_generator_validator. #ship"

"Query BigQuery for DNO details for distributor ID 14. #ship #terminal"

"Update the BESS sheet with DNO rates for voltage HV. #ship"
```

### VLP Analysis
```
"Analyze battery VLP revenue for unit FBPGM002 in last 30 days. 
Query bmrs_boalf for acceptances, bmrs_costs for prices. #ship"

"Calculate arbitrage opportunity using peak/off-peak spread. #ship"

"Find high-value periods (>£70/MWh) for aggressive deployment. #ship"
```

### IRIS Pipeline
```
"Check if IRIS data is fresh for bmrs_fuelinst_iris. #ship #terminal"

"Show me the latest 10 rows from bmrs_freq_iris. #ship #terminal"

"Verify IRIS uploader is running on the AlmaLinux server. #ship #terminal"
```

### Data Quality
```
"Check table coverage for bmrs_bod using check_table_coverage.sh. #ship #terminal"

"Validate that UNION query doesn't create duplicates. #ship"

"Compare row counts between historical and IRIS tables. #ship #terminal"
```

---

## 🎓 Learning & Onboarding

### Learn Codebase
```
"Give me a tour of the codebase structure. #reader #codebase"

"Explain the purpose of each directory in the repo. #reader"

"What are the main entry points / scripts to know about? #codebase"

"Walk me through a typical data ingestion flow. #reader"
```

### Learn Patterns
```
"Show me examples of how to query BigQuery in this project. #codebase"

"What's the standard pattern for error handling here? #reader"

"How do we handle authentication to Google services? #codebase"

"Show me the naming conventions used for BigQuery tables. #reader"
```

---

## 🛠️ Tool Set Examples

### Using #reader (safe exploration)
```
"#reader Explain the IRIS pipeline architecture"

"#reader Where is bmrs_costs queried?"

"#reader What's currently broken? Show errors."

"#reader How does battery revenue calculation work?"
```

### Using #ship (make changes)
```
"#ship Fix the BigQuery project ID in this file"

"#ship Add type hints to all functions"

"#ship Run the tests and fix failures"

"#ship Deploy the updated webhook server"
```

---

## 💡 Pro Tips

### Be Specific
❌ "Fix this"  
✅ "Fix the BigQuery location error on line 45 - should use 'US' not 'europe-west2'"

### Provide Context
❌ "Add tests"  
✅ "Add pytest unit tests for extract_core_from_full_mpan() with test cases for: valid MPAN, invalid format, empty string"

### Use Tool Sets
❌ "Look at the code and maybe check errors and also search for X"  
✅ "#reader Show me all usages of mpan_generator_validator"

### Combine Tools
✅ "Find all BigQuery queries that might have location errors. #codebase #problems"  
✅ "Review my changes and generate a commit message. #changes"  
✅ "Check for errors in recently modified files. #changes #problems"

### Iterate
✅ Start with #reader to understand, then use #ship to fix  
✅ Test with LIMIT first, then run full query  
✅ Run lint/tests after each change

---

## 🚨 Common Mistakes to Avoid

### ❌ Asking Without Context
```
Bad: "Fix the error"
Good: "Fix this BigQuery error: 'Table not found in europe-west2'. 
      The table is in location 'US' in project inner-cinema-476211-u9."
```

### ❌ Too Broad
```
Bad: "Improve this file"
Good: "Add error handling for BigQuery API failures and add logging 
      at INFO level for successful queries, ERROR for failures."
```

### ❌ Not Using Tool Sets
```
Bad: [no hashtags, Copilot guesses what tools to use]
Good: "#reader #codebase #usages [your question]"
```

---

*Last updated: December 2025*  
*See also: CONTRIBUTING.md, docs/copilot-agents.md*

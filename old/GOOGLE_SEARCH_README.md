# Google Search API Integration for Energy Research

🔍 **Comprehensive Google Search integration using your existing `jibber_jabber_key.json` service account**

This integration adds powerful web search capabilities to your BMRS energy data analysis pipeline, enabling enhanced research, market intelligence, and regulatory tracking.

## 🚀 Quick Start

### 1. Setup (One-time)

```bash
# Run the automated setup
python setup_google_search.py

# Follow the prompts to:
# ✅ Validate your service account
# ✅ Enable Custom Search API
# ✅ Create Custom Search Engine
# ✅ Test functionality
```

### 2. Configuration Required

You'll need to:
1. **Enable Custom Search API** in Google Cloud Console
2. **Create a Custom Search Engine** at https://cse.google.com/
3. **Set your Search Engine ID** when prompted

### 3. Usage Examples

```bash
# Search energy news
python search_cli.py news "renewable energy wind" --days 7

# Research companies (with BMRS data integration)
python search_cli.py company "National Grid" --include-bmrs

# Find government documents
python search_cli.py gov "net zero strategy" --file-type pdf

# Analyze market trends
python search_cli.py trends "battery storage" --days 14

# Track regulatory updates
python search_cli.py regulatory
```

## 📁 Files Created

| File                        | Purpose                                       |
| --------------------------- | --------------------------------------------- |
| `google_search_api.py`      | Core search API client with authentication    |
| `energy_research_engine.py` | BMRS + Search integration for energy research |
| `search_cli.py`             | Command-line interface for easy usage         |
| `setup_google_search.py`    | Automated setup and configuration script      |

## 🔧 Technical Features

### Authentication
- ✅ Uses your existing `jibber_jabber_key.json` service account
- ✅ No additional credentials needed
- ✅ Secure OAuth2 authentication

### Search Capabilities
- 🌐 **Web Search**: General web search with filtering
- 📰 **News Search**: Recent news with date filtering
- 🏛️ **Government Documents**: UK gov.uk document search
- 🖼️ **Image Search**: Energy-related image discovery
- 📊 **Market Research**: Combined search + BMRS data analysis

### Smart Features
- 🚀 **Rate Limiting**: Automatic API rate limiting protection
- 💾 **Caching**: Results caching with TTL (1 hour default)
- 📈 **Analytics**: BigQuery integration for search analytics
- 🎯 **Filtering**: Advanced search filters (date, site, file type)

## 🏗️ API Architecture

### Core Classes

```python
# Main search client
search_api = GoogleSearchAPI()

# Enhanced research engine (combines with BMRS data)
research_engine = EnergyResearchEngine()
```

### Key Methods

```python
# Basic search
results = search_api.search(
    query="renewable energy UK",
    num_results=10,
    search_type="web",
    date_restrict="m1"  # Last month
)

# Energy company research (with BMRS data)
company_data = research_engine.research_energy_company("National Grid")

# Market trends analysis
trends = research_engine.research_market_trends("battery storage", days_back=7)
```

## 📊 BMRS Integration

The energy research engine combines Google Search with your BMRS data:

- 🔍 **Company Lookup**: Find BM units for searched companies
- 📈 **Trend Correlation**: Match search trends with BMRS data patterns
- 📊 **Market Analysis**: Combine news sentiment with actual market data
- 🏢 **Company Profiles**: Complete company research with operational data

### Example BMRS + Search Integration

```python
# Research a company
company_research = research_engine.research_energy_company("National Grid")

print(f"BMRS Units: {company_research['bmrs_data']['total_units']}")
print(f"Recent News: {len(company_research['news']['items'])}")
print(f"Gov Docs: {len(company_research['government_documents']['pdf']['items'])}")
```

## 🛠️ Configuration Options

### Environment Variables
```bash
# Required
export GOOGLE_SEARCH_ENGINE_ID="your_custom_search_engine_id"

# Optional (uses service account by default)
export GOOGLE_API_KEY="your_api_key"

# BigQuery project (already configured)
export GOOGLE_CLOUD_PROJECT="jibber-jabber-knowledge"
```

### Search Parameters

| Parameter       | Description               | Example              |
| --------------- | ------------------------- | -------------------- |
| `num_results`   | Results to return (1-100) | `10`                 |
| `search_type`   | Type: web, news, image    | `"news"`             |
| `date_restrict` | Time filter               | `"d7"` (last 7 days) |
| `site_search`   | Restrict to site          | `"gov.uk"`           |
| `file_type`     | File type filter          | `"pdf"`              |
| `language`      | Language filter           | `"lang_en"`          |
| `country`       | Country filter            | `"countryUK"`        |

## 🎯 Use Cases

### 1. Market Intelligence
- Monitor news about energy companies in your BMRS data
- Track regulatory announcements affecting energy markets
- Research new market entrants and technology developments

### 2. Company Research
- Comprehensive profiles combining operational data + web presence
- Financial news and analyst reports
- Government contracts and regulatory filings

### 3. Regulatory Tracking
- Monitor Ofgem consultations and decisions
- Track government energy policy changes
- Find technical standards and grid code updates

### 4. Academic Research
- Find peer-reviewed research on energy topics
- Discover government reports and whitepapers
- Access technical documentation from industry bodies

## 🔒 Security & Rate Limits

- **Authentication**: Secure service account authentication
- **Rate Limiting**: Built-in request throttling (100ms between requests)
- **Caching**: Reduces API calls with intelligent caching
- **Error Handling**: Graceful handling of API limits and errors

## 📈 Analytics Integration

Search activity is automatically logged to BigQuery for analysis:

```sql
-- Example: Analyze search patterns
SELECT
    query,
    COUNT(*) as search_count,
    AVG(results_count) as avg_results
FROM `jibber-jabber-knowledge.uk_energy_insights.google_search_analytics`
WHERE timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 7 DAY)
GROUP BY query
ORDER BY search_count DESC
```

## 🚨 Important Notes

### API Setup Required
1. **Enable Custom Search API** in Google Cloud Console
2. **Create Custom Search Engine** at https://cse.google.com/
3. **Configure search sites** (recommend: *, *.gov.uk, *.ac.uk)

### Costs
- Custom Search API: **$5 per 1000 queries** after 100 free daily queries
- Monitor usage in Google Cloud Console

### Rate Limits
- **100 queries per day** (free tier)
- **10 queries per second** maximum
- Built-in rate limiting prevents exceeded limits

## 🔄 Integration with Your Pipeline

This search integration is designed to work seamlessly with your existing BMRS pipeline:

```python
# Example: Enhance your data analysis
from google_search_api import GoogleSearchAPI
from energy_research_engine import EnergyResearchEngine

# Your existing BMRS analysis
def analyze_company_performance(company_name):
    # ... your existing BMRS analysis ...

    # Enhance with web research
    research_engine = EnergyResearchEngine()
    web_data = research_engine.research_energy_company(company_name)

    return {
        'bmrs_analysis': bmrs_results,
        'market_intelligence': web_data,
        'timestamp': datetime.now().isoformat()
    }
```

## 📞 Support

If you encounter issues:
1. Run `python setup_google_search.py` to validate configuration
2. Check that Custom Search API is enabled in Google Cloud Console
3. Verify your Custom Search Engine ID is correct
4. Ensure `jibber_jabber_key.json` has proper permissions

---

**🎉 This integration transforms your BMRS data pipeline into a comprehensive energy market intelligence platform!**

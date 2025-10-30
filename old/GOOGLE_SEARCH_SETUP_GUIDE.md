# Google Custom Search JSON API - Setup Guide

## 📋 Prerequisites

You need:
1. **Google API Key** with Custom Search JSON API enabled
2. **Custom Search Engine ID** (cx parameter)

## 🔧 Step-by-Step Setup

### Step 1: Create Google API Key

1. Go to [Google Cloud Console](https://console.developers.google.com/)
2. Create a new project or select existing project
3. Enable the **Custom Search JSON API**:
   - Go to "APIs & Services" > "Library"
   - Search for "Custom Search JSON API"
   - Click "Enable"
4. Create API credentials:
   - Go to "APIs & Services" > "Credentials"
   - Click "Create Credentials" > "API Key"
   - Copy your API key (keep it secure!)

### Step 2: Create Custom Search Engine

1. Go to [Google Custom Search](https://cse.google.com/cse/)
2. Click "Add" to create a new search engine
3. Configure your search engine:
   - **Sites to search**: Enter `*.gov.uk` and `*.co.uk` (for UK DNO data)
   - **Name**: "UK DNO Data Search" (or your preference)
   - **Language**: English
4. Click "Create"
5. Copy your **Search Engine ID** (cx parameter)

### Step 3: Set Up Environment Variables

Create a `.env.search` file in your project directory:

```bash
# Google Custom Search JSON API Configuration
GOOGLE_SEARCH_API_KEY=your_api_key_here
GOOGLE_SEARCH_ENGINE_ID=your_search_engine_id_here
```

### Step 4: Install Dependencies

```bash
pip install requests pandas
```

### Step 5: Test Setup

Run the setup script:

```bash
python google_search_setup.py
```

## 🔍 Usage Examples

### Basic Search
```python
from google_search_setup import GoogleCustomSearch

# Initialize client
search = GoogleCustomSearch()

# Perform search
results = search.search("SSEN DUoS charges")
```

### DNO-Specific Search
```python
# Search for specific DNO data
dno_results = search.search_dno_data(
    dno_name="Northern Powergrid",
    data_types=["DUoS charges", "distribution tariffs"]
)
```

### Advanced Search Options
```python
# Search with filters
results = search.search(
    query="distribution charges",
    file_type="xlsx",
    site_search="ssen.co.uk",
    num_results=10
)
```

## 📊 DNO Search Targets

The setup includes pre-configured searches for:

- **SSEN**: Scottish Hydro Electric Power Distribution (SHEPD) & Southern Electric Power Distribution (SEPD)
- **Northern Powergrid**: North East & Yorkshire
- **National Grid Electricity Distribution**: East Midlands, West Midlands, South West, South Wales
- **SP Energy Networks**: SPD & SPM
- **Electricity North West**: ENWL

## 🔧 API Limits

- **Free Tier**: 100 searches per day
- **Paid Tier**: Up to 10,000 searches per day
- **Results per Query**: Maximum 10 results
- **Total Results**: Up to 100 results per query (with pagination)

## 🛡️ Security Best Practices

1. **Never commit API keys** to version control
2. **Use environment variables** for credentials
3. **Restrict API key usage** in Google Cloud Console
4. **Monitor API usage** to avoid unexpected charges

## 🚨 Troubleshooting

### Common Issues:

1. **"API key not valid"**
   - Check API key is correct
   - Ensure Custom Search JSON API is enabled
   - Verify API key restrictions

2. **"Invalid search engine"**
   - Check Search Engine ID (cx parameter)
   - Ensure search engine is public

3. **"Quota exceeded"**
   - Check daily usage limits
   - Consider upgrading to paid tier

4. **"No results found"**
   - Try broader search terms
   - Check site restrictions
   - Verify DNO websites are indexed

## 💡 Tips for DNO Data Discovery

1. **Target File Types**: Focus on `.xlsx`, `.pdf`, `.csv` files
2. **Site Restrictions**: Use `site:*.gov.uk` or `site:dnoname.co.uk`
3. **Keywords**: "DUoS", "charges", "tariffs", "connection", "distribution"
4. **Combine Terms**: "Northern Powergrid DUoS charges site:northernpowergrid.com"

## 📈 Next Steps

After setup:
1. Run demo searches to find DNO data sources
2. Analyze found URLs for data patterns
3. Automate data extraction from discovered sources
4. Integrate with BigQuery for storage

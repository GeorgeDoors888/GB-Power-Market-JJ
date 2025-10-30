# ELEXON Data Freshness Strategy

This document outlines our comprehensive strategy for ensuring access to the most up-to-date UK energy market data from Elexon.

## Data Freshness Requirements

Our analysis requires access to near real-time energy market data, including:
- Imbalance prices (IMBALNGC)
- Physical Notifications (PN)
- Bid-Offer Data (BOD)
- System frequency (FREQ)
- Generation by fuel type (FUELINST)
- Other market indicators

## Our Multi-Pronged Approach

We employ a complementary strategy using both pull and push-based data collection methods:

### 1. API-Based Collection (Pull)

#### Daily Batch Ingestion
- **Script**: `ingest_elexon_fixed.py`
- **Purpose**: Collect complete datasets for entire days
- **Schedule**: Runs once daily to collect previous day's data
- **Advantages**: Comprehensive, handles historical data well
- **Limitations**: Not suitable for near real-time data

#### Recent Data Fetching
- **Script**: `fetch_recent_elexon.py`
- **Purpose**: Retrieve very recent data (last 30 minutes)
- **Schedule**: Runs every 15-30 minutes
- **Advantages**: Gets latest data with minimal delay
- **Limitations**: Makes frequent API calls, potential rate limiting

### 2. IRIS-Based Collection (Push)

#### Real-Time Data Streaming
- **Implementation**: `elexon_iris/client.py`
- **Purpose**: Receive data immediately as it's published
- **Mechanism**: Azure Service Bus queue with push notifications
- **Advantages**:
  - Lowest possible latency
  - No polling required
  - No API rate limits
- **Limitations**:
  - Limited to 3 days of data retention
  - Requires persistent connection

## Integration Strategy

### Primary Data Flow
1. **IRIS Client** continuously receives and stores the most recent data
2. **Recent Data Fetcher** runs periodically as a backup for IRIS
3. **Daily Batch Ingestion** ensures complete historical datasets

### BigQuery Integration
- IRIS data is processed by `iris_to_bigquery.py` every 5 minutes
- Uses the same schema and structure as API-collected data
- Deduplication ensures no duplicate records between collection methods

### Monitoring and Alerting
- Monitor IRIS client uptime and connectivity
- Check for data gaps in both collection methods
- Alert if either method fails to collect data for an extended period

## Publication Timing Considerations

- **Settlement Periods**: UK energy market operates in 30-minute settlement periods
- **Indicative Prices**: Published ~15 minutes after a settlement period ends
- **Final Prices**: Published later, with various settlement runs

Our strategy accounts for these timing considerations:
- IRIS receives data as soon as it's published
- Recent data fetcher runs after the 15-minute publication delay
- Daily batch ingestion ensures we have the most complete data

## Implementation Details

### IRIS Setup
- See `elexon_iris/ELEXON_IRIS_SETUP.md` for detailed setup instructions
- Client credentials required from https://bmrs.elexon.co.uk/iris

### API Authentication
- API key management handled in environment variables
- See `api.env` for configuration

## Contingency Plans

If IRIS connection fails:
1. Rely on `fetch_recent_elexon.py` for recent data
2. Monitor for connectivity issues
3. Restart IRIS client when connectivity is restored

If API access fails:
1. Rely on IRIS for real-time data
2. Use BigQuery for historical queries
3. Backfill any gaps when API access is restored

## Future Improvements

- Implement automatic failover between IRIS and API
- Add more comprehensive data quality checks
- Set up cross-validation between data sources
- Create a unified data freshness dashboard

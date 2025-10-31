# 🚀 Future Analytics & Data Integration TODO

## 📊 Current State - Excellent Foundation!

### ✅ What We Have Now:
- **1.4+ BILLION historic records** in BigQuery (2022-2025)
- **862 million BOD records** (82 GB) - Bid-Offer Data
- **131 million PN records** (52.5 GB) - Physical Notifications  
- **116 million QPN records** (46.7 GB) - Quiescent Physical Notifications
- **98 million MELS records** (50 GB) - Maximum Export Limits
- **96 million MILS records** (48.7 GB) - Maximum Import Limits
- **19 million FREQ records** - Grid frequency
- **9 million BOALF records** - Bid-Offer Acceptances
- Daily dashboard with live metrics
- Graph data tracking (Settlement Periods 1-48)

**BigQuery Tables:**
- `bmrs_boalf`, `bmrs_bod`, `bmrs_freq`, `bmrs_fuelinst`
- `bmrs_mels`, `bmrs_mils`, `bmrs_pn`, `bmrs_qpn`
- `bmrs_mid`, `bmrs_remit_unavailability`
- Plus more...

---

## 🎯 Planned Analytics Projects

### 1. 📈 Trading Pattern Analysis
**Goal:** Identify profitable trading windows based on historic price patterns

**Tasks:**
- [ ] Analyze System Sell Price patterns by time of day/day of week
- [ ] Identify seasonal trends (winter peaks, summer lows)
- [ ] Calculate price volatility by settlement period
- [ ] Find correlation between demand and price spikes
- [ ] Build predictive model for high-price periods
- [ ] Create trading opportunity alerts

**Data Sources:**
- `bmrs_mid` (Market Index Data - prices)
- `bmrs_fuelinst` (generation levels)
- `bmrs_bod` (bid-offer patterns)

**Output:** Trading strategy dashboard showing:
- Best times to buy/sell
- Expected price ranges by period
- Risk metrics

---

### 2. ⚡ Battery Arbitrage Optimizer
**Goal:** Find optimal charge/discharge times based on price spreads

**Tasks:**
- [ ] Calculate intraday price spreads (high - low)
- [ ] Identify charge windows (lowest prices)
- [ ] Identify discharge windows (highest prices)
- [ ] Account for round-trip efficiency losses (85-90%)
- [ ] Calculate potential revenue per cycle
- [ ] Optimize for degradation (limit cycles per day)
- [ ] Factor in BSUoS costs

**Data Sources:**
- `bmrs_mid` (prices every 30 minutes)
- Historic BSUoS costs
- Grid frequency data (for frequency response opportunities)

**Output:** Battery arbitrage calculator showing:
- Daily revenue potential
- Optimal charge/discharge schedule
- ROI projections

---

### 3. 🔮 Price Forecasting (ML Model)
**Goal:** Predict System Sell Price based on demand/generation

**Tasks:**
- [ ] Feature engineering:
  - Hour of day, day of week, month
  - Total generation, fuel mix percentages
  - Interconnector flows
  - Weather data (if available)
  - Historic prices (lag features)
- [ ] Train ML model (Random Forest, XGBoost, or LSTM)
- [ ] Validate with test set (2024-2025 data)
- [ ] Deploy model for daily predictions
- [ ] Monitor model accuracy
- [ ] Retrain monthly with new data

**Data Sources:**
- `bmrs_fuelinst` (generation)
- `bmrs_mid` (historic prices)
- `bmrs_freq` (system stress indicator)
- `bmrs_mels`/`bmrs_mils` (capacity limits)

**Output:** 
- Price forecast dashboard (next 24-48 hours)
- Confidence intervals
- Model accuracy metrics

---

### 4. 📊 Market Trends Dashboard
**Goal:** Weekly/monthly trends in renewables, pricing, frequency events

**Tasks:**
- [ ] Weekly renewable generation trends
- [ ] Monthly price averages and volatility
- [ ] Frequency excursion analysis (deviations from 50.0 Hz)
- [ ] Capacity margin trends (generation vs demand)
- [ ] Interconnector utilization patterns
- [ ] Year-over-year comparisons

**Data Sources:**
- All existing BigQuery tables
- Time-series aggregations

**Output:** Executive summary dashboard with:
- KPIs (renewable %, avg price, grid stability)
- Trend charts (weekly/monthly/yearly)
- Anomaly detection

---

### 5. 💰 BSUoS Cost Analysis
**Goal:** Historical BSUoS patterns and cost optimization

**Tasks:**
- [ ] Analyze historic BSUoS rates by time of day
- [ ] Identify high-cost periods
- [ ] Calculate cost impact on different consumption profiles
- [ ] Optimize consumption schedules to minimize BSUoS
- [ ] Forecast future BSUoS costs

**Data Sources:**
- Historic BSUoS data (existing CSV files)
- `bmrs_fuelinst` (system demand)
- `bmrs_mid` (market prices)

**Output:** BSUoS optimization tool:
- High-cost period alerts
- Cost-minimized schedules
- Annual cost projections

---

### 6. 🌊 Interconnector Flow Analysis
**Goal:** Cross-border trading patterns and opportunities

**Tasks:**
- [ ] Analyze flow patterns for all 10 interconnectors:
  - NSL (Norway), IFA/IFA2/ElecLink (France)
  - Nemo (Belgium), Viking Link (Denmark)
  - BritNed (Netherlands), Moyle (NI)
  - East-West (Ireland), Greenlink (Ireland)
- [ ] Correlate flows with GB/EU price spreads
- [ ] Identify arbitrage opportunities
- [ ] Predict interconnector utilization

**Data Sources:**
- `bmrs_fuelinst` (interconnector generation)
- `bmrs_mid` (GB prices)
- EU market prices (if available)

**Output:** Interconnector dashboard:
- Real-time flow visualization
- Price spread alerts
- Trading opportunity indicators

---

### 7. ⚠️ Grid Stress Indicator
**Goal:** Predict tight margins using MILS/MELS ratios

**Tasks:**
- [ ] Calculate margin = Available Capacity - Demand
- [ ] Analyze MILS/MELS utilization percentages
- [ ] Identify stress events (margin < threshold)
- [ ] Correlate stress with price spikes
- [ ] Build early warning system
- [ ] Predict system warnings (demand control events)

**Data Sources:**
- `bmrs_mels` (export limits)
- `bmrs_mils` (import limits)
- `bmrs_fuelinst` (actual generation)
- `bmrs_pn`/`bmrs_qpn` (planned availability)

**Output:** Grid stress dashboard:
- Real-time margin indicator
- Stress event alerts
- Historic stress patterns

---

### 8. 📉 Imbalance Price Analysis
**Goal:** Historic spread between System Buy/Sell prices

**Tasks:**
- [ ] Analyze System Buy vs Sell price spreads
- [ ] Identify high-spread events
- [ ] Correlate with system imbalances
- [ ] Calculate imbalance costs for different profiles
- [ ] Optimize generation/consumption to minimize imbalance

**Data Sources:**
- `bmrs_mid` (System Sell Price, System Buy Price)
- `bmrs_bod` (balancing actions)
- `bmrs_boalf` (accepted offers)

**Output:** Imbalance analytics:
- Average spreads by period
- High-spread event analysis
- Cost impact calculator

---

## 🔄 IRIS Real-Time Data Integration

### 📡 About IRIS (Insights Real-Time Information Service)

**What is IRIS?**
- **Real-time push service** for Elexon Balancing Mechanism data
- Based on **AMQP** (Advanced Message Queuing Protocol)
- **FREE** and publicly available
- Near real-time data delivery (seconds/minutes delay)
- **3-day message TTL** (time-to-live)
- Same data format as Insights API

**Perfect for:**
- ✅ Keeping data up-to-date (rolling 3 months)
- ✅ Real-time monitoring and alerts
- ✅ Complementing historic data
- ✅ Live dashboard updates

**Repository:** https://github.com/elexon-data/iris-clients

---

## 🚀 IRIS Integration Plan

### Phase 1: Setup IRIS Client (Python)

**Tasks:**
- [ ] Register at https://bmrs.elexon.co.uk/iris
- [ ] Create queue and get credentials:
  - Client ID
  - Client Secret (expires after 2 years!)
  - Queue Name
  - Service Bus Namespace: `elexon-insights-iris`
  - Tenant ID: `4203b7a0-7773-4de5-b830-8b263a20426e`
- [ ] Configure dataset filters on IRIS portal:
  - BOD (Bid-Offer Data)
  - BOALF (Acceptances)
  - PN (Physical Notifications)
  - QPN (Quiescent)
  - MELS/MILS (Limits)
  - FREQ (Frequency)
  - FUELINST (Generation)
  - MID (Prices)
  - Plus any others needed
- [ ] Clone iris-clients repo
- [ ] Install Python dependencies:
  ```bash
  cd python
  python -m venv .venv
  ./.venv/bin/activate
  pip install -r requirements.txt
  ```
- [ ] Create `settings.json`:
  ```json
  {
    "ClientId": "YOUR_CLIENT_ID",
    "QueueName": "YOUR_QUEUE_NAME",
    "ServiceBusNamespace": "elexon-insights-iris",
    "Secret": "YOUR_SECRET",
    "RelativeFileDownloadDirectory": "./iris_data"
  }
  ```

---

### Phase 2: Adapt IRIS Client for BigQuery

**Current IRIS Client:**
- Receives messages via AMQP
- Saves to local files (JSON)
- Message subject = dataset name (e.g., "BOALF")

**Our Requirements:**
- ✅ Receive messages from IRIS
- ✅ Parse JSON data
- ✅ **Append to existing BigQuery tables** (same schema as historic data)
- ✅ **Add new columns** if IRIS has additional fields
- ✅ Handle schema evolution gracefully
- ✅ Run continuously (background service)

**Tasks:**
- [ ] Create `iris_to_bigquery.py` (based on iris-clients Python example)
- [ ] Modify message processor:
  ```python
  def process_message(msg: ServiceBusReceivedMessage):
      dataset = msg.subject  # e.g., "BOALF"
      data = json.loads(msg.body)
      
      # Determine BigQuery table
      table_name = f"bmrs_{dataset.lower()}"
      
      # Get existing schema
      existing_schema = get_bq_schema(table_name)
      
      # Detect new fields
      new_fields = detect_schema_changes(data, existing_schema)
      
      # Add new columns if needed
      if new_fields:
          add_columns_to_table(table_name, new_fields)
      
      # Insert data
      insert_to_bigquery(table_name, data)
      
      # Complete message (remove from queue)
      receiver.complete_message(msg)
  ```
- [ ] Implement schema evolution:
  - Detect new fields in IRIS data
  - Automatically add columns to BigQuery tables
  - Use NULLABLE mode for new columns
  - Log schema changes
- [ ] Add error handling:
  - Retry failed inserts
  - Dead-letter queue for problematic messages
  - Alert on repeated failures
- [ ] Create systemd service (Linux) or background task (macOS)
- [ ] Add monitoring and logging

---

### Phase 3: Data Merge Strategy

**Challenge:** How to merge IRIS (3-day rolling) with historic data (2022-2025)?

**Strategy:**
1. **Historic data (REST API):** 2022-01-01 to Yesterday
2. **Real-time data (IRIS):** Today onwards (rolling 3 days)
3. **Overlap handling:** 
   - Use `INSERT` for new records
   - Use `MERGE` or `INSERT ... ON CONFLICT` for updates
   - Primary key: Combination of timestamp + BMU ID + dataset-specific fields

**BigQuery Table Structure:**
```sql
-- Each table has these common fields:
- ingested_utc TIMESTAMP  -- When record was inserted
- window_from_utc TIMESTAMP  -- Data start time
- window_to_utc TIMESTAMP  -- Data end time
- settlement_date DATE
- settlement_period INTEGER
-- Plus dataset-specific fields
```

**IRIS Update Pattern:**
```sql
MERGE `project.dataset.bmrs_boalf` AS target
USING (SELECT * FROM UNNEST(@new_records)) AS source
ON target.settlement_date = source.settlement_date
   AND target.settlement_period = source.settlement_period
   AND target.bmu_id = source.bmu_id
   AND target.bid_offer_level = source.bid_offer_level
WHEN MATCHED THEN UPDATE SET *
WHEN NOT MATCHED THEN INSERT ROW
```

**Tasks:**
- [ ] Implement upsert logic for each dataset
- [ ] Create deduplication queries
- [ ] Test with overlapping data
- [ ] Schedule daily backfill (API) + continuous update (IRIS)

---

### Phase 4: Schema Discovery & Auto-Mapping

**Challenge:** IRIS may have new fields not in historic data

**Solution: Automatic schema evolution**

**Tasks:**
- [ ] Create schema comparison tool:
  ```python
  def compare_schemas(iris_data, bq_table):
      iris_fields = set(iris_data.keys())
      bq_fields = set([f.name for f in bq_table.schema])
      
      new_fields = iris_fields - bq_fields
      missing_fields = bq_fields - iris_fields
      
      return {
          'new_in_iris': new_fields,
          'missing_from_iris': missing_fields
      }
  ```
- [ ] Automatic column addition:
  ```python
  def add_new_columns(table_id, new_fields):
      schema = client.get_table(table_id).schema
      
      for field_name in new_fields:
          # Infer type from data
          field_type = infer_bq_type(field_value)
          
          new_field = bigquery.SchemaField(
              field_name, 
              field_type, 
              mode="NULLABLE"
          )
          schema.append(new_field)
      
      table = client.get_table(table_id)
      table.schema = schema
      client.update_table(table, ["schema"])
  ```
- [ ] Log all schema changes
- [ ] Alert on significant schema differences
- [ ] Create schema version tracking

---

### Phase 5: Production Deployment

**Tasks:**
- [ ] Deploy IRIS client as background service
- [ ] Set up monitoring:
  - Messages received per hour
  - Processing success rate
  - Schema change alerts
  - Error notifications
- [ ] Create health check endpoint
- [ ] Document maintenance procedures
- [ ] Set up automatic restarts on failure
- [ ] Schedule credential renewal reminder (2-year expiry!)

**Deployment Options:**

**Option A: Local Machine (Development)**
```bash
# Run in tmux/screen session
cd "/Users/georgemajor/GB Power Market JJ"
./.venv/bin/python iris_to_bigquery.py
```

**Option B: Cloud Run (Production)**
- Containerize IRIS client
- Deploy to Google Cloud Run
- Auto-scaling based on load
- Integrated with BigQuery

**Option C: VM/Server**
- Create systemd service
- Run 24/7 with auto-restart
- Log rotation

---

## 📋 IRIS Integration Advantages

### ✅ Benefits:

1. **Real-time updates** - Data within seconds/minutes
2. **3-month rolling window** - Perfect for recent analysis
3. **Same format as API** - Easy integration
4. **Free push service** - No polling needed
5. **Reduced API calls** - Save quota for backfills
6. **Live dashboard** - Charts always current
7. **Schema evolution** - Auto-adapt to new fields

### ⚠️ Considerations:

1. **3-day TTL** - Must run client at least every 3 days
2. **Credential expiry** - Renew client secret every 2 years
3. **One connection per queue** - Can't run multiple clients on same queue
4. **Message removal** - Once received, message is gone (can backfill from API if needed)
5. **No historic data** - Only rolling 3 months (use API for backfill)

---

## 🎯 Recommended Implementation Order

### Phase 1: IRIS Setup (1-2 days)
1. Register IRIS account
2. Set up Python client
3. Test message reception
4. Verify data format matches historic data

### Phase 2: Basic BigQuery Integration (2-3 days)
1. Create `iris_to_bigquery.py`
2. Test with one dataset (e.g., FUELINST)
3. Verify data appears in BigQuery
4. Confirm no duplicates

### Phase 3: Schema Evolution (2-3 days)
1. Implement schema comparison
2. Auto-add new columns
3. Test with all datasets
4. Handle edge cases

### Phase 4: Production Deployment (1-2 days)
1. Create background service
2. Set up monitoring
3. Test failover and recovery
4. Document operations

### Phase 5: Analytics Projects (Ongoing)
1. Start with Trading Pattern Analysis
2. Then Battery Arbitrage Optimizer
3. Build ML models for forecasting
4. Create comprehensive dashboards

---

## 📊 Expected Data Flow

```
┌─────────────────────────────────────────────────────────────┐
│  HISTORIC DATA (2022-2025)                                   │
│  Source: Insights API (REST)                                 │
│  Update: Daily backfill for yesterday                        │
│  ↓                                                            │
│  BigQuery Tables (bmrs_*)                                    │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│  REAL-TIME DATA (Rolling 3 days)                             │
│  Source: IRIS (AMQP Push)                                    │
│  Update: Continuous (seconds/minutes)                        │
│  ↓                                                            │
│  iris_to_bigquery.py                                         │
│  ↓                                                            │
│  Schema Evolution Check                                      │
│  ↓                                                            │
│  MERGE/INSERT into BigQuery Tables                           │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│  UNIFIED DATASET                                             │
│  BigQuery: Historic + Real-time                              │
│  ↓                                                            │
│  Analytics & ML Models                                       │
│  ↓                                                            │
│  Dashboards & Alerts                                         │
└─────────────────────────────────────────────────────────────┘
```

---

## 🎉 Summary

With **1.4 billion historic records** and **IRIS real-time integration**, you'll have:

- ✅ Complete historic dataset (2022-2025)
- ✅ Real-time updates (rolling 3 months)
- ✅ Automated schema evolution
- ✅ Unified BigQuery database
- ✅ Foundation for advanced analytics
- ✅ Live dashboards and alerts
- ✅ ML model training capability
- ✅ Trading opportunity detection

**Next Steps:**
1. Complete IRIS registration
2. Set up Python IRIS client
3. Test with single dataset
4. Integrate with BigQuery
5. Deploy as background service
6. Start building analytics!

---

**Last Updated:** 30 October 2025

**Status:** 📋 Planning Phase - Ready to implement!

**Related Files:**
- `TODO_CHARTS_CREATION.md` - Charts pending creation
- `watermarks_high_freq.json` - Current data inventory
- `dashboard_clean_design.py` - Daily dashboard updater

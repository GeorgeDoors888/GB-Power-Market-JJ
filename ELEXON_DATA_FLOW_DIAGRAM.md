# Elexon Data Architecture - Complete Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         ELEXON DATA SOURCES                                 │
└─────────────────────────────────────────────────────────────────────────────┘

┌──────────────────────┐  ┌──────────────────────┐  ┌──────────────────────┐
│   REST API           │  │   IRIS STREAMING     │  │   PORTAL HTTPS       │
│  (Historical 2020+)  │  │   (Real-time 24-48h) │  │  (Reference Files)   │
├──────────────────────┤  ├──────────────────────┤  ├──────────────────────┤
│ • BOD (Bid-Offer)    │  │ • BOD_iris           │  │ • REGISTERED_BMUNITS │
│ • MID (Market Index) │  │ • MID_iris           │  │ • REGISTERED_PARTIES │
│ • FREQ (Frequency)   │  │ • FREQ_iris          │  │ • TLM (Loss Mult)    │
│ • FUELHH (Gen)       │  │ • FUELHH_iris        │  │ • RCRC (Cashflow)    │
│ • FUELINST (Live)    │  │ • FUELINST_iris      │  │ • GSPGCF (Factors)   │
│ • BOALF (Accept)     │  │ • BOALF_iris         │  │ • Calendars          │
│ • costs, disbsad     │  │ • 10+ other topics   │  │ • ❌ MID (duplicate) │
│ • 174 total datasets │  │                      │  │ • ❌ FUELHH (dup)    │
└──────────┬───────────┘  └──────────┬───────────┘  └──────────┬───────────┘
           │                         │                         │
           │ REST queries            │ AMQP streaming          │ HTTPS scripting
           │ (on-demand backfill)    │ (Azure Service Bus)     │ (daily download)
           │                         │                         │
           └─────────────────────────┴─────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                    BIGQUERY: inner-cinema-476211-u9                         │
│                         Dataset: uk_energy_prod                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  📊 TIME-SERIES DATA (113 tables)                                          │
│  ├── bmrs_bod              (2.5M rows, latest: 2025-12-26) [BOD data]     │
│  ├── bmrs_bod_iris         (Real-time variant)                            │
│  ├── bmrs_mid              (32K rows, latest: 2025-12-27) [Market prices] │
│  ├── bmrs_mid_iris         (Real-time variant)                            │
│  ├── bmrs_freq             (45K rows, latest: 2025-12-27 18:29) [Freq]    │
│  ├── bmrs_freq_iris        (Real-time variant)                            │
│  ├── bmrs_fuelhh           (Generation by fuel type)                      │
│  ├── bmrs_fuelhh_iris      (Real-time variant)                            │
│  ├── bmrs_fuelinst         (Instantaneous generation)                     │
│  ├── bmrs_fuelinst_iris    (Real-time variant)                            │
│  ├── bmrs_boalf_complete   (11M rows, acceptances WITH PRICES) ⭐         │
│  ├── bmrs_boalf_iris       (Real-time variant)                            │
│  ├── bmrs_costs            (16K rows, latest: 2025-12-27) [SSP/SBP]      │
│  ├── bmrs_disbsad          (Settlement prices)                            │
│  └── ... 100+ other tables                                                │
│                                                                             │
│  🔑 REFERENCE DATA (2 tables) ✅                                           │
│  ├── dim_party             (351 parties, 18 VLPs identified) ⭐           │
│  │   ├── party_name: "Flexitricity Limited"                              │
│  │   ├── party_id: "FLEXTRCY"                                            │
│  │   ├── is_vlp: TRUE                                                    │
│  │   └── bmu_count: 59 units                                             │
│  └── vlp_unit_ownership    (9 VLP units mapped) ⭐                        │
│      ├── bm_unit: "FBPGM002"                                              │
│      └── vlp_name: "Flexitricity"                                         │
│                                                                             │
│  💰 MART TABLES (Analytics outputs)                                        │
│  └── mart_bm_value_by_vlp_sp (VLP revenue by settlement period) 🆕        │
│      ├── Created: 2025-12-27                                              │
│      └── Test: £157k Flexitricity revenue (Oct 17-23, 2025)              │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         VLP REVENUE CALCULATION                             │
│                     Script: calculate_vlp_revenue.py                        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  STEP 1: Clean BM Unit names                                               │
│  ┌────────────────────────────────────────────────────────────────┐        │
│  │ bmrs_boalf_complete.bmUnit = "2__FBPGM002" (with prefix)      │        │
│  │                          ↓ REGEXP_EXTRACT(r'__(.+)$')         │        │
│  │ clean_bm_unit = "FBPGM002" (prefix stripped)                  │        │
│  └────────────────────────────────────────────────────────────────┘        │
│                                                                             │
│  STEP 2: Join to VLP reference                                             │
│  ┌────────────────────────────────────────────────────────────────┐        │
│  │ JOIN vlp_unit_ownership ON clean_bm_unit = bm_unit            │        │
│  │ → vlp_name = "Flexitricity"                                   │        │
│  └────────────────────────────────────────────────────────────────┘        │
│                                                                             │
│  STEP 3: Calculate revenue                                                 │
│  ┌────────────────────────────────────────────────────────────────┐        │
│  │ accepted_mwh = acceptanceVolume × 0.5  (MW → MWh 30min)       │        │
│  │ gross_value_gbp = accepted_mwh × acceptancePrice              │        │
│  │ → Aggregate by: date, settlementPeriod, vlp_name              │        │
│  └────────────────────────────────────────────────────────────────┘        │
│                                                                             │
│  OUTPUT: mart_bm_value_by_vlp_sp table                                     │
│  ┌────────────────────────────────────────────────────────────────┐        │
│  │ Date: 2025-10-18                                               │        │
│  │ VLP: Flexitricity                                              │        │
│  │ Acceptances: 11                                                │        │
│  │ MWh: 112.0                                                     │        │
│  │ Revenue: £8,797.63                                             │        │
│  │ Avg Price: £91.67/MWh                                          │        │
│  └────────────────────────────────────────────────────────────────┘        │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                          DEPLOYMENT & USAGE                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  🔄 RAILWAY CRON (Automated Daily Updates)                                 │
│  ├── Schedule: 8am UTC (after BOALF data arrives)                         │
│  ├── Command: python3 calculate_vlp_revenue.py <start> <end>              │
│  └── Output: Updates mart_bm_value_by_vlp_sp table                        │
│                                                                             │
│  📊 GOOGLE SHEETS DASHBOARD                                                │
│  ├── Source: Query mart_bm_value_by_vlp_sp via Apps Script                │
│  ├── Refresh: realtime_dashboard_updater.py (every 5 min)                 │
│  └── Visualizations: VLP revenue charts, price trends, acceptance counts  │
│                                                                             │
│  💬 CHATGPT PROXY (Natural Language Queries)                               │
│  ├── Endpoint: https://gb-power-market-jj.vercel.app/api/proxy-v2         │
│  ├── Query: "What was Flexitricity's revenue on Oct 17-23?"               │
│  └── Response: "£157,328 from 258 acceptances, avg price £66/MWh"         │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘


═══════════════════════════════════════════════════════════════════════════════
                             KEY INSIGHTS
═══════════════════════════════════════════════════════════════════════════════

✅ DATA COVERAGE:
   • Historical: 2020-present via REST API (174 datasets, 113 tables ingested)
   • Real-time: Last 24-48h via IRIS streaming (10+ datasets with *_iris tables)
   • Reference: Party/VLP data exists (dim_party + vlp_unit_ownership)
   • Freshness: BOD (1d lag), FREQ/MID/costs (0d lag) ← CURRENT

✅ VLP REVENUE CALCULATION:
   • Input: bmrs_boalf_complete (11M acceptances with prices)
   • Join: vlp_unit_ownership (9 VLP units mapped)
   • Filter: validation_flag='Valid' (42.8% of records pass Elexon filters)
   • Formula: MW × 0.5 × price_gbp_per_mwh = gross_value_gbp
   • Output: mart_bm_value_by_vlp_sp (by date, SP, VLP)

✅ TEST RESULTS (Oct 17-23, 2025):
   • Flexitricity: 258 acceptances, 2,287.5 MWh, £157,328 revenue
   • Average price: £66/MWh (ranging £38-97/MWh across 6 days)
   • Script execution time: <5 seconds

⚠️ SCHEMA QUIRKS:
   • BM Unit prefix: BOALF has "2__FBPGM002" vs reference has "FBPGM002"
   • Solution: REGEXP_EXTRACT(bmUnit, r'__(.+)$') to strip prefix
   • Date types: Mix of TIMESTAMP and DATE requires CAST for joins
   • Validation: Only 42.8% of BOALF records pass validation_flag='Valid'

❌ IDENTIFIED DUPLICATES:
   • Portal MID file → Already have bmrs_mid (API) + bmrs_mid_iris (IRIS)
   • Portal FUELHH file → Already have bmrs_fuelhh + bmrs_fuelhh_iris
   • Frequency tables: 4 tables (bmrs_freq, freq_iris, freq_2025, system_freq)
   • Recommendation: Stop Portal MID/FUELHH ingestion, consolidate freq tables

🎯 PRODUCTION STATUS:
   • VLP revenue calculation: ✅ OPERATIONAL
   • Daily automation: Ready for Railway cron deployment
   • Google Sheets integration: Ready for dashboard updates
   • ChatGPT proxy: Ready for natural language queries
   • Documentation: Complete (ELEXON_DATA_ACCESS_AUDIT.md + this diagram)

═══════════════════════════════════════════════════════════════════════════════

Next Steps:
1. Add to Railway cron for daily updates (0 8 * * *)
2. Expand vlp_unit_ownership to cover all 18 VLPs (181 units remaining)
3. Optional: Add full BM Units reference (2764 total units) for non-VLP analysis
4. Optional: Ingest Portal TLM/RCRC/GSPGCF for advanced pricing analysis

═══════════════════════════════════════════════════════════════════════════════
```

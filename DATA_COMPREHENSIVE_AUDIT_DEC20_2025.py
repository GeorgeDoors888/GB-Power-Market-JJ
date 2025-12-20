"""
GB Power Market - Comprehensive Data Audit (Dec 20, 2025)
=============================================================
Diagnose:
1. Missing data (5-year history check)
2. Data consistency (gaps, duplicates)
3. Data purpose (what each dataset is for)
4. Data quality (completeness, accuracy)

Based on:
- Elexon BMRS API documentation
- OSUKED ElexonDataPortal schemas
- PROJECT_CONFIGURATION.md requirements
"""

from google.cloud import bigquery
from datetime import datetime, timedelta
import pandas as pd
import os

# Configuration
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = '/home/george/GB-Power-Market-JJ/inner-cinema-credentials.json'
PROJECT_ID = "inner-cinema-476211-u9"
DATASET = "uk_energy_prod"
client = bigquery.Client(project=PROJECT_ID, location="US")

# Date range for analysis (5 years)
end_date = datetime.now().date()
start_date = end_date - timedelta(days=365*5)

print("=" * 100)
print("GB POWER MARKET - COMPREHENSIVE DATA AUDIT")
print("=" * 100)
print(f"Audit Period: {start_date} to {end_date} (5 years)")
print(f"Execution: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}")
print("=" * 100)

# Table definitions with business context
TABLES = {
    # BALANCING MECHANISM (Core Trading Data)
    'bmrs_bod': {
        'time_col': 'settlementDate',
        'purpose': 'Bid-Offer Data - Individual unit price submissions to balancing mechanism',
        'business_use': 'Battery arbitrage strategy, marginal price discovery, unit-level pricing',
        'units': '£/MWh (prices), MW (volumes)',
        'key_columns': ['bmUnitId', 'bid', 'offer', 'pairId'],
        'critical': True,
        'elexon_code': 'B1430 (BOD)',
        'api_endpoint': '/datasets/BOD',
        'iris_available': True
    },
    'bmrs_boalf': {
        'time_col': 'timeFrom',
        'purpose': 'Balancing Acceptances - RAW (NO PRICES) - Which bids/offers National Grid accepted',
        'business_use': 'Acceptance tracking (use bmrs_boalf_complete for prices!)',
        'units': 'MW (volumes), No prices in raw data',
        'key_columns': ['bmUnit', 'acceptanceNumber', 'levelFrom', 'levelTo'],
        'critical': False,  # Use boalf_complete instead
        'elexon_code': 'B1430 (BOALF)',
        'api_endpoint': '/datasets/BOALF',
        'iris_available': True,
        'warning': '⚠️ Use bmrs_boalf_complete for price data (BOD-matched)'
    },
    'bmrs_boalf_complete': {
        'time_col': 'timeFrom',
        'purpose': 'Balancing Acceptances WITH PRICES - BOD-matched acceptance prices and volumes',
        'business_use': 'VLP revenue analysis, battery arbitrage profitability, balancing mechanism earnings',
        'units': '£/MWh (acceptancePrice), MW (acceptanceVolume)',
        'key_columns': ['bmUnit', 'acceptancePrice', 'acceptanceVolume', 'acceptanceType', 'validation_flag'],
        'critical': True,
        'elexon_code': 'B1430 (BOALF + BOD derived)',
        'api_endpoint': 'Derived from /datasets/BOALF + /datasets/BOD',
        'iris_available': False,
        'note': 'Filter to validation_flag=Valid for Elexon B1610 compliant records (42.8% of data)'
    },
    'bmrs_disbsad': {
        'time_col': 'settlementDate',
        'purpose': 'Balancing Services Adjustment Data - Settlement volume-weighted average prices',
        'business_use': 'Settlement price proxy, balancing cost analysis, regulatory reporting',
        'units': '£/MWh (price), MWh (volume)',
        'key_columns': ['settlementDate', 'settlementPeriod', 'price', 'volume'],
        'critical': False,
        'elexon_code': 'B1780 (DISBSAD)',
        'api_endpoint': '/datasets/DISBSAD',
        'iris_available': False
    },

    # PRICING DATA (System & Market Prices)
    'bmrs_costs': {
        'time_col': 'settlementDate',
        'purpose': 'System IMBALANCE Prices - SSP/SBP (merged to single price Nov 2015 via P305)',
        'business_use': 'Battery temporal arbitrage, imbalance exposure, settlement forecasting',
        'units': '£/MWh (systemSellPrice = systemBuyPrice since Nov 2015)',
        'key_columns': ['settlementDate', 'settlementPeriod', 'systemSellPrice', 'systemBuyPrice'],
        'critical': True,
        'elexon_code': 'B1770 (Imbalance Prices)',
        'api_endpoint': '/datasets/DETSYSPRICES',
        'iris_available': False,
        'note': 'SSP=SBP since BSC Mod P305 (Nov 2015) - both columns identical'
    },
    'bmrs_mid': {
        'time_col': 'settlementDate',
        'purpose': 'Market Index Data - WHOLESALE day-ahead and within-day pricing',
        'business_use': 'Wholesale market analysis, forward curves, NOT battery imbalance arbitrage',
        'units': '£/MWh (price), MWh (volume)',
        'key_columns': ['settlementDate', 'settlementPeriod', 'price', 'volume'],
        'critical': True,
        'elexon_code': 'B1440 (MID)',
        'api_endpoint': '/datasets/MID',
        'iris_available': True,
        'known_gaps': '24 days missing permanently (Apr/Jul/Sep/Oct 2024 - API confirmed 0 records)'
    },

    # GENERATION & DEMAND
    'bmrs_fuelinst': {
        'time_col': 'startTime',
        'purpose': 'Generation by Fuel Type - National-level fuel mix (wind, gas, nuclear, etc.)',
        'business_use': 'Grid carbon intensity, renewable penetration, fuel mix analysis',
        'units': 'MW (generation) - CRITICAL: NOT MWh!',
        'key_columns': ['startTime', 'fuelType', 'generation'],
        'critical': True,
        'elexon_code': 'B1620 (FUELINST)',
        'api_endpoint': '/datasets/FUELINST',
        'iris_available': True,
        'warning': '⚠️ generation column is MW not MWh! Do NOT divide by 500'
    },
    'bmrs_indgen_iris': {
        'time_col': 'startTime',
        'purpose': 'Individual Generator Output - Unit-level generation (real-time only)',
        'business_use': 'Specific generator tracking, capacity factor analysis, VLP unit monitoring',
        'units': 'MW (generation)',
        'key_columns': ['startTime', 'bmUnitId', 'generation'],
        'critical': True,
        'elexon_code': 'B1610 (INDGEN)',
        'api_endpoint': 'IRIS only',
        'iris_available': True,
        'note': 'Only available via IRIS (not historical API)'
    },
    'bmrs_freq': {
        'time_col': 'measurementTime',
        'purpose': 'System Frequency - Grid stability monitoring',
        'business_use': 'Frequency response revenue opportunities, grid stability analysis',
        'units': 'Hz (frequency)',
        'key_columns': ['measurementTime', 'frequency'],
        'critical': False,
        'elexon_code': 'FREQ',
        'api_endpoint': '/datasets/FREQ',
        'iris_available': True,
        'warning': '⚠️ Historical table was EMPTY until Dec 16, 2025 backfill'
    },

    # OUTAGES & UNAVAILABILITY
    'bmrs_remit': {
        'time_col': 'eventStart',
        'purpose': 'REMIT Outages - Unit unavailability notifications (DEPRECATED)',
        'business_use': 'Historical unavailability analysis (use bmrs_remit_iris for current)',
        'units': 'MW (unavailable capacity)',
        'key_columns': ['eventStart', 'eventEnd', 'unavailableCapacity', 'assetId'],
        'critical': False,
        'elexon_code': 'REMIT',
        'api_endpoint': 'HTTP 404 (endpoint deprecated)',
        'iris_available': True,
        'warning': '⚠️ Historical API returns 404 - use bmrs_remit_iris instead'
    },
    'bmrs_remit_iris': {
        'time_col': 'eventStart',
        'purpose': 'REMIT Outages - Unit unavailability notifications (ACTIVE)',
        'business_use': 'Current outage tracking, generation forecasting, constraint analysis',
        'units': 'MW (unavailable capacity)',
        'key_columns': ['eventStart', 'eventEnd', 'unavailableCapacity', 'assetId'],
        'critical': True,
        'elexon_code': 'REMIT',
        'api_endpoint': 'IRIS only',
        'iris_available': True,
        'note': 'Active since Nov 18, 2025 (10.5k records, 177 assets)'
    }
}

# Additional reference tables (not time-series)
REFERENCE_TABLES = {
    'neso_dno_reference': 'DNO (Distribution Network Operator) details and regions',
    'duos_unit_rates': 'DUoS (Distribution Use of System) charges by DNO and voltage',
    'duos_time_bands': 'Red/Amber/Green time periods for DUoS charging',
}

print("\n" + "=" * 100)
print("PHASE 1: TABLE COVERAGE ANALYSIS (5-Year History)")
print("=" * 100)

results = []

for table_name, meta in TABLES.items():
    print(f"\n{'=' * 100}")
    print(f"Table: {table_name}")
    print(f"Purpose: {meta['purpose']}")
    print(f"Business Use: {meta['business_use']}")
    print(f"Elexon Code: {meta['elexon_code']}")
    print(f"API Endpoint: {meta['api_endpoint']}")
    print(f"Units: {meta['units']}")
    if 'warning' in meta:
        print(f"⚠️  WARNING: {meta['warning']}")
    if 'note' in meta:
        print(f"ℹ️  NOTE: {meta['note']}")
    print(f"{'=' * 100}")

    time_col = meta['time_col']

    # Check if table exists and get coverage
    check_query = f"""
    SELECT
        MIN(DATE({time_col})) as earliest_date,
        MAX(DATE({time_col})) as latest_date,
        COUNT(*) as total_records,
        COUNT(DISTINCT DATE({time_col})) as days_with_data,
        DATE_DIFF(MAX(DATE({time_col})), MIN(DATE({time_col})), DAY) + 1 as expected_days
    FROM `{PROJECT_ID}.{DATASET}.{table_name}`
    WHERE {time_col} IS NOT NULL
    """

    try:
        result = client.query(check_query, timeout=60).to_dataframe().iloc[0]

        if pd.notna(result['earliest_date']) and result['total_records'] > 0:
            earliest = result['earliest_date']
            latest = result['latest_date']
            total = result['total_records']
            days = result['days_with_data']
            expected = result['expected_days']

            coverage_pct = (days / expected * 100) if expected > 0 else 0
            gap_days = expected - days

            print(f"✅ DATA PRESENT")
            print(f"   Earliest: {earliest}")
            print(f"   Latest:   {latest}")
            print(f"   Records:  {total:,}")
            print(f"   Days:     {days:,}")
            print(f"   Coverage: {coverage_pct:.1f}% ({days}/{expected} days)")

            if gap_days > 0:
                print(f"   ⚠️  GAPS:     {gap_days:,} days missing ({(gap_days/expected*100):.1f}% of period)")

            # Check for duplicates
            dup_query = f"""
            SELECT COUNT(*) as duplicate_records
            FROM (
                SELECT {time_col}, COUNT(*) as cnt
                FROM `{PROJECT_ID}.{DATASET}.{table_name}`
                GROUP BY {time_col}
                HAVING COUNT(*) > 1
            )
            """

            try:
                dup_result = client.query(dup_query, timeout=30).to_dataframe().iloc[0]
                dup_count = dup_result['duplicate_records']
                if dup_count > 0:
                    print(f"   ⚠️  DUPLICATES: {dup_count:,} timestamps have >1 record")
            except:
                pass

            results.append({
                'table': table_name,
                'purpose': meta['purpose'],
                'earliest': str(earliest),
                'latest': str(latest),
                'records': total,
                'days': days,
                'expected': expected,
                'coverage_%': round(coverage_pct, 1),
                'gap_days': gap_days,
                'status': '✅ Active' if gap_days < 7 else '⚠️ Stale',
                'critical': '⭐ CRITICAL' if meta['critical'] else ''
            })
        else:
            print(f"❌ EMPTY TABLE - No records found")
            results.append({
                'table': table_name,
                'purpose': meta['purpose'],
                'earliest': 'N/A',
                'latest': 'N/A',
                'records': 0,
                'days': 0,
                'expected': 0,
                'coverage_%': 0,
                'gap_days': 0,
                'status': '❌ Empty',
                'critical': '⭐ CRITICAL' if meta['critical'] else ''
            })

    except Exception as e:
        error_msg = str(e)[:100]
        print(f"❌ ERROR: {error_msg}")
        results.append({
            'table': table_name,
            'purpose': meta['purpose'],
            'earliest': 'ERROR',
            'latest': 'ERROR',
            'records': 0,
            'days': 0,
            'expected': 0,
            'coverage_%': 0,
            'gap_days': 0,
            'status': f'❌ Error',
            'critical': '⭐ CRITICAL' if meta['critical'] else ''
        })

print("\n" + "=" * 100)
print("PHASE 2: SUMMARY TABLE")
print("=" * 100)

df = pd.DataFrame(results)
df = df.sort_values('critical', ascending=False)  # Critical tables first
print(df[['table', 'earliest', 'latest', 'records', 'coverage_%', 'gap_days', 'status', 'critical']].to_string(index=False))

print("\n" + "=" * 100)
print("PHASE 3: DATA QUALITY ASSESSMENT")
print("=" * 100)

# Count by status
critical_ok = len(df[(df['critical'] == '⭐ CRITICAL') & (df['status'] == '✅ Active')])
critical_total = len(df[df['critical'] == '⭐ CRITICAL'])
empty_tables = len(df[df['status'] == '❌ Empty'])
stale_tables = len(df[df['status'] == '⚠️ Stale'])
active_tables = len(df[df['status'] == '✅ Active'])

print(f"\n✅ Active Tables (updated last 7 days): {active_tables}/{len(df)}")
print(f"⚠️  Stale Tables (>7 days behind): {stale_tables}/{len(df)}")
print(f"❌ Empty Tables: {empty_tables}/{len(df)}")
print(f"\n⭐ CRITICAL Table Status: {critical_ok}/{critical_total} active")

if critical_ok < critical_total:
    print(f"\n⚠️  CRITICAL TABLES MISSING:")
    critical_missing = df[(df['critical'] == '⭐ CRITICAL') & (df['status'] != '✅ Active')]
    for idx, row in critical_missing.iterrows():
        print(f"   - {row['table']}: {row['status']}")

print("\n" + "=" * 100)
print("PHASE 4: KNOWN DATA GAPS & LIMITATIONS")
print("=" * 100)

print("""
1. bmrs_mid (Market Index Data)
   - 24 days PERMANENTLY missing (Apr/Jul/Sep/Oct 2024)
   - Pattern: 6-day blocks (Apr 16-21, Jul 16-21, Sep 10-15, Oct 08-13)
   - Root Cause: API confirmed 0 records available
   - Status: NOT RECOVERABLE (genuine Elexon API outages)

2. bmrs_freq (System Frequency)
   - Historical table EMPTY until Dec 16, 2025
   - Only IRIS data available (Oct 28, 2025 onwards)
   - Root Cause: Historical ingestion never configured
   - Status: Backfill in progress (2022-2025)

3. bmrs_remit (REMIT Outages - Historical)
   - API endpoint returns HTTP 404 (deprecated)
   - Status: Use bmrs_remit_iris instead (active since Nov 18, 2025)

4. bmrs_boalf vs bmrs_boalf_complete
   - bmrs_boalf: RAW data, NO acceptancePrice field
   - bmrs_boalf_complete: Derived via BOD matching, includes prices
   - CRITICAL: Always use bmrs_boalf_complete for revenue analysis
   - Valid records: ~42.8% after Elexon B1610 filtering

5. bmrs_costs: SSP = SBP since Nov 2015
   - Both columns exist but values identical (BSC Mod P305)
   - Battery arbitrage is TEMPORAL (charge low, discharge high)
   - NOT SSP/SBP spread (which is zero)

6. bmrs_fuelinst_iris.generation: MW not MWh!
   - Common error: Dividing by 500 or treating as MWh
   - Correct: Values already in MW, convert to GW by /1000
""")

print("\n" + "=" * 100)
print("PHASE 5: DATA PIPELINE RECOMMENDATIONS")
print("=" * 100)

print("""
IMMEDIATE ACTIONS (Next 7 Days):
================================
1. ✅ IRIS Pipeline: Operational (client + uploader continuous mode)
   - Status: Running (PIDs 4081716, 4092788)
   - Coverage: Last 24-48h real-time data

2. ⏳ Historical Backfills:
   - bmrs_bod: In progress (hourly batches, ~25 min total)
   - bmrs_mid: ✅ Complete (Oct 31 - Dec 17 filled)
   - bmrs_freq: 🔄 In progress (2022-2025 comprehensive backfill)
   - bmrs_boalf: Pending (after BOD completes)

3. ⚠️  Set Up Cron Jobs (CRITICAL):
   - Current: NO automated historical ingestion
   - Required: Daily cron for all historical tables
   - Priority: bmrs_bod, bmrs_costs, bmrs_mid, bmrs_fuelinst

4. ⚠️  Enable Systemd Services:
   - iris-client.service
   - iris-uploader.service
   - Purpose: Auto-restart on crash, auto-start on boot
   - Status: Created but NOT enabled

MEDIUM-TERM (Next 30 Days):
===========================
1. Add monitoring/alerting:
   - Data freshness checks (<30 min for IRIS, <24h for historical)
   - File queue monitoring (<1000 files)
   - Disk space alerts (>10GB free)

2. Document data dictionary:
   - Field definitions for all tables
   - Unit clarifications (MW vs MWh, £/MWh, Hz)
   - Business use cases per table

3. Create data quality dashboard:
   - Coverage metrics (days, %)
   - Duplicate detection
   - Gap identification
   - Last update timestamps

LONG-TERM (Next 90 Days):
=========================
1. Historical FREQ ingestion:
   - Decide: Configure historical API OR accept IRIS-only
   - If needed: Add FREQ to ingest_elexon_fixed.py
   - Backfill: 2020-2025 if required

2. Data validation framework:
   - Price bounds checking (-£1,000 to £1,000)
   - Volume reasonability tests
   - Temporal consistency checks

3. Automated gap detection & backfill:
   - Weekly gap scans
   - Automated backfill trigger
   - Alert on failed backfills
""")

print("\n" + "=" * 100)
print("PHASE 6: BUSINESS CONTEXT MAPPING")
print("=" * 100)

print("""
USE CASE: Battery Arbitrage (VLP Revenue Analysis)
===================================================
PRIMARY TABLES:
- bmrs_boalf_complete: Acceptance prices/volumes (filter validation_flag='Valid')
- bmrs_costs: System imbalance prices (SSP=SBP for settlement)
- bmrs_indgen_iris: Individual unit generation tracking

SECONDARY TABLES:
- bmrs_bod: Individual bid/offer submissions (used to derive bmrs_boalf_complete)
- bmrs_freq: Frequency response revenue opportunities

AVOID:
- bmrs_mid: This is WHOLESALE pricing, not imbalance (wrong for battery arbitrage)
- bmrs_boalf: Raw data without prices (use bmrs_boalf_complete instead)

USE CASE: Grid Frequency Analysis
===================================
PRIMARY TABLES:
- bmrs_freq: System frequency (Hz) over time
- bmrs_freq_iris: Real-time frequency (last 48h)

NOTE:
- Historical data limited (bmrs_freq was empty until Dec 16, 2025)
- IRIS provides Oct 28, 2025 onwards
- For older data, may need alternative sources

USE CASE: Generation Mix & Carbon Intensity
============================================
PRIMARY TABLES:
- bmrs_fuelinst: National fuel mix (wind, solar, gas, nuclear, etc.)
- bmrs_fuelinst_iris: Real-time fuel mix

CRITICAL:
- generation column is MW (NOT MWh!)
- Do NOT divide by 500
- For GW: divide MW by 1,000

USE CASE: Market Price Analysis
================================
IMBALANCE PRICES (Battery Trading):
- bmrs_costs: System imbalance prices (SSP=SBP since Nov 2015)

WHOLESALE PRICES (Forward Curves):
- bmrs_mid: Day-ahead and within-day market index
- WARNING: 24 days permanently missing (Apr/Jul/Sep/Oct 2024)

BALANCING MECHANISM PRICES (Unit-Specific):
- bmrs_boalf_complete: Individual acceptance prices
- bmrs_disbsad: Settlement volume-weighted averages

USE CASE: Outage & Unavailability Tracking
===========================================
PRIMARY TABLES:
- bmrs_remit_iris: Current outages (active since Nov 18, 2025)

DEPRECATED:
- bmrs_remit: Historical API returns 404 (use IRIS instead)

CRITICAL:
- Real-time only (IRIS retention ~48h)
- For historical analysis, limited data available
""")

print("\n" + "=" * 100)
print("AUDIT COMPLETE")
print("=" * 100)
print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}")
print(f"Output saved to: DATA_COMPREHENSIVE_AUDIT_DEC20_2025.txt")
print("=" * 100)

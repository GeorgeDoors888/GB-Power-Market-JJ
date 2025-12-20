# Data Pipeline Fix - December 17, 2025

## Problem Identified

**BOALF and System Prices Stopped Updating**

| Data Source | Status Before | Latest Data | Days Behind |
|-------------|---------------|-------------|-------------|
| bmrs_costs (system prices) | ❌ Stale | Dec 8 | 9 days |
| bmrs_boalf_complete (BM acceptances) | ❌ Stale | Dec 14 | 3 days |
| bmrs_mid_iris (market index) | ✅ Working | Dec 17 | Current |

**Impact**: All market KPIs showing 0 values because data sources were outdated.

## Root Cause

**Scripts existed but were NOT scheduled in cron**:
- `auto_backfill_costs_daily.py` - Updates system prices from Elexon API
- `derive_boalf_prices.py` - Derives acceptance prices by matching BOALF with BOD

## Solution Implemented

### 1. Manual Backfill (Immediate Fix)

```bash
# Backfill system prices (Dec 10-17)
python3 auto_backfill_costs_daily.py
# Result: 374 records uploaded, bmrs_costs now current through Dec 17

# Backfill BOALF prices (Dec 15-17)
python3 derive_boalf_prices.py --start 2025-12-15 --end 2025-12-17
# Result: 1,306 acceptances processed, 528 valid (40.4% match rate)
```

### 2. Updated Market KPIs

```bash
python3 add_market_kpis_to_dashboard.py
```

**Results** (Before → After):
- Avg Acceptance Price: £0 → **£72.24/MWh** ✅
- Avg Market Index Price: £92.41 → **£77.88/MWh** ✅ (was using stale IRIS data)
- Avg System Buy Price: £0 → **£64.00/MWh** ✅
- Daily VLP Revenue: £0 → **£22,991** ✅
- Price Volatility: £0 → **£36.2/MWh** ✅

### 3. Automated Pipeline (Permanent Fix)

**Added to cron**:

```cron
# Auto-backfill system prices - Daily at 2 AM
0 2 * * * cd /home/george/GB-Power-Market-JJ && /usr/bin/python3 auto_backfill_costs_daily.py >> logs/costs_backfill.log 2>&1

# Auto-backfill BOALF prices - Daily at 3 AM (3-day lookback)
0 3 * * * cd /home/george/GB-Power-Market-JJ && /usr/bin/python3 derive_boalf_prices.py --start $(date -d '3 days ago' +\%Y-\%m-\%d) --end $(date +\%Y-\%m-\%d) >> logs/boalf_backfill.log 2>&1

# Update market KPIs - Every 30 minutes
*/30 * * * * cd /home/george/GB-Power-Market-JJ && /usr/bin/python3 add_market_kpis_to_dashboard.py >> logs/market_kpis.log 2>&1
```

## Verification

**Dashboard now shows all 20 KPIs with live data**:

| Metric | Value | Status |
|--------|-------|--------|
| Avg Acceptance Price | £72.24/MWh | ✅ |
| BM-MID Spread | -£5.64/MWh | ✅ |
| Volume-Weighted Avg Price | £70.13/MWh | ✅ |
| Avg Market Index Price | £77.88/MWh | ✅ |
| Avg System Buy Price | £64.00/MWh | ✅ |
| Avg System Sell Price | £64.00/MWh | ✅ |
| Daily VLP Revenue | £22,991 | ✅ |
| Price Volatility | £36.2/MWh | ✅ |

**Plus 12 more metrics** with sparklines showing 48-period trends.

## Monitoring

**Log files created**:
- `logs/costs_backfill.log` - System prices backfill logs
- `logs/boalf_backfill.log` - BOALF price derivation logs
- `logs/market_kpis.log` - Dashboard update logs

**Check pipeline health**:
```bash
# View recent logs
tail -50 logs/costs_backfill.log
tail -50 logs/boalf_backfill.log
tail -50 logs/market_kpis.log

# Check data freshness
python3 << 'EOF'
from google.cloud import bigquery
from datetime import date

client = bigquery.Client(project='inner-cinema-476211-u9', location='US')

for table in ['bmrs_costs', 'bmrs_boalf_complete']:
    query = f"SELECT MAX(CAST(settlementDate AS DATE)) as latest FROM `inner-cinema-476211-u9.uk_energy_prod.{table}`"
    result = client.query(query).to_dataframe()
    print(f"{table}: {result['latest'].iloc[0]}")

#!/usr/bin/env python3
"""
Detailed explanation of IRIS data streams with real examples
"""
from google.cloud import bigquery
from google.oauth2 import service_account
from datetime import datetime, timedelta
import pytz

PROJECT_ID = "inner-cinema-476211-u9"
DATASET = "uk_energy_prod"

credentials = service_account.Credentials.from_service_account_file('inner-cinema-credentials.json')
client = bigquery.Client(project=PROJECT_ID, location="US", credentials=credentials)

now_utc = datetime.now(pytz.UTC)

print("=" * 100)
print("📚 DETAILED IRIS DATA EXPLANATION WITH REAL EXAMPLES")
print("=" * 100)

# 1. Balancing Energy Bids (bmrs_beb_iris)
print("\n" + "=" * 100)
print("💡 BALANCING ENERGY BIDS (bmrs_beb_iris)")
print("=" * 100)
print("""
WHAT IT IS: Bids from generators/batteries to provide balancing energy to National Grid
WHY IT'S STALE: This data is event-driven - only published when bids are submitted
               (typically before each settlement period starts)

COLUMNS EXPLAINED:
- bidId: Unique identifier for the bid
- quantity: Amount of energy offered (MWh) - how much power they can provide
- energyPrice: Price per MWh (£/MWh) - what they want to be paid
- flowDirection: Import (consuming) or Export (generating)

EXAMPLE USE: Battery offers 50 MWh at £100/MWh for SP39 (19:00-19:30)
            If market price goes above £100, National Grid may accept the bid
""")

query = f"""
SELECT 
    settlementDate, settlementPeriod, bidId, quantity, energyPrice, flowDirection
FROM `{PROJECT_ID}.{DATASET}.bmrs_beb_iris`
WHERE ingested_utc >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 2 HOUR)
ORDER BY ingested_utc DESC
LIMIT 5
"""
try:
    df = client.query(query).to_dataframe()
    if not df.empty:
        print("\n📊 REAL DATA (last 2 hours):")
        for _, row in df.iterrows():
            print(f"   SP{row['settlementPeriod']}: {row['bidId']} - {row['quantity']:.0f} MWh @ £{row['energyPrice']:.2f}/MWh ({row['flowDirection']})")
    else:
        print("\n⚠️ No bids in last 2 hours (normal - bids are submitted ahead of time)")
except Exception as e:
    print(f"\n❌ Error: {e}")

# 2. Bid/Offer Acceptances (bmrs_boalf_iris)
print("\n" + "=" * 100)
print("⚙️ BID/OFFER ACCEPTANCES (bmrs_boalf_iris)")
print("=" * 100)
print("""
WHAT IT IS: When National Grid ACCEPTS a bid/offer to balance the system
WHY ALWAYS FRESH: Acceptances happen continuously as grid needs balancing

COLUMNS EXPLAINED:
- acceptanceNumber: Unique ID for this acceptance (6663, 5842, etc.)
- levelFrom: Starting price level (£/MWh) - what they were originally bidding
- levelTo: Final accepted price (£/MWh) - what they actually got paid
- bmUnit: Which generator/battery was accepted (T_THURB-1 = Thurrock Battery)

EXAMPLE: National Grid accepted Thurrock Battery's offer:
         Original bid: £67/MWh (levelFrom)
         Accepted at: £18/MWh (levelTo)
         This means battery will export at £18/MWh (lower than bid = SO instructed)
""")

query = f"""
SELECT 
    settlementDate, bmUnit, acceptanceNumber, levelFrom, levelTo,
    TIMESTAMP_DIFF(timeTo, timeFrom, MINUTE) as duration_minutes
FROM `{PROJECT_ID}.{DATASET}.bmrs_boalf_iris`
WHERE ingested_utc >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 30 MINUTE)
ORDER BY ingested_utc DESC
LIMIT 5
"""
try:
    df = client.query(query).to_dataframe()
    if not df.empty:
        print("\n📊 REAL ACCEPTANCES (last 30 min):")
        for _, row in df.iterrows():
            action = "IMPORT" if row['levelFrom'] < 0 else "EXPORT"
            print(f"   #{row['acceptanceNumber']}: {row['bmUnit']} - £{row['levelFrom']}/MWh → £{row['levelTo']}/MWh ({action}, {row['duration_minutes']}min)")
    else:
        print("\n⚠️ No acceptances in last 30 min")
except Exception as e:
    print(f"\n❌ Error: {e}")

# 3. Market Index Prices (bmrs_mid_iris)
print("\n" + "=" * 100)
print("💰 MARKET INDEX PRICES (bmrs_mid_iris)")
print("=" * 100)
print("""
WHAT IT IS: Published market prices for each settlement period
WHY IT'S STALE: Updates every 30 minutes (after settlement period ends)
               Latest: 19:12 UTC for SP39 (19:00-19:30) - published ~12 min after period starts

COLUMNS EXPLAINED:
- dataProvider: APXMIDP (APX Market Index Price) or N2EXMIDP (N2EX Market)
- price: Market clearing price (£/MWh) - THE price for that half hour
- volume: Total volume traded (MWh)
- settlementPeriod: Which 30-min period (1-48 per day)

ARBITRAGE USE: Battery charges when price is low (£30/MWh), discharges when high (£90/MWh)
               Profit = (£90 - £30) × MWh discharged = £60/MWh margin
""")

query = f"""
SELECT 
    settlementDate, settlementPeriod, dataProvider, price, volume,
    ingested_utc
FROM `{PROJECT_ID}.{DATASET}.bmrs_mid_iris`
WHERE settlementDate = CURRENT_DATE()
ORDER BY settlementPeriod DESC
LIMIT 5
"""
try:
    df = client.query(query).to_dataframe()
    if not df.empty:
        print("\n📊 TODAY'S MARKET PRICES (latest periods):")
        for _, row in df.iterrows():
            time_label = f"{(row['settlementPeriod']-1)//2:02d}:{30 if row['settlementPeriod']%2==0 else '00'}"
            print(f"   SP{row['settlementPeriod']} ({time_label}): £{row['price']:.2f}/MWh | Volume: {row['volume']:.0f} MWh | {row['dataProvider']}")
    else:
        print("\n⚠️ No market prices today")
except Exception as e:
    print(f"\n❌ Error: {e}")

# 4. Network Constraints (bmrs_mels_iris / bmrs_mils_iris)
print("\n" + "=" * 100)
print("🚨 NETWORK CONSTRAINTS (Export/Import Limits)")
print("=" * 100)
print("""
WHAT IT IS: Maximum power limits set by National Grid for grid stability
- MELS = Maximum Export Limit (how much a unit can GENERATE)
- MILS = Maximum Import Limit (how much a unit can CONSUME)

WHY IT MATTERS: Battery or generator may be constrained due to:
- Transmission line capacity
- Local network limits
- System stability requirements

COLUMNS EXPLAINED:
- bmUnit: Which battery/generator (2__FBPGM002 = Flexgen Battery)
- levelFrom: Previous limit (MW)
- levelTo: New limit (MW) - if lower, they're being constrained
- settlementPeriod: When this limit applies

EXAMPLE: Flexgen battery normally 50 MW, but constrained to 31 MW in SP40
         Lost capacity: 19 MW (can't earn on that 19 MW)
""")

query = f"""
SELECT 
    'EXPORT' as limit_type, settlementPeriod, bmUnit, levelFrom, levelTo
FROM `{PROJECT_ID}.{DATASET}.bmrs_mels_iris`
WHERE ingested_utc >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 30 MINUTE)
  AND ABS(levelTo - levelFrom) > 5  -- Only show significant changes
ORDER BY ingested_utc DESC
LIMIT 3
UNION ALL
SELECT 
    'IMPORT' as limit_type, settlementPeriod, bmUnit, levelFrom, levelTo
FROM `{PROJECT_ID}.{DATASET}.bmrs_mils_iris`
WHERE ingested_utc >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 30 MINUTE)
  AND ABS(levelTo - levelFrom) > 5
ORDER BY ingested_utc DESC
LIMIT 3
"""
try:
    df = client.query(query).to_dataframe()
    if not df.empty:
        print("\n📊 RECENT CONSTRAINT CHANGES (last 30 min):")
        for _, row in df.iterrows():
            change = row['levelTo'] - row['levelFrom']
            symbol = "🔴" if change < 0 else "🟢"
            print(f"   {symbol} SP{row['settlementPeriod']} {row['bmUnit']}: {row['levelFrom']:.0f} → {row['levelTo']:.0f} MW ({change:+.0f} MW {row['limit_type']})")
    else:
        print("\n✅ No major constraint changes in last 30 min")
except Exception as e:
    print(f"\n❌ Error: {e}")

# 5. Wind Forecast (bmrs_windfor_iris)
print("\n" + "=" * 100)
print("🌬️ WIND FORECAST (bmrs_windfor_iris)")
print("=" * 100)
print("""
WHAT IT IS: National Grid's forecast of wind generation 1-3 hours ahead
WHY IT MATTERS: Helps predict when wind will ramp up/down
               - High wind forecast → Prices drop (excess supply)
               - Low wind forecast → Prices rise (need more gas/coal)

USAGE: If forecast shows wind dropping from 15 GW → 8 GW in 2 hours,
       expect prices to spike as gas plants need to ramp up
""")

query = f"""
SELECT 
    publishTime, startTime, generation,
    TIMESTAMP_DIFF(startTime, publishTime, HOUR) as hours_ahead
FROM `{PROJECT_ID}.{DATASET}.bmrs_windfor_iris`
WHERE publishTime >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 1 HOUR)
ORDER BY publishTime DESC, startTime ASC
LIMIT 10
"""
try:
    df = client.query(query).to_dataframe()
    if not df.empty:
        print("\n📊 WIND FORECAST (next few hours):")
        current_time = None
        for _, row in df.iterrows():
            pub_time = row['publishTime'].strftime('%H:%M')
            start_time = row['startTime'].strftime('%H:%M')
            if pub_time != current_time:
                print(f"\n   Published at {pub_time}:")
                current_time = pub_time
            print(f"      {start_time}: {row['generation']:.0f} MW ({row['hours_ahead']:.1f}h ahead)")
    else:
        print("\n⚠️ No wind forecasts in last hour")
except Exception as e:
    print(f"\n❌ Error: {e}")

print("\n" + "=" * 100)
print("📊 SUMMARY: WHY EACH TABLE MATTERS FOR BATTERY ARBITRAGE")
print("=" * 100)
print("""
1. 💰 bmrs_mid_iris (Market Prices) - MOST CRITICAL
   → Tells you when to charge (low £) and discharge (high £)
   → Profit calculation: (sell price - buy price) × MWh

2. ⚙️ bmrs_boalf_iris (Acceptances) - REVENUE TRACKING
   → Shows when YOUR battery was dispatched by National Grid
   → Confirms you got paid for providing balancing services

3. 🚨 bmrs_mels/mils_iris (Constraints) - LOST OPPORTUNITY
   → If constrained down, you can't discharge at full capacity
   → Lost revenue = constraint_MW × market_price

4. 🌬️ bmrs_windfor_iris (Wind Forecast) - PRICE PREDICTION
   → High wind coming → Prices will drop (don't discharge yet)
   → Low wind coming → Prices will spike (discharge soon)

5. 💡 bmrs_beb_iris (Energy Bids) - BID STRATEGY
   → See what prices others are bidding at
   → Adjust your bids to be competitive
""")

print("\n" + "=" * 100)
print("✅ EXPLANATION COMPLETE")
print("=" * 100)
